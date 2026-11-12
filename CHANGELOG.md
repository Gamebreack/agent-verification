# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html); see CONTRIBUTING.md (Releasing).

## [Unreleased]

## [0.5.0] - 2026-11-11

Adds the review lifecycle to the verify skill (re-check loop, fixed report header, evidence labelling, branch-aware targets), tightens adjudication, and records behavioral runs on two hosts.

### Changed
- **Adjudication re-derives mechanisms from evidence:** the gate no longer takes a reviewer's stated mechanism on trust. It re-derives it from the evidence alone (shared-premise test; a caller echo or a weak test is not a mechanism).
- **Test-strength rule:** a wrong test is a defect; a test the contract names but that is absent is MISSING; a mocked test on broken code counts as merged evidence; a weak test on correct code is a NON_ISSUE.
- **Invariants trigger guard in panel selection:** a numeric parameter, format width or input-type statement is no longer an invariants trigger by itself; the trigger is a range, boundary, ordering or state rule the contract requires. A trivial pure formatter now gets exactly the acceptance and tests reviewers.
- **Branch-aware default target:** with no target given, the default is the branch against its merge base plus the working tree (including untracked files) when the branch has commits not on its base, otherwise the working-tree diff, or the branch against its merge base if the tree is clean. The base comes from the invocation or repository instructions, then `origin/HEAD`, then local `main` or `master`; with no base the target is the working-tree diff only. A target may also be a commit, range, branch, explicit file set, plan or design document, or a pull request when named. The report's Scope states what was covered and not covered (staged content that differs from the working tree is not reviewed).
- **Verdict and severity discipline:** the verdict follows from the validated findings; a severity may be downgraded only with stated evidence, and an unmet contract premise is reported rather than silently absorbed.
- **Reviewer briefs are clean:** reviewers get only the contract, the diff and their role; the contract is immutable once reviewers start, and a reviewer's `Out of mandate:` note is either adjudicated like any claim or listed under Open leads, never dropped.

### Added
- **`flow-map.md`:** the runtime flow of the skill (target resolution to report and the re-check loop) as three Mermaid diagrams; the single home of the flow diagram, linked from `docs/architecture.md`.
- **Re-check loop:** after fixes, a re-check re-runs the roles against prior findings; it is eligible only when a prior `FIX REQUIRED` report is available and its contract source is unchanged (a `--contract` file matched by blob hash, or a conversation that still contains the prior contract); otherwise a full verification runs. It records each prior finding's resolution with evidence, new defects, and the unresolved set; it has explicit stop and no-ship rules, including optional-only and unfixed-outside-delta cases.
- **Fixed report header:** every report opens with the same header: Verdict, Target, Assurance, Evidence (executed vs static), Scope, and Verified state.
- **Executed vs static evidence:** each piece of evidence is labelled executed or static; a capability check records whether reviewers could run anything (no reviewer shell), and a green-claim is not accepted without executed evidence.
- **Security retention and quick escalation:** at the panel bound a triggered security role is never the one omitted (it displaces the lowest-risk triggered specialist), and a quick-mode run with a security trigger or a high or critical surface escalates to `panel`.
- **Unresolved findings stay open:** a prior finding re-confirmed `unresolved` is re-emitted with its original id, claim, location and severity; prior `OPTIONAL` findings carry forward as notes.
- **Plan and document targets**, and a `verified_state` field recording what exactly was verified.
- **Harness layers, state guard and guards:** the harness scores in layers, guards against a changed source state, and adds checks for the new report fields.
- **16 new fixtures** (28 in total) covering the above.
- **v0.5 behavioral runs on two hosts (all 28 fixtures, no false negatives):** OpenCode 24/28 raw, 26/28 corrected, 27/28 after a `duplicate-event` re-run; Claude Code 25/28 raw, 27/28 corrected. Records are [`evals/runs/2026-11-11-opencode.json`](evals/runs/2026-11-11-opencode.json) and [`evals/runs/2026-11-11-claude-code.json`](evals/runs/2026-11-11-claude-code.json).
- **Cross-host behavioral eval records:** all 12 fixtures run headless on OpenCode (11/12) and Antigravity (10/12), with no false negatives on either host, plus Claude Code reruns after the adjudication and trigger changes. Records are under `evals/runs/` and summarized in `docs/evaluation.md`.

### Fixed
- **Scorer resolves criterion-id links:** a finding linked to a criterion id (for example A1) is now resolved through the criteria text, as the schema already allowed.
- **acceptance-omission fixture** accepts R1 or R2 as the violated requirement.
- **`json-report.md` wording:** untracked caches (such as `__pycache__`) do not make `source_unchanged` false.

## [0.4.0] - 2026-09-27

Simplifies the verify skill and makes it host-agnostic. The v0.3 incremental machinery is removed.

### Added
- **`--contract <path>` input** and a per-criterion PASS/FAIL report table.
- **`.claude/skills/verify` symlink** so Claude Code finds the skill in the repo.
- **Harness digest check:** `check` re-materializes the reference tree and compares digests; mode reviewer bounds are validated.

### Changed
- **Three modes (`quick`, `panel`, `release`) and five roles** (acceptance, tests, regression, security, invariants), in four reference files; no host, agent or model names anywhere in the skill, and one home per rule.
- **Fixtures remapped** to the new roles (12 fixtures, 12 unit tests).
- **README and docs** state structural and behavioral evidence honestly: v0.4 was not yet behaviorally evaluated at release.

### Removed
- **v0.3 incremental re-verification, state persistence and assurance-boundary targets**, with their five fixtures.
- **Vendor metadata file** (`agents/openai.yaml`).

## [0.3.0] - 2026-09-08

### Added
- **Incremental re-verification:** a prior verdict can be reused for an unchanged delta, with an invalidation map choosing which reviewers re-run.
- **State persistence:** a `.verify/state.json` file records the prior result and the target identity; identity drift refuses incremental mode.
- **Assurance-boundary targets** (`feature`, `subsystem`, `workflow`, `artifact`) with a target identity in the verification contract.
- **Five v0.3 behavioral fixtures** covering empty-delta reuse, identity drift and related cases.

## [0.2.0] - 2026-09-05

### Added
- **Staged escalation in panel selection:** a baseline of acceptance and test-adequacy reviewers, strict surface and risk triggers, a hard cap of five reviewers, and removal of irrelevant defaults, with INCONCLUSIVE preferred over an invented panel.
- **Reviewer efficiency contract:** shared method constraints (no general repo review, no rediscovery, batched inspection, stop when sufficient) and output discipline (one finding per claim, cited evidence, NO FINDINGS over invented ones), linked from every reviewer mandate.
- **Panel validation** before the adjudication gate: unjustified selections are rejected, and over-selection or a missing baseline is reported as OPTIONAL.
- **Three v0.2 behavioral fixtures** for panel size: a pure formatter, retry idempotency, and a multi-trigger change bounded at five reviewers.

## [0.1.0] - 2026-09-04

First tagged release: the verify skill as a portable Agent Skill, with a validation harness.

### Added
- **`verify` skill** (`.agents/skills/verify`): a panel of independent reviewers (eleven reviewer mandates), a verification contract, an evidence-gated adjudication, and a JSON report format.
- **OpenCode `/verify` command** as a thin adapter.
- **Eval harness** (`scripts/eval_harness.py`) with nine behavioral fixtures, unit tests and a GitHub Actions validation workflow.
- **Docs:** README, architecture, installation and evaluation, plus the first recorded run.

[Unreleased]: https://github.com/Gamebreack/agent-verification/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/Gamebreack/agent-verification/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/Gamebreack/agent-verification/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Gamebreack/agent-verification/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Gamebreack/agent-verification/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Gamebreack/agent-verification/releases/tag/v0.1.0
