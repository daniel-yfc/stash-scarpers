import json, glob
from lxml import html as LH
RAW="raw-80f5307"; SAN="sanitized"
ev="docs/qa/evidence/pr93-gateb-proxy-20261103"
bad=[]
for p in glob.glob(f"{RAW}/{ev}/**/*.json", recursive=True)+glob.glob(f"{SAN}/{ev}/**/*.json", recursive=True):
    try: json.load(open(p))
    except Exception as e: bad.append((p,str(e)[:60]))
print("json parse failures:", bad)
XP = {
 "Title": "//h1[1]",
 "Code": "//h2[normalize-space()='Clip']/preceding::h2[1]",
 "URLs": "//link[@rel='canonical']/@href",
 "Tags": "//meta[@name='keywords']/@content",
 "Details": "//div[@id='comp-kbfkf17h']//span[contains(@class,'wixui-rich-text__text')][normalize-space(translate(.,'​','')) != ''][1]",
 "PosterImgs": "//div[@id='comp-kbfkf17h']//img",
}
for n in ("282","284"):
    res={}
    for tn, root in (("raw",RAW),("san",SAN)):
        doc = LH.parse(f"{root}/{ev}/B3/page-html-{n}.html")
        r = {}
        for k,x in XP.items():
            v = doc.xpath(x)
            r[k] = [ (e.text_content().strip()[:60] if hasattr(e,'text_content') else str(e)[:80]) for e in v ]
        res[tn]=r
    print(f"page {n}: raw==sanitized replay: {res['raw']==res['san']}")
    for k in XP: print(f"   {k}: {res['raw'][k][:2]}")
# semantic equality of transformed JSONs after redacting raw the same way
import re
IP_RX = re.compile(r"\b100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b")
MUSE_RX = re.compile(r"https://muse\.ai/files/[^\s\"'<>\\]+")
for rel in ["B0/install-record.json","B0/installedPackages.json","ROLLBACK/post-rollback-packages.json","ROLLBACK/rollback-log.json","ROLLBACK/scene-stats-after.json","ROLLBACK/scene-stats-before.json"]:
    raw = open(f"{RAW}/{ev}/{rel}", encoding="utf-8").read()
    red = MUSE_RX.sub("https://REDACTED-FILE-LINK.invalid/gateb-index3.yml", IP_RX.sub("REDACTED-TAILNET-IP", raw))
    print(rel, "semantic-equal-after-redaction:", json.loads(red) == json.load(open(f"{SAN}/{ev}/{rel}")))
