#!/usr/bin/env python3
"""Lease -03 install sequence: add isolated source, swap baseline BRAVO -> candidate ce7ef6c.
Saves every GraphQL request/response under evidence/B0/."""
import json, sys, time, datetime
sys.path.insert(0, '/home/hatch/workspace/qa-pr93-gateb-20261103')
from gql import gql

EV = '/home/hatch/workspace/qa-pr93-gateb-proxy-20261103/evidence/B0'
INDEX_URL = 'https://muse.ai/files/1261807643693502/977119628804735/v8daql0o87t5s5fc6nvbn281/gateb-index3.yml'
YFC_URL = 'https://daniel-yfc.github.io/stash-scarpers/main/index.yml'
LOG = []

def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def call(label, query, variables=None):
    t0 = stamp()
    resp, dt = gql(query, variables)
    rec = {'label': label, 'timestamp_utc': t0, 'elapsed_s': dt,
           'request': {'query': query, 'variables': variables}, 'response': resp}
    LOG.append(rec)
    print(f"[{label}] elapsed={dt}s errors={bool(resp.get('errors'))}")
    if resp.get('errors'):
        print(json.dumps(resp['errors'])[:600])
    return resp

def installed():
    resp, _ = gql("{ installedPackages(type: Scraper) { package_id version sourceURL } }")
    return resp['data']['installedPackages']

def wait_bravo(pred, timeout=120):
    t0 = time.time()
    while time.time() - t0 < timeout:
        pkgs = installed()
        b = [p for p in pkgs if p['package_id'] == 'BRAVO']
        if pred(b):
            return pkgs, b
        time.sleep(3)
    return installed(), [p for p in installed() if p['package_id'] == 'BRAVO']

# 1. add isolated source
srcs = [
    {"name": "Community (stable)", "url": "https://stashapp.github.io/CommunityScrapers/stable/index.yml", "local_path": "community"},
    {"name": "yfc", "url": YFC_URL, "local_path": ""},
    {"name": "gateb-pr93-r3", "url": INDEX_URL, "local_path": "gateb-pr93-r3"},
]
r = call('configureGeneral-add-source',
         "mutation($i: ConfigGeneralInput!) { configureGeneral(input: $i) { scraperPackageSources { name url local_path } } }",
         {"i": {"scraperPackageSources": srcs}})
assert r.get('data'), 'add source failed'

# 2. available packages from isolated source
r = call('availablePackages-isolated',
         "query($s: String!) { availablePackages(type: Scraper, source: $s) { package_id version date } }",
         {"s": INDEX_URL})
json.dump(r, open(f'{EV}/available-isolated-response.json', 'w'), ensure_ascii=False, indent=1)

# 3. uninstall baseline BRAVO
r = call('uninstallPackages-baseline',
         "mutation { uninstallPackages(type: Scraper, packages: [{id: \"BRAVO\", sourceURL: \"%s\"}]) }" % YFC_URL)
pkgs, b = wait_bravo(lambda b: len(b) == 0)
print('after uninstall BRAVO:', b, 'total pkgs:', len(pkgs))
assert len(b) == 0, 'baseline uninstall did not land'

# 4. install candidate
r = call('installPackages-candidate',
         "mutation { installPackages(type: Scraper, packages: [{id: \"BRAVO\", sourceURL: \"%s\"}]) }" % INDEX_URL)
pkgs, b = wait_bravo(lambda b: len(b) == 1 and b[0]['version'] == 'ce7ef6c')
print('after install BRAVO:', b, 'total pkgs:', len(pkgs))
assert len(b) == 1 and b[0]['version'] == 'ce7ef6c', f'candidate install mismatch: {b}'

# 5. verification queries
r = call('installedPackages-after', "{ installedPackages(type: Scraper) { package_id name version date sourceURL } }")
json.dump(r, open(f'{EV}/installedPackages.json', 'w'), ensure_ascii=False, indent=1)
r = call('listScrapers-after', "{ listScrapers(types: [SCENE]) { id scene { supported_scrapes urls } } }")
json.dump(r, open(f'{EV}/listScrapers.json', 'w'), ensure_ascii=False, indent=1)
bravo = [s for s in r['data']['listScrapers'] if s['id'] == 'BRAVO']
print('BRAVO listScrapers entry:', bravo)
print('total scene scrapers:', len(r['data']['listScrapers']))

json.dump(LOG, open(f'{EV}/install-record.json', 'w'), ensure_ascii=False, indent=1)
print('INSTALL SEQUENCE OK')
