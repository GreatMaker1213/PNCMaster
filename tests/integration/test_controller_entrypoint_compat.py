# last update: 2026-03-25 10:55:00
# modifier: Codex

from __future__ import annotations

from pathlib import Path

from usv_sim.benchmark.runner import run_single_episode
from usv_sim.config import load_config
from usv_sim.envs.factory import create_env
from usv_sim.policies.factory import create_attacker_policy


ROOT = Path(__file__).resolve().parents[2]


def _run(config_name: str) -> dict:
    cfg = load_config(ROOT / "configs" / config_name)
    policy = create_attacker_policy(cfg, policy_type="goal_seeking")
    env = create_env(cfg)
    try:
        return run_single_episode(
            policy,
            env,
            seed=0,
            policy_name="goal_seeking",
            policy_type="goal_seeking",
            policy_config_name="attacker_goal_baseline",
        )
    finally:
        env.close()


def test_controller_entrypoint_compat_dynamic() -> None:
    episode = _run("v0_5_1_goal_only_dynamic.yaml")
    assert episode["env_backend"] == "dynamic"
    assert episode["terminated"] or episode["truncated"]


def test_controller_entrypoint_compat_kinematic() -> None:
    episode = _run("v0_5_1_goal_only_kinematic.yaml")
    assert episode["env_backend"] == "kinematic"
    assert episode["terminated"] or episode["truncated"]
