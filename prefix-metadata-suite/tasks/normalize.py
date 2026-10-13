"""Normalize task — renames studios in Stash to canonical names per alias table.

ONLY renames per the user-approved alias table. NEVER changes semantic conflicts.
Dry-run by default. Writes audit journal.

Reads: alias-table.json (canonical -> [aliases])
Does: find studios matching aliases, rename to canonical via studioUpdate.
"""
import json
import subprocess
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Stash GraphQL endpoint. Set STASH_URL env var for your instance;
# default is a local placeholder (no real address in the public repo).
STASH_URL = os.environ.get("STASH_URL", "http://localhost:9999/graphql")
ALIAS_TABLE = Path(__file__).parent.parent / "alias-table.json"


def graphql(query: str, variables: dict | None = None) -> dict:
    payload = json.dumps({"query": query, "variables": variables or {}})
    proxy = os.environ.get("HTTPS_PROXY", "")
    if proxy:
        proxy = proxy.rsplit(":", 1)[0] + ":3130"
    cmd = ["curl", "-s", "--max-time", "60", "--proxy", proxy,
           "-H", "Content-Type: application/json", "-d", payload, STASH_URL]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=70)
    return json.loads(result.stdout)


def find_studio_by_name(name: str) -> dict | None:
    q = """
    query($name: String!) {
      findStudios(studio_filter: {name: {value: $name, modifier: EQUALS}}) {
        studios { id name }
      }
    }
    """
    r = graphql(q, {"name": name})
    studios = r.get("data", {}).get("findStudios", {}).get("studios", [])
    return studios[0] if studios else None


def rename_studio(studio_id: str, new_name: str, dry_run: bool) -> bool:
    if dry_run:
        return True
    m = """
    mutation($id: ID!, $name: String!) {
      studioUpdate(input: {id: $id, name: $name}) { id name }
    }
    """
    r = graphql(m, {"id": studio_id, "name": new_name})
    return bool(r.get("data", {}).get("studioUpdate"))


def main():
    dry_run = "--live" not in sys.argv
    mode = "DRY-RUN" if dry_run else "LIVE"
    print(f"Normalize task [{mode}]")
    print(f"Usage: python3 tasks/normalize.py [--live]")

    alias_data = json.loads(ALIAS_TABLE.read_text(encoding="utf-8"))
    canonical_map = alias_data["canonical"]

    # Build alias -> canonical lookup
    alias_to_canon = {}
    for canon, aliases in canonical_map.items():
        for a in aliases:
            alias_to_canon[a] = canon

    plan = []  # (alias_name, canonical, studio_id or None)
    for alias, canon in alias_to_canon.items():
        # Skip if alias == canonical (shouldn't happen)
        if alias == canon:
            continue
        studio = find_studio_by_name(alias)
        # Check if canonical already exists
        canon_studio = find_studio_by_name(canon)
        plan.append({
            "alias": alias,
            "canonical": canon,
            "alias_id": studio["id"] if studio else None,
            "alias_found": bool(studio),
            "canonical_id": canon_studio["id"] if canon_studio else None,
            "canonical_exists": bool(canon_studio),
        })

    # Report
    print(f"\n{'Alias':<20} {'Canonical':<15} {'AliasInStash':<12} {'CanonInStash'}")
    print("-" * 65)
    for p in plan:
        print(f"{p['alias']:<20} {p['canonical']:<15} "
              f"{'YES('+p['alias_id']+')' if p['alias_found'] else 'no':<12} "
              f"{'YES' if p['canonical_exists'] else 'no'}")

    # Execute renames (only when alias exists in Stash)
    renamed = 0
    skipped = 0
    conflicts = []
    for p in plan:
        if not p["alias_found"]:
            skipped += 1
            continue
        if p["canonical_exists"]:
            # Both exist — needs manual merge, don't auto-rename
            conflicts.append(p)
            print(f"  CONFLICT: both '{p['alias']}' and '{p['canonical']}' exist in Stash — manual merge needed")
            continue
        ok = rename_studio(p["alias_id"], p["canonical"], dry_run)
        if ok:
            renamed += 1
            print(f"  {'[DRY] Would rename' if dry_run else 'Renamed'}: '{p['alias']}' -> '{p['canonical']}'")
        else:
            print(f"  FAILED to rename '{p['alias']}'")

    print(f"\nDone [{mode}]: renamed={renamed} skipped(no alias in Stash)={skipped} "
          f"conflicts(both exist)={len(conflicts)}")

    # Write journal
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    journal_dir = Path(__file__).parent.parent / "reports"
    journal_dir.mkdir(exist_ok=True)
    journal_path = journal_dir / f"audit-normalize-{mode.lower()}-{ts}.jsonl"
    with open(journal_path, "w", encoding="utf-8") as f:
        for p in plan:
            f.write(json.dumps({**p, "mode": mode, "ts": ts}, ensure_ascii=False) + "\n")
    print(f"Journal: {journal_path}")


if __name__ == "__main__":
    main()
