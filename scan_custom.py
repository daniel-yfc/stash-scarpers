import re, hashlib, json, os, sys
ROOT = "sanitized/docs/qa"
PATTERNS = {
 "cookie_header": re.compile(r"(?i)\b(set-)?cookie\s*[:=]"),
 "authorization": re.compile(r"(?i)\bauthorization\s*[:=]"),
 "bearer_basic": re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9+/=_.\-]{8,}"),
 "jwt": re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{5,}"),
 "wix_session": re.compile(r"(?i)(sessionId|mpaSessionId|instanceId|svSession|wixSession2?|wixClientId)[\"']?\s*[:=]"),
 "api_key_token": re.compile(r"(?i)(api[-_]?key|access[-_]?token|x-api-key|password|passwd|secret)\s*[:=]"),
 "tailscale_ip": re.compile(r"\b100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b"),
 "rfc1918": re.compile(r"\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"),
 "cdp_ws": re.compile(r"(ws://[^\s\"'<>]+|devtools/browser/[0-9a-f\-]{8,}|/json/(version|list))"),
 "internal_host": re.compile(r"(?i)(\blxc\b|tailnet|\.ts\.net|magicdns|100\.x)"),
 "email": re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),
 "graphql_auth": re.compile(r"(?i)(x-stash|stash[-_]?api|graphql[^\n]{0,40}(token|auth|key))"),
 "long_hex_token": re.compile(r"\b[0-9a-f]{32,}\b"),
}
findings = []
for dp, dn, fn in os.walk(ROOT):
    for f in sorted(fn):
        p = os.path.join(dp, f)
        try: data = open(p, "rb").read().decode("utf-8", "replace")
        except Exception: continue
        for i, line in enumerate(data.splitlines(), 1):
            for name, rx in PATTERNS.items():
                for m in rx.finditer(line):
                    val = m.group(0)
                    findings.append({"file": p.replace("raw-80f5307/",""), "line": i, "pattern": name,
                                     "value_sha256_12": hashlib.sha256(val.encode()).hexdigest()[:12],
                                     "value_len": len(val)})
out = {}
for fd in findings: out.setdefault(fd["pattern"], []).append(fd)
for k in sorted(out): print(f"{k}: {len(out[k])}")
json.dump(findings, open("custom-scan-findings.json","w"), indent=1)
print("total", len(findings))
