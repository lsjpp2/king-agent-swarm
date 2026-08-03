---
name: 国王-Agent蜂群
description: 搭建国王模型 Agent 集群治理框架（KAF v5.2）。自动生成声明式宪法、520 运行时护栏、记忆完整性协议、宰相轮值协议、平台适配器、模型经济学路由（真实计价+校准）、多视角审查（闭环写回）、共享账本。适用于多 Agent 协作治理场景（WorkBuddy + OpenCode + Codex + Claude + Kimi + Cursor 等）。触发词：国王模式、Agent蜂群、多Agent协作、集群搭建、宰相轮值、KAF、520护栏、模型经济学、经济学路由、多视角审查、角色分层、派发队列、共享账本。
agent_created: true
---

# 国王-Agent蜂群 Skill · KAF v5.2

你是一个 Agent 集群治理架构师。当用户提到「国王模式」「Agent蜂群」「多Agent协作」「集群搭建」「宰相轮值」「KAF」「520护栏」「模型经济学」「经济学路由」「多视角审查」「角色分层」时，加载此 skill。

---

## 核心理念：KAF v5.2 = 代码化治理框架（含 4 个进化方向落地）

> v4 是 md 文档约定；**v5.0 是代码化框架**——宪法从 md 变成可机器解析的 JSON，护栏从事后检查变成运行时强制（有 hook 接口的平台走 hook；WorkBuddy 等无 hook 平台走 agent 侧强制门禁 `kaf_gate.py`），记忆从"丢失后恢复"变成"写入前阻止覆盖"。

```
Constitution-as-Code   宪法从md文档 → 可解析JSON，规则可机器验证
520 Runtime Guard      从事后检查 → 运行时强制（hook 或 agent侧门禁 kaf_gate.py）
Memory Integrity       从"丢失后恢复" → "写入前阻止覆盖"
Platform Adapter       从绑定特定平台 → 5行代码接入任意平台
```

**KAF 管"怎么治理 Agent"，CrewAI/LangGraph 管"怎么执行任务"——互补，不替代。**

---

## 五层架构

```
┌─────────────────────────────────────────┐
│  Platform Adapters  平台适配器            │
│  WorkBuddy / Claude / OpenCode / ...    │
├─────────────────────────────────────────┤
│  Coordinator Protocol  宰相轮值协议       │
├─────────────────────────────────────────┤
│  520 Runtime Guard  运行时护栏            │
├─────────────────────────────────────────┤
│  Constitution-as-Code  声明式宪法         │
├─────────────────────────────────────────┤
│  Memory Integrity  记忆完整性             │
└─────────────────────────────────────────┘
```

---

## 本 skill 自带完整实现

代码已随 skill 分发在 `kaf/` 子目录：

```
kaf/
├── constitution.json      声明式宪法 v5.2（可机器解析，含 economics_routing/dispatch/review_loop/shared_ledger 四节）
├── coordinator.json       宰相注册表（role/cost_tier/轮值/投票/handover + 共享账本/派发队列引用）
├── guard520.py            520运行时护栏（4检查点 + self_check，真核查）
├── memory_integrity.py    记忆完整性（SHA-256指纹 + drift检测 + protect_write）
├── memory_ledger.py       结构化共享记忆账本（SQLite ledger：operation_log+fingerprint+drift，默认落共享层）
├── economics_router.py    模型经济学路由（任务分类 + 真实计价 + calibrate 校准）
├── review.py              多视角审查（低相关视角叠加 + BLOCK 写回闭环）
├── pricing.json           每 agent 真实计价表（成本-质量权衡数据源）
├── kaf_gate.py            强制门禁（agent侧强制层：删/移/覆盖前 MUST 过此门禁）
├── kaf.py                 CLI入口（init/check/verify/guard/rotate/status/route/review/review-commit/dispatch/calibrate）
├── adapters/
│   ├── base.py            适配器接口（8个方法，含 dispatch）
│   ├── workbuddy.py       WorkBuddy适配器（已实现，含 dispatch 写共享派发队列）
│   └── _template.py       新平台适配器模板
├── examples/basic/        基础示例（constitution.json）
└── README.md / README_EN.md
```

---

## 快速开始（CLI）

```bash
cd kaf/
python kaf.py init      # 初始化：生成 constitution.json + 注册记忆指纹
python kaf.py check     # 520自检（真核查：日志/备份/回滚/强制门禁均须实际存在）
python kaf.py verify    # 记忆完整性校验（指纹 + drift检测）
python kaf.py guard     # 打印运行时护栏检查点说明
python kaf.py status    # 查看集群状态（当前宰相/轮值历史）
python kaf.py rotate claude   # 宰相轮值：workbuddy → claude
python kaf.py route "重构支付模块的事务边界"     # 模型经济学路由：推荐 planner/worker + 成本估算
python kaf.py review D:/path/to/artifact.py      # 多视角审查：security/correctness/style/economics 叠加
python kaf.py review-commit findings.json       # 审查闭环：BLOCK 结论写回共享铁律/review_findings.md
python kaf.py dispatch "批量翻译这200篇文档"     # 路由落执行：推荐并派发到共享派发队列
python kaf.py calibrate                         # 据 usage_log 动态校准 ROLE_TOKEN_SHARE
# 强制门禁（agent侧）：任何删/移/覆盖操作前 MUST 先过此门禁
python kaf_gate.py check --op delete --target "<路径>"          # 无确认→BLOCK
python kaf_gate.py check --op delete --target "<路径>" --confirmed   # 已确认→OK
python kaf_gate.py check --op write --target "MEMORY.md" --content "<新内容>"  # 删520/铁律→BLOCK
```

---

## 执行流程（搭建一个新集群）

### 第一步：清点现有 Agent

扫描确认已安装的 Agent（WorkBuddy / OpenCode / Codex / Claude / Kimi / Cursor），**只写确认存在的**，不写未确认的。

### 第二步：初始化 KAF

```bash
cd kaf/ && python kaf.py init
```
生成 `constitution.json` 并注册记忆指纹（基于 `memory_integrity.py`）。

### 第三步：编辑 coordinator.json

填入实际 Agent 清单：

- `_king`: `"山禾"`（固定，唯一主权人）
- `current_coordinator`: 当前宰相（如 `"workbuddy"`，3票）
- `coordinators`: 每个 Agent 的 `identity_file` / `private_memory` / `votes` / `capabilities` / `status`

### 第四步：配置 520 护栏（运行时强制）

`guard520.py` 提供 4 个检查点。强制层的接入方式取决于平台：

| 检查点 | 触发 | 拦截规则 | 来源 |
|:---|:---|:---|:---|
| `pre_execute` | 破坏性操作 | 无脚本 → 拦截 | 铁律8 |
| `pre_delete` | 删除操作 | 未展示清单/未确认 → 拦截 | 铁律10 |
| `post_execute` | 所有操作 | 自动记录 `kaf_operations.log` | 可追溯 |
| `on_failure` | 操作失败 | 提供回滚方案 | 可恢复 |

**强制层接入方式（重要，已实测）：**
- **有原生 hook 接口的平台**（如 Claude/Codex 类）：通过 PreToolUse hook 自动调用上述检查点。参考 `adapters/_template.py` 的 `register_hook`。
- **WorkBuddy 桌面端等无 hook 接口的平台（已实测 ~/.workbuddy 无 hooks.json、settings 无 hook 字段、app.asar 无 PreToolUse/hook 关键字）**：无 OS/客户端钩子可接，强制层为 **agent 侧强制门禁 `kaf_gate.py`**。即 agent 在每次删/移/覆盖操作前**必须调用 `python kaf_gate.py check` 并服从其 BLOCK 结果**——这是 Constitution-as-Code 在无钩子平台上的诚实适配，不是降级。`adapters/workbuddy.py` 的 `register_hook` 已改为返回该 agent 侧策略（不再写无人读取的 hooks.json）。

**`kaf check` 的 `enforced` 项会真核查**：`kaf_gate.py` 存在 且 本工作区 `MEMORY.md` 已写入门禁铁律（铁律11）——二者缺一，`self_check` 即 FAIL。这保证"强制"是接进宪法的真强制，不是装饰。

### 第五步：接入新平台（可选）

```python
from adapters.base import PlatformAdapter

class MyAdapter(PlatformAdapter):
    platform_name = "my_platform"
    def read_constitution(self): ...
    def read_memory(self, key=None): ...
    def write_memory(self, key, value, protect_check=True): ...
    def register_hook(self, event, callback): ...
    def execute(self, action): ...
    def get_agent_id(self): ...
    def get_workspace(self): ...
```

### 第六步：验证

让每个 Agent 回答：① 你是谁？② 当前宰相是谁？③ 私有记忆库在哪？④ 能否读其他 Agent 记忆？

---

## 520 法则（核心，不可丢失）

| 原则 | 含义 | 工程化 |
|:---|:---|:---|
| 可追溯 | 每个操作有脚本+日志 | `kaf_operations.log` 自动记录 |
| 可恢复 | 删除走回收站，配置改前备份 | `FOF_ALLOWUNDO` + `.bak` |
| 可修复 | 错误可回滚 | `on_failure` 提供回滚方案 |
| 可进化 | 提炼工作流/铁律/skill | skill 自动封装 |

**铁律8/9/10**：
- 铁律8：操作必须写脚本+验证（rm/mv/copy → 先写 .py → 执行 → ls 验证）
- 铁律9：记忆数字必须实地核查（任何数量 → find/ls 验证）
- 铁律10：删除前展示清单（ls -R → 展示用户 → 确认才删）

> "就算世界灭亡，这个标准不能丢。"

---

## 宰相轮值协议

**三步流转**（无冷却期， king 下令即刻生效）：

1. **国王下令**：「从今天起 X 做宰相」
2. **旧宰相提权交接**：将 `active_tasks` / `pending_decisions` / `context_summary` 写入 `coordinator.json → handover_state`
3. **新宰相提权领命**：读 `coordinator.json` 确认身份，开始履职

投票规则：宰相 **3票**，其他 Agent 各 **1票**，国王 **一票否决**。

CLI 执行：`python kaf.py rotate <agent_name>`

---

## v5.1 完善：来自 Cursor Agent Swarm 研究

> 参考来源：Cursor 博客《智能体蜂群与新的模型经济学》(2026-07-20) 与其产物仓库 `cursor/minisqlite`。KAF v5.1 将其中可工程化的治理洞见吸收为框架能力。

### 1. 角色分层模型（Planner / Worker / King）

大型任务天然呈树状（根=目标 → 递归细分为叶子工作单元）。KAF 据此明确三层角色，且**上下文效率 > 并行性**——这是蜂群可扩展性的真正来源，而非并行本身。

| 角色 | 对应 KAF 实体 | 职责 | 上下文约束 |
|:---|:---|:---|:---|
| **King** | `_king`（人类山禾） | 唯一主权人，定目标、一票否决 | 全局意图 |
| **Planner** | `current_coordinator`（宰相，3票） | 拆解任务树、做设计决策、**不碰实现细节** | 只背规划上下文，不被实现细节污染 |
| **Worker** | 其余 Agent（各1票） | 执行被委派的具体叶子单元 | 只背局部任务，全上下文投入一小块 |

**落地**：`coordinator.json` 每个 Agent 增加 `role: planner|worker` 字段。宰相即唯一 Planner；Worker 永不负责规划。这把"记忆隔离墙 strict"（禁止读其他 Agent 私有记忆）从规则升级为**架构必然性**——Worker 背不动全局，Planner 不背细节。

### 2. 模型经济学路由（Economics Router）★ v5.1 新增核心能力

KAF v5.0 有平台适配器（接入任意平台），但**缺"何时用哪个平台/模型"的决策层**。研究结论：质量相近但成本可差 10 倍——worker 占 69%~90% token 但用便宜模型，planner token 少却用贵的前沿模型（占 ~2/3 成本）。真正需要前沿智能的环节极少（初始拆解、设计决策、权衡），一旦 Planner 把不确定性收敛为明确指令，便宜模型照执行即可。

**实现**（`economics_router.py`，CLI `kaf route "<task>"`）：
- `classify(task)` → `planner | worker | reviewer`
- `route(task_type, coordinators)` → 按 `role` + `cost_tier(frontier|balanced|economy)` + `votes` 推荐最优 Agent，并给出成本估算
- **分配原则**：规划/设计/权衡类 → `cost_tier=frontier` 的 Planner；执行/搬运/批量类 → `cost_tier=economy` 的 Worker；审查类 → 多视角低相关模型

### 3. 失效模式与协调机制（直接映射 Cursor 6 类）

| 失效模式 | 现象 | KAF 防护（落地为规则/模块） |
|:---|:---|:---|
| **脑裂 split-brain** | 两个不知情的 Planner 重复实现同一概念 | 单一 Planner 决策权（宰相唯一）；`禁止 Agent 改 current_coordinator`；确保不两个子树决定同一问题 |
| **规划器冲突** | 两套认知反复博弈同一批文件 | 决策记入 `constitution.json`（声明式宪法，可编译校验、可溯源）；冲突时协调器合并文档，引用传导下游 |
| **合并冲突** | Worker 不擅合并，常覆盖/放弃 | 中立第三方介入（arbiter 角色，类似合并队列）；KAF 强制门禁 `kaf_gate.py` 在覆盖前 BLOCK |
| **超大文件** | 文件成为冲突黑洞、拖慢一切 | Worker 可标记臃肿文件 → 阻止新提交 → 外部智能体拆分；对应"操作必须写脚本+验证" |
| **僵化** | Agent 不敢碰核心代码 | 允许有意破坏性变更 + 注释理由；编译器/护栏传导变更到下游 |
| **错误累积** | 长时间多 Agent 下小错变大错 | 多视角审查（见下）+ 520 自检 `kaf check` 周期运行 |

### 4. 多视角审查（Low-correlation Review）★ v5.1 新增

没有任何单一视角能发现所有问题，但**低相关视角叠加**可像自动驾驶那样达到高于人类的可靠性。审查成本远低于被审查工作（worker 占 90% token），投入回报高。

**实现**（`review.py`，CLI `kaf review <file>`）：派发 `security / correctness / style / economics` 等低相关视角并行审查，叠加结论。每视角可由不同模型/训练/个性运行。对应 KAF "可进化"——审查发现沉淀为铁律/skill。

### 5. Field Guide：跨 Agent 知识沉淀

Cursor 的 Field Guide 是"agent 写给 agent"的共享文件夹（`index.md` 启动时注入每个 Agent，有行数预算），记录"出乎意料的情况"让后继者轨迹更短。模型权重冻结，值得记录的恰恰是意外。

**对齐 KAF**：KAF 的 `MEMORY.md` / 记忆库即是 Field Guide。强化为**双向**——既 AI 写给人（META.md），也 Agent 写给 Agent（共享 context ledger）。`memory_ledger.py` 的 operation_log 即"可溯源的意外记录"。

### 6. 记忆后端升级（可选 SQLite Ledger）★ v5.1 新增

`minisqlite` 用 Rust 重实现 SQLite（极小 API：`open/execute/query`，COW 事务可回滚，WAL 快照并发不阻塞，双向兼容 SQLite 文件格式可被标准工具查询）。KAF 记忆完整性从"纯 JSON 指纹"升级为**可选结构化 ledger**：

**实现**（`memory_ledger.py`，基于 Python 标准库 `sqlite3`，零外部依赖）：
- 表 `operation_log`（操作/agent/时间戳/before_hash/after_hash）、`fingerprints`（SHA-256）、`drift`（漂移记录）
- COW 式事务（落盘前可回滚）、WAL 模式并发读不阻塞
- 向后兼容现有 `.fingerprints.json`；`kaf verify` 双路校验

---

## v5.2 进化：4 方向落地（来自 Cursor Agent Swarm 研究的"后续可进化方向"）

> v5.1 吸收了研究的洞见为框架能力；v5.2 把 v5.1 报告里列出的 4 个"后续可进化方向"**真正落地为代码 + 宪法条款**。每条都"宣称=实现"实地跑通。

### 方向1 · 路由真实化（pricing.json + calibrate）★ 新增
v5.1 的路由靠硬编码 `COST_WEIGHT` 估成本。v5.2 改为读 **`pricing.json` 真实计价表**（每 agent 每 1M token 相对价），成本估算来自真实数字；并新增 **`calibrate()`**：读 `usage_log.json`（各 agent 真实 token 消耗）动态重算 `ROLE_TOKEN_SHARE`，写入 `calibration.json`，路由实时采纳。

- 实现：`economics_router.py`（`route()` 用真实计价；`calibrate()` 重算占比）
- CLI：`kaf calibrate`（消费 usage_log 校准）
- 宪法条款：`constitution.json → economics_routing.calibration`

### 方向2 · 路由落执行（dispatch → 共享派发队列）★ 新增
v5.1 的 `route` 只推荐不交付。v5.2 新增 **`dispatch`**：先 route 推荐，再把任务票写入共享派发队列 `D:/Agent集群共享/dispatch_queue.json`，目标 agent 启动自检时读取执行。无原生跨 agent API 的平台统一走此路径。

- 实现：`adapters/base.py` 加 `dispatch()` 接口；`adapters/workbuddy.py` 写入共享队列；`kaf.py` 加 `cmd_dispatch`
- CLI：`kaf dispatch "<task>" [target_agent]`
- 宪法条款：`constitution.json → dispatch.queue`

### 方向3 · 审查闭环（BLOCK 写回共享铁律）★ 新增
v5.1 的审查只生成视角任务。v5.2 新增 **`commit()`**：`summarize()` 得 `BLOCK` 结论时，自动把发现写入共享 Field Guide `D:/Agent集群共享/铁律/review_findings.md`（Field Guide 双向化：agent 写给 agent），实现"审查发现 → 沉淀铁律"的闭环。

- 实现：`review.py`（`commit()` / `_write_back()`）；`kaf.py` 加 `cmd_review_commit`
- CLI：`kaf review-commit <findings.json>`
- 宪法条款：`constitution.json → review_loop.write_back`

### 方向4 · 共享账本持久化（与 memory_integrity 去重）★ 新增
v5.1 的 ledger 默认落本地。v5.2 改为默认落到 **共享层 `D:/Agent集群共享/.memory_ledger.db`**，所有 agent 读写同一本账。并明确与 `memory_integrity.py` 的**职责去重**：前者=共享操作审计（谁/何时/改了什么），后者=每 agent 文件指纹（文件长什么样）；互补不重复。

- 实现：`memory_ledger.py`（`SHARED_LEDGER` 默认路径；`_find_memory_dir` 含共享候选）
- 宪法条款：`constitution.json → shared_ledger.dedup_with_memory_integrity`

**v5.2 验证清单（宣称≠实现，均已实地跑通）**：`kaf check` PASS；`kaf route` 真实计价；`kaf dispatch` 写共享队列；`kaf review-commit` BLOCK 写回铁律；`MemoryLedger()` 默认共享账本。

---

## 禁忌

- **禁止**任何 Agent 自行修改 `coordinator.json` 中的 `current_coordinator`
- **禁止**任何 Agent 读取其他 Agent 的私有记忆库（记忆隔离墙 strict）
- **禁止**任何 Agent 修改宪法（除非国王明确下令）
- **禁止**在 `agent_registry` 中写入未确认安装的 Agent
- **禁止**无脚本执行破坏性操作（铁律8）

---

## 开源

- 仓库：https://github.com/lsjpp2/king-agent-swarm
- License：MIT
- 贡献流程：user_feedback → coordinator_evaluate → king_confirm → merge

---

*End of 国王-Agent蜂群 Skill · KAF v5.2*
