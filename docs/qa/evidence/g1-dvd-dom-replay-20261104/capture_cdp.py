#!/usr/bin/env python3
"""Agent D independent DOM capture via the environment's designated CDP
Chrome (stash-test headless browser). Browsing only: navigates public
BRAVO DVD pages, records the document navigation chain (statuses incl.
redirects) from CDP Network events, waits for an explicit completion
condition, and saves the rendered DOM + SHA-256. Stash (9098) is never
queried for writes; the only Stash call is the read-only CDP-path config
lookup used by all prior Gate B captures.
"""
import json, subprocess, sys, time, hashlib, os
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path.home() / "workspace/qa-pr93-gateb-20261103"))
from gql import gql, PROXY
import websocket

OUT = Path(__file__).parent
RAW = OUT / "raw"; RAW.mkdir(exist_ok=True)
PAGES = ["234", "084", "046", "00", "999999"]

resp, _ = gql('{ configuration { scraping { scraperCDPPath } } }')
CDP_BASE = resp['data']['configuration']['scraping']['scraperCDPPath'].rsplit('/json/version', 1)[0]

def cdp_http(method, path):
    r = subprocess.run(["curl", "-s", "--proxy", PROXY, "-X", method, CDP_BASE + path],
                       capture_output=True, text=True)
    return r.stdout

class CDP:
    def __init__(self, ws_url):
        os.environ["http_proxy"] = PROXY; os.environ["https_proxy"] = PROXY
        self.ws = websocket.create_connection(ws_url, timeout=90, suppress_origin=True)
        self.i = 0
        self.events = []
    def send(self, method, params=None, wait=True):
        self.i += 1
        mid = self.i
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        if not wait:
            return None
        while True:
            m = json.loads(self.ws.recv())
            if m.get("id") == mid:
                return m
            self.events.append(m)
    def pump(self, seconds):
        self.ws.settimeout(seconds)
        try:
            while True:
                self.events.append(json.loads(self.ws.recv()))
        except Exception:
            pass
        self.ws.settimeout(90)
    def eval(self, expr):
        r = self.send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
        return r["result"]["result"].get("value")
    def close(self):
        try: self.ws.close()
        except Exception: pass

def capture(code):
    url = f"https://www.bravo-japan.com/dvds/{code}"
    target = json.loads(cdp_http("PUT", "/json/new?about:blank"))
    cdp = CDP(target["webSocketDebuggerUrl"])
    rec = {"dvd": code, "requested_url": url,
           "captured_at_utc": datetime.now(timezone.utc).isoformat(),
           "capture_engine": "stash-test headless Chrome via CDP (Page/Network/Runtime)"}
    try:
        cdp.send("Page.enable"); cdp.send("Network.enable"); cdp.send("Runtime.enable")
        cdp.send("Page.navigate", {"url": url}, wait=False)
        # wait for completion condition: hinban h2 (products) or 404 title; cap 40s
        deadline = time.time() + 40
        cond = None
        while time.time() < deadline:
            cdp.pump(1.0)
            v = cdp.eval("JSON.stringify({hinban: !!document.evaluate(\"//h2[contains(.,'品番')]\", document).iterateNext(), title: document.title, ready: document.readyState})")
            if v:
                st = json.loads(v)
                if st.get("hinban"):
                    cond = "hinban_h2_present"; break
                if "404" in (st.get("title") or ""):
                    cond = "page_title_404"; break
            time.sleep(0.5)
        rec["completion_condition"] = cond or "timeout_40s"
        time.sleep(3)  # settle for late hydration
        cdp.pump(0.5)
        html = cdp.eval("document.documentElement.outerHTML")
        rec["final_url"] = cdp.eval("location.href")
        rec["page_title"] = cdp.eval("document.title")
        chain = []
        for e in cdp.events:
            if e.get("method") == "Network.responseReceived":
                p = e["params"]
                if p.get("type") == "Document":
                    chain.append({"url": p["response"]["url"], "status": p["response"]["status"]})
        rec["navigation_chain"] = chain
        rec["http_status_final_document"] = chain[-1]["status"] if chain else None
    finally:
        cdp.close()
        cdp_http("GET", "/json/close/" + target["id"])
    data = html.encode("utf-8")
    (RAW / f"dvd-{code}.rendered.html").write_bytes(data)
    rec["dom_file"] = f"dvd-{code}.rendered.html"
    rec["dom_bytes"] = len(data)
    rec["dom_sha256"] = hashlib.sha256(data).hexdigest()
    return rec

def main():
    results = []
    for code in PAGES:
        rec = capture(code)
        results.append(rec)
        print(code, "| status:", rec["http_status_final_document"], "| cond:", rec["completion_condition"],
              "| bytes:", rec["dom_bytes"], "| sha:", rec["dom_sha256"][:16], "| chain:", len(rec["navigation_chain"]))
    (OUT / "capture-provenance.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")

if __name__ == "__main__":
    main()
