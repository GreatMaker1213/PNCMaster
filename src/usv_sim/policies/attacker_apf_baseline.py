# last update: 2026-03-25 11:05:00
# modifier: Codex

from __future__ import annotations

from usv_sim.config import AttackerAPFBaselineConfig, VelocityTrackingControllerConfig
from usv_sim.controllers.velocity_tracking import VelocityTrackingController
from usv_sim.guidance.apf_guidance import APFGuidance
from usv_sim.policies.base import AttackerPolicy
from usv_sim.policies.controller_backed import ControllerBackedAttackerPolicy


_DEFAULT_VELOCITY_TRACKING_CONTROLLER = VelocityTrackingControllerConfig(
    type="sideslip_compensated_velocity",
    surge_gain=0.8,
    yaw_rate_gain=1.6,
    yaw_rate_damping=0.25,
    sideslip_gain=0.4,
    desired_surge_speed_max=3.0,
    desired_yaw_rate_max=1.2,
)


class APFAttackerPolicy(AttackerPolicy):
    def __init__(
        self,
        cfg: AttackerAPFBaselineConfig,
        controller_cfg: VelocityTrackingControllerConfig | None = None,
    ) -> None:
        resolved_cfg = controller_cfg or _DEFAULT_VELOCITY_TRACKING_CONTROLLER
        guidance = APFGuidance(
            cfg,
            desired_surge_speed_max=resolved_cfg.desired_surge_speed_max,
            desired_yaw_rate_max=resolved_cfg.desired_yaw_rate_max,
            
        )
        controller = VelocityTrackingController(resolved_cfg)
        self._delegate = ControllerBackedAttackerPolicy(guidance, controller)

    def reset(self, *, seed: int | None = None) -> None:
        self._delegate.reset(seed=seed)

    def act(self, obs):
        return self._delegate.act(obs)
