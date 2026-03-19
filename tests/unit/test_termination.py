# last update: 2026-03-19 09:36:00
# modifier: Claude Code

from __future__ import annotations

from pathlib import Path

from usv_sim.config import load_config
from usv_sim.core.events import StepEvents
from usv_sim.core.types import GoalRegion, RectBoundary, USVState, WorldState
from usv_sim.termination.checker import TerminationChecker


ROOT = Path(__file__).resolve().parents[2]
CFG = load_config(ROOT / "configs" / "v0_2_default.yaml")
CHECKER = TerminationChecker(CFG)


WORLD = WorldState(
    sim_time=0.0,
    step_count=10,
    seed=0,
    scenario_id="test",
    attacker=USVState(entity_id=0, x=0.0, y=0.0, psi=0.0, u=0.0, v=0.0, r=0.0, radius=1.0),
    defenders=tuple(),
    obstacles=tuple(),
    goal=GoalRegion(x=5.0, y=0.0, radius=3.0),
    boundary=RectBoundary(xmin=-10.0, xmax=10.0, ymin=-10.0, ymax=10.0),
)


def _events(**overrides) -> StepEvents:
    base = dict(
        goal_reached=False,
        captured=False,
        obstacle_collision=False,
        out_of_bounds=False,
        numerical_failure=False,
        min_defender_distance=float("inf"),
        min_obstacle_clearance=float("inf"),
        goal_distance=5.0,
    )
    base.update(overrides)
    return StepEvents(**base)


def test_termination_priority_prefers_numerical_failure() -> None:
    result = CHECKER.check(WORLD, _events(goal_reached=True, captured=True, numerical_failure=True))
    assert result.reason == "numerical_failure"
    assert result.terminated is True
    assert result.truncated is False


def test_time_limit_only_applies_without_real_terminal() -> None:
    world = WorldState(**{**WORLD.__dict__, "step_count": CFG.env.max_episode_steps})
    result = CHECKER.check(world, _events())
    assert result.reason == "time_limit"
    assert result.terminated is False
    assert result.truncated is True


def test_numerical_failure_reason_is_preserved() -> None:
    result = CHECKER.check(WORLD, _events(numerical_failure=True))
    assert result.reason == "numerical_failure"
    assert result.terminated != result.truncated
