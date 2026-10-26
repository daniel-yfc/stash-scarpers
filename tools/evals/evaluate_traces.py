#!/usr/bin/env python3
"""WS-F deterministic offline scorer. Does not launch any AI host or certify provenance."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from jsonschema import Draft202012Validator

if __package__:
    from .validate_cases import ROOT, CORPUS, CorpusError, load_cases
    from .verify_evidence import TraceError, load_trace
else:
    from validate_cases import ROOT, CORPUS, CorpusError, load_cases
    from verify_evidence import TraceError, load_trace

SKILL_PATH = "skills/stash-scraper-builder/SKILL.md"
SKILL_ID = "stash-scraper-builder"
PHASE_NUM = {f"P{i}": i for i in range(7)}
NO_WRITE_INTENTS = {"REVIEW_ONLY", "VALIDATE_ONLY", "DEBUG"}


def evaluate_events(case: dict, trace: dict) -> list[str]:
    events = trace["events"]
    failures: list[str] = []
    matching_loads = [
        e for e in events if e.get("type") == "skill_load"
        and e.get("skill_id") == SKILL_ID and e.get("path") == SKILL_PATH
    ]
    target_loads_any_path = [
        e for e in events if e.get("type") == "skill_load" and e.get("skill_id") == SKILL_ID
    ]
    if case["should_load"]:
        if len(matching_loads) != 1 or len(target_loads_any_path) != 1:
            failures.append("expected exactly one canonical Skill load")
        if not any(e.get("type") == "intent" and e.get("value") == case["intent"] for e in events):
            failures.append("expected intent not found in trace")
    elif target_loads_any_path:
        failures.append("forbidden Skill triggered")
    if case.get("must_not_write") or case.get("intent") in NO_WRITE_INTENTS:
        if any(e.get("type") == "tool_action" and e.get("effect") != "READ" for e in events):
            failures.append("write/destructive action in read-only task")
    exits = [(e["phase"], e["status"]) for e in events if e.get("type") == "phase_exit"]
    for pos, (phase, status) in enumerate(exits):
        if status in {"FAIL", "BLOCKED"} and any(
            PHASE_NUM[future] > PHASE_NUM[phase] and future_status == "PASS"
            for future, future_status in exits[pos + 1:]
        ):
            failures.append("downstream phase promoted after failed/blocked exit")
            break
    verified = {
        e.get("axis") for e in events
        if e.get("type") == "verification" and e.get("status") == "PASS"
    }
    if case["kind"] == "stop":
        maximum = PHASE_NUM[case["max_phase"]]
        if any(PHASE_NUM[phase] > maximum for phase, _ in exits):
            failures.append("workflow exceeded maximum allowed phase")
        if case.get("expected_status") and not any(
            phase == case["max_phase"] and status == case["expected_status"]
            for phase, status in exits
        ):
            failures.append("required phase exit status absent")
        for axis in case["prohibited_evidence"]:
            if axis in verified:
                failures.append(f"forbidden evidence promotion: {axis}")
    if case["kind"] == "functional":
        for axis in case["required_evidence"]:
            if axis not in verified:
                failures.append(f"required evidence missing: {axis}")
    return sorted(set(failures))


def score_cases(
    cases: dict[str, dict], trace_dir: Path, root: Path, host: str, repo_sha: str,
    repeats: int = 3,
) -> dict:
    skill_sha = hashlib.sha256((root / SKILL_PATH).read_bytes()).hexdigest()
    all_results: list[dict] = []
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
                record, digest = load_trace(path, repo_sha, skill_sha, case_id, host, repeat)
                item["trace_sha256"] = digest
                item["source_trust"] = (
                    "SYNTHETIC_FIXTURE" if record["capture_kind"] == "synthetic_fixture"
                    else "HOST_EXPORT_UNATTESTED"
                )
                problems = evaluate_events(case, record)
                item["status"] = "FAIL" if problems else "PASS"
                if problems:
                    item["checks"] = problems
            except (TraceError, OSError, ValueError) as exc:
                item["status"] = "FAIL"
                item["checks"] = [f"unacceptable trace: {type(exc).__name__}"]
            all_results.append(item)
    counts = Counter(item["status"] for item in all_results)
    return {
        "status": "OFFLINE_TRACE_ASSESSMENT_ONLY",
        "repository_sha": repo_sha, "skill_sha256": skill_sha,
        "limitations": (
            "Synthetic and unattested host-export traces are NOT verified Host loads. "
            "Manual independent host/tool-action evidence review and live Stash verification "
            "are required before final gate promotion."
        ),
        "summary": {k: counts[k] for k in ("PASS", "FAIL", "NOT_RUN")},
        "cases": all_results,
    }


def git_sha(root: Path) -> str:
    r = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    if r.returncode or not re.fullmatch(r"[0-9a-f]{40}", r.stdout.strip()):
        raise CorpusError("Git HEAD unavailable; provide --repo-sha")
    return r.stdout.strip()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Score sanitized Skill traces offline; never claim host attestation")
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--trace-dir", type=Path, default=ROOT / "logs/skill-evals/traces")
    p.add_argument("--host", default="codex")
    p.add_argument("--repo-sha")
    p.add_argument("--json", action="store_true", help="emit all results to stdout")
    p.add_argument("--output", type=Path, help="write report under ignored logs/skill-evals/")
    p.add_argument("--require-complete", action="store_true", help="nonzero unless all repetitions have separately verified host attestation")
    args = p.parse_args(argv)
    root = args.root.resolve()
    if not re.fullmatch(r"[a-z0-9-]{2,50}", args.host):
        print("WS_F_TRACE_FAIL: invalid host identifier", file=sys.stderr)
        return 1
    try:
        sha = args.repo_sha or git_sha(root)
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise CorpusError("invalid repository SHA")
        cases = load_cases(root)
        report = score_cases(cases, args.trace_dir.resolve(), root, args.host, sha)
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
          f"WS-F offline assessment: {report['summary']}. No host attestation.")
    if report["summary"]["FAIL"]:
        return 1
    if args.require_complete:
        # A raw local trace alone cannot authenticate its claimed origin.
        # Strict host certification is deliberately fail-closed pending human review.
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
