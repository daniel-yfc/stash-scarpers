#!/usr/bin/env python3
"""Auto-fix issues found by scripts/check-standalone.py.

Run from the standalone-skill branch root:
    python scripts/fix-standalone.py [--apply]

Without --apply: dry run, lists what would change.
With --apply: performs the safe fixes.

Safe auto-fixes (mechanical, no judgment needed):
  - Delete excluded files (METHODOLOGY.md §3).

NOT auto-fixed (require semantic reframe per METHODOLOGY.md §5):
  - **repo-only** markers: the standalone equivalent is usually a
    rewrite, not a deletion (e.g. repo test command -> scripts/
    equivalent). Reported with file:line for manual handling.
  - Repo path references: same reason — reported, not rewritten.

After fixing, re-run scripts/check-standalone.py to verify.
"""

import argparse
import sys
from pathlib import Path

# Import shared constants from the check script (hyphenated filename
# needs importlib).
import importlib.util

_check_spec = importlib.util.spec_from_file_location(
    "check_standalone", Path(__file__).resolve().parent / "check-standalone.py"
)
check = importlib.util.module_from_spec(_check_spec)
_check_spec.loader.exec_module(check)

ROOT = Path(__file__).resolve().parent.parent


def fix_excluded_files(apply: bool):
    fixed = []
    for rel in check.EXCLUDED_FILES:
        p = ROOT / rel
        if p.exists():
            fixed.append(rel)
            if apply:
                p.unlink()
    return fixed


def report_manual_items():
    """List markers and path issues that need human judgment."""
    import re

    items = []
    marker_pat = re.compile(r"\*\*repo-only\*\*", re.IGNORECASE)
    leak_pats = [re.compile(p) for p in check.LEAK_PATTERNS]
    for f in sorted(ROOT.rglob("*.md")):
        if f.name == "METHODOLOGY.md":
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            rel = f.relative_to(ROOT)
            if marker_pat.search(line):
                items.append(f"{rel}:{i}: repo-only marker needs reframe (§5)")
            elif any(p.search(line) for p in leak_pats):
                items.append(f"{rel}:{i}: possible repo path needs reframe (§5)")
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="perform fixes (default: dry run)")
    args = ap.parse_args()

    mode = "APPLYING" if args.apply else "DRY RUN"
    print(f"--- {mode} ---\n")

    fixed = fix_excluded_files(args.apply)
    if fixed:
        for rel in fixed:
            print(f"{'deleted' if args.apply else 'would delete'}: {rel}")
    else:
        print("No excluded files present. Nothing to auto-fix.")

    manual = report_manual_items()
    if manual:
        print(f"\n{len(manual)} item(s) need manual reframe (METHODOLOGY.md §5):")
        for item in manual:
            print(f"  - {item}")
    else:
        print("\nNo manual items. Tree is clean.")

    if not args.apply and (fixed or manual):
        print("\nRe-run with --apply to perform the safe fixes.")


if __name__ == "__main__":
    main()
