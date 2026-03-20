# last update: 2026-03-20 11:53:00
# modifier: Codex

from __future__ import annotations

from pathlib import Path

from usv_sim.benchmark.runner import evaluate_from_config


ROOT = Path(__file__).resolve().parents[2]


def test_benchmark_runner_evaluates_all_configured_seeds() -> None:
    config_path = ROOT / "configs" / "v0_3_goal_only.yaml"
    episodes, aggregate = evaluate_from_config(config_path, policy_type="goal_seeking")
    assert len(episodes) == 5
    assert aggregate["num_episodes"] == 5
    assert set(ep["seed"] for ep in episodes) == {0, 1, 2, 3, 4}
    assert aggregate["scenario_id"] == "goal_only"

