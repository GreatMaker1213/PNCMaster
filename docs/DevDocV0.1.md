# DevDocV0.1

> 本文档是 USV Sim v0.1 的**冻结附录**。
> 在 v0.1 正式开始编码前，以下 6 件事在本文档中冻结：
>
> 1. state 定义
> 2. action 定义
> 3. observation schema
> 4. 坐标/单位约定
> 5. 终止阈值
> 6. info/log 字段
>
> 若实现与本文档冲突，以本文档为准。

---

## 1. State 定义

### 1.1 设计原则

v0.1 中，`WorldState` 仅表示**当前时刻真值**，不承担业务逻辑。

冻结要求：

- `WorldState` 只存真值
- 不含 observation
- 不含 reward
- 不含 terminated/truncated
- 不含日志字段
- 不含上一时刻缓存
- 不含事件缓存

### 1.2 `USVState`

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
```

字段定义：

| 字段 | 含义 | 单位 | 约束 |
|---|---|---:|---|
| `entity_id` | 实体唯一 ID | - | episode 内唯一且稳定 |
| `x` | 世界坐标系位置 x | m | 有限实数 |
| `y` | 世界坐标系位置 y | m | 有限实数 |
| `psi` | 航向角 | rad | 始终规范化到 `(-pi, pi]` |
| `u` | 体坐标系 surge 速度 | m/s | 有限实数 |
| `v` | 体坐标系 sway 速度 | m/s | 有限实数 |
| `r` | 偏航角速度 | rad/s | 有限实数 |
| `radius` | 圆形碰撞半径 | m | `> 0` |

### 1.3 `CircularObstacle`

```python
@dataclass(slots=True)
class CircularObstacle:
    entity_id: int
    x: float
    y: float
    radius: float
```

### 1.4 `GoalRegion`

```python
@dataclass(slots=True)
class GoalRegion:
    x: float
    y: float
    radius: float
```

### 1.5 `RectBoundary`

```python
@dataclass(slots=True)
class RectBoundary:
    xmin: float
    xmax: float
    ymin: float
    ymax: float
```

约束：

- `xmin < xmax`
- `ymin < ymax`

### 1.6 `WorldState`

```python
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

字段定义：

| 字段 | 含义 |
|---|---|
| `sim_time` | 当前仿真时间，单位 s |
| `step_count` | 当前 env step 序号，从 0 开始 |
| `seed` | 当前 episode 的随机种子 |
| `scenario_id` | 场景模板或场景实例标识 |
| `attacker` | 唯一攻击艇真值状态 |
| `defenders` | 防守艇真值状态列表 |
| `obstacles` | 圆形障碍列表 |
| `goal` | 目标区域 |
| `boundary` | 矩形边界 |

### 1.7 state 冻结规则

v0.1 中禁止向 `WorldState` 新增以下类型字段：

- reward 缓存
- observation 缓存
- terminated/truncated 缓存
- 事件缓存
- debug 绘图对象
- 训练专用字段

如需这些内容，必须放到独立模块。

---

## 2. Action 定义

### 2.1 Env Action 冻结结论

v0.1 的 env action 冻结为：**归一化低层控制输入**。

```python
action_space = gym.spaces.Box(
    low=-1.0,
    high=1.0,
    shape=(2,),
    dtype=np.float32,
)
```

语义：

```text
action[0] -> normalized surge command
action[1] -> normalized yaw moment command
```

### 2.2 动作字段解释

| 索引 | 名称 | 语义 | 范围 | dtype |
|---|---|---|---|---|
| `0` | `surge_cmd` | 归一化纵向力指令 | `[-1, 1]` | `float32` |
| `1` | `yaw_cmd` | 归一化偏航力矩指令 | `[-1, 1]` | `float32` |

### 2.3 物理映射

令配置中：

- `max_surge_force = 40.0 N`
- `max_yaw_moment = 15.0 N·m`

则环境内部映射为：

```text
tau_u = clip(action[0], -1, 1) * max_surge_force
tau_r = clip(action[1], -1, 1) * max_yaw_moment
```

### 2.4 为什么不选 `[u_ref, psi_ref]`

v0.1 不选参考量动作作为 env action，原因如下：

1. 会迫使环境内置默认控制器
2. 环境职责会变重
3. RL 与传统控制的接口边界会模糊
4. 后续切换不同低层控制器时会破坏 env 语义稳定性

因此：

- RL 直接输出 env action
- MPC / RRT / APF / 轨迹生成模块若输出参考量，必须在环境外通过 controller / adapter 转成该动作

### 2.5 defender 动作语义

防守艇策略输出动作与 attacker 完全一致：

- shape `(2,)`
- `float32`
- 归一化 `surge_cmd, yaw_cmd`

v0.1 不允许 attacker 和 defender 使用两套不同动作协议。

---

## 3. Observation Schema

### 3.1 总体形式

v0.1 observation 冻结为 `gymnasium.spaces.Dict`。

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

### 3.2 总体原则

- 所有输出 dtype 为 `np.float32`
- shape 固定
- 不可见对象使用零填充
- mask 显式给出
- 只暴露 attacker 可见对象
- 默认在 **ego frame** 下编码相对信息
- 槽位顺序在 episode 内稳定

### 3.3 对象顺序规则

#### defenders 顺序

- 场景生成时为每个 defender 分配稳定 `entity_id`
- observation 中按 `entity_id` 升序映射到固定槽位
- 不因距离变化而重排

#### obstacles 顺序

- 场景生成时为每个 obstacle 分配稳定 `entity_id`
- observation 中按 `entity_id` 升序映射到固定槽位
- 不因距离变化而重排

### 3.4 `ego`

```python
shape = (6,)
dtype = np.float32
```

字段顺序：

| idx | 名称 | 含义 | 单位 |
|---|---|---|---:|
| 0 | `u` | surge 速度 | m/s |
| 1 | `v` | sway 速度 | m/s |
| 2 | `r` | 偏航角速度 | rad/s |
| 3 | `cos_psi` | 航向角余弦 | - |
| 4 | `sin_psi` | 航向角正弦 | - |
| 5 | `speed_norm` | `sqrt(u^2+v^2)` | m/s |

说明：

- `ego` 不直接暴露绝对 `(x, y)`
- 保留 `cos_psi, sin_psi` 是为了避免角度不连续问题

### 3.5 `goal`

```python
shape = (4,)
dtype = np.float32
```

字段顺序：

| idx | 名称 | 含义 | 单位 |
|---|---|---|---:|
| 0 | `rel_x` | 目标在 attacker ego frame 下的 x | m |
| 1 | `rel_y` | 目标在 attacker ego frame 下的 y | m |
| 2 | `distance` | attacker 到目标中心距离 | m |
| 3 | `goal_radius` | 目标区域半径 | m |

### 3.6 `boundary`

```python
shape = (4,)
dtype = np.float32
```

字段顺序：

| idx | 名称 | 含义 | 单位 |
|---|---|---|---:|
| 0 | `dist_left` | attacker 到左边界距离 | m |
| 1 | `dist_right` | attacker 到右边界距离 | m |
| 2 | `dist_bottom` | attacker 到下边界距离 | m |
| 3 | `dist_top` | attacker 到上边界距离 | m |

说明：

- 采用世界系边界距离，而不是 ego frame
- 若越界，距离可以为负

### 3.7 `defenders`

默认 `max_defenders = 4`。

```python
shape = (4, 7)
dtype = np.float32
```

每个 defender 槽位字段顺序：

| idx | 名称 | 含义 | 单位 |
|---|---|---|---:|
| 0 | `rel_x` | defender 在 ego frame 下的 x | m |
| 1 | `rel_y` | defender 在 ego frame 下的 y | m |
| 2 | `rel_u` | defender 相对 surge 速度近似量 | m/s |
| 3 | `rel_v` | defender 相对 sway 速度近似量 | m/s |
| 4 | `distance` | defender 到 attacker 中心距离 | m |
| 5 | `cos_dpsi` | 航向差余弦 | - |
| 6 | `sin_dpsi` | 航向差正弦 | - |

padding 规则：

- 若该槽位无 defender，整行全 0

### 3.8 `defenders_mask`

```python
shape = (4,)
dtype = np.float32
```

语义：

- `1.0` 表示该槽位有 defender 且当前可见
- `0.0` 表示不可见或该槽位不存在对象

说明：

v0.1 不额外区分：

- “存在但不可见”
- “槽位本身空”

二者统一编码为 0。后续版本如有需要再拆。

### 3.9 `obstacles`

默认 `max_obstacles = 8`。

```python
shape = (8, 4)
dtype = np.float32
```

每个 obstacle 槽位字段顺序：

| idx | 名称 | 含义 | 单位 |
|---|---|---|---:|
| 0 | `rel_x` | obstacle 在 ego frame 下的 x | m |
| 1 | `rel_y` | obstacle 在 ego frame 下的 y | m |
| 2 | `distance` | attacker 到障碍中心距离 | m |
| 3 | `radius` | 障碍半径 | m |

padding 规则：

- 若该槽位无 obstacle，整行全 0

### 3.10 `obstacles_mask`

```python
shape = (8,)
dtype = np.float32
```

语义：

- `1.0` 表示该槽位有 obstacle 且当前可见
- `0.0` 表示不可见或该槽位不存在对象

### 3.11 可见性规则

v0.1 仅采用距离可见性：

- 若目标对象中心到 attacker 中心距离 `<= sensing_radius`，则视为可见
- 无遮挡
- 无噪声
- 360° 全向可见

### 3.12 observation space 汇总表

| key | shape | dtype | 备注 |
|---|---|---|---|
| `ego` | `(6,)` | `float32` | 自身状态 |
| `goal` | `(4,)` | `float32` | 目标相对信息 |
| `boundary` | `(4,)` | `float32` | 到边界距离 |
| `defenders` | `(4, 7)` | `float32` | defender 固定槽位特征 |
| `defenders_mask` | `(4,)` | `float32` | defender 可见 mask |
| `obstacles` | `(8, 4)` | `float32` | obstacle 固定槽位特征 |
| `obstacles_mask` | `(8,)` | `float32` | obstacle 可见 mask |

---

## 4. 坐标 / 单位约定

这一节是强制软件契约。

### 4.1 世界坐标系

采用二维右手平面约定：

- `x` 轴：向右
- `y` 轴：向上
- 世界坐标中的角度正方向：逆时针

### 4.2 船体坐标系

对于每个 USV，体坐标系定义为：

- `x_b`：船头前向
- `y_b`：船体左向
- `z_b`：纸面外，不在 v0.1 中显式使用

因此：

- `u`：沿 `x_b` 的速度（surge）
- `v`：沿 `y_b` 的速度（sway）
- `r`：绕 `z_b` 的偏航角速度（yaw rate）

### 4.3 航向角定义

- `psi = 0`：船头指向世界系 `+x`
- `psi > 0`：相对世界系逆时针旋转
- `psi < 0`：相对世界系顺时针旋转

### 4.4 角度范围

所有角度统一使用：

```text
(-pi, pi]
```

冻结规则：

- `psi` 存储时必须已规范化
- 任何角度差在使用前必须先规范化到 `(-pi, pi]`

### 4.5 单位约定

| 量 | 单位 |
|---|---|
| 长度 | m |
| 时间 | s |
| 线速度 | m/s |
| 角度 | rad |
| 角速度 | rad/s |
| 力 | N |
| 力矩 | N·m |
| 奖励 | 无量纲 |

冻结规则：

- 代码内部严禁混用 degree 与 radian
- 配置文件中的角相关参数也一律采用 rad / rad/s

### 4.6 相对坐标编码

当文档写“ego frame 下相对位置”时，定义如下：

给定世界系下相对位移：

```text
dx = x_obj - x_att
dy = y_obj - y_att
```

则 ego frame 相对位置为：

```text
rel_x =  cos(psi_att) * dx + sin(psi_att) * dy
rel_y = -sin(psi_att) * dx + cos(psi_att) * dy
```

其中：

- `rel_x > 0` 表示物体在船前方
- `rel_y > 0` 表示物体在船左侧

### 4.7 边界判定

边界采用矩形闭区域：

```text
xmin <= x <= xmax
ymin <= y <= ymax
```

但考虑船体半径，合法判定使用 **船体中心** 还是 **外接圆**，v0.1 冻结如下：

- **终止判定按船体外接圆处理**
- 即若 attacker 的圆形碰撞体任一部分越界，则记为 `out_of_bounds`

具体等价条件：

```text
x - radius < xmin
or x + radius > xmax
or y - radius < ymin
or y + radius > ymax
```

---

## 5. 终止阈值

### 5.1 默认几何参数

v0.1 默认值冻结如下：

| 参数 | 默认值 | 单位 |
|---|---:|---:|
| `attacker_radius` | 1.0 | m |
| `defender_radius` | 1.0 | m |
| `goal_radius` | 3.0 | m |
| `capture_radius` | 4.0 | m |

### 5.2 目标到达判据

记 attacker 与 goal 中心距离为：

```text
d_goal = sqrt((x_att - x_goal)^2 + (y_att - y_goal)^2)
```

则：

```text
goal_reached := d_goal <= goal_radius
```

### 5.3 障碍碰撞判据

对于任意 obstacle：

```text
d_obs_i = distance(attacker_center, obstacle_center)
```

则碰撞定义为：

```text
obstacle_collision := exists i,
    d_obs_i <= attacker_radius + obstacle_i.radius
```

### 5.4 被捕获判据

对于任意 defender：

```text
d_def_i = distance(attacker_center, defender_i.center)
```

v0.1 冻结捕获定义为：

```text
captured := exists i,
    d_def_i <= capture_radius
```

说明：

- `capture_radius` 是任务层语义，不等于圆形碰撞半径之和
- 因此 capture 可以早于实体几何接触

### 5.5 越界判据

见 4.7。

### 5.6 numerical failure 判据

出现以下任一情况，视为 `numerical_failure`：

1. 任一 attacker 状态量为 `NaN` 或 `Inf`
2. `abs(u) > hard_u_limit`
3. `abs(v) > hard_v_limit`
4. `abs(r) > hard_r_limit`
5. `abs(x)` 或 `abs(y)` 超出 `1e6`

默认 hard limit：

| 参数 | 默认值 | 单位 |
|---|---:|---:|
| `hard_u_limit` | 8.0 | m/s |
| `hard_v_limit` | 4.0 | m/s |
| `hard_r_limit` | 2.5 | rad/s |

### 5.7 terminated / truncated 规则

#### terminated
以下任一条件触发 `terminated = True`：

- `goal_reached`
- `captured`
- `obstacle_collision`
- `out_of_bounds`
- `numerical_failure`

#### truncated
以下条件触发 `truncated = True`：

- `step_count >= max_episode_steps`

冻结规则：

- `time_limit` 只能对应 `truncated`
- `terminated` 与 `truncated` 不应同时为真，除非未来版本明确重新定义；v0.1 中禁止同时为真

### 5.8 reason 枚举

`info["termination_reason"]` 在 episode 结束时必须属于以下枚举之一：

- `goal_reached`
- `captured`
- `obstacle_collision`
- `out_of_bounds`
- `numerical_failure`
- `time_limit`
- `not_terminated`

---

## 6. Info / Log 字段

### 6.1 step 返回中的 `info`

每一步的 `info` 字段冻结为以下最小集合。

#### 基础字段

| key | 类型 | 含义 |
|---|---|---|
| `step_count` | `int` | 当前 step 序号 |
| `sim_time` | `float` | 当前仿真时间 |
| `scenario_id` | `str` | 当前场景 ID |
| `seed` | `int` | 当前 episode seed |

#### 几何/事件字段

| key | 类型 | 含义 |
|---|---|---|
| `goal_distance` | `float` | 当前 attacker 到 goal 中心距离 |
| `min_defender_distance` | `float` | 当前 attacker 到最近 defender 中心距离；若无 defender，填 `inf` |
| `min_obstacle_clearance` | `float` | 当前 attacker 到最近 obstacle 表面净空；若无 obstacle，填 `inf` |
| `goal_reached` | `bool` | 当前步是否触发到达目标 |
| `captured` | `bool` | 当前步是否触发捕获 |
| `obstacle_collision` | `bool` | 当前步是否触发障碍碰撞 |
| `out_of_bounds` | `bool` | 当前步是否越界 |
| `numerical_failure` | `bool` | 当前步是否出现数值异常 |

#### reward breakdown 字段

| key | 类型 | 含义 |
|---|---|---|
| `reward_total` | `float` | 总奖励 |
| `reward_progress` | `float` | 进度奖励 |
| `reward_goal` | `float` | 到达目标奖励 |
| `reward_capture` | `float` | 捕获惩罚 |
| `reward_collision` | `float` | 碰撞惩罚 |
| `reward_boundary` | `float` | 越界惩罚 |
| `reward_time` | `float` | 时间惩罚 |
| `reward_control` | `float` | 控制惩罚 |

#### 终止字段

| key | 类型 | 含义 |
|---|---|---|
| `is_success` | `bool` | 是否成功完成任务 |
| `termination_reason` | `str` | 当前终止原因；未结束时为 `not_terminated` |

### 6.2 `reset()` 返回中的 `info`

`reset()` 的 `info` 至少包含：

| key | 类型 | 含义 |
|---|---|---|
| `seed` | `int` | 当前 episode seed |
| `scenario_id` | `str` | 场景 ID |
| `goal_distance` | `float` | 初始目标距离 |
| `min_defender_distance` | `float` | 初始最近 defender 距离 |
| `min_obstacle_clearance` | `float` | 初始最近 obstacle 净空 |

### 6.3 episode log 最小字段

若使用 `RolloutRecorder`，则 episode summary 至少应包含：

| key | 类型 | 含义 |
|---|---|---|
| `seed` | `int` | episode seed |
| `scenario_id` | `str` | 场景 ID |
| `episode_length` | `int` | 运行步数 |
| `return` | `float` | 累积奖励 |
| `is_success` | `bool` | 是否成功 |
| `termination_reason` | `str` | 终止原因 |
| `min_goal_distance` | `float` | 整个 episode 中最小目标距离 |
| `min_defender_distance` | `float` | 整个 episode 中最小 defender 距离 |
| `min_obstacle_clearance` | `float` | 整个 episode 中最小 obstacle 净空 |

### 6.4 冻结要求

v0.1 中：

- `info` 可以增补 debug 字段
- 但不能删除本节定义的最小字段
- 字段名必须保持稳定
- reward breakdown key 名必须与本节完全一致

---

## 7. 最终冻结摘要

在 v0.1 中，以下内容不得随意变动：

1. `WorldState` 只存真值
2. env action 固定为 `(2,)` 的归一化 `[surge_cmd, yaw_cmd]`
3. observation 固定为 `Dict`，并按本文给出的 key/shape/dtype 实现
4. 坐标系、正方向、角度范围、单位严格按本文执行
5. 目标、碰撞、捕获、越界、数值异常判据按本文执行
6. `info` 与最小 episode log 字段按本文执行

如果后续要改这些内容，应视为 **v0.2 级别接口变更**，不应在 v0.1 编码中途漂移。