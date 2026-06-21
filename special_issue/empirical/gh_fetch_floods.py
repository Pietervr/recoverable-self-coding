import json
import os
import subprocess
import time

os.makedirs('/tmp/gh', exist_ok=True)
REPOS = [("public-apis", "public-apis"),
         ("MunGell", "awesome-for-beginners"),
         ("EddieHubCommunity", "BioDrop")]

Q = ('{ repository(owner:"%s",name:"%s"){ pullRequests(first:100%s, '
     'orderBy:{field:CREATED_AT,direction:ASC}){ '
     'nodes{ number createdAt mergedAt closedAt merged reviewDecision title } '
     'pageInfo{ hasNextPage endCursor } } } }')


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
        time.sleep(2 * (attempt + 1))
    raise RuntimeError("gql failed: " + last)


for o, n in REPOS:
    out = f'/tmp/gh/{o}__{n}.json'
    if os.path.exists(out):
        print(f'have {o}/{n}', flush=True)
        continue
    nodes, cursor, pages = [], None, 0
    while True:
        after = f', after: "{cursor}"' if cursor else ''
        pr = gql(Q % (o, n, after))['data']['repository']['pullRequests']
        nodes.extend(pr['nodes'])
        pages += 1
        if not pr['pageInfo']['hasNextPage']:
            break
        cursor = pr['pageInfo']['endCursor']
    json.dump(nodes, open(out, 'w'))
    print(f'DONE {o}/{n}: {len(nodes)} PRs', flush=True)
