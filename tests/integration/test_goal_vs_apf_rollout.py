# last update: 2026-03-20 11:54:00
# modifier: Codex

from __future__ import annotations

from pathlib import Path

from usv_sim.benchmark.runner import evaluate_from_config


ROOT = Path(__file__).resolve().parents[2]


def test_goal_and_apf_share_same_seed_set_on_obstacle_benchmark() -> None:
    config_path = ROOT / "configs" / "v0_3_obstacle_only.yaml"
    goal_episodes, goal_agg = evaluate_from_config(config_path, policy_type="goal_seeking")
    apf_episodes, apf_agg = evaluate_from_config(config_path, policy_type="apf")

    assert len(goal_episodes) == len(apf_episodes) == 5
    assert [ep["seed"] for ep in goal_episodes] == [ep["seed"] for ep in apf_episodes]
    assert goal_agg["num_episodes"] == apf_agg["num_episodes"] == 5
    assert goal_agg["scenario_id"] == "obstacle_only"
    assert apf_agg["scenario_id"] == "obstacle_only"


def test_apf_meets_t302_acceptance_on_obstacle_benchmark() -> None:
    config_path = ROOT / "configs" / "v0_3_obstacle_only.yaml"
    _, goal_agg = evaluate_from_config(config_path, policy_type="goal_seeking")
    _, apf_agg = evaluate_from_config(config_path, policy_type="apf")

    better_collision_rate = float(apf_agg["collision_rate"]) < float(goal_agg["collision_rate"])
    better_clearance = float(apf_agg["mean_min_obstacle_clearance"]) > float(goal_agg["mean_min_obstacle_clearance"])
    assert better_collision_rate or better_clearance
