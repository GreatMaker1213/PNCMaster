# last update: 2026-03-25 10:08:00
# modifier: Codex

from __future__ import annotations

import numpy as np

from usv_sim.core.math_utils import clip
from usv_sim.guidance.reference import DesiredVelocityReference


class GuidancePolicy:
    def reset(self, *, seed: int | None = None) -> None:
        del seed

    def plan(self, obs: dict[str, np.ndarray]) -> DesiredVelocityReference:
        del obs
        raise NotImplementedError


def resolve_desired_surge_speed(
    *,
    distance: float,
    goal_radius: float,
    heading_error: float,
    desired_speed_max: float,
    surge_nominal: float,
    surge_turning: float,
    surge_near_goal: float,
    heading_large_threshold: float,
    slowdown_distance: float,
) -> float:
    if distance <= goal_radius:
        return 0.0
    if distance < slowdown_distance:
        return float(surge_near_goal * desired_speed_max)
    if abs(heading_error) < heading_large_threshold:
        return float(surge_nominal * desired_speed_max)
    return float(surge_turning * desired_speed_max)


def resolve_desired_yaw_rate(
    *,
    heading_error: float,
    heading_gain: float,
    desired_yaw_rate_max: float,
) -> float:
    desired_yaw_rate = heading_gain * heading_error
    return clip(desired_yaw_rate, -desired_yaw_rate_max, desired_yaw_rate_max)
