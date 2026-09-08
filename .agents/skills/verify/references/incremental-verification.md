# Incremental Verification

When prior state exists for an assurance-boundary TARGET, the skill may recollect only the evidence invalidated by the DELTA. DELTA is the file-level change since the previously verified baseline, intersected with TARGET.in_scope.

## Gate

Incremental re-verification is allowed only when:

1. `target.kind` ∈ `{feature, subsystem, workflow, artifact}`.
2. A prior state file is reachable at `$VERIFY_STATE_PATH` (or default location) and passes the validation rules in [state-persistence.md](state-persistence.md).
3. `target_identity` in the current contract matches the one recorded in state.
4. The Verification Contract enumerates which acceptance criteria, invariants, and preserved behaviors still apply.

If any condition fails, the skill refuses incremental mode and either performs a fresh full verification or returns `INCONCLUSIVE` (when full verification cannot anchor safely).

## Delta computation

- File-level delta: `git diff <state.baseline.sha>..HEAD -- <state.target_identity.in_scope>`.
- A surface is "touched" if at least one file in `in_scope` contains a diff, OR if a file not in `in_scope` was moved/renamed into `in_scope`.
- Detect scope-boundary drift: if `in_scope` paths no longer resolve or the resolved set has changed (paths added/removed/renamed outside the user's intent), treat it as identity drift.

## Reviewer invalidation map

A reviewer is **invalidated** (must re-run) only when its specific trigger fires from the delta. If not invalidated, the skill reuses the prior verdict and runs only an evidence-paths existence check.

| Reviewer | Invalidate iff |
|---|---|
| Acceptance | any in-scope surface changed that touches an acceptance criterion |
| Test adequacy | any in-scope test changed, or the test command itself changed |
| Regression | behavior code for any `preserved_behaviors` entry moved or changed |
| Boundary/invariants | any invariant surface touched |
| Security | auth, authz, validation, secrets, or sensitive-data surface touched |
| Contract boundaries | API, schema, event, file, protocol, or service-boundary surface touched |
| Failure/observability | async, queue, retry, external dependency, or operational surface touched |
| Adversarial | material implementation claim changed, OR high uncertainty from delta |
| Mutation/sabotage | critical logic changed OR shallow/over-mocked test suite detected on touched code |
| Critical journey | user-facing critical path affected (rare from a delta; requires integration surface change) |
| Simplification | new code added that may be redundant (run only after correctness reviewers) |

## Empty delta

When the diff is empty AND the identity matches:

- Reuse the prior verdict verbatim.
- Run only an `evidence_paths` existence check (each recorded path must still exist).
- Do not redispatch reviewers.
- Record in `checks_executed`: `evidence_paths existence check`.

## Identity drift

Identity has drifted when:

- `state.target_identity` no longer matches the current contract's `target_identity` (different description, different `in_scope`, missing `acceptance_criteria`, different anchor).
- Either anchor.sha or state.baseline.sha is no longer reachable in git history.
- Any path in `state.target_identity.in_scope` no longer resolves.

When drift is detected, the skill refuses incremental mode and:

- Performs a fresh full verification, OR
- Returns `INCONCLUSIVE` if a full verification cannot anchor safely (e.g., the feature has been refactored beyond recognition).

Never silently reuse state across identity drift. Never guess.

## What incremental does NOT do

- It does not weaken the Verification Contract. Required evidence remains required.
- It does not change reviewer selection rules. Reviewers are still chosen by surface trigger / risk band.
- It does not relax depth-1 or read-only constraints.
- It does not run autonomously or modify the target.
- It does not merge or summarize reviewer output across runs. Each run produces its own JSON report.

## Report shape

When incremental mode is used, the JSON report must include:

- `incremental: true`
- `delta: {from_sha, to_sha, files_changed: [...]}` (where determinable)
- `invalidation: {<reviewer>: "REUSED | RE_RAN", ...}` for every reviewer considered
- For reused reviewers, a single checks_executed entry with command_or_inspection: "evidence_paths existence check" and result: "passed".

If identity drift is detected, the report must include `evidence_gaps` with kind `UNAVAILABLE` and explanation referencing the drift.
