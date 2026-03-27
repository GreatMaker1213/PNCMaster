# last update: 2026-03-25 10:28:00
# modifier: Codex

from __future__ import annotations

import numpy as np

from usv_sim.config import DefenderPolicyConfig, VelocityTrackingControllerConfig
from usv_sim.core.math_utils import clip, wrap_to_pi
from usv_sim.core.types import USVState, WorldState


class KinematicPurePursuitDefenderPolicy:
    def __init__(self, cfg: DefenderPolicyConfig, velocity_cfg: VelocityTrackingControllerConfig) -> None:
        self._cfg = cfg
        self._velocity_cfg = velocity_cfg

    def act(self, defender: USVState, world: WorldState) -> np.ndarray:
        dx = world.attacker.x - defender.x
        dy = world.attacker.y - defender.y
        desired_heading = np.arctan2(dy, dx)
        heading_error = wrap_to_pi(float(desired_heading - defender.psi))
        desired_speed = clip(
            float(self._cfg.surge_gain) * self._velocity_cfg.desired_surge_speed_max,
            0.0,
            self._velocity_cfg.desired_surge_speed_max,
        )
        desired_yaw_rate = clip(
            float(self._cfg.heading_gain) * heading_error,
            -self._velocity_cfg.desired_yaw_rate_max,
            self._velocity_cfg.desired_yaw_rate_max,
        )
        return np.array([desired_speed, desired_yaw_rate], dtype=np.float32)
