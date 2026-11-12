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

The lead checks every claim in order and rejects it as `NON_ISSUE` at the first unsupported link, with a one-line rejection reason:

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

Reviewer-proposed severity is advisory; the lead assigns validated severity. When the validated severity differs from the proposed one, record a one-line reason for the change; for a `NON_ISSUE`, its rejection reason is that reason.

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

- `MISSING`: the change lacks evidence reasonably required by its contract. Any `MISSING` gap yields `FIX REQUIRED`.
- `UNAVAILABLE`: the evidence could not be collected because of environment, permissions, unavailable services, or unresolved requirements. This can produce `INCONCLUSIVE`.
- Never convert an unavailable check into a passing check.

## Evidence labels

- `executed`: a command ran in this run and its output was observed. `static`: the evidence was only read.
- Record who ran each check: `lead` or the reviewer role.
- A claim by anyone else that a check passed is never executed evidence.
- List every required check not run, and why.

## Out-of-mandate notes

Every `Out of mandate:` note is either adjudicated (validated or rejected like any claim) or listed under Open leads with the reviewer that raised it. None is dropped.

## Verdict rules

- `PASS`: no validated `BLOCKER` or `SHOULD_FIX`, no `MISSING` gap; all required evidence is present and supports the contract.
- `PASS WITH NOTES`: as `PASS`, with one or more validated `OPTIONAL` findings; or the panel was empty because the change has nothing substantive to review (the note states why); or the only evidence gaps are `UNAVAILABLE` roles omitted for the panel maximum whose surfaces are rated `low` or `medium` (see [panel.md](panel.md#risk-bands)). An empty panel is never by itself a reason for `INCONCLUSIVE`.
- `FIX REQUIRED`: at least one validated `BLOCKER` or `SHOULD_FIX`, or any `MISSING` evidence gap.
- `INCONCLUSIVE`: essential evidence is `UNAVAILABLE`, the source of truth is materially ambiguous, or clean evaluation cannot be completed safely; or a role omitted for the panel maximum covered a surface rated `high` or `critical`.

## Verdict discipline

- Use only the four verdict words: `PASS`, `PASS WITH NOTES`, `FIX REQUIRED`, `INCONCLUSIVE`. Never substitute words such as APPROVE, READY, or REQUEST CHANGES.
- Never issue `PASS` or `PASS WITH NOTES` while a validated `BLOCKER` or `SHOULD_FIX`, or any `MISSING` gap, is open, or while any re-confirmed prior finding is `unresolved`.
- Never describe `FIX REQUIRED` or `INCONCLUSIVE` as ready, approved, or passed.

## Re-check

- Eligibility: a run is a re-check only when both hold:
  1. a prior `FIX REQUIRED` report for the same contract, carrying a `verified_state`, is in the conversation or supplied with the invocation; when several prior reports for the contract are available, the newest governs;
  2. the prior Verification Contract's source is still available unchanged: for a `--contract` file, its current blob id (`git hash-object <file>`) equals the prior `contract_summary.source_hash`, compared by hash, never by path; for a conversation source, the conversation still contains the prior contract. Any other source (`invocation`, `spec/PR <ref>`, `repository docs`) makes the run ineligible. If the lead cannot compute the blob id, it records `source_hash: null`, and that report is not a re-check baseline.

  Otherwise run a full verification and set `recheck` to `null`; a statement that a prior run failed is not a prior report.
- Contract: reuse the prior report's contract summary and criteria together with the unchanged source; never rebuild the contract.
- Delta since a verified state: the commits since `verified_state.head` (all commits when it is `null`); the working-tree status of all paths, including new untracked files; and every recorded path whose current content differs from its recorded hash. A path whose content still matches its recorded hash is excluded. The same rules apply to every target kind.
- Target: the delta plus the file of every open validated `BLOCKER` or `SHOULD_FIX` in the prior report.
- Re-confirmation: adjudicate each open prior finding `resolved` or `unresolved` with evidence, whether or not the fix touched its file. Re-emit each `unresolved` finding among the validated findings with its original id, claim, location, and severity, so it stays open in later rounds.
- Prior validated `OPTIONAL` findings are not re-confirmed; unless the target shows them addressed, they carry forward as notes (validated `OPTIONAL` findings with their original ids), so a re-check whose only remaining items are prior `OPTIONAL` findings is `PASS WITH NOTES`.
- Stop rule: the loop stops at the first re-check with no new or unresolved validated `BLOCKER` or `SHOULD_FIX` and no `MISSING` gap. `OPTIONAL` findings never open another round.
- No-ship rule: a `FIX REQUIRED` report states that the change must not be committed, pushed, or described as verified until a re-check passes. Its minimum next action names the re-check: the roles to re-run and the verified state it compares against.

## Markdown report

The fixed header comes first, in this order. Keep the report concise: header first, then blocking findings first within Validated findings; aim for about 60 lines in `panel` mode outside the criteria table.

```markdown
# Verification: <VERDICT>
Target: <resolved target>
Assurance: independent panel | degraded independence
Evidence: executed <checks, who ran each>; static <what was only read>; not run <check — why>
Scope: covered <what the target covered>; not covered <what the target excluded>
Verified state: <head> <aggregate hash> | not recorded (<why>)
## Contract summary
<source of truth (with its source hash), requirements, risks, invariants, preserved behaviors>
## Acceptance criteria
| Criterion | Result | Evidence |
|---|---|---|
| A1: <text> | PASS / FAIL / UNAVAILABLE | file:line or command |
## Panel
<role — baseline or trigger that selected it; non-obvious omissions; requested and effective mode>
## Checks executed
<command or inspection, executed or static, who ran it, result; checks not run and why>
## Prior findings (re-check only)
<id — resolved | unresolved, with evidence>
## Validated findings
<ordered BLOCKER, SHOULD_FIX, OPTIONAL; a changed severity shows proposed -> validated and the one-line reason>
## Rejected claims
<material disputes and non-issues only, with reason>
## Evidence gaps
<MISSING or UNAVAILABLE, and why each matters>
## Open leads
<Out of mandate: notes not adjudicated, each with the reviewer that raised it>
## Minimum next action
<smallest action that changes the verdict; for FIX REQUIRED, the re-check (roles, verified state) and the no-ship statement>
```

The `Verified state` values and the `Scope` notes are defined in [json-report.md](json-report.md#verified-state) and [verification-contract.md](verification-contract.md#scope).
