# Verification Contract

Create this contract before selecting reviewers. It is the shared source of truth for every reviewer, not a restatement of the implementation.

## Template

```yaml
target:
  kind: working-tree | range | commit | branch | pull-request | files | artifact
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

## Base resolution

Resolve the base of the default target read-only, before analysis, and never fetch. Use the first that resolves:

1. a base named by the invocation or by repository instructions;
2. `origin/HEAD` (a local ref; read it with `git symbolic-ref refs/remotes/origin/HEAD`), never the current branch's `@{upstream}`, which for a feature branch is usually the branch itself;
3. local `main`, else `master`;
4. no base: the target is the working-tree diff only, and the Scope states that branch commits were not covered. If the working tree is also clean, the target is empty: no reviewer is dispatched, the empty-panel rule applies (`PASS WITH NOTES`, see [adjudication.md](adjudication.md#verdict-rules)), and its note states that no base resolved and nothing was reviewed.

## Artifact targets

A plan or design document named as the target is an `artifact` target.

- Source of truth: the request the document answers, not the document itself. If there is none, use the document's stated goals and record that under `ambiguities`.
- Changed surfaces are the surfaces the document proposes to change; triggers and risk bands apply unchanged.
- Every role checks the document's factual claims and assumptions within its mandate against the repository.
- Evidence is mostly static; the report's Evidence line says so.

## Scope

The report's Scope names what the target covered and what it excluded: for example pre-existing code outside the target, commits outside the target, or staged content that differs from the working tree (staged content is not what was reviewed). Never imply that anything outside the target was covered.
