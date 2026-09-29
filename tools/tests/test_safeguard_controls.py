import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_self_evaluation():
    result = subprocess.run(
        [sys.executable, "tools/self_evaluate.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "not a live Stash run" in result.stdout
