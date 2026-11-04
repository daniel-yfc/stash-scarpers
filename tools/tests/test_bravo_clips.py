"""Wave 1B (STASH-E2E-03 / BRAVO part of STASH-E2E-04) structural regression.

These assertions are about the YAML routing itself, not about a live Stash
run: with no ``sceneByFragment`` declaration, Stash has no direct-fragment
route that could expand an empty ``{title}`` into ``clips/%7Btitle%7D``.
Gate B (independent QA on stash-test) remains the live check and is NOT_RUN
until it is actually performed.

Duration omission 2026-11-04 (Controller decision
WS-2E-DEF01-DEFER-20261104, R3 H4): production Scene.Duration is
REMOVED from BRAVO.yml because the Stash mapped runtime cannot
return a typed int for scene Duration (R3 end-to-end reproduction:
every mapped value is a string, IntPtr accepts only int). Duration
assertions in this file are therefore source-only: they evaluate
the deferred selector from docs/qa/PR93-DURATION-DEFERRED-SPEC.md
against the fixture HTMLs and check the minutes-to-seconds
conversion, without reading any Duration mapping from BRAVO.yml.
Details assertions still check the live Details selector
properties. Gate B (independent QA on stash-test, revised scope)
remains the live check and is NOT_RUN until it is performed.
"""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
BRAVO = ROOT / "scrapers" / "BRAVO.yml"


def load():
    return yaml.safe_load(BRAVO.read_text())


def test_clips_route_uses_clip_scraper_only():
    # Wave 2E (Agent F): the Clips route itself is unchanged and stays
    # first; the DVD route is a separate second entry (see the DVD
    # routing assertions below). "Clips-only" here means the Clips
    # route's patterns and handler, not the whole sceneByURL list.
    data = load()
    routes = data["sceneByURL"]
    clips = routes[0]
    assert clips["scraper"] == "clipSceneScraper"
    patterns = clips["url"]
    assert patterns == sorted(patterns)
    assert all("/clips/" in p for p in patterns)
    assert not any("/dvds/" in p for p in patterns)
    assert "clipSceneScraper" in data["xPathScrapers"]


def test_dvd_route_uses_dvd_scraper():
    data = load()
    routes = data["sceneByURL"]
    assert len(routes) == 2
    dvds = routes[1]
    assert dvds["scraper"] == "dvdSceneScraper"
    patterns = dvds["url"]
    assert patterns == sorted(patterns)
    assert all("/dvds/" in p for p in patterns)
    assert not any("/clips/" in p for p in patterns)
    assert "dvdSceneScraper" in data["xPathScrapers"]


def test_dvd_scraper_production_policy():
    # Wave 2E production mapping policy (Controller / Agent C v2.3):
    # Title / Code / URLs / Details / Date / Image only. Duration,
    # Studio, Tags and Performers must stay unmapped, and every
    # selector must be Agent A's G1-accepted verified XPath.
    data = load()
    dvd = data["xPathScrapers"]["dvdSceneScraper"]["scene"]
    assert set(dvd) == {"Title", "Code", "URLs", "Details", "Date", "Image"}
    assert "Duration" not in dvd
    assert "Studio" not in dvd
    assert "Tags" not in dvd
    assert "Performers" not in dvd
    assert dvd["Title"]["selector"] == "//h2[contains(.,'品番')]/preceding::h2[2]"
    assert dvd["Code"]["selector"] == "//h2[contains(.,'品番')]/following::h2[1]"
    assert dvd["URLs"]["selector"] == "//link[@rel='canonical']/@href"
    assert dvd["Details"]["selector"] == "//p[contains(@class,'font_8')]"
    assert dvd["Date"]["selector"] == "//h2[contains(.,'発売日')]/following::h2[1]"
    assert dvd["Image"]["selector"] == "//img[@alt!='' and contains(@src,'wixstatic')]/@src"
    # Date: Japanese format is validated + normalised by javascript,
    # then parsed with the standard Go layout; nothing else is a
    # production Date path.
    date_steps = dvd["Date"]["postProcess"]
    assert any("javascript" in s for s in date_steps)
    assert date_steps[-1] == {"parseDate": "2006-01-02"}
    # Image: the 084 sold-out artwork must never become a cover; the
    # rejection lives in the Image postProcess, not in a comment only.
    image_steps = dvd["Image"]["postProcess"]
    image_js = " ".join(str(s.get("javascript", "")) for s in image_steps)
    assert "soldout" in image_js
    assert "soldout" in BRAVO.read_text(encoding="utf-8")
    # No unsupported kill-switch style keys anywhere in the DVD block.
    assert "enabled" not in str(data["xPathScrapers"]["dvdSceneScraper"])


def test_no_direct_scene_by_fragment():
    data = load()
    assert "sceneByFragment" not in data


def test_query_fragment_removed_wave2e():
    # WS-2E-QF-001 (REMOVE_ORPHAN_QUERY_FRAGMENT_IN_WAVE2E): BRAVO has
    # no sceneByName, so sceneByQueryFragment was an orphan bound to
    # clipSceneScraper that applied Clips mappings to DVD URLs (Agent B
    # false-metadata reproduction). Wave 2E removes the entry entirely;
    # sceneByFragment stays absent. The runtime outcome of a direct
    # QueryFragment call after removal (clean unsupported vs upstream
    # panic, issue #97) is a Gate B question, not asserted here.
    data = load()
    assert "sceneByQueryFragment" not in data
    assert "sceneByFragment" not in data
    assert "sceneByName" not in data


def test_clip_selectors_are_not_dvd_selectors():
    data = load()
    clip = data["xPathScrapers"]["clipSceneScraper"]["scene"]
    for field in ("Title", "Code", "Details"):
        selector = clip[field]["selector"]
        assert "品番" not in selector, field
    assert clip["Title"]["selector"] == "//h1[1]"
    assert "Clip" in clip["Code"]["selector"]
    # Omission (WS-2E-DEF01-DEFER-20261104): production Duration must
    # be absent, not merely pointed elsewhere. Its source extraction
    # is covered by the deferred source-only tests below instead.
    assert "Duration" not in clip
    # No Date/Studio: the Clips source provides neither, so the fields must
    # stay absent rather than being fabricated.
    assert "Date" not in clip
    assert "Studio" not in clip


# Deferred Duration source (WS-2E-DEF01-DEFER-20261104, R3 H4).
# The selector below is the d6d6fbf production selector, verbatim,
# preserved here as a source-only regression test. It is NOT read
# from BRAVO.yml (production Duration is omitted) and it is NOT a
# new XPath iteration: it must equal the selector in
# docs/qa/PR93-DURATION-DEFERRED-SPEC.md (checked by
# test_deferred_duration_spec_matches_source_tests). The U+200B
# characters are written as escapes so they stay visible in diffs;
# at runtime they are the literal single U+200B codepoints. The
# selector must anchor on the ASCII "Clip" label, use a FORWARD axis
# only, skip empty / U+200B candidates via translate(), and require
# a digit start (so a price heading after Clip is not taken as
# minutes); it must not reference the 作品TIME label or any
# preceding:: axis (both reverse-axis forms failed live, and the H4
# finding makes the axis question moot for production until the
# runtime is fixed).
DEFERRED_DURATION_SELECTOR = (
    "//h2[normalize-space()='Clip']/following::h2[normalize-space(translate(., '\u200b', '')) != '' "
    "and translate(substring(normalize-space(translate(., '\u200b', '')), 1, 1), '0123456789', '') = ''][1]"
)

# (fixture html, expected future Duration seconds or None for absent).
# The conversion mirrors the deferred JS exactly: first digit group
# x 60, fail-closed to absent. Fixture HTMLs are read as UTF-8 text
# (they carry no charset meta; byte parsing would misread Japanese).
DEFERRED_DURATION_CASES = [
    ("clip-284.html", 1800),
    ("clip-282.html", 1800),
    ("clip-no-cover.html", 1800),  # 283
    ("clip-duration-price.html", 2700),  # 285, 45 minutes: not hardcoded
    ("clip-price-after-clip.html", 1800),  # 287: price heading skipped
    ("clip-spacer-after-clip.html", 1800),  # 288: spacer skipped
    ("clip-missing-duration.html", None),  # 289: no minutes, no guessing
]


def _deferred_duration_seconds(html_name):
    """Mirror the deferred selector's semantics with the stdlib only.

    CI installs only requirements.txt (pytest / pyyaml / jsonschema),
    so lxml is NOT available there (f4be5cf Full Test job failed on
    ``ModuleNotFoundError: No module named 'lxml'``); no other test
    in this file parses HTML, so no lxml dependency is introduced.
    The mirror implements the selector exactly: anchor on the h2
    whose normalized text is "Clip", then the first following h2
    whose U+200B-stripped normalized text is non-empty and starts
    with a digit; conversion is first digit group x 60, fail-closed.
    """
    import re
    from html.parser import HTMLParser

    class _H2Collector(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.h2_texts = []
            self._in_h2 = False
            self._buf = []

        def handle_starttag(self, tag, attrs):
            if tag == "h2" and not self._in_h2:
                self._in_h2 = True
                self._buf = []

        def handle_endtag(self, tag):
            if tag == "h2" and self._in_h2:
                self._in_h2 = False
                self.h2_texts.append("".join(self._buf))
                self._buf = []

        def handle_data(self, data):
            if self._in_h2:
                self._buf.append(data)

    def _norm(text):
        return " ".join(text.replace("\u200b", "").split())

    fixture = ROOT / "tests" / "fixtures" / "bravo" / html_name
    collector = _H2Collector()
    # Fixture HTMLs carry no charset meta; decode explicitly as UTF-8
    # (byte parsing would misread Japanese).
    collector.feed(fixture.read_text(encoding="utf-8"))
    texts = collector.h2_texts
    try:
        anchor = next(i for i, t in enumerate(texts) if _norm(t) == "Clip")
    except StopIteration:
        return None
    for text in texts[anchor + 1 :]:
        norm = _norm(text)
        if norm and norm[0] in "0123456789":
            match = re.search(r"(\d+)", norm)
            if not match:
                return None
            return int(match.group(1)) * 60
    return None


def test_no_lxml_dependency():
    # Regression guard for the f4be5cf CI failure: this file must run
    # under CI's requirements.txt, which has no lxml. (The word may
    # appear in comments explaining why; only an import is banned.)
    import re

    text = Path(__file__).read_text(encoding="utf-8")
    assert re.search(r"^ *(from|import) lxml\b", text, re.M) is None


def test_deferred_duration_selector_shape():
    assert DEFERRED_DURATION_SELECTOR != "//h2[normalize-space()='作品TIME']/preceding::h2[1]"
    assert "preceding::" not in DEFERRED_DURATION_SELECTOR
    assert "作品TIME" not in DEFERRED_DURATION_SELECTOR
    assert DEFERRED_DURATION_SELECTOR.startswith("//h2[normalize-space()='Clip']/following::h2[")
    assert "translate" in DEFERRED_DURATION_SELECTOR
    assert "\u200b" in DEFERRED_DURATION_SELECTOR
    assert "0123456789" in DEFERRED_DURATION_SELECTOR


def test_deferred_duration_source_cases():
    for html_name, want in DEFERRED_DURATION_CASES:
        assert _deferred_duration_seconds(html_name) == want, html_name


def test_deferred_duration_spec_matches_source_tests():
    spec = ROOT / "docs" / "qa" / "PR93-DURATION-DEFERRED-SPEC.md"
    text = spec.read_text(encoding="utf-8")
    assert "WS-2E-DEF01-DEFER-20261104" in text
    assert "## 7. Restoration" in text
    # The spec's xpath code block must carry the exact deferred selector.
    block = text.split("```xpath", 1)[1].split("```", 1)[0].strip()
    assert block == DEFERRED_DURATION_SELECTOR


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
    # R2 negatives: price after Clip, spacer after Clip, missing minutes.
    assert "BRAVO clip price after Clip" in names
    assert "BRAVO clip spacer after Clip" in names
    assert "BRAVO clip missing duration" in names
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
    # Omission: production mappedExpect.Duration assertions are gone
    # (WS-2E-DEF01-DEFER-20261104). The conversion expectations they
    # used to carry (45 min -> 2700 s; price/spacer traps -> 1800 s;
    # missing minutes -> absent) now live in the source-only tests
    # (DEFERRED_DURATION_CASES) instead of the production manifest.
    for case in by_name.values():
        fields = [m["field"] for m in case.get("mappedExpect", [])]
        assert "Duration" not in fields


def test_title_less_limitation_is_documented():
    # Declarative XPath cannot suppress Code/Duration/URLs when Title is
    # empty; that limitation must be recorded, not hidden, for Gate B.
    text = BRAVO.read_text()
    assert "Title-less" in text or "Title-less limitation" in text
    assert "must NOT be accepted as a successful scrape" in text
