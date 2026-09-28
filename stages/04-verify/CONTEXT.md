# Stage 04 — verify

Independent check in fresh context.

## Inputs
| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| Acceptance criteria | `../../docs/items/<id>.md` | Outcome + Scope | What must hold |
| Changed files | working tree (uncommitted changes) | Full diff | The result |

## Process
1. A fresh verifier (never the author) checks each criterion: PASS/FAIL
   with exact commands and output.
2. Ordinary items: verifier. Significant / cross-cutting / risky items:
   reviewer plus verifier; pre-release: an independent panel via the repo's own
   `verify` skill — `verify panel --contract docs/items/<id>.md` (or `release`);
   its per-criterion table is the verdict.
3. A mechanical-tier worker logs the verdict and sets the index row to
   review.
4. Verdict mapping: `PASS` / `PASS WITH NOTES` → row to `review`; `FIX REQUIRED`
   → back to stage 03 with validated findings; `INCONCLUSIVE` → back to stage 02
   to resolve missing intent or evidence; OPTIONAL findings may go back to stage
   03 at operator's discretion.

## Outputs
| Artifact | Location | Format |
|---|---|---|
| Verdict | item file log | per-criterion PASS/FAIL + overall |
| Row status | docs/backlog.md | review |

## Checkpoint
Operator reads the verdict and verdict mapping; corrective routing applies
(FIX REQUIRED, INCONCLUSIVE, or OPTIONAL findings may route back to stages 02/03).

## Audit
Verification never edits; any fix routes back through stage 03 as delegated
work, never as a "quick fix".
