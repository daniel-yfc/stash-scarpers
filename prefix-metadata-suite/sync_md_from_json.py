#!/usr/bin/env python3
"""Incrementally sync the 5-column prefix Markdown table from the suite JSONs.

Why incremental instead of full regeneration: md->json MERGES multiple rows
per prefix (ambiguous label/series go to _candidates, sorted), so a full
json->md rebuild cannot faithfully restore the original row order or the
label×series pairings (cartesian expansion would create phantom rows the
user never authored). Incremental sync keeps every authored md row
byte-for-byte and only applies the JSON-only deltas.

Reads:  ../code-prefix-table-5col-2026-10-12.md  (base table)
        prefix-table/*.json                      (skips _meta.json)
Writes: ../code-prefix-table-5col-vYYYYMMDD-HHMM.md (or argv[1])

Sync rules:
- JSON entry whose prefix already exists in the section -> untouched
  (md row wins; JSON-only field edits are NOT backported here).
- JSON entry whose prefix is absent from the section -> new row, inserted
  in sorted position (Studio -> Sub-Studio -> Label -> Prefix; stable).
- md row whose prefix no longer exists in the JSON (e.g. the superseded
  'STG/GMS' slash row) -> dropped.
- site JSON with no md section (justice, bravo) -> new section appended.
- Version stamp uses Asia/Taipei local time, per user convention.

Usage:
    python3 sync_md_from_json.py [output_path] [base_md_path]
"""
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).parent
TABLE_DIR = HERE / "prefix-table"
BASE_MD = HERE.parent / "code-prefix-table-5col-2026-10-12.md"

SECTION_ORDER = [
    ("games", "GAMES（games-video.co.jp）"),
    ("koshop", "KOShop（ko-shop.com）"),
    ("hunkch", "HunkCh（hunk-ch.com）"),
    ("hunkch_3rd", "HunkCh 配信・独占（hunk-ch.com）"),
    ("mensrushtv", "MensRushTV（mensrush.tv）"),
    ("mensrushtv_3rd", "MensRushTV 第三方（mensrush.tv）"),
    ("ckdownload", "CK-Download（ck-download.com）"),
    ("ckdownload_orig", "CK-Download CKオリジナル（ck-download.com）"),
    ("coat", "COAT（coat.co.jp）"),
    ("acceed", "ACCEED（acceed.jp）— 部分完成 ⚠️"),
]

TAIPEI = timezone(timedelta(hours=8))
ROW_RE = re.compile(
    r"^\| \d+ \| ([^|]*) \| ([^|]*) \| ([^|]*) \| ([^|]*) \| ([^|]*) \| ([^|]*) \|$"
)


def parse_md(path):
    content = path.read_text(encoding="utf-8")
    sections = {}  # title -> list of row dicts (in file order)
    order = []
    for m in re.finditer(r"## ([^\n]+)\n\n(.*?)(?=\n## |\Z)", content, re.DOTALL):
        title = m.group(1).strip()
        rows = []
        for line in m.group(2).split("\n"):
            r = ROW_RE.match(line)
            if r:
                vals = [x.strip() for x in r.groups()]
                if vals[0] == "Prefix":
                    continue
                rows.append(
                    {
                        "prefix": vals[0],
                        "studio": vals[1],
                        "sub_studio": vals[2],
                        "label": vals[3],
                        "series": vals[4],
                        "remark": vals[5],
                    }
                )
        sections[title] = rows
        order.append(title)
    return sections, order


def site_title(site_key, entries):
    known = dict(SECTION_ORDER)
    if site_key in known:
        return known[site_key]
    source_site = entries[0].get("source_site", "") if entries else ""
    studios = [e.get("studio") for e in entries if e.get("studio")]
    name = max(set(studios), key=studios.count) if studios else site_key
    return f"{name}（{source_site}）"


def sort_key(r):
    return (r["studio"], r["sub_studio"], r["label"], r["prefix"])


def main():
    stamp = datetime.now(TAIPEI).strftime("v%Y%m%d-%H%M")
    out_arg = sys.argv[1] if len(sys.argv) > 1 else (
        f"code-prefix-table-5col-{stamp}.md"
    )
    out_path = Path(out_arg)
    if not out_path.is_absolute():
        out_path = HERE.parent / out_path.name
    base_md = Path(sys.argv[2]) if len(sys.argv) > 2 else BASE_MD

    sections, order = parse_md(base_md)
    title_by_site = {sk: t for sk, t in SECTION_ORDER}

    json_entries = {}
    for fp in sorted(TABLE_DIR.glob("*.json")):
        if fp.name == "_meta.json":
            continue
        json_entries[fp.stem] = json.loads(fp.read_text(encoding="utf-8"))

    added, dropped = [], []
    new_sections = []

    for sk, entries in json_entries.items():
        title = title_by_site.get(sk)
        if title is None or title not in sections:
            # New site -> new section appended at the end.
            title = site_title(sk, entries)
            title_by_site[sk] = title
            sections[title] = []
            order.append(title)
            new_sections.append((sk, title))

        md_prefixes = {r["prefix"] for r in sections[title]}
        json_prefixes = {e["match"]["value"] or "" for e in entries}

        # Drop md rows whose prefix vanished from the JSON (superseded rows).
        kept = []
        for r in sections[title]:
            if r["prefix"] not in json_prefixes:
                dropped.append((sk, r["prefix"]))
            else:
                kept.append(r)
        sections[title] = kept

        # Add JSON-only prefixes as new rows.
        for e in entries:
            pfx = e["match"]["value"] or ""
            if pfx in md_prefixes or pfx in {r["prefix"] for r in kept}:
                continue
            # Ambiguous multi-row entries cannot be reconstructed safely
            # (md->json merge loses row order and label×series pairings);
            # warn instead of emitting phantom rows.
            if e.get("_candidates"):
                print(
                    f"  WARN: [{sk}] {pfx or '(blank)'} is JSON-only but "
                    f"ambiguous {e.get('ambiguous_fields')} — needs manual md rows",
                    file=sys.stderr,
                )
                continue
            sections[title].append(
                {
                    "prefix": pfx,
                    "studio": e.get("studio") or "",
                    "sub_studio": e.get("sub_studio") or "",
                    "label": e.get("label") or "",
                    "series": e.get("series") or "",
                    "remark": (e.get("remark") or "").strip(),
                }
            )
            added.append((sk, pfx))

        # Stable re-sort: existing rows keep relative order, new rows slot in.
        sections[title] = sorted(sections[title], key=sort_key)

    lines = [
        f"Version: {stamp}",
        "",
        "# Code Prefix 對應總表",
        "",
        "欄位：#｜Prefix｜Studio｜Sub-Studio｜Label｜Series｜Remark",
        "排序：Studio → Sub-Studio → Label。",
        "",
    ]
    total = 0
    for title in order:
        rows = sections[title]
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| # | Prefix | Studio | Sub-Studio | Label | Series | Remark |")
        lines.append("|---|--------|--------|------------|-------|--------|--------|")
        for i, r in enumerate(rows, 1):
            lines.append(
                f"| {i} | {r['prefix']} | {r['studio']} | {r['sub_studio']} "
                f"| {r['label']} | {r['series']} | {r['remark']} |"
            )
        lines.append("")
        total += len(rows)

    out_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {out_path} ({total} rows, {len(order)} sections), {stamp}")
    print(f"Added rows: {len(added)}")
    for sk, pfx in added:
        print(f"  + [{sk}] {pfx or '(blank)'}")
    print(f"Dropped rows: {len(dropped)}")
    for sk, pfx in dropped:
        print(f"  - [{sk}] {pfx or '(blank)'}")
    if new_sections:
        print("New sections:")
        for sk, t in new_sections:
            print(f"  ## {t}")


if __name__ == "__main__":
    main()
