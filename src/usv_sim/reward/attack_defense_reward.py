# last update: 2026-03-18 22:09:12
# modifier: Claude Code

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from usv_sim.config import RewardConfig
from usv_sim.core.events import StepEvents
from usv_sim.core.math_utils import distance2d
from usv_sim.core.types import WorldState


@dataclass(frozen=True)
class RewardBreakdown:
    total: float
    progress: float
    goal: float
    capture: float
    collision: float
    boundary: float
    numerical_failure: float
    time: float
    control: float


class AttackDefenseReward:
    def __init__(self, cfg: RewardConfig) -> None:
        self._cfg = cfg

    def compute(
        self,
        prev_world: WorldState,
        world: WorldState,
        events: StepEvents,
        attacker_action: np.ndarray,
        termination_reason: str,
    ) -> RewardBreakdown:
        d_prev = distance2d(prev_world.attacker.x, prev_world.attacker.y, prev_world.goal.x, prev_world.goal.y)
        d_curr = events.goal_distance
        progress = self._cfg.progress_weight * (d_prev - d_curr)
        time = self._cfg.time_penalty

        action = np.asarray(attacker_action, dtype=np.float64).reshape(-1)
        clipped = np.clip(action, -1.0, 1.0)
        control = float(self._cfg.control_l2_weight * float(np.sum(clipped * clipped)))

        goal = self._cfg.goal_reward if termination_reason == "goal_reached" else 0.0
        capture = self._cfg.capture_penalty if termination_reason == "captured" else 0.0
        collision = self._cfg.collision_penalty if termination_reason == "obstacle_collision" else 0.0
        boundary = self._cfg.boundary_penalty if termination_reason == "out_of_bounds" else 0.0
        numerical_failure = self._cfg.numerical_failure_penalty if termination_reason == "numerical_failure" else 0.0

        total = progress + time + control + goal + capture + collision + boundary + numerical_failure
        return RewardBreakdown(
            total=float(total),
            progress=float(progress),
            goal=float(goal),
            capture=float(capture),
            collision=float(collision),
            boundary=float(boundary),
            numerical_failure=float(numerical_failure),
            time=float(time),
            control=float(control),
        )
