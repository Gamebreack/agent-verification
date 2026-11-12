# agent-verification — repo rules

This repo holds the `verify` Agent Skill (an evidence-gated verification panel for agent-produced changes) and its evaluation harness.

## Hard rules

- No commits, pushes or remote changes without explicit operator authorization. Workers never push.
- The skill under `.agents/skills/verify/` stays host-agnostic: no host, agent-type or model names.
- One home per fact: never duplicate a rule or description into a second file; link instead.
- Reference docs stay under 200 lines.
- Secrets, credentials, personal endpoints and machine-specific paths never enter the repo.

## Required checks

These must pass before merge and before release:

```bash
python3 scripts/eval_harness.py validate
python3 -m unittest discover -s tests
```

## Releases

See [CONTRIBUTING.md](CONTRIBUTING.md) for the versioning policy and the release procedure.
