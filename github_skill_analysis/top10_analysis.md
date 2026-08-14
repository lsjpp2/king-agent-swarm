# GitHub 同类 Skill 热度榜 · 真实 Top 10 拆解 + KAF v5.3 演化分析

> 抓取日期：2026-08-04
> 目标：多智能体编排 / 蜂群治理 / Agent 治理 同类仓库，按 star 排序，深度拆解，反哺国王-Agent蜂群(KAF)技能。

---

## 0. 数据可信度声明（重要）

本环境 `api.github.com` 路由与 `ai-agents` 话题页返回**合成/注水数据**（如 `affaan-m/ECC` 237k、`NousResearch/hermes-agent` 225k、`langchain` 143k、`firecrawl` 160k——真实值远低于此且不一致膨胀 1.5–4.5×）。
**因此本报告完全弃用 api.github.com 与 ai-agents 话题页，仅采用经交叉验证的真实来源**：`multi-agent` / `agent-framework` 话题页、`agent swarm` / `multi-agent framework` 搜索结果页（这些页面 star 数与现实一致，如 MetaGPT 69.7k 与搜索结果吻合）。
单个仓库页不渲染侧边栏 star 数，故 star 取自上述话题/搜索页。抓取至末段触发 GitHub 二级限流，停止抓取。

**结论：下列 Top 10 的 star 均为真实来源核验值，非记忆、非合成。**

---

## 1. 真实 Top 10（多智能体编排 / 蜂群 / 治理类，按 star 降序）

| # | 仓库 | Star(真实) | 一句话定位 | 与 KAF 相关性 |
|---|------|-----------:|-----------|-------------|
| 1 | bytedance/deer-flow | 79.2k | 长程 SuperAgent harness：研究/编码/创作，含沙箱、记忆、技能 | 高（harness+技能+沙箱） |
| 2 | FoundationAgents/MetaGPT | 69.7k | 多智能体"软件公司"，自然语言编程，SOP 角色分工 | 极高（角色/SOP/层级） |
| 3 | ruvnet/ruflo | 67k | "agent meta-harness"：多玩家蜂群、自主工作流编排、技能、宪法式治理 | **极高（蜂群+技能+宪法）** |
| 4 | crewAIInc/crewAI | 56.6k | 角色扮演多智能体编排框架（Crews + Flows） | 高（角色/编排） |
| 5 | HKUDS/nanobot | 46.6k | 超轻量自托管 Agent 框架，含 MCP、记忆、多智能体工作流 | 中（轻量 harness） |
| 6 | 666ghj/BettaFish | 41.9k | 多 Agent 舆情分析，"论坛引擎"辩论机制：主持+链式思辨碰撞 | 高（ deliberation/辩论） |
| 7 | agentscope-ai/agentscope | 28.5k | 阿里多智能体框架，稳健/多样/灵活 | 中 |
| 8 | openai/openai-agents-python | 28.4k | 轻量多智能体工作流：handoffs、guardrails、sessions、tracing | **极高（handoff/guardrails）** |
| 9 | openai/swarm | 21.9k | 教学性轻量多智能体编排：handoffs + routines | 高（handoff 原语） |
| 10 | google/adk-python | 21k | Agent Development Kit：Agent+工具+部署+评估 | 中（评估/部署） |

### 关键同类项（star 真实但需单列说明）
- **langchain-ai/langgraph** — ~38.8k（**未能在本会话干净核验**：唯一出现该数的页面同时列出 langchain=143k 注水值，故不计入硬排名；但它是"图/有状态工作流+检查点+人机协同"标杆，必学）。
- **microsoft/agent-governance-toolkit** — 5.6k（**与 KAF 概念最接近**：策略执行/零信任身份/执行沙箱/SRE/kill-switch/防篡改审计/OWASP 10/10 覆盖）。star 不高但治理维度最全，是 KAF 最直接的对照系。
- **kyegomez/swarms** — 7k（企业级多智能体编排，swarm 治理）。
- **microsoft/agent-framework** — 12.6k（Python/.NET 编排）。
- **camel-ai/camel** — 17.5k（首个多智能体框架，角色扮演 society）。
- **ag2ai/ag2**（原 AutoGen  lineage）— 4.8k（对话式多智能体编排）。

### 已排除（非同类/数据不可信）
- CowAgent 46.3k：单 Agent 产品/Agent Harness，**非**多智能体 swarm 框架 → 排除。
- wshobson/agents 38.5k：跨 harness 插件**市场/组件生态**，非纯编排框架 → 排除。
- langchain/firecrawl/dify/browser-use/gemini-cli：通用 LLM 框架/工具/CLI，**非**多智能体治理 → 排除。
- ai-agents 话题页全部（注水）。

---

## 2. 逐库深度拆解（可复用的机制）

### ① MetaGPT（69.7k）— 角色/SOP/层级
- **机制**：把"软件公司"建模为角色（产品经理/架构师/工程师/Scrum Master），每条消息是**结构化**（角色+内容+产出标准），用 **SOP** 约束协作顺序；角色间通过**发布-订阅**共享上下文。
- **可复用**：KAF 宰相(Planner) + Worker 已有雏形，但缺**角色库 + SOP 模板 + 结构化消息契约**。可补 `roles.json` + `sop/` 模板。

### ② ruvnet/ruflo（67k）— 蜂群 meta-harness + 宪法
- **机制**：`meta-harness` = 编排"编排器"；多玩家 **swarm** 协调自主工作流；**skills** 作为可组合单元；内置 **Constitution** 概念（治理约束）。
- **与 KAF 强对齐**：KAF 已是"宪法即代码 + 蜂群"，ruflo 证明"技能即可组合治理单元 + 宪法式约束"是主流正确方向。KAF 应强化 **skill 作为一等公民治理单元** 与 **宪法可热更新**。

### ③ crewAI（56.6k）— Crews + Flows + 角色隔离
- **机制**：Crew=角色集合按 process（sequential/hierarchical）协作；Flow=事件驱动有状态工作流；每个 Agent 有显式 `role/goal/backstory/tools`；支持 **guardrails**。
- **可复用**：KAF 的 `coordinator.json` 角色可对齐 crewAI 的 Agent 定义；Flow 对应 KAF 的 dispatch 队列。补 **guardrails 作为 Agent 一等属性**。

### ④ openai/swarm + openai-agents-python（21.9k+28.4k）— Handoff 原语 ★
- **机制**：**handoff** = Agent 在对话中把任务**显式转交**给更专业的 Agent（带移交上下文）；**guardrails** = 输入/输出校验（在动作前/后拦截，结构化拒绝）；**tracing/sessions** = 全程可观测。
- **可复用（重点）**：KAF 目前 dispatch 只把整任务派给单个 agent，缺 **handoff 原语**（agent→agent 子任务转交 + guardrail 校验）。这是 v5.3 高价值补强。

### ⑤ microsoft/agent-governance-toolkit（5.6k）— 治理全栈 ★★★
- **机制**：① **Policy Enforcement**（YAML/OPA/Cedar，每次工具调用经策略评估，结构化 `GovernanceDenied`）；② **Zero-Trust Identity**（SPIFFE/DID/mTLS 标识 agent，归因）；③ **Execution Sandboxing**（privilege rings）；④ **SRE**（kill-switch、SLO、混沌测试、断路器）；⑤ **Tamper-evident Audit**（Merkle 审计）；⑥ OWASP Agentic Top 10 全量覆盖。
- **与 KAF 差距（诚实）**：KAF 的 520 guard 是**硬编码 Python 规则**，不是**声明式策略即代码**；无 kill-switch、无 agent 身份归因、无防篡改审计链。这是 KAF 当前最薄弱处。

### ⑥ BettaFish（41.9k）— 论坛辩论 deliberation
- **机制**：ForumEngine 引入**辩论主持人**，多个 Agent（Insight/Media/Query/Report）通过"论坛"链式思辨碰撞+辩论后收敛结论。
- **可复用**：KAF 决策多为"宰相拍板/国王否决"，缺**争议性决策的 deliberation 阶段**。可补 `deliberate()` 原语：高风险/分歧决策先经多 Agent 辩论再裁决。

### ⑦ langgraph（~38.8k，未干净核验）— 图/有状态/检查点
- **机制**：把工作流建模为**有状态图**，checkpointer 持久化状态，支持 conditional edges + **human-in-the-loop**。
- **可复用**：KAF dispatch 队列是线性票，可升级为**有状态图 + 检查点 + 人机协同节点**。

### ⑧ camel-ai/camel（17.5k）— 角色扮演 society
- **机制**：agent 通过角色扮演组成 society，协作/对抗涌现数据；探索 agent 缩放律。
- **可复用**：印证"角色隔离 + 协作"范式，与 KAF 角色分层一致。

---

## 3. 跨库共性模式（提炼）

1. **角色/技能是一等公民**：MetaGPT 角色、crewAI Agent、ruflo skills、openai handoff——都证明"可组合的治理单元"是编排核心。
2. **Handoff > 整任务派发**：openai 系把"转交"做成原语，KAF 的 dispatch 应升级支持 handoff。
3. **Guardrails 内建**：crewAI/openai 把输入/输出校验作为 Agent 属性，而非事后检查。
4. **治理即代码 + 结构化拒绝**：AGT 用策略即代码 + `GovernanceDenied`（带原因），KAF 的硬编码 guard 应升级为声明式 `policy.json` + 结构化 DENY(reason)。
5. **可观测/审计/评估**：AGT 防篡改审计、openai tracing、adk 评估——KAF 需 hash-chained 审计 + kill-switch + 评估钩子。
6. **Deliberation**：BettaFish 辩论机制——高风险决策先辩论。
7. **有状态图 + 检查点 + 人机协同**：langgraph 范式，KAF 队列可图化。

---

## 4. KAF 差距 → v5.3 改进路线（宣称=实现）

| 差距 | 对标 | v5.3 动作 | 本次是否落地 |
|---|------|----------|------------|
| 硬编码 guard，无策略即代码 | AGT | **新增 `governance.py`：声明式 `policy.json` + 结构化 DENY(reason) + kill-switch + 防篡改审计链 + agent 归因** | ✅ 已落地+自测 |
| 无 kill-switch | AGT SRE | 全局急停开关（共享状态） | ✅ |
| 无防篡改审计 | AGT Merkle | hash-chained append-only 审计 | ✅ |
| 无 agent 身份归因 | AGT zero-trust | HMAC 风格 agent 身份断言 | ✅（基础版） |
| dispatch 不支持 handoff | openai handoff | `handoff` 原语（agent→agent 子任务转交 + guardrail） | 📋 路线（待 v5.3.1） |
| 缺 deliberation | BettaFish | `deliberate()` 辩论原语（高风险决策先辩论） | 📋 路线 |
| 线性队列 | langgraph | dispatch 队列→有状态图+检查点+人机协同 | 📋 路线 |
| 角色库/SOP 模板 | MetaGPT/crewAI | `roles.json` + `sop/` 模板 | 📋 路线 |

本次交付：`governance.py`（Policy-as-Code + kill-switch + audit + attestation）、`policy.json`（默认声明式策略）、`kaf govern` / `kaf kill-switch` / `kaf audit-tail` 命令、自测 `governance_selftest.py`（真跑通）。

---

*End of Top-10 Analysis · 国王-Agent蜂群 KAF v5.3 演化依据*
