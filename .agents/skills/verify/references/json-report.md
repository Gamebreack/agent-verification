# Machine-readable Report

Use this format only when the invocation requests JSON. Return one JSON object and no surrounding prose or code fence.

```json
{
  "case_id": null,
  "verdict": "PASS | PASS WITH NOTES | FIX REQUIRED | INCONCLUSIVE",
  "assurance": "independent panel | degraded independence",
  "target": "resolved target",
  "contract_summary": {
    "requirements": ["R1: observable behavior"],
    "risks": ["surface: level and rationale"],
    "invariants": ["I1: rule"],
    "preserved_behaviors": ["P1: behavior"]
  },
  "selected_reviewers": ["acceptance", "test-adequacy"],
  "selection_reasons": {"acceptance": "reason"},
  "incremental": true,
  "delta": {
    "from_sha": "<sha>",
    "to_sha": "<sha>",
    "files_changed": ["..."]
  },
  "invalidation": {
    "<reviewer_role>": "RE_RAN | REUSED"
  },
  "checks_executed": [
    {"command_or_inspection": "what ran", "result": "observable result"}
  ],
  "findings": [
    {
      "id": "role-1",
      "status": "VALIDATED | NON_ISSUE",
      "reviewer": "role",
      "claim": "falsifiable claim",
      "requirement_or_invariant": "R1 | I1 | P1 | none",
      "evidence": ["path:line or command result"],
      "failure_mechanism": "trigger -> behavior -> impact",
      "severity": "BLOCKER | SHOULD_FIX | OPTIONAL | NON_ISSUE",
      "rejection_reason": null
    }
  ],
  "evidence_gaps": [
    {"kind": "MISSING | UNAVAILABLE", "evidence": "what is absent and why it matters"}
  ],
  "source_unchanged": true,
  "minimum_next_action": "smallest action that changes the verdict"
}
```

`case_id` is normally `null`; set it only when an evaluation invocation supplies one. Preserve rejected seeded claims as `NON_ISSUE` findings so adjudication can be evaluated. Do not report an unavailable check as successful.

## Properties

- `incremental`: boolean (optional). True when incremental re-verification was executed.
- `delta`: object (optional). Contains `from_sha`, `to_sha`, and `files_changed`.
- `invalidation`: object (optional). Mapping of reviewer role to `RE_RAN` or `REUSED`. For reused reviewers, record a single entry in `checks_executed` with `command_or_inspection: "evidence_paths existence check"` and `result: "passed"`.
