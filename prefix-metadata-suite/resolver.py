"""Prefix resolver — pure functions, no Stash dependency.

Resolves a product-code prefix against the prefix table JSONs.
Longest-prefix match wins (spec §4.1).
"""
import hashlib
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


# Sub-Studio values that are distribution categories, not real studios.
# When these are the only Sub-Studio, Enrich falls through to Studio.
CATEGORY_SUB_STUDIOS = {"オリジナル", "独占", "配信"}


def effective_studio(res: ResolveResult) -> str | None:
    """Studio value Enrich writes / Doctor compares.

    Priority: Label > Series > Sub-Studio > Studio
    (user 2026-10-12: Label/Series 當成 Studio 填入).
    Shared by Doctor and Enrich so their verdicts agree.
    """
    if res.label:
        return res.label
    if res.series:
        return res.series
    if res.sub_studio and res.sub_studio not in CATEGORY_SUB_STUDIOS:
        return res.sub_studio
    return res.studio


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
        # Real table version, computed from the files actually loaded.
        # _meta.json's declared version is included for reference but is
        # NOT trusted on its own (it went stale on 2026-10-12: declared
        # v20261012-1012 while JSONs kept changing until 21:48).
        self.version_info = self._compute_version(table_dir)

    @staticmethod
    def _compute_version(table_dir: Path) -> dict:
        meta = {}
        meta_path = Path(table_dir) / "_meta.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                meta = {}
        h = hashlib.sha1()
        count = 0
        for jf in sorted(Path(table_dir).glob("*.json")):
            if jf.name == "_meta.json":
                continue
            h.update(jf.name.encode("utf-8"))
            h.update(b"\0")
            h.update(hashlib.sha1(jf.read_bytes()).digest())
            count += 1
        return {
            "meta_version": meta.get("table_version"),
            "meta_generated_at": meta.get("generated_at"),
            "fingerprint": h.hexdigest()[:12],
            "files": count,
        }

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
