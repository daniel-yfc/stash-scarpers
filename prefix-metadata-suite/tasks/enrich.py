"""Enrich task — fills empty scene fields from prefix resolution.

ONLY fills empty values. NEVER overwrites existing data.
Dry-run by default. Writes audit journal.

Fillable:
  - studio (from resolved studio/sub_studio)
  - code (from extracted product code)
  - series as tag (from resolved series)

Skipped:
  - ambiguous resolutions (needs manual)
  - scenes that already have the field filled
"""
import csv
import json
import subprocess
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractor import extract_from_path
from resolver import PrefixTable

# Stash GraphQL endpoint. Set STASH_URL env var for your instance;
# default is a local placeholder (no real address in the public repo).
STASH_URL = os.environ.get("STASH_URL", "http://localhost:9999/graphql")
BATCH_SIZE = 50


def graphql(query: str, variables: dict | None = None) -> dict:
    payload = json.dumps({"query": query, "variables": variables or {}})
    proxy = os.environ.get("HTTPS_PROXY", "")
    if proxy:
        proxy = proxy.rsplit(":", 1)[0] + ":3130"
    cmd = ["curl", "-s", "--max-time", "60", "--proxy", proxy,
           "-H", "Content-Type: application/json", "-d", payload, STASH_URL]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=70)
    return json.loads(result.stdout)


def find_or_create_studio(name: str, dry_run: bool) -> str | None:
    """Find studio by name, or create it. Returns studio ID."""
    # Find
    q = """
    query($name: String!) {
      findStudios(studio_filter: {name: {value: $name, modifier: EQUALS}}) {
        studios { id name }
      }
    }
    """
    result = graphql(q, {"name": name})
    studios = (result.get("data") or {}).get("findStudios", {}).get("studios", [])
    if studios:
        return studios[0]["id"]
    # Create
    if dry_run:
        return f"DRYRUN-NEW-{name}"
    q = """
    mutation($input: StudioCreateInput!) {
      studioCreate(input: $input) { id name }
    }
    """
    result = graphql(q, {"input": {"name": name}})
    data = result.get("data") or {}
    created = data.get("studioCreate")
    if created:
        return created["id"]
    # If create failed (e.g. duplicate), try finding again
    print(f"  WARN: studioCreate failed for '{name}': {result.get('errors')}")
    result = graphql("""
    query($name: String!) {
      findStudios(studio_filter: {name: {value: $name, modifier: EQUALS}}) {
        studios { id name }
      }
    }
    """, {"name": name})
    studios = (result.get("data") or {}).get("findStudios", {}).get("studios", [])
    if studios:
        return studios[0]["id"]
    return None


def update_scene(scene_id: str, studio_id: str | None, code: str | None,
                 dry_run: bool) -> bool:
    """Update scene studio and/or code. Returns True on success."""
    if dry_run:
        return True
    # Don't use DRYRUN IDs for real writes
    if studio_id and studio_id.startswith("DRYRUN-"):
        return False
    q = """
    mutation($input: SceneUpdateInput!) {
      sceneUpdate(input: $input) { id }
    }
    """
    input_data = {"id": scene_id}
    if studio_id:
        input_data["studio_id"] = studio_id
    if code:
        input_data["code"] = code
    result = graphql(q, {"input": input_data})
    return bool(result.get("data") and result["data"].get("sceneUpdate"))


def enrich(table: PrefixTable, out_dir: Path, dry_run: bool = True,
           limit: int | None = None):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    mode = "dryrun" if dry_run else "live"
    journal_path = out_dir / f"audit-enrich-{mode}-{timestamp}.jsonl"
    csv_path = out_dir / f"enrich-report-{mode}-{timestamp}.csv"

    journal = open(journal_path, "w", encoding="utf-8")
    csv_file = open(csv_path, "w", encoding="utf-8", newline="")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["scene_id", "title", "code_extracted", "code_filled",
                         "studio_set", "action"])

    stats = {"scanned": 0, "fillable": 0, "filled": 0, "skipped": 0, "errors": 0,
             "studio_filled": 0, "code_filled": 0}
    studio_cache = {}

    page = 1
    while True:
        q = """
        query($filter: FindFilterType) {
          findScenes(filter: $filter) {
            count
            scenes { id title code studio { id name } files { basename path } }
          }
        }
        """
        result = graphql(q, {"filter": {"page": page, "per_page": BATCH_SIZE}})
        data = result["data"]["findScenes"]
        scenes, total = data["scenes"], data["count"]
        if not scenes:
            break

        for scene in scenes:
            stats["scanned"] += 1
            sid = scene["id"]

            # Extract and resolve
            files = scene.get("files") or []
            path = files[0].get("path", "") if files else ""
            ext = extract_from_path(path)
            res = table.resolve(ext.prefix)

            # Determine what needs filling
            need_studio = not scene.get("studio")
            need_code = not scene.get("code") and ext.code

            # Only unique confidence; need at least one fillable field
            if res.confidence != "unique":
                stats["skipped"] += 1
                continue
            if not need_studio and not need_code:
                stats["skipped"] += 1
                continue
            if need_studio and not res.studio and not need_code:
                stats["skipped"] += 1
                continue

            stats["fillable"] += 1

            # Determine studio (if needed)
            # Priority: Label > Series > sub_studio > studio
            # (user 2026-10-12: Label/Series 當成 Studio 填入)
            studio_id = None
            studio_name = ""
            if need_studio and res.studio:
                if res.label:
                    studio_name = res.label
                elif res.series:
                    studio_name = res.series
                else:
                    _CATEGORY_SUBS = {"オリジナル", "独占", "配信"}
                    if res.sub_studio and res.sub_studio not in _CATEGORY_SUBS:
                        studio_name = res.sub_studio
                    else:
                        studio_name = res.studio
                if studio_name not in studio_cache:
                    studio_cache[studio_name] = find_or_create_studio(studio_name, dry_run)
                studio_id = studio_cache[studio_name]
                # Skip if studio creation failed and no code to fill
                if not studio_id and not code_to_fill:
                    stats["errors"] += 1
                    continue

            # Determine code (if needed)
            code_to_fill = ext.code if need_code else None

            # Update scene
            success = update_scene(sid, studio_id, code_to_fill, dry_run)
            if success:
                stats["filled"] += 1
                if studio_id:
                    stats["studio_filled"] += 1
                if code_to_fill:
                    stats["code_filled"] += 1
                action = "DRYRUN-WOULD-FILL" if dry_run else "FILLED"
            else:
                stats["errors"] += 1
                action = "ERROR"

            csv_writer.writerow([sid, scene.get("title", ""), ext.code or "",
                                 code_to_fill or "", studio_name, action])
            journal.write(json.dumps({
                "scene_id": sid,
                "prefix": ext.prefix,
                "code": ext.code,
                "code_filled": bool(code_to_fill),
                "studio_set": studio_name,
                "studio_id": studio_id,
                "action": action,
                "dry_run": dry_run,
                "table_id": res.table_id,
            }, ensure_ascii=False) + "\n")

            if limit and stats["scanned"] >= limit:
                break

        print(f"  Page {page}: scanned={stats['scanned']}/{total} "
              f"fillable={stats['fillable']} filled={stats['filled']}")
        if limit and stats["scanned"] >= limit:
            break
        if stats["scanned"] >= total:
            break
        page += 1

    journal.close()
    csv_file.close()

    print(f"\nEnrich {mode} done:")
    print(f"  scanned:       {stats['scanned']}")
    print(f"  fillable:      {stats['fillable']}")
    print(f"  filled:        {stats['filled']}")
    print(f"  studio_filled: {stats['studio_filled']}")
    print(f"  code_filled:   {stats['code_filled']}")
    print(f"  skipped:       {stats['skipped']}")
    print(f"  errors:        {stats['errors']}")
    print(f"\nJournal: {journal_path}")
    print(f"Report:  {csv_path}")
    return stats


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--live", action="store_true", help="Actually write (default is dry-run)")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", type=str, default="reports")
    args = parser.parse_args()

    dry_run = not args.live
    if not dry_run:
        confirm = input("LIVE MODE: This will write to Stash. Type YES to confirm: ")
        if confirm != "YES":
            print("Aborted.")
            sys.exit(1)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    table = PrefixTable(Path(__file__).parent.parent / "prefix-table")
    print(f"Loaded {len(table.entries)} prefix entries")
    print(f"Mode: {'DRY-RUN' if dry_run else 'LIVE'}")
    enrich(table, out_dir, dry_run=dry_run, limit=args.limit)
