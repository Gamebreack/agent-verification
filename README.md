# Agent Verification Harness

An evidence-gated software verification skill for agent-produced changes.

It derives a Verification Contract from the original task, selects a small risk-appropriate panel of clean-context reviewers, and adjudicates their claims before returning a ship verdict. Passing tests and reviewer agreement are treated as evidence to inspect, not proof.

## Status

**v0.4.0.**

The package has a deterministic structural validation harness and 12 behavioral fixtures covering acceptance omissions, bogus tests, boundary errors, idempotency, contract regressions, tenant authorization, speculative findings, unavailable evidence, a correct low-risk change, and bounded multi-trigger panels. Structural validation passes; behavioral evaluation of this version has been run once, on Claude Code (see [Evidence](#evidence)).

## Core properties

- risk-based reviewer selection from a fixed five-role panel;
- independent, depth-one specialist reviews;
- acceptance checked against original intent, including an optional `--contract` file;
- semantic test-adequacy analysis as part of the `tests` role;
- evidence-gated severity and adjudication of every claim;
- read-only verification with no autonomous fixing.

## Invocation

```text
verify [quick|panel|release] [target] [--contract <path>] [--report markdown|json]
```

- Mode: default `panel`.
- Target: default is the working-tree diff; also accepts a commit, range, branch, pull request, or explicit file set.
- `--contract <path>`: a markdown or text file holding the task statement, acceptance criteria, and non-goals. When supplied, it is the authoritative source of truth.
- Report: default `markdown`; `json` returns the machine-readable report only.

The canonical skill lives at [`.agents/skills/verify`](.agents/skills/verify).

## Reviewer roles

`acceptance`, `tests`, `regression`, `invariants`, `security`. See [Architecture](docs/architecture.md).

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

## Validate

```bash
python3 scripts/eval_harness.py validate
python3 -m unittest discover -s tests -v
python3 scripts/eval_harness.py prepare <case_id> <destination>
python3 scripts/eval_harness.py check <case_id> <report.json> <destination>
```

See [Behavioral evaluation](docs/evaluation.md) to materialize and score cases against a model host.

## Evidence

- **Structural validation** (`scripts/eval_harness.py validate`) is deterministic: it checks the skill package's required files, validates all 12 fixture manifests, materializes each as a real Git repository, and confirms the candidate's own tests pass without mutating the fixture source. It does not require a model.
- **Behavioral evaluation** requires a model host, because the artifact under test is an Agent Skill that must be invoked by an agent. The latest retained behavioral run is **v0.4.0 (Claude Code, 2026-09-28): 10/12 matched, 0 false negatives, 2 over-strict verdicts** — see [`evals/runs/2026-09-28-claude-code.json`](evals/runs/2026-09-28-claude-code.json) (per-case reports alongside it). The prior run, [`evals/runs/2026-09-04-chatgpt-work.json`](evals/runs/2026-09-04-chatgpt-work.json) (skill v0.1.0, 9 cases, host ChatGPT Work), is kept as history. A 5-case rerun after the adjudication-policy fix matched 5/5 ([`evals/runs/2026-09-28-claude-code-rerun.json`](evals/runs/2026-09-28-claude-code-rerun.json)).

## Discovery

The skill is a portable Agent Skill package with no host-specific runtime. Hosts discover it from one of these locations:

| Host | Discovery path | Notes |
|---|---|---|
| Canonical | `.agents/skills/verify` | Source of truth; every other location is a copy or symlink of this. |
| Claude Code | `.claude/skills/verify` | Symlinked to the canonical path in this repository. |
| OpenCode | `.agents/skills` + `.opencode/commands/verify.md` | The command file is a thin invocation adapter; it does not duplicate verification policy. |
| Antigravity | `.agents/skills` | Auto-registers as a slash command in interactive use. |
| Codex, Cursor | `.agents/skills` | Read directly from the canonical Agent Skills location. |

See [Installation](docs/installation.md) for user-wide symlink locations.

## Documentation

- [Architecture](docs/architecture.md)
- [Installation](docs/installation.md)
- [Behavioral evaluation](docs/evaluation.md)
- [Latest evaluation run](evals/runs/2026-09-28-claude-code.json)

## License

Released under the [MIT License](LICENSE).
