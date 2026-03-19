# last update: 2026-03-19 09:31:00
# modifier: Claude Code

from __future__ import annotations

import numpy as np

from usv_sim.core.types import USVState, WorldState


class DefenderPolicy:
    def act(self, defender: USVState, world: WorldState):
        raise NotImplementedError


class AttackerPolicy:
    def act(self, obs: dict[str, np.ndarray]) -> np.ndarray:
        raise NotImplementedError
