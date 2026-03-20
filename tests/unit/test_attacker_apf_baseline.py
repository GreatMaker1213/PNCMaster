# last update: 2026-03-20 11:49:00
# modifier: Codex

from __future__ import annotations

from pathlib import Path

import numpy as np

from usv_sim.config import load_config
from usv_sim.policies.attacker_apf_baseline import APFAttackerPolicy


ROOT = Path(__file__).resolve().parents[2]
CFG = load_config(ROOT / "configs" / "v0_3_obstacle_only.yaml")


def _build_obs() -> dict[str, np.ndarray]:
    return {
        "ego": np.array([0.0, 0.0, 0.0, 1.0, 0.0, 0.0], dtype=np.float32),
        "goal": np.array([20.0, 0.0, 20.0, 3.0], dtype=np.float32),
        "boundary": np.array([50.0, 50.0, 50.0, 50.0], dtype=np.float32),
        "defenders": np.zeros((4, 7), dtype=np.float32),
        "defenders_mask": np.zeros((4,), dtype=np.float32),
        "obstacles": np.zeros((8, 4), dtype=np.float32),
        "obstacles_mask": np.zeros((8,), dtype=np.float32),
    }


def test_apf_policy_action_shape_dtype_and_bounds() -> None:
    policy = APFAttackerPolicy(CFG.attacker_apf_baseline)
    obs = _build_obs()
    action = policy.act(obs)
    assert action.shape == (2,)
    assert action.dtype == np.float32
    assert float(action.min()) >= -1.0
    assert float(action.max()) <= 1.0


def test_apf_policy_steers_away_from_visible_obstacle() -> None:
    policy = APFAttackerPolicy(CFG.attacker_apf_baseline)
    obs = _build_obs()
    obs["obstacles_mask"][0] = 1.0
    obs["obstacles"][0] = np.array([5.0, 2.0, np.hypot(5.0, 2.0), 1.0], dtype=np.float32)
    action = policy.act(obs)
    assert float(action[1]) < 0.0


def test_apf_policy_reset_is_noop_and_safe() -> None:
    policy = APFAttackerPolicy(CFG.attacker_apf_baseline)
    policy.reset(seed=123)
    action = policy.act(_build_obs())
    assert action.shape == (2,)

