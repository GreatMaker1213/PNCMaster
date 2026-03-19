# last update: 2026-03-19 09:36:00
# modifier: Claude Code

from __future__ import annotations

from pathlib import Path

import numpy as np

from usv_sim.config import load_config
from usv_sim.core.events import StepEvents
from usv_sim.core.types import GoalRegion, RectBoundary, USVState, WorldState
from usv_sim.reward.attack_defense_reward import AttackDefenseReward


ROOT = Path(__file__).resolve().parents[2]
CFG = load_config(ROOT / "configs" / "v0_2_default.yaml")
REWARD = AttackDefenseReward(CFG.reward)


def _make_world(x: float) -> WorldState:
    attacker = USVState(entity_id=0, x=x, y=0.0, psi=0.0, u=0.0, v=0.0, r=0.0, radius=1.0)
    return WorldState(
        sim_time=0.0,
        step_count=0,
        seed=0,
        scenario_id="test",
        attacker=attacker,
        defenders=tuple(),
        obstacles=tuple(),
        goal=GoalRegion(x=10.0, y=0.0, radius=3.0),
        boundary=RectBoundary(xmin=-10.0, xmax=20.0, ymin=-10.0, ymax=10.0),
    )


def test_reward_progress_time_and_control_terms_match_formula() -> None:
    prev_world = _make_world(0.0)
    next_world = _make_world(1.0)
    events = StepEvents(
        goal_reached=False,
        captured=False,
        obstacle_collision=False,
        out_of_bounds=False,
        numerical_failure=False,
        min_defender_distance=float("inf"),
        min_obstacle_clearance=float("inf"),
        goal_distance=9.0,
    )
    action = np.array([0.5, -0.5], dtype=np.float32)
    breakdown = REWARD.compute(prev_world, next_world, events, action, "not_terminated")
    assert breakdown.progress == 1.0
    assert breakdown.time == CFG.reward.time_penalty
    assert breakdown.control == CFG.reward.control_l2_weight * 0.5
    assert breakdown.goal == 0.0
    assert breakdown.total == breakdown.progress + breakdown.time + breakdown.control


def test_terminal_reward_does_not_stack() -> None:
    prev_world = _make_world(8.0)
    next_world = _make_world(10.0)
    events = StepEvents(
        goal_reached=True,
        captured=True,
        obstacle_collision=False,
        out_of_bounds=False,
        numerical_failure=False,
        min_defender_distance=0.0,
        min_obstacle_clearance=float("inf"),
        goal_distance=0.0,
    )
    breakdown = REWARD.compute(prev_world, next_world, events, np.array([0.0, 0.0], dtype=np.float32), "goal_reached")
    assert breakdown.goal == CFG.reward.goal_reward
    assert breakdown.capture == 0.0
    assert breakdown.collision == 0.0
    assert breakdown.boundary == 0.0
    assert breakdown.numerical_failure == 0.0
