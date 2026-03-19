# last update: 2026-03-18 22:09:12
# modifier: Claude Code

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class USVState:
    entity_id: int
    x: float
    y: float
    psi: float
    u: float
    v: float
    r: float
    radius: float


@dataclass(frozen=True)
class CircularObstacle:
    entity_id: int
    x: float
    y: float
    radius: float


@dataclass(frozen=True)
class GoalRegion:
    x: float
    y: float
    radius: float


@dataclass(frozen=True)
class RectBoundary:
    xmin: float
    xmax: float
    ymin: float
    ymax: float


@dataclass(frozen=True)
class WorldState:
    sim_time: float
    step_count: int
    seed: int
    scenario_id: str
    attacker: USVState
    defenders: tuple[USVState, ...]
    obstacles: tuple[CircularObstacle, ...]
    goal: GoalRegion
    boundary: RectBoundary
