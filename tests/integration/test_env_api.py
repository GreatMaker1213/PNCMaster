# last update: 2026-03-19 09:36:00
# modifier: Claude Code

from __future__ import annotations

from pathlib import Path

import numpy as np

from usv_sim.config import load_config
from usv_sim.envs.attack_defense_env import AttackDefenseEnv


ROOT = Path(__file__).resolve().parents[2]
CFG = load_config(ROOT / "configs" / "v0_2_default.yaml")


def test_env_reset_and_step_follow_gymnasium_contract() -> None:
    env = AttackDefenseEnv(cfg=CFG)
    obs, info = env.reset(seed=123)
    assert set(obs.keys()) == {"ego", "goal", "boundary", "defenders", "defenders_mask", "obstacles", "obstacles_mask"}
    assert "goal_distance" in info
    step_out = env.step(np.array([0.0, 0.0], dtype=np.float32))
    assert len(step_out) == 5
    _, reward, terminated, truncated, step_info = step_out
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert "termination_reason" in step_info
    env.close()
