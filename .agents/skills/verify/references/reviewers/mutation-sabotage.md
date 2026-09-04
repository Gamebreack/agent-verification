# Mutation and Sabotage Reviewer

## Question

Would plausible defects survive the existing evidence?

## Method

When mutation tooling is already configured, run the narrowest targeted mutation command in an isolated temporary copy or worktree. Do not install or configure tooling.

Otherwise reason through a small, contract-derived sabotage set, such as:

- invert a comparison or permission decision;
- remove persistence or a validation branch;
- replace a computed result with a constant success;
- change an inclusive boundary;
- return stale data;
- drop an error path;
- execute an event twice;
- remove idempotency.

State which existing test should detect each mutation. Report a finding only when a material mutation plausibly survives. Do not mutate the user's source checkout.
