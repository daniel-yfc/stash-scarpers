#!/usr/bin/env python3
"""Build an installable Stash scraper Source index and versioned ZIP packages.

Produces <output>/index.yml and <output>/<id>.zip. Requires a complete
Git history, as upstream scraper sources derive versions from file commits.
Only scrapers/*.yml are published; nested, private and test sidecars are excluded.
"""

from __future__ import annotations

import argparse
import hashlib
import io
from pathlib import Path
import re
import subprocess
import sys
import zipfile

import yaml

REPO = Path(__file__).resolve().parents[1]
SCRAPER_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
REQUIRES = re.compile(r"^#\s*requires:\s*(.*?)\s*$", re.MULTILINE)
SECRET_KEYS = re.compile(
    r"(?:cookie|authorization|api[_-]?key|password|session[_-]?token)",
    re.IGNORECASE,
)
ENTRYPOINTS = (
    "sceneByURL", "sceneByName", "sceneByFragment", "sceneByQueryFragment",
    "performerByURL", "performerByName", "performerByFragment",
    "groupByURL", "galleryByURL", "galleryByFragment",
    "imageByURL", "imageByFragment",
)


class SourceError(ValueError):
    """Raised when building would create an invalid/unsafe source."""


def commit_version(repo: Path, scraper: Path) -> tuple[str, str]:
    """Return last committed source revision and UTC date (Stash source format)."""
    relative = scraper.relative_to(repo)
    cmd = ["git", "-C", str(repo), "log", "-1",
           "--format=%h%n%cI", "--", relative.as_posix()]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    lines = result.stdout.splitlines()
    if result.returncode or len(lines) != 2 or not re.fullmatch(r"[0-9a-f]{7,40}", lines[0]):
        raise SourceError(f"missing full Git history for {relative} (fetch-depth: 0 required)")
    # Git ISO 8601 committer timestamp, normalized to UTC in the published index.
    from datetime import datetime, timezone

    try:
        when = datetime.fromisoformat(lines[1]).astimezone(timezone.utc)
    except ValueError as exc:
        raise SourceError(f"invalid Git date for {relative}") from exc
    return lines[0], when.strftime("%Y-%m-%d %H:%M:%S")


def check_scraper(source: str, path: Path) -> tuple[str, list[str]]:
    try:
        config = yaml.safe_load(source)
    except yaml.YAMLError as exc:
        raise SourceError(f"invalid YAML in {path.name}") from exc
    if not isinstance(config, dict) or not isinstance(config.get("name"), str) or not config["name"].strip():
        raise SourceError(f"{path.name}: missing root name")
    # Do not publish active credentials, even if a repository-wide scanner misses one.
    driver = config.get("driver") or {}
    if not isinstance(driver, dict):
        raise SourceError(f"{path.name}: driver must be a mapping")
    if "cookies" in driver:
        raise SourceError(f"{path.name}: driver.cookies cannot be published")
    for item in driver.get("headers") or []:
        if not isinstance(item, dict):
            raise SourceError(f"{path.name}: invalid driver.headers entry")
        header_name = str(item.get("Key") or "").strip().lower()
        if header_name in {"cookie", "authorization", "proxy-authorization", "x-api-key", "x-auth-token"} or (
            any(word in header_name for word in ("token", "secret", "apikey", "api-key", "session", "csrf"))
        ):
            raise SourceError(f"{path.name}: credential-bearing driver.header cannot be published")
    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if SECRET_KEYS.search(str(key)) and value:
                    raise SourceError(f"{path.name}: populated secret-looking key cannot be published")
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    # Published YAML must be credential-free. Headers such as User-Agent are fine.
    walk(config)
    # Standalone ZIPs cannot install external script/dependency files. Fail closed.
    for key in ENTRYPOINTS:
        mappings = config.get(key)
        for definition in mappings if isinstance(mappings, list) else [mappings]:
            if isinstance(definition, dict) and definition.get("action") == "script":
                raise SourceError(f"{path.name}: script action needs a separately bundled package")
    match = REQUIRES.search(source)
    requires = [p.strip() for p in match.group(1).split(",")] if match else []
    if any(not SCRAPER_NAME.fullmatch(item) for item in requires):
        raise SourceError(f"{path.name}: invalid requires declaration")
    return config["name"].strip(), requires


def make_zip(filename: str, body: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        info = zipfile.ZipInfo(filename, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, body)
    return buffer.getvalue()


def build(repo: Path, output: Path) -> list[dict]:
    repo = repo.resolve()
    scrapers = repo / "scrapers"
    if not scrapers.is_dir() or output.resolve().is_relative_to(scrapers.resolve()):
        raise SourceError("invalid scraper root or output inside scraper root")

    inputs = sorted(scrapers.glob("*.yml"), key=lambda p: (p.stem.casefold(), p.stem))
    if not inputs:
        raise SourceError("no public scraper YAML files found")
    # Nested variants (scrapers/private/) are intentionally not published.
    entries: list[dict] = []
    packages: dict[str, bytes] = {}
    ids: set[str] = set()
    for source_file in inputs:
        if not source_file.is_file() or source_file.is_symlink():
            raise SourceError(f"unsafe scraper file: {source_file.name}")
        package_id = source_file.stem
        if not SCRAPER_NAME.fullmatch(package_id) or package_id.casefold() in ids:
            raise SourceError(f"invalid or duplicate package id: {package_id}")
        ids.add(package_id.casefold())
        body = source_file.read_bytes()
        name, requires = check_scraper(body.decode("utf-8"), source_file)
        version, date = commit_version(repo, source_file)
        payload = make_zip(source_file.name, body)
        entry = {
            "id": package_id,
            "name": name,
            "version": version,
            "date": date,
            "path": f"{package_id}.zip",
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
        if requires:
            entry["requires"] = requires
        packages[entry["path"]] = payload
        entries.append(entry)
    published = {entry["id"] for entry in entries}
    for entry in entries:
        for required in entry.get("requires", []):
            if required not in published:
                raise SourceError(f"{entry['id']} needs unpublished package {required}")
    output.mkdir(parents=True, exist_ok=True)
    for stale in output.glob("*.zip"):
        stale.unlink()
    for name, payload in packages.items():
        (output / name).write_bytes(payload)
    (output / "index.yml").write_text(
        yaml.safe_dump(entries, allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )
    verify(output)
    return entries


def verify(output: Path) -> None:
    manifest = yaml.safe_load((output / "index.yml").read_text(encoding="utf-8"))
    if not isinstance(manifest, list) or not manifest:
        raise SourceError("index.yml must contain a nonempty list")
    ids = set()
    for entry in manifest:
        if set(entry) - {"id", "name", "version", "date", "path", "sha256", "requires"}:
            raise SourceError("unexpected index fields")
        if not all(entry.get(k) for k in ("id", "name", "version", "date", "path", "sha256")):
            raise SourceError("missing index fields")
        if entry["id"] in ids or entry["path"] != f"{entry['id']}.zip":
            raise SourceError("duplicate id or mismatched package path")
        ids.add(entry["id"])
        file = output / entry["path"]
        if not file.is_file() or file.is_symlink():
            raise SourceError("missing ZIP package")
        body = file.read_bytes()
        if hashlib.sha256(body).hexdigest() != entry["sha256"]:
            raise SourceError("ZIP checksum mismatch")
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            if archive.namelist() != [f"{entry['id']}.yml"]:
                raise SourceError("ZIP contains unexpected content")
            data = yaml.safe_load(archive.read(archive.namelist()[0]))
            if not isinstance(data, dict) or data.get("name") != entry["name"]:
                raise SourceError("ZIP metadata does not match index")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Stash installable scraper source packages")
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--output", type=Path, default=REPO / "_site" / "main")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.verify_only:
            verify(args.output)
            print(f"Stash source integrity OK: {args.output}")
        else:
            entries = build(args.repo, args.output)
            print(f"Stash source: {len(entries)} public packages; index: {args.output / 'index.yml'}")
        return 0
    except (SourceError, OSError, UnicodeError) as exc:
        # Never log scraper contents or secret values.
        print(f"Stash source build failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
