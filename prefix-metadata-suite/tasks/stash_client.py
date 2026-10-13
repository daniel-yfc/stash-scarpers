"""Shared Stash GraphQL client for the suite's task scripts.

Single home for address, timeout, proxy, and response parsing, so a
timeout / error-text / connection change applies to every task at once.
The five task scripts import graphql() from here instead of defining
their own copies.

Address: STASH_URL env var (default: local placeholder, no real
address in the public repo). It is the only address input.

Proxy: curl is used (urllib proxy handling is unreliable here).
  - STASH_PROXY, when set, is passed to curl --proxy unchanged.
  - Otherwise HTTPS_PROXY is used, with its port rewritten to the
    Stash egress port (3130): the ambient HTTPS_PROXY points at the
    general egress proxy (:3128), while Stash traffic must go through
    the same proxy host on the Stash port. Only the port is swapped;
    scheme, auth, and host are preserved.
  - When neither is set, no --proxy is passed at all (an empty
    --proxy can fail and surface as a JSON parse error).

Errors: a non-zero curl exit or a non-JSON response raises
StashConnectionError instead of a bare JSONDecodeError.
"""
import json
import os
import subprocess
from urllib.parse import urlparse, urlunparse

DEFAULT_URL = "http://localhost:9999/graphql"
TIMEOUT = 60
STASH_PROXY_PORT = "3130"


class StashConnectionError(ConnectionError):
    """Stash endpoint unreachable, or answered with non-JSON."""


def _proxy_args() -> list[str]:
    """Build the curl --proxy args (empty list when no proxy is set)."""
    proxy = os.environ.get("STASH_PROXY", "")
    if proxy:
        return ["--proxy", proxy]
    proxy = os.environ.get("HTTPS_PROXY", "")
    if not proxy:
        return []
    parsed = urlparse(proxy)
    if not parsed.port:
        return ["--proxy", proxy]
    netloc = parsed.hostname or ""
    if parsed.username:
        auth = parsed.username
        if parsed.password:
            auth += ":" + parsed.password
        netloc = auth + "@" + netloc
    netloc += ":" + STASH_PROXY_PORT
    return ["--proxy", urlunparse((parsed.scheme, netloc, "", "", "", ""))]


def graphql(query: str, variables: dict | None = None) -> dict:
    """POST one GraphQL query to Stash and return the parsed JSON."""
    url = os.environ.get("STASH_URL", DEFAULT_URL)
    payload = json.dumps({"query": query, "variables": variables or {}})
    cmd = [
        "curl", "-s", "--max-time", str(TIMEOUT),
        *_proxy_args(),
        "-H", "Content-Type: application/json",
        "-d", payload,
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT + 10)
    if result.returncode != 0:
        raise StashConnectionError(
            f"curl exited {result.returncode}: {result.stderr.strip()[:300]}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise StashConnectionError(
            f"non-JSON response from Stash: {result.stdout[:300]!r}") from exc
