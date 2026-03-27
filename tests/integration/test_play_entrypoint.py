# last update: 2026-03-25 11:00:00
# modifier: Codex

from __future__ import annotations

from pathlib import Path

import play
from usv_sim.envs.attack_defense_env import AttackDefenseEnv
from usv_sim.envs.attack_defense_kinematic_env import AttackDefenseKinematicEnv


ROOT = Path(__file__).resolve().parents[2]


def test_play_entrypoint_runs_single_episode(monkeypatch) -> None:
    monkeypatch.setattr(AttackDefenseEnv, "render", lambda self: None)
    monkeypatch.setattr(play.plt, "ioff", lambda: None)
    monkeypatch.setattr(play.plt, "show", lambda *args, **kwargs: None)

    rc = play.main(
        [
            "--config",
            str(ROOT / "configs" / "v0_2_baseline_validation.yaml"),
            "--policy",
            "goal_seeking",
            "--seed",
            "0",
        ]
    )
    assert rc == 0


def test_play_entrypoint_runs_single_kinematic_episode(monkeypatch) -> None:
    monkeypatch.setattr(AttackDefenseKinematicEnv, "render", lambda self: None)
    monkeypatch.setattr(play.plt, "ioff", lambda: None)
    monkeypatch.setattr(play.plt, "show", lambda *args, **kwargs: None)

    rc = play.main(
        [
            "--config",
            str(ROOT / "configs" / "v0_5_1_goal_only_kinematic.yaml"),
            "--policy",
            "goal_seeking",
            "--seed",
            "0",
        ]
    )
    assert rc == 0
