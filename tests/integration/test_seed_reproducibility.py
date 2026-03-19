# last update: 2026-03-19 09:36:00
# modifier: Claude Code

from __future__ import annotations

from pathlib import Path

import numpy as np

from usv_sim.config import load_config
from usv_sim.envs.attack_defense_env import AttackDefenseEnv


ROOT = Path(__file__).resolve().parents[2]
CFG = load_config(ROOT / "configs" / "v0_2_default.yaml")


def test_same_seed_and_action_sequence_are_reproducible() -> None:
    actions = [
        np.array([0.5, 0.1], dtype=np.float32),
        np.array([0.4, -0.2], dtype=np.float32),
        np.array([0.0, 0.0], dtype=np.float32),
    ]
    env_a = AttackDefenseEnv(cfg=CFG)
    env_b = AttackDefenseEnv(cfg=CFG)
    obs_a, _ = env_a.reset(seed=321)
    obs_b, _ = env_b.reset(seed=321)
    np.testing.assert_allclose(obs_a["goal"], obs_b["goal"])
    for action in actions:
        step_a = env_a.step(action)
        step_b = env_b.step(action)
        np.testing.assert_allclose(step_a[0]["ego"], step_b[0]["ego"])
        assert step_a[1:] == step_b[1:]
    env_a.close()
    env_b.close()
