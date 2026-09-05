# MVP Backlog

## Milestone 1: Executable skill

- [x] Canonical Agent Skill layout.
- [x] Verification Contract schema.
- [x] Risk- and surface-based reviewer selection.
- [x] Specialist reviewer mandates.
- [x] Finding schema and adjudication rules.
- [x] OpenCode invocation adapter.
- [x] Validate behavior on realistic fixture repositories.
- [x] Revise prompts only from observed failures.

## Milestone 2: Behavioral evaluation

Create small fixtures where the expected verdict is externally knowable:

- [x] Feature is implemented but acceptance criterion is omitted.
- [x] Tests pass while mocking the behavior under test.
- [x] Boundary comparison is inverted.
- [x] Duplicate event breaks idempotency.
- [x] Public contract breaks one consumer.
- [x] Authorization allows a forbidden tenant.
- [x] Reviewer raises a plausible-sounding non-issue that adjudication must reject.
- [x] Essential service is unavailable, requiring `INCONCLUSIVE`.
- [x] Correct low-risk change passes without unnecessary reviewers.

Evaluate outcomes and reasoning, not exact wording. Record false negatives, false positives, over-severity, unnecessary reviewer selection, and context leakage.

## Milestone 3: Portability checks

- [ ] Cursor discovery and `/verify` invocation.
- [ ] Codex discovery and `$verify` invocation.
- [ ] OpenCode discovery and wrapper invocation.
- [ ] Confirm reviewers receive clean context on each target host.
- [x] Confirm depth-one and read-only constraints in ChatGPT Work.

## Milestone 4: Distribution

- [x] Choose a license. (MIT — see `LICENSE`.)
- [x] Decide standalone-skill versus plugin release packaging. (Standalone Agent Skill at `.agents/skills/verify`, with a thin OpenCode adapter. Marketplace packaging deferred until portability gates pass.)
- [x] Add installation instructions with explicit untested-host boundaries.
- [x] Add versioning and release criteria.
- [ ] Publish only after behavioral fixtures pass on at least two hosts.

## MVP gate

Satisfied on 2026-09-04 in ChatGPT Work:

- [x] Derive a correct contract from an explicit task.
- [x] Select a bounded, relevant panel.
- [x] Keep reviewer contexts independent in an end-to-end panel run.
- [x] Reject a seeded speculative finding.
- [x] Catch seeded acceptance, bogus-test, regression, invariant, and authorization defects.
- [x] Distinguish `FIX REQUIRED` from `INCONCLUSIVE`.
- [x] Leave target source unchanged.

Portable release still requires successful Cursor and OpenCode runs plus a license decision.
