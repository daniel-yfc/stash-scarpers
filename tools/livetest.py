#!/usr/bin/env python3
"""Live-site test harness for daniel-yfc/stash-scarpers.

For every scraper YAML, picks a URL to crawl, fetches it through
`gsk crawl --raw`, then evaluates every XPath declared in the scraper
against the rendered HTML using lxml. Writes per-scraper results to JSON and
prints a markdown summary.

Caveats:
- CDP-gated scrapers (useCDP: true) cannot be tested anonymously. They are
classified as `login_required` and SKIPPED. Toggling SKIP_LOGIN_GATED = False
will attempt them anyway but expect the crawler to land on the login page.
- lxml covers XPath 1.0; selectors using XPath 2.0 functions or exotic axes
(ancestor::, following-sibling::, etc.) are skipped with `unsupported`.
- Concurrency defaults to 4; raise MAX_PARALLEL for faster runs.

Note: incorporated from the 2026-10-01 stash-scraper-builder workflow run.
The gsk envelope tag matcher is tag-name agnostic (any first tagged block
is treated as the metadata envelope); the original run used `gsk crawl
--raw`'s native envelope.

Requires: the Genspark CLI (`npm install -g @genspark/cli`) on PATH and a
`GSK_API_KEY` environment variable. `gsk` is a metered cloud-service CLI,
not a plain local crawler: the harness cannot run on machines without it
(including GitHub Actions runners) and each crawl consumes Genspark credits.
The preflight check fails fast with install instructions when `gsk` is
absent.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml
from lxml import html, etree

# ----- Inputs / Outputs -----------------------------------------------------

SCRAPERS_DIR = Path(__file__).resolve().parents[1] / "scrapers"
RESULTS_DIR = Path("/tmp/stash-scarpers-live/results")
LIVE_DIR = Path("/tmp/stash-scarpers-live/html")
LIVE_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ----- Tunables -------------------------------------------------------------

SKIP_LOGIN_GATED = True  # if True: don't crawl CDP-gated URLs anonymously
SKIP_DOMAINS = (  # URLs whose host matches these patterns are NEVER crawled
    "adult.",
    "fc2.com",
    "xvideos.com",
    "pornhub.com",
    "xhamster.com",
)
MAX_PARALLEL = 4  # parallel crawls (gsk has its own limits)
CRAWL_TIMEOUT_SEC = 90  # per-URL deadline
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

# Selectors whose XPath body uses unsupported features are recorded as such
# so a maintainer can decide whether to chase the parity or switch tools.
# XPath 1.0 supports all standard axes; only XPath 2.0+ functions are unsupported here.
UNSUPPORTED_AXES: tuple[str, ...] = ()
UNSUPPORTED_FNS = ("upper-case(", "lower-case(", "matches(", "replace(",
                  "ends-with(", "tokenize(", "analyze-string(")


class _StashYamlLoader(yaml.SafeLoader):
    pass


def _string_passthrough(loader, node):
    return loader.construct_scalar(node)


_StashYamlLoader.add_constructor("tag:yaml.org,2002:timestamp", _string_passthrough)
_StashYamlLoader.add_constructor("tag:yaml.org,2002:date", _string_passthrough)

# ----- URL discovery --------------------------------------------------------

URL_HINT_RE = re.compile(
    r'#\s*(?:Test\s*URLs?|Test\s*URLs?\s*from|URL):\s*(.+)', re.I)
LIST_LINE_RE = re.compile(r'#\s*-\s*(https?://\S+)', re.I)
ANY_URL_RE = re.compile(r'https?://[^\s\)\]\"]#]+')


def discover_test_urls(text: str) -> list[str]:
    """Pull URLs from YAML header comments. Strategy:

    1. If a comment introduces an explicit list ("Test URL:" / "Test URLs:" /
       "URL:"), gather the bullet lines that follow until the comment block
       ends.
    2. If no explicit introduction is found, scan the first 60 lines and
       pick any URL that appears as a bullet under a verification block
       ("Verification status", "Test URLs", "Verified against", etc.).
    3. Otherwise, look at the first literal https://... URLs in the header
       comment block.
    """
    urls: list[str] = []
    seen: set[str] = set()

    def add(u: str):
        u = u.rstrip(".,)")
        if u and u not in seen:
            seen.add(u)
            urls.append(u)

    in_list = False
    in_verification = False
    lines = text.splitlines()
    for i, line in enumerate(lines[:80]):  # only the header comment
        if not line.startswith("#"):
            in_list = False
            # a non-comment line ends the comment block; reset verification
            in_verification = False
            continue
        if URL_HINT_RE.search(line):
            in_list = True
            for m in ANY_URL_RE.findall(line):
                add(m)
            continue
        if in_list:
            m = LIST_LINE_RE.match(line)
            if m:
                add(m.group(1))
                continue
            stripped = line.strip()
            # End of bullet list: a comment line that isn't a bullet, or a blank section
            in_list = False
            if stripped == "#":
                continue
            if not stripped.startswith("# -") and not stripped.startswith("#- "):
                in_list = False
                continue
        # Look for inline URLs in verification blocks
        if re.search(r'Verification|Verified|Test', line, re.I):
            in_verification = True
        if in_verification:
            for m in LIST_LINE_RE.finditer(line):
                add(m.group(1))
        for m in re.finditer(r'(https?://[^\s\)\]\"]+)', line):
            # Skip sibling site captures that are clearly not scenes
            if "scraper.schema" in m.group(1):
                continue
            add(m.group(1))
        # Always sweep the line for inline URLs as a last resort — but stop
        # at the first non-comment non-empty line, because that means we
        # have left the header.
        for m in re.finditer(r'(https?://[^\s\)\]\"]+)', line):
            if "scraper.schema" in m.group(1):
                continue
            add(m.group(1))

    return urls


def pick_target_url(data: dict, text: str, file: Path) -> tuple[str, str]:
    """Return (url, source) — source is 'comment' / 'sceneByURL' / 'queryURL'."""
    # 1. Try explicit test URLs in comments first
    comment_urls = discover_test_urls(text)
    for u in comment_urls:
        return u, "comment"
    # 2. sceneByURL.url[0]
    sb = data.get("sceneByURL")
    if isinstance(sb, list):
        for entry in sb:
            urls = entry.get("url") if isinstance(entry, dict) else None
            if isinstance(urls, list) and urls:
                return urls[0], "sceneByURL"
    if isinstance(sb, dict):
        urls = sb.get("url")
        if isinstance(urls, list) and urls:
            return urls[0], "sceneByURL"
    # 3. sceneByName.queryURL with the {} placeholder replaced
    sbn = data.get("sceneByName")
    if isinstance(sbn, dict):
        q = sbn.get("queryURL")
        if isinstance(q, str) and "{}" in q:
            return q.replace("{}", "TEST"), "sceneByName.queryURL"
    return "", "none"


# ----- Selector extraction --------------------------------------------------

def _looks_like_xpath(s: str) -> bool:
    if not isinstance(s, str):
        return False
    s = s.strip()
    if s.startswith("//") or s.startswith("/"):
        return True
    if s.startswith("$"):  # Stash XPath variables like $results
        return True
    return False


def collect_selectors(data: dict) -> list[tuple[str, str]]:
    """Yield (where, xpath_string) for every XPath declared in the file."""
    out: list[tuple[str, str]] = []

    def walk(node, path, *, parent_key: str | None = None):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else k, parent_key=k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]", parent_key=parent_key)
        elif isinstance(node, str):
            if parent_key in ("selector", "queryURL") and _looks_like_xpath(node):
                out.append((path, node))

    sections = [
        ("xPathScrapers", data.get("xPathScrapers") or {}),
        ("jsonScrapers", data.get("jsonScrapers") or {}),
    ]
    for sec_name, sec in sections:
        if not isinstance(sec, dict):
            continue
        for scraper_name, body in sec.items():
            if isinstance(body, dict):
                walk(body, f"{sec_name}.{scraper_name}", parent_key=None)
    return out


def collect_common_vars(data: dict) -> dict[str, str]:
    """Collect the $name → XPath map from each scraper's common block."""
    out: dict[str, str] = {}
    sections = [
        ("xPathScrapers", data.get("xPathScrapers") or {}),
        ("jsonScrapers", data.get("jsonScrapers") or {}),
    ]
    for sec_name, sec in sections:
        if not isinstance(sec, dict):
            continue
        for scraper_name, body in sec.items():
            if not isinstance(body, dict):
                continue
            common = body.get("common") or {}
            if isinstance(common, dict):
                for k, v in common.items():
                    if isinstance(k, str) and k.startswith("$") and isinstance(v, str):
                        out[k] = v.strip()
    return out


VARIABLE_RE = re.compile(r'\$([A-Za-z_][A-Za-z0-9_]*)')


def resolve_variables(xpath: str, vars_map: dict[str, str], _depth: int = 0) -> str:
    """Recursively substitute $var references with their declared XPath.
    Missing variables are left in place; lxml will then raise an error we
    surface as `unresolved_variable: name`.
    """
    if _depth > 4:
        return xpath

    def replace(m):
        name = "$" + m.group(1)
        if name in vars_map:
            # Wrap in parens so it composes with surrounding predicates
            return "(" + vars_map[name] + ")"
        return name

    return VARIABLE_RE.sub(replace, xpath)


def is_supported(xpath: str) -> bool:
    for ax in UNSUPPORTED_AXES:
        if ax in xpath:
            return False
    for fn in UNSUPPORTED_FNS:
        if fn in xpath:
            return False
    return True


# ----- Crawl ----------------------------------------------------------------

ENVELOPE_RE = re.compile(r"<([A-Za-z][A-Za-z0-9_-]*)>(.*?)</\1>", re.S)


def _strip_envelope(raw: str) -> tuple[str, dict]:
    """gsk crawl --raw wraps the response in a tagged metadata envelope.

    The body is JSON-string-escaped (literal "\\n", "\\u", "\\\""), so we
    decode the JSON-escapes by routing the body back through json.loads.
    Returns the body (everything after the closing tag) and parsed metadata.
    """
    meta = {}
    body = raw
    m = ENVELOPE_RE.search(raw)
    if m:
        envelope = m.group(2)
        body = raw[m.end():]
        for line in envelope.splitlines():
            line = line.strip()
            if line.startswith("URL:"):
                meta["url"] = line[4:].strip()
            elif line.startswith("HTTP Status:"):
                try:
                    meta["http_status"] = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Content-Type:"):
                meta["content_type"] = line.split(":", 1)[1].strip()
            elif line.startswith("Bytes returned:"):
                meta["bytes"] = line.split(":", 1)[1].strip()
            elif line.startswith("Has more:"):
                meta["has_more"] = "offset=" in line
    # Decode JSON escapes — gsk returns the body as a JSON string with literal
    # backslash-n / backslash-u / backslash-quote (notably for HTML pages).
    try:
        body = json.loads('"' + body.replace('"', '\\"') + '"')
    except json.JSONDecodeError:
        # Best-effort fallback for messy payloads
        body = body.encode().decode("unicode_escape", errors="ignore")
    body = re.sub(r'^\ufeff', '', body)
    return body, meta


def crawl(url: str, max_bytes: int = 50000) -> tuple[str, dict]:
    """Fetch raw HTML via gsk crawl --raw.

    Reads in 10000-byte chunks (gsk's per-call limit) until we hit
    max_bytes or the server stops emitting more. Returns the concatenated
    body and the parsed metadata of the first chunk.
    """
    chunks: list[str] = []
    last_meta: dict = {}
    offset = 0
    safe_name = re.sub(r'[^A-Za-z0-9]+', '_', url)[:80]
    out_html = LIVE_DIR / f"{safe_name}.html"

    while offset < max_bytes:
        cmd = ["gsk", "crawl", url, "--raw", f"--offset={offset}"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=CRAWL_TIMEOUT_SEC)
        except subprocess.TimeoutExpired:
            break
        if proc.returncode != 0:
            raise RuntimeError(f"gsk crawl exited {proc.returncode}: {proc.stderr[:200]}")
        body, meta = _strip_envelope(proc.stdout)
        if not last_meta:
            last_meta = meta
        if not body:
            break
        chunks.append(body)
        # The gsk docs say "Has more: pass offset=10000 to read the next chunk."
        # is a hint not a contract. Advance by exactly 10000 each time, and
        # stop when the chunk is shorter than 10000 (server is done).
        next_offset = offset + 10000
        if len(body) < 10000:
            break
        offset = next_offset

    full = "".join(chunks)
    out_html.write_text(full)
    return full, last_meta


# ----- Live eval ------------------------------------------------------------

def evaluate_xpath(html_text: str, xpath: str, vars_map: dict[str, str]) -> dict:
    try:
        tree = html.fromstring(html_text)
    except (etree.XMLSyntaxError, etree.ParserError) as e:
        return {"status": "parse_error", "matches": 0, "error": str(e)[:120]}
    resolved = resolve_variables(xpath, vars_map)
    # Detect unresolved variables BEFORE lxml so we can record them clearly
    unresolved = sorted(set(VARIABLE_RE.findall(resolved)))
    if unresolved:
        names = ", ".join("$" + n for n in unresolved)
        return {"status": "unresolved_variable",
                "matches": 0,
                "error": f"unresolved variables: {names}",
                "resolved_xpath": resolved}
    try:
        nodes = tree.xpath(resolved)
    except etree.XPathEvalError as e:
        return {"status": "xpath_error", "matches": 0, "error": str(e)[:120],
                "resolved_xpath": resolved}
    except Exception as e:
        return {"status": "error", "matches": 0, "error": str(e)[:120],
                "resolved_xpath": resolved}
    samples = []
    for n in nodes[:3]:
        if isinstance(n, etree._Element):
            txt = " ".join(t.strip() for t in n.itertext() if t.strip())
            samples.append(txt[:80])
        elif isinstance(n, str):
            samples.append(n[:80])
        else:
            samples.append(repr(n)[:80])
    return {"status": "ok", "matches": len(nodes), "samples": samples,
            "resolved_xpath": resolved if resolved != xpath else None}


# ----- Pipeline -------------------------------------------------------------

def process(file: Path) -> dict:
    text = file.read_text()
    data = yaml.load(text, Loader=_StashYamlLoader) or {}
    name = data.get("name", file.stem)
    driver = data.get("driver") or {}
    uses_cdp = bool(driver.get("useCDP"))
    has_cookies = bool(driver.get("cookies"))
    login_required = uses_cdp or has_cookies

    target, source = pick_target_url(data, text, file)
    if target and not target.startswith(("http://", "https://")):
        target = "https://" + target
        source += ("+scheme" if source else "scheme")
    # Disqualify URLs that are just a host (no path) — those don't carry a
    # console page to validate against
    if target and re.search(r'^https?://[^/]+/?$', target):
        target = ""
        source = "trivial_host_skipped"

    result = {
        "file": file.name,
        "name": name,
        "uses_cdp": uses_cdp,
        "login_required": login_required,
        "target_url": target,
        "url_source": source,
        "selectors_total": 0,
        "selectors_evaluated": 0,
        "selectors_match": 0,
        "selectors_zero": 0,
        "selectors_unsupported": 0,
        "selectors_error": 0,
        "selector_results": [],
        "crawl_status": None,
        "notes": [],
    }

    if not target:
        result["crawl_status"] = "no_target_url"
        result["notes"].append("couldn't discover a usable target URL (bare host or absent)")
        return result

    # Domain-level skip for sensitive targets — extends the policy beyond CDP
    if any(domain in target for domain in SKIP_DOMAINS):
        result["crawl_status"] = "domain_skipped"
        result["notes"].append("target host matches SKIP_DOMAINS list — not crawling")
        return result

    selectors = collect_selectors(data)
    vars_map = collect_common_vars(data)
    # de-dup by xpath
    seen = set()
    unique = []
    for path, xpath in selectors:
        if xpath in seen:
            continue
        seen.add(xpath)
        unique.append((path, xpath))
    result["selectors_total"] = len(unique)

    if not unique:
        result["crawl_status"] = "no_selectors"
        return result

    try:
        body, meta = crawl(target)
    except subprocess.TimeoutExpired:
        result["crawl_status"] = "timeout"
        return result
    except Exception as e:
        result["crawl_status"] = "fetch_error"
        result["notes"].append(str(e)[:120])
        return result

    result["crawl_status"] = "ok"
    result["page_meta"] = meta
    page_bytes = len(body)
    result["page_bytes"] = page_bytes

    for path, xpath in unique:
        if not is_supported(xpath):
            result["selectors_unsupported"] += 1
            result["selector_results"].append({
                "where": path,
                "xpath": xpath,
                "status": "unsupported",
            })
            continue
        result["selectors_evaluated"] += 1
        ev = evaluate_xpath(body, xpath, vars_map)
        ev["where"] = path
        ev["xpath"] = xpath
        result["selector_results"].append(ev)
        if ev["status"] == "ok" and ev["matches"] > 0:
            result["selectors_match"] += 1
        elif ev["status"] == "ok":
            result["selectors_zero"] += 1
        else:
            result["selectors_error"] += 1

    return result


def _preflight() -> None:
    """Fail fast when the gsk CLI (Genspark) is unavailable."""
    if shutil.which("gsk") is None:
        sys.exit(
            "livetest.py: the `gsk` CLI is not on PATH.\n"
            "Install the Genspark CLI first:  npm install -g @genspark/cli\n"
            "Then set GSK_API_KEY (see https://www.genspark.ai Settings > API Key)."
        )
    if not os.environ.get("GSK_API_KEY"):
        print("warning: GSK_API_KEY is not set; gsk crawl may fail to authenticate.",
              file=sys.stderr)


def main():
    _preflight()
    paths = sorted(SCRAPERS_DIR.glob("*.yml"))
    results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as ex:
        futures = {ex.submit(process, p): p for p in paths}
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            sys.stdout.write(
                f" [{r['crawl_status']:>14}] {r['file']:<20} "
                f"target={r['target_url'] or '-':<60} "
                f"selectors matched={r['selectors_match']}/{r['selectors_evaluated']}\n"
            )
    results.sort(key=lambda r: r["file"])
    (RESULTS_DIR / "live-test.json").write_text(json.dumps(results, indent=2, default=str))
    elapsed = time.time() - t0

    # summary stats
    n_total = len(results)
    n_login = sum(1 for r in results if r["crawl_status"] == "login_required")
    n_crawled = sum(1 for r in results if r["crawl_status"] == "ok")
    n_no_match = sum(1 for r in results if r["selectors_zero"] > 0 and r["selectors_evaluated"] > 0)
    n_full_match = sum(1 for r in results if r["selectors_evaluated"] > 0 and r["selectors_zero"] == 0)
    n_no_target = sum(1 for r in results if r["crawl_status"] in ("no_target_url", "no_selectors"))

    print()
    print(f"=== Live-test pass: {n_total} scrapers, {elapsed:.1f}s elapsed ===")
    print(f"  crawled ok        : {n_crawled}")
    print(f"  login-gated       : {n_login} (useCDP/cookies; skipped per policy)")
    print(f"  no target URL     : {n_no_target}")
    print(f"  full XPath match  : {n_full_match}")
    print(f"  partial match     : {sum(1 for r in results if 0 < r['selectors_zero'] < r['selectors_evaluated'])}")
    print(f"  0 XPath matches   : {n_no_match}")


if __name__ == "__main__":
    main()
