# last update: 2026-03-23 15:22:00
# modifier: Codex

import numpy as np
from types import SimpleNamespace

from usv_sim.guidance.goal_guidance import GoalGuidance
from usv_sim.guidance.reference import HeadingSpeedReference


def _build_obs(y_offset: float) -> dict[str, np.ndarray]:
    distance = np.hypot(10.0, y_offset)
    return {
        "goal": np.array([10.0, y_offset, distance, 3.0], dtype=np.float32),
        "ego": np.array([0.0, 0.0, 0.0, 1.0, 0.0, 0.0], dtype=np.float32),
    }


def test_goal_guidance_plan_aligns_with_goal_direction() -> None:
    cfg = SimpleNamespace(
        heading_gain=1.5,
        yaw_rate_damping=0.2,
        surge_nominal=0.8,
        surge_turning=0.3,
        surge_near_goal=0.2,
        heading_large_threshold=0.7854,
        slowdown_distance=8.0,
    )
    guidance = GoalGuidance(cfg)
    reference = guidance.plan(_build_obs(y_offset=5.0))
    assert isinstance(reference, HeadingSpeedReference)
    assert reference.desired_heading_error > 0.0
    assert reference.desired_surge_speed <= cfg.surge_nominal
