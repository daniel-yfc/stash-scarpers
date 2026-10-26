"""WS-A synthetic negative controls. Never store real session material."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from scan_session_material import scan_scraper_yaml, scan_text, tracked_paths


@pytest.mark.parametrize("source,rule", [
    ("name: X\ndriver:\n  cookies:\n    - Cookies: []\n", "ACTIVE_DRIVER_COOKIES"),
    ("name: X\ndriver:\n  cookies: []\n", "ACTIVE_DRIVER_COOKIES"),
    ("name: X\ndriver:\n  cookies:\n", "ACTIVE_DRIVER_COOKIES"),
    ("name: X\ndriver:\n  headers:\n    - Key: Authorization\n      Value: fake\n", "AUTH_HEADER"),
    ("name: X\ndriver:\n  headers:\n    - Key: Cookie\n      Value: fake\n", "AUTH_HEADER"),
    ("name: X\napi_key: fake-value\n", "CREDENTIAL_FIELD"),
    ("name: [invalid\n", "YAML_PARSE_FAILED"),
])
def test_structural_rejection(source, rule):
    assert rule in scan_scraper_yaml(source)


def test_comment_only_placement_allowed(tmp_path):
    scrapers = tmp_path / "scrapers"
    scrapers.mkdir()
    path = scrapers / "Example.yml"
    path.write_text('name: X\ndriver:\n  useCDP: true\n# cookies:\n#   - Cookies:\n#       - Name: X\n#         Value: "<LOCAL_ONLY_VALUE>"\n')
    assert scan_text(path, tmp_path) == set()


def test_non_placeholder_comment_block_rejected(tmp_path):
    scrapers = tmp_path / "scrapers" / "private"
    scrapers.mkdir(parents=True)
    path = scrapers / "Test.yml"
    path.write_text('name: Test\n# cookies:\n#   - Cookies:\n#       - Name: X\n#         Value: "synthetic_session_value"\n')
    assert "NON_PLACEHOLDER_COOKIE_TEMPLATE" in scan_text(path, tmp_path)


def test_nested_private_not_exempt(tmp_path):
    scrapers = tmp_path / "scrapers" / "private"
    scrapers.mkdir(parents=True)
    path = scrapers / "Test.yml"
    path.write_text('name: Test\ndriver:\n  cookies: {}\n')
    assert "ACTIVE_DRIVER_COOKIES" in scan_text(path, tmp_path)


def test_symlink_fail_closed(tmp_path):
    p = tmp_path / "link.yml"
    p.symlink_to(tmp_path / "nonexistent")
    assert "SYMLINK_NOT_INSPECTED" in scan_text(p, tmp_path)


def test_missing_git_inventory_fails_closed(tmp_path):
    with pytest.raises(RuntimeError):
        tracked_paths(tmp_path)


def test_scrutiny_rejects_cli_cookie_without_echo():
    process = subprocess.run(
        ["node", "tools/scrutiny.js", "--cookie=SYNTHETIC_VALUE_NEVER_A_REAL_COOKIE"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert process.returncode != 0
    combined = process.stdout + process.stderr
    assert "CLI_COOKIE_FORBIDDEN" in combined
    assert "SYNTHETIC_VALUE_NEVER_A_REAL_COOKIE" not in combined


def test_scrutiny_help_preserves_environment_option():
    process = subprocess.run(["node", "tools/scrutiny.js", "--help"], cwd=ROOT, capture_output=True, text=True)
    assert process.returncode == 0
    assert "SCRUTINY_COOKIE" in process.stdout
