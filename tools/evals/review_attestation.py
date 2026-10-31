#!/usr/bin/env python3
"""Verify an independent review signature over one exact host trace.

The reviewer key is supplied outside Git and must not be available to the
evaluated agent. A signature records a human/trusted adapter's assertion; it
cannot prove host provenance independently of that trust relationship.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

HEX64 = set("0123456789abcdef")
FIELDS = (
    "version", "case_id", "host", "repeat", "repo_sha", "skill_sha256",
    "trace_sha256", "reviewer", "host_origin_verified",
    "tool_capture_verified", "workspace_verified", "artifacts_verified",
)

def canonical_bytes(record: dict) -> bytes:
    return json.dumps(
        {k: record[k] for k in FIELDS}, sort_keys=True,
        ensure_ascii=True, separators=(",", ":"),
    ).encode("utf-8")


def load_review_records(path: Path | None) -> dict[tuple[str, str, int], dict]:
    if path is None:
        return {}
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
        raise ValueError("review records missing, linked, or oversized")
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or doc.get("version") != 1 or not isinstance(doc.get("reviews"), list):
        raise ValueError("invalid independent review manifest")
    reviews = {}
    for entry in doc["reviews"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("repeat"), int):
            raise ValueError("invalid review record")
        key = (entry.get("case_id"), entry.get("host"), entry["repeat"])
        if key in reviews:
            raise ValueError("duplicate review record")
        reviews[key] = entry
    return reviews


def is_attested(
    record: dict | None, trace: dict, trace_digest: str,
    reviewer_key: bytes | None,
) -> bool:
    if not record or not reviewer_key or len(reviewer_key) < 32:
        return False
    if trace.get("capture_kind") != "host_export":
        return False
    if any(k not in record for k in (*FIELDS, "signature")):
        return False
    if set(record) != set((*FIELDS, "signature")):
        return False
    if record["version"] != 1 or not isinstance(record["reviewer"], str) or not record["reviewer"].strip():
        return False
    if not all(record.get(k) is True for k in (
        "host_origin_verified", "tool_capture_verified",
        "workspace_verified", "artifacts_verified",
    )):
        return False
    expected = {
        "case_id": trace.get("case_id"),
        "host": trace.get("host"),
        "repeat": trace.get("repeat"),
        "repo_sha": trace.get("repo_sha"),
        "skill_sha256": trace.get("skill_sha256"),
        "trace_sha256": trace_digest,
    }
    if any(record.get(k) != value for k, value in expected.items()):
        return False
    signature = record["signature"]
    if not isinstance(signature, str) or len(signature) != 64 or any(c not in HEX64 for c in signature):
        return False
    computed = hmac.new(reviewer_key, canonical_bytes(record), hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, signature)
