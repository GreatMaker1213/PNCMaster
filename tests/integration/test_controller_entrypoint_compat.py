# last update: 2026-03-23 16:33:00
# modifier: Codex

from __future__ import annotations

from pathlib import Path

from usv_sim.benchmark.runner import run_single_episode
from usv_sim.config import load_config
from usv_sim.controllers.heading_speed import HeadingSpeedTrackingController
from usv_sim.envs.attack_defense_env import AttackDefenseEnv
from usv_sim.guidance.goal_guidance import GoalGuidance
from usv_sim.policies.controller_backed import ControllerBackedAttackerPolicy


ROOT = Path(__file__).resolve().parents[2]


def test_controller_backed_policy_rollout_works_with_existing_benchmark_chain() -> None:
    cfg = load_config(ROOT / "configs" / "v0_2_baseline_validation.yaml")
    guidance = GoalGuidance(cfg.attacker_goal_baseline, desired_speed_max=cfg.tracking_controller.desired_speed_max)
    controller = HeadingSpeedTrackingController(cfg.tracking_controller)
    controller_policy = ControllerBackedAttackerPolicy(guidance, controller)
    env = AttackDefenseEnv(cfg=cfg)
    try:
        episode = run_single_episode(
            controller_policy,
            env,
            seed=0,
            policy_name="controller_backed_goal",
            policy_type="goal_seeking",
            policy_config_name="attacker_goal_baseline",
        )
        assert episode["policy_type"] == "goal_seeking"
        assert episode["policy_config_name"] == "attacker_goal_baseline"
        assert episode["terminated"] or episode["truncated"]
    finally:
        env.close()
