#!/usr/bin/env python3
"""Validate the machine-readable documentation index."""

from pathlib import Path
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "docs" / "index.yml"
ALLOWED_STATUS = {"draft", "active", "deprecated", "archived"}
ALLOWED_LAYER = {"repository", "skill", "template", "status", "tool"}
ID_PATTERN = re.compile(r"^(DOC|REF|TPL|STATUS|SKILL)(?:-[A-Z0-9]+)*-\d{2}$")
REQUIRED_FIELDS = {"doc_id", "title", "path", "layer", "status", "intents"}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    try:
        data = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def expected_markdown_paths() -> set[str]:
    expected = {
        "README.md",
        "AGENTS.md",
        "CLAUDE.md",
        "CONTRIBUTING.md",
        "scrapers/README.md",
        "templates/README.md",
        "tools/README.md",
        "tools/SRB-2.0-documentation.md",
        "validator/README.md",
        "skills/stash-scraper-builder/SKILL.md",
    }
    expected.update(path.relative_to(ROOT).as_posix() for path in (ROOT / "docs").glob("*.md"))
    expected.update(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "skills" / "stash-scraper-builder" / "references").glob("*.md")
    )
    return expected


def main() -> int:
    errors: list[str] = []

    if not INDEX_PATH.exists():
        fail(errors, "docs/index.yml is missing")
    if not (ROOT / ".prettierrc.yml").exists():
        fail(errors, ".prettierrc.yml is missing")
    if not (ROOT / ".prettierignore").exists():
        fail(errors, ".prettierignore is missing")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    data = yaml.safe_load(INDEX_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != 1:
        fail(errors, "docs/index.yml must declare version: 1")
        data = {"documents": []}

    documents = data.get("documents")
    if not isinstance(documents, list):
        fail(errors, "docs/index.yml must contain a documents list")
        documents = []

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()

    for position, document in enumerate(documents, start=1):
        label = f"document #{position}"
        if not isinstance(document, dict):
            fail(errors, f"{label} must be a mapping")
            continue

        missing = REQUIRED_FIELDS - set(document)
        if missing:
            fail(errors, f"{label} missing fields: {', '.join(sorted(missing))}")
            continue

        doc_id = document["doc_id"]
        path_value = document["path"]
        status = document["status"]
        layer = document["layer"]
        intents = document["intents"]

        if not isinstance(doc_id, str) or not ID_PATTERN.match(doc_id):
            fail(errors, f"{label} has invalid doc_id: {doc_id!r}")
        elif doc_id in seen_ids:
            fail(errors, f"duplicate doc_id: {doc_id}")
        else:
            seen_ids.add(doc_id)

        if not isinstance(path_value, str) or not path_value:
            fail(errors, f"{doc_id}: path must be a non-empty string")
            continue

        normalized_path = Path(path_value).as_posix()
        if normalized_path in seen_paths:
            fail(errors, f"duplicate indexed path: {normalized_path}")
        seen_paths.add(normalized_path)

        markdown_path = ROOT / normalized_path
        if not markdown_path.exists():
            fail(errors, f"{doc_id}: indexed path does not exist: {normalized_path}")
        elif markdown_path.suffix.lower() != ".md":
            fail(errors, f"{doc_id}: indexed path is not Markdown: {normalized_path}")
        else:
            metadata = frontmatter(markdown_path)
            if "doc_id" in metadata and metadata["doc_id"] != doc_id:
                fail(
                    errors,
                    f"{doc_id}: front matter doc_id {metadata['doc_id']!r} does not match index",
                )

        if status not in ALLOWED_STATUS:
            fail(errors, f"{doc_id}: invalid status {status!r}")
        if layer not in ALLOWED_LAYER:
            fail(errors, f"{doc_id}: invalid layer {layer!r}")
        if not isinstance(intents, list) or not intents or not all(isinstance(item, str) for item in intents):
            fail(errors, f"{doc_id}: intents must be a non-empty string list")

        for relation in ("read_after", "read_before"):
            for related_id in document.get(relation, []) or []:
                if related_id not in seen_ids:
                    fail(errors, f"{doc_id}: {relation} references unknown or later ID {related_id!r}")

    indexed_paths = seen_paths
    missing_paths = sorted(expected_markdown_paths() - indexed_paths)
    for path in missing_paths:
        fail(errors, f"Markdown document is not indexed: {path}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"Documentation index OK: {len(seen_ids)} documents")
    return 0


if __name__ == "__main__":
    sys.exit(main())
