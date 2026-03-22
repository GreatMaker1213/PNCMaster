# last update: 2026-03-21 20点03分
# modifier: KanviRen


from __future__ import annotations

import pytest

import play


def test_play_parse_args_defaults() -> None:
    args = play.parse_args(["--config", "configs/v0_3_goal_only.yaml"])
    assert args.config == "configs/v0_3_goal_only.yaml"
    assert args.policy is None
    assert args.seed == 0
    assert args.render_mode == "human"


def test_play_parse_args_rejects_non_human_render_mode() -> None:
    with pytest.raises(SystemExit):
        play.parse_args(["--config", "configs/v0_3_goal_only.yaml", "--render-mode", "none"])

