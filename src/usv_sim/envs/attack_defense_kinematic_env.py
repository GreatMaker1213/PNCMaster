# last update: 2026-03-25 10:28:00
# modifier: Codex

from __future__ import annotations

from pathlib import Path

import numpy as np

import gymnasium as gym

from usv_sim.config import ProjectConfig, load_config
from usv_sim.core.events import StepEvents
from usv_sim.core.kinematic_simulator import KinematicWorldSimulator
from usv_sim.core.types import WorldState
from usv_sim.dynamics.kinematic3dof import Kinematic3DOF
from usv_sim.logging.rollout import RolloutRecorder
from usv_sim.observation.builder import ObservationBuilder
from usv_sim.policies.defender_pursuit_kinematic import KinematicPurePursuitDefenderPolicy
from usv_sim.rendering.simple_2d import Simple2DRenderer
from usv_sim.reward.attack_defense_reward import AttackDefenseReward
from usv_sim.scenarios.generator import ScenarioGenerator
from usv_sim.termination.checker import TerminationChecker


_RENDER_MODE_SENTINEL = object()


class AttackDefenseKinematicEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        cfg: ProjectConfig | None = None,
        config_path: str | Path | None = None,
        render_mode: str | None | object = _RENDER_MODE_SENTINEL,
    ) -> None:
        super().__init__()
        if cfg is None:
            if config_path is None:
                raise ValueError("either cfg or config_path must be provided")
            cfg = load_config(config_path)
        self.cfg = cfg
        resolved_render_mode = cfg.env.render_mode if render_mode is _RENDER_MODE_SENTINEL else render_mode
        if resolved_render_mode not in {None, "human"}:
            raise ValueError("render_mode must be one of {None, 'human'}")
        self.render_mode = resolved_render_mode
        self._generator = ScenarioGenerator(cfg)
        self._propagator = Kinematic3DOF(
            surge_speed_max=cfg.velocity_tracking_controller.desired_surge_speed_max,
            yaw_rate_max=cfg.velocity_tracking_controller.desired_yaw_rate_max,
        )
        self._defender_policy = KinematicPurePursuitDefenderPolicy(cfg.defender_policy, cfg.velocity_tracking_controller)
        self._simulator = KinematicWorldSimulator(self._propagator, self._defender_policy, cfg)
        self._observation_builder = ObservationBuilder(cfg.observation)
        self._reward = AttackDefenseReward(cfg.reward)
        self._termination = TerminationChecker(cfg)
        self._recorder = RolloutRecorder()
        self._renderer: Simple2DRenderer | None = None
        self.action_space = gym.spaces.Box(
            low=np.array([0.0, -cfg.velocity_tracking_controller.desired_yaw_rate_max], dtype=np.float32),
            high=np.array(
                [cfg.velocity_tracking_controller.desired_surge_speed_max, cfg.velocity_tracking_controller.desired_yaw_rate_max],
                dtype=np.float32,
            ),
            dtype=np.float32,
        )
        self.observation_space = gym.spaces.Dict(
            {
                "ego": gym.spaces.Box(low=np.full((6,), -1e6, dtype=np.float32), high=np.full((6,), 1e6, dtype=np.float32), dtype=np.float32),
                "goal": gym.spaces.Box(low=np.full((4,), -1e6, dtype=np.float32), high=np.full((4,), 1e6, dtype=np.float32), dtype=np.float32),
                "boundary": gym.spaces.Box(low=np.full((4,), -1e6, dtype=np.float32), high=np.full((4,), 1e6, dtype=np.float32), dtype=np.float32),
                "defenders": gym.spaces.Box(low=np.full((cfg.observation.max_defenders, 7), -1e6, dtype=np.float32), high=np.full((cfg.observation.max_defenders, 7), 1e6, dtype=np.float32), dtype=np.float32),
                "defenders_mask": gym.spaces.Box(low=np.zeros((cfg.observation.max_defenders,), dtype=np.float32), high=np.ones((cfg.observation.max_defenders,), dtype=np.float32), dtype=np.float32),
                "obstacles": gym.spaces.Box(low=np.full((cfg.observation.max_obstacles, 4), -1e6, dtype=np.float32), high=np.full((cfg.observation.max_obstacles, 4), 1e6, dtype=np.float32), dtype=np.float32),
                "obstacles_mask": gym.spaces.Box(low=np.zeros((cfg.observation.max_obstacles,), dtype=np.float32), high=np.ones((cfg.observation.max_obstacles,), dtype=np.float32), dtype=np.float32),
            }
        )
        self._world: WorldState | None = None
        self._last_episode_summary: dict | None = None
        self._last_info: dict | None = None
        self._default_seed = 0

    def _make_reset_info(self, world: WorldState) -> dict:
        attacker = world.attacker
        goal_distance = float(np.hypot(world.goal.x - attacker.x, world.goal.y - attacker.y))
        min_defender_distance = min(
            (float(np.hypot(defender.x - attacker.x, defender.y - attacker.y)) for defender in world.defenders),
            default=float("inf"),
        )
        min_obstacle_clearance = min(
            (
                float(np.hypot(obstacle.x - attacker.x, obstacle.y - attacker.y) - attacker.radius - obstacle.radius)
                for obstacle in world.obstacles
            ),
            default=float("inf"),
        )
        return {
            "seed": world.seed,
            "scenario_id": world.scenario_id,
            "goal_distance": goal_distance,
            "min_defender_distance": min_defender_distance,
            "min_obstacle_clearance": min_obstacle_clearance,
            "termination_reason": "not_terminated",
        }

    def _make_step_info(self, world: WorldState, events: StepEvents, reward_breakdown, termination_result) -> dict:
        return {
            "step_count": world.step_count,
            "sim_time": world.sim_time,
            "scenario_id": world.scenario_id,
            "seed": world.seed,
            "goal_distance": events.goal_distance,
            "min_defender_distance": events.min_defender_distance,
            "min_obstacle_clearance": events.min_obstacle_clearance,
            "goal_reached": events.goal_reached,
            "captured": events.captured,
            "obstacle_collision": events.obstacle_collision,
            "out_of_bounds": events.out_of_bounds,
            "numerical_failure": events.numerical_failure,
            "reward_total": reward_breakdown.total,
            "reward_progress": reward_breakdown.progress,
            "reward_goal": reward_breakdown.goal,
            "reward_capture": reward_breakdown.capture,
            "reward_collision": reward_breakdown.collision,
            "reward_boundary": reward_breakdown.boundary,
            "reward_numerical_failure": reward_breakdown.numerical_failure,
            "reward_time": reward_breakdown.time,
            "reward_control": reward_breakdown.control,
            "is_success": termination_result.is_success,
            "termination_reason": termination_result.reason,
        }

    def _normalize_action_for_reward(self, action: np.ndarray) -> np.ndarray:
        action = np.asarray(action, dtype=np.float64).reshape(-1)
        if action.shape != (2,):
            raise ValueError("action must have shape (2,)")
        normalized = np.array(
            [
                action[0] / self.cfg.velocity_tracking_controller.desired_surge_speed_max,
                action[1] / self.cfg.velocity_tracking_controller.desired_yaw_rate_max,
            ],
            dtype=np.float32,
        )
        return normalized

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        del options
        if seed is None:
            seed = self._default_seed
            self._default_seed += 1
        self._world = self._generator.generate(int(seed))
        obs = self._observation_builder.build(self._world)
        info = self._make_reset_info(self._world)
        self._recorder.reset()
        self._recorder.start_episode(self._world, obs, info)
        self._last_episode_summary = None
        self._last_info = info
        return obs, info

    def step(self, action: np.ndarray):
        if self._world is None:
            raise RuntimeError("reset must be called before step")

        prev_world = self._world
        next_world, events = self._simulator.step(prev_world, action)
        termination_result = self._termination.check(next_world, events)
        normalized_action = self._normalize_action_for_reward(action)
        reward_breakdown = self._reward.compute(prev_world, next_world, events, normalized_action, termination_result.reason)
        obs = self._observation_builder.build(next_world)
        self._world = next_world
        info = self._make_step_info(next_world, events, reward_breakdown, termination_result)
        self._recorder.record_step(next_world, obs, action, info)
        if termination_result.terminated or termination_result.truncated:
            self._last_episode_summary = self._recorder.finalize_episode()
            info["episode_summary"] = self._last_episode_summary
        self._last_info = info
        return obs, float(reward_breakdown.total), termination_result.terminated, termination_result.truncated, info

    def render(self):
        if self.render_mode is None:
            return None
        if self._world is None:
            raise RuntimeError("reset must be called before render")
        if self.render_mode == "human":
            if self._renderer is None:
                self._renderer = Simple2DRenderer()
            self._renderer.render_world(self._world, self._last_info)
            return None
        raise ValueError(f"unsupported render_mode: {self.render_mode}")

    def close(self):
        if self._renderer is not None:
            self._renderer.close()
            self._renderer = None
        return None
