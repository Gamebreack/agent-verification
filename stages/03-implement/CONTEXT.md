# Stage 03 — implement

Delegated edits by specialist workers.

## Inputs
| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| Approved proposal | `../../docs/items/<id>.md` | log (latest proposal) | The plan |
| Working files | paths the proposal names | As named | Edit targets |

## Process
1. The orchestrator delegates each unit to the tier the work needs:
   deterministic edits → mechanical; ordinary work → implementer; genuinely
   difficult → hard-implementer. At most 3 concurrent workers; group tiny
   edits by file ownership, never one worker per edit.
2. Workers report files changed, verification run, failures. On failure the
   orchestrator resumes the same task with feedback; escalation only after
   a retry fails.
3. A mechanical-tier worker logs what happened (not what was intended).

## Outputs
| Artifact | Location | Format |
|---|---|---|
| Edits | working tree | smallest complete change |
| Worker reports | item file log | dated entries |

## Audit
This stage produces working-tree edits only; shipping happens in stage 05.
Worker self-verification is a claim, not evidence — stage 04 checks it.
