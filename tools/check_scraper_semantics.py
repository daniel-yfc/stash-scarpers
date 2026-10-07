#!/usr/bin/env python3
"""Semantic checks on scraper YAML that the JSON schema cannot express.

1. Gender values: `fixed:` and `map:` values under a `Gender:` field must be
   in the official enum (case-insensitive):
   male, female, transgender_male, transgender_female, intersex, non_binary.
2. movieByURL: deprecated; warn if present (use groupByURL).
3. parseDate: format string should contain `2006` (Go reference year).
   Catches yyyy-MM-dd / %Y-%m-%d style mistakes the blacklist may miss.

Exit 0 if clean, 1 with details otherwise.
Usage: python3 tools/check_scraper_semantics.py [file ...]
       (no args = all scrapers/*.yml)
"""

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
GENDER_ENUM = {
    "male", "female", "transgender_male", "transgender_female",
    "intersex", "non_binary",
}

errors = []
warnings = []


def check_gender(data, path):
    """Walk the YAML tree; validate Gender fixed/map values."""
    def walk(node, trail=""):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "Gender":
                    check_gender_node(v, f"{path}:{trail}/Gender")
                else:
                    walk(v, f"{trail}/{k}")
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{trail}[{i}]")

    def check_gender_node(node, loc):
        if not isinstance(node, dict):
            return
        fixed = node.get("fixed")
        if isinstance(fixed, str) and fixed.lower() not in GENDER_ENUM:
            errors.append(f"{loc}: Gender fixed value {fixed!r} not in enum {sorted(GENDER_ENUM)}")
        mapping = node.get("map")
        if isinstance(mapping, dict):
            for src, dst in mapping.items():
                if isinstance(dst, str) and dst.lower() not in GENDER_ENUM:
                    errors.append(
                        f"{loc}: Gender map value {dst!r} (for {src!r}) not in enum"
                    )

    walk(data)


def check_movie_by_url(data, path):
    if "movieByURL" in data:
        warnings.append(
            f"{path}: movieByURL is deprecated; use groupByURL"
        )


def check_parse_date(data, path):
    def walk(node, trail=""):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "parseDate" and isinstance(v, str):
                    if "2006" not in v:
                        errors.append(
                            f"{path}:{trail}/parseDate: {v!r} does not look like a "
                            "Go reference layout (expected 2006-01-02 style)"
                        )
                else:
                    walk(v, f"{trail}/{k}")
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{trail}[{i}]")

    walk(data)


def check_file(path):
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except Exception as e:
        errors.append(f"{path}: YAML parse failed: {e}")
        return
    if not isinstance(data, dict):
        return
    check_gender(data, path)
    check_movie_by_url(data, path)
    check_parse_date(data, path)


def main():
    args = sys.argv[1:]
    if args:
        files = [Path(a) for a in args]
    else:
        files = sorted((ROOT / "scrapers").rglob("*.yml"))

    for f in files:
        if f.is_file():
            check_file(f)

    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")

    if errors:
        print(f"\n{len(errors)} semantic error(s) found.")
        return 1
    print("Scraper semantics check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
