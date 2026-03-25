# last update: 2026-03-23 15:24:00
# modifier: Codex

import numpy as np
from types import SimpleNamespace

from usv_sim.guidance.apf_guidance import APFGuidance
from usv_sim.guidance.reference import HeadingSpeedReference


def _base_obs(rel_y: float) -> dict[str, np.ndarray]:
    distance = np.hypot(10.0, rel_y)
    return {
        "goal": np.array([10.0, rel_y, distance, 3.0], dtype=np.float32),
        "ego": np.array([0.0, 0.0, 0.0, 1.0, 0.0, 0.0], dtype=np.float32),
        "boundary": np.array([20.0, 20.0, 20.0, 20.0], dtype=np.float32),
        "obstacles": np.zeros((8, 4), dtype=np.float32),
        "obstacles_mask": np.zeros((8,), dtype=np.float32),
        "defenders": np.zeros((4, 7), dtype=np.float32),
        "defenders_mask": np.zeros((4,), dtype=np.float32),
    }


def test_apf_guidance_builds_reference_steering_around_obstacle() -> None:
    cfg = SimpleNamespace(
        attractive_gain=1.0,
        obstacle_repulsive_gain=5.0,
        defender_repulsive_gain=0.0,
        boundary_repulsive_gain=0.0,
        influence_radius=10.0,
        potential_eps=0.1,
        surge_nominal=0.7,
        surge_turning=0.25,
        surge_near_goal=0.2,
        heading_gain=1.5,
        yaw_rate_damping=0.2,
        heading_large_threshold=0.7854,
        slowdown_distance=8.0,
    )
    guidance = APFGuidance(cfg)
    obs = _base_obs(rel_y=0.0)
    obs["obstacles_mask"][0] = 1.0
    obs["obstacles"][0] = np.array([5.0, 2.0, 5.385, 1.0], dtype=np.float32)
    reference = guidance.plan(obs)
    assert isinstance(reference, HeadingSpeedReference)
    assert abs(reference.desired_heading_error) > 0.0
    assert 0.0 <= reference.desired_surge_speed <= cfg.surge_nominal
