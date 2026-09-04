# Agent Verification Harness

An evidence-gated software verification skill for agent-produced changes.

It derives a Verification Contract from the original task, selects a small risk-appropriate panel of clean-context reviewers, and adjudicates their claims before returning a ship verdict. Passing tests and reviewer agreement are treated as evidence to inspect, not proof.

## Status

Architecture/specification draft. The first behavioral evaluation suite is still to be implemented.

## Core properties

- risk-based reviewer selection;
- independent, depth-one specialist reviews;
- acceptance checked against original intent;
- semantic test-adequacy and mutation/sabotage analysis;
- evidence-gated severity and reviewer-of-reviewers adjudication;
- read-only verification with no autonomous fixing;
- portable Agent Skills package with thin host adapters.

## Invocation

- Cursor: `/verify [mode] [target]`
- ChatGPT Work: select `verify` with `@`
- Codex CLI/IDE: `$verify [mode] [target]`
- OpenCode: `/verify [mode] [target]`

Modes: `auto`, `quick`, `tests`, `feature`, `full`, and `release`.

The canonical skill lives at [`.agents/skills/verify`](.agents/skills/verify). OpenCode's command file is only an invocation adapter; verification policy remains in the shared skill.

## Verdicts

- `PASS`
- `PASS WITH NOTES`
- `FIX REQUIRED`
- `INCONCLUSIVE`

`INCONCLUSIVE` is used when essential evidence cannot be collected or the source of truth is materially ambiguous. It prevents an unavailable check from being silently treated as a pass.

## Non-goals

- custom agent runtime;
- custom mutation engine or test framework;
- recursive delegation;
- autonomous fixes;
- replacement for static analyzers or CI;
- a generic list-everything code review.

## Documentation

- [Architecture](docs/architecture.md)
- [MVP backlog](docs/mvp-backlog.md)
