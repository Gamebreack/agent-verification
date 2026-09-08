#!/usr/bin/env python3
"""Materialize and score behavioral evaluations for the verify skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = ROOT / "evals" / "cases"
SKILL_DIR = ROOT / ".agents" / "skills" / "verify"


class EvaluationError(Exception):
    pass


def run(command: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=check,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def load_case(case_id: str) -> tuple[Path, dict[str, Any]]:
    case_dir = CASES_DIR / case_id
    manifest = case_dir / "case.json"
    if not manifest.is_file():
        raise EvaluationError(f"unknown case: {case_id}")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("id") != case_id:
        raise EvaluationError(f"{manifest}: id must match directory name")
    return case_dir, data


def case_ids() -> list[str]:
    return sorted(path.parent.name for path in CASES_DIR.glob("*/case.json"))


def copy_snapshot(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise EvaluationError(f"missing snapshot: {source}")
    shutil.copytree(source, destination, dirs_exist_ok=True)


def materialize(case_id: str, destination: Path) -> dict[str, Any]:
    case_dir, case = load_case(case_id)
    if destination.exists() and any(destination.iterdir()):
        raise EvaluationError(f"destination is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    copy_snapshot(case_dir / "base", destination)
    run(["git", "init", "-q", "-b", "main"], destination)
    run(["git", "config", "user.name", "Verify Eval"], destination)
    run(["git", "config", "user.email", "verify-eval@example.invalid"], destination)
    exclude = destination / ".git" / "info" / "exclude"
    with exclude.open("a", encoding="utf-8") as handle:
        handle.write("\n.verify/\n.verify-eval/\n")
    run(["git", "add", "."], destination)
    run(["git", "commit", "-q", "-m", "baseline"], destination)
    base_sha = run(["git", "rev-parse", "HEAD"], destination).stdout.strip()
    copy_snapshot(case_dir / "candidate", destination)

    state_file = destination / ".verify" / "state.json"
    if state_file.is_file():
        state_text = state_file.read_text(encoding="utf-8")
        if "0000000000000000000000000000000000000000" in state_text:
            state_text = state_text.replace("0000000000000000000000000000000000000000", base_sha)
            state_file.write_text(state_text, encoding="utf-8")

    eval_dir = destination / ".verify-eval"
    eval_dir.mkdir()
    (eval_dir / "task.md").write_text(case["task"].rstrip() + "\n", encoding="utf-8")
    if claim := case.get("seeded_reviewer_claim"):
        (eval_dir / "reviewer-claim.md").write_text(claim.rstrip() + "\n", encoding="utf-8")
    return case


def prompt_for(case_id: str, destination: Path) -> str:
    _, case = load_case(case_id)
    extra = ""
    if case.get("seeded_reviewer_claim"):
        extra = (
            " Also adjudicate the reviewer claim in "
            f"{destination / '.verify-eval' / 'reviewer-claim.md'}."
        )
    return (
        f"Use $verify in {case['mode']} mode against the working-tree diff in {destination}. "
        f"The authoritative task is {destination / '.verify-eval' / 'task.md'}.{extra} "
        "Return only the machine-readable JSON report defined by "
        f"{SKILL_DIR / 'references' / 'json-report.md'}, set case_id to "
        f"{case_id!r}, and do not read any files outside the materialized repository and the verify skill."
    )


def tree_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for file in sorted(item for item in path.rglob("*") if item.is_file()):
        if ".git" in file.parts or ".verify-eval" in file.parts or "__pycache__" in file.parts:
            continue
        digest.update(str(file.relative_to(path)).encode())
        digest.update(file.read_bytes())
    return digest.hexdigest()


def validate_manifest(case_id: str, case: dict[str, Any]) -> None:
    required = {"id", "title", "mode", "task", "test_expectation", "expected"}
    missing = required - case.keys()
    if missing:
        raise EvaluationError(f"{case_id}: missing manifest keys: {sorted(missing)}")
    expected = case["expected"]
    if expected.get("verdict") not in {"PASS", "PASS WITH NOTES", "FIX REQUIRED", "INCONCLUSIVE"}:
        raise EvaluationError(f"{case_id}: invalid expected verdict")
    if case["test_expectation"] not in {"pass", "unavailable"}:
        raise EvaluationError(f"{case_id}: invalid test_expectation")
    incremental = case.get("incremental")
    if incremental is not None:
        if not isinstance(incremental, dict):
            raise EvaluationError(f"{case_id}: incremental must be an object")
        target_kind = incremental.get("target_kind")
        if target_kind not in {"feature", "subsystem", "workflow", "artifact", "files"}:
            raise EvaluationError(f"{case_id}: invalid incremental.target_kind: {target_kind!r}")
        if not isinstance(incremental.get("expects_incremental", False), bool):
            raise EvaluationError(f"{case_id}: incremental.expects_incremental must be a boolean")
        expected_invalidation = incremental.get("expected_invalidation")
        if expected_invalidation is not None and not isinstance(expected_invalidation, dict):
            raise EvaluationError(f"{case_id}: incremental.expected_invalidation must be an object")
        for key in ("expected_drift", "expected_scope_rejection"):
            value = incremental.get(key)
            if value is not None and not isinstance(value, bool):
                raise EvaluationError(f"{case_id}: incremental.{key} must be a boolean")


def validate_package() -> None:
    errors: list[str] = []
    required_skill_files = [
        SKILL_DIR / "SKILL.md",
        SKILL_DIR / "agents" / "openai.yaml",
        SKILL_DIR / "references" / "verification-contract.md",
        SKILL_DIR / "references" / "reviewer-selection.md",
        SKILL_DIR / "references" / "finding-and-adjudication.md",
        SKILL_DIR / "references" / "json-report.md",
        SKILL_DIR / "references" / "incremental-verification.md",
        SKILL_DIR / "references" / "state-persistence.md",
    ]
    for path in required_skill_files:
        if not path.is_file():
            errors.append(f"missing {path.relative_to(ROOT)}")

    ids = case_ids()
    if not ids:
        errors.append("no behavioral cases found")

    for case_id in ids:
        try:
            _, case = load_case(case_id)
            validate_manifest(case_id, case)
            with tempfile.TemporaryDirectory(prefix=f"verify-{case_id}-") as tmp:
                repo = Path(tmp) / "repo"
                materialize(case_id, repo)
                if case.get("incremental", {}).get("expects_incremental"):
                    state_path = repo / ".verify" / "state.json"
                    if not state_path.is_file():
                        raise EvaluationError(
                            f"{case_id}: incremental case requires base/.verify/state.json"
                        )
                if run(["git", "diff", "--quiet"], repo, check=False).returncode == 0:
                    raise EvaluationError(f"{case_id}: candidate has no working-tree diff")
                before = tree_digest(repo)
                if case["test_expectation"] == "pass":
                    result = run(
                        [sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test*.py"],
                        repo,
                        check=False,
                    )
                    if result.returncode != 0:
                        raise EvaluationError(
                            f"{case_id}: candidate tests should pass but failed\n{result.stdout}{result.stderr}"
                        )
                if tree_digest(repo) != before:
                    raise EvaluationError(f"{case_id}: running tests changed fixture source")
        except (EvaluationError, json.JSONDecodeError) as exc:
            errors.append(str(exc))

    if errors:
        raise EvaluationError("\n".join(errors))
    print(f"PASS: skill package and {len(ids)} behavioral cases are structurally valid")


def normalized_text(value: Any) -> str:
    if isinstance(value, str):
        return value.lower()
    return json.dumps(value, sort_keys=True).lower()


def finding_matches(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    if actual.get("status") != expected.get("status", "VALIDATED"):
        return False
    allowed_ids = set(expected.get("requirement_or_invariant", []))
    actual_ids = {
        value.strip()
        for value in re.split(r"[,/|]", str(actual.get("requirement_or_invariant", "")))
        if value.strip()
    }
    if allowed_ids and not allowed_ids.intersection(actual_ids):
        return False
    allowed_severities = expected.get("severities", [])
    if allowed_severities and actual.get("severity") not in allowed_severities:
        return False
    evidence = normalized_text(actual.get("evidence", []))
    if any(path.lower() not in evidence for path in expected.get("evidence_paths", [])):
        return False
    narrative = normalized_text(
        [actual.get("claim", ""), actual.get("failure_mechanism", ""), actual.get("rejection_reason", "")]
    )
    terms = expected.get("terms_any", [])
    return not terms or any(term.lower() in narrative for term in terms)


def score_report(case_id: str, report_path: Path) -> None:
    _, case = load_case(case_id)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    expected = case["expected"]
    errors: list[str] = []

    if report.get("case_id") != case_id:
        errors.append(f"case_id must be {case_id!r}")
    incremental = case.get("incremental")
    expected_drift = incremental.get("expected_drift") if incremental else False
    if expected_drift:
        if report.get("verdict") not in {"INCONCLUSIVE", "PASS"}:
            errors.append(
                f"drift case verdict: expected INCONCLUSIVE or PASS, got {report.get('verdict')!r}"
            )
        if report.get("incremental"):
            errors.append("drift case must not report incremental: true")
    elif report.get("verdict") != expected["verdict"]:
        errors.append(f"verdict: expected {expected['verdict']!r}, got {report.get('verdict')!r}")
    reviewers = report.get("selected_reviewers", [])
    required_reviewers = expected.get("required_reviewers", [])
    missing_reviewers = sorted(set(required_reviewers) - set(reviewers))
    if missing_reviewers:
        errors.append(f"missing reviewers: {missing_reviewers}")
    if exact := expected.get("exact_reviewers"):
        if set(reviewers) != set(exact):
            errors.append(f"reviewers: expected exactly {sorted(exact)}, got {sorted(reviewers)}")
    if len(reviewers) > expected.get("max_reviewers", 5):
        errors.append(f"selected {len(reviewers)} reviewers; panel bound exceeded")
    forbidden = sorted(set(expected.get("forbidden_reviewers", [])) & set(reviewers))
    if forbidden:
        errors.append(f"forbidden reviewers selected: {forbidden}")

    findings = report.get("findings", [])
    for expected_finding in expected.get("findings", []):
        if not any(finding_matches(actual, expected_finding) for actual in findings):
            errors.append(f"missing semantic finding: {expected_finding.get('name', expected_finding)}")

    gap_kinds = {gap.get("kind") for gap in report.get("evidence_gaps", [])}
    for kind in expected.get("evidence_gap_kinds", []):
        if kind not in gap_kinds:
            errors.append(f"missing evidence gap kind: {kind}")
    if report.get("source_unchanged") is not True:
        errors.append("source_unchanged must be true")

    incremental = case.get("incremental")
    if incremental and incremental.get("expects_incremental"):
        if not incremental.get("expected_drift") and not report.get("incremental"):
            errors.append("report.incremental must be true for incremental cases")
        expected_invalidation = incremental.get("expected_invalidation", {})
        actual_invalidation = report.get("invalidation", {})
        for reviewer, expected_state in expected_invalidation.items():
            actual_state = actual_invalidation.get(reviewer)
            if actual_state != expected_state:
                errors.append(
                    f"invalidation[{reviewer}]: expected {expected_state!r}, got {actual_state!r}"
                )
        if incremental.get("expected_drift"):
            gap_kinds = {gap.get("kind") for gap in report.get("evidence_gaps", [])}
            if "UNAVAILABLE" not in gap_kinds:
                errors.append("drift case must have UNAVAILABLE evidence gap")
        if incremental.get("expected_scope_rejection"):
            has_scope_rejection = any(
                "out-of-target-narrowing" in str(finding.get("rejection_reason", ""))
                for finding in report.get("findings", [])
            )
            if not has_scope_rejection:
                errors.append(
                    "scope rejection case must have at least one finding with "
                    "rejection_reason containing 'out-of-target-narrowing'"
                )

    if errors:
        raise EvaluationError("\n".join(errors))
    print(f"PASS: {case_id} matched its semantic expectations")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="list evaluation cases")
    subparsers.add_parser("validate", help="validate package and fixtures")

    prepare_parser = subparsers.add_parser("prepare", help="materialize a case as a git working tree")
    prepare_parser.add_argument("case_id")
    prepare_parser.add_argument("destination", type=Path)

    prompt_parser = subparsers.add_parser("prompt", help="print the isolated verifier prompt")
    prompt_parser.add_argument("case_id")
    prompt_parser.add_argument("destination", type=Path)

    check_parser = subparsers.add_parser("check", help="score a JSON verifier report")
    check_parser.add_argument("case_id")
    check_parser.add_argument("report", type=Path)

    args = parser.parse_args()
    try:
        if args.command == "list":
            for case_id in case_ids():
                _, case = load_case(case_id)
                print(f"{case_id}\t{case['title']}")
        elif args.command == "validate":
            validate_package()
        elif args.command == "prepare":
            materialize(args.case_id, args.destination.resolve())
            print(prompt_for(args.case_id, args.destination.resolve()))
        elif args.command == "prompt":
            print(prompt_for(args.case_id, args.destination.resolve()))
        elif args.command == "check":
            score_report(args.case_id, args.report)
    except (EvaluationError, json.JSONDecodeError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
