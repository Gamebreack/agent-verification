# Where work goes

A host-agnostic Agent Skill (`verify`) that independently verifies an implemented change against its original requirements, plus the fixture harness that evaluates it.

| You want to... | Go to |
|---|---|
| Read project conventions | AGENTS.md |
| Start or resume a work item | docs/backlog.md, then the item's file |
| Know how an item flows | stages/ (below) |
| Understand the skill | docs/ (architecture, installation, evaluation) |

## Stage routing

| Stage | Job | Executed by | Operator checkpoint |
|---|---|---|---|
| stages/01-intake/ | request → work item | orchestrator + mechanical worker | scope confirmed |
| stages/02-design/ | inspect + proposal | explore / scout + orchestrator + mechanical worker | plan approved |
| stages/03-implement/ | delegated edits | mechanical / implementer / hard-implementer (delegated by orchestrator) | — |
| stages/04-verify/ | independent check | verifier / reviewer + mechanical worker | verdict read |
| stages/05-release/ | record + ship | orchestrator + worker | release authorized |

Handoff state between stages: the item's log, the index row's status, and
the working tree. Nothing else carries state.

## Surfaces touched by work here

| Surface | Path | Why |
|---|---|---|
| Skill implementation | `.agents/skills/verify/` | SKILL.md + references/ |
| Evaluation harness | `scripts/eval_harness.py`, `tests/` | Harness runs + unit tests |
| Behavioral fixtures | `evals/cases/`, `evals/runs/` | Test cases + retained runs |
| Documentation | `docs/` | Architecture, installation, evaluation |
| Host discovery | `.opencode/commands/verify.md`, `.claude/skills/verify` | Symlink |

## Boundaries — inherited by every work item

**Out of scope:** a custom agent runtime; host-specific agent/model bindings inside the skill; autonomous fixing; plugin/marketplace packaging; installing tooling into target repos.

**Never enters this workspace:** secrets, credentials, personal MCP endpoints, machine-specific paths; no host/model names inside `.agents/skills/verify/`; no vendor-named files under `.agents/skills/verify/`.
