# USV Sim v0.1 Implementation Spec

> 本文档是 `devREADEME.md` 的 **v0.1 可编码收敛版**。
> 它不替代主文档的长期架构视角，而是给出一版能够直接指导编码的约束。
> 若本文档与 [devREADEME.md](devREADEME.md) 存在冲突，**以本文档作为 v0.1 编码依据**。

---

## 1. v0.1 目标与边界

### 1.1 v0.1 目标

v0.1 的目标不是做成完整研究平台，而是做出一个 **最小可用、可复现、可扩展、能继续往上长的仿真内核**。

v0.1 必须交付以下能力：

- 基于 **Fossen 3-DOF 平面模型** 的真值动力学推进
- 基于 **gymnasium** 的标准环境接口
- 1 个攻击艇（attacker）
- 0~N 个防守艇（defender），但第一批验收至少覆盖 `0` 和 `1` 两种情况
- 固定圆形障碍物
- 矩形边界海域
- 圆形目标区域
- 基于几何距离的有限感知
- 固定 shape 的 observation schema
- 冻结的 env action 定义
- 可复现的场景生成
- 一套最基本 reward / termination / info 语义
- 至少 1 个脚本防守策略
- 至少 1 个 baseline 控制器用于 smoke test

### 1.2 v0.1 明确不做

v0.1 不做以下内容：

- 雷达/声呐原始观测仿真
- 遮挡建模
- 观测噪声与时延
- 6-DOF
- 非圆形障碍物
- 多智能体联合训练框架
- diffusion / flow matching 的训练管线
- 渲染系统的复杂化
- 海流/风浪扰动
- 为某一种算法定制 observation 或 reward

---

## 2. 本轮收敛后的关键决策

这一节直接回应你提出的 6 个问题。

### 2.1 WorldState 只存真值，不做业务逻辑

v0.1 中，`WorldState` 的职责明确冻结为：

- 存储世界真值状态
- 不生成 observation
- 不计算 reward
- 不判定 termination
- 不导出日志
- 不缓存“上一步发生了什么”的业务事件

因此，`WorldState` 是 **data container**，不是 God object。

与之配套的职责拆分如下：

- `ObservationBuilder`：消费 `WorldState`，生成 observation
- `AttackDefenseReward`：消费 `prev_world`、`world`、`events`，计算 reward
- `TerminationChecker`：消费 `world`、`events`，判定终止
- `RolloutRecorder`：消费 `world`、`obs`、`action`、`info`，记录日志
- `WorldSimulator`：负责推进 world，并产生 `StepEvents`

### 2.2 Env Action 在 v0.1 直接冻结

v0.1 的环境动作定义冻结为：

- `action.shape == (2,)`
- `dtype == np.float32`
- `action_space = Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)`
- 语义为 **归一化执行级动作**：
  - `action[0]`: 归一化 surge command
  - `action[1]`: 归一化 yaw moment command

线性映射为：

- `tau_u = action[0] * cfg.action.max_surge_force`
- `tau_r = action[1] * cfg.action.max_yaw_moment`

即，v0.1 的 env action 不是 `[u_ref, psi_ref]`，也不是 waypoint，而是 **直接作用于动力学推进的低层控制输入**。

这样做的原因：

1. 物理语义最清楚
2. 环境内不需要再内嵌一个“默认低层控制器”
3. RL 接口稳定
4. 传统规划/控制算法可以在环境外通过 adapter / tracking controller 转成该动作
5. 为后续 CBF / safety filter 保留清晰插入点

### 2.3 坐标系、单位和角度范围冻结为软件契约

v0.1 不再把这一部分当“注意事项”，而是直接冻结成编码规范。详细内容见 [DevDocV0.1.md](DevDocV0.1.md)。

这里先给出摘要：

- 世界坐标系：二维平面，`x` 向右，`y` 向上
- 航向 `psi = 0` 指向世界系 `+x`
- `psi` 和 `r` 的正方向均为 **逆时针**
- 所有角度统一用 **弧度**
- 角度规范化范围：`(-pi, pi]`
- 速度单位：`m/s`
- 角速度单位：`rad/s`
- 力/力矩单位：`N` / `N·m`
- 体坐标系：`x_b` 向前，`y_b` 向左

### 2.4 Observation schema 在开工前冻结

v0.1 采用 `gymnasium.spaces.Dict`，但不只停留在“用 Dict”，而是冻结 key、shape、dtype、padding、mask、对象顺序规则。

权威版本见 [DevDocV0.1.md](DevDocV0.1.md)。

### 2.5 关键阈值给出默认值

v0.1 直接给默认值，避免 reward / termination 边写边漂。

默认值同样冻结到 [DevDocV0.1.md](DevDocV0.1.md)，包括：

- `goal_radius`
- `capture_radius`
- `attacker_radius`
- `defender_radius`
- `boundary` 越界判据
- `numerical_failure` 判据

### 2.6 配置系统命名收敛

为避免 `src/usv_sim/config/` 和根目录 `configs/` 概念冲突，v0.1 采用以下收敛方案：

- 根目录 `configs/`：只放 YAML 配置文件
- `src/usv_sim/config.py`：只放配置 dataclass/schema 和加载逻辑

**v0.1 不创建 `src/usv_sim/config/` 目录。**

---

## 3. v0.1 目录冻结

```text
project_root/
├─ src/
│  └─ usv_sim/
│     ├─ __init__.py
│     ├─ config.py
│     ├─ core/
│     │  ├─ types.py
│     │  ├─ events.py
│     │  └─ simulator.py
│     ├─ dynamics/
│     │  └─ fossen3dof.py
│     ├─ scenarios/
│     │  └─ generator.py
│     ├─ policies/
│     │  ├─ base.py
│     │  └─ defender_pursuit.py
│     ├─ observation/
│     │  ├─ visibility.py
│     │  └─ builder.py
│     ├─ reward/
│     │  └─ attack_defense_reward.py
│     ├─ termination/
│     │  └─ checker.py
│     ├─ envs/
│     │  └─ attack_defense_env.py
│     └─ logging/
│        └─ rollout.py
├─ configs/
│  └─ v0_1_default.yaml
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  └─ smoke/
├─ devREADEME.md
├─ ImplementationSpecV0.1.md
└─ DevDocV0.1.md
```

说明：

- `core/` 放纯状态结构、事件结构和仿真编排
- `policies/` 放防守艇脚本策略
- `reward/` 和 `termination/` 独立，避免环境主文件过重
- `logging/` 只做数据记录，不参与环境语义

---

## 4. 核心模块接口与类名

这一节是直接面向编码的。

## 4.1 `src/usv_sim/config.py`

职责：

- 定义配置 dataclass
- 从 YAML 加载配置
- 做基础校验

建议类名：

```python
@dataclass(slots=True)
class ActionConfig: ...

@dataclass(slots=True)
class DynamicsConfig: ...

@dataclass(slots=True)
class ScenarioConfig: ...

@dataclass(slots=True)
class ObservationConfig: ...

@dataclass(slots=True)
class RewardConfig: ...

@dataclass(slots=True)
class TerminationConfig: ...

@dataclass(slots=True)
class DefenderPolicyConfig: ...

@dataclass(slots=True)
class EnvConfig: ...

@dataclass(slots=True)
class ProjectConfig: ...


def load_config(path: str | Path) -> ProjectConfig: ...
```

要求：

- `ProjectConfig` 是顶层配置对象
- 所有默认值都能从 `configs/v0_1_default.yaml` 完整加载
- 在这里完成基础合法性校验，而不是运行时再散落检查

---

## 4.2 `src/usv_sim/core/types.py`

职责：

- 只定义真值状态结构
- 不写业务逻辑

建议类名：

```python
@dataclass(slots=True)
class USVState:
    entity_id: int
    x: float
    y: float
    psi: float
    u: float
    v: float
    r: float
    radius: float


@dataclass(slots=True)
class CircularObstacle:
    entity_id: int
    x: float
    y: float
    radius: float


@dataclass(slots=True)
class GoalRegion:
    x: float
    y: float
    radius: float


@dataclass(slots=True)
class RectBoundary:
    xmin: float
    xmax: float
    ymin: float
    ymax: float


@dataclass(slots=True)
class WorldState:
    sim_time: float
    step_count: int
    seed: int
    scenario_id: str
    attacker: USVState
    defenders: list[USVState]
    obstacles: list[CircularObstacle]
    goal: GoalRegion
    boundary: RectBoundary
```

约束：

- `WorldState` 不带 reward / obs / terminated 字段
- `WorldState` 不带事件缓存
- `WorldState` 不带日志缓存
- `WorldState` 只表示当前时刻真值

---

## 4.3 `src/usv_sim/core/events.py`

职责：

- 定义 step 级事件
- 供 reward 和 termination 消费

建议类名：

```python
@dataclass(slots=True)
class StepEvents:
    goal_reached: bool
    captured: bool
    obstacle_collision: bool
    out_of_bounds: bool
    numerical_failure: bool
    min_defender_distance: float
    min_obstacle_clearance: float
    goal_distance: float
```

说明：

- `StepEvents` 不并入 `WorldState`
- `StepEvents` 由 `WorldSimulator` 每步产出

---

## 4.4 `src/usv_sim/dynamics/fossen3dof.py`

职责：

- 给定 USV 当前状态和动作，推进一步
- 不关心 reward / observation / termination

建议类名：

```python
class Fossen3DOFDynamics:
    def __init__(self, cfg: DynamicsConfig, action_cfg: ActionConfig) -> None: ...

    def step(self, state: USVState, action: np.ndarray, dt: float) -> USVState: ...
```

动作约束：

- 输入动作必须是 shape `(2,)`
- 内部先 clip 到 `[-1, 1]`
- 再映射到 `tau_u` 和 `tau_r`

说明：

- `v0.1` 不接受 waypoint / heading reference 作为 env 原生动作
- 若后续需要 `u_ref / psi_ref`，应在环境外层写 controller / adapter

---

## 4.5 `src/usv_sim/scenarios/generator.py`

职责：

- 根据 seed 和配置生成合法初始场景
- 输出初始 `WorldState`

建议类名：

```python
class ScenarioGenerator:
    def __init__(self, cfg: ScenarioConfig, term_cfg: TerminationConfig) -> None: ...

    def generate(self, seed: int) -> WorldState: ...
```

要求：

- 同一 seed 必须可复现
- 障碍、attacker、goal、defender 初始位置不能重叠
- 初始 attacker 不得已处于 goal/capture/collision/out_of_bounds 状态
- obstacle `entity_id` 和 defender `entity_id` 在 episode 内固定

---

## 4.6 `src/usv_sim/policies/base.py`

职责：

- 定义防守艇脚本策略协议

建议接口：

```python
class DefenderPolicy(Protocol):
    def act(self, defender: USVState, world: WorldState) -> np.ndarray: ...
```

约束：

- 输出与 env action 相同：shape `(2,)` 的归一化低层动作
- 这样避免 defender 分支和 attacker 分支使用两套动作语义

---

## 4.7 `src/usv_sim/policies/defender_pursuit.py`

职责：

- 提供 v0.1 默认防守策略

建议类名：

```python
class PurePursuitDefenderPolicy:
    def __init__(self, cfg: DefenderPolicyConfig) -> None: ...

    def act(self, defender: USVState, world: WorldState) -> np.ndarray: ...
```

最低要求：

- 纯追击 attacker
- 输出动作可稳定运行，不出现 NaN
- 先不做复杂避障，撞障碍只记为环境现象，不要求策略很聪明

---

## 4.8 `src/usv_sim/core/simulator.py`

职责：

- 接收 attacker action
- 调用 defender policy
- 执行多个物理 substeps
- 更新整个 world
- 计算 `StepEvents`

建议类名：

```python
class WorldSimulator:
    def __init__(
        self,
        dynamics: Fossen3DOFDynamics,
        defender_policy: DefenderPolicy,
        cfg: ProjectConfig,
    ) -> None: ...

    def step(self, world: WorldState, attacker_action: np.ndarray) -> tuple[WorldState, StepEvents]: ...
```

职责边界：

- `WorldSimulator` 负责“推进世界”
- 不负责 reward composition
- 不负责 observation encoding
- 不直接返回 terminated/truncated

---

## 4.9 `src/usv_sim/observation/visibility.py`

职责：

- 根据感知半径筛选可见对象

建议类名：

```python
@dataclass(slots=True)
class VisibleEntities:
    defenders: list[USVState]
    obstacles: list[CircularObstacle]


class VisibilityFilter:
    def __init__(self, cfg: ObservationConfig) -> None: ...

    def select(self, world: WorldState) -> VisibleEntities: ...
```

v0.1 规则：

- 360°
- 仅按距离判断可见
- 无遮挡
- 无噪声

---

## 4.10 `src/usv_sim/observation/builder.py`

职责：

- 将 `WorldState` 编码成固定 shape 的 observation dict

建议类名：

```python
class ObservationBuilder:
    def __init__(self, cfg: ObservationConfig, env_cfg: EnvConfig) -> None: ...

    @property
    def observation_space(self) -> gym.Space: ...

    def build(self, world: WorldState) -> dict[str, np.ndarray]: ...
```

要求：

- `observation_space` 与真实输出严格一致
- 对象顺序规则固定
- padding 规则固定
- mask 规则固定
- 编码细节以 [DevDocV0.1.md](DevDocV0.1.md) 为准

---

## 4.11 `src/usv_sim/reward/attack_defense_reward.py`

职责：

- 计算 reward 和 reward breakdown

建议类名：

```python
@dataclass(slots=True)
class RewardBreakdown:
    total: float
    progress: float
    goal: float
    capture: float
    collision: float
    boundary: float
    time: float
    control: float


class AttackDefenseReward:
    def __init__(self, cfg: RewardConfig) -> None: ...

    def compute(
        self,
        prev_world: WorldState,
        world: WorldState,
        events: StepEvents,
        attacker_action: np.ndarray,
    ) -> RewardBreakdown: ...
```

约束：

- reward 仅消费 `prev_world`、`world`、`events`、`action`
- 不回写 `WorldState`

---

## 4.12 `src/usv_sim/termination/checker.py`

职责：

- 计算 terminated / truncated / reason / success

建议类名：

```python
@dataclass(slots=True)
class TerminationResult:
    terminated: bool
    truncated: bool
    reason: str
    is_success: bool


class TerminationChecker:
    def __init__(self, cfg: TerminationConfig, env_cfg: EnvConfig) -> None: ...

    def check(self, world: WorldState, events: StepEvents) -> TerminationResult: ...
```

约束：

- 阈值与判据以 [DevDocV0.1.md](DevDocV0.1.md) 为准
- `time_limit` 只能作为 `truncated`

---

## 4.13 `src/usv_sim/logging/rollout.py`

职责：

- 保存 episode/step 数据
- 与环境语义解耦

建议类名：

```python
class RolloutRecorder:
    def reset(self) -> None: ...

    def record_step(
        self,
        world: WorldState,
        obs: dict[str, np.ndarray],
        action: np.ndarray,
        info: dict,
    ) -> None: ...

    def finalize_episode(self) -> dict: ...
```

v0.1 要求：

- 可先做内存版 recorder
- 不要求第一版就写磁盘格式

---

## 4.14 `src/usv_sim/envs/attack_defense_env.py`

职责：

- 组装上述所有模块
- 暴露 gymnasium 标准接口

建议类名：

```python
class AttackDefenseEnv(gym.Env):
    metadata = {"render_modes": [None]}

    def __init__(self, cfg: ProjectConfig) -> None: ...

    def reset(self, *, seed: int | None = None, options: dict | None = None): ...

    def step(self, action: np.ndarray): ...

    def render(self): ...

    def close(self): ...
```

内部持有：

- `ScenarioGenerator`
- `Fossen3DOFDynamics`
- `WorldSimulator`
- `ObservationBuilder`
- `AttackDefenseReward`
- `TerminationChecker`
- `RolloutRecorder`

---

## 5. reset / step 的权威数据流

### 5.1 `reset()`

固定流程：

1. 接收 `seed`
2. 加载/使用已有 `ProjectConfig`
3. `ScenarioGenerator.generate(seed)` 产出初始 `WorldState`
4. `ObservationBuilder.build(world)` 产出 `obs`
5. `RolloutRecorder.reset()`
6. 构造 `info`
7. 返回 `obs, info`

### 5.2 `step(action)`

固定流程：

1. 保存 `prev_world`
2. `WorldSimulator.step(world, attacker_action)` 产出 `next_world, events`
3. `ObservationBuilder.build(next_world)`
4. `AttackDefenseReward.compute(prev_world, next_world, events, action)`
5. `TerminationChecker.check(next_world, events)`
6. 组装 `info`
7. `RolloutRecorder.record_step(...)`
8. 返回五元组

说明：

- `AttackDefenseEnv` 是 orchestrator，不自行做动力学和业务计算
- obs / reward / termination 全部外置模块化

---

## 6. 配置项冻结

以下为 v0.1 第一版必须存在的配置项。

## 6.1 `EnvConfig`

```yaml
env:
  max_episode_steps: 400
  dt_env: 0.20
  sim_substeps: 4
  render_mode: null
```

语义：

- `dt_env`：一次 env step 的决策周期
- `sim_substeps`：每个 env step 的物理积分子步数
- `dt_sim = dt_env / sim_substeps`

## 6.2 `ActionConfig`

```yaml
action:
  max_surge_force: 40.0
  max_yaw_moment: 15.0
```

说明：

- env action 始终是归一化动作
- 这里只定义物理映射尺度

## 6.3 `DynamicsConfig`

```yaml
dynamics:
  m11: 30.0
  m22: 40.0
  m33: 10.0
  d11: 8.0
  d22: 12.0
  d33: 6.0
  u_max_soft: 4.0
  v_max_soft: 2.0
  r_max_soft: 1.2
```

说明：

- `m11/m22/m33`：简化质量/惯量项
- `d11/d22/d33`：简化线性阻尼项
- `*_soft` 仅用于动作/状态限制，不替代 numerical failure hard bound

## 6.4 `ScenarioConfig`

```yaml
scenario:
  scenario_id: default
  boundary:
    xmin: 0.0
    xmax: 100.0
    ymin: 0.0
    ymax: 100.0
  attacker_radius: 1.0
  defender_radius: 1.0
  n_defenders: 1
  n_obstacles: 3
  obstacle_radius_min: 2.0
  obstacle_radius_max: 5.0
  spawn_clearance: 8.0
  goal_clearance: 8.0
```

## 6.5 `ObservationConfig`

```yaml
observation:
  sensing_radius: 35.0
  max_defenders: 4
  max_obstacles: 8
  dtype: float32
```

## 6.6 `RewardConfig`

```yaml
reward:
  progress_weight: 1.0
  goal_reward: 100.0
  capture_penalty: -100.0
  collision_penalty: -100.0
  boundary_penalty: -100.0
  time_penalty: -0.01
  control_l2_weight: -0.001
```

## 6.7 `TerminationConfig`

```yaml
termination:
  goal_radius: 3.0
  capture_radius: 4.0
  hard_u_limit: 8.0
  hard_v_limit: 4.0
  hard_r_limit: 2.5
```

## 6.8 `DefenderPolicyConfig`

```yaml
defender_policy:
  type: pure_pursuit
  surge_gain: 0.8
  heading_gain: 1.2
```

---

## 7. v0.1 观察、奖励、终止的冻结依赖关系

### 7.1 观察依赖

- `ObservationBuilder` 只能读取 `WorldState`
- 不读取 reward 或 termination 中间量
- 不在 observation 中泄漏不可见对象信息

### 7.2 奖励依赖

- `AttackDefenseReward` 可读取：`prev_world`、`world`、`events`、`action`
- 不可依赖“未来状态”
- 不可在 reward 中偷偷使用未暴露给 agent 的非因果信息做 shaping

### 7.3 终止依赖

- `TerminationChecker` 可读取：`world`、`events`
- 终止阈值全部配置化
- `time_limit` 只能是 `truncated`

---

## 8. v0.1 第一批 TODO

下面这批任务的颗粒度，应该能直接用于开始编码。

| ID | 任务 | 输出 | 验收标准 |
|---|---|---|---|
| T01 | 建立项目骨架 | 目录、`__init__.py`、空模块 | import 不报错 |
| T02 | 实现配置系统 | `config.py` + `configs/v0_1_default.yaml` | 配置可加载并通过基础校验 |
| T03 | 实现真值状态 dataclass | `core/types.py` | `WorldState` 不含业务逻辑字段 |
| T04 | 实现 step 事件结构 | `core/events.py` | `StepEvents` 足以支撑 reward/termination |
| T05 | 实现 Fossen 3-DOF 推进 | `dynamics/fossen3dof.py` | 1000 步积分无 NaN，动作裁剪生效 |
| T06 | 实现场景生成器 | `scenarios/generator.py` | 同 seed 可复现，初始状态合法 |
| T07 | 实现防守艇默认策略 | `policies/defender_pursuit.py` | 1 defender 追击 attacker 时可稳定输出动作 |
| T08 | 实现 world simulator | `core/simulator.py` | 能输出 `next_world + events` |
| T09 | 实现 observation builder | `observation/visibility.py` + `builder.py` | 输出与 `observation_space` 完全一致 |
| T10 | 实现 reward 模块 | `reward/attack_defense_reward.py` | 返回 total + breakdown |
| T11 | 实现 termination checker | `termination/checker.py` | 正确区分 terminated / truncated |
| T12 | 实现 gym env | `envs/attack_defense_env.py` | 通过 `gymnasium` env checker |
| T13 | 实现 rollout recorder | `logging/rollout.py` | 能记录 step/episode 摘要 |
| T14 | 写 smoke tests | `tests/smoke/` | 0 defender / 1 defender 两组都可跑完 episode |
| T15 | 写最小 baseline | tracking 或手工策略 | 目标场景下能非随机移动并产生合理 reward |

---

## 9. v0.1 验收标准

v0.1 完成时，至少满足以下条件：

### 9.1 接口正确性

- `AttackDefenseEnv` 通过 gymnasium env checker
- `reset()` 返回 `(obs, info)`
- `step()` 返回 `(obs, reward, terminated, truncated, info)`
- observation 与 action space 完全一致

### 9.2 可复现性

- 相同 seed 生成相同场景
- 相同 seed + 相同动作序列得到相同轨迹

### 9.3 数值稳定性

- 在默认配置下运行 100 个 episode 不出现 NaN/Inf 崩溃
- numerical failure 只在异常情况下触发，不应成为常态

### 9.4 语义稳定性

- Env action 永远是归一化 `[surge_cmd, yaw_moment_cmd]`
- `WorldState` 永远只存真值
- `time_limit` 永远是 `truncated`
- observation slot 顺序在 episode 内稳定

### 9.5 工程边界正确

- 不允许把 reward、termination、observation 逻辑塞回 `WorldState`
- 不允许在环境主文件里复制一份独立物理逻辑
- 不允许再引入 `src/usv_sim/config/` 目录

---

## 10. 推荐的编码顺序

建议严格按以下顺序推进：

1. `config.py`
2. `core/types.py`
3. `core/events.py`
4. `dynamics/fossen3dof.py`
5. `scenarios/generator.py`
6. `policies/defender_pursuit.py`
7. `core/simulator.py`
8. `observation/visibility.py`
9. `observation/builder.py`
10. `reward/attack_defense_reward.py`
11. `termination/checker.py`
12. `envs/attack_defense_env.py`
13. `logging/rollout.py`
14. smoke tests
15. baseline

这样可以保证：

- 先把真值推进和状态结构打稳
- 再做外层任务壳
- 最后才组装 gym env

---

## 11. 与冻结附录的关系

开始编码前，应同时遵守 [DevDocV0.1.md](DevDocV0.1.md)。

其中以下 6 项必须视作 **冻结接口**：

1. state 定义
2. action 定义
3. observation schema
4. 坐标/单位约定
5. 终止阈值
6. info/log 字段

换句话说：

- `ImplementationSpecV0.1.md` 决定模块怎么拆、类怎么起名、先做什么
- [DevDocV0.1.md](DevDocV0.1.md) 决定最关键的数据契约长什么样

这两份文档共同构成 v0.1 的直接编码依据。