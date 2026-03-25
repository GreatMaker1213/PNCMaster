# DevDocV0.5

> 本文档是 USV Sim 项目的 **V0.5 最终开发文档**。
>
> 它建立在 `docs/devREADEME.md`、`docs/FinalDevDocV0.1.md`、`docs/DevDocV0.2.md`、`docs/DevDocV0.3.md`、`docs/DevDocV0.4.md` 与当前 `V0.4.2` 代码状态基础上，用于定义 **V0.5 的核心目标：梳理清楚当前规划控制链路，并在尽量小改现有代码和架构的前提下接入 controller 层，同时兼容未来端到端方法**。
>
> 本文档以 `docs/DevDocV0.5.md` 的完整实现型结构为主体，并吸收 `docs/DevDocV0.5_cc.md` 中关于“最小扰动、谨慎迁移、不要过早承诺大规模重构”的约束结论。
>
> 若 V0.5 文档与 V0.1~V0.4 文档冲突：
>
> - **未被 V0.5 显式修改的内容，继续继承 V0.1~V0.4**
> - **被 V0.5 显式新增或调整的内容，以本文为准**

---

## 1. V0.5 版本定位

### 1.1 V0.5 核心目标

V0.4 已经具备：

- 稳定的 `gymnasium` 环境闭环
- 统一的 `play.py` / `evaluate.py` 顶层入口
- 多个 classical attacker baseline
- benchmark、结果落盘与自动化测试基础

但当前 attacker 侧仍存在一个关键工程问题：

> 现有方法大多是“规划/引导逻辑 + 简化控制映射”混在一个 policy 里，直接从 observation 输出执行级 action，缺少清晰的 controller 层。

这带来三个问题：

1. 传统规划控制链路没有被显式分层，后续接 APF / waypoint / RRT / MPC 风格方法时不够自然
2. 低层控制逻辑无法复用，多个方法容易各自手写一套“reference -> action”映射
3. 未来端到端 RL / diffusion / flow matching 方法的链路位置不够清楚，容易和 controller 方案相互干扰

因此，V0.5 的目标冻结为：

1. **系统梳理当前 project 的规划控制运行链路**
2. **在不破坏现有 env 接口、`play.py` / `evaluate.py`、benchmark 和测试链路的前提下，接入最小可用 controller 层**
3. **明确 future end-to-end 方法与 classical planner/controller 方法在同一工程骨架中的共存方式**

### 1.2 V0.5 工程意义

V0.5 不追求“再新增一种算法”，而是要把项目从：

- “多个策略都能跑”

推进到：

- “传统规划控制链路更清楚、controller 位置更明确”
- “未来端到端方法仍可直接复用现有 env / play / evaluate / benchmark”

换句话说，V0.5 要解决的是：

- 当前环境、观测、策略、执行器是怎么串起来的？
- controller 应该放在哪一层，才既适合传统规划控制，也不妨碍未来端到端方法？

---

## 2. V0.5 范围与非目标

### 2.1 V0.5 范围

V0.5 范围冻结为以下四类内容：

#### A. 当前链路梳理

把当前 project 中以下链路明确写清楚：

- 环境如何定义
- 环境如何创建
- 场景如何生成
- 观测如何生成
- 观测如何传给 attacker agent
- agent 如何构造策略
- 策略如何根据观测输出动作
- 动作如何传给 simulator / dynamics 执行
- reward / termination / recorder / benchmark 如何复用同一条链路

#### B. 接入最小 controller 层

在 attacker 侧引入一个最小 tracking controller，使：

- 规划/引导层负责输出 reference
- 控制层负责把 reference 收敛为 env action

#### C. 保持现有外部入口稳定

V0.5 必须尽量复用现有：

- `play.py`
- `evaluate.py`
- `create_attacker_policy(...)`
- benchmark runner / evaluator
- 现有自动化测试入口

即：

- 外部使用方式尽量不变
- 现有脚本入口继续可用

#### D. 为 future end-to-end 方法预留位置

明确 future：

- RL direct policy
- diffusion / flow matching direct-action policy
- 或其他 obs-to-action 端到端方法

在链路中的位置，并保证它们可以：

- 继续复用当前 env
- 继续复用当前 `play.py` / `evaluate.py`
- 继续复用当前 benchmark / logging / testing 体系

### 2.2 V0.5 明确不做

V0.5 不做以下内容：

- 不重写 V0.1 的 dynamics / reward / termination / observation 冻结语义
- 不修改 env 原生 action 语义 `[surge_cmd, yaw_cmd]`
- 不把 controller 塞进 `AttackDefenseEnv` 内部
- 不重做 `WorldSimulator` / `Fossen3DOFDynamics` 主时序
- **不承诺 V0.5 第一阶段改造 substep inner-loop controller 调度**
- 不实现完整 RL 训练框架
- 不实现完整 MPC / RRT / CBF 正式算法版本
- 不重做 V0.4 的 `play.py` / `evaluate.py`
- 不重做 V0.3 benchmark 指标定义
- 不引入新的 GUI 或 dashboard

---

## 3. 当前 Project 规划控制链路梳理

这一节是 V0.5 的基础。后续接 controller 时，必须以本节描述作为统一理解。

## 3.1 当前环境如何定义

当前主环境是：

```python
class AttackDefenseEnv(gym.Env):
```

其职责包括：

- 组织 `reset()` / `step()`
- 持有 scenario generator、simulator、reward、termination、observation builder
- 对外暴露固定的 `action_space` 与 `observation_space`

当前 env 原生动作冻结为：

```text
action = [surge_cmd, yaw_cmd]
```

其中：

- `surge_cmd`：归一化纵向推进输入
- `yaw_cmd`：归一化偏航输入

这一语义来自 V0.1，V0.5 不改。

## 3.2 当前环境如何创建

当前正式入口链路为：

```text
play.py / evaluate.py
    -> load_config(...)
    -> AttackDefenseEnv(cfg=...)
```

在 env 初始化过程中，会装配：

- `ScenarioGenerator`
- `Fossen3DOFDynamics`
- `PurePursuitDefenderPolicy`
- `WorldSimulator`
- `ObservationBuilder`
- `AttackDefenseReward`
- `TerminationChecker`
- `RolloutRecorder`

因此当前 env 本质上是：

> 一个已经组装好的任务闭环容器。

## 3.3 当前场景如何生成

当前 reset 时的主链路为：

```text
env.reset(seed)
    -> ScenarioGenerator.generate(seed)
    -> WorldState
```

`WorldState` 继续是：

- 真值唯一来源
- observation、reward、termination 的共同输入基础

V0.5 不改这一点。

## 3.4 当前观测如何产生

当前 observation 生成链路是：

```text
WorldState
    -> VisibilityFilter.select(world)
    -> ObservationBuilder.build(world)
    -> obs: dict[str, np.ndarray]
```

其中：

- `VisibilityFilter` 负责从真值中筛出 attacker 当前可见的 defender / obstacle
- `ObservationBuilder` 负责把这些信息编码成固定 shape observation

当前 observation 默认包括：

- `ego`
- `goal`
- `boundary`
- `defenders`
- `defenders_mask`
- `obstacles`
- `obstacles_mask`

## 3.5 当前观测如何传给 attacker agent

当前 attacker 侧正式运行链路为：

```text
play.py / benchmark runner
    -> create_attacker_policy(cfg, policy_type)
    -> policy.reset(seed=...)
    -> policy.act(obs)
```

也就是说，外部入口只知道：

- 有一个 `AttackerPolicy`
- 它接收 observation
- 它输出 env action

当前统一动作级接口是：

```python
class AttackerPolicy:
    def reset(self, *, seed: int | None = None) -> None: ...
    def act(self, obs: dict[str, np.ndarray]) -> np.ndarray: ...
```

## 3.6 当前 attacker policy 如何创建

当前策略由 factory 创建：

```text
create_attacker_policy(cfg, policy_type)
```

当前公开支持的策略类型主要包括：

- `goal_seeking`
- `apf`
- `heading_hold`

这些策略目前都是：

> 直接从 observation 出发，内部自己完成“任务/引导逻辑 + 简化控制映射”，最后直接输出 env action。

## 3.7 当前动作如何进入执行器

当前 attacker 动作执行链路为：

```text
policy.act(obs)
    -> env.step(action)
    -> WorldSimulator.step(world, attacker_action)
    -> Fossen3DOFDynamics.step(state, action, dt)
```

在 `Fossen3DOFDynamics.step(...)` 中，会完成：

1. 对归一化动作裁剪
2. 将 `surge_cmd / yaw_cmd` 映射到 `tau_u / tau_r`
3. 按 V0.1 冻结动力学方程推进状态

因此，当前所谓“执行器”本质上是：

- env action 到动力学输入的映射
- 再加 `Fossen3DOFDynamics` 的状态推进

## 3.8 当前 reward / termination / recorder 如何复用同一动作链

当前 `env.step(action)` 之后，统一继续走：

```text
WorldSimulator.step(...)
    -> StepEvents
    -> TerminationChecker.check(...)
    -> AttackDefenseReward.compute(...)
    -> RolloutRecorder.record_step(...)
```

也就是说：

- reward、termination、logging 都依赖“最终实际生效的 env action 及其推进结果”
- 这也是为什么 controller 不应插到 env 内部的原因之一

## 3.9 当前 play / evaluate / benchmark 如何复用同一条链

当前外部入口复用关系已经比较稳定：

### `play.py`

用于：

- 单回合
- 可视化
- 快速观察行为

### `evaluate.py`

用于：

- 多回合
- 无渲染
- 结果落盘

### benchmark runner / evaluator

用于：

- 固定 seeds 批量 rollout
- 聚合指标输出

它们共同依赖的 attacker 侧契约仍然是：

```text
AttackerPolicy.reset(...)
AttackerPolicy.act(obs)
```

这条链路在 V0.5 中必须保持。

## 3.10 当前架构的主要问题

当前架构在工程上可运行，但在规划控制分层上存在三个问题：

### A. 规划层与控制层没有显式边界

当前 `goal_seeking`、`apf` 等方法在一个类里同时完成：

- 几何推理 / 任务引导
- 参考量构造
- 低层动作映射

这不利于传统规划控制扩展。

### B. 控制逻辑不可复用

如果未来要接：

- APF
- waypoint follower
- RRT path follower
- diffusion 轨迹跟踪

当前结构下容易各写各的“reference -> action”映射。

### C. 未来端到端方法位置不清晰

如果未来 RL 直接根据 observation 输出低层动作，那么它其实不需要 controller。

因此必须明确：

- controller 是一种 **可插拔中间层**
- 不是 env 的固定组成部分

---

## 4. V0.5 核心设计结论

这一节是 V0.5 最关键的冻结内容。

## 4.1 controller 的插入位置

V0.5 冻结结论为：

> controller 的最安全、最小扰动插入点是 `AttackerPolicy` / `policies.factory` 一层，而不是 `AttackDefenseEnv`、`WorldSimulator` 或 `Fossen3DOFDynamics` 内部。

也就是说，controller 应位于：

```text
obs
    -> guidance / planner / policy
    -> controller
    -> env action
    -> env.step(action)
```

而不是：

```text
obs
    -> env
    -> 内部 controller
    -> env action
```

## 4.2 对 env 保持不变的部分

V0.5 明确冻结以下内容不变：

- env 原生 action 仍为 `[surge_cmd, yaw_cmd]`
- `AttackDefenseEnv.step(action)` 仍只接收执行级动作
- `WorldSimulator.step(...)` 不因 controller 接入而改变主语义
- `Fossen3DOFDynamics.step(...)` 不因 controller 接入而改变主语义
- reward / termination / recorder 仍然以 env action 后的世界推进结果为准

## 4.3 对 play/evaluate/benchmark 保持不变的部分

V0.5 明确冻结以下对外契约不变：

- `play.py` 仍通过 `create_attacker_policy(...)` 获取策略
- `evaluate.py` 仍通过统一 policy factory 获取策略
- benchmark runner / evaluator 仍以 `AttackerPolicy.reset/act` 为唯一 attacker 接口

即：

- **controller 的引入不能要求外部脚本新增新的调用分支**
- **controller 细节必须被封装在 strategy / adapter 内部**

## 4.4 两类 attacker 方法的统一外部契约

V0.5 要求 attacker 侧支持两类方法，但它们对外都统一为：

```python
class AttackerPolicy:
    def reset(self, *, seed: int | None = None) -> None: ...
    def act(self, obs: dict[str, np.ndarray]) -> np.ndarray: ...
```

### A. classical stack

传统规划控制类方法走：

```text
obs
    -> planner / guidance
    -> reference
    -> controller
    -> env action
```

### B. end-to-end stack

端到端方法走：

```text
obs
    -> direct-action policy
    -> env action
```

这两类方法对外都仍表现为一个 `AttackerPolicy`。

---

## 5. V0.5 总体原则

### 5.1 原则 A：env 原生接口不变

V0.5 继续冻结：

- env 原生动作仍为 `[surge_cmd, yaw_cmd]`
- `AttackDefenseEnv.step(action)` 仍只接收执行级动作
- dynamics / simulator / reward / termination 不因 controller 接入而改语义

### 5.2 原则 B：`AttackerPolicy` 继续作为唯一对外接口

无论方法内部是否带 controller，外部都只看见：

```python
policy.reset(seed=...)
policy.act(obs) -> action
```

V0.5 不改变这一点。

### 5.3 原则 C：controller 在策略内部组合，不进入 env

controller 的正确位置是：

```text
Guidance / Planner
    -> Controller
    -> Env Action
```

原因：

- env 应保持算法中立
- future RL 端到端方法不需要被迫经过 controller
- benchmark / play / evaluate 不应关心 controller 实现细节

### 5.4 原则 D：direct-action 与 controller-backed 路径并存

V0.5 必须同时支持：

#### A. 直接动作型方法

例如未来：

- RL direct policy
- end-to-end diffusion action policy

链路为：

```text
obs -> AttackerPolicy -> env action
```

#### B. controller-backed 方法

例如：

- goal guidance
- APF guidance
- future waypoint / path / trajectory planner

链路为：

```text
obs -> Guidance/Reference -> Controller -> env action
```

### 5.5 原则 E：优先最小修改现有代码

V0.5 第一阶段必须优先满足：

- `play.py` 不需要感知 controller 细节
- `evaluate.py` 不需要感知 controller 细节
- `create_attacker_policy(...)` 仍是统一构造入口
- 现有 benchmark / logging / tests 尽量只做增量扩展

### 5.6 原则 F：不强制一次性重写现有所有策略

这是吸收 `DevDocV0.5_cc.md` 后新增的重要保守约束。

V0.5 第一阶段：

- **允许现有 action-level policy 暂时继续存在**
- **不要求一开始就把全部 `goal_seeking / apf / heading_hold` 完全拆成 guidance + controller**

更推荐的方式是：

- 先引入 controller 相关抽象
- 再渐进迁移一到两个策略
- 其余策略保留兼容壳，避免大规模一次性重构

### 5.7 原则 G：V0.5 第一阶段不承诺 inner-loop controller 改造

V0.5 明确不把以下内容作为第一阶段必做项：

- 在 `sim_substeps` 内部引入更高频 controller 更新
- 在 `WorldSimulator` 内部重做 attacker / defender 决策频率
- 在 dynamics/simulator 层引入更复杂执行器状态

V0.5 第一阶段只处理：

- policy 层 / adapter 层 / controller 层的组织关系

---

## 6. V0.5 建议抽象层次

## 6.1 对外总链路

V0.5 后，对外仍保持：

```text
play.py / evaluate.py / benchmark runner
    -> create_attacker_policy(...)
    -> AttackerPolicy.reset(...)
    -> AttackerPolicy.act(obs)
    -> env.step(action)
```

## 6.2 Guidance / Reference 层

V0.5 建议新增一个参考级接口，用于表达“规划层输出 reference，而不是直接输出执行器动作”：

```python
class GuidancePolicy:
    def reset(self, *, seed: int | None = None) -> None: ...
    def plan(self, obs: dict[str, np.ndarray]) -> HeadingSpeedReference: ...
```

这里优先使用 `GuidancePolicy` 命名，而不是 `Planner`，因为 V0.5 首批要承接的更像：

- goal guidance
- APF guidance

而不是完整全局 planner。

## 6.3 最小 reference 结构

V0.5 推荐冻结第一个最小参考量结构为：

```python
@dataclass(frozen=True)
class HeadingSpeedReference:
    desired_heading_error: float
    desired_surge_speed: float
```

字段语义冻结为：

- `desired_heading_error`
  - attacker ego frame 下的期望航向误差
  - 单位 `rad`
  - 规范到 `(-pi, pi]`

- `desired_surge_speed`
  - 期望 surge 速度
  - 单位 `m/s`
  - 非归一化物理量

这套 reference 的选择原因是：

- 足以覆盖当前 `goal_seeking` / `apf`
- 能自然映射到当前 env action
- 比 waypoint / trajectory 更小、更适合作为第一阶段落地点

## 6.4 TrackingController 层

V0.5 新增最小控制器接口：

```python
class TrackingController:
    def reset(self, *, seed: int | None = None) -> None: ...
    def act(
        self,
        obs: dict[str, np.ndarray],
        reference: HeadingSpeedReference,
    ) -> np.ndarray: ...
```

其职责冻结为：

- 输入 observation 与 reference
- 输出 env 原生动作 `[surge_cmd, yaw_cmd]`

controller 不进入 env，而是策略内部组合对象。

## 6.5 Action-level adapter / AttackerPolicy 层

V0.5 推荐新增一个组合式策略壳：

```python
class ControllerBackedAttackerPolicy(AttackerPolicy):
    def __init__(self, guidance: GuidancePolicy, controller: TrackingController) -> None: ...
```

其内部执行流程冻结为：

```text
reset(seed)
    -> guidance.reset(seed)
    -> controller.reset(seed)

act(obs)
    -> reference = guidance.plan(obs)
    -> action = controller.act(obs, reference)
    -> return action
```

这样：

- 外部仍然只看见 `AttackerPolicy`
- 内部实现了明确的“规划层 / 控制层”分离

---

## 7. V0.5 最小 controller 语义

## 7.1 推荐的首个 controller

V0.5 推荐引入：

- `HeadingSpeedTrackingController`

它是一个最小 tracking controller，用来把：

- 期望航向误差
- 期望 surge 速度

转换成：

- `surge_cmd`
- `yaw_cmd`

## 7.2 最小数学语义

给定 observation：

```text
ego = [u, v, r, cos_psi, sin_psi, speed_norm]
```

给定参考量：

```text
reference = [desired_heading_error, desired_surge_speed]
```

V0.5 建议 controller 最小公式冻结为：

### yaw 通道

```text
yaw_cmd = clip(
    k_heading * desired_heading_error / pi
    - k_yaw_rate * r,
    -1,
    1,
)
```

### surge 通道

```text
surge_cmd = clip(
    k_surge * (desired_surge_speed - u),
    -1,
    1,
)
```

说明：

- `u` 来自 observation 中 attacker 当前 surge 速度
- `r` 来自 observation 中 attacker 当前 yaw rate
- controller 输出仍是归一化 env action

## 7.3 为什么 controller 不直接输出物理推力

因为 V0.1 已冻结：

- env 外部动作语义是归一化 `[surge_cmd, yaw_cmd]`

V0.5 不应为 controller 再起一套并行动作协议。正确做法是：

- controller 输出 env action
- dynamics 继续负责 env action 到物理输入的映射

---

## 8. 对现有策略的兼容迁移口径

这是 V0.5 文档相对上一版最重要的保守修订之一。

## 8.1 总体迁移原则

V0.5 第一阶段不要求：

- 一次性重写全部现有 attacker policy
- 一次性把全部 baseline 强制改成 guidance + controller

V0.5 更推荐：

1. 先定义 controller 相关抽象
2. 先完成一条最小可用 controller-backed 路径
3. 再渐进式迁移现有 baseline

## 8.2 `goal_seeking`

V0.5 推荐目标形态是：

```text
GoalSeekingGuidance
    + HeadingSpeedTrackingController
    -> ControllerBackedAttackerPolicy
```

但第一阶段允许两种实现策略：

### A. 保守策略

- 保留现有 `attacker_goal_baseline.py`
- 新增 guidance/controller 版本作为并行实现
- factory 先只在受控配置下切换到新链路

### B. 渐进替换策略

- 在不改外部 `policy_type="goal_seeking"` 的前提下
- 让内部实现逐步转向 guidance + controller

V0.5 推荐优先采用：

- **渐进替换，但保留回退空间**

## 8.3 `apf`

V0.5 推荐目标形态是：

```text
APFGuidance
    + HeadingSpeedTrackingController
    -> ControllerBackedAttackerPolicy
```

但同样不强制一次性彻底重写。

V0.5 第一阶段更保守的要求是：

- 至少让 APF 在架构上具备“拆成 guidance + controller”的明确方向
- 允许保留旧 action-level 逻辑作为过渡实现

## 8.4 `heading_hold`

当前 `heading_hold` 在概念上更接近 controller 而不是 planner。

因此 V0.5 推荐：

- 将其核心控制逻辑沉淀到 `HeadingSpeedTrackingController`
- 但保留 `policy_type="heading_hold"` 作为兼容别名

兼容别名在第一阶段不必追求极致纯粹，只需保证：

- 外部入口不变
- 行为大体兼容
- 不因 controller 重组破坏现有 benchmark / play / evaluate

## 8.5 第一阶段最小落地建议

从“立即可开发”的角度，V0.5 最保守的落地建议是：

1. 新增 controller 抽象与最小实现
2. 新增 reference / guidance 抽象与最小实现
3. 先让 **一条** controller-backed goal 路径跑通
4. APF 做第二条迁移对象
5. `heading_hold` 先以兼容方式保留，不强求第一批彻底重构

---

## 9. 与 future RL / diffusion / flow matching 的兼容策略

## 9.1 future end-to-end 方法的链路位置

V0.5 必须明确：

未来端到端 RL 不应被迫经过 controller。

它的链路应为：

```text
obs
    -> RLDirectActionPolicy
    -> env action
```

也就是说：

- controller 是 **可选中间层**
- 不是所有方法都必须经过 controller

## 9.2 V0.5 后推荐的统一抽象链

V0.5 建议 attacker 侧方法统一抽象为：

```text
Observation
    -> Guidance / Planner / Policy
    -> Reference (optional)
    -> Controller (optional)
    -> Env Action
    -> Dynamics Executor
```

其中：

- direct-action 方法走“无 Reference / 无 Controller”分支
- traditional planner/control 方法走“Reference + Controller”分支

## 9.3 safety filter 的未来位置

V0.5 暂不实现 safety filter，但要为 future CBF / shield 保留位置：

```text
Reference / Direct Action
    -> Controller (optional)
    -> Safety Filter (future)
    -> Env Action
```

这样 future：

- CBF
- shielded RL
- 安全投影层

都不需要回头重构 env。

---

## 10. 配置系统在 V0.5 的建议

## 10.1 保留 `attacker_policy.type` 作为外部主入口

V0.5 不推翻 V0.3 / V0.4 已经形成的使用方式。

继续保留：

```yaml
attacker_policy:
  type: goal_seeking | apf | heading_hold
```

外部 `play.py` / `evaluate.py` 仍使用：

- `config.attacker_policy.type`
- 或 CLI `--policy` 覆盖

## 10.2 新增 `tracking_controller` 配置块

V0.5 建议新增：

```yaml
tracking_controller:
  type: heading_speed
  heading_gain: 1.5
  yaw_rate_damping: 0.2
  surge_gain: 0.8
  desired_speed_max: 3.0
```

说明：

- `heading_gain`：航向误差比例增益
- `yaw_rate_damping`：偏航角速度阻尼
- `surge_gain`：surge 跟踪增益
- `desired_speed_max`：参考 surge 速度上限

## 10.3 现有 baseline 配置块尽量复用

V0.5 建议尽量复用已有：

- `attacker_goal_baseline`
- `attacker_apf_baseline`
- `attacker_heading_baseline`

但重新解释其角色：

- `attacker_goal_baseline`：goal guidance 参数
- `attacker_apf_baseline`：APF guidance 参数
- `attacker_heading_baseline`：heading-hold 兼容 preset 参数

V0.5 优先通过：

- **重新组织职责**

而不是：

- **大规模重命名配置**

来完成升级。

---

## 11. 目录与模块增量设计

V0.5 建议新增如下结构：

```text
project_root/
├─ src/
│  └─ usv_sim/
│     ├─ controllers/
│     │  ├─ base.py
│     │  └─ heading_speed.py
│     ├─ guidance/
│     │  ├─ base.py
│     │  ├─ reference.py
│     │  ├─ goal_guidance.py
│     │  └─ apf_guidance.py
│     ├─ policies/
│     │  ├─ base.py
│     │  ├─ controller_backed.py
│     │  ├─ attacker_goal_baseline.py
│     │  ├─ attacker_apf_baseline.py
│     │  ├─ attacker_heading_baseline.py
│     │  └─ factory.py
│     └─ ...
└─ docs/
   └─ DevDocV0.5.md
```

### 说明

- `controllers/`：新增，承接“reference -> env action”
- `guidance/`：新增，承接“obs -> reference”
- `policies/controller_backed.py`：新增，承接对外统一 `AttackerPolicy`
- `play.py` / `evaluate.py`：V0.5 原则上只允许极小或零修改

---

## 12. 测试与验收设计

## 12.1 单元测试建议新增

建议新增：

- `tests/unit/test_heading_speed_reference.py`
- `tests/unit/test_heading_speed_controller.py`
- `tests/unit/test_goal_guidance.py`
- `tests/unit/test_apf_guidance.py`
- `tests/unit/test_controller_backed_policy.py`

覆盖重点：

- reference 数据结构与单位语义
- controller 输出 action 的 shape / dtype / range
- goal guidance / APF guidance 输出 reference 合法
- controller-backed policy 的 `reset/act` 组合逻辑正确

## 12.2 集成测试建议新增

建议新增：

- `tests/integration/test_controller_backed_goal_rollout.py`
- `tests/integration/test_controller_backed_apf_rollout.py`
- `tests/integration/test_play_entrypoint_controller_compat.py`
- `tests/integration/test_evaluate_entrypoint_controller_compat.py`

覆盖重点：

- `play.py` 不需要感知 controller 细节也能跑 controller-backed policy
- `evaluate.py` 不需要感知 controller 细节也能跑 controller-backed policy
- V0.4 的正式入口在 V0.5 后仍可用

## 12.3 面向 future end-to-end 方法的回归保护

虽然 V0.5 不正式实现 RL direct policy，但建议新增一个最小 stub / mock 测试，验证：

```text
DirectActionPolicy
    -> AttackerPolicy.act(obs)
    -> env action
```

仍然能走通现有 runner / evaluator。

这样可以提前保护：

- controller 不是强制路径

这一关键架构原则。

---

## 13. 推荐开发顺序

1. **先把当前链路写清楚并冻结**
2. **新增最小 reference 数据结构**
3. **新增 `TrackingController` 与 `HeadingSpeedTrackingController`**
4. **新增 `GuidancePolicy` 与 goal guidance**
5. **先跑通一条 controller-backed goal 路径**
6. **再扩展到 APF guidance + controller**
7. **在 factory 中完成最小兼容迁移**
8. **补 unit / integration tests**
9. **最后再增加 direct-action stub 回归保护**

这个顺序比上一版更保守，原因是：

- 先梳理链路，后实施最小改动
- 先只让一条新链跑通，再迁移更多策略
- 先保证外部入口稳定，再推进更多架构纯化

---

## 14. V0.5 第一批 TODO

| ID | 任务 | 输出 | 验收标准 |
|---|---|---|---|
| T501 | 梳理并冻结当前链路 | `docs/DevDocV0.5.md` | 明确 env / obs / policy / action / executor 链路 |
| T502 | 实现最小 reference 数据结构 | `guidance/reference.py` | `HeadingSpeedReference` 单位与字段清晰 |
| T503 | 实现 tracking controller 接口 | `controllers/base.py` | controller 边界明确 |
| T504 | 实现 `HeadingSpeedTrackingController` | `controllers/heading_speed.py` | reference 能稳定映射为 env action |
| T505 | 实现 goal guidance 原型 | `guidance/goal_guidance.py` | 一条 controller-backed goal 路径跑通 |
| T506 | 实现组合式 attacker policy | `policies/controller_backed.py` | 外部仍只见 `AttackerPolicy` |
| T507 | 最小兼容迁移 factory | `policies/factory.py` | `play.py` / `evaluate.py` 调用方式不变 |
| T508 | 扩展到 APF guidance | `guidance/apf_guidance.py` | APF 具备 guidance + controller 路径 |
| T509 | 补 controller 相关单测 | `tests/unit/` | controller / guidance / composition 可回归 |
| T510 | 补入口兼容集成测试 | `tests/integration/` | V0.4 正式入口在 V0.5 后保持可用 |
| T511 | 预留 direct-action 路径约束 | 文档 + stub test | future RL 可不经过 controller |

---

## 15. V0.5 验收标准

### 15.1 功能验收

V0.5 完成时至少满足：

- 当前 project 链路在文档中被清晰梳理
- attacker 侧存在最小 controller 层
- 至少一条 controller-backed goal 路径可运行
- APF 在架构上具备迁移到 guidance + controller 的明确路径
- `play.py` 与 `evaluate.py` 的外部用法不需要重写

### 15.2 架构验收

V0.5 完成时必须满足：

- env 原生 action 语义不变
- `AttackerPolicy` 继续作为唯一对外动作级接口
- controller 不进入 env 内部
- direct-action 路径与 controller-backed 路径可共存
- V0.5 第一阶段不要求重做 simulator inner-loop

### 15.3 面向 future 方法的可扩展性验收

V0.5 至少应达到：

1. future RL direct policy 可直接复用当前 play/evaluate/evaluator
2. future waypoint/path/trajectory 类方法可通过 reference + controller 接入
3. future safety filter / CBF 可放在 controller 之后、env 之前，而无需重构 env

---

## 16. 推荐验收命令

V0.5 完成后建议形成如下回归入口：

```bash
conda run -n RL python play.py --config configs/v0_3_goal_only.yaml --policy goal_seeking --seed 0
conda run -n RL python play.py --config configs/v0_3_obstacle_only.yaml --policy apf --seed 1

conda run -n RL python evaluate.py --config configs/v0_3_goal_only.yaml --policy goal_seeking --output-dir outputs/v0_5_goal_eval
conda run -n RL python evaluate.py --config configs/v0_3_obstacle_only.yaml --policy apf --output-dir outputs/v0_5_apf_eval

conda run -n RL python -m pytest tests/unit tests/integration -q
```

---

## 17. 最终结论

V0.5 的关键不是“再加一个 planner”，而是：

- **把当前链路说清楚**
- **把 controller 放到正确的位置**
- **让传统规划控制与 future 端到端方法都能复用同一套项目骨架**

如果说：

- V0.3 解决的是“多 baseline 如何统一比较”
- V0.4 解决的是“如何统一正式运行与评测”

那么 V0.5 要解决的就是：

- **规划如何输出 reference**
- **controller 如何把 reference 变成 env action**
- **future 端到端方法如何在不经过 controller 的前提下继续复用现有 env、runner、benchmark 与脚本入口**

只要 V0.5 严格按本文执行，USV Sim 就会从“多策略可运行平台”进一步升级为“**规划/控制/端到端方法可共存的统一验证平台**”。
