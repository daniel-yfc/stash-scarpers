#!/usr/bin/env python3
"""Check documentation claims and embedded YAML against the vendored official schema.

Usage: python tools/check_scraper_docs.py
Requires: PyYAML and jsonschema (requirements.txt).
"""
from pathlib import Path
import re
import sys
import yaml
from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "validator" / "scraper.schema.json"
DOC_ROOT = ROOT / "skills" / "stash-scraper-builder"


def full_yaml_blocks(path):
    return re.findall(r"```yaml\r?\n(.*?)```", path.read_text(encoding="utf-8"), flags=re.S)


def has_mapping(doc):
    return isinstance(doc, dict) and any(k.endswith(("ByURL", "ByName", "ByFragment", "ByQueryFragment")) for k in doc)


def main():
    if not SCHEMA.exists():
        print(f"missing schema: {SCHEMA}", file=sys.stderr)
        return 2
    try:
        schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
        validator = Draft7Validator(schema)
    except (OSError, yaml.YAMLError, TypeError) as exc:
        print(f"unable to load schema: {exc}", file=sys.stderr)
        return 2

    failures = []
    checked = 0

    for path in sorted(DOC_ROOT.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        # debugging.md / incident-reviews.md record the stale claim as a
        # corrected incident ("incorrect causal claim"), not as guidance.
        if path.name not in ("debugging.md", "incident-reviews.md"):
            if "No root `name" in text or "禁止 root `name" in text:
                failures.append(f"{path}: documentation still forbids root name")
            if "sceneByFragment` prevents" in text:
                failures.append(f"{path}: stale nil-pointer prevention claim")
        for index, block in enumerate(full_yaml_blocks(path), 1):
            try:
                data = yaml.safe_load(block)
            except yaml.YAMLError as exc:
                failures.append(f"{path} YAML block {index}: parse error: {exc}")
                continue
            if not isinstance(data, dict) or "name" not in data or not has_mapping(data):
                continue
            checked += 1
            errors = sorted(validator.iter_errors(data), key=lambda error: list(error.path))
            for error in errors:
                failures.append(f"{path} YAML block {index} {list(error.path)}: {error.message}")

    print(f"Checked {checked} embedded full-document YAML blocks.")
    if failures:
        print("Documentation contradiction/schema failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Documentation contradiction check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
