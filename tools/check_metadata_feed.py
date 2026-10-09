#!/usr/bin/env python3
"""Offline website-scraper contracts; never writes to Stash or stash-box.

No arguments checks all scraper YAML. --inventory prints declared capabilities.
--payload checks a JSON array of ScrapedScene results (or a scrapeSingleScene
GraphQL response). This checks shape/quality, not factual identity or live access.
"""

import argparse
import datetime
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
MAPPED = {"scrapeXPath": "xPathScrapers", "scrapeJson": "jsonScrapers"}


def definition_errors(data):
    errors = []
    for entry, node in data.items():
        if not isinstance(node, dict) or node.get("action") not in MAPPED:
            continue
        query = node.get("queryURL", "")
        if entry.endswith("ByName") and ("{}" not in query or "{url}" in query):
            errors.append(f"{entry}: mapped name search must use {{}}; {{url}} is not substituted")
        if entry == "sceneByName":
            if not isinstance(data.get("sceneByQueryFragment"), dict):
                errors.append("sceneByName: missing selected-result detail entry point")
            block = data.get(MAPPED[node["action"]], {}).get(node.get("scraper"), {})
            scene = block.get("scene", {})
            if not scene.get("Title") or not (scene.get("URLs") or scene.get("URL")):
                errors.append("sceneByName: result needs Title and URL(s) for selection")
    fragment = data.get("sceneByFragment", {})
    search = data.get("sceneByName", {})
    if fragment.get("action") in MAPPED and search.get("action") == fragment.get("action"):
        same_mapper = fragment.get("scraper") == search.get("scraper")
        fragment_url = fragment.get("queryURL", "").split("?", 1)[0]
        search_url = search.get("queryURL", "").split("?", 1)[0]
        same_search_page = bool(fragment_url) and fragment_url == search_url and "{" not in fragment_url
        if same_mapper or same_search_page:
            errors.append("sceneByFragment: search-page reuse can silently select the first candidate; use manual search/detail")
    return errors


def capabilities(path, data):
    fragment = data.get("sceneByFragment")
    fields = set()
    for section in MAPPED.values():
        for block in data.get(section, {}).values():
            fields.update(block.get("scene", {}).keys())
    return {
        "file": path.as_posix(),
        "name": data.get("name"),
        "scene_url": bool(data.get("sceneByURL")),
        "scene_search": bool(data.get("sceneByName")),
        "identify_declared": bool(fragment),
        "identify_query": fragment.get("queryURL") if fragment else None,
        "cdp_required": bool(data.get("driver", {}).get("useCDP")),
        "scene_fields": sorted(fields),
        "live_stash": "UNVERIFIED",
        "stash_box_feed": "not implemented",
        "auto_tag": "indirect: saved local entity names only",
    }


def valid_url(value):
    if not isinstance(value, str) or value != value.strip() or re.search(r"[\s{}]", value):
        return False
    try:
        url = urlsplit(value)
        return url.scheme in ("http", "https") and bool(url.hostname) and not url.username and not url.password
    except ValueError:
        return False


def payload_errors(payload, allow_empty=False):
    """Repository quality policy for website-scraped scenes, not a GraphQL schema."""
    errors = []
    if isinstance(payload, dict):
        if payload.get("errors"):
            return ["GraphQL response contains errors (details suppressed)"]
        data = payload.get("data")
        payload = data.get("scrapeSingleScene") if isinstance(data, dict) else None
    if not isinstance(payload, list):
        return ["expected a scene array or data.scrapeSingleScene array"]
    if not payload and not allow_empty:
        return ["empty result: use --allow-empty only for a deliberate negative control"]
    seen_urls = set()

    def text(value):
        return isinstance(value, str) and bool(value.strip()) and value == value.strip() and not re.search(r"<[^>]+>", value)

    def urls_for(row, location, required=False):
        values = row.get("urls")
        if values is None:
            values = [row["url"]] if row.get("url") else []
        if not isinstance(values, list):
            errors.append(f"{location}: urls must be an array")
            return []
        if required and not values:
            errors.append(f"{location}: source URL required for traceability")
        if any(not valid_url(v) for v in values):
            errors.append(f"{location}: URLs must be absolute HTTP(S), without credentials or placeholders")
        valid = [v for v in values if valid_url(v)]
        if len(valid) != len(set(valid)):
            errors.append(f"{location}: duplicate URLs")
        return valid

    def identity(row, location):
        for key in ("remote_site_id", "stash_id", "stash_ids", "fingerprints"):
            if row.get(key):
                errors.append(f"{location}: website feed must not fabricate {key}; keep site code and URLs")

    for i, row in enumerate(payload):
        loc = f"scene[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{loc}: expected object")
            continue
        identity(row, loc)
        if not text(row.get("title")):
            errors.append(f"{loc}: nonempty plain source-language title required")
        for url in urls_for(row, loc, required=True):
            if url in seen_urls:
                errors.append(f"{loc}: source URL repeated across candidates")
            seen_urls.add(url)
        for field in ("date", "production_date"):
            value = row.get(field)
            if value is not None:
                try:
                    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                        raise ValueError()
                    datetime.date.fromisoformat(value)
                except ValueError:
                    errors.append(f"{loc}.{field}: valid ISO calendar date or null required")
        duration = row.get("duration")
        if duration is not None and (type(duration) is not int or duration <= 0):
            errors.append(f"{loc}.duration: positive integer seconds or null required")
        for field in ("performers", "tags", "studio"):
            value = row.get(field)
            if value is None:
                continue
            values = [value] if field == "studio" else value
            if not isinstance(values, list):
                errors.append(f"{loc}.{field}: expected array")
                continue
            names = set()
            for n, entity in enumerate(values):
                where = f"{loc}.{field}[{n}]"
                if not isinstance(entity, dict) or not text(entity.get("name")):
                    errors.append(f"{where}: nonempty plain name required")
                    continue
                name = entity["name"].casefold()
                if name in names:
                    errors.append(f"{where}: duplicate name requires identity review")
                names.add(name)
                identity(entity, where)
                urls_for(entity, where)
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--inventory", action="store_true")
    parser.add_argument("--payload", type=Path)
    parser.add_argument("--allow-empty", action="store_true")
    args = parser.parse_args(argv)
    errors, inventory = [], []
    if args.payload:
        try:
            errors = payload_errors(json.loads(args.payload.read_text(encoding="utf-8")), args.allow_empty)
        except (OSError, ValueError):
            errors = ["payload could not be read as JSON (contents suppressed)"]
    else:
        files = args.files or sorted((ROOT / "scrapers").rglob("*.yml"))
        if not files:
            errors.append("no scraper files found")
        for path in files:
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    raise ValueError()
                errors.extend(f"{path.name}: {e}" for e in definition_errors(data))
                inventory.append(capabilities(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path, data))
            except (OSError, ValueError, yaml.YAMLError):
                errors.append(f"{path.name}: unreadable scraper mapping (contents suppressed)")
    if args.inventory:
        print(json.dumps({"capabilities": inventory, "errors": errors}, ensure_ascii=False, indent=2))
    else:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Metadata feed contract: {'FAIL' if errors else 'PASS'}; offline checks only")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
