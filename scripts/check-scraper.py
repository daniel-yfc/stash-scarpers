#!/usr/bin/env python3
"""Mechanical pre-checks for a Stash scraper YAML file.

Encodes the machine-checkable half of references/schema-checklist.md.
The official CommunityScrapers validator remains the authority; this is a
fast pre-check, not a replacement.

Usage:
    python scripts/check-scraper.py path/to/Scraper.yml

Exit 0 when no FAIL; exit 1 otherwise. No network access, no credentials.
"""

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("FAIL: PyYAML is required (pip install pyyaml)")
    sys.exit(1)

PLACEHOLDER_MARKERS = ("請填入實際值", "YOUR_", "XXX", "example", "placeholder",
                       "TODO", "FILL", "changeme", "test")

FRAGMENT_ACTIONS = ("sceneByFragment", "performerByFragment", "groupByFragment",
                    "galleryByFragment", "imageByFragment")


def check_url_sort(data, results):
    """All url: arrays must be sorted A-Z (validator -s)."""

    def walk(node, trail=""):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "url" and isinstance(value, list) and value:
                    items = [str(i) for i in value]
                    if items != sorted(items):
                        results.append(("FAIL", f"{trail}/url: not sorted A-Z"))
                    else:
                        results.append(("PASS", f"{trail}/url: sorted"))
                else:
                    walk(value, f"{trail}/{key}")
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{trail}[{i}]")

    walk(data)


def check_fragment_queryurl(data, results):
    for action in FRAGMENT_ACTIONS:
        node = data.get(action)
        if node is None:
            continue
        if isinstance(node, dict) and "queryURL" not in node:
            results.append(("FAIL", f"{action}: missing required queryURL"))
        elif isinstance(node, dict) and str(node.get("queryURL", "")).strip() == "{url}":
            results.append(("FAIL", f"{action}: bare queryURL \"{{url}}\" does not expand on "
                           "URL-less fragments (upstream nil-pointer panic risk); use "
                           "{{title}}/{{code}}/{{filename}} with queryURLReplace, or omit"))
        else:
            results.append(("PASS", f"{action}: queryURL present"))


def check_cookie_placeholders(data, results):
    driver = data.get("driver") or {}
    groups = driver.get("cookies") or []
    if not groups:
        results.append(("PASS", "driver.cookies: absent, nothing to check"))
        return
    for gi, group in enumerate(groups):
        for cookie in group.get("Cookies") or []:
            name = cookie.get("Name", "?")
            value = str(cookie.get("Value", ""))
            if not value:
                continue  # ValueRandom style
            if len(value) >= 24 and not any(m in value for m in PLACEHOLDER_MARKERS):
                results.append(("WARN", f"cookie {name}: value looks real, not a placeholder"))
            else:
                results.append(("PASS", f"cookie {name}: placeholder-like value"))


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__.strip().splitlines()[0])
        print("Usage: python scripts/check-scraper.py path/to/Scraper.yml")
        return 0 if len(sys.argv) == 2 else 2

    path = Path(sys.argv[1])
    results = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - report any parse failure plainly
        print(f"FAIL: YAML parse error: {exc}")
        return 1
    if not isinstance(data, dict):
        print("FAIL: top level is not a mapping")
        return 1
    results.append(("PASS", "YAML parses"))

    name = data.get("name")
    if not name:
        results.append(("FAIL", "root name: is required"))
    else:
        results.append(("PASS", "root name: present"))
        stem = path.stem
        if str(name) != stem:
            results.append(("WARN", f"root name: {name!r} != filename {stem!r} (convention)"))
        else:
            results.append(("PASS", "root name: matches filename"))

    check_url_sort(data, results)
    check_fragment_queryurl(data, results)
    check_cookie_placeholders(data, results)

    failed = warned = 0
    for status, msg in results:
        print(f"{status}: {msg}")
        failed += status == "FAIL"
        warned += status == "WARN"
    print(f"{len(results)} checks: {failed} FAIL, {warned} WARN")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
