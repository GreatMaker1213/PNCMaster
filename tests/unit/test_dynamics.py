# last update: 2026-03-19 09:35:00
# modifier: Claude Code

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from usv_sim.config import load_config
from usv_sim.core.types import USVState
from usv_sim.dynamics.fossen3dof import Fossen3DOFDynamics


ROOT = Path(__file__).resolve().parents[2]
CFG = load_config(ROOT / "configs" / "v0_2_default.yaml")
DYNAMICS = Fossen3DOFDynamics(CFG.dynamics, CFG.action)


def _make_state(**overrides) -> USVState:
    base = dict(entity_id=0, x=0.0, y=0.0, psi=0.0, u=0.0, v=0.0, r=0.0, radius=1.0)
    base.update(overrides)
    return USVState(**base)


def test_zero_action_damps_forward_velocity() -> None:
    state = _make_state(u=1.5)
    next_state = DYNAMICS.step(state, np.array([0.0, 0.0], dtype=np.float32), 0.1)
    assert next_state.u < state.u
    assert next_state.x > state.x


def test_nonzero_yaw_action_changes_r_and_then_psi() -> None:
    state = _make_state()
    next_state = DYNAMICS.step(state, np.array([0.0, 1.0], dtype=np.float32), 0.1)
    next_next_state = DYNAMICS.step(next_state, np.array([0.0, 1.0], dtype=np.float32), 0.1)
    assert next_state.r > 0.0
    assert not math.isclose(next_next_state.psi, state.psi)


def test_heading_is_wrapped_into_pi_interval() -> None:
    state = _make_state(psi=3.13, r=1.2)
    next_state = DYNAMICS.step(state, np.array([0.0, 0.0], dtype=np.float32), 1.0)
    assert -math.pi < next_state.psi <= math.pi


def test_soft_limits_are_applied_to_velocity_components() -> None:
    state = _make_state(u=10.0, v=5.0, r=3.0)
    next_state = DYNAMICS.step(state, np.array([1.0, 1.0], dtype=np.float32), 0.1)
    assert abs(next_state.u) <= CFG.dynamics.u_max_soft
    assert abs(next_state.v) <= CFG.dynamics.v_max_soft
    assert abs(next_state.r) <= CFG.dynamics.r_max_soft


def test_bounded_input_keeps_state_finite() -> None:
    state = _make_state(u=0.5, v=0.1, r=0.05)
    next_state = DYNAMICS.step(state, np.array([1.0, -1.0], dtype=np.float32), 0.1)
    values = (next_state.x, next_state.y, next_state.psi, next_state.u, next_state.v, next_state.r)
    assert all(math.isfinite(value) for value in values)
