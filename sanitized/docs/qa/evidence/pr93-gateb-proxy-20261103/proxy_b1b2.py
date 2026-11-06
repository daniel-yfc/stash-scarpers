#!/usr/bin/env python3
"""B1/B2: clips 284 & 282, 3 independent scrapeSceneURL runs each.
reloadScrapers before run 3 of each page to defeat caching. Saves spec-named request/response files."""
import json, sys, datetime
sys.path.insert(0, '/home/hatch/workspace/qa-pr93-gateb-20261103')
from gql import gql

EV = '/home/hatch/workspace/qa-pr93-gateb-proxy-20261103/evidence/B1_B2'
Q = """query($u: String!) { scrapeSceneURL(url: $u) {
  title code details duration image urls date
  studio { name } tags { name } performers { name } } }"""

def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

summary = []
for page in (284, 282):
    url = f'https://www.bravo-japan.com/clips/{page}'
    for run in (1, 2, 3):
        if run == 3:
            r, _ = gql("mutation { reloadScrapers }")
            print(f'page {page}: reloadScrapers before run3 ->', r.get('data'))
        variables = {"u": url}
        ts = stamp()
        resp, dt = gql(Q, variables)
        json.dump({'timestamp_utc': ts, 'operation': 'scrapeSceneURL',
                   'request': {'query': Q, 'variables': variables}},
                  open(f'{EV}/clips-{page}-run{run}-request.json', 'w'), ensure_ascii=False, indent=1)
        json.dump({'timestamp_utc': ts, 'elapsed_s': dt, 'response': resp},
                  open(f'{EV}/clips-{page}-run{run}-response.json', 'w'), ensure_ascii=False, indent=1)
        d = (resp.get('data') or {}).get('scrapeSceneURL')
        if d:
            det = d.get('details')
            summary.append({'page': page, 'run': run, 'title': d.get('title'), 'code': d.get('code'),
                            'duration': d.get('duration'), 'details_len': len(det) if det else 0,
                            'details_repr_head': repr(det[:40]) if det else repr(det),
                            'image': d.get('image'), 'urls': d.get('urls'), 'date': d.get('date'),
                            'studio': d.get('studio'), 'tags_n': len(d.get('tags') or [])})
            print(f"{page} run{run}: title={d.get('title')!r} code={d.get('code')!r} duration={d.get('duration')!r} details_len={len(det) if det else 0} image={d.get('image')!r}")
        else:
            summary.append({'page': page, 'run': run, 'errors': resp.get('errors')})
            print(f'{page} run{run}: NO DATA errors={json.dumps(resp.get("errors"))[:300]}')
json.dump(summary, open(f'{EV}/field-summary.json', 'w'), ensure_ascii=False, indent=1)
print('B1/B2 DONE')
