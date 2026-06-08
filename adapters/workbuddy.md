# WorkBuddy Adapter

> WorkBuddy is the current Prime Minister in the reference implementation.

---

## How to Inject Identity into WorkBuddy

WorkBuddy loads skills from two locations:
- **User-level**: `~/.workbuddy/skills/` (shared across all projects)
- **Project-level**: `{workspace}/.workbuddy/skills/` (project-specific)

### Method: Create a Skill

1. Create the skill directory:
   ```
   ~/.workbuddy/skills/${AGENT_NAME}-identity/
   ```

2. Create `SKILL.md` with the identity card content:

```markdown
---
name: ${AGENT_NAME}-identity
description: Identity card for ${AGENT_NAME} in the King Agent Swarm cluster.
agent_created: true
---

# ${AGENT_NAME} Identity Card

[Full identity card content from templates/agent-identity.md]
```

3. WorkBuddy will load this skill automatically when the agent name is mentioned.

---

## Verifying

Ask WorkBuddy:
1. "你是谁?" → should answer agent name and role
2. "当前宰相是谁?" → should read from `coordinator.json`
3. "你的私有记忆库在哪里?" → should answer its private memory path

---

## Notes

- WorkBuddy's memory system (`.workbuddy/memory/`) serves as the private memory layer
- The shared layer is `${CLUSTER_ROOT}/` (typically `D:\Agent集群共享\` in the reference implementation)
- WorkBuddy can directly edit `coordinator.json` (since it's currently PM)
