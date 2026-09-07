# KAF ↔ DeepSeek Harness 严谨对齐报告

> 装载源：`https://github.com/deepseek-ai/deepseek-harness` @ `master`
> 装载时间：2026-08-18 ｜ 对齐框架：KAF v5.4.3（国王-Agent蜂群）
> 交付物：`kaf/adapters/deepseek_harness.py`（装载适配器，已自测通过）

---

## 0. 装载摘要（Load Summary）

| 项 | 值 |
|---|---|
| 仓库 | `deepseek-ai/deepseek-harness`（DeepSeek AI 官方） |
| 副标题 | **DeepSeek Harness: Everything is a Plugin.** |
| 默认分支 | `master` |
| Stars / Forks | **149,165** / 15,274 |
| Commits | 12,404 |
| License | MIT（2026-08-13 起对 DSH packages 采用） |
| 运行时版本 | `dsh` 0.1.0-rc.7（developer preview，破坏性变更预警） |
| 核心引擎 | **Cordis**（spatiotemporal composability 插件框架，vendored） |
| 形态 | pnpm monorepo：TS packages + Python SDK + native `landlock-run` + Web UI(`:3080`) |
| 启动 | `npx @deepseek-ai/dsh web` 或 `pnpm dsh web` |

**dsh 的治理相关硬事实（来自 docs/architecture.md / AGENTS.md / subsystems/tools.md / cordis-primer.md）：**

1. **无特权核心**：一切皆插件（含模型适配器、工具注册表、会话日志、agent loop）；插件向共享 `ctx` 贡献 services / typed events / reversible effects；注册即效应，卸载可回退。
2. **能力接缝(seam)** = Service Definition + Service Provider + Consumer 三者齐备，缺一不叫 seam；fs/shell/subagents/telemetry 都是 seam。
3. **工具执行流水线**（受护栏）：`tools/pre-execute`(allow|deny|ask 瀑布) → `ToolGuard`(单调拒绝，只缩权不翻盘) → `tools/execute`(around-dispatch) → `tools/post-execute`(accept|block) → `tools/result`(不可变权威)。
4. **会话日志不变式**：`ctx.sessions` 是 append-only `SessionEvent`；**「模型可见 ⟺ 已记录」**，运行时断言。新模型可见输入必须新增 session event。
5. **原生事件瀑布**：`emit / waterfall / parallel / serial` 四种 dispatch mode；`agent/*` 与 `tools/*` 是一等拦截点（`agent/pre-step` 决定模型看到什么，`agent/turn-stopping` 可停回合）。
6. **ctx.llm 路由**：每调用按 `provider+model` 路由，`llm/stream` 瀑布可拦截/短路，按适配器实例隔离（replay 状态不跨实例）。
7. **ctx.subagents**：子代理委派，多 provider（spawn-in-process / fork / acp / codex / claude-code / dsh-sdk）。
8. **ctx.sandbox**：`landlock-run` 沙箱后端，消费者 spawn 前包裹 argv。
9. **审批/权限**：`packages/interaction` 提供 permission/approval/ask-user；`ToolGuard`+`ToolRestriction` 做单调拒绝与作用域遮罩。
10. **自修改**：`packages/self-modification` 允许 agent 检视/挂载自身插件（运行时改自身）。

**关键对齐结论**：dsh 拥有**原生事件瀑布**作为一等拦截点，因此 KAF 的强制层在 dsh 上应做成**原生监听者插件**（native_event），而非 WorkBuddy 平台的 agent 侧门禁。这是比 WorkBuddy 适配更强的挂载方式。

---

## 1. 概念映射表（Concept Map）

| KAF v5.4 组件 | DeepSeek Harness 对应 | 同构性 |
|---|---|---|
| **Constitution-as-Code** (`constitution.json`) | dsh `profile` + `bundle` + `cordis.patch.yml` | 都是「声明式组合配方」；KAF=治理宪法，dsh=能力组合，二者**正交** |
| **Platform Adapters** (`base.py`) | Cordis 插件 + `ctx.<key>` 接缝 | **高度同构**：都是可插拔后端；但 dsh 用 Definition/Provider/Consumer 三角色 |
| **520 Runtime Guard** (`guard520` + `kaf_gate`) | `tools/pre-execute` + `ToolGuard`(单调拒绝) + `agent/pre-step` | **高度同构**：都是执行前拦截瀑布 |
| **Governance Layer** (`policy.json` + kill-switch + 审计链 + HMAC 归因) | `dsh-base` approval policy + `fs-observation-policy` + 会话日志不可变 | **部分同构**：dsh 有审批/观察策略，但**无显式 kill-switch / 防篡改审计链 / 策略即代码** |
| **Dynamic King** (`king.py:resolve_king`) | dsh harness home + profile owner | **不同**：dsh 无「国王」主权概念，是组合优先（谁部署谁定 profile） |
| **Economics Router** (frontier/balanced/economy) | `ctx.llm` 路由(provider+model) + 双 LLM 思想(ADR 0010) | **同构**：都是「按任务/调用选模型档位」 |
| **Coordinator / 宰相轮值** | `ctx.agents` 注册表 + `agent/*` 事件 | **部分同构**：dsh 有 agent registry 但无「轮值宰相」治理角色 |
| **Memory Integrity** (SHA-256 指纹 + drift) | 会话日志 append-only + `deriveMessages` 不变式 | **同构**：都是「不可变/可校验追溯」 |
| **Shared Ledger** (SQLite) | `sessionPersistence` 后端 + 会话日志 | **同构**：都是共享审计账本 |
| **Cognition Spine** (反模式/检索注入/deliberate/蒸馏/校准/Loop) | `self-modification` + `workflow` + **无显式反模式库** | **KAF 独有**：dsh 无「进智智慧层」 |
| **Multi-view Review** | 多 `subagent` provider(codex/claude-code) | **可映射**：用不同 subagent provider 做低相关审查 |
| **dispatch 派发队列** | `ctx.subagents` 委派 + `workflow` | **同构**：都是任务派发到子代理 |

---

## 2. 逐层对齐（Layer-by-layer）

### L1 声明式宪法（Constitution-as-Code）
- **dsh**：`profile` 列出 bundles 顺序 + out-of-tree 插件 + `cordis.patch.yml`；`dsh-base` 是第一层。配置即代码，可 patch 任意 row。
- **KAF**：`constitution.json` 六节（economics_routing/dispatch/review_loop/shared_ledger/governance/cognition）+ `sovereign.king_resolver`。
- **对齐**：KAF 的宪法是**治理维度**的声明式；dsh 的 profile 是**能力维度**的声明式。互补，不冲突。KAF 适配器以 `constitution.json` 为治理真相源，dsh profile 为能力真相源。

### L2 记忆完整性（Memory Integrity）
- **dsh**：会话日志 append-only + 「模型可见⟺已记录」不变式；`deriveMessages()` 从日志投影。
- **KAF**：`memory_integrity.py` 做 SHA-256 指纹 + drift 检测 + `protect_write`（防覆盖受保护段落）。
- **对齐**：都是不可变/可校验。KAF 多了一层「受保护内容防覆盖」语义（520 铁律），dsh 多了一层「模型可见必须可重建」的不变式。可互相借鉴：KAF 应增加「模型可见⟺已记录」不变式审计；dsh 应增加 `protect_write` 防配置被覆盖。

### L3 520 运行时护栏（520 Runtime Guard）
- **dsh**：`tools/pre-execute`(allow|deny|ask) → `ToolGuard`(单调拒绝) → `tools/execute` → `tools/post-execute` → `tools/result`。`agent/pre-step` 可重写/拒绝模型所见。
- **KAF**：`guard520.py` 4 检查点；`kaf_gate.py` agent 侧强制门禁（删/移/覆盖前 MUST 过）。
- **对齐**：**高度同构**。dsh 的 `tools/pre-execute` 瀑布就是 KAF 门禁的原生宿主——KAF 门禁应作为 dsh 的 `tools/pre-execute` 监听者（返回 allow/deny/ask），而非 agent 侧自调用。本适配器已实现此桥接。

### L4 平台适配器（Platform Adapters）
- **dsh**：Cordis 插件通过 `ctx.<key>` 暴露 service；消费方依赖 key 不依赖实现；`register()` 返回 disposer（reversible effect）。
- **KAF**：`PlatformAdapter` 8 方法；WorkBuddy 适配是 agent 侧门禁，dsh 适配应是 native event listener。
- **对齐**：KAF 应把「单角色适配器」升级为 dsh 式的 **seam 三角色**（Definition/Provider/Consumer），使后端可整体替换。本适配器已按此思路把 dsh 的 seam 当 Provider、KAF 治理当 Consumer。

### L5 宰相轮值协议（Coordinator Protocol）
- **dsh**：`ctx.agents` 注册表 + `agent/*` 事件（inbox/step/status/request/validation/continuation）；subagent 委派通过 `tool-subagent`。
- **KAF**：`coordinator.json` 宰相(3票)/各 agent(1票)/国王(一票否决)；轮值 3 步流转。
- **对齐**：dsh 有 agent 注册表但**无「轮值宰相」治理角色**与投票机制。KAF 的轮值协议可映射为 dsh 的一个 `coordinator` 插件，监听 `agent/*` 做身份/投票裁决。KAF 可借鉴 dsh 的「per-agent scoped registration」实现记忆隔离墙的架构化（Worker 背不动全局 = 架构必然性）。

### L6 治理层（Governance Layer，v5.3）
- **dsh**：`dsh-base` approval policy + `fs-observation-policy`（通过 `fs/*` 事件门贡献观察检查）；审批走 `tools/pre-execute` 的 `ask`。**无** 全局急停、无 hash-chained 审计链、无 HMAC 身份归因、无 Policy-as-Code 声明文件。
- **KAF**：`policy.json`(Policy-as-Code) + `kill-switch`(全局急停) + `AuditChain`(防篡改) + `attest()`(HMAC 归因)。
- **对齐**：**KAF 治理层是 dsh 的明确超集**。dsh 的审批/观察策略是 KAF 治理层的「子集实现」。建议把 KAF 治理层打包成 dsh 插件 `kaf-govern`，贡献 `tools/pre-execute` + `agent/pre-step` 监听者 = 在 dsh 内强制 KAF 治理。本适配器即该插件的桥接核心。

### L7 进智脊柱（Cognition Spine，v5.4）
- **dsh**：`self-modification`（运行时挂载/检视自身插件）+ `workflow`（worker-thread provider）。**无**显式反模式库、检索注入、deliberate 门控、经验蒸馏、决策校准、Loop Driver。
- **KAF**：反模式库(8 条真实种子) + retrieval_inject + deliberate(元认知软刹车) + experience_distillation + calibration_engine + loop_driver(闭环自修)。
- **对齐**：**KAF 独有**。dsh 的 `self-modification` 是「能改自己」，KAF 的进智脊柱是「改自己时不被历史反模式绊倒」。建议把 KAF 反模式检索注入为 dsh `agent/pre-step` 的注入块（`agent.inject()`），让 dsh agent 在动手前看到历史雷区。（本适配器 `bridge_agent_pre_step` 已接 `retrieval_inject`。）

---

## 3. 缺口分析（Gap Analysis）

### dsh 有、KAF 缺（KAF 应向 dsh 借鉴）
| 缺口 | dsh 实现 | KAF 获益 |
|---|---|---|
| **原生事件瀑布 hook  substrate** | `emit/waterfall/parallel/serial` + `agent/*`/`tools/*` 一等拦截点 | KAF 强制层从「平台特定 glue / agent 侧门禁」升级为**通用事件瀑布**，统一所有平台 |
| **能力接缝三角色** | Definition/Provider/Consumer 齐备，可整体替换 | KAF PlatformAdapter 升级为 seam 模型，后端替换更干净 |
| **会话日志不变式** | 「模型可见⟺已记录」运行时断言 | KAF 增加「模型可见必须可重建」审计，强化可追溯 |
| **可逆效应** | `ctx.effect()` 返回 disposer，卸载可回退 | KAF 所有注册（skill/gate/adapter）带 disposer，清理可预测 |
| **双 LLM / 每调用路由** | `ctx.llm` provider+model 路由 + replay 隔离 | 与 KAF economics_router 同构，可统一为「task-tier → provider+model」 |
| **运行时自修改** | `self-modification` 插件 | KAF 技能自动封装可借鉴为可逆运行时挂载 |

### KAF 有、dsh 缺（KAF 可向 dsh 输出）
| 缺口 | KAF 实现 | dsh 获益 |
|---|---|---|
| **主权国王 + 一票否决** | `king.py:resolve_king`（Deployer=King） | dsh 组合优先、无单一主权；治理类操作需明确 sovereign |
| **全局急停 kill-switch** | `governance.set_kill_switch` | dsh 无全局熔断开关 |
| **策略即代码 + 防篡改审计 + 归因** | `policy.json` + `AuditChain`(hash-chained) + `attest()`(HMAC) | dsh 审批散落各包，无统一声明式策略与可验证审计 |
| **进智脊柱** | 反模式/检索注入/deliberate/蒸馏/校准/Loop | dsh 无「智慧层」，同类错误易重犯 |
| **520 硬铁律 + agent 侧门禁兜底** | 铁律8/9/10 + `kaf_gate` | dsh 守卫仅原生，无 agent 侧兜底 |
| **记忆完整性 drift 检测** | `memory_integrity.drift` | dsh 会话日志不可变但无配置漂移防护 |

---

## 4. 借鉴清单（Borrow List，严谨、带优先级）

### [dsh → KAF] 高优先级
1. **采纳 Cordis 事件瀑布（waterfall/emit/parallel/serial）作为 KAF 通用 hook substrate**，替换平台特定 hook glue。KAF 的 `kaf_gate` / `governance` / `review` 都应通过事件瀑布接入，而非各自写平台适配。→ 直接收益：WorkBuddy 适配的 agent 侧门禁可升级为「事件瀑布监听者」，dsh 适配天然 native。
2. **PlatformAdapter 升级为 seam 三角色**（Definition/Provider/Consumer）。把 `read_constitution/read_memory/...` 当作 Consumer，KAF 治理为 Definition，平台实现为 Provider。
3. **增加「模型可见⟺已记录」不变式审计**到 Memory Integrity：任何进入模型的上下文必须能从审计链重建。

### [dsh → KAF] 中优先级
4. **可逆效应 disposer**：KAF 所有注册（适配器/门禁/技能）返回 disposer，卸载可预测回退。
5. **economics_router ↔ ctx.llm 路由统一**：`task-tier(frontier/balanced/economy)` → `provider+model`，并采纳 dsh 的 replay 隔离语义。

### [KAF → dsh] 高优先级（以本适配器为载体）
6. **治理插件 `kaf-govern`**：贡献 `tools/pre-execute` + `agent/pre-step` 监听者 = KAF 520 护栏 + 治理层。本适配器 `bridge_pre_execute` / `bridge_agent_pre_step` 即该监听者实现。
7. **kill-switch 作为 dsh approval policy 插件**；`king_resolver` 映射为 profile owner。
8. **进智注入作为 `agent/pre-step` 注入块**：`retrieval_inject` 输出经 `agent.inject()` 落地（已接 `bridge_agent_pre_step`）。

### [KAF → dsh] 中优先级
9. **策略即代码 + 防篡改审计链**：把 dsh 散落的审批/观察策略收敛为 `policy.json` + hash-chained `AuditChain`。
10. **记忆隔离墙架构化**：借鉴 dsh 的 per-agent scoped registration，使「Worker 背不动全局」成为架构必然性（呼应 KAF 记忆隔离墙 strict）。

---

## 5. 集成方案（Integration Plan：如何把 KAF 挂载到 dsh）

### 5.1 适配器落地
- 文件：`kaf/adapters/deepseek_harness.py`（已写入 + 自测通过）。
- 它实现 `PlatformAdapter` 全部 8 方法，并提供桥接函数：
  - `bridge_pre_execute(exec_meta)` → 返回 dsh `PreToolDecision`(allow/deny/ask)，内部串 `kaf_gate` + `Governance.evaluate`（已修正大小写与 `--reason/--script/--op` 归一化）。
  - `bridge_agent_pre_step(messages)` → 注入 KAF 治理 + 进智反模式块。
  - `bridge_llm_route(task_type)` → provider+model 推荐。
  - `dispatch(...)` → 写共享派发队列 + 附 dsh `subagent` 委派提示。

### 5.2 dsh 插件注册（cordis.yml 配方）
```yaml
# packages/kaf-govern/cordis.yml（建议新增包）
kaf-govern:
  dependencies:
    - ctx.tools
    - ctx.agents
  mount:
    # 工具执行前拦截：KAF 520 护栏 + 治理层
    - ctx.on('tools/pre-execute', async (exec, next) => {
        const r = await kafBridge.bridge_pre_execute({
          op: exec.name, target: exec.arguments?.path,
          confirmed: exec.user_confirmed, script: exec.script,
          reason: exec.reason, agent: exec.agent,
        });
        if (r.decision === 'deny') return { allow: false, reason: r.reason };
        if (r.decision === 'ask')  return { allow: false, ask: r.reason };
        return next();
      })
    # 模型可见前拦截：KAF 治理 + 进智注入
    - ctx.on('agent/pre-step', async (claimed, next) => {
        const r = kafBridge.bridge_agent_pre_step(claimed);
        if (r.reject) return; // 拒绝该步
        if (r.inject) ctx.agents.inject(r.inject); // 注入反模式块
        return next();
      })
```

### 5.3 环境变量
```bash
export KAF_SHARED_DIR="$HOME/.kaf/shared"   # 共享账本/派发队列/治理审计
export KAF_KING="你的名字"                   # 动态国王（Deployer=King）
export KAF_AGENT="kaf-govern"               # 适配器在 dsh 中的身份
export DSH_HOME="$HOME/.dsh"                # dsh harness home
```

### 5.4 验证命令
```bash
# dsh 侧：确认 KAF 监听者已挂载
dsh --profile web --dump-config | grep kaf-govern

# KAF 侧：集群自检仍 PASS（不破坏现有强制层）
cd kaf && python kaf.py check
python kaf.py govern "delete" --resource "D:/x/MEMORY.md" --user_confirmed --has_script --king_confirmed
python kaf.py kill-switch on && python kaf.py kill-switch off
python kaf.py audit-tail 10

# 适配器自测
python adapters/deepseek_harness.py
```

---

## 6. 验证（Verification，本次已执行）

| 验证项 | 结果 |
|---|---|
| `py_compile` 适配器语法 | ✅ PASS |
| `bridge_pre_execute` 未确认删除 → DENY（铁律8/10） | ✅ 返回 `decision=deny`, `rule_id=gov-destructive-needs-script` |
| `bridge_pre_execute` 已确认+脚本+理由删除 → ALLOW | ✅ `decision=allow` |
| `bridge_pre_execute` 已确认+脚本+理由重命名 → ALLOW | ✅ `decision=allow`（op 归一化 mv + `--script` 转发修复后） |
| `bridge_pre_execute` 未确认发布 → DENY（外部发送需确认） | ✅ `rule_id=gov-external-send-needs-approval` |
| `bridge_pre_execute` 只读 → ALLOW | ✅ `rule_id=gov-read-allow` |
| `bridge_llm_route('planner')` → provider+model | ✅ `deepseek-chat / balanced` |
| `bridge_agent_pre_step` 进智注入 | ✅ 调用 `retrieval_inject`（cognition 模块缺失时安全降级为空块） |
| `dispatch` 写共享派发队列 | ✅ 写入 `shared/dispatch_queue.json` |

**修复的硬伤（严谨对齐必须抓出的）**：
- `Governance.evaluate()` 真实签名是 `(action, agent_id=None, resource=None, context=None)`，初版错传 `user=` → 已改为 `agent_id` + `context`，并补 `attest(agent_id)` 满足零信任归因。
- 治理层 `effect` 返回**小写** `"deny"/"allow"`（Decision.DENY="deny"），初版比对**大写** `"DENY"` 导致已 DENY 却放行 → 已改为小写比对。
- kaf_gate `--op` 仅接受 `delete/rm/move/mv/write/copy/rmtree`，dsh 的 `archive/rename/bulk_write/publish` 会被 argparse 拒（退出码 2）→ 已做 `OP_TO_GATE` 归一化，且 `returncode != 0` 一律视为 BLOCK（安全失败）。
- 适配器未把 `exec_meta` 的 `--script`/`--reason` 转发给 kaf_gate → 已补齐（铁律8 脚本 / 铁律12 可追溯理由）。

---

## 7. 结论

KAF 与 dsh **互补而非竞争**：
- **dsh 提供运行时基座**（插件 / 事件瀑布 / 能力接缝 / 会话日志 / 原生拦截点）；
- **KAF 提供治理脊柱**（主权国王 / 520 护栏 / 治理层 / 进智智慧层）。

二者结合 = **一个被治理的插件化 harness**：dsh 的 `tools/*` 与 `agent/*` 瀑布成为 KAF 强制层的原生宿主，KAF 的国王/急停/审计/反模式成为 dsh 插件生态的治理护栏。

`kaf/adapters/deepseek_harness.py` 即这一结合的桥：它让 KAF 能以一个 dsh 插件的形态存在，在 dsh 的原生事件瀑布中强制 KAF 治理。本次装载已通过分层防御自测，并修复了 4 处会让治理「名存实亡」的硬伤。

---

*End of KAF ↔ DeepSeek Harness Alignment Report*
