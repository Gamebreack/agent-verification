# Machine-readable Report

Use this format only when the invocation requests JSON. Return one JSON object and no surrounding prose or code fence. Field meanings follow the markdown report in [adjudication.md](adjudication.md#markdown-report).

```json
{
  "case_id": null,
  "verdict": "PASS | PASS WITH NOTES | FIX REQUIRED | INCONCLUSIVE",
  "assurance": "independent panel | degraded independence",
  "requested_mode": "quick | panel | release",
  "effective_mode": "quick | panel | release",
  "target": "resolved target",
  "scope": {
    "covered": ["what the target covered"],
    "not_covered": ["what the target excluded"]
  },
  "contract_summary": {
    "source_of_truth": "intent source used",
    "source_hash": "blob id of the --contract file | null",
    "requirements": ["R1: observable behavior"],
    "risks": ["surface: level and rationale"],
    "invariants": ["I1: rule"],
    "preserved_behaviors": ["P1: behavior"]
  },
  "criteria": [
    {"id": "A1", "text": "full acceptance-criterion text", "result": "PASS | FAIL | UNAVAILABLE", "evidence": "path:line or command result"}
  ],
  "selected_reviewers": ["acceptance", "tests"],
  "selection_reasons": {"acceptance": "reason"},
  "checks_executed": [
    {
      "command_or_inspection": "what ran or was read",
      "result": "observable result",
      "execution": "executed | static",
      "run_by": "lead | role"
    }
  ],
  "checks_not_run": [
    {"check": "command or inspection", "reason": "why it was not run"}
  ],
  "findings": [
    {
      "id": "role-1",
      "status": "VALIDATED | NON_ISSUE",
      "reviewer": "role | lead",
      "claim": "falsifiable claim",
      "requirement_or_invariant": "R1 | A1 | I1 | P1 | none",
      "evidence": ["path:line or command result"],
      "failure_mechanism": "trigger -> behavior -> impact",
      "proposed_severity": "BLOCKER | SHOULD_FIX | OPTIONAL",
      "severity": "BLOCKER | SHOULD_FIX | OPTIONAL | NON_ISSUE",
      "severity_change_reason": null,
      "rejection_reason": null
    }
  ],
  "out_of_mandate": [
    {"reviewer": "role", "note": "one-line note", "disposition": "adjudicated | open_lead", "finding_id": "role-1"}
  ],
  "evidence_gaps": [
    {"kind": "MISSING | UNAVAILABLE", "evidence": "what is absent and why it matters"}
  ],
  "verified_state": {
    "head": "commit sha",
    "files": {"path/to/file": "blob id"}
  },
  "recheck": {
    "round": 1,
    "prior_verdict": "FIX REQUIRED",
    "prior_findings": [
      {"id": "role-1", "resolution": "resolved | unresolved", "evidence": ["path:line or command result"]}
    ],
    "roles": ["acceptance", "tests"],
    "delta": {"commits": ["sha"], "paths": ["path/to/file"]},
    "another_round_required": false
  },
  "source_unchanged": true,
  "minimum_next_action": "smallest action that changes the verdict"
}
```

## Fields

- `case_id` is normally `null`; set it only when an evaluation invocation supplies one.
- `requested_mode` is the mode invoked; `effective_mode` is the mode run after any escalation.
- `contract_summary.source_of_truth` names the intent source the contract was built from, for example `"--contract <path>"`, `"invocation"`, `"conversation"`, `"spec/PR <ref>"`, or `"repository docs"`.
- `contract_summary.source_hash` is the `--contract` file's blob id (`git hash-object <file>`, never with `-w`), taken when the contract is built; `null` for any other source. A re-check compares it ([adjudication.md](adjudication.md#re-check)).
- `criteria[].id` uses the acceptance-criterion id from the Verification Contract, including ids kept from a `--contract` file; `criteria[].text` is that criterion's full text, so a re-check can reuse the contract.
- `selected_reviewers` is an empty array when the panel was empty. In `quick` mode it lists both roles carried by the single reviewer (`["acceptance", "tests"]`).
- `checks_executed[].execution` and `run_by` follow [adjudication.md](adjudication.md#evidence-labels). Do not report an unavailable check as successful.
- `findings[].proposed_severity` is required when a reviewer originated the finding; a finding the lead originated has `reviewer: "lead"` and may omit it. `severity_change_reason` is a non-empty string when `severity` differs from `proposed_severity`, else `null`; for a `NON_ISSUE`, the `rejection_reason` is that reason.
- In a re-check, a re-emitted `unresolved` prior finding or a carried-forward `OPTIONAL` is a `findings` entry with `status: "VALIDATED"` and its original `id` ([adjudication.md](adjudication.md#re-check)).
- Preserve rejected seeded claims as `NON_ISSUE` findings with a `rejection_reason`, so adjudication can be evaluated.
- `out_of_mandate[].finding_id` names the finding an adjudicated note became, or is `null`.
- `recheck` is `null` unless the run is a re-check ([adjudication.md](adjudication.md#re-check)). `prior_findings` lists every open validated `BLOCKER` or `SHOULD_FIX` of the prior report. `another_round_required` is `true` while a new or unresolved validated `BLOCKER` or `SHOULD_FIX`, or a `MISSING` gap, remains.
- `source_unchanged` is `true` only when the working tree is unchanged by the verification run. Untracked caches or coverage files produced by existing project commands do not make it `false`; only changes to tracked or pre-existing content do.

## Verified state

Record it read-only, for the working-tree content reviewers read:

- `head`: `git rev-parse HEAD`, or `null` when the repository has no commits.
- `files`: each target path mapped to `git hash-object <path>` (never with `-w`), or `null` for a deleted path. In a re-check, cover the union of the prior `verified_state.files` paths, the delta's paths, and the files of open prior findings.
- Never hash the index. When staged content differs from the working tree, say so in the Scope ([verification-contract.md](verification-contract.md#scope)).
- There is no `source` field: `verified_state` records working-tree content only when reviewers read the working tree. For a commit, range, or pull-request target that is not the checked-out working tree, record `verified_state: null` and state in the Scope that the verified state was not recorded; such a report is not a re-check baseline.
- The markdown `Verified state` line shows `head` and one aggregate hash: `git hash-object --stdin` over the sorted `<blob> <path>` lines, where a deleted path's line is `null <path>`. Per-file ids appear only in JSON.
- Post-commit match: a property the committing agent or a harness can check, not a step of the run. Committed blob ids (`git rev-parse HEAD:<path>`) equal to `files` show the commit is what was verified; any mismatch, including a commit of only part of the reviewed content, means the commit must not be described as verified.
