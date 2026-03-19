# last update: 2026-03-19 09:40:00
# modifier: Claude Code

from usv_sim.config import ProjectConfig, load_config

__all__ = ["AttackDefenseEnv", "ProjectConfig", "load_config"]


def __getattr__(name: str):
    if name == "AttackDefenseEnv":
        from usv_sim.envs.attack_defense_env import AttackDefenseEnv

        return AttackDefenseEnv
    raise AttributeError(f"module 'usv_sim' has no attribute {name!r}")
