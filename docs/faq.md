# FAQ

## General

### Q: Is this a coding framework?
**A**: No. It's a *coordination protocol* — a set of conventions (Markdown files + JSON configs) that tell your agents how to work together. You can use it alongside any coding framework (AutoGen, LangGraph, etc.) or with no framework at all.

---

### Q: How is this different from RuFlo Swarm?
**A**: RuFlo uses homogeneous Claude Code instances with shared memory. King Agent Swarm uses *heterogeneous* agents (Claude + Cursor + OpenCode + ...) with *memory isolation*. 

If all your agents are Claude Code → RuFlo is simpler.
If you have different types of agents → King Swarm is the only option.

---

### Q: Do agents talk to each other directly?
**A**: No. Al coordination happens through shared files:
- `coordinator.json` — who's in charge
- `progress/YYYY-MM-DD.md` — shared progress log
- `handover_state` in coordinator.json — PM handover context

This avoids the "telephone game" problem where messages get distorted.

---

### Q: Minimum number of agents?
**A**: 2 (King + 1 agent, PM role defaults to the only agent). Useful configuration: 3 agents (King + 2 agents, one acts as PM).

---

### Q: Can I use this with just 1 agent?
**A**: Technically yes, but there's no point — the value is in coordination. With 1 agent, just use its native memory/system prompt.

---

## Configuration

### Q: Where do I put `${CLUSTER_ROOT}`?
**A**: Any directory all your agents can read/write. Typically:
- Windows: `D:\agent-cluster\` or `C:\Users\You\agent-cluster\`
- macOS/Linux: `~/agent-cluster/`

---

### Q: What if I add a new agent later?
**A**: 
1. Add it to `coordinator.json → agent_registry`
2. Create its identity card at `agent-identities/NAME-identity.md`
3. Inject the identity into the agent (see `adapters/`)
4. Tell King (yourself): "X is now part of the swarm"

---

### Q: Can an agent be PM and do work at the same time?
**A**: Yes. PM is a *role*, not a full-time job. The PM agent still executes tasks — it just also coordinates and gets 3 votes in conflicts.

---

## Rotation

### Q: What happens to in-progress tasks during rotation?
**A**: `handover_state` in `coordinator.json` carries forward:
- `active_projects` — what's in progress
- `pending_decisions` — what needs a decision
- `last_handover_dump` — free-text context summary

The new PM reads this and continues.

---

### Q: Can I rotate PM in the middle of a task?
**A**: Yes, but it's not recommended. Rotate between tasks for clean handover. If you must rotate mid-task, ensure `handover_state` includes the task's current state.

---

### Q: What if the PM agent crashes or is unavailable?
**A**: King manually appoints a new PM: "X is PM now." The old PM's `handover_state` may be incomplete — King and new PM should do a quick sync.

---

## Security

### Q: Can an agent "lie" about being PM?
**A**: Technically yes (an agent could claim to be PM in its responses). The protocol relies on *you* (King) checking `coordinator.json` to verify. Future versions may add cryptographic signing.

---

### Q: Is my private memory exposed?
**A**: No. The protocol explicitly forbids agents from reading each other's private memory. Each agent's private memory path is listed in `coordinator.json` but agents are instructed (via their identity card) not to read others'.

---

## Troubleshooting

### Q: My agent says "I don't know who King is."
**A**: Identity injection failed. Check:
1. Did you add the identity card path to the agent's system prompt / instructions?
2. Does the agent actually read files? (Some agents don't auto-read; you may need to paste the identity card into the first message.)

---

### Q: Agents still contradict each other.
**A**: Memory isolation means they don't share context automatically. Use the shared layer (`progress/` files) to explicitly share key decisions. Also ensure PM is doing its job coordinating.

---

### Q: Rotation didn't work — old PM didn't hand over.
**A**: The current implementation relies on the old PM *voluntarily* executing the handover steps. If the old PM is non-compliant or confused, King (you) must manually update `coordinator.json` and tell the new PM to take over.

---

## Contributing

### Q: I found a bug / have a suggestion.
**A**: Open a GitHub Issue or Pull Request. This is an open-source project — improvements welcome.

---

### Q: Can I fork this for my own variant?
**A**: Absolutely. MIT License — go wild. Credit appreciated but not required.
