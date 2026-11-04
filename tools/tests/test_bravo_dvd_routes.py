"""Wave 2E (WS-2E-20, Agent B) BRAVO DVD routing & QueryFragment safety tests.

These tests are deliberately independent of ``tools/tests/test_bravo_clips.py``
(Agent F owns that shared file at integration time) and they never modify the
production ``scrapers/BRAVO.yml``.

Three layers, kept separate on purpose:

1. **Synthetic candidate tests** — build an in-memory candidate dual-route
   configuration (the ``docs/61-bravo-dvd-wave-2e.md`` design sketch: the
   existing Clips route plus a second ``/dvds/`` route to a new
   ``dvdSceneScraper``) and verify the *test logic itself* against a
   Stash-compatible matcher model.

2. **Production-contract tests** — assertions about the real
   ``scrapers/BRAVO.yml``.  The Clips half passes today (Wave 1B baseline,
   PR #93).  The DVD half is marked ``EXPECTED_RED`` (xfail, strict): the
   production YAML does not implement DVD routing yet, and Agent F must
   remove the markers when integrating — a strict XPASS then fails loudly
   instead of silently leaving stale markers behind.

3. **Safety-expectation tests** — the behaviour a *safe* router would have
   (host-boundary aware, query strings cannot hijack routing).  Stash's
   substring matcher cannot provide these guarantees, so they are marked
   ``KNOWN_UPSTREAM_LIMITATION`` (xfail, strict).  They exist as reproducible
   failure evidence for a Controller decision, NOT as tests the YAML can be
   edited to pass.  Do not weaken the matcher model to make them pass.

Matcher model (B-01)
--------------------
The model mirrors the Stash build that runs on ``stash-test``,
``v0.31.1-182-g9e9ad972`` (upstream commit
``9e9ad972643320e737c711884f10e4285f0f3a88``):

* ``pkg/scraper/definition.go:163`` — ``ByURLDefinition.matchesURL`` is a
  plain substring test — Go ``strings.Contains(url, configuredPattern)``
  — not a hostname/path validation, not a regex, and case-sensitive.
* ``pkg/scraper/defined_scraper.go:108`` — ``viaURL`` walks the declared
  ``sceneByURL`` list in declaration order; the first route whose
  ``matchesURL`` returns true is executed first.  (Nuance: if that scrape
  returns a nil result with no error, ``viaURL`` continues to the next
  matching candidate; with non-nil results — the normal case — the first
  match decides.)
* ``pkg/scraper/cache.go:312`` — globally, ``Cache.ScrapeURL`` picks the
  first *scraper file* in cache order whose ``supportsURL`` is true; that
  is a different level from the within-file route choice above.  With no
  matching scraper at all it returns ``(nil, nil)``; the resulting
  empty-result handling is the separate upstream panic tracked in issue
  #97, not a routing behaviour this file asserts.
* ``pkg/scraper/definition.go:41`` — ``sceneByQueryFragment`` is a single
  ``*ByFragmentDefinition`` (not a list), and
  ``pkg/scraper/defined_scraper.go:46`` ``viaFragment`` hands a Scene
  input directly to that one definition's scraper.  It never re-runs
  ``viaURL`` selection.

Because matching is substring-based over the *whole* URL string, the query
string and fragment are part of the matched text, and the declared route
order decides collisions.  One nuance the negative matrix pins down: each
pattern is a *contiguous* ``host + path`` string, so an embedded family
only collides when the embedding carries the host part too (a bare
``/clips/284`` in a query string matches nothing; a full
``https://www.bravo-japan.com/clips/284`` in a query string matches both
patterns of the Clips route).  A prefix-attached lookalike host
(``notbravo-japan.com``) matches; a suffix-attached one
(``bravo-japan.com.evil.example``) does not, because ``.evil.example``
breaks the contiguous pattern.

QueryFragment (B-06)
--------------------
``sceneByQueryFragment`` in the Wave 1B YAML is a *single* definition whose
``scraper`` is hard-wired to ``clipSceneScraper``.  Nothing in that entry
point re-runs ``sceneByURL`` selection, so a DVD URL submitted through
QueryFragment is scraped with the Clips XPath set.  The offline extraction
tests at the bottom apply the production Clips selectors to the four
historical DVD DOM fixtures and pin the observed result: Title/Code/
Duration/Details/Image are empty, but ``URLs`` returns the (correct-looking)
DVD canonical and ``Tags`` returns a non-empty list that is *identical
across four different DVDs* — i.e. plausible, partial, cross-mode metadata.
See ``WAVE2E-B-ROUTING-REPORT.md`` for the decision record
(``FALSE_METADATA_RISK_CONFIRMED`` / ``RELEASE_BLOCKER``).

Addendum (docs/63) — B-08/B-09: route selection and product validity are
independent assertions.  The ``TestRouteVersusProductValidity`` section
pins the fail-closed validity gate (product marker + Title + string Code
identical to the canonical's last segment): ``/dvds/00`` and
``/dvds/999999`` route to ``dvdSceneScraper`` by URL shape yet are NOT
valid products, even though their canonical link is populated.

Readiness (WAVE2E-B-ROUTING-QF-READINESS-20261104; Controller decision
WS-2E-QF-001, docs/66): ``TestWave2EQFRemovalReadiness`` prepares the
contract for Agent F's removal of the orphaned ``sceneByQueryFragment``
in the Wave 2E candidate — synthetic-candidate assertions pass now, the
production assertion is EXPECTED_RED until F lands the removal, and the
historical hazard reproduction above stays in place regardless.  Nothing
in this file claims the mitigation is implemented or runtime-verified.
"""

import copy
import hashlib
from html.parser import HTMLParser
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
BRAVO = ROOT / "scrapers" / "BRAVO.yml"
DVD_FIXTURE_DIR = ROOT / "tests" / "fixtures" / "bravo"
HISTORICAL_MANIFEST = DVD_FIXTURE_DIR / "bravo-fixtures.yml"
HISTORICAL_SHA256 = "be1885d2097683e8c4ae5f2440120e8bd7945ac16f62c1910ac87e5d009d39b2"

CLIP_URL_284 = "https://www.bravo-japan.com/clips/284"
CLIP_URL_282 = "https://www.bravo-japan.com/clips/282"
DVD_URL_234 = "https://www.bravo-japan.com/dvds/234"
DVD_URL_084 = "https://www.bravo-japan.com/dvds/084"
DVD_URL_046 = "https://www.bravo-japan.com/dvds/046"

EXPECTED_RED = pytest.mark.xfail(
    strict=True,
    reason=(
        "EXPECTED_RED: Wave 2E DVD routing is not integrated in production "
        "BRAVO.yml yet; Agent F removes this marker at integration."
    ),
)
KNOWN_LIMITATION = pytest.mark.xfail(
    strict=True,
    reason=(
        "KNOWN_UPSTREAM_LIMITATION: Stash matchesURL is strings.Contains "
        "over the whole URL; YAML patterns cannot provide this guarantee."
    ),
)


# --------------------------------------------------------------------------
# Stash-compatible matcher model (B-01).  This mirrors the runtime; it must
# NOT be "fixed" to make safety expectations pass.
# --------------------------------------------------------------------------

def stash_matches(url, pattern):
    """Go strings.Contains(url, pattern): substring, case-sensitive."""
    return pattern in url


def select_handler(routes, url):
    """First route in declaration order with any pattern contained in url.

    Returns the route's scraper name, or None when no route matches.
    """
    for route in routes:
        patterns = route["url"]
        if isinstance(patterns, str):
            patterns = [patterns]
        if any(stash_matches(url, p) for p in patterns):
            return route["scraper"]
    return None


def matching_routes(routes, url):
    """All routes that match, in declaration order (collision evidence)."""
    out = []
    for route in routes:
        patterns = route["url"]
        if isinstance(patterns, str):
            patterns = [patterns]
        if any(stash_matches(url, p) for p in patterns):
            out.append(route["scraper"])
    return out


# --------------------------------------------------------------------------
# Configuration builders
# --------------------------------------------------------------------------

def load_production():
    return yaml.safe_load(BRAVO.read_text())


def candidate_config():
    """Production YAML + the doc-61 design-sketch DVD route, in memory only."""
    data = copy.deepcopy(load_production())
    data["sceneByURL"].append(
        {
            "action": "scrapeXPath",
            "url": [
                "bravo-japan.com/dvds/",
                "www.bravo-japan.com/dvds/",
            ],
            "scraper": "dvdSceneScraper",
        }
    )
    # Route selection only needs the handler to exist; Agent A/F supply the
    # real DVD XPath set.  An empty scene map is an explicit stub, not a
    # claim about DVD fields.
    data["xPathScrapers"]["dvdSceneScraper"] = {"scene": {}}
    return data


def candidate_routes():
    return candidate_config()["sceneByURL"]


def wave2e_candidate_config():
    """The Wave 2E target candidate per Controller decision WS-2E-QF-001
    (docs/66): candidate dual-route config with the orphaned
    ``sceneByQueryFragment`` removed entirely and ``sceneByFragment``
    absent.  Built in memory only; Agent F implements it in the real
    YAML, and independent QA must still verify the runtime behaviour —
    a config-level absence is not proof of a safe unsupported response.
    """
    data = candidate_config()
    data.pop("sceneByQueryFragment", None)
    data.pop("sceneByFragment", None)
    return data


# --------------------------------------------------------------------------
# B-02 — Positive routing on the synthetic candidate configuration
# --------------------------------------------------------------------------

class TestCandidatePositiveRouting:
    @pytest.mark.parametrize(
        "url,expected",
        [
            (CLIP_URL_284, "clipSceneScraper"),   # B-P01
            (CLIP_URL_282, "clipSceneScraper"),   # B-P02
            (DVD_URL_234, "dvdSceneScraper"),     # B-P03
            (DVD_URL_084, "dvdSceneScraper"),     # B-P04
            (DVD_URL_046, "dvdSceneScraper"),     # B-P05 (leading zero kept)
        ],
    )
    def test_positive_matrix(self, url, expected):
        assert select_handler(candidate_routes(), url) == expected

    @pytest.mark.parametrize(
        "url,expected",
        [
            # B-P06: www and non-www forms.  Note the non-www pattern is a
            # substring of the www URL too, so both patterns of a family
            # match the www form; the handler is still unambiguous because
            # patterns of one family live in one route.
            ("https://bravo-japan.com/clips/284", "clipSceneScraper"),
            ("https://www.bravo-japan.com/clips/284", "clipSceneScraper"),
            ("https://bravo-japan.com/dvds/234", "dvdSceneScraper"),
            ("https://www.bravo-japan.com/dvds/234", "dvdSceneScraper"),
        ],
    )
    def test_www_and_non_www(self, url, expected):
        assert select_handler(candidate_routes(), url) == expected

    def test_each_positive_url_matches_exactly_one_route(self):
        for url in (CLIP_URL_284, CLIP_URL_282, DVD_URL_234, DVD_URL_084, DVD_URL_046):
            assert len(matching_routes(candidate_routes(), url)) == 1, url


# --------------------------------------------------------------------------
# B-03 — Negative & collision cases: what the runtime model actually does.
# Classification per case:
#   EXPECTED_SAFE            - no handler / correct handler, no ambiguity
#   OBSERVED_RUNTIME_MATCH   - runtime matches; recorded as observed fact
#   UNSAFE_MATCH             - runtime routes a URL it should not route
#   KNOWN_UPSTREAM_LIMITATION- the unsafe behaviour is inherent to Contains
# --------------------------------------------------------------------------

class TestCandidateNegativeAndCollision:
    @pytest.mark.parametrize(
        "url,expected,classification",
        [
            # Unrelated host without the pattern string anywhere: safe.
            ("https://example.com/clips/284", None, "EXPECTED_SAFE"),
            ("https://example.com/dvds/234", None, "EXPECTED_SAFE"),
            # Incomplete path: pattern ends with "/dvds/", bare "/dvds"
            # does not contain it.
            ("https://www.bravo-japan.com/dvds", None, "EXPECTED_SAFE"),
            ("https://www.bravo-japan.com/clips", None, "EXPECTED_SAFE"),
            # Case sensitivity: strings.Contains is case-sensitive.
            ("https://www.bravo-japan.com/CLIPS/284", None, "OBSERVED_RUNTIME_MATCH"),
            # /dvds/ with no work ID still matches the route pattern: route
            # selection succeeds, the scrape itself has no ID to fetch.
            (DVD_URL_234.rsplit("/", 1)[0] + "/", "dvdSceneScraper", "OBSERVED_RUNTIME_MATCH"),
            # Suffix-attached lookalike host: ".evil.example" breaks the
            # contiguous host+path pattern, so this one does NOT match.
            ("https://bravo-japan.com.evil.example/clips/284", None, "EXPECTED_SAFE"),
            # Prefix-attached lookalike host: "not" + pattern is still a
            # superstring of the pattern. UNSAFE, inherent to the matcher.
            ("https://notbravo-japan.com/clips/284", "clipSceneScraper", "UNSAFE_MATCH"),
            # Pattern embedded in a foreign host's path or query (with the
            # host part included) matches. UNSAFE, inherent to the matcher.
            ("https://evil.example/bravo-japan.com/clips/284", "clipSceneScraper", "UNSAFE_MATCH"),
            ("https://example.com/?u=bravo-japan.com/dvds/234", "dvdSceneScraper", "UNSAFE_MATCH"),
            # A bare family path inside a query string matches NOTHING,
            # because every pattern includes the host part.  The path's own
            # family is the only match, in both directions.
            (CLIP_URL_284 + "?next=/dvds/234", "clipSceneScraper", "EXPECTED_SAFE"),
            (DVD_URL_234 + "?ref=/clips/284", "dvdSceneScraper", "EXPECTED_SAFE"),
            (DVD_URL_234 + "#/clips/284", "dvdSceneScraper", "EXPECTED_SAFE"),
            # A FULL foreign-family URL embedded in the query string does
            # collide: both routes match.  On a Clips URL the first declared
            # route is still the path's own family...
            (CLIP_URL_284 + "?next=" + DVD_URL_234, "clipSceneScraper", "OBSERVED_RUNTIME_MATCH"),
            # ...but on a DVD URL the same trick HIJACKS routing to the
            # Clips handler, purely because Clips is declared first.
            (DVD_URL_234 + "?ref=" + CLIP_URL_284, "clipSceneScraper", "UNSAFE_MATCH"),
            (DVD_URL_234 + "#" + CLIP_URL_284, "clipSceneScraper", "UNSAFE_MATCH"),
            # Both families in the path: only the family whose pattern is
            # contiguous with the host matches; the trailing "/dvds/234"
            # has no host part in front of it.
            ("https://www.bravo-japan.com/clips/284/dvds/234", "clipSceneScraper", "OBSERVED_RUNTIME_MATCH"),
        ],
    )
    def test_runtime_model_outcomes(self, url, expected, classification):
        assert select_handler(candidate_routes(), url) == expected, classification

    def test_query_hijack_is_a_real_collision(self):
        # Both routes match the hijack URL; selection is purely order-based.
        url = DVD_URL_234 + "?ref=" + CLIP_URL_284
        assert matching_routes(candidate_routes(), url) == [
            "clipSceneScraper",
            "dvdSceneScraper",
        ]


class TestRouteOrderDependence:
    """Reversing declaration order flips every collision outcome, which
    proves selection is order-based, not specificity-based."""

    def reversed_candidate_routes(self):
        routes = candidate_routes()
        return list(reversed(routes))

    def test_reversed_order_flips_query_hijack(self):
        url = DVD_URL_234 + "?ref=" + CLIP_URL_284
        assert select_handler(self.reversed_candidate_routes(), url) == "dvdSceneScraper"

    def test_reversed_order_flips_clips_url_embed(self):
        url = CLIP_URL_284 + "?next=" + DVD_URL_234
        assert select_handler(self.reversed_candidate_routes(), url) == "dvdSceneScraper"

    def test_dual_path_is_order_independent(self):
        # Only the host-contiguous family matches, so order cannot flip it.
        url = "https://www.bravo-japan.com/clips/284/dvds/234"
        assert select_handler(self.reversed_candidate_routes(), url) == "clipSceneScraper"

    def test_reversed_order_keeps_clean_urls_correct(self):
        routes = self.reversed_candidate_routes()
        assert select_handler(routes, CLIP_URL_284) == "clipSceneScraper"
        assert select_handler(routes, DVD_URL_234) == "dvdSceneScraper"


class TestSafetyExpectations:
    """What a safe router SHOULD do.  All xfail: strings.Contains cannot
    deliver host-boundary or query isolation.  Kept as decision evidence
    for the Controller; not fixable at YAML level."""

    @KNOWN_LIMITATION
    def test_lookalike_host_must_not_route(self):
        assert select_handler(candidate_routes(), "https://notbravo-japan.com/clips/284") is None

    @KNOWN_LIMITATION
    def test_pattern_in_query_of_foreign_host_must_not_route(self):
        url = "https://example.com/?u=bravo-japan.com/dvds/234"
        assert select_handler(candidate_routes(), url) is None

    @KNOWN_LIMITATION
    def test_dvd_url_with_full_clips_url_in_query_must_use_dvd_handler(self):
        url = DVD_URL_234 + "?ref=" + CLIP_URL_284
        assert select_handler(candidate_routes(), url) == "dvdSceneScraper"


# --------------------------------------------------------------------------
# Production contract (B-02/B-04/B-07).  Clips assertions pass on the
# Wave 1B baseline; DVD assertions are EXPECTED_RED until Agent F integrates.
# --------------------------------------------------------------------------

def _routes_by_family(data):
    clips, dvds, other = [], [], []
    for route in data["sceneByURL"]:
        patterns = route["url"] if isinstance(route["url"], list) else [route["url"]]
        if all("/clips/" in p for p in patterns):
            clips.append(route)
        elif all("/dvds/" in p for p in patterns):
            dvds.append(route)
        else:
            other.append(route)
    return clips, dvds, other


class TestProductionRoutingContract:
    def test_exactly_one_clips_route_to_clip_scraper(self):
        clips, _, _ = _routes_by_family(load_production())
        assert len(clips) == 1
        assert clips[0]["scraper"] == "clipSceneScraper"
        patterns = clips[0]["url"]
        assert patterns == sorted(patterns)

    def test_no_unexpected_third_route(self):
        data = load_production()
        clips, dvds, other = _routes_by_family(data)
        assert other == []
        assert len(clips) + len(dvds) == len(data["sceneByURL"])

    def test_production_clips_urls_select_clip_handler(self):
        routes = load_production()["sceneByURL"]
        assert select_handler(routes, CLIP_URL_284) == "clipSceneScraper"
        assert select_handler(routes, CLIP_URL_282) == "clipSceneScraper"

    def test_no_scene_by_fragment(self):
        assert "sceneByFragment" not in load_production()

    @EXPECTED_RED
    def test_exactly_one_dvd_route_to_dvd_scraper(self):
        _, dvds, _ = _routes_by_family(load_production())
        assert len(dvds) == 1
        assert dvds[0]["scraper"] == "dvdSceneScraper"
        patterns = dvds[0]["url"]
        assert patterns == sorted(patterns)

    @EXPECTED_RED
    def test_exactly_two_routes_total(self):
        assert len(load_production()["sceneByURL"]) == 2

    @EXPECTED_RED
    def test_dvd_scraper_defined(self):
        assert "dvdSceneScraper" in load_production()["xPathScrapers"]

    @EXPECTED_RED
    @pytest.mark.parametrize("url", [DVD_URL_234, DVD_URL_084, DVD_URL_046])
    def test_production_dvd_urls_select_dvd_handler(self, url):
        routes = load_production()["sceneByURL"]
        assert select_handler(routes, url) == "dvdSceneScraper"


# --------------------------------------------------------------------------
# B-06 — QueryFragment routing facts
# --------------------------------------------------------------------------

class TestQueryFragmentContract:
    """Baseline (Wave 1B / PR #93) QueryFragment facts.  These describe the
    pre-Wave-2E configuration that creates the hazard; once Agent F applies
    WS-2E-QF-001 and the entry is removed, they skip explicitly and the
    readiness contract in TestWave2EQFRemovalReadiness takes over.  The
    hazard reproduction itself lives in
    TestQueryFragmentOfflineExtraction and does not depend on the entry
    still being configured."""

    def test_query_fragment_is_a_single_clip_bound_definition(self):
        data = load_production()
        if "sceneByQueryFragment" not in data:
            pytest.skip("superseded by WS-2E-QF-001 removal; see TestWave2EQFRemovalReadiness")
        qf = data["sceneByQueryFragment"]
        # A single mapping (not a list): there is exactly one QueryFragment
        # handler slot, and Wave 1B binds it to the Clips scraper.
        assert isinstance(qf, dict)
        assert qf["queryURL"] == "{url}"
        assert qf["scraper"] == "clipSceneScraper"

    def test_query_fragment_does_not_reselect_by_url(self):
        # Model of the entry point: the handler is the constant declared in
        # sceneByQueryFragment, independent of the submitted URL.  A DVD
        # URL therefore reaches clipSceneScraper, never dvdSceneScraper,
        # regardless of any future sceneByURL DVD route.
        data = candidate_config()
        if "sceneByQueryFragment" not in data:
            pytest.skip("superseded by WS-2E-QF-001 removal; see TestWave2EQFRemovalReadiness")
        qf_handler = data["sceneByQueryFragment"]["scraper"]
        assert qf_handler == "clipSceneScraper"
        assert select_handler(data["sceneByURL"], DVD_URL_234) == "dvdSceneScraper"
        assert qf_handler != select_handler(data["sceneByURL"], DVD_URL_234)


# --------------------------------------------------------------------------
# Readiness for WS-2E-QF-001 (docs/66): removal of the orphaned
# QueryFragment in the Wave 2E candidate.  Agent B only PREPARES these
# tests: the production assertions are EXPECTED_RED until Agent F removes
# the entry on feat/e2e-bravo-dvds, and the runtime outcome of a direct
# fragment call after removal (clean unsupported vs upstream panic) can
# only be settled by independent Gate B cases QF-05/06/07 — never by a
# config assertion in this file.
# --------------------------------------------------------------------------

class TestWave2EQFRemovalReadiness:
    def test_synthetic_wave2e_candidate_has_no_fragment_entries(self):
        data = wave2e_candidate_config()
        assert "sceneByQueryFragment" not in data
        assert "sceneByFragment" not in data

    def test_synthetic_wave2e_candidate_routing_survives_qf_removal(self):
        # URL mode does not depend on the QueryFragment entry (docs/66
        # rationale): removing it must not change handler selection.
        routes = wave2e_candidate_config()["sceneByURL"]
        assert select_handler(routes, CLIP_URL_284) == "clipSceneScraper"
        assert select_handler(routes, CLIP_URL_282) == "clipSceneScraper"
        assert select_handler(routes, DVD_URL_234) == "dvdSceneScraper"
        assert select_handler(routes, DVD_URL_084) == "dvdSceneScraper"
        assert select_handler(routes, DVD_URL_046) == "dvdSceneScraper"

    def test_synthetic_wave2e_candidate_has_no_fragment_handler(self):
        # Model of defined_scraper.go viaFragment with no Scene fragment
        # definition configured: the Scene branch finds no fragment
        # scraper (the Performer URL fallback does not apply to Scene
        # input), so the config-level outcome is "no handler".  Whether
        # the real runtime surfaces that as a clean unsupported error or
        # as the upstream panic is Gate B QF-05/06/07 evidence, NOT
        # asserted here.
        data = wave2e_candidate_config()
        assert data.get("sceneByQueryFragment") is None
        assert data.get("sceneByFragment") is None

    @EXPECTED_RED
    def test_production_candidate_has_query_fragment_removed(self):
        # WS-2E-QF-001 target contract for Agent F's candidate.  On the
        # PR #93 baseline the entry is still present, hence EXPECTED_RED;
        # F retires this marker when the removal lands (docs/66 section
        # 3.4: retire strict EXPECTED_RED only when the feature state is
        # present; KNOWN_UPSTREAM_LIMITATION cases stay).
        assert "sceneByQueryFragment" not in load_production()

    def test_production_scene_by_fragment_stays_absent(self):
        # Already true on the baseline and binding after removal (QF-08).
        assert "sceneByFragment" not in load_production()


# --------------------------------------------------------------------------
# B-06 — Offline extraction: production Clips XPath set applied to the
# historical DVD DOM fixtures.  Uses a tiny DOM + an evaluator for exactly
# the selector shapes the Clips scraper declares; an unknown selector shape
# fails the test loudly instead of silently passing.
# --------------------------------------------------------------------------

_VOID = {"meta", "link", "img", "br", "hr", "input", "source"}


class _Node:
    __slots__ = ("tag", "attrs", "children", "parent", "text")

    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children = []
        self.parent = parent
        self.text = ""


class _DOM(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node("#root", [], None)
        self.stack = [self.root]
        self.order = []

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        self.order.append(node)
        if tag not in _VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = _Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        self.order.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.stack[-1].text += data


def _text(node):
    parts = [node.text]
    for child in node.children:
        parts.append(_text(child))
    return "".join(parts)


def _norm(node):
    return " ".join(_text(node).split())


def eval_clip_selector(dom, selector):
    """Evaluate one production Clips selector against a parsed fixture.

    Supports only the shapes currently declared in clipSceneScraper.
    Returns a list of raw strings (attribute values or element texts).
    """
    import re

    m = re.fullmatch(r"//h1\[1\]", selector)
    if m:
        return [_text(n) for n in dom.order if n.tag == "h1"][:1]
    m = re.fullmatch(r"//link\[@rel='canonical'\]/@href", selector)
    if m:
        return [n.attrs["href"] for n in dom.order if n.tag == "link" and n.attrs.get("rel") == "canonical" and "href" in n.attrs]
    m = re.fullmatch(r"//meta\[@name='keywords'\]/@content", selector)
    if m:
        return [n.attrs["content"] for n in dom.order if n.tag == "meta" and n.attrs.get("name") == "keywords" and "content" in n.attrs]
    m = re.fullmatch(r"//video/@poster", selector)
    if m:
        return [n.attrs["poster"] for n in dom.order if n.tag == "video" and "poster" in n.attrs]
    m = re.fullmatch(r"//h2\[normalize-space\(\)='(.+)'\]/preceding::h2\[1\]", selector)
    if m:
        label = m.group(1)
        h2s = [n for n in dom.order if n.tag == "h2"]
        for i, n in enumerate(h2s):
            if _norm(n) == label:
                return [_text(h2s[i - 1])] if i > 0 else []
        return []
    m = re.fullmatch(r"//h1\[1\]/following::h2\[1\]", selector)
    if m:
        seen_h1 = False
        for n in dom.order:
            if n.tag == "h1" and not seen_h1:
                seen_h1 = True
                continue
            if seen_h1 and n.tag == "h2":
                return [_text(n)]
        return []
    m = re.fullmatch(r"//h2\[contains\(\.,'(.+)'\)\]", selector)
    if m:
        label = m.group(1)
        return [_text(n) for n in dom.order if n.tag == "h2" and label in _text(n)]
    m = re.fullmatch(r"//h2\[contains\(\.,'(.+)'\)\]/preceding::h2\[(\d+)\]", selector)
    if m:
        label, idx = m.group(1), int(m.group(2))
        h2s = [n for n in dom.order if n.tag == "h2"]
        for i, n in enumerate(h2s):
            if label in _text(n):
                return [_text(h2s[i - idx])] if i - idx >= 0 else []
        return []
    m = re.fullmatch(r"//h2\[contains\(\.,'(.+)'\)\]/following::h2\[(\d+)\]", selector)
    if m:
        label, idx = m.group(1), int(m.group(2))
        h2s = [n for n in dom.order if n.tag == "h2"]
        for i, n in enumerate(h2s):
            if label in _text(n):
                return [_text(h2s[i + idx])] if i + idx < len(h2s) else []
        return []
    m = re.fullmatch(r"//img\[@alt!='' and contains\(@src,'wixstatic'\)\]/@src", selector)
    if m:
        return [
            n.attrs["src"]
            for n in dom.order
            if n.tag == "img" and n.attrs.get("alt") and "wixstatic" in n.attrs.get("src", "")
        ]
    m = re.fullmatch(
        r"//div\[@id='([^']+)'\]//span\[contains\(@class,\s*'([^']+)'\)\]\[normalize-space\(translate\(\.,\s*'[^']*',\s*''\)\)\s*!=\s*''\]\[1\]",
        selector,
    )
    if m:
        # DEF-02-corrected Details shape (PR #93 @ ce7ef6c): the first
        # rich-text span inside the $desc container whose text is non-empty
        # after removing zero-width spaces.
        div_id, class_part = m.group(1), m.group(2)

        def descendants(node):
            for child in node.children:
                yield child
                yield from descendants(child)

        for div in (n for n in dom.order if n.tag == "div" and n.attrs.get("id") == div_id):
            for span in descendants(div):
                if span.tag == "span" and class_part in span.attrs.get("class", ""):
                    if _norm(span).replace("\u200b", "").strip():
                        return [_text(span)]
            return []
        return []
    raise AssertionError(f"Unsupported selector shape in route test evaluator: {selector}")


def clip_extract_on(fixture_name):
    data = load_production()
    scraper_def = data["xPathScrapers"]["clipSceneScraper"]
    scene = scraper_def["scene"]
    common = scraper_def.get("common", {})
    dom = _DOM()
    dom.feed((DVD_FIXTURE_DIR / fixture_name).read_text(encoding="utf-8", errors="replace"))
    out = {}
    for field, spec in scene.items():
        selector = spec["Name"]["selector"] if field == "Tags" else spec["selector"]
        # Resolve $common variables the way the fixture runner does
        # (verify-scraper-mappings.mjs resolveSelector: literal replaceAll,
        # longest key first).
        for key in sorted(common, key=len, reverse=True):
            name = key if key.startswith("$") else "$" + key
            selector = selector.replace(name, common[key])
        out[field] = [v.strip() for v in eval_clip_selector(dom, selector)]
    return out


DVD_FIXTURES = ["dvd-046.html", "dvd-281.html", "dvd-173.html", "dvd-215.html"]


class TestQueryFragmentOfflineExtraction:
    """What a DVD QueryFragment submission would extract TODAY with the
    Clips XPath set, on the four historical DVD DOM captures.  These tests
    PASS by pinning the hazardous observed behaviour; they are the offline
    evidence behind FALSE_METADATA_RISK_CONFIRMED."""

    @pytest.mark.parametrize("fixture", DVD_FIXTURES)
    def test_dvd_dom_yields_no_core_fields(self, fixture):
        out = clip_extract_on(fixture)
        assert out["Title"] == []
        assert out["Code"] == []
        # Duration: unmapped in production since WS-2E-DEF01-DEFER-20261104,
        # so absence and empty are the same outcome here; when this suite
        # ran against the pre-deferral baseline the mapped selector also
        # extracted nothing from DVD DOM.
        assert out.get("Duration", []) == []
        assert out["Details"] == []
        assert out["Image"] == []

    @pytest.mark.parametrize(
        "fixture,canonical",
        [
            ("dvd-046.html", "https://www.bravo-japan.com/dvds/046"),
            ("dvd-281.html", "https://www.bravo-japan.com/dvds/281"),
            ("dvd-173.html", "https://www.bravo-japan.com/dvds/173"),
            ("dvd-215.html", "https://www.bravo-japan.com/dvds/215"),
        ],
    )
    def test_dvd_dom_yields_plausible_url_and_tags(self, fixture, canonical):
        out = clip_extract_on(fixture)
        # The URL is the page's own canonical — correct-looking — and Tags
        # are non-empty.  Together with the empty core fields above, this
        # is a partial, plausible result, not a clean failure.
        assert out["URLs"] == [canonical]
        assert out["Tags"] != []

    def test_tags_are_identical_across_four_different_dvds(self):
        # The same keywords list on four different works proves the Tags
        # value is a site/section-level list on DVD pages, not work-specific
        # metadata.  Returning it as a DVD scene's Tags via the Clips
        # handler would be false metadata.
        tag_sets = [tuple(clip_extract_on(f)["Tags"]) for f in DVD_FIXTURES]
        assert len(set(tag_sets)) == 1


# --------------------------------------------------------------------------
# B-08/B-09 (assignment addendum, docs/63) — Route selection is NOT product
# validity.  Two independent assertions:
#   (1) Stash-compatible first-match handler selection (sections above).
#   (2) Content validity of what the selected handler would extract.
# A 404 page can satisfy (1) — its URL shape matches the DVD route — and
# still carry a canonical link, so (2) must reject it explicitly.  The
# validity oracle follows Agent A's raw-DOM addendum (commit 16224b4):
# the product marker //h2[contains(.,'品番')] is the validity gate, Title
# and Code come from its neighbouring h2 elements, Code is a string and
# must equal the canonical's last segment (leading zeros preserved).
# Agent A's status pair is recorded, not upgraded: AUTHOR_HANDOFF=READY,
# INDEPENDENT_EVIDENCE_ACCEPTANCE=CHANGES_REQUESTED.  The historical repo
# fixtures below independently reproduce A's reported Title/Code for
# dvds/046 and dvds/281; that is partial corroboration, not G1 acceptance.
# --------------------------------------------------------------------------

# Agent A's final-spec selector subset relevant to validity.  Used ONLY as
# a test extractor; Agent B does not implement production YAML.
DVD_VALIDITY_SELECTORS = {
    "Marker": "//h2[contains(.,'品番')]",
    "Title": "//h2[contains(.,'品番')]/preceding::h2[2]",
    "Code": "//h2[contains(.,'品番')]/following::h2[1]",
    "URLs": "//link[@rel='canonical']/@href",
    "Image": "//img[@alt!='' and contains(@src,'wixstatic')]/@src",
}


def extract_with(dom, selectors):
    return {
        field: [v.strip() for v in eval_clip_selector(dom, selector)]
        for field, selector in selectors.items()
    }


def parse_html(text):
    dom = _DOM()
    dom.feed(text)
    return dom


def dvd_extract_on(fixture_name):
    text = (DVD_FIXTURE_DIR / fixture_name).read_text(encoding="utf-8", errors="replace")
    return extract_with(parse_html(text), DVD_VALIDITY_SELECTORS)


def product_validity(extract, url):
    """Fail-closed product-validity gate (B-09).

    Returns (is_valid, reasons).  A result is a valid product only when
    the product marker exists, Title is non-empty, Code is a non-empty
    string identical to the canonical URL's last segment, and the
    extracted canonical equals the requested URL.  A populated canonical
    alone proves nothing.
    """
    reasons = []
    segment = url.rstrip("/").rsplit("/", 1)[-1]
    if not extract["Marker"]:
        reasons.append("product marker (品番) absent")
    if not extract["Title"] or not extract["Title"][0]:
        reasons.append("Title empty")
    code = extract["Code"][0] if extract["Code"] else ""
    if not code:
        reasons.append("Code empty")
    elif code != segment:
        reasons.append(f"Code/URL identity mismatch: Code {code!r} != URL segment {segment!r}")
    canonical = extract["URLs"][0] if extract["URLs"] else ""
    if canonical != url:
        reasons.append(f"canonical mismatch: {canonical!r} != {url!r}")
    return (not reasons, reasons)


# A 404 DVD page modelled on the characteristics Agent A documented for
# /dvds/00 and /dvds/999999 (raw DOM stays in A's restricted workspace;
# this is a modelled control, not A's evidence): document title is a 404,
# a canonical link IS present and points at the 404 URL itself, the same
# site-generic keywords meta is present, there is no 品番 marker, and the
# only wixstatic image is an alt-less site asset.
SYNTHETIC_404_TEMPLATE = """<html lang="ja"><head>
<title>404 | bravo-works</title>
<link rel="canonical" href="{url}">
<meta name="keywords" content="BL, ぽっちゃり, アナル, ガチムチ">
</head><body>
<h2>BRAVO-JAPAN</h2>
<h2>404 Not Found</h2>
<img src="https://static.wixstatic.com/media/site-asset.png" alt="">
</body></html>"""


class TestRouteVersusProductValidity:
    @pytest.mark.parametrize(
        "fixture,url,title,code",
        [
            ("dvd-046.html", DVD_URL_046, "ゆるゆる雄太のデブ竿ぽちゃ穴食べ放題!", "046"),
            ("dvd-281.html", "https://www.bravo-japan.com/dvds/281", "熊ケツ4", "281"),
            ("dvd-173.html", "https://www.bravo-japan.com/dvds/173", "筋肉BANANA", "173"),
            ("dvd-215.html", "https://www.bravo-japan.com/dvds/215", "種竿狂", "215"),
        ],
    )
    def test_historical_dvd_products_are_valid(self, fixture, url, title, code):
        extract = dvd_extract_on(fixture)
        assert extract["Title"] == [title]
        assert extract["Code"] == [code]
        assert isinstance(extract["Code"][0], str)  # "046", never int 46
        valid, reasons = product_validity(extract, url)
        assert valid, reasons

    @pytest.mark.parametrize("url", ["https://www.bravo-japan.com/dvds/00", "https://www.bravo-japan.com/dvds/999999"])
    def test_404_routes_by_shape_but_is_not_a_product(self, url):
        # (1) Route selection: the URL shape matches the DVD route.
        assert select_handler(candidate_routes(), url) == "dvdSceneScraper"
        # (2) Product validity: rejected, even though a canonical exists.
        dom = parse_html(SYNTHETIC_404_TEMPLATE.format(url=url))
        extract = extract_with(dom, DVD_VALIDITY_SELECTORS)
        assert extract["Marker"] == []
        assert extract["Title"] == [] and extract["Code"] == []
        # The hazard, pinned: URLs is populated on an invalid product.
        assert extract["URLs"] == [url]
        valid, reasons = product_validity(extract, url)
        assert not valid
        assert any("marker" in r for r in reasons)

    @pytest.mark.parametrize("url", ["https://www.bravo-japan.com/dvds/00", "https://www.bravo-japan.com/dvds/999999"])
    def test_404_through_clip_selectors_also_fails_validity(self, url):
        # The same partial-metadata shape appears if a 404 DVD page is
        # reached through the Clips XPath set (e.g. via QueryFragment):
        # canonical + site-generic Tags populated, core fields empty.
        dom = parse_html(SYNTHETIC_404_TEMPLATE.format(url=url))
        clip = load_production()["xPathScrapers"]["clipSceneScraper"]["scene"]
        selectors = {
            "Marker": "//h2[contains(.,'品番')]",
            "Title": clip["Title"]["selector"],
            "Code": clip["Code"]["selector"],
            "URLs": clip["URLs"]["selector"],
        }
        extract = extract_with(dom, selectors)
        assert extract["URLs"] == [url]
        valid, _ = product_validity(extract, url)
        assert not valid

    def test_404_image_selector_is_fail_closed(self):
        # A's Image selector returns nothing on the modelled 404 even
        # though a wixstatic site asset is present (alt is empty).  A real
        # product page without a cover must likewise yield no Image rather
        # than site artwork; /dvds/084's sold-out artwork is a separate
        # policy case for F/Controller, not generic-absence evidence.
        url = "https://www.bravo-japan.com/dvds/00"
        dom = parse_html(SYNTHETIC_404_TEMPLATE.format(url=url))
        extract = extract_with(dom, DVD_VALIDITY_SELECTORS)
        assert extract["Image"] == []

    def test_route_and_validity_are_independent_axes(self):
        # Same handler, opposite validity — neither implies the other.
        routes = candidate_routes()
        assert select_handler(routes, DVD_URL_046) == "dvdSceneScraper"
        assert select_handler(routes, "https://www.bravo-japan.com/dvds/00") == "dvdSceneScraper"
        assert product_validity(dvd_extract_on("dvd-046.html"), DVD_URL_046)[0] is True
        dom = parse_html(SYNTHETIC_404_TEMPLATE.format(url="https://www.bravo-japan.com/dvds/00"))
        assert product_validity(extract_with(dom, DVD_VALIDITY_SELECTORS), "https://www.bravo-japan.com/dvds/00")[0] is False

    def test_unmatched_control_has_no_handler(self):
        # B-08 control case; the resulting Stash behaviour is upstream
        # issue #97, tracked separately and not asserted here.
        assert select_handler(candidate_routes(), "https://example.com/dvds/234") is None

    def test_canonical_alone_is_never_sufficient(self):
        # Even for a REAL product URL, an extraction whose only populated
        # field is the canonical URL must be rejected: canonical presence
        # is not product validity (docs/63 risk line, docs/66 section 1).
        extract = {
            "Marker": [],
            "Title": [],
            "Code": [],
            "URLs": [DVD_URL_234],
            "Image": [],
        }
        valid, reasons = product_validity(extract, DVD_URL_234)
        assert not valid
        assert any("marker" in r for r in reasons)
        assert any("Title" in r for r in reasons)
        assert any("Code" in r for r in reasons)


# --------------------------------------------------------------------------
# B-07 — Clips regression preservation (production, independent of the
# shared test_bravo_clips.py so F can diff the two at integration).
# --------------------------------------------------------------------------

class TestClipsRegressionContract:
    def test_clip_selectors_unchanged(self):
        clip = load_production()["xPathScrapers"]["clipSceneScraper"]["scene"]
        assert clip["Title"]["selector"] == "//h1[1]"
        assert "Clip" in clip["Code"]["selector"]
        assert clip["URLs"]["selector"] == "//link[@rel='canonical']/@href"
        for field in ("Title", "Code", "Details"):
            assert "品番" not in clip[field]["selector"], field
        assert "Date" not in clip and "Studio" not in clip

    def test_production_duration_is_not_mapped(self):
        # Controller decision WS-2E-DEF01-DEFER-20261104 (PR #93 @ f4be5cf,
        # Gate B PASS under the revised scope): production Scene.Duration
        # is deliberately NOT mapped, because Stash's scrapedScene()
        # IntPtr conversion rejects the string value every XPath mapping
        # produces (R3 H4).  Asserting a Duration selector here would
        # contradict the approved baseline; restoration follows the
        # deferred spec, not this regression contract.
        clip = load_production()["xPathScrapers"]["clipSceneScraper"]["scene"]
        assert "Duration" not in clip
        assert "WS-2E-DEF01-DEFER-20261104" in BRAVO.read_text()

    def test_duration_source_evidence_preserved_independently(self):
        # The deferral removes the PRODUCTION mapping, not the source
        # evidence: the deferred spec and the source-level cases remain
        # in the tree, owned by PR #93's own tests, and the production
        # fixture manifest carries no Duration mappedExpect anymore.
        spec = ROOT / "docs" / "qa" / "PR93-DURATION-DEFERRED-SPEC.md"
        assert spec.exists()
        assert "WS-2E-DEF01-DEFER-20261104" in spec.read_text()
        assert (DVD_FIXTURE_DIR / "clip-missing-duration.html").exists()
        manifest = yaml.safe_load(
            (DVD_FIXTURE_DIR / "bravo-clips-fixtures.yml").read_text()
        )
        for case in manifest["cases"]:
            for assertion in case.get("mappedExpect", []):
                assert assertion["field"] != "Duration", case["name"]

    def test_clip_image_is_poster_only(self):
        clip = load_production()["xPathScrapers"]["clipSceneScraper"]["scene"]
        assert clip["Image"]["selector"] == "//video/@poster"

    def test_historical_fixture_digest_preserved(self):
        digest = hashlib.sha256(HISTORICAL_MANIFEST.read_bytes()).hexdigest()
        assert digest == HISTORICAL_SHA256
