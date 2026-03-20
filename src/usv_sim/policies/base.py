# last update: 2026-03-20 11:23:00
# modifier: Codex

from __future__ import annotations

import numpy as np

from usv_sim.core.types import USVState, WorldState


class DefenderPolicy:
    def act(self, defender: USVState, world: WorldState):
        raise NotImplementedError


class AttackerPolicy:
    def reset(self, *, seed: int | None = None) -> None:
        del seed

    def act(self, obs: dict[str, np.ndarray]) -> np.ndarray:
        raise NotImplementedError
