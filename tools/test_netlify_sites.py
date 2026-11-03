import urllib.request
import json

token = 'nfp_iUtF5syw757JnXXGpoX7sB3cwVFJ3jtu4ad3'
req = urllib.request.Request(
    'https://api.netlify.com/api/v1/sites',
    headers={'Authorization': f'Bearer {token}'}
)
with urllib.request.urlopen(req) as resp:
    sites = json.loads(resp.read().decode())
    print(f'Total existing sites on Netlify: {len(sites)}')
    for s in sites[:10]:
        print(f"- {s.get('name')} | {s.get('ssl_url')} | id: {s.get('id')}")
