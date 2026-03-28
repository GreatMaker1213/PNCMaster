# last update: 2026-03-27 10:40:00
# modifier: Codex

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

    def _defender_clearance(self, attacker: USVState, defender: USVState) -> float:
        return distance2d(attacker.x, attacker.y, defender.x, defender.y) - attacker.radius - defender.radius

    # return defenders obstancles in the attacker's sense radius
    def select(self, world: WorldState) -> VisibleEntities:
        attacker = world.attacker
        defenders = tuple(
            defender
            for defender in world.defenders
            if self._defender_clearance(attacker, defender) <= self._cfg.sensing_radius
        )
        obstacles = tuple(
            obstacle
            for obstacle in world.obstacles
            if distance2d(attacker.x, attacker.y, obstacle.x, obstacle.y) - attacker.radius - obstacle.radius <= self._cfg.sensing_radius
        )
        return VisibleEntities(defenders=defenders, obstacles=obstacles)
