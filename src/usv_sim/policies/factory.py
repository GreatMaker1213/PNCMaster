# last update: 2026-03-23 16:28:00
# modifier: Codex

from __future__ import annotations

from usv_sim.config import ProjectConfig
from usv_sim.policies.attacker_apf_baseline import APFAttackerPolicy
from usv_sim.policies.attacker_goal_baseline import GoalSeekingAttackerPolicy
from usv_sim.policies.attacker_heading_baseline import HeadingHoldAttackerPolicy
from usv_sim.policies.base import AttackerPolicy


def create_attacker_policy(cfg: ProjectConfig, policy_type: str | None = None) -> AttackerPolicy:
    selected = policy_type or cfg.attacker_policy.type
    if selected == "goal_seeking":
        return GoalSeekingAttackerPolicy(cfg.attacker_goal_baseline, cfg.tracking_controller)
    if selected == "apf":
        return APFAttackerPolicy(cfg.attacker_apf_baseline, cfg.tracking_controller)
    if selected == "heading_hold":
        return HeadingHoldAttackerPolicy(cfg.attacker_heading_baseline, cfg.tracking_controller)
    raise ValueError(f"unsupported attacker policy type: {selected}")
