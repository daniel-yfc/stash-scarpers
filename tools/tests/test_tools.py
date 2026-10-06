"""Smoke tests for the consolidated tools/ directory."""

import subprocess
from pathlib import Path

# 已移除：build-site.sh, clean.sh, install.sh, test.sh
TOOL_SCRIPTS = [
    "tools/scraper-quality-gate.sh",
    "tools/validate-all.sh",
]

TOOL_FILES = TOOL_SCRIPTS + [
    "tools/check_scraper_docs.py",
    "tools/scrutiny.js",
    "tools/README.md",
]


def test_tool_files_exist():
    """所有工具檔案存在"""
    for path in TOOL_FILES:
        assert Path(path).is_file(), f"缺少 {path}"


def test_shell_scripts_syntax():
    """Shell 腳本通過 bash -n 語法檢查"""
    for script in TOOL_SCRIPTS:
        result = subprocess.run(["bash", "-n", script], capture_output=True, text=True)
        assert result.returncode == 0, f"{script} 語法錯誤：{result.stderr}"


def test_scrutiny_cli_help():
    """scrutiny.js CLI 正常支援 --help"""
    result = subprocess.run(["node", "tools/scrutiny.js", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Usage: node tools/scrutiny.js" in result.stdout