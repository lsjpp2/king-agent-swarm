# 👑 King Agent Swarm

**A coordination protocol for multi-AI-agent clusters.**

You have 3+ AI coding agents (Claude Code, Cursor, OpenCode, Codex, etc.).
They talk to you. They don't talk to each other.
They step on each other's memory. They give conflicting answers.

**King Agent Swarm fixes this** with three simple files and one clear metaphor:

```
You (King)
  └── Prime Minister (active coordinator, rotates)
        ├── Agent A
        ├── Agent B
        └── Agent C
```

---

## What It Does

| Problem | Solution |
|:---|:---|
| 6 agents, zero coordination | `coordinator.json` — one source of truth for who's in charge |
| Agent memories contaminate each other | Memory isolation walls — each agent has its own private memory |
| No way to switch who leads | Rotation protocol — king says "X is PM now," old PM hands over, new PM takes over |
| Agents drift from original intent | Anti-Drift checkpoint every 5 steps |

---

## Quick Start

```bash
git clone https://github.com/YOUR_USER/king-agent-swarm.git
cd king-agent-swarm

# Generate your cluster config
./init.sh --king "YourName" --cluster-path "/path/to/cluster/shared"

# Deploy to your agents
cat templates/constitution.md      # Copy to all agents
cat templates/handover-protocol.md # Copy to all agents
```

Read the full guide: [docs/quick-start.md](docs/quick-start.md)

---

## Why "King & Prime Minister"?

Most multi-agent frameworks use dry terms like "orchestrator" and "worker." Nobody remembers what those mean the next day.

**King / Prime Minister / Swarm** is:
- One mental model, instantly understood
- Culturally intuitive (from monarchy to modern governance)
- Easy to explain to non-technical stakeholders

---

## Architecture

See [docs/architecture.md](docs/architecture.md) for full design philosophy, comparison with alternatives (RuFlo, AutoGen, CrewAI), and formal state definitions.

Key diagrams:

| Diagram | Description |
|:---|:---|
| [Power Structure](diagrams/01-power-structure.svg) | King → PM → Agent hierarchy |
| [Memory Isolation](diagrams/02-memory-isolation.svg) | Shared layer vs private memory walls |
| [Rotation Flow](diagrams/03-rotation-flow.svg) | PM handover protocol |

---

## Supported Agents

| Agent | Adapter | Method |
|:---|:---|:---|
| Claude Code | [adapters/claude.md](adapters/claude.md) | `CLAUDE.md` project-level injection |
| Cursor | [adapters/cursor.md](adapters/cursor.md) | `.cursorrules` injection |
| OpenCode | [adapters/opencode.md](adapters/opencode.md) | `opencode.jsonc` instructions array |
| Codex | [adapters/generic.md](adapters/generic.md) | Config JSON injection |
| Kimi | [adapters/generic.md](adapters/generic.md) | First-message identity paste |
| WorkBuddy | [adapters/generic.md](adapters/generic.md) | System prompt hook |
| **Any LLM agent** | [adapters/generic.md](adapters/generic.md) | `system_prompt` injection |

---

## Core Principles

1. **Human sovereignty** — the king (human) has absolute veto power
2. **Memory isolation** — agents never read each other's private memory
3. **Coordinator rotation** — prime minister role rotates on king's command
4. **Conflict resolution** — PM gets 3 votes, others get 1, king vetoes
5. **Anti-drift** — alignment check every 5 tool calls on long tasks

Design rationale for each principle: [docs/principles.md](docs/principles.md)

---

## Repository Structure

```
king-agent-swarm/
├── README.md              # You are here
├── LICENSE                # MIT
├── docs/
│   ├── architecture.md    # Full design philosophy
│   ├── quick-start.md     # 10-minute setup guide
│   ├── principles.md      # Why each rule exists
│   └── faq.md             # Common questions
├── templates/
│   ├── coordinator.json   # Agent registry template
│   ├── constitution.md    # Cluster constitution template
│   ├── handover-protocol.md
│   └── agent-identity.md  # Per-agent identity card template
├── adapters/
│   ├── claude.md          # Claude Code adapter
│   ├── cursor.md          # Cursor adapter
│   ├── opencode.md        # OpenCode adapter
│   └── generic.md         # Universal LLM agent adapter
├── diagrams/              # SVG architecture diagrams
├── examples/
│   ├── minimal-3-agent.md # Simplest possible cluster
│   └── 6-agent-cluster.md # Full production cluster
├── init.sh                # Unix setup script
└── init.ps1               # Windows setup script
```

---

## FAQ

**Is this tied to a specific platform?**
No. It's pure config files (Markdown + JSON). Any LLM agent that can read files can join the swarm.

**Why not use AutoGen / CrewAI / LangGraph?**
Those are code-level orchestration frameworks. King Agent Swarm operates at the **protocol level** — it's about rules and conventions, not API calls. You can use it alongside any orchestration framework.

**Does it work with only 2 agents?**
Yes. The minimum viable swarm is: King + 1 Agent (acting as PM by default).

**How do agents actually communicate?**
Through the shared layer (`coordinator.json` + progress log). Direct agent-to-agent messaging is out of scope (and often the source of chaos).

---

## License

MIT — see [LICENSE](LICENSE)
