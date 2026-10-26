#!/usr/bin/env python3
"""Guard the WS-D runtime/resource boundary and moved-resource Markdown links."""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = "skills/stash-scraper-builder/"
FORMER = (
    "eval-pack.md", "incident-reviews.md", "upstream-sources.md",
)
MOVED = (
    "tests/skill-evals/legacy-functional-eval.md",
    "docs/archive/incident-reviews-2026-10.md",
    "docs/43-upstream-sources.md",
    "skills/stash-scraper-builder/references/schema-provenance.md",
)
ENTRY_DOCS = (
    "skills/stash-scraper-builder/SKILL.md",
    "skills/stash-scraper-builder/references/debugging.md",
    "skills/stash-scraper-builder/references/schema-checklist.md",
    "skills/stash-scraper-builder/references/authoring-checklist.md",
    "README.md", "readme-zh-tw.md", "CONTRIBUTING.md", "templates/README.md",
    "docs/00-documentation-architecture.md", "docs/40-ci-workflows.md",
    "docs/50-testing-guide.md", "docs/43-upstream-sources.md",
    "docs/README.md", "tests/skill-evals/legacy-functional-eval.md",
    "docs/archive/incident-reviews-2026-10.md",
)
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
OLD_LINK = re.compile(r"(?:skills/stash-scraper-builder/)?references/(?:"
                      + "|".join(re.escape(x) for x in FORMER) + r")")
# Any runtime-skill Markdown named as a routed evaluation/incident is prohibited.
FORBIDDEN_RUNTIME_PATHS = tuple(SKILL + "references/" + x for x in FORMER)


def tracked_markdown_paths(root: Path) -> tuple[str, ...]:
    """Inspect Git's actual tracked Markdown set, not a maintained path whitelist."""
    proc = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", "*.md"],
        capture_output=True, check=False,
    )
    if proc.returncode:
        raise RuntimeError("tracked Markdown inventory is unavailable")
    return tuple(sorted(p.decode("utf-8", errors="surrogateescape")
                        for p in proc.stdout.split(b"\x00") if p))


def inspect(root: Path, paths: tuple[str, ...] | None = None) -> list[str]:
    errors: list[str] = []
    if paths is None:
        try:
            paths = tracked_markdown_paths(root)
        except RuntimeError:
            return ["TRACKED_MARKDOWN_INVENTORY_FAILED"]
        if not paths:
            return ["TRACKED_MARKDOWN_INVENTORY_EMPTY"]
    for moved in MOVED:
        if not (root / moved).is_file():
            errors.append(f"MISSING_MOVED_RESOURCE: {moved}")
    for path in FORBIDDEN_RUNTIME_PATHS:
        if (root / path).exists():
            errors.append(f"NON_RUNTIME_FILE_IN_SKILL: {path}")
    for rel in paths:
        p = root / rel
        if not p.is_file():
            errors.append(f"MISSING_RELATED_DOC: {rel}")
            continue
        content = p.read_text(encoding="utf-8")
        if not rel.startswith("docs/archive/") and OLD_LINK.search(content):
            # Exclude historical *name* mentions, but never a stale live reference.
            # The code pattern is anchored to 'references/' for this reason.
            errors.append(f"STALE_RUNTIME_REFERENCE: {rel}")
        # Archived material is historical and cannot be a runtime route.
        # Keep legacy external references as history, but validate active
        # Markdown links across the full tracked inventory.
        if rel.startswith("docs/archive/"):
            continue
        for raw in LINK.findall(content):
            href = raw.split("#", 1)[0].strip()
            if not href or "://" in href or href.startswith(("mailto:", "data:", "/", "#")):
                continue
            if not (p.parent / href).exists():
                errors.append(f"BROKEN_LOCAL_LINK: {rel}")
    return sorted(set(errors))


def main() -> int:
    # File existence/relative links are deterministic, read-only checks.
    errors = inspect(ROOT)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("WS-D resource placement and migrated Markdown links: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
