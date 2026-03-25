# last update: 2026-03-23 15:21:00
# modifier: Codex

import numpy as np

from usv_sim.controllers.heading_speed import HeadingSpeedTrackingController
from usv_sim.guidance.reference import HeadingSpeedReference


def _build_obs() -> dict[str, np.ndarray]:
    return {
        "ego": np.array([1.0, 0.0, 0.1, 0.99, 0.1, 1.0], dtype=np.float32),
        "goal": np.array([10.0, 0.0, 10.0, 3.0], dtype=np.float32),
        "boundary": np.array([20.0, 20.0, 20.0, 20.0], dtype=np.float32),
        "defenders": np.zeros((4, 7), dtype=np.float32),
        "defenders_mask": np.zeros((4,), dtype=np.float32),
        "obstacles": np.zeros((8, 4), dtype=np.float32),
        "obstacles_mask": np.zeros((8,), dtype=np.float32),
    }


def test_heading_speed_controller_clips_and_tracks_reference() -> None:
    controller = HeadingSpeedTrackingController(heading_gain=2.0, yaw_rate_damping=0.5, surge_gain=1.2)
    obs = _build_obs()
    reference = HeadingSpeedReference(desired_heading_error=0.8, desired_surge_speed=2.0)
    action = controller.act(obs, reference)
    assert action.shape == (2,)
    assert action.dtype == np.float32
    assert -1.0 <= float(action[0]) <= 1.0
    assert -1.0 <= float(action[1]) <= 1.0
    assert float(action[1]) > 0.0
