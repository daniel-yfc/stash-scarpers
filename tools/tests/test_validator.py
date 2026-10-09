import subprocess
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_validator_exists():
    assert (ROOT / "validator/index.mjs").exists()
    assert (ROOT / "validator/scraper.schema.json").exists()
    assert not (ROOT / "validator/index-zh-TW.mjs").exists()


def test_validator_runs():
    result = subprocess.run(
        ["node", "validator/index.mjs", "-a", "scrapers"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_sort_check_runs():
    result = subprocess.run(
        ["node", "validator/index.mjs", "-a", "-s", "scrapers"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_validator_unit_tests():
    result = subprocess.run(
        [shutil.which("npm") or "npm", "test"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
