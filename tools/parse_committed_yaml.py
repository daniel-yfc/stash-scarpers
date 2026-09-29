#!/usr/bin/env python3
"""Parse the exact YAML files in the checkout."""

from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors = []
    paths = sorted((ROOT / "scrapers").rglob("*.yml"))
    for path in paths:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc.__class__.__name__}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{path.relative_to(ROOT)}: root is not a mapping")
    print(f"Parsed {len(paths)} committed scraper YAML file(s)")
    if errors:
        for error in errors:
            print(f"- yaml-parse: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
