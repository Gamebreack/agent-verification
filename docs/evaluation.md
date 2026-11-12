# Behavioral Evaluation

The evaluation corpus tests decisions, not prose. Each case contains an authoritative task, a baseline snapshot, a candidate change, and semantic expectations for the verdict, panel, findings, and evidence gaps.

## Validate the package

```bash
python3 scripts/eval_harness.py validate
```

It checks, without a model:

- the skill package: required files, no stale reference files, a host-agnostic denylist (host, agent-type, and model names, matched case-insensitively on word boundaries in every file under `.agents/skills/verify/`), and line budgets (`SKILL.md` at most 110 lines, reference files under 200, role files at most 30);
- every manifest against the keys in [Manifest keys](#manifest-keys);
- each case as a real Git repository: every layer materializes; a target is present (a non-empty `git status --porcelain`, which counts untracked files, or branch commits, or an existing artifact target); and the candidate's tests pass or fail as `test_expectation` declares, leaving the source unchanged.

On success it prints `PASS: skill package and N behavioral cases are structurally valid`.

Passing fixture tests are deliberately insufficient: most defective candidates have green tests. **This command proves the harness and fixtures are structurally consistent. It does not prove the skill behaves correctly — that requires a model host.**

## Run a behavioral case

```bash
tmpdir="$(mktemp -d)"
python3 scripts/eval_harness.py prepare acceptance-omission "$tmpdir/repo"
```

The command creates a real Git working tree and prints a clean-context invocation prompt (including the `--contract` path). Give that prompt to a host with the `verify` skill installed. Save its JSON output, then score it against the same repository directory:

```bash
python3 scripts/eval_harness.py check acceptance-omission report.json "$tmpdir/repo"
```

`check` independently re-applies every layer the case defines (base, branch commits, previous, staged, candidate, then artifact files, in that order) into a fresh scratch directory, computes a content digest of that reference tree, and compares it against a digest of `$tmpdir/repo`. It never trusts anything stored inside the checked repository itself (for example a `.verify-eval/digest` file), since a verifier with write access could edit or delete such a file to hide a mutation. A digest mismatch — including an untracked extra file — fails immediately with a clear "source changed" error; a report cannot claim `source_unchanged: true` over a repository that was actually mutated. `check` also fails when `.verify-eval/task.md` differs from the case task, so an edited contract cannot pass. It also requires a `--contract` source's `contract_summary.source_hash` to equal the blob id of `.verify-eval/task.md`.

`check` guards repository state too, again against a fresh reference materialization: a change to the git index, to `HEAD` (compared through its history, ref name, and reflog, since commit ids carry timestamps), or to an injected `.verify-eval/` artifact fails with "verification cannot be trusted". In a re-check, the injected prior report must carry the repository's own `HEAD` as its recorded head.

`check` then requires `report.source_unchanged` to be `true` and scores the report's semantic properties:

- the verdict;
- report consistency, for every case: the v0.5 keys (`verified_state`, `recheck`, `out_of_mandate`, `checks_not_run`, `effective_mode`) are present; no `PASS` or `PASS WITH NOTES` with an open validated `BLOCKER`/`SHOULD_FIX` or `MISSING` gap; a `FIX REQUIRED` next action names the re-check; reviewer-originated findings carry `proposed_severity`; each severity change has a reason (`rejection_reason` for `NON_ISSUE`); out-of-mandate dispositions and `checks_executed` `execution` values are valid, and each check has a `run_by`; `scope.covered` is non-empty; `contract_summary.source_of_truth` is a non-empty string, every `criteria` entry carries its id and full `text`; no `PASS` or `PASS WITH NOTES` while any prior finding is marked `unresolved` in `recheck.prior_findings`;
- effective mode, required, exact, and forbidden reviewers, and the panel bound (`max_reviewers`, defaulting to the effective mode's maximum);
- semantic findings, matched on `id`, status, linked requirement or invariant, severity, `proposed_severities`, evidence paths, and narrative terms; an expected `id` pins a re-emitted or carried-forward prior finding, such as a validated `OPTIONAL` note, to its original id;
- per-criterion results, evidence-gap kinds, and required checks;
- out-of-mandate terms, `scope_not_covered_terms`, and `next_action_or_gap_terms` (in `minimum_next_action` or an evidence gap);
- re-check: `recheck` is `null` without a prior report, or when the prior report is not eligible (not `FIX REQUIRED`, no `verified_state`, or a `contract_summary.source_hash` that differs from the contract file's blob id; the path is never compared); with an eligible one, every open prior finding (a validated `BLOCKER`/`SHOULD_FIX`, or one an earlier re-check left `unresolved`) is listed with a `resolution` and non-empty evidence, the unresolved set equals `expected.recheck_unresolved`, and `recheck.roles` and `another_round_required` match. Roles must include `recheck_roles` and may add only `recheck_optional_roles`;
- verified state: recorded blob ids match the working tree, `head` equals `HEAD`, and every target path is recorded. In a re-check the recorded files also cover the previous snapshot's paths and the files named by the evidence of each open prior finding. `verified_state: null` passes only for a commit, range, or pull-request target, and only when Scope says it was not recorded; any other target must record `{head, files}`.

The rules themselves live in the skill: [adjudication.md](../.agents/skills/verify/references/adjudication.md#re-check) and [json-report.md](../.agents/skills/verify/references/json-report.md#verified-state).

## Manifest keys

Top-level keys of `evals/cases/<id>/case.json`:

| Key | Meaning |
|---|---|
| `id`, `title`, `mode`, `task` | `id` matches the directory; `mode` is `quick`, `panel`, or `release`; `task` is written to `.verify-eval/task.md`, the contract the run must not change. |
| `test_expectation` | `pass`, `fail`, or `unavailable`: whether the candidate's tests must pass or fail during `validate`. |
| `branch_commits` | Snapshot directories committed in order on branch `feature` from the baseline; `main` stays at the baseline. The prompt then says "the default target". |
| `origin` | Exactly `{default: main, upstream: feature}`, only with `branch_commits`. Sets local remote-tracking refs and an unreachable remote, points `origin/HEAD` at `origin/main`, and deletes local `main`, so only the `origin/HEAD` rule resolves the base. |
| `previous` | Snapshot committed after the branch commits as the verified state. |
| `staged` | Snapshot staged into the index before the candidate is applied. |
| `target` | `{kind: artifact, path}` for a plan or design document; the prompt names the artifact. |
| `reviewer_capability` | `no-shell`: the prompt states that reviewers cannot execute commands. |
| `handoff_note` | Written to `.verify-eval/handoff.md`; the prompt calls it the implementer's note. |
| `seeded_reviewer_claim` | Written to `.verify-eval/reviewer-claim.md` for the lead to adjudicate. |
| `prior_report` | A `FIX REQUIRED` report written to `.verify-eval/prior-report.json`, with `verified_state` set to the `previous` commit and its blob ids. Requires `previous`, a `--contract` `contract_summary.source_hash`, and `criteria` with full text. The prompt only says the report is supplied; eligibility is the verifier's call. With any re-check expectation, `validate` requires the prior to be eligible (its `source_hash` is the materialized `task.md` blob id) and every open prior finding to name an existing file in its evidence. |

Keys under `expected`:

| Key | Meaning |
|---|---|
| `verdict` | One of the four verdict words. |
| `effective_mode` | The report's expected `effective_mode`; defaults to `mode` and sets the default panel bound. |
| `required_reviewers`, `exact_reviewers`, `forbidden_reviewers` | Roles the report must include, must equal, or must not include. |
| `max_reviewers` | Panel bound; may not exceed the effective mode's maximum. |
| `criteria` | Map of criterion id to `PASS`, `FAIL`, or `UNAVAILABLE`. |
| `evidence_gap_kinds` | Gap kinds the report must contain (`MISSING`, `UNAVAILABLE`). |
| `findings` | Matchers with optional `name` (display), `id` (in a re-check case, must name a prior finding), `status` (default `VALIDATED`), `requirement_or_invariant`, `severities`, `proposed_severities`, `evidence_paths`, and `terms_any`. |
| `checks` | Required `checks_executed` entries: `execution` (required), `run_by` and `command_terms` (optional). |
| `out_of_mandate_terms` | Terms a note must name: a string (any valid disposition), or `{term, disposition}` requiring that exact disposition, `adjudicated` or `open_lead`. |
| `scope_not_covered_terms` | Terms `scope.not_covered` must name. |
| `next_action_or_gap_terms` | Terms `minimum_next_action` or an evidence gap must name. |
| `recheck_roles`, `recheck_optional_roles`, `recheck_unresolved`, `another_round_required` | Re-check expectations, each requiring `prior_report`. `recheck_roles` must all appear; `recheck_optional_roles` lists the only extra roles tolerated; `recheck_unresolved` names open prior findings. |

## v0.5 fixtures

- Target and base: `v0.5-branch-commits`, `v0.5-base-origin-head`, `v0.5-plan-artifact`, `v0.5-staged-differs`.
- Verdicts and adjudication: `v0.5-severity-downgrade`, `v0.5-out-of-mandate-lead`, `v0.5-contract-premise-false`, `v0.5-code-claims-contract-outdated`.
- Execution and evidence: `v0.5-no-shell-reviewers`, `v0.5-green-claim-false`.
- Panel bounds and escalation: `v0.5-security-retained`, `v0.5-quick-security-escalation`.
- Re-check: `v0.5-recheck-fixed`, `v0.5-recheck-new-defect`, `v0.5-recheck-optional-only`, `v0.5-recheck-unfixed-outside-delta`.

### Re-check limitation

The four re-check fixtures supply a `previous` snapshot and a `prior_report`, so the run is scored as a re-check: open prior findings, their resolutions and evidence, the roles, the unresolved set, and `another_round_required`, all checked against the supplied report.

**Limitation:** these fixtures supply the prior report; they do not test a live multi-turn loop. No fixture drives successive invocations, carries the verified state between them, or checks that a re-check follows a commit. The runtime re-check loop is not drawn anywhere yet: `flow-map.md` does not exist, so the `repo-structure-and-release` change must include the re-check loop in its task 7.2.

## Assurance boundary

Structural validation is deterministic and covers all 12 fixtures without a model. Behavioral evaluation requires a model host because the artifact being tested is an Agent Skill. Results must record whether reviewers actually received independent contexts; a report created without subagents must say `degraded independence`.

Record the host/model/version with retained evaluation reports so regressions can be compared honestly. The latest retained run is [`evals/runs/2026-09-28-claude-code.json`](../evals/runs/2026-09-28-claude-code.json) (skill v0.4.0, 12 cases, host Claude Code; per-case reports alongside it under `evals/runs/2026-09-28-claude-code/`). The prior run, [`evals/runs/2026-09-04-chatgpt-work.json`](../evals/runs/2026-09-04-chatgpt-work.json) (skill v0.1.0, 9 cases, host ChatGPT Work), is kept as history.

The 2026-09-28 run matched 10 of 12 expected verdicts with zero false negatives. Both mismatches were over-strict: `v0.2-retry-idempotency` and `v0.2-multi-trigger-bounded` returned `PASS WITH NOTES` where `PASS` was expected, each on OPTIONAL test-strength findings against otherwise-correct code. The multi-trigger case also surfaced a lead adjudication error — a BLOCKER validated on four-reviewer agreement was later withdrawn because the claimed disclosure was a caller-supplied argument, not internal state; the corrected report is retained alongside the original and still checks `FAIL` (over-strict) against the expected `PASS`. After the adjudication-policy fix, a 5-case rerun of the three mismatched cases plus two defect cases matched 5/5 — see [`evals/runs/2026-09-28-claude-code-rerun.json`](../evals/runs/2026-09-28-claude-code-rerun.json).

Cross-host runs on 2026-09-28: OpenCode 11/12 and Antigravity 10/12, both with zero false negatives — see [`evals/runs/2026-09-28-opencode.json`](../evals/runs/2026-09-28-opencode.json) and [`evals/runs/2026-09-28-antigravity.json`](../evals/runs/2026-09-28-antigravity.json). Both mismatches on `v0.2-pure-formatter-no-overflow` are the same over-inclusive reviewer selection; Antigravity's `duplicate-event` mismatch is a finding-vocabulary miss with the defect detected.

After the invariants-trigger guard, `v0.2-pure-formatter-no-overflow` re-run on all three hosts selected exactly acceptance + tests, 3/3 — see [`evals/runs/2026-09-28-item05-rerun.json`](../evals/runs/2026-09-28-item05-rerun.json).
