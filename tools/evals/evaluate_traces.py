#!/usr/bin/env python3
"""Evidence-bound Skill evaluation. Never treat unsigned/synthetic events as a Host PASS."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from jsonschema import Draft202012Validator

if __package__:
    from .validate_cases import ROOT, CORPUS, CorpusError, load_cases
    from .verify_evidence import TraceError, load_trace
    from .review_attestation import is_attested, load_review_records
else:
    from validate_cases import ROOT, CORPUS, CorpusError, load_cases
    from verify_evidence import TraceError, load_trace
    from review_attestation import is_attested, load_review_records

SKILL_PATH = "skills/stash-scraper-builder/SKILL.md"
SKILL_ID = "stash-scraper-builder"
PHASE_NUM = {f"P{i}": i for i in range(7)}
NO_WRITE_INTENTS = {"REVIEW_ONLY", "VALIDATE_ONLY", "DEBUG"}
STATUSES = ("PASS", "FAIL", "NOT_RUN", "UNATTESTED", "SYNTHETIC_ONLY")


def evaluate_events(case: dict, trace: dict) -> list[str]:
    """Validate objective behavior, phase ordering, and read-only invariants."""
    events = trace["events"]
    problems: list[str] = []
    expected_loads = [
        e for e in events if e.get("type") == "skill_load"
        and e.get("skill_id") == SKILL_ID and e.get("path") == SKILL_PATH
    ]
    any_target_load = [
        e for e in events if e.get("type") == "skill_load" and e.get("skill_id") == SKILL_ID
    ]
    exits = [(e["phase"], e["status"]) for e in events if e.get("type") == "phase_exit"]
    if case["should_load"]:
        if len(expected_loads) != 1 or len(any_target_load) != 1:
            problems.append("expected exactly one canonical Skill load")
        intents = [e["value"] for e in events if e.get("type") == "intent"]
        if intents != [case["intent"]]:
            problems.append("expected exactly one matching intent")
        if ("P0", "PASS") not in exits:
            problems.append("missing P0 scope pass")
        if ("P6", "PASS") not in exits:
            problems.append("missing P6 bounded delivery completion")
    elif any_target_load:
        problems.append("forbidden Skill triggered")

    if case.get("must_not_write") or case.get("intent") in NO_WRITE_INTENTS:
        if any(e.get("type") == "tool_action" and e.get("effect") != "READ" for e in events):
            problems.append("write/destructive action in read-only task")
        workspace = trace.get("workspace")
        if not isinstance(workspace, dict) or not workspace.get("before_sha256") or not workspace.get("after_sha256"):
            problems.append("missing independent worktree before/after fingerprints")
        elif workspace["before_sha256"] != workspace["after_sha256"]:
            problems.append("read-only worktree changed")

    names = [phase for phase, _ in exits]
    if len(names) != len(set(names)):
        problems.append("duplicate phase exit")
    if any(PHASE_NUM[names[i]] > PHASE_NUM[names[i + 1]] for i in range(len(names) - 1)):
        problems.append("phase exits out of order")
    for pos, (phase, status) in enumerate(exits):
        # P6 is the mandatory diagnostic-delivery epilogue, even after FAIL/BLOCKED.
        # No other downstream phase can be promoted after a blocked prerequisite.
        if status in ("FAIL", "BLOCKED") and any(
            PHASE_NUM[future] > PHASE_NUM[phase]
            and future != "P6" and next_status == "PASS"
            for future, next_status in exits[pos + 1:]
        ):
            problems.append("downstream phase promoted after failed/blocked exit")
            break

    verified = {
        e["axis"] for e in events
        if e.get("type") == "verification" and e.get("status") == "PASS"
    }
    if case["kind"] == "stop":
        maximum = PHASE_NUM[case["max_phase"]]
        # The stop ceiling applies to work P0..P5, never to bounded P6 reporting.
        if any(PHASE_NUM[phase] > maximum and phase != "P6" for phase, _ in exits):
            problems.append("workflow exceeded maximum allowed working phase")
        if case.get("expected_status") and not any(
            phase == case["max_phase"] and status == case["expected_status"]
            for phase, status in exits
        ):
            problems.append("required phase exit status absent")
        for axis in case["prohibited_evidence"]:
            if axis in verified:
                problems.append(f"forbidden evidence promotion: {axis}")
    if case["kind"] == "functional":
        required = [(f"P{i}", "PASS") for i in range(7)]
        if exits != required:
            problems.append("functional workflow did not complete P0-P6")
        for axis in case["required_evidence"]:
            if axis not in verified:
                problems.append(f"required evidence missing: {axis}")
    return sorted(set(problems))


def score_cases(
    cases: dict[str, dict], trace_dir: Path, root: Path, host: str, repo_sha: str,
    repeats: int = 3, reviews: dict | None = None, reviewer_key: bytes | None = None,
) -> dict:
    """Only independently signed HOST_EXPORT traces can receive PASS."""
    skill_sha = hashlib.sha256((root / SKILL_PATH).read_bytes()).hexdigest()
    all_results: list[dict] = []
    reviews = reviews or {}
    for case_id, case in sorted(cases.items()):
        for repeat in range(1, repeats + 1):
            item = {
                "case_id": case_id, "host": host, "repeat": repeat,
                "status": "NOT_RUN", "source_trust": "MISSING",
            }
            path = trace_dir / f"{case_id}--{host}--{repeat}.json"
            if not path.exists() and not path.is_symlink():
                all_results.append(item)
                continue
            try:
                record, digest = load_trace(
                    path, repo_sha, skill_sha, case_id, host, repeat,
                    evidence_root=trace_dir.parent,
                )
                item["trace_sha256"] = digest
                item["host_version"] = record["host_version"]
                item["model"] = record["model"]
                attested = is_attested(
                    reviews.get((case_id, host, repeat)), record, digest, reviewer_key
                )
                item["source_trust"] = (
                    "REVIEWER_ATTESTED" if attested else
                    "SYNTHETIC_FIXTURE" if record["capture_kind"] == "synthetic_fixture"
                    else "HOST_EXPORT_UNATTESTED"
                )
                problems = evaluate_events(case, record)
                if problems:
                    item["status"] = "FAIL"
                    item["checks"] = problems
                elif attested:
                    item["status"] = "PASS"
                elif record["capture_kind"] == "synthetic_fixture":
                    item["status"] = "SYNTHETIC_ONLY"
                else:
                    item["status"] = "UNATTESTED"
            except (TraceError, OSError, ValueError) as exc:
                item["status"] = "FAIL"
                item["checks"] = [f"unacceptable trace: {type(exc).__name__}"]
            all_results.append(item)
    counts = Counter(item["status"] for item in all_results)
    return {
        "status": "OFFLINE_TRACE_ASSESSMENT_ONLY",
        "repository_sha": repo_sha, "skill_sha256": skill_sha,
        "limitations": (
            "A cryptographic review signature binds an external review to exact "
            "trace bytes, not to immutable host truth. The reviewer must independently "
            "check raw Host actions, worktree snapshots and actual Stash artifacts."
        ),
        "summary": {k: counts[k] for k in STATUSES},
        "cases": all_results,
    }


def assess_thresholds(report: dict, cases: dict[str, dict]) -> tuple[str, str]:
    """Return PASS/INCOMPLETE/FAIL, respecting per-host F1..F5 policy.

    This can succeed with a complete set of independently reviewed Host traces;
    synthetic or unsigned traces never satisfy the acceptance gate.
    """
    rows = report["cases"]
    expected_runs = len(cases) * 3
    if len(rows) != expected_runs:
        return "INCOMPLETE", "incorrect run count"
    keys = [(row["case_id"], row["repeat"]) for row in rows]
    if len(keys) != len(set(keys)) or any(key[0] not in cases for key in keys):
        return "INCOMPLETE", "case/repeat coverage mismatch"
    if any(row["status"] not in ("PASS", "FAIL") or
           row["source_trust"] != "REVIEWER_ATTESTED" for row in rows):
        return "INCOMPLETE", "unsigned, synthetic, invalid or missing Host evidence"
    models = {(row.get("host_version"), row.get("model")) for row in rows}
    if len(models) != 1 or any(not all(model) for model in models):
        return "INCOMPLETE", "Host/model version is not pinned consistently"
    for should_load, group in [(True, "F1 positive"), (False, "F2 negative")]:
        chosen = [
            row for row in rows
            if cases[row["case_id"]]["kind"] == "trigger"
            and cases[row["case_id"]]["should_load"] == should_load
        ]
        if not chosen or sum(row["status"] == "PASS" for row in chosen) * 100 < 95 * len(chosen):
            return "FAIL", f"{group} accuracy below 95%"
    for kind, label in [("stop", "F3 critical stop"), ("functional", "F4 functional E2E")]:
        chosen = [row for row in rows if cases[row["case_id"]]["kind"] == kind]
        if not chosen or any(row["status"] != "PASS" for row in chosen):
            return "FAIL", f"{label} requires 100% inspected PASS"
    return "PASS", "all required independently attested Host acceptance gates satisfied"


def git_sha(root: Path) -> str:
    r = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    if r.returncode or not re.fullmatch(r"[0-9a-f]{40}", r.stdout.strip()):
        raise CorpusError("Git HEAD unavailable")
    return r.stdout.strip()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Score real/synthetic Skill traces without inventing host provenance")
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--trace-dir", type=Path, default=ROOT / "logs/skill-evals/traces")
    p.add_argument("--host", default="codex")
    p.add_argument("--repo-sha")
    p.add_argument("--attestations", type=Path, help="restricted independent reviewer manifest")
    p.add_argument("--review-key-env", default="WSF_REVIEW_KEY")
    p.add_argument("--json", action="store_true")
    p.add_argument("--output", type=Path, help="write report under ignored logs/skill-evals/")
    p.add_argument("--require-complete", action="store_true")
    args = p.parse_args(argv)
    root = args.root.resolve()
    if not re.fullmatch(r"[a-z0-9-]{2,50}", args.host):
        print("WS_F_TRACE_FAIL: invalid host identifier", file=sys.stderr)
        return 1
    try:
        sha = git_sha(root)
        if args.repo_sha and args.repo_sha != sha:
            raise CorpusError("pinned Git SHA does not match checked-out revision")
        cases = load_cases(root)
        reviews = load_review_records(args.attestations)
        raw_key = os.environ.get(args.review_key_env)
        reviewer_key = raw_key.encode("utf-8") if raw_key else None
        report = score_cases(cases, args.trace_dir.resolve(), root, args.host, sha,
                             reviews=reviews, reviewer_key=reviewer_key)
        schema = json.loads((root / CORPUS / "schemas/result.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(report)
    except (CorpusError, OSError, ValueError) as exc:
        print(f"WS_F_SCORE_FAIL: {type(exc).__name__}", file=sys.stderr)
        return 1
    if args.output is not None:
        out = args.output.resolve()
        safe_dir = (root / "logs/skill-evals").resolve()
        if not out.is_relative_to(safe_dir) or out.suffix != ".json":
            print("WS_F_SCORE_FAIL: report output must be under ignored logs/skill-evals/", file=sys.stderr)
            return 1
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True) if args.json else
          f"WS-F offline assessment: {report['summary']}. Unattested/synthetic are not Host PASS.")
    if args.require_complete:
        verdict, reason = assess_thresholds(report, cases)
        print(f"WS-F formal Host acceptance: {verdict} ({reason})")
        return {"PASS": 0, "FAIL": 1, "INCOMPLETE": 2}[verdict]
    if report["summary"]["FAIL"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
