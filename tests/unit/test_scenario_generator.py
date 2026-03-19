# last update: 2026-03-19 09:36:00
# modifier: Claude Code

from __future__ import annotations

from pathlib import Path

from usv_sim.config import load_config
from usv_sim.core.geometry import obstacle_clearance, within_boundary
from usv_sim.core.math_utils import distance2d
from usv_sim.scenarios.generator import ScenarioGenerator


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CFG = load_config(ROOT / "configs" / "v0_2_default.yaml")
BASELINE_CFG = load_config(ROOT / "configs" / "v0_2_baseline_validation.yaml")


def test_default_scenario_is_reproducible_for_same_seed() -> None:
    generator = ScenarioGenerator(DEFAULT_CFG)
    world_a = generator.generate(123)
    world_b = generator.generate(123)
    assert world_a == world_b


def test_default_scenario_has_valid_initial_geometry() -> None:
    generator = ScenarioGenerator(DEFAULT_CFG)
    world = generator.generate(7)
    attacker = world.attacker
    assert within_boundary(attacker, world.boundary)
    assert distance2d(attacker.x, attacker.y, world.goal.x, world.goal.y) > world.goal.radius
    for defender in world.defenders:
        assert distance2d(attacker.x, attacker.y, defender.x, defender.y) > DEFAULT_CFG.scenario.capture_radius
    for obstacle in world.obstacles:
        assert obstacle_clearance(attacker, obstacle) > 0.0


def test_baseline_validation_scenario_matches_fixed_contract() -> None:
    generator = ScenarioGenerator(BASELINE_CFG)
    world = generator.generate(99)
    assert world.seed == 99
    assert world.scenario_id == "baseline_validation"
    assert world.attacker.x == 20.0
    assert world.attacker.y == 50.0
    assert world.attacker.psi == 0.0
    assert world.goal.x == 80.0
    assert world.goal.y == 50.0
    assert world.defenders == tuple()
    assert world.obstacles == tuple()
