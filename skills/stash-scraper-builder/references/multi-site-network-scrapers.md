# Multi-site network scrapers

**Load when:** one scraper must cover multiple sites or a site network.

Canonical reference:

- https://deepwiki.com/stashapp/CommunityScrapers/4.2-multi-site-network-scrapers

## When to use (G7)

Use a network scraper when:

- 20–100+ domains share the **same HTML structure** (identical templates).
- Studio name can be derived from the domain or a small mapping.
- You want a single YAML file instead of many near-duplicates.

## Patterns

- URL routing via domain substrings.
- Studio name normalization from domain or small map.
- YAML anchors for shared scene/group blocks (**same file only**).
- Network-specific edge cases (different image hosts, slight template variants).

## Merge criteria (G7)

Merge network sites **only when templates match**. Use:

- Anchors for shared blocks.
- Domain map for studio names.
- Per-domain overrides when DOM / image host diverges.

Refer to multi-site configs in the upstream CommunityScrapers corpus (e.g. `Andomark.yml`) as structural examples.

## Filename & URL list (G5)

- Filename: CamelCase (network name, e.g. `GammaEntertainment.yml`).
- `url` fragments: specific enough to avoid clashes with other scrapers.
- List sorted **A–Z** (validator `-s` checks this).
- Not "longest path first" — alphabetical order only.
