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
BRAVO = ROOT / "scrapers" / "BRAVO.yml"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "bravo"
JSDOM = ROOT / "node_modules" / "jsdom"

VERIFIED_SELECTORS = {
    "Title": "//h2[contains(.,'品番')]/preceding::h2[2]",
    "Code": "//h2[contains(.,'品番')]/following::h2[1]",
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


def test_dvd_scraper_field_set_is_exactly_the_authorized_set():
    assert set(dvd_scene()) == {"Title", "Code", "URLs", "Details", "Date", "Image"}


def test_dvd_selectors_match_g1_verified_values():
    scene = dvd_scene()
    for field, selector in VERIFIED_SELECTORS.items():
        assert scene[field]["selector"] == selector, field


def test_dvd_urls_selector_is_gated_on_the_product_marker():
    selector = dvd_scene()["URLs"]["selector"]
    assert selector == "//link[@rel='canonical'][//h2[contains(.,'品番')]]/@href"


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
