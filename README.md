# 👑 KAF — King-Agent Framework

> **The governance layer for multi-agent swarms.**
> Stop your AI agents from deleting your files, escaping their workspace, and gaslighting each other.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org)
[![520-Compliant](https://img.shields.io/badge/520-Rule%20Compliant-ff69b4.svg)](#-the-520-rule)
[![Platform-agnostic](https://img.shields.io/badge/Platform-Agnostic-lightgrey.svg)](#-platform-adapters)
[![Made from real scars](https://img.shields.io/badge/forged%20in-production-red.svg)](#-your-agents-are-out-of-control-and-you-know-it)

You run 3+ AI coding agents — Claude Code, Cursor, OpenCode, Codex, Kimi… They talk to **you**. They don't talk to **each other**. And they have **no rules about what they can touch.**

**CrewAI / LangGraph / Ruflo answer "how do agents execute tasks together."**
**KAF answers "how do you stop agents from wrecking your machine."**

It's not an orchestrator. It's the **constitution + runtime guardrail** that sits *under* any orchestrator.

---

## 🔥 Your agents are out of control (and you know it)

- An agent `rm -rf`'d a folder it shouldn't have. **Gone. No backup.**
- An agent dropped 47 temp files across your `C:\` drive.
- An agent overwrote `constitution.json`. **Your rules vanished.**
- Two agents read each other's private memory. **Context contaminated.**
- Something broke at 2 AM. **No script, no log. Nobody knows what happened.**

### This is not theoretical

KAF was forged inside a real 6-agent cluster (WorkBuddy + OpenCode + Claude + Kimi + Cursor) running daily for 3 months. We lost **2000+ map assets** to one irreversible delete before we built the guardrails.

**KAF is the scar tissue. MIT-licensed, so you don't have to bleed for it.**

---

## 🛡️ The 520 Rule — four principles, three iron laws

Every action an agent takes must be:

| | Principle | What it means in code |
|:--|:--|:--|
| **5** | **Traceable** | Every op has a script + log entry (`kaf_operations.log`) |
| **2** | **Recoverable** | Deletes go to recycle bin; configs are backed up first |
| **0** | **Fixable** | On failure, `on_failure()` hands you rollback options |
| **+** | **Evolvable** | Good workflows auto-crystallize into reusable Skills |

**Three Iron Laws — violations are blocked at runtime, not just warned:**

- 🔒 **Law 8** — Destructive ops (`rm` / `mv` / `copy`) MUST come from a script, then be verified.
- 🔒 **Law 9** — Any number written to memory MUST be verified against the filesystem.
- 🔒 **Law 10** — Before deleting, the agent MUST show the full file list and get your confirmation.

### Live guardrail interception

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

**No config, no `--force`, no "are you sure?" bypass. The guard returns `BLOCK` and writes it to the log.**

---

## 🏛️ Architecture — five layers

```
┌─────────────────────────────────────────────┐
│  Platform Adapters   (WorkBuddy/Claude/...)  │  5 lines of code to plug in
├─────────────────────────────────────────────┤
│  Coordinator Protocol  (Prime Minister rotate)│  who's in charge, right now
├─────────────────────────────────────────────┤
│  520 Runtime Guard     (4 checkpoints)        │  blocks Law 8/9/10 violations
├─────────────────────────────────────────────┤
│  Constitution-as-Code (JSON, machine-readable)│  rules you can diff & CI-test
├─────────────────────────────────────────────┤
│  Memory Integrity      (SHA-256 fingerprint)  │  detect unauthorized drift
└─────────────────────────────────────────────┘
```

Why JSON, not a markdown doc? So your constitution can be **parsed, diffed, and CI-tested** — not just read.

---

## ⚡ Quick start

```bash
git clone https://github.com/lsjpp2/king-agent-swarm.git
cd king-agent-swarm/kaf

python kaf.py init      # generate constitution.json + register memory fingerprints
python kaf.py check     # 520 self-check  →  ✅ PASS
python kaf.py verify    # memory integrity (fingerprint + drift detect)
python kaf.py status    # who's the current Prime Minister
```

Real `kaf check` output on a fresh cluster:

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

## 📜 Constitution-as-Code

Your governance is a JSON file, not a vibe:

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

Path discipline alone stops ~90% of "why is my Desktop full of agent junk" incidents.

---

## 🆚 How is KAF different?

| | KAF | CrewAI / LangGraph | RuFlo | AutoGen |
|:--|:--|:--|:--|:--|
| Layer | **Governance** (how to *rule* agents) | Orchestration (how to *run* tasks) | Homogeneous swarm | Conversation orchestration |
| Dangerous-op guard | ✅ runtime **BLOCK** | ❌ | ❌ | ❌ |
| Path discipline | ✅ built-in | ❌ | ❌ | ❌ |
| Memory isolation walls | ✅ | ⚠️ manual | ❌ | ❌ |
| Constitution-as-Code | ✅ JSON, CI-testable | ❌ | ❌ | ❌ |
| Heterogeneous agents | ✅ Claude+Cursor+…+ | ⚠️ | ❌ (Claude-only) | ⚠️ |
| Platform-agnostic | ✅ adapter SDK | varies | ❌ | ⚠️ |

**KAF doesn't replace them. It governs them.** Drop it under any orchestrator.

---

## 🔌 Platform Adapters

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

The `WorkBuddy` adapter ships in-box. `Claude` / `Cursor` / `OpenCode` adapters are doc-based (`adapters/*.md`). Full SDK in [`kaf/adapters/`](kaf/adapters).

---

## 📂 Repository layout

```
king-agent-swarm/
├── kaf/                      # ★ KAF v5.0 core (this is the framework)
│   ├── constitution.json     # declarative constitution (machine-readable)
│   ├── guard520.py           # 520 runtime guard — 4 checkpoints
│   ├── memory_integrity.py   # SHA-256 fingerprint + drift detection
│   ├── coordinator.json      # Prime Minister registry (rotate / vote)
│   ├── kaf.py                # CLI: init / check / verify / guard / rotate / status
│   ├── adapters/             # platform SDK (base / workbuddy / template)
│   └── README.md             # deep dive (中文 + English)
├── templates/                # coordination-protocol layer (v1, config-only)
├── docs/                     # architecture / quick-start / principles / faq
├── adapters/                 # per-platform injection guides (.md)
├── diagrams/                 # SVG architecture diagrams
└── examples/                 # minimal 3-agent & 6-agent clusters
```

KAF is the engine; `templates/` + `docs/` + `diagrams/` form the **coordination-protocol layer** — the v1 "King / Prime Minister / Swarm" metaphor that KAF grew out of.

---

## 🤝 Contributing

PRs, issues, and war stories welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

Even the governance is governed: `user_feedback → coordinator_evaluate → king_confirm → merge`.

## 📄 License

MIT — see [LICENSE](LICENSE).
