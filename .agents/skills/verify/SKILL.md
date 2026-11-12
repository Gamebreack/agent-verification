---
name: verify
description: Independently verify an implemented software change against its original requirements using a small, risk-selected panel of fresh-context reviewers and evidence-gated adjudication. Use after implementation, before merge or release, or when tests may pass without proving correctness. Do not use for ordinary implementation, autonomous fixing, or style-only review.
---

# Verify

Determine whether a software change is justified by relevant, trustworthy evidence. Treat passing tests and reviewer claims as evidence to inspect, not proof.

## Invocation

```text
verify [quick|panel|release] [target] [--contract <path>] [--report markdown|json]
```

- Mode: default `panel`. Modes are defined in [references/panel.md](references/panel.md).
- Target: the default is branch-aware. When the branch has commits not on its base, it is the branch against its merge base plus the working tree, including untracked files; otherwise the working-tree diff, or, if that is clean, the branch against its merge base. A target may also be a commit, a range, a branch, a pull request (only when named), an explicit file set, or a plan or design document (an artifact target). Base resolution, artifact targets, and the Scope statement: [references/verification-contract.md](references/verification-contract.md#base-resolution).
- `--contract <path>`: a markdown or text file (for example a work-item file) holding the task statement, acceptance criteria, and non-goals. When supplied, it is the authoritative source of truth and outranks every other intent source.
- Report: default `markdown`. For `json`, follow [references/json-report.md](references/json-report.md) and return only that object.
- Never guess a destructive or remote target. Resolve every target read-only before analysis.

## Hard constraints

- Remain read-only with respect to source, tests, configuration, dependencies, and external systems. Never write any file, including the `--contract` file. Read-only covers intent: never edit or reinterpret the `--contract` file or the completed Verification Contract during a run. Code that differs from the contract is a finding; if the contract conflicts with repository reality, ask or return `INCONCLUSIVE`.
- Caches, coverage files, and reports are acceptable only when produced by existing project commands and left untracked. Do not add packages or configuration.
- Use at most one delegation level. Reviewers never delegate.
- Reviewers find claims; the lead adjudicates them.
- Keep implementation reasoning away from reviewers unless it is itself part of the requirement, and never pass on a claim that checks passed, that a review happened, or that a finding was fixed.
- Reviewer count, agreement, and confidence are not evidence.
- Prefer the smallest existing project command that establishes the needed behavior. Do not run broad, costly, or production-affecting checks when narrower evidence suffices.
- Do not fix the change. Report; never repair.

## Workflow

### 1. Resolve the target and the source of truth

Inspect repository instructions and resolve the exact diff, file set, or artifact. Determine intent from the first available source, in order:

0. the `--contract` file, when supplied (outranks everything below);
1. requirements explicitly supplied with the invocation;
2. a linked issue, specification, accepted plan, or pull-request description;
3. task text available in the current conversation;
4. repository documentation and observable pre-change behavior.

Never infer intent from the implementation. If missing intent could materially change the verdict, ask for it or return `INCONCLUSIVE`.

### 2. Build the Verification Contract

Follow [references/verification-contract.md](references/verification-contract.md). Complete the contract before selecting reviewers.

### 3. Select the panel

Follow [references/panel.md](references/panel.md). It is the only source for mode baselines, surface triggers, risk bands, panel bounds, and selection justification.

### 4. Dispatch reviewers in fresh contexts

Capability check: before dispatch, determine whether reviewers can run commands; if unknown, assume they cannot. If they cannot, run the narrow, read-only existing project commands the required evidence names, and record the lead as their runner.

Run each selected role as a reviewer in a fresh context, concurrently when the host allows. Give each reviewer only:

- the Verification Contract;
- the resolved target and read access to the repository;
- its role file(s) under `references/reviewers/`;
- the finding schema from [references/adjudication.md](references/adjudication.md);
- an output budget;
- any lead-run command outputs, each with its exact command;
- in a re-check, its open prior findings (step 7).

Instruct every reviewer:

- Inspect only the surfaces relevant to your mandate; stop once it is established or refuted.
- Cite `file:line` or the command you ran and its result for every claim.
- Report one falsifiable claim per finding, with a `trigger -> behavior -> impact` chain.
- Do not edit, fix, propose patches, or delegate.
- You may run existing read-only analysis and test commands.
- Treat the Verification Contract as the source of truth for intent.
- Return `NO FINDINGS` rather than invent concerns.
- If you notice something outside your mandate, add a one-line `Out of mandate:` note and do not investigate it.
- Stay within your output budget: findings first, one block per claim, no narrative. If you cannot finish, return a partial report listing what you checked and what remains unchecked.

If the host cannot provide fresh contexts, run the roles sequentially with strict role boundaries and report `Assurance: degraded independence`. Do not imply independent review occurred.

### 5. Adjudicate

Follow [references/adjudication.md](references/adjudication.md). Validate every claim against evidence, mechanism, contract relevance, materiality, and counter-evidence; merge duplicates by root cause. The lead may inspect more context or run one narrow confirming command. `Out of mandate:` notes are leads for the lead, not findings, until adjudicated with evidence. Cover each item a partial report left unchecked, or record it as an `UNAVAILABLE` evidence gap.

### 6. Report

Return exactly one verdict — `PASS`, `PASS WITH NOTES`, `FIX REQUIRED`, or `INCONCLUSIVE` — using the report template in [references/adjudication.md](references/adjudication.md), opening with its fixed header, or the JSON object when requested.

Do not claim the change is bug-free; report what the evidence establishes.

### 7. Re-check after FIX REQUIRED

Re-check only when eligible ([references/adjudication.md](references/adjudication.md#re-check)); otherwise run a full verification.

- Dispatch fresh contexts; never resume a prior reviewer.
- Brief every open prior finding to the reviewer whose mandate covers it as claim, evidence, and location, without its severity or verdict label.
- Panel: [references/panel.md](references/panel.md#re-check-panel). Contract, target, re-confirmation, stop rule, and no-ship rule: [references/adjudication.md](references/adjudication.md#re-check).

## Reviewer roles

Load only the selected roles:

- [Acceptance](references/reviewers/acceptance.md) — every requested behavior is present and complete.
- [Tests](references/reviewers/tests.md) — the tests would actually catch a broken implementation.
- [Regression](references/reviewers/regression.md) — preserved behavior and consumers of changed interfaces.
- [Invariants](references/reviewers/invariants.md) — boundaries, ordering, state transitions, and failure paths.
- [Security](references/reviewers/security.md) — authorization, isolation, secrets, and trust boundaries.
