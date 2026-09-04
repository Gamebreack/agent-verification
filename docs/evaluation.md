# Behavioral Evaluation

The evaluation corpus tests decisions, not prose. Each case contains an authoritative task, a baseline snapshot, a candidate change, and semantic expectations for the verdict, panel, findings, and evidence gaps.

## Validate the package

```bash
python3 scripts/eval_harness.py validate
```

This checks skill resources, manifests, reproducible candidate diffs, and the fixture test expectations. Passing fixture tests are deliberately insufficient: most defective candidates have green tests.

## Run a behavioral case

```bash
tmpdir="$(mktemp -d)"
python3 scripts/eval_harness.py prepare acceptance-omission "$tmpdir/repo"
```

The command creates a real Git working tree and prints a clean-context invocation prompt. Give that prompt to a host with the `verify` skill installed. Save its JSON output, then score it:

```bash
python3 scripts/eval_harness.py check acceptance-omission report.json
```

The scorer checks semantic properties rather than exact wording:

- correct verdict;
- justified reviewer selection and panel bound;
- expected requirement or invariant linkage;
- concrete evidence paths and defect concepts;
- correct handling of missing versus unavailable evidence;
- confirmation that verification left source unchanged.

## Assurance boundary

Structural validation is deterministic. Behavioral evaluation requires a model host because the artifact being tested is an Agent Skill. Results must record whether reviewers actually received independent contexts. A report created without subagents may still diagnose prompt behavior, but it must say `degraded independence`.

Cross-host runs are release evidence, not a prerequisite for iterating on the MVP. Record the host/model/version with retained evaluation reports so regressions can be compared honestly.

The latest retained run summary is [`evals/runs/2026-09-04-chatgpt-work.json`](../evals/runs/2026-09-04-chatgpt-work.json).
