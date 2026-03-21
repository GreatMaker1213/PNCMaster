# last update: 2026年3月21日 15点30分
# modifier: KanviRen

"""
本脚用来测试一组指定配置的性能，并聚合指标输出到指定文件
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from usv_sim.benchmark.evaluator import evaluate_and_save


def main() -> None:
    config_path = ROOT / "configs" / "v0_3_obstacle_only.yaml"
    output_dir = ROOT / "outputs" / "benchmark_demo_apf"
    episodes, aggregate = evaluate_and_save(config_path=config_path, output_dir=output_dir, policy_type="apf")
    print({"episodes": len(episodes), "aggregate": aggregate, "output_dir": str(output_dir)})


if __name__ == "__main__":
    main()

