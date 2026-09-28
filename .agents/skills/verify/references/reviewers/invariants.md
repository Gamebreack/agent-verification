# Invariants Reviewer

## Question

Can a boundary state, state transition, or failure path violate a rule that must always hold — or fail silently?

## Method

- Cover the contract's P*/I* entries first; list any categories of your mandate you could not examine under `Out of mandate:` so the lead sees the gap.
- Probe zero, one, maximum, empty, null, negative, overflow, malformed, duplicate, and inclusive/exclusive boundary inputs.
- Check ordering, uniqueness, conservation, monotonicity, capacity, and forbidden lifecycle or state-machine transitions.
- Check timeouts, retries, backoff, duplicate delivery, idempotency, concurrency, stale reads, and conflicting updates.
- Check error paths and partial failure: is the outcome safe, recoverable, and visible, or silently or misleadingly successful?
- For each invariant, identify the smallest counterexample. Note when a property-based test would prove a rule better than enumerated examples.

## Out of mandate

Generic edge-case checklists unrelated to the contract, and observability machinery for trivial code. Tie every finding to a concrete invariant or failure.
