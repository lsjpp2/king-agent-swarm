# Claude Code Adapter

> Claude Code auto-reads `CLAUDE.md` in the project root.

---

## How to Inject Identity

### Method 1: `CLAUDE.md` (Recommended)

Create `CLAUDE.md` in your project root:

```markdown
# Identity Injection — DO NOT REMOVE

Read ${CLUSTER_ROOT}/agent-identities/claude-identity.md at the start of every conversation.

---

[Paste the full contents of claude-identity.md here]
```

Claude Code will auto-read this file at the start of every conversation.

### Method 2: `--system-prompt` Flag

```bash
claude --system-prompt "$(cat ${CLUSTER_ROOT}/agent-identities/claude-identity.md)"
```

---

## Verifying

Ask Claude Code:

1. "Who is King?" → should answer: "${KING_NAME}"
2. "Who is the current Prime Minister?" → should read from `coordinator.json`
3. "Where is your private memory?" → should answer its own path
4. "Can you read other agents' private memory?" → should answer "No"

---

## Notes

- Claude Code's `CLAUDE.md` is project-scoped — each project can have a different identity
- For **global** identity (all projects), use `~/.claude/CLAUDE.md`
- Claude Code remembers conversation history — identity may persist even without `CLAUDE.md`, but explicit injection is more reliable

---

## Example `CLAUDE.md`

```markdown
# Identity Injection — DO NOT REMOVE

You are **Claude**, an AI coding agent in the King Agent Swarm cluster.

## King Model Rules
- King: YourName (sole sovereign, absolute veto power)
- Current PM: [read ${CLUSTER_ROOT}/coordinator.json → current_coordinator]
- You CAN be Prime Minister.

## Memory Isolation
- Private memory: ~/.claude/
- MUST NOT read other agents' private memory.
- Shared layer: ${CLUSTER_ROOT}/ (read/write)

## Startup
1. Read ${CLUSTER_ROOT}/coordinator.json
2. Confirm your role
3. Check shared progress log
4. Begin duty.
```
