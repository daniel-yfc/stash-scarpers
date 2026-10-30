"""Contract tests for the Stash installable scraper source index generator."""

from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from build_scraper_source import SourceError, build, verify  # noqa: E402


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args], check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


@pytest.fixture
def source_repo(tmp_path):
    repo = tmp_path / "repository"
    scrapers = repo / "scrapers"
    scrapers.mkdir(parents=True)
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Stash Source Test")
    git(repo, "config", "user.email", "stash-source@example.invalid")
    (scrapers / "Trance.yml").write_text(
        "name: Trance\nsceneByURL:\n  - action: scrapeXPath\n    url: [example.org/product/]\n    scraper: detail\n",
        encoding="utf-8",
    )
    (scrapers / "GetFilm.yml").write_text(
        "name: Get Film\nsceneByURL:\n  - action: scrapeXPath\n    url: [example.net/scene/]\n    scraper: detail\n",
        encoding="utf-8",
    )
    (scrapers / "Trance.test.yaml").write_text("url: https://example.org/", encoding="utf-8")
    nested = scrapers / "private"
    nested.mkdir()
    (nested / "Hidden.yml").write_text("name: Hidden\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "test fixtures")
    return repo


def test_index_has_official_fields_and_real_checksums(source_repo, tmp_path):
    output = tmp_path / "site" / "main"
    entries = build(source_repo, output)
    assert [row["id"] for row in entries] == ["GetFilm", "Trance"]
    assert all(row["version"] and row["date"] and len(row["sha256"]) == 64 for row in entries)
    assert not any("private" in str(row).lower() for row in entries)
    assert yaml.safe_load((output / "index.yml").read_text()) == entries
    assert sorted(p.name for p in output.iterdir()) == ["GetFilm.zip", "Trance.zip", "index.yml"]
    for row in entries:
        package = output / row["path"]
        assert sha256(package.read_bytes()).hexdigest() == row["sha256"]
        with zipfile.ZipFile(package) as archive:
            assert archive.namelist() == [row["id"] + ".yml"]
            assert yaml.safe_load(archive.read(row["id"] + ".yml"))["name"] == row["name"]
    verify(output)
    # Byte-for-byte deterministic package and index for the same committed source.
    previous = {p.name: p.read_bytes() for p in output.iterdir()}
    build(source_repo, output)
    assert {p.name: p.read_bytes() for p in output.iterdir()} == previous


def test_tampered_package_and_manifest_fail(source_repo, tmp_path):
    output = tmp_path / "site"
    build(source_repo, output)
    with (output / "Trance.zip").open("ab") as out:
        out.write(b"tampering")
    with pytest.raises(SourceError, match="checksum"):
        verify(output)
    build(source_repo, output)
    index = yaml.safe_load((output / "index.yml").read_text())
    index[0]["path"] = "../../bad.zip"
    (output / "index.yml").write_text(yaml.safe_dump(index))
    with pytest.raises(SourceError, match="mismatched package path"):
        verify(output)


def test_new_committed_version_changes_only_affected_package(source_repo, tmp_path):
    output = tmp_path / "site"
    before = build(source_repo, output)
    filename = source_repo / "scrapers" / "Trance.yml"
    filename.write_text(filename.read_text() + "\n# documented update\n", encoding="utf-8")
    git(source_repo, "add", "scrapers/Trance.yml")
    git(source_repo, "commit", "-qm", "update Trance")
    after = build(source_repo, output)
    old = {r["id"]: r for r in before}
    new = {r["id"]: r for r in after}
    assert old["Trance"]["sha256"] != new["Trance"]["sha256"]
    assert old["Trance"]["version"] != new["Trance"]["version"]
    assert old["GetFilm"] == new["GetFilm"]


@pytest.mark.parametrize("bad_yaml,expected", [
    ("sceneByURL: []\n", "missing root name"),
    ("name: Unsafe\ndriver:\n  cookies:\n    - Key: Cookie\n      Value: secret\n", "driver.cookies"),
    ("name: Unsafe\napi_key: real-secret\n", "secret-looking key"),
    ("name: Unsafe\ndriver:\n  headers:\n    - Key: Cookie\n      Value: session-value\n", "credential-bearing driver.header"),
    ("name: Unsafe\ndriver:\n  headers:\n    - Key: Authorization\n      Value: Bearer-example\n", "credential-bearing driver.header"),
    ("name: Unsafe\ndriver:\n  headers:\n    - Key: X-Auth-Token\n      Value: session-value\n", "credential-bearing driver.header"),
    ("name: Unsafe\nsceneByName:\n  action: script\n  script: [python, scraper.py]\n", "script action"),
    ("# requires: absent-package\nname: Unsafe\n", "unpublished package"),
])
def test_unsafe_or_uninstallable_scrapers_fail_closed(source_repo, tmp_path, bad_yaml, expected):
    (source_repo / "scrapers" / "Trance.yml").write_text(bad_yaml, encoding="utf-8")
    with pytest.raises(SourceError, match=expected):
        build(source_repo, tmp_path / "site")


def test_missing_git_history_fails_without_fake_versions(tmp_path):
    repo = tmp_path / "repo"
    (repo / "scrapers").mkdir(parents=True)
    (repo / "scrapers" / "Fake.yml").write_text("name: Fake\n", encoding="utf-8")
    with pytest.raises(SourceError, match="full Git history"):
        build(repo, tmp_path / "site")
