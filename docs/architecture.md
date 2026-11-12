# Architecture

## Decision

Build one canonical Agent Skill at `.agents/skills/verify`. Keep the orchestration policy in `SKILL.md`, detailed contracts in shared references, and each reviewer mandate in its own role file. There is no custom runtime; the verification lead uses the host's native subagent capability.

The runtime flow, from target resolution through the report and the re-check loop, is drawn in [`flow-map.md`](../flow-map.md).

## Modes

`quick` (one reviewer context carrying both the acceptance and tests roles; max roles 2), `panel` (default; baseline: acceptance + tests; max roles 4), `release` (baseline: acceptance + tests + regression; max roles 5). Surface triggers and risk bands select any additional roles up to the mode's maximum; see [`references/panel.md`](../.agents/skills/verify/references/panel.md).

Security retention: a triggered security role is never the one omitted at the bound; it displaces the lowest-risk triggered specialist. A security trigger in `quick` mode escalates the run to `panel` and says so.

## Reviewer roles

Exactly five: `acceptance`, `tests`, `regression`, `invariants`, `security`. Each role runs as one reviewer; a role is never split across reviewers.

## The `--contract` file

An optional human-editable file (for example a work-item or issue export) holding the task statement, acceptance criteria, and non-goals. When supplied it outranks every other intent source and its acceptance-criterion ids are preserved verbatim into the report.

## Targets and scope

The default target is branch-aware: when the branch has commits not on its base, it is the branch against its merge base plus the working tree, including untracked files; otherwise the working-tree diff, or the branch against its merge base when the tree is clean. Other targets are a commit, range, branch, explicit file set, a pull request (only when named), or an artifact: a plan or design document, whose source of truth is the request it answers.

Base resolution is read-only and never fetches. The first rule that resolves wins: a base named by the invocation or repository instructions; `origin/HEAD` (never the current branch's `@{upstream}`); local `main`, then `master`; otherwise the working-tree diff only, stated in Scope. With no base and a clean tree, the target is empty and the report says that no base resolved and nothing was reviewed. Rules: [base resolution](../.agents/skills/verify/references/verification-contract.md#base-resolution) and [artifact targets](../.agents/skills/verify/references/verification-contract.md#artifact-targets).

Every report's Scope names what the target covered and what it excluded, including staged content that differs from the working tree.

## Report

Every markdown report opens with a fixed header, in this order, before `## Contract summary`: `# Verification: <VERDICT>`, `Target:`, `Assurance:`, `Evidence:`, `Scope:`, `Verified state:`. Blocking findings come first. Out-of-mandate notes are adjudicated or listed under Open leads, never dropped. The JSON form carries the same facts as named fields ([json-report.md](../.agents/skills/verify/references/json-report.md)).

Verdict discipline: only the four verdict words are used. `PASS` and `PASS WITH NOTES` are never issued while a validated `BLOCKER` or `SHOULD_FIX`, or any `MISSING` gap, is open. `FIX REQUIRED` and `INCONCLUSIVE` are never described as ready or passed. Full rules: [verdict discipline](../.agents/skills/verify/references/adjudication.md#verdict-discipline).

## Execution boundaries

- Maximum delegation depth: one. Reviewers never delegate or fix.
- The verification lead adjudicates; reviewer output never directly determines the verdict.
- Capability check: before dispatch, the lead determines whether reviewers can execute commands (unknown means cannot). If they cannot, the lead runs the narrow, read-only commands the required evidence names and records itself as the runner.
- Brief hygiene: a reviewer's brief holds the contract, the resolved target, its role files, the finding schema, an output budget, and any lead-run outputs with their exact commands. It never carries a claim that a check passed, that a review happened, or that a finding was fixed. A reviewer that cannot finish returns a partial report listing its unchecked items; the lead covers them or records them as `UNAVAILABLE`.
- Contract immutability: the `--contract` file and the completed Verification Contract are neither edited nor reinterpreted during a run. Code that differs from the contract is a finding; a conflict with repository reality leads to a question or `INCONCLUSIVE`.
- Existing project tools may be executed; the skill installs no new dependencies.
- The skill is read-only with respect to source, tests, configuration, and the `--contract` file.

## Host behavior

The same skill is discoverable by every compliant host from `.agents/skills` (or a host-specific symlink); see [Installation](installation.md) for the discovery table. Host-specific files may invoke or expose the canonical skill but must not duplicate its verification policy.

## Assurance degradation

If the host lacks subagents, the lead may run roles sequentially, but must label the report `degraded independence`. Essential unavailable evidence or materially ambiguous intent produces `INCONCLUSIVE`, not `PASS`.

## Evaluation architecture

`scripts/eval_harness.py` materializes each fixture as a real Git repository with a baseline commit and a candidate working-tree diff, plus any branch commits, previous, or staged layers the case names. `check` independently re-materializes every layer the case defines (base, branch commits, previous, staged, candidate, then artifact files, in that order) into a scratch directory and compares content digests, rather than trusting anything recorded inside the checked repository. A verifier report is then scored against semantic expectations — verdict, selected roles, evidence paths, defect concepts, and evidence gaps — rather than exact prose.
