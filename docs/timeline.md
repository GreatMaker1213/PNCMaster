# Timeline

## 2026-03-18

### 当前进度
- 完成 USV 仿真平台 v0.1 开发文档收敛，形成最终开发约束与实现边界。
- 完成基础项目骨架搭建，已实现基于 `gymnasium` 的 `AttackDefenseEnv`。
- 完成核心状态结构定义，包括攻击方、守方、障碍物、目标区与边界。
- 完成 3-DOF 简化动力学模型与前向欧拉积分。
- 完成场景生成器，支持基于随机种子的可复现场景初始化。
- 完成守方基础追击策略 `PurePursuitDefenderPolicy`。
- 完成观测构建模块，支持 ego、goal、boundary、defenders、obstacles 及对应 mask。
- 完成奖励模块与终止条件模块，实现目标到达、被捕获、碰撞、越界、数值失败等判定。
- 完成 rollout 记录器基础能力，支持 episode 起始、逐步记录与结束汇总。
- 完成基础 smoke test，验证 0 defender 与 1 defender 情况下环境可正常运行。

### 当前结论
- 已具备“进攻 USV 到达目标区域”这一任务机制的基础实现。
- 已具备可运行的首版仿真环境。
- 尚未实现实时可视化渲染，`render()` 目前未提供图形显示能力。
- 尚未实现稳定的智能进攻策略，目前主要完成的是环境侧能力，而非完整演示级策略系统。

### 下一步建议
- 实现最小可用的 2D 实时可视化。
- 增加一个面向目标航行的 attacker baseline policy。
- 补充更完整的单元测试与集成测试。

## 2026-03-19

### 当前进度
- 完成 V0.2 开发文档定稿，当前 V0.2 主文档固定为 `docs/DevDocV0.2.md`。
- 完成文档位置约束更新：从本阶段开始，项目文档统一维护在当前工程下的 `docs/` 目录中。
- 完成配置系统 V0.2 扩展，在 `src/usv_sim/config.py` 中增加 `AttackerBaselineConfig`，并保持对 V0.1 配置的向后兼容。
- 完成 V0.2 配置文件，新增 `configs/v0_2_default.yaml` 与 `configs/v0_2_baseline_validation.yaml`。
- 完成固定验证场景 `baseline_validation`，用于 attacker baseline 演示、集成测试与回归验证。
- 完成最小可用的 2D 实时可视化，`AttackDefenseEnv` 已支持 `render_mode="human"`，并接入 `matplotlib` 渲染器 `Simple2DRenderer`。
- 完成 attacker 侧目标航行基线策略 `GoalSeekingAttackerPolicy`，主接口为 `act(obs)`，满足 V0.2 文档冻结约束。
- 完成测试体系扩展，新增 unit tests、integration tests、升级后的 smoke test 以及本地 demo 入口脚本。
- 在 `RL` 环境中完成验证：unit tests 共 22 项通过，integration tests 共 4 项通过，smoke test 通过。
- 完成包初始化导入路径修正，并为 `RL` 环境补齐 `pytest`，使文档中的测试命令可执行。

### 当前结论
- V0.2 已完成“可观察、可演示、可验证”的阶段目标，平台从 V0.1 的最小可运行内核升级为具备基础研发支撑能力的研究原型平台。
- 当前环境已具备最小可用的 2D 实时可视化能力。
- 当前环境已具备在固定验证场景中稳定到达目标的 attacker baseline policy。
- 当前项目已具备更完整的自动化验证基础，能够对核心冻结契约提供回归保护。
- 当前文档体系已切换到 `docs/` 目录统一维护，后续版本文档、时间线与提交说明均应放置于该目录。

### 下一步建议
- 撰写并冻结 V0.3 开发文档，明确下一阶段的 classical planning/control 基线与 benchmark 方向。
- 在 V0.3 中优先引入 APF 等首批传统规划控制基线，并建立统一的评测入口。
- 继续增强结果记录、基准场景与对比评测能力，为后续 MPC / RRT / CBF / RL 等方法接入做准备。
