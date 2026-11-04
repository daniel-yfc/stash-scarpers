"""Independent Delta QA matrix — extracts selectors/JS from production YAML at 3f3b455."""
import json, subprocess, sys
from pathlib import Path
import yaml
from lxml import html as LH

ROOT = Path.home() / "workspace/crossqa-pr104-delta/repo"
EV = Path.home() / "workspace/crossqa-pr104-delta/output/evidence"
cfg = yaml.safe_load((ROOT/"scrapers/BRAVO.yml").read_text(encoding="utf-8"))
dvd = cfg["xPathScrapers"]["dvdSceneScraper"]["scene"]
clip = cfg["xPathScrapers"]["clipSceneScraper"]["scene"]
print("DVD fields:", sorted(dvd.keys()))
print("URLs selector:", dvd["URLs"]["selector"])
print("QF present:", "sceneByQueryFragment" in cfg, "| Fragment present:", "sceneByFragment" in cfg)
print("Routes:", [(r.get("url"), r.get("scraper")) for r in cfg["sceneByURL"]])

def run_js(script, value):
    prog = "function __f(value) {\n%s\n}\nconsole.log(__f(%s));" % (script, json.dumps(value, ensure_ascii=False))
    r = subprocess.run(["node","-e",prog], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode==0, r.stderr
    return r.stdout.rstrip("\n")

date_js = [s["javascript"] for s in dvd["Date"]["postProcess"] if "javascript" in s][0]
print("Date postProcess steps:", [list(s.keys()) for s in dvd["Date"]["postProcess"]])
DATE = {
 "2018年8月29日":"2018-08-29","2010年09月30日":"2010-09-30",
 "2020年2月29日":"2020-02-29","2019年2月29日":"","2000年2月29日":"2000-02-29",
 "1900年2月29日":"","2100年2月29日":"","2400年2月29日":"2400-02-29",
 "2026年4月31日":"","2018年13月1日":"","2018年00月10日":"","2018年1月32日":"",
 "2018年8月00日":"","2019年2月30日":"", "":"", "not a date":"",
 "発売日は2018年8月29日です":"2018-08-29",  # embedded text: regex is unanchored (same as before delta)
 "0000年1月1日":"0000-01-01",  # year 0000: parseInt 0; leap calc (0%400==0 -> leap); Jan 1 valid
 "0000年2月29日":"0000-02-29",  # year 0 divisible by 400 -> leap per JS rule
 "2018年2月29日":"", "2024年12月31日":"2024-12-31", "2024年1月31日":"2024-01-31",
}
print("\n== DATE MATRIX (production JS via node) ==")
bad=0
for inp, exp in DATE.items():
    got = run_js(date_js, inp)
    ok = "OK " if got==exp else "MISMATCH"
    if got!=exp: bad+=1
    print(f"{ok} {inp!r:34} -> {got!r:14} expected {exp!r}")
print("date mismatches vs my expectation:", bad)

def ev_lxml(doc, sel):
    try:
        r = doc.xpath(sel)
    except Exception as e:
        return f"XPATH-ERROR: {e}"
    out=[]
    for n in r:
        out.append(n if isinstance(n,str) else (n.text_content().strip() if hasattr(n,'text_content') else str(n)))
    return out

FIELDS = ["Title","Code","URLs","Details","Date","Image"]
def all_fields_from_string(s):
    doc = LH.fromstring(s)
    res={}
    for f in FIELDS:
        sel = dvd[f]["selector"]
        res[f]=ev_lxml(doc, sel)
    return res

def page(canonical, h2s, extra=""):
    head = f'<link rel="canonical" href="{canonical}">' if canonical else ""
    body = "".join(f"<h2>{h}</h2>" for h in h2s) + extra
    return f"<!DOCTYPE html><html><head>{head}</head><body>{body}</body></html>"

CASES = {}
# original Cross-QA A fake page: canonical + 1 nav h2 + marker, nothing after
CASES["orig-fake-marker-777"] = page("https://www.bravo-japan.com/dvds/777", ["some nav","品番について"])
# upgraded fake: >=2 unrelated non-blank h2 before marker, >=1 after
CASES["upgraded-fake-777"] = page("https://www.bravo-japan.com/dvds/777",
    ["サイト案内","キャンペーン情報","新着情報","品番","お問い合わせ"])
# code missing: marker + title pair, following h2 is label only (misalignment shape)
CASES["code-is-label"] = page("https://www.bravo-japan.com/dvds/234",
    ["BRAVO-JAPAN","GO to BRAVO-CLIPS","勃起する白き花よ","Mr.Lily 編","品番","発売日","2018年8月29日"])
# title blank: preceding h2[2] whitespace only
CASES["title-blank"] = page("https://www.bravo-japan.com/dvds/234",
    ["BRAVO-JAPAN","GO to BRAVO-CLIPS","   ","Mr.Lily 編","品番","234","発売日","2018年8月29日"])
# code blank: following h2[1] whitespace only
CASES["code-blank"] = page("https://www.bravo-japan.com/dvds/234",
    ["BRAVO-JAPAN","GO to BRAVO-CLIPS","勃起する白き花よ","Mr.Lily 編","品番","  ","発売日","2018年8月29日"])
# code/canonical mismatch
CASES["mismatch-234-vs-999"] = page("https://www.bravo-japan.com/dvds/999",
    ["BRAVO-JAPAN","GO to BRAVO-CLIPS","勃起する白き花よ","Mr.Lily 編","品番","234","発売日","2018年8月29日"])
# multi-marker: real product marker first, second stray marker later with junk h2s around
CASES["multi-marker-real-first"] = page("https://www.bravo-japan.com/dvds/234",
    ["BRAVO-JAPAN","GO to BRAVO-CLIPS","勃起する白き花よ","Mr.Lily 編","品番","234","発売日","2018年8月29日","品番","999"])
# multi-marker: stray marker FIRST (before real structure), product marker second
CASES["multi-marker-stray-first"] = page("https://www.bravo-japan.com/dvds/234",
    ["案内","品番","問合せ","BRAVO-JAPAN","GO to BRAVO-CLIPS","勃起する白き花よ","Mr.Lily 編","品番","234","発売日","2018年8月29日"])
# canonical-only
CASES["canonical-only"] = page("https://www.bravo-japan.com/dvds/555", [])

print("\n== ADVERSARIAL PAGES (lxml, all production field selectors, raw before postProcess) ==")
for name, s in CASES.items():
    (EV/f"adv-{name}.html").write_text(s, encoding="utf-8")
    res = all_fields_from_string(s)
    print(f"-- {name}: URLs={res['URLs']} Title={res['Title']} Code={res['Code']} Date={res['Date']}")

print("\n== FIXTURES (lxml) ==")
for f in sorted((ROOT/"tests/fixtures/bravo").glob("dvd-synthetic-*.html")):
    doc = LH.parse(str(f))
    res = {fld: ev_lxml(doc, dvd[fld]["selector"]) for fld in FIELDS}
    print(f"{f.name}: URLs={res['URLs']} Title={res['Title']} Code={res['Code']}")
