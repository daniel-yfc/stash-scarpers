"""Fix the 3 scenes mis-written by the buggy resolver during the 2026-10-12 live enrich.

Background: resolver.py sorted by raw prefix length (dashes included), so
"KG-" (3) tied "KGS" (3) and load order let hunkch_3rd:KG- -> KONG win over
koshop:KGS -> KO COMPANY. The live enrich (audit-enrich-live-20261012-033621)
therefore wrote Studio=KONG (id 733) into 3 scenes whose prefixes actually
resolve to the KO family. The sort-key bug is fixed (dash-stripped length,
exact matches first); this script repairs the live DB.

User approvals (2026-10-13T01:44:14Z, chat c16195d2):
  - 套用 : resolver fix applied + verified 2026-10-13T02:05Z
  - 修改 : correct the 3 scenes' Studio values
  - 裁   : KG- prefix tie-break (KO vs KONG) stays with the user

Modes:
  - default (no flags): READ-ONLY. Fetches current studio/code for the 3
    scenes and reports current vs expected. Exit 0 = the two approved
    corrections are already correct; exit 2 = corrections still pending.
  - --apply: writes ONLY the two user-approved corrections
    (14634, 14636 -> 合法ショタ). Scene 6866 is NEVER touched here:
    its value awaits the user's tie-break ruling (KO vs KONG).

Writes an audit journal like the other tasks.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from stash_client import graphql

# scene_id -> (code, approved studio name). Approved by user 2026-10-13T01:44:14Z.
APPROVED_FIXES = {
    "14634": ("KGS-001", "合法ショタ"),
    "14636": ("KGS-003", "合法ショタ"),
}
# scene 6866 (KG-447) currently holds the mis-written KONG; value awaits
# the user's own tie-break ruling (KO vs KONG). DO NOT auto-correct.
PENDING_RULING = {"6866": ("KG-447", "KO vs KONG (user adjudicates)")}


def fetch_scene(scene_id: str) -> dict | None:
    q = """
    query($id: ID!) {
      findScene(id: $id) { id title code studio { id name } }
    }
    """
    try:
        data = graphql(q, {"id": scene_id}).get("data") or {}
    except Exception as e:  # noqa: BLE001 - connectivity unknown until tried
        print(f"  ERROR: Stash unreachable ({e})", file=sys.stderr)
        return None
    scene = data.get("findScene")
    if scene is None:
        print(f"  ERROR: scene {scene_id} not found or query failed",
              file=sys.stderr)
    return scene


def find_studio_id(name: str) -> str | None:
    """Find studio by exact name. Never creates; returns None if absent."""
    q = """
    query($name: String!) {
      findStudios(studio_filter: {name: {value: $name, modifier: EQUALS}}) {
        studios { id name }
      }
    }
    """
    data = (graphql(q, {"name": name}).get("data") or {})
    studios = data.get("findStudios", {}).get("studios", [])
    return studios[0]["id"] if studios else None


def set_studio(scene_id: str, studio_id: str) -> bool:
    q = """
    mutation($input: SceneUpdateInput!) {
      sceneUpdate(input: $input) { id }
    }
    """
    data = (graphql(q, {"input": {"id": scene_id, "studio_id": studio_id}})
            .get("data") or {})
    return bool(data.get("sceneUpdate"))


def check() -> int:
    """Read-only status check. Returns 0 if approved fixes already applied,
    2 if any approved fix is still pending, 3 if Stash unreachable."""
    print("== read-only check (no writes) ==")
    pending = 0
    for sid, (code, target) in APPROVED_FIXES.items():
        scene = fetch_scene(sid)
        if scene is None:
            return 3
        cur = (scene.get("studio") or {}).get("name")
        ok = cur == target
        print(f"  scene {sid} ({code}): current Studio={cur!r} "
              f"-> target {target!r} [{'OK' if ok else 'PENDING'}]")
        if not ok:
            pending += 1
    for sid, (code, note) in PENDING_RULING.items():
        scene = fetch_scene(sid)
        cur = (scene.get("studio") or {}).get("name") if scene else "?"
        print(f"  scene {sid} ({code}): current Studio={cur!r} "
              f"-> {note} [NOT touched by this script]")
    return 2 if pending else 0


def apply(out_dir: Path) -> int:
    """Apply ONLY the two user-approved corrections."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    journal_path = out_dir / f"audit-fix-miswritten-studios-{ts}.jsonl"
    results = []
    print("== applying user-approved corrections ==")
    for sid, (code, target) in APPROVED_FIXES.items():
        scene = fetch_scene(sid)
        if scene is None:
            results.append({"scene_id": sid, "ok": False,
                            "reason": "fetch failed"})
            continue
        cur = (scene.get("studio") or {}).get("name")
        if cur == target:
            print(f"  scene {sid}: already {target!r}, skipping")
            results.append({"scene_id": sid, "ok": True, "skipped": True,
                            "before": cur, "after": cur})
            continue
        studio_id = find_studio_id(target)
        if not studio_id:
            print(f"  scene {sid}: studio {target!r} not found, ABORTING",
                  file=sys.stderr)
            results.append({"scene_id": sid, "ok": False,
                            "reason": f"studio {target!r} not found"})
            continue
        if not set_studio(sid, studio_id):
            print(f"  scene {sid}: sceneUpdate failed", file=sys.stderr)
            results.append({"scene_id": sid, "ok": False,
                            "reason": "sceneUpdate failed"})
            continue
        # verify
        after = fetch_scene(sid)
        after_name = (after.get("studio") or {}).get("name") if after else None
        ok = after_name == target
        print(f"  scene {sid}: {cur!r} -> {after_name!r} "
              f"[{'VERIFIED' if ok else 'MISMATCH!'}]")
        results.append({"scene_id": sid, "code": code, "ok": ok,
                        "before": cur, "after": after_name,
                        "studio_id": studio_id})
    journal_path.write_text(
        "".join(json.dumps({"ts": ts, **r}, ensure_ascii=False) + "\n"
                for r in results), encoding="utf-8")
    print(f"  journal: {journal_path}")
    for sid, (code, note) in PENDING_RULING.items():
        print(f"  NOTE: scene {sid} ({code}) untouched - {note}")
    return 0 if all(r["ok"] for r in results) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="write the two user-approved corrections "
                         "(default is read-only check)")
    args = ap.parse_args()
    out_dir = Path(__file__).parent.parent / "reports"
    out_dir.mkdir(exist_ok=True)
    if args.apply:
        return apply(out_dir)
    return check()


if __name__ == "__main__":
    sys.exit(main())
