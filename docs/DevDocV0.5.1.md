> last update: 2026-03-25 11:18:00
> modifier: Codex

# DevDocV0.5.1

> 本文档是 USV Sim 项目的 **V0.5.1 开发文档**。
>
> 它建立在 `docs/devREADEME.md`、`docs/FinalDevDocV0.1.md`、`docs/DevDocV0.2.md`、`docs/DevDocV0.3.md`、`docs/DevDocV0.4.md`、`docs/DevDocV0.5.md` 与当前 `V0.5` 代码状态基础上，用于定义 **V0.5.1 的核心目标：补一个控制能力更强的 controller，并新增一个只考虑运动学的 sibling env，使规划效果与控制效果可以被清晰拆分观察**。
>
> 本版文档基于进一步讨论，对 `V0.5.1` 的统一局部规划输出形式作出明确收敛：
>
> - 不再把 planner-facing canonical output 定义为 `desired_course + desired_speed`
> - 而是定义为更适合当前 project、且更贴近现有局部规划器最大公共部分的：
>   **`DesiredVelocityReference(u_d, r_d)`**
>
> 若 V0.5.1 文档与 V0.1~V0.5 文档冲突：
>
> - **未被 V0.5.1 显式修改的内容，继续继承 V0.1~V0.5**
> - **被 V0.5.1 显式新增或调整的内容，以本文为准**

---

## 1. V0.5.1 版本定位

### 1.1 V0.5.1 核心目标

V0.5 已经完成：

- planning / guidance / controller 的最小分层
- `goal_seeking` 与 `apf` 的 controller-backed 路径
- `play.py` / `evaluate.py` / benchmark 外部入口保持稳定

但在实际 `play` 观察中，当前 controller 仍然存在明显问题：

- 轨迹侧滑明显
- 船头角度变化与实际速度方向并不一致
- planner 的几何效果被 controller 与 dynamics 混在一起，难以单独判断

因此，V0.5.1 的目标冻结为：

1. **为动态 env 引入一个控制能力更强、能显式抑制侧滑的 controller**
2. **新增一个只考虑运动学的 sibling env，使 planner 输出可以直接被执行，从而直观看见规划器效果**
3. **重新整理 planner / controller / env 的分层接口，使 planner 与 controller 可以耦合但不紧密耦合**

### 1.2 V0.5.1 工程意义

V0.5.1 要解决的不是“再接一个新算法”，而是两个更基础的问题：

#### A. 当前动态 env 中，controller 太弱

现有 `HeadingSpeedTrackingController` 只利用：

- `u`
- `r`

而没有显式处理：

- `v`
- 侧滑角
- 速度方向与船首方向不一致的问题

因此它无法很好地把规划器的几何目标稳定执行出来。

#### B. 当前 project 里缺少 planner-only 观察通道

现有 env 默认嵌入了动力学推进，因此：

- planner 输出是否好
- controller 是否把 planner 跟住

在可视化和评估里是混在一起的。

如果存在一个：

- 场景语义完全相同
- 但只执行运动学传播

的 env，那么 planner 输出的效果就能被直接观察。

---

## 2. V0.5.1 范围与非目标

### 2.1 V0.5.1 范围

V0.5.1 范围冻结为以下四类内容：

#### A. 动态 env 侧新增 stronger controller

在当前动态 env 中，新增一个显式考虑侧滑/横向速度影响的 controller，用于替换或补充当前简单 `HeadingSpeedTrackingController`。

#### B. 新增运动学 env

新增一个与当前 `AttackDefenseEnv` 场景语义一致的 sibling env，但推进内核改为：

- 速度
- 角速度
- `dt`

直接驱动的运动学传播，而不是 force-level 动力学传播。

#### C. 重新定义 planner-facing 输出

将当前 V0.5 更偏 controller 视角的 reference：

- `desired_heading_error`
- `desired_surge_speed`

升级为更适合作为局部规划器统一输出的 reference：

- `u_d`
- `r_d`

即：

```python
DesiredVelocityReference:
    desired_surge_speed
    desired_yaw_rate
```

#### D. 继续保持现有外部入口稳定

尽量复用现有：

- `play.py`
- `evaluate.py`
- benchmark runner / evaluator
- scenario generator
- observation builder
- termination / recorder / rendering

### 2.2 V0.5.1 明确不做

V0.5.1 不做以下内容：

- 不重写 V0.1 的真值 3-DOF 动力学公式
- 不重做 V0.5 的 guidance/controller/policy 总分层
- 不在 V0.5.1 第一阶段直接上 MPC 作为主 controller
- 不在 V0.5.1 第一阶段引入完整 RRT / MPC / CBF 算法实现
- 不让纯运动学 env 取代当前动态 env
- 不引入新的 GUI 或 dashboard
- 不在 V0.5.1 第一阶段重做 `sim_substeps` 主时序

---

## 3. 当前问题分析

## 3.1 当前 controller 为什么控制不住

当前 controller 实现见：

- `src/usv_sim/controllers/heading_speed.py`

它的主要控制量是：

- `desired_heading_error`
- `desired_surge_speed`

并利用当前：

- `u`
- `r`

生成：

- `surge_cmd`
- `yaw_cmd`

但它没有显式利用：

- `v`
- 侧滑角
- 航迹方向与船首方向不一致的问题

这意味着：

- controller 只在控船首方向与前进速度
- 没有真正控“实际速度方向”

对于 underactuated 3-DOF USV 来说，这是当前 `play` 中明显侧滑的直接来源。

## 3.2 当前 planner/controller 耦合仍偏紧

V0.5 引入了：

- `HeadingSpeedReference`

这是比 V0.4 更好的分层，但它仍然更偏 controller 视角，因为：

- `desired_heading_error` 是一个相对当前姿态的误差量

这意味着：

- planner 其实在为当前 controller 生成 reference
- 而不是生成一个更独立的局部运动目标

如果 future 继续接更多局部规划器，继续沿用 `heading_error` 作为统一输出，会增加适配耦合。

## 3.3 为什么统一局部规划输出应收敛到 `(u_d, r_d)`

本次讨论后的结论是：

> 对当前 project 中“局部规划器 / 局部引导器”这一层来说，最大公共部分更接近 **期望 surge 速度 `u_d` 与期望偏航角速度 `r_d`**，而不是更高层的 course/path/trajectory。

原因如下：

### A. 它更贴近当前已有方法

当前 V0.5 中的：

- `goal_guidance`
- `apf_guidance`

已经天然接近：

- 由目标/合力大小生成速度意图
- 由 heading error 生成角速度意图

只需很少逻辑改动就能收敛到：

\[
(u_d,\ r_d)
\]

### B. 它是很多局部规划器的共同输出形式

对于局部规划器而言，常见输出往往可以收敛为：

- 期望前进速度
- 期望角速度

这与移动机器人常用的：

\[
(v,\ \omega)
\]

是同一类语义，只是当前 USV 项目里更自然写成：

\[
(u,\ r)
\]

### C. 它对动态 env 和运动学 env 都自然

#### 在动态 env 中

planner 输出：

\[
(u_d,\ r_d)
\]

再由 stronger controller 跟踪它，输出：

\[
[surge\_cmd,\ yaw\_cmd]
\]

#### 在运动学 env 中

planner 输出：

\[
(u_d,\ r_d)
\]

可以直接作为 env 的上层输入，被直接执行。

因此：

- planner 不需要知道 controller 细节
- controller 不需要改变 planner 的输出协议
- 运动学 env 可以直接体现 planner 效果

---

## 4. Controller 选型结论

## 4.1 候选 controller 排序

结合当前代码、项目阶段与实现复杂度，controller 候选排序如下：

### 第一选择：Sideslip-Compensated Surge-Yaw Velocity Tracking Controller

这是 V0.5.1 主方案。

特点：

- 显式考虑侧滑角或横向速度
- 控制目标是跟踪：
  - 期望 surge 速度 \(u_d\)
  - 期望 yaw rate \(r_d\)
- 比当前简单 controller 更贴合当前统一输出形式 `(u_d, r_d)`
- 复杂度明显低于 MPC / backstepping 全套实现

### 第二选择：Surge-Yaw PD Controller with Sideslip Damping

这是保守 fallback 方案。

特点：

- 基本延续当前 controller 结构
- 但显式加入 `v` 或侧滑角反馈
- 改动最小，但效果一般不如更完整的侧滑补偿 controller

### 第三选择：Backstepping-Style Underactuated USV Tracker

理论上更强，但 V0.5.1 第一阶段不推荐。

原因：

- 公式和调参成本明显更高
- 会把版本复杂度快速拉高

### 第四选择：MPC-lite / Linear MPC

不推荐作为 V0.5.1 主方案。

原因：

- 当前版本的核心问题还是分层和可解释性
- 现在就上 MPC 会过早引入额外复杂度

## 4.2 V0.5.1 主 controller 冻结结论

V0.5.1 主 controller 选择冻结为：

> **Sideslip-Compensated Surge-Yaw Velocity Tracking Controller**

它的设计目标是：

- 显式抑制侧滑
- 更稳定地跟踪局部规划器输出的 `(u_d, r_d)`
- 提高 `play` 中 planner 效果的可视化可解释性

## 4.3 为什么不把 MPC 作为主方案

因为 V0.5.1 当前最需要解决的是：

- 让控制效果比 V0.5 明显更好
- 同时不要破坏当前项目的最小改动原则

在这个阶段，MPC 太重，性价比不高。

---

## 5. V0.5.1 核心设计结论

## 5.1 planner-facing 输出正式升级

V0.5 的：

- `HeadingSpeedReference(desired_heading_error, desired_surge_speed)`

更偏 controller 视角。

V0.5.1 建议把局部规划器的 canonical output 升级为：

```python
DesiredVelocityReference:
    desired_surge_speed
    desired_yaw_rate
```

也可以记为：

\[
(u_d,\ r_d)
\]

### 设计意图

这样做的好处是：

- 更贴近当前局部规划器的最大公共输出
- 更适合作为 current planner/controller 的统一接口
- 运动学 env 中可以直接执行
- 动态 env 中可以直接被 controller 跟踪

## 5.2 动态 env 保持低层 action 不变

当前动态 env 中：

- env action 仍保持 `[surge_cmd, yaw_cmd]`

V0.5.1 不改这一点。

也就是说，动态 env 的链路应变成：

```text
Local Planner
    -> DesiredVelocityReference(u_d, r_d)
    -> Stronger Controller
    -> [surge_cmd, yaw_cmd]
    -> AttackDefenseEnv
```

## 5.3 运动学 env 直接执行 planner 输出

新增纯运动学 env 后，链路应变成：

```text
Local Planner
    -> DesiredVelocityReference(u_d, r_d)
    -> AttackDefenseKinematicEnv
```

即：

- planner 输出可以直接作为运动学 env 的上层输入
- 不再经过 controller

这正是“planner 和 controller 可以耦合但不紧密耦合”的关键。

## 5.4 纯运动学 env 必须是 sibling env，而不是 wrapper

V0.5.1 冻结结论：

> 新环境应作为 **sibling env** 新增，而不是对现有 `AttackDefenseEnv` 再套 wrapper。

推荐新增：

- `src/usv_sim/envs/attack_defense_kinematic_env.py`

原因：

- 动态 env 与运动学 env 的动作语义不同
- 推进内核不同
- 若强行做成一个双模式 env，会增加后续维护风险

---

## 6. 动态 env 新 controller 设计

## 6.1 当前 controller 的控制对象

当前 V0.5 controller 实际控制的是：

- heading error
- surge speed error

而 V0.5.1 新 controller 应控制的是：

- surge speed error
- yaw rate error
- 侧滑量

## 6.2 关键状态量

定义：

- 期望 surge 速度：
\[
u_d
\]

- 当前 surge 速度：
\[
u
\]

- 期望 yaw rate：
\[
r_d
\]

- 当前 yaw rate：
\[
r
\]

- 侧滑角：
\[
\beta = \arctan2(v,\ u)
\]

## 6.3 推荐最小控制律

V0.5.1 第一阶段建议采用如下最小控制律：

### yaw 通道

\[
yaw\_cmd
=
\mathrm{clip}
\left(
k_r (r_d - r) - k_\beta \beta,\ -1,\ 1
\right)
\]

如果希望更进一步利用横向速度，也可扩成：

\[
yaw\_cmd
=
\mathrm{clip}
\left(
k_r (r_d - r) - k_\beta \beta - k_v v,\ -1,\ 1
\right)
\]

### surge 通道

\[
surge\_cmd
=
\mathrm{clip}
\left(
k_u \frac{u_d - u}{u_{d,\max}},\ -1,\ 1
\right)
\]

其中：

- \(u_d\)：期望速度
- \(u_{d,\max}\)：controller 允许的最大参考速度

### 解释

- `k_r`：跟踪期望 yaw rate
- `k_beta`：显式抑制侧滑
- `k_v`：可选，用于额外抑制横向速度
- `k_u`：控制 surge 跟踪

## 6.4 为什么这里不再直接使用 heading error

因为一旦 planner-facing 输出冻结为：

\[
(u_d,\ r_d)
\]

那么 controller 的职责就应该是：

- 跟踪期望速度
- 跟踪期望角速度

而不是继续回退到：

- 重新解释 planner 输出为 heading error

这样职责更清楚，也更利于 planner/controller 解耦。

---

## 7. 纯运动学 env 设计

## 7.1 应保持一致的部分

以下内容应尽量与当前动态 env 保持一致：

- 场景语义
- `ScenarioGenerator`
- `WorldState` 数据结构
- `ObservationBuilder`
- `TerminationChecker`
- `RolloutRecorder`
- `Simple2DRenderer`
- 大部分 reward / info / benchmark 外壳

## 7.2 应不同的部分

纯运动学 env 应只替换：

- 推进内核
- 动作语义

即从：

```text
WorldSimulator + Fossen3DOFDynamics
```

替换为：

```text
KinematicWorldSimulator + KinematicPropagator
```

## 7.3 运动学 env 的 action 语义

V0.5.1 建议其执行语义就是：

\[
a_{kin} = [u_d,\ r_d]
\]

其中：

- \(u_d\)：期望 surge 速度
- \(r_d\)：期望偏航角速度

这与 planner-facing canonical output 完全一致。

这意味着：

- planner 不需要为运动学 env 再写一层 adapter

## 7.4 运动学状态传播

V0.5.1 第一阶段建议采用最直观的传播：

\[
\psi_{k+1} = \mathrm{wrap}(\psi_k + r_d \Delta t)
\]

\[
u_{k+1} = u_d
\]

\[
v_{k+1} = 0
\]

\[
r_{k+1} = r_d
\]

\[
x_{k+1} = x_k + \Delta t \cdot u_{k+1} \cos(\psi_k)
\]

\[
y_{k+1} = y_k + \Delta t \cdot u_{k+1} \sin(\psi_k)
\]

### 解释

这样做的目的不是高保真，而是：

- 让 planner 输出能被直接看见
- 把 controller 与 force-level dynamics 的影响拿掉

## 7.5 观测兼容策略

为了继续复用 `ObservationBuilder`，运动学 env 中：

- `u = u_d`
- `v = 0`
- `r = r_d`

这样当前 observation schema 可以继续使用，无需重写。

## 7.6 defender 在运动学 env 中的处理

当前动态 env defender 使用：

- `PurePursuitDefenderPolicy`

它输出的是低层 action，不适合直接复用到运动学 env。

因此 V0.5.1 建议新增：

- `KinematicPurePursuitDefenderPolicy`

其作用是：

- 保持同样的追击几何意图
- 但输出改成：
\[
(u_d,\ r_d)
\]

这样可以保证：

- 场景仍然一致
- defender 行为语义仍然相似

---

## 8. 新旧两种 env 的关系

## 8.1 动态 env

用途：

- 测试 planner + controller + dynamics 的整体效果
- 观察控制能力是否足够强

链路：

```text
Local Planner
    -> DesiredVelocityReference(u_d, r_d)
    -> Stronger Controller
    -> Dynamic Env
```

## 8.2 运动学 env

用途：

- 直接观察 planner 本身输出的效果
- 做 planner-only sanity check
- 给 planner 提供接近“理想执行”下的参考结果

链路：

```text
Local Planner
    -> DesiredVelocityReference(u_d, r_d)
    -> Kinematic Env
```

## 8.3 两者的关系

V0.5.1 不把这两个 env 设计成竞争关系，而是设计成：

- 同一 planner 输出
- 两个不同执行后端

这样就能比较：

- planner 单独效果
- planner + controller + dynamics 效果

---

## 9. 最小改动的模块设计建议

## 9.1 推荐新增文件

建议新增：

- `src/usv_sim/controllers/velocity_tracking.py`
- `src/usv_sim/envs/attack_defense_kinematic_env.py`
- `src/usv_sim/core/kinematic_simulator.py`
- `src/usv_sim/dynamics/kinematic3dof.py`
- `src/usv_sim/policies/defender_pursuit_kinematic.py`
- `src/usv_sim/envs/factory.py`

## 9.2 推荐扩展文件

建议扩展：

- `src/usv_sim/guidance/reference.py`
  新增 `DesiredVelocityReference`

- `src/usv_sim/policies/factory.py`
  增加 planner/controller 组合方式与 env backend 的兼容逻辑

- `play.py`
- `evaluate.py`
- `src/usv_sim/benchmark/runner.py`
  从直接实例化 `AttackDefenseEnv` 过渡到 `create_env(cfg, ...)`

## 9.3 推荐保持不变的模块

尽量保持不变：

- `src/usv_sim/observation/*`
- `src/usv_sim/reward/*`
- `src/usv_sim/termination/*`
- `src/usv_sim/rendering/*`
- `src/usv_sim/scenarios/generator.py`

---

## 10. 配置系统建议

## 10.1 新 controller 配置

建议新增：

```yaml
velocity_tracking_controller:
  type: sideslip_compensated_velocity
  surge_gain: 0.8
  yaw_rate_gain: 1.6
  yaw_rate_damping: 0.25
  sideslip_gain: 0.4
  desired_surge_speed_max: 3.0
  desired_yaw_rate_max: 1.2
```

## 10.2 env backend 配置

建议新增：

```yaml
env:
  backend: dynamic | kinematic
```

默认保持：

```yaml
backend: dynamic
```

这样：

- 旧配置默认继续走动态 env
- 新增配置可以显式选择运动学 env

## 10.3 planner-facing 输出配置

V0.5.1 建议把局部规划器统一输出收敛到：

- `DesiredVelocityReference`

因此旧的：

- `HeadingSpeedReference`

在 V0.5.1 中应视为：

- 仍可兼容
- 但不再是 future 局部规划器的首选 canonical output

---

## 11. 测试与验收建议

## 11.1 stronger controller 的验收

V0.5.1 应新增以下 controller 评估指标：

- `mean_abs_sideslip_angle`
\[
\mathrm{mean}(|\beta|)
\]

- `mean_abs_sway_velocity`
\[
\mathrm{mean}(|v|)
\]

- `success_rate`

- `mean_final_goal_distance`

### 验收要求

在固定场景和固定 seeds 上，相比当前 V0.5 controller：

- `mean_abs_sideslip_angle` 降低
- `mean_abs_sway_velocity` 降低
- 成功率不降低

## 11.2 运动学 env 的验收

至少应验证：

- 与动态 env 使用同一 scenario generator
- observation key / shape / dtype 保持兼容
- planner 给定相同 `DesiredVelocityReference` 时，运动学 env 可以直接推进
- `play.py` / `evaluate.py` 仅通过 env factory 切换 backend，不需要重写外部命令

## 11.3 planner / controller 解耦验收

至少应验证：

- 同一个 planner 输出可以同时喂给：
  - dynamic env + controller
  - kinematic env

- planner 不需要知道 controller 的具体增益

---

## 12. 推荐开发顺序

1. **先冻结 `DesiredVelocityReference` 语义**
2. **实现 stronger velocity-tracking controller**
3. **把现有 `goal_seeking` / `apf` guidance 输出升级到 `u_d, r_d` 语义**
4. **新增 kinematic propagator 与 kinematic simulator**
5. **新增 `AttackDefenseKinematicEnv`**
6. **补 `create_env(...)` 工厂**
7. **让 `play.py` / `evaluate.py` 通过 env factory 选择 backend**
8. **补 controller 指标测试与 kinematic env 测试**

---

## 13. V0.5.1 第一批 TODO

| ID | 任务 | 输出 | 验收标准 |
|---|---|---|---|
| T511 | 冻结局部规划统一输出 | `DesiredVelocityReference` | planner 输出可直接供两个 env backend 使用 |
| T512 | 实现 stronger controller | `velocity_tracking.py` | 比 V0.5 controller 侧滑更小 |
| T513 | 升级 guidance 输出 | `goal/apf guidance` | 输出从 heading-error 视角升级为 `u_d, r_d` 视角 |
| T514 | 实现 kinematic propagator | `kinematic3dof.py` | 能按速度+角速度+dt 推进状态 |
| T515 | 实现 kinematic simulator | `core/kinematic_simulator.py` | 与当前 simulator 结构相似但只做运动学推进 |
| T516 | 实现 sibling env | `attack_defense_kinematic_env.py` | 与当前场景/观测/终止语义兼容 |
| T517 | 实现 kinematic defender policy | `defender_pursuit_kinematic.py` | defender 在 kinematic env 中可运行 |
| T518 | 补 env factory | `envs/factory.py` | `play.py` / `evaluate.py` 可按 config 选择 backend |
| T519 | 补 controller 评估指标 | tests + metrics | 能量化 V0.5.1 controller 改进效果 |
| T520 | 补 kinematic env 回归测试 | tests/integration | planner-only 路径可稳定运行 |

---

## 14. V0.5.1 验收标准

### 14.1 功能验收

V0.5.1 完成时至少满足：

- 存在一个显式考虑侧滑的 stronger controller
- 存在一个只考虑运动学的 sibling env
- planner 输出可直接供 kinematic env 使用
- planner 输出也可供 dynamic env 的 controller 使用

### 14.2 架构验收

V0.5.1 完成时必须满足：

- 当前动态 env 不被重写成双模式大杂烩
- 运动学 env 为 sibling env
- env / simulator / dynamics 的职责边界更清晰
- `play.py` / `evaluate.py` 外部命令形式尽量不变

### 14.3 研究可用性验收

V0.5.1 至少应达到：

1. 可以直接看见 planner 在理想运动学执行下的效果
2. 可以单独评价 stronger controller 是否改善了侧滑
3. 可以清晰区分“planner 有问题”还是“controller 没跟住”

---

## 15. 推荐验收命令

V0.5.1 完成后建议形成如下入口：

```bash
conda run -n RL python play.py --config configs/v0_3_goal_only.yaml --policy goal_seeking
conda run -n RL python play.py --config configs/v0_5_1_goal_only_kinematic.yaml --policy goal_seeking

conda run -n RL python evaluate.py --config configs/v0_5_1_goal_only_dynamic.yaml --policy goal_seeking --output-dir outputs/v0_5_1_dynamic
conda run -n RL python evaluate.py --config configs/v0_5_1_goal_only_kinematic.yaml --policy goal_seeking --output-dir outputs/v0_5_1_kinematic

conda run -n RL python -m pytest tests/unit tests/integration -q
```

---

## 16. 最终结论

V0.5.1 的关键不是“再加一个更复杂的 controller”，而是：

- **让 controller 真正能把 planner 的局部速度指令执行出来**
- **让 planner 的效果可以脱离 dynamics 单独观察**
- **让 planner 输出成为 dynamic env 与 kinematic env 的共同上层接口**

如果说：

- V0.5 解决的是“controller 应该放在 policy 层，而不是 env 层”

那么 V0.5.1 要解决的就是：

- **controller 怎么从简单 heading tracking 升级到 velocity tracking + sideslip compensation**
- **planner 输出怎么从 controller-oriented 升级为局部规划器统一输出 `(u_d, r_d)`**
- **dynamic env 和 kinematic env 怎么共享同一套上层 planner 输出**

只要 V0.5.1 按本文执行，USV Sim 就会从“最小 planner/controller 分层平台”进一步升级为“**可区分 planner 效果与 controller 效果的双后端验证平台**”。  

