#!/usr/bin/env python3
"""Scan fixtures, evidence, and logs for session-material assignments.

Prints rule IDs and paths only. Never prints matched values.
"""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ROOTS = ["scrapers", "tests/fixtures", "evidence", "logs"]
RULES = {
    "cookie-assignment": re.compile(r"(?i)(?:set-cookie|cf_clearance|csrf(?:_token)?)\s*[:=]"),
    "credential-assignment": re.compile(r"(?i)(?:password|api[_-]?key|session[_-]?token)\s*[:=]\s*\S+"),
    "browser-profile-assignment": re.compile(r"(?i)(?:user-data-dir|browser[_-]?profile)\s*[:=]\s*\S+"),
}


def files():
    for relative in ROOTS:
        base = ROOT / relative
        if not base.exists():
            continue
        yield from (path for path in base.rglob("*") if path.is_file())


def main() -> int:
    findings = []
    scanned = 0
    for path in files():
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        for rule, pattern in RULES.items():
            if pattern.search(text):
                findings.append(f"{rule}: {path.relative_to(ROOT)}")
    print(f"Scanned {scanned} fixture, evidence, log, and scraper file(s)")
    if findings:
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("Session-material scan passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
