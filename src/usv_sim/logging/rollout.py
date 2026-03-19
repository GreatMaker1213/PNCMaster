# last update: 2026-03-18 21:56:31
# modifier: Claude Code

from __future__ import annotations

from usv_sim.core.types import WorldState


class RolloutRecorder:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._steps = []
        self._summary = None
        self._return = 0.0
        self._min_goal_distance = float("inf")
        self._min_defender_distance = float("inf")
        self._min_obstacle_clearance = float("inf")
        self._seed = None
        self._scenario_id = None

    def start_episode(self, world: WorldState, obs: dict, info: dict) -> None:
        self._seed = world.seed
        self._scenario_id = world.scenario_id
        self._min_goal_distance = min(self._min_goal_distance, float(info["goal_distance"]))
        self._min_defender_distance = min(self._min_defender_distance, float(info["min_defender_distance"]))
        self._min_obstacle_clearance = min(self._min_obstacle_clearance, float(info["min_obstacle_clearance"]))
        self._steps.append({"world": world, "obs": obs, "info": info, "action": None})

    def record_step(self, world: WorldState, obs: dict, action, info: dict) -> None:
        self._return += float(info["reward_total"])
        self._min_goal_distance = min(self._min_goal_distance, float(info["goal_distance"]))
        self._min_defender_distance = min(self._min_defender_distance, float(info["min_defender_distance"]))
        self._min_obstacle_clearance = min(self._min_obstacle_clearance, float(info["min_obstacle_clearance"]))
        self._steps.append({"world": world, "obs": obs, "info": info, "action": action})

    def finalize_episode(self) -> dict:
        last_info = self._steps[-1]["info"] if self._steps else {}
        self._summary = {
            "seed": self._seed,
            "scenario_id": self._scenario_id,
            "episode_length": max(len(self._steps) - 1, 0),
            "return": self._return,
            "is_success": bool(last_info.get("is_success", False)),
            "termination_reason": last_info.get("termination_reason", "not_terminated"),
            "min_goal_distance": self._min_goal_distance,
            "min_defender_distance": self._min_defender_distance,
            "min_obstacle_clearance": self._min_obstacle_clearance,
        }
        return self._summary
