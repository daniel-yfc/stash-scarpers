"""Wave 1B (STASH-E2E-03 / BRAVO part of STASH-E2E-04) structural regression.

These assertions are about the YAML routing itself, not about a live Stash
run: with no ``sceneByFragment`` declaration, Stash has no direct-fragment
route that could expand an empty ``{title}`` into ``clips/%7Btitle%7D``.
Gate B (independent QA on stash-test) remains the live check and is NOT_RUN
until it is actually performed.

Corrective fix 2026-11-03 (Gate B DEF-01/02): Duration and Details
assertions check selector *properties* (label, spacer guard, container
scope, digit guard, Clip anchor), not an exact XPath string, so a
reasonable selector revision is not blocked by a hardcoded string test.
The exact corrected selectors are verified end-to-end by the fixture
manifest (mappedExpect) instead.
"""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
BRAVO = ROOT / "scrapers" / "BRAVO.yml"


def load():
    return yaml.safe_load(BRAVO.read_text())


def test_clips_route_uses_clip_scraper_only():
    data = load()
    routes = data["sceneByURL"]
    assert len(routes) == 1
    assert routes[0]["scraper"] == "clipSceneScraper"
    patterns = routes[0]["url"]
    assert patterns == sorted(patterns)
    assert all("/clips/" in p for p in patterns)
    assert not any("/dvds/" in p for p in patterns)
    assert "clipSceneScraper" in data["xPathScrapers"]


def test_no_direct_scene_by_fragment():
    data = load()
    assert "sceneByFragment" not in data


def test_query_fragment_preserves_url():
    data = load()
    qf = data["sceneByQueryFragment"]
    assert qf["queryURL"] == "{url}"
    assert qf["scraper"] == "clipSceneScraper"


def test_clip_selectors_are_not_dvd_selectors():
    data = load()
    clip = data["xPathScrapers"]["clipSceneScraper"]["scene"]
    for field in ("Title", "Code", "Duration", "Details"):
        selector = clip[field]["selector"]
        assert "品番" not in selector, field
    assert clip["Title"]["selector"] == "//h1[1]"
    assert "Clip" in clip["Code"]["selector"]
    assert "作品TIME" in clip["Duration"]["selector"]
    # No Date/Studio: the Clips source provides neither, so the fields must
    # stay absent rather than being fabricated.
    assert "Date" not in clip
    assert "Studio" not in clip


def test_duration_selector_is_spacer_and_label_proof():
    # DEF-01: the old exact-equality + immediate-adjacency selector
    # ("//h2[normalize-space()='作品TIME']/preceding::h2[1]") must not
    # return. The corrected selector must: match the label even with a
    # leading U+200B, skip empty/U+200B candidates, require a digit
    # start (so a currency price is not taken), and anchor the candidate
    # after the "Clip" label (so the filtered set is a singleton and the
    # result does not depend on reverse-axis ordering semantics).
    # The literal U+200B character must be present by codepoint, not
    # merely claimed in a comment.
    data = load()
    selector = data["xPathScrapers"]["clipSceneScraper"]["scene"]["Duration"]["selector"]
    assert selector != "//h2[normalize-space()='作品TIME']/preceding::h2[1]"
    assert "作品TIME" in selector
    assert "translate" in selector
    assert "\u200b" in selector
    assert "0123456789" in selector
    assert "Clip" in selector
    assert "preceding::h2" in selector


def test_details_selector_is_container_scoped_rich_text():
    # DEF-02: Details must come from the product description container,
    # not from the first h2 after the h1 (spacer) and not from a global
    # rich-text span (nav/promo). $desc must be the baseline container.
    data = load()
    scraper = data["xPathScrapers"]["clipSceneScraper"]
    assert scraper["common"]["$desc"] == "//div[@id='comp-kbfkf17h']"
    selector = scraper["scene"]["Details"]["selector"]
    assert selector.startswith("$desc")
    assert not selector.startswith("//span")
    assert "wixui-rich-text__text" in selector
    assert "translate" in selector
    assert "\u200b" in selector
    assert selector != "//h1[1]/following::h2[1]"
    # Post-processing must strip U+200B at the edges; a plain \s trim
    # cannot, so the JS form (with a \u200b escape) is required.
    steps = scraper["scene"]["Details"]["postProcess"]
    js = " ".join(str(s.get("javascript", "")) for s in steps if isinstance(s, dict))
    assert "200b" in js


def test_clip_image_is_poster_only():
    # Stabilization: no <img> fallback at all. The previous union was
    # document-order dependent and could return unrelated Wix artwork;
    # poster-only is fail-closed (no poster attribute -> no Image).
    # Live poster value is SOURCE_IMAGE_UNVERIFIED, pending Gate B.
    data = load()
    selector = data["xPathScrapers"]["clipSceneScraper"]["scene"]["Image"]["selector"]
    assert selector == "//video/@poster"
    assert "img" not in selector
    text = BRAVO.read_text()
    assert "SOURCE_IMAGE_UNVERIFIED" in text


def test_historical_fixture_manifest_preserved():
    # The archived evidence record pins this file by digest; Wave 1B must
    # not edit it. Clips cases live in bravo-clips-fixtures.yml instead.
    import hashlib

    import yaml as yaml_lib

    historical = ROOT / "tests" / "fixtures" / "bravo" / "bravo-fixtures.yml"
    digest = hashlib.sha256(historical.read_bytes()).hexdigest()
    assert digest == "be1885d2097683e8c4ae5f2440120e8bd7945ac16f62c1910ac87e5d009d39b2"
    manifest = yaml_lib.safe_load(historical.read_text())
    assert "scraper" not in manifest
    names = [c["name"] for c in manifest["cases"]]
    assert names == [
        "BRAVO dvd 281",
        "BRAVO dvd 046",
        "BRAVO Cloudflare challenge",
    ]
    evidence = yaml_lib.safe_load(
        (ROOT / "docs" / "archive" / "evidence" / "status" / "bravo.yml").read_text()
    )
    fixture = evidence["states"]["fixture"]
    assert fixture["artifact"] == "tests/fixtures/bravo/bravo-fixtures.yml"
    assert fixture["sha256"] == digest
    assert fixture["captured_at"] == "2026-10-14T19:09:10+08:00"


def test_clips_manifest_is_isolated():
    import yaml as yaml_lib

    manifest = yaml_lib.safe_load(
        (ROOT / "tests" / "fixtures" / "bravo" / "bravo-clips-fixtures.yml").read_text()
    )
    assert manifest["scraper"] == "scrapers/BRAVO.yml"
    names = [c["name"] for c in manifest["cases"]]
    assert "BRAVO clip 284" in names
    assert "BRAVO clip 282" in names
    assert "BRAVO clip missing title" in names
    assert "BRAVO clip no verified cover" in names
    assert "BRAVO clip 284 with extra headings" in names
    assert "BRAVO clip rich-text mixed" in names
    assert "BRAVO clip duration with price heading" in names
    assert not any("dvd" in n.lower() for n in names)


def test_manifest_descriptions_are_distinct_and_clean():
    # DEF-02 anti-contamination: 284 and 282 descriptions must differ,
    # so returning one page's description for the other fails. No
    # expected description may contain a zero-width space or be empty
    # for a completed clip page, and the missing-title case must not
    # invent a description.
    import yaml as yaml_lib

    manifest = yaml_lib.safe_load(
        (ROOT / "tests" / "fixtures" / "bravo" / "bravo-clips-fixtures.yml").read_text()
    )
    by_name = {c["name"]: c for c in manifest["cases"]}
    details = {}
    for name in ("BRAVO clip 284", "BRAVO clip 282"):
        mapped = {m["field"]: m["values"] for m in by_name[name]["mappedExpect"]}
        values = mapped["Details"]
        assert len(values) == 1 and values[0]
        assert "\u200b" not in values[0]
        details[name] = values[0]
    assert details["BRAVO clip 284"] != details["BRAVO clip 282"]
    mapped_missing = {
        m["field"]: m["values"] for m in by_name["BRAVO clip missing title"]["mappedExpect"]
    }
    assert mapped_missing["Details"] == []
    # The price-heading case proves the conversion is not hardcoded to
    # 1800: 45 minutes must map to 2700 seconds.
    mapped_price = {
        m["field"]: m["values"]
        for m in by_name["BRAVO clip duration with price heading"]["mappedExpect"]
    }
    assert mapped_price["Duration"] == ["2700"]


def test_title_less_limitation_is_documented():
    # Declarative XPath cannot suppress Code/Duration/URLs when Title is
    # empty; that limitation must be recorded, not hidden, for Gate B.
    text = BRAVO.read_text()
    assert "Title-less" in text or "Title-less limitation" in text
    assert "must NOT be accepted as a successful scrape" in text
