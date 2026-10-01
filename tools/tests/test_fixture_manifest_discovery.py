from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_fixture_manifests import run


def test_no_manifests_is_not_reported_as_a_pass(tmp_path, capsys):
    assert run(tmp_path, [sys.executable, "-c", "raise SystemExit(99)"], []) == 0
    assert "UNVERIFIED" in capsys.readouterr().out


def test_missing_expected_manifest_fails(tmp_path, capsys):
    assert run(tmp_path, [sys.executable, "-c", "raise SystemExit(0)"], ["tests/fixtures/gayerdar-fixtures.yml"]) == 1
    assert "MISSING EXPECTED" in capsys.readouterr().err


def test_discovers_manifest_and_propagates_runner_failure(tmp_path):
    folder = tmp_path / "tests" / "fixtures"
    folder.mkdir(parents=True)
    (folder / "example-fixtures.yml").write_text("cases: []\n", encoding="utf-8")
    assert run(tmp_path, [sys.executable, "-c", "raise SystemExit(0)"], []) == 0
    assert run(tmp_path, [sys.executable, "-c", "raise SystemExit(3)"], []) == 1
