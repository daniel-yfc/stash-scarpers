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

@pytest.mark.parametrize("extension,kind", [
    (".md", "Authorization"),
    (".js", "Cookie"),
    (".html", "Set-Cookie"),
    ("", "api_key"),
    (".txt", "PHPSESSID"),
])
def test_session_material_in_any_tracked_text_type_is_detected(tmp_path, extension, kind):
    # Synthesize non-replayable values at runtime; the repository stores
    # neither real credentials nor a contiguous credential-shaped fixture.
    target = tmp_path / ("sample" + extension)
    payload = kind + ": " + ("X" * 24)
    target.write_text(payload, encoding="utf-8")
    assert "REPLAYABLE_AUTH_ASSIGNMENT" in scan_text(target, tmp_path)


def test_even_commented_markdown_auth_line_rejected(tmp_path):
    target = tmp_path / "readme.md"
    target.write_text("# " + "Authorization: Bearer " + ("Z" * 24), encoding="utf-8")
    assert "REPLAYABLE_AUTH_ASSIGNMENT" in scan_text(target, tmp_path)


def test_synthetic_json_cookie_assignment_rejected(tmp_path):
    target = tmp_path / "sample.json"
    target.write_text('{"' + "Cookie" + '": "' + "sessionid=" + "V" * 24 + '"}', encoding="utf-8")
    assert "REPLAYABLE_AUTH_ASSIGNMENT" in scan_text(target, tmp_path)


def test_safe_placeholder_in_markdown_allowed(tmp_path):
    target = tmp_path / "safe.md"
    target.write_text("Authorization: <LOCAL_ONLY_VALUE>", encoding="utf-8")
    assert scan_text(target, tmp_path) == set()

def test_code_reference_is_not_replayable_session_material(tmp_path):
    js = tmp_path / "script.js"
    js.write_text("const opts = { " + "cookie" + ": process.env.SCRUTINY_COOKIE };", encoding="utf-8")
    assert "REPLAYABLE_AUTH_ASSIGNMENT" not in scan_text(js, tmp_path)
    html = tmp_path / "page.html"
    html.write_text("<script>const obj = {" + "session" + "Id: window.location.href};</script>", encoding="utf-8")
    assert "REPLAYABLE_AUTH_ASSIGNMENT" not in scan_text(html, tmp_path)


def test_quoted_session_id_is_still_rejected(tmp_path):
    html = tmp_path / "page.html"
    html.write_text('{"' + "sessionId" + '": "' + "x" * 36 + '"}', encoding="utf-8")
    assert "REPLAYABLE_AUTH_ASSIGNMENT" in scan_text(html, tmp_path)


def test_rendered_dom_snapshots_have_no_active_auth_material():
    for name in ("dvd-046.html", "dvd-173.html", "dvd-215.html", "dvd-281.html"):
        path = ROOT / "tests" / "fixtures" / "bravo" / name
        assert "REPLAYABLE_AUTH_ASSIGNMENT" not in scan_text(path, ROOT), name
