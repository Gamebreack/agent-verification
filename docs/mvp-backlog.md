# MVP Backlog

## Milestone 1: Executable skill draft

- [x] Canonical Agent Skill layout.
- [x] Verification Contract schema.
- [x] Risk- and surface-based reviewer selection.
- [x] Specialist reviewer mandates.
- [x] Finding schema and adjudication rules.
- [x] OpenCode invocation adapter.
- [ ] Validate behavior on realistic fixture repositories.
- [ ] Revise prompts only from observed failures.

## Milestone 2: Behavioral evaluation

Create small fixtures where the expected verdict is externally knowable:

- [ ] Feature is implemented but acceptance criterion is omitted.
- [ ] Tests pass while mocking the behavior under test.
- [ ] Boundary comparison is inverted.
- [ ] Duplicate event breaks idempotency.
- [ ] Public contract breaks one consumer.
- [ ] Authorization allows a forbidden tenant.
- [ ] Reviewer raises a plausible-sounding non-issue that adjudication must reject.
- [ ] Essential service is unavailable, requiring `INCONCLUSIVE`.
- [ ] Correct low-risk change passes without unnecessary reviewers.

Evaluate outcomes and reasoning, not exact wording. Record false negatives, false positives, over-severity, unnecessary reviewer selection, and context leakage.

## Milestone 3: Portability checks

- [ ] Cursor discovery and `/verify` invocation.
- [ ] Codex discovery and `$verify` invocation.
- [ ] OpenCode discovery and wrapper invocation.
- [ ] Confirm reviewers receive clean context on each host.
- [ ] Confirm depth-one and read-only constraints are respected.

## Milestone 4: Distribution

- [ ] Choose a license.
- [ ] Decide standalone-skill versus plugin release packaging.
- [ ] Add installation instructions supported by tested hosts.
- [ ] Add versioning and release criteria.
- [ ] Publish only after behavioral fixtures pass on at least two hosts.

## Release gate

The MVP is ready when it can:

1. derive a correct contract from an explicit task;
2. select a bounded, relevant panel;
3. keep reviewer contexts independent;
4. reject at least one seeded speculative finding;
5. catch the seeded acceptance, bogus-test, regression, invariant, and authorization defects;
6. distinguish `FIX REQUIRED` from `INCONCLUSIVE`;
7. leave the target source unchanged.
