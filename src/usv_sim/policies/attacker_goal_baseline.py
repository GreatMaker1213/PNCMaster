# last update: 2026-03-23 16:28:00
# modifier: Codex

from __future__ import annotations

from usv_sim.config import AttackerBaselineConfig, TrackingControllerConfig
from usv_sim.controllers.heading_speed import HeadingSpeedTrackingController
from usv_sim.guidance.goal_guidance import GoalGuidance
from usv_sim.policies.base import AttackerPolicy
from usv_sim.policies.controller_backed import ControllerBackedAttackerPolicy


_DEFAULT_TRACKING_CONTROLLER = TrackingControllerConfig(
    type="heading_speed",
    heading_gain=1.5,
    yaw_rate_damping=0.2,
    surge_gain=0.8,
    desired_speed_max=3.0,
)


class GoalSeekingAttackerPolicy(AttackerPolicy):
    def __init__(
        self,
        cfg: AttackerBaselineConfig,
        controller_cfg: TrackingControllerConfig | None = None,
    ) -> None:
        resolved_controller_cfg = controller_cfg or _DEFAULT_TRACKING_CONTROLLER
        guidance = GoalGuidance(cfg, desired_speed_max=resolved_controller_cfg.desired_speed_max)
        controller = HeadingSpeedTrackingController(resolved_controller_cfg)
        self._delegate = ControllerBackedAttackerPolicy(guidance, controller)

    def reset(self, *, seed: int | None = None) -> None:
        self._delegate.reset(seed=seed)

    def act(self, obs):
        return self._delegate.act(obs)
