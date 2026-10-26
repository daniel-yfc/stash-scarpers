"""Negative/positive controls for moving maintainer files out of runtime references."""
from pathlib import Path

from tools.check_resource_placement import inspect, MOVED, ROOT


def fixture_root(tmp_path: Path) -> Path:
    for rel in MOVED:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# synthetic\n", encoding="utf-8")
    return tmp_path


def test_live_repository_resource_boundary():
    assert inspect(ROOT) == []


def test_missing_moved_file_is_blocking(tmp_path):
    r = fixture_root(tmp_path)
    (r / MOVED[0]).unlink()
    assert any(x.startswith("MISSING_MOVED_RESOURCE:") for x in inspect(r, paths=()))


def test_old_runtime_reference_is_rejected(tmp_path):
    r = fixture_root(tmp_path)
    (r / "active.md").write_text(
        "See [old](skills/stash-scraper-builder/references/eval-pack.md).\n",
        encoding="utf-8",
    )
    errors = inspect(r, paths=("active.md",))
    assert any(x.startswith("STALE_RUNTIME_REFERENCE:") for x in errors)


def test_local_link_migration_is_verified(tmp_path):
    r = fixture_root(tmp_path)
    (r / "active.md").write_text("[new](tests/skill-evals/legacy-functional-eval.md)\n", encoding="utf-8")
    assert inspect(r, paths=("active.md",)) == []


def test_broken_local_link_fails(tmp_path):
    r = fixture_root(tmp_path)
    (r / "active.md").write_text("[missing](not-found.md)\n", encoding="utf-8")
    assert any(x.startswith("BROKEN_LOCAL_LINK:") for x in inspect(r, paths=("active.md",)))


def test_incident_file_returned_to_runtime_is_rejected(tmp_path):
    r = fixture_root(tmp_path)
    p = r / "skills/stash-scraper-builder/references/incident-reviews.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("# forbidden\n", encoding="utf-8")
    assert any(x.startswith("NON_RUNTIME_FILE_IN_SKILL:") for x in inspect(r, paths=()))


def test_markdown_archive_is_not_a_runtime_route(tmp_path):
    r = fixture_root(tmp_path)
    archived = r / MOVED[1]
    archived.write_text(
        "Historical [source](../../skills/stash-scraper-builder/references/debugging.md)\n",
        encoding="utf-8",
    )
    # Unlike active docs, archived historical text may mention the prior path
    # but a still-live link must resolve before this test is positive.
    active = r / "skills/stash-scraper-builder/references/debugging.md"
    active.parent.mkdir(parents=True, exist_ok=True)
    active.write_text("# current\n", encoding="utf-8")
    assert inspect(r, paths=(MOVED[1],)) == []
