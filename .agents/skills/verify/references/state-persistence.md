# State Persistence

Incremental re-verification needs a stable record of the previously verified target, baseline, and evidence surface. This file defines that record. The skill itself never writes state — it emits the record in its report and a host action (e.g., `/verify save`) stores it at `$VERIFY_STATE_PATH` or the default `<target-repo>/.verify/state.json`.

## Storage

- Default location: `<target-repo>/.verify/state.json`.
- Override: set the environment variable `VERIFY_STATE_PATH` to an absolute path before invoking the skill.
- The state file lives in the **target repository**, never in the skill source. The skill never writes to the target repo on its own.
- Never auto-commit. Add `.verify/` to the target repository's `.gitignore` unless the team explicitly opts in.

## Schema

```yaml
schema_version: 1
target_kind: feature | subsystem | workflow | artifact | files
target_identity:
  description: <feature/subsystem/workflow/artifact name>
  in_scope:
    - <path, glob, or behavior anchor>
  out_of_scope:
    - <...>
  anchor:
    branch: <branch>
    sha: <baseline sha>
    range: <commit range or null>
    pr: <pull request id or null>
  acceptance_criteria:
    - R1
baseline:
  sha: <git sha at the time of verification>
  branch: <branch name>
  ts: <ISO-8601 UTC timestamp>
  verifier_version: <skill VERSION at run time>
reviewers_used:
  - acceptance
  - test-adequacy
verdict: PASS | PASS WITH NOTES | FIX REQUIRED | INCONCLUSIVE
evidence_paths:
  - <path or command that produced evidence>
preserved_behaviors_validated:
  - P1
contract_hash: <sha256 of references/verification-contract.md at run time>
reviewer_files_hashes:
  acceptance: <sha256 of references/reviewers/acceptance.md>
  test-adequacy: <sha256 of references/reviewers/test-adequacy.md>
```

## Rules

1. The skill writes only via the host's save action (`/verify save` or equivalent); it does not directly create, overwrite, or commit the state file.
2. On every run the skill re-validates the state file before relying on it:
   - every path/glob in `target_identity.in_scope` must still exist;
   - every `target_identity.acceptance_criteria` id must still appear in the current `verification-contract.md`;
   - `contract_hash` must match the current contract file's sha256;
   - every `reviewer_files_hashes.<role>` must match the current reviewer file's sha256 for that role.
3. If any check fails, the skill refuses to use the prior state. It either returns `INCONCLUSIVE` (when full verification cannot anchor safely) or falls back to a fresh full verification.
4. The state file is target-local and target-scoped. Two different TARGETs in the same repository must use distinct `target_kind` + `target_identity.description` keys.
5. Never share state across hosts, branches, or worktrees.

## What is not in state

- Reviewer prose, intermediate reasoning, or non-validated claims.
- Implementation details that were not part of the Verification Contract.
- Telemetry, costs, or runtime measurements.

## Out of scope

- Server-side or shared verification caches.
- Auto-discovery of `target_identity` from commit messages, READMEs, or branch names.
- Cross-target global state for monorepos with many features.
- Concurrent incremental verifications across branches or worktrees.
