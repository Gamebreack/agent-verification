# Contributing

## How to propose a change

1. For anything beyond a small fix, open an issue first and describe the problem.
2. Then open a pull request against `main`. Every change lands through a pull request.

## Rules a change must keep

Every change keeps the rules in [AGENTS.md](AGENTS.md). They are not repeated here.

## Testing a change

Both checks must pass before merge:

```bash
python3 scripts/eval_harness.py validate
python3 -m unittest discover -s tests
```

If a change alters verdict behavior (panel selection, adjudication, report), also run the affected fixtures on at least one host and record the run under `evals/runs/` (see [docs/evaluation.md](docs/evaluation.md)).

## Versioning

Versions follow SemVer, applied to the skill's behavior:

- **Patch:** wording and fixes that do not change verdicts or reports.
- **Minor:** new or changed behavior, verdict rules, modes, roles or report fields.
- **Major:** a breaking change to the invocation or the report format.

## Releasing

1. In a pull request, move the `[Unreleased]` entries in `CHANGELOG.md` under `## [X.Y.Z] - YYYY-MM-DD` and update the compare links.
2. Run pre-release verification on that pull request while it is up to date with `main`: a fresh verifier run plus an independent review panel (for example the `verify` skill). Merge only with no open BLOCKER or SHOULD-FIX finding. If anything else lands on the pull request or on `main` afterwards, run it again.
3. Only with the operator's approval, which covers this step and the next: after the pull request merges, create the annotated tag `vX.Y.Z` on the merge commit and push it.
4. Create the GitHub release with that version's changelog section as its notes: `gh release create vX.Y.Z --verify-tag --title "vX.Y.Z — <summary>" --notes-file <section>`. `--verify-tag` stops the release if the tag from step 3 is not on the remote.
