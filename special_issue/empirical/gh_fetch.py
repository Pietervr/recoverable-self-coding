import json
import os
import subprocess

os.makedirs('/tmp/gh', exist_ok=True)
REPOS = [("pallets", "flask"), ("cli", "cli"), ("vercel", "next.js")]

Q = ('{ repository(owner:"%s",name:"%s"){ pullRequests(first:100%s, '
     'orderBy:{field:CREATED_AT,direction:ASC}){ '
     'nodes{ number createdAt mergedAt closedAt merged reviewDecision title } '
     'pageInfo{ hasNextPage endCursor } } } }')


import time


def gql(query):
    last = ''
    for attempt in range(6):
        try:
            r = subprocess.run(["gh", "api", "graphql", "-f", "query=" + query],
                               capture_output=True, text=True, timeout=90)
            if r.returncode == 0:
                return json.loads(r.stdout)
            last = r.stderr[:200]
        except Exception as e:
            last = str(e)[:200]
        time.sleep(2 * (attempt + 1))  # 2,4,6,8,10s backoff for transient 502/timeouts
    raise RuntimeError("gql failed after retries: " + last)


for o, n in REPOS:
    out = f'/tmp/gh/{o}__{n}.json'
    if os.path.exists(out):
        print(f'have {o}/{n}', flush=True)
        continue
    nodes, cursor, pages = [], None, 0
    while True:
        after = f', after: "{cursor}"' if cursor else ''
        d = gql(Q % (o, n, after))
        pr = d['data']['repository']['pullRequests']
        nodes.extend(pr['nodes'])
        pages += 1
        pi = pr['pageInfo']
        if pages % 25 == 0:
            print(f'  {o}/{n}: {len(nodes)} PRs...', flush=True)
        if not pi['hasNextPage']:
            break
        cursor = pi['endCursor']
    json.dump(nodes, open(out, 'w'))
    print(f'DONE {o}/{n}: {len(nodes)} PRs', flush=True)
