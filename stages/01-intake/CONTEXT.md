# Stage 01 — intake

Turn a request into a work item.

## Inputs
| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| Request | operator message / linked spec | Full | The work requested |
| Work index | `../../docs/backlog.md` | Index | Next ID + live rows |

## Process
1. The orchestrator (primary session) runs the intake interview — the
   operator answers — until every answer names something checkable.
2. The orchestrator restates the scope as what will NOT be touched; the
   operator confirms.
3. A mechanical-tier worker creates the index row (next ID) and, when the
   item needs a file, the item file.
4. The mechanical worker logs the opening in the item's log.

## Outputs
| Artifact | Location | Format |
|---|---|---|
| Index row | `docs/backlog.md` | in-progress |
| Item file | `docs/items/<id>.md` | when needed |

## Checkpoint
Operator confirms the scope restatement before the row exists. If corrected
twice and still wrong: stop, write nothing.

## Audit
The row ID is one past the highest in the index or the done ledger; no ID is
reused; the done ledger is untouched.
