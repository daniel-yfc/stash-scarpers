import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_scrapers_valid():
    result = subprocess.run(
        ["node", "validator/index.mjs", "-a", "-s", "scrapers"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_scrapers_have_name():
    for scraper in (ROOT / "scrapers").rglob("*.yml"):
        content = scraper.read_text()
        assert "name:" in content, f"{scraper} missing name"


def test_fragment_mapping_is_optional_but_valid_when_present():
    import re
    for scraper in (ROOT / "scrapers").rglob("*.yml"):
        data = scraper.read_text()
        if "sceneByQueryFragment:" not in data:
            continue
        block = data.split("sceneByQueryFragment:", 1)[1]
        # Stop at the next top-level key (no indentation) so we only inspect
        # the sceneByQueryFragment block.
        block = re.split(r"\n[A-Za-z]", block, maxsplit=1)[0]
        # The fragment placeholder must drive the queryURL: either the raw
        # "{url}" passthrough, or an endpoint template embedding {url}
        # (API scrapers rewrite the selected hit URL into their detail
        # endpoint, e.g. GAYERDAR's api/v2/videos/{url}).
        query_url_lines = [ln for ln in block.splitlines() if "queryURL:" in ln]
        assert any("{url}" in ln for ln in query_url_lines), (
            f"{scraper}: sceneByQueryFragment queryURL must use the {{url}} placeholder"
        )
