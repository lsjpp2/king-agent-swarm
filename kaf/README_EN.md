# KAF · King-Agent Framework

> **Multi-Agent Governance Framework** — Constitution-as-Code + 520 Runtime Guard  
> Give your AI agent swarm rules, memory protection, and audit trails

[中文](./README.md) | English

---

## Why KAF?

You use CrewAI/Ruflo/MetaGPT to orchestrate multi-agent task execution, but you find:

- Agents **delete files they shouldn't** (your data is gone)
- Agents **scatter temp files everywhere** (disk fills up)
- Agents **overwrite critical configs** (rules/memories lost)
- Multiple agents **read each other's private memory** (isolation wall breached)
- When things go wrong, **no traceability** (no scripts, no logs)

**CrewAI manages "how to execute tasks". KAF manages "how to govern agents".** They complement each other.

## Core Concepts

```
Constitution-as-Code   Constitution: md docs → parseable JSON, rules machine-verifiable
520 Runtime Guard      From post-hoc checks → runtime hook interception
Memory Integrity       From "recover after loss" → "block before overwrite"
Platform Adapter       From platform-locked → 5 lines to adapt any platform
```

## Quick Start

```bash
# Initialize KAF
python kaf.py init

# 520 self-check (traceable/recoverable/fixable/evolvable)
python kaf.py check

# Memory integrity verification (fingerprint + drift detection)
python kaf.py verify

# View cluster status
python kaf.py status

# Coordinator rotation
python kaf.py rotate claude
```

## Five-Layer Architecture

```
┌─────────────────────────────────────────┐
│  Platform Adapters                       │
│  WorkBuddy / Claude / OpenCode / ...    │
├─────────────────────────────────────────┤
│  Coordinator Protocol (Prime Minister)   │
├─────────────────────────────────────────┤
│  520 Runtime Guard                       │
├─────────────────────────────────────────┤
│  Constitution-as-Code                    │
├─────────────────────────────────────────┤
│  Memory Integrity (SHA-256 + Drift)      │
└─────────────────────────────────────────┘
```

## The 520 Rule (Core)

| Principle | Meaning | Implementation |
|-----------|---------|----------------|
| Traceable | Every action has script + log | `kaf_operations.log` auto-recorded |
| Recoverable | Deletes go to recycle bin, configs backed up | `FOF_ALLOWUNDO` + `.bak` |
| Fixable | Errors can rollback | `on_failure` provides rollback plan |
| Evolvable | Extract workflows/rules/skills | Auto-skill packaging |

**Iron Laws 8/9/10**:
- Law 8: Script before execute + verify (rm/mv/copy → write .py → execute → ls verify)
- Law 9: Verify any number in memory (any quantity → find/ls verification)
- Law 10: Show list before delete (ls -R → show user → confirm then delete)

## File Structure

```
kaf/
├── constitution.json      Declarative constitution (machine-parseable)
├── guard520.py            520 runtime guard (4 checkpoints)
├── memory_integrity.py    Memory integrity (SHA-256 fingerprint + drift)
├── coordinator.json       Coordinator registry (rotation/voting/handover)
├── kaf.py                 CLI (init/check/verify/guard/rotate/status)
├── adapters/
│   ├── base.py            Adapter interface (7 methods)
│   ├── workbuddy.py       WorkBuddy adapter (implemented)
│   └── _template.py       New platform adapter template
└── examples/
    └── basic/             Basic example
```

## Add a New Platform

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

## Governance Layer vs Orchestration Layer

```
Your stack:
  CrewAI / Ruflo / LangGraph    ← Orchestration layer (how to execute tasks)
          +
  KAF                           ← Governance layer (how to govern agents)
          +
  SKILL.md standard             ← Skill standard
```

**KAF doesn't replace any framework — it adds a governance layer to all of them.**

## Battle-Tested

KAF originated from a real multi-agent cluster (WorkBuddy+OpenCode+Claude+Kimi+Cursor), refined through 3 months of production use and the v4 map deletion incident (2000+ historical maps irreversibly lost).

Not a toy demo — governance experience paid for with real data.

## License

MIT
