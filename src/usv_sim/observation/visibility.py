# last update: 2026-03-21 20点46分
# modifier: KanviRen

from __future__ import annotations

from dataclasses import dataclass

from usv_sim.config import ObservationConfig
from usv_sim.core.math_utils import distance2d
from usv_sim.core.types import CircularObstacle, USVState, WorldState


@dataclass(frozen=True)
class VisibleEntities:
    defenders: tuple[USVState, ...]
    obstacles: tuple[CircularObstacle, ...]


class VisibilityFilter:
    def __init__(self, cfg: ObservationConfig) -> None:
        self._cfg = cfg
    
    # return defenders obstancles in the attacker's sense radius
    def select(self, world: WorldState) -> VisibleEntities:
        px = world.attacker.x
        py = world.attacker.y
        defenders = tuple(
            defender
            for defender in world.defenders
            if distance2d(px, py, defender.x, defender.y) <= self._cfg.sensing_radius
        )
        obstacles = tuple(
            obstacle
            for obstacle in world.obstacles
            if distance2d(px, py, obstacle.x, obstacle.y) <= self._cfg.sensing_radius
        )
        return VisibleEntities(defenders=defenders, obstacles=obstacles)
