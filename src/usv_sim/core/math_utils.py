# last update: 2026-03-18 21:27:07
# modifier: Claude Code

from __future__ import annotations

import math

import numpy as np


TWO_PI = 2.0 * math.pi


def wrap_to_pi(angle: float) -> float:
    wrapped = (angle + math.pi) % TWO_PI - math.pi
    if wrapped <= -math.pi:
        wrapped += TWO_PI
    return wrapped


def distance2d(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)


def rotation_matrix(theta: float) -> np.ndarray:
    c = math.cos(theta)
    s = math.sin(theta)
    return np.array([[c, -s], [s, c]], dtype=np.float64)


def world_to_ego(dx: float, dy: float, psi: float) -> tuple[float, float]:
    c = math.cos(psi)
    s = math.sin(psi)
    rel_x = c * dx + s * dy
    rel_y = -s * dx + c * dy
    return rel_x, rel_y


def body_velocity_to_world(u: float, v: float, psi: float) -> tuple[float, float]:
    c = math.cos(psi)
    s = math.sin(psi)
    vx = c * u - s * v
    vy = s * u + c * v
    return vx, vy


def world_velocity_to_ego(vx: float, vy: float, psi: float) -> tuple[float, float]:
    return world_to_ego(vx, vy, psi)


def clip(value: float, low: float, high: float) -> float:
    return float(min(max(value, low), high))


def finite_all(*values: float) -> bool:
    return all(math.isfinite(v) for v in values)
