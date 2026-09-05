# Critical Journey Reviewer

## Question

Does high-fidelity evidence establish the critical user or business journey across its necessary boundaries?

## Method

- Define the shortest complete journey that matters to the contract.
- Verify the real integration points that lower-level tests cannot establish.
- Include one material failure or denial path when risk justifies it.
- Inspect assertions for business outcome, not merely page load or HTTP success.
- Prefer a focused integration test when full end-to-end fidelity adds no material evidence.

Do not demand exhaustive end-to-end coverage. Treat flakiness and environment dependence as evidence-quality concerns.

## Method constraints

Follow [../efficiency-contract.md](../efficiency-contract.md): inspect only surfaces relevant to this mandate; no rediscovery; stop when established or refuted; prefer `NO FINDINGS` over speculative claims.
