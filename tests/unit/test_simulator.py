# last update: 2026-03-19 09:36:00
# modifier: Claude Code

from __future__ import annotations

from pathlib import Path

import numpy as np

from usv_sim.config import load_config
from usv_sim.core.simulator import WorldSimulator
from usv_sim.dynamics.fossen3dof import Fossen3DOFDynamics
from usv_sim.policies.defender_pursuit import PurePursuitDefenderPolicy
from usv_sim.scenarios.generator import ScenarioGenerator


ROOT = Path(__file__).resolve().parents[2]
CFG = load_config(ROOT / "configs" / "v0_2_baseline_validation.yaml")
SIMULATOR = WorldSimulator(Fossen3DOFDynamics(CFG.dynamics, CFG.action), PurePursuitDefenderPolicy(CFG.defender_policy), CFG)
GENERATOR = ScenarioGenerator(CFG)


def test_simulator_preserves_substep_early_stop_on_real_terminal() -> None:
    world = GENERATOR.generate(0)
    next_world, events = SIMULATOR.step(world, np.array([1.0, 0.0], dtype=np.float32))
    assert next_world.step_count == world.step_count + 1
    assert next_world.sim_time <= world.sim_time + CFG.env.dt_env
    assert next_world.sim_time > world.sim_time
    assert events.goal_distance <= 60.0
