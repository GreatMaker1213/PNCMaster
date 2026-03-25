# last update: 2026-03-23 16:26:00
# modifier: Codex

from __future__ import annotations

import numpy as np

from usv_sim.guidance.base import GuidancePolicy, resolve_desired_surge_speed
from usv_sim.guidance.reference import HeadingSpeedReference


class GoalGuidance(GuidancePolicy):
    def __init__(self, cfg, *, desired_speed_max: float = 1.0) -> None:
        self._surge_nominal = float(cfg.surge_nominal)
        self._surge_turning = float(cfg.surge_turning)
        self._surge_near_goal = float(cfg.surge_near_goal)
        self._heading_large_threshold = float(cfg.heading_large_threshold)
        self._slowdown_distance = float(cfg.slowdown_distance)
        self._desired_speed_max = float(desired_speed_max)

    def plan(self, obs: dict[str, np.ndarray]) -> HeadingSpeedReference:
        goal = np.asarray(obs["goal"], dtype=np.float64)
        if goal.shape != (4,):
            raise ValueError("obs['goal'] must have shape (4,)")

        rel_x = float(goal[0])
        rel_y = float(goal[1])
        distance = float(goal[2])
        goal_radius = float(goal[3])
        heading_error = float(np.arctan2(rel_y, rel_x))
        desired_speed = resolve_desired_surge_speed(
            distance=distance,
            goal_radius=goal_radius,
            heading_error=heading_error,
            desired_speed_max=self._desired_speed_max,
            surge_nominal=self._surge_nominal,
            surge_turning=self._surge_turning,
            surge_near_goal=self._surge_near_goal,
            heading_large_threshold=self._heading_large_threshold,
            slowdown_distance=self._slowdown_distance,
        )
        return HeadingSpeedReference(
            desired_heading_error=heading_error,
            desired_surge_speed=desired_speed,
        )
