# last update: 2026-03-19 09:30:00
# modifier: Claude Code

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ActionConfig:
    max_surge_force: float
    max_yaw_moment: float


@dataclass(frozen=True)
class DynamicsConfig:
    m11: float
    m22: float
    m33: float
    d11: float
    d22: float
    d33: float
    u_max_soft: float
    v_max_soft: float
    r_max_soft: float
    hard_u_limit: float
    hard_v_limit: float
    hard_r_limit: float


@dataclass(frozen=True)
class BoundaryConfig:
    xmin: float
    xmax: float
    ymin: float
    ymax: float


@dataclass(frozen=True)
class ScenarioConfig:
    scenario_id: str
    boundary: BoundaryConfig
    attacker_radius: float
    defender_radius: float
    goal_radius: float
    capture_radius: float
    n_defenders: int
    n_obstacles: int
    obstacle_radius_min: float
    obstacle_radius_max: float
    spawn_clearance: float
    goal_clearance: float


@dataclass(frozen=True)
class ObservationConfig:
    sensing_radius: float
    max_defenders: int
    max_obstacles: int
    dtype: str


@dataclass(frozen=True)
class RewardConfig:
    progress_weight: float
    goal_reward: float
    capture_penalty: float
    collision_penalty: float
    boundary_penalty: float
    numerical_failure_penalty: float
    time_penalty: float
    control_l2_weight: float


@dataclass(frozen=True)
class EnvConfig:
    max_episode_steps: int
    dt_env: float
    sim_substeps: int
    render_mode: str | None


@dataclass(frozen=True)
class DefenderPolicyConfig:
    type: str
    surge_gain: float
    heading_gain: float


@dataclass(frozen=True)
class AttackerBaselineConfig:
    type: str
    surge_nominal: float
    surge_turning: float
    surge_near_goal: float
    heading_gain: float
    yaw_rate_damping: float
    heading_large_threshold: float
    slowdown_distance: float


@dataclass(frozen=True)
class ProjectConfig:
    env: EnvConfig
    action: ActionConfig
    dynamics: DynamicsConfig
    scenario: ScenarioConfig
    observation: ObservationConfig
    reward: RewardConfig
    defender_policy: DefenderPolicyConfig
    attacker_baseline: AttackerBaselineConfig


_DEFAULT_ATTACKER_BASELINE = {
    "type": "goal_seeking",
    "surge_nominal": 0.8,
    "surge_turning": 0.3,
    "surge_near_goal": 0.2,
    "heading_gain": 1.5,
    "yaw_rate_damping": 0.2,
    "heading_large_threshold": 0.7854,
    "slowdown_distance": 8.0,
}

_ALLOWED_RENDER_MODES = {None, "human"}


def _ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _validate(cfg: ProjectConfig) -> None:
    width = cfg.scenario.boundary.xmax - cfg.scenario.boundary.xmin
    height = cfg.scenario.boundary.ymax - cfg.scenario.boundary.ymin
    max_obstacle_radius = cfg.scenario.obstacle_radius_max
    largest_body_radius = max(
        cfg.scenario.attacker_radius,
        cfg.scenario.defender_radius,
        cfg.scenario.goal_radius,
        max_obstacle_radius,
    )

    _ensure(cfg.env.max_episode_steps >= 1, "env.max_episode_steps must be >= 1")
    _ensure(cfg.env.dt_env > 0.0, "env.dt_env must be > 0")
    _ensure(cfg.env.sim_substeps >= 1, "env.sim_substeps must be >= 1")
    _ensure(cfg.env.render_mode in _ALLOWED_RENDER_MODES, "env.render_mode must be one of {null, 'human'} in v0.2")

    _ensure(cfg.action.max_surge_force > 0.0, "action.max_surge_force must be > 0")
    _ensure(cfg.action.max_yaw_moment > 0.0, "action.max_yaw_moment must be > 0")

    _ensure(cfg.dynamics.m11 > 0.0, "dynamics.m11 must be > 0")
    _ensure(cfg.dynamics.m22 > 0.0, "dynamics.m22 must be > 0")
    _ensure(cfg.dynamics.m33 > 0.0, "dynamics.m33 must be > 0")
    _ensure(cfg.dynamics.u_max_soft > 0.0, "dynamics.u_max_soft must be > 0")
    _ensure(cfg.dynamics.v_max_soft > 0.0, "dynamics.v_max_soft must be > 0")
    _ensure(cfg.dynamics.r_max_soft > 0.0, "dynamics.r_max_soft must be > 0")
    _ensure(cfg.dynamics.hard_u_limit >= cfg.dynamics.u_max_soft, "dynamics.hard_u_limit must be >= dynamics.u_max_soft")
    _ensure(cfg.dynamics.hard_v_limit >= cfg.dynamics.v_max_soft, "dynamics.hard_v_limit must be >= dynamics.v_max_soft")
    _ensure(cfg.dynamics.hard_r_limit >= cfg.dynamics.r_max_soft, "dynamics.hard_r_limit must be >= dynamics.r_max_soft")

    _ensure(cfg.scenario.boundary.xmin < cfg.scenario.boundary.xmax, "scenario.boundary.xmin must be < xmax")
    _ensure(cfg.scenario.boundary.ymin < cfg.scenario.boundary.ymax, "scenario.boundary.ymin must be < ymax")
    _ensure(cfg.scenario.attacker_radius > 0.0, "scenario.attacker_radius must be > 0")
    _ensure(cfg.scenario.defender_radius > 0.0, "scenario.defender_radius must be > 0")
    _ensure(cfg.scenario.goal_radius > 0.0, "scenario.goal_radius must be > 0")
    _ensure(cfg.scenario.capture_radius > 0.0, "scenario.capture_radius must be > 0")
    _ensure(cfg.scenario.n_defenders >= 0, "scenario.n_defenders must be >= 0")
    _ensure(cfg.scenario.n_obstacles >= 0, "scenario.n_obstacles must be >= 0")
    _ensure(cfg.scenario.obstacle_radius_min > 0.0, "scenario.obstacle_radius_min must be > 0")
    _ensure(cfg.scenario.obstacle_radius_max >= cfg.scenario.obstacle_radius_min, "scenario.obstacle_radius_max must be >= obstacle_radius_min")
    _ensure(cfg.scenario.spawn_clearance >= 0.0, "scenario.spawn_clearance must be >= 0")
    _ensure(cfg.scenario.goal_clearance >= 0.0, "scenario.goal_clearance must be >= 0")

    _ensure(cfg.observation.sensing_radius > 0.0, "observation.sensing_radius must be > 0")
    _ensure(cfg.observation.max_defenders >= 0, "observation.max_defenders must be >= 0")
    _ensure(cfg.observation.max_obstacles >= 0, "observation.max_obstacles must be >= 0")
    _ensure(cfg.scenario.n_defenders <= cfg.observation.max_defenders, "scenario.n_defenders must be <= observation.max_defenders")
    _ensure(cfg.scenario.n_obstacles <= cfg.observation.max_obstacles, "scenario.n_obstacles must be <= observation.max_obstacles")

    _ensure(width > 2.0 * largest_body_radius, "boundary width is too small for configured geometry")
    _ensure(height > 2.0 * largest_body_radius, "boundary height is too small for configured geometry")

    min_width_for_spawn_goal = 2.0 * max(cfg.scenario.attacker_radius, cfg.scenario.goal_radius) + cfg.scenario.spawn_clearance + cfg.scenario.goal_clearance
    min_height_for_spawn_goal = min_width_for_spawn_goal
    _ensure(width > min_width_for_spawn_goal, "boundary width is too small to satisfy spawn_clearance/goal_clearance")
    _ensure(height > min_height_for_spawn_goal, "boundary height is too small to satisfy spawn_clearance/goal_clearance")

    _ensure(cfg.defender_policy.type == "pure_pursuit", "only defender_policy.type='pure_pursuit' is supported in v0.1/v0.2")

    _ensure(cfg.attacker_baseline.type == "goal_seeking", "only attacker_baseline.type='goal_seeking' is supported in v0.2")
    _ensure(0.0 <= cfg.attacker_baseline.surge_nominal <= 1.0, "attacker_baseline.surge_nominal must be in [0, 1]")
    _ensure(0.0 <= cfg.attacker_baseline.surge_turning <= 1.0, "attacker_baseline.surge_turning must be in [0, 1]")
    _ensure(0.0 <= cfg.attacker_baseline.surge_near_goal <= 1.0, "attacker_baseline.surge_near_goal must be in [0, 1]")
    _ensure(cfg.attacker_baseline.heading_gain >= 0.0, "attacker_baseline.heading_gain must be >= 0")
    _ensure(cfg.attacker_baseline.yaw_rate_damping >= 0.0, "attacker_baseline.yaw_rate_damping must be >= 0")
    _ensure(0.0 <= cfg.attacker_baseline.heading_large_threshold <= 3.141592653589793, "attacker_baseline.heading_large_threshold must be in [0, pi]")
    _ensure(cfg.attacker_baseline.slowdown_distance >= 0.0, "attacker_baseline.slowdown_distance must be >= 0")

    if cfg.scenario.scenario_id == "baseline_validation":
        _ensure(cfg.scenario.n_defenders == 0, "baseline_validation scenario must use n_defenders == 0")
        _ensure(cfg.scenario.n_obstacles == 0, "baseline_validation scenario must use n_obstacles == 0")


def load_config(path: str | Path) -> ProjectConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    attacker_baseline_raw = raw.get("attacker_baseline", _DEFAULT_ATTACKER_BASELINE)
    cfg = ProjectConfig(
        env=EnvConfig(**raw["env"]),
        action=ActionConfig(**raw["action"]),
        dynamics=DynamicsConfig(**raw["dynamics"]),
        scenario=ScenarioConfig(
            boundary=BoundaryConfig(**raw["scenario"]["boundary"]),
            **{k: v for k, v in raw["scenario"].items() if k != "boundary"},
        ),
        observation=ObservationConfig(**raw["observation"]),
        reward=RewardConfig(**raw["reward"]),
        defender_policy=DefenderPolicyConfig(**raw["defender_policy"]),
        attacker_baseline=AttackerBaselineConfig(**attacker_baseline_raw),
    )
    _validate(cfg)
    return cfg
