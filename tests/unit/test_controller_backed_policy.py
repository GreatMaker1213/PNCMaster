# last update: 2026-03-23 15:26:00
# modifier: Codex

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from usv_sim.policies.controller_backed import ControllerBackedAttackerPolicy
from usv_sim.guidance.reference import HeadingSpeedReference


class _StubGuidance:
    def __init__(self) -> None:
        self.reset_calls = 0

    def reset(self, *, seed: int | None = None) -> None:
        self.reset_calls += 1

    def plan(self, obs: dict[str, np.ndarray]) -> HeadingSpeedReference:
        return HeadingSpeedReference(desired_heading_error=0.2, desired_surge_speed=0.5)


@dataclass
class _StubController:
    last_reference: HeadingSpeedReference | None = None

    def reset(self, *, seed: int | None = None) -> None:
        pass

    def act(self, obs: dict[str, np.ndarray], reference: HeadingSpeedReference) -> np.ndarray:
        self.last_reference = reference
        return np.array([reference.desired_surge_speed, reference.desired_heading_error], dtype=np.float32)


def test_controller_backed_policy_composes_guidance_and_controller() -> None:
    guidance = _StubGuidance()
    controller = _StubController()
    policy = ControllerBackedAttackerPolicy(guidance, controller)
    policy.reset(seed=42)
    dummy_obs = {
        "ego": np.zeros(6, dtype=np.float32),
        "goal": np.zeros(4, dtype=np.float32),
        "boundary": np.zeros(4, dtype=np.float32),
        "defenders": np.zeros((4, 7), dtype=np.float32),
        "defenders_mask": np.zeros(4, dtype=np.float32),
        "obstacles": np.zeros((8, 4), dtype=np.float32),
        "obstacles_mask": np.zeros(8, dtype=np.float32),
    }
    action = policy.act(dummy_obs)
    assert guidance.reset_calls == 1
    assert controller.last_reference is not None
    assert action.shape == (2,)
    assert float(action[0]) == controller.last_reference.desired_surge_speed
