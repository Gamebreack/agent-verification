# Findings and Adjudication

## Reviewer output

Return `NO FINDINGS` or one block per claim:

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

## Panel validation

Before adjudicating findings, validate the panel composition itself. For each selected reviewer:

- Confirm an explicit surface trigger or risk band justifies its inclusion.
- If a baseline reviewer (Acceptance or Test adequacy) is absent for a substantive change, confirm a documented removal reason.

If the panel exceeds two reviewers without per-reviewer justification, surface a single panel-level `OPTIONAL` finding labeled `panel-over-selection`. If a baseline reviewer is absent without a documented reason, surface `panel-missing-baseline`. Both are advisory; they do not block `PASS` unless they correlate with a substantive defect.

## Scope preservation

A reviewer must report against the TARGET the user requested, not against a narrower boundary the implementation suggests. If a finding's `scope_relevance` describes a smaller surface than the user's TARGET (e.g., it cites only the latest commit, only the changed file, or only the latest diff when the user asked for the whole feature), the adjudicator rejects it as `NON_ISSUE` with reason `out-of-target-narrowing`. This rule applies to every verification regardless of mode; it exists to prevent incremental re-verification from silently narrowing assurance.

## Adjudication gate

For every claim, determine:

0. Does the finding's `scope_relevance` narrow the user's TARGET below what was originally requested? If yes → `NON_ISSUE` with `rejection_reason: out-of-target-narrowing`.
1. Is the cited evidence real and attributable to the resolved target?
2. Does the failure mechanism follow from that evidence?
3. Is the claim relevant to a requirement, invariant, preserved behavior, constraint, or necessary release property?
4. Is the impact material at the stated severity?
5. Does counter-evidence invalidate or narrow it?
6. Is it a duplicate symptom of an already accepted root cause?

Reject a finding as `NON_ISSUE` when any required link is unsupported. Preserve a concise rejection reason for disputed or high-severity claims.

## Validated severity

- `BLOCKER`: the requested behavior is absent or wrong, or there is demonstrated risk to security, authorization, data integrity, destructive safety, or deployability that makes shipping unsafe.
- `SHOULD_FIX`: a real, evidenced defect with plausible material impact that should be corrected before considering the change complete.
- `OPTIONAL`: a supported improvement that is not required for correctness, safety, or the agreed scope.
- `NON_ISSUE`: unsupported, irrelevant, contradicted, duplicate, or preference-only.

Reviewer-proposed severity is advisory. The verification lead assigns validated severity.

## Evidence gaps

- `MISSING`: the change lacks evidence reasonably required by its contract. This can produce `FIX REQUIRED`.
- `UNAVAILABLE`: the evidence could not be collected because of environment, permissions, unavailable services, or unresolved requirements. This can produce `INCONCLUSIVE`.
- Do not convert an unavailable check into a passing check.

## Verdict rules

- `PASS`: no validated `BLOCKER` or `SHOULD_FIX`; all required evidence is present and supports the contract.
- `PASS WITH NOTES`: same as `PASS`, with one or more validated `OPTIONAL` findings.
- `FIX REQUIRED`: at least one validated `BLOCKER` or `SHOULD_FIX`, or a material `MISSING` evidence requirement that the implementation should supply.
- `INCONCLUSIVE`: essential evidence is `UNAVAILABLE`, the source of truth is materially ambiguous, or clean evaluation cannot be completed safely.

## Final report

```markdown
# Verification: <VERDICT>

Target: <resolved target>
Assurance: independent panel | degraded independence

## Contract
<requirements, risks, invariants, and preserved behavior>

## Panel
<reviewer and selection reason>

## Checks executed
<command/inspection and result; distinguish not run>

## Validated findings
<ordered BLOCKER, SHOULD_FIX, OPTIONAL>

## Rejected claims
<only material disputes/non-issues>

## Evidence gaps
<missing or unavailable evidence>

## Minimum next action
<smallest action that changes the verdict>
```
