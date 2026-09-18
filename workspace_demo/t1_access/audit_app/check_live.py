"""Read-only check of a deployed audit site: every reader's link loads their dealt items in order, a bad
token is refused, and /r/<token> serves the page. Writes nothing.

    python3 check_live.py [base]    # default https://audit.raconteur-road.com
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://audit.raconteur-road.com"
HERE = Path(__file__).resolve().parent
READERS = json.loads((HERE / "readers.local.json").read_text())
PLAN = json.loads((HERE / "assignment.json").read_text())["slots"]
UA = {"user-agent": "audit-check/1"}


def get(path):
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE + path, headers=UA)) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


for slot, rd in sorted(READERS.items()):
    s, body = get(f"/api/state?t={rd['token']}")
    st = json.loads(body)
    ok = s == 200 and [i["id"] for i in st["items"]] == PLAN[slot]["items"]
    print(f"{slot}: {s} {st.get('name')!r}, {len(st.get('items', []))} items in dealt order: {ok}, "
          f"{len(st.get('marks', {}))} marks saved")
    assert ok
s, _ = get("/api/state?t=not-a-real-token-at-all")
print("bad token:", s)
assert s == 404
s, page = get("/r/" + READERS["A"]["token"])
print("page:", s, b"<title>Clue Check</title>" in page)
assert s == 200 and b"<title>Clue Check</title>" in page
print("LIVE OK")
