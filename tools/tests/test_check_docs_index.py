"""Unit tests for tools/check_docs_index.py frontmatter error paths."""

import yaml

from tools import check_docs_index


def test_frontmatter_yaml_error_raised(tmp_path, monkeypatch):
    """Test frontmatter extraction when yaml.safe_load raises yaml.YAMLError."""
    md_file = tmp_path / "doc.md"
    md_file.write_text("---\nkey: value\n---\n", encoding="utf-8")

    def mock_safe_load(stream):
        raise yaml.YAMLError("Simulated YAML parsing error")

    monkeypatch.setattr(yaml, "safe_load", mock_safe_load)
    assert check_docs_index.frontmatter(md_file) == {}
