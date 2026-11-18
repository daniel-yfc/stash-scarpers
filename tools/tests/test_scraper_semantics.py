"""General driver-mode validation: CDP and Surf are both valid fetch
modes for any scraper; enabling both at once is rejected. These tests
cover the rule in tools/check_scraper_semantics.py uniformly -- they
are not fitted to any single scraper."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "semantics", ROOT / "tools/check_scraper_semantics.py"
)
semantics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(semantics)


def driver_errors(data):
    semantics.errors = []
    semantics.check_driver_mode(data, "synthetic.yml")
    return list(semantics.errors)


def test_cdp_only_is_valid():
    assert driver_errors({"driver": {"useCDP": True}}) == []


def test_surf_only_is_valid():
    assert driver_errors({"driver": {"useSurf": True}}) == []


def test_no_driver_is_valid():
    assert driver_errors({}) == []
    assert driver_errors({"driver": {"headers": []}}) == []


def test_both_modes_enabled_is_rejected():
    errs = driver_errors({"driver": {"useCDP": True, "useSurf": True}})
    assert len(errs) == 1
    assert "useCDP" in errs[0] and "useSurf" in errs[0]


def test_all_committed_scrapers_satisfy_driver_rule():
    import yaml

    for path in sorted((ROOT / "scrapers").rglob("*.yml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            assert driver_errors(data) == [], path
