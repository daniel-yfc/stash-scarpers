"""WS-F corpus, negative gate and synthetic trace scoring tests.

These are deterministic offline tests, not real Host Skill invocations.
"""
import hashlib
import json

import pytest

from tools.evals.validate_cases import ROOT, CorpusError, load_cases
from tools.evals.evaluate_traces import evaluate_events, score_cases
from tools.evals.verify_evidence import TraceError, load_trace


def sample_trace(case_id="POS-01", host="codex", repeat=1):
    return {
        "case_id": case_id, "host": host, "repeat": repeat,
        "repo_sha": "a" * 40, "skill_sha256": "b" * 64,
        "host_version": "synthetic-1", "model": "test-model",
        "capture_kind": "synthetic_fixture", "event_capture_complete": True,
        "events": [
            {"type": "skill_load", "skill_id": "stash-scraper-builder",
             "path": "skills/stash-scraper-builder/SKILL.md"},
            {"type": "intent", "value": "CREATE"},
            {"type": "phase_exit", "phase": "P0", "status": "PASS"},
        ],
    }


def test_corpus_45_cases_four_suites():
    cases = load_cases(ROOT)
    assert len(cases) == 45
    assert sum(key.startswith("POS-") for key in cases) == 10
    assert sum(key.startswith("NEG-") for key in cases) == 10
    assert sum(key.startswith("NM-") for key in cases) == 10
    assert sum(key.startswith("STOP-") for key in cases) == 10
    assert sum(key.startswith("E2E-") for key in cases) == 5


def test_unavailable_schema_fails_closed(tmp_path):
    with pytest.raises(CorpusError):
        load_cases(tmp_path)


def test_trace_load_good_synthetic_provisional(tmp_path):
    f = tmp_path / "trace.json"
    f.write_text(json.dumps(sample_trace()), encoding="utf-8")
    result, digest = load_trace(f, "a" * 40, "b" * 64, "POS-01", "codex", 1)
    assert digest == hashlib.sha256(f.read_bytes()).hexdigest()
    assert result["capture_kind"] == "synthetic_fixture"


def test_trace_rejects_self_declared_verdict(tmp_path):
    record = sample_trace()
    record["verdict"] = "PASS"
    f = tmp_path / "trace.json"
    f.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(TraceError):
        load_trace(f, "a" * 40, "b" * 64, "POS-01", "codex", 1)


def test_trace_rejects_secret_content_without_echo(tmp_path):
    record = sample_trace()
    record["cookie"] = "synthetic-session-value-not-real"
    f = tmp_path / "trace.json"
    f.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(TraceError, match="potential session material"):
        load_trace(f, "a" * 40, "b" * 64, "POS-01", "codex", 1)


def test_trace_rejects_missing_tool_capture(tmp_path):
    record = sample_trace()
    record["event_capture_complete"] = False
    f = tmp_path / "trace.json"
    f.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(TraceError, match="complete tool-event"):
        load_trace(f, "a" * 40, "b" * 64, "POS-01", "codex", 1)


def test_trace_rejects_wrong_revision(tmp_path):
    f = tmp_path / "trace.json"
    f.write_text(json.dumps(sample_trace()), encoding="utf-8")
    with pytest.raises(TraceError):
        load_trace(f, "c" * 40, "b" * 64, "POS-01", "codex", 1)


def test_trace_rejects_unsupported_verification_pass(tmp_path):
    record = sample_trace()
    record["events"].append({"type": "verification", "axis": "LOADER", "status": "PASS"})
    f = tmp_path / "trace.json"
    f.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(TraceError, match="evidence reference"):
        load_trace(f, "a" * 40, "b" * 64, "POS-01", "codex", 1)


def test_trigger_must_actually_load():
    cases = load_cases(ROOT)
    assert evaluate_events(cases["POS-01"], sample_trace()) == []
    rec = sample_trace()
    rec["events"] = [{"type": "intent", "value": "CREATE"}]
    assert any("Skill load" in x for x in evaluate_events(cases["POS-01"], rec))


def test_near_miss_forbidden_skill_load():
    cases = load_cases(ROOT)
    rec = sample_trace()
    assert any("forbidden Skill" in x for x in evaluate_events(cases["NEG-01"], rec))


def test_review_only_forbidden_write():
    cases = load_cases(ROOT)
    rec = sample_trace()
    rec["events"][1]["value"] = "REVIEW_ONLY"
    rec["events"].append({"type": "tool_action", "effect": "WRITE", "name": "github-update-file"})
    assert any("write/destructive" in x for x in evaluate_events(cases["STOP-02"], rec))


def test_stop_phase_promotion_rejected():
    cases = load_cases(ROOT)
    rec = sample_trace()
    rec["events"][1]["value"] = "VALIDATE_ONLY"
    rec["events"].extend([
        {"type": "phase_exit", "phase": "P4", "status": "FAIL"},
        {"type": "phase_exit", "phase": "P5", "status": "PASS"},
    ])
    assert any("downstream phase" in x for x in evaluate_events(cases["STOP-05"], rec))


def test_fixture_selftest_not_loader_pass():
    cases = load_cases(ROOT)
    rec = sample_trace()
    rec["events"][1]["value"] = "VALIDATE_ONLY"
    rec["events"].append({
        "type": "verification", "axis": "LOADER", "status": "PASS",
        "artifact_ref": "synthetic:loader", "artifact_sha256": "c" * 64
    })
    assert any("LOADER" in x for x in evaluate_events(cases["STOP-06"], rec))


def test_functional_e2e_fails_without_runtime_proof():
    cases = load_cases(ROOT)
    rec = sample_trace()
    assert any("required evidence missing: LOADER" in x
               for x in evaluate_events(cases["E2E-01"], rec))


def test_no_traces_remain_not_run(tmp_path):
    cases = {"POS-01": load_cases(ROOT)["POS-01"]}
    result = score_cases(cases, tmp_path, ROOT, "codex", "a" * 40)
    assert result["summary"] == {"PASS": 0, "FAIL": 0, "NOT_RUN": 3}
    assert result["status"] == "OFFLINE_TRACE_ASSESSMENT_ONLY"
    assert all(item["source_trust"] == "MISSING" for item in result["cases"])
