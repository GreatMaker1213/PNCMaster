# last update: 2026-03-19 09:30:00
# modifier: Claude Code

from __future__ import annotations

import random
from typing import Iterable

from usv_sim.config import ProjectConfig
from usv_sim.core.math_utils import distance2d, wrap_to_pi
from usv_sim.core.types import CircularObstacle, GoalRegion, RectBoundary, USVState, WorldState


class ScenarioGenerator:
    def __init__(self, cfg: ProjectConfig) -> None:
        self._cfg = cfg

    def _sample_point(self, rng: random.Random, margin: float) -> tuple[float, float]:
        boundary = self._cfg.scenario.boundary
        x = rng.uniform(boundary.xmin + margin, boundary.xmax - margin)
        y = rng.uniform(boundary.ymin + margin, boundary.ymax - margin)
        return x, y

    def _valid_against_circles(self, x: float, y: float, radius: float, circles: Iterable[tuple[float, float, float]], clearance: float = 0.0) -> bool:
        for cx, cy, cr in circles:
            if distance2d(x, y, cx, cy) <= radius + cr + clearance:
                return False
        return True

    def _make_boundary(self) -> RectBoundary:
        cfg = self._cfg.scenario.boundary
        return RectBoundary(xmin=cfg.xmin, xmax=cfg.xmax, ymin=cfg.ymin, ymax=cfg.ymax)

    def _generate_baseline_validation(self, seed: int) -> WorldState:
        cfg = self._cfg.scenario
        boundary = self._make_boundary()
        attacker = USVState(
            entity_id=0,
            x=20.0,
            y=50.0,
            psi=0.0,
            u=0.0,
            v=0.0,
            r=0.0,
            radius=cfg.attacker_radius,
        )
        goal = GoalRegion(x=80.0, y=50.0, radius=cfg.goal_radius)
        return WorldState(
            sim_time=0.0,
            step_count=0,
            seed=seed,
            scenario_id=cfg.scenario_id,
            attacker=attacker,
            defenders=tuple(),
            obstacles=tuple(),
            goal=goal,
            boundary=boundary,
        )

    def _generate_default(self, seed: int) -> WorldState:
        rng = random.Random(seed)
        cfg = self._cfg.scenario
        boundary = self._make_boundary()

        circles: list[tuple[float, float, float]] = []

        for _ in range(2000):
            ax, ay = self._sample_point(rng, cfg.attacker_radius + cfg.spawn_clearance)
            gx, gy = self._sample_point(rng, cfg.goal_radius + cfg.goal_clearance)
            if distance2d(ax, ay, gx, gy) > cfg.spawn_clearance + cfg.goal_clearance + cfg.attacker_radius + cfg.goal_radius:
                break
        else:
            raise RuntimeError("failed to sample attacker/goal positions")

        attacker = USVState(
            entity_id=0,
            x=ax,
            y=ay,
            psi=wrap_to_pi(rng.uniform(-3.141592653589793, 3.141592653589793)),
            u=0.0,
            v=0.0,
            r=0.0,
            radius=cfg.attacker_radius,
        )
        goal = GoalRegion(x=gx, y=gy, radius=cfg.goal_radius)
        circles.append((ax, ay, cfg.attacker_radius))
        circles.append((gx, gy, cfg.goal_radius))

        obstacles = []
        for i in range(cfg.n_obstacles):
            for _ in range(2000):
                radius = rng.uniform(cfg.obstacle_radius_min, cfg.obstacle_radius_max)
                ox, oy = self._sample_point(rng, radius)
                if self._valid_against_circles(ox, oy, radius, circles, clearance=cfg.goal_clearance):
                    obstacles.append(CircularObstacle(entity_id=1000 + i, x=ox, y=oy, radius=radius))
                    circles.append((ox, oy, radius))
                    break
            else:
                raise RuntimeError("failed to sample obstacle positions")

        defenders = []
        for i in range(cfg.n_defenders):
            for _ in range(2000):
                dx, dy = self._sample_point(rng, cfg.defender_radius + cfg.spawn_clearance)
                if not self._valid_against_circles(dx, dy, cfg.defender_radius, circles, clearance=cfg.spawn_clearance):
                    continue
                if distance2d(dx, dy, attacker.x, attacker.y) <= cfg.capture_radius + cfg.defender_radius:
                    continue
                defenders.append(
                    USVState(
                        entity_id=2000 + i,
                        x=dx,
                        y=dy,
                        psi=wrap_to_pi(rng.uniform(-3.141592653589793, 3.141592653589793)),
                        u=0.0,
                        v=0.0,
                        r=0.0,
                        radius=cfg.defender_radius,
                    )
                )
                circles.append((dx, dy, cfg.defender_radius))
                break
            else:
                raise RuntimeError("failed to sample defender positions")

        return WorldState(
            sim_time=0.0,
            step_count=0,
            seed=seed,
            scenario_id=cfg.scenario_id,
            attacker=attacker,
            defenders=tuple(defenders),
            obstacles=tuple(obstacles),
            goal=goal,
            boundary=boundary,
        )

    def generate(self, seed: int) -> WorldState:
        if self._cfg.scenario.scenario_id == "baseline_validation":
            return self._generate_baseline_validation(seed)
        return self._generate_default(seed)
