# last update: 2026-03-27 10:40:00
# modifier: Codex

from __future__ import annotations

import math

import numpy as np

from usv_sim.config import AttackerAPFBaselineConfig
from usv_sim.core.math_utils import world_to_ego
from usv_sim.guidance.base import GuidancePolicy, resolve_desired_surge_speed, resolve_desired_yaw_rate
from usv_sim.guidance.reference import DesiredVelocityReference

class APFGuidance(GuidancePolicy):
    def __init__(
        self,
        cfg: AttackerAPFBaselineConfig,
        *,
        desired_surge_speed_max: float,
        desired_yaw_rate_max: float,
    ) -> None:
        self._cfg = cfg
        self._desired_surge_speed_max = float(desired_surge_speed_max)
        self._desired_yaw_rate_max = float(desired_yaw_rate_max)

    def _repulsive_force(self, rel_x: float, rel_y: float, clearance: float, gain: float) -> np.ndarray:
        radius = float(self._cfg.influence_radius)
        eps = float(self._cfg.potential_eps)
        distance = max(float(clearance), eps)
        if distance >= radius or gain <= 0.0:
            return np.zeros((2,), dtype=np.float64)
        scale = -gain * (1.0 / distance - 1.0 / radius) / (distance * distance)
        center_distance = max(float(math.hypot(rel_x, rel_y)), eps)
        unit_x = rel_x / center_distance
        unit_y = rel_y / center_distance

        return np.array([scale * unit_x, scale * unit_y], dtype=np.float64)

    def _boundary_repulsive_force(self, boundary: np.ndarray, psi: float) -> np.ndarray:
        radius = float(self._cfg.influence_radius)
        eps = float(self._cfg.potential_eps)
        gain = float(self._cfg.boundary_repulsive_gain)
        if gain <= 0.0:
            return np.zeros((2,), dtype=np.float64)

        dist_left, dist_right, dist_bottom, dist_top = [float(v) for v in boundary]
        world_fx = 0.0
        world_fy = 0.0

        if dist_left < radius:
            d = max(dist_left, eps)
            world_fx += gain * (1.0 / d - 1.0 / radius) / (d * d)
        if dist_right < radius:
            d = max(dist_right, eps)
            world_fx -= gain * (1.0 / d - 1.0 / radius) / (d * d)
        if dist_bottom < radius:
            d = max(dist_bottom, eps)
            world_fy += gain * (1.0 / d - 1.0 / radius) / (d * d)
        if dist_top < radius:
            d = max(dist_top, eps)
            world_fy -= gain * (1.0 / d - 1.0 / radius) / (d * d)

        ego_fx, ego_fy = world_to_ego(world_fx, world_fy, psi)
        return np.array([ego_fx, ego_fy], dtype=np.float64)

    def plan(self, obs: dict[str, np.ndarray]) -> DesiredVelocityReference:
        goal = np.asarray(obs["goal"], dtype=np.float64)
        ego = np.asarray(obs["ego"], dtype=np.float64)
        boundary = np.asarray(obs["boundary"], dtype=np.float64)
        obstacles = np.asarray(obs["obstacles"], dtype=np.float64)
        obstacles_mask = np.asarray(obs["obstacles_mask"], dtype=np.float64)
        defenders = np.asarray(obs["defenders"], dtype=np.float64)
        defenders_mask = np.asarray(obs["defenders_mask"], dtype=np.float64)

        if goal.shape != (4,):
            raise ValueError("obs['goal'] must have shape (4,)")
        if ego.shape != (6,):
            raise ValueError("obs['ego'] must have shape (6,)")

        goal_rel_x = float(goal[0])
        goal_rel_y = float(goal[1])
        distance = float(goal[2])
        goal_radius = float(goal[3])
        psi = float(math.atan2(float(ego[4]), float(ego[3])))

        force_total = np.array([goal_rel_x,goal_rel_y,], dtype=np.float64)
        force_total=force_total*min(distance,1.0)/distance
        print("="*60)
        for index, mask_value in enumerate(obstacles_mask.tolist()):
            if float(mask_value) < 0.5:
                continue
            print("find a obstacle")
            force_total += self._repulsive_force(
                float(obstacles[index, 0]),
                float(obstacles[index, 1]),
                float(obstacles[index, 2]),
                float(self._cfg.obstacle_repulsive_gain),
            )
        
        for index, mask_value in enumerate(defenders_mask.tolist()):
            if float(mask_value) < 0.5:
                continue
            print("find a defender")
            force_total += self._repulsive_force(
                float(defenders[index, 0]),
                float(defenders[index, 1]),
                float(defenders[index, 4]),
                float(self._cfg.defender_repulsive_gain),
            )
        force_total += self._boundary_repulsive_force(boundary, psi)
        print(f"total force:{force_total}")
        force_norm = float(np.hypot(force_total[0], force_total[1]))
        if not np.isfinite(force_norm) or force_norm < float(self._cfg.potential_eps):
            force_total = np.array([goal_rel_x, goal_rel_y], dtype=np.float64)

        heading_error = float(math.atan2(force_total[1], force_total[0]))
        desired_speed = resolve_desired_surge_speed(
            distance=distance,
            goal_radius=goal_radius,
            heading_error=heading_error,
            desired_speed_max=self._desired_surge_speed_max,
            surge_nominal=float(self._cfg.surge_nominal),
            surge_turning=float(self._cfg.surge_turning),
            surge_near_goal=float(self._cfg.surge_near_goal),
            heading_large_threshold=float(self._cfg.heading_large_threshold),
            slowdown_distance=float(self._cfg.slowdown_distance),
        )
        desired_yaw_rate = resolve_desired_yaw_rate(
            heading_error=heading_error,
            heading_gain=float(self._cfg.heading_gain),
            desired_yaw_rate_max=self._desired_yaw_rate_max,
        )
        return DesiredVelocityReference(
            desired_surge_speed=desired_speed,
            desired_yaw_rate=desired_yaw_rate,
        )
