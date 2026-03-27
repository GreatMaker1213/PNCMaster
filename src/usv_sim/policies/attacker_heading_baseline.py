# last update: 2026-03-25 10:36:00
# modifier: Codex

from __future__ import annotations

import numpy as np

from usv_sim.config import AttackerHeadingBaselineConfig, TrackingControllerConfig, VelocityTrackingControllerConfig
from usv_sim.core.math_utils import clip
from usv_sim.guidance.base import GuidancePolicy, resolve_desired_surge_speed, resolve_desired_yaw_rate
from usv_sim.guidance.reference import DesiredVelocityReference
from usv_sim.policies.base import AttackerPolicy


class HeadingHoldVelocityGuidance(GuidancePolicy):
    def __init__(
        self,
        cfg: AttackerHeadingBaselineConfig,
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
        return DesiredVelocityReference(desired_surge_speed=desired_speed, desired_yaw_rate=desired_yaw_rate)


class HeadingHoldAttackerPolicy(AttackerPolicy):
    def __init__(
        self,
        cfg: AttackerHeadingBaselineConfig,
        controller_cfg: TrackingControllerConfig | VelocityTrackingControllerConfig | None = None,
    ) -> None:
        self._cfg = cfg
        del controller_cfg

    def reset(self, *, seed: int | None = None) -> None:
        del seed

    def act(self, obs: dict[str, np.ndarray]) -> np.ndarray:
        goal = np.asarray(obs["goal"], dtype=np.float64)
        ego = np.asarray(obs["ego"], dtype=np.float64)
        if goal.shape != (4,):
            raise ValueError("obs['goal'] must have shape (4,)")
        if ego.shape != (6,):
            raise ValueError("obs['ego'] must have shape (6,)")

        rel_x = float(goal[0])
        rel_y = float(goal[1])
        distance = float(goal[2])
        goal_radius = float(goal[3])
        yaw_rate = float(ego[2])

        heading_error = float(np.arctan2(rel_y, rel_x))
        yaw_cmd = clip(self._cfg.heading_gain * heading_error / np.pi - self._cfg.yaw_rate_damping * yaw_rate, -1.0, 1.0)

        if distance <= goal_radius:
            surge_cmd = 0.0
        elif distance < self._cfg.slowdown_distance:
            surge_cmd = self._cfg.surge_near_goal
        elif abs(heading_error) < self._cfg.heading_large_threshold:
            surge_cmd = self._cfg.surge_nominal
        else:
            surge_cmd = self._cfg.surge_turning

        return np.array([surge_cmd, yaw_cmd], dtype=np.float32)
