#!/usr/bin/env python3
"""WS-A tracked-file session policy scanner. Report rule ID + path only; never values.

Git-tracked files (including scrapers/private/) have no confidentiality boundary.
This is a targeted policy check, not a substitute for a full secret-scanning service.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDERS = ("<LOCAL_ONLY_VALUE>", "<COOKIE_NAME>", "<TOKEN_PLACEHOLDER>", "<REDACTED>")
SENSITIVE_KEY = re.compile(r"^(?:cookie|authorization|proxy-authorization|x-api-key|x-auth-token|access_token|api_key|apikey|api-key|password|passwd|session_token|csrf_token|cf_clearance)$", re.I)
COOKIE_FIELD = re.compile(r"^(?:cookies?|cookieurl|cookie_url)$", re.I)
SCRAPER_EXTENSIONS = frozenset((".yml", ".yaml"))
MAX_FILE_BYTES = 16 * 1024 * 1024
COMMENT_VALUE = re.compile(r"^\s*#\s*(?:-\s*)?Value:\s*(.+?)\s*$", re.I)
HEADER_PATTERN = re.compile(r"""(?i)(?:^|[\s'"])(?:cookie|set-cookie|authorization|proxy-authorization|x-api-key|x-auth-token)(?:['"])?\s*[:=]\s*['"]?(?:(?:Bearer|Basic|Token|Digest|ApiKey)\s+)?([A-Za-z0-9_+./=%;~\-]{8,})""")
ASSIGNMENT = re.compile(r"""(?i)\b(?:session[_-]?token|sessionid|phpsessid|cf_clearance|csrf[_-]?token|api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd)\s*['"]?\s*[:=]\s*['"]?([A-Za-z0-9_+./=~\-]{8,})""")


def tracked_paths(root: Path) -> list[Path]:
    result = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True)
    if result.returncode:
        raise RuntimeError("git-tracked inventory unavailable")
    return [root / Path(p.decode("utf-8", "surrogateescape"))
            for p in result.stdout.split(b"\x00") if p]


def is_placeholder(value: str) -> bool:
    value = value.strip().strip("'\"").strip()
    return value in PLACEHOLDERS


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
            if isinstance(entry, dict) and SENSITIVE_KEY.fullmatch(str(entry.get("Key", ""))):
                errors.add("AUTH_HEADER")
    def walk(value):
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
        for pattern in (HEADER_PATTERN, ASSIGNMENT):
            for match in pattern.finditer(line):
                candidate = match.group(1)
                # This is a variable reference, not the value of the secret.
                # Match the entire expression, never use substring allowlists.
                runtime_ref = re.fullmatch(
                    r"(?:process\.env|import\.meta\.env|os\.environ)\.[A-Za-z_][A-Za-z0-9_]*",
                    candidate,
                )
                js_reference = (
                    path.suffix.lower() in (".js", ".html")
                    and re.fullmatch(
                        r"[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+",
                        candidate,
                    )
                    and re.search(r"(?i)\bsessionId\s*:\s*$", line[:match.start(1)])
                )
                if not is_placeholder(candidate) and not runtime_ref and not js_reference:
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
