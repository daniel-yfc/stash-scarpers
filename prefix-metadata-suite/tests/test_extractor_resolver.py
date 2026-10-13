"""Tests for extractor and resolver (spec §2: pure functions, pytest)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from extractor import extract, extract_from_path
from resolver import PrefixTable, ResolveResult, effective_studio

TABLE_DIR = Path(__file__).parent.parent / "prefix-table"


class TestExtractor:
    def test_simple_prefix_dash(self):
        r = extract(basename="KKE-0305.mp4")
        assert r.code == "KKE-0305"
        assert r.prefix == "KKE"
        assert r.source == "basename"

    def test_prefix_no_dash(self):
        r = extract(basename="ACSM001.mp4")
        assert r.prefix == "ACSM"

    def test_gv_compound(self):
        r = extract(basename="GV-DSK12.mp4")
        assert r.prefix == "GV-DSK"
        assert r.code == "GV-DSK-12"

    def test_folder_priority(self):
        # Folder wins over basename
        r = extract(basename="random_title.mp4", folder="KO - EAST")
        # "KO - EAST" has no code pattern; basename has none either
        assert r.code is None

    def test_folder_with_code(self):
        r = extract(basename="video.mp4", folder="[KKE-0305]")
        assert r.prefix == "KKE"
        assert r.source == "folder"

    def test_no_match(self):
        r = extract(basename="赤兔 CHITU - MASSAGE SUMMER PLUS.mp4")
        assert r.code is None
        assert r.source is None

    def test_full_path_windows(self):
        r = extract_from_path("T:\\share\\GV-Japan\\KO - EAST\\KKE-0305.mp4")
        assert r.prefix == "KKE"

    def test_full_path_unix(self):
        r = extract_from_path("/data/G@MES/GV-DSK12.mp4")
        assert r.prefix == "GV-DSK"


class TestResolver:
    @classmethod
    def setup_class(cls):
        cls.table = PrefixTable(TABLE_DIR)

    def test_unique_match(self):
        r = self.table.resolve("KRA")
        assert r.confidence == "unique"
        assert r.studio == "KO COMPANY"

    def test_ambiguous_kke(self):
        r = self.table.resolve("KKE")
        assert r.confidence == "ambiguous"
        assert "label" in r.ambiguous_fields
        assert r.studio == "KO COMPANY"
        assert r.sub_studio == "KO East"

    def test_absent(self):
        r = self.table.resolve("ZZZZ")
        assert r.confidence == "absent"
        assert r.studio is None

    def test_none_prefix(self):
        r = self.table.resolve(None)
        assert r.confidence == "absent"

    def test_longest_match(self):
        # GV-DSK should match GV-DSK, not GV-
        r = self.table.resolve("GV-DSK")
        assert r.matched_prefix == "GV-DSK"

    def test_case_insensitive(self):
        r = self.table.resolve("kke")
        assert r.confidence == "ambiguous"


def _res(studio=None, sub_studio=None, label=None, series=None):
    return ResolveResult(
        studio=studio, sub_studio=sub_studio, label=label, series=series,
        confidence="unique",
    )


class TestEffectiveStudio:
    def test_label_wins(self):
        assert effective_studio(_res("S", "SS", "L", "SE")) == "L"

    def test_series_fallback(self):
        assert effective_studio(_res("S", "SS", None, "SE")) == "SE"

    def test_sub_studio_fallback(self):
        assert effective_studio(_res("S", "SS", None, None)) == "SS"

    def test_category_sub_studio_skipped(self):
        # 配信 / 独占 / オリジナル are categories, not studios.
        for cat in ("配信", "独占", "オリジナル"):
            assert effective_studio(_res("S", cat, None, None)) == "S"

    def test_studio_fallback(self):
        assert effective_studio(_res("S", None, None, None)) == "S"

    def test_matches_live_table(self):
        # KGS resolves to label 合法ショタ: Doctor and Enrich must agree.
        table = PrefixTable(TABLE_DIR)
        assert effective_studio(table.resolve("KGS")) == "合法ショタ"

    def test_version_info(self):
        table = PrefixTable(TABLE_DIR)
        vi = table.version_info
        assert set(vi) == {"meta_version", "meta_generated_at",
                           "fingerprint", "files"}
        assert len(vi["fingerprint"]) == 12
        assert vi["files"] > 0
        # Fingerprint is stable across loads of the same files.
        assert PrefixTable(TABLE_DIR).version_info == vi
