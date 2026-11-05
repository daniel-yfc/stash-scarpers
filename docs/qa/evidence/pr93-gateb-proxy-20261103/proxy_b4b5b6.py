#!/usr/bin/env python3
"""B4 live negative, B5 fragment safety, B6 control + upstream-panic separation (lease -03)."""
import json, sys, datetime
sys.path.insert(0, '/home/hatch/workspace/qa-pr93-gateb-20261103')
from gql import gql

ROOT = '/home/hatch/workspace/qa-pr93-gateb-proxy-20261103/evidence'
FIELDS = "title code details duration image urls date studio { name } tags { name }"

def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def save_pair(folder, stem, query, variables):
    ts = stamp()
    resp, dt = gql(query, variables)
    json.dump({'timestamp_utc': ts, 'request': {'query': query, 'variables': variables}},
              open(f'{ROOT}/{folder}/{stem}-request.json', 'w'), ensure_ascii=False, indent=1)
    json.dump({'timestamp_utc': ts, 'elapsed_s': dt, 'response': resp},
              open(f'{ROOT}/{folder}/{stem}-response.json', 'w'), ensure_ascii=False, indent=1)
    return resp

# ---- B4 live: nonexistent clips/999999 via sceneByURL
q_url = "query($u: String!) { scrapeSceneURL(url: $u) { %s } }" % FIELDS
resp = save_pair('B4', 'live-nonexistent-999999', q_url, {"u": "https://www.bravo-japan.com/clips/999999"})
print('B4 999999:', json.dumps((resp.get('data') or {}).get('scrapeSceneURL')), 'errors:', json.dumps(resp.get('errors'))[:200])

# ---- B5 valid QueryFragment (scene_input with url)
q_single = """query($src: ScraperSourceInput!, $in: ScrapeSingleSceneInput!) {
  scrapeSingleScene(source: $src, input: $in) { %s } }""" % FIELDS
resp = save_pair('B5', 'queryfragment-valid', q_single,
                 {"src": {"scraper_id": "BRAVO"}, "in": {"scene_input": {"url": "https://www.bravo-japan.com/clips/284"}}})
d = (resp.get('data') or {}).get('scrapeSingleScene')
print('B5 QF valid:', json.dumps(d, ensure_ascii=False)[:300], 'errors:', json.dumps(resp.get('errors'))[:200])

# ---- B5 direct fragment negative: empty-title scenes (two variants in one file pair)
cases = [
    {"case": "empty-scene_input", "variables": {"src": {"scraper_id": "BRAVO"}, "in": {"scene_input": {}}}},
    {"case": "empty-title", "variables": {"src": {"scraper_id": "BRAVO"}, "in": {"scene_input": {"title": ""}}}},
]
out_req, out_resp = [], []
for c in cases:
    ts = stamp()
    resp, dt = gql(q_single, c["variables"])
    out_req.append({'case': c['case'], 'timestamp_utc': ts, 'request': {'query': q_single, 'variables': c['variables']}})
    out_resp.append({'case': c['case'], 'timestamp_utc': ts, 'elapsed_s': dt, 'response': resp})
    print('B5 negative', c['case'], ':', json.dumps((resp.get('data') or {}).get('scrapeSingleScene'))[:150],
          'errors:', json.dumps(resp.get('errors'), ensure_ascii=False)[:300])
json.dump(out_req, open(f'{ROOT}/B5/direct-fragment-negative-request.json', 'w'), ensure_ascii=False, indent=1)
json.dump(out_resp, open(f'{ROOT}/B5/direct-fragment-negative-response.json', 'w'), ensure_ascii=False, indent=1)

# ---- B6 control: KOShop frozen case product_id=41979 (other scraper, must be unaffected)
resp = save_pair('B6', 'control-scraper-result', q_url, {"u": "https://www.ko-shop.com/products/detail.php?product_id=41979"})
d = (resp.get('data') or {}).get('scrapeSceneURL')
ctrl = {'scraper': 'KOShop', 'url': 'https://www.ko-shop.com/products/detail.php?product_id=41979',
        '_note': 'control result is stored in control-scraper-result-response.json alongside this summary'}
if d:
    ctrl.update({'title': d.get('title'), 'code': d.get('code'), 'urls': d.get('urls')})
    print('B6 KOShop control:', d.get('title'), '| code:', d.get('code'))
else:
    ctrl.update({'errors': resp.get('errors')})
    print('B6 KOShop control NO DATA:', json.dumps(resp.get('errors'))[:300])
json.dump(ctrl, open(f'{ROOT}/B6/control-scraper-summary.json', 'w'), ensure_ascii=False, indent=1)

# ---- B6 separation: unmatched DVD URL (known upstream panic; recorded separately, not a PR #93 case)
resp = save_pair('B6', 'upstream-unmatched-dvds284', q_url, {"u": "https://www.bravo-japan.com/dvds/284"})
print('B6 dvds/284:', json.dumps((resp.get('data') or {}).get('scrapeSceneURL'))[:100],
      'errors:', json.dumps(resp.get('errors'), ensure_ascii=False)[:300])
print('B4/B5/B6 GraphQL DONE')
