# Architecture

## Decision

Build one canonical Agent Skill at `.agents/skills/verify`. Keep the orchestration policy in `SKILL.md`, detailed contracts in shared references, and each reviewer mandate in its own role file.

The verification lead uses the host's native subagent capability. There is no custom runtime.

```mermaid
flowchart TD
    A["Task + resolved change"] --> B["Verification Contract"]
    B --> C["Risk and surface selection"]
    C --> D["Clean-context reviewers"]
    D --> E["Evidence-gated adjudication"]
    E --> F["PASS / NOTES / FIX / INCONCLUSIVE"]
```

## Why a single orchestrator skill

- Specialist roles are implementation details, not capabilities users need to discover independently.
- Separate role files preserve progressive disclosure and let clean-context reviewers load only their mandate.
- Permanent host-specific agent definitions would duplicate policy and drift.
- The same skill is discoverable by Codex, OpenCode, Cursor, and Antigravity from `.agents/skills`, following the Agent Skills standard.

## Execution boundaries

- Maximum delegation depth: one.
- Normal automatic panel: two to five reviewers.
- Reviewers are read-only and cannot fix or delegate.
- The verification lead adjudicates; reviewer output never directly determines the verdict.
- Existing project tools may be executed. New verification dependencies are not installed by the skill.
- Actual mutation testing runs only when already configured and only in an isolated copy/worktree. Otherwise use semantic sabotage analysis.

## Host behavior

| Host | Canonical skill | Invocation | Adapter |
|---|---|---|---|
| Cursor | `.agents/skills/verify` or installed GitHub skill | `/verify` | None |
| ChatGPT Work | plugin-bundled skill | `@verify` | Future plugin packaging |
| Codex CLI/IDE | `.agents/skills/verify` | `$verify` | None |
| OpenCode | `.agents/skills/verify` | `/verify` | `.opencode/commands/verify.md` |
| Antigravity (`agy`) | `.agents/skills/verify` | `/verify` (interactive TUI) / contextual (CLI `-p`) | None |

Host-specific files may invoke or expose the canonical skill, but must not duplicate its verification policy.

## Assurance degradation

If the host lacks subagents, the lead may run roles sequentially, but must label the report `degraded independence`. Essential unavailable evidence or materially ambiguous intent produces `INCONCLUSIVE`, not `PASS`.

## Evaluation architecture

`scripts/eval_harness.py` materializes each case as a real Git repository with a baseline commit and candidate working-tree diff. The candidate's own tests normally pass. A verifier report is scored against semantic expectations—verdict, selected roles, contract linkage, evidence paths, defect concepts, evidence gaps, and source immutability—rather than exact prose.

## Deferred decisions

- Plugin packaging and marketplace distribution.
- CI/non-interactive report format.
- Default license.
- Optional host-specific permission profiles for stronger read-only enforcement.
