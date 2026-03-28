# last update: 2026-03-27 10:42:00
# modifier: Codex

from __future__ import annotations

import numpy as np

from usv_sim.config import ObservationConfig
from usv_sim.core.types import CircularObstacle, GoalRegion, RectBoundary, USVState, WorldState
from usv_sim.observation.builder import ObservationBuilder


def _make_world() -> WorldState:
    attacker = USVState(entity_id=0, x=0.0, y=0.0, psi=0.0, u=0.2, v=0.0, r=0.1, radius=1.0)
    defenders = (
        USVState(entity_id=20, x=3.0, y=0.0, psi=0.0, u=0.0, v=0.0, r=0.0, radius=1.0),
        USVState(entity_id=10, x=9.0, y=0.0, psi=0.0, u=0.0, v=0.0, r=0.0, radius=1.0),
    )
    obstacles = (
        CircularObstacle(entity_id=200, x=4.0, y=0.0, radius=2.0),
        CircularObstacle(entity_id=100, x=8.0, y=0.0, radius=1.5),
    )
    return WorldState(
        sim_time=0.0,
        step_count=0,
        seed=0,
        scenario_id="test",
        attacker=attacker,
        defenders=defenders,
        obstacles=obstacles,
        goal=GoalRegion(x=100.0, y=0.0, radius=3.0),
        boundary=RectBoundary(xmin=-10.0, xmax=120.0, ymin=-10.0, ymax=10.0),
    )


def test_observation_builder_matches_schema_and_keeps_goal_visible() -> None:
    builder = ObservationBuilder(ObservationConfig(sensing_radius=5.0, max_defenders=3, max_obstacles=3, dtype="float32"))
    obs = builder.build(_make_world())

    assert set(obs.keys()) == {"ego", "goal", "boundary", "defenders", "defenders_mask", "obstacles", "obstacles_mask"}
    assert obs["ego"].shape == (6,)
    assert obs["goal"].shape == (4,)
    assert obs["boundary"].shape == (4,)
    assert obs["defenders"].shape == (3, 7)
    assert obs["defenders_mask"].shape == (3,)
    assert obs["obstacles"].shape == (3, 4)
    assert obs["obstacles_mask"].shape == (3,)
    assert all(value.dtype == np.float32 for value in obs.values())

    np.testing.assert_allclose(obs["goal"], np.array([100.0, 0.0, 100.0, 3.0], dtype=np.float32))
    np.testing.assert_allclose(obs["defenders"][0], np.zeros((7,), dtype=np.float32))
    assert obs["defenders_mask"].tolist() == [0.0, 1.0, 0.0]
    assert float(obs["defenders"][1, 4]) == 1.0
    np.testing.assert_allclose(obs["obstacles"][0], np.zeros((4,), dtype=np.float32))
    assert obs["obstacles_mask"].tolist() == [0.0, 1.0, 0.0]
    assert float(obs["obstacles"][1, 2]) == 1.0
