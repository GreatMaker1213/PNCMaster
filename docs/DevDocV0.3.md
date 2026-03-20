# DevDocV0.3

> 本文档是 USV Sim 项目的 **V0.3 开发文档**。
>
> 它建立在 `docs/FinalDevDocV0.1.md` 与 `docs/DevDocV0.2.md` 已完成的基础上，用于定义 **V0.3 的新增目标、模块扩展、评测基线、统一实验入口与验收标准**。
>
> 若 V0.3 文档与 V0.1 / V0.2 文档存在冲突：
>
> - **未被 V0.3 显式修改的内容，继续继承 V0.1 / V0.2**
> - **被 V0.3 显式新增或调整的内容，以本文为准**

---

## 1. V0.3 版本定位

### 1.1 V0.3 核心目标

V0.3 的目标不是继续补环境工程脚手架，而是让平台正式进入“**算法基线可对比**”阶段。

在 V0.2 中，项目已经具备：

- 可运行的仿真核心
- 最小可用 2D 实时可视化
- 一个 attacker 目标航行 baseline
- 更完整的自动化测试体系

因此 V0.3 需要把重点转移到：

1. **引入第一批传统规划/控制 baseline**
2. **建立统一的算法运行与评测入口**
3. **补齐结果记录、回合统计与 benchmark 场景体系**

### 1.2 V0.3 的工程意义

如果没有 V0.3，当前平台仍然主要只能回答两个问题：

- 环境能不能跑？
- 一个简单的目标航行脚本策略能不能动起来？

但后续真正的研发问题是：

- APF、Pure Pursuit、Heading Hold、MPC、RRT 等方法谁更适合当前任务？
- 不同障碍/防守密度下，方法之间表现如何？
- 后续 RL、扩散模型、流匹配方法接入后，应该和哪些 classical baseline 对比？

所以 V0.3 的本质是：

> 把平台从“能开发单个方法”推进到“能系统比较多种方法”的阶段。

---

## 2. V0.3 范围与非目标

### 2.1 V0.3 范围

V0.3 范围冻结为以下四类内容：

#### A. 第一批 classical baseline
V0.3 至少引入两类非学习 baseline：

- **APF attacker baseline**
- **heading / waypoint-style control baseline**

其目标不是求最优，而是建立清晰、稳定、可复现的 classical 参考线。

#### B. 统一算法运行接口
将 attacker baseline 从“单个策略文件”提升为“统一的 attacker 方法接口”，支持：

- 目标航行 baseline
- APF baseline
- 后续 MPC / RRT / RL policy adapter

#### C. benchmark 场景与评测入口
V0.3 要开始建立：

- 一组命名 benchmark 场景
- 一套统一 rollout / evaluation 入口
- 一组稳定的核心指标输出

#### D. 结果记录与对比分析基础
V0.3 要让每种方法在相同场景、相同步数预算下，都可以输出结构一致的结果记录，便于后续做表格、画图和算法对比。

### 2.2 V0.3 明确不做

V0.3 不做以下内容：

- 训练级 RL pipeline
- replay buffer / learner / trainer 框架
- diffusion / flow matching 的训练与采样实现
- 完整 MPC 求解器工程化接入
- 完整 RRT* / kinodynamic planner 框架
- 多 attacker / 多智能体协同训练
- 感知噪声建模、状态估计器、belief update 正式实现
- 复杂 GUI 面板、结果可视化 dashboard

---

## 3. V0.3 总体原则

### 3.1 原则 A：方法扩展不能污染 env 主逻辑

V0.3 继续坚持：

- env 只接收 action
- baseline / planner / controller 都是 env 外部调用者
- env 不因为方法数量增加而塞入算法分支逻辑

### 3.2 原则 B：统一接口优先于单点快写

从 V0.3 开始，不再鼓励每增加一个方法就单独发明一套调用方式。

所有 attacker 方法都应向统一接口收敛，避免后续：

- demo 启动方式不一致
- 测试入口不一致
- benchmark 统计口径不一致

### 3.3 原则 C：benchmark 要先追求稳定，再追求丰富

V0.3 的 benchmark 场景数量不需要很多，但必须：

- 命名清晰
- 难度分层明确
- 配置可复现
- 结果易解释

### 3.4 原则 D：先做 classical baseline，再接学习算法

因为 classical baseline 的意义是为后续学习算法提供：

- 最低性能参考
- 行为合理性参考
- 问题难度参考

如果没有这些参考线，后续 RL / diffusion 方法即使跑通，也很难知道结果究竟好不好。

---

## 4. V0.3 对 V0.2 的继承关系

以下内容在 V0.3 中默认继续继承：

- V0.1 的 dynamics / reward / termination / observation 冻结语义
- V0.2 的 human render 语义
- V0.2 的固定验证场景
- V0.2 的 attacker goal baseline
- V0.2 的 unit / integration / smoke 测试框架

V0.3 不重写这些能力，只新增：

- 统一 attacker 方法接口
- 第一批传统规划/控制 baseline
- benchmark 场景体系
- evaluation/rollout 入口
- 结果记录与基础分析格式

---

## 5. V0.3 核心新增目标

## 5.1 统一 attacker 方法接口

V0.3 建议把 attacker 侧方法抽象为统一的**动作级 attacker 接口**，例如：

```python
class AttackerPolicy:
    def reset(self, *, seed: int | None = None) -> None: ...
    def act(self, obs: dict[str, np.ndarray]) -> np.ndarray: ...
```

并在此接口上扩展：

- `GoalSeekingAttackerPolicy`
- `APFAttackerPolicy`
- `HeadingHoldAttackerPolicy`
- 更后续的 `MPCPolicyAdapter` / `RRTPolicyAdapter` / `RLPolicyAdapter`

这里需要明确一点：

- V0.3 统一的是**面向 rollout / benchmark 的动作级接口**
- 对于输出 waypoint、参考航向、参考轨迹的更复杂方法，不直接改 env 接口，而是通过 adapter 收敛到 `AttackerPolicy`
- 因此，未来 `MPC`、`RRT`、belief control、CBF 外挂等都应以“adapter 后输出 action”的形式接入统一评测链路

### 冻结要求

- `reset(seed=...)` 是统一接口的一部分，runner 必须在每个 episode 开始前调用
- 所有 attacker 方法输出仍为 `[surge_cmd, yaw_cmd]`
- 不允许引入新的 env action 维度
- benchmark / demo / integration test 统一走这一接口层
- env 侧仍只接收动作，不直接识别 policy 类型
- 若方法天然输出 reference / waypoint / trajectory，则必须通过独立 adapter 收敛到该接口，而不是修改 env action 语义

---

## 5.2 第一批 classical baseline

### A. APF attacker baseline

V0.3 首个重点 baseline 建议为 **APF（Artificial Potential Field）**。

目标：

- 对 goal 施加吸引项
- 对 obstacle / defender / boundary 施加排斥项
- 输出期望航向，再映射为 `[surge_cmd, yaw_cmd]`

为了避免实现阶段漂移，V0.3 建议冻结 APF 的最小数学语义如下：

1. **只允许使用 observation 中可见对象信息**
   - goal 始终可见，可使用 `goal` observation
   - obstacle / defender 只允许使用 observation 中当前可见且 `mask == 1` 的对象
   - 不允许 APF baseline 直接读取 `WorldState` 中不可见真值对象以获取“超视距规避能力”

2. **goal 吸引项在 ego frame 下定义**

```text
f_att = k_att * [goal_rel_x, goal_rel_y]
```

3. **obstacle / defender 排斥项采用带 influence radius 的截断排斥形式**

对任一威胁源相对位置 `p = [rel_x, rel_y]`，记：

```text
d = max(||p||_2, eps)
```

若 `d < influence_radius`，则：

```text
f_rep_i = -k_rep * (1 / d - 1 / influence_radius) / (d * d) * p / d
```

否则：

```text
f_rep_i = 0
```

其中：

- `eps` 为防止奇异的正数下界
- `influence_radius` 外排斥项严格为 0

4. **boundary 排斥项允许基于 boundary observation 构造**
   - 其实现可以是世界系下左右/上下边界排斥合成后再转回 ego frame
   - 但必须只依赖 observation 中已有边界距离字段，不得额外读取隐藏真值辅助信息

5. **总势场向量合成与动作映射**

```text
f_total = f_att + sum(f_rep_obstacles) + sum(f_rep_defenders) + f_boundary
desired_heading = atan2(f_total_y, f_total_x)
```

再使用与 V0.2 goal baseline 一致风格的 yaw/surge 映射：

- yaw 命令根据 `desired_heading` 的相对航向误差生成
- surge 命令使用转向减速规则
- 当 `||f_total||` 过小或数值不稳定时，允许退化为 goal-heading baseline 行为，而不是输出随机动作

V0.3 中 APF 的职责：

- 作为第一种“显式考虑障碍与威胁”的 classical baseline
- 用于与 V0.2 的 goal baseline 对比
- 为后续更复杂 planner 提供中间层参考

### B. Heading-hold baseline

为了避免接口和验收口径模糊，V0.3 建议**只选择一种**第二 classical baseline：

- `HeadingHoldAttackerPolicy`

而**不在 V0.3 同时引入 waypoint follower**。

其最小职责建议为：

- 使用 goal 在 ego frame 下的相对方向构造期望相对航向
- 使用 heading hold + yaw rate damping 生成 `yaw_cmd`
- 使用简单 surge schedule 生成 `surge_cmd`

它的作用是：

- 提供一个比 goal baseline 更规范的控制式参考
- 区分“纯任务朝向控制”与“显式环境规避”的行为差异

### 对 baseline 的要求

V0.3 中每个 baseline 都必须：

- 参数可配置
- rollout 可复现
- 可纳入统一 benchmark 入口
- 可通过统一统计字段输出结果

---

## 5.3 Benchmark 场景体系

V0.3 需要把“一个 baseline_validation 场景”扩展为“一组 benchmark 场景”。

同时建议明确：

- `baseline_validation` 不只是 V0.2 遗留场景，而是 **V0.3 的 mandatory regression scene**
- 它继续用于保护“最基本目标到达能力”和 goal/heading 类 baseline 的回归正确性

推荐至少定义三类：

### B300: Baseline-validation（mandatory regression）
- 直接继承 V0.2 的固定验证场景
- 主要用于：
  - goal baseline 回归
  - heading baseline 回归
  - benchmark runner 最基础正确性验证

### B301: Goal-only
- 无 defender
- 无 obstacle
- 用于验证最基本目标到达能力

### B302: Obstacle-only
- 有 obstacle
- 无 defender
- 用于验证避障能力
- V0.3 第一阶段建议只保留**一个默认难度版本**，不要同时引入 easy / medium / hard

### B303: Defender-pressure
- 有 defender
- V0.3 第一阶段建议先固定为 **1 个 defender、0 个 obstacle**，避免把“规避追击”和“障碍绕行”混在一个 benchmark 里
- 用于验证面对追击时的任务鲁棒性

### Benchmark 设计约束

每个 benchmark 场景都应：

- 使用命名 `scenario_id`
- 具有固定种子集合
- 在 V0.3 第一阶段只要求一个默认难度级别，后续版本再扩展难度分层
- 具有单独配置或统一生成规则
- 在 policy 对比时，所有 policy 必须使用**同一场景配置、同一 seed 集合、同一 episode budget**

建议 V0.3 默认 benchmark seed 集合先冻结为：

```text
[0, 1, 2, 3, 4]
```

---

## 5.4 统一 rollout / evaluation 入口

V0.3 建议新增统一评测入口，例如：

- `run_single_episode(policy, env, seed)`
- `evaluate_policy(policy, config, seeds)`

这些入口的职责：

- 在给定配置与种子集合下执行 rollout
- 收集统一字段的结果
- 输出结构化评测结果

并建议明确：

- `run_single_episode(...)` 内部应负责调用 `policy.reset(seed=seed)`
- `evaluate_policy(...)` 的输入 policy 必须实现统一 `AttackerPolicy` 接口
- evaluator 只评测动作级接口，不直接识别 APF / RL / MPC 等具体方法类型

### 单回合输出字段

至少应包含：

- `policy_name`
- `policy_type`
- `policy_config_name`
- `scenario_id`
- `seed`
- `terminated`
- `truncated`
- `termination_reason`
- `is_success`
- `episode_length`
- `return`
- `min_goal_distance`
- `min_defender_distance`
- `min_obstacle_clearance`
- `final_goal_distance`

### 聚合输出字段

除单回合结果外，V0.3 benchmark 至少应输出一份 aggregate summary，包含：

- `policy_name`
- `scenario_id`
- `num_episodes`
- `success_rate`
- `goal_reached_rate`
- `collision_rate`
- `capture_rate`
- `out_of_bounds_rate`
- `time_limit_rate`
- `mean_return`
- `std_return`
- `mean_episode_length`
- `std_episode_length`
- `mean_min_goal_distance`
- `mean_final_goal_distance`

---

## 5.5 结果记录与分析基础

V0.3 不要求复杂 dashboard，但至少要有统一结果落盘格式。

建议使用：

- `json` 或 `jsonl` 保存每回合 summary
- 可选汇总为 `csv`

并建议冻结：

- 单回合结果与 aggregate summary 分开保存
- 文件中必须记录 `policy_name`、`policy_config_name`、`scenario_id`、seed 集合摘要
- benchmark 对比结果应可在不依赖代码上下文的情况下被外部脚本直接读取

V0.3 的目标不是做前端，而是保证后续做对比图表时数据来源稳定一致。

---

## 6. 目录与模块增量设计

推荐新增如下结构：

```text
project_root/
├─ docs/
│  ├─ DevDocV0.2.md
│  ├─ DevDocV0.3.md
│  ├─ timeline.md
│  └─ ...
├─ src/
│  └─ usv_sim/
│     ├─ policies/
│     │  ├─ attacker_goal_baseline.py
│     │  ├─ attacker_apf_baseline.py
│     │  └─ attacker_heading_baseline.py
│     ├─ benchmark/
│     │  ├─ runner.py
│     │  ├─ evaluator.py
│     │  └─ metrics.py
│     ├─ scenarios/
│     │  └─ generator.py
│     └─ ...
├─ configs/
│  ├─ v0_3_goal_only.yaml
│  ├─ v0_3_obstacle_only.yaml
│  └─ v0_3_defender_pressure.yaml
├─ demos/
│  ├─ run_attacker_baseline_demo.py
│  └─ run_benchmark_demo.py
└─ tests/
   ├─ unit/
   ├─ integration/
   └─ smoke/
```

---

## 7. 配置系统在 V0.3 的扩展建议

### 7.1 attacker 方法配置扩展

V0.3 需要开始支持多种 attacker baseline，因此建议从单个：

- `attacker_baseline`

逐步扩展为更清晰的 attacker policy 配置体系，例如：

```yaml
attacker_policy:
  type: goal_seeking
```

并对不同类型策略增加对应参数块：

```yaml
attacker_goal_baseline:
  surge_nominal: 0.8
  surge_turning: 0.3
  ...

attacker_apf_baseline:
  attractive_gain: 1.0
  obstacle_repulsive_gain: 3.0
  defender_repulsive_gain: 4.0
  boundary_repulsive_gain: 2.0
  influence_radius: 12.0
  surge_nominal: 0.7
  surge_turning: 0.25
```

V0.3 允许保守过渡：

- `attacker_policy` 作为 **V0.3 的 canonical 配置入口**
- 继续兼容 `attacker_baseline`，但仅作为过渡兼容字段

冻结建议：

- 若 `attacker_policy` 与 `attacker_baseline` 同时存在，则 **`attacker_policy` 优先**
- 所有新的 V0.3 benchmark 配置文件只应使用 `attacker_policy`
- `attacker_baseline` 不再作为 V0.3 新功能的首选配置入口

### 7.2 benchmark 配置

建议每个 benchmark 场景拥有单独配置文件，或者一个统一 benchmark config：

```yaml
benchmark:
  name: obstacle_only
  seeds: [0, 1, 2, 3, 4]
  max_episodes: 5
```

并建议明确：

- `max_episodes` 与 `seeds` 至少在 V0.3 第一阶段保持一致，即默认 `max_episodes == len(seeds)`
- 不建议在同一 benchmark 里对不同 policy 使用不同 seed 子集

---

## 8. 测试体系在 V0.3 的新增要求

V0.3 的测试重点应转向“多方法一致性”和“benchmark 结果稳定性”。

### 8.1 单元测试新增重点

建议新增：

- `test_attacker_apf_baseline.py`
- `test_attacker_heading_baseline.py`
- `test_benchmark_metrics.py`

至少覆盖：

- APF 势场合成方向是否正确
- 不同 threat source 的排斥项是否可控
- benchmark 指标计算是否稳定
- `AttackerPolicy.reset(seed=...)` 在统一 runner 中被正确调用

### 8.2 集成测试新增重点

建议新增：

- `test_benchmark_runner.py`
- `test_policy_evaluator.py`
- `test_goal_vs_apf_rollout.py`

至少覆盖：

- 不同 policy 在统一入口下都可运行
- benchmark 输出字段完整一致
- 同场景同种子下结果可复现
- 不同 policy 对比时使用的是同一 benchmark config 与同一 seed 集合

### 8.3 smoke test 新要求

V0.3 至少保留三类 smoke：

1. V0.1 常数动作 smoke
2. V0.2 goal baseline smoke
3. V0.3 APF baseline smoke

---

## 9. 推荐开发顺序

V0.3 推荐按以下顺序推进：

1. **统一 attacker policy 接口与配置结构**
2. **实现 APF baseline**
3. **实现 heading-hold baseline**
4. **建立 benchmark 场景配置**
5. **实现 runner / evaluator / metrics**
6. **补齐 unit / integration / smoke tests**
7. **补 benchmark demo 与结果落盘能力**

这样可以保证：

- 先把接口层稳定下来
- 再往上叠方法
- 最后再叠统一评测与记录系统

---

## 10. V0.3 第一批 TODO

| ID | 任务 | 输出 | 验收标准 |
|---|---|---|---|
| T301 | 统一 attacker policy 接口 | `policies/` 接口收敛 | 多方法可共享同一 rollout 入口 |
| T302 | 实现 APF baseline | `attacker_apf_baseline.py` | 在 B302 固定 seeds 上可完成全部 rollout，并相对 goal baseline 产生更低的 `obstacle_collision_rate` 或更大的 `mean_min_obstacle_clearance` |
| T303 | 实现 heading-hold baseline | `attacker_heading_baseline.py` | 在 `baseline_validation` 与 B301 固定 seeds 上可复现运行，并成功到达目标 |
| T304 | 建立 benchmark 场景配置 | `configs/v0_3_*.yaml` | 至少三类 benchmark 场景 |
| T305 | 实现统一 runner/evaluator | `benchmark/` 模块 | 可批量评测多个 seed |
| T306 | 统一结果记录字段 | metrics / summary | 各 policy 输出字段一致 |
| T307 | 补 baseline 与 benchmark 单测 | `tests/unit/` | 方法与指标契约可回归 |
| T308 | 补 benchmark 集成测试 | `tests/integration/` | rollout / evaluation 稳定 |
| T309 | 增加 benchmark smoke 与 demo | `tests/smoke/` + `demos/` | APF baseline 可直接演示 |

---

## 11. V0.3 验收标准

### 11.1 功能验收

V0.3 完成时，至少应满足：

- 统一比较集合中至少包含三类 attacker 方法：V0.2 `goal baseline`、V0.3 `APF baseline`、V0.3 `heading-hold baseline`
- 存在至少三类 benchmark 场景
- 存在统一 rollout / evaluation 入口
- 存在统一结果记录结构

### 11.2 语义验收

V0.3 完成时，不得破坏：

- V0.1 的 dynamics / reward / termination / observation 冻结语义
- V0.2 的 render 语义
- V0.2 的 goal baseline 与 baseline_validation 场景

### 11.3 研究可用性验收

V0.3 至少应达到：

1. 开发者可以在统一入口下运行多种 attacker 方法
2. 开发者可以在统一 benchmark 场景下比较不同方法表现
3. 后续引入 RL / MPC / RRT 方法时，已有 classical baseline 可作为正式对比基线

---

## 12. 推荐验收命令

V0.3 完成后建议形成如下入口：

```bash
conda run -n RL python -m pytest tests/unit -q
conda run -n RL python -m pytest tests/integration -q
conda run -n RL python tests/smoke/test_env_smoke.py
conda run -n RL python demos/run_benchmark_demo.py
```

以及类似：

```bash
conda run -n RL python -m usv_sim.benchmark.runner --config configs/v0_3_obstacle_only.yaml --policy apf
```

---

## 13. 最终结论

V0.3 的目标不是继续补环境基础能力，而是正式进入“**算法基线可比较、实验结果可记录、benchmark 入口可统一**”的新阶段。

如果 V0.2 回答的是：

- 环境能不能看见？
- baseline 能不能跑起来？

那么 V0.3 回答的就是：

- 不同 classical 方法谁更合适？
- 不同 benchmark 场景下表现如何？
- 后续更先进方法应该和什么基线进行比较？

因此，V0.3 是这个平台从“研究原型”走向“算法验证平台”的关键一步。
