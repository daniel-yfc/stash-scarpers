#!/usr/bin/env python3
"""Scaffold a new Stash scraper YAML from an asset template.

Copies the matching assets/ template and substitutes the scraper name,
eliminating the #1 mechanical error class (name/filename mismatch).

Usage:
    python scripts/new-scraper.py --name SiteName --mode xpath|json|performer [--out SiteName.yml]

With --out, writes the file; otherwise prints to stdout. No network access.
"""

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATES = {
    "xpath": HERE / "../assets/scene-xpath-template.yml",
    "json": HERE / "../assets/scene-json-template.yml",
    "performer": HERE / "../assets/performer-xpath-template.yml",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a Stash scraper from an asset template.")
    parser.add_argument("--name", required=True, help="CamelCase scraper name, e.g. SiteName")
    parser.add_argument("--mode", required=True, choices=sorted(TEMPLATES),
                        help="Template flavour to scaffold from")
    parser.add_argument("--out", help="Write to this file instead of stdout")
    args = parser.parse_args()

    template = TEMPLATES[args.mode].resolve()
    if not template.exists():
        print(f"FAIL: template not found: {template}", file=sys.stderr)
        return 1
    text = template.read_text(encoding="utf-8")
    text = text.replace("SiteName", args.name)
    text = text.replace("ExamplePerformer", args.name)

    if args.out:
        out = Path(args.out)
        out.write_text(text, encoding="utf-8")
        print(f"Wrote {out} from {template.name}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
