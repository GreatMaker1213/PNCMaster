# last update: 2026-03-25 10:55:00
# modifier: Codex

import numpy as np

from usv_sim.config import VelocityTrackingControllerConfig
from usv_sim.controllers.velocity_tracking import VelocityTrackingController
from usv_sim.guidance.reference import DesiredVelocityReference


def _build_obs() -> dict[str, np.ndarray]:
    return {
        "ego": np.array([1.0, 0.3, 0.1, 0.99, 0.1, 1.04], dtype=np.float32),
        "goal": np.array([10.0, 0.0, 10.0, 3.0], dtype=np.float32),
        "boundary": np.array([20.0, 20.0, 20.0, 20.0], dtype=np.float32),
        "defenders": np.zeros((4, 7), dtype=np.float32),
        "defenders_mask": np.zeros((4,), dtype=np.float32),
        "obstacles": np.zeros((8, 4), dtype=np.float32),
        "obstacles_mask": np.zeros((8,), dtype=np.float32),
    }


def test_velocity_tracking_controller_clips_and_tracks_reference() -> None:
    cfg = VelocityTrackingControllerConfig(
        type="sideslip_compensated_velocity",
        surge_gain=0.8,
        yaw_rate_gain=1.6,
        yaw_rate_damping=0.25,
        sideslip_gain=0.4,
        desired_surge_speed_max=3.0,
        desired_yaw_rate_max=1.2,
    )
    controller = VelocityTrackingController(cfg)
    obs = _build_obs()
    reference = DesiredVelocityReference(desired_surge_speed=2.0, desired_yaw_rate=0.6)
    action = controller.act(obs, reference)
    assert action.shape == (2,)
    assert action.dtype == np.float32
    assert -1.0 <= float(action[0]) <= 1.0
    assert -1.0 <= float(action[1]) <= 1.0
    assert float(action[1]) > 0.0
