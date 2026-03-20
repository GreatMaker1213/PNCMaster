# last update: 2026-03-20 11:50:00
# modifier: Codex

from __future__ import annotations

from pathlib import Path

import numpy as np

from usv_sim.config import load_config
from usv_sim.policies.attacker_heading_baseline import HeadingHoldAttackerPolicy


ROOT = Path(__file__).resolve().parents[2]
CFG = load_config(ROOT / "configs" / "v0_3_goal_only.yaml")


def _build_obs(rel_y: float) -> dict[str, np.ndarray]:
    return {
        "ego": np.array([0.0, 0.0, 0.1, 1.0, 0.0, 0.0], dtype=np.float32),
        "goal": np.array([20.0, rel_y, np.hypot(20.0, rel_y), 3.0], dtype=np.float32),
        "boundary": np.array([50.0, 50.0, 50.0, 50.0], dtype=np.float32),
        "defenders": np.zeros((4, 7), dtype=np.float32),
        "defenders_mask": np.zeros((4,), dtype=np.float32),
        "obstacles": np.zeros((8, 4), dtype=np.float32),
        "obstacles_mask": np.zeros((8,), dtype=np.float32),
    }


def test_heading_policy_turns_toward_positive_goal_offset() -> None:
    policy = HeadingHoldAttackerPolicy(CFG.attacker_heading_baseline)
    action = policy.act(_build_obs(rel_y=5.0))
    assert action.shape == (2,)
    assert float(action[1]) > 0.0


def test_heading_policy_reset_is_noop_and_safe() -> None:
    policy = HeadingHoldAttackerPolicy(CFG.attacker_heading_baseline)
    policy.reset(seed=0)
    action = policy.act(_build_obs(rel_y=-5.0))
    assert action.dtype == np.float32
    assert float(action.min()) >= -1.0
    assert float(action.max()) <= 1.0

