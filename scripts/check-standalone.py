#!/usr/bin/env python3
"""Phase 4 validation for the standalone skill (METHODOLOGY.md).

Run from the standalone-skill branch root:
    python scripts/check-standalone.py

Checks:
  1. No **repo-only** markers remain.
  2. No excluded files are present.
  3. No repo path leakage (per METHODOLOGY.md Phase 4).
  4. SKILL.md frontmatter is valid (name, description, metadata).
  5. Schema references point to the official CommunityScrapers URL,
     not local repo paths.

Exit 0 if clean, 1 if issues found. Suitable for CI.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Files deliberately removed in standalone (see METHODOLOGY.md §3).
EXCLUDED_FILES = [
    "references/json-examples.md",
    "references/phase0-secrets-policy.md",
    "references/skill-read-order.md",
]

# Repo-specific path patterns that must not leak into standalone.
# (METHODOLOGY.md Phase 4 + sync-from-main.sh leakage check.)
LEAK_PATTERNS = [
    r"skills/stash-scraper-builder",
    r"docs/0[1-7]_",
    r"validator/index",
    r"\.github/",
    r"(?<![\w/.-])tools/",
    r"(?<![\w/.-])docs/",
]

OFFICIAL_SCHEMA_URL = "github.com/stashapp/CommunityScrapers"

_errors = []
_warnings = []


def _md_files():
    return sorted((ROOT).rglob("*.md"))


def check_markers():
    """No **repo-only** markers may remain."""
    pat = re.compile(r"\*\*repo-only\*\*", re.IGNORECASE)
    for f in _md_files():
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if pat.search(line):
                _errors.append(f"{f.relative_to(ROOT)}:{i}: repo-only marker remains")


def check_excluded_files():
    """Excluded files must not exist."""
    for rel in EXCLUDED_FILES:
        if (ROOT / rel).exists():
            _errors.append(f"{rel}: excluded file present in standalone")


def check_path_leakage():
    """No repo-specific path references."""
    pats = [re.compile(p) for p in LEAK_PATTERNS]
    for f in _md_files():
        # METHODOLOGY.md documents the mapping, so its references are intentional.
        if f.name == "METHODOLOGY.md":
            continue
        text = f.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            for p in pats:
                if p.search(line):
                    _warnings.append(
                        f"{f.relative_to(ROOT)}:{i}: possible repo path leakage: {line.strip()[:80]}"
                    )
                    break


def check_frontmatter():
    """SKILL.md frontmatter must have name, description, metadata."""
    import re as _re

    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    if not text.startswith("---"):
        _errors.append("SKILL.md: missing frontmatter")
        return
    fm = text.split("---", 2)[1]
    for key in ("name:", "description:", "metadata:"):
        if key not in fm:
            _errors.append(f"SKILL.md: frontmatter missing {key.rstrip(':')}")
    # metadata.version should look like a date
    m = _re.search(r"version:\s*['\"]?(\d{4}-\d{2}-\d{2})", fm)
    if not m:
        _warnings.append("SKILL.md: metadata.version is not a date")


def check_schema_url():
    """Schema references must use the official URL, not local paths."""
    for f in _md_files():
        if f.name == "METHODOLOGY.md":
            continue
        text = f.read_text(encoding="utf-8")
        if "scraper.schema.json" in text and OFFICIAL_SCHEMA_URL not in text:
            # Local relative reference like ../validator/scraper.schema.json
            if re.search(r"[`'\"]\.{0,2}/[^`'\"]*scraper\.schema\.json", text):
                _errors.append(
                    f"{f.relative_to(ROOT)}: local schema path reference (use official URL)"
                )


def main():
    check_markers()
    check_excluded_files()
    check_path_leakage()
    check_frontmatter()
    check_schema_url()

    for w in _warnings:
        print(f"WARN: {w}")
    for e in _errors:
        print(f"ERROR: {e}")

    if _errors:
        print(f"\n{len(_errors)} error(s), {len(_warnings)} warning(s) — FAILED")
        return 1
    print(f"\nClean ({len(_warnings)} warning(s)) — PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
