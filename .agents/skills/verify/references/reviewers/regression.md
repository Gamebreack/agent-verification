# Regression Reviewer

## Question

Which previously valid behaviors could this target have changed unintentionally?

## Examine

- callers and public interfaces;
- schemas, migrations, persisted state, and serialization;
- authorization and side effects;
- event, API, CLI, and file contracts;
- defaults, configuration, and backward compatibility;
- historical tests and documented behavior;
- shared code paths outside the stated feature.

Connect every finding to an actual affected consumer or preserved behavior. A theoretical blast radius without a plausible changed behavior is not a finding.

## Method constraints

Follow [../efficiency-contract.md](../efficiency-contract.md): inspect only surfaces relevant to this mandate; no rediscovery; stop when established or refuted; prefer `NO FINDINGS` over speculative claims.
