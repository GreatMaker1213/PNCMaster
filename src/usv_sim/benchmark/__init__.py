# last update: 2026-03-20 11:56:00
# modifier: Codex

__all__ = [
    "BenchmarkConfig",
    "aggregate_episode_metrics",
    "run_single_episode",
    "evaluate_policy",
    "evaluate_from_config",
]


def __getattr__(name: str):
    if name == "aggregate_episode_metrics":
        from usv_sim.benchmark.metrics import aggregate_episode_metrics

        return aggregate_episode_metrics
    if name in {"BenchmarkConfig", "run_single_episode", "evaluate_policy", "evaluate_from_config"}:
        from usv_sim.benchmark.runner import BenchmarkConfig, evaluate_from_config, evaluate_policy, run_single_episode

        mapping = {
            "BenchmarkConfig": BenchmarkConfig,
            "run_single_episode": run_single_episode,
            "evaluate_policy": evaluate_policy,
            "evaluate_from_config": evaluate_from_config,
        }
        return mapping[name]
    raise AttributeError(f"module 'usv_sim.benchmark' has no attribute {name!r}")
