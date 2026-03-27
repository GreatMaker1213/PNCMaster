# last update: 2026-03-25 10:36:00
# modifier: Codex

from __future__ import annotations

from usv_sim.config import ProjectConfig
from usv_sim.guidance.apf_guidance import APFGuidance
from usv_sim.guidance.goal_guidance import GoalGuidance
from usv_sim.policies.attacker_apf_baseline import APFAttackerPolicy
from usv_sim.policies.attacker_goal_baseline import GoalSeekingAttackerPolicy
from usv_sim.policies.attacker_heading_baseline import HeadingHoldAttackerPolicy, HeadingHoldVelocityGuidance
from usv_sim.policies.base import AttackerPolicy
from usv_sim.policies.controller_backed import ReferenceBackedAttackerPolicy


def create_attacker_policy(cfg: ProjectConfig, policy_type: str | None = None) -> AttackerPolicy:
    selected = policy_type or cfg.attacker_policy.type
    if cfg.env.backend == "dynamic":
        if selected == "goal_seeking":
            return GoalSeekingAttackerPolicy(cfg.attacker_goal_baseline, cfg.velocity_tracking_controller)
        if selected == "apf":
            return APFAttackerPolicy(cfg.attacker_apf_baseline, cfg.velocity_tracking_controller)
        if selected == "heading_hold":
            return HeadingHoldAttackerPolicy(cfg.attacker_heading_baseline, cfg.tracking_controller)
        raise ValueError(f"unsupported attacker policy type: {selected}")

    if cfg.env.backend == "kinematic":
        if selected == "goal_seeking":
            return ReferenceBackedAttackerPolicy(
                GoalGuidance(
                    cfg.attacker_goal_baseline,
                    desired_surge_speed_max=cfg.velocity_tracking_controller.desired_surge_speed_max,
                    desired_yaw_rate_max=cfg.velocity_tracking_controller.desired_yaw_rate_max,
                )
            )
        if selected == "apf":
            return ReferenceBackedAttackerPolicy(
                APFGuidance(
                    cfg.attacker_apf_baseline,
                    desired_surge_speed_max=cfg.velocity_tracking_controller.desired_surge_speed_max,
                    desired_yaw_rate_max=cfg.velocity_tracking_controller.desired_yaw_rate_max,
                )
            )
        if selected == "heading_hold":
            return ReferenceBackedAttackerPolicy(
                HeadingHoldVelocityGuidance(
                    cfg.attacker_heading_baseline,
                    desired_surge_speed_max=cfg.velocity_tracking_controller.desired_surge_speed_max,
                    desired_yaw_rate_max=cfg.velocity_tracking_controller.desired_yaw_rate_max,
                )
            )
        raise ValueError(f"unsupported attacker policy type: {selected}")

    raise ValueError(f"unsupported env backend: {cfg.env.backend}")
