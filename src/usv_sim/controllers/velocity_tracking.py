# last update: 2026-03-25 10:20:00
# modifier: Codex

from __future__ import annotations

import math

import numpy as np

from usv_sim.config import VelocityTrackingControllerConfig
from usv_sim.controllers.base import TrackingController
from usv_sim.core.math_utils import clip
from usv_sim.guidance.reference import DesiredVelocityReference


class VelocityTrackingController(TrackingController):
    def __init__(self, cfg: VelocityTrackingControllerConfig) -> None:
        self._cfg = cfg

    def act(self, obs: dict[str, np.ndarray], reference: DesiredVelocityReference) -> np.ndarray:
        ego = np.asarray(obs["ego"], dtype=np.float64)
        if ego.shape != (6,):
            raise ValueError("obs['ego'] must have shape (6,)")

        current_u = float(ego[0])
        current_v = float(ego[1])
        current_r = float(ego[2])
        desired_u = clip(float(reference.desired_surge_speed), 0.0, self._cfg.desired_surge_speed_max)
        desired_r = clip(
            float(reference.desired_yaw_rate),
            -self._cfg.desired_yaw_rate_max,
            self._cfg.desired_yaw_rate_max,
        )
        beta = math.atan2(current_v, max(abs(current_u), 1e-6))

        surge_cmd = clip(
            self._cfg.surge_gain * (desired_u - current_u) / self._cfg.desired_surge_speed_max,
            -1.0,
            1.0,
        )
        yaw_cmd = clip(
            self._cfg.yaw_rate_gain * (desired_r - current_r) / self._cfg.desired_yaw_rate_max
            - self._cfg.yaw_rate_damping * current_r
            - self._cfg.sideslip_gain * beta,
            -1.0,
            1.0,
        )
        return np.array([surge_cmd, yaw_cmd], dtype=np.float32)
