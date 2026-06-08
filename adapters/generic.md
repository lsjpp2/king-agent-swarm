# Generic Adapter — Any LLM Agent

> Use this adapter for any agent that supports a `system_prompt`, `instructions`, or project-level config file.

---

## Does Your Agent Support System Prompt Injection?

| Agent supports... | Use this method |
|:---|:---|
| `system_prompt` parameter | Pass identity card as system prompt |
| Project-level config (e.g. `CLAUDE.md`, `.cursorrules`) | Paste identity card into that file |
| Only chat interface | Paste identity card as first message of conversation |

---

## Method 1: System Prompt Parameter

If your agent API accepts a `system_prompt` field:

```python
system_prompt = open("${CLUSTER_ROOT}/agent-identities/${AGENT_NAME}-identity.md").read()

# Pass to your agent API
response = agent.chat(system_prompt=system_prompt, user_prompt=...)
```

---

## Method 2: Project-Level Config File

Most coding agents auto-read a project-level file. Create or edit:

| Agent | File | Location |
|:---|:---|:---|
| Claude Code | `CLAUDE.md` | Project root |
| Cursor | `.cursorrules` | Project root |
| OpenCode | `opencode.jsonc` → `instructions` array | `~/.config/opencode/` |
| Codex | `codex-config.json` → `system_prompt` | Agent config dir |
| Windsurf | `.windsurfrules` | Project root |
| **Any agent** | `[agent-name].md` | Project root (paste contents into first message if auto-read fails) |

**What to paste into the file**:

```markdown
# Identity Injection — DO NOT REMOVE

Read `${CLUSTER_ROOT}/agent-identities/${YOUR_AGENT_NAME}-identity.md` on every conversation start.

If you cannot read files, ask the user to paste the identity card into this window.

---

[PASTE IDENTITY CARD CONTENTS HERE]
```

---

## Method 3: First-Message Paste (Fallback)

If the agent has *no* system prompt support:

1. Start a new conversation with the agent
2. Paste the entire identity card (`${CLUSTER_ROOT}/agent-identities/${YOUR_AGENT_NAME}-identity.md`)
3. Say: "This is your identity. Please confirm you understand."

The agent should acknowledge and retain this for the conversation.

**Limitation**: Does not persist across conversations. You must re-paste each time.

---

## Verifying Injection Worked

After injecting identity, ask the agent:

1. "Who is King?" → should answer: "${KING_NAME}"
2. "Who is the current Prime Minister?" → should read from `coordinator.json`
3. "Where is your private memory?" → should answer its own path
4. "Can you read other agents' private memory?" → should answer "No"

If any answer is wrong, the injection didn't work. Try a different method.

---

## Minimal Identity Card for Generic Agents

```markdown
# ${AGENT_NAME} Identity Card

## Core Identity
You are **${AGENT_NAME}**, a ${ROLE_DESCRIPTION}.

## King Model Rules
- King: ${KING_NAME} (sole sovereign, absolute veto)
- Current PM: [read ${CLUSTER_ROOT}/coordinator.json → current_coordinator]
- You ${CAN_BE_PM} take over as PM.

## Memory Isolation
- Private memory: ${PRIVATE_MEMORY_PATH}
- MUST NOT read other agents' private memory.
- Shared layer: ${CLUSTER_ROOT}/ (read/write)

## Startup
1. Read coordinator.json
2. Confirm your role
3. Check shared progress log
4. Begin duty.
```

---

## Troubleshooting

**Agent ignores identity card** → The agent may not actually load system prompts. Try Method 3 (first-message paste).

**Agent "forgets" its identity mid-conversation** → LLM context decay. The identity card should be re-pasted or re-read periodically in long conversations.

**Agent reads other agents' private memory anyway** → The protocol is conventions, not enforcement. The agent's model may not respect the rule. Add explicit reminders in the identity card.
