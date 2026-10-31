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


def test_clip_image_excludes_placeholder_gif():
    data = load()
    selector = data["xPathScrapers"]["clipSceneScraper"]["scene"]["Image"]["selector"]
    assert ".gif" in selector
    assert "not(" in selector
