"""Doctor task — read-only scan. NEVER writes to Stash.

For each scene:
  1. Extract product code from file path (folder > basename)
  2. Resolve prefix against prefix table
  3. Compare resolved studio vs existing studio
  4. Categorize and write to audit journal + CSV report

Categories:
  - match: existing studio == resolved studio
  - mismatch: existing studio != resolved studio (needs review)
  - fillable: no studio, resolved unique (Enrich candidate)
  - ambiguous: no studio, resolved ambiguous (needs manual)
  - no_code: no product code extracted
  - absent: code extracted but prefix not in table
"""
import csv
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractor import extract_from_path
from resolver import PrefixTable

# Stash GraphQL endpoint. Set STASH_URL env var for your instance;
# default is a local placeholder (no real address in the public repo).
STASH_URL = os.environ.get("STASH_URL", "http://localhost:9999/graphql")
BATCH_SIZE = 100


def graphql(query: str, variables: dict | None = None) -> dict:
    import os
    import subprocess
    payload = json.dumps({"query": query, "variables": variables or {}})
    # Use curl via tunnel proxy (urllib proxy handling is unreliable here)
    proxy = os.environ.get("HTTPS_PROXY", "")
    if proxy:
        proxy = proxy.rsplit(":", 1)[0] + ":3130"
    cmd = [
        "curl", "-s", "--max-time", "60",
        "--proxy", proxy,
        "-H", "Content-Type: application/json",
        "-d", payload,
        STASH_URL,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=70)
    return json.loads(result.stdout)


SCENES_QUERY = """
query($filter: FindFilterType) {
  findScenes(filter: $filter) {
    count
    scenes {
      id
      title
      code
      studio { id name }
      files { basename path }
    }
  }
}
"""


def fetch_scenes_batch(page: int) -> tuple[list, int]:
    result = graphql(SCENES_QUERY, {"filter": {"page": page, "per_page": BATCH_SIZE}})
    data = result["data"]["findScenes"]
    return data["scenes"], data["count"]


def get_primary_path(scene: dict) -> str:
    files = scene.get("files") or []
    if not files:
        return ""
    # Prefer first file's path
    f = files[0]
    return f.get("path") or f.get("basename") or ""


def doctor(table: PrefixTable, out_dir: Path, limit: int | None = None):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    journal_path = out_dir / f"audit-doctor-{timestamp}.jsonl"
    csv_path = out_dir / f"doctor-report-{timestamp}.csv"

    stats = {
        "total": 0, "match": 0, "mismatch": 0, "fillable": 0,
        "ambiguous": 0, "no_code": 0, "absent": 0,
    }

    journal = open(journal_path, "w", encoding="utf-8")
    csv_file = open(csv_path, "w", encoding="utf-8", newline="")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow([
        "scene_id", "title", "code_extracted", "prefix",
        "resolved_studio", "resolved_sub_studio", "existing_studio",
        "category", "confidence",
    ])

    page = 1
    total = None
    while True:
        scenes, total = fetch_scenes_batch(page)
        if not scenes:
            break

        for scene in scenes:
            stats["total"] += 1
            sid = scene["id"]
            path = get_primary_path(scene)
            ext = extract_from_path(path)
            res = table.resolve(ext.prefix)

            existing = (scene.get("studio") or {}).get("name")

            # Categorize
            if not ext.code:
                category = "no_code"
            elif res.confidence == "absent":
                category = "absent"
            elif res.confidence == "ambiguous":
                category = "ambiguous" if not existing else "mismatch"
                # ambiguous + existing studio = potential mismatch, flag for review
            elif not existing:
                category = "fillable"
            elif existing == res.studio:
                category = "match"
            else:
                category = "mismatch"

            stats[category] += 1

            # Journal entry
            journal.write(json.dumps({
                "scene_id": sid,
                "prefix": ext.prefix,
                "code": ext.code,
                "code_source": ext.source,
                "table_version": "v20261012-1012",
                "confidence": res.confidence,
                "resolved_studio": res.studio,
                "resolved_sub_studio": res.sub_studio,
                "existing_studio": existing,
                "category": category,
                "needs_review": category in ("mismatch", "ambiguous"),
                "table_id": res.table_id,
            }, ensure_ascii=False) + "\n")

            # CSV row (only non-match for brevity)
            if category != "match":
                csv_writer.writerow([
                    sid, scene.get("title", ""), ext.code or "",
                    ext.prefix or "", res.studio or "",
                    res.sub_studio or "", existing or "",
                    category, res.confidence,
                ])

            if limit and stats["total"] >= limit:
                break

        print(f"  Page {page}: {stats['total']}/{total} "
              f"(match={stats['match']} mismatch={stats['mismatch']} "
              f"fillable={stats['fillable']} ambiguous={stats['ambiguous']})")
        if limit and stats["total"] >= limit:
            break
        if stats["total"] >= total:
            break
        page += 1

    journal.close()
    csv_file.close()

    print(f"\nDone. Total: {stats['total']}")
    print(f"  match:     {stats['match']}")
    print(f"  mismatch:  {stats['mismatch']}  <- needs review")
    print(f"  fillable:  {stats['fillable']}  <- Enrich candidates")
    print(f"  ambiguous: {stats['ambiguous']}  <- needs manual")
    print(f"  no_code:   {stats['no_code']}")
    print(f"  absent:    {stats['absent']}")
    print(f"\nJournal: {journal_path}")
    print(f"Report:  {csv_path}")
    return stats


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Max scenes (for testing)")
    parser.add_argument("--out", type=str, default="reports")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    table = PrefixTable(Path(__file__).parent.parent / "prefix-table")
    print(f"Loaded {len(table.entries)} prefix entries")
    doctor(table, out_dir, limit=args.limit)
