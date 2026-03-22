# last update: 2026-03-21 20点03分
# modifier: KanviRen

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import yaml

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from usv_sim.benchmark.evaluator import evaluate_and_save


POLICY_CHOICES = ("goal_seeking", "apf", "heading_hold")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate selected attacker policy on benchmark config and save metrics.")
    parser.add_argument("--config", required=True, help="Path to config yaml")
    parser.add_argument("--policy", default=None, choices=POLICY_CHOICES, help="Policy override")
    parser.add_argument("--output-dir", required=True, help="Output directory path")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting existing non-empty output directory")
    return parser.parse_args(argv)


def _load_raw_config(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file)
    if not isinstance(raw, dict):
        raise ValueError("config file must contain a yaml mapping")
    return raw


def _ensure_benchmark_seeds(raw: dict[str, Any]) -> list[int]:
    benchmark = raw.get("benchmark")
    if not isinstance(benchmark, dict):
        raise ValueError("config must include benchmark section with benchmark.seeds")
    seeds = benchmark.get("seeds")
    if not isinstance(seeds, list) or len(seeds) == 0:
        raise ValueError("benchmark.seeds must be a non-empty list")
    normalized: list[int] = []
    for index, seed in enumerate(seeds):
        try:
            normalized.append(int(seed))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"benchmark.seeds[{index}] is not a valid integer") from exc
    return normalized


def _prepare_output_dir(path: Path, *, overwrite: bool) -> Path:
    if path.exists() and path.is_file():
        raise ValueError(f"output path points to a file: {path}")
    if path.exists():
        has_content = any(path.iterdir())
        if has_content and not overwrite:
            raise ValueError(f"output directory is not empty: {path}. Use --overwrite to replace it.")
        if has_content and overwrite:
            shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _try_get_git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "-c", f"safe.directory={ROOT}", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    commit = result.stdout.strip()
    return commit or None


def _save_run_meta(
    *,
    output_dir: Path,
    config_path: Path,
    policy_type: str | None,
    aggregate: dict[str, Any],
    command: Sequence[str],
) -> None:
    resolved_policy = policy_type or str(aggregate.get("policy_type", "unknown"))
    run_meta = {
        "config_path": str(config_path.resolve()),
        "policy_type": resolved_policy,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "command": " ".join(command),
        "git_commit": _try_get_git_commit(),
    }
    with (output_dir / "run_meta.json").open("w", encoding="utf-8") as file:
        json.dump(run_meta, file, ensure_ascii=False, indent=2)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)
    output_dir = Path(args.output_dir)
    try:
        raw = _load_raw_config(config_path)
        _ensure_benchmark_seeds(raw)
        prepared_output_dir = _prepare_output_dir(output_dir, overwrite=bool(args.overwrite))
        episodes, aggregate = evaluate_and_save(
            config_path=config_path,
            output_dir=prepared_output_dir,
            policy_type=args.policy,
        )
        _save_run_meta(
            output_dir=prepared_output_dir,
            config_path=config_path,
            policy_type=args.policy,
            aggregate=aggregate,
            command=sys.argv if argv is None else ["evaluate.py", *argv],
        )
        print(
            {
                "episodes": len(episodes),
                "aggregate": aggregate,
                "output_dir": str(prepared_output_dir),
            }
        )
    except Exception as exc:
        print(f"[evaluate.py] error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

