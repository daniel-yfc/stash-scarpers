"""Tests for docs-vs-schema alignment and scraper semantics checkers."""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent


def run_checker(script, *args):
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / script), *args],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    return result


def test_docs_official_passes():
    """check_docs_official.py passes on the current repo state."""
    result = run_checker("check_docs_official.py")
    assert result.returncode == 0, f"Docs-vs-schema check failed:\n{result.stdout}"


def test_semantics_passes_on_repo():
    """check_scraper_semantics.py passes on all committed scrapers."""
    result = run_checker("check_scraper_semantics.py")
    assert result.returncode == 0, f"Semantics check failed:\n{result.stdout}"


def test_semantics_catches_bad_gender():
    """Invalid Gender fixed value is rejected."""
    bad = {
        "name": "Bad",
        "sceneByURL": [{"action": "scrapeXPath", "url": ["x.com"], "scraper": "s"}],
        "xPathScrapers": {"s": {"performer": {"Gender": {"fixed": "Unknown"}}}},
    }
    with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False) as f:
        yaml.safe_dump(bad, f)
        path = f.name
    try:
        result = run_checker("check_scraper_semantics.py", path)
        assert result.returncode == 1
        assert "Gender" in result.stdout
    finally:
        Path(path).unlink()


def test_semantics_catches_bad_parse_date():
    """Non-Go parseDate layout is rejected."""
    bad = {
        "name": "Bad",
        "sceneByURL": [{"action": "scrapeXPath", "url": ["x.com"], "scraper": "s"}],
        "xPathScrapers": {
            "s": {
                "scene": {
                    "Date": {
                        "selector": "//x",
                        "postProcess": [{"parseDate": "yyyy-MM-dd"}],
                    }
                }
            }
        },
    }
    with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False) as f:
        yaml.safe_dump(bad, f)
        path = f.name
    try:
        result = run_checker("check_scraper_semantics.py", path)
        assert result.returncode == 1
        assert "parseDate" in result.stdout
    finally:
        Path(path).unlink()


def test_semantics_warns_movie_by_url():
    """movieByURL triggers a deprecation warning but not a failure."""
    bad = {
        "name": "Bad",
        "movieByURL": [{"action": "scrapeXPath", "url": ["x.com"], "scraper": "s"}],
        "xPathScrapers": {"s": {"scene": {"Title": {"selector": "//h1"}}}},
    }
    with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False) as f:
        yaml.safe_dump(bad, f)
        path = f.name
    try:
        result = run_checker("check_scraper_semantics.py", path)
        assert result.returncode == 0  # warning only
        assert "movieByURL" in result.stdout
        assert "WARNING" in result.stdout
    finally:
        Path(path).unlink()


def test_semantics_accepts_valid_gender_map():
    """Valid Gender map values pass."""
    good = {
        "name": "Good",
        "sceneByURL": [{"action": "scrapeXPath", "url": ["x.com"], "scraper": "s"}],
        "xPathScrapers": {
            "s": {
                "performer": {
                    "Gender": {"map": {"男": "Male", "女": "Female"}},
                },
                "scene": {
                    "Date": {
                        "selector": "//x",
                        "postProcess": [{"parseDate": "2006-01-02"}],
                    }
                },
            }
        },
    }
    with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False) as f:
        yaml.safe_dump(good, f)
        path = f.name
    try:
        result = run_checker("check_scraper_semantics.py", path)
        assert result.returncode == 0, result.stdout
    finally:
        Path(path).unlink()
