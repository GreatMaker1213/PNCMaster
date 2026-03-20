# last update: 2026-03-20 11:33:00
# modifier: Codex

from __future__ import annotations

from statistics import mean, pstdev
from typing import Any


def _safe_mean(values: list[float]) -> float:
    return float(mean(values)) if values else 0.0


def _safe_std(values: list[float]) -> float:
    return float(pstdev(values)) if len(values) > 1 else 0.0


def aggregate_episode_metrics(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    if not episodes:
        return {
            "policy_name": "unknown",
            "policy_type": "unknown",
            "policy_config_name": "unknown",
            "scenario_id": "unknown",
            "seed_set_summary": {"count": 0, "min": None, "max": None, "values": []},
            "num_episodes": 0,
            "success_rate": 0.0,
            "goal_reached_rate": 0.0,
            "collision_rate": 0.0,
            "capture_rate": 0.0,
            "out_of_bounds_rate": 0.0,
            "time_limit_rate": 0.0,
            "mean_return": 0.0,
            "std_return": 0.0,
            "mean_episode_length": 0.0,
            "std_episode_length": 0.0,
            "mean_min_goal_distance": 0.0,
            "mean_min_obstacle_clearance": 0.0,
            "mean_final_goal_distance": 0.0,
        }

    num_episodes = len(episodes)
    seed_values = [int(ep["seed"]) for ep in episodes]
    unique_seeds = sorted(set(seed_values))
    min_seed = unique_seeds[0] if unique_seeds else None
    max_seed = unique_seeds[-1] if unique_seeds else None
    returns = [float(ep["return"]) for ep in episodes]
    lengths = [float(ep["episode_length"]) for ep in episodes]
    min_goal_distances = [float(ep["min_goal_distance"]) for ep in episodes]
    min_obstacle_clearances = [float(ep["min_obstacle_clearance"]) for ep in episodes]
    final_goal_distances = [float(ep["final_goal_distance"]) for ep in episodes]
    reasons = [str(ep["termination_reason"]) for ep in episodes]

    def _rate(reason: str) -> float:
        return float(sum(1 for item in reasons if item == reason) / num_episodes)

    return {
        "policy_name": episodes[0].get("policy_name", "unknown"),
        "policy_type": episodes[0].get("policy_type", "unknown"),
        "policy_config_name": episodes[0].get("policy_config_name", "unknown"),
        "scenario_id": episodes[0].get("scenario_id", "unknown"),
        "seed_set_summary": {
            "count": len(unique_seeds),
            "min": min_seed,
            "max": max_seed,
            "values": unique_seeds,
        },
        "num_episodes": num_episodes,
        "success_rate": float(sum(1 for ep in episodes if bool(ep.get("is_success", False))) / num_episodes),
        "goal_reached_rate": _rate("goal_reached"),
        "collision_rate": _rate("obstacle_collision"),
        "capture_rate": _rate("captured"),
        "out_of_bounds_rate": _rate("out_of_bounds"),
        "time_limit_rate": _rate("time_limit"),
        "mean_return": _safe_mean(returns),
        "std_return": _safe_std(returns),
        "mean_episode_length": _safe_mean(lengths),
        "std_episode_length": _safe_std(lengths),
        "mean_min_goal_distance": _safe_mean(min_goal_distances),
        "mean_min_obstacle_clearance": _safe_mean(min_obstacle_clearances),
        "mean_final_goal_distance": _safe_mean(final_goal_distances),
    }
