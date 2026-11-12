import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts import eval_harness


def text_blob_id(text: str) -> str:
    """The git blob id of `text` (what `git hash-object` prints for a file holding it)."""
    data = text.encode("utf-8")
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def skill_copy(tmp: str) -> Path:
    """A temporary copy of the current verify skill directory."""
    copy = Path(tmp) / "verify"
    shutil.copytree(eval_harness.SKILL_DIR, copy)
    return copy


def pad_to(path: Path, lines: int) -> None:
    """Rewrite `path` so it has exactly `lines` lines, keeping its leading text."""
    existing = path.read_text(encoding="utf-8").splitlines()[:lines]
    existing += ["filler"] * (lines - len(existing))
    path.write_text("\n".join(existing) + "\n", encoding="utf-8")


class SkillPackageGuardTest(unittest.TestCase):
    def test_current_skill_passes_every_package_guard(self) -> None:
        self.assertEqual(eval_harness.skill_package_errors(eval_harness.SKILL_DIR), [])

    def test_denylisted_term_in_skill_text_fails_validation(self) -> None:
        for term in ("Claude", "OPENAI", "gpt-4o", "general-purpose", "Sonnet"):
            with self.subTest(term=term), tempfile.TemporaryDirectory() as tmp:
                skill = skill_copy(tmp)
                target = skill / "references" / "panel.md"
                target.write_text(
                    target.read_text(encoding="utf-8") + f"\nDispatch with the {term} reviewer.\n",
                    encoding="utf-8",
                )
                errors = eval_harness.skill_package_errors(skill)
                self.assertTrue(any("host-specific" in error and "panel.md" in error for error in errors), errors)

    def test_denylist_matches_whole_words_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = skill_copy(tmp)
            target = skill / "SKILL.md"
            # Edit in place so the line count, and hence the size budget, is unchanged.
            lines = target.read_text(encoding="utf-8").splitlines()
            lines[-1] += " A magnum-opusculum of gptools and claudette."
            target.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.assertEqual(eval_harness.skill_package_errors(skill), [])

    def test_denylisted_file_name_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = skill_copy(tmp)
            (skill / "agents").mkdir()
            (skill / "agents" / "openai.yaml").write_text("name: verify\n", encoding="utf-8")
            errors = eval_harness.skill_package_errors(skill)
            self.assertTrue(any("host-specific" in error and "openai.yaml" in error for error in errors), errors)

    def test_validate_package_reports_denylisted_term(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = skill_copy(tmp)
            target = skill / "SKILL.md"
            target.write_text(target.read_text(encoding="utf-8") + "\nRun as a Codex agent.\n", encoding="utf-8")
            with patch.object(eval_harness, "SKILL_DIR", skill), patch.object(
                eval_harness, "case_ids", return_value=[]
            ):
                with self.assertRaises(eval_harness.EvaluationError) as ctx:
                    eval_harness.validate_package()
            self.assertIn("host-specific term(s) ['codex']", str(ctx.exception))

    def test_reference_file_must_have_fewer_than_200_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = skill_copy(tmp)
            target = skill / "references" / "adjudication.md"
            pad_to(target, 199)
            self.assertEqual(eval_harness.skill_package_errors(skill), [])
            pad_to(target, 200)
            errors = eval_harness.skill_package_errors(skill)
            self.assertTrue(any("adjudication.md has 200 lines" in error for error in errors), errors)

    def test_role_file_must_have_at_most_30_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = skill_copy(tmp)
            target = skill / "references" / "reviewers" / "tests.md"
            pad_to(target, 30)
            self.assertEqual(eval_harness.skill_package_errors(skill), [])
            pad_to(target, 31)
            errors = eval_harness.skill_package_errors(skill)
            self.assertTrue(any("tests.md has 31 lines" in error and "at most 30" in error for error in errors), errors)

    def test_skill_file_must_have_at_most_110_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = skill_copy(tmp)
            target = skill / "SKILL.md"
            pad_to(target, 110)
            self.assertEqual(eval_harness.skill_package_errors(skill), [])
            pad_to(target, 111)
            errors = eval_harness.skill_package_errors(skill)
            self.assertTrue(any("SKILL.md has 111 lines" in error for error in errors), errors)


LEAD_DUTIES_LINE = (
    "The lead adjudicates, reports with the verify header, and a FIX REQUIRED needs a re-check before shipping."
)
REVIEWER_ROLES = ("acceptance", "tests", "regression", "invariants", "security")


def skill_text(relative: str) -> str:
    """A skill file's text with whitespace collapsed, so phrases survive re-wrapping."""
    return " ".join((eval_harness.SKILL_DIR / relative).read_text(encoding="utf-8").split())


class SkillTextStructureTest(unittest.TestCase):
    """Structural checks for the v0.5 skill-text tasks (2.1, 2.2, 2.9, 3.1, 3.2, 4.1, 5.1, 5.2, 6.1, 6.2)."""

    def assert_phrases(self, relative: str, *phrases: str) -> str:
        text = skill_text(relative)
        for phrase in phrases:
            self.assertIn(phrase, text, f"{relative} lacks: {phrase}")
        return text

    def assert_in_order(self, text: str, *phrases: str) -> None:
        positions = [text.index(phrase) for phrase in phrases]
        self.assertEqual(positions, sorted(positions), f"out of order: {phrases}")

    def test_markdown_template_opens_with_the_fixed_header(self) -> None:  # 2.1
        raw = (eval_harness.SKILL_DIR / "references" / "adjudication.md").read_text(encoding="utf-8")
        template = raw[raw.index("```markdown"):]
        template = template[: template.index("```", len("```markdown"))]
        lines = [line for line in template.splitlines()[1:] if line.strip()]
        self.assertEqual(
            [line.split(":")[0] for line in lines[:7]],
            ["# Verification", "Target", "Assurance", "Evidence", "Scope", "Verified state", "## Contract summary"],
        )
        self.assertIn("independent panel | degraded independence", lines[2])
        self.assertIn("not run", lines[3])
        self.assertIn("not covered", lines[4])
        self.assertIn("aggregate hash", lines[5])
        self.assertIn("## Open leads", lines)
        self.assert_phrases("references/adjudication.md", "header first", "blocking findings first")

    def test_adjudication_states_verdict_discipline(self) -> None:  # 2.2
        text = self.assert_phrases(
            "references/adjudication.md",
            "Use only the four verdict words",
            "Never issue `PASS` or `PASS WITH NOTES` while a validated `BLOCKER` or `SHOULD_FIX`, or any `MISSING` gap, is open",
            "Never describe `FIX REQUIRED` or `INCONCLUSIVE` as ready",
            "`PASS`: no validated `BLOCKER` or `SHOULD_FIX`, no `MISSING` gap",
            "`FIX REQUIRED`: at least one validated `BLOCKER` or `SHOULD_FIX`, or any `MISSING` evidence gap",
            "record a one-line reason for the change; for a `NON_ISSUE`, its rejection reason is that reason",
            "either adjudicated",
            "listed under Open leads",
            "None is dropped",
        )
        self.assertNotIn("material `MISSING` evidence", text)
        self.assertLess(eval_harness.line_count(eval_harness.SKILL_DIR / "references" / "adjudication.md"), 200)

    def test_every_role_file_carries_the_lead_duties_line(self) -> None:  # 2.9
        for role in REVIEWER_ROLES:
            with self.subTest(role=role):
                path = eval_harness.SKILL_DIR / "references" / "reviewers" / f"{role}.md"
                lines = path.read_text(encoding="utf-8").splitlines()
                self.assertEqual(lines.count(LEAD_DUTIES_LINE), 1)
                self.assertLessEqual(len(lines), 30)

    def test_skill_states_capability_check_brief_hygiene_and_contract_immutability(self) -> None:  # 3.1
        text = self.assert_phrases(
            "SKILL.md",
            "Capability check: before dispatch, determine whether reviewers can run commands; if unknown, assume they cannot.",
            "run the narrow, read-only existing project commands the required evidence names, and record the lead as their runner",
            "an output budget;",
            "any lead-run command outputs, each with its exact command;",
            "never pass on a claim that checks passed, that a review happened, or that a finding was fixed",
            "partial report",
            "remains unchecked",
            "Cover each item a partial report left unchecked, or record it as an `UNAVAILABLE` evidence gap",
        )
        read_only = next(
            line for line in (eval_harness.SKILL_DIR / "SKILL.md").read_text(encoding="utf-8").splitlines()
            if line.startswith("- Remain read-only")
        )
        for phrase in (
            "never edit or reinterpret the `--contract` file or the completed Verification Contract during a run",
            "Code that differs from the contract is a finding",
            "ask or return `INCONCLUSIVE`",
        ):
            self.assertIn(phrase, read_only)
        self.assertNotIn("immutab", text.lower())
        self.assertLessEqual(eval_harness.line_count(eval_harness.SKILL_DIR / "SKILL.md"), eval_harness.SKILL_MAX_LINES)

    def test_tests_role_labels_unexecuted_conclusions_static(self) -> None:  # 3.2
        self.assert_phrases(
            "references/reviewers/tests.md",
            "Label every conclusion drawn from reading tests without executing them `static`",
        )
        self.assertLessEqual(
            eval_harness.line_count(eval_harness.SKILL_DIR / "references" / "reviewers" / "tests.md"), 30
        )

    def test_panel_retains_security_and_escalates_quick(self) -> None:  # 4.1
        self.assert_phrases(
            "references/panel.md",
            "a triggered security role is never the one omitted at the bound; it displaces the lowest-risk triggered specialist",
            "if `quick` is requested and a surface is `high` or `critical`, or the security trigger fires, run `panel`",
        )
        self.assertLess(eval_harness.line_count(eval_harness.SKILL_DIR / "references" / "panel.md"), 200)

    def test_invocation_names_the_branch_aware_default_and_artifact_targets(self) -> None:  # 5.1
        invocation = next(
            line for line in (eval_harness.SKILL_DIR / "SKILL.md").read_text(encoding="utf-8").splitlines()
            if line.startswith("- Target:")
        )
        for phrase in (
            "the default is branch-aware",
            "the branch against its merge base plus the working tree",
            "a pull request (only when named)",
            "a plan or design document (an artifact target)",
            "references/verification-contract.md#base-resolution",
        ):
            self.assertIn(phrase, invocation)

    def test_contract_reference_states_base_order_and_artifact_rules(self) -> None:  # 5.2
        text = self.assert_phrases(
            "references/verification-contract.md",
            "kind: working-tree | range | commit | branch | pull-request | files | artifact",
            "never fetch",
            "never the current branch's `@{upstream}`",
            "the Scope states that branch commits were not covered",
            "no base resolved and nothing was reviewed",
            "Source of truth: the request the document answers, not the document itself",
            "use the document's stated goals and record that under `ambiguities`",
            "staged content that differs from the working tree",
        )
        self.assert_in_order(
            text,
            "a base named by the invocation or by repository instructions",
            "`origin/HEAD`",
            "local `main`, else `master`",
            "no base: the target is the working-tree diff only",
        )
        self.assert_phrases(
            "references/reviewers/acceptance.md",
            "For an `artifact` target (a plan or design document)",
            "A false premise, a fail-open path, or an unmet requirement is a finding",
        )
        for relative in ("references/verification-contract.md", "references/reviewers/acceptance.md"):
            self.assertEqual(
                [error for error in eval_harness.skill_package_errors(eval_harness.SKILL_DIR) if relative in error], []
            )

    def test_skill_step_7_rechecks_after_fix_required(self) -> None:  # 6.1
        text = self.assert_phrases(
            "SKILL.md",
            "### 7. Re-check after FIX REQUIRED",
            "Re-check only when eligible",
            "references/adjudication.md#re-check",
            "otherwise run a full verification",
            "Dispatch fresh contexts; never resume a prior reviewer.",
            "Brief every open prior finding",
            "without its severity or verdict label",
            "references/panel.md#re-check-panel",
        )
        # Step 7 points to adjudication.md for eligibility instead of restating it.
        step_7 = text[text.index("### 7. Re-check after FIX REQUIRED"):text.index("## Reviewer roles")]
        self.assertNotIn("newest", step_7)
        self.assertNotIn("carrying `verified_state`", step_7)

    def test_recheck_rules_live_in_their_homes(self) -> None:  # 6.2
        self.assert_phrases(
            "references/panel.md",
            "its baseline roles: acceptance and tests, plus regression in `release`",
            "every specialist with an open validated `BLOCKER` or `SHOULD_FIX` in the prior report",
            "every role whose trigger the fix delta newly fires",
            "never from claims about what the fix addressed",
            "A role with an open prior finding is never omitted at the bound",
            "escalate the mode and say so; in `release`, return `INCONCLUSIVE`",
            "never displace a role with an open prior finding",
            "A `quick` re-check whose fix delta newly fires a specialist trigger escalates to `panel` and says so",
        )
        self.assert_phrases(
            "references/adjudication.md",
            # eligibility: both conditions, the newest prior report governs
            "a re-check only when both hold",
            "a prior `FIX REQUIRED` report for the same contract, carrying a `verified_state`",
            "the newest governs",
            "the prior Verification Contract's source is still available unchanged",
            "its current blob id (`git hash-object <file>`) equals the prior `contract_summary.source_hash`",
            "compared by hash, never by path",
            "the conversation still contains the prior contract",
            "reuse the prior report's contract summary and criteria together with the unchanged source; never rebuild",
            # delta and target
            "the commits since `verified_state.head`",
            "including new untracked files",
            "every recorded path whose current content differs from its recorded hash",
            "The same rules apply to every target kind",
            "the delta plus the file of every open validated `BLOCKER` or `SHOULD_FIX` in the prior report",
            # re-confirmation, re-emission, carry-forward
            "adjudicate each open prior finding `resolved` or `unresolved` with evidence",
            "Re-emit each `unresolved` finding among the validated findings with its original id",
            "stays open",
            "or while any re-confirmed prior finding is `unresolved`",
            "Prior validated `OPTIONAL` findings are not re-confirmed",
            "unless the target shows them addressed",
            "carry forward as notes",
            "with their original ids",
            # stop and no-ship rules
            "no new or unresolved validated `BLOCKER` or `SHOULD_FIX` and no `MISSING` gap",
            "`OPTIONAL` findings never open another round",
            "must not be committed, pushed, or described as verified until a re-check passes",
            "names the re-check: the roles to re-run and the verified state",
        )
        self.assert_phrases(
            "references/json-report.md",
            "`git hash-object <path>` (never with `-w`)",
            "`null` for a deleted path",
            "`null` when the repository has no commits",
            "the union of the prior `verified_state.files` paths, the delta's paths, and the files of open prior findings",
            "a re-emitted `unresolved` prior finding or a carried-forward `OPTIONAL` is a `findings` entry",
            "with `status: \"VALIDATED\"` and its original `id`",
            "`contract_summary.source_hash` is the `--contract` file's blob id",
            "`null` for any other source",
            "`criteria[].text` is that criterion's full text",
            "For a commit, range, or pull-request target",
            "record `verified_state: null`",
            "When staged content differs from the working tree, say so in the Scope",
            "`git hash-object --stdin` over the sorted `<blob> <path>` lines",
            "a deleted path's line is `null <path>`",
            "a property the committing agent or a harness can check, not a step of the run",
        )
        self.assertEqual(eval_harness.skill_package_errors(eval_harness.SKILL_DIR), [])

    def test_skill_links_and_anchors_resolve(self) -> None:
        def anchors(path: Path) -> set[str]:
            found = set()
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("#"):
                    title = line.lstrip("#").strip().lower()
                    found.add(re.sub(r"[^a-z0-9 _-]", "", title).replace(" ", "-"))
            return found

        for source in sorted(eval_harness.SKILL_DIR.rglob("*.md")):
            for target in re.findall(r"\]\(([^)\s]+)\)", source.read_text(encoding="utf-8")):
                if "://" in target:
                    continue
                with self.subTest(source=source.name, link=target):
                    file_part, _, anchor = target.partition("#")
                    resolved = (source.parent / file_part).resolve() if file_part else source
                    self.assertTrue(resolved.is_file(), f"{source.name}: missing {file_part}")
                    if anchor:
                        self.assertIn(anchor, anchors(resolved), f"{source.name}: missing anchor #{anchor}")


def write_case(cases_dir: Path, case_id: str, snapshots: dict[str, dict[str, str]], **manifest: object) -> None:
    """Write a synthetic case: `snapshots` maps a layer directory to {path: content}."""
    case_dir = cases_dir / case_id
    for layer, files in snapshots.items():
        (case_dir / layer).mkdir(parents=True, exist_ok=True)
        for relative, content in files.items():
            target = case_dir / layer / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    data = {
        "id": case_id,
        "title": case_id,
        "mode": "quick",
        "task": "R1: synthetic task.",
        "test_expectation": "unavailable",
        "expected": {"verdict": "PASS"},
        **manifest,
    }
    (case_dir / "case.json").write_text(json.dumps(data), encoding="utf-8")


def git(repo: Path, *args: str, check: bool = True) -> str:
    return eval_harness.run(["git", *args], repo, check=check).stdout.strip()


def valid_report(case_id: str, repo: Path, **overrides: object) -> dict:
    """A report satisfying every v0.5 consistency rule for `case_id`, with the
    verified state of the materialized `repo`'s target paths."""
    _, case = eval_harness.load_case(case_id)
    report = {
        "case_id": case_id,
        "verdict": case["expected"]["verdict"],
        "assurance": "independent panel",
        "requested_mode": case["mode"],
        "effective_mode": case["expected"].get("effective_mode", case["mode"]),
        "target": "working-tree diff",
        "scope": {"covered": ["working-tree diff"], "not_covered": ["pre-existing code outside the diff"]},
        "contract_summary": {"source_of_truth": "invocation"},
        "criteria": [],
        "selected_reviewers": ["acceptance", "tests"],
        "selection_reasons": {},
        "checks_executed": [],
        "checks_not_run": [],
        "findings": [],
        "out_of_mandate": [],
        "evidence_gaps": [],
        "verified_state": {
            "head": git(repo, "rev-parse", "HEAD"),
            "files": eval_harness.blob_ids(repo, eval_harness.target_paths(case, repo)),
        },
        "recheck": None,
        "source_unchanged": True,
        "minimum_next_action": "none",
    }
    report.update(overrides)
    return report


class SyntheticCaseTest(unittest.TestCase):
    """Base for tests over synthetic cases in a temporary CASES_DIR."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.cases_dir = self.tmp / "cases"
        patcher = patch.object(eval_harness, "CASES_DIR", self.cases_dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def materialize(self, case_id: str) -> Path:
        repo = self.tmp / f"repo-{case_id}"
        eval_harness.materialize(case_id, repo)
        return repo

    def score(self, case_id: str, repo: Path, report: dict) -> None:
        path = self.tmp / f"report-{case_id}.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        eval_harness.score_report(case_id, path, repo)

    def assert_rejected(self, case_id: str, repo: Path, report: dict, fragment: str) -> None:
        with self.assertRaises(eval_harness.EvaluationError) as ctx:
            self.score(case_id, repo, report)
        self.assertIn(fragment, str(ctx.exception))


class LayeredMaterializationTest(unittest.TestCase):
    CASE_ID = "synthetic-layers"

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.cases_dir = self.tmp / "cases"
        write_case(
            self.cases_dir,
            self.CASE_ID,
            {
                "base": {"app.py": "VERSION = 0\n"},
                "commits/one": {"feature.py": "def feature():\n    return 1\n"},
                "commits/two": {"helper.py": "HELP = True\n", "app.py": "VERSION = 1\n"},
                "previous": {"verified.py": "STATE = 'verified'\n"},
                "candidate": {"app.py": "VERSION = 2\n"},
            },
            branch_commits=["commits/one", "commits/two"],
            previous="previous",
            seeded_reviewer_claim="Claim: something.",
        )
        patcher = patch.object(eval_harness, "CASES_DIR", self.cases_dir)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tmp.cleanup)
        self.repo = self.tmp / "repo"
        eval_harness.materialize(self.CASE_ID, self.repo)
        self.report = self.tmp / "report.json"
        self.report.write_text(json.dumps({"case_id": self.CASE_ID}), encoding="utf-8")

    def test_layers_are_ordered(self) -> None:
        _, case = eval_harness.load_case(self.CASE_ID)
        case["staged"] = "staged"
        self.assertEqual(
            [(layer.kind, layer.source or layer.path) for layer in eval_harness.layers(case)],
            [
                ("base", "base"),
                ("branch_commit", "commits/one"),
                ("branch_commit", "commits/two"),
                ("previous", "previous"),
                ("staged", "staged"),
                ("candidate", "candidate"),
                ("artifact", ".verify-eval/task.md"),
                ("artifact", ".verify-eval/reviewer-claim.md"),
            ],
        )

    def test_reference_digest_covers_every_layer(self) -> None:
        self.assertEqual(eval_harness.reference_tree_digest(self.CASE_ID), eval_harness.tree_digest(self.repo))
        for name in ("feature.py", "helper.py", "verified.py"):
            self.assertTrue((self.repo / name).is_file(), name)
        self.assertEqual((self.repo / "app.py").read_text(encoding="utf-8"), "VERSION = 2\n")
        self.assertTrue((self.repo / ".verify-eval" / "reviewer-claim.md").is_file())

    def test_layers_are_committed_in_order_before_the_candidate(self) -> None:
        log = eval_harness.run(["git", "log", "--format=%s", "main..HEAD"], self.repo).stdout.splitlines()
        self.assertEqual(log, ["verified state", "branch commit 2: commits/two", "branch commit 1: commits/one"])
        status = eval_harness.run(["git", "status", "--porcelain"], self.repo).stdout.splitlines()
        self.assertEqual(status, [" M app.py"])

    def test_same_size_overlay_with_equal_source_mtimes_is_seen_by_git(self) -> None:
        # Layers overwrite a file with same-size content whose source mtimes are
        # equal; git's stat cache must not mistake the overlay for unchanged.
        write_case(
            self.cases_dir,
            "same-stat",
            {
                "base": {"config.py": "SIZE = 25\n"},
                "previous": {"config.py": "SIZE = 50\n"},
                "candidate": {"config.py": "SIZE = 75\n"},
            },
            previous="previous",
        )
        for layer in ("base", "previous", "candidate"):
            os.utime(self.cases_dir / "same-stat" / layer / "config.py", (1_000_000_000, 1_000_000_000))
        repo = self.tmp / "same-stat-repo"
        eval_harness.materialize("same-stat", repo)
        self.assertEqual(eval_harness.run(["git", "show", "HEAD:config.py"], repo).stdout, "SIZE = 50\n")
        self.assertEqual(eval_harness.run(["git", "status", "--porcelain"], repo).stdout, " M config.py\n")

    def test_check_detects_an_edited_branch_commit_file(self) -> None:
        (self.repo / "feature.py").write_text("def feature():\n    return 2\n", encoding="utf-8")
        with self.assertRaises(eval_harness.EvaluationError) as ctx:
            eval_harness.score_report(self.CASE_ID, self.report, self.repo)
        self.assertIn("source changed", str(ctx.exception))

    def test_check_detects_an_edited_previous_file(self) -> None:
        (self.repo / "verified.py").write_text("STATE = 'tampered'\n", encoding="utf-8")
        with self.assertRaises(eval_harness.EvaluationError) as ctx:
            eval_harness.score_report(self.CASE_ID, self.report, self.repo)
        self.assertIn("source changed", str(ctx.exception))

    def test_check_accepts_the_untouched_layered_tree(self) -> None:
        # Reaches the semantic scorer (not the digest guard) on an unmodified tree.
        with self.assertRaises(eval_harness.EvaluationError) as ctx:
            eval_harness.score_report(self.CASE_ID, self.report, self.repo)
        self.assertNotIn("source changed", str(ctx.exception))


class TargetPresenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.cases_dir = self.tmp / "cases"
        patcher = patch.object(eval_harness, "CASES_DIR", self.cases_dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def check(self, case_id: str) -> None:
        _, case = eval_harness.load_case(case_id)
        repo = self.tmp / f"repo-{case_id}"
        eval_harness.materialize(case_id, repo)
        eval_harness.check_target_present(case_id, case, repo)

    def test_untracked_only_candidate_passes(self) -> None:
        write_case(
            self.cases_dir,
            "untracked-only",
            {"base": {"app.py": "A = 1\n"}, "candidate": {"test_new.py": "# new untracked test\n"}},
        )
        self.check("untracked-only")

    def test_artifact_only_case_passes(self) -> None:
        write_case(
            self.cases_dir,
            "artifact-only",
            {"base": {"config.py": "KEYS = set()\n", "docs/plan.md": "# Plan\n"}, "candidate": {}},
            target={"kind": "artifact", "path": "docs/plan.md"},
        )
        self.check("artifact-only")

    def test_branch_commits_only_case_passes(self) -> None:
        write_case(
            self.cases_dir,
            "branch-only",
            {"base": {"app.py": "A = 1\n"}, "commits/one": {"app.py": "A = 2\n"}, "candidate": {}},
            branch_commits=["commits/one"],
        )
        self.check("branch-only")

    def test_case_without_target_content_fails(self) -> None:
        write_case(
            self.cases_dir,
            "no-target",
            {"base": {"app.py": "A = 1\n"}, "candidate": {"app.py": "A = 1\n"}},
        )
        with self.assertRaises(eval_harness.EvaluationError) as ctx:
            self.check("no-target")
        self.assertIn("no target content", str(ctx.exception))

    def test_missing_artifact_target_fails(self) -> None:
        write_case(
            self.cases_dir,
            "missing-artifact",
            {"base": {"app.py": "A = 1\n"}, "candidate": {}},
            target={"kind": "artifact", "path": "docs/plan.md"},
        )
        with self.assertRaises(eval_harness.EvaluationError):
            self.check("missing-artifact")

    def test_validate_package_reports_a_case_without_target_content(self) -> None:
        write_case(
            self.cases_dir,
            "no-target",
            {"base": {"app.py": "A = 1\n"}, "candidate": {"app.py": "A = 1\n"}},
        )
        with self.assertRaises(eval_harness.EvaluationError) as ctx:
            eval_harness.validate_package()
        self.assertIn("no-target: no target content", str(ctx.exception))


SIMPLE = {"base": {"app.py": "A = 1\n"}, "candidate": {"app.py": "A = 2\n"}}


class ReportConsistencyTest(SyntheticCaseTest):
    """Task 2.4: rules applied to every report, one rejecting test per rule."""

    def setUp(self) -> None:
        super().setUp()
        write_case(self.cases_dir, "consistency", SIMPLE)
        self.repo = self.materialize("consistency")

    def report(self, **overrides: object) -> dict:
        return valid_report("consistency", self.repo, **overrides)

    def finding(self, **overrides: object) -> dict:
        finding = {
            "id": "tests-1",
            "status": "VALIDATED",
            "reviewer": "tests",
            "claim": "claim",
            "requirement_or_invariant": "R1",
            "evidence": ["app.py:1"],
            "failure_mechanism": "a -> b -> c",
            "proposed_severity": "OPTIONAL",
            "severity": "OPTIONAL",
            "severity_change_reason": None,
            "rejection_reason": None,
        }
        finding.update(overrides)
        return finding

    def rejected(self, fragment: str, **overrides: object) -> None:
        self.assert_rejected("consistency", self.repo, self.report(**overrides), fragment)

    def test_a_consistent_report_passes(self) -> None:
        self.score("consistency", self.repo, self.report())

    def test_each_required_key_must_be_present(self) -> None:
        for key in eval_harness.REQUIRED_REPORT_KEYS:
            with self.subTest(key=key):
                report = self.report()
                del report[key]
                self.assert_rejected("consistency", self.repo, report, f"missing report keys: ['{key}']")

    def test_contract_summary_needs_a_source_of_truth(self) -> None:
        for summary in ({}, {"source_of_truth": " "}, None):
            with self.subTest(summary=summary):
                self.rejected("contract_summary.source_of_truth", contract_summary=summary)

    def test_a_contract_file_source_needs_its_blob_id(self) -> None:
        task_hash = git(self.repo, "hash-object", eval_harness.TASK_FILE)
        self.assertEqual(task_hash, text_blob_id(SYNTHETIC_TASK))
        self.assertEqual(eval_harness.contract_blob_id(self.repo), task_hash)
        source = f"--contract {self.repo / eval_harness.TASK_FILE}"
        for summary in ({"source_of_truth": source}, {"source_of_truth": source, "source_hash": "abc"}):
            with self.subTest(summary=summary):
                self.rejected("contract_summary.source_hash must be the --contract file's blob id", contract_summary=summary)
        # A well-formed blob id that is not the contract file's own.
        self.rejected(
            f"the --contract file's blob id is {task_hash!r}",
            contract_summary={"source_of_truth": source, "source_hash": "0" * 40},
        )
        # Compared by hash, so a relative path is as good as the absolute one the prompt passes.
        for path in (str(self.repo / eval_harness.TASK_FILE), eval_harness.TASK_FILE):
            with self.subTest(path=path):
                summary = {"source_of_truth": f"--contract {path}", "source_hash": task_hash}
                self.score("consistency", self.repo, self.report(contract_summary=summary))
        # Any other source records `null` and is not checked.
        self.score("consistency", self.repo, self.report(contract_summary={"source_of_truth": "conversation", "source_hash": None}))

    def test_criteria_carry_their_full_text(self) -> None:
        for entry in ({"id": "A1", "result": "PASS", "evidence": "app.py:1"}, {"id": "A1", "text": " ", "result": "PASS"}):
            with self.subTest(entry=entry):
                self.rejected("criteria[0] needs a non-empty id and text", criteria=[entry])
        full = {"id": "A1", "text": "A is 2", "result": "PASS", "evidence": "app.py:1"}
        self.score("consistency", self.repo, self.report(criteria=[full]))

    def test_verdict_must_be_one_of_the_four_words(self) -> None:
        self.rejected("is not one of", verdict="APPROVE")

    def test_no_pass_with_an_open_validated_should_fix(self) -> None:
        for verdict in ("PASS", "PASS WITH NOTES"):
            with self.subTest(verdict=verdict):
                self.rejected(
                    "open validated BLOCKER/SHOULD_FIX ['tests-1']",
                    verdict=verdict,
                    findings=[self.finding(proposed_severity="SHOULD_FIX", severity="SHOULD_FIX")],
                )

    def test_no_pass_with_a_missing_gap(self) -> None:
        self.rejected(
            "1 MISSING gap(s)",
            verdict="PASS WITH NOTES",
            evidence_gaps=[{"kind": "MISSING", "evidence": "no boundary test"}],
        )

    def test_fix_required_next_action_must_name_the_recheck(self) -> None:
        self.rejected("must name the re-check", verdict="FIX REQUIRED", minimum_next_action="Fix app.py.")
        report = self.report(verdict="FIX REQUIRED", minimum_next_action="Fix app.py, then re-check with acceptance.")
        with self.assertRaises(eval_harness.EvaluationError) as ctx:
            self.score("consistency", self.repo, report)
        self.assertNotIn("re-check", str(ctx.exception))  # only the expected-verdict mismatch remains

    def test_reviewer_findings_need_a_proposed_severity(self) -> None:
        self.rejected("proposed_severity is required", findings=[self.finding(proposed_severity=None)])
        lead_finding = self.finding(reviewer="lead")
        del lead_finding["proposed_severity"]
        self.score("consistency", self.repo, self.report(verdict="PASS", findings=[lead_finding]))

    def test_severity_change_needs_a_reason(self) -> None:
        self.rejected(
            "needs a non-empty severity_change_reason",
            findings=[self.finding(proposed_severity="SHOULD_FIX", severity="OPTIONAL", severity_change_reason=" ")],
        )
        changed = self.finding(proposed_severity="SHOULD_FIX", severity="OPTIONAL", severity_change_reason="no impact")
        self.score("consistency", self.repo, self.report(findings=[changed]))

    def test_non_issue_needs_a_rejection_reason(self) -> None:
        self.rejected(
            "NON_ISSUE needs a non-empty rejection_reason",
            findings=[self.finding(status="NON_ISSUE", proposed_severity="BLOCKER", severity="NON_ISSUE")],
        )

    def test_out_of_mandate_disposition_must_be_valid(self) -> None:
        self.rejected(
            "invalid disposition",
            out_of_mandate=[{"reviewer": "regression", "note": "lock", "disposition": "ignored", "finding_id": None}],
        )

    def test_checks_need_a_valid_execution_and_run_by(self) -> None:
        self.rejected(
            "execution must be one of",
            checks_executed=[{"command_or_inspection": "unittest", "result": "ok", "execution": "ran", "run_by": "lead"}],
        )
        self.rejected(
            "run_by is required",
            checks_executed=[{"command_or_inspection": "unittest", "result": "ok", "execution": "executed"}],
        )

    def test_scope_covered_must_be_non_empty(self) -> None:
        self.rejected("scope.covered must be non-empty", scope={"covered": [], "not_covered": []})


class ManifestExpectationTest(SyntheticCaseTest):
    """Tasks 2.5, 3.3, 3.4, 4.2: new manifest keys and their scoring."""

    def test_out_of_mandate_terms(self) -> None:
        write_case(
            self.cases_dir,
            "oom",
            SIMPLE,
            seeded_reviewer_claim="NO FINDINGS\nOut of mandate: lock held across network call",
            expected={"verdict": "PASS", "out_of_mandate_terms": [{"term": "lock", "disposition": "adjudicated"}]},
        )
        repo = self.materialize("oom")
        claim = (repo / ".verify-eval" / "reviewer-claim.md").read_text(encoding="utf-8")
        self.assertIn("Out of mandate: lock held across network call", claim)
        note = {"reviewer": "regression", "note": "Lock held across network call", "finding_id": None}
        self.score("oom", repo, valid_report("oom", repo, out_of_mandate=[{**note, "disposition": "adjudicated"}]))
        self.assert_rejected(
            "oom", repo, valid_report("oom", repo, out_of_mandate=[note]), "missing out_of_mandate note naming 'lock'"
        )
        self.assert_rejected(
            "oom",
            repo,
            valid_report("oom", repo, out_of_mandate=[{**note, "disposition": "open_lead"}]),
            "with disposition 'adjudicated'",
        )

    def test_proposed_severities_in_finding_matcher(self) -> None:
        actual = {
            "status": "VALIDATED",
            "requirement_or_invariant": "C1",
            "severity": "SHOULD_FIX",
            "proposed_severity": "BLOCKER",
            "evidence": ["export.py:9"],
            "claim": "partial file left behind",
        }
        expected = {"requirement_or_invariant": ["C1"], "severities": ["SHOULD_FIX"], "proposed_severities": ["BLOCKER"]}
        self.assertTrue(eval_harness.finding_matches(actual, expected))
        self.assertFalse(eval_harness.finding_matches({**actual, "proposed_severity": "SHOULD_FIX"}, expected))
        self.assertFalse(eval_harness.finding_matches({k: v for k, v in actual.items() if k != "proposed_severity"}, expected))

    def test_criterion_linked_finding_resolves_through_criteria_text(self) -> None:
        actual = {"status": "VALIDATED", "requirement_or_invariant": "A1", "severity": "SHOULD_FIX"}
        expected = {"requirement_or_invariant": ["R2"]}
        covers = [{"id": "A1", "text": "A1 (R2, I1): last name is kept"}]
        self.assertTrue(eval_harness.finding_matches(actual, expected, covers))
        self.assertFalse(eval_harness.finding_matches(actual, expected, [{"id": "A1", "text": "A1: unrelated"}]))
        self.assertFalse(eval_harness.finding_matches(actual, expected))

    def test_expected_finding_id_must_match_and_name_a_prior_finding(self) -> None:
        actual = {"id": "F2", "status": "VALIDATED", "severity": "OPTIONAL", "claim": "message omits text"}
        self.assertTrue(eval_harness.finding_matches(actual, {"id": "F2", "severities": ["OPTIONAL"]}))
        self.assertFalse(eval_harness.finding_matches({**actual, "id": "acceptance-1"}, {"id": "F2"}))
        self.assertTrue(eval_harness.finding_matches({**actual, "id": "acceptance-1"}, {"severities": ["OPTIONAL"]}))
        case = {
            "id": "c", "title": "c", "mode": "panel", "task": "t", "test_expectation": "pass", "previous": "previous",
            "prior_report": PRIOR_REPORT, "expected": {"verdict": "PASS WITH NOTES", "findings": [{"id": "F3"}]},
        }
        eval_harness.validate_manifest("c", case)
        case["expected"]["findings"] = [{"id": "F9"}]
        with self.assertRaises(eval_harness.EvaluationError) as ctx:
            eval_harness.validate_manifest("c", case)
        self.assertIn("'F9' names no prior finding", str(ctx.exception))

    def test_prompt_states_no_shell_reviewers_and_the_handoff_note(self) -> None:
        write_case(self.cases_dir, "plain", SIMPLE)
        write_case(
            self.cases_dir, "hygiene", SIMPLE, reviewer_capability="no-shell", handoff_note="All tests are green."
        )
        repo = self.materialize("hygiene")
        self.assertEqual((repo / ".verify-eval" / "handoff.md").read_text(encoding="utf-8"), "All tests are green.\n")
        prompt = eval_harness.prompt_for("hygiene", repo)
        self.assertIn("Reviewers in this run cannot execute commands", prompt)
        self.assertIn(f"The implementer's note is {repo / '.verify-eval' / 'handoff.md'}.", prompt)
        plain = eval_harness.prompt_for("plain", repo)
        self.assertNotIn("cannot execute commands", plain)
        self.assertNotIn("implementer's note", plain)
        self.assertEqual(eval_harness.reference_tree_digest("hygiene"), eval_harness.tree_digest(repo))

    def test_fail_expectation_requires_failing_candidate_tests(self) -> None:
        failing = "import unittest\n\nclass T(unittest.TestCase):\n    def test_it(self):\n        self.assertEqual(1, 2)\n"
        passing = "import unittest\n\nclass T(unittest.TestCase):\n    def test_it(self):\n        self.assertEqual(1, 1)\n"
        write_case(self.cases_dir, "fails", {"base": {"app.py": "A = 1\n"}, "candidate": {"test_app.py": failing}},
                   test_expectation="fail")
        eval_harness.validate_package()
        write_case(self.cases_dir, "passes", {"base": {"app.py": "A = 1\n"}, "candidate": {"test_app.py": passing}},
                   test_expectation="fail")
        with self.assertRaises(eval_harness.EvaluationError) as ctx:
            eval_harness.validate_package()
        self.assertIn("passes: candidate tests should fail but did not", str(ctx.exception))
        self.assertNotIn("fails:", str(ctx.exception))

    def test_expected_checks_match_execution_run_by_and_command_terms(self) -> None:
        write_case(
            self.cases_dir,
            "checks",
            SIMPLE,
            expected={"verdict": "PASS", "checks": [{"execution": "executed", "run_by": "lead", "command_terms": ["unittest"]}]},
        )
        repo = self.materialize("checks")
        check = {"command_or_inspection": "python3 -m unittest -v", "result": "OK", "execution": "executed", "run_by": "lead"}
        self.score("checks", repo, valid_report("checks", repo, checks_executed=[check]))
        for name, variant in (
            ("run_by", {**check, "run_by": "tests"}),
            ("execution", {**check, "execution": "static"}),
            ("command", {**check, "command_or_inspection": "read test_app.py"}),
        ):
            with self.subTest(mismatch=name):
                self.assert_rejected("checks", repo, valid_report("checks", repo, checks_executed=[variant]),
                                     "missing executed check")

    def test_check_rejects_an_edited_task_file(self) -> None:
        write_case(self.cases_dir, "immutable", SIMPLE)
        repo = self.materialize("immutable")
        report = valid_report("immutable", repo)
        self.score("immutable", repo, report)
        task = repo / ".verify-eval" / "task.md"
        task.write_text(task.read_text(encoding="utf-8") + "R2 is outdated.\n", encoding="utf-8")
        self.assert_rejected("immutable", repo, report, "the contract was edited")
        task.unlink()
        self.assert_rejected("immutable", repo, report, "the contract was edited")

    def test_effective_mode_sets_the_reviewer_bound(self) -> None:
        write_case(
            self.cases_dir,
            "escalated",
            SIMPLE,
            expected={"verdict": "PASS", "effective_mode": "panel", "required_reviewers": ["acceptance", "tests", "security"]},
        )
        eval_harness.validate_manifest("escalated", eval_harness.load_case("escalated")[1])
        repo = self.materialize("escalated")
        three = ["acceptance", "tests", "security"]
        self.score("escalated", repo, valid_report("escalated", repo, selected_reviewers=three))
        self.assert_rejected(
            "escalated",
            repo,
            valid_report("escalated", repo, selected_reviewers=three, effective_mode="quick"),
            "effective_mode: expected 'panel', got 'quick'",
        )
        write_case(self.cases_dir, "plain-quick", SIMPLE)
        plain = self.materialize("plain-quick")
        self.assert_rejected(
            "plain-quick", plain, valid_report("plain-quick", plain, selected_reviewers=three), "panel bound exceeded"
        )

    def test_effective_mode_raises_the_manifest_max_reviewers_bound(self) -> None:
        case = {
            "id": "c", "title": "c", "mode": "quick", "task": "t", "test_expectation": "pass",
            "expected": {"verdict": "PASS", "effective_mode": "panel", "max_reviewers": 4},
        }
        eval_harness.validate_manifest("c", case)
        case["expected"]["effective_mode"] = "fast"
        with self.assertRaises(eval_harness.EvaluationError):
            eval_harness.validate_manifest("c", case)


class TargetMaterializationTest(SyntheticCaseTest):
    """Task 5.3: branch commits, origin refs, staged layer, artifact target, scope terms."""

    BRANCH = {
        "base": {"app.py": "A = 1\n"},
        "commits/one": {"feature.py": "F = 1\n"},
        "commits/two": {"feature.py": "F = 2\n"},
        "candidate": {"app.py": "A = 2\n"},
    }

    def test_branch_commits_without_origin(self) -> None:
        write_case(self.cases_dir, "branch", self.BRANCH, branch_commits=["commits/one", "commits/two"])
        repo = self.materialize("branch")
        self.assertEqual(
            git(repo, "log", "--format=%s", "main..feature").splitlines(),
            ["branch commit 2: commits/two", "branch commit 1: commits/one"],
        )
        baseline = git(repo, "rev-list", "--max-parents=0", "HEAD")
        self.assertEqual(git(repo, "merge-base", "main", "feature"), baseline)
        self.assertEqual(git(repo, "rev-parse", "main"), baseline)
        self.assertEqual(git(repo, "remote"), "")
        self.assertIn("against the default target in", eval_harness.prompt_for("branch", repo))
        self.assertNotIn("working-tree diff", eval_harness.prompt_for("branch", repo))

    def test_origin_refs_hide_the_base_from_upstream(self) -> None:
        write_case(
            self.cases_dir,
            "origin",
            self.BRANCH,
            branch_commits=["commits/one", "commits/two"],
            origin={"default": "main", "upstream": "feature"},
        )
        repo = self.materialize("origin")
        baseline = git(repo, "rev-list", "--max-parents=0", "HEAD")
        self.assertEqual(git(repo, "symbolic-ref", "refs/remotes/origin/HEAD"), "refs/remotes/origin/main")
        self.assertEqual(git(repo, "rev-parse", "origin/main"), baseline)
        self.assertEqual(git(repo, "rev-parse", "origin/feature"), git(repo, "rev-parse", "HEAD"))
        self.assertEqual(git(repo, "rev-parse", "--abbrev-ref", "@{upstream}"), "origin/feature")
        self.assertEqual(git(repo, "rev-list", "@{upstream}..HEAD"), "")
        self.assertEqual(len(git(repo, "rev-list", "origin/HEAD..HEAD").splitlines()), 2)
        self.assertNotEqual(eval_harness.run(["git", "rev-parse", "--verify", "-q", "main"], repo, check=False).returncode, 0)
        self.assertEqual(git(repo, "config", "remote.origin.fetch"), "+refs/heads/*:refs/remotes/origin/*")
        self.assertEqual(git(repo, "remote"), "origin")
        fetch = eval_harness.run(["git", "fetch", "-q", "origin"], repo, check=False)
        self.assertNotEqual(fetch.returncode, 0)
        self.assertEqual(eval_harness.reference_tree_digest("origin"), eval_harness.tree_digest(repo))
        # The verified-state check derives the target from the baseline sha, not `main`.
        self.score("origin", repo, valid_report("origin", repo))
        self.assertIn("feature.py", eval_harness.target_paths(eval_harness.load_case("origin")[1], repo))

    def test_origin_requires_branch_commits(self) -> None:
        write_case(self.cases_dir, "bad-origin", SIMPLE, origin={"default": "main", "upstream": "feature"})
        with self.assertRaises(eval_harness.EvaluationError):
            eval_harness.validate_manifest("bad-origin", eval_harness.load_case("bad-origin")[1])

    def test_staged_layer_differs_from_the_working_tree(self) -> None:
        write_case(
            self.cases_dir,
            "staged",
            {"base": {"slug.py": "V = 0\n"}, "staged": {"slug.py": "V = 1\n"}, "candidate": {"slug.py": "V = 2\n"}},
            staged="staged",
            expected={"verdict": "PASS", "scope_not_covered_terms": ["staged"]},
        )
        repo = self.materialize("staged")
        self.assertIn("V = 1", git(repo, "diff", "--cached"))
        self.assertIn("V = 2", git(repo, "diff"))
        self.assertIn("against the working-tree diff in", eval_harness.prompt_for("staged", repo))
        good = valid_report("staged", repo, scope={"covered": ["slug.py"], "not_covered": ["staged content of slug.py"]})
        self.score("staged", repo, good)
        self.assertEqual(good["verified_state"]["files"]["slug.py"], git(repo, "hash-object", "slug.py"))
        self.assert_rejected(
            "staged", repo, valid_report("staged", repo), "scope.not_covered does not name 'staged'"
        )

    def test_artifact_target_is_named_in_the_prompt(self) -> None:
        write_case(
            self.cases_dir,
            "artifact",
            {"base": {"config.py": "KEYS = set()\n"}, "candidate": {"docs/plan.md": "# Plan\n"}},
            target={"kind": "artifact", "path": "docs/plan.md"},
        )
        repo = self.materialize("artifact")
        prompt = eval_harness.prompt_for("artifact", repo)
        self.assertIn(f"against the artifact target {repo / 'docs' / 'plan.md'} in {repo}", prompt)
        self.assertIn("docs/plan.md", eval_harness.target_paths(eval_harness.load_case("artifact")[1], repo))

    def test_invalid_artifact_target_is_rejected(self) -> None:
        for target in ({"kind": "file", "path": "a"}, {"kind": "artifact", "path": "../a"}, {"kind": "artifact"}):
            with self.subTest(target=target):
                write_case(self.cases_dir, "bad-target", SIMPLE, target=target)
                with self.assertRaises(eval_harness.EvaluationError):
                    eval_harness.validate_manifest("bad-target", eval_harness.load_case("bad-target")[1])


SYNTHETIC_TASK = "R1: synthetic task.\n"  # write_case's default task, as materialized
PRIOR_REPORT = {
    "verdict": "FIX REQUIRED",
    "effective_mode": "panel",
    "contract_summary": {
        "source_of_truth": "--contract .verify-eval/task.md",
        "source_hash": text_blob_id(SYNTHETIC_TASK),
        "requirements": ["R1: synthetic task."],
    },
    "criteria": [{"id": "A1", "text": "R1: synthetic task holds.", "result": "FAIL", "evidence": "limits.py:1"}],
    "findings": [
        {"id": "F1", "status": "VALIDATED", "reviewer": "invariants", "claim": "limit is exclusive",
         "evidence": ["limits.py:1"], "proposed_severity": "SHOULD_FIX", "severity": "SHOULD_FIX"},
        {"id": "F2", "status": "VALIDATED", "reviewer": "regression", "claim": "default changed",
         "evidence": ["config.py:1"], "proposed_severity": "SHOULD_FIX", "severity": "SHOULD_FIX"},
        {"id": "F3", "status": "VALIDATED", "reviewer": "acceptance", "claim": "message wording",
         "evidence": ["limits.py:1"], "proposed_severity": "OPTIONAL", "severity": "OPTIONAL"},
        {"id": "F4", "status": "NON_ISSUE", "reviewer": "tests", "claim": "speculative",
         "evidence": ["limits.py:1"], "proposed_severity": "BLOCKER", "severity": "NON_ISSUE",
         "rejection_reason": "unsupported"},
    ],
    "verified_state": None,
    "recheck": None,
    "minimum_next_action": "Fix F1 and F2, then re-check.",
}


class RecheckTest(SyntheticCaseTest):
    """Task 6.3: the previous snapshot, the injected prior report, and re-check scoring."""

    SNAPSHOTS = {
        "base": {"limits.py": "LIMIT = 1\n", "config.py": "PAGE = 10\n"},
        "previous": {"limits.py": "LIMIT = 2\n", "config.py": "PAGE = 50\n"},
        "candidate": {"limits.py": "LIMIT = 3\n", "test_limits.py": "# boundary test\n"},
    }

    def setUp(self) -> None:
        super().setUp()
        write_case(
            self.cases_dir,
            "recheck",
            self.SNAPSHOTS,
            mode="panel",
            previous="previous",
            prior_report=PRIOR_REPORT,
            handoff_note="F1 and F2 were addressed.",
            expected={
                "verdict": "FIX REQUIRED",
                "recheck_roles": ["acceptance", "tests", "invariants", "regression"],
                "recheck_unresolved": ["F2"],
                "another_round_required": True,
            },
        )
        self.repo = self.materialize("recheck")

    def recheck(self, **overrides: object) -> dict:
        recheck = {
            "round": 1,
            "prior_verdict": "FIX REQUIRED",
            "prior_findings": [
                {"id": "F1", "resolution": "resolved", "evidence": ["limits.py:1 now inclusive"]},
                {"id": "F2", "resolution": "unresolved", "evidence": ["config.py:1 still 50"]},
            ],
            "roles": ["acceptance", "tests", "invariants", "regression"],
            "delta": {"commits": [], "paths": ["limits.py", "test_limits.py"]},
            "another_round_required": True,
        }
        recheck.update(overrides)
        return recheck

    def report(self, **overrides: object) -> dict:
        defaults = {
            "selected_reviewers": ["acceptance", "tests", "invariants", "regression"],
            "minimum_next_action": "Restore PAGE, then re-check with acceptance, tests, invariants, regression.",
            "recheck": self.recheck(),
        }
        return valid_report("recheck", self.repo, **{**defaults, **overrides})

    def test_prior_report_carries_the_verified_state(self) -> None:
        prior = json.loads((self.repo / ".verify-eval" / "prior-report.json").read_text(encoding="utf-8"))
        self.assertEqual(git(self.repo, "log", "-1", "--format=%s"), "verified state")
        self.assertEqual(prior["verified_state"]["head"], git(self.repo, "rev-parse", "HEAD"))
        previous_dir = self.cases_dir / "recheck" / "previous"
        expected_files = {
            name: git(self.repo, "hash-object", str(previous_dir / name)) for name in ("config.py", "limits.py")
        }
        self.assertEqual(prior["verified_state"]["files"], expected_files)
        self.assertEqual(prior["findings"], PRIOR_REPORT["findings"])
        prompt = eval_harness.prompt_for("recheck", self.repo)
        self.assertIn("A prior FIX REQUIRED report from an earlier verify run is supplied", prompt)
        self.assertNotIn("is a re-check", prompt)  # eligibility is the verifier's call
        self.assertIn(str(self.repo / ".verify-eval" / "prior-report.json"), prompt)
        self.assertEqual(eval_harness.reference_tree_digest("recheck"), eval_harness.tree_digest(self.repo))

    def test_a_matching_recheck_report_passes(self) -> None:
        self.score("recheck", self.repo, self.report())

    def test_recheck_roles_are_exact(self) -> None:
        self.assert_rejected(
            "recheck", self.repo, self.report(recheck=self.recheck(roles=["acceptance", "tests", "invariants"])),
            "recheck.roles: expected exactly",
        )

    def test_recheck_optional_roles_are_tolerated_but_not_required(self) -> None:
        case_dir = self.cases_dir / "recheck"
        case = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
        case["expected"]["recheck_roles"] = ["acceptance", "tests", "invariants"]
        case["expected"]["recheck_optional_roles"] = ["regression"]
        (case_dir / "case.json").write_text(json.dumps(case), encoding="utf-8")
        eval_harness.validate_manifest("recheck", case)
        self.score("recheck", self.repo, self.report())  # with regression
        three = ["acceptance", "tests", "invariants"]
        self.score("recheck", self.repo, self.report(recheck=self.recheck(roles=three)))  # without
        self.assert_rejected(
            "recheck", self.repo, self.report(recheck=self.recheck(roles=["acceptance", "tests", "regression"])),
            "recheck.roles: expected exactly ['acceptance', 'invariants', 'tests'] (optionally plus ['regression'])",
        )
        self.assert_rejected(
            "recheck", self.repo, self.report(recheck=self.recheck(roles=[*three, "security"])),
            "recheck.roles: expected exactly",
        )
        for bad, message in (
            ({"recheck_optional_roles": ["tests"]}, "repeats recheck_roles"),
            ({"recheck_optional_roles": ["fuzzing"]}, "invalid reviewer name(s)"),
        ):
            with self.subTest(bad=bad), self.assertRaises(eval_harness.EvaluationError) as ctx:
                eval_harness.validate_manifest("recheck", {**case, "expected": {**case["expected"], **bad}})
            self.assertIn(message, str(ctx.exception))
        no_roles = {k: v for k, v in case["expected"].items() if k != "recheck_roles"}
        with self.assertRaises(eval_harness.EvaluationError):
            eval_harness.validate_manifest("recheck", {**case, "expected": no_roles})

    def test_another_round_required_is_scored(self) -> None:
        self.assert_rejected(
            "recheck", self.repo, self.report(recheck=self.recheck(another_round_required=False)),
            "recheck.another_round_required: expected True",
        )

    def test_every_open_prior_finding_is_listed(self) -> None:
        only_f2 = self.recheck(prior_findings=[{"id": "F2", "resolution": "unresolved", "evidence": ["config.py:1"]}])
        self.assert_rejected("recheck", self.repo, self.report(recheck=only_f2), "missing open prior finding F1")

    def test_prior_finding_needs_evidence(self) -> None:
        no_evidence = self.recheck(prior_findings=[
            {"id": "F1", "resolution": "resolved", "evidence": []},
            {"id": "F2", "resolution": "unresolved", "evidence": ["config.py:1"]},
        ])
        self.assert_rejected("recheck", self.repo, self.report(recheck=no_evidence), "F1]: evidence must be non-empty")

    def test_unresolved_set_must_match(self) -> None:
        all_resolved = self.recheck(prior_findings=[
            {"id": "F1", "resolution": "resolved", "evidence": ["limits.py:1"]},
            {"id": "F2", "resolution": "resolved", "evidence": ["config.py:1"]},
        ])
        self.assert_rejected(
            "recheck", self.repo, self.report(recheck=all_resolved), "recheck unresolved: expected ['F2'], got []"
        )

    def test_no_pass_while_a_prior_finding_is_unresolved(self) -> None:
        for verdict in ("PASS", "PASS WITH NOTES"):
            with self.subTest(verdict=verdict):
                report = self.report(verdict=verdict, minimum_next_action="none")
                self.assertIn(
                    f"verdict {verdict!r} with unresolved prior finding(s) ['F2']",
                    eval_harness.report_consistency_errors(report),
                )
                self.assert_rejected("recheck", self.repo, report, "with unresolved prior finding(s) ['F2']")
        resolved = self.recheck(prior_findings=[
            {"id": "F1", "resolution": "resolved", "evidence": ["limits.py:1"]},
            {"id": "F2", "resolution": "resolved", "evidence": ["config.py:1"]},
        ])
        report = self.report(verdict="PASS", minimum_next_action="none", recheck=resolved)
        self.assertEqual(eval_harness.report_consistency_errors(report), [])
        fix_required = self.report()
        self.assertEqual(eval_harness.report_consistency_errors(fix_required), [])

    def test_unresolved_findings_of_a_prior_recheck_stay_open(self) -> None:
        prior = {
            "verdict": "FIX REQUIRED",
            "findings": [],
            "recheck": {"prior_findings": [
                {"id": "F1", "resolution": "resolved", "evidence": ["limits.py:1"]},
                {"id": "F2", "resolution": "unresolved", "evidence": ["config.py:1"]},
            ]},
        }
        self.assertEqual(eval_harness.open_prior_finding_ids(prior), {"F2"})
        prior["findings"] = [PRIOR_REPORT["findings"][0]]
        self.assertEqual(eval_harness.open_prior_finding_ids(prior), {"F1", "F2"})
        self.assertEqual(eval_harness.open_prior_finding_ids({"findings": [], "recheck": None}), set())

    def test_recheck_must_be_an_object_with_a_prior_report(self) -> None:
        self.assert_rejected("recheck", self.repo, self.report(recheck=None), "recheck must be an object")

    def test_recheck_must_be_null_without_a_prior_report(self) -> None:
        write_case(self.cases_dir, "first-run", SIMPLE)
        repo = self.materialize("first-run")
        self.assert_rejected(
            "first-run", repo, valid_report("first-run", repo, recheck=self.recheck()),
            "recheck must be null without a prior report",
        )

    def test_recheck_report_must_record_every_prior_path(self) -> None:
        report = self.report()
        self.assertIn("config.py", report["verified_state"]["files"])
        # config.py is unchanged since the verified state, so only the prior report requires it.
        report["verified_state"]["files"].pop("config.py")
        with patch.object(eval_harness, "target_paths", return_value={"limits.py", "test_limits.py"}):
            self.assert_rejected("recheck", self.repo, report, "missing target path(s): ['config.py']")

    def test_recheck_report_cannot_drop_its_verified_state(self) -> None:
        scope = {"covered": ["limits.py"], "not_covered": ["verified state not recorded"]}
        self.assert_rejected(
            "recheck", self.repo, self.report(verified_state=None, scope=scope),
            "verified_state is null, but a working-tree target must record {head, files}",
        )

    def test_recheck_report_must_record_the_files_of_open_prior_findings(self) -> None:
        _, case = eval_harness.load_case("recheck")
        case_dir = self.cases_dir / "recheck"
        # F1 and F2 are open (limits.py, config.py); F3 is OPTIONAL and F4 NON_ISSUE.
        self.assertEqual(eval_harness.open_finding_files(case_dir, case, self.repo), {"config.py", "limits.py"})
        prior = json.loads(json.dumps(PRIOR_REPORT))
        prior["findings"][1]["evidence"] = ["extra.py:3 sets PAGE", "python3 -m unittest: OK"]
        (self.repo / "extra.py").write_text("PAGE = 50\n", encoding="utf-8")
        self.assertEqual(
            eval_harness.open_finding_files(case_dir, {**case, "prior_report": prior}, self.repo),
            {"extra.py", "limits.py"},
        )
        (self.repo / "extra.py").unlink()
        self.assertEqual(
            eval_harness.open_finding_files(case_dir, {**case, "prior_report": prior}, self.repo), {"limits.py"}
        )

    def test_recheck_keys_require_a_prior_report(self) -> None:
        case = {
            "id": "c", "title": "c", "mode": "panel", "task": "t", "test_expectation": "pass",
            "expected": {"verdict": "PASS", "recheck_roles": ["acceptance", "tests"]},
        }
        with self.assertRaises(eval_harness.EvaluationError):
            eval_harness.validate_manifest("c", case)

    def supplied_prior(self) -> dict:
        return json.loads((self.repo / eval_harness.PRIOR_REPORT_FILE).read_text(encoding="utf-8"))

    def test_matching_source_hash_is_eligible_whatever_the_path(self) -> None:
        contract_hash = eval_harness.contract_blob_id(self.repo)
        prior = self.supplied_prior()
        self.assertEqual(prior["contract_summary"]["source_hash"], contract_hash)
        self.assertEqual(eval_harness.recheck_eligibility_errors(prior, contract_hash), [])
        # The prior report records a relative path; the prompt passes an absolute one.
        self.assertIn(f"--contract {self.repo / eval_harness.TASK_FILE} ", eval_harness.prompt_for("recheck", self.repo))
        moved = json.loads(json.dumps(prior))
        moved["contract_summary"]["source_of_truth"] = "--contract /elsewhere/work-item.md"
        self.assertEqual(eval_harness.recheck_eligibility_errors(moved, contract_hash), [])

    def test_hash_mismatch_or_other_defects_make_a_strict_recheck_ineligible(self) -> None:
        contract_hash = eval_harness.contract_blob_id(self.repo)
        prior = self.supplied_prior()
        for name, edit, reason in (
            ("hash mismatch", lambda p: p["contract_summary"].update(source_hash="0" * 40),
             "differs from the contract file's blob id"),
            ("no hash", lambda p: p["contract_summary"].pop("source_hash"), "differs from the contract file's blob id"),
            ("conversation source", lambda p: p["contract_summary"].update(source_of_truth="conversation"),
             "not a --contract file"),
            ("no verified state", lambda p: p.update(verified_state=None), "no verified_state"),
            ("not FIX REQUIRED", lambda p: p.update(verdict="PASS"), "not 'FIX REQUIRED'"),
        ):
            with self.subTest(case=name):
                changed = json.loads(json.dumps(prior))
                edit(changed)
                errors = eval_harness.recheck_eligibility_errors(changed, contract_hash)
                self.assertTrue(any(reason in error for error in errors), errors)
        self.assertEqual(eval_harness.recheck_eligibility_errors(None, contract_hash), ["no prior report"])

    def write_stale_contract_case(self, **expected: object) -> Path:
        stale = json.loads(json.dumps(PRIOR_REPORT))
        stale["contract_summary"]["source_hash"] = text_blob_id("R1: the contract before it was edited.\n")
        write_case(
            self.cases_dir, "stale", self.SNAPSHOTS, mode="panel", previous="previous", prior_report=stale,
            expected={"verdict": "FIX REQUIRED", **expected},
        )
        return self.materialize("stale")

    def test_a_stale_contract_hash_is_scored_as_a_full_verification(self) -> None:
        repo = self.write_stale_contract_case()
        eval_harness.validate_manifest("stale", eval_harness.load_case("stale")[1])
        report = valid_report("stale", repo, minimum_next_action="Fix it, then re-check with acceptance, tests.")
        self.score("stale", repo, report)  # recheck: null
        self.assert_rejected(
            "stale", repo, {**report, "recheck": self.recheck()},
            "recheck must be null: the prior report is not re-check eligible (prior contract_summary.source_hash",
        )

    def test_a_fixture_expecting_a_recheck_must_supply_an_eligible_prior(self) -> None:
        case_dir, case = eval_harness.load_case("recheck")
        self.assertEqual(eval_harness.recheck_fixture_errors("recheck", case_dir, case, self.repo), [])
        repo = self.write_stale_contract_case(recheck_roles=["acceptance", "tests"])
        case_dir, case = eval_harness.load_case("stale")
        errors = eval_harness.recheck_fixture_errors("stale", case_dir, case, repo)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("stale: prior_report is not re-check eligible: prior contract_summary.source_hash", errors[0])

    def test_validate_flags_an_open_prior_finding_without_a_file(self) -> None:
        case_dir, case = eval_harness.load_case("recheck")
        prior = json.loads(json.dumps(PRIOR_REPORT))
        prior["findings"][1]["evidence"] = ["the default page size changed"]  # free text, no path
        errors = eval_harness.recheck_fixture_errors("recheck", case_dir, {**case, "prior_report": prior}, self.repo)
        self.assertEqual(errors, ["recheck: open prior finding F2 names no existing file in its evidence"])

    def test_prior_report_manifest_needs_a_hashed_contract_source_and_criteria_text(self) -> None:
        _, case = eval_harness.load_case("recheck")
        eval_harness.validate_manifest("recheck", case)
        for name, edit, message in (
            ("no source hash", lambda p: p["contract_summary"].pop("source_hash"), "blob-id source_hash"),
            ("conversation", lambda p: p["contract_summary"].update(source_of_truth="conversation"), "--contract source"),
            ("no criteria", lambda p: p.update(criteria=[]), "full text"),
            ("criteria ids only", lambda p: p.update(criteria=[{"id": "A1", "result": "FAIL"}]), "full text"),
        ):
            prior = json.loads(json.dumps(case["prior_report"]))
            edit(prior)
            with self.subTest(case=name), self.assertRaises(eval_harness.EvaluationError) as ctx:
                eval_harness.validate_manifest("recheck", {**case, "prior_report": prior})
            self.assertIn(message, str(ctx.exception))


class RepositoryStateGuardTest(SyntheticCaseTest):
    """`check` rejects writes to the index, HEAD, and the injected artifacts."""

    def setUp(self) -> None:
        super().setUp()
        write_case(
            self.cases_dir,
            "guard",
            {
                "base": {"limits.py": "LIMIT = 1\n", "config.py": "PAGE = 10\n"},
                "previous": {"limits.py": "LIMIT = 2\n", "config.py": "PAGE = 50\n"},
                "staged": {"config.py": "PAGE = 25\n"},
                "candidate": {"limits.py": "LIMIT = 3\n"},
            },
            mode="panel",
            previous="previous",
            staged="staged",
            prior_report=PRIOR_REPORT,
            handoff_note="F1 and F2 were addressed.",
            seeded_reviewer_claim="Claim: the limit is exclusive.",
        )
        self.repo = self.materialize("guard")

    def errors(self) -> list[str]:
        return eval_harness.repository_state_errors("guard", eval_harness.load_case("guard")[1], self.repo)

    def test_an_untouched_repository_has_no_state_errors(self) -> None:
        git(self.repo, "status")  # may refresh the index stat cache; not a write of content
        git(self.repo, "diff", "--cached")
        git(self.repo, "log", "--oneline")
        self.assertEqual(self.errors(), [])

    def test_index_writes_are_detected(self) -> None:
        git(self.repo, "add", "limits.py")
        self.assertEqual(self.errors(), ["guard: git index changed since materialization"])
        git(self.repo, "restore", "--staged", "limits.py")
        self.assertEqual(self.errors(), [])
        git(self.repo, "rm", "-q", "--cached", "config.py")
        self.assertEqual(self.errors(), ["guard: git index changed since materialization"])

    def test_head_writes_are_detected(self) -> None:
        head = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "commit", "-q", "--allow-empty", "-m", "verifier commit")
        self.assertIn("guard: git HEAD history changed since materialization", self.errors())
        git(self.repo, "reset", "-q", "--soft", head)
        # History restored, but the reflog still records the commit and the reset.
        self.assertEqual(self.errors(), ["guard: git HEAD reflog changed since materialization"])

    def test_branch_switch_is_detected(self) -> None:
        git(self.repo, "checkout", "-q", "-b", "elsewhere")
        errors = self.errors()
        self.assertIn("guard: git HEAD ref changed since materialization", errors)
        self.assertIn("guard: git HEAD reflog changed since materialization", errors)

    def test_injected_artifact_writes_are_detected(self) -> None:
        for name in ("prior-report.json", "handoff.md", "reviewer-claim.md"):
            with self.subTest(artifact=name):
                path = self.repo / ".verify-eval" / name
                original = path.read_text(encoding="utf-8")
                path.write_text(original.replace("F2", "F9") + "edited\n", encoding="utf-8")
                self.assertEqual(self.errors(), [f"guard: .verify-eval/{name} differs from the injected artifact"])
                path.unlink()
                self.assertEqual(self.errors(), [f"guard: .verify-eval/{name} differs from the injected artifact"])
                path.write_text(original, encoding="utf-8")
                self.assertEqual(self.errors(), [])

    def test_score_report_rejects_a_state_write(self) -> None:
        report = valid_report("guard", self.repo)
        git(self.repo, "add", "limits.py")
        self.assert_rejected("guard", self.repo, report, "git index changed since materialization")


class VerifiedStateTest(SyntheticCaseTest):
    """Task 6.4: the verified_state check and the post-commit match."""

    def setUp(self) -> None:
        super().setUp()
        write_case(
            self.cases_dir,
            "state",
            {"base": {"a.py": "A = 1\n", "b.py": "B = 1\n"}, "candidate": {"a.py": "A = 2\n", "b.py": "B = 2\n", "new.py": "N = 1\n"}},
        )
        self.repo = self.materialize("state")

    def files(self) -> dict:
        return {name: git(self.repo, "hash-object", name) for name in ("a.py", "b.py", "new.py")}

    def report(self, files: dict, **overrides: object) -> dict:
        return valid_report(
            "state", self.repo, verified_state={"head": git(self.repo, "rev-parse", "HEAD"), "files": files}, **overrides
        )

    def test_matching_state_passes(self) -> None:
        self.score("state", self.repo, self.report(self.files()))
        self.assertEqual(eval_harness.verified_state_mismatches(self.files(), self.repo), [])

    def test_wrong_hash_fails(self) -> None:
        files = {**self.files(), "a.py": git(self.repo, "rev-parse", "HEAD:a.py")}
        self.assert_rejected("state", self.repo, self.report(files), "verified_state.files[a.py]")

    def test_missing_target_path_fails(self) -> None:
        files = self.files()
        files.pop("new.py")  # untracked files are target paths too
        self.assert_rejected("state", self.repo, self.report(files), "missing target path(s): ['new.py']")

    def test_wrong_head_fails(self) -> None:
        report = self.report(self.files())
        report["verified_state"]["head"] = "0" * 40
        self.assert_rejected("state", self.repo, report, "verified_state.head")

    NOT_RECORDED = {"covered": ["commit abc"], "not_covered": ["verified state not recorded: commit target"]}

    def test_null_state_is_rejected_for_a_working_tree_target(self) -> None:
        for scope in (None, self.NOT_RECORDED):
            with self.subTest(scope=scope):
                overrides = {"scope": scope} if scope else {}
                self.assert_rejected(
                    "state", self.repo, valid_report("state", self.repo, verified_state=None, **overrides),
                    "verified_state is null, but a working-tree target must record {head, files}",
                )

    def test_null_state_is_rejected_for_branch_and_artifact_targets(self) -> None:
        _, case = eval_harness.load_case("state")
        report = valid_report("state", self.repo, verified_state=None, scope=self.NOT_RECORDED)
        for kind, extra in (
            ("branch", {"branch_commits": ["commits/one"]}),
            ("artifact", {"target": {"kind": "artifact", "path": "a.py"}}),
        ):
            with self.subTest(kind=kind):
                errors = eval_harness.verified_state_errors(self.tmp, {**case, **extra}, report, self.repo)
                self.assertEqual(errors, [f"verified_state is null, but a {kind} target must record {{head, files}}"])

    def test_null_state_is_allowed_only_for_commit_range_or_pr_targets_with_a_not_recorded_scope(self) -> None:
        _, case = eval_harness.load_case("state")
        for kind in sorted(eval_harness.NULL_STATE_TARGET_KINDS):
            with self.subTest(kind=kind):
                target_case = {**case, "target": {"kind": kind}}
                recorded = valid_report("state", self.repo, verified_state=None, scope=self.NOT_RECORDED)
                self.assertEqual(eval_harness.verified_state_errors(self.tmp, target_case, recorded, self.repo), [])
                silent = valid_report("state", self.repo, verified_state=None)
                self.assertIn(
                    "scope does not state that the verified state was not recorded",
                    eval_harness.verified_state_errors(self.tmp, target_case, silent, self.repo)[0],
                )

    def test_partial_commit_fails_the_post_commit_match(self) -> None:
        files = self.files()
        git(self.repo, "add", "a.py", "new.py")
        git(self.repo, "commit", "-q", "-m", "commit part of the reviewed change")
        mismatches = eval_harness.verified_state_mismatches(files, self.repo, commit="HEAD")
        self.assertEqual(len(mismatches), 1, mismatches)
        self.assertIn("verified_state.files[b.py]", mismatches[0])
        git(self.repo, "add", "b.py")
        git(self.repo, "commit", "-q", "-m", "commit the rest")
        self.assertEqual(eval_harness.verified_state_mismatches(files, self.repo, commit="HEAD"), [])

    def test_invalid_path_is_reported(self) -> None:
        self.assertIn("invalid path", eval_harness.verified_state_mismatches({"../x": "abc"}, self.repo)[0])


def synthesized_report(case_id: str, repo: Path) -> dict:
    """The report an ideal verifier would return for a fixture, built from the
    fixture's own expectations, to prove each fixture is satisfiable."""
    case_dir, case = eval_harness.load_case(case_id)
    expected = case["expected"]
    findings = []
    for index, wanted in enumerate(expected.get("findings", [])):
        severity = wanted.get("severities", ["SHOULD_FIX"])[0]
        proposed = wanted.get("proposed_severities", [severity if severity != "NON_ISSUE" else "BLOCKER"])[0]
        findings.append({
            "id": wanted.get("id", f"acceptance-{index + 1}"),
            "status": wanted.get("status", "VALIDATED"),
            "reviewer": "acceptance",
            "claim": " ".join(wanted.get("terms_any", ["claim"])),
            "requirement_or_invariant": ", ".join(wanted.get("requirement_or_invariant", ["none"])),
            "evidence": [f"{path}:1" for path in wanted.get("evidence_paths", [])] or ["observed"],
            "failure_mechanism": "trigger -> behavior -> impact",
            "proposed_severity": proposed,
            "severity": severity,
            "severity_change_reason": "one-line reason" if proposed != severity and severity != "NON_ISSUE" else None,
            "rejection_reason": "one-line reason" if severity == "NON_ISSUE" else None,
        })
    out_of_mandate = [
        {
            "reviewer": "regression",
            "note": entry if isinstance(entry, str) else entry["term"],
            "disposition": "adjudicated" if isinstance(entry, str) else entry.get("disposition", "adjudicated"),
            "finding_id": None,
        }
        for entry in expected.get("out_of_mandate_terms", [])
    ]
    checks = [
        {
            "command_or_inspection": "python3 -m " + " ".join(check.get("command_terms", [])),
            "result": "observed",
            "execution": check["execution"],
            "run_by": check.get("run_by", "lead"),
        }
        for check in expected.get("checks", [])
    ]
    prior = case.get("prior_report")
    recheck = None
    if prior is not None:
        unresolved = set(expected.get("recheck_unresolved", []))
        recheck = {
            "round": 1,
            "prior_verdict": "FIX REQUIRED",
            "prior_findings": [
                {"id": fid, "resolution": "unresolved" if fid in unresolved else "resolved", "evidence": ["file:1"]}
                for fid in sorted(eval_harness.open_prior_finding_ids(prior))
            ],
            "roles": expected.get("recheck_roles", ["acceptance", "tests"]),
            "delta": {"commits": [], "paths": []},
            "another_round_required": expected.get("another_round_required", False),
        }
    paths = eval_harness.target_paths(case, repo)
    if prior is not None:
        paths |= set(eval_harness.snapshot_files(case_dir, case["previous"]))
    return {
        "case_id": case_id,
        "verdict": expected["verdict"],
        "assurance": "independent panel",
        "requested_mode": case["mode"],
        "effective_mode": expected.get("effective_mode", case["mode"]),
        "target": "default target",
        "scope": {
            "covered": ["the target"],
            "not_covered": ["pre-existing code outside the target", *expected.get("scope_not_covered_terms", [])],
        },
        "contract_summary": {
            "source_of_truth": f"--contract {repo / eval_harness.TASK_FILE}",
            "source_hash": git(repo, "hash-object", eval_harness.TASK_FILE),
        },
        "criteria": [
            {"id": key, "text": f"{key} holds", "result": value, "evidence": "x:1"}
            for key, value in expected.get("criteria", {}).items()
        ],
        "selected_reviewers": expected.get("exact_reviewers") or expected.get("required_reviewers") or ["acceptance", "tests"],
        "selection_reasons": {},
        "checks_executed": checks,
        "checks_not_run": [],
        "findings": findings,
        "out_of_mandate": out_of_mandate,
        "evidence_gaps": [{"kind": kind, "evidence": "why"} for kind in expected.get("evidence_gap_kinds", [])],
        "verified_state": {"head": git(repo, "rev-parse", "HEAD"), "files": eval_harness.blob_ids(repo, paths)},
        "recheck": recheck,
        "source_unchanged": True,
        "minimum_next_action": "Re-check after the fix. " + " ".join(expected.get("next_action_or_gap_terms", [])),
    }


V05_CASES = [case_id for case_id in eval_harness.case_ids() if case_id.startswith("v0.5-")]


class V05FixtureTest(unittest.TestCase):
    """Every v0.5 fixture is satisfiable by an ideal report and its layers are set up as the task requires."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def materialize(self, case_id: str) -> Path:
        repo = self.tmp / case_id
        eval_harness.materialize(case_id, repo)
        return repo

    def score(self, case_id: str, repo: Path, report: dict) -> None:
        path = self.tmp / f"{case_id}.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        eval_harness.score_report(case_id, path, repo)

    def test_every_v05_fixture_accepts_an_ideal_report_and_rejects_a_wrong_verdict(self) -> None:
        self.assertEqual(len(V05_CASES), 16)
        for case_id in V05_CASES:
            with self.subTest(case=case_id):
                repo = self.materialize(case_id)
                report = synthesized_report(case_id, repo)
                self.score(case_id, repo, report)
                wrong = "PASS" if report["verdict"] != "PASS" else "FIX REQUIRED"
                with self.assertRaises(eval_harness.EvaluationError):
                    self.score(case_id, repo, {**report, "verdict": wrong})

    def test_recheck_fixtures_keep_the_prior_contract_source_available(self) -> None:
        # Eligibility needs the prior contract's source unchanged: the same --contract
        # file, whose content is the very task text the prior report summarizes.
        rechecks = [case_id for case_id in V05_CASES if eval_harness.load_case(case_id)[1].get("prior_report")]
        self.assertEqual(len(rechecks), 4)
        for case_id in rechecks:
            with self.subTest(case=case_id):
                repo = self.materialize(case_id)
                _, case = eval_harness.load_case(case_id)
                task_path = repo / eval_harness.TASK_FILE
                self.assertIn(f"--contract {task_path} ", eval_harness.prompt_for(case_id, repo))
                self.assertEqual(task_path.read_text(encoding="utf-8"), eval_harness.task_text(case))
                prior = json.loads((repo / eval_harness.PRIOR_REPORT_FILE).read_text(encoding="utf-8"))
                summary = prior["contract_summary"]
                self.assertEqual(summary["source_of_truth"], f"--contract {eval_harness.TASK_FILE}")
                # Eligible by hash: the prior source_hash is the materialized contract's blob id.
                self.assertEqual(summary["source_hash"], git(repo, "hash-object", eval_harness.TASK_FILE))
                self.assertEqual(eval_harness.recheck_eligibility_errors(prior, eval_harness.contract_blob_id(repo)), [])
                self.assertEqual(
                    eval_harness.recheck_fixture_errors(case_id, eval_harness.CASES_DIR / case_id, case, repo), []
                )
                # Reusable criteria: each carries its full text and traces to a task requirement.
                self.assertTrue(prior["criteria"])
                for criterion in prior["criteria"]:
                    self.assertTrue(criterion["text"].strip())
                    self.assertIn(criterion["text"].split(":")[0], case["task"])
                items = [item for key in ("requirements", "invariants", "preserved_behaviors") for item in summary[key]]
                self.assertTrue(items)
                for item in items:
                    self.assertIn(item, case["task"])
                task_ids = set(re.findall(r"\b([RCNIP]\d+)(?: \([^)]*\))?:", case["task"]))
                self.assertEqual({item.split(":")[0].split(" ")[0] for item in items}, task_ids)

    def test_staged_differs_layers(self) -> None:
        repo = self.materialize("v0.5-staged-differs")
        self.assertIn("a-z]+", git(repo, "diff", "--cached", "--", "slug.py"))
        self.assertIn("a-z0-9]+", git(repo, "diff", "--", "slug.py"))
        report = synthesized_report("v0.5-staged-differs", repo)
        self.assertEqual(report["verified_state"]["files"]["slug.py"], git(repo, "hash-object", "slug.py"))
        self.assertNotEqual(report["verified_state"]["files"]["slug.py"], git(repo, "rev-parse", ":slug.py"))

    def test_base_origin_head_hides_branch_commits_from_upstream(self) -> None:
        repo = self.materialize("v0.5-base-origin-head")
        self.assertEqual(git(repo, "rev-list", "@{upstream}..HEAD"), "")
        self.assertIn("window.py", git(repo, "diff", "--name-only", "origin/HEAD...HEAD"))
        self.assertIn("against the default target", eval_harness.prompt_for("v0.5-base-origin-head", repo))

    def test_branch_commits_put_the_defect_before_the_working_tree(self) -> None:
        repo = self.materialize("v0.5-branch-commits")
        self.assertIn("paginate.py", git(repo, "diff", "--name-only", "main...feature"))
        status = eval_harness.run(["git", "status", "--porcelain"], repo).stdout.splitlines()
        self.assertEqual(status, [" M labels.py", " M test_labels.py"])

    def test_recheck_unfixed_finding_is_outside_the_fix_delta(self) -> None:
        repo = self.materialize("v0.5-recheck-unfixed-outside-delta")
        self.assertEqual(git(repo, "diff", "HEAD", "--", "config.py"), "")
        prior = json.loads((repo / ".verify-eval" / "prior-report.json").read_text(encoding="utf-8"))
        self.assertEqual(prior["verified_state"]["head"], git(repo, "rev-parse", "HEAD"))
        self.assertEqual(prior["verified_state"]["files"]["config.py"], git(repo, "hash-object", "config.py"))
        self.assertNotEqual(prior["verified_state"]["files"]["limits.py"], git(repo, "hash-object", "limits.py"))
        report = synthesized_report("v0.5-recheck-unfixed-outside-delta", repo)
        report["recheck"]["prior_findings"] = [
            {**entry, "resolution": "resolved"} for entry in report["recheck"]["prior_findings"]
        ]
        with self.assertRaises(eval_harness.EvaluationError) as ctx:
            self.score("v0.5-recheck-unfixed-outside-delta", repo, report)
        self.assertIn("recheck unresolved: expected ['F2']", str(ctx.exception))

    def test_recheck_unfixed_finding_is_re_emitted_with_its_original_id(self) -> None:
        case_id = "v0.5-recheck-unfixed-outside-delta"
        repo = self.materialize(case_id)
        report = synthesized_report(case_id, repo)
        self.assertEqual([finding["id"] for finding in report["findings"]], ["F2"])
        report["findings"][0]["id"] = "regression-1"
        with self.assertRaises(eval_harness.EvaluationError) as ctx:
            self.score(case_id, repo, report)
        self.assertIn("missing semantic finding: default-page-size-still-changed", str(ctx.exception))

    def test_recheck_optional_only_carries_the_prior_optional_forward(self) -> None:
        case_id = "v0.5-recheck-optional-only"
        repo = self.materialize(case_id)
        _, case = eval_harness.load_case(case_id)
        prior = json.loads((repo / ".verify-eval" / "prior-report.json").read_text(encoding="utf-8"))
        # The OPTIONAL finding's file is outside the fix delta and the open-finding files.
        self.assertEqual(prior["verified_state"]["files"]["amounts.py"], git(repo, "hash-object", "amounts.py"))
        self.assertEqual(git(repo, "status", "--porcelain"), "M test_amounts.py")
        self.assertEqual(eval_harness.open_prior_finding_ids(case["prior_report"]), {"F1"})
        self.assertEqual(
            eval_harness.open_finding_files(eval_harness.CASES_DIR / case_id, case, repo), {"test_amounts.py"}
        )
        report = synthesized_report(case_id, repo)
        carried = report["findings"][0]
        self.assertEqual((carried["id"], carried["status"], carried["severity"]), ("F2", "VALIDATED", "OPTIONAL"))
        self.score(case_id, repo, report)
        for name, findings in (("dropped", []), ("renumbered", [{**carried, "id": "acceptance-1"}])):
            with self.subTest(note=name), self.assertRaises(eval_harness.EvaluationError) as ctx:
                self.score(case_id, repo, {**report, "findings": findings})
            self.assertIn("missing semantic finding: prior-optional-note-carried-forward", str(ctx.exception))

    def test_severity_downgrade_accepts_either_severity_and_scores_the_change_reason(self) -> None:
        case_id = "v0.5-severity-downgrade"
        repo = self.materialize(case_id)
        report = synthesized_report(case_id, repo)
        finding = report["findings"][0]
        self.assertEqual((finding["proposed_severity"], finding["severity"]), ("BLOCKER", "SHOULD_FIX"))
        self.score(case_id, repo, report)  # downgraded, with a reason
        kept = {**finding, "severity": "BLOCKER", "severity_change_reason": None}
        self.score(case_id, repo, {**report, "findings": [kept]})  # proposed severity upheld, no reason needed
        for reason in (None, " "):
            with self.subTest(reason=reason), self.assertRaises(eval_harness.EvaluationError) as ctx:
                self.score(case_id, repo, {**report, "findings": [{**finding, "severity_change_reason": reason}]})
            self.assertIn("BLOCKER -> SHOULD_FIX needs a non-empty severity_change_reason", str(ctx.exception))
        optional = {**finding, "severity": "OPTIONAL"}
        with self.assertRaises(eval_harness.EvaluationError) as ctx:
            self.score(case_id, repo, {**report, "verdict": "PASS WITH NOTES", "findings": [optional]})
        self.assertIn("missing semantic finding: partial-file-on-write-error", str(ctx.exception))

    def test_recheck_new_defect_resolves_f1_and_breaks_only_i1(self) -> None:
        case_id = "v0.5-recheck-new-defect"
        repo = self.materialize(case_id)
        _, case = eval_harness.load_case(case_id)
        self.assertEqual(case["prior_report"]["findings"][0]["requirement_or_invariant"], "R2")
        probe = (
            "from events import process_events\n"
            "def run(events):\n"
            "    seen = []\n"
            "    process_events(events, seen.append)\n"
            "    return [e['id'] for e in seen]\n"
            "e = lambda i, k: {'id': i, 'kind': k, 'payload': None}\n"
            "print(run([e(1, 'created'), e(2, 'paid'), e(1, 'created')]))\n"  # F1 / R2: resolved
            "print(run([e(1, 'created'), e(2, 'created')]))\n"  # I1: distinct id dropped
        )
        result = eval_harness.run([sys.executable, "-I", "-c", f"import sys; sys.path.insert(0, '.')\n{probe}"], repo)
        self.assertEqual(result.stdout.splitlines(), ["[1, 2]", "[1]"])
        report = synthesized_report(case_id, repo)
        report["recheck"]["roles"] = [*report["recheck"]["roles"], "regression"]
        report["selected_reviewers"] = [*report["selected_reviewers"], "regression"]
        self.score(case_id, repo, report)

    def test_recheck_fixed_adds_an_untracked_test_file_to_the_delta(self) -> None:
        repo = self.materialize("v0.5-recheck-fixed")
        self.assertIn("?? test_rate_boundary.py", git(repo, "status", "--porcelain"))


class EvaluationHarnessTest(unittest.TestCase):
    def test_expected_case_corpus_is_present(self) -> None:
        self.assertEqual(
            set(eval_harness.case_ids()),
            {
                "acceptance-omission",
                "bogus-mock",
                "boundary-inversion",
                "contract-regression",
                "correct-low-risk",
                "duplicate-event",
                "speculative-non-issue",
                "tenant-authorization",
                "unavailable-service",
                "v0.2-multi-trigger-bounded",
                "v0.2-pure-formatter-no-overflow",
                "v0.2-retry-idempotency",
                # 2. report header, verdict discipline, JSON fields
                "v0.5-severity-downgrade",
                "v0.5-out-of-mandate-lead",
                # 3. execution capability and brief hygiene
                "v0.5-no-shell-reviewers",
                "v0.5-green-claim-false",
                "v0.5-contract-premise-false",
                "v0.5-code-claims-contract-outdated",
                # 4. security retention
                "v0.5-security-retained",
                "v0.5-quick-security-escalation",
                # 5. targets and scope
                "v0.5-branch-commits",
                "v0.5-plan-artifact",
                "v0.5-base-origin-head",
                "v0.5-staged-differs",
                # 6. fix loop
                "v0.5-recheck-fixed",
                "v0.5-recheck-new-defect",
                "v0.5-recheck-optional-only",
                "v0.5-recheck-unfixed-outside-delta",
            },
        )

    def test_materialize_creates_a_real_candidate_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "repo"
            eval_harness.materialize("boundary-inversion", destination)
            diff = eval_harness.run(["git", "diff", "--", "slots.py"], destination)
            self.assertIn("return active_slots < purchased_slots", diff.stdout)
            self.assertTrue((destination / ".verify-eval" / "task.md").is_file())
            self.assertTrue((destination / ".verify-eval" / "digest").is_file())

    def test_semantic_scorer_accepts_a_matching_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            eval_harness.materialize("correct-low-risk", repo)
            report_path = Path(tmp) / "report.json"
            report_path.write_text(json.dumps(valid_report("correct-low-risk", repo)), encoding="utf-8")
            eval_harness.score_report("correct-low-risk", report_path, repo)

    def test_semantic_scorer_rejects_a_wrong_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            eval_harness.materialize("correct-low-risk", repo)
            report = valid_report(
                "correct-low-risk", repo, verdict="FIX REQUIRED", minimum_next_action="Fix it, then re-check."
            )
            report_path = Path(tmp) / "report.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaises(eval_harness.EvaluationError) as ctx:
                eval_harness.score_report("correct-low-risk", report_path, repo)
            self.assertEqual(str(ctx.exception), "verdict: expected 'PASS', got 'FIX REQUIRED'")

    def test_check_rejects_a_mutated_repo_even_if_report_claims_source_unchanged(self) -> None:
        report = {
            "case_id": "correct-low-risk",
            "verdict": "PASS",
            "selected_reviewers": ["acceptance", "tests"],
            "findings": [],
            "evidence_gaps": [],
            "source_unchanged": True,
        }
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            eval_harness.materialize("correct-low-risk", repo)
            report_path = Path(tmp) / "report.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")

            # Mutate a source file in the materialized repo after the digest was recorded.
            mutated = next(repo.glob("*.py"))
            mutated.write_text(mutated.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")

            with self.assertRaises(eval_harness.EvaluationError) as ctx:
                eval_harness.score_report("correct-low-risk", report_path, repo)
            self.assertIn("source changed", str(ctx.exception))

    def test_check_rejects_an_extra_untracked_file_in_the_repo(self) -> None:
        report = {
            "case_id": "correct-low-risk",
            "verdict": "PASS",
            "selected_reviewers": ["acceptance", "tests"],
            "findings": [],
            "evidence_gaps": [],
            "source_unchanged": True,
        }
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            eval_harness.materialize("correct-low-risk", repo)
            (repo / "extra.py").write_text("# not part of the fixture\n", encoding="utf-8")
            report_path = Path(tmp) / "report.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")

            with self.assertRaises(eval_harness.EvaluationError) as ctx:
                eval_harness.score_report("correct-low-risk", report_path, repo)
            self.assertIn("source changed", str(ctx.exception))

    def test_check_ignores_a_tampered_or_missing_digest_file(self) -> None:
        report = {
            "case_id": "correct-low-risk",
            "verdict": "PASS",
            "selected_reviewers": ["acceptance", "tests"],
            "findings": [],
            "evidence_gaps": [],
            "source_unchanged": True,
        }
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            eval_harness.materialize("correct-low-risk", repo)
            report_path = Path(tmp) / "report.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")

            # Mutate a source file, then try to hide it by deleting the (purely
            # informational) digest artifact `check` never reads.
            mutated = next(repo.glob("*.py"))
            mutated.write_text(mutated.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
            digest_file = repo / ".verify-eval" / "digest"
            self.assertTrue(digest_file.is_file())
            digest_file.unlink()

            with self.assertRaises(eval_harness.EvaluationError) as ctx:
                eval_harness.score_report("correct-low-risk", report_path, repo)
            self.assertIn("source changed", str(ctx.exception))

    def test_semantic_scorer_rejects_a_criteria_mismatch(self) -> None:
        real_case_dir, real_case = eval_harness.load_case("correct-low-risk")
        fake_case = dict(real_case)
        fake_case["expected"] = dict(real_case["expected"])
        fake_case["expected"]["criteria"] = {"A1": "FAIL"}
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            eval_harness.materialize("correct-low-risk", repo)
            report = valid_report(
                "correct-low-risk", repo, criteria=[{"id": "A1", "text": "status is reported", "result": "PASS", "evidence": "status.py:1"}]
            )
            report_path = Path(tmp) / "report.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")

            with patch.object(eval_harness, "load_case", return_value=(real_case_dir, fake_case)):
                with self.assertRaises(eval_harness.EvaluationError) as ctx:
                    eval_harness.score_report("correct-low-risk", report_path, repo)
            self.assertEqual(str(ctx.exception), "criteria[A1]: expected 'FAIL', got 'PASS'")

    def test_finding_can_link_multiple_contract_ids(self) -> None:
        actual = {
            "status": "VALIDATED",
            "requirement_or_invariant": "R2, I1",
            "severity": "BLOCKER",
            "evidence": ["history.py:6"],
            "claim": "Repeated delivery creates a duplicate entry.",
            "failure_mechanism": "same event -> duplicate history",
        }
        expected = {
            "requirement_or_invariant": ["R2", "I1"],
            "severities": ["BLOCKER"],
            "evidence_paths": ["history.py"],
            "terms_any": ["duplicate"],
        }
        self.assertTrue(eval_harness.finding_matches(actual, expected))

    def test_validate_manifest_rejects_a_retired_mode(self) -> None:
        case = {
            "id": "bad-mode",
            "title": "bad mode",
            "mode": "auto",
            "task": "irrelevant",
            "test_expectation": "pass",
            "expected": {"verdict": "PASS"},
        }
        with self.assertRaises(eval_harness.EvaluationError):
            eval_harness.validate_manifest("bad-mode", case)

    def test_validate_manifest_rejects_max_reviewers_above_the_mode_bound(self) -> None:
        case = {
            "id": "bad-bound",
            "title": "bad bound",
            "mode": "quick",
            "task": "irrelevant",
            "test_expectation": "pass",
            "expected": {"verdict": "PASS", "max_reviewers": 5},
        }
        with self.assertRaises(eval_harness.EvaluationError):
            eval_harness.validate_manifest("bad-bound", case)

    def test_adjudication_reference_states_evidence_and_test_strength_rules(self) -> None:
        adjudication_path = (
            Path(__file__).resolve().parent.parent
            / ".agents"
            / "skills"
            / "verify"
            / "references"
            / "adjudication.md"
        )
        text = adjudication_path.read_text(encoding="utf-8")
        self.assertIn("evidence alone", text)
        self.assertIn("share a premise", text)
        self.assertIn("caller supplied", text)
        self.assertIn("Test-strength observations", text)
        self.assertIn("test-strength on correct code", text)
        line_count = len(text.splitlines())
        self.assertLess(line_count, 200)

    def test_panel_reference_states_invariants_trigger_guard(self) -> None:
        panel_path = (
            Path(__file__).resolve().parent.parent
            / ".agents"
            / "skills"
            / "verify"
            / "references"
            / "panel.md"
        )
        text = panel_path.read_text(encoding="utf-8")
        self.assertIn("not by itself an invariants trigger", text)
        line_count = len(text.splitlines())
        self.assertLess(line_count, 200)

    def test_validate_manifest_rejects_a_retired_reviewer_role(self) -> None:
        case = {
            "id": "bad-reviewer",
            "title": "bad reviewer",
            "mode": "panel",
            "task": "irrelevant",
            "test_expectation": "pass",
            "expected": {
                "verdict": "PASS",
                "required_reviewers": ["adversarial"],
            },
        }
        with self.assertRaises(eval_harness.EvaluationError):
            eval_harness.validate_manifest("bad-reviewer", case)


if __name__ == "__main__":
    unittest.main()
