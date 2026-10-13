#!/usr/bin/env python3
"""Convert the 5-column prefix Markdown table to spec-compliant JSON.

Reads: ../code-prefix-table-5col-2026-10-12.md
Writes: prefix-table/{site}.json + _meta.json

Spec §4.1 schema per entry:
{
  "id": "hunkch:GV-DSK",
  "source_site": "hunk-ch.com",
  "match": {"kind": "prefix", "value": "GV-DSK", "priority": 20},
  "studio": "G＠MES",
  "sub_studio": null,
  "label": null,
  "label_is_publisher": false,   # NEEDS MANUAL REVIEW (defaults false)
  "series": "筋肉雄マラ大失禁!!",
  "ambiguous_fields": [],
  "title_hints": []
}
"""
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
MD_PATH = HERE.parent / "code-prefix-table-5col-2026-10-12.md"
OUT_DIR = HERE / "prefix-table"

# Map markdown section titles to (site_key, source_site)
SECTION_MAP = {
    "GAMES（games-video.co.jp）": ("games", "games-video.co.jp"),
    "KOShop（ko-shop.com）": ("koshop", "ko-shop.com"),
    "HunkCh（hunk-ch.com）": ("hunkch", "hunk-ch.com"),
    "HunkCh 配信・独占（hunk-ch.com）": ("hunkch_3rd", "hunk-ch.com"),
    "MensRushTV（mensrush.tv）": ("mensrushtv", "mensrush.tv"),
    "MensRushTV 第三方（mensrush.tv）": ("mensrushtv_3rd", "mensrush.tv"),
    "CK-Download（ck-download.com）": ("ckdownload", "ck-download.com"),
    "CK-Download CKオリジナル（ck-download.com）": ("ckdownload_orig", "ck-download.com"),
    "COAT（coat.co.jp）": ("coat", "coat.co.jp"),
    "ACCEED（acceed.jp）— 部分完成 ⚠️": ("acceed", "acceed.jp"),
}


def parse_markdown():
    content = MD_PATH.read_text(encoding="utf-8")
    version_m = re.search(r"^Version: (\S+)", content, re.MULTILINE)
    version = version_m.group(1) if version_m else "unknown"

    sections = {}
    for m in re.finditer(r"## ([^\n]+)\n\n(.*?)(?=\n## |\Z)", content, re.DOTALL):
        title = m.group(1).strip()
        body = m.group(2)
        rows = []
        for line in body.split("\n"):
            r = re.match(
                r"^\| \d+ \| ([^|]*) \| ([^|]*) \| ([^|]*) \| ([^|]*) \| ([^|]*) \| ([^|]*) \|$",
                line,
            )
            if r:
                prefix, studio, sub, label, series, remark = [
                    x.strip() for x in r.groups()
                ]
                if prefix == "Prefix":
                    continue
                rows.append(
                    {
                        "prefix": prefix,
                        "studio": studio or None,
                        "sub_studio": sub or None,
                        "label": label or None,
                        "series": series or None,
                        "remark": remark or None,
                    }
                )
        if title in SECTION_MAP:
            sections[title] = rows
        else:
            print(f"WARN: unmapped section '{title}'", file=sys.stderr)
    return version, sections


def detect_ambiguous(rows):
    """A prefix shared by multiple distinct series/labels -> ambiguous_fields."""
    by_prefix = defaultdict(list)
    for r in rows:
        if r["prefix"]:
            by_prefix[r["prefix"]].append(r)
    ambiguous = {}
    for prefix, group in by_prefix.items():
        if len(group) <= 1:
            continue
        series_vals = {g["series"] for g in group if g["series"]}
        label_vals = {g["label"] for g in group if g["label"]}
        fields = []
        if len(series_vals) > 1:
            fields.append("series")
        if len(label_vals) > 1:
            fields.append("label")
        if fields:
            ambiguous[prefix] = fields
    return ambiguous


def merge_by_prefix(rows):
    """Merge rows sharing the same prefix into a single entry.

    Spec §4.1: id is source_site:match (unique per prefix per site).
    Fields identical across all rows stay; differing fields -> null + ambiguous_fields.
    """
    by_prefix = defaultdict(list)
    for r in rows:
        by_prefix[r["prefix"]].append(r)

    merged = []
    for prefix, group in by_prefix.items():
        studios = {g["studio"] for g in group}
        subs = {g["sub_studio"] for g in group}
        labels = {g["label"] for g in group}
        series_vals = {g["series"] for g in group}

        def unique(vals):
            vals = {v for v in vals if v}  # drop None/empty
            return next(iter(vals)) if len(vals) == 1 else None

        ambiguous = []
        studio_v = unique(studios)
        sub_v = unique(subs)
        label_v = unique(labels)
        series_v = unique(series_vals)
        if len({v for v in labels if v}) > 1:
            ambiguous.append("label")
        if len({v for v in series_vals if v}) > 1:
            ambiguous.append("series")
        if len({v for v in subs if v}) > 1:
            ambiguous.append("sub_studio")
        if len({v for v in studios if v}) > 1:
            ambiguous.append("studio")

        # Preserve table remarks (e.g. FANS- creator semantics); dedup, keep order.
        remarks = []
        for g in group:
            rm = (g.get("remark") or "").strip()
            if rm and rm not in remarks:
                remarks.append(rm)

        merged.append(
            {
                "prefix": prefix,
                "studio": studio_v,
                "sub_studio": sub_v,
                "label": label_v,
                "series": series_v,
                "ambiguous_fields": ambiguous,
                "remark": " ／ ".join(remarks) if remarks else None,
                # candidates for manual review
                "candidates": {
                    "labels": sorted({v for v in labels if v}),
                    "series": sorted({v for v in series_vals if v}),
                }
                if ambiguous
                else {},
                "row_count": len(group),
            }
        )
    return merged


def build_entry(site_key, source_site, merged_row, needs_review_list):
    prefix = merged_row["prefix"]
    base_id = (
        f"{site_key}:{prefix}"
        if prefix
        else f"{site_key}:blank-{merged_row['label'] or merged_row['series'] or 'unknown'}"
    )
    entry = {
        "id": base_id,
        "source_site": source_site,
        "match": {"kind": "prefix", "value": prefix, "priority": 20},
        "studio": merged_row["studio"],
        "sub_studio": merged_row["sub_studio"],
        "label": merged_row["label"],
        # MANUAL REVIEW REQUIRED - default false, reviewer sets true for publishers
        "label_is_publisher": False,
        "series": merged_row["series"],
        "ambiguous_fields": merged_row["ambiguous_fields"],
        "title_hints": [],
    }
    if merged_row.get("remark"):
        entry["remark"] = merged_row["remark"]
    # candidates kept as extension (not in spec, but useful for review)
    if merged_row["candidates"]:
        entry["_candidates"] = merged_row["candidates"]
    if not prefix:
        needs_review_list.append(f"{base_id}: blank prefix")
    return entry


def main():
    version, sections = parse_markdown()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    meta = {
        "table_version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": MD_PATH.name,
        "sites": {},
    }
    needs_review = []

    for title, (site_key, source_site) in SECTION_MAP.items():
        rows = sections.get(title, [])
        if not rows:
            print(f"WARN: no rows for '{title}'", file=sys.stderr)
            continue
        merged = merge_by_prefix(rows)
        entries = []
        seen_ids = set()
        for mrow in merged:
            entry = build_entry(site_key, source_site, mrow, needs_review)
            # Ensure unique ids
            eid = entry["id"]
            n = 2
            while eid in seen_ids:
                eid = f"{entry['id']}#{n}"
                n += 1
            entry["id"] = eid
            seen_ids.add(eid)
            entries.append(entry)

        out_path = OUT_DIR / f"{site_key}.json"
        out_path.write_text(
            json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        amb_count = sum(1 for e in entries if e["ambiguous_fields"])
        print(f"{site_key}.json: {len(entries)} entries ({amb_count} ambiguous)")
        meta["sites"][site_key] = {
            "source_site": source_site,
            "entries": len(entries),
            "ambiguous": amb_count,
        }

    meta["label_is_publisher_note"] = (
        "All entries default to false. Manual review required: "
        "set true where the Label is the publishing entity (vs a series name)."
    )
    (OUT_DIR / "_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if needs_review:
        print(f"\nNEEDS REVIEW ({len(needs_review)}):")
        for item in needs_review[:20]:
            print(f"  - {item}")

    print(f"\nDone. Table version: {version}")


if __name__ == "__main__":
    main()
