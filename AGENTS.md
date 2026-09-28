# agent-verification — repo conventions

Layer 0 of this repo's ICM structure; read CONTEXT.md next for routing.

## How work happens here

- **Hybrid ICM** (locked 2026-09-27): numbered stages under stages/ organize
  each work item; specialist agents execute the stage work. docs/backlog.md
  decides WHAT work exists; stages/ decide HOW an item flows. One home per
  fact — never duplicate a rule into a second file.
- **Backlog** owns the work index: docs/backlog.md is the only live index;
  item files under docs/items/ hold the detail. The done ledger
  (docs/done.md) is written by the operator only.
- **Tier discipline:** read-only tiers inspect, mechanical/implementer tiers
  edit, fresh verifier/reviewer tiers check. The primary orchestrator never
  writes files.

## Hard rules

- No commits, pushes, or remote changes without explicit operator
  authorization. Workers never push (permission-denied by design).
- Keep every CONTEXT.md under 80 lines; reference docs under 200.
- Before any item reaches stage 05: `python3 scripts/eval_harness.py validate`
  and `python3 -m unittest discover -s tests` must pass.
- The skill under `.agents/skills/verify/` stays host-agnostic: no host,
  agent-type or model names. One home per fact.
- Secrets, personal MCP endpoints, credentials and machine-specific paths
  never enter this repo (portability boundary).
