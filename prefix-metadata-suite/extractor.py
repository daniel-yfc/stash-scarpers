"""Product code extractor — pure functions, no Stash dependency.

Path formats in this library:
  data/Japan/{Studio}/{code} {title}.mp4    e.g. data/Japan/Acceed/ACSM165[ACD162] ...
  data/Google/Asian/...                      descriptive names, usually no code

Priority: basename (has code) → folder path components (studio name)
"""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractResult:
    code: str | None       # full code e.g. "ACSM165"
    prefix: str | None     # prefix part e.g. "ACSM"
    source: str | None     # "basename" | "folder" | None
    studio_from_folder: str | None = None  # e.g. "Acceed" from data/Japan/Acceed/


# Denylist: patterns that look like codes but aren't studio prefixes
# (personal IDs, usernames, etc.)
_DENYLIST = {
    "THHY", "KBEYES",  # PnP/Asian personal IDs (user-confirmed 2026-10-12)
    "GSL", "HAO", "DAYO", "CZDG", "WTHC",  # not prefixes (user-confirmed 2026-10-12)
    "TACH", "SIR", "JEFF", "BOSS", "BTM", "HENG", "BARD", "POLP", "LING", "HI", "PNP",  # not prefixes (user-confirmed 2026-10-12)
}

# Bracketed alternate code: [ACD162]
_BRACKET_RE = re.compile(r"\[([A-Z]{2,6}\d{2,5}[A-Z]?)\]")

# Standard: PREFIX-1234 or PREFIX1234
# Prefix: 2-4 uppercase letters (strict, avoid false positives like OF-lion)
_CODE_RE = re.compile(
    r"(?<![A-Z0-9])"
    r"([A-Z]{2,4}(?:-[A-Z]{2,4})?)"  # prefix, optionally PREFIX-SUB
    r"-?"
    r"(\d{3,5})"                      # numeric part (3-5 digits, strict)
    r"(?![0-9])"
)

# GV- compound: GV-DSK12
_GV_RE = re.compile(r"(?<![A-Z0-9])(GV-[A-Z]{2,4})-?(\d{1,4})(?![0-9])")


def _extract_from_text(text: str) -> tuple[str | None, str | None]:
    if not text:
        return None, None
    upper = text.upper()
    # 1. GV- compound (most specific)
    m = _GV_RE.search(upper)
    if m and m.group(1) not in _DENYLIST:
        return f"{m.group(1)}-{m.group(2)}", m.group(1)
    # 2. Standard code (non-bracketed preferred)
    #    Remove bracketed parts first to prefer the main code
    no_bracket = _BRACKET_RE.sub("", upper)
    m = _CODE_RE.search(no_bracket)
    if m:
        prefix = m.group(1)
        if prefix not in _DENYLIST:
            num = m.group(2)
            return f"{prefix}-{num}", prefix
    # 3. Bracketed code as fallback (stricter: 3+ letter prefix)
    m = _BRACKET_RE.search(upper)
    if m:
        full = m.group(1)
        prefix_m = re.match(r"([A-Z]{3,})", full)
        if prefix_m and prefix_m.group(1) not in _DENYLIST:
            return full, prefix_m.group(1)
    return None, None


def extract(basename: str = "", folder: str = "", url: str = "") -> ExtractResult:
    """Extract product code. Basename first (has code), then folder for studio."""
    # 1. Try basename for product code
    code, prefix = _extract_from_text(basename)
    if code:
        studio = _studio_from_folder(folder)
        return ExtractResult(code=code, prefix=prefix, source="basename",
                             studio_from_folder=studio)

    # 2. Try folder path for code (e.g. folder named "[KKE-0305]")
    code, prefix = _extract_from_text(folder)
    if code:
        studio = _studio_from_folder(folder)
        return ExtractResult(code=code, prefix=prefix, source="folder",
                             studio_from_folder=studio)

    # 3. No code, but folder may still give studio
    studio = _studio_from_folder(folder)
    if studio:
        return ExtractResult(code=None, prefix=None, source="folder",
                             studio_from_folder=studio)

    return ExtractResult(code=None, prefix=None, source=None)


def _studio_from_folder(folder: str) -> str | None:
    """Extract studio from path like data/Japan/Acceed/..."""
    if not folder:
        return None
    parts = folder.replace("\\", "/").split("/")
    # Look for Japan/{Studio} pattern
    for i, p in enumerate(parts):
        if p.lower() == "japan" and i + 1 < len(parts):
            return parts[i + 1]
        if p.lower() == "asian" and i + 1 < len(parts):
            # Asian subfolders are categories, not studios; skip
            pass
    return None


def extract_from_path(full_path: str) -> ExtractResult:
    normalized = full_path.replace("\\", "/")
    # Split into folder path + basename
    if "/" in normalized:
        folder_path, basename = normalized.rsplit("/", 1)
    else:
        folder_path, basename = "", normalized
    basename_no_ext = re.sub(r"\.[a-zA-Z0-9]{2,4}$", "", basename)
    return extract(basename=basename_no_ext, folder=folder_path)
