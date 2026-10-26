"""WS-F corpus, negative gate and synthetic trace scoring tests.

These are deterministic offline tests, not real Host Skill invocations.
"""
import hashlib
import json

import pytest

from tools.evals.validate_cases import ROOT, CorpusError, load_cases
from tools.evals.evaluate_traces import evaluate_events, score_cases, assess_thresholds
from tools.evals.verify_evidence import TraceError, load_trace
from tools.evals.review_attestation import is_attested, canonical_bytes


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
            {"type": "phase_exit", "phase": "P6", "status": "PASS"},
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
    assert result["summary"] == {"PASS": 0, "FAIL": 0, "NOT_RUN": 3, "UNATTESTED": 0, "SYNTHETIC_ONLY": 0}
    assert result["status"] == "OFFLINE_TRACE_ASSESSMENT_ONLY"
    assert all(item["source_trust"] == "MISSING" for item in result["cases"])


def test_trigger_requires_bounded_delivery_not_just_p0():
    rec = sample_trace()
    rec["events"] = [x for x in rec["events"]
                     if x.get("phase") != "P6"]
    problems = evaluate_events(load_cases(ROOT)["POS-01"], rec)
    assert "missing P6 bounded delivery completion" in problems


def test_p4_fail_then_p6_report_is_valid_stop():
    rec = sample_trace(case_id="STOP-05")
    rec["events"][1]["value"] = "VALIDATE_ONLY"
    rec["events"].insert(-1, {"type": "phase_exit", "phase": "P4", "status": "FAIL"})
    rec["workspace"] = {
        "method": "tracked-and-untracked-worktree-sha256-v1",
        "before_sha256": "1" * 64, "after_sha256": "1" * 64,
    }
    assert evaluate_events(load_cases(ROOT)["STOP-05"], rec) == []


def test_p4_fail_then_p5_pass_is_forbidden_even_with_p6():
    rec = sample_trace(case_id="STOP-05")
    rec["events"][1]["value"] = "VALIDATE_ONLY"
    rec["events"].insert(-1, {"type": "phase_exit", "phase": "P4", "status": "FAIL"})
    rec["events"].insert(-1, {"type": "phase_exit", "phase": "P5", "status": "PASS"})
    rec["workspace"] = {
        "method": "tracked-and-untracked-worktree-sha256-v1",
        "before_sha256": "1" * 64, "after_sha256": "1" * 64,
    }
    assert any("downstream phase promoted" in e
               for e in evaluate_events(load_cases(ROOT)["STOP-05"], rec))


def test_read_only_case_without_independent_workspace_digest_fails():
    rec = sample_trace(case_id="STOP-02")
    rec["events"][1]["value"] = "REVIEW_ONLY"
    assert any("worktree" in s
               for s in evaluate_events(load_cases(ROOT)["STOP-02"], rec))


def test_read_only_workspace_mutation_detected_even_without_tool_write():
    rec = sample_trace(case_id="STOP-02")
    rec["events"][1]["value"] = "REVIEW_ONLY"
    rec["workspace"] = {
        "method": "tracked-and-untracked-worktree-sha256-v1",
        "before_sha256": "a" * 64, "after_sha256": "b" * 64,
    }
    assert "read-only worktree changed" in evaluate_events(load_cases(ROOT)["STOP-02"], rec)


def test_matching_but_fake_artifact_digest_fails(tmp_path):
    rec = sample_trace()
    rec["events"].append({
        "type": "verification", "axis": "LOADER", "status": "PASS",
        "artifact_ref": "artifacts/loader.json", "artifact_sha256": "a" * 64,
    })
    artifact = tmp_path / "artifacts" / "loader.json"
    artifact.parent.mkdir()
    artifact.write_text("different bytes", encoding="utf-8")
    trace_path = tmp_path / "traces" / "trace.json"
    trace_path.parent.mkdir()
    trace_path.write_text(json.dumps(rec), encoding="utf-8")
    with pytest.raises(TraceError, match="digest mismatch"):
        load_trace(trace_path, "a" * 40, "b" * 64, "POS-01", "codex", 1,
                   evidence_root=tmp_path)


def test_signed_external_review_has_a_real_success_path():
    import hmac
    payload = sample_trace()
    payload["capture_kind"] = "host_export"
    record = {
        "version": 1, "case_id": "POS-01", "host": "codex", "repeat": 1,
        "repo_sha": payload["repo_sha"],
        "skill_sha256": payload["skill_sha256"],
        "trace_sha256": "c" * 64,
        "reviewer": "independent-qa",
        "host_origin_verified": True,
        "tool_capture_verified": True,
        "workspace_verified": True,
        "artifacts_verified": True,
    }
    key = b"K" * 32  # Synthetic unit-test key; no real credentials.
    record["signature"] = hmac.new(key, canonical_bytes(record), hashlib.sha256).hexdigest()
    assert is_attested(record, payload, "c" * 64, key)
    payload["capture_kind"] = "synthetic_fixture"
    assert not is_attested(record, payload, "c" * 64, key)


def test_exact_host_threshold_pass_and_fail_paths():
    cases = load_cases(ROOT)
    rows = []
    for case in cases:
        for repeat in (1, 2, 3):
            rows.append({
                "case_id": case, "repeat": repeat, "status": "PASS",
                "source_trust": "REVIEWER_ATTESTED", "host_version": "host-1",
                "model": "model-pinned",
            })
    assert assess_thresholds({"cases": rows}, cases)[0] == "PASS"
    rows[0]["source_trust"] = "SYNTHETIC_FIXTURE"
    assert assess_thresholds({"cases": rows}, cases)[0] == "INCOMPLETE"
    rows[0]["source_trust"] = "REVIEWER_ATTESTED"
    for row in rows:
        if row["case_id"] == "STOP-02":
            row["status"] = "FAIL"
    assert assess_thresholds({"cases": rows}, cases)[0] == "FAIL"


def test_unattested_trace_never_grants_formal_pass(tmp_path):
    cases = {"POS-01": load_cases(ROOT)["POS-01"]}
    digest = hashlib.sha256((ROOT / "skills/stash-scraper-builder/SKILL.md").read_bytes()).hexdigest()
    rec = sample_trace()
    rec["skill_sha256"] = digest
    rec["capture_kind"] = "host_export"
    f = tmp_path / "POS-01--codex--1.json"
    f.write_text(json.dumps(rec), encoding="utf-8")
    result = score_cases(cases, tmp_path, ROOT, "codex", rec["repo_sha"])
    assert result["cases"][0]["status"] == "UNATTESTED"
    assert result["cases"][0]["source_trust"] == "HOST_EXPORT_UNATTESTED"
    assert assess_thresholds(result, cases)[0] == "INCOMPLETE"
