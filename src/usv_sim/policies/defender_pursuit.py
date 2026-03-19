# last update: 2026-03-18 21:27:07
# modifier: Claude Code

from __future__ import annotations

import numpy as np

from usv_sim.config import DefenderPolicyConfig
from usv_sim.core.math_utils import wrap_to_pi
from usv_sim.core.types import USVState, WorldState
from usv_sim.policies.base import DefenderPolicy


class PurePursuitDefenderPolicy(DefenderPolicy):
    def __init__(self, cfg: DefenderPolicyConfig) -> None:
        self._cfg = cfg

    def act(self, defender: USVState, world: WorldState) -> np.ndarray:
        dx = world.attacker.x - defender.x
        dy = world.attacker.y - defender.y
        desired_heading = np.arctan2(dy, dx)
        heading_error = wrap_to_pi(float(desired_heading - defender.psi))

        surge_cmd = float(np.clip(self._cfg.surge_gain, -1.0, 1.0))
        yaw_cmd = float(np.clip(self._cfg.heading_gain * heading_error / np.pi, -1.0, 1.0))
        return np.array([surge_cmd, yaw_cmd], dtype=np.float32)
