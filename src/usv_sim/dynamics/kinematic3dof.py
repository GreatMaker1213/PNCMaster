# last update: 2026-03-25 10:28:00
# modifier: Codex

from __future__ import annotations

import numpy as np

from usv_sim.core.math_utils import clip, finite_all, wrap_to_pi
from usv_sim.core.types import USVState


class Kinematic3DOF:
    def __init__(self, *, surge_speed_max: float, yaw_rate_max: float) -> None:
        self._surge_speed_max = float(surge_speed_max)
        self._yaw_rate_max = float(yaw_rate_max)

    def step(self, state: USVState, action: np.ndarray, dt: float) -> USVState:
        action = np.asarray(action, dtype=np.float64).reshape(-1)
        if action.shape != (2,):
            raise ValueError("action must have shape (2,)")

        desired_u = clip(float(action[0]), 0.0, self._surge_speed_max)
        desired_r = clip(float(action[1]), -self._yaw_rate_max, self._yaw_rate_max)
        psi = wrap_to_pi(float(state.psi + dt * desired_r))
        x = float(state.x + dt * desired_u * np.cos(psi))
        y = float(state.y + dt * desired_u * np.sin(psi))
        u = desired_u
        v = 0.0
        r = desired_r

        if not finite_all(x, y, psi, u, v, r):
            return USVState(
                entity_id=state.entity_id,
                x=x,
                y=y,
                psi=psi,
                u=u,
                v=v,
                r=r,
                radius=state.radius,
            )

        return USVState(
            entity_id=state.entity_id,
            x=x,
            y=y,
            psi=psi,
            u=u,
            v=v,
            r=r,
            radius=state.radius,
        )
