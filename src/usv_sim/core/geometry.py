# last update: 2026-03-18 21:56:31
# modifier: Claude Code

from __future__ import annotations

from usv_sim.core.math_utils import distance2d
from usv_sim.core.types import CircularObstacle, RectBoundary, USVState


def obstacle_clearance(usv: USVState, obstacle: CircularObstacle) -> float:
    return distance2d(usv.x, usv.y, obstacle.x, obstacle.y) - usv.radius - obstacle.radius


def within_boundary(usv: USVState, boundary: RectBoundary) -> bool:
    return (
        usv.x - usv.radius >= boundary.xmin
        and usv.x + usv.radius <= boundary.xmax
        and usv.y - usv.radius >= boundary.ymin
        and usv.y + usv.radius <= boundary.ymax
    )
