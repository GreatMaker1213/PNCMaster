# last update: 2026-03-25 10:20:00
# modifier: Codex

from __future__ import annotations

import numpy as np


class TrackingController:
    def reset(self, *, seed: int | None = None) -> None:
        del seed

    def act(self, obs: dict[str, np.ndarray], reference) -> np.ndarray:
        del obs
        del reference
        raise NotImplementedError
