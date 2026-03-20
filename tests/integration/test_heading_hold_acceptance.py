# last update: 2026-03-20
# modifier: Codex

from __future__ import annotations

from pathlib import Path

from usv_sim.benchmark.runner import evaluate_from_config


ROOT = Path(__file__).resolve().parents[2]


def _assert_heading_hold_goal_reached(config_name: str, expected_scenario: str) -> None:
    config_path = ROOT / "configs" / config_name
    episodes, aggregate = evaluate_from_config(config_path, policy_type="heading_hold")

    assert len(episodes) == 5
    assert [ep["seed"] for ep in episodes] == [0, 1, 2, 3, 4]
    assert aggregate["scenario_id"] == expected_scenario
    assert aggregate["goal_reached_rate"] == 1.0
    assert aggregate["success_rate"] == 1.0


def test_heading_hold_meets_t303_on_baseline_validation() -> None:
    _assert_heading_hold_goal_reached("v0_2_baseline_validation.yaml", "baseline_validation")


def test_heading_hold_meets_t303_on_b301_goal_only() -> None:
    _assert_heading_hold_goal_reached("v0_3_goal_only.yaml", "goal_only")
