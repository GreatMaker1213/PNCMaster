# last update: 2026-03-19 09:37:00
# modifier: Claude Code

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from usv_sim.config import load_config
from usv_sim.envs.attack_defense_env import AttackDefenseEnv
from usv_sim.policies.attacker_goal_baseline import GoalSeekingAttackerPolicy


def main() -> None:
    cfg = load_config(ROOT / "configs" / "v0_2_baseline_validation.yaml")
    env = AttackDefenseEnv(cfg=cfg, render_mode="human")
    policy = GoalSeekingAttackerPolicy(cfg.attacker_baseline)
    obs, info = env.reset(seed=0)
    env.render()
    terminated = False
    truncated = False
    try:
        while not (terminated or truncated):
            action = policy.act(obs)
            obs, reward, terminated, truncated, info = env.step(action)
            del reward
            env.render()
        print({"termination_reason": info["termination_reason"], "goal_distance": info["goal_distance"]})
    finally:
        env.close()


if __name__ == "__main__":
    main()
