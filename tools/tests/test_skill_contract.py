"""WS-C deterministic contract checks (not host-level implicit trigger eval)."""
from pathlib import Path
import re
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/stash-scraper-builder/SKILL.md"
REFS = SKILL.parent / "references"

@pytest.fixture(scope="module")
def contract():
    source = SKILL.read_text(encoding="utf-8")
    assert source.startswith("---\n")
    front, body = source.split("\n---\n", 1)
    return yaml.safe_load(front[4:]), body

def test_trigger(contract):
    front, _ = contract
    assert front["name"] == SKILL.parent.name
    description = front["description"]
    assert len(description) <= 1024
    assert "Do not use" in description[:350]
    for word in ("review", "validat", "debug", "XPath", "JSON", "CDP"):
        assert word.lower() in description.lower()
    assert len(SKILL.read_text(encoding="utf-8").splitlines()) < 500

def test_only_one_skill_entry(contract):
    _, body = contract
    assert "references/skill-read-order.md" not in body
    assert not (REFS / "skill-read-order.md").exists()
    assert (ROOT / "docs/archive/skill-read-order-2026-10-27.md").exists()
    for intent in ("CREATE", "REVISE", "VALIDATE_ONLY", "DEBUG", "REVIEW_ONLY"):
        assert intent in body
    assert "no unauthorized writes" in body
    assert "never author changes" in body

def test_phase_exit_contract(contract):
    _, body = contract
    phase_ids = re.findall(r"\*\*P([0-6]) [A-Z_]+\*\*", body)
    assert phase_ids == list("0123456")
    for state in ("PASS", "FAIL", "BLOCKED", "NOT_RUN", "N/A"):
        assert state in body
    assert "SCHEMA_VALIDATED" in body
    assert "P6 DELIVERY_COMPLETE" in body
    assert "production acceptance" in body

def test_refs_exist(contract):
    _, body = contract
    paths = set(re.findall(r"references/([a-z0-9-]+\.md)", body))
    assert len(paths) >= 8
    for name in paths:
        assert (REFS / name).is_file(), name
    assert "references/eval-pack.md" not in body
    assert "references/incident-reviews.md" not in body

@pytest.mark.parametrize("path", [
    "AGENTS.md", "README.md", "readme-zh-tw.md",
    "docs/00-documentation-architecture.md", "CLAUDE.md",
    ".github/copilot-instructions.md",
])
def test_no_old_route(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    assert "references/skill-read-order.md" not in text

def test_index_and_security(contract):
    index = yaml.safe_load((ROOT / "docs/index.yml").read_text(encoding="utf-8"))
    rows = {r["doc_id"]: r for r in index["documents"]}
    assert rows["REF-CORE-00"]["status"] == "archived"
    assert rows["REF-CORE-00"]["path"] == "docs/archive/skill-read-order-2026-10-27.md"
    _, body = contract
    assert "scrapers/private/" in body
    assert "active cookies" in body
    assert "outside this Git working tree" in body
