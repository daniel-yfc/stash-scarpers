#!/usr/bin/env python3
"""Validate WS-F case corpus. No host invocation, network, or writes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CORPUS = "tests/skill-evals"
SUITES = {
    "stash-scraper-builder-trigger-cases.json": ("stash-scraper-builder", 20),
    "near-miss-cases.json": ("near-miss", 10),
    "workflow-stop-cases.json": ("workflow-stop", 10),
    "functional-cases.json": ("functional-e2e", 5),
}

class CorpusError(ValueError):
    pass


def load_cases(root: Path = ROOT) -> dict[str, dict]:
    schema_path = root / CORPUS / "schemas/case.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
    except (OSError, ValueError) as exc:
        raise CorpusError("case schema unavailable or invalid") from exc
    cases: dict[str, dict] = {}
    for filename, (expected_suite, expected_count) in SUITES.items():
        path = root / CORPUS / filename
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise CorpusError(f"manifest unreadable: {filename}") from exc
        if not isinstance(manifest, dict) or manifest.get("suite") != expected_suite:
            raise CorpusError(f"wrong suite name: {filename}")
        if (manifest.get("skill_id") != "stash-scraper-builder"
                or manifest.get("expected_skill_path") != "skills/stash-scraper-builder/SKILL.md"
                or manifest.get("repeat_per_host") != 3):
            raise CorpusError(f"unapproved skill/repeat contract: {filename}")
        records = manifest.get("cases")
        if not isinstance(records, list) or len(records) != expected_count:
            raise CorpusError(f"unexpected case count: {filename}")
        for position, record in enumerate(records):
            errors = list(validator.iter_errors(record))
            if errors:
                raise CorpusError(f"case schema invalid: {filename}, row {position + 1}, {errors[0].validator}")
            name = record["id"]
            if name in cases:
                raise CorpusError(f"duplicate case id: {name}")
            if (filename == "functional-cases.json") != (record["kind"] == "functional"):
                raise CorpusError(f"wrong case kind: {name}")
            if (filename == "workflow-stop-cases.json") != (record["kind"] == "stop"):
                raise CorpusError(f"wrong case kind: {name}")
            if filename in ("stash-scraper-builder-trigger-cases.json", "near-miss-cases.json") and record["kind"] != "trigger":
                raise CorpusError(f"wrong trigger case kind: {name}")
            if record["kind"] == "functional" and not (root / record["source_path"]).is_file():
                raise CorpusError(f"missing legacy functional task source: {name}")
            cases[name] = record
    baseline = [r for r in cases.values() if r["id"].startswith(("POS-", "NEG-"))]
    if sum(bool(r["should_load"]) for r in baseline) != 10:
        raise CorpusError("baseline trigger expected exactly ten positive/ten negative cases")
    return cases


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Validate WS-F versioned Skill evaluation cases (read-only)")
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    try:
        cases = load_cases(args.root.resolve())
    except CorpusError as exc:
        print(f"WS_F_CORPUS_FAIL: {exc}", file=sys.stderr)
        return 1
    summary = {"status": "CORPUS_VALIDATED_ONLY", "cases": len(cases), "host_traces": "NOT_RUN"}
    print(json.dumps(summary, sort_keys=True) if args.json else f"WS-F corpus PASS: {len(cases)} cases. Host runs NOT_RUN.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
