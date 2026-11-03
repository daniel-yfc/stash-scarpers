"""Wave 2E WS-2E-40 - BRAVO DVD fixture engineering regression (Agent C, v2.2).

Evidence basis
--------------
Agent A RAW-DOM-VERIFICATION-ADDENDUM.md (WAVE2E-A-DVD-DOM-20261102):
9 CDP-verified product pages (046/234/084/281/377/383/384/304/315) with
cardinality=1 for Title/Code/URLs/Details/Image/Date/Studio/Duration, plus
2 verified 404 pages (/dvds/00, /dvds/999999). The current DOM has NO h1
and no historical Wix comp IDs; product data exists only after CDP
rendering (driver.useCDP is required).

What these tests enforce
------------------------
* Green here and now: manifest structure, Agent A verified-value matrix,
  404 fail-closed behaviour, isolation from the archived historical
  manifest and the Wave 1B Clips manifest (case names AND html filenames),
  historical digest preservation, and mutation tests proving the shared
  fixture runner rejects wrong expectations.
* Deliberately red on the scaffold branch (and asserted as such): running
  the full DVD manifest must fail with "Ambiguous entrypoint; specify
  scraper for sceneByURL" until Agent F implements the /dvds/ route and
  dvdSceneScraper. When implemented, the same test requires a full PASS.
* Conditional guards (active once dvdSceneScraper exists): no stale //h1
  or comp-kbfkf16x selectors, no site-generic keywords as Tags.

Revision history
----------------
* v2.1 (C-FIX-1/2/3): DVD case names renamed so none collide with the
  archived historical manifest; the failure control was renamed
  "BRAVO dvd Cloudflare challenge (dvd manifest control)"; isolation test
  asserts html-filename isolation; stale-h1 test guards the failure case
  via case.get("expect", []); report HEAD_SHA is a real commit SHA.
* v2.2 (C-FIX-1 follow-up): the failure control previously SHARED the
  archived real capture failure-cloudflare.html with the historical and
  Clips manifests, which still violated html-filename isolation. It now
  uses a DVD-owned synthetic model, dvd-synthetic-cloudflare-challenge.html
  (SYNTHETIC_REGRESSION). Every fixture referenced by the DVD manifest is
  DVD-owned and synthetic-marked; the archived file is not modified and
  remains referenced only by the historical and Clips manifests.

These tests do NOT claim live/runtime verification (Gate B) and do not
modify the shared runner, scrapers/BRAVO.yml, tools/tests/test_bravo_clips.py
or the archived historical manifest.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
BRAVO = ROOT / "scrapers" / "BRAVO.yml"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "bravo"
DVD_MANIFEST = FIXTURE_DIR / "bravo-dvds-fixtures.yml"
HISTORICAL_MANIFEST = FIXTURE_DIR / "bravo-fixtures.yml"
CLIPS_MANIFEST = FIXTURE_DIR / "bravo-clips-fixtures.yml"
HARNESS_HTML = FIXTURE_DIR / "dvd-mutation-harness.html"
EVIDENCE_STATUS = ROOT / "docs" / "archive" / "evidence" / "status" / "bravo.yml"
RUNNER = ["node", "tools/verify-scraper-fixtures.mjs"]
HISTORICAL_DIGEST = (
    "be1885d2097683e8c4ae5f2440120e8bd7945ac16f62c1910ac87e5d009d39b2"
)
# The archived real capture stays shared by the historical and Clips
# manifests; the DVD manifest must NEVER reference it (v2.2).
SHARED_ARCHIVED_FAILURE_HTML = "failure-cloudflare.html"
WAVE_1B_CLIPS_CASE_NAMES = {
    "BRAVO clip 284",
    "BRAVO clip 282",
    "BRAVO clip missing title",
    "BRAVO clip no verified cover",
    "BRAVO clip 284 with extra headings",
    "BRAVO Cloudflare challenge",
}
FAILURE_MARKERS = (
    "cf-challenge", "Just a moment", "Attention Required",
    "Application error", "404 Not Found",
)

# Agent A verified matrix (RAW-DOM-VERIFICATION-ADDENDUM.md section 2).
# Duration is the full-feature total in minutes, converted to seconds.
AGENT_A_VERIFIED = {
    "234": {"title": "勃起する白き花よ", "code": "234", "studio": "GAYSIAN",
             "duration_seconds": "6600", "date": "2018年8月29日"},
    "084": {"title": "少年集団強姦", "code": "084", "studio": "Lucifer",
             "duration_seconds": "8400", "date": "2012年11月17日"},
    "281": {"title": "熊ケツ4", "code": "281", "studio": "ooooPS!!",
             "duration_seconds": "7200", "date": "2020年7月31日"},
    "046": {"title": "ゆるゆる雄太のデブ竿ぽちゃ穴食べ放題!", "code": "046",
             "studio": "ooooPS!!", "duration_seconds": "15600",
             "date": "2010年09月30日"},
    "377": {"title": "騒乱みだれ穴５", "code": "377", "studio": "BRAVO!",
             "duration_seconds": "6600", "date": "2026年5月31日"},
    "384": {"title": "ナマ狂い種壺待機５", "code": "384", "studio": "BRAVO-RAW",
             "duration_seconds": "6000", "date": "2026年10月22日"},
}
POSITIVE_CODES = ("234", "084", "281", "046", "377", "384")
NOT_FOUND_CODES = ("00", "999999")


def load_manifest(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dvd_cases() -> list[dict]:
    return load_manifest(DVD_MANIFEST)["cases"]


def case_by_html(html: str) -> dict:
    return next(c for c in dvd_cases() if c["html"] == html)


def mapped(case: dict, field: str) -> dict:
    return next(a for a in case["mappedExpect"] if a["field"] == field)


def run_runner(manifest_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [*RUNNER, str(manifest_path)], cwd=ROOT, text=True,
        capture_output=True, check=False,
    )


def dvd_scraper(data: dict | None = None) -> dict | None:
    data = data if data is not None else yaml.safe_load(BRAVO.read_text(encoding="utf-8"))
    return (data.get("xPathScrapers") or {}).get("dvdSceneScraper")


# --------------------------------------------------------------------------
# C-01 - fixture architecture and manifest structure
# --------------------------------------------------------------------------

def test_dvd_manifest_exists_with_scraper_key():
    assert DVD_MANIFEST.is_file()
    manifest = load_manifest(DVD_MANIFEST)
    assert manifest["scraper"] == "scrapers/BRAVO.yml"


def test_dvd_manifest_case_inventory():
    cases = dvd_cases()
    names = [c["name"] for c in cases]
    assert len(names) == len(set(names))
    assert len(cases) == 10
    assert sum(c["classification"] == "completed" for c in cases) == 9
    assert sum(c["classification"] == "failure" for c in cases) >= 1
    assert any(c.get("optionalField") for c in cases)
    for case in cases:
        assert isinstance(case["html"], str)
        assert (FIXTURE_DIR / case["html"]).is_file(), case["html"]


def test_positive_cases_cover_agent_a_matrix():
    cases = {c["html"]: c for c in dvd_cases()}
    for code in POSITIVE_CODES:
        case = cases[f"dvd-synthetic-{code}.html"]
        expected = AGENT_A_VERIFIED[code]
        assert mapped(case, "Title")["values"] == [expected["title"]]
        assert mapped(case, "Code")["values"] == [expected["code"]]
        assert mapped(case, "URLs")["values"] == [
            f"https://www.bravo-japan.com/dvds/{code}"
        ]
        assert mapped(case, "Duration")["values"] == [expected["duration_seconds"]]
        assert mapped(case, "Studio")["values"] == [expected["studio"]]
        # C-04 cardinality: every verified field is pinned to exactly 1 hit.
        for field, xpath in (
            ("Title", "//h2[contains(.,'品番')]/preceding::h2[2]"),
            ("Code", "//h2[contains(.,'品番')]/following::h2[1]"),
            ("Date", "//h2[contains(.,'発売日')]/following::h2[1]"),
            ("Studio", "//h2[contains(.,'レーベル')]/preceding::h2[1]"),
            ("Duration", "//h2[contains(.,'収録時間')]/following::h2[1]"),
        ):
            assertion = next(a for a in case["expect"] if a["xpath"] == xpath)
            assert assertion["min"] == 1 and assertion["max"] == 1, (code, field)
        date_assertion = next(
            a for a in case["expect"] if "発売日" in a["xpath"]
        )
        assert date_assertion["values"] == [expected["date"]]


def test_046_leading_zero_is_preserved():
    case = case_by_html("dvd-synthetic-046.html")
    assert mapped(case, "Code")["values"] == ["046"]
    code_assertion = next(
        a for a in case["expect"] if "following::h2[1]" in a["xpath"]
    )
    assert code_assertion["values"] == ["046"]
    assert isinstance(code_assertion["values"][0], str)
    assert len(code_assertion["values"][0]) == 3


# --------------------------------------------------------------------------
# C-05 - 084 empty Details must stay empty
# --------------------------------------------------------------------------

def test_084_details_stay_empty():
    case = case_by_html("dvd-synthetic-084.html")
    assert mapped(case, "Details")["values"] == [""]
    fixture = (FIXTURE_DIR / "dvd-synthetic-084.html").read_text(encoding="utf-8")
    # The p.font_8 slot exists but carries no default/placeholder content.
    match = re.search(r'<p class="font_8">([^<]*)</p>', fixture)
    assert match is not None
    assert match.group(1) == ""


# --------------------------------------------------------------------------
# C-06 - 084 soldout image is an explicit decision, never silent
# --------------------------------------------------------------------------

def test_084_soldout_image_is_flagged():
    case = case_by_html("dvd-synthetic-084.html")
    fixture = (FIXTURE_DIR / "dvd-synthetic-084.html").read_text(encoding="utf-8")
    assert "soldout" in fixture
    image_assertion = next(
        a for a in case["expect"] if "wixstatic" in a["xpath"]
    )
    # The soldout cover exists on the page (cardinality 1)...
    assert image_assertion["min"] == 1 and image_assertion["max"] == 1
    # ...but Image is not silently blessed as scene metadata: either it is
    # not mapped at all, or the production YAML documents the decision.
    bravo_text = BRAVO.read_text(encoding="utf-8")
    if any(a["field"] == "Image" for a in case["mappedExpect"]):
        assert "soldout" in bravo_text


# --------------------------------------------------------------------------
# C-07 - site-generic keywords must not become product Tags
# --------------------------------------------------------------------------

def test_site_generic_keywords_are_not_product_tags():
    # The keywords meta exists on every fixture (including 404 pages) as a
    # standing trap; no DVD case may map it into Tags.
    for case in dvd_cases():
        assert not any(
            a["field"].startswith("Tags") for a in case.get("mappedExpect", [])
        ), case["name"]
    data = yaml.safe_load(BRAVO.read_text(encoding="utf-8"))
    dvd = dvd_scraper(data)
    if dvd is None:
        return  # enforced again once Agent F implements dvdSceneScraper
    tags = (dvd.get("scene") or {}).get("Tags")
    if tags is None:
        return
    selector = tags.get("Name", {}).get("selector", "") if isinstance(tags, dict) else str(tags)
    assert "keywords" not in selector


# --------------------------------------------------------------------------
# C-08 - CDP dependency is recorded and preserved
# --------------------------------------------------------------------------

def test_cdp_driver_requirement_is_preserved():
    data = yaml.safe_load(BRAVO.read_text(encoding="utf-8"))
    assert data["driver"]["useCDP"] is True


# --------------------------------------------------------------------------
# C-03 - 404 negative pages fail closed
# --------------------------------------------------------------------------

def test_404_pages_fail_closed():
    for code in NOT_FOUND_CODES:
        case = case_by_html(f"dvd-synthetic-404-{code}.html")
        assert case["classification"] == "completed"
        for field in ("Title", "Code", "Details", "Image"):
            assert mapped(case, field)["values"] == [], (code, field)
        # canonical exists but points at the 404 URL: it never proves a
        # valid product page; the 品番 gate is the validity signal.
        canonical = next(a for a in case["expect"] if "canonical" in a["xpath"])
        assert canonical["values"] == [f"https://www.bravo-japan.com/dvds/{code}"]
        hinban = next(a for a in case["expect"] if "品番" in a["xpath"])
        assert hinban["min"] == 0 and hinban["max"] == 0


def test_logo_with_empty_alt_is_not_an_image():
    case = case_by_html("dvd-synthetic-logo-empty-alt.html")
    assert mapped(case, "Image")["values"] == []
    fixture = (FIXTURE_DIR / "dvd-synthetic-logo-empty-alt.html").read_text(encoding="utf-8")
    assert 'alt=""' in fixture and "wixstatic" in fixture


# --------------------------------------------------------------------------
# Evidence contract preservation and isolation
# --------------------------------------------------------------------------

def test_historical_fixture_manifest_digest_unchanged():
    digest = hashlib.sha256(HISTORICAL_MANIFEST.read_bytes()).hexdigest()
    assert digest == HISTORICAL_DIGEST
    historical = load_manifest(HISTORICAL_MANIFEST)
    assert [c["name"] for c in historical["cases"]] == [
        "BRAVO dvd 281",
        "BRAVO dvd 046",
        "BRAVO Cloudflare challenge",
    ]
    evidence = load_manifest(EVIDENCE_STATUS)
    fixture = evidence["states"]["fixture"]
    assert fixture["artifact"] == "tests/fixtures/bravo/bravo-fixtures.yml"
    assert fixture["sha256"] == digest
    assert fixture["captured_at"] == "2026-10-14T19:09:10+08:00"


def test_dvd_manifest_is_isolated_from_historical_and_clips():
    dvd_names = {c["name"] for c in dvd_cases()}
    historical_names = {c["name"] for c in load_manifest(HISTORICAL_MANIFEST)["cases"]}
    clips_names = {c["name"] for c in load_manifest(CLIPS_MANIFEST)["cases"]}
    # C-FIX-1: neither case names nor fixture html filenames may collide.
    assert not (dvd_names & historical_names), dvd_names & historical_names
    assert not (dvd_names & clips_names), dvd_names & clips_names
    dvd_htmls = {c["html"] for c in dvd_cases()}
    historical_htmls = {c["html"] for c in load_manifest(HISTORICAL_MANIFEST)["cases"]}
    clips_htmls = {c["html"] for c in load_manifest(CLIPS_MANIFEST)["cases"]}
    assert not (dvd_htmls & historical_htmls), dvd_htmls & historical_htmls
    assert not (dvd_htmls & clips_htmls), dvd_htmls & clips_htmls
    assert WAVE_1B_CLIPS_CASE_NAMES <= clips_names
    for case in dvd_cases():
        assert not case["html"].startswith("clip-"), case["name"]


def test_failure_case_uses_dvd_owned_synthetic_fixture():
    # v2.2: the DVD failure control must own its fixture. The archived real
    # capture stays referenced only by the historical and Clips manifests.
    failures = [c for c in dvd_cases() if c["classification"] == "failure"]
    assert len(failures) == 1
    case = failures[0]
    assert case["name"] == "BRAVO dvd Cloudflare challenge (dvd manifest control)"
    assert case["html"] != SHARED_ARCHIVED_FAILURE_HTML
    assert case["html"].startswith("dvd-synthetic-")
    fixture = FIXTURE_DIR / case["html"]
    assert fixture.is_file()
    content = fixture.read_text(encoding="utf-8")
    assert "SYNTHETIC_REGRESSION" in content
    # The synthetic model carries a failure marker and no product content,
    # so a scraper must fail (no product metadata) on it.
    assert any(marker in content for marker in ("cf-challenge", "Just a moment"))
    assert "品番" not in content


def test_dvd_manifest_does_not_reuse_stale_h1_selectors():
    # The current DOM has h1 = 0 on all verified pages; the historical
    # h1/comp-ID selectors are obsolete and must not reappear here.
    # C-FIX-2: the failure control case has no expect block - guard it.
    for case in dvd_cases():
        for assertion in case.get("expect", []):
            assert "//h1" not in assertion["xpath"], case["name"]
            assert "comp-kbfkf16x" not in assertion["xpath"], case["name"]


def test_synthetic_fixtures_are_marked():
    # v2.2: EVERY fixture referenced by the DVD manifest is DVD-owned and
    # must carry the SYNTHETIC_REGRESSION marker - no exceptions, no shared
    # archived captures.
    for case in dvd_cases():
        assert case["html"].startswith("dvd-synthetic-"), case["name"]
        content = (FIXTURE_DIR / case["html"]).read_text(encoding="utf-8")
        assert "SYNTHETIC_REGRESSION" in content, case["html"]
    harness = HARNESS_HTML.read_text(encoding="utf-8")
    assert "SYNTHETIC_REGRESSION" in harness
    assert "MUTATION_HARNESS_ONLY" in harness


def test_label_h2s_carry_zero_width_space_hazard():
    # Agent A: label h2 text contains U+200B (e.g. "\u200b品番"); selectors
    # must use contains(), never exact matching, and postProcess must strip
    # U+200B from extracted values.
    fixture = (FIXTURE_DIR / "dvd-synthetic-046.html").read_text(encoding="utf-8")
    assert "\u200b品番" in fixture


def test_completed_pages_do_not_contain_failure_markers():
    for case in dvd_cases():
        if case["classification"] != "completed":
            continue
        content = (FIXTURE_DIR / case["html"]).read_text(encoding="utf-8")
        for marker in FAILURE_MARKERS:
            assert marker not in content, (case["name"], marker)


# --------------------------------------------------------------------------
# C-07 - execution state: expected red until dvdSceneScraper exists
# --------------------------------------------------------------------------

def dvd_route_implemented() -> bool:
    data = yaml.safe_load(BRAVO.read_text(encoding="utf-8"))
    routes = data.get("sceneByURL") or []
    named = any(
        isinstance(route, dict) and route.get("scraper") == "dvdSceneScraper"
        for route in routes
    )
    return named and dvd_scraper(data) is not None


def test_dvd_manifest_execution_state():
    result = run_runner(DVD_MANIFEST)
    if not dvd_route_implemented():
        assert result.returncode != 0, result.stdout
        assert "Ambiguous entrypoint" in result.stderr, result.stderr
    else:
        assert result.returncode == 0, result.stderr
        assert "cases verified" in result.stdout, result.stdout


# --------------------------------------------------------------------------
# C-06 - test the tests: controlled mutations must be rejected
# --------------------------------------------------------------------------

def harness_manifest() -> dict:
    return {
        "scraper": "scrapers/BRAVO.yml",
        "cases": [
            {
                "name": "BRAVO dvd mutation harness (synthetic)",
                "classification": "completed",
                "html": "dvd-mutation-harness.html",
                "locale": {"lang": "ja", "text": "046"},
                "mappedExpect": [
                    {"field": "Title", "scraper": "clipSceneScraper",
                     "values": ["046"]},
                    {"field": "Code", "scraper": "clipSceneScraper",
                     "values": ["046"]},
                    {"field": "Duration", "scraper": "clipSceneScraper",
                     "values": ["1800"]},
                    {"field": "Details", "scraper": "clipSceneScraper",
                     "values": ["ミューテーション用の説明文です。"]},
                    {"field": "Image", "scraper": "clipSceneScraper",
                     "values": ["https://example.invalid/dvd-046-harness-poster.jpg"]},
                ],
                "expect": [
                    {"xpath": "//h1", "min": 1, "max": 1, "values": ["046"]},
                    {"xpath": "//link[@rel='canonical']/@href", "min": 1, "max": 1,
                     "values": ["https://www.bravo-japan.com/dvds/046"]},
                ],
                "optionalField": {
                    "xpath": "//h2[normalize-space()='品番']", "expectedCount": 0,
                },
            },
            {
                # Staged manifest (not the DVD manifest): the archived real
                # capture is reused here only as a generic failure input for
                # mutation staging, mirroring the Clips manifest. Isolation
                # rules apply to the DVD manifest itself, not to this
                # tmp-staged runner input.
                "name": "BRAVO Cloudflare challenge",
                "classification": "failure",
                "html": "failure-cloudflare.html",
            },
        ],
    }


def stage(tmp_path: Path, manifest: dict, html_names: list[str]) -> Path:
    for name in html_names:
        shutil.copy(FIXTURE_DIR / name, tmp_path / name)
    target = tmp_path / "staged-fixtures.yml"
    target.write_text(
        yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return target


def test_mutation_harness_control_passes(tmp_path):
    target = stage(
        tmp_path, harness_manifest(),
        ["dvd-mutation-harness.html", "failure-cloudflare.html"],
    )
    result = run_runner(target)
    assert result.returncode == 0, result.stderr
    assert "2 cases verified" in result.stdout, result.stdout


def test_mutation_leading_zero_code_drop_is_rejected(tmp_path):
    manifest = harness_manifest()
    manifest["cases"][0]["mappedExpect"][1]["values"] = ["46"]
    result = run_runner(stage(tmp_path, manifest, ["dvd-mutation-harness.html", "failure-cloudflare.html"]))
    assert result.returncode != 0
    assert "Code" in result.stderr and '"46"' in result.stderr and '"046"' in result.stderr


def test_mutation_logo_as_image_is_rejected(tmp_path):
    manifest = harness_manifest()
    manifest["cases"][0]["mappedExpect"][4]["values"] = [
        "https://example.invalid/site-logo.gif"
    ]
    result = run_runner(stage(tmp_path, manifest, ["dvd-mutation-harness.html", "failure-cloudflare.html"]))
    assert result.returncode != 0
    assert "Image" in result.stderr and "site-logo" in result.stderr


def test_mutation_expected_empty_but_value_present_is_rejected(tmp_path):
    manifest = harness_manifest()
    manifest["cases"][0]["mappedExpect"][0]["values"] = []
    result = run_runner(stage(tmp_path, manifest, ["dvd-mutation-harness.html", "failure-cloudflare.html"]))
    assert result.returncode != 0
    assert "Title" in result.stderr and '"046"' in result.stderr


def test_mutation_cross_family_url_is_rejected_by_route_through(tmp_path):
    manifest = harness_manifest()
    manifest["cases"][0]["mappedExpect"].append(
        {"field": "URLs", "scraper": "clipSceneScraper",
         "routeThrough": "sceneByURL",
         "values": ["https://www.bravo-japan.com/dvds/046"]}
    )
    result = run_runner(stage(tmp_path, manifest, ["dvd-mutation-harness.html", "failure-cloudflare.html"]))
    assert result.returncode != 0
    assert "does not match sceneByURL" in result.stderr
