## What and why

<!-- What changes, and the problem it solves. Link the issue if there is one. -->

## Hosts tested in

<!-- Host and version (Claude Code, OpenCode, Antigravity, ...), or "docs only". -->

## Checklist

- [ ] Follows the rules in AGENTS.md
- [ ] `CHANGELOG.md` entry under `[Unreleased]`, or not user-facing
- [ ] `flow-map.md` updated if the flow changed
- [ ] `python3 scripts/eval_harness.py validate` and `python3 -m unittest discover -s tests` pass
- [ ] Behavioral run recorded under `evals/runs/` if verdict behavior changed
