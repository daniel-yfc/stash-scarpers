"""Wave 2E Agent F — BRAVO DVD integration tests (feat/e2e-bravo-dvds).

Covers what Agent B/C tests deliberately do not: the production
dvdSceneScraper itself — its field set, its verified selectors, the
品番-gated URLs selector, and the JavaScript postProcess logic for
Date normalization and the 084 sold-out Image filter. The JavaScript
is read from the production YAML and executed with node, so these
tests verify the shipped code, not a copy of it.

Policy enforced here (G1 acceptance + Controller decisions):
* Production DVD fields are exactly Title, Code, URLs, Details,
  Date, Image. Duration (whole-DVD total), Studio (source Label),
  site-generic Tags and Performers are NOT mapped.
* sceneByQueryFragment is removed (WS-2E-QF-001); sceneByFragment
  stays absent; sceneByURL carries exactly the Clips and DVD routes.
* A 404 DVD page yields no fields at all: the URLs selector is
  gated on the 品番 marker, so the 404 canonical is suppressed.
* Date normalizes both Japanese source forms (2018年8月29日 and
  2010年09月30日) to Stash YYYY-MM-DD; unparseable input is empty.
* 084's BR-084soldout.jpg placeholder maps to empty Image.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
BRAVO = ROOT / "scrapers" / "BRAVO_JAPAN.yml"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "bravo"
JSDOM = ROOT / "node_modules" / "jsdom"

VERIFIED_SELECTORS = {
    # Title/Code superseded 2026-11-15 (Gate B GATEB-BRAVO-FINETUNE-
    # 20261115 runtime fix): the G1 positional forms are correct in a
    # spec engine but not in the Stash runtime's antchfx engine, whose
    # per-batch axis predicates swept the header chrome lines into
    # Title and every following h2 into Code. The replacements keep
    # the same target elements under both engines; behaviour is
    # pinned by tools/tests/bravo-runtime-model.test.mjs.
    "Title": "//h2[contains(.,'品番')]/preceding::h2[not(contains(.,'BRAVO-JAPAN') or contains(.,'BRAVO-CLIPS'))][2] | //h2[contains(.,'品番')]/preceding::h2[not(contains(.,'BRAVO-JAPAN') or contains(.,'BRAVO-CLIPS'))][1]",
    "Code": "(//h2[contains(.,'品番')]/following::h2)[1] | (//h2[contains(.,'品番')]/following::h2)[2][contains(.,'-')]",
    "Details": "//p[contains(@class,'font_8')]",
    "Date": "//h2[contains(.,'発売日')]/following::h2[1]",
    "Image": "//img[@alt!='' and contains(@src,'wixstatic')]/@src",
}

# Agent A verified release dates (RAW-DOM-VERIFICATION-ADDENDUM.md §2).
DATE_CASES = {
    "2018年8月29日": "2018-08-29",
    "2012年11月17日": "2012-11-17",
    "2020年7月31日": "2020-07-31",
    "2010年09月30日": "2010-09-30",
    "2026年5月31日": "2026-05-31",
    "2026年10月22日": "2026-10-22",
    "2026年9月21日": "2026-09-21",
    "2021年10月15日": "2021-10-15",
    "2022年6月26日": "2022-06-26",
    "": "",
    "not a date": "",
    # WAVE2E-F-PR104-HARDENING-20261104-R4 (A-01, PR104-CROSSQA-P1-3):
    # calendar validation — executed from the production YAML JS.
    "2024年2月29日": "2024-02-29",  # leap year, valid
    "2000年2月29日": "2000-02-29",  # divisible by 400, leap
    "2023年2月29日": "",  # non-leap February
    "1900年2月29日": "",  # divisible by 100 but not 400, not leap
    "2019年2月30日": "",
    "2026年4月31日": "",
    "2018年13月1日": "",
    "2018年00月10日": "",
    "2018年1月32日": "",
    "2018年8月00日": "",
}

IMAGE_CASES = {
    "https://static.wixstatic.com/media/BR234.jpg": "https://static.wixstatic.com/media/BR234.jpg",
    "https://static.wixstatic.com/media/BR-084soldout.jpg": "",
    "https://static.wixstatic.com/media/br084SOLDOUT.png": "",
    "": "",
    "//static.wixstatic.com/media/x.jpg": "https://static.wixstatic.com/media/x.jpg",
    "/media/x.jpg": "https://www.bravo-japan.com/media/x.jpg",
}


def load():
    return yaml.safe_load(BRAVO.read_text(encoding="utf-8"))


def dvd_scene():
    return load()["xPathScrapers"]["dvdSceneScraper"]["scene"]


def run_js(script: str, value: str) -> str:
    """Execute a production postProcess javascript snippet with node."""
    program = f"function __f(value) {{\n{script}\n}}\nconsole.log(__f({json.dumps(value, ensure_ascii=False)}));"
    result = subprocess.run(
        ["node", "-e", program], capture_output=True, text=True, cwd=ROOT
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.rstrip("\n")


def field_js(field: str) -> str:
    steps = dvd_scene()[field]["postProcess"]
    js = [s["javascript"] for s in steps if "javascript" in s]
    assert len(js) == 1, field
    return js[0]


def eval_xpath(html_file: str, selector: str) -> list:
    program = (
        "const fs=require('fs');"
        f"const {{JSDOM}}=require({json.dumps(str(JSDOM))});"
        "const doc=new JSDOM(fs.readFileSync(process.argv[1],'utf-8')).window.document;"
        "const r=doc.evaluate(process.env.SEL,doc,null,"
        "doc.defaultView.XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,null);"
        "const out=[];"
        "for(let i=0;i<r.snapshotLength;i++)out.push(r.snapshotItem(i).nodeValue);"
        "console.log(JSON.stringify(out));"
    )
    env = {**os.environ, "SEL": selector}
    result = subprocess.run(
        ["node", "-e", program, str(FIXTURE_DIR / html_file)],
        capture_output=True, text=True, cwd=ROOT, env=env,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def eval_html(html: str, selector: str) -> list:
    """Evaluate a production selector against raw inline HTML (jsdom).

    Same evaluator as eval_xpath, but the document comes from a string
    so adversarial page shapes can be pinned without new fixture files.
    Returns attribute values for attribute nodes, text for elements.
    """
    program = (
        "const {JSDOM}=require(%s);"
        "const doc=new JSDOM(process.env.HTML,'utf-8').window.document;"
        "const r=doc.evaluate(process.env.SEL,doc,null,"
        "doc.defaultView.XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,null);"
        "const out=[];"
        "for(let i=0;i<r.snapshotLength;i++){const n=r.snapshotItem(i);"
        "out.push(n.nodeValue!==null?n.nodeValue:n.textContent);}"
        "console.log(JSON.stringify(out));"
    ) % json.dumps(str(JSDOM))
    env = {**os.environ, "SEL": selector, "HTML": html}
    result = subprocess.run(
        ["node", "-e", program],
        capture_output=True, text=True, cwd=ROOT, env=env,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_dvd_scraper_field_set_is_exactly_the_authorized_set():
    assert set(dvd_scene()) == {"Title", "Code", "URLs", "Details", "Date", "Image"}


def test_dvd_selectors_match_g1_verified_values():
    scene = dvd_scene()
    for field, selector in VERIFIED_SELECTORS.items():
        assert scene[field]["selector"] == selector, field


def test_dvd_urls_selector_is_gated_on_the_product_marker():
    # R4 hardening: marker + non-blank marker-anchored Title/Code.
    # The two extra predicates close missing-Title, missing-Code and
    # marker-without-structure shapes; they do NOT close Code
    # misalignment or canonical mismatch (see adversarial matrix below).
    selector = dvd_scene()["URLs"]["selector"]
    assert selector == (
        "//link[@rel='canonical'][//h2[contains(.,'品番')]]"
        "[normalize-space(//h2[contains(.,'品番')]/preceding::h2[2])!='']"
        "[normalize-space(//h2[contains(.,'品番')]/following::h2[1])!='']/@href"
    )


def test_dvd_routing_contract():
    data = load()
    assert "sceneByQueryFragment" not in data
    assert "sceneByFragment" not in data
    routes = data["sceneByURL"]
    assert len(routes) == 2
    assert routes[0]["scraper"] == "clipSceneScraper"
    assert routes[1]["scraper"] == "dvdSceneScraper"
    assert routes[1]["url"] == sorted(routes[1]["url"])
    assert all("/dvds/" in p for p in routes[1]["url"])


def test_clip_scraper_is_untouched_by_dvd_work():
    clip = load()["xPathScrapers"]["clipSceneScraper"]["scene"]
    assert clip["Title"]["selector"] == "//h1[1]"
    assert clip["URLs"]["selector"] == "//link[@rel='canonical']/@href"
    assert "Duration" not in clip  # WS-2E-DEF01-DEFER-20261104
    assert "Date" not in clip
    assert "Studio" not in clip


@pytest.mark.parametrize("source,expected", sorted(DATE_CASES.items()))
def test_date_js_normalizes_japanese_dates(source, expected):
    assert run_js(field_js("Date"), source) == expected


@pytest.mark.parametrize("source,expected", sorted(IMAGE_CASES.items()))
def test_image_js_filters_soldout_and_normalizes_urls(source, expected):
    assert run_js(field_js("Image"), source) == expected


# Finetune 2026-11-14: Title composes the two title h2 lines. The JS
# receives the concat-joined raw lines (attribute-level concat runs
# before postProcess) and joins non-blank lines with " - ".
TITLE_JS_CASES = {
    "体育会DASH! 4\nヌル穴大学生": "体育会DASH! 4 - ヌル穴大学生",
    "勃起する白き花よ\nMr.Lily 編": "勃起する白き花よ - Mr.Lily 編",
    "少年集団強姦": "少年集団強姦",
    "少年集団強姦\n": "少年集団強姦",
    "​少年集団強姦\n​": "少年集団強姦",
    "": "",
    "\n": "",
}


@pytest.mark.parametrize("source,expected", sorted(TITLE_JS_CASES.items()))
def test_title_js_composes_main_and_subtitle_lines(source, expected):
    assert run_js(field_js("Title"), source) == expected


def eval_concat_field(html_file: str, field: str) -> str:
    """Run a production concat field (selector + concat + JS) on a fixture.

    Mirrors the documented pipeline: matches in document order, raw
    values trimmed, joined with the field's concat string, then the
    field's javascript postProcess runs once on the joined string.
    """
    mapping = dvd_scene()[field]
    program = (
        "const fs=require('fs');"
        f"const {{JSDOM}}=require({json.dumps(str(JSDOM))});"
        "const doc=new JSDOM(fs.readFileSync(process.argv[1],'utf-8')).window.document;"
        "const r=doc.evaluate(process.env.SEL,doc,null,"
        "doc.defaultView.XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,null);"
        "const parts=[];"
        "for(let i=0;i<r.snapshotLength;i++){const n=r.snapshotItem(i);"
        "parts.push((n.nodeValue!==null?n.nodeValue:n.textContent).trim());}"
        "const value=parts.join(process.env.CONCAT);"
        "const f=new Function('value', process.env.JS);"
        "console.log(f(value));"
    )
    js = [s["javascript"] for s in mapping["postProcess"] if "javascript" in s]
    assert len(js) == 1, field
    env = {**os.environ, "SEL": mapping["selector"], "CONCAT": mapping["concat"], "JS": js[0]}
    result = subprocess.run(
        ["node", "-e", program, str(FIXTURE_DIR / html_file)],
        capture_output=True, text=True, cwd=ROOT, env=env,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.rstrip("\n")


@pytest.mark.parametrize(
    "html,expected",
    [
        # Real-template fixtures (carry the 'BR -' code element and,
        # where present, a subtitle h2) — not the synthetic manifest set.
        ("dvd-281.html", "熊ケツ4 - しゅうた参上！"),
        ("dvd-173.html", "筋肉BANANA - 自分のチンポ型ディルドをハメた台湾BOY!"),
        ("dvd-215.html", "種竿狂"),
        ("dvd-046.html", "ゆるゆる雄太のデブ竿ぽちゃ穴食べ放題!"),
    ],
)
def test_production_title_composition_on_real_template_fixtures(html, expected):
    assert eval_concat_field(html, "Title") == expected


# Finetune 2026-11-14: Code composes the "BR -" prefix element with
# the number element. The JS receives the concat-joined parts in
# document order (number first, prefix second).
CODE_JS_CASES = {
    "198\nBR -": "BR-198",
    "046\nBR -": "BR-046",
    "084\nBR-": "BR-084",
    "046": "046",
    "BR-198": "BR-198",
    "BR - 198": "BR-198",
    "": "",
}


@pytest.mark.parametrize("source,expected", sorted(CODE_JS_CASES.items()))
def test_code_js_composes_prefix_and_number(source, expected):
    assert run_js(field_js("Code"), source) == expected


@pytest.mark.parametrize(
    "html,expected",
    [
        ("dvd-281.html", "BR-281"),
        ("dvd-173.html", "BR-173"),
        ("dvd-215.html", "BR-215"),
        ("dvd-046.html", "BR-046"),
    ],
)
def test_production_code_composition_on_real_template_fixtures(html, expected):
    assert eval_concat_field(html, "Code") == expected


@pytest.mark.parametrize(
    "html,expected",
    [
        ("dvd-synthetic-234.html", ["https://www.bravo-japan.com/dvds/234"]),
        ("dvd-synthetic-084.html", ["https://www.bravo-japan.com/dvds/084"]),
        ("dvd-synthetic-046.html", ["https://www.bravo-japan.com/dvds/046"]),
        ("dvd-synthetic-404-00.html", []),
        ("dvd-synthetic-404-999999.html", []),
    ],
)
def test_production_urls_selector_is_fail_closed_on_404(html, expected):
    assert eval_xpath(html, dvd_scene()["URLs"]["selector"]) == expected


def _adv_page(canonical, h2s):
    """Minimal BRAVO-shaped page: optional canonical + a run of h2s."""
    head = f'<link rel="canonical" href="{canonical}">' if canonical else ""
    body = "".join(f"<h2>{h}</h2>" for h in h2s)
    return f"<!DOCTYPE html><html><head>{head}</head><body>{body}</body></html>"


# WAVE2E-F-PR104-HARDENING-20261104-R4 (A-02, PR104-CROSSQA-P1-1).
# Statuses: VALID = genuine product shape, URLs emitted. SUPPRESSED =
# production YAML yields no URLs (gate closed). RESIDUAL = production YAML
# still emits URLs; the case is PINNED here and classified in
# PRODUCT_IDENTITY_RESIDUAL_RISK — it is NOT silently accepted, and the
# expectation is the actual emitted value, not a wished-for [].
ADVERSARIAL_IDENTITY_CASES = [
    # Valid product shape: full template run (nav pair + Title +
    # subtitle + marker + Code + date label + date). Title selector
    # preceding::h2[2] needs two h2s before the marker pair position.
    ("valid-product",
     _adv_page("https://www.bravo-japan.com/dvds/234",
               ["BRAVO-JAPAN", "GO to BRAVO-CLIPS", "勃起する白き花よ",
                "Mr.Lily 編", "品番", "234", "発売日", "2018年8月29日"]),
     ["https://www.bravo-japan.com/dvds/234"], "VALID"),
    # Canonical only, no marker at all (404 shape).
    ("canonical-only-404",
     _adv_page("https://www.bravo-japan.com/dvds/555", []),
     [], "SUPPRESSED"),
    # Stray marker with no Code h2 after it (Cross-QA A fake-marker-777).
    ("fake-marker-no-code",
     _adv_page("https://www.bravo-japan.com/dvds/777",
               ["BRAVO-JAPAN", "GO to BRAVO-CLIPS", "品番"]),
     [], "SUPPRESSED"),
    # Marker present but no Title h2 pair before it.
    ("missing-title",
     _adv_page("https://www.bravo-japan.com/dvds/501", ["品番", "501"]),
     [], "SUPPRESSED"),
    # Title pair present, but no Code h2 after the marker at all.
    ("missing-code",
     _adv_page("https://www.bravo-japan.com/dvds/500",
               ["BRAVO-JAPAN", "GO to BRAVO-CLIPS", "Real Title",
                "sub", "品番"]),
     [], "SUPPRESSED"),
    # Code h2 exists but is the wrong node: the label h2 is picked up
    # as Code (Cross-QA A code-missing shape). Non-blank check cannot
    # tell a label from a code.
    ("code-misaligned-as-label",
     _adv_page("https://www.bravo-japan.com/dvds/234",
               ["BRAVO-JAPAN", "GO to BRAVO-CLIPS", "勃起する白き花よ",
                "Mr.Lily 編", "品番", "発売日", "2018年8月29日"]),
     ["https://www.bravo-japan.com/dvds/234"], "RESIDUAL"),
    # Full product structure, but the canonical points elsewhere.
    ("canonical-mismatch",
     _adv_page("https://www.bravo-japan.com/dvds/999",
               ["BRAVO-JAPAN", "GO to BRAVO-CLIPS", "勃起する白き花よ",
                "Mr.Lily 編", "品番", "234", "発売日", "2018年8月29日"]),
     ["https://www.bravo-japan.com/dvds/999"], "RESIDUAL"),
    # Stray marker embedded between unrelated h2s: Title and Code
    # checks both pass on unrelated text. Structural genuineness is
    # not expressible in pure XPath without template constraints.
    ("marker-outside-product-structure",
     _adv_page("https://www.bravo-japan.com/dvds/888",
               ["BRAVO-JAPAN", "GO to BRAVO-CLIPS", "品番",
                "サイト案内", "お問い合わせ"]),
     ["https://www.bravo-japan.com/dvds/888"], "RESIDUAL"),
    # Incomplete hydration: canonical present, no product h2s at all.
    ("incomplete-hydration",
     _adv_page("https://www.bravo-japan.com/dvds/234", []),
     [], "SUPPRESSED"),
    # Challenge page: no canonical, no marker.
    ("challenge-page",
     _adv_page(None, []),
     [], "SUPPRESSED"),
]


@pytest.mark.parametrize(
    "case,html,expected,status",
    [(c, h, e, s) for c, h, e, s in ADVERSARIAL_IDENTITY_CASES],
    ids=[c for c, _, _, _ in ADVERSARIAL_IDENTITY_CASES],
)
def test_production_urls_selector_adversarial_identity_matrix(
    case, html, expected, status
):
    selector = dvd_scene()["URLs"]["selector"]
    assert eval_html(html, selector) == expected, case
    # RESIDUAL expectations are the actual emitted values: the test
    # pins the hole for Controller/Gate B, it does not hide it.
    assert status in ("VALID", "SUPPRESSED", "RESIDUAL"), case
