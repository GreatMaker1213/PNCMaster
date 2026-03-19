# last update: 2026-03-18 21:27:07
# modifier: Claude Code

from __future__ import annotations

from usv_sim.core.types import USVState, WorldState


class DefenderPolicy:
    def act(self, defender: USVState, world: WorldState):
        raise NotImplementedError
