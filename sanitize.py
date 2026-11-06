import re, os, shutil, hashlib, csv, json
BASE = os.path.expanduser("~/workspace/pr93-lease03-remediation-20261106")
RAW = os.path.join(BASE, "raw-80f5307")
SAN = os.path.join(BASE, "sanitized")
SCOPE = []
ev = "docs/qa/evidence/pr93-gateb-proxy-20261103"
for dp, dn, fn in os.walk(os.path.join(RAW, ev)):
    for f in fn: SCOPE.append(os.path.relpath(os.path.join(dp, f), RAW))
for f in os.listdir(os.path.join(RAW, "docs/qa")):
    if f.startswith("PR93-GATEB-PROXY-") or f == "PR93-DURATION-DEFERRED-SPEC.md":
        SCOPE.append(os.path.join("docs/qa", f))
SCOPE = sorted(set(SCOPE))

IP_RX = re.compile(r"\b100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b")
MUSE_RX = re.compile(r"https://muse\.ai/files/[^\s\"'<>\\]+")
MPA_RX = re.compile(r"((?:mpaSessionId|\"mpaSessionId\")[\"']?\s*[:=]\s*\"?)([A-Za-z0-9_\-]{8,})")
HOST_RX = re.compile(r"\blxc:(9222|9999|9098)\b")

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""): h.update(chunk)
    return h.hexdigest()

rows = []
for rel in SCOPE:
    src = os.path.join(RAW, rel); dst = os.path.join(SAN, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    data = open(src, "rb").read()
    osha = hashlib.sha256(data).hexdigest()
    text = data.decode("utf-8", "surrogateescape")
    trans = []
    new, n = IP_RX.subn("REDACTED-TAILNET-IP", text)
    if n: text = new; trans.append(f"tailnet_ip_redacted x{n}")
    new, n = MUSE_RX.subn("https://REDACTED-FILE-LINK.invalid/gateb-index3.yml", text)
    if n: text = new; trans.append(f"file_share_url_redacted x{n}")
    if rel.endswith(".html"):
        def mpa_sub(m): return m.group(1) + "REDACTED-00001"[:len(m.group(2))] if len(m.group(2)) >= 14 else m.group(1) + "REDACTED"
        new, n = MPA_RX.subn(mpa_sub, text)
        if n: text = new; trans.append(f"wix_mpa_session_id_redacted x{n}")
    new, n = HOST_RX.subn(r"stash-test-host:\1", text)
    if n: text = new; trans.append(f"internal_hostname_redacted x{n}")
    out = text.encode("utf-8", "surrogateescape")
    if rel.endswith("MANIFEST-LIVE.sha256"):
        # regenerated later, after all other sanitized files exist
        rows.append([rel, osha, rel, "REGENERATED", "manifest_regenerated_for_sanitized_bytes"])
        open(dst, "wb").write(b"")
        continue
    open(dst, "wb").write(out)
    ssha = hashlib.sha256(out).hexdigest()
    rows.append([rel, osha, rel, ssha, "; ".join(trans) if trans else "none (byte-identical copy)"])

# regenerate sanitized MANIFEST-LIVE.sha256 from sanitized evidence bytes
evdir = os.path.join(SAN, ev)
entries = []
for dp, dn, fn in os.walk(evdir):
    for f in sorted(fn):
        p = os.path.join(dp, f); r = os.path.relpath(p, evdir)
        if r == "MANIFEST-LIVE.sha256": continue
        entries.append((r, sha(p)))
entries.sort()
with open(os.path.join(evdir, "MANIFEST-LIVE.sha256"), "w") as fh:
    for r, h in entries: fh.write(f"{h}  ./{r}\n")
for row in rows:
    if row[3] == "REGENERATED":
        row[3] = sha(os.path.join(SAN, row[0]))

with open(os.path.join(BASE, "ORIGINAL-TO-SANITIZED-MAPPING.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["original_path", "original_sha256", "sanitized_path", "sanitized_sha256", "transformation"])
    w.writerows(rows)
with open(os.path.join(BASE, "PUBLIC-SANITIZED-MANIFEST.sha256"), "w") as fh:
    for r in rows: fh.write(f"{r[3]}  {r[2]}\n")
changed = [r for r in rows if "none" not in r[4]]
print(f"scope files: {len(rows)}; transformed: {len(changed)}")
for r in changed: print(" ", r[0], "->", r[4])
