# last update: 2026-03-27 10:42:00
# modifier: Codex

from __future__ import annotations

from usv_sim.config import ObservationConfig
from usv_sim.core.types import CircularObstacle, GoalRegion, RectBoundary, USVState, WorldState
from usv_sim.observation.visibility import VisibilityFilter


def _make_world() -> WorldState:
    attacker = USVState(entity_id=0, x=0.0, y=0.0, psi=0.0, u=0.0, v=0.0, r=0.0, radius=1.0)
    defenders = (
        USVState(entity_id=1, x=6.0, y=0.0, psi=0.0, u=0.0, v=0.0, r=0.0, radius=2.0),
        USVState(entity_id=2, x=8.0, y=0.0, psi=0.0, u=0.0, v=0.0, r=0.0, radius=1.0),
    )
    obstacles = (
        CircularObstacle(entity_id=101, x=6.0, y=0.0, radius=2.0),
        CircularObstacle(entity_id=102, x=9.0, y=0.0, radius=1.0),
    )
    return WorldState(
        sim_time=0.0,
        step_count=0,
        seed=0,
        scenario_id="test",
        attacker=attacker,
        defenders=defenders,
        obstacles=obstacles,
        goal=GoalRegion(x=20.0, y=0.0, radius=3.0),
        boundary=RectBoundary(xmin=-10.0, xmax=30.0, ymin=-10.0, ymax=10.0),
    )


def test_visibility_filter_respects_sensing_radius() -> None:
    visibility = VisibilityFilter(ObservationConfig(sensing_radius=5.0, max_defenders=4, max_obstacles=4, dtype="float32"))
    visible = visibility.select(_make_world())
    assert tuple(item.entity_id for item in visible.defenders) == (1,)
    assert tuple(item.entity_id for item in visible.obstacles) == (101,)
