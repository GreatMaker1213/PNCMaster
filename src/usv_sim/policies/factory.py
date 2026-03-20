# last update: 2026-03-20 11:30:00
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
        return GoalSeekingAttackerPolicy(cfg.attacker_goal_baseline)
    if selected == "apf":
        return APFAttackerPolicy(cfg.attacker_apf_baseline)
    if selected == "heading_hold":
        return HeadingHoldAttackerPolicy(cfg.attacker_heading_baseline)
    raise ValueError(f"unsupported attacker policy type: {selected}")

