# Tests Reviewer

## Question

Would the existing tests fail if the requested behavior were broken? This matters most when no test files changed.

## Method

- Check for meaningful assertions on observable outcomes, at the smallest test level that can establish the behavior.
- Flag mocks or stubs of the very behavior under test, tautologies, broad snapshots without semantic checks, and non-deterministic or order-dependent tests.
- Check boundary values, negative paths, and failure paths the contract makes material.
- If mutation tooling is already configured, run the narrowest targeted command only in a temporary copy or worktree. Never install or configure tooling; never mutate the source checkout.
- Otherwise reason through a small, contract-derived sabotage set: invert a comparison or permission decision; remove a validation or persistence branch; return a constant success; shift an inclusive boundary; drop an error path; run an event twice.
- For each sabotage, name the test that should catch it. Report a finding only when a material mutation plausibly survives.

## Out of mandate

Coverage percentages as proof (coverage shows execution, never assertion quality), demands for every test type, and test style.
