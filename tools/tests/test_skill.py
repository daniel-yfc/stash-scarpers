"""Skill structure checks with dynamic reference discovery."""

from pathlib import Path

SKILL_DIR = Path("skills/stash-scraper-builder")
REFS_DIR = SKILL_DIR / "references"

CORE_REFERENCES = [
    "xpath-patterns.md",
    "json-patterns.md",
    "post-processing.md",
    "schema-checklist.md",
    "scraper.schema.json",
    "script-actions.md",
    "eval-pack.md",
]


def test_skill_md_exists():
    """測試 SKILL.md 存在"""
    assert (SKILL_DIR / "SKILL.md").exists()


def test_skill_md_has_frontmatter():
    """測試 SKILL.md 有 frontmatter"""
    content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert content.startswith("---")
    assert "name:" in content
    assert "description:" in content


def test_core_references_exist():
    """測試核心參考文件存在"""
    for ref in CORE_REFERENCES:
        assert (REFS_DIR / ref).exists(), f"缺少 {ref}"


def test_references_dir_populated():
    """參考文件目錄維持完整（動態計數，避免清單過期）"""
    md_files = list(REFS_DIR.glob("*.md"))
    assert len(md_files) >= 16, f"references/ 只有 {len(md_files)} 個 Markdown 檔案"
