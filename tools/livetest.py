#!/usr/bin/env python3
"""Live-site test harness for daniel-yfc/stash-scarpers.

For every scraper YAML, picks a URL to crawl, fetches it through
`gsk crawl --raw` (anonymous) or via Chrome DevTools Protocol (when
`--cdp-url` is supplied), then evaluates every XPath declared in the
scraper against the rendered HTML using lxml. Writes per-scraper results
to JSON and prints a markdown summary.

When `--cases <path>` is supplied, the harness uses explicit
target URLs and expected field values — as supplied by the maintainer —
instead of inferring targets from the YAML comments. Each declared
`expected` / `expected_match` value is compared against the actual XPath
output and reported as match / mismatch / no_match.

Caveats:
- CDP-gated scrapers (useCDP: true) cannot be tested anonymously. They are
  classified as `login_required` and SKIPPED unless `--cdp-url` is provided.
- Test cases marked `auth: true` without a working CDP connection are
  reported as `auth_required` and do not produce a verified result.
- lxml covers XPath 1.0; selectors using XPath 2.0 functions are skipped
  with `unsupported`.
- Concurrency defaults to 4; raise MAX_PARALLEL for faster runs.
- Adult-domain matches in `SKIP_DOMAINS` are NEVER crawled regardless of
  any `--cases` override.

Requires:
- Mode A (anonymous per-file pass) and anonymous test cases: the Genspark
  CLI (`npm install -g @genspark/cli`) on PATH plus a `GSK_API_KEY`
  environment variable. `gsk` is a metered cloud-service CLI — each crawl
  consumes Genspark credits, and it is NOT available on GitHub Actions
  runners or fresh clones. The preflight check fails fast with install
  instructions when `gsk` is absent.
- Mode B with CDP login modes (cdp / cookies / form): a Chrome instance
  started with `--remote-debugging-port=9222`, plus ONE of the two
  optional backends:

  - `playwright` (recommended, optional): `pip install playwright`.
    No browser download is needed when connecting to your existing
    Chrome (`connect_over_cdp`); only run `playwright install chromium`
    if you also want Playwright to launch its own browser.
  - `websockets` (fallback, optional): `pip install websockets`.
    A hand-rolled minimal CDP client kept for environments where
    Playwright cannot be installed.

  `--engine auto` (the default) picks Playwright when it is importable
  and falls back to the websockets client otherwise. Neither backend is
  a hard dependency of this repository — the harness degrades to a clear
  error message when both are absent.

Security model: credentials never live in YAML — `login.fields` values
support `${env:VAR}` placeholders resolved from the shell environment,
and cookie files (EditThisCookie JSON or Netscape cookies.txt) are
expected under an untracked `.local/` directory.

Note: incorporated from the 2026-10-02 stash-scraper-builder workflow run
(upgrade of the 2026-10-01 edition). The CdpSession reader wiring was
completed during reconstruction — the attachment transfer strips Python
indentation, and the reader-task spawn / load-event plumbing did not
survive it. The Playwright backend (added in the same pass) is the
recommended path around that hand-rolled code.
"""
import argparse
import asyncio
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

try:
    import websockets  # lightweight CDP client
except ImportError:
    websockets = None

try:
    from playwright.sync_api import sync_playwright, Error as PlaywrightError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

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

# CDP backend for Mode B login flows: "auto" | "websockets" | "playwright".
# Set from --engine in main(); "auto" prefers Playwright when importable.
ENGINE = "auto"

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
ANY_URL_RE = re.compile(r'https?://[^\s\)\]\"#]+')


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

def _strip_envelope(raw: str) -> tuple[str, dict]:
    """gsk crawl --raw wraps the response in <raw-response>...</raw-response>.

    The body is JSON-string-escaped (literal "\\n", "\\u", "\\\""), so we
    decode the JSON-escapes by routing the body back through json.loads.
    Returns the body (everything after the closing tag) and parsed metadata.
    """
    meta = {}
    body = raw
    m = re.search(r'<raw-response>(.*?)</raw-response>', raw, re.S)
    if m:
        envelope = m.group(1)
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


# ----- CDP (Chrome DevTools Protocol) client --------------------------------

CDP_MSG_ID = 0


def _cdp_msg(method: str, params: dict | None = None) -> tuple[int, dict]:
    global CDP_MSG_ID
    CDP_MSG_ID += 1
    return CDP_MSG_ID, {"id": CDP_MSG_ID, "method": method, "params": params or {}}


async def cdp_fetch(url: str, cdp_url: str, timeout: float = 60.0) -> str:
    """Open a tab in the user's CDP-attached Chrome, navigate, return outerHTML.

    Spoken protocol: `websockets` against `ws://host:9222/devtools/page/<id>`.
    Falls back to `Target.getTargets` + page discovery if a stable
    page WS URL is not provided up-front.
    """
    if websockets is None:
        raise RuntimeError("`websockets` python package not installed; pip install websockets")
    if cdp_url.endswith("/browser") or "/devtools/page/" in cdp_url:
        page_ws = cdp_url
    else:
        async with websockets.connect(
            cdp_url + "/devtools/browser", max_size=8 * 1024 * 1024, open_timeout=10
        ) as ws:
            tid, tmsg = _cdp_msg("Target.getTargets")
            await ws.send(json.dumps(tmsg))
            page_id = None
            try:
                async with asyncio.timeout(10):
                    while True:
                        raw = json.loads(await ws.recv())
                        if raw.get("id") == tid:
                            targets = raw["result"]["targetInfos"]
                            for t in targets:
                                if t["type"] == "page":
                                    page_id = t["targetId"]
                                    break
                            break
            except (asyncio.TimeoutError, KeyError):
                pass
            if not page_id:
                raise RuntimeError("no `page`-typed target found in Chrome")
            page_ws = f"{cdp_url}/devtools/page/{page_id}"

    async with websockets.connect(page_ws, max_size=8 * 1024 * 1024, open_timeout=10) as ws:
        for domain in ("Page", "Runtime"):
            mid, m = _cdp_msg(f"{domain}.enable")
            await ws.send(json.dumps(m))
        nav_id, nav_msg = _cdp_msg("Page.navigate", {"url": url})
        await ws.send(json.dumps(nav_msg))
        loaded = False
        try:
            async with asyncio.timeout(timeout):
                while not loaded:
                    raw = json.loads(await ws.recv())
                    mtype = raw.get("method")
                    if mtype == "Page.loadEventFired":
                        loaded = True
                    elif raw.get("id") == nav_id and "error" in (raw.get("result") or {}):
                        raise RuntimeError(f"Page.navigate error: {raw['result']['errorText']}")
        except asyncio.TimeoutError:
            raise RuntimeError("CDP navigate timed out waiting for Page.loadEventFired")

        eval_id, eval_msg = _cdp_msg("Runtime.evaluate", {
            "expression": "document.documentElement.outerHTML",
            "returnByValue": True,
        })
        await ws.send(json.dumps(eval_msg))

        html_value = ""
        try:
            async with asyncio.timeout(15):
                while True:
                    raw = json.loads(await ws.recv())
                    if raw.get("id") == eval_id:
                        result = raw.get("result", {}).get("result", {})
                        html_value = result.get("value", "")
                        break
        except asyncio.TimeoutError:
            raise RuntimeError("CDP Runtime.evaluate timed out")
        return html_value


# ----- Stateful CDP session for login flows ---------------------------------

class CdpSession:
    """Reusable CDP session attached to one `page` target.

    Provides navigate, set_cookies, fill_form, evaluate. Used by the
    login flows below.

    Reconstruction note: the attachment's reader-task spawn and load-event
    wiring did not survive the transfer pipeline; they are completed here so
    that _send()/navigate() resolve correctly. A single _reader() task is
    the sole consumer of the websocket. Prefer the Playwright backend
    (`--engine playwright`) where installable — it replaces this hand-rolled
    client entirely.
    """

    def __init__(self, cdp_url: str):
        self.cdp_url = cdp_url
        self.ws = None
        self._next_id = 0
        self._inflight: dict[int, asyncio.Future] = {}
        self._loop = None
        self._reader_task = None
        self._load_event = asyncio.Event()

    async def connect(self):
        if websockets is None:
            raise RuntimeError("`websockets` python package not installed; pip install websockets")
        # Resolve to a page WS URL
        if self.cdp_url.endswith("/browser") or "/devtools/page/" in self.cdp_url:
            page_ws = self.cdp_url
        else:
            async with websockets.connect(
                self.cdp_url + "/devtools/browser",
                max_size=8 * 1024 * 1024, open_timeout=10,
            ) as ws:
                msg = {"id": self._next_msg_id(), "method": "Target.getTargets"}
                await ws.send(json.dumps(msg))
                page_id = None
                async with asyncio.timeout(10):
                    while True:
                        raw = json.loads(await ws.recv())
                        if raw.get("id") == msg["id"]:
                            for t in raw["result"]["targetInfos"]:
                                if t["type"] == "page":
                                    page_id = t["targetId"]
                                    break
                            break
                if not page_id:
                    raise RuntimeError("no `page` target in Chrome at " + self.cdp_url)
                page_ws = f"{self.cdp_url}/devtools/page/{page_id}"
        self.ws = await websockets.connect(
            page_ws, max_size=8 * 1024 * 1024, open_timeout=10,
        )
        await self._enable("Page", "Runtime", "Network")
        self._load_event = asyncio.Event()
        self._reader_task = asyncio.get_running_loop().create_task(self._reader())

    def _next_msg_id(self) -> int:
        self._next_id += 1
        return self._next_id

    async def _enable(self, *domains: str):
        for d in domains:
            await self._send({"id": self._next_msg_id(), "method": f"{d}.enable"})

    async def _send(self, msg: dict) -> dict | None:
        mid = msg["id"]
        fut = asyncio.get_running_loop().create_future()
        self._inflight[mid] = fut
        await self.ws.send(json.dumps(msg))
        # Reader task drains events into futures
        return await asyncio.wait_for(fut, timeout=60)

    async def _reader(self):
        try:
            async for raw_text in self.ws:
                try:
                    msg = json.loads(raw_text)
                except json.JSONDecodeError:
                    continue
                if "id" in msg and msg["id"] in self._inflight:
                    fut = self._inflight.pop(msg["id"])
                    if not fut.done():
                        fut.set_result(msg)
                elif msg.get("method") == "Page.loadEventFired":
                    self._load_event.set()
        except Exception:
            pass

    async def close(self):
        if self._reader_task is not None:
            self._reader_task.cancel()
            self._reader_task = None
        if self.ws is not None:
            await self.ws.close()
            self.ws = None

    async def navigate(self, url: str, wait_load: bool = True, timeout: float = 60.0) -> str:
        if self.ws is None:
            await self.connect()
        self._load_event.clear()
        await self._send({"id": self._next_msg_id(), "method": "Page.navigate", "params": {"url": url}})
        if not wait_load:
            return ""
        # Read messages until Page.loadEventFired
        try:
            await asyncio.wait_for(self._load_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            raise RuntimeError("CDP navigate timeout")
        # Tiny settle delay for client-rendered content
        await asyncio.sleep(0.2)
        return await self.outer_html()

    async def evaluate(self, expr: str, return_by_value: bool = True) -> dict:
        msg = {"id": self._next_msg_id(),
               "method": "Runtime.evaluate",
               "params": {"expression": expr, "returnByValue": return_by_value}}
        return await self._send(msg)

    async def outer_html(self) -> str:
        resp = await self.evaluate("document.documentElement.outerHTML")
        if not resp:
            return ""
        return resp.get("result", {}).get("result", {}).get("value", "") or ""

    async def set_cookies(self, cookies: list[dict]) -> None:
        """cookies: [{name, value, domain, path?, httpOnly?, secure?, sameSite?, expires?}, ...]"""
        # Normalise: ensure each cookie has a domain OR url
        for c in cookies:
            if "domain" not in c and "url" not in c:
                raise ValueError(f"cookie `{c.get('name')}` missing domain/url")
        await self._send({"id": self._next_msg_id(),
                          "method": "Network.setCookies",
                          "params": {"cookies": cookies}})

    async def fill_form(self, fields: dict[str, str],
                        submit: bool = True,
                        submit_button_selector: str | None = None,
                        wait_after: float = 2.0) -> None:
        """For each k,v in fields, look for an element with name=k (or id=k)
        and set its value to v. Then submit the form containing the first
        field. If submit_button_selector is provided, click that element.

        Returns once the page load settles (or wait_after seconds elapsed).
        """
        # Build a single JS expression that fills fields by name and submits
        # the parent form. We avoid touching DOM structure beyond that.
        field_payload = json.dumps(fields)
        script = f"""
        (() => {{
        const fields = {field_payload};
        for (const [name, value] of Object.entries(fields)) {{
            let el = document.querySelector(`input[name="${{name}}"], textarea[name="${{name}}"], select[name="${{name}}"]`);
            if (!el) el = document.getElementById(name);
            if (!el) continue;
            const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype
                : el.tagName === 'SELECT' ? HTMLSelectElement.prototype
                : HTMLInputElement.prototype;
            const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
            setter.call(el, value);
            el.dispatchEvent(new Event('input', {{bubbles: true}}));
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
        }}
        return Object.keys(fields).length;
        }})()
        """
        resp = await self.evaluate(script)
        filled = (resp or {}).get("result", {}).get("result", {}).get("value", 0)

        if submit:
            if submit_button_selector:
                click_script = f"""
                (() => {{
                const el = document.querySelector(`{submit_button_selector}`);
                if (el) {{ el.click(); return true; }}
                return false;
                }})()
                """
            else:
                click_script = """
                (() => {
                const forms = document.querySelectorAll('form');
                for (const f of forms) {
                // Try to find a submit button inside the form
                const btn = f.querySelector('input[type=submit], button[type=submit], button:not([type])');
                if (btn) { btn.click(); return true; }
                // Otherwise request form.submit() and return
                if (typeof f.submit === 'function') { f.submit(); return true; }
                }
                return false;
                })()
                """
            await self.evaluate(click_script)
        await asyncio.sleep(wait_after)
        return filled


# ----- Cookie file loaders ---------------------------------------------------

def load_cookie_file(path: Path) -> list[dict]:
    """Load cookies from a JSON file (EditThisCookie export format) or a
    Netscape cookies.txt file. Returns a list of `Network.setCookies`-shaped
    cookie dicts.
    """
    text = path.read_text()
    # 1. JSON path
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, list) and data and isinstance(data[0], dict):
        out = []
        for c in data:
            out.append({
                "name": c.get("name"),
                "value": c.get("value"),
                "domain": c.get("domain"),
                "path": c.get("path") or "/",
                "httpOnly": bool(c.get("httpOnly")),
                "secure": bool(c.get("secure")),
            })
        return out
    # 2. Netscape cookies.txt path
    out = []
    for line in text.splitlines():
        if not line.strip() or line.startswith("# "):
            continue
        if line.startswith("#"):
            # e.g. "#HttpOnly_" prefix denoting HttpOnly
            line = line.lstrip("#")
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        # domain, hostonly?, path, secure?, expires, name, value
        domain = parts[0].lstrip("#")
        path = parts[2]
        secure = parts[3].upper() == "TRUE"
        expires_raw = parts[4]
        try:
            expires = int(float(expires_raw))
        except ValueError:
            expires = -1
        out.append({
            "name": parts[5],
            "value": parts[6],
            "domain": domain,
            "path": path,
            "secure": secure,
            "expires": expires if expires > 0 else -1,
        })
    return out


def env_or(value):
    """Resolve ${env:VAR} style placeholders. Skips non-string values."""
    if not isinstance(value, str):
        return value
    m = re.match(r'^\$\{env:([A-Z_][A-Z0-9_]*)\}$', value.strip())
    if m:
        import os
        return os.environ.get(m.group(1), "")
    return value


# ----- Optional Playwright backend -------------------------------------------

def _pw_endpoint(cdp_url: str) -> str:
    """Convert a ws:// (or http://) CDP endpoint into the http://host:port
    form Playwright's connect_over_cdp expects. Any /devtools/... suffix
    is discarded — connect_over_cdp discovers pages itself.
    """
    m = re.match(r'^(?:wss?|https?)://([^/:]+)(?::(\d+))?', (cdp_url or "").strip())
    if not m:
        return "http://localhost:9222"
    host, port = m.group(1), m.group(2) or "9222"
    return f"http://{host}:{port}"


def _pw_cookies(cookies: list[dict]) -> list[dict]:
    """Convert Network.setCookies-shaped dicts into Playwright
    context.add_cookies format (domain+path or url; sameSite must be
    Strict/Lax/None; expires in seconds).
    """
    out = []
    for c in cookies:
        pc = {"name": c["name"], "value": c["value"]}
        if c.get("domain"):
            pc["domain"] = c["domain"]
            pc["path"] = c.get("path") or "/"
        elif c.get("url"):
            pc["url"] = c["url"]
        else:
            raise ValueError(f"cookie `{c.get('name')}` missing domain/url")
        if isinstance(c.get("expires"), (int, float)) and c["expires"] > 0:
            pc["expires"] = c["expires"]
        if "secure" in c:
            pc["secure"] = bool(c["secure"])
        if "httpOnly" in c:
            pc["httpOnly"] = bool(c["httpOnly"])
        if c.get("sameSite") in ("Strict", "Lax", "None"):
            pc["sameSite"] = c["sameSite"]
        out.append(pc)
    return out


def playwright_fetch(case: dict, auth_mode: str, cdp_url: str, target: str) -> str:
    """Fetch the target's rendered HTML via Playwright connected over CDP.

    Optional backend (`pip install playwright` — no browser download is
    needed when attaching to your existing Chrome). Handles the same auth
    modes as the websockets CdpSession path:
    - cdp: pre-logged-in Chrome — reuse the default context, just navigate
    - cookies: context.add_cookies(...) from login.cookies / cookies_file
    - form: fill the login form by name/id, submit, then navigate
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError("`playwright` python package not installed; pip install playwright")
    login = case.get("login") or {}
    endpoint = _pw_endpoint(cdp_url)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(endpoint)
        try:
            # contexts[0] is the user's real profile in the attached Chrome —
            # reusing it keeps the pre-logged-in session cookies.
            context = browser.contexts[0] if browser.contexts else browser.new_context()

            if auth_mode == "cookies":
                cookies: list[dict] = list(login.get("cookies") or [])
                cookies_file = login.get("cookies_file")
                if cookies_file:
                    cf_path = (SCRAPERS_DIR / cookies_file) if not cookies_file.startswith("/") else Path(cookies_file)
                    cookies.extend(load_cookie_file(cf_path))
                if not cookies:
                    raise RuntimeError("auth: cookies requires `login.cookies:` or `login.cookies_file:`")
                context.add_cookies(_pw_cookies(cookies))

            page = context.new_page()
            try:
                if auth_mode == "form":
                    login_url = login.get("url")
                    if not login_url:
                        raise RuntimeError("auth: form requires `login.url:` pointing at the login page")
                    fields = {k: env_or(v) for k, v in (login.get("fields") or {}).items()}
                    if not fields:
                        raise RuntimeError("auth: form requires `login.fields:` with at least one input")
                    page.goto(login_url, wait_until="domcontentloaded")
                    for name, value in fields.items():
                        try:
                            page.fill(f'[name="{name}"]', value, timeout=5000)
                        except PlaywrightError:
                            page.fill(f'#{name}', value, timeout=5000)
                    if login.get("submit_selector"):
                        page.click(login["submit_selector"])
                    else:
                        page.keyboard.press("Enter")
                    page.wait_for_load_state("domcontentloaded")
                    page.wait_for_timeout(int(float(login.get("wait_after", 2.0)) * 1000))

                if auth_mode == "cdp" and login.get("url"):
                    page.goto(login["url"], wait_until="domcontentloaded")

                page.goto(target, wait_until="domcontentloaded")
                page.wait_for_timeout(200)
                return page.content()
            finally:
                page.close()
        finally:
            browser.close()


def _resolve_engine() -> str:
    """Resolve the ENGINE setting to a concrete backend, with clear errors."""
    if ENGINE == "auto":
        return "playwright" if PLAYWRIGHT_AVAILABLE else "websockets"
    if ENGINE == "playwright" and not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError(
            "`playwright` python package not installed; pip install playwright "
            "(or rerun with --engine websockets)"
        )
    return ENGINE


# ----- Expected-key resolver (selectors: or stash_keys:) --------------------


def _resolve_expected_keys(case: dict) -> list[dict]:
    """Convert a case's expected keys into a normalised `selectors:` list
    so the downstream comparison logic only deals with one shape.

    Two equivalent inputs:

        stash_keys:
          Title: "Some exact title"
          Code: WIG-001

        selectors:
          - name: Title
            expected: "Some exact title"
          - name: Code
            expected: WIG-001
    """
    selectors = list(case.get("selectors") or [])
    if not selectors:
        for k, v in (case.get("stash_keys") or {}).items():
            if isinstance(v, str):
                selectors.append({"name": k, "expected": v})
            elif isinstance(v, dict):
                # allows stash_keys: {Title: {expected_match: "...", case_insensitive: true}}
                selectors.append({"name": k, **v})
    return selectors


# ----- Login-aware flows ----------------------------------------------------

async def _cdp_with_login(case: dict, auth_mode: str, cdp_url: str, target: str) -> str:
    """Drive the CDP session per the case's auth_mode. Returns rendered HTML
    of the target URL after login has been applied.
    """
    session = CdpSession(cdp_url)
    await session.connect()
    try:
        login = case.get("login") or {}
        if auth_mode == "cdp":
            # Pre-logged-in Chrome — just navigate
            if login.get("url"):
                await session.navigate(login["url"])
            return await session.navigate(target)

        if auth_mode == "cookies":
            cookies: list[dict] = []
            cookies.extend(login.get("cookies") or [])
            cookies_file = login.get("cookies_file")
            if cookies_file:
                cf_path = (SCRAPERS_DIR / cookies_file) if not cookies_file.startswith("/") else Path(cookies_file)
                cookies.extend(load_cookie_file(cf_path))
            if not cookies:
                raise RuntimeError("auth: cookies requires `login.cookies:` or `login.cookies_file:`")
            await session.set_cookies(cookies)
            return await session.navigate(target)

        if auth_mode == "form":
            login_url = login.get("url")
            if not login_url:
                raise RuntimeError("auth: form requires `login.url:` pointing at the login page")
            fields = login.get("fields") or {}
            # Allow {username: ${env:VAR}} substitution so creds stay out of YAML
            fields = {k: env_or(v) for k, v in fields.items()}
            if not fields:
                raise RuntimeError("auth: form requires `login.fields:` with at least one input")
            await session.navigate(login_url)
            await session.fill_form(
                fields,
                submit=login.get("submit", True),
                submit_button_selector=login.get("submit_selector"),
                wait_after=float(login.get("wait_after", 2.0)),
            )
            return await session.navigate(target)

        raise RuntimeError(f"unknown auth_mode: {auth_mode}")
    finally:
        await session.close()


# ----- Test-cases loader -----------------------------------------------------

def load_test_cases(path: Path) -> tuple[dict, list[dict]]:
    """Load a test-cases YAML file.

    Schema (loose — extra keys are ignored):

        auth:
          cdp_url: ws://localhost:9222   # global CDP endpoint
        cases:
          - file: ACCEED.yml
            target: https://acceed.jp/detail.ACST424.html
            auth: true                    # requires CDP
            selectors:
              - name: Title               # scraper field name (e.g. xPathScrapers.sceneScraper.scene.Title)
                expected: "..."           # equality match (whitespace-trimmed)
                expected_match: "wig-387"  # substring / case-insensitive match

    Returns (auth_dict, list_of_cases).
    """
    raw = path.read_text()
    data = yaml.load(raw, Loader=_StashYamlLoader) or {}
    return data.get("auth") or {}, data.get("cases") or []


def compare_expected(actual: str, spec: dict) -> dict:
    """Apply the expected vs actual comparison policy."""
    actual = (actual or "").strip()
    if "expected" in spec:
        want = (spec["expected"] or "").strip()
        return {"outcome": "match" if actual == want else "mismatch",
                "expected": want, "actual": actual}
    if "expected_match" in spec:
        needle = (spec["expected_match"] or "").strip()
        if spec.get("case_insensitive", True):
            hit = needle.lower() in actual.lower()
        else:
            hit = needle in actual
        return {"outcome": "match" if hit else "no_match",
                "expected_match": needle, "actual": actual[:300]}
    if "expected_regex" in spec:
        pat = re.compile(spec["expected_regex"])
        m = pat.search(actual)
        return {"outcome": "match" if m else "no_match",
                "expected_regex": spec["expected_regex"], "actual": actual[:300]}
    return {"outcome": "skipped", "reason": "no expected value declared"}


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

    if login_required and SKIP_LOGIN_GATED:
        result["crawl_status"] = "login_required"
        result["notes"].append("useCDP or driver.cookies — skipping anonymous crawl")
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


def process_case(case: dict, auth_cfg: dict) -> dict:
    """Process a single test-case from the test-cases.yaml file.

    Login modes supported via `auth:` (default = anonymous):
    - false / missing → gsk crawl anonymously
    - true / "cdp"    → use a pre-logged-in Chrome at --cdp-url
    - "cookies"       → call Network.setCookies via CDP, then navigate
    - "form"          → fill a login form via CDP, then navigate to target

    Output shape per case:
      file, target_url, auth, scraper_name, crawl_status,
      fields: [{name, expected, actual, outcome, ...}]
    """
    file_name = case.get("file", "?")
    target = case.get("target", "")
    auth_value = case.get("auth", False)
    if isinstance(auth_value, bool):
        auth_mode = "cdp" if auth_value else "anonymous"
    else:
        auth_mode = str(auth_value).strip().lower()
    case_auth = case.get("auth") if isinstance(case.get("auth"), dict) else {}
    cdp_url = (auth_cfg or {}).get("cdp_url") or case_auth.get("cdp_url")
    if isinstance(cdp_url, dict):
        cdp_url = cdp_url.get("cdp_url")

    result = {
        "file": file_name,
        "target_url": target,
        "auth": auth_mode,
        "cdp_url_used": cdp_url,
        "scraper_name": None,
        "crawl_status": None,
        "fields": [],
        "summary": {},
    }

    file_path = SCRAPERS_DIR / file_name
    if not file_path.exists():
        result["crawl_status"] = "scraper_not_found"
        return result

    text = file_path.read_text()
    data = yaml.load(text, Loader=_StashYamlLoader) or {}
    result["scraper_name"] = data.get("name", file_path.stem)

    if any(domain in target for domain in SKIP_DOMAINS):
        result["crawl_status"] = "domain_skipped"
        return result

    # Path that needs a CDP endpoint (auth: cdp/cookies/form/true) but has none:
    if auth_mode != "anonymous" and not cdp_url:
        result["crawl_status"] = "auth_required"
        for f in _resolve_expected_keys(case):
            result["fields"].append({"name": f.get("name"),
                                     "outcome": "auth_required",
                                     "expected": f.get("expected") or f.get("expected_match"),
                                     "actual": None})
        return result

    body = None
    page_meta: dict = {}
    try:
        if auth_mode == "anonymous":
            body, page_meta = crawl(target)
        elif _resolve_engine() == "playwright":
            body = playwright_fetch(case, auth_mode, cdp_url, target)
        else:
            body = asyncio.run(_cdp_with_login(case, auth_mode, cdp_url, target))
        result["crawl_status"] = "ok"
    except Exception as e:
        result["crawl_status"] = "cdp_error" if auth_mode != "anonymous" else "fetch_error"
        result["fields"].append({
            "name": "(fetch)", "outcome": "error",
            "auth": auth_mode, "error": str(e)[:200],
        })
        return result

    result["page_bytes"] = len(body or "")
    try:
        tree = html.fromstring(body or "")
    except (etree.XMLSyntaxError, etree.ParserError) as e:
        result["crawl_status"] = "parse_error"
        result["fields"].append({"name": "(parse)", "outcome": "error", "error": str(e)[:200]})
        return result

    # Build a selector lookup from the scraper so cases can target by field name
    vars_map = collect_common_vars(data)
    case_selectors = {s.get("name"): s for s in _resolve_expected_keys(case)}
    all_selectors = collect_selectors(data)

    matched = 0
    not_matched = 0
    mismatched = 0
    no_expected = 0
    seen_fields: set[str] = set()

    # Try scraper-defined XPath first; if it yields content, use that.
    # Otherwise fall back to the next XPath with the same leaf field name.
    by_field: dict[str, list[tuple[str, str]]] = {}
    for where, xpath in all_selectors:
        leaf = where.split(".")[-2] if where.endswith(".selector") else where.split(".")[-1]
        if leaf not in case_selectors:
            continue
        by_field.setdefault(leaf, []).append((where, xpath))

    for leaf, decls in by_field.items():
        spec = case_selectors[leaf]
        # Empty expected values mean "not yet known" — record and skip the comparison.
        if not any(spec.get(k) for k in ("expected", "expected_match", "expected_regex")):
            result["fields"].append({
                "name": leaf, "outcome": "no_expected",
                "expected": None, "actual": None,
                "xpath_count": len(decls),
            })
            no_expected += 1
            seen_fields.add(leaf)
            continue
        chosen = None
        chosen_actual = ""
        chosen_xpath = ""
        for where, xpath in decls:
            resolved = resolve_variables(xpath, vars_map)
            try:
                nodes = tree.xpath(resolved)
            except etree.XPathEvalError:
                continue
            if not nodes:
                continue
            n = nodes[0]
            if isinstance(n, etree._Element):
                actual = " ".join(t.strip() for t in n.itertext() if t.strip())
            elif isinstance(n, str):
                actual = n
            else:
                continue
            if actual.strip():
                chosen = (where, xpath)
                chosen_actual = actual
                chosen_xpath = xpath
                break
        if chosen is None:
            result["fields"].append({
                "name": leaf, "outcome": "no_match",
                "expected": spec.get("expected") or spec.get("expected_match") or spec.get("expected_regex"),
                "actual": "",
                "xpath_count": len(decls),
            })
            not_matched += 1
        else:
            cmp = compare_expected(chosen_actual, spec)
            cmp["name"] = leaf
            cmp["xpath"] = chosen_xpath
            result["fields"].append(cmp)
            if cmp["outcome"] == "match":
                matched += 1
            elif cmp["outcome"] == "mismatch":
                mismatched += 1
            elif cmp["outcome"] == "no_match":
                not_matched += 1
        seen_fields.add(leaf)

    result["summary"] = {
        "matched": matched,
        "mismatch": mismatched,
        "no_match": not_matched,
        "no_expected": no_expected,
        "fields_total": len(case_selectors),
    }
    return result


# ----- Entry points ---------------------------------------------------------

def run_pass_per_file() -> list[dict]:
    paths = sorted(SCRAPERS_DIR.glob("*.yml"))
    results: list[dict] = []
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
    return results


def run_pass_per_case(cases: list[dict], auth_cfg: dict) -> list[dict]:
    results: list[dict] = []
    for case in cases:
        r = process_case(case, auth_cfg)
        results.append(r)
        s = r.get("summary", {})
        cmp = ", ".join(
            f"{f['name']}={f['outcome']}" for f in r.get("fields", [])
        )
        sys.stdout.write(
            f" [{r['crawl_status']:>14}] auth={r.get('auth','-'):<9} "
            f"{r['file']:<22} target={(r['target_url'] or '-')[:50]:<50} "
            f"matched={s.get('matched',0)}/{s.get('fields_total',0)} "
            f"{cmp}\n"
        )
    return results


def _preflight(cases_mode: bool, engine: str) -> None:
    """Fail fast when a required fetch backend is unavailable."""
    if not cases_mode:
        if shutil.which("gsk") is None:
            sys.exit(
                "livetest.py: the `gsk` CLI is not on PATH (Mode A anonymous pass needs it).\n"
                "Install the Genspark CLI first:  npm install -g @genspark/cli\n"
                "Then set GSK_API_KEY — or run Mode B with CDP auth: --cases <file> --cdp-url ws://localhost:9222"
            )
        if not os.environ.get("GSK_API_KEY"):
            print("warning: GSK_API_KEY is not set; gsk crawl may fail to authenticate.",
                  file=sys.stderr)
        return
    if engine == "playwright" and not PLAYWRIGHT_AVAILABLE:
        sys.exit(
            "livetest.py: --engine playwright but the `playwright` package is not installed.\n"
            "Install it with:  pip install playwright\n"
            "(no browser download needed when connecting to your Chrome via --cdp-url)"
        )
    if websockets is None and not PLAYWRIGHT_AVAILABLE:
        print("warning: neither `playwright` nor `websockets` is installed; "
              "CDP login modes are unavailable "
              "(pip install playwright — recommended — or pip install websockets).",
              file=sys.stderr)
    elif websockets is None and PLAYWRIGHT_AVAILABLE:
        print("note: `websockets` not installed; CDP login modes will use the "
              "Playwright backend.", file=sys.stderr)


def main():
    global ENGINE

    parser = argparse.ArgumentParser(description="Live XPath test for Stash scrapers.")
    parser.add_argument("--cases", type=Path,
                        help="Path to test-cases YAML (replaces per-file pass)")
    parser.add_argument("--cdp-url", type=str, default=None,
                        help="Chrome DevTools Protocol endpoint, e.g. ws://localhost:9222")
    parser.add_argument("--engine", choices=["auto", "websockets", "playwright"],
                        default="auto",
                        help="CDP backend for login flows (default: auto = playwright "
                             "when installed, else websockets)")
    args = parser.parse_args()

    ENGINE = args.engine
    _preflight(bool(args.cases), ENGINE)

    cdp_url = args.cdp_url
    t0 = time.time()

    if args.cases:
        auth_cfg, cases = load_test_cases(args.cases)
        # CLI --cdp-url overrides YAML auth.cdp_url
        if cdp_url and not (auth_cfg or {}).get("cdp_url"):
            auth_cfg = dict(auth_cfg or {})
            auth_cfg["cdp_url"] = cdp_url
        results = run_pass_per_case(cases, auth_cfg or {})
        out_path = RESULTS_DIR / "live-test-cases.json"
        out_path.write_text(
            json.dumps({"auth": auth_cfg, "engine": ENGINE, "cases": results}, indent=2, default=str)
        )

        n_ok = sum(1 for r in results if r["crawl_status"] == "ok")
        n_auth = sum(1 for r in results if r["crawl_status"] == "auth_required")
        n_skip = sum(1 for r in results if r["crawl_status"] == "domain_skipped")
        n_err = sum(1 for r in results if r["crawl_status"] in ("fetch_error", "cdp_error", "parse_error", "scraper_not_found"))
        # Bucket by login mode for the "anonymous / cookies / form / cdp" summary
        n_anonymous = sum(1 for r in results if r.get("auth") == "anonymous")
        n_cookies = sum(1 for r in results if r.get("auth") == "cookies")
        n_form = sum(1 for r in results if r.get("auth") == "form")
        n_cdp = sum(1 for r in results if r.get("auth") == "cdp")
        total_matched = sum(r.get("summary", {}).get("matched", 0) for r in results)
        total_mismatched = sum(r.get("summary", {}).get("mismatch", 0) for r in results)
        total_no_match = sum(r.get("summary", {}).get("no_match", 0) for r in results)
        total_no_expected = sum(r.get("summary", {}).get("no_expected", 0) for r in results)

        print()
        print(f"=== Live-test (cases pass): {len(results)} cases, {time.time()-t0:.1f}s ===")
        print(f"  engine             : {_resolve_engine()}")
        print(f"  crawled ok         : {n_ok}")
        print(f"  auth-required      : {n_auth}")
        print(f"  domain-skipped     : {n_skip}")
        print(f"  errors             : {n_err}")
        print(f"  by login mode      : anonymous={n_anonymous} cookies={n_cookies} form={n_form} cdp={n_cdp}")
        print(f"  fields matched     : {total_matched}")
        print(f"  fields mismatch    : {total_mismatched}")
        print(f"  fields no_match    : {total_no_match}")
        print(f"  fields no_expected : {total_no_expected}")
        print(f"  results json       : {out_path}")
        return

    # Default: per-file auto-discovery pass
    results = run_pass_per_file()
    results.sort(key=lambda r: r["file"])
    (RESULTS_DIR / "live-test.json").write_text(json.dumps(results, indent=2, default=str))
    elapsed = time.time() - t0

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
