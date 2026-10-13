"""Prefix resolver — pure functions, no Stash dependency.

Resolves a product-code prefix against the prefix table JSONs.
Longest-prefix match wins (spec §4.1).
"""
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ResolveResult:
    studio: str | None
    sub_studio: str | None
    label: str | None
    series: str | None
    confidence: str          # "unique" | "ambiguous" | "absent"
    ambiguous_fields: tuple = ()
    matched_prefix: str | None = None
    table_id: str | None = None


class PrefixTable:
    def __init__(self, table_dir: str | Path):
        self.entries = []
        table_dir = Path(table_dir)
        for jf in sorted(table_dir.glob("*.json")):
            if jf.name == "_meta.json":
                continue
            data = json.loads(jf.read_text(encoding="utf-8"))
            self.entries.extend(data)
        # Sort by prefix length desc for longest-match.
        # Use dash-stripped length so "KG-" (2) doesn't tie with "KGS" (3)
        # on raw length; exact matches then win over startswith ties.
        self.entries.sort(
            key=lambda e: len((e["match"]["value"] or "").rstrip("-")),
            reverse=True,
        )

    def resolve(self, prefix: str | None) -> ResolveResult:
        """Longest-prefix match. Dash-insensitive. Returns absent if no match."""
        if not prefix:
            return ResolveResult(
                studio=None, sub_studio=None, label=None, series=None,
                confidence="absent",
            )
        # Normalize: uppercase, strip trailing dashes
        prefix_norm = prefix.upper().rstrip("-")
        # Two passes: exact matches first, then startswith.
        # This ensures "KGS" hits koshop:KGS before hunkch_3rd:KG-
        # even when sort order ties.
        for exact_only in (True, False):
            for entry in self.entries:
                table_prefix = (entry["match"]["value"] or "").upper().rstrip("-")
                if not table_prefix:
                    continue
                is_exact = prefix_norm == table_prefix
                if exact_only and not is_exact:
                    continue
                if is_exact or prefix_norm.startswith(table_prefix):
                    ambiguous = tuple(entry.get("ambiguous_fields", []))
                    return ResolveResult(
                    studio=entry.get("studio"),
                    sub_studio=entry.get("sub_studio"),
                    label=entry.get("label"),
                    series=entry.get("series"),
                    confidence="ambiguous" if ambiguous else "unique",
                    ambiguous_fields=ambiguous,
                    matched_prefix=entry["match"]["value"],
                    table_id=entry["id"],
                )
        return ResolveResult(
            studio=None, sub_studio=None, label=None, series=None,
            confidence="absent",
        )

    def resolve_code(self, code: str | None, extractor_prefix: str | None = None) -> ResolveResult:
        """Resolve from a full code; falls back to extractor-derived prefix."""
        return self.resolve(extractor_prefix or code)
