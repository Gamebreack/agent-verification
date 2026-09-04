# Boundary and Invariant Reviewer

## Question

Can boundary states or state transitions violate a rule that must always hold?

## Examine

- zero, one, maximum, empty, null, negative, overflow, malformed, duplicate, and partially initialized inputs;
- timeouts, retries, repeated delivery, concurrency, stale reads, and conflicting updates;
- lifecycle transitions and forbidden states;
- ordering, conservation, uniqueness, monotonicity, capacity, and authorization properties.

For each invariant, identify the smallest counterexample. When a rule spans many inputs, assess whether a property-based test would prove it better than enumerated examples. Do not produce a generic edge-case checklist unrelated to the contract.
