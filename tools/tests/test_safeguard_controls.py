import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_fixture_runner_self_test():
    result = subprocess.run(
        ["node", "tools/verify-scraper-fixtures.mjs", "--self-test"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_safeguard_audit():
    result = subprocess.run(
        [sys.executable, "tools/safeguard_audit.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
