"""Catch destructive documentation rewrites without enforcing prose wording."""

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = {
    "docs/02_Quality_Gate_Overview.md": (
        "## 技術檢核原則", "## 驗證層級", "## CI 工作流", "## 狀態追蹤",
        "python tools/check_scraper_docs.py", "python tools/check_docs_index.py",
        "LIVE_TEST_STATUS.md", "07_Rendered_DOM_Fixture_Testing.md",
    ),
    "docs/05_CI_Workflows.md": (
        "validate.yml", "pr-check.yml", "scrutiny.yml", "eval.yml",
        "link-check.yml", "cdp-evidence-gate.yml", "npm ci",
        "tools/verify-scraper-fixtures.mjs", "tools/check_docs_index.py",
    ),
    "docs/repository-documentation-architecture.md": (
        "## Ownership model", "## Document identity and numbering",
        "## Naming rules", "## Metadata rules", "## Indexing rules",
        "## Agent routing", "## Formatter policy",
        "## Canonical command policy", "## Cross-level linking rules",
        "## Review checklist", "UPSTREAM_SOURCES.md",
        "07_Rendered_DOM_Fixture_Testing.md",
    ),
}


def missing(text, markers):
    return [marker for marker in markers if marker not in text]


def test_critical_docs_preserve_owned_sections():
    for relative, markers in REQUIRED.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert not missing(text, markers), f"{relative} missing: {missing(text, markers)}"


def test_human_and_machine_routes_agree():
    index = yaml.safe_load((ROOT / "docs/index.yml").read_text(encoding="utf-8"))
    entries = {item["doc_id"]: item["path"] for item in index["documents"]}
    target = "docs/07_Rendered_DOM_Fixture_Testing.md"
    assert entries["DOC-TEST-51"] == target
    assert "07_Rendered_DOM_Fixture_Testing.md" in (ROOT / "docs/README.md").read_text(encoding="utf-8")
    document = (ROOT / target).read_text(encoding="utf-8")
    assert document.startswith("---\n")
    assert "doc_id: DOC-TEST-51" in document


def test_truncated_content_is_detected():
    for markers in REQUIRED.values():
        assert missing("# Brief summary\n", markers)
    assert "## Formatter policy" in missing("## Ownership model\n", REQUIRED["docs/repository-documentation-architecture.md"])
