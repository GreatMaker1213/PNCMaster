# last update: 2026-03-25 10:09:00
# modifier: Codex

from __future__ import annotations

import numpy as np

from usv_sim.config import AttackerBaselineConfig
from usv_sim.guidance.base import GuidancePolicy, resolve_desired_surge_speed, resolve_desired_yaw_rate
from usv_sim.guidance.reference import DesiredVelocityReference


class GoalGuidance(GuidancePolicy):
    def __init__(
        self,
        cfg: AttackerBaselineConfig,
        *,
        desired_surge_speed_max: float,
        desired_yaw_rate_max: float,
    ) -> None:
        self._cfg = cfg
        self._desired_surge_speed_max = float(desired_surge_speed_max)
        self._desired_yaw_rate_max = float(desired_yaw_rate_max)

    def plan(self, obs: dict[str, np.ndarray]) -> DesiredVelocityReference:
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
            desired_speed_max=self._desired_surge_speed_max,
            surge_nominal=self._cfg.surge_nominal,
            surge_turning=self._cfg.surge_turning,
            surge_near_goal=self._cfg.surge_near_goal,
            heading_large_threshold=self._cfg.heading_large_threshold,
            slowdown_distance=self._cfg.slowdown_distance,
        )
        desired_yaw_rate = resolve_desired_yaw_rate(
            heading_error=heading_error,
            heading_gain=self._cfg.heading_gain,
            desired_yaw_rate_max=self._desired_yaw_rate_max,
        )
        return DesiredVelocityReference(
            desired_surge_speed=desired_speed,
            desired_yaw_rate=desired_yaw_rate,
        )
