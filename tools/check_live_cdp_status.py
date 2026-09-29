#!/usr/bin/env python3
"""Fail closed for live Stash/CDP claims.

This does not launch Stash or a browser. A verified claim requires an artifact
path recorded as `cdp_artifact: <existing-path>` in the evidence file. Absent
runtime evidence remains UNVERIFIED and does not count as a pass.
"""

from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    evidence = ROOT / "evidence"
    files = sorted(evidence.glob("*.md")) if evidence.exists() else []
    stash = shutil.which("stash")
    print(f"stash-runtime: {'present' if stash else 'absent'}")
    for path in files:
        text = path.read_text(encoding="utf-8")
        if re.search(r"Live Stash CDP:\s*(verified|pass|done)\b", text, re.I):
            match = re.search(r"cdp_artifact:\s*(\S+)", text)
            artifact = ROOT / match.group(1) if match else None
            if not artifact or not artifact.exists():
                print(f"- cdp-overclaim: {path.relative_to(ROOT)}")
                return 1
    print("Live Stash/CDP status: UNVERIFIED")
    print("No live CDP pass is asserted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
