# last update: 2026-03-18 22:09:12
# modifier: Claude Code

from __future__ import annotations

from dataclasses import dataclass

from usv_sim.config import ProjectConfig
from usv_sim.core.events import StepEvents
from usv_sim.core.types import WorldState


_TERMINATION_PRIORITY = (
    "numerical_failure",
    "obstacle_collision",
    "out_of_bounds",
    "captured",
    "goal_reached",
)


@dataclass(frozen=True)
class TerminationResult:
    terminated: bool
    truncated: bool
    reason: str
    is_success: bool


class TerminationChecker:
    def __init__(self, cfg: ProjectConfig) -> None:
        self._cfg = cfg

    def check(self, world: WorldState, events: StepEvents) -> TerminationResult:
        flags = {
            "numerical_failure": events.numerical_failure,
            "obstacle_collision": events.obstacle_collision,
            "out_of_bounds": events.out_of_bounds,
            "captured": events.captured,
            "goal_reached": events.goal_reached,
        }
        for reason in _TERMINATION_PRIORITY:
            if flags[reason]:
                return TerminationResult(
                    terminated=True,
                    truncated=False,
                    reason=reason,
                    is_success=(reason == "goal_reached"),
                )

        if world.step_count >= self._cfg.env.max_episode_steps:
            return TerminationResult(
                terminated=False,
                truncated=True,
                reason="time_limit",
                is_success=False,
            )

        return TerminationResult(
            terminated=False,
            truncated=False,
            reason="not_terminated",
            is_success=False,
        )
