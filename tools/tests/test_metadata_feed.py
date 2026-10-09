"""Synthetic contract controls; these are not live scraper evidence."""
import copy
import importlib.util
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("feed", ROOT / "tools/check_metadata_feed.py")
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)


def search_config():
    return {
        "name": "Synthetic",
        "sceneByName": {"action": "scrapeXPath", "queryURL": "https://example.org/search?q={}", "scraper": "search"},
        "sceneByQueryFragment": {"action": "scrapeXPath", "queryURL": "{url}", "scraper": "detail"},
        "xPathScrapers": {"search": {"scene": {"Title": "//h2", "URLs": "//h2/a/@href"}}},
    }


def scene():
    return {"title": "作品 阿東", "urls": ["https://example.org/product/123"],
            "date": "2024-02-29", "duration": 60,
            "studio": {"name": "BE A MODEL"},
            "performers": [{"name": "阿東", "urls": ["https://example.org/cast/1"]}],
            "tags": [{"name": "訪談"}]}


def test_search_page_must_not_be_used_as_single_identify_result():
    config = search_config()
    assert not feed.definition_errors(config)
    config["sceneByFragment"] = dict(config["sceneByName"], queryURL="https://example.org/search?q={title}")
    assert any("first candidate" in e for e in feed.definition_errors(config))
    config["sceneByFragment"]["scraper"] = "detail"
    assert any("first candidate" in e for e in feed.definition_errors(config))


@pytest.mark.parametrize("query", ["{url}", "https://example.org/search?q={query}", "https://example.org/search"])
def test_unsupported_name_placeholders(query):
    config = search_config()
    config["sceneByName"]["queryURL"] = query
    assert feed.definition_errors(config)


def test_search_requires_selection_url_and_detail_mapping():
    config = search_config()
    del config["xPathScrapers"]["search"]["scene"]["URLs"]
    del config["sceneByQueryFragment"]
    assert len(feed.definition_errors(config)) == 2


def test_script_contract_is_not_assumed_to_be_xpath():
    config = {"sceneByName": {"action": "script", "script": ["python", "example.py"]}}
    assert not feed.definition_errors(config)


def test_repository_definitions():
    for path in (ROOT / "scrapers").rglob("*.yml"):
        assert not feed.definition_errors(yaml.safe_load(path.read_text(encoding="utf-8"))), path


def test_source_language_and_optional_unknown_fields_preserved():
    row = scene()
    row.update(date=None, duration=None, image=None)
    original = copy.deepcopy(row)
    assert not feed.payload_errors([row])
    assert row == original


@pytest.mark.parametrize("date", ["2025-02-29", "2026-13-01", "2026/10/10", "", 20261010])
def test_invalid_calendar_dates(date):
    row = scene()
    row["date"] = date
    assert feed.payload_errors([row])


@pytest.mark.parametrize("duration", ["60", -1, 0, True, 1.5])
def test_duration_must_be_integer_seconds(duration):
    row = scene()
    row["duration"] = duration
    assert feed.payload_errors([row])


@pytest.mark.parametrize("url", ["/product/1", "javascript:alert(1)", "https://user:secret@example.org/1", "https://example.org/{url}", "https://example.org/a b"])
def test_reject_nonportable_or_credential_urls_without_echoing(url):
    row = scene()
    row["urls"] = [url]
    errors = feed.payload_errors([row])
    assert errors and all(url not in e for e in errors)


def test_reject_duplicate_candidates_and_entities():
    row = scene()
    row["tags"] += [{"name": "訪談"}]
    assert any("duplicate name" in e for e in feed.payload_errors([row]))
    assert any("across candidates" in e for e in feed.payload_errors([scene(), scene()]))


def test_site_codes_are_not_remote_ids():
    row = scene()
    row["code"] = "LOCAL-123"
    assert not feed.payload_errors([row])
    row["studio"]["remote_site_id"] = "LOCAL-123"
    assert feed.payload_errors([row])


def test_graphql_errors_and_negative_controls():
    assert not feed.payload_errors({"data": {"scrapeSingleScene": [scene()]}})
    assert feed.payload_errors({"errors": [{"message": "secret"}], "data": {"scrapeSingleScene": [scene()]}})
    assert feed.payload_errors([])
    assert not feed.payload_errors([], allow_empty=True)
    assert feed.payload_errors({"data": {"scrapeSingleScene": None}}, allow_empty=True)


def test_cli_missing_file_fails_closed(tmp_path):
    assert feed.main([str(tmp_path / "absent.yml")]) == 1
    assert feed.main(["--payload", str(tmp_path / "absent.json")]) == 1
