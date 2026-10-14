"""Unit tests for tools/check_scraper_docs.py."""

from pathlib import Path

import pytest

from tools import check_scraper_docs


def test_full_yaml_blocks_single_block(tmp_path: Path):
    """Extract single YAML block from markdown."""
    md_file = tmp_path / "test.md"
    content = (
        "# Title\n\n"
        "```yaml\n"
        "name: test_scraper\n"
        "sceneByURL:\n"
        "  - action: scrape\n"
        "```\n"
    )
    md_file.write_text(content, encoding="utf-8")
    blocks = check_scraper_docs.full_yaml_blocks(md_file)
    assert len(blocks) == 1
    assert blocks[0] == "name: test_scraper\nsceneByURL:\n  - action: scrape\n"


def test_full_yaml_blocks_multiple_blocks(tmp_path: Path):
    """Extract multiple YAML blocks from markdown."""
    md_file = tmp_path / "test.md"
    content = (
        "```yaml\n"
        "block1: true\n"
        "```\n\n"
        "Some text\n\n"
        "```yaml\n"
        "block2: true\n"
        "```\n"
    )
    md_file.write_text(content, encoding="utf-8")
    blocks = check_scraper_docs.full_yaml_blocks(md_file)
    assert len(blocks) == 2
    assert blocks[0] == "block1: true\n"
    assert blocks[1] == "block2: true\n"


def test_full_yaml_blocks_crlf_line_endings(tmp_path: Path):
    """Extract YAML blocks with CRLF (\r\n) line endings."""
    md_file = tmp_path / "test.md"
    content = (
        "```yaml\r\n"
        "name: crlf_test\r\n"
        "sceneByName:\r\n"
        "  - action: scrape\r\n"
        "```\r\n"
    )
    md_file.write_bytes(content.encode("utf-8"))
    blocks = check_scraper_docs.full_yaml_blocks(md_file)
    assert len(blocks) == 1
    assert "name: crlf_test" in blocks[0]


def test_full_yaml_blocks_no_yaml_blocks(tmp_path: Path):
    """Return empty list when no yaml blocks are present."""
    md_file = tmp_path / "test.md"
    content = (
        "# Heading\n\n"
        "```python\n"
        "print('hello')\n"
        "```\n\n"
        "```json\n"
        '{"key": "value"}\n'
        "```\n"
    )
    md_file.write_text(content, encoding="utf-8")
    blocks = check_scraper_docs.full_yaml_blocks(md_file)
    assert blocks == []


def test_full_yaml_blocks_empty_yaml_block(tmp_path: Path):
    """Extract empty YAML code block."""
    md_file = tmp_path / "test.md"
    content = "```yaml\n```\n"
    md_file.write_text(content, encoding="utf-8")
    blocks = check_scraper_docs.full_yaml_blocks(md_file)
    assert len(blocks) == 1
    assert blocks[0] == ""


def test_has_mapping():
    """Test mapping identification helper."""
    assert check_scraper_docs.has_mapping({"name": "test", "sceneByURL": []}) is True
    assert check_scraper_docs.has_mapping({"name": "test", "performerByName": []}) is True
    assert check_scraper_docs.has_mapping({"name": "test", "movieByFragment": []}) is True
    assert check_scraper_docs.has_mapping({"name": "test", "galleryByQueryFragment": []}) is True
    assert check_scraper_docs.has_mapping({"name": "test"}) is False
    assert check_scraper_docs.has_mapping(["not", "a", "dict"]) is False
    assert check_scraper_docs.has_mapping(None) is False
