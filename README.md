# Agent Verification Harness

An evidence-gated software verification skill for agent-produced changes.

It derives a Verification Contract from the original task, selects a small risk-appropriate panel of clean-context reviewers, and adjudicates their claims before returning a ship verdict. Passing tests and reviewer agreement are treated as evidence to inspect, not proof.

## Status

**Release — v0.3.0.**

The package has a deterministic validation harness and 17 behavioral fixtures covering acceptance omissions, bogus tests, boundary errors, idempotency, contract regressions, tenant authorization, speculative findings, unavailable evidence, a correct low-risk change, and v0.3 incremental re-verification and assurance boundaries. All 17 semantic evaluations pass against the test harness.

Skill discovery verified for Cursor, Codex, OpenCode, and Antigravity (`agy`). End-to-end `/verify` runs on seeded fixtures remain before the portable release gate. ChatGPT web/mobile distribution also requires plugin packaging.

## Core properties

- risk-based reviewer selection;
- independent, depth-one specialist reviews;
- acceptance checked against original intent;
- semantic test-adequacy and mutation/sabotage analysis;
- evidence-gated severity and reviewer-of-reviewers adjudication;
- assurance-boundary targets (feature, subsystem, workflow, artifact) with target identity contracts;
- opt-in incremental re-verification using target-local state persistence and delta invalidation;
- scope-preservation guards against artificial assurance narrowing;
- read-only verification with no autonomous fixing;
- portable Agent Skills package with thin host adapters.

## Invocation

- Cursor: `/verify [mode] [target] [--report markdown|json]`
- ChatGPT Work: available after future plugin packaging
- Codex CLI/IDE: `$verify [mode] [target] [--report markdown|json]`
- OpenCode: `/verify [mode] [target] [--report markdown|json]`
- Antigravity (`agy`): `/verify [mode] [target] [--report markdown|json]` in interactive TUI (workspace skill auto-registers as slash command); in `-p` print mode invoke contextually (e.g., "use the verify skill on this diff")

Modes: `auto`, `quick`, `tests`, `feature`, `full`, and `release`.

Targets:
- Working-tree diff (default), commit, range, branch, PR, or explicit file set;
- Assurance-boundary targets: `feature:<name>`, `subsystem:<name>`, `workflow:<name>`, `artifact:<name>` (requiring `target.identity` in the Verification Contract).

The canonical skill lives at [`.agents/skills/verify`](.agents/skills/verify). OpenCode's command file is only an invocation adapter; verification policy remains in the shared skill.

## Validate

```bash
python3 scripts/eval_harness.py validate
python3 -m unittest discover -s tests -v
```

See [Behavioral evaluation](docs/evaluation.md) to materialize and score cases against a model host.

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
- [Installation](docs/installation.md)
- [Behavioral evaluation](docs/evaluation.md)
- [Latest evaluation run](evals/runs/2026-09-04-chatgpt-work.json)

## Distribution

v1 ships as a standalone Agent Skill at `.agents/skills/verify`, with a thin
OpenCode invocation adapter at `.opencode/commands/verify.md`. The Skill is
discovered by Codex, Cursor, OpenCode, and Antigravity from this layout, and is symlinked
or copied to each host's user skill location for global use.

Marketplace packaging (ChatGPT web/mobile, plugin manifests, hosted stores)
is intentionally deferred until behavioral fixtures pass on at least two
hosts and the cross-host portability gate is satisfied.

## License

Released under the [MIT License](LICENSE).
