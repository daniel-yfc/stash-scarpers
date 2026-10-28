#!/usr/bin/env python3
"""WS-A tracked-file session policy scanner. Report rule ID + path only; never values.

Git-tracked files (including scrapers/private/) have no confidentiality boundary.
This is a targeted policy check, not a substitute for a full secret-scanning service.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDERS = ("<LOCAL_ONLY_VALUE>", "<COOKIE_NAME>", "<TOKEN_PLACEHOLDER>", "<REDACTED>")
SENSITIVE_KEY = re.compile(r"^(?:cookie|authorization|proxy-authorization|x-api-key|x-auth-token|access_token|api_key|apikey|api-key|password|passwd|set-cookie|x-session-token|session_token|csrf_token|cf_clearance)$", re.I)
COOKIE_FIELD = re.compile(r"^(?:cookies?|cookieurl|cookie_url)$", re.I)
SCRAPER_EXTENSIONS = frozenset((".yml", ".yaml"))
MAX_FILE_BYTES = 16 * 1024 * 1024
COMMENT_VALUE = re.compile(r"^\s*#\s*(?:-\s*)?Value:\s*(.+?)\s*$", re.I)
HEADER_PATTERN = re.compile(r"""(?i)(?:^|[\s'"])(?:cookie|set-cookie|authorization|proxy-authorization|x-api-key|x-auth-token)(?:['"])?\s*[:=]\s*['"]?(?:(?:Bearer|Basic|Token|Digest|ApiKey)\s+)?([A-Za-z0-9_+./=%;~!\-]{8,})""")
ASSIGNMENT = re.compile(r"""(?i)\b(?:session[_-]?token|sessionid|phpsessid|cf_clearance|csrf[_-]?token|api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd)\s*['"]?\s*[:=]\s*['"]?([A-Za-z0-9_+./=~!@#$%^&*?:\-]{8,})""")
# QA-17 F02: an explicit Cookie/Set-Cookie header line is structural evidence
# on its own; a short token threshold must not be the only line of defence.
COOKIE_HEADER_LINE = re.compile(r"""(?i)^\s*(?:[-#]\s*)?['"]?(cookie|set-cookie)['"]?\s*[:=]\s*(.+?)\s*$""")
COOKIE_ATTRIBUTE_NAMES = frozenset(("path", "expires", "max-age", "domain", "samesite", "secure", "httponly", "priority", "partitioned"))
RUNTIME_REF = re.compile(r"(?:process\.env|import\.meta\.env|os\.environ)\.[A-Za-z_][A-Za-z0-9_]*")
NETSCAPE_DOMAIN = re.compile(r"^\.?[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$")
UNICODE_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})")


def tracked_paths(root: Path) -> list[Path]:
    result = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True)
    if result.returncode:
        raise RuntimeError("git-tracked inventory unavailable")
    return [root / Path(p.decode("utf-8", "surrogateescape"))
            for p in result.stdout.split(b"\x00") if p]


def is_placeholder(value: str) -> bool:
    value = value.strip().strip("'\"").strip()
    return value in PLACEHOLDERS


def is_netscape_cookie_record(line: str) -> bool:
    """QA-17 F01: structurally valid Netscape cookie-file record.

    Requires the full 7-field tab-separated shape (domain, include-subdomains
    flag, path, secure flag, numeric expiry, name, value) so ordinary TSV
    data is not misclassified. ``#HttpOnly_`` prefixes and CRLF endings are
    part of the format; other ``#`` lines are comments, not records.
    """
    work = line.strip()
    if not work:
        return False
    if work[:10].lower() == "#httponly_":
        work = work[10:]
    elif work.startswith("#"):
        return False
    fields = [field.strip() for field in work.split("\t")]
    if len(fields) != 7:
        return False
    domain, include_sub, path, secure, expiry, name, value = fields
    if not NETSCAPE_DOMAIN.match(domain):
        return False
    if include_sub.upper() not in ("TRUE", "FALSE"):
        return False
    if secure.upper() not in ("TRUE", "FALSE"):
        return False
    if not path.startswith("/"):
        return False
    if not expiry.isdigit():
        return False
    if not name or any(ch.isspace() or ch in "=;" for ch in name):
        return False
    if not value or is_placeholder(value):
        return False
    return True


def cookie_header_is_replayable(line: str) -> bool:
    """QA-17 F02: structural check for explicit Cookie/Set-Cookie lines.

    A concrete ``name=value`` pair on an explicitly named cookie header is
    replayable material even when punctuation splits the value into short
    segments. Placeholders and runtime environment references stay allowed.
    For Set-Cookie only the first segment is the cookie pair; the rest are
    attributes (Path, Expires, ...), which are not credentials.
    """
    m = COOKIE_HEADER_LINE.match(line)
    if not m:
        return False
    segments = m.group(2).split(";")
    if m.group(1).lower() == "set-cookie":
        segments = segments[:1]
    for segment in segments:
        # A bare punctuation-joined token (``aaa!bbb!ccc``) is one value
        # split into short segments; judge the token as a whole. Only a
        # whitespace-free segment can be a bare value — multi-word prose
        # after a header-shaped label is documentation, not a cookie value.
        token = segment.strip().strip("'\"").rstrip(",")
        if (token and not any(ch.isspace() for ch in token)
                and len(token) >= 8 and any(ch.isalnum() for ch in token)
                and "=" not in token
                and token != "cookie_file"
                and not is_placeholder(token)
                and not any(ph in token for ph in PLACEHOLDERS)
                and not RUNTIME_REF.search(token)):
            return True
    for segment in segments:
        segment = segment.strip()
        if "=" not in segment:
            continue
        name, _, value = segment.partition("=")
        if name.strip().lower() in COOKIE_ATTRIBUTE_NAMES:
            continue
        value = value.strip().strip("'\"").strip()
        if not value or is_placeholder(value):
            continue
        if RUNTIME_REF.fullmatch(value):
            continue
        if len(value) >= 4:
            return True
    return False


def scan_json_structure(text: str) -> set[str]:
    """QA-17 F03: scan parsed JSON keys (the parser resolves \\uXXXX escapes).

    A parse failure returns no structural findings here; the caller still
    runs the raw-text and unicode-normalised pattern scans, so malformed
    JSON is never reported clean on the basis of this check alone.
    """
    try:
        doc = json.loads(text)
    except ValueError:
        return set()
    errors: set[str] = set()
    visited: set[int] = set()

    def walk(value):
        if isinstance(value, (dict, list)):
            if id(value) in visited:
                return
            visited.add(id(value))
        if isinstance(value, dict):
            for k, v in value.items():
                key = str(k)
                if key.lower() in ("properties", "definitions", "$defs") and isinstance(v, dict):
                    # JSON Schema: names under ``properties``/``definitions``
                    # are schema definition names, not credential fields.
                    # Still scan the subschemas themselves for material in
                    # values.
                    for subschema in v.values():
                        walk(subschema)
                    continue
                if COOKIE_FIELD.fullmatch(key):
                    errors.add("ACTIVE_COOKIE_FIELD")
                elif SENSITIVE_KEY.fullmatch(key) and v not in (None, "", [], {}):
                    errors.add("CREDENTIAL_FIELD")
                walk(v)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(doc)
    return errors


def scan_scraper_yaml(text: str) -> set[str]:
    errors: set[str] = set()
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError:
        return {"YAML_PARSE_FAILED"}
    if not isinstance(doc, dict):
        return {"YAML_ROOT_INVALID"}
    driver = doc.get("driver")
    if isinstance(driver, dict):
        if "cookies" in driver:
            errors.add("ACTIVE_DRIVER_COOKIES")
        for entry in driver.get("headers", []) or []:
            if not isinstance(entry, dict):
                continue
            # QA-17 F04: the header-name field itself is case-insensitive
            # (key/Key/KEY are the same driver mapping field).
            for field_name, field_value in entry.items():
                if (str(field_name).lower() == "key"
                        and SENSITIVE_KEY.fullmatch(str(field_value))):
                    errors.add("AUTH_HEADER")
    visited: set[int] = set()
    def walk(value):
        if isinstance(value, (dict, list)):
            if id(value) in visited:
                return
            visited.add(id(value))
        if isinstance(value, dict):
            for k, v in value.items():
                key = str(k)
                # The presence of any active cookie/URL mapping is disallowed,
                # even when empty. This also covers nested cookie groups.
                if COOKIE_FIELD.fullmatch(key):
                    errors.add("ACTIVE_COOKIE_FIELD")
                elif SENSITIVE_KEY.fullmatch(key) and v not in (None, "", [], {}):
                    errors.add("CREDENTIAL_FIELD")
                walk(v)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(doc)
    return errors


def scan_text(path: Path, root: Path) -> set[str]:
    if path.is_symlink():
        return {"SYMLINK_NOT_INSPECTED"}
    try:
        data = path.read_bytes()
    except OSError:
        return {"FILE_UNREADABLE"}
    # This repository currently tracks source/text files only. Unknown binary
    # assets must be explicitly reviewed; never let NUL hide an auth string.
    if len(data) > MAX_FILE_BYTES:
        return {"FILE_TOO_LARGE_NOT_INSPECTED"}
    if b"\x00" in data:
        return {"BINARY_CONTENT_NOT_INSPECTED"}
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return {"TEXT_DECODE_FAILED"}
    rel = path.relative_to(root).as_posix()
    errors: set[str] = set()
    if rel.startswith("scrapers/") and path.suffix.lower() in SCRAPER_EXTENSIONS:
        errors |= scan_scraper_yaml(text)
        for line in text.splitlines():
            m = COMMENT_VALUE.match(line)
            if m and not is_placeholder(m.group(1)):
                errors.add("NON_PLACEHOLDER_COOKIE_TEMPLATE")
    # Scan every decodable Git-tracked text file, irrespective of extension.
    # A .md/.js/.html file is not a credential-safe exception. Commented
    # session values are secrets too; placeholders remain explicitly allowed.
    # Never emit matched contents, even on failure.
    for line in text.splitlines():
        if is_netscape_cookie_record(line):
            errors.add("NETSCAPE_COOKIE_RECORD")
        if cookie_header_is_replayable(line):
            errors.add("REPLAYABLE_AUTH_ASSIGNMENT")
    errors |= _pattern_scan(text.splitlines(), path, rel)
    if path.suffix.lower() == ".json":
        # QA-17 F03: parsed keys are already unicode-unescaped by json.loads;
        # a normalised copy additionally lets the raw patterns see escaped
        # keys in values and in malformed JSON that the parser rejected.
        errors |= scan_json_structure(text)
        normalised = UNICODE_ESCAPE.sub(
            lambda m: chr(int(m.group(1), 16)), text)
        if normalised != text:
            errors |= _pattern_scan(normalised.splitlines(), path, rel)
    return errors


def _pattern_scan(lines: list[str], path: Path, rel: str) -> set[str]:
    errors: set[str] = set()
    for line in lines:
        for pattern in (HEADER_PATTERN, ASSIGNMENT):
            for match in pattern.finditer(line):
                candidate = match.group(1)
                # This is a variable reference, not the value of the secret.
                # Match the entire expression, never use substring allowlists.
                runtime_ref = re.fullmatch(
                    r"(?:process\.env|import\.meta\.env|os\.environ)\.[A-Za-z_][A-Za-z0-9_]*",
                    candidate,
                )
                # Unquoted JavaScript member expressions are references, not
                # replayable credentials. Restrict this exception to assignments
                # (not HTTP headers), only the field names actually used by the
                # browser adapters, and never quoted literal strings.
                member_expression = (
                    path.suffix.lower() in (".js", ".mjs", ".html")
                    and pattern is ASSIGNMENT
                    and re.match(
                        r"(?i)^(?:sessionId|access_token|auth_token)\s*['\"]?\s*[:=]",
                        match.group(0).lstrip(),
                    )
                    and re.fullmatch(
                        r"[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+",
                        candidate,
                    )
                    and line[match.start(1) - 1] not in ("'", '"')
                )
                # A known Request Builder enum label names a cookie FILE
                # input type, not a Cookie header or its contents.
                safe_enum_label = (
                    rel == "tools/SPB-2.0.html"
                    and pattern is HEADER_PATTERN
                    and candidate == "cookie_file"
                    and re.search(
                        r"(?i)\bcookie\s*:\s*[\"']?$",
                        line[:match.start(1)],
                    )
                )
                # A capture that stops exactly at a placeholder marker
                # (``name=<LOCAL_ONLY_VALUE>``) captured only the field
                # name; the value itself is the allowed placeholder.
                placeholder_value = any(
                    line[match.end(1):].startswith(ph) for ph in PLACEHOLDERS)
                if (not is_placeholder(candidate)
                        and not placeholder_value
                        and not runtime_ref
                        and not member_expression
                        and not safe_enum_label):
                    errors.add("REPLAYABLE_AUTH_ASSIGNMENT")
    return errors


def scan(root: Path, paths: list[Path] | None = None) -> tuple[list[tuple[str, str]], int]:
    paths = tracked_paths(root) if paths is None else paths
    findings: list[tuple[str, str]] = []
    for path in paths:
        if not path.exists() and not path.is_symlink():
            findings.append(("TRACKED_FILE_MISSING", str(path.relative_to(root))))
            continue
        for rule in sorted(scan_text(path, root)):
            findings.append((rule, path.relative_to(root).as_posix()))
    return findings, len(paths)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan Git tracked files for session material without printing values")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        findings, count = scan(args.root.resolve())
    except (RuntimeError, OSError) as exc:
        print(f"SESSION_SCAN_UNAVAILABLE: {type(exc).__name__}", file=sys.stderr)
        return 2
    print(f"Scanned {count} Git-tracked files")
    if findings:
        for rule, path in findings:
            print(f"{rule}: {path}")
        return 1
    print("Tracked-file session policy passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
