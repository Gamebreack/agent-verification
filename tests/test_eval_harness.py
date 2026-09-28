import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import eval_harness


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
        report = {
            "case_id": "correct-low-risk",
            "verdict": "PASS",
            "assurance": "degraded independence",
            "target": "working-tree diff",
            "contract_summary": {},
            "selected_reviewers": ["acceptance", "tests"],
            "selection_reasons": {},
            "checks_executed": [],
            "findings": [],
            "evidence_gaps": [],
            "source_unchanged": True,
            "minimum_next_action": "none",
        }
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            eval_harness.materialize("correct-low-risk", repo)
            report_path = Path(tmp) / "report.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            eval_harness.score_report("correct-low-risk", report_path, repo)

    def test_semantic_scorer_rejects_a_wrong_verdict(self) -> None:
        report = {
            "case_id": "correct-low-risk",
            "verdict": "FIX REQUIRED",
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
            with self.assertRaises(eval_harness.EvaluationError):
                eval_harness.score_report("correct-low-risk", report_path, repo)

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
        report = {
            "case_id": "correct-low-risk",
            "verdict": "PASS",
            "selected_reviewers": ["acceptance", "tests"],
            "findings": [],
            "evidence_gaps": [],
            "source_unchanged": True,
            "criteria": [{"id": "A1", "result": "PASS", "evidence": "status.py:1"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            eval_harness.materialize("correct-low-risk", repo)
            report_path = Path(tmp) / "report.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")

            with patch.object(eval_harness, "load_case", return_value=(real_case_dir, fake_case)):
                with self.assertRaises(eval_harness.EvaluationError) as ctx:
                    eval_harness.score_report("correct-low-risk", report_path, repo)
            self.assertIn("criteria[A1]", str(ctx.exception))

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
