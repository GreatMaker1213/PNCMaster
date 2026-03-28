> last update: 2026-03-27 10:15:00
> modifier: Codex

# DevDocV0.5.2

> 本文档是 USV Sim 项目的 **V0.5.2 开发文档**。
>
> 它建立在 `docs/devREADEME.md`、`docs/FinalDevDocV0.1.md`、`docs/DevDocV0.2.md`、`docs/DevDocV0.3.md`、`docs/DevDocV0.4.md`、`docs/DevDocV0.5.md`、`docs/DevDocV0.5.1.md` 与当前 `V0.5.1` 代码状态基础上，用于定义 **V0.5.2 的核心目标：修正 observation 距离语义，使障碍物/defender 的观测距离、mask 判定和 APF 距离统一回到“最近距离/净空距离”语义**。
>
> 若 V0.5.2 文档与 V0.1~V0.5.1 文档冲突：
>
> - **未被 V0.5.2 显式修改的内容，继续继承 V0.1~V0.5.1**
> - **被 V0.5.2 显式新增或调整的内容，以本文为准**

---

## 1. V0.5.2 版本定位

### 1.1 V0.5.2 核心目标

V0.5.1 已经完成：

- `DesiredVelocityReference(u_d, r_d)` 的局部规划统一输出
- stronger controller
- dynamic / kinematic 双后端 env

但当前 observation 仍存在一个语义问题：

- 障碍物和 defender 的“距离”字段使用的是**圆心距**
- mask 判定也基于**圆心距**
- APF 排斥力大小同样基于**圆心距**

这会带来两个问题：

1. 与真实传感器特别是雷达/测距设备的“返回最近表面距离”直觉不一致
2. 观测距离、可见性判定、APF 排斥强度三者的距离语义不统一

因此，V0.5.2 的目标冻结为：

1. **将 observation 中 defender / obstacle 的距离字段统一改为最近距离（净空距离）**
2. **将 defender / obstacle 的 mask 判定统一改为基于最近距离**
3. **将 APF 排斥力的距离度量统一改为基于最近距离**
4. **在尽量小改现有 observation schema 和上层代码的前提下完成上述修正**

### 1.2 V0.5.2 工程意义

V0.5.2 不是一个“新算法版本”，而是一个**观测语义修正版**。

它要解决的是：

- observation 里“distance”到底是什么意思
- APF 里“距离越近排斥越强”到底按什么距离算
- 传感器可见性边界到底按什么几何量定义

V0.5.2 完成后，当前 project 在这一层将更加一致：

- observation distance
- visibility mask
- APF force magnitude

都基于同一个量：

\[
d_{\text{clear}} = d_{\text{center}} - r_{\text{att}} - r_{\text{obj}}
\]

---

## 2. 当前问题分析

## 2.1 当前 observation distance 的语义

当前 [builder.py](d:\Python\pythonproject\ProjectsinHitwh\UnmannedSystems\USV_sim\src\usv_sim\observation\builder.py) 中：

- defender row 的 `distance`
- obstacle row 的 `distance`

都是按：

\[
d_{\text{center}} = \|p_{\text{obj}} - p_{\text{att}}\|_2
\]

即圆心距来计算。

## 2.2 当前 mask 的语义

当前 [visibility.py](d:\Python\pythonproject\ProjectsinHitwh\UnmannedSystems\USV_sim\src\usv_sim\observation\visibility.py) 中：

- defender 是否可见
- obstacle 是否可见

也是按：

\[
d_{\text{center}} \le sensing\_radius
\]

来判定。

## 2.3 当前 APF 的语义

当前 [apf_guidance.py](d:\Python\pythonproject\ProjectsinHitwh\UnmannedSystems\USV_sim\src\usv_sim\guidance\apf_guidance.py) 中，排斥力大小使用的距离同样是：

\[
d_{\text{center}} = \sqrt{rel_x^2 + rel_y^2}
\]

并没有减掉：

- attacker 半径
- obstacle / defender 半径

## 2.4 为什么这不合理

对于真实世界中的测距型感知，尤其当我们希望 observation 更接近“传感器返回值”时，物体距离更合理的定义应是：

\[
d_{\text{clear}} = d_{\text{center}} - r_{\text{att}} - r_{\text{obj}}
\]

这个量表示：

> attacker 外表面到目标物体外表面的最近距离

它更符合：

- 雷达/测距设备返回最近表面距离的直觉
- APF 里“几何上越接近碰撞，排斥应越强”的需求
- visibility 里“一个大障碍物应比一个小障碍物更早进入可观测范围”的现实意义

---

## 3. V0.5.2 核心设计结论

## 3.1 新的统一距离语义

V0.5.2 对 defender / obstacle 的统一距离语义冻结为：

\[
d_{\text{clear}} = d_{\text{center}} - r_{\text{att}} - r_{\text{obj}}
\]

其中：

\[
d_{\text{center}} = \|p_{\text{obj}} - p_{\text{att}}\|_2
\]

### 说明

- 对 obstacle：\(r_{\text{obj}} = r_{\text{obs}}\)
- 对 defender：\(r_{\text{obj}} = r_{\text{def}}\)
- 允许 `d_clear < 0`，表示发生几何重叠

## 3.2 V0.5.2 不删除相对坐标

虽然本版本要把距离语义改成最近距离，但**不删除**当前 observation 中的：

- `rel_x`
- `rel_y`

原因：

- planner / APF / future 几何策略仍然需要方向信息
- 仅靠一个标量最近距离不足以决定作用方向

因此 V0.5.2 的原则是：

> **保留相对坐标作为几何方向编码，但把所有 distance 字段的语义统一改成最近距离/净空距离。**

这也是当前版本下最合理、最小扰动的方案。

## 3.3 mask 判定统一基于最近距离

V0.5.2 冻结 defender / obstacle 的可见性判定为：

\[
d_{\text{clear}} \le sensing\_radius
\]

而不是：

\[
d_{\text{center}} \le sensing\_radius
\]

### 含义

如果某个障碍物更大，那么在相同圆心距下：

- 它的最近表面更近
- 因此应更早进入“可见”集合

这个结果是符合现实感知直觉的。

## 3.4 APF 排斥力大小统一基于最近距离

V0.5.2 冻结 APF 排斥力的标量距离输入改为：

\[
d_{\text{clear}} = d_{\text{center}} - r_{\text{att}} - r_{\text{obj}}
\]

但排斥力方向仍由相对位置向量给出：

\[
\hat{p} = \frac{[rel_x,\ rel_y]}{\|[rel_x,\ rel_y]\|_2}
\]

也就是说：

- **方向**：仍由中心连线方向决定
- **强度**：由最近距离决定

这是当前 APF 最合理也最稳定的改法。

---

## 4. Observation Schema 调整

## 4.1 defender observation

当前 defender row 大致为：

\[
[rel_x,\ rel_y,\ rel_u,\ rel_v,\ distance,\ cos(\Delta\psi),\ sin(\Delta\psi)]
\]

V0.5.2 冻结为：

\[
[rel_x,\ rel_y,\ rel_u,\ rel_v,\ clearance,\ cos(\Delta\psi),\ sin(\Delta\psi)]
\]

即：

- shape 不变
- dtype 不变
- 第 5 个槽位的语义从 `center distance` 改为 `nearest distance / clearance`

## 4.2 obstacle observation

当前 obstacle row 大致为：

\[
[rel_x,\ rel_y,\ distance,\ radius]
\]

V0.5.2 冻结为：

\[
[rel_x,\ rel_y,\ clearance,\ radius]
\]

同样：

- shape 不变
- dtype 不变
- 第 3 个槽位的语义从 `center distance` 改为 `nearest distance / clearance`

## 4.3 goal observation 不改

V0.5.2 不修改 `goal` 的 distance 语义。

仍保持：

\[
goal\_distance = \|p_{\text{goal}} - p_{\text{att}}\|_2
\]

原因：

- goal 不是障碍物/实体感知问题
- goal region 的判定本身就与 `goal.radius` 绑定
- 保持它不变可以减少无谓改动

---

## 5. 需要联动修改的代码模块

## 5.1 `src/usv_sim/observation/visibility.py`

这是 V0.5.2 必改文件之一。

需要修改：

- defender 可见性判定从圆心距改为最近距离
- obstacle 可见性判定从圆心距改为最近距离

当前：

\[
d_{\text{center}} \le sensing\_radius
\]

修改后：

\[
d_{\text{clear}} \le sensing\_radius
\]

## 5.2 `src/usv_sim/observation/builder.py`

这是 V0.5.2 必改文件之一。

需要修改：

- defender row 的 `distance` 槽位改为 `clearance`
- obstacle row 的 `distance` 槽位改为 `clearance`

相对位置 `rel_x, rel_y` 保留。

## 5.3 `src/usv_sim/guidance/apf_guidance.py`

这是 V0.5.2 必改文件之一。

需要修改：

- `_repulsive_force(...)` 的距离度量从中心距改为净空距离
- obstacle repulsion 和 defender repulsion 都应统一到最近距离语义

### 参数来源原则

attacker radius 与 defender / obstacle radius 不建议再额外复制到 APF 配置中。

更符合当前架构的做法是：

- attacker radius 来自 `scenario`
- defender / obstacle radius 来自 observation 或 world 真值

而不是：

- 在 `attacker_apf_baseline` 里再重复定义一份几何半径

## 5.4 `src/usv_sim/policies/attacker_apf_baseline.py`

如果 `APFGuidance` 需要在构造时获得：

- `scenario.attacker_radius`

那么这里需要作为参数透传层修改。

## 5.5 `src/usv_sim/policies/factory.py`

如果采用“从 `scenario` 把 attacker radius 传给 `APFGuidance`”的更合理方案，那么这里也需要同步改。

原因：

- `factory.py` 是当前最稳定拿到完整 `ProjectConfig` 的地方
- `scenario.attacker_radius` 应从这里往下传

## 5.6 `tests/*`

V0.5.2 至少需要同步修改或新增以下测试：

- `tests/unit/test_visibility.py`
- `tests/unit/test_observation_builder.py`
- `tests/unit/test_apf_guidance.py`
- `tests/integration/test_goal_vs_apf_rollout.py`

---

## 6. 最小改动原则

V0.5.2 明确坚持以下保守原则：

### 6.1 不重做 observation 总结构

不新增一大堆新 key，不重写 `spaces.Dict` 总框架。

### 6.2 不删除相对坐标

`rel_x` / `rel_y` 保留，避免破坏当前 planner / guidance 几何逻辑。

### 6.3 只修正 distance 语义

本版本的核心是：

- **把 distance 的含义改对**

而不是：

- 重新发明一套全新 observation

### 6.4 APF 距离语义与 observation 距离语义统一

V0.5.2 要求：

- APF 中使用的距离
- observation 中暴露给下游的距离
- visibility/mask 使用的距离

统一为同一个最近距离定义。

---

## 7. 推荐开发顺序

1. **先冻结 V0.5.2 的统一距离定义**
2. **修改 `visibility.py`，让 mask 判定先统一**
3. **修改 `builder.py`，让 observation 中的 distance 槽位语义统一**
4. **修改 `apf_guidance.py`，让 APF 力大小也切到最近距离**
5. **如需要，补 `factory.py` / `attacker_apf_baseline.py` 的半径传递**
6. **补 unit / integration tests**

---

## 8. V0.5.2 第一批 TODO

| ID | 任务 | 输出 | 验收标准 |
|---|---|---|---|
| T521 | 冻结 defender/obstacle 最近距离定义 | 文档 + 实现 | `d_clear = d_center - r_att - r_obj` |
| T522 | 修改 visibility 逻辑 | `visibility.py` | mask 判定统一基于最近距离 |
| T523 | 修改 observation distance 语义 | `builder.py` | defender/obstacle distance 槽位改为 clearance |
| T524 | 修改 APF repulsive distance | `apf_guidance.py` | APF 力大小统一基于 clearance |
| T525 | 处理 attacker radius 传递 | `factory.py` / `attacker_apf_baseline.py` | APF 能拿到 `scenario.attacker_radius` |
| T526 | 更新单元测试 | `tests/unit/*` | visibility/builder/APF 口径一致 |
| T527 | 更新集成测试 | `tests/integration/*` | APF rollout 在新距离语义下稳定可运行 |

---

## 9. 验收标准

V0.5.2 完成时至少满足：

1. defender / obstacle 的 observation `distance` 字段语义统一为最近距离
2. defender / obstacle 的 mask 判定统一基于最近距离
3. APF repulsive force 大小统一基于最近距离
4. 相对坐标字段仍保留，现有几何方向逻辑不被破坏
5. 现有 `play.py` / `evaluate.py` / benchmark 链路继续可用

---

## 10. 最终结论

V0.5.2 的关键不是“增加更多观测字段”，而是：

- **把 observation 里已有的 distance 语义修正到更合理的几何量**
- **让 mask、APF、observation 三者的距离定义统一**
- **让当前 perception-like observation 更接近真实测距设备返回的最近距离语义**

如果说：

- V0.5.1 解决的是 planner / controller / env backend 的分层

那么 V0.5.2 要解决的就是：

- **当前 observation 里 distance 到底代表什么**
- **mask 的感知边界按什么距离定义**
- **APF 对障碍物和 defender 的排斥强度按什么距离定义**

只要 V0.5.2 按本文执行，当前 project 在观测层、可见性层和 APF 几何层的距离语义就会统一下来，这会让后续规控算法和 learning 方法都更容易建立一致的理解。  
