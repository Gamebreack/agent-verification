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

Record the host/model/version with retained evaluation reports so regressions can be compared honestly. The latest retained run is [`evals/runs/2026-09-04-chatgpt-work.json`](../evals/runs/2026-09-04-chatgpt-work.json) (skill v0.1.0, 9 cases, host ChatGPT Work). v0.4.0 has not yet been behaviorally evaluated on any host.
