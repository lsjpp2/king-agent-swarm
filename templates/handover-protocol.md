# PM Rotation Handover Protocol v1

> Trigger: "X is Prime Minister from now on."

---

## Three-Step Rotation

### Step 1: King's Command

King (${KING_NAME}) issues command verbally or in text:

> "From now on, [Agent Name] is Prime Minister."

Effective immediately. No cooldown.

---

### Step 2: Old PM Hands Over

Old PM (current coordinator) executes:

1. Write current work status to `${CLUSTER_ROOT}/progress/YYYY-MM-DD.md`
2. Package active projects / pending decisions / context summary into `handover_state` in `coordinator.json`
3. Update `coordinator.json`:
   - `previous_coordinator` = old PM name
   - `current_coordinator` = new PM name
   - `since` = current timestamp
   - Append to `rotation_history`
4. Notify King: "[New PM Name] has been handed over to."

---

### Step 3: New PM Takes Over

New PM (incoming coordinator) executes:

1. Read `coordinator.json` — confirm `current_coordinator` is self
2. Read `handover_state` — get context
3. Read `${CLUSTER_ROOT}/progress/` — get today's progress
4. Confirm to King: "[New PM Name] has taken over as Prime Minister. Beginning duty."
5. Notify other agents: "Prime Minister is now [New PM Name]."

---

## Handover Content Checklist

`handover_state` MUST contain:

```json
{
  "active_projects": ["Project A", "Project B"],
  "pending_decisions": ["Decision X"],
  "last_handover_dump": "Context summary..."
}
```

---

## Taboos

- **NO** agent may modify `current_coordinator` in `coordinator.json` on its own.
- **NO** loss of `handover_state` content during handover.
- **NO** new PM begins duty without confirming `coordinator.json`.

---
