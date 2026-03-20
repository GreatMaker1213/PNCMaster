# last update: 2026-03-20 11:45:00
# modifier: Codex

from __future__ import annotations

from dataclasses import replace
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np

from usv_sim.config import load_config
from usv_sim.envs.attack_defense_env import AttackDefenseEnv
from usv_sim.policies.attacker_apf_baseline import APFAttackerPolicy
from usv_sim.policies.attacker_goal_baseline import GoalSeekingAttackerPolicy


def run_constant_episode(n_defenders: int) -> tuple[bool, int]:
    cfg = load_config(ROOT / "configs" / "v0_1_default.yaml")
    cfg = replace(cfg, scenario=replace(cfg.scenario, n_defenders=n_defenders))
    env = AttackDefenseEnv(cfg=cfg)
    obs, info = env.reset(seed=123)
    assert obs["ego"].shape == (6,)
    assert obs["goal"].shape == (4,)
    steps = 0
    terminated = False
    truncated = False
    while not (terminated or truncated):
        action = np.array([0.5, 0.0], dtype=np.float32)
        obs, reward, terminated, truncated, info = env.step(action)
        assert np.isfinite(reward)
        steps += 1
        if steps > cfg.env.max_episode_steps + 2:
            raise AssertionError("episode did not terminate within expected horizon")
    env.close()
    return bool(info["termination_reason"] in {"goal_reached", "captured", "obstacle_collision", "out_of_bounds", "numerical_failure", "time_limit"}), steps


def run_baseline_episode() -> tuple[bool, int]:
    cfg = load_config(ROOT / "configs" / "v0_2_baseline_validation.yaml")
    env = AttackDefenseEnv(cfg=cfg)
    policy = GoalSeekingAttackerPolicy(cfg.attacker_baseline)
    obs, _ = env.reset(seed=123)
    steps = 0
    terminated = False
    truncated = False
    info = {}
    while not (terminated or truncated):
        action = policy.act(obs)
        obs, reward, terminated, truncated, info = env.step(action)
        assert np.isfinite(reward)
        steps += 1
        if steps > cfg.env.max_episode_steps + 2:
            raise AssertionError("baseline episode did not terminate within expected horizon")
    env.close()
    return bool(info["termination_reason"] == "goal_reached"), steps


def run_apf_episode() -> tuple[bool, int]:
    cfg = load_config(ROOT / "configs" / "v0_3_obstacle_only.yaml")
    env = AttackDefenseEnv(cfg=cfg)
    policy = APFAttackerPolicy(cfg.attacker_apf_baseline)
    obs, _ = env.reset(seed=123)
    steps = 0
    terminated = False
    truncated = False
    info = {}
    while not (terminated or truncated):
        action = policy.act(obs)
        obs, reward, terminated, truncated, info = env.step(action)
        assert np.isfinite(reward)
        steps += 1
        if steps > cfg.env.max_episode_steps + 2:
            raise AssertionError("apf episode did not terminate within expected horizon")
    env.close()
    return bool(info["termination_reason"] in {"goal_reached", "captured", "obstacle_collision", "out_of_bounds", "numerical_failure", "time_limit"}), steps


def main() -> None:
    ok0, steps0 = run_constant_episode(0)
    ok1, steps1 = run_constant_episode(1)
    okb, stepsb = run_baseline_episode()
    oka, stepsa = run_apf_episode()
    print({"zero_defenders": (ok0, steps0), "one_defenders": (ok1, steps1), "baseline_validation": (okb, stepsb), "apf_obstacle_only": (oka, stepsa)})


if __name__ == "__main__":
    main()
