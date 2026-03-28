# last update: 2026-03-27 10:40:00
# modifier: Codex

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from usv_sim.config import ObservationConfig
from usv_sim.core.geometry import obstacle_clearance
from usv_sim.core.math_utils import body_velocity_to_world, distance2d, world_to_ego
from usv_sim.core.types import WorldState
from usv_sim.observation.visibility import VisibilityFilter


@dataclass(frozen=True)
class SimpleBoxSpace:
    low: float
    high: float
    shape: tuple[int, ...]
    dtype: type


@dataclass(frozen=True)
class SimpleDictSpace:
    spaces: dict


class ObservationBuilder:
    def __init__(self, cfg: ObservationConfig) -> None:
        self._cfg = cfg
        self._visibility = VisibilityFilter(cfg)
        self._observation_space = SimpleDictSpace(
            spaces={
                "ego": SimpleBoxSpace(-np.inf, np.inf, (6,), np.float32),
                "goal": SimpleBoxSpace(-np.inf, np.inf, (4,), np.float32),
                "boundary": SimpleBoxSpace(-np.inf, np.inf, (4,), np.float32),
                "defenders": SimpleBoxSpace(-np.inf, np.inf, (cfg.max_defenders, 7), np.float32),
                "defenders_mask": SimpleBoxSpace(0.0, 1.0, (cfg.max_defenders,), np.float32),
                "obstacles": SimpleBoxSpace(-np.inf, np.inf, (cfg.max_obstacles, 4), np.float32),
                "obstacles_mask": SimpleBoxSpace(0.0, 1.0, (cfg.max_obstacles,), np.float32),
            }
        )

    @property
    def observation_space(self):
        return self._observation_space

    def build(self, world: WorldState) -> dict[str, np.ndarray]:
        visible = self._visibility.select(world)
        attacker = world.attacker

        speed_norm = np.sqrt(attacker.u * attacker.u + attacker.v * attacker.v)
        ego = np.array(
            [
                attacker.u,
                attacker.v,
                attacker.r,
                np.cos(attacker.psi),
                np.sin(attacker.psi),
                speed_norm,
            ],
            dtype=np.float32,
        )

        goal_dx = world.goal.x - attacker.x
        goal_dy = world.goal.y - attacker.y
        goal_rel_x, goal_rel_y = world_to_ego(goal_dx, goal_dy, attacker.psi)
        goal_distance = distance2d(attacker.x, attacker.y, world.goal.x, world.goal.y)
        goal = np.array([goal_rel_x, goal_rel_y, goal_distance, world.goal.radius], dtype=np.float32)

        boundary = np.array(
            [
                attacker.x - world.boundary.xmin,
                world.boundary.xmax - attacker.x,
                attacker.y - world.boundary.ymin,
                world.boundary.ymax - attacker.y,
            ],
            dtype=np.float32,
        )

        defender_rows = np.zeros((self._cfg.max_defenders, 7), dtype=np.float32)
        defender_mask = np.zeros((self._cfg.max_defenders,), dtype=np.float32)
        visible_defenders = {d.entity_id: d for d in visible.defenders} # build visible defenders dict:key=entity_id value=defender
        for idx, defender in enumerate(sorted(world.defenders, key=lambda item: item.entity_id)[: self._cfg.max_defenders]):
            if defender.entity_id not in visible_defenders:
                continue
            dx = defender.x - attacker.x
            dy = defender.y - attacker.y
            rel_x, rel_y = world_to_ego(dx, dy, attacker.psi)
            att_vx, att_vy = body_velocity_to_world(attacker.u, attacker.v, attacker.psi)
            def_vx, def_vy = body_velocity_to_world(defender.u, defender.v, defender.psi)
            rel_world_x = def_vx - att_vx
            rel_world_y = def_vy - att_vy
            rel_u, rel_v = world_to_ego(rel_world_x, rel_world_y, attacker.psi)
            clearance = distance2d(attacker.x, attacker.y, defender.x, defender.y) - attacker.radius - defender.radius
            dpsi = defender.psi - attacker.psi
            defender_rows[idx] = np.array(
                [rel_x, rel_y, rel_u, rel_v, clearance, np.cos(dpsi), np.sin(dpsi)],
                dtype=np.float32,
            )
            defender_mask[idx] = 1.0

        obstacle_rows = np.zeros((self._cfg.max_obstacles, 4), dtype=np.float32)
        obstacle_mask = np.zeros((self._cfg.max_obstacles,), dtype=np.float32)
        visible_obstacles = {o.entity_id: o for o in visible.obstacles}
        for idx, obstacle in enumerate(sorted(world.obstacles, key=lambda item: item.entity_id)[: self._cfg.max_obstacles]):
            if obstacle.entity_id not in visible_obstacles:
                continue
            dx = obstacle.x - attacker.x
            dy = obstacle.y - attacker.y
            rel_x, rel_y = world_to_ego(dx, dy, attacker.psi)
            clearance = obstacle_clearance(attacker, obstacle)
            obstacle_rows[idx] = np.array([rel_x, rel_y, clearance, obstacle.radius], dtype=np.float32)
            obstacle_mask[idx] = 1.0

        return {
            "ego": ego,
            "goal": goal,
            "boundary": boundary,
            "defenders": defender_rows,
            "defenders_mask": defender_mask,
            "obstacles": obstacle_rows,
            "obstacles_mask": obstacle_mask,
        }
