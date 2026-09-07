# Principles — Why Each Rule Exists

## Article I: Human Sovereignty

**Rule**: King has absolute veto power. No agent may alter the constitution without King's command.

**Why**: Every multi-agent framework eventually faces the question: "Who's in charge?" If the answer is "the agents decide collectively," the human has lost control. King Agent Swarm makes the answer explicit and non-negotiable.

**Alternative considered**: Democratic voting among agents. Rejected — agents have no skin in the game and can outvote the human.

---

## Article II: Memory Isolation

**Rule**: Agents MUST NOT read each other's private memory. Shared layer is for coordination only.

**Why**: Without this rule, agent A's context (which may include incorrect assumptions, abandoned approaches, or personal notes) leaks into agent B's responses. This is the #1 cause of "my agents seem confused" complaints.

**Alternative considered**: Fully shared memory (like RuFlo). Rejected — it optimizes for convenience but destroys隔离. The whole point of multiple agents is that they bring different perspectives.

---

## Article III: Prime Minister Rotation

**Rule**: PM role rotates on King's command. No cooldown. Old PM hands over `handover_state`.

**Why**: Different agents have different strengths. A coding task may benefit from Cursor as PM; a writing task may benefit from Claude as PM. Fixed PM = suboptimal task assignment.

**Alternative considered**: Election among agents. Rejected — agents don't know the full context of what task is coming next; only King does.

---

## Article IV: Weighted Voting

**Rule**: PM gets 3 votes, others get 1, King gets absolute veto.

**Why**: 
- PM needs enough votes to make decisions efficiently (otherwise every decision is a discussion)
- But not so many that PM is a dictator (other agents can override with consensus)
- King's veto is the ultimate safety net

**The math**: With 3 agents (PM + 2 others), PM can win 3-2. With 4 agents, PM can win 3-3 (tie). Ties go to King. This is intentional.

---

## Article V: Anti-Drift Checkpoint

**Rule**: Every 5 steps on long tasks, re-align with original goal.

**Why**: LLM agents drift. They start building what they think you want, not what you asked for. Catching this every 5 steps keeps the task on track without micromanaging.

**Why 5 steps, not 3 or 10?**: 
- 3 = too frequent, wastes tokens on checking
- 10 = too late, agent has already built the wrong thing
- 5 = empirical sweet spot (needs validation in production)

---

## Article VI: No Self-Promotion

**Rule**: No agent may modify `current_coordinator` in `coordinator.json` on its own.

**Why**: An agent that decides "I should be PM" creates an unauthorized power grab. Only King can appoint PM. Period.

---

## Article VII: Handover State Completeness

**Rule**: `handover_state` MUST include active projects, pending decisions, and context summary.

**Why**: If the handover is incomplete, the new PM starts blind. The entire point of rotation is continuity — if continuity breaks, rotation is worse than no rotation.

---

## Article VIII: Platform Agnosticism

**Rule**: The protocol is Markdown + JSON. No platform-specific code.

**Why**: Today you use Claude Code + Cursor. Tomorrow you might add Kimi or a custom agent. If the protocol is tied to one platform, you have to rebuild everything when you switch.

---

## Article IX: Zero Telemetry

**Rule**: This protocol collects nothing, phones home nowhere.

**Why**: Your agent conversations are private. The coordination protocol must not become a surveillance vector. Everything stays in your local files.
