# last update: 2026-03-19 09:35:00
# modifier: Claude Code

from __future__ import annotations

from usv_sim.core.geometry import obstacle_clearance, within_boundary
from usv_sim.core.types import CircularObstacle, RectBoundary, USVState


BOUNDARY = RectBoundary(xmin=0.0, xmax=10.0, ymin=0.0, ymax=10.0)


def _make_usv(x: float, y: float, radius: float = 1.0) -> USVState:
    return USVState(entity_id=0, x=x, y=y, psi=0.0, u=0.0, v=0.0, r=0.0, radius=radius)


def test_obstacle_clearance_handles_positive_zero_and_negative() -> None:
    obstacle = CircularObstacle(entity_id=1, x=5.0, y=5.0, radius=1.0)
    assert obstacle_clearance(_make_usv(2.0, 5.0), obstacle) > 0.0
    assert obstacle_clearance(_make_usv(3.0, 5.0), obstacle) == 0.0
    assert obstacle_clearance(_make_usv(3.5, 5.0), obstacle) < 0.0


def test_within_boundary_uses_circular_body_not_centroid() -> None:
    assert within_boundary(_make_usv(1.0, 5.0), BOUNDARY)
    assert not within_boundary(_make_usv(0.9, 5.0), BOUNDARY)
    assert not within_boundary(_make_usv(5.0, 9.2), BOUNDARY)
