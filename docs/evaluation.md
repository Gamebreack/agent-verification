# Behavioral Evaluation

The evaluation corpus tests decisions, not prose. Each case contains an authoritative task, a baseline snapshot, a candidate change, and semantic expectations for the verdict, panel, findings, and evidence gaps.

## Validate the package

```bash
python3 scripts/eval_harness.py validate
```

This checks skill resources (including that no stale reference files remain), manifests, reproducible candidate diffs, and the fixture test expectations. Passing fixture tests are deliberately insufficient: most defective candidates have green tests. **This command proves the harness and fixtures are structurally consistent. It does not prove the skill behaves correctly — that requires a model host.**

## Run a behavioral case

```bash
tmpdir="$(mktemp -d)"
python3 scripts/eval_harness.py prepare acceptance-omission "$tmpdir/repo"
```

The command creates a real Git working tree and prints a clean-context invocation prompt (including the `--contract` path). Give that prompt to a host with the `verify` skill installed. Save its JSON output, then score it against the same repository directory:

```bash
python3 scripts/eval_harness.py check acceptance-omission report.json "$tmpdir/repo"
```

`check` independently re-materializes the case's own base and candidate snapshots into a fresh scratch directory, computes a content digest of that reference tree, and compares it against a digest of `$tmpdir/repo`. It never trusts anything stored inside the checked repository itself (for example a `.verify-eval/digest` file), since a verifier with write access could edit or delete such a file to hide a mutation. A digest mismatch — including an untracked extra file — fails immediately with a clear "source changed" error; a report cannot claim `source_unchanged: true` over a repository that was actually mutated. `check` then also requires `report.source_unchanged` to be `true` and scores the report's semantic properties:

- correct verdict;
- justified reviewer selection and panel bound;
- expected requirement or invariant linkage;
- concrete evidence paths and defect concepts;
- correct handling of missing versus unavailable evidence;
- per-criterion results, when the case declares `expected.criteria`.

## Assurance boundary

Structural validation is deterministic and covers all 12 fixtures without a model. Behavioral evaluation requires a model host because the artifact being tested is an Agent Skill. Results must record whether reviewers actually received independent contexts; a report created without subagents must say `degraded independence`.

Record the host/model/version with retained evaluation reports so regressions can be compared honestly. The latest retained run is [`evals/runs/2026-09-28-claude-code.json`](../evals/runs/2026-09-28-claude-code.json) (skill v0.4.0, 12 cases, host Claude Code; per-case reports alongside it under `evals/runs/2026-09-28-claude-code/`). The prior run, [`evals/runs/2026-09-04-chatgpt-work.json`](../evals/runs/2026-09-04-chatgpt-work.json) (skill v0.1.0, 9 cases, host ChatGPT Work), is kept as history.

The 2026-09-28 run matched 10 of 12 expected verdicts with zero false negatives. Both mismatches were over-strict: `v0.2-retry-idempotency` and `v0.2-multi-trigger-bounded` returned `PASS WITH NOTES` where `PASS` was expected, each on OPTIONAL test-strength findings against otherwise-correct code. The multi-trigger case also surfaced a lead adjudication error — a BLOCKER validated on four-reviewer agreement was later withdrawn because the claimed disclosure was a caller-supplied argument, not internal state; the corrected report is retained alongside the original and still checks `FAIL` (over-strict) against the expected `PASS`. After the adjudication-policy fix (item 03), a 5-case rerun of the three mismatched cases plus two defect cases matched 5/5 — see [`evals/runs/2026-09-28-claude-code-rerun.json`](../evals/runs/2026-09-28-claude-code-rerun.json).
