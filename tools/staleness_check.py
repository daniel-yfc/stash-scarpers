#!/usr/bin/env python3
"""
Verification metadata staleness harness for stash scrapers.

Parses verification metadata from YAML comment blocks and reports:
  - STALE  : validated_on older than `ttl_days` (default 30) — exit 1
  - AGING  : validated_on within TTL but ≥ TTL/2             — exit 0, listed
  - FRESH  : validated_on within TTL                         — summary only
  - NO_META: no verification metadata block found            — exit 0, listed

Only whitelisted metadata keys are parsed; general comments such as
`# Last Updated:` are intentionally ignored.

Renamed from livetest.py to free that name for the live-XPath/CDP test
harness under development on the tools/live-xpath-harness branch.
"""

import re
from datetime import date
from pathlib import Path
from typing import Dict, List

KNOWN_KEYS = {
    "validated_on",
    "ttl_days",
    "staleness_status",
    "tested_urls",
    "url_patterns_declared",
    "url_patterns_tested",
    "coverage_status",
    "postprocess_validated",
    "stash_integration_tested",
    "value_match_level",
    "robustness_notes",
    "last_robustness_check",
}

_KEY_ALTERNATION = "|".join(sorted(KNOWN_KEYS))
METADATA_PATTERN = re.compile(r"^#\s*(" + _KEY_ALTERNATION + r"):\s*(.+)$")


def parse_verification_metadata(yaml_content: str) -> Dict[str, str]:
    """Extract whitelisted verification metadata from comment lines."""
    metadata: Dict[str, str] = {}
    for line in yaml_content.split("\n"):
        m = METADATA_PATTERN.match(line)
        if m:
            key, value = m.groups()
            metadata[key] = value.strip()
    return metadata


def classify(validated_on: str, ttl_days: int = 30) -> str:
    """Classify a verified scraper date into STALE / AGING / FRESH."""
    try:
        validated = date.fromisoformat(validated_on)
    except (ValueError, TypeError):
        return "UNKNOWN"
    age = (date.today() - validated).days
    if age < 0:
        return "UNKNOWN"  # future date — treat as misconfigured
    if age > ttl_days:
        return "STALE"
    if age >= ttl_days / 2:
        return "AGING"
    return "FRESH"


def load_scraper_metadata(scraper_path: Path) -> Dict:
    """Load scraper YAML text and extract verification metadata."""
    content = scraper_path.read_text(encoding="utf-8")
    meta = parse_verification_metadata(content)
    if "validated_on" in meta:
        ttl = int(meta.get("ttl_days", 30))
        meta["staleness_status"] = classify(meta["validated_on"], ttl)
    else:
        meta["staleness_status"] = "NO_META"
    return meta


def scan(scraper_dirs: List[Path]) -> Dict[str, List[Dict]]:
    """Scan all given directories for scrapers and bucket by staleness."""
    buckets: Dict[str, List[Dict]] = {
        "STALE": [], "AGING": [], "FRESH": [], "UNKNOWN": [], "NO_META": [],
    }
    for scraper_dir in scraper_dirs:
        if not scraper_dir.is_dir():
            continue
        for f in sorted(scraper_dir.glob("*.yml")) + sorted(scraper_dir.glob("*.yaml")):
            meta = load_scraper_metadata(f)
            buckets[meta["staleness_status"]].append(
                {"file": f.name, "validated_on": meta.get("validated_on", "—")}
            )
    return buckets


def main() -> None:
    repo_root = Path(__file__).parent.parent
    scraper_dirs = [repo_root / "scrapers", repo_root / "scrapers" / "private"]

    print("=== Verification Metadata Check ===\n")
    buckets = scan(scraper_dirs)

    for status in ("STALE", "AGING", "FRESH", "UNKNOWN", "NO_META"):
        entries = buckets[status]
        if not entries:
            continue
        print(f"{status}: {len(entries)} scraper(s)")
        for e in entries:
            print(f"  - {e['file']}  (validated_on={e['validated_on']})")
        print()

    if buckets["STALE"]:
        print("❌ STALE scrapers found. Re-run live verification to refresh metadata.")
        raise SystemExit(1)

    if buckets["AGING"]:
        print("⚠️  AGING scrapers exist — schedule re-verification before they go STALE.")
    if buckets["NO_META"]:
        print("ℹ️  Scrapers without metadata are not yet covered by the staleness system.")
    if not (buckets["STALE"] or buckets["AGING"] or buckets["NO_META"]):
        print("✅ All tracked scrapers are FRESH.")


if __name__ == "__main__":
    main()
