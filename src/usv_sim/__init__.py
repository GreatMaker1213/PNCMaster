# last update: 2026-03-25 11:12:00
# modifier: Codex

from usv_sim.config import ProjectConfig, load_config

__all__ = ["AttackDefenseEnv", "AttackDefenseKinematicEnv", "ProjectConfig", "create_env", "load_config"]


def __getattr__(name: str):
    if name == "AttackDefenseEnv":
        from usv_sim.envs.attack_defense_env import AttackDefenseEnv

        return AttackDefenseEnv
    if name == "AttackDefenseKinematicEnv":
        from usv_sim.envs.attack_defense_kinematic_env import AttackDefenseKinematicEnv

        return AttackDefenseKinematicEnv
    if name == "create_env":
        from usv_sim.envs.factory import create_env

        return create_env
    raise AttributeError(f"module 'usv_sim' has no attribute {name!r}")

