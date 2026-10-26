#!/usr/bin/env python3
"""Validate sanitized host-export trace envelopes.

An envelope and SHA256 are integrity aids, not proof a host executed it.
External capture authentication/reviewer checks are required for real host PASS.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

MAX_TRACE_BYTES = 1024 * 1024
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SESSION_KEY = re.compile(r"(?i)\"(?:cookie|set-cookie|authorization|access_token|api_key|password|session_token)\"\s*:")
INLINE_AUTH = re.compile(r"(?i)(?:cookie|authorization|set-cookie)\s*[:=]\s*(?!<REDACTED>)[A-Za-z0-9_/+.=%-]{10,}")
EVENT_TYPES = {"skill_load", "intent", "phase_exit", "verification", "tool_action"}
EVIDENCE_AXES = {"SCHEMA", "VALUE_MATCH", "SCRIPT_IO", "FIXTURE_SITE", "LOADER", "LIVE_SEARCH", "LIVE_DETAIL", "CDP"}
STATUSES = {"PASS", "FAIL", "BLOCKED", "NOT_RUN", "N/A"}


class TraceError(ValueError):
    pass


def load_trace(path: Path, repo_sha: str, skill_sha: str, case_id: str, host: str, repeat: int) -> tuple[dict, str]:
    if path.is_symlink() or not path.is_file():
        raise TraceError("trace file missing or a symlink")
    data = path.read_bytes()
    if not data or len(data) > MAX_TRACE_BYTES:
        raise TraceError("empty or oversized trace")
    if SESSION_KEY.search(data.decode("utf-8", errors="replace")) or INLINE_AUTH.search(data.decode("utf-8", errors="replace")):
        raise TraceError("potential session material in trace: output suppressed")
    try:
        obj = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TraceError("trace not valid JSON") from exc
    if not isinstance(obj, dict) or "verdict" in obj or "result" in obj:
        raise TraceError("invalid trace envelope or self-declared verdict")
    exact = {
        "case_id": case_id, "repo_sha": repo_sha, "skill_sha256": skill_sha,
        "host": host, "repeat": repeat,
    }
    if any(obj.get(k) != v for k, v in exact.items()):
        raise TraceError("trace does not match pinned case, host, repeat, repo or skill")
    if not HEX40.fullmatch(repo_sha) or not HEX64.fullmatch(skill_sha):
        raise TraceError("invalid pinned repository SHA or skill digest")
    if obj.get("capture_kind") not in ("host_export", "synthetic_fixture"):
        raise TraceError("unrecognized capture kind")
    if obj.get("event_capture_complete") is not True:
        raise TraceError("trace lacks complete tool-event capture assertion")
    if not isinstance(obj.get("host_version"), str) or not obj["host_version"].strip():
        raise TraceError("host version missing")
    if not isinstance(obj.get("model"), str) or not obj["model"].strip():
        raise TraceError("pinned model missing")
    events = obj.get("events")
    if not isinstance(events, list) or not events:
        raise TraceError("trace events missing")
    for e in events:
        if not isinstance(e, dict) or e.get("type") not in EVENT_TYPES:
            raise TraceError("unrecognized trace event")
        kind = e["type"]
        if kind == "skill_load" and (not isinstance(e.get("skill_id"), str) or not isinstance(e.get("path"), str)):
            raise TraceError("incomplete skill-load event")
        if kind == "intent" and not isinstance(e.get("value"), str):
            raise TraceError("incomplete intent event")
        if kind == "phase_exit" and (e.get("phase") not in ("P0", "P1", "P2", "P3", "P4", "P5", "P6")
                                     or e.get("status") not in STATUSES):
            raise TraceError("invalid phase exit event")
        if kind == "tool_action" and e.get("effect") not in ("READ", "WRITE", "DESTRUCTIVE"):
            raise TraceError("unclassified tool-action effect")
        if kind == "verification":
            if e.get("axis") not in EVIDENCE_AXES or e.get("status") not in STATUSES:
                raise TraceError("invalid verification axis/status")
            if e.get("status") == "PASS" and (
                not isinstance(e.get("artifact_ref"), str)
                or not e["artifact_ref"].strip()
                or not HEX64.fullmatch(str(e.get("artifact_sha256", "")))
            ):
                raise TraceError("verification PASS lacks an evidence reference and digest")
    return obj, hashlib.sha256(data).hexdigest()
