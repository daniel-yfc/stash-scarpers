#!/usr/bin/env python3
"""Validate structured evidence metadata, never live runtime behavior."""

from datetime import datetime
from hashlib import sha256
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
import yaml

ROOT = Path(__file__).resolve().parents[1]
STAGES = (
    "schema", "policy", "fixture", "live_search", "live_detail", "live_cdp", "production"
)
ALLOWED_ARTIFACT_ROOTS = ("evidence/artifacts/", "tests/fixtures/")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def validate(record: dict, root: Path) -> list[str]:
    errors = []
    if not isinstance(record, dict) or not isinstance(record.get("scraper"), str):
        return ["invalid record or scraper name"]
    states = record.get("states")
    if not isinstance(states, dict) or set(states) != set(STAGES):
        return ["states must contain exactly the seven named evidence stages"]
    for stage in STAGES:
        state = states[stage]
        if not isinstance(state, dict) or state.get("status") not in {"verified", "unverified"}:
            errors.append(f"{stage}: invalid status")
            continue
        if state["status"] == "unverified":
            if set(state) != {"status"}:
                errors.append(f"{stage}: unverified state must not carry artifact or provenance")
            continue
        required = {"status", "artifact", "sha256", "captured_at", "source_url", "revision"}
        if set(state) != required:
            errors.append(f"{stage}: incomplete provenance fields")
            continue
        artifact = state["artifact"]
        if not isinstance(artifact, str) or not artifact.startswith(ALLOWED_ARTIFACT_ROOTS) or ".." in Path(artifact).parts:
            errors.append(f"{stage}: unsafe artifact path")
            continue
        location = root / artifact
        if not location.is_file() or location.is_symlink():
            errors.append(f"{stage}: artifact absent or symlink")
        elif not HEX64.fullmatch(str(state["sha256"])) or sha256(location.read_bytes()).hexdigest() != state["sha256"]:
            errors.append(f"{stage}: artifact digest mismatch")
        try:
            captured = datetime.fromisoformat(str(state["captured_at"]).replace("Z", "+00:00"))
            if captured.tzinfo is None:
                raise ValueError
        except ValueError:
            errors.append(f"{stage}: timestamp lacks timezone or is invalid")
        source = urlsplit(str(state["source_url"]))
        if source.scheme != "https" or not source.hostname or source.username or source.password or source.query or source.fragment:
            errors.append(f"{stage}: unsafe or incomplete source URL")
        if not HEX40.fullmatch(str(state["revision"])):
            errors.append(f"{stage}: revision must be a full commit SHA")
    return errors


def main() -> int:
    directory = ROOT / "evidence" / "status"
    files = sorted(directory.glob("*.yml")) if directory.exists() else []
    if not files:
        print("EVIDENCE CONTRACT: UNVERIFIED (no status records)")
        return 1
    failures = []
    for file in files:
        try:
            record = yaml.safe_load(file.read_text(encoding="utf-8"))
            failures.extend(f"{file.relative_to(ROOT)}: {error}" for error in validate(record, ROOT))
        except (OSError, yaml.YAMLError):
            failures.append(f"{file.relative_to(ROOT)}: cannot load status record")
    for failure in failures:
        print(f"- {failure}", file=sys.stderr)
    print(f"Evidence records checked: {len(files)}; failures: {len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
