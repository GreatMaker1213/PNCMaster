# last update: 2026-03-25 10:40:00
# modifier: Codex

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from usv_sim.config import load_config
from usv_sim.envs.factory import create_env
from usv_sim.policies.factory import create_attacker_policy


POLICY_CHOICES = ("goal_seeking", "apf", "heading_hold")
RENDER_MODE_CHOICES = ("human",)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one visualized episode with selected config and attacker policy.")
    parser.add_argument("--config", required=True, help="Path to config yaml")
    parser.add_argument("--policy", default=None, choices=POLICY_CHOICES, help="Policy override")
    parser.add_argument("--seed", type=int, default=0, help="Episode seed")
    parser.add_argument("--render-mode", default="human", choices=RENDER_MODE_CHOICES, help="Render mode")
    return parser.parse_args(argv)


def run_episode(*, config_path: str, policy_type: str | None, seed: int, render_mode: str) -> dict[str, object]:
    cfg = load_config(config_path)
    selected_policy = policy_type or cfg.attacker_policy.type
    policy = create_attacker_policy(cfg, selected_policy)
    env = create_env(cfg, render_mode=render_mode)

    terminated = False
    truncated = False
    total_reward = 0.0
    info: dict[str, object] = {}
    try:
        policy.reset(seed=seed)
        obs, _ = env.reset(seed=seed)
        env.render()
        while not (terminated or truncated):
            action = policy.act(obs)
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += float(reward)
            env.render()

        summary = {
            "config_path": str(Path(config_path)),
            "env_backend": cfg.env.backend,
            "policy_type": selected_policy,
            "seed": seed,
            "terminated": bool(terminated),
            "truncated": bool(truncated),
            "termination_reason": info.get("termination_reason", "unknown"),
            "episode_length": int(info.get("step_count", 0)),
            "return": float(total_reward),
            "goal_distance": float(info.get("goal_distance", float("nan"))),
            "min_defender_distance": float(info.get("min_defender_distance", float("nan"))),
            "min_obstacle_clearance": float(info.get("min_obstacle_clearance", float("nan"))),
        }
        print(summary)
        plt.ioff()
        plt.show(block=True)
        return summary
    finally:
        env.close()


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        run_episode(
            config_path=args.config,
            policy_type=args.policy,
            seed=int(args.seed),
            render_mode=str(args.render_mode),
        )
    except Exception as exc:
        print(f"[play.py] error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
