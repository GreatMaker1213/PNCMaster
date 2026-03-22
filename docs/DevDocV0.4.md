# DevDocV0.4

> 本文档是 USV Sim 项目的 **V0.4 开发文档**。  
>
> 它建立在 `docs/devREADEME.md`、`docs/FinalDevDocV0.1.md`、`docs/DevDocV0.2.md`、`docs/DevDocV0.3.md`、`V0.3.1` 代码状态基础上，定义 V0.4 的核心目标：  
> **新增顶层统一入口 `play.py` 与 `evaluate.py`，解决“策略+场景无法一键正式运行”的工程问题。**
>
> 说明：原先偏“RL 适配链/训练评测分离”的设计内容，已由你重命名为 `docs/DevDocV0.5.md` 管理；V0.4 聚焦本次更高优先级的入口工程化工作。
>
> 若 V0.4 文档与 V0.1~V0.3 文档冲突：
>
> - **未被 V0.4 显式修改的内容，继续继承 V0.1~V0.3**
> - **被 V0.4 显式新增或调整的内容，以本文为准**

---

## 1. V0.4 版本定位

### 1.1 V0.4 核心目标

V0.3.1 已经具备：

- 多种 attacker 策略（goal/APF/heading-hold）
- 多个场景配置（goal_only/obstacle_only/defender_pressure）
- 统一 benchmark runner/evaluator 能力
- demo 级运行脚本

但当前研发流程仍有明显摩擦：

- 缺少“仓库顶层、明确正式、参数统一”的入口脚本
- 现有 `demos/` 脚本定位偏演示，不适合作为长期迭代入口
- 迭代时容易出现“配置/策略更新了，入口使用方式没同步”的问题

因此 V0.4 的目标冻结为：

1. 在顶层新增 `play.py`：单回合、实时渲染、用于策略行为观察
2. 在顶层新增 `evaluate.py`：多回合、无渲染、用于指标评估与结果落盘
3. 两者都支持：指定配置文件 + 指定策略
4. 统一参数契约与验收口径，作为后续算法开发默认入口

### 1.2 V0.4 工程意义

V0.4 不追求增加新算法，而是补足“可用性基础设施”：

- 从“功能存在”升级为“入口统一、协作友好、使用稳定”
- 让后续 RL / MPC / RRT / CBF / belief control 接入时，不再为运行入口重复造轮子

---

## 2. V0.4 范围与非目标

### 2.1 V0.4 范围

#### A. 顶层 `play.py`

提供单回合可视化运行能力：

- 指定配置文件路径
- 指定策略类型（可覆盖 config）
- 指定 seed
- 实时渲染
- 输出回合摘要

#### B. 顶层 `evaluate.py`

提供多回合评估能力：

- 指定配置文件路径
- 指定策略类型（可覆盖 config）
- 批量运行 episode（使用 benchmark seeds）
- 聚合统计并输出到指定目录

#### C. 稳定复用现有模块

V0.4 入口脚本应复用既有实现，不重复实现业务逻辑：

- `load_config(...)`
- `AttackDefenseEnv`
- `create_attacker_policy(...)`
- `evaluate_and_save(...)` / `evaluate_from_config(...)`

#### D. `demos/` 与正式入口分层

- `demos/`：保留演示与临时验证用途
- 顶层 `play.py` / `evaluate.py`：作为正式研发入口
- `demos/run_play.py`、`demos/run_evaluate.py` 在 V0.4 后不再作为正式入口维护，不承诺与后续配置/策略版本严格同步

### 2.2 V0.4 明确不做

- 不新增 RL 训练器框架（迁移到 V0.5）
- 不新增 MPC/RRT/CBF 正式实现
- 不改写 env/reward/termination 冻结语义
- 不改写 V0.3 benchmark 指标定义
- 不引入 GUI dashboard

---

## 3. 设计原则

### 3.1 原则 A：入口统一，核心逻辑不复制

顶层脚本只负责：

- 解析参数
- 组装对象
- 调用已有模块
- 输出结果

不在脚本内复制 simulator / evaluator 业务代码。

### 3.2 原则 B：策略选择口径统一

策略选择统一遵循：

1. CLI `--policy`（若提供）优先
2. 否则使用 `config.attacker_policy.type`

并冻结实现约束：

- 顶层入口脚本中策略实例化必须调用 `create_attacker_policy(cfg, policy_type)`
- 不允许在入口脚本中手写 `if policy == ...` 的具体策略类分支

### 3.3 原则 C：配置文件驱动

场景参数全部来自 yaml，不在脚本中硬编码世界参数。

### 3.4 原则 D：`play` 与 `evaluate` 职责严格分离

- `play.py`：看行为（可视化）
- `evaluate.py`：看指标（批量、落盘）

### 3.5 原则 E：输出可追溯

`evaluate.py` 输出目录中除 episode/aggregate 外，建议补充运行元数据（`run_meta.json`）。

---

## 4. 核心功能设计

## 4.1 `play.py` 功能定义

### 输入参数（建议冻结）

- `--config`：配置路径，必填
- `--policy`：策略类型，可选（`goal_seeking|apf|heading_hold`）
- `--seed`：回合种子，可选，默认 `0`
- `--render-mode`：可选，但在 V0.4 仅允许 `human`（默认 `human`）

### 执行流程

1. `cfg = load_config(config_path)`
2. 用 `create_attacker_policy(cfg, policy_type)` 创建策略
3. 构造 `AttackDefenseEnv(cfg=cfg, render_mode=render_mode)`
4. `policy.reset(seed=seed)` 与 `env.reset(seed=seed)`
5. 循环执行：`act -> step -> render`
6. 结束后打印回合摘要（终止原因、step、return、关键距离）
7. 回合结束后保持窗口，等待用户主动关闭（推荐 `plt.show(block=True)`）
8. `env.close()`

### 输出要求

- 默认输出到控制台
- 不强制写文件（可作为后续可选增强）

---

## 4.2 `evaluate.py` 功能定义

### 输入参数（建议冻结）

- `--config`：配置路径，必填
- `--policy`：策略类型，可选
- `--output-dir`：输出目录，必填
- `--overwrite`：可选，允许覆盖已存在且非空输出目录（默认关闭）

### 执行流程

1. 检查配置中必须存在 `benchmark.seeds`，缺失则直接报错退出
2. 若输出目录已存在且非空：默认报错退出；仅 `--overwrite` 时允许覆盖
3. 调用 `evaluate_and_save(config_path, output_dir, policy_type)` 执行评估
4. 策略实例化链路固定为：`evaluate_and_save -> evaluate_from_config -> create_attacker_policy`，不允许入口脚本直接实例化具体策略类
5. 落盘：
   - `episodes.jsonl`
   - `episodes.csv`
   - `aggregate.json`
6. 打印聚合摘要（num_episodes/success_rate/collision_rate/...）
7. 推荐额外落盘 `run_meta.json`

### `run_meta.json` 建议字段

- `config_path`
- `policy_type`
- `timestamp`
- `command`
- `git_commit`（可选）

`git_commit` 字段实现要求：

- 尝试获取 git commit（如 `git rev-parse HEAD`）
- 若失败（无 git / 非 git 目录 / 权限问题），写入 `null`
- 不允许因 commit 读取失败中断评测流程

---

## 4.3 策略支持范围（V0.4）

V0.4 冻结支持：

- `goal_seeking`
- `apf`
- `heading_hold`

错误处理要求：

- 策略不支持：报错并列出可选项
- 配置缺失/格式错误：报错并退出
- 配置缺失 `benchmark.seeds`：报错并退出（不允许静默 fallback）
- 输出目录不可写：明确报错，不静默失败
- 输出目录已存在且非空：默认报错；仅 `--overwrite` 允许覆盖

---

## 5. 与现有脚本关系

V0.4 之后建议约定：

- 顶层：
  - `play.py`（正式单回合可视化入口）
  - `evaluate.py`（正式批量评测入口）
- `demos/`：
  - `run_play.py`
  - `run_evaluate.py`
  仅用于演示与临时验证，不作为正式入口维护

建议在 `demos/` 脚本说明中标注“正式入口在顶层脚本”，并提示可能滞后于主版本功能。

---

## 6. 目录增量设计

```text
project_root/
├─ play.py
├─ evaluate.py
├─ demos/
│  ├─ run_play.py
│  └─ run_evaluate.py
├─ src/usv_sim/
│  ├─ envs/
│  ├─ policies/
│  └─ benchmark/
└─ configs/
```

---

## 7. 测试与验收设计

## 7.1 单元测试建议新增

- `tests/unit/test_play_cli_args.py`
- `tests/unit/test_evaluate_cli_args.py`

覆盖重点：

- 参数默认值
- 参数覆盖优先级
- 路径参数合法性校验

## 7.2 集成测试建议新增

- `tests/integration/test_play_entrypoint.py`
- `tests/integration/test_evaluate_entrypoint.py`

覆盖重点：

- `play.py` 能加载配置、创建策略、完成 1 episode
- `evaluate.py` 能落盘标准结果文件
- `--policy` 可覆盖配置项

## 7.3 Smoke 建议新增

- `play.py` 最小 smoke（固定 seed）
- `evaluate.py` 最小 smoke（小规模输出目录）

---

## 8. 推荐开发顺序

1. 固化 CLI 参数契约
2. 实现 `play.py`（复用 env + policy factory）
3. 实现 `evaluate.py`（复用 evaluator）
4. 增加 `run_meta.json` 落盘
5. 补 tests（unit/integration/smoke）
6. 更新文档与使用示例

---

## 9. V0.4 第一批 TODO

| ID | 任务 | 输出 | 验收标准 |
|---|---|---|---|
| T401 | 实现顶层 `play.py` | `play.py` | 可指定 config/policy/seed 并完成可视化单回合 |
| T402 | 实现顶层 `evaluate.py` | `evaluate.py` | 可指定 config/policy/output-dir 并完成批量评测 |
| T403 | 统一策略选择优先级 | CLI + factory | `--policy` 可覆盖 config |
| T404 | 统一评测结果落盘 | 输出目录 | 必含 `episodes.jsonl/csv` 与 `aggregate.json` |
| T405 | 增加运行元数据 | `run_meta.json` | 可追溯配置与运行上下文 |
| T406 | 补入口集成测试 | `tests/integration/` | 两个入口均可稳定运行 |
| T407 | 更新说明文档 | `docs/` | 新成员可按文档直接上手运行 |

---

## 10. V0.4 验收标准

### 10.1 功能验收

V0.4 完成时至少满足：

- 仓库顶层存在 `play.py` 与 `evaluate.py`
- `play.py` 可指定配置与策略完成单回合可视化
- `evaluate.py` 可指定配置与策略完成批量评估并落盘
- 与当前 V0.3.1 策略/场景兼容

### 10.2 语义验收

V0.4 完成时不得破坏：

- V0.1 动力学/奖励/终止/观测冻结语义
- V0.2 渲染语义
- V0.3 benchmark 指标与输出口径
- V0.3.1 simulator 公平性修复语义

### 10.3 研究可用性验收

V0.4 至少达到：

1. 算法迭代时可直接使用 `play.py` 快速观察行为
2. 算法对比时可直接使用 `evaluate.py` 输出标准化评测结果
3. 协作开发时无需修改内部模块即可切换策略和场景

---

## 11. 推荐验收命令

```bash
conda run -n RL python play.py --config configs/v0_3_goal_only.yaml --policy goal_seeking --seed 0
conda run -n RL python play.py --config configs/v0_3_obstacle_only.yaml --policy apf --seed 1

conda run -n RL python evaluate.py --config configs/v0_3_goal_only.yaml --policy heading_hold --output-dir outputs/eval_goal_heading
conda run -n RL python evaluate.py --config configs/v0_3_obstacle_only.yaml --policy apf --output-dir outputs/eval_obstacle_apf
```

建议回归命令：

```bash
conda run -n RL python -m pytest tests/unit tests/integration -q
conda run -n RL python tests/smoke/test_env_smoke.py
```

---

## 12. 最终结论

V0.4 的关键不是“再加算法”，而是把“如何稳定运行与评估算法”工程化。  
当 `play.py` 与 `evaluate.py` 落地后，USV Sim 将具备更清晰的日常研发入口，显著提升后续 V0.5（适配链与学习型策略）开发效率与协作一致性。
