# Reviewer Selection

Use the requested mode as a starting point, then add a specialist only when a changed surface or risk justifies it.

## Modes

| Mode | Default panel | Intended use |
|---|---|---|
| `auto` | Acceptance + Test adequacy; add specialists by trigger | Normal default |
| `quick` | Acceptance + Test adequacy | Small, low-risk change |
| `tests` | Test adequacy + Mutation/sabotage + Boundary/invariants | Evaluate whether tests prove behavior |
| `feature` | Acceptance + Test adequacy + Regression + Boundary/invariants + Adversarial | Substantive feature work |
| `full` | All applicable correctness reviewers; Simplification last | Deep pre-merge review |
| `release` | Acceptance + Regression + Security when applicable + Failure/observability + Critical journey | Release readiness |

The lead still removes irrelevant reviewers. `full` does not mean every reviewer regardless of scope.

## Surface triggers

| Changed surface or risk | Add reviewer | Typical evidence |
|---|---|---|
| Existing behavior, public interface, shared module, migration, persisted state | Regression | historical tests, caller inspection, compatibility checks |
| Numeric ranges, quotas, state machines, ordering, concurrency, retries, idempotency | Boundary/invariants | boundary cases, properties, race/idempotency evidence |
| New or changed tests; suspiciously easy green suite | Mutation/sabotage | existing mutation report or semantic sabotage analysis |
| Auth, authorization, sessions, secrets, sensitive data, validation, admin paths, cryptography | Security | applicable threat model, negative authorization tests, static analysis |
| API/schema/event/file/protocol/service boundary | Contract boundaries | schema/consumer compatibility and integration evidence |
| Async jobs, queues, retries, partial failure, external dependencies, operations | Failure/observability | failure injection, retry/idempotency checks, logs/metrics/runbook evidence |
| Critical user or business journey | Critical journey | narrow end-to-end or high-fidelity integration evidence |
| Material implementation claims or high uncertainty | Adversarial | concrete falsification attempts |
| Correct but unusually complex substantive change | Simplification | demonstrated redundant path or avoidable mechanism |

## Risk escalation

- `low`: normally two reviewers; run narrow checks.
- `medium`: add Regression or the directly relevant specialist.
- `high`: include Acceptance, Test adequacy, Regression, and all surface-triggered specialists.
- `critical`: use release-grade evidence and return `INCONCLUSIVE` if the environment cannot establish essential safety.

## Bounds

- In `auto`, normally select two to five reviewers.
- Never add reviewers merely to make the panel look comprehensive.
- Never let a reviewer spawn another agent.
- Run Simplification only after correctness reviewers find no validated material defect.
- Explain every inclusion and any non-obvious omission.
