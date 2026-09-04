# Verification Contract

Create this contract before dispatching reviewers. It is the shared source of truth, not a restatement of the implementation.

## Template

```yaml
target:
  kind: working-tree | range | commit | branch | pull-request | files
  value: <resolved target>
source_of_truth:
  - <task, issue, specification, accepted plan, or explicit user statement>
requested_behaviors:
  - id: R1
    behavior: <externally observable behavior>
acceptance_criteria:
  - id: A1
    requirement: R1
    observable: <what would demonstrate success>
non_goals:
  - <explicit exclusion>
constraints:
  - <settled architecture, compatibility, performance, policy, or operational limit>
changed_surfaces:
  - surface: <module, interface, schema, workflow, or external boundary>
    risk: low | medium | high | critical
    rationale: <impact and likelihood, not change size alone>
invariants:
  - id: I1
    rule: <condition that must always hold>
preserved_behaviors:
  - id: P1
    behavior: <previously valid behavior that must not regress>
required_evidence:
  - id: E1
    proves: R1 | I1 | P1
    evidence: <test, analysis, inspection, runtime observation, or other check>
ambiguities:
  - <unknown that could affect reviewer scope or verdict>
```

## Rules

- Phrase requirements as observable behavior, not implementation choices.
- Trace each acceptance criterion to a requested behavior.
- Treat risk as impact multiplied by plausible likelihood. A one-line authorization change may be critical; a large generated-file change may be low risk.
- Derive invariants from business, data, authorization, concurrency, ordering, idempotency, and lifecycle rules where applicable.
- Required evidence must match the failure mode. Line coverage alone is never sufficient.
- Distinguish absent evidence from evidence that could not be collected. The former may require a fix; the latter may make the verdict inconclusive.
- Preserve ambiguities. Do not silently resolve them in favor of the implementation.
