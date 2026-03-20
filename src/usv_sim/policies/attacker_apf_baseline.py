# last update: 2026-03-20 11:28:00
# modifier: Codex

from __future__ import annotations

import math

import numpy as np

from usv_sim.config import AttackerAPFBaselineConfig
from usv_sim.core.math_utils import clip, world_to_ego
from usv_sim.policies.base import AttackerPolicy


class APFAttackerPolicy(AttackerPolicy):
    def __init__(self, cfg: AttackerAPFBaselineConfig) -> None:
        self._cfg = cfg

    def reset(self, *, seed: int | None = None) -> None:
        del seed

    def _repulsive_force(self, rel_x: float, rel_y: float, gain: float) -> np.ndarray:
        radius = self._cfg.influence_radius
        eps = self._cfg.potential_eps
        distance = max(float(math.hypot(rel_x, rel_y)), eps)
        if distance >= radius or gain <= 0.0:
            return np.zeros((2,), dtype=np.float64)
        scale = -gain * (1.0 / distance - 1.0 / radius) / (distance * distance)
        unit_x = rel_x / distance
        unit_y = rel_y / distance
        return np.array([scale * unit_x, scale * unit_y], dtype=np.float64)

    def _boundary_repulsive_force(self, boundary: np.ndarray, psi: float) -> np.ndarray:
        radius = self._cfg.influence_radius
        eps = self._cfg.potential_eps
        gain = self._cfg.boundary_repulsive_gain
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

    def act(self, obs: dict[str, np.ndarray]) -> np.ndarray:
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
        yaw_rate = float(ego[2])
        psi = float(math.atan2(float(ego[4]), float(ego[3])))

        force_total = np.array(
            [
                self._cfg.attractive_gain * goal_rel_x,
                self._cfg.attractive_gain * goal_rel_y,
            ],
            dtype=np.float64,
        )

        for index, mask_value in enumerate(obstacles_mask.tolist()):
            if float(mask_value) < 0.5:
                continue
            rel_x = float(obstacles[index, 0])
            rel_y = float(obstacles[index, 1])
            force_total += self._repulsive_force(rel_x, rel_y, self._cfg.obstacle_repulsive_gain)

        for index, mask_value in enumerate(defenders_mask.tolist()):
            if float(mask_value) < 0.5:
                continue
            rel_x = float(defenders[index, 0])
            rel_y = float(defenders[index, 1])
            force_total += self._repulsive_force(rel_x, rel_y, self._cfg.defender_repulsive_gain)

        force_total += self._boundary_repulsive_force(boundary, psi)
        force_norm = float(np.hypot(force_total[0], force_total[1]))
        if not np.isfinite(force_norm) or force_norm < self._cfg.potential_eps:
            force_total = np.array([goal_rel_x, goal_rel_y], dtype=np.float64)

        heading_error = float(math.atan2(force_total[1], force_total[0]))
        yaw_cmd = clip(self._cfg.heading_gain * heading_error / np.pi - self._cfg.yaw_rate_damping * yaw_rate, -1.0, 1.0)

        if distance <= goal_radius:
            surge_cmd = 0.0
        elif distance < self._cfg.slowdown_distance:
            surge_cmd = self._cfg.surge_near_goal
        elif abs(heading_error) < self._cfg.heading_large_threshold:
            surge_cmd = self._cfg.surge_nominal
        else:
            surge_cmd = self._cfg.surge_turning

        return np.array([surge_cmd, yaw_cmd], dtype=np.float32)

