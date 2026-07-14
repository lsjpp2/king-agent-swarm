# 👑 KAF — 国王智能体框架

> **多智能体集群的治理层。**
> 别让你的 AI Agent 删了你的文件、越界乱建目录、还互相污染记忆。

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org)
[![520-Compliant](https://img.shields.io/badge/520-Rule%20Compliant-ff69b4.svg)](#-520-法则四原则三铁律)
[![Platform-agnostic](https://img.shields.io/badge/Platform-Agnostic-lightgrey.svg)](#-平台适配器)

你有 3+ 个 AI 编程助手 —— Claude Code、Cursor、OpenCode、Codex、Kimi…… 它们都跟你说话，彼此不沟通，而且**没有任何规则约束它们能碰什么**。

**CrewAI / LangGraph / Ruflo 解决"Agent 怎么一起执行任务"。**
**KAF 解决"你怎么管住 Agent 别把机器搞炸"。**

它不是编排器，而是架在任意编排器**之下**的**宪法 + 运行时护栏**。

---

## 🔥 你的 Agent 已经失控了（你心里有数）

- 某个 Agent `rm -rf` 了一个不该删的文件夹。**没了，没备份。**
- 某个 Agent 在你的 `C:\` 盘丢了 47 个临时文件。
- 某个 Agent 覆盖了 `constitution.json`。**你的规则没了。**
- 两个 Agent 读了对方的私有记忆。**上下文被污染。**
- 凌晨 2 点出了事。**没脚本、没日志，没人知道发生了什么。**

### 这不是纸上谈兵

KAF 诞生于一个真实运行 3 个月的 6-Agent 集群（WorkBuddy + OpenCode + Claude + Kimi + Cursor）。我们曾因一次不可逆删除，**丢了 2000+ 张地图素材**，之后才筑起这些护栏。

**KAF 是伤疤长出的肉。MIT 协议开源，你不用再流血。**

---

## 🛡️ 520 法则：四原则，三铁律

Agent 的每一个操作都必须满足：

| | 原则 | 代码里的含义 |
|:--|:--|:--|
| **5** | **可追溯** | 每个操作有脚本 + 日志（`kaf_operations.log`） |
| **2** | **可恢复** | 删除走回收站；配置改动前先备份 |
| **0** | **可修复** | 失败时 `on_failure()` 给你回滚方案 |
| **+** | **可进化** | 好工作流自动结晶成可复用 Skill |

**三条铁律 —— 运行时直接拦截，不只是警告：**

- 🔒 **铁律8** — 破坏性操作（`rm` / `mv` / `copy`）必须有脚本，且执行后验证。
- 🔒 **铁律9** — 写进记忆的任何数字，必须对照文件系统实地核查。
- 🔒 **铁律10** — 删除前，Agent 必须展示完整文件清单，并获得你确认。

### 运行时护栏实时拦截

```bash
$ python kaf.py guard
  pre:delete          → 铁律10：删除前展示清单+用户确认
  pre:destructive_op  → 铁律8：破坏性操作必须有脚本
  post:write_memory   → 铁律9：记忆数字实地核查
  startup             → 记忆完整性：指纹校验
```

```python
from guard520 import Guard520
guard = Guard520("constitution.json")

guard.pre_execute({"type": "rm", "target": "D:/x"})
# → block: 铁律8违规：rm 操作无脚本

guard.pre_delete({"type": "rm", "target": "constitution.json"})
# → block: 铁律10违规：未展示清单/未获确认。待删1项

guard.pre_execute({"type": "rm", "target": "D:/x", "script": "clean.py", "verified": True})
# → ok
```

**没有配置项、没有 `--force`、没有"你确定吗"可以绕过。护栏返回 `BLOCK` 并写进日志。**

---

## 🏛️ 架构：五层

```
┌─────────────────────────────────────────────┐
│  平台适配器   (WorkBuddy/Claude/...)          │  5 行代码接入
├─────────────────────────────────────────────┤
│  协调协议   (宰相轮值)                         │  此刻谁说了算
├─────────────────────────────────────────────┤
│  520 运行时护栏 (4 个检查点)                   │  拦截铁律8/9/10 违规
├─────────────────────────────────────────────┤
│  宪法即代码 (JSON，可机读)                     │  规则可 diff、可 CI 测试
├─────────────────────────────────────────────┤
│  记忆完整性 (SHA-256 指纹)                     │  检测未授权漂移
└─────────────────────────────────────────────┘
```

为什么用 JSON 而不是 markdown 文档？因为你的宪法要能**被解析、被 diff、被 CI 测试**，而不只是被读。

---

## ⚡ 快速开始

```bash
git clone https://github.com/lsjpp2/king-agent-swarm.git
cd king-agent-swarm/kaf

python kaf.py init      # 生成 constitution.json + 注册记忆指纹
python kaf.py check     # 520 自检  →  ✅ PASS
python kaf.py verify    # 记忆完整性（指纹 + 漂移检测）
python kaf.py status    # 当前谁是宰相
```

新集群真实 `kaf check` 输出：

```
==================================================
  KAF 520 自检
==================================================
  ✅ traceable: 日志记录能力: 就绪 | 日志文件: 待生成（首次运行正常）
  ✅ recoverable: 删除操作走回收站(FOF_ALLOWUNDO)
  ✅ fixable: on_failure提供回滚方案
  ✅ evolvable: skill目录: .../.workbuddy/skills (25个skill)

  总体: PASS
```

---

## 📜 宪法即代码

你的治理是一份 JSON，不是一句感觉：

```json
{
  "rule_520": {
    "enabled": true,
    "immutable": true,
    "note": "就算世界灭亡，这个标准不能丢",
    "iron_laws": {
      "law_8": "script_then_execute_then_verify",
      "law_9": "verify_any_number_in_memory",
      "law_10": "show_list_before_delete"
    }
  },
  "rules": [
    { "id": "delete_auth", "trigger": "pre:delete",
      "require": "user_confirm", "irreversible_action": "warn_and_block" },
    { "id": "path_discipline", "trigger": "pre:write",
      "allow_only": "{{workspace}}/**",
      "blocked_zones": ["Desktop", "Documents", "Downloads", "system_root"] }
  ]
}
```

光是路径纪律这一条，就能挡掉约 90% 的"为什么我桌面全是 Agent 垃圾"事故。

---

## 🆚 KAF 有什么不同？

| | KAF | CrewAI / LangGraph | RuFlo | AutoGen |
|:--|:--|:--|:--|:--|
| 层级 | **治理层**（怎么*管* Agent） | 编排层（怎么*跑*任务） | 同质蜂群 | 对话编排 |
| 危险操作护栏 | ✅ 运行时**拦截** | ❌ | ❌ | ❌ |
| 路径纪律 | ✅ 内置 | ❌ | ❌ | ❌ |
| 记忆隔离墙 | ✅ | ⚠️ 手动 | ❌ | ❌ |
| 宪法即代码 | ✅ JSON，可 CI 测 | ❌ | ❌ | ❌ |
| 异构 Agent | ✅ Claude+Cursor+…+ | ⚠️ | ❌ (仅 Claude) | ⚠️ |
| 跨平台 | ✅ 适配器 SDK | 各异 | ❌ | ⚠️ |

**KAF 不取代它们，它治理它们。** 架在任意编排器之下即可。

---

## 🔌 平台适配器

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

`WorkBuddy` 适配器已内置。`Claude` / `Cursor` / `OpenCode` 适配器为文档式（`adapters/*.md`）。完整 SDK 见 [`kaf/adapters/`](kaf/adapters)。

---

## 📂 仓库结构

```
king-agent-swarm/
├── kaf/                      # ★ KAF v5.0 核心（这才是框架）
│   ├── constitution.json     # 声明式宪法（可机读）
│   ├── guard520.py           # 520 运行时护栏（4 检查点）
│   ├── memory_integrity.py   # SHA-256 指纹 + 漂移检测
│   ├── coordinator.json      # 宰相注册表（轮值 / 投票）
│   ├── kaf.py                # CLI: init / check / verify / guard / rotate / status
│   ├── adapters/             # 平台 SDK（base / workbuddy / template）
│   └── README.md             # 深入解析（中文 + English）
├── templates/                # 协调协议层（v1，纯配置）
├── docs/                     # 架构 / 快速开始 / 原则 / FAQ
├── adapters/                 # 各平台注入指南（.md）
├── diagrams/                 # SVG 架构图
└── examples/                 # 最小 3-Agent 与完整 6-Agent 集群
```

KAF 是引擎；`templates/` + `docs/` + `diagrams/` 构成**协调协议层** —— KAF 脱胎自的 v1"国王 / 宰相 / 蜂群"隐喻。

---

## 🤝 贡献

欢迎 PR、Issue、和你的血泪史。见 [CONTRIBUTING.md](CONTRIBUTING.md)。

连治理本身也被治理：`用户反馈 → 宰相评估 → 国王确认 → 合并`。

## 📄 许可证

MIT — 见 [LICENSE](LICENSE)。
