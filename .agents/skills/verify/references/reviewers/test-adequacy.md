# Test Adequacy Reviewer

## Question

Do the tests provide trustworthy evidence for the requested behavior and risks?

## Examine

- meaningful assertions on observable outcomes;
- tests that would fail if the feature were removed or inverted;
- appropriate fidelity for the boundary under test;
- negative, failure, and boundary paths justified by risk;
- determinism, isolation, order independence, and realistic synchronization;
- excessive coupling to implementation details;
- mocks of the very behavior supposedly being proved;
- tautologies, duplicate tests, broad snapshots without semantic checks, and framework-language trivia;
- untested branches that matter to the contract.

Coverage may identify unexecuted code but never proves assertion quality. Prefer the smallest test level that can establish the behavior. Do not demand every test type.
