#!/usr/bin/env python3
"""Repository safeguard audit. Reports locations and rule IDs, never values."""

from pathlib import Path
import re
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
SECRET_RULES = {
    "cookie-assignment": re.compile(r"(?i)(?:set-cookie|cf_clearance)\s*[:=]"),
    "credential-assignment": re.compile(r"(?i)(?:password|api[_-]?key|session[_-]?token)\s*[:=]\s*\S+"),
}


def main() -> int:
    errors = []
    for path in sorted((ROOT / "scrapers").rglob("*.yml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            errors.append(f"yaml-parse: {path.relative_to(ROOT)}: {exc.__class__.__name__}")
            continue
        if not isinstance(data, dict):
            errors.append(f"yaml-shape: {path.relative_to(ROOT)}")
            continue
        relative = path.relative_to(ROOT).as_posix()
        cookies = ((data.get("driver") or {}).get("cookies"))
        if cookies and relative.startswith("scrapers/") and "/" not in relative.removeprefix("scrapers/"):
            errors.append(f"public-cookies: {relative}")

    for path in sorted((ROOT / "evidence").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if re.search(r"fixture verification.*\bDONE\b", text, re.I | re.S):
            errors.append(f"evidence-overclaim: {path.relative_to(ROOT)}")

    for path in [ROOT / "tools" / "verify-scraper-fixtures.mjs"]:
        if not path.exists():
            errors.append(f"missing-control: {path.relative_to(ROOT)}")

    for path in sorted(ROOT.rglob("*")):
        if path.suffix.lower() not in {".yml", ".yaml", ".md", ".js", ".mjs", ".py"}:
            continue
        if "tools/tests" in path.as_posix():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for rule, pattern in SECRET_RULES.items():
            if pattern.search(text):
                errors.append(f"{rule}: {path.relative_to(ROOT)}")

    if errors:
        print("Safeguard audit failed")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Safeguard audit passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
