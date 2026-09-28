# Stage 05 — release

Ledger, close-out, ship.

## Inputs
| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| Verdict | `../../docs/items/<id>.md` | log (latest) | Release evidence |
| Ledger | `docs/done.md` | Table | Where the line goes |

## Process
1. The operator writes the ledger line (ID, date, one sentence). The
   operator's line — never agent-written.
2. Close-out in one commit, with operator authorization: the orchestrator
   delegates the edits to a worker — delete the index row, delete the item
   file (it stays reachable in history), update the as-built doc if the
   item changed what exists.
3. The operator ships (push is operator-only).

## Outputs
| Artifact | Location | Format |
|---|---|---|
| Ledger line | docs/done.md | operator-written |
| Close-out commit | version control | row + item file deleted |

## Checkpoint
Operator authorizes the commit and runs the ship step. Nothing ships
without both.

## Audit
The ledger line exists before the close-out commit. The index row and the
item file are deleted in the same commit. The ship step was run by the
operator.
