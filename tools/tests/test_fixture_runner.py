import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_fixture_contract_self_test():
    result = subprocess.run(
        ["node", "tools/verify-scraper-fixtures.mjs", "--self-test"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "positive and 6 negative cases passed" in result.stdout
