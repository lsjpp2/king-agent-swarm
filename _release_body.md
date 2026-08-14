# 👑 KAF — King-Agent Framework v5.3

> **The governance layer for multi-agent swarms.**
> Give any collection of AI agents a constitution, runtime guardrails, and a clear chain of command — without locking you into one vendor or one "owner."

If you run **more than one** AI agent (Claude Code, Cursor, OpenCode, Codex, Qwen, Kimi, WorkBuddy…), they each make decisions independently with **no shared rules** about what they may touch. KAF answers: *how do you govern agents so they stay safe, accountable, and aligned* — sitting **under** any orchestrator you already use. It is not an orchestrator; it is the **constitution + runtime guardrail** layer.

## What's new in v5.3 (vs v5.0 / v5.1 / v5.2)

Two foundational additions:

### A. Governance Layer (NEW)
- `kaf/governance.py`: every write action passes `Governance.evaluate()` → `kill-switch → agent HMAC attestation → 520 guard → policy`.
- **Tamper-evident audit chain** — each decision is hash-linked (`governance/audit_chain.log`); any tampering is detectable.
- Before v5.3 there was only `kaf check` self-test with no persistent tamper record. Now every operation leaves on-chain evidence — closing the "claims ≠ implementation" gap.

### B. Dynamic King — Deployer = King (NEW)
- The framework ships with **no hardcoded owner**. `resolve_king()` resolves in order: `KAF_KING env > kaf_config.json["king"] > local author env > current OS user`.
- You deploy it → you're King. Someone forks and deploys → *they* are King. Meant to be **copied, not adopted wholesale**.

## Capability comparison

| Capability | v5.0 | v5.1 | v5.2 | **v5.3** |
|:--|:--:|:--:|:--:|:--:|
| Constitution-as-Code (JSON) | ✅ | ✅ | ✅ | ✅ |
| 520 Runtime Guard (Law 8/9/10 block at runtime) | ✅ | ✅ | ✅ | ✅ |
| Memory Integrity (SHA-256 fingerprint) | ✅ | ✅ | ✅ | ✅ |
| Platform Adapters (~5 lines) | — | ✅ | ✅ | ✅ |
| Economics Router (real pricing + calibrate) | — | ✅ | ✅ | ✅ |
| Multi-view Review (BLOCK→write-back loop) | — | ✅ | ✅ | ✅ |
| Shared Ledger (SQLite) | — | ✅ | ✅ | ✅ |
| **Governance Layer (kill-switch/attestation/audit)** | — | — | — | **✅** |
| **Dynamic King (Deployer=King, no hardcoded owner)** | — | — | — | **✅** |

## Why teams adopt KAF
- **Constitution-as-Code** — governance is a parseable JSON file you can diff, review, and CI-test.
- **Runtime guardrails (520 Rule)** — destructive ops blocked at execution time, with a real audit log.
- **Memory integrity** — private memory isolated; shared memory fingerprinted.
- **Platform adapters** — plug in any agent platform in ~5 lines. No vendor lock-in.
- **Tamper-evident audit chain** — prove what happened.
- **Whoever deploys it is King** — no hardcoded owner.

## Quick start

```bash
git clone https://github.com/lsjpp2/king-agent-swarm.git
cd king-agent-swarm/kaf
python kaf.py init      # generate constitution.json + register memory fingerprints
python kaf.py check     # 520 self-check → ✅ PASS
python kaf.py status    # who's the current Prime Minister (you are King by default)
```

## Diagrams (all in `diagrams/`)
- **Architecture (v5.3)** — six layers, governance on top, dynamic King: `diagrams/04-architecture.svg`
- **Governance flow** — `diagrams/05-governance-flow.svg`
- **King resolution** — `diagrams/08-king-resolution.svg`
- Plus power-structure / memory-isolation / rotation / audit-chain / shared-state, and an offline `diagrams/index.html` tour.

## For remote adopters (copy & own)
1. `git clone` → `cd kaf` → `python kaf.py init`.
2. Your OS user becomes King automatically. Override with `KAF_KING=YourName` or `kaf_config.json {"king":"YourName"}`.
3. Add a platform adapter in ~5 lines (`adapters/_template.py`).
4. PRs welcome — especially new adapters and governance policies.

## Verification
- Local tip `80975a1` pushed to `origin/master`; v5.3 tag points to `f09f477`; docs refreshed in `80975a1` (SHA verified consistent with remote).
- `governance_selftest.py` PASS=8; `kaf govern` DENY/ALLOW verified; `kaf audit-tail` integrity valid.
- Shared archive: `${KAF_SHARED_DIR}/国王技能KAF/v5.3/` (git archive snapshot).

MIT licensed. Fork it, deploy it, make it yours.
