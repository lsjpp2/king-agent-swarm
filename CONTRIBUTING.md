# Contributing to King Agent Swarm

Thank you for your interest! This project is a coordination protocol for multi-AI-agent clusters, and we welcome improvements of all kinds.

---

## Ways to Contribute

- **Bug reports**: Something in the protocol doesn't work as described? Open an Issue.
- **Design critique**: The constitutional articles are opinionated. Disagree with one? Open a Discussion.
- **Platform adapters**: Have an agent platform not listed in `adapters/`? Submit one.
- **Real-world validation**: Have you actually run this with 3+ agents? We need battle reports.
- **Documentation**: `docs/` can always be clearer.

---

## Architecture Philosophy

Before contributing, understand the design philosophy:

1. **Convention, not code** — this is a *protocol* (Markdown + JSON), not a Python/TypeScript library. Keep it that way.
2. **Platform agnostic** — no adapter should assume a specific OS or agent vendor.
3. **Human sovereignty is non-negotiable** — Article I of the constitution is not up for debate.
4. **Memory isolation is a hard requirement** — if a change weakens isolation, it will be rejected.

---

## Pull Request Guidelines

1. **Fork** the repo
2. **Create a branch** with a descriptive name: `fix/rotation-handover`, `docs/add-windsurf-adapter`, etc.
3. **Write a clear PR description**: what changed, why, and how to test it.
4. **Update docs** if your change affects user-facing behavior.
5. **Test the templates**: if you change `templates/`, make sure `init.sh` / `init.ps1` still generate valid output.

---

## Issue Guidelines

**Bug report template**:
```
- King Agent Swarm version: (v1)
- Agents used: (e.g. Claude Code + Cursor)
- What I expected:
- What happened:
- Steps to reproduce:
```

**Design discussion template**:
```
- Article / section: (e.g. Article VII · Conflict Resolution)
- Current text:
- Proposed change:
- Rationale:
```

---

## Code of Conduct

- Be respectful. Disagree with ideas, not people.
- King Agent Swarm is a serious project but we don't take ourselves too seriously.
- If you're rude in an Issue/PR, we'll ask you to re-phrase. Repeat offenders get blocked.

---

## License

By contributing, you agree that your contribution will be licensed under MIT (same as the project).

---

## Questions?

Open a [GitHub Discussion]((https://github.com/YOUR_USER/king-agent-swarm/discussions) or reach out via [Issue]((https://github.com/YOUR_USER/king-agent-swarm/issues).
