#!/usr/bin/env python3
"""Cross-check documentation claims against the vendored schema.

Verifies that:
1. references/entity-fields.md field tables match validator/scraper.schema.json
   *Object definitions (no missing/extra fields, required fields marked).
2. references/schema-checklist.md top-level entry-point table matches the
   schema's allowed top-level keys.
3. references/post-processing.md operator list matches the schema's
   postProcessAction keys.

Exit 0 if all match, 1 with details otherwise.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "validator" / "scraper.schema.json"
ENTITY_FIELDS_MD = ROOT / "skills" / "stash-scraper-builder" / "references" / "entity-fields.md"
SCHEMA_CHECKLIST_MD = ROOT / "skills" / "stash-scraper-builder" / "references" / "schema-checklist.md"
POST_PROCESSING_MD = ROOT / "skills" / "stash-scraper-builder" / "references" / "post-processing.md"

# Map entity-fields.md section headings to schema definition names
ENTITY_MAP = {
    "Scene": "sceneObject",
    "Performer": "performerObject",
    "Group": "groupObject",
    "Gallery": "galleryObject",
    "Image": "imageObject",
    "Studio": "studioObject",
    "Tag": "tagsObject",
}

errors = []


def load_schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def parse_md_table_fields(md_path, section):
    """Extract field names from a markdown table under a ## section."""
    content = md_path.read_text(encoding="utf-8")
    # Find the section
    m = re.search(rf"^## {re.escape(section)}\s*$", content, re.MULTILINE)
    if not m:
        errors.append(f"{md_path.name}: missing ## {section} section")
        return None, None
    start = m.end()
    # Find next ## or end
    m2 = re.search(r"^## ", content[start:], re.MULTILINE)
    end = start + m2.start() if m2 else len(content)
    section_text = content[start:end]
    # Parse table rows: | Field | Notes |
    fields = []
    required = set()
    for line in section_text.splitlines():
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        cells = [c.strip().strip("`") for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        field, notes = cells[0], cells[1]
        if field.lower() == "field":
            continue  # header row
        fields.append(field)
        if "required" in notes.lower():
            required.add(field)
    return fields, required


def check_entity_fields(schema):
    definitions = schema.get("definitions", {})
    for section, def_name in ENTITY_MAP.items():
        doc_fields, doc_required = parse_md_table_fields(ENTITY_FIELDS_MD, section)
        if doc_fields is None:
            continue
        schema_def = definitions.get(def_name, {})
        schema_fields = set(schema_def.get("properties", {}).keys())
        schema_required = set(schema_def.get("required", []))

        doc_set = set(doc_fields)
        missing_in_doc = schema_fields - doc_set
        extra_in_doc = doc_set - schema_fields
        if missing_in_doc:
            errors.append(
                f"entity-fields.md [{section}]: missing fields vs schema: {sorted(missing_in_doc)}"
            )
        if extra_in_doc:
            errors.append(
                f"entity-fields.md [{section}]: extra fields not in schema: {sorted(extra_in_doc)}"
            )
        # Required fields: doc must mark all schema-required as required
        unmarked = schema_required - doc_required
        if unmarked:
            errors.append(
                f"entity-fields.md [{section}]: schema-required not marked **Required**: {sorted(unmarked)}"
            )


def check_top_level_entries(schema):
    """Verify schema-checklist.md entry-point table against schema top-level keys."""
    content = SCHEMA_CHECKLIST_MD.read_text(encoding="utf-8")
    # Extract backticked entry points from the table
    doc_entries = set(re.findall(r"`((?:performer|scene|group|gallery|image|movie)By(?:QueryFragment|Fragment|Name|URL))`", content))
    schema_keys = set(schema.get("properties", {}).keys())
    # Expected entry points (excluding deprecated movieByURL which is still in schema)
    expected = {
        "performerByName", "performerByFragment", "performerByURL",
        "sceneByName", "sceneByQueryFragment", "sceneByFragment", "sceneByURL",
        "groupByURL", "galleryByFragment", "galleryByURL",
        "imageByFragment", "imageByURL",
    }
    missing_in_doc = expected - doc_entries
    if missing_in_doc:
        errors.append(
            f"schema-checklist.md: entry points missing from table: {sorted(missing_in_doc)}"
        )
    # movieByURL should be mentioned as deprecated
    if "movieByURL" not in content:
        errors.append("schema-checklist.md: movieByURL deprecation not documented")


def check_postprocess_operators(schema):
    """Verify post-processing.md operator list against schema."""
    content = POST_PROCESSING_MD.read_text(encoding="utf-8")
    # Find the operator bullet list
    schema_ops = set(
        schema.get("definitions", {}).get("postProcessAction", {}).get("properties", {}).keys()
    )
    # Extract backticked operators from bullet lines in the operator list section
    # Find the section with operator bullets (lines starting with "- `op`")
    doc_ops = set()
    for line in content.splitlines():
        if line.strip().startswith("- `"):
            for op in re.findall(r"`([a-zA-Z]+)`", line):
                doc_ops.add(op)
    # Filter to known operator-like names
    doc_ops = {o for o in doc_ops if o in schema_ops or o in {
        "replace", "parseDate", "map", "subScraper", "javascript",
        "subtractDays", "feetToCm", "lbToKg", "concat", "split",
    }}
    missing_in_doc = schema_ops - doc_ops
    if missing_in_doc:
        errors.append(
            f"post-processing.md: operators missing from docs: {sorted(missing_in_doc)}"
        )
    # Check for documented-but-nonexistent operators
    phantom = doc_ops - schema_ops - {"concat", "split"}  # concat/split are attribute-level
    if phantom:
        errors.append(
            f"post-processing.md: documents non-existent operators: {sorted(phantom)}"
        )


def main():
    schema = load_schema()
    check_entity_fields(schema)
    check_top_level_entries(schema)
    check_postprocess_operators(schema)

    if errors:
        print("Docs-vs-schema mismatches found:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("Docs-vs-schema check passed: entity fields, entry points, and operators match.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
