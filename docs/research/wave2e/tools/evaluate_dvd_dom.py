#!/usr/bin/env python3
"""Research-only OFFLINE XPath evaluation for BRAVO rendered DOM (no network/Stash).
Usage: python docs/research/wave2e/tools/evaluate_dvd_dom.py INPUT.html [INPUT.html ...] [--output path]
Requires: pip install lxml
Do NOT publish unsanitized source HTML, credentials or private page captures.
"""
import argparse, hashlib, json, re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from lxml import html

ZWSP = "\u200b"
XP = {
  "title_historical_preceding2": "//h2[normalize-space(translate(string(.), '\u200b', ''))='品番']/preceding::h2[2]",
  "code_historical_following1": "//h2[normalize-space(translate(string(.), '\u200b', ''))='品番']/following::h2[1]",
  "canonical": "//link[@rel='canonical']/@href",
  "details_meta": "//meta[@name='description']/@content",
  "og_title": "//meta[@property='og:title']/@content",
  "og_image": "//meta[@property='og:image']/@content",
  "release_date_historical_following1": "//h2[normalize-space(.)='発売日']/following::h2[1]",
  "dvd_total_minutes_historical_following1": "//h2[normalize-space(.)='収録時間']/following::h2[1]",
  "label_historical_preceding1": "//h2[normalize-space(.)='レーベル']/preceding::h2[1]",
  "sitewide_keywords": "//meta[@name='keywords']/@content",
  "all_image_urls_unsafe": "//img/@src",
  "video_posters": "//video/@poster",
}
HISTORICAL = {
  "281": ("熊ケツ4", "281"),
  "046": ("ゆるゆる雄太のデブ竿ぽちゃ穴食べ放題!", "046"),
  "173": ("筋肉BANANA", "173"),
  "215": ("種竿狂", "215"),
}
def clean(v):
  if isinstance(v,str): return " ".join(v.replace(ZWSP, "").split())
  return " ".join(v.itertext()).replace(ZWSP,"").strip()
def safe_url(v):
  if not v: return ""
  p=urlsplit(v)
  if p.scheme not in {"https","http"} or p.username or p.password: return "[UNSAFE_URL_SUPPRESSED]"
  return urlunsplit((p.scheme,p.hostname or "",p.path,"",""))
def evaluate(path):
  data=path.read_bytes()
  doc=html.fromstring(data.decode("utf-8"))
  title=clean(doc.xpath("string(//title[1])"))
  challenge="just a moment" in title.lower() or bool(doc.xpath("//*[contains(@class,'cf-challenge')]"))
  result={
    "file":path.name,
    "input_sha256":hashlib.sha256(data).hexdigest(),
    "input_bytes":len(data),
    "classification":"CHALLENGE_HTML" if challenge else "DOM_PARSE_ONLY_NOT_LIVE_VERIFIED",
    "page_title":title[:160],
    "selectors":{},
  }
  for name,xpath in XP.items():
    nodes=doc.xpath(xpath)
    values=[clean(n) for n in nodes]
    if name in {"canonical","og_image","all_image_urls_unsafe","video_posters"}:
      values=[safe_url(v) for v in values]
    elif name in {"details_meta","sitewide_keywords"}:
      values=["sha256:"+hashlib.sha256(v.encode("utf8")).hexdigest()+";chars:"+str(len(v)) for v in values]
    result["selectors"][name]={"xpath":xpath,"cardinality":len(nodes),"values":values[:8],"truncated":len(nodes)>8}
  og=doc.xpath(XP["og_image"])
  media=re.findall(r"(?:^|/)media/([^/]+)",og[0]) if og else []
  heroes=[img for img in doc.xpath("//img[@src]") if media and media[0] in (img.get("src") or "")]
  result["hero_vs_og_image"]={"same_media_asset_img_count":len(heroes),"alts":[clean(x.get("alt") or "") for x in heroes[:4]],"note":"same asset does not guarantee actual DVD cover"}
  product=path.stem.replace("dvd-","")
  if product in HISTORICAL:
    expected_title,expected_code=HISTORICAL[product]
    result["historical_expectation"]={
      "title_match":result["selectors"]["title_historical_preceding2"]["values"]==[expected_title],
      "code_match":result["selectors"]["code_historical_following1"]["values"]==[expected_code],
      "code_preserves_leading_zero":expected_code.startswith("0"),
    }
  result["caveat"]="Offline file alone cannot prove HTTP/CDP readiness or current website behavior. Review output & sanitize source before committing."
  return result
def main():
  ap=argparse.ArgumentParser(description=__doc__)
  ap.add_argument("paths",nargs="+",type=Path)
  ap.add_argument("--output",type=Path)
  args=ap.parse_args()
  records=[evaluate(path) for path in args.paths]
  s=json.dumps({"tool":"evaluate_dvd_dom.py","classification":"OFFLINE_XPATH_ONLY","records":records},ensure_ascii=False,indent=2)+"\n"
  if args.output: args.output.write_text(s,encoding="utf8")
  else: print(s)
if __name__=="__main__": main()
