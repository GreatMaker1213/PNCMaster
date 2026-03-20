# last update: 2026-03-20 11:52:00
# modifier: Codex

from __future__ import annotations

from typing import Any

import numpy as np

from usv_sim.benchmark.metrics import aggregate_episode_metrics
from usv_sim.benchmark.runner import run_single_episode
from usv_sim.policies.base import AttackerPolicy


class _DummyPolicy(AttackerPolicy):
    def __init__(self) -> None:
        self.reset_calls: list[int | None] = []

    def reset(self, *, seed: int | None = None) -> None:
        self.reset_calls.append(seed)

    def act(self, obs: dict[str, np.ndarray]) -> np.ndarray:
        del obs
        return np.array([0.0, 0.0], dtype=np.float32)


class _DummyEnv:
    def reset(self, *, seed: int | None = None):
        del seed
        obs = {"goal": np.array([1.0, 0.0, 1.0, 1.0], dtype=np.float32), "ego": np.zeros((6,), dtype=np.float32)}
        info = {"seed": 0, "scenario_id": "dummy"}
        return obs, info

    def step(self, action: np.ndarray):
        del action
        obs = {"goal": np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32), "ego": np.zeros((6,), dtype=np.float32)}
        info: dict[str, Any] = {
            "goal_distance": 0.0,
            "scenario_id": "dummy",
            "episode_summary": {
                "seed": 3,
                "scenario_id": "dummy",
                "episode_length": 1,
                "return": 10.0,
                "is_success": True,
                "termination_reason": "goal_reached",
                "min_goal_distance": 0.0,
                "min_defender_distance": float("inf"),
                "min_obstacle_clearance": float("inf"),
            },
        }
        return obs, 10.0, True, False, info


def test_run_single_episode_calls_policy_reset() -> None:
    env = _DummyEnv()
    policy = _DummyPolicy()
    result = run_single_episode(
        policy,
        env,  # type: ignore[arg-type]
        3,
        policy_name="dummy",
        policy_type="goal_seeking",
        policy_config_name="attacker_goal_baseline",
    )
    assert policy.reset_calls == [3]
    assert result["seed"] == 3
    assert result["termination_reason"] == "goal_reached"


def test_aggregate_metrics_computes_rates_and_moments() -> None:
    episodes = [
        {
            "policy_name": "goal_seeking",
            "policy_type": "goal_seeking",
            "policy_config_name": "attacker_goal_baseline",
            "scenario_id": "goal_only",
            "seed": 0,
            "termination_reason": "goal_reached",
            "is_success": True,
            "return": 10.0,
            "episode_length": 20,
            "min_goal_distance": 0.5,
            "min_obstacle_clearance": 9.0,
            "final_goal_distance": 0.0,
        },
        {
            "policy_name": "goal_seeking",
            "policy_type": "goal_seeking",
            "policy_config_name": "attacker_goal_baseline",
            "scenario_id": "goal_only",
            "seed": 1,
            "termination_reason": "time_limit",
            "is_success": False,
            "return": -5.0,
            "episode_length": 40,
            "min_goal_distance": 5.0,
            "min_obstacle_clearance": 7.0,
            "final_goal_distance": 8.0,
        },
    ]
    summary = aggregate_episode_metrics(episodes)
    assert summary["policy_config_name"] == "attacker_goal_baseline"
    assert summary["seed_set_summary"] == {"count": 2, "min": 0, "max": 1, "values": [0, 1]}
    assert summary["num_episodes"] == 2
    assert summary["success_rate"] == 0.5
    assert summary["goal_reached_rate"] == 0.5
    assert summary["time_limit_rate"] == 0.5
    assert summary["mean_return"] == 2.5
    assert summary["mean_episode_length"] == 30.0
    assert summary["mean_min_obstacle_clearance"] == 8.0
