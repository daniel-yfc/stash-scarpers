"""WS-A synthetic negative controls. Never store real session material."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from scan_session_material import (
    cookie_header_is_replayable,
    is_netscape_cookie_record,
    scan_json_lexical_fallback,
    scan_json_structure,
    scan_scraper_yaml,
    scan_text,
    tracked_paths,
)


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


# Independent QA-02/03/04 regressions. The following strings are all synthetic,
# built only inside tmp_path to avoid committing replayable-looking fixtures.
@pytest.mark.parametrize("extension", [".yml", ".yaml", ".YAML", ".Yml"])
@pytest.mark.parametrize("block", [
    "driver:\n  cookies: []\n",
    "driver:\n  cookies:\n    - CookieURL: example.invalid\n",
    "driver:\n  nested:\n    cookies: {}\n",
    "driver:\n  nested:\n    - CookieURL: example.invalid\n",
])
def test_every_scraper_yaml_extension_rejects_active_cookie_mapping(tmp_path, extension, block):
    root = tmp_path / "scrapers" / "private"
    root.mkdir(parents=True)
    path = root / ("Probe" + extension)
    path.write_text("name: Probe\n" + block, encoding="utf-8")
    findings = scan_text(path, tmp_path)
    assert "ACTIVE_COOKIE_FIELD" in findings or "ACTIVE_DRIVER_COOKIES" in findings


@pytest.mark.parametrize("extension", [".yaml", ".YAML", ".Yml", ".yml"])
def test_cookie_comment_value_requires_exact_placeholder_for_yaml_extensions(tmp_path, extension):
    root = tmp_path / "scrapers"
    root.mkdir()
    path = root / ("Probe" + extension)
    path.write_text(
        "name: Probe\n# cookies:\n# - Name: Test\n#   Value: " +
        '"synthetic_' + "X" * 24 + '"\n',
        encoding="utf-8",
    )
    assert "NON_PLACEHOLDER_COOKIE_TEMPLATE" in scan_text(path, tmp_path)
    path.write_text('name: Probe\n# Value: "<LOCAL_ONLY_VALUE>"\n', encoding="utf-8")
    assert scan_text(path, tmp_path) == set()


@pytest.mark.parametrize("extension", [".md", ".js", ".yml", ".html", ".unknown"])
def test_nul_payload_cannot_smuggle_credentials(tmp_path, extension):
    p = tmp_path / ("probe" + extension)
    p.write_bytes(b"\x00" + b"Cookie" + b": " + b"X" * 25)
    assert "BINARY_CONTENT_NOT_INSPECTED" in scan_text(p, tmp_path)


@pytest.mark.parametrize("extension", [".md", ".js", ".yml", ".py", ".sh"])
@pytest.mark.parametrize("encoding", ["utf-16-le", "utf-16-be", "utf-16", "latin-1"])
def test_non_utf8_text_never_silently_passes(tmp_path, extension, encoding):
    p = tmp_path / ("probe" + extension)
    p.write_bytes(("Authorization" + ": Basic " + "X" * 24 + "é").encode(encoding))
    assert scan_text(p, tmp_path) & {
        "BINARY_CONTENT_NOT_INSPECTED", "TEXT_DECODE_FAILED",
        "REPLAYABLE_AUTH_ASSIGNMENT",
    }


@pytest.mark.parametrize("scheme", ["Basic", "Token", "Digest", "Bearer"])
def test_non_bearer_header_schemes_detected(tmp_path, scheme):
    p = tmp_path / "probe.txt"
    p.write_text("Authorization" + ": " + scheme + " " + "X" * 25, encoding="utf-8")
    assert "REPLAYABLE_AUTH_ASSIGNMENT" in scan_text(p, tmp_path)


@pytest.mark.parametrize("key", ["password", "passwd", "authorization", "Cookie"])
def test_generic_text_auth_field_detected(tmp_path, key):
    p = tmp_path / "probe.txt"
    p.write_text(key + ": " + "X" * 25, encoding="utf-8")
    assert "REPLAYABLE_AUTH_ASSIGNMENT" in scan_text(p, tmp_path)


def test_multiple_auth_assignments_on_one_line_cannot_hide_second(tmp_path):
    p = tmp_path / "probe.js"
    p.write_text(
        "cookie" + ": process.env.SCRUTINY_COOKIE; " +
        "Authorization" + ": Token " + "X" * 25, encoding="utf-8",
    )
    assert "REPLAYABLE_AUTH_ASSIGNMENT" in scan_text(p, tmp_path)


def test_oversized_tracked_text_is_not_silently_skipped(tmp_path, monkeypatch):
    from scan_session_material import MAX_FILE_BYTES
    p = tmp_path / "probe.dat"
    p.write_bytes(b"X" * (MAX_FILE_BYTES + 1))
    assert "FILE_TOO_LARGE_NOT_INSPECTED" in scan_text(p, tmp_path)


def test_scraper_set_cookie_header_rejected():
    source = (
        "name: Probe\n"
        "driver:\n"
        "  headers:\n"
        "    - Key: Set-" + "Cookie\n"
        "      Value: " + "synthetic" + "_only\n"
    )
    assert "AUTH_HEADER" in scan_scraper_yaml(source)


def test_password_with_special_punctuation_not_missed(tmp_path):
    path = tmp_path / "test.txt"
    # Compose the probe rather than storing a password-shaped literal.
    path.write_text("pass" + "word: " + "Ab7" + "!@#$" + "gH19K9", encoding="utf-8")
    assert "REPLAYABLE_AUTH_ASSIGNMENT" in scan_text(path, tmp_path)


def test_cyclic_yaml_alias_does_not_bypass_cookie_check():
    source = (
        "name: Probe\n"
        "data: &ref\n"
        "  cookies: []\n"
        "  self: *ref\n"
    )
    assert "ACTIVE_COOKIE_FIELD" in scan_scraper_yaml(source)


# --- QA-17 remediation (IMPL-WS-A-QA17-20261029-01) -------------------------
# All values below are synthetic and assembled at runtime so this tracked
# test file never itself contains replayable-shaped material.

SYNTH_VALUE = "SYNTH" + "ETIC" + "_VALUE_" + "0123456789"


def _netscape_record(domain=".example.com", sub="TRUE", path="/", secure="FALSE",
                      expiry="1893456000", name="sessionid", value=SYNTH_VALUE,
                      prefix=""):
    return prefix + "\t".join([domain, sub, path, secure, expiry, name, value])


def _run_production_scanner(tmp_path, files):
    """Production-boundary harness: tracked fixture in a real tmp Git repo,
    scanned by the real scanner CLI. Returns the CompletedProcess."""
    root = tmp_path / "repo"
    root.mkdir()
    for rel, content in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content.encode("utf-8"))
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "scan_session_material.py"),
         "--root", str(root)],
        capture_output=True, text=True,
    )


# F01 — raw Netscape cookie-file records
@pytest.mark.parametrize("record", [
    _netscape_record(),
    _netscape_record(prefix="#HttpOnly_"),
    _netscape_record(prefix="#httponly_"),
    _netscape_record(sub="true", secure="False"),
    _netscape_record(expiry="0"),
    _netscape_record(domain="sub.example.co.jp", name="ECSESSID"),
    "  " + _netscape_record() + "  ",
])
def test_netscape_record_unit_positive(record):
    assert is_netscape_cookie_record(record)


@pytest.mark.parametrize("line", [
    "",
    "# Netscape HTTP Cookie File",
    "# " + _netscape_record(),                      # commented-out record
    "\t".join(["name", "count", "city", "score", "note", "grade", "comment"]),
    "\t".join(["example.com", "12", "/", "9", "123", "name", "value"]),
    "\t".join([".example.com", "TRUE", "/", "FALSE", "1893456000", "sid"]),  # 6 fields
    _netscape_record(expiry="not-a-number"),
    _netscape_record(path="relative"),
    _netscape_record(value=""),
    _netscape_record(value="<LOCAL_ONLY_VALUE>"),
    _netscape_record().replace("\t", " "),           # space-separated is not Netscape
])
def test_netscape_record_unit_benign(line):
    assert not is_netscape_cookie_record(line)


def test_netscape_record_crlf_and_any_filename(tmp_path):
    target = tmp_path / "export-data.txt"
    target.write_bytes((_netscape_record() + "\r\n").encode("utf-8"))
    assert "NETSCAPE_COOKIE_RECORD" in scan_text(target, tmp_path)


def test_netscape_cli_tracked_file_rejected_without_value_echo(tmp_path):
    process = _run_production_scanner(tmp_path, {"cookies.txt": _netscape_record() + "\n"})
    assert process.returncode == 1
    assert "NETSCAPE_COOKIE_RECORD: cookies.txt" in process.stdout
    assert SYNTH_VALUE not in process.stdout + process.stderr


def test_netscape_cli_arbitrary_filename_not_a_whitelist(tmp_path):
    process = _run_production_scanner(
        tmp_path, {"notes/readme.md": "intro\n" + _netscape_record() + "\n"})
    assert process.returncode == 1
    assert "NETSCAPE_COOKIE_RECORD" in process.stdout
    assert SYNTH_VALUE not in process.stdout + process.stderr


def test_netscape_cli_benign_tsv_and_comments_pass(tmp_path):
    content = (
        "# Netscape HTTP Cookie File\n"
        "# " + _netscape_record() + "\n"
        + "\t".join(["name", "count", "city", "score", "note", "grade", "comment"]) + "\n"
        + _netscape_record(value="<LOCAL_ONLY_VALUE>") + "\n"
    )
    process = _run_production_scanner(tmp_path, {"data.tsv": content})
    assert process.returncode == 0, process.stdout


# F02 — punctuated Cookie / Set-Cookie header values
@pytest.mark.parametrize("line", [
    "Cook" + "ie: " + "!".join(["aaa", "bbb", "ccc", "ddd", "eee"]),
    "Cook" + "ie: " + "@".join(["aaa", "bbb", "ccc", "ddd"]),
    "Set-Cook" + "ie: sess=" + "!".join(["aa", "bb", "cc", "dd"]) + "; Path=/",
    "Cook" + "ie: a=aa!bb; b=cc!dd",
    "Cook" + "ie: " + "tok" + "%".join(["111", "222", "333", "444"]),
])
def test_punctuated_cookie_header_unit_positive(line):
    assert cookie_header_is_replayable(line)


@pytest.mark.parametrize("line", [
    "Cook" + "ie: <LOCAL_ONLY_VALUE>",
    "Cook" + "ie: session=<LOCAL_ONLY_VALUE>",
    "Cook" + "ie: process.env.SCRUTINY_COOKIE",
    "Set-Cook" + "ie: session=<LOCAL_ONLY_VALUE>; Expires=Wed, 21 Oct 2099 07:28:00 GMT; Path=/",
    "- cook" + "ie: NOT SUPPORTED (use SCRUTINY_COOKIE environment variable)",
    "Cook" + "ie: a=b",
])
def test_punctuated_cookie_header_unit_benign(line):
    assert not cookie_header_is_replayable(line)


def test_punctuated_cookie_header_scan_text(tmp_path):
    target = tmp_path / "note.txt"
    target.write_text("Cook" + "ie: " + "!".join(["aaa", "bbb", "ccc", "ddd"]) + "\n", encoding="utf-8")
    assert "REPLAYABLE_AUTH_ASSIGNMENT" in scan_text(target, tmp_path)


def test_punctuated_cookie_cli_rejected_without_value_echo(tmp_path):
    secret = "!".join(["zz9", "yy8", "xx7", "ww6", "vv5"])
    process = _run_production_scanner(tmp_path, {"note.txt": "Cook" + "ie: " + secret + "\n"})
    assert process.returncode == 1
    assert "REPLAYABLE_AUTH_ASSIGNMENT: note.txt" in process.stdout
    assert secret not in process.stdout + process.stderr


def test_cookie_placeholder_pair_cli_passes(tmp_path):
    process = _run_production_scanner(
        tmp_path, {"note.txt": "Cook" + "ie: session=<LOCAL_ONLY_VALUE>\n"})
    assert process.returncode == 0, process.stdout


# F03 — JSON unicode-escaped credential keys
ESC = chr(92) + "u"  # backslash-u, assembled so this file holds no escaped key


@pytest.mark.parametrize("source,rule", [
    ('{"Cook' + ESC + '0069e": "abc!def!ghi"}', "ACTIVE_COOKIE_FIELD"),
    ('{"pass' + ESC + '0077ord": "abc!def!ghi"}', "CREDENTIAL_FIELD"),
    ('{"outer": [{"Cook' + ESC + '0069e": "x"}]}', "ACTIVE_COOKIE_FIELD"),
    ('{"CoOk' + ESC + '0069E": "abc!def!ghi"}', "ACTIVE_COOKIE_FIELD"),
    ('{"api' + ESC + '005fkey": "abc!def!ghi"}', "CREDENTIAL_FIELD"),
])
def test_json_escaped_key_unit_positive(source, rule):
    assert rule in scan_json_structure(source)


@pytest.mark.parametrize("source", [
    '{"name": "example", "theme": "dark"}',
    '{"$schema": "https://json-schema.org/draft/2020-12/schema",'
    ' "definitions": {"cookie": {"type": "object"}},'
    ' "properties": {"password": {"type": "string"}, "cookies": {"type": "array"}}}',
    '{"password_hint": "shown on screen"}',
    'not json at all',
])
def test_json_structure_unit_benign(source):
    assert scan_json_structure(source) == set()


def test_json_escaped_key_cli_rejected_without_value_echo(tmp_path):
    payload = '{"Cook' + ESC + '0069e": "' + "abc!def!ghi!jkl" + '"}'
    process = _run_production_scanner(tmp_path, {"data.json": payload})
    assert process.returncode == 1
    assert "data.json" in process.stdout
    assert "abc!def!ghi!jkl" not in process.stdout + process.stderr


def test_json_malformed_with_escaped_key_still_rejected_cli(tmp_path):
    # Trailing comma: json.loads fails, the normalised pattern scan must
    # still see the escaped key — a parse failure is never a clean result.
    payload = '{"pass' + ESC + '0077ord": "' + "abc!def!ghi!jkl" + '",}'
    process = _run_production_scanner(tmp_path, {"data.json": payload})
    assert process.returncode == 1
    assert "abc!def!ghi!jkl" not in process.stdout + process.stderr


def test_json_benign_cli_passes(tmp_path):
    process = _run_production_scanner(
        tmp_path, {"data.json": '{"name": "example", "theme": "dark"}'})
    assert process.returncode == 0, process.stdout


# QA-18 — malformed JSON must not fail open for short values: when
# json.loads rejects the document, the lexical pair fallback applies the
# same field policy as the parsed walk (any non-empty value counts).
@pytest.mark.parametrize("source,rule", [
    ('{"pass' + ESC + '0077ord": "abc",}', "CREDENTIAL_FIELD"),
    ('{"Cook' + ESC + '0069e": "abc",}', "ACTIVE_COOKIE_FIELD"),
    ('{"password": "abc",}', "CREDENTIAL_FIELD"),
    ('{"pass' + ESC + '0077ord": 1234,}', "CREDENTIAL_FIELD"),
    ('{"outer": {"pass' + ESC + '0077ord": "xy",},}', "CREDENTIAL_FIELD"),
    ('{"password": "abc', "CREDENTIAL_FIELD"),
    ('{"cookie": "",}', "ACTIVE_COOKIE_FIELD"),
])
def test_json_lexical_fallback_unit_positive(source, rule):
    assert rule in scan_json_lexical_fallback(source)


@pytest.mark.parametrize("source", [
    '{"name": "example",}',
    '{"password": null,}',
    '{"password": "",}',
    '{"password": "<LOCAL_ONLY_VALUE>",}',
    '{"password_hint": "abc",}',
    '{"theme": "dark", "count": 3,}',
])
def test_json_lexical_fallback_unit_benign(source):
    assert scan_json_lexical_fallback(source) == set()


@pytest.mark.parametrize("payload", [
    '{"pass' + ESC + '0077ord": "abc",}',
    '{"Cook' + ESC + '0069e": "abc",}',
    '{"outer": {"pass' + ESC + '0077ord": "xy",},}',
    '{"password": "abc",}',
])
def test_json_malformed_short_value_rejected_cli(tmp_path, payload):
    process = _run_production_scanner(tmp_path, {"data.json": payload})
    assert process.returncode == 1


def test_json_malformed_benign_cli_passes(tmp_path):
    process = _run_production_scanner(tmp_path, {"data.json": '{"name": "x",}'})
    assert process.returncode == 0, process.stdout


def test_scan_text_routes_unparseable_json_to_fallback(tmp_path):
    path = tmp_path / "data.json"
    path.write_text('{"password": "abc",}', encoding="utf-8")
    assert "CREDENTIAL_FIELD" in scan_text(path, tmp_path)


# QA-19 — malformed JSON whose sensitive value is a container (object or
# array, including truncated/unclosed) must not fail open either: a
# non-empty container under a sensitive key is flagged by key, mirroring
# the parsed walk; empty containers stay clean, as in the parsed walk.
@pytest.mark.parametrize("source,rule", [
    ('{"password": {"value": "abc"},}', "CREDENTIAL_FIELD"),
    ('{"password": ["abc"],}', "CREDENTIAL_FIELD"),
    ('{"password": {"token": "abc"},}', "CREDENTIAL_FIELD"),
    ('{"cookie": {"name": "session", "value": "abc"},}', "ACTIVE_COOKIE_FIELD"),
    ('{"cookies": {},}', "ACTIVE_COOKIE_FIELD"),
    ('{"authorization": ["Bearer abc"],}', "CREDENTIAL_FIELD"),
    ('{"password": {"a": {"b": "abc"}},}', "CREDENTIAL_FIELD"),
    ('{"password": {"value": "abc"', "CREDENTIAL_FIELD"),
    ('{"password": ["abc"', "CREDENTIAL_FIELD"),
    ('{"pass' + ESC + '0077ord": {"value": "abc"},}', "CREDENTIAL_FIELD"),
])
def test_json_lexical_container_unit_positive(source, rule):
    assert rule in scan_json_lexical_fallback(source)


@pytest.mark.parametrize("source", [
    '{"password": {},}',
    '{"password": [],}',
    '{"password": { },}',
    '{"password": [',
    '{"theme": {"mode": "dark"},}',
    '{"auth": {"user": "bob", "pass": "abc"},}',
])
def test_json_lexical_container_unit_benign(source):
    assert scan_json_lexical_fallback(source) == set()


@pytest.mark.parametrize("payload", [
    '{"password": {"value": "abc"},}',
    '{"password": ["abc"],}',
    '{"cookie": {"name": "session", "value": "abc"},}',
])
def test_json_malformed_container_rejected_cli(tmp_path, payload):
    process = _run_production_scanner(tmp_path, {"data.json": payload})
    assert process.returncode == 1


@pytest.mark.parametrize("payload", [
    '{"theme": {"mode": "dark"},}',
    '{"password": {},}',
])
def test_json_malformed_container_benign_cli_passes(tmp_path, payload):
    process = _run_production_scanner(tmp_path, {"data.json": payload})
    assert process.returncode == 0, process.stdout


# F04 — driver header key case variants
@pytest.mark.parametrize("field", ["key", "Key", "KEY", "kEy"])
def test_driver_header_key_case_variants(field):
    source = (
        "name: Probe\ndriver:\n  headers:\n    - " + field + ": Authorization\n"
        "      value: synthetic_only\n"
    )
    assert "AUTH_HEADER" in scan_scraper_yaml(source)


def test_driver_header_lowercase_key_cli_rejected_without_echo(tmp_path):
    source = (
        "name: Probe\ndriver:\n  headers:\n    - key: Cook" + "ie\n"
        "      value: " + SYNTH_VALUE + "\n"
    )
    process = _run_production_scanner(tmp_path, {"scrapers/Probe.yml": source})
    assert process.returncode == 1
    assert "AUTH_HEADER: scrapers/Probe.yml" in process.stdout
    assert SYNTH_VALUE not in process.stdout + process.stderr


@pytest.mark.parametrize("source", [
    "name: Probe\nitems:\n  - key: Authorization\n    value: dark\n",   # not driver.headers
    "name: Probe\ndriver:\n  headers:\n    - key: X-Custom-Header\n      value: dark\n",
    "name: Probe\ndriver:\n  headers:\n    - Key: Content-Type\n      Value: text/html\n",
])
def test_driver_header_key_benign_controls(source):
    assert "AUTH_HEADER" not in scan_scraper_yaml(source)


# QA-02/03 preservation spot checks alongside the QA-17 changes
def test_qa02_yaml_extension_and_qa03_nul_still_fail_closed(tmp_path):
    root = tmp_path / "scrapers"
    root.mkdir()
    path = root / "Probe.YAML"
    path.write_text("name: Probe\ndriver:\n  cookies: []\n", encoding="utf-8")
    assert "ACTIVE_DRIVER_COOKIES" in scan_text(path, tmp_path)
    binary = tmp_path / "probe.md"
    binary.write_bytes(b"\x00" + b"Cook" + b"ie: " + b"X" * 25)
    assert "BINARY_CONTENT_NOT_INSPECTED" in scan_text(binary, tmp_path)
