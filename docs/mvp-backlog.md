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

- [x] Cursor discovery and `/verify` invocation.
- [x] Codex discovery and `$verify` invocation.
- [x] OpenCode discovery and wrapper invocation.
- [x] Antigravity skill discovery and `/verify` slash-command surface in interactive TUI (per [official docs](https://antigravity.google/docs/cli/plugins/)).
- [ ] Confirm reviewers receive clean context on each target host.
- [ ] End-to-end `/verify quick <fixture>` on at least two hosts (closes the portable release gate).
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

Portable release still requires end-to-end `/verify` runs on seeded fixtures on at least two hosts. License decided (MIT).

## Milestone 5: Incremental re-verification (v0.3)

Separate TARGET (user's assurance boundary) from DELTA (changes since last verify). Incremental re-verification may shrink what evidence is recollected; it must NEVER silently narrow TARGET to the latest commit.

- [x] Extend `target.kind` enum with `feature | subsystem | workflow | artifact | files`.
- [x] Add `target.identity` block (description, in_scope, out_of_scope, anchor, acceptance_criteria).
- [x] Per-kind resolution rules in SKILL.md §1.
- [x] Invocation grammar supports `feature:<name>`, `subsystem:<name>`, `workflow:<name>`, `artifact:<name>`.
- [x] State persistence schema (`.verify/state.json`) — opt-in, target-local, host-wrapped save.
- [x] Incremental verification reference (delta computation, invalidation map, identity drift handling).
- [x] Scope-preservation guard: adjudicator rejects reviewer output that narrows TARGET (`out-of-target-narrowing`).
- [x] Behavioral fixtures: `v0.3-target-preserved-on-validation-fix`, `v0.3-invalidation-expands-on-grown-scope`, `v0.3-identity-drift-inconclusive`, `v0.3-empty-delta-reuses-verdict`, `v0.3-reviewer-scope-narrowing-rejected`.
- [x] Corpus grew from 12 to 17 cases; all structurally valid; 5/5 unittests OK.
- [ ] Cross-host reruns of v0.2 fixtures on Codex + Cursor (no regression).
- [ ] Cross-host reruns of v0.3 fixtures on Codex + Cursor.

## v0.3 gate

- [x] 9 v0.2 fixtures still pass structurally; no FP/FN regression.
- [x] 5 new v0.3 fixtures structurally valid.
- [x] Adjudicator rejects `out-of-target-narrowing` scope_relevance.
- [x] State persistence is opt-in and host-wrapped; skill remains read-only.
