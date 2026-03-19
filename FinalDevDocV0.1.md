# FinalDevDocV0.1

> 本文档是 USV Sim 项目的 **V0.1 最终开发文档**。
> 它合并并取代此前的 [ImplementationSpecV0.1.md](ImplementationSpecV0.1.md) 与 [DevDocV0.1.md](DevDocV0.1.md) 在 v0.1 范围内的约束作用。
>
> 从本文件写完开始，**v0.1 开发以本文为唯一直接依据**。
> 若本文与此前文档存在冲突，以本文为准。

---

## 1. V0.1 范围与目标

### 1.1 V0.1 目标

v0.1 的目标是构建一个可运行、可复现、可继续扩展的最小 USV 仿真内核，满足：

- 基于 **Fossen 风格简化 3-DOF 平面模型** 的真值推进
- 基于 **gymnasium** 的环境接口
- 1 个 attacker
- 0~N 个 defender（至少支持 0 和 1）
- 固定圆形障碍物
- 矩形边界海域
- 圆形目标区域
- 固定 shape 的 observation
- 固定的 env action 语义
- 可复现的场景生成
- 明确的 reward / termination / info 语义

### 1.2 V0.1 不做

v0.1 不做以下内容：

- 雷达/声呐原始观测
- 遮挡
- 观测噪声和时延
- 6-DOF
- 非圆形障碍物
- 多智能体训练框架
- diffusion / flow matching 训练管线
- 海流/风浪扰动
- 复杂渲染系统
- 针对单一算法定制 env 接口

---

## 2. 冻结总则

v0.1 中，以下准则冻结：

1. `WorldState` 只存真值，不承担 reward / obs / termination / logging 逻辑
2. env action 固定为 `(2,)` 归一化低层控制输入 `[surge_cmd, yaw_cmd]`
3. goal **始终可见**，不受 `sensing_radius` 限制
4. 一个 `env.step()` 内部有多个 substep；一旦某个 substep 首次触发真实终止事件，立即停止后续 substep
5. 终止判定优先级固定：先真实终止事件，再 `time_limit`
6. `Dynamics.step()` 和 `WorldSimulator.step()` **禁止原地修改输入对象**，必须返回新对象
7. 几何真值只以 `WorldState` 为准；配置只用于生成初值和默认参数

若未来要改上述规则，应视为 **v0.2 接口变更**。

---

## 3. 目录与模块冻结

```text
project_root/
├─ src/
│  └─ usv_sim/
│     ├─ __init__.py
│     ├─ config.py
│     ├─ core/
│     │  ├─ math_utils.py
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
├─ DevDocV0.1.md
└─ FinalDevDocV0.1.md
```

说明：

- 根目录 `configs/` 只放 YAML
- `src/usv_sim/config.py` 只放 schema / dataclass / 加载逻辑
- v0.1 **不创建** `src/usv_sim/config/` 目录

---

## 4. 数据结构冻结

### 4.1 不可变语义

v0.1 中所有核心状态对象采用不可变语义：

- dataclass 使用 `frozen=True, slots=True`
- `WorldState.defenders` 与 `WorldState.obstacles` 使用 tuple
- `Dynamics.step()`、`WorldSimulator.step()` 返回新对象
- 禁止原地修改输入 `WorldState` / `USVState`

这样做是为了避免：

- `prev_world` 被隐式污染
- 多 substep 中引用别名导致的难查 bug
- reward 与 termination 读取到已被改写的数据

### 4.2 `USVState`

```python
@dataclass(frozen=True, slots=True)
class USVState:
    entity_id: int
    x: float
    y: float
    psi: float
    u: float
    v: float
    r: float
    radius: float
```

### 4.3 `CircularObstacle`

```python
@dataclass(frozen=True, slots=True)
class CircularObstacle:
    entity_id: int
    x: float
    y: float
    radius: float
```

### 4.4 `GoalRegion`

```python
@dataclass(frozen=True, slots=True)
class GoalRegion:
    x: float
    y: float
    radius: float
```

### 4.5 `RectBoundary`

```python
@dataclass(frozen=True, slots=True)
class RectBoundary:
    xmin: float
    xmax: float
    ymin: float
    ymax: float
```

### 4.6 `WorldState`

```python
@dataclass(frozen=True, slots=True)
class WorldState:
    sim_time: float
    step_count: int
    seed: int
    scenario_id: str
    attacker: USVState
    defenders: tuple[USVState, ...]
    obstacles: tuple[CircularObstacle, ...]
    goal: GoalRegion
    boundary: RectBoundary
```

冻结要求：

- `WorldState` 不含 observation
- `WorldState` 不含 reward
- `WorldState` 不含 terminated/truncated
- `WorldState` 不含事件缓存
- `WorldState` 不含 logging 字段

---

## 5. 坐标系、单位与角度契约

### 5.1 世界坐标系

- `x`：向右
- `y`：向上
- 角度正方向：逆时针

### 5.2 船体坐标系

- `x_b`：前向
- `y_b`：左向

因此：

- `u`：surge，沿 `x_b`
- `v`：sway，沿 `y_b`
- `r`：yaw rate，逆时针为正

### 5.3 航向角

- `psi = 0`：船头指向世界系 `+x`
- `psi > 0`：逆时针旋转
- `psi < 0`：顺时针旋转

### 5.4 角度范围

所有角度统一使用：

```text
(-pi, pi]
```

冻结要求：

- `psi` 存储时必须已规范化
- 任意角度差必须先规范化到 `(-pi, pi]`

### 5.5 单位

| 量 | 单位 |
|---|---|
| 长度 | m |
| 时间 | s |
| 线速度 | m/s |
| 角度 | rad |
| 角速度 | rad/s |
| 力 | N |
| 力矩 | N·m |

### 5.6 ego frame 相对位置

给定对象世界系相对位移：

```text
dx = x_obj - x_att
dy = y_obj - y_att
```

则 attacker ego frame 相对位置定义为：

```text
rel_x =  cos(psi_att) * dx + sin(psi_att) * dy
rel_y = -sin(psi_att) * dx + cos(psi_att) * dy
```

解释：

- `rel_x > 0`：物体在 attacker 前方
- `rel_y > 0`：物体在 attacker 左侧

---

## 6. Env Action 冻结

### 6.1 action space

```python
action_space = gym.spaces.Box(
    low=-1.0,
    high=1.0,
    shape=(2,),
    dtype=np.float32,
)
```

### 6.2 动作语义

| 索引 | 名称 | 语义 |
|---|---|---|
| `0` | `surge_cmd` | 归一化 surge 力输入 |
| `1` | `yaw_cmd` | 归一化 yaw 力矩输入 |

### 6.3 物理映射

令配置中：

- `max_surge_force`
- `max_yaw_moment`

则：

```text
tau_u = clip(action[0], -1, 1) * max_surge_force
tau_v = 0
tau_r = clip(action[1], -1, 1) * max_yaw_moment
```

因此 v0.1 中控制输入固定为：

```text
τ = [tau_u, 0, tau_r]^T
```

### 6.4 为什么不使用 `[u_ref, psi_ref]`

v0.1 不把参考量当作 env 原生动作，原因：

- 否则环境内必须内置默认控制器
- env 语义会与控制器设计耦合
- RL 与传统控制的边界会变模糊

因此：

- RL 直接输出 env action
- APF / MPC / RRT / 轨迹生成器若输出参考量，需在环境外通过 controller / adapter 转成该动作

### 6.5 defender 动作语义

defender 与 attacker 动作协议完全相同：

- shape `(2,)`
- dtype `float32`
- `[surge_cmd, yaw_cmd]`

---

## 7. V0.1 动力学权威公式与积分器

这一节是 v0.1 新增的权威冻结内容。

### 7.1 状态向量

定义：

```text
eta = [x, y, psi]^T
nu  = [u, v, r]^T
```

### 7.2 运动学方程

采用 [kinematic_model.md](kinematic_model.md) 中给出的标准形式：

```math
\dot{\eta} = J(\eta)\nu
```

其中：

```math
\begin{bmatrix} \dot{x} \\ \dot{y} \\ \dot{\psi} \end{bmatrix} =
\begin{bmatrix}
\cos\psi & -\sin\psi & 0 \\
\sin\psi & \cos\psi & 0 \\
0 & 0 & 1
\end{bmatrix}
\begin{bmatrix} u \\ v \\ r \end{bmatrix}
```

即：

```math
\dot{x} = u\cos\psi - v\sin\psi
```

```math
\dot{y} = u\sin\psi + v\cos\psi
```

```math
\dot{\psi} = r
```

### 7.3 动力学方程

v0.1 冻结为一个**简化的对角质量矩阵 + 线性阻尼 + Fossen 风格 Coriolis 项**模型。

令：

```math
M = \mathrm{diag}(m_{11}, m_{22}, m_{33})
```

```math
D(\nu) = \mathrm{diag}(d_{11}, d_{22}, d_{33})
```

```math
\tau = [\tau_u, 0, \tau_r]^T
```

采用简化 Coriolis 项：

```math
C(\nu)\nu =
\begin{bmatrix}
-m_{22}vr \\
 m_{11}ur \\
 (m_{22}-m_{11})uv
\end{bmatrix}
```

于是：

```math
M\dot{\nu} + C(\nu)\nu + D(\nu)\nu = \tau
```

展开后冻结为：

```math
\dot{u} = \frac{\tau_u + m_{22}vr - d_{11}u}{m_{11}}
```

```math
\dot{v} = \frac{-m_{11}ur - d_{22}v}{m_{22}}
```

```math
\dot{r} = \frac{\tau_r + (m_{11}-m_{22})uv - d_{33}r}{m_{33}}
```

### 7.4 `tau_v`

v0.1 中明确冻结：

```text
tau_v = 0
```

不允许在 v0.1 中引入第三个 env 动作维度。

### 7.5 积分器类型

v0.1 固定使用：

- **固定步长 Forward Euler 显式欧拉积分**
- 每个 env step 内部执行 `sim_substeps` 次积分
- `dt_sim = dt_env / sim_substeps`

即对任一 substep：

```text
state_next = state_curr + dt_sim * f(state_curr, action_curr)
```

### 7.6 每个 substep 的计算顺序

对于 attacker 或 defender 的每个 substep，顺序冻结为：

1. clip 动作到 `[-1, 1]`
2. 映射到 `tau_u, tau_r`
3. 按 7.2、7.3 计算状态导数
4. 用 Forward Euler 得到候选下一状态
5. 将 `psi` 规范化到 `(-pi, pi]`
6. 检查硬异常：NaN / Inf / hard limit / 极端位置
7. 若未触发硬异常，则对 `u, v, r` 施加 soft limit 裁剪
8. 返回该 substep 新状态

### 7.7 soft limit 施加位置

v0.1 冻结为：

- soft limit 在 **积分之后、硬异常检查之后** 施加
- soft limit 只作用于 `u, v, r`
- 不作用于 `x, y, psi`

因此：

```text
u <- clip(u, -u_max_soft, u_max_soft)
v <- clip(v, -v_max_soft, v_max_soft)
r <- clip(r, -r_max_soft, r_max_soft)
```

### 7.8 hard numerical failure 判据

若候选 attacker 状态出现以下任一情况，则记为 `numerical_failure`：

1. 任一状态量是 `NaN`
2. 任一状态量是 `Inf`
3. `abs(u) > hard_u_limit`
4. `abs(v) > hard_v_limit`
5. `abs(r) > hard_r_limit`
6. `abs(x) > 1e6` 或 `abs(y) > 1e6`

### 7.9 Why Euler

v0.1 选择显式欧拉是出于以下考虑：

- 简单
- 易调试
- 可与多 substep 组合控制数值误差
- 对 RL / 脚本控制 baseline 足够

更高阶积分器（如 RK4）留到后续版本再引入。

---

## 8. Observation Schema 冻结

### 8.1 总体形式

v0.1 采用：

```python
spaces.Dict({
    "ego": ...,
    "goal": ...,
    "boundary": ...,
    "defenders": ...,
    "defenders_mask": ...,
    "obstacles": ...,
    "obstacles_mask": ...,
})
```

### 8.2 总体规则

- 所有输出 dtype 都是 `np.float32`
- shape 固定
- goal **始终可见**
- defender / obstacle 只在 `distance <= sensing_radius` 时可见
- 不可见对象整行零填充
- mask 显式给出
- 对象顺序在 episode 内稳定，不按距离重排

### 8.3 对象顺序规则

- defender：按 `entity_id` 升序映射到槽位
- obstacle：按 `entity_id` 升序映射到槽位

### 8.4 `ego`

```text
shape = (6,)
dtype = float32
```

字段顺序：

| idx | 名称 | 含义 |
|---|---|---|
| 0 | `u` | surge 速度 |
| 1 | `v` | sway 速度 |
| 2 | `r` | yaw rate |
| 3 | `cos_psi` | 航向余弦 |
| 4 | `sin_psi` | 航向正弦 |
| 5 | `speed_norm` | `sqrt(u^2 + v^2)` |

### 8.5 `goal`

goal 在 v0.1 中 **始终可见，不受感知半径限制**。

```text
shape = (4,)
dtype = float32
```

字段顺序：

| idx | 名称 | 含义 |
|---|---|---|
| 0 | `rel_x` | goal 在 attacker ego frame 下的 x |
| 1 | `rel_y` | goal 在 attacker ego frame 下的 y |
| 2 | `distance` | attacker 到 goal 中心距离 |
| 3 | `goal_radius` | `world.goal.radius` |

说明：

- v0.1 **没有** `goal_mask`
- 也不把 goal 纳入 `sensing_radius` 可见性规则

### 8.6 `boundary`

```text
shape = (4,)
dtype = float32
```

字段顺序：

| idx | 名称 | 含义 |
|---|---|---|
| 0 | `dist_left` | 到左边界距离 |
| 1 | `dist_right` | 到右边界距离 |
| 2 | `dist_bottom` | 到下边界距离 |
| 3 | `dist_top` | 到上边界距离 |

若越界，允许为负。

### 8.7 `defenders`

默认 `max_defenders = 4`。

```text
shape = (4, 7)
dtype = float32
```

每个槽位字段顺序：

| idx | 名称 | 含义 |
|---|---|---|
| 0 | `rel_x` | defender 在 attacker ego frame 下的 x |
| 1 | `rel_y` | defender 在 attacker ego frame 下的 y |
| 2 | `rel_u` | defender 相对速度在 attacker ego frame 下的 x 分量 |
| 3 | `rel_v` | defender 相对速度在 attacker ego frame 下的 y 分量 |
| 4 | `distance` | defender 到 attacker 中心距离 |
| 5 | `cos_dpsi` | 航向差余弦 |
| 6 | `sin_dpsi` | 航向差正弦 |

#### `rel_u` / `rel_v` 数学定义

这部分在 v0.1 中冻结为：

1. 将 attacker 的体速度转换到世界系：

```text
v_att_world = R(psi_att) @ [u_att, v_att]^T
```

2. 将 defender 的体速度转换到世界系：

```text
v_def_world = R(psi_def) @ [u_def, v_def]^T
```

3. 求世界系相对速度：

```text
v_rel_world = v_def_world - v_att_world
```

4. 再转回 attacker ego frame：

```text
[rel_u, rel_v]^T = R(-psi_att) @ v_rel_world
```

其中 `R(theta)` 为二维旋转矩阵。

### 8.8 `defenders_mask`

```text
shape = (4,)
dtype = float32
```

语义：

- `1.0`：该槽位有 defender 且当前可见
- `0.0`：不可见或该槽位空

### 8.9 `obstacles`

默认 `max_obstacles = 8`。

```text
shape = (8, 4)
dtype = float32
```

每个槽位字段顺序：

| idx | 名称 | 含义 |
|---|---|---|
| 0 | `rel_x` | obstacle 在 ego frame 下的 x |
| 1 | `rel_y` | obstacle 在 ego frame 下的 y |
| 2 | `distance` | obstacle 中心到 attacker 中心距离 |
| 3 | `radius` | obstacle 半径 |

### 8.10 `obstacles_mask`

```text
shape = (8,)
dtype = float32
```

语义：

- `1.0`：该槽位有 obstacle 且当前可见
- `0.0`：不可见或该槽位空

### 8.11 可见性规则

v0.1 冻结为：

- goal：始终可见
- defender：若中心距离 `<= sensing_radius` 则可见
- obstacle：若中心距离 `<= sensing_radius` 则可见
- 360° 全向
- 无遮挡
- 无噪声

---

## 9. 几何判据与 StepEvents

### 9.1 `StepEvents`

```python
@dataclass(frozen=True, slots=True)
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

### 9.2 `goal_distance`

```text
goal_distance = ||p_att - p_goal||_2
```

### 9.3 `min_defender_distance`

若存在 defender：

```text
min_defender_distance = min_i ||p_def_i - p_att||_2
```

若不存在 defender：

```text
min_defender_distance = inf
```

### 9.4 `min_obstacle_clearance`

这部分在 v0.1 中冻结为：

```text
min_obstacle_clearance = min_i ( ||p_obs_i - p_att||_2 - r_att - r_obs_i )
```

说明：

- 允许为负
- 若不存在 obstacle，则为 `inf`

### 9.5 goal reached 判据

```text
goal_reached := goal_distance <= world.goal.radius
```

注意：

- 终止判据使用 `world.goal.radius`
- 配置中的 `goal_radius` 只用于生成初始 `GoalRegion`

### 9.6 obstacle collision 判据

```text
obstacle_collision := exists i,
    ||p_obs_i - p_att||_2 <= r_att + r_obs_i
```

### 9.7 captured 判据

```text
captured := exists i,
    ||p_def_i - p_att||_2 <= capture_radius
```

说明：

- `capture_radius` 是任务层语义
- 不等于船体几何碰撞半径之和

### 9.8 out of bounds 判据

攻击艇越界按圆形外接体判定：

```text
x_att - r_att < xmin
or x_att + r_att > xmax
or y_att - r_att < ymin
or y_att + r_att > ymax
```

### 9.9 numerical failure 判据

见第 7 节。

---

## 10. Multi-substep 语义冻结

### 10.1 env.step 与 substep

一次 `env.step()` = 一次决策周期。

内部执行：

```text
sim_substeps
```

次物理积分。

### 10.2 首次终止即停止 substep

v0.1 中，一旦某个 substep 首次触发以下任一真实终止事件：

- `goal_reached`
- `captured`
- `obstacle_collision`
- `out_of_bounds`
- `numerical_failure`

则：

- 立即停止剩余 substep
- 以该 substep 的状态作为该次 `env.step()` 的输出 `next_world`
- 不再继续推进本次决策周期内的后续 substep

### 10.3 `step_count` 递增时机

v0.1 中：

- 初始 reset 后，`world.step_count = 0`
- 每执行一次 `env.step()`，无论内部跑了几个 substep，`next_world.step_count = prev_world.step_count + 1`

即：

- `step_count` 表示 **完成了多少个 env step**
- 而不是完成了多少个 substep

---

## 11. 终止优先级与最后一步规则

### 11.1 真实终止事件优先级

v0.1 中真实终止事件优先级冻结为：

```text
numerical_failure
> obstacle_collision
> out_of_bounds
> captured
> goal_reached
```

说明：

- 若同一最终状态同时满足多个真实终止事件，只取优先级最高者作为 `termination_reason`
- reward 终止项也按同一优先级只取一个

### 11.2 time limit 规则

`time_limit` 只对应 `truncated`。

触发条件冻结为：

```text
next_world.step_count >= max_episode_steps
```

### 11.3 最后一步同时发生真实终止与 time limit

v0.1 固定规则：

1. 先判真实终止事件
2. 若存在真实终止事件，则 `terminated=True, truncated=False`
3. 仅当不存在真实终止事件且 `next_world.step_count >= max_episode_steps` 时，才 `truncated=True`

因此：

- 真实终止事件优先于 `time_limit`
- `terminated` 与 `truncated` 在 v0.1 中禁止同时为真

### 11.4 `termination_reason` 枚举

结束时必须属于以下之一：

- `numerical_failure`
- `obstacle_collision`
- `out_of_bounds`
- `captured`
- `goal_reached`
- `time_limit`
- `not_terminated`

---

## 12. Reward 公式冻结

### 12.1 reward 组成

v0.1 reward 由以下项组成：

```text
reward_total = progress + time + control + terminal_event_reward
```

其中 `terminal_event_reward` 由终止优先级决定，最多取一个。

### 12.2 progress

冻结为：

```text
progress = progress_weight * (d_prev - d_curr)
```

其中：

- `d_prev`：上一步到 goal 中心距离
- `d_curr`：当前步到 goal 中心距离

### 12.3 time

冻结为：

```text
time = time_penalty
```

即每 step 固定加一个常数，通常为负值。

### 12.4 control

冻结为：

```text
control = control_l2_weight * ||clip(action, -1, 1)||_2^2
```

说明：

- 使用实际生效的归一化动作
- 若 `control_l2_weight < 0`，则为惩罚项

### 12.5 terminal event reward

冻结为：

- 若 `termination_reason == goal_reached`，加 `goal_reward`
- 若 `termination_reason == captured`，加 `capture_penalty`
- 若 `termination_reason == obstacle_collision`，加 `collision_penalty`
- 若 `termination_reason == out_of_bounds`，加 `boundary_penalty`
- 若 `termination_reason == numerical_failure`，加 `numerical_failure_penalty`
- 若 `time_limit` 或未终止，则终止项为 `0`

### 12.6 多个终止事件同一步发生

若同一步满足多个真实终止事件：

- reward 终止项按第 11 节优先级只取一个
- 不叠加多个终止奖励/惩罚

### 12.7 reward breakdown 字段冻结

```python
@dataclass(frozen=True, slots=True)
class RewardBreakdown:
    total: float
    progress: float
    goal: float
    capture: float
    collision: float
    boundary: float
    numerical_failure: float
    time: float
    control: float
```

其中只有命中的终止项非零，其余终止项为 0。

---

## 13. Defender 运行时物理语义

这一节是 v0.1 必须明确的。

### 13.1 相同之处

defender 与 attacker 在以下方面相同：

- 使用同一动力学模型
- 使用同一动作语义
- 使用同一 soft velocity limit
- 使用同一积分器

### 13.2 不同之处

defender 在 v0.1 中的任务逻辑与 attacker 不同：

- defender 自身越界、数值异常、碰撞不直接终止 episode
- 只有 attacker 的任务事件用于 reward / termination

### 13.3 defender 与边界 / 障碍的处理

v0.1 冻结为以下简化语义：

- defender **受边界和障碍几何约束**
- 对某个 defender 的某个 substep，先得到候选新状态
- 若候选状态越界或与任一 obstacle 碰撞，则：
  - 放弃该候选状态
  - defender 保持上一个位置与航向
  - defender 的 `u=v=r=0`

即，v0.1 中 defender 的边界/障碍处理采用**阻塞式简化响应**。

### 13.4 defender-defender 碰撞

v0.1 中：

- 不显式处理 defender-defender 碰撞
- 不把 defender 与 goal 的交互纳入任务逻辑

这样可以控制 v0.1 复杂度。

---

## 14. 配置项冻结

## 14.1 `EnvConfig`

```yaml
env:
  max_episode_steps: 400
  dt_env: 0.20
  sim_substeps: 4
  render_mode: null
```

## 14.2 `ActionConfig`

```yaml
action:
  max_surge_force: 40.0
  max_yaw_moment: 15.0
```

## 14.3 `DynamicsConfig`

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
  hard_u_limit: 8.0
  hard_v_limit: 4.0
  hard_r_limit: 2.5
```

## 14.4 `ScenarioConfig`

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
  goal_radius: 3.0
  capture_radius: 4.0
  n_defenders: 1
  n_obstacles: 3
  obstacle_radius_min: 2.0
  obstacle_radius_max: 5.0
  spawn_clearance: 8.0
  goal_clearance: 8.0
```

说明：

- `goal_radius` / `attacker_radius` / `defender_radius` / obstacle 半径只用于生成真值对象
- 终止判据从 `WorldState` 读取真值几何
- `capture_radius` 是任务参数，可由 termination 读取配置

## 14.5 `ObservationConfig`

```yaml
observation:
  sensing_radius: 35.0
  max_defenders: 4
  max_obstacles: 8
  dtype: float32
```

## 14.6 `RewardConfig`

```yaml
reward:
  progress_weight: 1.0
  goal_reward: 100.0
  capture_penalty: -100.0
  collision_penalty: -100.0
  boundary_penalty: -100.0
  numerical_failure_penalty: -100.0
  time_penalty: -0.01
  control_l2_weight: -0.001
```

## 14.7 `DefenderPolicyConfig`

```yaml
defender_policy:
  type: pure_pursuit
  surge_gain: 0.8
  heading_gain: 1.2
```

---

## 15. 配置校验冻结

加载配置时必须显式校验：

1. `dt_env > 0`
2. `sim_substeps >= 1`
3. `boundary.xmin < boundary.xmax`
4. `boundary.ymin < boundary.ymax`
5. `obstacle_radius_min > 0`
6. `obstacle_radius_max >= obstacle_radius_min`
7. `n_defenders >= 0`
8. `n_obstacles >= 0`
9. `n_defenders <= max_defenders`
10. `n_obstacles <= max_obstacles`
11. `spawn_clearance >= 0`
12. `goal_clearance >= 0`
13. 当前边界尺寸必须允许至少容纳 attacker、goal 和基础 clearance
14. 当前边界尺寸必须允许 obstacle 生成上限的最小几何可行布置；若明显不可能，直接报错

v0.1 中至少要对第 9、10、11、12 条做明确实现，对第 13、14 条做保守可行性检查。

---

## 16. 核心类与接口冻结

## 16.1 `config.py`

```python
@dataclass(frozen=True, slots=True)
class ActionConfig: ...

@dataclass(frozen=True, slots=True)
class DynamicsConfig: ...

@dataclass(frozen=True, slots=True)
class BoundaryConfig: ...

@dataclass(frozen=True, slots=True)
class ScenarioConfig: ...

@dataclass(frozen=True, slots=True)
class ObservationConfig: ...

@dataclass(frozen=True, slots=True)
class RewardConfig: ...

@dataclass(frozen=True, slots=True)
class EnvConfig: ...

@dataclass(frozen=True, slots=True)
class DefenderPolicyConfig: ...

@dataclass(frozen=True, slots=True)
class ProjectConfig: ...


def load_config(path: str | Path) -> ProjectConfig: ...
```

## 16.2 `dynamics/fossen3dof.py`

```python
class Fossen3DOFDynamics:
    def __init__(self, cfg: DynamicsConfig, action_cfg: ActionConfig) -> None: ...

    def step(self, state: USVState, action: np.ndarray, dt: float) -> USVState: ...
```

要求：

- 不原地修改 `state`
- 返回新 `USVState`

## 16.3 `scenarios/generator.py`

```python
class ScenarioGenerator:
    def __init__(self, cfg: ProjectConfig) -> None: ...

    def generate(self, seed: int) -> WorldState: ...
```

## 16.4 `policies/base.py`

```python
class DefenderPolicy(Protocol):
    def act(self, defender: USVState, world: WorldState) -> np.ndarray: ...
```

## 16.5 `policies/defender_pursuit.py`

```python
class PurePursuitDefenderPolicy:
    def __init__(self, cfg: DefenderPolicyConfig) -> None: ...

    def act(self, defender: USVState, world: WorldState) -> np.ndarray: ...
```

## 16.6 `core/simulator.py`

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

冻结要求：

- 不原地修改输入 world
- 首次真实终止事件触发即停止 substep 循环

## 16.7 `observation/visibility.py`

```python
@dataclass(frozen=True, slots=True)
class VisibleEntities:
    defenders: tuple[USVState, ...]
    obstacles: tuple[CircularObstacle, ...]


class VisibilityFilter:
    def __init__(self, cfg: ObservationConfig) -> None: ...

    def select(self, world: WorldState) -> VisibleEntities: ...
```

## 16.8 `observation/builder.py`

```python
class ObservationBuilder:
    def __init__(self, cfg: ObservationConfig) -> None: ...

    @property
    def observation_space(self) -> gym.Space: ...

    def build(self, world: WorldState) -> dict[str, np.ndarray]: ...
```

## 16.9 `reward/attack_defense_reward.py`

```python
class AttackDefenseReward:
    def __init__(self, cfg: RewardConfig) -> None: ...

    def compute(
        self,
        prev_world: WorldState,
        world: WorldState,
        events: StepEvents,
        attacker_action: np.ndarray,
        termination_reason: str,
    ) -> RewardBreakdown: ...
```

## 16.10 `termination/checker.py`

```python
@dataclass(frozen=True, slots=True)
class TerminationResult:
    terminated: bool
    truncated: bool
    reason: str
    is_success: bool


class TerminationChecker:
    def __init__(self, cfg: ProjectConfig) -> None: ...

    def check(self, world: WorldState, events: StepEvents) -> TerminationResult: ...
```

## 16.11 `logging/rollout.py`

`RolloutRecorder` API 在 v0.1 中冻结为：

```python
class RolloutRecorder:
    def reset(self) -> None: ...

    def start_episode(
        self,
        world: WorldState,
        obs: dict[str, np.ndarray],
        info: dict,
    ) -> None: ...

    def record_step(
        self,
        world: WorldState,
        obs: dict[str, np.ndarray],
        action: np.ndarray,
        info: dict,
    ) -> None: ...

    def finalize_episode(self) -> dict: ...
```

`start_episode(...)` 是必需的，因为初始最小距离等统计不能漏掉。

## 16.12 `envs/attack_defense_env.py`

```python
class AttackDefenseEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, cfg: ProjectConfig) -> None: ...

    def reset(self, *, seed: int | None = None, options: dict | None = None): ...

    def step(self, action: np.ndarray): ...

    def render(self): ...

    def close(self): ...
```

说明：

- `render_modes` 不放 `None`
- v0.1 可先不实现实际渲染

---

## 17. reset / step 权威流程

### 17.1 `reset()`

1. 选定 seed
2. `ScenarioGenerator.generate(seed)` 生成初始 `WorldState`
3. `ObservationBuilder.build(world)` 生成 obs
4. 生成 reset info
5. `RolloutRecorder.reset()`
6. `RolloutRecorder.start_episode(world, obs, info)`
7. 返回 `obs, info`

### 17.2 `step(action)`

1. 保存 `prev_world`
2. `WorldSimulator.step(world, action)` 得到 `next_world, events`
3. `TerminationChecker.check(next_world, events)` 得到 `termination_result`
4. `ObservationBuilder.build(next_world)`
5. `AttackDefenseReward.compute(prev_world, next_world, events, action, termination_result.reason)`
6. 组装 `info`
7. `RolloutRecorder.record_step(...)`
8. 若 episode 结束，可 `finalize_episode()`
9. 返回五元组

---

## 18. Info / Log 字段冻结

### 18.1 `reset()` 的 `info`

至少包含：

- `seed`
- `scenario_id`
- `goal_distance`
- `min_defender_distance`
- `min_obstacle_clearance`

### 18.2 `step()` 的 `info`

#### 基础字段

- `step_count`
- `sim_time`
- `scenario_id`
- `seed`

#### 几何/事件字段

- `goal_distance`
- `min_defender_distance`
- `min_obstacle_clearance`
- `goal_reached`
- `captured`
- `obstacle_collision`
- `out_of_bounds`
- `numerical_failure`

#### reward breakdown 字段

- `reward_total`
- `reward_progress`
- `reward_goal`
- `reward_capture`
- `reward_collision`
- `reward_boundary`
- `reward_numerical_failure`
- `reward_time`
- `reward_control`

#### 终止字段

- `is_success`
- `termination_reason`

### 18.3 episode summary 最小字段

- `seed`
- `scenario_id`
- `episode_length`
- `return`
- `is_success`
- `termination_reason`
- `min_goal_distance`
- `min_defender_distance`
- `min_obstacle_clearance`

---

## 19. 场景生成冻结规则

场景生成器必须满足：

- 同一 seed 可复现
- attacker / defender / obstacle / goal 初始不重叠
- attacker 初始不在 goal 区域内
- attacker 初始不在 capture 区域内
- attacker 初始不越界
- `entity_id` 在 episode 内稳定

### 19.1 几何真值单一来源

v0.1 中，几何真值以 `WorldState` 为准：

- `goal radius`：读 `world.goal.radius`
- `attacker radius`：读 `world.attacker.radius`
- `defender radius`：读 `world.defenders[i].radius`
- `obstacle radius`：读 `world.obstacles[i].radius`

配置只用于：

- 初始化这些对象
- 做默认值与生成约束

---

## 20. 第一批 TODO

| ID | 任务 | 输出 | 验收标准 |
|---|---|---|---|
| T01 | 建立项目骨架 | 目录与空模块 | import 路径正确 |
| T02 | 实现配置系统 | `config.py` + `configs/v0_1_default.yaml` | 能加载并校验配置 |
| T03 | 实现不可变状态结构 | `core/types.py` | `WorldState` 无业务逻辑字段 |
| T04 | 实现数学辅助函数 | `core/math_utils.py` | 角度、旋转、距离计算正确 |
| T05 | 实现 `StepEvents` | `core/events.py` | 足以支撑 reward/termination |
| T06 | 实现简化 3-DOF 动力学 | `dynamics/fossen3dof.py` | Forward Euler + soft/hard limit 语义正确 |
| T07 | 实现场景生成器 | `scenarios/generator.py` | 同 seed 可复现，初始状态合法 |
| T08 | 实现 defender 默认策略 | `policies/defender_pursuit.py` | 能稳定输出动作 |
| T09 | 实现 world simulator | `core/simulator.py` | 多 substep + 首次终止即停 生效 |
| T10 | 实现可见性筛选 | `observation/visibility.py` | goal 始终可见，其他按 sensing radius |
| T11 | 实现 observation builder | `observation/builder.py` | shape / dtype / order / mask 完全匹配 |
| T12 | 实现 termination checker | `termination/checker.py` | 终止优先级和 time_limit 规则正确 |
| T13 | 实现 reward 模块 | `reward/attack_defense_reward.py` | 公式与优先级正确 |
| T14 | 实现 rollout recorder | `logging/rollout.py` | 包含 `start_episode(...)` |
| T15 | 实现 gym env | `envs/attack_defense_env.py` | reset/step 流程正确 |
| T16 | 写 smoke tests | `tests/smoke/` | 0 defender / 1 defender 场景可跑通 |

---

## 21. V0.1 验收标准

### 21.1 接口正确性

- env 满足 gymnasium reset/step 语义
- action / observation 与文档冻结定义一致
- `WorldState` 保持只存真值

### 21.2 数值稳定性

- 默认配置下连续运行多个 episode 不出现崩溃
- `numerical_failure` 不是常态

### 21.3 可复现性

- 同一 seed 生成同一场景
- 同一 seed + 同一动作序列生成同一轨迹

### 21.4 语义正确性

- goal 始终可见
- substep 首次终止即停
- time limit 后判
- reward 终止项不叠加
- 几何真值读取自 `WorldState`

### 21.5 工程边界正确

- 不允许把 reward / observation / termination 逻辑塞回 `WorldState`
- 不允许对输入 world/state 原地修改
- 不允许再引入第二套 env action 语义

---

## 22. 立即开发指令

从本文档写完开始，v0.1 直接按本文开发，无需再等待文档审核。

开发过程中若出现局部实现选择，只允许在**不违反本文冻结约束**的前提下做最小决策。