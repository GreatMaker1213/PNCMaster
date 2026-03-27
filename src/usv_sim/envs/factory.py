# last update: 2026-03-25 10:50:00
# modifier: Codex

from __future__ import annotations

from pathlib import Path

from usv_sim.config import ProjectConfig, load_config
from usv_sim.envs.attack_defense_env import AttackDefenseEnv
from usv_sim.envs.attack_defense_kinematic_env import AttackDefenseKinematicEnv


_RENDER_MODE_SENTINEL = object()


def create_env(
    cfg: ProjectConfig | None = None,
    *,
    config_path: str | Path | None = None,
    render_mode: str | None | object = _RENDER_MODE_SENTINEL,
):
    if cfg is None:
        if config_path is None:
            raise ValueError("either cfg or config_path must be provided")
        cfg = load_config(config_path)
    if cfg.env.backend == "dynamic":
        if render_mode is _RENDER_MODE_SENTINEL:
            return AttackDefenseEnv(cfg=cfg)
        return AttackDefenseEnv(cfg=cfg, render_mode=render_mode)
    if cfg.env.backend == "kinematic":
        if render_mode is _RENDER_MODE_SENTINEL:
            return AttackDefenseKinematicEnv(cfg=cfg)
        return AttackDefenseKinematicEnv(cfg=cfg, render_mode=render_mode)
    raise ValueError(f"unsupported env backend: {cfg.env.backend}")
