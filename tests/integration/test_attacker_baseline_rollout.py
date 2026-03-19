# last update: 2026-03-19 09:37:00
# modifier: Claude Code

from __future__ import annotations

from pathlib import Path

from usv_sim.config import load_config
from usv_sim.envs.attack_defense_env import AttackDefenseEnv
from usv_sim.policies.attacker_goal_baseline import GoalSeekingAttackerPolicy


ROOT = Path(__file__).resolve().parents[2]
CFG = load_config(ROOT / "configs" / "v0_2_baseline_validation.yaml")


def test_attacker_baseline_reaches_goal_in_fixed_validation_scenario() -> None:
    env = AttackDefenseEnv(cfg=CFG)
    policy = GoalSeekingAttackerPolicy(CFG.attacker_baseline)
    obs, _ = env.reset(seed=42)
    terminated = False
    truncated = False
    info = {}
    steps = 0
    while not (terminated or truncated):
        action = policy.act(obs)
        assert action.shape == (2,)
        assert action.dtype.name == "float32"
        assert float(action.min()) >= -1.0
        assert float(action.max()) <= 1.0
        obs, _, terminated, truncated, info = env.step(action)
        steps += 1
        if steps > CFG.env.max_episode_steps:
            raise AssertionError("baseline did not terminate within the configured horizon")
    assert info["termination_reason"] == "goal_reached"
    env.close()
