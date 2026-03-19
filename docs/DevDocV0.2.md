# DevDocV0.2

> 本文档是 USV Sim 项目的 **V0.2 开发文档**。
>
> 它建立在 [FinalDevDocV0.1.md](FinalDevDocV0.1.md) 已完成并通过灰度测试的基础上，用于定义 **V0.2 的新增目标、冻结边界、模块变更、测试增强与验收标准**。
>
> 若 V0.2 文档与 V0.1 文档存在冲突：
>
> - **未被 V0.2 显式修改的内容，继续继承 V0.1**
> - **被 V0.2 显式新增或调整的内容，以本文为准**

---

## 1. V0.2 版本定位

### 1.1 V0.2 核心目标

V0.2 不是重新设计物理内核，而是在 **不破坏 V0.1 冻结语义** 的前提下，把项目从“可运行的最小仿真内核”推进到“**可观察、可演示、可验证** 的研究原型平台”。

本阶段只做三件明确的事：

1. **实现最小可用的 2D 实时可视化**
2. **增加一个面向目标航行的 attacker baseline policy**
3. **补充更完整的单元测试和集成测试**

### 1.2 V0.2 的工程意义

V0.1 已证明：

- 动力学、场景生成、观测、奖励、终止和 gym 接口已经形成闭环
- 默认配置下环境可运行
- 0 defender / 1 defender 场景可通过 smoke test

但 V0.1 仍存在三个直接限制：

- 缺少实时可视化，难以观察行为是否符合直觉
- 缺少 attacker baseline，无法快速判断“任务本身是否可达、奖励是否合理、难度是否合适”
- 自动化测试粒度偏粗，尚不足以支撑后续 V0.3+ 的稳定迭代

因此 V0.2 的目标不是“加大功能面”，而是补齐这三个研究平台最关键的开发支撑能力。

---

## 2. V0.2 范围与非目标

### 2.1 V0.2 范围

V0.2 范围冻结为以下三类新增内容：

#### A. 渲染与演示能力
- 为 `AttackDefenseEnv` 提供最小 2D 可视化能力
- 支持逐步刷新、实时观察 attacker / defender / obstacle / goal / boundary
- 支持基于 `render_mode` 的标准 gymnasium 调用方式
- 支持最基础的视觉调试信息

#### B. baseline policy 能力
- 增加一个 **attacker 侧、面向目标航行** 的脚本策略
- 该策略用于：
  - 快速验证环境可控性
  - 验证 reward 是否基本合理
  - 作为后续 APF / MPC / RL 的最弱比较基线
- 该 baseline 仅要求“可运行、可解释、可复现”，不追求最优性能

#### C. 测试能力增强
- 增加针对动力学、几何、观测、reward、termination、scenario 的单元测试
- 增加 reset/step/render/baseline rollout 的集成测试
- 将 V0.1 的 smoke test 保留并升级为更明确的验收入口之一

### 2.2 V0.2 明确不做

V0.2 不做以下内容：

- 复杂 GUI 框架
- 3D 可视化
- 轨迹回放系统的复杂交互界面
- 视频导出系统
- 多 attacker 或多智能体联合训练接口
- APF / MPC / RRT / CBF 的正式实现
- belief state / history wrapper 的正式引入
- 更复杂的 defender 行为树或博弈式策略
- 感知噪声、遮挡、部分可见历史融合
- diffusion / flow matching 的训练与采样管线

### 2.3 为什么 V0.2 只做这三件事

因为这三项是后续几乎所有工作的共同底座：

- 没有可视化，很难快速判断物理与任务语义是否符合直觉
- 没有 baseline，很难区分“算法不行”还是“环境/奖励设计有问题”
- 没有更细粒度测试，后续每次改动都可能破坏既有能力

---

## 3. V0.2 总体原则

V0.2 继续继承 V0.1 的所有核心原则，新增以下三条：

### 3.1 原则 A：新增能力不得反向污染 V0.1 真值语义

- 可视化只消费 `WorldState` 与 step info
- baseline policy 只消费 observation 或结构化状态快照
- 测试只验证行为，不改变环境核心语义

不得为了渲染或 baseline 而修改：

- 动力学公式
- reward 公式
- termination 优先级
- observation schema
- env action 语义

### 3.2 原则 B：渲染是附加能力，不是主逻辑入口

渲染系统必须是“旁路能力”，而不是“环境核心依赖项”。

换句话说：

- 没有 render 时，环境仍能正常训练和测试
- render 失败不能改变 world step 结果
- render 不应持有独立真值状态

### 3.3 原则 C：baseline 是参考，不是接口耦合点

attacker baseline 的职责是：

- 提供一个稳定、简单、可解释的默认控制策略
- 用于可视化 demo、回归测试、基本任务验证

它**不是**环境内置主逻辑的一部分，不得导致 env 接口变为“依赖 baseline 才能工作”。

### 3.4 原则 D：测试优先覆盖冻结契约而不是覆盖率数字

V0.2 测试的重点不在“追求形式上的高覆盖率”，而在于验证：

- V0.1/V0.2 的冻结契约有没有被破坏
- 后续迭代最容易出错的部分有没有保护起来

---

## 4. V0.2 对 V0.1 的继承关系

以下内容在 V0.2 中 **默认完全继承 V0.1**：

- `WorldState` 只存真值
- action 为 shape `(2,)` 的 `[surge_cmd, yaw_cmd]`
- 动力学公式、积分器与数值限制
- goal 始终可见
- defender / obstacle 感知范围规则
- multi-substep 语义
- 终止优先级与 `time_limit` 规则
- reward 公式与 breakdown 字段
- scenario 几何合法性约束
- reset / step 基础流程

V0.2 不重写这些内容，只在必要处新增：

- render mode 与 renderer 语义
- attacker baseline policy 约束
- 测试分层与验收脚本要求

---

## 5. 目录与模块增量设计

V0.2 在 V0.1 目录基础上，建议新增以下模块：

```text
project_root/
├─ src/
│  └─ usv_sim/
│     ├─ rendering/
│     │  └─ simple_2d.py
│     ├─ policies/
│     │  ├─ base.py
│     │  ├─ defender_pursuit.py
│     │  └─ attacker_goal_baseline.py
│     └─ ...
├─ tests/
│  ├─ unit/
│  │  ├─ test_math_utils.py
│  │  ├─ test_geometry.py
│  │  ├─ test_dynamics.py
│  │  ├─ test_visibility.py
│  │  ├─ test_observation_builder.py
│  │  ├─ test_reward.py
│  │  ├─ test_termination.py
│  │  └─ test_scenario_generator.py
│  ├─ integration/
│  │  ├─ test_env_api.py
│  │  ├─ test_seed_reproducibility.py
│  │  ├─ test_render_loop.py
│  │  └─ test_attacker_baseline_rollout.py
│  └─ smoke/
│     └─ test_env_smoke.py
└─ DevDocV0.2.md
```

### 5.1 新增模块职责

#### `rendering/simple_2d.py`
最小 2D 渲染器，实现：

- boundary 绘制
- attacker / defender / obstacle / goal 绘制
- 基础轨迹或朝向线显示
- human 模式刷新
- rgb_array 模式图像输出（若选择实现）

#### `policies/attacker_goal_baseline.py`
实现 attacker 基线策略：

- 输入 observation 或当前 `WorldState`
- 输出 env action `[surge_cmd, yaw_cmd]`
- 目标：朝 goal 航行，必要时进行最小限度转向

#### `tests/unit/`
覆盖小粒度、可独立验证的数学/逻辑契约。

#### `tests/integration/`
验证多个模块组合后的整体行为。

---

## 6. 最小 2D 实时可视化设计

这一部分是 V0.2 最重要的新增冻结内容之一。

### 6.1 可视化目标

V0.2 的 2D 实时可视化只追求“**最小可用**”，即：

- 能看到 world 中的主要对象
- 能随 `env.step()` 实时刷新
- 能帮助开发者直观判断：
  - attacker 是否朝目标航行
  - defender 是否在追击
  - obstacle / boundary 几何是否正确
  - 终止是否符合预期

V0.2 不追求：

- 高质量 UI
- 可交互编辑场景
- 多窗口调试面板
- 专业动画系统

### 6.2 render mode 设计

V0.2 建议把 `AttackDefenseEnv.metadata` 从：

```python
{"render_modes": []}
```

升级为至少支持：

```python
{"render_modes": ["human"]}
```

若实现成本可控，可同时支持：

```python
{"render_modes": ["human", "rgb_array"]}
```

#### 冻结建议

- `human`：打开窗口并实时刷新
- `rgb_array`：返回当前帧图像数组
- `None`：不渲染，供训练/测试使用

V0.2 的最低要求是 **`human` 模式可用**。

同时建议明确以下调用优先级，以保持与 gymnasium 常见用法一致：

- `AttackDefenseEnv(..., render_mode="human")` 形式的**构造函数显式传参优先级高于配置文件**
- 配置文件中的 `env.render_mode` 用于提供默认值，而不是屏蔽构造函数显式选择
- 这样可以支持训练脚本默认不渲染、调试脚本临时切换到 `human` 的标准工作流

### 6.3 渲染后端建议

V0.2 推荐选择：

- **matplotlib** 作为最小可用渲染后端

原因：

- Python 环境中普遍可用
- 对 2D 几何对象绘制足够
- 工程复杂度低
- 易于实现 human 刷新
- 后续若需要，也可导出 `rgb_array`

V0.2 不建议优先引入：

- pygame
- pyqt / pyside 图形系统
- OpenGL 类渲染依赖

除非后续确认 matplotlib 在当前环境下不可接受。

### 6.4 渲染对象最小集合

V0.2 `human` 模式下，至少绘制：

- 矩形边界
- goal 圆形区域
- obstacle 圆
- attacker 圆 + 朝向线
- defender 圆 + 朝向线

### 6.5 颜色与视觉语义建议

建议采用稳定而简单的默认视觉语义：

- attacker：蓝色
- defender：红色
- obstacle：灰色或黑色
- goal：绿色半透明圆
- boundary：黑色线框
- attacker 轨迹：浅蓝色折线（可选）
- defender 轨迹：浅红色折线（可选）

颜色选择不是重点，但必须：

- attacker / defender / goal 明显可区分
- 不依赖复杂主题系统

### 6.6 坐标映射语义

渲染坐标必须直接对应世界坐标：

- x 轴向右
- y 轴向上
- 轴比例保持 1:1
- 不允许为了显示方便扭曲几何比例

### 6.7 `render()` 的行为契约

V0.2 中，`AttackDefenseEnv.render()` 语义建议冻结为：

#### 当 `render_mode is None`
- `render()` 返回 `None`
- 不创建窗口

#### 当 `render_mode == "human"`
- 首次调用时初始化渲染器资源
- 每次调用显示当前 world 状态
- 返回 `None`

#### 当 `render_mode == "rgb_array"`（若实现）
- 返回 `np.ndarray`
- shape 建议为 `(H, W, 3)`
- dtype 建议为 `uint8`

### 6.8 渲染器与环境的边界

环境不应直接持有复杂绘图逻辑。

建议结构：

```python
class Simple2DRenderer:
    def render_world(self, world: WorldState, info: dict | None = None): ...
    def close(self) -> None: ...
```

然后在 env 内只负责：

- 懒加载 renderer
- 把当前 `world` 和必要 `info` 交给 renderer
- 在 `close()` 中释放 renderer

### 6.9 `close()` 的新增要求

V0.2 中，若开启过渲染：

- `env.close()` 必须释放窗口/figure 资源
- 允许重复调用 `close()` 而不报错

### 6.10 实时可视化的最小验收效果

最低验收标准：

1. 可以运行一个 while loop：
   - `reset()`
   - 多次 `step()`
   - 每步调用 `render()`
2. 屏幕中能看到 attacker 连续运动
3. 目标、障碍、边界位置与 world 一致
4. episode 结束后窗口不会卡死
5. `close()` 后资源释放正常

---

## 7. Attacker baseline policy 设计

### 7.1 目标

V0.2 新增的 attacker baseline policy 只做一件事：

> 在不依赖学习的前提下，让 attacker 依据 goal 相对方位，输出一个稳定、简单、可复现的朝目标航行动作。

### 7.2 为什么必须有 attacker baseline

它至少承担四个作用：

1. **任务 sanity check**
   - 判断目标是否在多数简单场景中可达
2. **reward sanity check**
   - 判断 progress / goal reward 是否与目标行为一致
3. **可视化 demo 驱动器**
   - 让渲染不只是“随机船乱动”
4. **后续算法基线**
   - 为 APF / MPC / RL 提供一个最低比较参考

### 7.3 baseline 的定位

该 baseline 是：

- 脚本策略
- 单步反应式策略
- 可解释策略

而不是：

- 最优控制器
- 避障器
- 追求高成功率的复杂 planner

### 7.4 推荐策略形式

V0.2 推荐最小实现为：

> **Goal-heading baseline**：根据 goal 在 ego frame 下的位置计算期望转向，根据航向误差输出 yaw_cmd，并给出固定或分段式 surge_cmd。

### 7.5 输入与输出

建议该 baseline 提供统一接口：

```python
class GoalSeekingAttackerPolicy:
    def act(self, obs: dict[str, np.ndarray]) -> np.ndarray: ...
```

原因：

- 面向 observation，更贴近后续 RL / imitation / policy 接口
- 避免 baseline 直接依赖内部 world 真值结构

若实现上更方便，也可以提供辅助接口：

```python
def act_from_world(self, world: WorldState) -> np.ndarray: ...
```

但主接口建议仍以 `obs` 为主。

冻结建议：

- 正式 rollout、demo 与集成测试应优先使用 `act(obs)`
- `act_from_world(...)` 仅作为调试或局部单元测试辅助接口
- 不建议让 baseline 在正式使用路径上依赖 `WorldState` 真值输入

### 7.6 策略数学语义建议

建议 baseline 仍保持“单步反应式”，但不要弱到只剩一个纯比例转向。

给定 observation 中的：

```text
goal = [rel_x, rel_y, distance, goal_radius]
ego  = [u, v, r, cos_psi, sin_psi, speed_norm]
```

建议采用如下最小但更稳的数学语义：

1. 定义航向误差：

```text
heading_error = atan2(rel_y, rel_x)
```

2. yaw 命令由“航向误差比例项 + 当前偏航角速度阻尼项”组成：

```text
yaw_cmd = clip(k_heading * heading_error / pi - k_yaw_rate * r, -1, 1)
```

3. surge 命令采用“转向减速 + 近目标减速”的简单规则：

```text
if distance <= goal_radius:
    surge_cmd = 0.0
elif distance < slowdown_distance:
    surge_cmd = surge_near_goal
elif abs(heading_error) < heading_large_threshold:
    surge_cmd = surge_nominal
else:
    surge_cmd = surge_turning
```

这样做的原因：

- 保持策略可解释、可复现、易于实现
- 相比纯比例转向，更不容易出现明显左右摆振
- 接近目标时主动降速，更适合作为科研 sanity check baseline
- 仍然不引入避障、博弈、多步规划等额外职责

### 7.7 baseline 在 V0.2 中不承担的职责

该 baseline 在 V0.2 中明确 **不承担**：

- obstacle avoidance
- defender avoidance
- boundary aware planning
- 轨迹平滑优化
- 多步前瞻规划

也就是说：

- 它可能在简单场景有效
- 在复杂障碍/defender 场景失败是允许的

### 7.8 配置化建议

为了不把常数写死在代码里，建议新增最小配置块：

```yaml
attacker_baseline:
  type: goal_seeking
  surge_nominal: 0.8
  surge_turning: 0.3
  surge_near_goal: 0.2
  heading_gain: 1.5
  yaw_rate_damping: 0.2
  heading_large_threshold: 0.7854
  slowdown_distance: 8.0
```

说明：

- 所有角相关参数继续继承 V0.1 单位契约，统一使用 **rad / rad/s**
- `heading_large_threshold = 0.7854` 对应约 `45°`
- `yaw_rate_damping` 直接作用于 observation 中的 `r`

冻结建议：

- V0.2 中 **应将 attacker baseline 参数正式纳入配置系统**
- 不建议仅依赖策略类构造函数中的隐藏默认值
- baseline 既然要承担 demo、测试和验收职责，其参数就应当可记录、可追溯、可复现

### 7.9 基线 rollout 语义

V0.2 中建议提供一个最小 demo 用法：

- `reset(seed=...)`
- while not done:
  - `action = baseline.act(obs)`
  - `obs, reward, terminated, truncated, info = env.step(action)`
  - `env.render()`

这样既可作为演示，也可作为集成测试原型。

### 7.10 baseline 专用验证场景

为了避免 baseline 验收标准过于口语化、测试结果发飘，V0.2 建议冻结一个**专用简单验证场景**，用于 demo 与集成测试。

推荐场景条件：

- 边界沿用默认矩形海域
- `n_defenders = 0`
- `n_obstacles = 0`
- attacker 初始状态固定为：
  - `x = 20.0`
  - `y = 50.0`
  - `psi = 0.0`
  - `u = v = r = 0.0`
- goal 固定为：
  - `x = 80.0`
  - `y = 50.0`
  - `radius` 继承 V0.1 默认目标半径

该场景可以通过以下任一方式实现：

- 单独的测试配置文件
- 在测试中手工构造确定性初始 `WorldState`

但无论采用哪种方式，都应保证它是**确定性的、专用于 baseline 验证**的场景，而不是依赖随机默认场景“碰运气”。

### 7.11 baseline 最小验收标准

最低验收要求：

1. baseline 输出始终满足：
   - shape `(2,)`
   - dtype `float32`
   - 值域在 `[-1, 1]`
2. 在 **7.10 定义的 baseline 专用验证场景** 中，baseline 应能在给定步数预算内触发 `goal_reached`
3. 同 seed + 同初始状态 + 同 baseline 参数下，行为可复现
4. baseline rollout 可与 `render()` 联合工作

---

## 8. 测试体系增强设计

V0.2 的测试不再只满足“能跑通”，而要开始覆盖关键契约。

## 8.1 测试分层

V0.2 测试体系建议分为三层：

### A. Unit tests
验证局部模块的数学与逻辑正确性。

### B. Integration tests
验证多个模块组合后的行为契约。

### C. Smoke tests
保留最低成本的端到端冒烟检查，用于快速确认项目没有整体性崩坏。

---

## 8.2 单元测试建议清单

### 8.2.1 `test_math_utils.py`
至少覆盖：

- `wrap_to_pi()` 边界值
- `distance2d()`
- `world_to_ego()` 坐标变换方向
- `body_velocity_to_world()` 结果正确性

### 8.2.2 `test_geometry.py`
至少覆盖：

- `obstacle_clearance()` 正值 / 零 / 负值情况
- attacker 按**圆形外接体**的越界判定语义，而不是仅按质心点判定

### 8.2.3 `test_dynamics.py`
至少覆盖：

- 零动作时状态推进是否符合阻尼趋势
- 非零 yaw 动作时 `r` 与 `psi` 是否变化
- `psi` 是否规范化到 `(-pi, pi]`
- soft limit 是否施加到 `u, v, r`
- 在有界正常动作输入下，状态推进结果保持有限，不产生非预期 `NaN/Inf`

### 8.2.4 `test_visibility.py`
至少覆盖：

- goal 不受 `sensing_radius` 影响
- defender 在感知半径内可见、外不可见
- obstacle 在感知半径内可见、外不可见

### 8.2.5 `test_observation_builder.py`
至少覆盖：

- key 集合是否与 schema 一致
- 各字段 shape / dtype 是否正确
- 不可见对象是否零填充
- mask 是否正确
- defender / obstacle 槽位排序是否稳定
- `goal` 始终可见

### 8.2.6 `test_reward.py`
至少覆盖：

- progress 公式
- control 公式
- time penalty 常数项
- 终止 reward 不叠加
- 不同 termination reason 下 breakdown 字段是否匹配

### 8.2.7 `test_termination.py`
至少覆盖：

- 终止优先级顺序
- `time_limit` 只在无真实终止时生效
- `terminated` 与 `truncated` 不同时为真
- `numerical_failure` 事件能正确映射到 `termination_reason == "numerical_failure"`

### 8.2.8 `test_scenario_generator.py`
至少覆盖：

- 同 seed 结果一致
- 初始 attacker / goal / defender / obstacle 不重叠
- attacker 初始不越界
- attacker 初始不在 goal 区或 capture 区内

---

## 8.3 集成测试建议清单

### 8.3.1 `test_env_api.py`
验证：

- `reset()` 返回 `(obs, info)`
- `step()` 返回五元组
- `terminated` / `truncated` 为布尔值
- `info` 包含文档约定的关键字段

### 8.3.2 `test_seed_reproducibility.py`
验证：

- 同 seed reset 初始 world 一致
- 同 seed + 同动作序列 rollout 结果一致

### 8.3.3 `test_render_loop.py`
验证：

- `render_mode="human"` 时环境可创建并调用 render
- 连续多步 render 不崩溃
- `render()` 前后 world 语义不发生变化，例如不额外推进 `step_count` / `sim_time`
- `close()` 可正常释放
- `close()` 可重复调用而不报错

若 CI/无显示环境不稳定，可对 `human` 做条件化测试，并在本地保留完整测试。

### 8.3.4 `test_attacker_baseline_rollout.py`
验证：

- baseline 与 env 接口兼容
- baseline 输出合法动作
- baseline rollout 能在若干步内持续推进而不报错
- 在 **7.10 定义的 baseline 专用验证场景** 中，baseline 应在固定步数预算内触发 `goal_reached`

这里不再使用“总体下降”“明显变小”这类主观描述，而采用固定场景 + 明确终止判据的验收方式。

---

## 8.4 smoke test 的 V0.2 定位

V0.1 的 smoke test 继续保留，但 V0.2 中它的地位调整为：

- **快速健康检查**
- 不是唯一验收依据

推荐继续保留至少两类 smoke：

1. 常数动作 smoke
2. attacker baseline smoke

---

## 9. 配置系统在 V0.2 的扩展建议

V0.2 可能需要最小幅度扩展配置，以支持渲染和 attacker baseline。

### 9.1 `env.render_mode`
当前已有：

```yaml
env:
  render_mode: null
```

V0.2 继续沿用该字段，但其语义扩展为：

- `null`：不渲染
- `human`：人类实时显示
- `rgb_array`：返回图像数组（若实现）

并补充一条实现约束：

- 若 `AttackDefenseEnv` 构造函数显式传入 `render_mode`，则**构造函数参数优先于配置文件默认值**

### 9.2 `rendering` 配置块（可选）
建议可选加入：

```yaml
rendering:
  width: 800
  height: 800
  show_trajectory: true
  attacker_color: blue
  defender_color: red
```

若 V0.2 想保持配置极简，也可以暂不引入该配置块，把这些做成 renderer 默认值。

### 9.3 `attacker_baseline` 配置块（推荐）
建议新增：

```yaml
attacker_baseline:
  type: goal_seeking
  surge_nominal: 0.8
  surge_turning: 0.3
  surge_near_goal: 0.2
  heading_gain: 1.5
  yaw_rate_damping: 0.2
  heading_large_threshold: 0.7854
  slowdown_distance: 8.0
```

理由：

- baseline 参数将来很可能需要调
- 若不配置化，测试和 demo 很难统一
- 统一进入配置后，实验记录与结果复现更直接

---

## 10. 对核心接口的 V0.2 增量要求

## 10.1 `envs/attack_defense_env.py`

V0.2 中，`AttackDefenseEnv` 需要从“无 render 实现”升级为“支持最小 render mode 语义”。

建议新增或调整：

- `metadata["render_modes"]`
- `self.render_mode`
- `self._renderer`
- `render()`
- `close()`
- 构造函数显式 `render_mode` 入参，并允许覆盖配置默认值

但以下内容不得改变：

- `reset()` 返回语义
- `step()` 返回语义
- `action_space`
- `observation_space`

## 10.2 `policies/base.py`

V0.2 建议让策略边界更明确：

- defender policy 保持原接口
- attacker baseline 作为独立策略类，不直接塞入 env 核心

也就是说：

- env 仍只接收动作
- baseline 是 env 外部调用者

## 10.3 `logging/rollout.py`

V0.2 可以考虑做很小的增强，但不是强制：

- episode summary 中记录 render/demo 使用的 policy name
- 记录最小 goal distance
- 记录 baseline rollout 的成功与否

若当前 recorder 已能满足这些统计，则不必为了 V0.2 过度扩展。

---

## 11. V0.2 文档级冻结条款

以下为 V0.2 新增冻结要求。

### 11.1 Render 冻结条款

1. render 是附加能力，不得改变 world step 结果
2. render 只读取当前 world 和必要 info，不维护第二份真值
3. `close()` 必须可重复调用且安全
4. `human` 模式是 V0.2 最低要求
5. 若实现 `rgb_array`，输出必须是标准图像数组
6. `render()` 调用前后不得额外修改 `step_count`、`sim_time` 或其他真值状态

### 11.2 Attacker baseline 冻结条款

1. baseline 输出必须遵守 env action 语义 `[surge_cmd, yaw_cmd]`
2. baseline 不得直接改写 env 内部状态
3. baseline 不得引入新的 env action 维度
4. baseline 在 V0.2 中不承担避障/防守规避规划职责
5. baseline 的主要目标是“朝 goal 航行”，不是高性能求解器
6. baseline 的正式 public interface 以 `act(obs)` 为主，不以 `WorldState` 真值接口作为主要使用路径
7. baseline 相关参数应进入配置系统并可记录，不建议依赖隐藏默认值

### 11.3 测试冻结条款

1. V0.1 smoke test 不得删除
2. V0.2 必须新增 unit tests 与 integration tests
3. 关键冻结契约至少要有一条测试保护：
   - goal 始终可见
   - termination 优先级
   - reward 不叠加
   - substep 首次终止即停
   - 同 seed 可复现
4. 测试代码不得依赖手工观察结果作为唯一判据
5. attacker baseline 必须基于**固定验证场景**进行至少一条自动化集成测试
6. render 至少要有一条“无副作用”测试，而不仅是“能打开窗口”

---

## 12. 推荐开发顺序

V0.2 推荐按以下顺序推进：

1. **先实现 attacker baseline**
   - 因为它可以立刻用于 demo 和测试
2. **再实现最小 human render**
   - 用 baseline 驱动 render，快速可见结果
3. **再补 unit tests**
   - 先覆盖数学/逻辑冻结契约
4. **最后补 integration tests**
   - 用 baseline + render + env 串起来做端到端验证

这个顺序的原因是：

- baseline 最容易快速暴露“任务是否合理”
- render 没有 baseline 时演示价值较弱
- 测试应建立在已有明确行为之上

---

## 13. V0.2 第一批 TODO

| ID | 任务 | 输出 | 验收标准 |
|---|---|---|---|
| T201 | 设计最小 render mode 语义 | `AttackDefenseEnv` 接口调整 | `human` 模式可调用 |
| T202 | 实现 2D 渲染器 | `rendering/simple_2d.py` | 能显示 boundary/goal/USV/obstacle |
| T203 | 接入 env.render() / close() | `attack_defense_env.py` | 连续 render 不崩溃，close 可释放 |
| T204 | 实现 attacker baseline policy | `policies/attacker_goal_baseline.py` | 输出合法 action，朝 goal 航行 |
| T205 | 添加 baseline demo rollout | demo 或集成测试 | baseline 可驱动一个 episode |
| T206 | 补 math/geometry/dynamics 单测 | `tests/unit/` | 关键数学契约受保护 |
| T207 | 补 visibility/obs/reward/termination 单测 | `tests/unit/` | 任务层契约受保护 |
| T208 | 补 scenario/reproducibility 测试 | `tests/unit/` + `tests/integration/` | 同 seed 可复现 |
| T209 | 补 env API 集成测试 | `tests/integration/test_env_api.py` | reset/step 语义稳定 |
| T210 | 补 render 集成测试 | `tests/integration/test_render_loop.py` | render/close 可正常工作 |
| T211 | 保留并升级 smoke tests | `tests/smoke/` | 常数动作和 baseline 均能跑通 |

---

## 14. V0.2 验收标准

### 14.1 功能验收

V0.2 完成时，必须满足：

#### A. 可视化
- `render_mode="human"` 可用
- 默认场景下可以实时看到 attacker / defender / obstacle / goal / boundary
- `close()` 资源释放正常

#### B. baseline
- 存在一个 attacker baseline policy
- baseline 输出满足 env action 约束
- baseline 在 7.10 定义的固定验证场景中可在步数预算内到达目标

#### C. 测试
- 单元测试覆盖关键冻结契约
- 集成测试覆盖 env API、seed reproducibility、baseline rollout、render loop
- smoke test 保持通过

### 14.2 语义验收

V0.2 完成时，以下 V0.1 语义不得被破坏：

- action 仍为 `[surge_cmd, yaw_cmd]`
- reward 仍按已有公式计算
- termination 优先级不变
- goal 始终可见
- WorldState 不塞回业务逻辑
- Dynamics / Simulator 不原地改输入

### 14.3 研究可用性验收

V0.2 至少应达到以下研究使用门槛：

1. 开发者可以开一个窗口直接观察环境行为
2. 开发者可以用 baseline 在固定验证场景中快速判断“环境、奖励、render、测试入口”是否协同正常
3. 后续修改核心逻辑时，能通过测试快速发现是否破坏契约

---

## 15. 推荐验收命令

以下命令是 V0.2 建议形成的正式验收入口。

### 15.1 单元测试

```bash
conda run -n RL pytest tests/unit -q
```

### 15.2 集成测试

```bash
conda run -n RL pytest tests/integration -q
```

### 15.3 smoke test

```bash
conda run -n RL python tests/smoke/test_env_smoke.py
```

### 15.4 本地可视化 demo（建议补一个脚本）

```bash
conda run -n RL python demos/run_attacker_baseline_demo.py
```

若 V0.2 不想新建 `demos/` 目录，也可以先通过测试或临时脚本方式运行，但从工程清晰度上，建议后续有一个明确 demo 入口。

---

## 16. 后续对 V0.3 的铺垫

V0.2 完成后，项目将自然具备以下升级条件：

- 可视化让 APF / MPC / RRT 行为更容易调试
- attacker baseline 让后续控制器/规划器有明确最低参考
- 更完整测试让加入新方法时更不容易破坏旧能力

因此 V0.2 是后续扩展到以下方向的直接前置：

- APF baseline
- 路径跟踪控制器
- RRT/MPC adapter
- 更系统的 benchmark
- 训练前数据质量验证

---

## 17. 最终结论

V0.2 的本质不是“再堆功能”，而是把项目推进到一个更适合算法研发的状态：

- **看得见**：最小 2D 实时可视化
- **跑得动**：目标航行 attacker baseline
- **改得稳**：更完整的单元测试和集成测试

只要严格遵守本文件与 [FinalDevDocV0.1.md](FinalDevDocV0.1.md) 的冻结边界，V0.2 完成后，这个 USV 仿真平台就会从“最小内核”升级为“具备基础研发支撑能力的可验证平台”。
