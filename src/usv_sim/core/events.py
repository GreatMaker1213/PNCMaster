# last update: 2026-03-18 22:09:12
# modifier: Claude Code

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StepEvents:
    goal_reached: bool
    captured: bool
    obstacle_collision: bool
    out_of_bounds: bool
    numerical_failure: bool
    min_defender_distance: float
    min_obstacle_clearance: float
    goal_distance: float
