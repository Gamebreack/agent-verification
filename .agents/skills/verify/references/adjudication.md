# Findings and Adjudication

## Finding schema

Reviewers return `NO FINDINGS` or one block per claim:

```yaml
id: <role>-<number>
reviewer: <role>
claim: <one falsifiable defect claim>
requirement_or_invariant: <contract id or none>
evidence:
  - <file and line, command and result, or direct observation>
failure_mechanism: <trigger -> behavior -> impact>
proposed_severity: BLOCKER | SHOULD_FIX | OPTIONAL
confidence: high | medium | low
scope_relevance: <why this belongs to the target contract>
suggested_check: <smallest check that would confirm or refute the claim, if needed>
```

Do not combine unrelated defects. Do not report style preferences, generic risk language, or a concern without a plausible failure chain.

## Adjudication gate

The lead checks every claim in order and rejects it as `NON_ISSUE` at the first unsupported link, keeping a concise rejection reason for disputed or high-severity claims:

1. Is the cited evidence real in the repository at the target state and causally linked to a change in the target? (Evidence may live in unchanged files, e.g. a caller or consumer; it need not be inside the diff.)
2. Does the failure mechanism follow from that evidence alone? Re-derive it
   from the cited lines, not from the reviewer's framing; when several
   reviewers share a premise, test the premise: would the mechanism still
   hold if it were false?
   - Echoing a value the caller supplied is not exposure of internal state,
     unless the contract makes the response recipient less trusted than
     that caller.
   - A weak or missing test for behavior verified correct is not a failure
     mechanism (see Test-strength observations).
3. Is the claim relevant to a requirement, acceptance criterion, invariant, preserved behavior, constraint, or necessary release property?
4. Is the impact material at the stated severity?
5. Does counter-evidence invalidate or narrow it?
6. Is it a duplicate symptom of an already accepted root cause? If so, merge it.

## Validated severity

- `BLOCKER`: the requested behavior is absent or wrong, or there is demonstrated risk to security, authorization, data integrity, destructive safety, or deployability that makes shipping unsafe.
- `SHOULD_FIX`: a real, evidenced defect with plausible material impact that should be corrected before the change is considered complete.
- `OPTIONAL`: a supported improvement not required for correctness, safety, or the agreed scope.
- `NON_ISSUE`: unsupported, irrelevant, contradicted, duplicate, or preference-only.

Reviewer-proposed severity is advisory; the lead assigns validated severity.

### Test-strength observations

- A test that asserts wrong behavior is a defect: severity follows the code
  it protects (`SHOULD_FIX` or `BLOCKER`).
- A test the contract's `required_evidence` names and that is absent is a
  `MISSING` evidence gap, not a finding.
- A test that mocks the code under test, or cannot fail, while the
  requirement it claims to prove is broken is evidence of that defect: keep
  its evidence and merge it with the code defect (gate step 6).
- A weak or absent test for behavior the lead has verified correct by
  reading is `NON_ISSUE`; record it under Rejected claims with the reason
  "test-strength on correct code". It does not produce `PASS WITH NOTES`.

## Evidence gaps

- `MISSING`: the change lacks evidence reasonably required by its contract. This can produce `FIX REQUIRED`.
- `UNAVAILABLE`: the evidence could not be collected because of environment, permissions, unavailable services, or unresolved requirements. This can produce `INCONCLUSIVE`.
- Never convert an unavailable check into a passing check.

## Verdict rules

- `PASS`: no validated `BLOCKER` or `SHOULD_FIX`; all required evidence is present and supports the contract.
- `PASS WITH NOTES`: as `PASS`, with one or more validated `OPTIONAL` findings; or the panel was empty because the change has nothing substantive to review (the note states why); or the only evidence gaps are `UNAVAILABLE` roles omitted for the panel maximum whose surfaces are rated `low` or `medium` (see [panel.md](panel.md#risk-bands)). An empty panel is never by itself a reason for `INCONCLUSIVE`.
- `FIX REQUIRED`: at least one validated `BLOCKER` or `SHOULD_FIX`, or a material `MISSING` evidence requirement the implementation should supply.
- `INCONCLUSIVE`: essential evidence is `UNAVAILABLE`, the source of truth is materially ambiguous, or clean evaluation cannot be completed safely; or a role omitted for the panel maximum covered a surface rated `high` or `critical`.

## Markdown report

```markdown
# Verification: <VERDICT>
Target: <resolved target>
Assurance: independent panel | degraded independence
## Contract summary
<source of truth, requirements, risks, invariants, preserved behaviors>
## Acceptance criteria
| Criterion | Result | Evidence |
|---|---|---|
| A1: <text> | PASS / FAIL / UNAVAILABLE | file:line or command |
## Panel
<role — baseline or trigger that selected it; non-obvious omissions>
## Checks executed
<command or inspection and result; list checks not run and why>
## Validated findings
<ordered BLOCKER, SHOULD_FIX, OPTIONAL>
## Rejected claims
<material disputes and non-issues only, with reason>
## Evidence gaps
<MISSING or UNAVAILABLE, and why each matters>
## Minimum next action
<smallest action that changes the verdict>
```
