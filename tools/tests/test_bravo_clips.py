"""Wave 1B (STASH-E2E-03 / BRAVO part of STASH-E2E-04) structural regression.

These assertions are about the YAML routing itself, not about a live Stash
run: with no ``sceneByFragment`` declaration, Stash has no direct-fragment
route that could expand an empty ``{title}`` into ``clips/%7Btitle%7D``.
Gate B (independent QA on stash-test) remains the live check and is NOT_RUN
until it is actually performed.
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
    assert not any("dvd" in n.lower() for n in names)


def test_title_less_limitation_is_documented():
    # Declarative XPath cannot suppress Code/Duration/URLs when Title is
    # empty; that limitation must be recorded, not hidden, for Gate B.
    text = BRAVO.read_text()
    assert "Title-less" in text or "Title-less limitation" in text
    assert "must NOT be accepted as a successful scrape" in text
