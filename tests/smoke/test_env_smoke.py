# last update: 2026-03-18 21:56:31
# modifier: Claude Code

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np

from usv_sim.config import load_config
from usv_sim.envs.attack_defense_env import AttackDefenseEnv


def run_episode(n_defenders: int) -> tuple[bool, int]:
    cfg = load_config(ROOT / "configs" / "v0_1_default.yaml")
    cfg = type(cfg)(
        env=cfg.env,
        action=cfg.action,
        dynamics=cfg.dynamics,
        scenario=type(cfg.scenario)(
            scenario_id=cfg.scenario.scenario_id,
            boundary=cfg.scenario.boundary,
            attacker_radius=cfg.scenario.attacker_radius,
            defender_radius=cfg.scenario.defender_radius,
            goal_radius=cfg.scenario.goal_radius,
            capture_radius=cfg.scenario.capture_radius,
            n_defenders=n_defenders,
            n_obstacles=cfg.scenario.n_obstacles,
            obstacle_radius_min=cfg.scenario.obstacle_radius_min,
            obstacle_radius_max=cfg.scenario.obstacle_radius_max,
            spawn_clearance=cfg.scenario.spawn_clearance,
            goal_clearance=cfg.scenario.goal_clearance,
        ),
        observation=cfg.observation,
        reward=cfg.reward,
        defender_policy=cfg.defender_policy,
    )
    env = AttackDefenseEnv(cfg=cfg)
    obs, info = env.reset(seed=123)
    assert obs["ego"].shape == (6,)
    assert obs["goal"].shape == (4,)
    steps = 0
    terminated = False
    truncated = False
    while not (terminated or truncated):
        action = np.array([0.5, 0.0], dtype=np.float32)
        obs, reward, terminated, truncated, info = env.step(action)
        assert np.isfinite(reward)
        steps += 1
        if steps > cfg.env.max_episode_steps + 2:
            raise AssertionError("episode did not terminate within expected horizon")
    return bool(info["termination_reason"] in {"goal_reached", "captured", "obstacle_collision", "out_of_bounds", "numerical_failure", "time_limit"}), steps


def main() -> None:
    ok0, steps0 = run_episode(0)
    ok1, steps1 = run_episode(1)
    print({"zero_defenders": (ok0, steps0), "one_defender": (ok1, steps1)})


if __name__ == "__main__":
    main()
