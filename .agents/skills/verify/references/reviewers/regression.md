# Regression Reviewer

## Question

Which previously valid behaviors, or consumers of the changed interfaces, could this target break?

## Method

- Cover the contract's P*/I* entries first; list any categories of your mandate you could not examine under `Out of mandate:` so the lead sees the gap.
- Check each preserved behavior in the contract against the change and historical tests.
- Find the callers and consumers of every changed interface. Reading unchanged caller files is in scope for this role.
- Check compatibility of request, response, event, schema, file, CLI, and protocol shapes: required vs. optional fields, defaults, nullability, enums, structured response keys, error semantics, and serialization.
- Check migrations, persisted state, configuration defaults, and side effects.
- When the required outcome spans several components, verify the shortest complete path through the real integration points, including one material failure path when risk justifies it; prefer a focused integration test over full end-to-end.

## Out of mandate

Theoretical blast radius without a plausible changed behavior. Name the affected producer and consumer, or the preserved behavior, for every finding.
