# last update: 2026-03-21 20点03分
# modifier: KanviRen


from __future__ import annotations

import json
from pathlib import Path
import shutil
import uuid

import evaluate
import yaml


ROOT = Path(__file__).resolve().parents[2]
OUTPUTS_ROOT = ROOT / "outputs"


def _new_workspace_output_dir(prefix: str) -> Path:
    OUTPUTS_ROOT.mkdir(parents=True, exist_ok=True)
    return OUTPUTS_ROOT / f"{prefix}_{uuid.uuid4().hex[:10]}"


def test_evaluate_entrypoint_writes_expected_outputs() -> None:
    output_dir = _new_workspace_output_dir("test_eval_entry")
    try:
        rc = evaluate.main(
            [
                "--config",
                str(ROOT / "configs" / "v0_3_goal_only.yaml"),
                "--policy",
                "heading_hold",
                "--output-dir",
                str(output_dir),
            ]
        )
        assert rc == 0
        assert (output_dir / "episodes.jsonl").exists()
        assert (output_dir / "episodes.csv").exists()
        assert (output_dir / "aggregate.json").exists()
        assert (output_dir / "run_meta.json").exists()

        run_meta = json.loads((output_dir / "run_meta.json").read_text(encoding="utf-8"))
        assert "config_path" in run_meta
        assert "policy_type" in run_meta
        assert "timestamp_utc" in run_meta
        assert "git_commit" in run_meta
    finally:
        if output_dir.exists():
            shutil.rmtree(output_dir)


def test_evaluate_rejects_non_empty_output_without_overwrite() -> None:
    output_dir = _new_workspace_output_dir("test_eval_no_overwrite")
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        (output_dir / "existing.txt").write_text("keep", encoding="utf-8")
        rc = evaluate.main(
            [
                "--config",
                str(ROOT / "configs" / "v0_3_goal_only.yaml"),
                "--output-dir",
                str(output_dir),
            ]
        )
        assert rc == 1
    finally:
        if output_dir.exists():
            shutil.rmtree(output_dir)


def test_evaluate_overwrite_allows_replacing_existing_output() -> None:
    output_dir = _new_workspace_output_dir("test_eval_overwrite")
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        (output_dir / "existing.txt").write_text("stale", encoding="utf-8")
        rc = evaluate.main(
            [
                "--config",
                str(ROOT / "configs" / "v0_3_goal_only.yaml"),
                "--output-dir",
                str(output_dir),
                "--overwrite",
            ]
        )
        assert rc == 0
        assert not (output_dir / "existing.txt").exists()
        assert (output_dir / "aggregate.json").exists()
    finally:
        if output_dir.exists():
            shutil.rmtree(output_dir)


def test_evaluate_requires_benchmark_seeds() -> None:
    src_cfg = yaml.safe_load((ROOT / "configs" / "v0_3_goal_only.yaml").read_text(encoding="utf-8"))
    src_cfg["benchmark"].pop("seeds", None)
    cfg_dir = _new_workspace_output_dir("test_eval_cfg")
    output_dir = _new_workspace_output_dir("test_eval_no_seeds")
    cfg_path = cfg_dir / "invalid_no_seeds.yaml"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(yaml.safe_dump(src_cfg, allow_unicode=True), encoding="utf-8")
    try:
        rc = evaluate.main(
            [
                "--config",
                str(cfg_path),
                "--output-dir",
                str(output_dir),
            ]
        )
        assert rc == 1
    finally:
        if cfg_dir.exists():
            shutil.rmtree(cfg_dir)
        if output_dir.exists():
            shutil.rmtree(output_dir)
