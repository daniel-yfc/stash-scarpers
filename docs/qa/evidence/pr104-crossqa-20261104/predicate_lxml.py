#!/usr/bin/env python3
"""CrossQA PR104: evaluate PR #104 production DVD selectors with lxml (XPath 1.0).

Selectors are taken verbatim from scrapers/BRAVO.yml @ 86ce058.
"""
import sys, json
from pathlib import Path
from lxml import html as LH

REPO = Path.home() / "workspace/crossqa-pr104/repo"
FIX = REPO / "tests/fixtures/bravo"
ADV = Path.home() / "workspace/crossqa-pr104/output/evidence"

SELECTORS = {
    "Title":   "//h2[contains(.,'品番')]/preceding::h2[2]",
    "Code":    "//h2[contains(.,'品番')]/following::h2[1]",
    "URLs_GATED": "//link[@rel='canonical'][//h2[contains(.,'品番')]]/@href",
    "URLs_PLAIN": "//link[@rel='canonical']/@href",
    "Details": "//p[contains(@class,'font_8')]",
    "Date":    "//h2[contains(.,'発売日')]/following::h2[1]",
    "Image":   "//img[@alt!='' and contains(@src,'wixstatic')]/@src",
}

PAGES = [
    ("fixture", "dvd-synthetic-234.html"),
    ("fixture", "dvd-synthetic-084.html"),
    ("fixture", "dvd-synthetic-046.html"),
    ("fixture", "dvd-synthetic-281.html"),
    ("fixture", "dvd-synthetic-377.html"),
    ("fixture", "dvd-synthetic-384.html"),
    ("fixture", "dvd-synthetic-404-00.html"),
    ("fixture", "dvd-synthetic-404-999999.html"),
    ("fixture", "dvd-synthetic-cloudflare-challenge.html"),
    ("fixture", "dvd-synthetic-logo-empty-alt.html"),
    ("adversarial", "adversarial-fake-marker-777.html"),
    ("adversarial", "adversarial-canonical-only-404.html"),
    ("adversarial", "adversarial-marker-in-p.html"),
    ("adversarial", "adversarial-code-missing.html"),
    ("adversarial", "adversarial-canonical-mismatch.html"),
    ("adversarial", "adversarial-marker-after-canonical-position.html"),
]

def val(node):
    if isinstance(node, str):
        return node.strip()
    return (node.text_content() or "").strip().replace("​", "")

out = {}
for kind, name in PAGES:
    path = (FIX if kind == "fixture" else ADV) / name
    doc = LH.parse(str(path))
    row = {}
    for field, sel in SELECTORS.items():
        try:
            res = doc.xpath(sel)
            row[field] = [val(n) for n in res]
        except Exception as e:
            row[field] = f"ERROR: {e}"
    out[name] = row
    print(f"== {name}")
    for f, v in row.items():
        print(f"   {f:12s} {v}")
print("\nJSON:")
print(json.dumps(out, ensure_ascii=False, indent=1))
