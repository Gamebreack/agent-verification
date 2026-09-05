# Reviewer Selection

Use the requested mode as the baseline, then add or drop specialists by explicit surface trigger or risk band. State why each inclusion and any non-obvious omission.

## Staged escalation

1. **Baseline**: Acceptance + Test adequacy. Apply to substantive code changes across `auto`, `quick`, `feature`, and `release` modes.
2. **Add specialist**: only when a concrete surface trigger or risk band applies. Each addition must cite its trigger.
3. **Drop default**: when the contract shows a default reviewer is irrelevant (e.g., Test adequacy with no test changes), omit it.
4. **Empty panel**: acceptable for trivial changes. Return `INCONCLUSIVE` over inventing reviewers.

## Modes

| Mode | Default panel | Intended use |
|---|---|---|
| `auto` | Acceptance + Test adequacy; add specialists by trigger | Normal default |
| `quick` | Acceptance + Test adequacy | Small, low-risk change |
| `tests` | Test adequacy + Mutation/sabotage + Boundary/invariants | Evaluate whether tests prove behavior |
| `feature` | Acceptance + Test adequacy + Regression + Boundary/invariants + Adversarial | Substantive feature work |
| `full` | All applicable correctness reviewers; Simplification last | Deep pre-merge review |
| `release` | Acceptance + Regression when existing behavior is exposed + applicable release specialists | Release readiness |

The lead still removes irrelevant reviewers. `full` does not mean every reviewer regardless of scope.

## Surface triggers

| Changed surface or risk | Add reviewer | Typical evidence |
|---|---|---|
| Existing behavior, public interface, shared module, migration, persisted state | Regression | historical tests, caller inspection, compatibility checks |
| Numeric ranges, quotas, state machines, ordering, concurrency, retries, idempotency | Boundary/invariants | boundary cases, properties, race/idempotency evidence |
| New or changed tests; suspiciously easy green suite | Mutation/sabotage | existing mutation report or semantic sabotage analysis |
| Auth, authorization, sessions, secrets, sensitive data, validation, admin paths, cryptography | Security | applicable threat model, negative authorization tests, static analysis |
| API/schema/event/file/protocol/service boundary, including structured response keys consumed by another module | Contract boundaries | schema/consumer compatibility and integration evidence |
| Async jobs, queues, retries, partial failure, external dependencies, operations | Failure/observability | failure injection, retry/idempotency checks, logs/metrics/runbook evidence |
| Critical user or business journey spanning multiple components or boundaries | Critical journey | narrow end-to-end or high-fidelity integration evidence |
| Material implementation claims or high uncertainty | Adversarial | concrete falsification attempts |
| Correct but unusually complex substantive change | Simplification | demonstrated redundant path or avoidable mechanism |

## Risk escalation

- `low`: normally two reviewers; run narrow checks.
- `medium`: add Regression or the directly relevant specialist.
- `high`: include Acceptance, Test adequacy, Regression, and all surface-triggered specialists.
- `critical`: use release-grade evidence and return `INCONCLUSIVE` if the environment cannot establish essential safety.

## Bounds

- In `auto`, `quick`, `feature`, and `release`, select no more than five reviewers. `tests` normally uses three. `full` may exceed five only when distinct changed surfaces justify every additional role.
- Modes are starting points, not additive checklists. Remove default reviewers that are irrelevant to the resolved target.
- Prefer a directly triggered specialist over generic Adversarial review. Never substitute Adversarial for Security, Contract boundaries, Boundary/invariants, or Failure/observability when that specialist is triggered.
- A pure function is not by itself a critical journey. Select Critical journey only when the required outcome spans integration boundaries that narrower evidence cannot establish.
- Select Failure/observability only for asynchronous work, external dependency failure, recovery, or an operational path where silent failure is plausible. Do not add it merely because the mode is `release`.
- Never add reviewers merely to make the panel look comprehensive.
- Never let a reviewer spawn another agent.
- Run Simplification only after correctness reviewers find no validated material defect.
- Explain every inclusion and any non-obvious omission.
