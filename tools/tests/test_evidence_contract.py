from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_evidence_contract import STAGES, validate


def blank():
    return {"scraper": "scrapers/private/example.yml", "states": {key: {"status": "unverified"} for key in STAGES}}


def test_unverified_stages_are_accepted(tmp_path):
    assert validate(blank(), tmp_path) == []


def test_verified_requires_artifact_and_provenance(tmp_path):
    record = blank()
    record["states"]["fixture"] = {"status": "verified"}
    assert any("incomplete provenance" in error for error in validate(record, tmp_path))


def test_unsafe_artifact_and_unverified_overclaim_fail(tmp_path):
    record = blank()
    record["states"]["live_cdp"] = {"status": "unverified", "artifact": "missing.txt"}
    assert any("must not carry" in error for error in validate(record, tmp_path))
    record["states"]["live_cdp"] = {
        "status": "verified", "artifact": "../outside.txt", "sha256": "0" * 64,
        "captured_at": "2026-10-01T00:00:00Z", "source_url": "https://example.invalid/",
        "revision": "0" * 40,
    }
    assert any("unsafe artifact" in error for error in validate(record, tmp_path))
