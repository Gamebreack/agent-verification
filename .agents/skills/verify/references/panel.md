# Panel Selection

This file is the only home for mode baselines, triggers, risk bands, and panel bounds. Start from the mode baseline, add a specialist only for a concrete trigger, and state every inclusion reason and any non-obvious omission.

## Modes

| Mode | Always | Add by trigger | Max roles | Intended use |
|---|---|---|---|---|
| `quick` | acceptance, tests — carried by one reviewer context given both role files | none | 2 | small, low-risk change |
| `panel` (default) | acceptance, tests | regression, invariants, security | 4 | normal pre-merge verification |
| `release` | acceptance, tests, regression | invariants, security | 5 | release readiness |

Escalate and say so: if `quick` is requested and a surface is `high` or `critical`, run `panel`; if `panel` is requested and a surface is `critical`, run `release`.

## Surface triggers

| Changed surface | Add role | Typical evidence |
|---|---|---|
| Behavior observable by another caller, consumer, or user beyond the edited function itself; public or shared interface; persisted state; migration; defaults or configuration | regression | historical tests, caller inspection, compatibility checks |
| API, schema, event, file, CLI, or protocol boundary, including structured response keys consumed by another module | regression | producer/consumer compatibility, focused integration evidence |
| Outcome that spans several components or boundaries (critical user or business journey) | regression | narrow end-to-end or high-fidelity integration evidence |
| Numeric ranges, quotas, inclusive/exclusive boundaries, ordering, state machines, lifecycle transitions | invariants | boundary cases, properties, smallest counterexample |
| Concurrency, retries, idempotency, duplicate delivery, async jobs, queues, external dependency failure, partial failure | invariants | race/idempotency evidence, failure-path tests, silent-failure analysis |
| Authentication, authorization, tenancy, sessions, secrets, sensitive data, input validation at trust boundaries, admin paths, cryptography | security | negative authorization tests, threat model, static analysis |

Editing a function body is not by itself a regression trigger; the trigger is a consumer or persisted surface that could observe the difference. A pure function is not by itself a cross-boundary journey. Triggers are concrete changed surfaces, not generic risk language. A numeric parameter, a format width, or a statement of the input type is not by itself an invariants trigger; the trigger is a range, boundary, ordering, or state rule that the contract requires the change to hold. Speculating about inputs the contract excludes is not a trigger.

## Risk bands

Use the per-surface risk recorded in the Verification Contract.

- `low` / `medium`: mode baseline plus only directly triggered specialists.
- `high`: every triggered specialist is included and ambiguous triggers resolve to inclusion.
- `critical`: as `high`, and essential safety requires release-grade evidence. If the environment cannot produce it, the verdict is `INCONCLUSIVE`.

Baseline roles (acceptance, tests; plus regression in `release`) are never dropped. When triggered specialists exceed the mode maximum, keep those covering the highest-risk surfaces and record each omitted role as an `UNAVAILABLE` evidence gap naming the surface. Its verdict effect is defined in [adjudication.md](adjudication.md#verdict-rules) and is never `FIX REQUIRED` on its own. Name the larger mode as the minimum next action.

## Rules

- Do not drop `tests` because no test files changed. That is exactly when it matters most.
- A change with nothing substantive to review (documentation, comments, or formatting only, with no behavioral effect) gets an empty panel. Its verdict is defined in [adjudication.md](adjudication.md#verdict-rules).
- Never add roles to make the panel look thorough.
- Never split a role across reviewers or exceed the mode maximum. Only `quick` combines two roles in one reviewer context.
- Record for every selected role the baseline or trigger that selected it, and explain any non-obvious omission.
