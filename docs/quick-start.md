# Quick Start Guide

## Prerequisites

- 2+ AI coding agents installed (Claude Code, Cursor, OpenCode, Codex, etc.)
- Basic familiarity with editing JSON and Markdown files

---

## Step 1: Clone & Initialize

```bash
git clone https://github.com/YOUR_USER/king-agent-swarm.git
cd king-agent-swarm

# Copy templates to your cluster root
cp templates/* ${CLUSTER_ROOT}/
```

Set these environment variables (or edit the templates directly):

```bash
export KING_NAME="YourName"
export CLUSTER_ROOT="/path/to/your/cluster/shared"
export DEFAULT_PM="AgentName"  # which agent is PM first
```

---

## Step 2: Edit `coordinator.json`

Open `coordinator.json` and fill in your agents:

```json
{
  "_king": "YourName",
  "current_coordinator": "Cursor",
  "agent_registry": {
    "Cursor": {
      "platform": "Cursor IDE",
      "role": "Prime Minister (rotating)",
      "can_be_pm": true,
      "identity_file": "/path/to/cluster/shared/agent-identities/cursor-identity.md",
      "private_memory": "/path/to/cursor/memory"
    },
    "Claude": {
      "platform": "Claude Code",
      "role": "Agent (can be PM)",
      "can_be_pm": true,
      "identity_file": "/path/to/cluster/shared/agent-identities/claude-identity.md",
      "private_memory": "/path/to/claude/memory"
    }
  }
}
```

---

## Step 3: Create Agent Identity Cards

For each agent, create `agent-identities/${AGENT_NAME}-identity.md`:

```markdown
# Cursor Identity Card

## Core Identity
You are **Cursor**, an AI coding agent embedded in VS Code.

## King Model Rules
- King: YourName (sole sovereign)
- Current PM: [read from coordinator.json]
- You CAN be Prime Minister.

## Memory Isolation
- Private memory: /path/to/cursor/memory
- MUST NOT read other agents' private memory.
- Shared layer: /path/to/cluster/shared/ (read/write)

## Startup Self-Check
1. Read /path/to/cluster/shared/coordinator.json
2. Read this identity file
3. Read /path/to/cluster/shared/progress/ today's file
4. Begin duty.
```

---

## Step 4: Inject Identity into Each Agent

| Agent | How to Inject |
|:---|:---|
| Cursor | Add to `.cursorrules` in project root |
| Claude Code | Add to `CLAUDE.md` in project root |
| OpenCode | Add to `opencode.jsonc` → `instructions` array |
| Codex | Add to `codex-config.json` → `system_prompt` |
| Kimi | Paste identity card at start of first conversation |
| **Any LLM** | Add as `system_prompt` |

See `adapters/` directory for detailed instructions per platform.

---

## Step 5: Verify

Ask each agent:

1. "Who is King?" → should answer your name
2. "Who is the current Prime Minister?" → should answer from `coordinator.json`
3. "Where is your private memory?" → should answer its own path
4. "Can you read other agents' private memory?" → should answer "No"

If any agent fails these checks, re-check the identity injection.

---

## Step 6: First Rotation (Optional)

Once everything works, test rotation:

Say to any agent: **"From now on, Claude is Prime Minister."**

Expected behavior:
1. Current PM hands over `handover_state`
2. `coordinator.json` updates `current_coordinator` to `"Claude"`
3. Claude confirms: "I have taken over as Prime Minister."

---

## Minimal Example: 2 Agents

You don't need 6 agents. A minimal swarm is:

```
You (King)
  └── Agent A (PM by default)
        └── Agent B
```

Even this gives you: memory isolation + clear coordination + rotation ability.

See `examples/minimal-3-agent.md` for a step-by-step walkthrough.

---

## Next Steps

- Read `docs/principles.md` — why each rule exists
- Read `docs/architecture.md` — full design philosophy
- Join the discussion: [GitHub Discussions](https://github.com/YOUR_USER/king-agent-swarm/discussions)
