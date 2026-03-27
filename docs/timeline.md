> last update: 2026-03-25 11:18:00
> modifier: Codex

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

## 2026-03-20

### 当前进度
- 完成 V0.2 可视化问题排查，确认 baseline demo 能正常结束但 human render 在 episode 执行期间出现小白窗、不连续刷新的异常。
- 通过在 `src/usv_sim/rendering/simple_2d.py` 中添加调试阻塞，定位到 `flush_events()` 与 `plt.pause(...)` 没有进入执行。
- 确认问题根因是对 matplotlib backend 的过度判断：此前使用 `"agg"` 相关条件时，会把 `TkAgg` 这类默认可交互后端误判为不应执行 GUI 刷新路径。
- 完成 `Simple2DRenderer` 修复：去除错误的 backend 刷新分支，保证在当前 Windows + RL 环境下正常执行 `plt.show(block=False)`、`flush_events()` 与 `plt.pause(...)`。
- 完成 `demos/run_attacker_baseline_demo.py` 配套修复：结束后直接使用 `plt.ioff()` 与 `plt.show()` 保持窗口显示，而不再依赖错误判断逻辑。
- 本地验证通过，`run_attacker_baseline_demo.py` 现已能够正常实时渲染并完成 baseline episode 演示。

### 当前结论
- V0.2 的最小可用 2D 实时可视化现在已具备稳定可演示状态。
- 本次修复属于 V0.2 的 patch 级 bugfix，应作为 `V0.2.1` 版本记录。
- 本次问题说明：在当前项目的人机交互渲染场景下，不应对默认交互后端做过度保守判断，否则会直接破坏实时刷新链路。

### 下一步建议
- 将当前修复提交到 git，打上 `V0.2.1` tag 并推送远程仓库，形成可回退的稳定补丁版本。
- 后续如继续扩展 render 能力，再考虑更严格地区分纯 `Agg` 与交互 backend，但应以可视化主链路稳定为前提。
- 在进入 V0.3 开发前，以当前可正常演示的 V0.2.1 作为基线版本继续管理。

## 2026-03-20（V0.3）

### 当前进度
- 完成 V0.3 开发文档收敛，明确 `T301~T309` 任务边界、benchmark 口径与验收标准。
- 完成统一 attacker 策略接口收敛：`AttackerPolicy.reset(seed=...)` + `act(obs)`，并新增策略工厂统一创建入口。
- 完成两类 classical baseline：`APFAttackerPolicy` 与 `HeadingHoldAttackerPolicy`，并保留 V0.2 `GoalSeekingAttackerPolicy` 对比链路。
- 完成 benchmark 模块：`runner`、`evaluator`、`metrics`，支持多 seed 批量评测与统一结果统计。
- 完成 V0.3 场景配置：`goal_only`、`obstacle_only`、`defender_pressure`，固定 seeds 为 `[0, 1, 2, 3, 4]`。
- 完成 benchmark 结果落盘：`episodes.jsonl`、`episodes.csv`、`aggregate.json`，统一输出字段用于后续对比分析。
- 完成 V0.3 demo 与测试补齐：新增 unit/integration/smoke 覆盖，形成 APF/heading/goal 的可回归对比链路。
- 完成两项闭环补齐：  
  1) aggregate 增加 `policy_config_name` 与 `seed_set_summary` 等字段；  
  2) 将 `T302/T303` 验收标准固化为自动化集成测试断言。
- 在 `RL` 环境完成验证：`pytest tests/unit tests/integration -q` 通过（39 passed）。

### 当前结论
- V0.3 已从“单策略可运行”升级为“多策略可比较”的研究验证平台形态。
- APF、goal、heading-hold 已在统一 rollout/evaluation 入口下可复现运行，具备稳定 benchmark 基线能力。
- V0.3 文档要求的关键闭环已完成：指标与元数据可稳定落盘，验收条件可自动回归校验。
- 当前系统已满足“科研算法验证与快速迭代”目标层级，可作为后续 RL / MPC / RRT / CBF / belief control 接入基线。

### 下一步建议
- 冻结 V0.3 配置与测试基线，整理一次 `V0.3` 提交说明并打版本 tag。
- 基于当前 benchmark 输出补一版标准对比脚本（表格 + 曲线），形成可直接引用的实验报告模板。
- 在 V0.4 优先实现 `RLPolicyAdapter`（保持 action-level 接口不变），接入第一个学习型策略对比实验。

## 2026-03-21（V0.3.1）

### 当前进度
- 完成 `WorldSimulator` 子步仿真时序修正，避免 defender 在同一 substep 决策中直接读取 attacker 的最新中间状态，修复先后更新导致的“信息优势”问题。
- 完成 attacker/defender 决策频率口径统一：在每个 env step 内固定双方决策节奏，修复 defender 在每个 substep 高频重决策而 attacker 仅 step 级决策的不平衡问题。
- 完成 `demos/` 目录脚本命名收敛：  
  - `run_attacker_baseline_demo.py` 重命名为 `run_play.py`  
  - `run_benchmark_demo.py` 重命名为 `run_evaluate.py`
- 完成本地回归验证：`tests/unit/test_simulator.py` 与 `tests/smoke/test_env_smoke.py` 通过，入口重命名后 demo 运行链路可用。
- 完成 `V0.3.1` 版本提交与 tag 组织，用于记录本次公平性修复与入口脚本命名规范化改动。

### 当前结论
- `V0.3.1` 属于 V0.3 的 patch 版本，核心价值是修复仿真公平性问题，而非新增算法能力。
- 本次修复后，当前平台在“策略比较实验”的时序一致性与决策频率一致性上更符合研究评测的公平口径。
- `demos` 脚本命名语义更清晰：`play` 对应单回合可视化观察，`evaluate` 对应多回合指标评估。

### 下一步建议
- 在 `V0.4` 中将当前 `demos` 级能力正式上移到仓库顶层：实现统一入口 `play.py` 与 `evaluate.py`。
- 在 `V0.4` 中补齐顶层入口的参数契约、集成测试与输出元数据（建议增加 `run_meta.json`），保证长期协作开发稳定性。
- 更新 `README` / 开发文档中的运行命令，明确“顶层正式入口”与“demos 演示入口”的职责边界。

## 2026-03-22（V0.4）

### 当前进度
- 完成 V0.4 开发文档定稿，明确版本目标为“统一正式入口”，并将偏学习型适配链设计迁移到 `V0.5` 文档管理。
- 在仓库顶层实现 `play.py`：支持按配置文件与策略类型运行单回合，可实时渲染并输出回合摘要。
- 在仓库顶层实现 `evaluate.py`：支持按配置文件与策略类型执行多回合评估，输出 `episodes.jsonl`、`episodes.csv`、`aggregate.json`。
- 在 `evaluate.py` 中增加运行元数据落盘 `run_meta.json`，并实现 `git_commit` 获取失败时的降级处理（记录为 `null`，不阻断评测）。
- 完成输出目录策略收敛：默认不覆盖非空目录，显式 `--overwrite` 时允许覆盖。
- 完成入口参数与行为约束收敛：`play.py` 保持窗口直至用户关闭；`evaluate.py` 要求 `benchmark.seeds` 明确存在并可解析。
- 补齐 V0.4 入口相关测试（unit + integration），并在当前环境完成通过。

### 当前结论
- V0.4 已实现“场景配置 + 策略类型”直达运行能力，解决了此前入口分散、演示脚本与研发流程混用的问题。
- 当前项目已具备稳定的顶层研发入口：`play.py` 用于行为观察，`evaluate.py` 用于批量指标评估与结果沉淀。
- 本版本属于工程化可用性增强版本，核心收益是提高算法迭代效率与协作一致性，而非新增算法能力。

### 下一步建议
- 以 `V0.4` 为基线更新主文档中的运行指引，统一推荐使用顶层 `play.py` 与 `evaluate.py`。
- 继续推进 `V0.5`：聚焦 learning policy adapter、训练/评测配置分离与更系统的策略适配链路。
- 在下一版本中补充自动化发布说明模板（含运行命令、输出目录规范、实验记录建议），降低协作成本。

## 2026-03-23（V0.5）

### 当前进度
- 完成 V0.5 代码主线落地：在不改变 `AttackDefenseEnv`、`play.py`、`evaluate.py`、benchmark runner 外部使用方式的前提下，引入最小 controller 层。
- 完成 `TrackingControllerConfig` 配置接入，在 `src/usv_sim/config.py` 中增加 `tracking_controller` 配置块、默认值、加载逻辑与校验逻辑。
- 新增 `src/usv_sim/controllers/` 与 `src/usv_sim/guidance/` 模块，形成 `guidance -> reference -> controller -> env action` 的最小抽象链。
- 完成 `HeadingSpeedReference`、`GuidancePolicy`、`GoalGuidance`、`APFGuidance`、`TrackingController`、`HeadingSpeedTrackingController` 的实现。
- 新增 `src/usv_sim/policies/controller_backed.py`，将 guidance 与 controller 组合成仍满足 `AttackerPolicy.reset/act` 契约的统一对外策略对象。
- 将 `GoalSeekingAttackerPolicy` 与 `APFAttackerPolicy` 迁移为 controller-backed 实现，并保留 `HeadingHoldAttackerPolicy` 的兼容 direct-action 版本以维持既有验收口径。
- 更新 `src/usv_sim/policies/factory.py`，统一向 attacker policy 注入 `cfg.tracking_controller`，保证 V0.4 顶层入口和 V0.3 benchmark 链路无需改写。
- 更新配置文件 `configs/v0_2_default.yaml`、`configs/v0_2_baseline_validation.yaml`、`configs/v0_3_goal_only.yaml`、`configs/v0_3_obstacle_only.yaml`、`configs/v0_3_defender_pressure.yaml`，显式增加 `tracking_controller` 配置块。
- 补充 V0.5 单元测试与集成测试，覆盖 reference、controller、guidance、controller-backed policy 组合及与既有 benchmark 链路的兼容性。

### 新增或改动文件
- `src/usv_sim/config.py`
  新增 `TrackingControllerConfig`、默认 controller 配置、校验与加载逻辑，并将其纳入 `ProjectConfig`。
- `src/usv_sim/controllers/__init__.py`
  暴露 controller 模块公共接口。
- `src/usv_sim/controllers/base.py`
  定义 `TrackingController` 基础接口。
- `src/usv_sim/controllers/heading_speed.py`
  实现最小 `HeadingSpeedTrackingController`，将 heading/surge reference 映射为 env action。
- `src/usv_sim/guidance/__init__.py`
  暴露 guidance 模块公共接口。
- `src/usv_sim/guidance/base.py`
  定义 `GuidancePolicy` 基础接口与期望 surge 速度解析辅助逻辑。
- `src/usv_sim/guidance/reference.py`
  定义 `HeadingSpeedReference` 数据结构。
- `src/usv_sim/guidance/goal_guidance.py`
  实现基于 goal observation 的最小 guidance。
- `src/usv_sim/guidance/apf_guidance.py`
  实现基于 APF 的最小 guidance，将势场方向转换为 reference。
- `src/usv_sim/policies/controller_backed.py`
  实现 `ControllerBackedAttackerPolicy`，对外继续暴露 `AttackerPolicy` 契约。
- `src/usv_sim/policies/attacker_goal_baseline.py`
  迁移为 `GoalGuidance + HeadingSpeedTrackingController` 的组合实现。
- `src/usv_sim/policies/attacker_apf_baseline.py`
  迁移为 `APFGuidance + HeadingSpeedTrackingController` 的组合实现。
- `src/usv_sim/policies/attacker_heading_baseline.py`
  迁移为兼容 `heading_hold` 语义的 controller-backed 实现。
- `src/usv_sim/policies/factory.py`
  改为统一向 attacker policy 注入 `tracking_controller` 配置。
- `configs/v0_2_default.yaml`
  显式增加 `tracking_controller` 配置块。
- `configs/v0_2_baseline_validation.yaml`
  显式增加 `tracking_controller` 配置块。
- `configs/v0_3_goal_only.yaml`
  显式增加 `tracking_controller` 配置块。
- `configs/v0_3_obstacle_only.yaml`
  显式增加 `tracking_controller` 配置块。
- `configs/v0_3_defender_pressure.yaml`
  显式增加 `tracking_controller` 配置块。
- `tests/unit/test_heading_speed_reference.py`
  验证 `HeadingSpeedReference` 字段与基本语义。
- `tests/unit/test_heading_speed_controller.py`
  验证 controller 输出 shape、dtype、范围与基本控制方向。
- `tests/unit/test_goal_guidance.py`
  验证 goal guidance 的 reference 输出方向与速度逻辑。
- `tests/unit/test_apf_guidance.py`
  验证 APF guidance 在障碍存在时能输出合理 reference。
- `tests/unit/test_controller_backed_policy.py`
  验证 guidance + controller 组合后仍满足 `AttackerPolicy` 契约。
- `tests/integration/test_controller_entrypoint_compat.py`
  验证 controller-backed policy 可以通过既有 benchmark runner 跑通一回合。
- `docs/timeline.md`
  记录本次 V0.5 开发内容与变更文件，方便协作开发者上手。

### 当前结论
- V0.5 已按“最小扰动”原则落地了最小 controller 架构：controller 插入点位于 `AttackerPolicy / factory` 一层，而非 env / simulator / dynamics 内部。
- 现有 `play.py`、`evaluate.py`、benchmark runner/evaluator 的外部用法保持不变。
- 当前平台已同时具备两类链路的工程基础：
  1) traditional guidance/controller 路径；
  2) future direct-action end-to-end 路径。
- 本次实现没有承诺或引入 substep inner-loop controller 改造，符合 V0.5 第一阶段边界。

### 下一步建议
- 在 `RL` 环境中完成 V0.5 新增测试与既有入口测试回归，确认 controller-backed goal/apf 在当前 benchmark 上稳定可运行。
- 后续如继续推进 V0.5，可优先增加 direct-action stub regression test，进一步保护 future RL/扩散/流匹配方法可跳过 controller 的路径。
- 若进入 V0.6，再考虑在不破坏当前 V0.5 契约的前提下，引入更复杂的 planner/reference 类型与 safety filter 链路。


## 2026-03-25（V0.5.1）

### 当前进度
- 完成 V0.5.1 主线开发，在当前动态 env 保持低层 action 语义 `[surge_cmd, yaw_cmd]` 不变的前提下，引入更强的 velocity-tracking controller。
- 完成局部规划统一输出升级：从 V0.5 的 `HeadingSpeedReference` 主路径转向 `DesiredVelocityReference(u_d, r_d)`，使局部规划器输出更接近当前 project 中局部规划算法的最大公共部分。
- 完成 `VelocityTrackingControllerConfig` 配置接入，并为旧配置提供兼容回退，使未显式声明 `velocity_tracking_controller` 的历史配置仍可运行。
- 完成 `VelocityTrackingController` 实现，在 yaw 通道中显式加入 yaw-rate tracking 与 sideslip 补偿项，用于缓解 V0.5 中明显的打滑问题。
- 完成 `GoalGuidance` 与 `APFGuidance` 升级，改为直接输出 `DesiredVelocityReference`，便于同一 planner 输出同时接入动态 env 与纯运动学 env。
- 新增 sibling env：`AttackDefenseKinematicEnv`，以及对应的 `Kinematic3DOF`、`KinematicWorldSimulator`、`KinematicPurePursuitDefenderPolicy`，用于直接执行规划器输出并观察 planner-only 效果。
- 新增 `envs/factory.py`，统一根据 `cfg.env.backend` 创建动态 env 或运动学 env。
- 更新 `play.py`、`evaluate.py`、`benchmark/runner.py`，改为通过 env factory 选后端，使入口脚本外部使用方式保持稳定。
- 新增 V0.5.1 示例配置 `configs/v0_5_1_goal_only_dynamic.yaml` 与 `configs/v0_5_1_goal_only_kinematic.yaml`。
- 补齐 V0.5.1 单元测试、集成测试与 smoke，覆盖新 reference、新 controller、kinematic backend 和入口兼容链路。
- 在 `RL` 环境完成验证：
  - `pytest tests/unit tests/integration -q`：`60 passed, 2 warnings`
  - `python tests/smoke/test_env_smoke.py`：通过

### 新增或改动文件
- `src/usv_sim/config.py`
  新增 `env.backend` 与 `VelocityTrackingControllerConfig`，并增加相应默认值、加载与校验逻辑。
- `src/usv_sim/guidance/reference.py`
  增加 `DesiredVelocityReference`，作为 V0.5.1 的局部规划统一输出结构。
- `src/usv_sim/guidance/base.py`
  将 guidance 主接口切换到 `DesiredVelocityReference`，并增加 `resolve_desired_yaw_rate(...)` 辅助逻辑。
- `src/usv_sim/guidance/goal_guidance.py`
  改为输出 `(u_d, r_d)` 形式的规划参考量。
- `src/usv_sim/guidance/apf_guidance.py`
  改为输出 `(u_d, r_d)` 形式的 APF 规划参考量。
- `src/usv_sim/guidance/__init__.py`
  暴露新的 reference 类型与 guidance 模块公共接口。
- `src/usv_sim/controllers/base.py`
  继续作为 controller 抽象基类，放宽 reference 类型约束以兼容 V0.5.1 新 reference。
- `src/usv_sim/controllers/velocity_tracking.py`
  新增 stronger controller，实现基于 `u, v, r` 的 velocity tracking + sideslip compensation。
- `src/usv_sim/controllers/__init__.py`
  暴露新的 `VelocityTrackingController`。
- `src/usv_sim/dynamics/kinematic3dof.py`
  新增运动学推进器，按 `(u_d, r_d, dt)` 推进状态。
- `src/usv_sim/core/kinematic_simulator.py`
  新增运动学版本 simulator，复用现有任务事件判定逻辑。
- `src/usv_sim/policies/defender_pursuit_kinematic.py`
  新增运动学 defender 策略，输出 `(u_d, r_d)`。
- `src/usv_sim/envs/attack_defense_kinematic_env.py`
  新增 sibling 纯运动学 env，与动态 env 共享场景/观测/奖励/终止语义。
- `src/usv_sim/envs/factory.py`
  新增 env factory，统一创建 dynamic 或 kinematic env。
- `src/usv_sim/policies/controller_backed.py`
  新增 `ReferenceBackedAttackerPolicy`，用于让 planner 输出直接作为 kinematic env 的上层输入。
- `src/usv_sim/policies/attacker_goal_baseline.py`
  改为使用新 velocity controller 的动态路径实现。
- `src/usv_sim/policies/attacker_apf_baseline.py`
  改为使用新 velocity controller 的动态路径实现。
- `src/usv_sim/policies/attacker_heading_baseline.py`
  保留动态 direct-action `heading_hold`，并增加 `HeadingHoldVelocityGuidance` 供 kinematic backend 使用。
- `src/usv_sim/policies/factory.py`
  改为同时按 `policy_type` 和 `env.backend` 创建动态后端或运动学后端所需策略。
- `src/usv_sim/__init__.py`
  增加 `AttackDefenseKinematicEnv` 与 `create_env` 的延迟导出。
- `src/usv_sim/benchmark/runner.py`
  改为通过 env factory 创建 env，并在 episode/aggregate 中记录 `env_backend`。
- `src/usv_sim/benchmark/metrics.py`
  聚合输出增加 `env_backend` 字段。
- `play.py`
  改为通过 env factory 选择后端，summary 增加 `env_backend`。
- `evaluate.py`
  `run_meta.json` 与输出打印增加 `env_backend` 语义。
- `configs/v0_5_1_goal_only_dynamic.yaml`
  新增 V0.5.1 动态 env 示例配置。
- `configs/v0_5_1_goal_only_kinematic.yaml`
  新增 V0.5.1 运动学 env 示例配置。
- `tests/unit/test_heading_speed_reference.py`
  补充 `DesiredVelocityReference` 的单元测试。
- `tests/unit/test_velocity_tracking_controller.py`
  新增 stronger controller 单元测试。
- `tests/unit/test_goal_guidance.py`
  更新为验证 `GoalGuidance` 输出 `DesiredVelocityReference`。
- `tests/unit/test_apf_guidance.py`
  更新为验证 `APFGuidance` 输出 `DesiredVelocityReference`。
- `tests/unit/test_controller_backed_policy.py`
  新增 `ReferenceBackedAttackerPolicy` 覆盖，并适配新的 reference 语义。
- `tests/integration/test_controller_entrypoint_compat.py`
  改为同时验证 dynamic / kinematic 两个 backend 的插入点兼容性。
- `tests/integration/test_play_entrypoint.py`
  增加 kinematic backend 的入口测试。
- `tests/integration/test_evaluate_entrypoint.py`
  增加 kinematic backend 的评估入口测试。
- `tests/smoke/test_env_smoke.py`
  补充 `goal_only_kinematic` smoke，并改为通过 env factory / policy factory 走正式链路。
- `docs/timeline.md`
  记录本次 V0.5.1 开发内容，方便协作开发者上手。

### 当前结论
- V0.5.1 已完成两条后端链路的打通：
  1) `DesiredVelocityReference -> stronger controller -> dynamic env`
  2) `DesiredVelocityReference -> kinematic env`
- 当前 project 已具备区分“planner 本身效果”和“planner + controller + dynamics 效果”的基础设施。
- 本次实现继续保持最小扰动原则：未重写 `AttackDefenseEnv`、`WorldSimulator`、`Fossen3DOFDynamics` 的主语义，也没有改变 `play.py` / `evaluate.py` 的外部命令形式。

### 下一步建议
- 在固定 benchmark 场景下量化比较 V0.5 与 V0.5.1 controller 的侧滑指标，例如 `mean_abs_sideslip_angle` 与 `mean_abs_sway_velocity`。
- 继续补 planner-only 与 dynamic backend 的对照实验模板，使 `evaluate.py` 可以直接产出 dynamic vs kinematic 对照结果。
- 后续若进入 V0.5.2/V0.6，可继续考虑更高层的 waypoint/path/trajectory reference 与 safety filter 链路。

