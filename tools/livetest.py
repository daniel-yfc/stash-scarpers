#!/usr/bin/env python3
"""
Live test harness for stash scrapers with verification metadata parsing.

Parses verification metadata from YAML comment blocks and computes staleness.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List

METADATA_PATTERN = re.compile(r'^#\s*(\w+):\s*(.+)$')

def parse_verification_metadata(yaml_content: str) -> Dict[str, str]:
    """Parse verification metadata from YAML comment block."""
    metadata = {}
    for line in yaml_content.split('\n'):
        match = METADATA_PATTERN.match(line)
        if match:
            key, value = match.groups()
            metadata[key] = value.strip()
    return metadata

def compute_staleness(validated_on: str, ttl_days: int = 30) -> str:
    """Compute staleness status from validated_on date."""
    try:
        validated = datetime.strptime(validated_on, '%Y-%m-%d')
        age = (datetime.now() - validated).days
        if age <= ttl_days:
            return 'FRESH'
        elif age <= 90:
            return 'AGING'
        else:
            return 'STALE'
    except (ValueError, TypeError):
        return 'UNKNOWN'

def load_scraper_metadata(scraper_path: Path) -> Dict:
    """Load scraper YAML and parse verification metadata."""
    with open(scraper_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse metadata from comments
    metadata = parse_verification_metadata(content)
    
    # Compute staleness
    if 'validated_on' in metadata:
        ttl = int(metadata.get('ttl_days', 30))
        metadata['staleness_status'] = compute_staleness(metadata['validated_on'], ttl)
    else:
        metadata['staleness_status'] = 'UNKNOWN'
    
    return metadata

def check_stale_scrapers(scraper_dir: Path) -> List[Dict]:
    """Find all scrapers with STALE verification status."""
    stale = []
    for scraper_file in scraper_dir.glob('*.yml'):
        metadata = load_scraper_metadata(scraper_file)
        if metadata.get('staleness_status') == 'STALE':
            stale.append({
                'file': scraper_file.name,
                'validated_on': metadata.get('validated_on', 'UNKNOWN'),
                'staleness_status': 'STALE'
            })
    return stale

def main():
    scraper_dir = Path(__file__).parent.parent / 'scrapers'
    
    print("=== Verification Metadata Check ===\n")
    
    stale = check_stale_scrapers(scraper_dir)
    
    if stale:
        print(f"⚠️  Found {len(stale)} STALE scraper(s):\n")
        for s in stale:
            print(f"  - {s['file']}: validated_on={s['validated_on']}")
        print(f"\n💡 Action: Re-run live tests on these scrapers to refresh verification status.")
    else:
        print("✅ All scrapers are FRESH or have no verification metadata.")
    
    # CI exit code
    if stale:
        exit(1)

if __name__ == '__main__':
    main()
