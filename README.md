# Agent Verification Harness

An evidence-gated software verification skill for agent-produced changes.

It derives a Verification Contract from the original task, selects a small risk-appropriate panel of clean-context reviewers, and adjudicates their claims before returning a ship verdict. Passing tests and reviewer agreement are treated as evidence to inspect, not proof.

The package has a deterministic structural validation harness and behavioral fixtures covering acceptance omissions, bogus tests, boundary errors, idempotency, contract regressions, tenant authorization, speculative findings, unavailable evidence, a correct low-risk change, and bounded multi-trigger panels (see [Evidence](#evidence)).

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
- Target: default is branch-aware: the branch against its merge base plus the working tree when the branch has commits not on its base; otherwise the working-tree diff (or the branch against its merge base when the tree is clean). Also accepts a commit, range, branch, explicit file set, a plan or design document (an artifact target), or a pull request (only when named). Base resolution is read-only; see [verification-contract.md](.agents/skills/verify/references/verification-contract.md#base-resolution).
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

- **Structural validation** (`scripts/eval_harness.py validate`) is deterministic: it checks the skill package's required files, validates every fixture manifest, materializes each as a real Git repository, and confirms the candidate's own tests pass without mutating the fixture source. It does not require a model.
- **Behavioral evaluation** requires a model host, because the artifact under test is an Agent Skill that must be invoked by an agent. Results are recorded per run; see the latest run and its analysis in [Behavioral evaluation](docs/evaluation.md#assurance-boundary) and the retained records under [`evals/runs/`](evals/runs/).

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
- [Flow map](flow-map.md): the runtime flow as diagrams
- [Installation](docs/installation.md)
- [Behavioral evaluation](docs/evaluation.md)
- Latest evaluation run (2026-11-11): [OpenCode](evals/runs/2026-11-11-opencode.json), [Claude Code](evals/runs/2026-11-11-claude-code.json); see [assurance boundary](docs/evaluation.md#assurance-boundary)

## License

Released under the [MIT License](LICENSE).
