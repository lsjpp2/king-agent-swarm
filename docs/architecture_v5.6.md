# Architecture & Design Philosophy (KAF v5.6)

> 升级自 v5.4 / v5.5。
> - v5.3 把「防错」做成代码可强制的**治理层**；
> - v5.4 把「进智」做成可运行、可闭环、可对齐检验的**进智脊柱**；
> - v5.5 把治理**前移**——从「写出来之后怎么审」挪到「该不该写」（L2 预执行决策层）；
> - v5.6 再补**预执行经济学**——「该派给谁写」（T2 复杂度分级路由）与「省的钱到底在哪一层」（T1 四层 token 治理）。
>
> 一句话：v5.5 解决**该不该写**，v5.6 解决**该派给谁写**和**省在哪一层**。三件事都发生在动手之前，成本最低、收益最高。

---

## Why King Agent Swarm Exists

If you have 2+ AI coding agents installed, you've hit these problems:

1. **No coordination** — each agent answers independently, often contradicting each other
2. **No memory safety** — one agent overwrites another's context, work silently lost
3. **No authority model** — nobody owns the final call; decisions ping-pong
4. **No cost model** — a trivial job gets routed to the most expensive model (v5.6 T2)
5. **No "should we even write this" gate** — code gets written that a native feature already provides (v5.5)

KAF is a **governance framework**, not an execution framework. It does not run your agents —
it decides who may act, what they may touch, what gets remembered, and (since v5.5/v5.6)
whether the work should be done at all and by whom.

> KAF 管「怎么治理 Agent」，CrewAI / LangGraph 管「怎么执行任务」——互补，不替代。

---

## Design Principles

### 1. Sovereignty (King) — whoever deploys, is King

框架**不硬编码任何所有者**。国王身份由 `king.py: resolve_king()` 动态解析：

```
KAF_KING 环境变量 > kaf_config.json > 本地作者环境 > 当前 OS 用户 > "operator"
```

远程新手克隆后默认**自己就是国王**，不需要改任何代码。

### 2. Constitution-as-Code

宪法从 md 文档变成 `constitution.json`（可机器解析、可编译校验、可溯源）。
规则不是"约定"，是数据；`kaf check` 会真核查它。

### 3. 520 Runtime Guard — 可追溯 / 可恢复 / 可修复 / 可进化

四个检查点（`guard520.py`）：`pre_execute` / `pre_delete` / `post_execute` / `on_failure`。
在**无原生 hook 接口的平台**（如 WorkBuddy 桌面端，已实测无 hooks.json、无 PreToolUse 字段），
强制层退化为 **agent 侧强制门禁 `kaf_gate.py`** ——这是诚实适配，不是降级。

### 4. Memory Integrity — 写入前阻止覆盖，而非丢失后恢复

`memory_integrity.py` 维护 SHA-256 指纹 + drift 检测 + `protect_write()`。

### 5. Cognition Spine (v5.4) — 进智脊柱

把经验从「只写不读的坟场」变成可运行、可闭环、可对齐检验的智慧层。
五零件：反模式库 / 检索注入 / 经验蒸馏 / 决策校准 / deliberate 门控，外加 Loop Driver 闭环自修。

### 6. L2 预执行决策层 (v5.5 NEW) — 写前先问「要不要写」

融合 Ponytail 极简主义，7 级梯：

```
need? → exists? → stdlib? → native? → dep? → oneliner? → minimal
```

停在**第一个成立的台阶**。最大削减来源是 `native`——例如 `<input type="date">` 替代手搓日期选择器。
安全红线永不妥协（trust-boundary / data-loss / 安全 / 无障碍），思考型模型上自动 bypass。

### 7. 预执行经济学 (v5.6 NEW) — 派给谁写、省在哪一层

| | 解决什么 | 入口 |
|---|---|---|
| **T2 复杂度分级路由** | 只按 role 选档 → 简单活派给贵模型 | `kaf route "<task>"` |
| **T1 四层 token 治理** | 误以为 Ponytail 全能省 token | `kaf tokens "<task>"` |

---

## 🗺️ Diagrams (v5.6)

| 图 | 内容 | 版本 |
|---|---|---|
| **`diagrams/16-architecture-v5.6.svg`** | **★ 九层全栈架构（最新）** | v5.6 |
| `diagrams/12-architecture-v5.4.svg` | 七层架构（含进智层） | v5.4 · 历史 |
| `diagrams/04-architecture.svg` | 六层架构（治理层在顶） | v5.3 · 历史 |
| `diagrams/13-cognition-full.svg` | 进智脊柱全景 | v5.4 |
| `diagrams/14-loop-closure.svg` | Loop Driver 闭环（阈值三档） | v5.4 |
| `diagrams/05-governance-flow.svg` | 治理流（写操作必经 evaluate） | v5.3 |
| `diagrams/08-king-resolution.svg` | 国王动态解析 | v5.3 |

> ⚠️ 标「历史」的图**保留供版本对照，不代表当前架构**。

---

## 九层架构（v5.6）

```
┌─────────────────────────────────────────┐
│  预执行经济学(v5.6)                      │  T2 复杂度路由 80/15/5 · T1 四层 token 治理
├─────────────────────────────────────────┤
│  L2 预执行决策层(v5.5·Ponytail)          │  7级梯 need?→exists?→stdlib?→native?→dep?→oneliner?→minimal
├─────────────────────────────────────────┤
│  Cognition Spine  进智脊柱(v5.4)         │  反模式/检索注入/蒸馏/校准/deliberate/闭环(与治理层正交)
├─────────────────────────────────────────┤
│  Governance Layer  治理层(v5.3)          │  策略即代码/急停/审计链/身份归因
├─────────────────────────────────────────┤
│  Platform Adapters  平台适配器            │  5行代码接入任意平台
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

### 执行管线 L0 → L6

```
L0 用户意图
L1 task-classifier          编码任务 vs 内容生产分流
L2 预执行决策 (v5.5/5.6)     Ponytail 7级梯 + T2 复杂度定档 + T1 token 层判定   ← 省在这里
L3 执行                      agent 干活
L4 kaf_gate 硬门禁           删/移/覆盖前必过（铁律12）
L5 review 多视角审查          security/correctness/style/economics（含 T1/T2）
L6 520 自检 + 审计链
```

---

## v5.6 · T2 复杂度分级路由（80/15/5）

**问题**：v5.5 及之前只按 `role`（planner/worker/reviewer）选成本档。一个"改圆角"的需求
因命中「设计」关键词被判为 planner，直接上 frontier 档——**简单活派给了贵模型**。

| 级别 | 目标占比 | 默认档 | 判据 |
|---|---|---|---|
| routine | 80% | economy | 机械 / 单点 / 有明确先例 |
| moderate | 15% | balanced | 多步骤但路径清楚 |
| complex | 5% | frontier | 跨模块 / 高风险 / 需权衡设计 |

**校正规则**：routine 取 role 档与复杂度档中**更便宜**者（降档省钱）；
complex 取**更强**者（升档保质）；moderate 不动。

**跨 role 放宽（`role_filter_relaxed`）**：目标档在本 role 内无候选时放宽 role 过滤。
> ⚠️ 这是 v5.6 实测发现并修复的**架空 bug**：初版把校正后的目标档交给原 role 过滤器，
> 结果 worker 任务判为 complex 也拿不到 frontier 候选（frontier 档只有 planner 的 claude），
> 80/15/5 里的 5% 形同虚设。

**实测**（`kaf route "设计一下按钮的圆角要多大"`）：

```
任务类型: planner
角色: worker | 成本档: economy
复杂度[T2]: routine (目标占比 80%) | 档位 frontier→economy ⤳已校正
        ⚠️ 已跨 role 放宽以取得 economy 档候选
```

策略入宪：`policy.json → gov-routine-no-frontier`（routine 派 frontier 须 `cost_justified`）。

---

## v5.6 · T1 四层 token 治理（诚实边界）

**问题**：v5.5 把 Ponytail 当成"省 token 的方案"，实际上它只管**代码生成**一层。
若真实开销落在读码或命令输出层，精简代码救不了成本。

| 层 | 实测可省 | 归属工具 | KAF 状态 |
|---|---|---|---|
| L1 code_read | −66% | serena (MCP·LSP 符号级检索) | ❌ 未集成（外部 MCP，集成成本高） |
| L2 command_output | −65% | rtk (输出裁剪) | ❌ 未集成（外部 MCP） |
| L3 prose_output | −6% | caveman (精简语体) | ❌ 未集成（收益极低，优先级最末） |
| L4 code_gen | −40% | **Ponytail L2 决策梯** | ✅ 已集成（v5.5） |

- 四层堆叠上限 **−69.6%**；**KAF 当前只吃到 code_gen 一层（−40%）**
- ⚠️ **诚实口径入宪**：`constitution.json → token_governance.honest_note` 写死
  "宣称省 69.6% 属虚假，须外接 serena/rtk 才成立"

**实测**（`kaf tokens "定位并修复登录接口的空指针"`）：

```
主要开销层: code_read
L1 code_read       -66%  未集成  ◀ 本任务命中
L4 code_gen        -40%  ✅ 已集成（v5.5 · kaf ponytail） ◀ 本任务命中
KAF 已覆盖: ['code_gen']
```

**实战价值**：T1 的作用不是"省 token"，而是**指出真正的省钱着力点**——
避免在错误的层上使劲。

---

## Memory Isolation (Red Wall)

- 每个 Agent 有私有记忆路径（`{{agent_memory_path}}`）
- 隔离级别 `strict`：禁止读其他 Agent 私有记忆
- 共享层仅 `${KAF_SHARED_DIR}/`（账本 / 派发队列 / 铁律 / 审查发现）

## Prime Minister Rotation

宰相 = 唯一 Planner（3 票），其余 Agent 各 1 票，国王**一票否决**。
轮值三步：国王下令 → 旧宰相写 `handover_state` → 新宰相读 `coordinator.json` 领命。
**禁止任何 Agent 自行修改 `current_coordinator`。**

## Conflict Resolution (Weighted Voting)

| 角色 | 票数 |
|---|---|
| 国王 | 一票否决 |
| 宰相（Planner） | 3 |
| 其他 Agent | 1 |

## Governance Layer (v5.3)

评估顺序：`kill_switch → attestation(HMAC) → guard520 → policy_as_code`。
- **策略即代码**：`policy.json`，DENY 优先，`require` 为豁免条件
- **急停**：`${KAF_SHARED_DIR}/governance/kill_switch.json`
- **防篡改审计**：hash 链式 append-only，`verify()` 可检测篡改
- **身份归因**：`attest(agent)`，未归因动作 DENY

## Cognition Spine 五零件 (v5.4)

1. **反模式库** `anti_patterns.jsonl` — 记「绝对不要做」+ 触发条件 + 正确替代
2. **检索注入** `retrieval_inject.py` — 任务起点主动拉相关反模式进上下文
3. **经验蒸馏** `experience_distillation.py` — `{context, action, outcome, confidence}`
4. **决策校准** `calibration_engine.py` — 比对历史 outcome/confidence，标注误校准
5. **元认知门控** `deliberate()` — 高利害动作前软刹车（命中 high → `DELIBERATE_HOLD`）

**Loop Driver**：候选 → 对齐检验 → 修订 → 再检验 → 收敛（≤5 轮，阈值三档：硬 / 软 / 国王兜底）。

---

## State Model

| 状态文件 | 作用 |
|---|---|
| `constitution.json` | 声明式宪法（唯一权威规则源） |
| `coordinator.json` | 宰相注册表 + 轮值历史 + handover_state |
| `.fingerprints.json` | 每 Agent 记忆指纹 |
| `${KAF_SHARED_DIR}/.memory_ledger.db` | 共享操作审计账本 |
| `${KAF_SHARED_DIR}/dispatch_queue.json` | 跨 Agent 派发队列 |
| `${KAF_SHARED_DIR}/governance/audit_chain.log` | 防篡改审计链 |

## Security Model

- 受保护资产（`MEMORY.md` / 520 / 铁律 / `constitution.json`）写删移须 `king_confirmed`
- 所有写操作过 `Governance.evaluate()` 并落审计链
- 身份归因：未 HMAC 归因的 Agent 动作一律 DENY
- 记忆隔离墙 strict

## Comparison with Alternatives

| | KAF | CrewAI | LangGraph | openai-swarm |
|---|---|---|---|---|
| 治理/权限 | ✅ 宪法+策略代码 | 部分 | 无 | 无 |
| 记忆安全 | ✅ 指纹+写入前拦截 | 无 | 检查点 | 无 |
| 成本路由 | ✅ T2 复杂度分级 | 无 | 无 | 无 |
| 预执行门禁 | ✅ Ponytail 7级梯 | 无 | 无 | 无 |
| 执行编排 | ❌ 不管 | ✅ | ✅ | ✅ |

## Limitations & Future Work

1. **serena / rtk 未集成**（T1 的 L1/L2 层，−66%/−65%，收益最大但需接外部 MCP）
2. **T2 无 A/B 实测数据**（当前仅结构性保证，无真实成本削减的实测）
3. **dispatch 队列仍是无状态文件**（未升级为有状态图 + 检查点，见 langgraph）
4. **复杂度信号词是启发式**（关键词 + 长度，可接 cognition 经验蒸馏做数据驱动校准）
5. **`deliberate()` 多 Agent 辩论未实现**（对标 BettaFish ForumEngine）

---

*KAF v5.6 · 平台无关 · 谁部署谁为王*
