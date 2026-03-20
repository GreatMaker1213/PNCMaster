# last update: 2026-03-20 11:38:00
# modifier: Codex

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from usv_sim.benchmark.runner import evaluate_from_config


def save_episode_jsonl(path: str | Path, episodes: list[dict[str, Any]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        for row in episodes:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def save_aggregate_json(path: str | Path, aggregate: dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(aggregate, file, ensure_ascii=False, indent=2)


def save_episode_csv(path: str | Path, episodes: list[dict[str, Any]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not episodes:
        with output_path.open("w", encoding="utf-8") as file:
            file.write("")
        return
    fieldnames = list(episodes[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in episodes:
            writer.writerow(row)


def evaluate_and_save(
    config_path: str | Path,
    output_dir: str | Path,
    policy_type: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    episodes, aggregate = evaluate_from_config(config_path, policy_type)
    output_root = Path(output_dir)
    save_episode_jsonl(output_root / "episodes.jsonl", episodes)
    save_aggregate_json(output_root / "aggregate.json", aggregate)
    save_episode_csv(output_root / "episodes.csv", episodes)
    return episodes, aggregate

