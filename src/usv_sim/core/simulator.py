# last update: 2026-03-18 22:13:27
# modifier: Claude Code

from __future__ import annotations

from dataclasses import dataclass

from usv_sim.config import ProjectConfig
from usv_sim.core.events import StepEvents
from usv_sim.core.geometry import obstacle_clearance, within_boundary
from usv_sim.core.math_utils import distance2d, finite_all
from usv_sim.core.types import USVState, WorldState
from usv_sim.dynamics.fossen3dof import Fossen3DOFDynamics
from usv_sim.policies.base import DefenderPolicy


@dataclass(frozen=True)
class _EventSnapshot:
    goal_distance: float
    min_defender_distance: float
    min_obstacle_clearance: float
    goal_reached: bool
    captured: bool
    obstacle_collision: bool
    out_of_bounds: bool
    numerical_failure: bool


class WorldSimulator:
    def __init__(
        self,
        dynamics: Fossen3DOFDynamics,
        defender_policy: DefenderPolicy,
        cfg: ProjectConfig,
    ) -> None:
        self._dynamics = dynamics
        self._defender_policy = defender_policy
        self._cfg = cfg
        self._dt_sim = cfg.env.dt_env / cfg.env.sim_substeps

    def _is_numerical_failure(self, usv: USVState) -> bool:
        return not finite_all(usv.x, usv.y, usv.psi, usv.u, usv.v, usv.r) or abs(usv.u) > self._cfg.dynamics.hard_u_limit or abs(usv.v) > self._cfg.dynamics.hard_v_limit or abs(usv.r) > self._cfg.dynamics.hard_r_limit or abs(usv.x) > 1e6 or abs(usv.y) > 1e6

    def _evaluate(self, attacker: USVState, defenders: tuple[USVState, ...], obstacles, goal, boundary) -> _EventSnapshot:
        goal_distance = distance2d(attacker.x, attacker.y, goal.x, goal.y)
        min_defender_distance = min((distance2d(attacker.x, attacker.y, d.x, d.y) for d in defenders), default=float("inf"))
        min_obstacle_clearance = min((obstacle_clearance(attacker, obs) for obs in obstacles), default=float("inf"))
        goal_reached = goal_distance <= goal.radius
        captured = min_defender_distance <= self._cfg.scenario.capture_radius
        obstacle_collision = min_obstacle_clearance <= 0.0
        out_of_bounds = not within_boundary(attacker, boundary)
        numerical_failure = self._is_numerical_failure(attacker)
        return _EventSnapshot(
            goal_distance=goal_distance,
            min_defender_distance=min_defender_distance,
            min_obstacle_clearance=min_obstacle_clearance,
            goal_reached=goal_reached,
            captured=captured,
            obstacle_collision=obstacle_collision,
            out_of_bounds=out_of_bounds,
            numerical_failure=numerical_failure,
        )

    def _is_real_terminal(self, snapshot: _EventSnapshot) -> bool:
        return any(
            [
                snapshot.goal_reached,
                snapshot.captured,
                snapshot.obstacle_collision,
                snapshot.out_of_bounds,
                snapshot.numerical_failure,
            ]
        )

    def _step_defender(self, defender: USVState, world: WorldState) -> USVState:
        action = self._defender_policy.act(defender, world)
        candidate = self._dynamics.step(defender, action, self._dt_sim)
        invalid_obstacle = any(obstacle_clearance(candidate, obstacle) <= 0.0 for obstacle in world.obstacles)
        invalid_boundary = not within_boundary(candidate, world.boundary)
        if invalid_obstacle or invalid_boundary or self._is_numerical_failure(candidate):
            return USVState(
                entity_id=defender.entity_id,
                x=defender.x,
                y=defender.y,
                psi=defender.psi,
                u=0.0,
                v=0.0,
                r=0.0,
                radius=defender.radius,
            )
        return candidate

    def step(self, world: WorldState, attacker_action) -> tuple[WorldState, StepEvents]:
        current_attacker = world.attacker
        current_defenders = world.defenders
        final_snapshot = self._evaluate(current_attacker, current_defenders, world.obstacles, world.goal, world.boundary)

        elapsed = 0.0
        for _ in range(self._cfg.env.sim_substeps):
            candidate_attacker = self._dynamics.step(current_attacker, attacker_action, self._dt_sim)
            intermediate_world = WorldState(
                sim_time=world.sim_time + elapsed + self._dt_sim,
                step_count=world.step_count,
                seed=world.seed,
                scenario_id=world.scenario_id,
                attacker=candidate_attacker,
                defenders=current_defenders,
                obstacles=world.obstacles,
                goal=world.goal,
                boundary=world.boundary,
            )
            candidate_defenders = tuple(self._step_defender(defender, intermediate_world) for defender in current_defenders)
            snapshot = self._evaluate(candidate_attacker, candidate_defenders, world.obstacles, world.goal, world.boundary)
            current_attacker = candidate_attacker
            current_defenders = candidate_defenders
            final_snapshot = snapshot
            elapsed += self._dt_sim
            if self._is_real_terminal(snapshot):
                break

        next_world = WorldState(
            sim_time=world.sim_time + elapsed,
            step_count=world.step_count + 1,
            seed=world.seed,
            scenario_id=world.scenario_id,
            attacker=current_attacker,
            defenders=current_defenders,
            obstacles=world.obstacles,
            goal=world.goal,
            boundary=world.boundary,
        )
        events = StepEvents(
            goal_reached=final_snapshot.goal_reached,
            captured=final_snapshot.captured,
            obstacle_collision=final_snapshot.obstacle_collision,
            out_of_bounds=final_snapshot.out_of_bounds,
            numerical_failure=final_snapshot.numerical_failure,
            min_defender_distance=final_snapshot.min_defender_distance,
            min_obstacle_clearance=final_snapshot.min_obstacle_clearance,
            goal_distance=final_snapshot.goal_distance,
        )
        return next_world, events
