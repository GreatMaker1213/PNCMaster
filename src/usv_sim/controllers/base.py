# last update: 2026-03-23 16:26:00
# modifier: Codex

from __future__ import annotations

import numpy as np

from usv_sim.guidance.reference import HeadingSpeedReference


class TrackingController:
    def reset(self, *, seed: int | None = None) -> None:
        del seed

    def act(self, obs: dict[str, np.ndarray], reference: HeadingSpeedReference) -> np.ndarray:
        del obs
        del reference
        raise NotImplementedError
