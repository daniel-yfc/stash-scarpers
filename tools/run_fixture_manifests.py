#!/usr/bin/env python3
"""Discover and verify committed rendered-DOM fixture manifests.

No manifests means UNVERIFIED, never a site-fixture pass. Use --expect for a
scraper whose evidence claims fixture coverage; a missing expected manifest
fails. The called runner verifies each manifest and controls its own exit code.
"""

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(root: Path, runner: list[str], expected: list[str]) -> int:
    fixture_root = root / "tests" / "fixtures"
    manifests = sorted(fixture_root.rglob("*-fixtures.yml")) if fixture_root.exists() else []
    discovered = {p.relative_to(root).as_posix() for p in manifests}
    missing = sorted(set(expected) - discovered)
    for item in missing:
        print(f"MISSING EXPECTED FIXTURE MANIFEST: {item}", file=sys.stderr)
    if missing:
        return 1
    if not manifests:
        print("SITE FIXTURE VERIFICATION: UNVERIFIED (no committed manifests)")
        return 0
    failed = False
    for manifest in manifests:
        relative = manifest.relative_to(root).as_posix()
        result = subprocess.run([*runner, relative], cwd=root, check=False)
        print(f"{relative}: {'PASS' if result.returncode == 0 else 'FAIL'}")
        failed |= result.returncode != 0
    print(f"Fixture manifests discovered: {len(manifests)}")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expect", action="append", default=[], metavar="RELATIVE_PATH")
    args = parser.parse_args()
    return run(ROOT, ["node", "tools/verify-scraper-fixtures.mjs"], args.expect)


if __name__ == "__main__":
    sys.exit(main())
