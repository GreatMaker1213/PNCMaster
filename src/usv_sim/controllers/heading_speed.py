# last update: 2026-03-23 16:26:00
# modifier: Codex

from __future__ import annotations

import numpy as np

from usv_sim.config import TrackingControllerConfig
from usv_sim.controllers.base import TrackingController
from usv_sim.core.math_utils import clip
from usv_sim.guidance.reference import HeadingSpeedReference


class HeadingSpeedTrackingController(TrackingController):
    def __init__(
        self,
        cfg: TrackingControllerConfig | None = None,
        *,
        heading_gain: float | None = None,
        yaw_rate_damping: float | None = None,
        surge_gain: float | None = None,
        desired_speed_max: float | None = None,
    ) -> None:
        self.heading_gain = float(heading_gain if heading_gain is not None else (cfg.heading_gain if cfg is not None else 1.5))
        self.yaw_rate_damping = float(
            yaw_rate_damping if yaw_rate_damping is not None else (cfg.yaw_rate_damping if cfg is not None else 0.2)
        )
        self.surge_gain = float(surge_gain if surge_gain is not None else (cfg.surge_gain if cfg is not None else 0.8))
        self.desired_speed_max = float(
            desired_speed_max if desired_speed_max is not None else (cfg.desired_speed_max if cfg is not None else 3.0)
        )

    def act(self, obs: dict[str, np.ndarray], reference: HeadingSpeedReference) -> np.ndarray:
        ego = np.asarray(obs["ego"], dtype=np.float64)
        if ego.shape != (6,):
            raise ValueError("obs['ego'] must have shape (6,)")

        current_u = float(ego[0])
        yaw_rate = float(ego[2])
        desired_heading_error = float(reference.desired_heading_error)
        desired_surge_speed = clip(float(reference.desired_surge_speed), 0.0, self.desired_speed_max)
        yaw_cmd = clip(self.heading_gain * desired_heading_error / np.pi - self.yaw_rate_damping * yaw_rate, -1.0, 1.0)
        surge_cmd = clip(self.surge_gain * (desired_surge_speed - current_u) / self.desired_speed_max, -1.0, 1.0)
        return np.array([surge_cmd, yaw_cmd], dtype=np.float32)
