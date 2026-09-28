# Stage 02 — design

Inspect the touched surfaces and propose the change.

## Inputs
| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| Item file | `../../docs/items/<id>.md` | Outcome + Touches | What and where |
| Project files | paths named in the item's Touches | As named | Current state |
| External docs | web (scout tier) | When needed | Correct references |

## Process
1. Explore (read-only tier) maps the touched surfaces with file:line evidence.
2. The orchestrator composes the proposal: files to change, order, risks.
3. A mechanical-tier worker records the proposal in the item's log and
   rewrites the item's scope to current truth (never appending to it).

## Outputs
| Artifact | Location | Format |
|---|---|---|
| Proposal | item file log | dated entry, checkable steps |
| Scope update | item file scope | rewritten |

## Checkpoint
Operator approves the proposal before stage 03 runs. No implementation
before approval.

## Audit
Proposal names in-scope and out-of-scope paths; every step is checkable (a
file, a command, an observable behavior); no scope broadening.
