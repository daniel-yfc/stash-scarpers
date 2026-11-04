#!/usr/bin/env python3
"""Agent D independent XPath replay: Agent A's recorded selectors
(xpath-evaluation-results.json @ 4963523/9b4ab10) evaluated with lxml on
Agent D's own CDP captures (raw/), compared field-by-field against A's
published node counts and values for DVD 234/084/046/00/999999."""
import json, hashlib
from pathlib import Path
from lxml import html

BASE = Path(__file__).parent
A = json.loads((BASE / "a-evaluation.json").read_text(encoding="utf-8"))
ZWSP = "\u200b"

def clean(v):
    if isinstance(v, str):
        return " ".join(v.replace(ZWSP, "").split())
    return " ".join(" ".join(v.itertext()).replace(ZWSP, "").split())

def main():
    prov = {r["dvd"]: r for r in json.loads((BASE / "capture-provenance.json").read_text(encoding="utf-8"))}
    out = {"assignment": "WAVE2E-D-G1-DVD-DOM-INDEPENDENT-REPLAY-20261104",
           "evaluator": "lxml (Agent D venv) xpath-1.0",
           "a_reference": "research/e2e-bravo-dvd-dom @9b4ab10, xpath-evaluation-results.json",
           "pages": []}
    all_ok = True
    for page in A["pages"]:
        code = page["dvd"]
        if code not in ("234", "084", "046", "00", "999999"):
            continue
        raw = (BASE / "raw" / f"dvd-{code}.rendered.html").read_bytes()
        doc = html.fromstring(raw.decode("utf-8"))
        prec = {"dvd": code, "a_input_sha256": page["input_sha256"],
                "d_capture": prov[code], "fields": [], "page_ok": True}
        for fname, f in page["fields"].items():
            nodes = doc.xpath(f["xpath"])
            values = [clean(n) for n in nodes]
            exp_values = [clean(v) if isinstance(v, str) else v for v in f.get("values", [])]
            count_ok = len(nodes) == f.get("node_count")
            values_ok = values == exp_values
            match_mode = "exact"
            if not values_ok and fname == "Details" and len(values) == len(exp_values) == 1:
                import re as _re
                if _re.sub(r"\s+", "", values[0]) == _re.sub(r"\s+", "", exp_values[0]):
                    values_ok, match_mode = True, "whitespace_boundary_only (inline-element joins; content identical)"
            if not values_ok and fname == "h2_total":
                # A stores only the first 3 h2 values; node_count carries the total
                if values[:len(exp_values)] == exp_values and count_ok:
                    values_ok, match_mode = True, "stored_prefix (A truncates h2 values to 3)"
            ok = count_ok and values_ok
            prec["page_ok"] = prec["page_ok"] and ok
            prec["fields"].append({
                "field": fname, "xpath": f["xpath"],
                "expected_nodes": f.get("node_count"), "actual_nodes": len(nodes),
                "nodes_match": count_ok, "values_match": values_ok, "match_mode": match_mode,
                "expected_values": exp_values if not values_ok else "== actual",
                "actual_values": values if (not values_ok or fname in ("Title", "Code", "Details")) else f["values"][:1],
            })
        all_ok = all_ok and prec["page_ok"]
        out["pages"].append(prec)
        print(code, "page_ok:", prec["page_ok"],
              "| mismatches:", [x["field"] for x in prec["fields"] if not (x["nodes_match"] and x["values_match"])])
    out["all_pages_ok"] = all_ok
    (BASE / "replay-results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ALL_PAGES_OK:", all_ok)

if __name__ == "__main__":
    main()
