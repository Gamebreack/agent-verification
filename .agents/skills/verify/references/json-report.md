# Machine-readable Report

Use this format only when the invocation requests JSON. Return one JSON object and no surrounding prose or code fence. Field meanings follow the markdown report in [adjudication.md](adjudication.md#markdown-report).

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
  "criteria": [
    {"id": "A1", "result": "PASS | FAIL | UNAVAILABLE", "evidence": "path:line or command result"}
  ],
  "selected_reviewers": ["acceptance", "tests"],
  "selection_reasons": {"acceptance": "reason"},
  "checks_executed": [
    {"command_or_inspection": "what ran", "result": "observable result"}
  ],
  "findings": [
    {
      "id": "role-1",
      "status": "VALIDATED | NON_ISSUE",
      "reviewer": "role",
      "claim": "falsifiable claim",
      "requirement_or_invariant": "R1 | A1 | I1 | P1 | none",
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

- `case_id` is normally `null`; set it only when an evaluation invocation supplies one.
- `criteria[].id` uses the acceptance-criterion id from the Verification Contract, including ids kept from a `--contract` file.
- Preserve rejected seeded claims as `NON_ISSUE` findings with a `rejection_reason`, so adjudication can be evaluated.
- `selected_reviewers` is an empty array when the panel was empty. In `quick` mode it lists both roles carried by the single reviewer (`["acceptance", "tests"]`).
- `source_unchanged` is `true` only when the working tree is unchanged by the verification run.
- Do not report an unavailable check as successful.
