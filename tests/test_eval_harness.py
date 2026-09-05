import json
from pathlib import Path
import tempfile
import unittest

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

    def test_semantic_scorer_accepts_a_matching_report(self) -> None:
        report = {
            "case_id": "correct-low-risk",
            "verdict": "PASS",
            "assurance": "degraded independence",
            "target": "working-tree diff",
            "contract_summary": {},
            "selected_reviewers": ["acceptance", "test-adequacy"],
            "selection_reasons": {},
            "checks_executed": [],
            "findings": [],
            "evidence_gaps": [],
            "source_unchanged": True,
            "minimum_next_action": "none",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            eval_harness.score_report("correct-low-risk", path)

    def test_semantic_scorer_rejects_a_wrong_verdict(self) -> None:
        report = {
            "case_id": "correct-low-risk",
            "verdict": "FIX REQUIRED",
            "selected_reviewers": ["acceptance", "test-adequacy"],
            "findings": [],
            "evidence_gaps": [],
            "source_unchanged": True,
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaises(eval_harness.EvaluationError):
                eval_harness.score_report("correct-low-risk", path)

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


if __name__ == "__main__":
    unittest.main()
