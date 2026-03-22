# last update: 2026-03-21 20点03分
# modifier: KanviRen


from __future__ import annotations

import evaluate


def test_evaluate_parse_args_defaults() -> None:
    args = evaluate.parse_args(["--config", "configs/v0_3_goal_only.yaml", "--output-dir", "outputs/test_eval"])
    assert args.config == "configs/v0_3_goal_only.yaml"
    assert args.output_dir == "outputs/test_eval"
    assert args.policy is None
    assert args.overwrite is False


def test_evaluate_parse_args_overwrite_flag() -> None:
    args = evaluate.parse_args(
        ["--config", "configs/v0_3_goal_only.yaml", "--output-dir", "outputs/test_eval", "--overwrite"]
    )
    assert args.overwrite is True

