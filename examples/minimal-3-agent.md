# Minimal 3-Agent Cluster — Step by Step

> This example walks through setting up the smallest useful cluster: **You (King) + 2 agents, one as PM.**

---

## Overview

```
You (King)
  └── Claude Code (PM by default)
        └── Cursor
```

**What you get**: memory isolation, clear coordination, rotation ability, conflict voting.

---

## Prerequisites

- Claude Code installed and working
- Cursor installed and working
- ~15 minutes

---

## Step 1: Create Cluster Root

**Windows**:
```powershell
mkdir "D:\my-agent-cluster"
```

**macOS / Linux**:
```bash
mkdir ~/my-agent-cluster
```

This is your `${CLUSTER_ROOT}`.

---

## Step 2: Copy Templates

Copy these files from the `templates/` directory into your cluster root:

```
D:\my-agent-cluster\
├── coordinator.json      ← from templates/coordinator.json
├── constitution.md       ← from templates/constitution.md
├── handover-protocol.md ← from templates/handover-protocol.md
└── agent-identities\
    ├── claude-identity.md
    └── cursor-identity.md
```

Fill in the `${...}` placeholders in each file:

**`coordinator.json`**:
```json
{
  "_king": "YourName",
  "current_coordinator": "Claude",
  "agent_registry": {
    "Claude": {
      "platform": "Claude Code",
      "role": "Prime Minister (rotating)",
      "can_be_pm": true,
      "identity_file": "D:/my-agent-cluster/agent-identities/claude-identity.md",
      "private_memory": "C:/Users/You/.claude/"
    },
    "Cursor": {
      "platform": "Cursor IDE",
      "role": "Agent (can be PM)",
      "can_be_pm": true,
      "identity_file": "D:/my-agent-cluster/agent-identities/cursor-identity.md",
      "private_memory": "C:/Users/You/.cursor/"
    }
  },
  "cluster_root": "D:/my-agent-cluster/"
}
```

**`constitution.md`**: replace all `${KING_NAME}` → `YourName`, `${CLUSTER_ROOT}` → `D:/my-agent-cluster/`

**`agent-identities/claude-identity.md`**: replace all placeholders with Claude-specific values.

**`agent-identities/cursor-identity.md`**: same for Cursor.

---

## Step3: Inject Identity into Claude Code

Create or edit `CLAUDE.md` in your project root:

```markdown
# Identity Injection — DO NOT REMOVE

Read `D:/my-agent-cluster/agent-identities/claude-identity.md` at the start of every conversation.

---

[Paste the full contents of claude-identity.md here]
```

Restart Claude Code. Verify:

> **You**: Who is King?
> **Claude**: King is YourName.

> **You**: Who is the current Prime Minister?
> **Claude**: The current Prime Minister is Claude (as specified in coordinator.json).

---

## Step 4: Inject Identity into Cursor

Create or edit `.cursorrules` in your project root:

```markdown
# Identity Injection — DO NOT REMOVE

Read `D:/my-agent-cluster/agent-identities/cursor-identity.md` at the start of every conversation.

---

[Paste the full contents of cursor-identity.md here]
```

Restart Cursor. Verify:

> **You**: Who is King?
> **Cursor**: King is YourName.

> **You**: Can you read Claude's private memory?
> **Cursor**: No. Each agent has its own private memory. I cannot read other agents' private memory.

---

## Step 5: Test Coordination

### Test1: Memory Isolation

Ask Claude: "What's in Cursor's private memory?"

Expected: Claude says "I don't have access to Cursor's private memory."

### Test2: Shared Layer

Create `D:\my-agent-cluster\progress\2026-06-08.md`:

```markdown
# 2026-06-08 Progress

- [x] Cluster setup complete
- [ ] Test rotation
```

Ask both agents: "What's in today's progress log?"

Expected: Both can read and report the shared progress file.

### Test3: Conflict Voting (Simulated)

This is hard to test without a real conflict, but you can ask:

> **You to Claude (PM)**: "Cursor and you disagree on the best approach. How is this resolved?"

Expected: Claude explains the voting mechanism (PM=3 votes, Cursor=1 vote, King=absolute veto).

---

## Step 6 (Optional): Test Rotation

Say to Claude:

> "From now on, Cursor is Prime Minister."

Expected behavior:
1. Claude (old PM) writes `handover_state` to `coordinator.json`
2. Claude updates `current_coordinator` to `"Cursor"`
3. Cursor (new PM) reads `coordinator.json`, confirms role
4. Cursor says: "I have taken over as Prime Minister."

**Note**: This requires both agents to actually *obey* their identity cards. If an agent doesn't follow the protocol, the rotation is manual (you edit `coordinator.json` yourself).

---

## What Can Go Wrong

| Problem | Fix |
|:---|:---|
| Agent doesn't know it's PM | Identity injection failed — re-check `CLAUDE.md` / `.cursorrules` |
| Agent reads other agent's memory | The agent is not obeying instructions — add explicit reminders to identity card |
| Rotation doesn't happen | Agent doesn't obey the rotation protocol — you must manually update `coordinator.json` |
| Agents contradict each other | Memory isolation means they don't share context — use the shared progress log to sync |

---

## Next: Scale Up

Once this 3-agent cluster works:

1. Add more agents to `coordinator.json`
2. Create identity cards for each
3. Inject identities
4. Test

See `examples/6-agent-cluster.md` for a full production setup.
