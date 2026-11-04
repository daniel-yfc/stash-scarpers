#!/usr/bin/env python3
"""CrossQA PR104 section 7: run PR #104 production Date/Image postProcess JS
(extracted verbatim from scrapers/BRAVO.yml @ 86ce058) under node."""
import json, subprocess, sys
from pathlib import Path
import yaml

repo = Path.home() / "workspace/crossqa-pr104/repo"
doc = yaml.safe_load((repo / "scrapers/BRAVO.yml").read_text(encoding="utf-8"))
scene = doc["xPathScrapers"]["dvdSceneScraper"]["scene"]

def js_of(field):
    return [s["javascript"] for s in scene[field]["postProcess"] if "javascript" in s][0]

def run_js(script, value):
    prog = f"function __f(value) {{\n{script}\n}}\nconsole.log(__f({json.dumps(value, ensure_ascii=False)}));"
    r = subprocess.run(["node", "-e", prog], capture_output=True, text=True, cwd=repo)
    assert r.returncode == 0, r.stderr
    return r.stdout.rstrip("\n")

DATE_CASES = [
    ("2018年8月29日", "unpadded valid"),
    ("2010年09月30日", "zero-padded valid"),
    ("", "empty"),
    ("2018年13月1日", "month 13 - format-valid chars, JS does NOT range-check"),
    ("2018年1月32日", "day 32 - JS does NOT range-check"),
    ("2019年2月30日", "Feb 30 - calendar-invalid, format-valid"),
    ("発売日は2018年8月29日です", "embedded text - regex not anchored"),
    ("　2018年8月29日　", "full-width spaces around"),
    ("2018年​8月29日", "zero-width space inside"),
    ("2018/8/29", "wrong separators"),
    ("2018年8月29", "missing 日"),
]
IMAGE_CASES = [
    ("https://static.wixstatic.com/media/BR234.jpg", "genuine cover"),
    ("https://static.wixstatic.com/media/BR-084soldout.jpg", "soldout lower"),
    ("https://static.wixstatic.com/media/BR-084SoldOut.jpg", "SoldOut mixed case"),
    ("https://static.wixstatic.com/media/BR-084SOLDOUT.jpg", "SOLDOUT upper"),
    ("", "empty"),
    ("//static.wixstatic.com/media/x.jpg", "protocol-relative"),
    ("https://static.wixstatic.com/media/x.jpg?dn=abc", "query params stripped"),
    ("http://static.wixstatic.com/media/x.jpg", "http upgraded"),
    ("/media/x.jpg", "root-relative"),
    ("media/x.jpg", "relative"),
    ("./media/x.jpg", "dot-relative"),
    ("https://example.com/not-wixstatic.jpg", "unrelated host (JS alone does not check host; selector does)"),
    ("https://static.wixstatic.com/media/soldoutish-cover.jpg", "filename merely containing 'soldout' substring"),
]

print("== DATE_JS")
for v, note in DATE_CASES:
    print(f"  {v!r:40s} -> {run_js(js_of('Date'), v)!r}   # {note}")
print("== IMAGE_JS")
for v, note in IMAGE_CASES:
    print(f"  {v!r:55s} -> {run_js(js_of('Image'), v)!r}   # {note}")
# Also verify whether Date even has a parseDate step in YAML:
print("Date postProcess step kinds:", [list(s.keys()) for s in scene["Date"]["postProcess"]])
print("Image postProcess step kinds:", [list(s.keys()) for s in scene["Image"]["postProcess"]])
