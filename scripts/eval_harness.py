#!/usr/bin/env python3
"""Materialize and score behavioral evaluations for the verify skill."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
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
    # `shutil.copy`, not the default `copy2`: preserving source mtimes lets an
    # overlay replace a same-size file with an identical mtime, which git's stat
    # cache then treats as unchanged (wrong status, layer missing from a commit).
    shutil.copytree(source, destination, dirs_exist_ok=True, copy_function=shutil.copy)


EVAL_DIR = ".verify-eval"


@dataclass(frozen=True)
class Layer:
    """One step of a case's materialization, in `layers(case)` order.

    Snapshot layers (`base`, `branch_commit`, `previous`, `staged`, `candidate`)
    name a directory relative to the case directory and are additive overlays.
    `artifact` layers are evaluation files written under `.verify-eval/`.
    """

    kind: str
    source: str | None = None
    path: str | None = None
    content: str | None = None


def layers(case: dict[str, Any]) -> list[Layer]:
    """The single ordered layer list that drives both `materialize` and
    `reference_tree_digest`: base, each branch commit, previous, staged,
    candidate, then artifact files."""
    ordered = [Layer("base", "base")]
    ordered += [Layer("branch_commit", name) for name in case.get("branch_commits", [])]
    if previous := case.get("previous"):
        ordered.append(Layer("previous", previous))
    if staged := case.get("staged"):
        ordered.append(Layer("staged", staged))
    ordered.append(Layer("candidate", "candidate"))
    ordered.append(Layer("artifact", path=TASK_FILE, content=task_text(case)))
    if claim := case.get("seeded_reviewer_claim"):
        ordered.append(
            Layer("artifact", path=f"{EVAL_DIR}/reviewer-claim.md", content=claim.rstrip() + "\n")
        )
    if note := case.get("handoff_note"):
        ordered.append(Layer("artifact", path=HANDOFF_FILE, content=note.rstrip() + "\n"))
    if (prior := case.get("prior_report")) is not None:
        # The template; `materialize` injects the real verified state into it.
        ordered.append(Layer("artifact", path=PRIOR_REPORT_FILE, content=json.dumps(prior, indent=2) + "\n"))
    return ordered


TASK_FILE = f"{EVAL_DIR}/task.md"
HANDOFF_FILE = f"{EVAL_DIR}/handoff.md"
PRIOR_REPORT_FILE = f"{EVAL_DIR}/prior-report.json"


def task_text(case: dict[str, Any]) -> str:
    return case["task"].rstrip() + "\n"


def snapshot_files(case_dir: Path, name: str) -> list[str]:
    """Relative POSIX paths of the files a snapshot layer contributes."""
    root = snapshot_dir(case_dir, name)
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )


def inject_verified_state(prior: dict[str, Any], head: str, files: dict[str, str]) -> str:
    report = json.loads(json.dumps(prior))
    report["verified_state"] = {"head": head, "files": files}
    return json.dumps(report, indent=2) + "\n"


def snapshot_dir(case_dir: Path, name: str) -> Path:
    path = (case_dir / name).resolve()
    if path == case_dir.resolve() or case_dir.resolve() not in path.parents:
        raise EvaluationError(f"snapshot must be a directory inside the case: {name!r}")
    return path


def write_layer(case_dir: Path, layer: Layer, destination: Path, content: str | None = None) -> None:
    """Apply a layer's working-tree content; git actions belong to `materialize`.
    `content` overrides an artifact layer's content (the injected prior report)."""
    if layer.kind == "artifact":
        target = destination / layer.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(layer.content if content is None else content, encoding="utf-8")
    else:
        copy_snapshot(snapshot_dir(case_dir, layer.source), destination)


# A remote URL that never resolves: it names a path inside `.git` that the
# harness never creates, so `git fetch` fails without touching the network.
UNREACHABLE_REMOTE = "verify-eval-unreachable-origin"


def setup_origin(destination: Path, baseline: str) -> None:
    """Local remote-tracking refs for `origin: {default: main, upstream: feature}`:
    `origin/main` at the baseline, `origin/feature` at the feature tip,
    `origin/HEAD` -> `origin/main`, the feature branch tracking `origin/feature`,
    no reachable remote, and local `main` deleted, so only the `origin/HEAD`
    rule finds the base and `@{upstream}..HEAD` is empty."""
    unreachable = destination / ".git" / UNREACHABLE_REMOTE
    for command in (
        ["git", "config", "remote.origin.url", str(unreachable)],
        ["git", "config", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*"],
        ["git", "update-ref", "refs/remotes/origin/main", baseline],
        ["git", "update-ref", "refs/remotes/origin/feature", "HEAD"],
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main"],
        ["git", "config", "branch.feature.remote", "origin"],
        ["git", "config", "branch.feature.merge", "refs/heads/feature"],
        ["git", "branch", "-q", "-D", "main"],
    ):
        run(command, destination)


def materialize(case_id: str, destination: Path) -> dict[str, Any]:
    case_dir, case = load_case(case_id)
    if destination.exists() and any(destination.iterdir()):
        raise EvaluationError(f"destination is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    branch_commits = 0
    baseline = ""
    verified: tuple[str, dict[str, str]] | None = None
    origin_pending = bool(case.get("origin"))
    for layer in layers(case):
        if origin_pending and layer.kind in {"staged", "candidate"}:
            setup_origin(destination, baseline)
            origin_pending = False
        content = None
        if layer.path == PRIOR_REPORT_FILE:
            if verified is None:
                raise EvaluationError(f"{case_id}: prior_report requires a previous snapshot")
            content = inject_verified_state(case["prior_report"], *verified)
        write_layer(case_dir, layer, destination, content)
        if layer.kind == "base":
            run(["git", "init", "-q", "-b", "main"], destination)
            run(["git", "config", "user.name", "Verify Eval"], destination)
            run(["git", "config", "user.email", "verify-eval@example.invalid"], destination)
            exclude = destination / ".git" / "info" / "exclude"
            with exclude.open("a", encoding="utf-8") as handle:
                handle.write(f"\n{EVAL_DIR}/\n")
            run(["git", "add", "."], destination)
            run(["git", "commit", "-q", "-m", "baseline"], destination)
            baseline = run(["git", "rev-parse", "HEAD"], destination).stdout.strip()
        elif layer.kind == "branch_commit":
            if branch_commits == 0:
                run(["git", "checkout", "-q", "-b", "feature"], destination)
            branch_commits += 1
            run(["git", "add", "-A"], destination)
            run(
                ["git", "commit", "-q", "--allow-empty", "-m", f"branch commit {branch_commits}: {layer.source}"],
                destination,
            )
        elif layer.kind == "previous":
            run(["git", "add", "-A"], destination)
            run(["git", "commit", "-q", "--allow-empty", "-m", "verified state"], destination)
            head = run(["git", "rev-parse", "HEAD"], destination).stdout.strip()
            verified = (head, blob_ids(destination, snapshot_files(case_dir, layer.source), commit=head))
        elif layer.kind == "staged":
            run(["git", "add", "-A"], destination)

    # Informational only: `check` never trusts this file, since it lives inside the
    # repository the verifier could itself write. It re-materializes the reference
    # tree instead. See `reference_tree_digest`.
    (destination / EVAL_DIR / "digest").write_text(tree_digest(destination), encoding="utf-8")
    return case


def prompt_for(case_id: str, destination: Path) -> str:
    _, case = load_case(case_id)
    extra = ""
    if case.get("seeded_reviewer_claim"):
        extra += (
            " Also adjudicate the reviewer claim in "
            f"{destination / '.verify-eval' / 'reviewer-claim.md'}."
        )
    if case.get("handoff_note"):
        extra += f" The implementer's note is {destination / HANDOFF_FILE}."
    if case.get("reviewer_capability") == "no-shell":
        extra += " Reviewers in this run cannot execute commands; only the lead can run commands."
    if case.get("prior_report") is not None:
        # Neutral on purpose: whether the run is a re-check is the verifier's call
        # (adjudication.md#re-check eligibility), not the prompt's.
        extra += (
            " A prior FIX REQUIRED report from an earlier verify run is supplied with this "
            f"invocation: {destination / PRIOR_REPORT_FILE}."
        )
    target = case.get("target")
    if isinstance(target, dict) and target.get("kind") == "artifact":
        target_text = f"against the artifact target {destination / target['path']} in {destination}"
    elif case.get("branch_commits"):
        target_text = f"against the default target in {destination}"
    else:
        target_text = f"against the working-tree diff in {destination}"
    task_path = destination / TASK_FILE
    return (
        f"Use the verify skill in {case['mode']} mode with --contract {task_path} "
        f"{target_text}. "
        f"The authoritative task is {task_path}.{extra} "
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
        digest.update(b"\0")
        digest.update(file.read_bytes())
    return digest.hexdigest()


def reference_tree_digest(case_id: str) -> str:
    """Recompute the expected tree digest by re-applying every layer the case
    defines (`layers(case)`, in order) from the case's own snapshots, independent
    of anything the verifier could have written into a `check`-time repo
    (including a stale or edited digest file). Git actions do not change the
    working tree, so overlaying the layers reproduces `materialize`'s tree."""
    case_dir, case = load_case(case_id)
    with tempfile.TemporaryDirectory(prefix=f"verify-ref-{case_id}-") as tmp:
        reference = Path(tmp) / "reference"
        reference.mkdir()
        for layer in layers(case):
            write_layer(case_dir, layer, reference)
        return tree_digest(reference)


def git_state(repo: Path) -> dict[str, str]:
    """Read-only, timestamp-free views of the repository state a verifier must not
    write: the branch HEAD names, HEAD's history (tree and subject per commit),
    HEAD's reflog (any commit, reset, checkout or stash adds an entry), and the
    index entries (mode, blob, stage, path; stat data is excluded, so a refresh
    by `git status` is not a change)."""

    def out(*args: str) -> str:
        return run(["git", *args], repo, check=False).stdout

    return {
        "HEAD ref": out("symbolic-ref", "-q", "HEAD"),
        "HEAD history": out("log", "--format=%T %s", "HEAD"),
        "HEAD reflog": out("reflog", "show", "--format=%gs", "HEAD"),
        "index": out("ls-files", "-s", "-z"),
    }


@dataclass(frozen=True)
class ReferenceState:
    git: dict[str, str]
    head: str
    artifacts: dict[str, str]


def reference_state(case_id: str) -> ReferenceState:
    """Materialize the case afresh (outside anything the verifier can write) and
    record its git state, HEAD, and the injected `.verify-eval/` artifacts."""
    case_dir, case = load_case(case_id)
    with tempfile.TemporaryDirectory(prefix=f"verify-ref-git-{case_id}-") as tmp:
        reference = Path(tmp) / "reference"
        materialize(case_id, reference)
        artifacts = {
            layer.path: (reference / layer.path).read_text(encoding="utf-8")
            for layer in layers(case)
            if layer.kind == "artifact"
        }
        head = run(["git", "rev-parse", "HEAD"], reference).stdout.strip()
        return ReferenceState(git_state(reference), head, artifacts)


def repository_state_errors(case_id: str, case: dict[str, Any], repo: Path) -> list[str]:
    """Writes to the index, HEAD, or an injected artifact since materialization.
    Commit ids carry timestamps, so HEAD is compared through its history, ref
    name and reflog; the prior report's recorded head must be the repo's HEAD."""
    reference = reference_state(case_id)
    current = git_state(repo)
    errors = [
        f"{case_id}: git {aspect} changed since materialization"
        for aspect, value in reference.git.items()
        if current.get(aspect) != value
    ]
    head = run(["git", "rev-parse", "--verify", "-q", "HEAD"], repo, check=False).stdout.strip()
    for path, expected in reference.artifacts.items():
        if path == PRIOR_REPORT_FILE:
            files = json.loads(expected)["verified_state"]["files"]
            expected = inject_verified_state(case["prior_report"], head, files)
        target = repo / path
        if not target.is_file() or target.read_text(encoding="utf-8") != expected:
            errors.append(f"{case_id}: {path} differs from the injected artifact")
    return errors


VALID_MODES = {"quick", "panel", "release"}
VALID_REVIEWERS = {"acceptance", "tests", "regression", "invariants", "security"}
MODE_MAX = {"quick": 2, "panel": 4, "release": 5}
VERDICTS = {"PASS", "PASS WITH NOTES", "FIX REQUIRED", "INCONCLUSIVE"}
BLOCKING_SEVERITIES = {"BLOCKER", "SHOULD_FIX"}
PROPOSED_SEVERITIES = {"BLOCKER", "SHOULD_FIX", "OPTIONAL"}
VALID_EXECUTIONS = {"executed", "static"}
VALID_DISPOSITIONS = {"adjudicated", "open_lead"}
VALID_RESOLUTIONS = {"resolved", "unresolved"}
REQUIRED_REPORT_KEYS = ("verified_state", "recheck", "out_of_mandate", "checks_not_run", "effective_mode")


def unresolved_recheck_ids(report: dict[str, Any] | None) -> set[str]:
    """Ids a report's own `recheck.prior_findings` marks `unresolved`."""
    recheck = report.get("recheck") if isinstance(report, dict) else None
    entries = recheck.get("prior_findings") if isinstance(recheck, dict) else None
    return {
        str(entry.get("id"))
        for entry in (entries if isinstance(entries, list) else [])
        if isinstance(entry, dict) and entry.get("resolution") == "unresolved"
    }


def open_prior_finding_ids(prior: dict[str, Any] | None) -> set[str]:
    """Ids of the open findings of a prior report: its validated BLOCKER/SHOULD_FIX
    findings plus, when the prior report was itself a re-check, every earlier
    finding it adjudicated `unresolved` (an unresolved finding stays open)."""
    if not prior:
        return set()
    return {
        str(finding.get("id"))
        for finding in prior.get("findings", [])
        if finding.get("status") == "VALIDATED" and finding.get("severity") in BLOCKING_SEVERITIES
    } | unresolved_recheck_ids(prior)


RECHECK_EXPECTATION_KEYS = ("recheck_roles", "recheck_optional_roles", "recheck_unresolved", "another_round_required")
BLOB_ID_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
CONTRACT_SOURCE_RE = re.compile(r"^\s*--contract\b")


def contract_file_source(summary: Any) -> bool:
    """Whether a `contract_summary` names a `--contract` file as its source."""
    return isinstance(summary, dict) and bool(CONTRACT_SOURCE_RE.match(str(summary.get("source_of_truth") or "")))


def contract_blob_id(repo: Path) -> str:
    """The blob id of the materialized contract file (`git hash-object`, no `-w`)."""
    return run(["git", "hash-object", "--", TASK_FILE], repo).stdout.strip()


def criteria_text_errors(criteria: Any, where: str) -> list[str]:
    """Each criterion must carry its id and full text, so a re-check can reuse it."""
    if not isinstance(criteria, list):
        return [f"{where} must be a list"]
    return [
        f"{where}[{index}] needs a non-empty id and text"
        for index, entry in enumerate(criteria)
        if not (isinstance(entry, dict) and non_empty(entry.get("id")) and non_empty(entry.get("text")))
    ]


def recheck_eligibility_errors(prior: Any, contract_hash: str) -> list[str]:
    """Why `prior` cannot make this run a re-check (adjudication.md#re-check):
    it must be a `FIX REQUIRED` report with a `verified_state`, and its contract
    source must be unchanged. An evaluation supplies no conversation, so only a
    `--contract` source qualifies, compared by `source_hash` with the blob id of
    the contract file the invocation passes, never by path."""
    if not isinstance(prior, dict):
        return ["no prior report"]
    errors = []
    if prior.get("verdict") != "FIX REQUIRED":
        errors.append(f"prior verdict is {prior.get('verdict')!r}, not 'FIX REQUIRED'")
    if not isinstance(prior.get("verified_state"), dict):
        errors.append("prior report has no verified_state")
    summary = prior.get("contract_summary")
    if not contract_file_source(summary):
        errors.append("prior contract source is not a --contract file")
    elif summary.get("source_hash") != contract_hash:
        errors.append(
            f"prior contract_summary.source_hash {summary.get('source_hash')!r} differs from "
            f"the contract file's blob id {contract_hash!r}"
        )
    return errors


def validate_manifest(case_id: str, case: dict[str, Any]) -> None:
    required = {"id", "title", "mode", "task", "test_expectation", "expected"}
    missing = required - case.keys()
    if missing:
        raise EvaluationError(f"{case_id}: missing manifest keys: {sorted(missing)}")
    if case["mode"] not in VALID_MODES:
        raise EvaluationError(f"{case_id}: invalid mode: {case['mode']!r}")
    expected = case["expected"]
    if expected.get("verdict") not in {"PASS", "PASS WITH NOTES", "FIX REQUIRED", "INCONCLUSIVE"}:
        raise EvaluationError(f"{case_id}: invalid expected verdict")
    if case["test_expectation"] not in {"pass", "fail", "unavailable"}:
        raise EvaluationError(f"{case_id}: invalid test_expectation")
    branch_commits = case.get("branch_commits", [])
    if not isinstance(branch_commits, list) or not all(
        isinstance(name, str) and name for name in branch_commits
    ):
        raise EvaluationError(f"{case_id}: branch_commits must be a list of snapshot directory names")
    for key in ("previous", "staged"):
        if key in case and not (isinstance(case[key], str) and case[key]):
            raise EvaluationError(f"{case_id}: {key} must be a snapshot directory name")
    if "origin" in case:
        if case["origin"] != {"default": "main", "upstream": "feature"}:
            raise EvaluationError(f"{case_id}: origin must be {{default: main, upstream: feature}}")
        if not branch_commits:
            raise EvaluationError(f"{case_id}: origin requires branch_commits")
    if "target" in case:
        target = case["target"]
        path = target.get("path") if isinstance(target, dict) else None
        if not (
            isinstance(target, dict)
            and target.get("kind") == "artifact"
            and isinstance(path, str)
            and path
            and not Path(path).is_absolute()
            and ".." not in Path(path).parts
        ):
            raise EvaluationError(f"{case_id}: target must be {{kind: artifact, path: <relative path>}}")
    if "reviewer_capability" in case and case["reviewer_capability"] != "no-shell":
        raise EvaluationError(f"{case_id}: reviewer_capability must be 'no-shell'")
    if "handoff_note" in case and not (isinstance(case["handoff_note"], str) and case["handoff_note"].strip()):
        raise EvaluationError(f"{case_id}: handoff_note must be non-empty text")
    prior = case.get("prior_report")
    if prior is not None:
        if not case.get("previous"):
            raise EvaluationError(f"{case_id}: prior_report requires a previous snapshot")
        if not (isinstance(prior, dict) and isinstance(prior.get("findings"), list)):
            raise EvaluationError(f"{case_id}: prior_report must be a report object with findings")
        if prior.get("verdict") != "FIX REQUIRED":
            raise EvaluationError(f"{case_id}: prior_report must be a FIX REQUIRED report")
        summary = prior.get("contract_summary")
        if not (contract_file_source(summary) and BLOB_ID_RE.match(str(summary.get("source_hash") or ""))):
            raise EvaluationError(
                f"{case_id}: prior_report.contract_summary must name a --contract source with a blob-id source_hash"
            )
        criteria_errors = criteria_text_errors(prior.get("criteria"), "prior_report.criteria")
        if not prior.get("criteria") or criteria_errors:
            raise EvaluationError(
                f"{case_id}: prior_report.criteria must list each criterion with its full text {criteria_errors}"
            )
    for key in RECHECK_EXPECTATION_KEYS:
        if key in expected and prior is None:
            raise EvaluationError(f"{case_id}: expected.{key} requires prior_report")
    if "recheck_optional_roles" in expected:
        if "recheck_roles" not in expected:
            raise EvaluationError(f"{case_id}: expected.recheck_optional_roles requires recheck_roles")
        overlap = sorted(set(expected["recheck_optional_roles"]) & set(expected["recheck_roles"]))
        if overlap:
            raise EvaluationError(f"{case_id}: expected.recheck_optional_roles repeats recheck_roles: {overlap}")
    if "recheck_unresolved" in expected:
        unknown = sorted(set(expected["recheck_unresolved"]) - open_prior_finding_ids(prior))
        if unknown:
            raise EvaluationError(f"{case_id}: recheck_unresolved names no open prior finding: {unknown}")
    if "another_round_required" in expected and not isinstance(expected["another_round_required"], bool):
        raise EvaluationError(f"{case_id}: expected.another_round_required must be a boolean")
    effective_mode = expected.get("effective_mode", case["mode"])
    if effective_mode not in VALID_MODES:
        raise EvaluationError(f"{case_id}: invalid expected.effective_mode: {effective_mode!r}")
    for key in ("required_reviewers", "exact_reviewers", "forbidden_reviewers", "recheck_roles", "recheck_optional_roles"):
        names = expected.get(key)
        if names is None:
            continue
        invalid = sorted(set(names) - VALID_REVIEWERS)
        if invalid:
            raise EvaluationError(f"{case_id}: invalid reviewer name(s) in {key}: {invalid}")
    max_reviewers = expected.get("max_reviewers")
    if max_reviewers is not None:
        bound = MODE_MAX[effective_mode]
        if max_reviewers > bound:
            raise EvaluationError(
                f"{case_id}: expected.max_reviewers ({max_reviewers}) exceeds the "
                f"{effective_mode} mode bound ({bound})"
            )
    for check in expected.get("checks", []):
        if not (
            isinstance(check, dict)
            and check.get("execution") in VALID_EXECUTIONS
            and isinstance(check.get("command_terms", []), list)
        ):
            raise EvaluationError(f"{case_id}: invalid expected.checks entry: {check!r}")
    for entry in expected.get("out_of_mandate_terms", []):
        if isinstance(entry, dict):
            if not entry.get("term") or entry.get("disposition", "adjudicated") not in VALID_DISPOSITIONS:
                raise EvaluationError(f"{case_id}: invalid expected.out_of_mandate_terms entry: {entry!r}")
        elif not (isinstance(entry, str) and entry):
            raise EvaluationError(f"{case_id}: invalid expected.out_of_mandate_terms entry: {entry!r}")
    for key in ("scope_not_covered_terms", "next_action_or_gap_terms"):
        terms = expected.get(key, [])
        if not (isinstance(terms, list) and all(isinstance(term, str) and term for term in terms)):
            raise EvaluationError(f"{case_id}: expected.{key} must be a list of non-empty strings")
    prior_ids = {str(finding.get("id")) for finding in (prior or {}).get("findings", [])}
    for finding in expected.get("findings", []):
        invalid = sorted(set(finding.get("proposed_severities", [])) - PROPOSED_SEVERITIES)
        if invalid:
            raise EvaluationError(f"{case_id}: invalid proposed_severities: {invalid}")
        if "id" in finding and finding["id"] not in prior_ids:
            raise EvaluationError(f"{case_id}: expected finding id {finding['id']!r} names no prior finding")


# Host, agent-type and model names the skill must not mention (repo rule: the
# skill stays host-agnostic). Matched case-insensitively on word boundaries, so
# "gpt" also catches "GPT-4o" but not "gptools". Ambiguous common words (for
# example "cursor", "explore", "plan") are deliberately left out.
HOST_DENYLIST = (
    # hosts and vendors
    "anthropic", "openai", "claude", "chatgpt", "codex", "opencode", "copilot",
    "windsurf", "aider", "cline", "devin", "junie", "vscode", "jetbrains",
    # model families
    "gpt", "gemini", "opus", "sonnet", "haiku", "llama", "mistral", "mixtral",
    "deepseek", "qwen", "grok",
    # agent types
    "subagent_type", "general-purpose", "mao",
)
HOST_DENYLIST_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(term) for term in HOST_DENYLIST) + r")\b",
    re.IGNORECASE,
)
SKILL_MAX_LINES = 110
REFERENCE_LINE_LIMIT = 200  # exclusive: every reference file has fewer lines
ROLE_MAX_LINES = 30


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def skill_package_errors(skill_dir: Path) -> list[str]:
    """Structural checks on a verify skill directory: required and stale files,
    the host-agnostic denylist, and the line budgets."""
    errors: list[str] = []

    def shown(path: Path) -> str:
        try:
            return str(path.resolve().relative_to(ROOT))
        except ValueError:
            return str(Path(skill_dir.name) / path.relative_to(skill_dir))

    references_dir = skill_dir / "references"
    reviewers_dir = references_dir / "reviewers"
    reviewer_roles = ["acceptance", "tests", "regression", "invariants", "security"]
    required_skill_files = [
        skill_dir / "SKILL.md",
        references_dir / "verification-contract.md",
        references_dir / "panel.md",
        references_dir / "adjudication.md",
        references_dir / "json-report.md",
        *(reviewers_dir / f"{role}.md" for role in reviewer_roles),
    ]
    for path in required_skill_files:
        if not path.is_file():
            errors.append(f"missing {shown(path)}")

    if references_dir.is_dir():
        allowed = {path.resolve() for path in required_skill_files if str(path).startswith(str(references_dir))}
        for path in references_dir.rglob("*"):
            if path.is_file() and path.resolve() not in allowed:
                errors.append(f"stale reference file: {shown(path)}")

    if skill_dir.is_dir():
        for path in sorted(item for item in skill_dir.rglob("*") if item.is_file()):
            relative = str(path.relative_to(skill_dir))
            terms = {match.group(0).lower() for match in HOST_DENYLIST_RE.finditer(relative)}
            text = path.read_text(encoding="utf-8", errors="replace")
            terms |= {match.group(0).lower() for match in HOST_DENYLIST_RE.finditer(text)}
            if terms:
                errors.append(f"host-specific term(s) {sorted(terms)} in {shown(path)}")

    skill_file = skill_dir / "SKILL.md"
    if skill_file.is_file() and (count := line_count(skill_file)) > SKILL_MAX_LINES:
        errors.append(f"{shown(skill_file)} has {count} lines; budget is at most {SKILL_MAX_LINES}")
    if references_dir.is_dir():
        for path in sorted(item for item in references_dir.rglob("*") if item.is_file()):
            count = line_count(path)
            if count >= REFERENCE_LINE_LIMIT:
                errors.append(
                    f"{shown(path)} has {count} lines; reference files must have fewer than {REFERENCE_LINE_LIMIT}"
                )
            if reviewers_dir in path.parents and count > ROLE_MAX_LINES:
                errors.append(f"{shown(path)} has {count} lines; role files have at most {ROLE_MAX_LINES}")
    return errors


def check_target_present(case_id: str, case: dict[str, Any], repo: Path) -> None:
    """A materialized case must give the verifier something to verify: a
    non-empty `git status --porcelain` (untracked files count; `.verify-eval/`
    is excluded through `.git/info/exclude`), branch commits, or an artifact
    target that exists in the materialized tree."""
    if run(["git", "status", "--porcelain"], repo).stdout.strip():
        return
    if case.get("branch_commits"):
        return
    target = case.get("target")
    if isinstance(target, dict) and target.get("kind") == "artifact" and target.get("path"):
        artifact = (repo / target["path"]).resolve()
        if repo.resolve() in artifact.parents and artifact.is_file():
            return
    raise EvaluationError(
        f"{case_id}: no target content (clean working tree, no branch commits, no existing artifact target)"
    )


def recheck_fixture_errors(case_id: str, case_dir: Path, case: dict[str, Any], repo: Path) -> list[str]:
    """A fixture that expects a re-check must supply an eligible prior report: its
    `source_hash` equals the blob id of the materialized contract file. Every open
    prior finding must name at least one existing file in its evidence, or the
    open-finding paths the scorer requires would silently shrink."""
    if case.get("prior_report") is None:
        return []
    errors: list[str] = []
    if any(key in case["expected"] for key in RECHECK_EXPECTATION_KEYS):
        errors += [
            f"{case_id}: prior_report is not re-check eligible: {reason}"
            for reason in recheck_eligibility_errors(
                json.loads((repo / PRIOR_REPORT_FILE).read_text(encoding="utf-8")), contract_blob_id(repo)
            )
        ]
    for finding_id, paths in sorted(open_finding_files_by_id(case_dir, case, repo).items()):
        if not paths:
            errors.append(f"{case_id}: open prior finding {finding_id} names no existing file in its evidence")
    return errors


def validate_package() -> None:
    errors = skill_package_errors(SKILL_DIR)

    ids = case_ids()
    if not ids:
        errors.append("no behavioral cases found")

    for case_id in ids:
        try:
            case_dir, case = load_case(case_id)
            validate_manifest(case_id, case)
            with tempfile.TemporaryDirectory(prefix=f"verify-{case_id}-") as tmp:
                repo = Path(tmp) / "repo"
                materialize(case_id, repo)
                check_target_present(case_id, case, repo)
                errors += recheck_fixture_errors(case_id, case_dir, case, repo)
                before = tree_digest(repo)
                if case["test_expectation"] in {"pass", "fail"}:
                    result = run(
                        [sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test*.py"],
                        repo,
                        check=False,
                    )
                    output = f"{result.stdout}{result.stderr}"
                    if case["test_expectation"] == "pass" and result.returncode != 0:
                        raise EvaluationError(f"{case_id}: candidate tests should pass but failed\n{output}")
                    if case["test_expectation"] == "fail" and (
                        result.returncode == 0 or "FAILED (" not in output
                    ):
                        raise EvaluationError(f"{case_id}: candidate tests should fail but did not\n{output}")
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


def finding_matches(
    actual: dict[str, Any], expected: dict[str, Any], criteria: list[Any] | None = None
) -> bool:
    if actual.get("status") != expected.get("status", "VALIDATED"):
        return False
    # A re-emitted or carried-forward prior finding keeps its original id.
    if "id" in expected and str(actual.get("id")) != expected["id"]:
        return False
    allowed_ids = set(expected.get("requirement_or_invariant", []))
    actual_ids = {
        value.strip()
        for value in re.split(r"[,/|]", str(actual.get("requirement_or_invariant", "")))
        if value.strip()
    }
    # A finding may link a criterion id (A1); it covers the ids its criterion text names.
    for entry in criteria if isinstance(criteria, list) else []:
        if isinstance(entry, dict) and str(entry.get("id", "")).strip() in actual_ids:
            actual_ids.update(re.findall(r"[RIPE]\d+", str(entry.get("text", ""))))
    if allowed_ids and not allowed_ids.intersection(actual_ids):
        return False
    allowed_severities = expected.get("severities", [])
    if allowed_severities and actual.get("severity") not in allowed_severities:
        return False
    proposed = expected.get("proposed_severities", [])
    if proposed and actual.get("proposed_severity") not in proposed:
        return False
    evidence = normalized_text(actual.get("evidence", []))
    if any(path.lower() not in evidence for path in expected.get("evidence_paths", [])):
        return False
    narrative = normalized_text(
        [actual.get("claim", ""), actual.get("failure_mechanism", ""), actual.get("rejection_reason", "")]
    )
    terms = expected.get("terms_any", [])
    return not terms or any(term.lower() in narrative for term in terms)


def non_empty(value: Any) -> bool:
    """A non-empty string, or a non-empty list holding at least one non-empty string."""
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(isinstance(item, str) and item.strip() for item in value)
    return False


def report_consistency_errors(report: dict[str, Any]) -> list[str]:
    """Rules every v0.5 report must satisfy, whatever the case expects."""
    errors: list[str] = []
    missing = [key for key in REQUIRED_REPORT_KEYS if key not in report]
    if missing:
        errors.append(f"missing report keys: {missing}")
    verdict = report.get("verdict")
    if verdict not in VERDICTS:
        errors.append(f"verdict {verdict!r} is not one of {sorted(VERDICTS)}")

    findings = report.get("findings", [])
    blocking = sorted(
        str(finding.get("id"))
        for finding in findings
        if finding.get("status") == "VALIDATED" and finding.get("severity") in BLOCKING_SEVERITIES
    )
    missing_gaps = [gap for gap in report.get("evidence_gaps", []) if gap.get("kind") == "MISSING"]
    if verdict in {"PASS", "PASS WITH NOTES"} and (blocking or missing_gaps):
        errors.append(
            f"verdict {verdict!r} with open validated BLOCKER/SHOULD_FIX {blocking} "
            f"or {len(missing_gaps)} MISSING gap(s)"
        )
    unresolved = sorted(unresolved_recheck_ids(report))
    if verdict in {"PASS", "PASS WITH NOTES"} and unresolved:
        errors.append(f"verdict {verdict!r} with unresolved prior finding(s) {unresolved}")
    if verdict == "FIX REQUIRED" and not re.search(
        r"\bre-?check", str(report.get("minimum_next_action") or ""), re.IGNORECASE
    ):
        errors.append("FIX REQUIRED minimum_next_action must name the re-check")

    for finding in findings:
        name = finding.get("id", finding.get("claim", "?"))
        proposed = finding.get("proposed_severity")
        if finding.get("reviewer") != "lead" and proposed is None:
            errors.append(f"finding {name}: proposed_severity is required unless reviewer is 'lead'")
        if proposed is not None and proposed not in PROPOSED_SEVERITIES:
            errors.append(f"finding {name}: invalid proposed_severity {proposed!r}")
        if proposed is not None and finding.get("severity") != proposed:
            if finding.get("severity") == "NON_ISSUE":
                if not non_empty(finding.get("rejection_reason")):
                    errors.append(f"finding {name}: NON_ISSUE needs a non-empty rejection_reason")
            elif not non_empty(finding.get("severity_change_reason")):
                errors.append(
                    f"finding {name}: severity {proposed} -> {finding.get('severity')} "
                    "needs a non-empty severity_change_reason"
                )

    out_of_mandate = report.get("out_of_mandate")
    for note in out_of_mandate if isinstance(out_of_mandate, list) else []:
        if note.get("disposition") not in VALID_DISPOSITIONS:
            errors.append(f"out_of_mandate note {note.get('note')!r}: invalid disposition {note.get('disposition')!r}")
    if "out_of_mandate" in report and not isinstance(out_of_mandate, list):
        errors.append("out_of_mandate must be a list")

    for check in report.get("checks_executed", []):
        label = check.get("command_or_inspection", "?")
        if check.get("execution") not in VALID_EXECUTIONS:
            errors.append(f"check {label!r}: execution must be one of {sorted(VALID_EXECUTIONS)}")
        if not non_empty(check.get("run_by")):
            errors.append(f"check {label!r}: run_by is required")

    summary = report.get("contract_summary")
    if not (isinstance(summary, dict) and non_empty(summary.get("source_of_truth"))):
        errors.append("contract_summary.source_of_truth must be a non-empty string")
    elif contract_file_source(summary) and not BLOB_ID_RE.match(str(summary.get("source_hash") or "")):
        errors.append("contract_summary.source_hash must be the --contract file's blob id")
    errors += criteria_text_errors(report.get("criteria", []), "criteria")

    scope = report.get("scope")
    if not (isinstance(scope, dict) and scope.get("covered")):
        errors.append("scope.covered must be non-empty")
    return errors


def check_matches(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    if actual.get("execution") != expected.get("execution"):
        return False
    if "run_by" in expected and str(actual.get("run_by", "")).lower() != expected["run_by"].lower():
        return False
    command = normalized_text(actual.get("command_or_inspection", ""))
    return all(term.lower() in command for term in expected.get("command_terms", []))


def out_of_mandate_errors(report: dict[str, Any], expected_terms: list[Any]) -> list[str]:
    notes = report.get("out_of_mandate")
    notes = notes if isinstance(notes, list) else []
    errors = []
    for entry in expected_terms:
        term, disposition = (entry, None) if isinstance(entry, str) else (entry["term"], entry.get("disposition"))
        if not any(
            term.lower() in normalized_text(note.get("note", ""))
            and note.get("disposition") in VALID_DISPOSITIONS
            and (disposition is None or note.get("disposition") == disposition)
            for note in notes
        ):
            wanted = f" with disposition {disposition!r}" if disposition else " with a valid disposition"
            errors.append(f"missing out_of_mandate note naming {term!r}{wanted}")
    return errors


def recheck_errors(case: dict[str, Any], report: dict[str, Any], prior: dict[str, Any] | None, contract_hash: str) -> list[str]:
    """`prior` is the prior report as supplied (with its injected verified state);
    `contract_hash` is the blob id of the contract file the invocation passes."""
    expected = case["expected"]
    recheck = report.get("recheck")
    if prior is None:
        return ["recheck must be null without a prior report"] if recheck is not None else []
    if ineligible := recheck_eligibility_errors(prior, contract_hash):
        if recheck is not None:
            return [f"recheck must be null: the prior report is not re-check eligible ({'; '.join(ineligible)})"]
        return []
    if not isinstance(recheck, dict):
        return ["recheck must be an object in a re-check run"]
    errors: list[str] = []
    listed: dict[str, dict[str, Any]] = {}
    for entry in recheck.get("prior_findings") or []:
        listed[str(entry.get("id"))] = entry
    for finding_id in sorted(open_prior_finding_ids(prior)):
        entry = listed.get(finding_id)
        if entry is None:
            errors.append(f"recheck.prior_findings is missing open prior finding {finding_id}")
            continue
        if entry.get("resolution") not in VALID_RESOLUTIONS:
            errors.append(f"recheck.prior_findings[{finding_id}]: resolution must be resolved or unresolved")
        if not non_empty(entry.get("evidence")):
            errors.append(f"recheck.prior_findings[{finding_id}]: evidence must be non-empty")
    unresolved = {finding_id for finding_id, entry in listed.items() if entry.get("resolution") == "unresolved"}
    expected_unresolved = set(expected.get("recheck_unresolved", []))
    if unresolved != expected_unresolved:
        errors.append(f"recheck unresolved: expected {sorted(expected_unresolved)}, got {sorted(unresolved)}")
    if "recheck_roles" in expected:
        roles = set(recheck.get("roles") or [])
        required_roles = set(expected["recheck_roles"])
        tolerated = required_roles | set(expected.get("recheck_optional_roles", []))
        if not required_roles <= roles <= tolerated:
            extra = sorted(tolerated - required_roles)
            errors.append(
                f"recheck.roles: expected exactly {sorted(required_roles)}"
                + (f" (optionally plus {extra})" if extra else "")
                + f", got {sorted(roles)}"
            )
    if "another_round_required" in expected and recheck.get("another_round_required") is not expected[
        "another_round_required"
    ]:
        errors.append(
            f"recheck.another_round_required: expected {expected['another_round_required']}, "
            f"got {recheck.get('another_round_required')!r}"
        )
    return errors


def safe_relative(path: str) -> bool:
    candidate = Path(path)
    return bool(path) and not candidate.is_absolute() and ".." not in candidate.parts


def blob_ids(repo: Path, paths: list[str] | set[str], *, commit: str | None = None) -> dict[str, str | None]:
    """Blob ids of `paths`, read-only: the working-tree content (`git hash-object`
    without `-w`) or, with `commit`, the committed content (`git rev-parse
    <commit>:<path>`). A path that does not exist there maps to `None`."""
    result: dict[str, str | None] = {}
    for path in sorted(paths):
        if commit is not None:
            found = run(["git", "rev-parse", "--verify", "-q", f"{commit}:{path}"], repo, check=False)
            result[path] = found.stdout.strip() if found.returncode == 0 else None
        elif (repo / path).is_file():
            result[path] = run(["git", "hash-object", "--", path], repo).stdout.strip()
        else:
            result[path] = None
    return result


def verified_state_mismatches(
    files: dict[str, Any], repo: Path, *, commit: str | None = None
) -> list[str]:
    """Compare recorded blob ids with the working tree, or with `commit` (the
    post-commit match)."""
    errors = [f"verified_state.files: invalid path {path!r}" for path in files if not safe_relative(path)]
    valid = [path for path in files if safe_relative(path)]
    where = commit or "the working tree"
    for path, actual in blob_ids(repo, valid, commit=commit).items():
        if files[path] != actual:
            errors.append(f"verified_state.files[{path}]: recorded {files[path]!r}, {where} has {actual!r}")
    return errors


def baseline_commit(repo: Path) -> str:
    """The harness baseline: the root commit materialize created (`main` may be
    deleted in origin cases, so never resolve it through a branch name)."""
    roots = run(["git", "rev-list", "--max-parents=0", "HEAD"], repo).stdout.split()
    if len(roots) != 1:
        raise EvaluationError(f"expected one baseline root commit, found {len(roots)}")
    return roots[0]


def target_paths(case: dict[str, Any], repo: Path) -> set[str]:
    """Every path the case's target covers: porcelain status (untracked files
    included), changes since the baseline commit, and the artifact path."""
    paths: set[str] = set()
    entries = run(["git", "status", "--porcelain", "-z", "--untracked-files=all"], repo).stdout.split("\0")
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if not entry:
            continue
        if entry[0] in "RC":
            index += 1  # skip the rename/copy source path
        paths.add(entry[3:])
    changed = run(["git", "diff", "--name-only", "-z", baseline_commit(repo)], repo).stdout.split("\0")
    paths.update(path for path in changed if path)
    target = case.get("target")
    if isinstance(target, dict) and target.get("kind") == "artifact":
        paths.add(target["path"])
    return {path for path in paths if "__pycache__" not in Path(path).parts}


# Target kinds whose content is not the checked-out working tree: only these may
# record `verified_state: null` (with a Scope saying it was not recorded). No
# current case materializes one; manifests accept only artifact targets.
NULL_STATE_TARGET_KINDS = {"commit", "range", "pull-request"}


def target_kind(case: dict[str, Any]) -> str:
    target = case.get("target")
    if isinstance(target, dict) and target.get("kind"):
        return str(target["kind"])
    return "branch" if case.get("branch_commits") else "working-tree"


EVIDENCE_PATH_RE = re.compile(r"^\s*([\w./-]+\.\w+)(?=$|[:\s,])")


def open_finding_files_by_id(case_dir: Path, case: dict[str, Any], repo: Path) -> dict[str, set[str]]:
    """For each open prior finding listed in the prior report's `findings`, the
    files named by the leading `path[:line]` of its evidence, kept when the path
    exists in the working tree or the verified state."""
    prior = case.get("prior_report") or {}
    open_ids = open_prior_finding_ids(prior)
    known = set(snapshot_files(case_dir, case["previous"])) if case.get("previous") else set()
    result: dict[str, set[str]] = {}
    for finding in prior.get("findings", []):
        finding_id = str(finding.get("id"))
        if finding_id not in open_ids:
            continue
        paths = result.setdefault(finding_id, set())
        for item in finding.get("evidence", []) if isinstance(finding.get("evidence"), list) else []:
            match = EVIDENCE_PATH_RE.match(str(item))
            if match and safe_relative(match.group(1)) and (
                match.group(1) in known or (repo / match.group(1)).is_file()
            ):
                paths.add(match.group(1))
    return result


def open_finding_files(case_dir: Path, case: dict[str, Any], repo: Path) -> set[str]:
    """Files of every open prior finding (see `open_finding_files_by_id`)."""
    return set().union(*open_finding_files_by_id(case_dir, case, repo).values())


def verified_state_errors(
    case_dir: Path, case: dict[str, Any], report: dict[str, Any], repo: Path, *, recheck: bool | None = None
) -> list[str]:
    """`recheck` says whether the run is a re-check; by default, whether the case
    supplies a prior report."""
    if recheck is None:
        recheck = case.get("prior_report") is not None
    state = report.get("verified_state")
    if state is None:
        kind = target_kind(case)
        if kind not in NULL_STATE_TARGET_KINDS:
            return [f"verified_state is null, but a {kind} target must record {{head, files}}"]
        if "not recorded" in normalized_text(report.get("scope", "")):
            return []
        return ["verified_state is null but scope does not state that the verified state was not recorded"]
    if not (isinstance(state, dict) and isinstance(state.get("files"), dict)):
        return ["verified_state must be {head, files} or null"]
    files = state["files"]
    errors = verified_state_mismatches(files, repo)
    head = run(["git", "rev-parse", "--verify", "-q", "HEAD"], repo, check=False).stdout.strip() or None
    if state.get("head") != head:
        errors.append(f"verified_state.head: recorded {state.get('head')!r}, HEAD is {head!r}")
    required = target_paths(case, repo)
    if recheck:
        # Re-check: prior verified paths, the delta (within `required` already),
        # and the files of open prior findings.
        required.update(snapshot_files(case_dir, case["previous"]))
        required.update(open_finding_files(case_dir, case, repo))
    missing = sorted(required - set(files))
    if missing:
        errors.append(f"verified_state.files is missing target path(s): {missing}")
    return errors


def score_report(case_id: str, report_path: Path, repo: Path) -> None:
    case_dir, case = load_case(case_id)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    expected = case["expected"]
    errors: list[str] = []

    if not repo.is_dir():
        raise EvaluationError(f"repo directory does not exist: {repo}")
    # Contract immutability: the run must not edit or replace the contract file.
    task_file = repo / TASK_FILE
    if not task_file.is_file() or task_file.read_text(encoding="utf-8") != task_text(case):
        raise EvaluationError(
            f"{case_id}: {TASK_FILE} differs from the case task; the contract was edited during the run"
        )
    # Recompute the expected digest from the case's own base+candidate snapshots
    # rather than trusting anything stored inside `repo` (a verifier with write
    # access could edit or delete an in-repo digest file to hide a mutation).
    expected_digest = reference_tree_digest(case_id)
    current_digest = tree_digest(repo)
    if current_digest != expected_digest:
        raise EvaluationError(
            f"{case_id}: repo source changed since materialization "
            f"(expected {expected_digest}, now {current_digest}); verification cannot be trusted"
        )
    if state_errors := repository_state_errors(case_id, case, repo):
        raise EvaluationError("\n".join(state_errors) + "\nverification cannot be trusted")
    if report.get("source_unchanged") is not True:
        errors.append("source_unchanged must be true")

    if report.get("case_id") != case_id:
        errors.append(f"case_id must be {case_id!r}")
    if report.get("verdict") != expected["verdict"]:
        errors.append(f"verdict: expected {expected['verdict']!r}, got {report.get('verdict')!r}")
    errors += report_consistency_errors(report)
    effective_mode = expected.get("effective_mode", case["mode"])
    if "effective_mode" in expected and report.get("effective_mode") != effective_mode:
        errors.append(f"effective_mode: expected {effective_mode!r}, got {report.get('effective_mode')!r}")
    reviewers = report.get("selected_reviewers", [])
    required_reviewers = expected.get("required_reviewers", [])
    missing_reviewers = sorted(set(required_reviewers) - set(reviewers))
    if missing_reviewers:
        errors.append(f"missing reviewers: {missing_reviewers}")
    if exact := expected.get("exact_reviewers"):
        if set(reviewers) != set(exact):
            errors.append(f"reviewers: expected exactly {sorted(exact)}, got {sorted(reviewers)}")
    if len(reviewers) > expected.get("max_reviewers", MODE_MAX[effective_mode]):
        errors.append(f"selected {len(reviewers)} reviewers; panel bound exceeded")
    forbidden = sorted(set(expected.get("forbidden_reviewers", [])) & set(reviewers))
    if forbidden:
        errors.append(f"forbidden reviewers selected: {forbidden}")

    findings = report.get("findings", [])
    for expected_finding in expected.get("findings", []):
        if not any(finding_matches(actual, expected_finding, report.get("criteria")) for actual in findings):
            errors.append(f"missing semantic finding: {expected_finding.get('name', expected_finding)}")

    gap_kinds = {gap.get("kind") for gap in report.get("evidence_gaps", [])}
    for kind in expected.get("evidence_gap_kinds", []):
        if kind not in gap_kinds:
            errors.append(f"missing evidence gap kind: {kind}")

    expected_criteria = expected.get("criteria")
    if expected_criteria:
        actual_criteria = {
            entry.get("id"): entry.get("result") for entry in report.get("criteria", [])
        }
        for criterion_id, expected_result in expected_criteria.items():
            actual_result = actual_criteria.get(criterion_id)
            if actual_result != expected_result:
                errors.append(
                    f"criteria[{criterion_id}]: expected {expected_result!r}, got {actual_result!r}"
                )

    checks = report.get("checks_executed", [])
    for expected_check in expected.get("checks", []):
        if not any(check_matches(actual, expected_check) for actual in checks):
            errors.append(f"missing executed check: {expected_check}")

    errors += out_of_mandate_errors(report, expected.get("out_of_mandate_terms", []))

    scope = report.get("scope")
    not_covered = normalized_text(scope.get("not_covered", []) if isinstance(scope, dict) else "")
    for term in expected.get("scope_not_covered_terms", []):
        if term.lower() not in not_covered:
            errors.append(f"scope.not_covered does not name {term!r}")

    next_action_or_gaps = normalized_text(
        [report.get("minimum_next_action", ""), [gap.get("evidence", "") for gap in report.get("evidence_gaps", [])]]
    )
    for term in expected.get("next_action_or_gap_terms", []):
        if term.lower() not in next_action_or_gaps:
            errors.append(f"neither minimum_next_action nor an evidence gap names {term!r}")

    contract_hash = contract_blob_id(repo)
    summary = report.get("contract_summary")
    if contract_file_source(summary) and summary.get("source_hash") != contract_hash:
        errors.append(
            f"contract_summary.source_hash: recorded {summary.get('source_hash')!r}, "
            f"the --contract file's blob id is {contract_hash!r}"
        )
    # The guard above proved the supplied prior report equals the injected artifact.
    prior = (
        json.loads((repo / PRIOR_REPORT_FILE).read_text(encoding="utf-8"))
        if case.get("prior_report") is not None
        else None
    )
    errors += recheck_errors(case, report, prior, contract_hash)
    is_recheck = prior is not None and not recheck_eligibility_errors(prior, contract_hash)
    errors += verified_state_errors(case_dir, case, report, repo, recheck=is_recheck)

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
    check_parser.add_argument("repo", type=Path)

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
            score_report(args.case_id, args.report, args.repo.resolve())
    except (EvaluationError, json.JSONDecodeError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
