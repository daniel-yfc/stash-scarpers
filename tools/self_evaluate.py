#!/usr/bin/env python3
"""Run safeguard controls and report what each result does not prove."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CHECKS = [
    [sys.executable, "tools/parse_committed_yaml.py"],
    ["node", "tools/verify-scraper-fixtures.mjs", "--self-test"],
    [sys.executable, "tools/scan_session_material.py"],
    [sys.executable, "tools/check_evidence_labels.py"],
    [sys.executable, "tools/check_live_cdp_status.py"],
]


def main() -> int:
    failed = False
    print("| Control | Result | Boundary |")
    print("|---|---|---|")
    boundaries = {
        "parse_committed_yaml.py": "Parses the checkout only; not a schema pass.",
        "verify-scraper-fixtures.mjs": "Self-test only unless a manifest path is supplied.",
        "scan_session_material.py": "Pattern locations only; values are not printed.",
        "check_evidence_labels.py": "Rejects overclaims; does not create evidence.",
        "check_live_cdp_status.py": "Fail-closed status; not a live Stash run.",
    }
    for command in CHECKS:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        name = Path(command[1]).name
        status = "PASS" if result.returncode == 0 else "FAIL"
        if result.returncode != 0:
            failed = True
        print(f"| {name} | {status} | {boundaries[name]} |")
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
    print("Self-evaluation complete. A PASS does not imply production readiness.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
