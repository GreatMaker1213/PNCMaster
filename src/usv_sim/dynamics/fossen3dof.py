# last update: 2026-03-18 21:27:07
# modifier: Claude Code

from __future__ import annotations

import numpy as np

from usv_sim.config import ActionConfig, DynamicsConfig
from usv_sim.core.math_utils import clip, finite_all, wrap_to_pi
from usv_sim.core.types import USVState


class Fossen3DOFDynamics:
    def __init__(self, cfg: DynamicsConfig, action_cfg: ActionConfig) -> None:
        self._cfg = cfg
        self._action_cfg = action_cfg

    def step(self, state: USVState, action: np.ndarray, dt: float) -> USVState:
        action = np.asarray(action, dtype=np.float64).reshape(-1)
        if action.shape != (2,):
            raise ValueError("action must have shape (2,)")

        surge_cmd = clip(float(action[0]), -1.0, 1.0)
        yaw_cmd = clip(float(action[1]), -1.0, 1.0)

        tau_u = surge_cmd * self._action_cfg.max_surge_force
        tau_r = yaw_cmd * self._action_cfg.max_yaw_moment

        du = (tau_u + self._cfg.m22 * state.v * state.r - self._cfg.d11 * state.u) / self._cfg.m11
        dv = (-self._cfg.m11 * state.u * state.r - self._cfg.d22 * state.v) / self._cfg.m22
        dr = (tau_r + (self._cfg.m11 - self._cfg.m22) * state.u * state.v - self._cfg.d33 * state.r) / self._cfg.m33

        dx = state.u * np.cos(state.psi) - state.v * np.sin(state.psi)
        dy = state.u * np.sin(state.psi) + state.v * np.cos(state.psi)
        dpsi = state.r

        x = float(state.x + dt * dx)
        y = float(state.y + dt * dy)
        psi = wrap_to_pi(float(state.psi + dt * dpsi))
        u = float(state.u + dt * du)
        v = float(state.v + dt * dv)
        r = float(state.r + dt * dr)

        if finite_all(x, y, psi, u, v, r):
            u = clip(u, -self._cfg.u_max_soft, self._cfg.u_max_soft)
            v = clip(v, -self._cfg.v_max_soft, self._cfg.v_max_soft)
            r = clip(r, -self._cfg.r_max_soft, self._cfg.r_max_soft)

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
