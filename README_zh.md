# 👑 国王-Agent蜂群

**多 AI Agent 集群的协调协议。**

你有 3+ 个 AI 编程助手（Claude Code、Cursor、OpenCode、Codex 等）。
它们都跟你说话，但彼此不沟通。
它们互相污染记忆。它们给出的答案互相矛盾。

**国王-Agent蜂群用三个文件和一组清晰的比喻解决这个问题：**

```
你（国王）
  └── 宰相（当前协调者，可轮值）
        ├── Agent A
        ├── Agent B
        └── Agent C
```

---

## 它解决什么问题

| 问题 | 解决方案 |
|:---|:---|
| 6 个 Agent，零协调 | `coordinator.json` — 谁在负责，唯一真相源 |
| Agent 记忆互相污染 | 记忆隔离墙 — 每个 Agent 有自己的私有记忆库 |
| 无法切换负责人 | 轮值协议 — 国王说"X 现在做宰相"，旧宰相交接，新宰相接任 |
| Agent 偏离原始意图 | Anti-Drift 检查点 — 长期任务每 5 步做一次对齐 |

---

## 快速开始

```bash
git clone https://github.com/YOUR_USER/king-agent-swarm.git
cd king-agent-swarm

# 生成你的集群配置
./init.sh --king "你的名字" --cluster-path "/path/to/集群共享目录"

# 部署到你的 Agents
cat templates/constitution.md      # 复制到所有 Agent
cat templates/handover-protocol.md # 复制到所有 Agent
```

完整指南：[docs/quick-start.md](docs/quick-start.md)

---

## 为什么叫"国王 & 宰相"？

大多数多 Agent 框架用"orchestrator"和"worker"这种干巴巴的词。第二天没人记得它们是什么意思。

**国王 / 宰相 / 蜂群** 是：
- 一个心智模型，瞬间理解
- 文化直觉（从君主制到现代治理）
- 容易向非技术干系人解释

---

## 架构

完整设计理念、与竞品对比（RuFlo、AutoGen、CrewAI）和形式化状态定义，见 [docs/architecture.md](docs/architecture.md)。

核心图解：

| 图解 | 说明 |
|:---|:---|
| [权力结构](diagrams/01-power-structure.svg) | 国王 → 宰相 → Agent 层次 |
| [记忆隔离墙](diagrams/02-memory-isolation.svg) | 共享层 vs 私有记忆墙 |
| [宰相轮值流程](diagrams/03-rotation-flow.svg) | 宰相交接协议 |

---

## 支持的 Agent 平台

| Agent | 适配器 | 注入方式 |
|:---|:---|:---|
| Claude Code | [adapters/claude.md](adapters/claude.md) | `CLAUDE.md` 项目级注入 |
| Cursor | [adapters/cursor.md](adapters/cursor.md) | `.cursorrules` 注入 |
| OpenCode | [adapters/opencode.md](adapters/opencode.md) | `opencode.jsonc` instructions 数组 |
| Codex | [adapters/generic.md](adapters/generic.md) | 配置 JSON 注入 |
| Kimi | [adapters/generic.md](adapters/generic.md) | 首条消息粘贴身份 |
| WorkBuddy | [adapters/generic.md](adapters/generic.md) | 系统提示词钩子 |
| **任何 LLM Agent** | [adapters/generic.md](adapters/generic.md) | `system_prompt` 注入 |

---

## 核心原则

1. **人类主权** — 国王（人类）拥有一票否决权
2. **记忆隔离** — Agent 之间永不读取对方的私有记忆
3. **协调者轮值** — 宰相角色随国王指令流转
4. **冲突决策** — 宰相=3票，其他 Agent 各1票，国王否决
5. **Anti-Drift** — 长期任务每 5 次工具调用做一次对齐检查

每条原则的设计理由：[docs/principles.md](docs/principles.md)

---

## 仓库结构

```
king-agent-swarm/
├── README.md              # 英文说明
├── README_zh.md           # 中文说明（本文件）
├── LICENSE                # MIT
├── docs/
│   ├── architecture.md    # 完整设计理念
│   ├── quick-start.md     # 10分钟搭建指南
│   ├── principles.md      # 每条规则为什么存在
│   └── faq.md             # 常见问题
├── templates/
│   ├── coordinator.json   # Agent 注册表模板
│   ├── constitution.md    # 集群宪法模板
│   ├── handover-protocol.md
│   └── agent-identity.md  # 每 Agent 身份卡模板
├── adapters/
│   ├── claude.md          # Claude Code 适配器
│   ├── cursor.md          # Cursor 适配器
│   ├── opencode.md        # OpenCode 适配器
│   └── generic.md         # 通用 LLM Agent 适配器
├── diagrams/              # SVG 架构图解
├── examples/
│   ├── minimal-3-agent.md # 最简单的集群
│   └── 6-agent-cluster.md # 完整生产集群
├── init.sh                # Unix 初始化脚本
└── init.ps1               # Windows 初始化脚本
```

---

## 常见问题

**这个跟特定平台绑定吗？**
不。它是纯配置文件（Markdown + JSON）。任何能读文件的 LLM Agent 都能加入蜂群。

**为什么不用 AutoGen / CrewAI / LangGraph？**
那些是代码级编排框架。国王-Agent蜂群在**协议层**运作——它是关于规则和约定，而不是 API 调用。你可以把它和任何编排框架一起使用。

**只有 2 个 Agent 能用吗？**
能。最小可行蜂群是：国王 + 1 个 Agent（默认兼任宰相）。

**Agent 之间怎么实际通信？**
通过共享层（`coordinator.json` + 进度日志）。Agent 对 Agent 的直接消息传递不在范围内（而且通常是混乱的根源）。

**这个跟 RuFlo 比怎么样？**
RuFlo 是成熟的同构蜂群（只支持 Claude Code 实例），5分钟就能搭好。国王-Agent蜂群支持异构 Agent（Claude + Cursor + OpenCode + ...），并在主权、记忆隔离、宰相轮值上有针对性设计。见 [docs/architecture.md](docs/architecture.md) 完整对比。

---

## 发版计划

- [x] v1.0 — 去个人化，MIT 协议，基本文档
- [ ] v1.1 — `validate.sh` 配置校验脚本
- [ ] v1.2 — `examples/6-agent-cluster.md` 完整生产配置
- [ ] v2.0 — 实战验证后的 Anti-Drift 纠正机制

---

## 贡献

欢迎 PR、Issue、讨论。见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 许可证

MIT — 见 [LICENSE](LICENSE)
