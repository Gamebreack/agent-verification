# Verification Contract

Create this contract before selecting reviewers. It is the shared source of truth for every reviewer, not a restatement of the implementation.

## Template

```yaml
target:
  kind: working-tree | range | commit | branch | pull-request | files
  value: <resolved target>
source_of_truth:
  - <--contract file, task, issue, specification, accepted plan, or explicit user statement>
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

## When `--contract` is supplied

- Extract requested behaviors, acceptance criteria, and non-goals from it verbatim where possible.
- Keep each acceptance criterion's own numbering and wording from the source file (for example `AC-3` stays `AC-3`), so the report's per-criterion table maps back to the file 1:1. Use `A1..An` only when the file has no numbering.
- Fill the remaining fields (surfaces, invariants, preserved behaviors, evidence) from the diff and repository, but never let them contradict or narrow the file.
- Record any conflict between the file and other intent sources under `ambiguities`; the precedence in SKILL.md decides it.
