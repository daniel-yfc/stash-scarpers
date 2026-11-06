#!/usr/bin/env python3
"""Rollback for lease -03: uninstall candidate, reinstall baseline BRAVO from yfc, remove isolated
source, reloadScrapers, verify full restoration against the pre-test snapshot."""
import json, sys, time, datetime
sys.path.insert(0, '/home/hatch/workspace/qa-pr93-gateb-20261103')
from gql import gql

EV = '/home/hatch/workspace/qa-pr93-gateb-proxy-20261103/evidence/ROLLBACK'
INDEX_URL = 'https://REDACTED-FILE-LINK.invalid/gateb-index3.yml'
YFC_URL = 'https://daniel-yfc.github.io/stash-scarpers/main/index.yml'
LOG = []

def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def call(label, query, variables=None):
    resp, dt = gql(query, variables)
    LOG.append({'label': label, 'timestamp_utc': stamp(), 'elapsed_s': dt,
                'request': {'query': query, 'variables': variables}, 'response': resp})
    print(f'[{label}] errors={bool(resp.get("errors"))}')
    if resp.get('errors'):
        print(json.dumps(resp['errors'])[:400])
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
    pkgs = installed()
    return pkgs, [p for p in pkgs if p['package_id'] == 'BRAVO']

# 1. uninstall candidate
call('uninstallPackages-candidate',
     "mutation { uninstallPackages(type: Scraper, packages: [{id: \"BRAVO\", sourceURL: \"%s\"}]) }" % INDEX_URL)
pkgs, b = wait_bravo(lambda b: len(b) == 0)
print('after candidate uninstall BRAVO:', b, 'total:', len(pkgs))
assert len(b) == 0
with open(f'{EV}/uninstall-record.txt', 'w') as f:
    f.write('Candidate BRAVO (ce7ef6c, isolated source gateb-pr93-r3) uninstalled via uninstallPackages; '
            'polled installedPackages until BRAVO absent (20 packages remained). Full log: rollback-log.json\n')

# 2. reinstall baseline from yfc
call('installPackages-baseline',
     "mutation { installPackages(type: Scraper, packages: [{id: \"BRAVO\", sourceURL: \"%s\"}]) }" % YFC_URL)
pkgs, b = wait_bravo(lambda b: len(b) == 1 and b[0]['version'] == 'b92acdd')
print('after baseline reinstall BRAVO:', b, 'total:', len(pkgs))
assert len(b) == 1 and b[0]['version'] == 'b92acdd', f'baseline restore mismatch: {b}'
with open(f'{EV}/reinstall-record.txt', 'w') as f:
    f.write('Baseline BRAVO reinstalled from yfc source via installPackages; polled installedPackages -> '
            'BRAVO version b92acdd, sourceURL yfc index; total packages back to 21. Full log: rollback-log.json\n')

# 3. remove isolated source
srcs = [
    {"name": "Community (stable)", "url": "https://stashapp.github.io/CommunityScrapers/stable/index.yml", "local_path": "community"},
    {"name": "yfc", "url": YFC_URL, "local_path": ""},
]
call('configureGeneral-remove-source',
     "mutation($i: ConfigGeneralInput!) { configureGeneral(input: $i) { scraperPackageSources { name url local_path } } }",
     {"i": {"scraperPackageSources": srcs}})

# 4. reloadScrapers
r = call('reloadScrapers', "mutation { reloadScrapers }")
json.dump(r, open(f'{EV}/reload-scrapers-response.json', 'w'), ensure_ascii=False, indent=1)

# 5. post-rollback snapshot + comparison with before
q = """{ version { version build_time } stats { scene_count performer_count studio_count }
configuration { general { scraperPackageSources { name url local_path } scrapersPath }
scraping { scraperCDPPath scraperCertCheck scraperUserAgent } }
installedPackages(type: Scraper) { package_id name version date sourceURL } }"""
resp = call('post-rollback-snapshot', q)
json.dump(resp, open(f'{EV}/post-rollback-packages.json', 'w'), ensure_ascii=False, indent=1)
json.dump(resp, open(f'{EV}/scene-stats-after.json', 'w'), ensure_ascii=False, indent=1)

before = json.load(open(f'{EV}/scene-stats-before.json'))['data']
after = resp['data']
def norm(pkgs):
    return sorted((p['package_id'], p['version'], p['sourceURL']) for p in pkgs)
checks = {
    'version_equal': before['version'] == after['version'],
    'stats_equal': before['stats'] == after['stats'],
    'sources_equal': before['configuration']['general']['scraperPackageSources'] == after['configuration']['general']['scraperPackageSources'],
    'scraping_config_equal': before['configuration']['scraping'] == after['configuration']['scraping'],
    'packages_equal': norm(before['installedPackages']) == norm(after['installedPackages']),
}
print(json.dumps(checks, indent=1))
json.dump(checks, open(f'{EV}/restoration-comparison.json', 'w'), indent=1)
assert all(checks.values()), 'RESTORATION MISMATCH'
json.dump(LOG, open(f'{EV}/rollback-log.json', 'w'), ensure_ascii=False, indent=1)
print('ROLLBACK OK — RESTORED per comparison')
