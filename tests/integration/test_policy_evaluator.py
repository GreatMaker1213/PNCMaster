# last update: 2026-03-20 11:54:00
# modifier: Codex

from __future__ import annotations

import json
from pathlib import Path
import shutil
import uuid

from usv_sim.benchmark.evaluator import evaluate_and_save


ROOT = Path(__file__).resolve().parents[2]
OUTPUTS_ROOT = ROOT / "outputs"


def test_policy_evaluator_saves_jsonl_json_and_csv() -> None:
    config_path = ROOT / "configs" / "v0_3_goal_only.yaml"
    OUTPUTS_ROOT.mkdir(parents=True, exist_ok=True)
    output_dir = OUTPUTS_ROOT / f"test_policy_eval_{uuid.uuid4().hex[:10]}"
    try:
        episodes, aggregate = evaluate_and_save(config_path, output_dir, policy_type="heading_hold")
        assert len(episodes) == 5
        assert aggregate["num_episodes"] == 5
        assert aggregate["policy_config_name"] == "attacker_heading_baseline"
        assert aggregate["seed_set_summary"] == {"count": 5, "min": 0, "max": 4, "values": [0, 1, 2, 3, 4]}

        episode_jsonl = output_dir / "episodes.jsonl"
        aggregate_json = output_dir / "aggregate.json"
        episode_csv = output_dir / "episodes.csv"
        assert episode_jsonl.exists()
        assert aggregate_json.exists()
        assert episode_csv.exists()

        lines = episode_jsonl.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 5
        first = json.loads(lines[0])
        assert "policy_name" in first
        assert "scenario_id" in first
    finally:
        if output_dir.exists():
            shutil.rmtree(output_dir)
