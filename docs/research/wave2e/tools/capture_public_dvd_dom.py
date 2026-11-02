#!/usr/bin/env python3
"""Anonymous, read-only BRAVO DVD public-page capture; NEVER touches Stash.

Usage:
  pip install playwright lxml
  python -m playwright install chromium
  python capture_public_dvd_dom.py --private-output /path/to/restricted-folder \
      https://www.bravo-japan.com/dvds/234 https://www.bravo-japan.com/dvds/084

The sanitized HTML is a structural evidence CANDIDATE, not an automatically
publishable DOM; manual sensitive-material screening and XPath QA are required.
"""
import argparse
import asyncio
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from lxml import html
from playwright.async_api import async_playwright

SITE = {"bravo-japan.com", "www.bravo-japan.com"}
MEDIA = SITE | {"static.wixstatic.com", "video.wixstatic.com"}
URL_PATH = re.compile(r"^/dvds/[0-9]{1,9}/?$")
PUBLIC_META = {"description", "keywords"}
OG_META = {"og:title", "og:description", "og:image", "og:url", "og:site_name", "og:type"}
DROP = "//script | //style | //iframe | //form | //input | //textarea | //template | //noscript | //svg"
SENSITIVE = re.compile(rb"(?i)(authorization\s*[:=]|bearer\s+[a-z0-9_.-]+|(?:session|api[_-]?key|access[_-]?token|secret|password|set-cookie)\s*[:=])")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def public_url(value, domains=MEDIA):
    try:
        u = urlsplit(value)
    except ValueError:
        return None
    if u.scheme != "https" or u.hostname not in domains or u.username or u.password:
        return None
    return urlunsplit(("https", u.hostname, u.path, "", ""))


def plain(node):
    return " ".join(node.itertext()).replace("\u200b", "").strip()


def sanitize_dom(raw):
    tree = html.fromstring(raw)
    for el in list(tree.xpath(DROP)):
        if el.getparent() is not None:
            el.drop_tree()
    for comment in list(tree.xpath("//comment()")):
        if comment.getparent() is not None:
            comment.getparent().remove(comment)
    for el in tree.iter():
        if not isinstance(el.tag, str):
            continue
        tag = el.tag.lower()
        allowed = {"id", "class", "data-testid"}
        if tag == "link" and el.get("rel") == "canonical":
            allowed |= {"rel", "href"}
        elif tag == "meta":
            name, prop = el.get("name"), el.get("property")
            if name in PUBLIC_META or prop in OG_META:
                allowed |= {"name", "property", "content"}
        elif tag == "img":
            allowed |= {"src", "alt", "width", "height"}
        elif tag == "video":
            allowed |= {"poster"}
        for key in list(el.attrib):
            if key not in allowed:
                del el.attrib[key]
        for key in ("href", "src", "poster"):
            if key in el.attrib:
                filtered = public_url(el.get(key), SITE if key == "href" else MEDIA)
                if filtered is None:
                    del el.attrib[key]
                else:
                    el.set(key, filtered)
        if tag == "meta" and el.get("property") in {"og:image", "og:url"}:
            content = el.get("content")
            filtered = public_url(content, MEDIA if el.get("property") == "og:image" else SITE)
            if filtered is None:
                el.attrib.pop("content", None)
            else:
                el.set("content", filtered)
        for key in ("id", "data-testid"):
            if key in el.attrib and not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]{0,80}", el.get(key)):
                del el.attrib[key]
        if "class" in el.attrib and not re.fullmatch(r"[a-zA-Z0-9_\s-]{1,512}", el.get("class")):
            del el.attrib["class"]
    result = html.tostring(tree, encoding="utf-8", method="html")
    if SENSITIVE.search(result):
        raise ValueError("Sensitive-material signature in sanitized HTML; refuse to write DOM")
    return result


def read_identity(page, requested):
    parsed = html.fromstring(page)
    canonical = parsed.xpath("//link[@rel='canonical']/@href")
    headings = parsed.xpath("//h1 | //h2 | //h3")
    label_count = sum(plain(el) == "\u54c1\u756a" for el in headings)
    body = " ".join(parsed.xpath("//body//text()"))
    challenge = ("just a moment" in " ".join(parsed.xpath("//title/text()")).lower()) or "cf-challenge" in page
    normalized = [public_url(x, SITE) for x in canonical]
    wanted = public_url(requested, SITE)
    matches = len(normalized) == 1 and normalized[0] == wanted
    return {"canonical": normalized, "canonical_matches_requested": matches,
            "code_label_heading_count": label_count, "has_code_label_text": "\u54c1\u756a" in body,
            "challenge_detected": challenge,
            "structure_ready": matches and "\u54c1\u756a" in body and not challenge}


async def capture(context, target, output):
    page = await context.new_page()
    record = {"requested_url": target, "captured_at_utc": utc_now(),
              "http_status": None, "final_url": None, "redirect_chain": [],
              "browser": "playwright chromium isolated headless; no login/profile",
              "classification": "NOT_OBSERVED", "sanitized_html": None, "sha256": None}
    try:
        response = await page.goto(target, wait_until="domcontentloaded", timeout=45000)
        if response is not None:
            record["http_status"] = response.status
            req = response.request
            while req is not None:
                record["redirect_chain"].append(public_url(req.url, SITE) or "[EXTERNAL_URL_SUPPRESSED]")
                req = req.redirected_from
            record["redirect_chain"].reverse()
        record["final_url"] = public_url(page.url, SITE) or "[EXTERNAL_URL_SUPPRESSED]"
        if not public_url(page.url, SITE):
            record["classification"] = "REDIRECT_OUTSIDE_ALLOWED_DOMAIN"
            return record
        try:
            await page.wait_for_function("document.body && document.body.innerText.includes('\\u54c1\\u756a')", timeout=15000)
        except Exception:
            record["wait_for_product_label"] = "TIMED_OUT_OR_ABSENT"
        await page.wait_for_timeout(1200)
        raw = await page.content()
        ident = read_identity(raw, target)
        record.update(ident)
        if record["http_status"] != 200 or not ident["structure_ready"]:
            record["classification"] = "HTTP_OR_PRODUCT_IDENTITY_NOT_VERIFIED"
            return record
        safe = sanitize_dom(raw)
        name = urlsplit(target).path.rstrip("/").split("/")[-1]
        filename = f"dvd-{name}.sanitized-rendered.html"
        destination = output / filename
        destination.write_bytes(safe)
        record.update({"classification": "SANITIZED_STRUCTURAL_DOM_CANDIDATE_MANUAL_REVIEW_REQUIRED",
                       "sanitized_html": filename, "sha256": hashlib.sha256(safe).hexdigest(),
                       "bytes": len(safe), "public_release_authorized": False})
        return record
    except Exception as exc:
        record["classification"] = "FETCH_OR_SANITIZER_FAILED"
        record["error_type"] = type(exc).__name__
        return record
    finally:
        await page.close()


async def main_async(args):
    os.umask(0o077)
    target = args.private_output.resolve()
    if any((d / ".git").exists() for d in (target, *target.parents)):
        raise ValueError("Private evidence destination must not be inside a Git checkout")
    target.mkdir(mode=0o700, parents=True, exist_ok=True)
    for url in args.urls:
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.hostname not in SITE or
                not URL_PATH.fullmatch(parsed.path) or parsed.query or parsed.fragment):
            raise ValueError("Only public BRAVO /dvds/<digits> HTTPS URLs without query/fragment are allowed")
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            records = []
            for url in args.urls:
                context = await browser.new_context(storage_state=None, service_workers="block")
                try:
                    records.append(await capture(context, url, target))
                finally:
                    await context.close()
        finally:
            await browser.close()
    manifest = {"assignment":"WAVE2E-A-DVD-DOM-20261102", "captured_at_utc":utc_now(),
                "not_automatic_acceptance": "Structural DOM must be manually reviewed before any GitHub commit",
                "no_stash_test_access": True, "records": records}
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    (target / "manifest.private.json").write_text(manifest_text, encoding="utf-8")
    sums = [f"{r['sha256']}  {r['sanitized_html']}" for r in records if r["sha256"]]
    (target / "SHA256SUMS.private.txt").write_text("\n".join(sums) + ("\n" if sums else ""), encoding="utf-8")
    print(json.dumps({"output":str(target), "statuses":[(r["requested_url"],r["classification"]) for r in records]}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+", help="Allowed public BRAVO DVD URLs")
    parser.add_argument("--private-output", type=Path, required=True,
                        help="Restricted destination; do not point at a Git checkout")
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
