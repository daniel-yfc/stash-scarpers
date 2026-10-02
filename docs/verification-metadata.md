# Verification Metadata Specification

This document defines the structured metadata format for scraper verification status. All metadata is stored in YAML comment blocks (prefixed with `#`) to ensure Stash ignores them while remaining machine-readable by tooling.

## Axes

Four orthogonal axes define verification completeness:

| Axis | Purpose | Fields |
|------|---------|--------|
| **Temporal** | When was it last verified, and is it still fresh? | `validated_on`, `ttl_days`, `staleness_status` |
| **Coverage** | Which URLs and page types were actually tested? | `tested_urls`, `url_patterns_declared`, `url_patterns_tested`, `coverage_status` |
| **Extraction** | Are postProcess chains and Stash integration validated? | `postprocess_validated`, `stash_integration_tested`, `value_match_level` |
| **Robustness** | Known failure modes, rate limits, geo-blocks? | `robustness_notes`, `last_robustness_check` |

## Field Definitions

### Temporal

| Field | Type | Description |
|-------|------|-------------|
| `validated_on` | `YYYY-MM-DD` | ISO date of last successful verification |
| `ttl_days` | `INTEGER` | Days before verification is considered stale (recommended: 30) |
| `staleness_status` | `ENUM` | Auto-computed: `FRESH` (≤30d), `AGING` (31–90d), `STALE` (>90d), `UNKNOWN` |

### Coverage

| Field | Type | Description |
|-------|------|-------------|
| `tested_urls` | `[URL]` | List of actual URLs tested |
| `url_patterns_declared` | `INTEGER` | Number of URL patterns declared in `scraper.schema.json` |
| `url_patterns_tested` | `INTEGER` | Number of patterns with at least one tested URL |
| `coverage_status` | `ENUM` | `COMPLETE` (all patterns tested), `PARTIAL`, `NONE` |

### Extraction

| Field | Type | Description |
|-------|------|-------------|
| `postprocess_validated` | `BOOLEAN` | Whether postProcess chains (replace/parseDate/javascript) were validated |
| `stash_integration_tested` | `BOOLEAN` | Whether scrape results were verified in Stash UI |
| `value_match_level` | `ENUM` | Evidence level: `L1` (schema only) through `L6` (value-level match) |

### Robustness

| Field | Type | Description |
|-------|------|-------------|
| `robustness_notes` | `TEXT` | Known issues: age gates, rate limits, geo-blocks, delisted content |
| `last_robustness_check` | `YYYY-MM-DD` | Date of last robustness assessment |

## Example Scraper Header

```yaml
# =============================================================================
# Verification metadata (Stash-ignored comment block)
# =============================================================================
# validated_on: 2026-09-06
# ttl_days: 30
# staleness_status: FRESH
# tested_urls:
#   - https://www.acceed.co.jp/detail.ACST424.html
#   - https://www.acceed.co.jp/detail.OCON059.html
# url_patterns_declared: 2
# url_patterns_tested: 2
# coverage_status: COMPLETE
# postprocess_validated: false
# stash_integration_tested: false
# value_match_level: L4
# robustness_notes: "Anonymous fetch works; detail pages require login (redirects to /login.php)"
# last_robustness_check: 2026-09-06
# =============================================================================

name: ACCEED
# ... rest of scraper YAML ...
```

## Machine Parsing

Tools (e.g., `tools/livetest.py`) should parse these comments using regex patterns:

```python
import re
from datetime import datetime, timedelta

METADATA_PATTERN = re.compile(r'^#\s*(\w+):\s*(.+)$')

def parse_verification_metadata(yaml_content: str) -> dict:
    metadata = {}
    for line in yaml_content.split('\n'):
        match = METADATA_PATTERN.match(line)
        if match:
            key, value = match.groups()
            metadata[key] = value.strip()
    return metadata

def compute_staleness(validated_on: str, ttl_days: int = 30) -> str:
    validated = datetime.strptime(validated_on, '%Y-%m-%d')
    age = (datetime.now() - validated).days
    if age <= ttl_days:
        return 'FRESH'
    elif age <= 90:
        return 'AGING'
    else:
        return 'STALE'
```

## Integration with LIVE_TEST_STATUS.md

The `LIVE_TEST_STATUS.md` table should include these columns:

| Scraper | Schema | Search card | Detail core | validated_on | ttl_days | staleness | coverage | postprocess | stash_int |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| ACCEED | Pass | L4 | UNVERIFIED | 2026-09-06 | 30 | FRESH | COMPLETE | false | false |
| Games-Video | Pass | n/a | L4 | 2026-09-06 | 30 | STALE | PARTIAL | false | false |

## CI Integration

The `link-check` workflow should:

1. Parse `validated_on` from each scraper file
2. Compute `staleness_status`
3. Fail or warn if `staleness_status == 'STALE'`
4. Post a comment on PRs with stale scrapers

See `tools/livetest.py` for implementation.
