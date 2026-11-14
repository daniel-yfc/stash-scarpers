#!/usr/bin/env python3
"""Write the GVDB ID custom field for performers scraped with GVDB.yml.

Why this exists: YAML scrapers cannot return custom_fields (the Stash
v0.31.1 scraper schema has no such performer field; upstream stash #6394).
The GVDB scraper therefore keeps the source URL in the performer's URLs,
and this tool derives the GVDB ID from that URL and writes it afterwards:

    performerUpdate with input { id, custom_fields: { partial: {"GVDB ID": N} } }
    (sent as a JSON variable, because the key contains a space)

Only `partial` is ever used, so existing custom fields are never cleared
and no other performer field is touched. Performers whose URLs contain
two different GVDB IDs are reported and skipped, never guessed.

Default is a dry run (no writes). Pass --apply to write.

Usage:
    STASH_API_KEY=<key> python3 tools/gvdb_custom_fields.py [--apply]
    python3 tools/gvdb_custom_fields.py --url http://192.168.1.10:9999/graphql

The API key comes from --api-key or the STASH_API_KEY environment
variable; never hardcode a real key in this file or commit one.
"""

import argparse
import json
import os
import re
import sys
import urllib.request

GVDB_URL_RE = re.compile(r"md\.gvdb\.org/(\d+)")
FIELD_NAME = "GVDB ID"

FIND_PERFORMERS = """
query FindPerformers($page: Int) {
  findPerformers(filter: { per_page: 100, page: $page, sort: "id", direction: ASC }) {
    count
    performers { id name urls custom_fields }
  }
}
"""

# The whole input goes through a variable on purpose: "GVDB ID" contains a
# space, which is not a valid GraphQL Name token in an inline input literal,
# but is fine as a JSON key inside a variable (custom_fields partial is a Map).
PERFORMER_UPDATE = """
mutation PerformerUpdate($input: PerformerUpdateInput!) {
  performerUpdate(input: $input) {
    id
    name
    custom_fields
  }
}
"""


def gql(url, api_key, query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("ApiKey", api_key)
    with urllib.request.urlopen(req) as resp:
        payload = json.loads(resp.read().decode())
    if payload.get("errors"):
        raise RuntimeError("GraphQL errors: %s" % payload["errors"])
    return payload["data"]


def fetch_all_performers(url, api_key):
    performers, page = [], 1
    while True:
        data = gql(url, api_key, FIND_PERFORMERS, {"page": page})["findPerformers"]
        performers.extend(data["performers"])
        if len(performers) >= data["count"] or not data["performers"]:
            return performers
        page += 1


def planned_updates(performers):
    """Return (updates, problems). updates: dicts with id/name/current/target."""
    updates, problems = [], []
    for perf in performers:
        ids = []
        for u in perf.get("urls") or []:
            m = GVDB_URL_RE.search(u or "")
            if m:
                ids.append(int(m.group(1)))
        unique = sorted(set(ids))
        if not unique:
            continue
        if len(unique) > 1:
            problems.append((perf, unique))
            continue
        target = unique[0]
        current = (perf.get("custom_fields") or {}).get(FIELD_NAME)
        if current is not None:
            try:
                if int(current) == target:
                    continue
            except (TypeError, ValueError):
                pass
        updates.append(
            {"id": perf["id"], "name": perf.get("name"), "current": current, "target": target}
        )
    return updates, problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:9999/graphql", help="Stash GraphQL endpoint")
    ap.add_argument("--api-key", default=os.environ.get("STASH_API_KEY", ""), help="Stash API key (or STASH_API_KEY env)")
    ap.add_argument("--apply", action="store_true", help="actually write (default: dry run)")
    args = ap.parse_args(argv)

    performers = fetch_all_performers(args.url, args.api_key)
    updates, problems = planned_updates(performers)

    for perf, ids in problems:
        print("SKIP performer %s (%s): multiple GVDB IDs in URLs: %s" % (perf["id"], perf.get("name"), ids))

    if not updates:
        print("Nothing to do: no performer needs a GVDB ID write (%d performers scanned)." % len(performers))
        return 0

    print("%s %d performer(s):" % ("Applying" if args.apply else "Dry run, would update", len(updates)))
    for upd in updates:
        print("  performer %s (%s): GVDB ID %r -> %d" % (upd["id"], upd["name"], upd["current"], upd["target"]))

    if not args.apply:
        print("Dry run only. Re-run with --apply to write.")
        return 0

    for upd in updates:
        variables = {
            "input": {
                "id": upd["id"],
                "custom_fields": {"partial": {FIELD_NAME: upd["target"]}},
            }
        }
        data = gql(args.url, args.api_key, PERFORMER_UPDATE, variables)
        written = (data["performerUpdate"].get("custom_fields") or {}).get(FIELD_NAME)
        try:
            ok = int(written) == upd["target"]
        except (TypeError, ValueError):
            ok = False
        print("  performer %s: %s (custom_fields GVDB ID now %r)" % (upd["id"], "OK" if ok else "VERIFY FAILED", written))
        if not ok:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
