# last update: 2026-03-20 11:36:00
# modifier: Codex

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TYPE_CHECKING

import yaml

from usv_sim.benchmark.metrics import aggregate_episode_metrics
from usv_sim.config import ProjectConfig, load_config
from usv_sim.policies.base import AttackerPolicy
from usv_sim.policies.factory import create_attacker_policy

if TYPE_CHECKING:
    from usv_sim.envs.attack_defense_env import AttackDefenseEnv


@dataclass(frozen=True)
class BenchmarkConfig:
    name: str
    seeds: tuple[int, ...]
    max_episodes: int


def load_benchmark_config(path: str | Path) -> BenchmarkConfig:
    with Path(path).open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file)
    benchmark_raw = raw.get("benchmark", {})
    name = str(benchmark_raw.get("name", raw["scenario"]["scenario_id"]))
    seeds_raw = benchmark_raw.get("seeds", [0, 1, 2, 3, 4])
    seeds = tuple(int(seed) for seed in seeds_raw)
    max_episodes = int(benchmark_raw.get("max_episodes", len(seeds)))
    if max_episodes <= 0:
        raise ValueError("benchmark.max_episodes must be >= 1")
    if len(seeds) == 0:
        raise ValueError("benchmark.seeds must not be empty")
    return BenchmarkConfig(name=name, seeds=seeds, max_episodes=max_episodes)


def _resolve_policy_config_name(policy_type: str) -> str:
    if policy_type == "goal_seeking":
        return "attacker_goal_baseline"
    if policy_type == "apf":
        return "attacker_apf_baseline"
    if policy_type == "heading_hold":
        return "attacker_heading_baseline"
    return "unknown_policy_config"


def run_single_episode(
    policy: AttackerPolicy,
    env,
    seed: int,
    *,
    policy_name: str,
    policy_type: str,
    policy_config_name: str,
) -> dict[str, Any]:
    policy.reset(seed=seed)
    obs, _ = env.reset(seed=seed)

    terminated = False
    truncated = False
    info: dict[str, Any] = {}
    while not (terminated or truncated):
        action = policy.act(obs)
        obs, _, terminated, truncated, info = env.step(action)

    episode_summary = info.get("episode_summary")
    if episode_summary is None:
        episode_summary = {
            "seed": seed,
            "scenario_id": info["scenario_id"],
            "episode_length": info["step_count"],
            "return": float(info["reward_total"]),
            "is_success": bool(info["is_success"]),
            "termination_reason": info["termination_reason"],
            "min_goal_distance": float(info["goal_distance"]),
            "min_defender_distance": float(info["min_defender_distance"]),
            "min_obstacle_clearance": float(info["min_obstacle_clearance"]),
        }

    return {
        "policy_name": policy_name,
        "policy_type": policy_type,
        "policy_config_name": policy_config_name,
        "scenario_id": str(episode_summary["scenario_id"]),
        "seed": int(episode_summary["seed"]),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "termination_reason": str(episode_summary["termination_reason"]),
        "is_success": bool(episode_summary["is_success"]),
        "episode_length": int(episode_summary["episode_length"]),
        "return": float(episode_summary["return"]),
        "min_goal_distance": float(episode_summary["min_goal_distance"]),
        "min_defender_distance": float(episode_summary["min_defender_distance"]),
        "min_obstacle_clearance": float(episode_summary["min_obstacle_clearance"]),
        "final_goal_distance": float(info["goal_distance"]),
    }


def evaluate_policy(
    policy: AttackerPolicy,
    env,
    seeds: tuple[int, ...],
    *,
    max_episodes: int | None = None,
    policy_name: str = "attacker_policy",
    policy_type: str = "unknown",
    policy_config_name: str = "unknown",
) -> list[dict[str, Any]]:
    if max_episodes is None:
        max_episodes = len(seeds)
    selected_seeds = list(seeds[: max_episodes])
    results = []
    for seed in selected_seeds:
        results.append(
            run_single_episode(
                policy,
                env,
                int(seed),
                policy_name=policy_name,
                policy_type=policy_type,
                policy_config_name=policy_config_name,
            )
        )
    return results


def evaluate_from_config(config_path: str | Path, policy_type: str | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cfg: ProjectConfig = load_config(config_path)
    benchmark_cfg = load_benchmark_config(config_path)
    resolved_policy_type = policy_type or cfg.attacker_policy.type
    policy = create_attacker_policy(cfg, resolved_policy_type)
    from usv_sim.envs.attack_defense_env import AttackDefenseEnv

    env = AttackDefenseEnv(cfg=cfg)
    try:
        policy_config_name = _resolve_policy_config_name(resolved_policy_type)
        episodes = evaluate_policy(
            policy,
            env,
            benchmark_cfg.seeds,
            max_episodes=benchmark_cfg.max_episodes,
            policy_name=resolved_policy_type,
            policy_type=resolved_policy_type,
            policy_config_name=policy_config_name,
        )
    finally:
        env.close()
    aggregate = aggregate_episode_metrics(episodes)
    return episodes, aggregate


def main() -> None:
    parser = argparse.ArgumentParser(description="Run USV benchmark with a selected attacker policy.")
    parser.add_argument("--config", required=True, help="Path to benchmark config yaml")
    parser.add_argument("--policy", default=None, help="Policy type override: goal_seeking | apf | heading_hold")
    args = parser.parse_args()

    episodes, aggregate = evaluate_from_config(args.config, args.policy)
    print({"episodes": len(episodes), "aggregate": aggregate})


if __name__ == "__main__":
    main()
