# last update: 2026-03-19 09:35:00
# modifier: Claude Code

from __future__ import annotations

import math

from usv_sim.core.math_utils import body_velocity_to_world, distance2d, world_to_ego, wrap_to_pi


def test_wrap_to_pi_handles_boundary_values() -> None:
    assert math.isclose(wrap_to_pi(0.0), 0.0)
    assert math.isclose(wrap_to_pi(math.pi), math.pi)
    assert math.isclose(wrap_to_pi(-math.pi), math.pi)
    assert math.isclose(wrap_to_pi(3.0 * math.pi), math.pi)


def test_distance2d_returns_euclidean_distance() -> None:
    assert math.isclose(distance2d(0.0, 0.0, 3.0, 4.0), 5.0)


def test_world_to_ego_matches_heading_convention() -> None:
    rel_x, rel_y = world_to_ego(0.0, 1.0, math.pi / 2.0)
    assert math.isclose(rel_x, 1.0, abs_tol=1e-6)
    assert math.isclose(rel_y, 0.0, abs_tol=1e-6)


def test_body_velocity_to_world_rotates_body_velocity() -> None:
    vx, vy = body_velocity_to_world(1.0, 0.0, math.pi / 2.0)
    assert math.isclose(vx, 0.0, abs_tol=1e-6)
    assert math.isclose(vy, 1.0, abs_tol=1e-6)
