# last update: 2026-03-25 10:36:00
# modifier: Codex

from __future__ import annotations

import numpy as np

from usv_sim.controllers.base import TrackingController
from usv_sim.guidance.base import GuidancePolicy
from usv_sim.guidance.reference import DesiredVelocityReference
from usv_sim.policies.base import AttackerPolicy


class ControllerBackedAttackerPolicy(AttackerPolicy):
    def __init__(self, guidance: GuidancePolicy, controller: TrackingController) -> None:
        self._guidance = guidance
        self._controller = controller

    def reset(self, *, seed: int | None = None) -> None:
        self._guidance.reset(seed=seed)
        self._controller.reset(seed=seed)

    def act(self, obs: dict[str, np.ndarray]) -> np.ndarray:
        reference = self._guidance.plan(obs)
        return self._controller.act(obs, reference)


class ReferenceBackedAttackerPolicy(AttackerPolicy):
    def __init__(self, guidance: GuidancePolicy) -> None:
        self._guidance = guidance

    def reset(self, *, seed: int | None = None) -> None:
        self._guidance.reset(seed=seed)

    def act(self, obs: dict[str, np.ndarray]) -> np.ndarray:
        reference = self._guidance.plan(obs)
        if not isinstance(reference, DesiredVelocityReference):
            raise TypeError("ReferenceBackedAttackerPolicy requires DesiredVelocityReference output")
        return np.array([reference.desired_surge_speed, reference.desired_yaw_rate], dtype=np.float32)
