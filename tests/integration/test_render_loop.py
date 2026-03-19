# last update: 2026-03-19 09:37:00
# modifier: Claude Code

from __future__ import annotations

from pathlib import Path

import numpy as np

from usv_sim.config import load_config
from usv_sim.envs.attack_defense_env import AttackDefenseEnv


ROOT = Path(__file__).resolve().parents[2]
CFG = load_config(ROOT / "configs" / "v0_2_baseline_validation.yaml")


def test_render_is_side_effect_free_and_close_is_idempotent() -> None:
    env = AttackDefenseEnv(cfg=CFG, render_mode="human")
    env.reset(seed=5)
    before = env._world
    env.render()
    after = env._world
    assert before == after
    assert env._world is not None
    env.step(np.array([0.0, 0.0], dtype=np.float32))
    before_step_render = env._world
    env.render()
    assert env._world == before_step_render
    env.close()
    env.close()
