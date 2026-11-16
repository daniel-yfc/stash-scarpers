"""Unit tests for tools/gvdb_custom_fields.py planned_updates().

planned_updates is the pure decision core of the GVDB ID writer: given the
performer list (id, urls, custom_fields) it decides which performers need a
write, which are already correct, and which must be skipped because their
URLs carry two different GVDB IDs. These tests pin that behaviour without
any network access; the GraphQL transport is not covered here.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import gvdb_custom_fields as gcf  # noqa: E402


def perf(pid, urls=None, current="__absent__", name="P"):
    p = {"id": pid, "name": name, "urls": urls}
    if current != "__absent__":
        p["custom_fields"] = {gcf.FIELD_NAME: current}
    else:
        p["custom_fields"] = {}
    return p


def test_no_gvdb_url_is_ignored():
    updates, problems = gcf.planned_updates(
        [perf("1", ["https://example.com/x"]), perf("2", None), perf("3", [])]
    )
    assert updates == [] and problems == []


def test_single_id_without_current_needs_write():
    updates, problems = gcf.planned_updates([perf("7", ["https://md.gvdb.org/12345/"])])
    assert problems == []
    assert updates == [{"id": "7", "name": "P", "current": None, "target": 12345}]


def test_already_correct_is_skipped_int_and_str():
    updates, _ = gcf.planned_updates(
        [perf("1", ["https://md.gvdb.org/42/"], current=42),
         perf("2", ["https://md.gvdb.org/43/"], current="43")]
    )
    assert updates == []


def test_stale_current_is_updated():
    updates, _ = gcf.planned_updates([perf("1", ["https://md.gvdb.org/42/"], current=41)])
    assert len(updates) == 1 and updates[0]["current"] == 41 and updates[0]["target"] == 42


def test_non_numeric_current_is_updated():
    updates, _ = gcf.planned_updates([perf("1", ["https://md.gvdb.org/42/"], current="n/a")])
    assert len(updates) == 1 and updates[0]["target"] == 42


def test_two_different_ids_are_a_problem_never_a_write():
    p = perf("9", ["https://md.gvdb.org/100/", "https://md.gvdb.org/200/"])
    updates, problems = gcf.planned_updates([p])
    assert updates == []
    assert problems == [(p, [100, 200])]


def test_same_id_repeated_across_urls_is_one_write():
    updates, problems = gcf.planned_updates(
        [perf("5", ["https://md.gvdb.org/77/", "http://md.gvdb.org/77"])]
    )
    assert problems == []
    assert len(updates) == 1 and updates[0]["target"] == 77
