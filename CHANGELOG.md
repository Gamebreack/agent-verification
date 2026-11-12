# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html); see CONTRIBUTING.md (Releasing).

## [Unreleased]

### Changed
- **Adjudication re-derives mechanisms from evidence:** the gate no longer takes a reviewer's stated mechanism on trust. It re-derives it from the evidence alone (shared-premise test; a caller echo or a weak test is not a mechanism).
- **Test-strength rule:** a wrong test is a defect; a test the contract names but that is absent is MISSING; a mocked test on broken code counts as merged evidence; a weak test on correct code is a NON_ISSUE.
- **Invariants trigger guard in panel selection:** a numeric parameter, format width or input-type statement is no longer an invariants trigger by itself; the trigger is a range, boundary, ordering or state rule the contract requires. A trivial pure formatter now gets exactly the acceptance and tests reviewers.

### Added
- **Cross-host behavioral eval records:** all 12 fixtures run headless on OpenCode (11/12) and Antigravity (10/12), with no false negatives on either host, plus Claude Code reruns after the adjudication and trigger changes. Records are under `evals/runs/` and summarized in `docs/evaluation.md`.

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

[Unreleased]: https://github.com/Gamebreack/agent-verification/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/Gamebreack/agent-verification/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Gamebreack/agent-verification/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Gamebreack/agent-verification/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Gamebreack/agent-verification/releases/tag/v0.1.0
