#!/usr/bin/env python3
"""Reject evidence labels that claim verification without an artifact."""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
OVERCLAIMS = [
    re.compile(r"fixture verification.{0,80}\b(DONE|PASS|verified)\b", re.I | re.S),
    re.compile(r"Live Stash CDP:\s*(verified|pass|done)\b", re.I),
    re.compile(r"Production readiness:\s*(verified|pass|done|ready)\b", re.I),
]


def main() -> int:
    errors = []
    evidence = ROOT / "evidence"
    files = sorted(evidence.glob("*.md")) if evidence.exists() else []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern in OVERCLAIMS:
            if pattern.search(text):
                errors.append(f"evidence-overclaim: {path.relative_to(ROOT)}")
                break
        if "tests/fixtures/" in text and "not established" not in text.lower():
            errors.append(f"evidence-fixture-reference: {path.relative_to(ROOT)}")
    print(f"Checked {len(files)} evidence record(s)")
    if errors:
        for error in errors:
            print(f"- {error}")
        return 1
    print("Evidence-label check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
