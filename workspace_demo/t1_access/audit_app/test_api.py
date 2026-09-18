"""Executable spec for the audit API, against the LOCAL rig only (python3 push.py --local, then
wrangler --cwd <this dir> pages dev --port 8797). Never point it at production: it writes marks.

    python3 test_api.py [base]      # default http://127.0.0.1:8797

It uses slot D's token and removes every mark it made, so the local rig ends as it started.
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8797"
assert "127.0.0.1" in BASE or "localhost" in BASE, "local rig only"
HERE = Path(__file__).resolve().parent
TOK = json.loads((HERE / "readers.local.json").read_text())["D"]["token"]
PLAN = json.loads((HERE / "assignment.json").read_text())["slots"]
passed = 0


def call(path, body=None):
    req = urllib.request.Request(BASE + path, method="POST" if body is not None else "GET",
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def check(cond, what):
    global passed
    assert cond, what
    passed += 1


s, st = call(f"/api/state?t={TOK}")
check(s == 200, "state 200")
ids = [i["id"] for i in st["items"]]
check(ids == PLAN["D"]["items"], "items in the dealt order, exactly slot D's")
check(sum(i["kind"] == "clue" for i in st["items"]) == 384, "384 clauses")
check(sum(i["kind"] == "prop" for i in st["items"]) == 25, "25 questions")
check(st["marks"] == {}, "no marks at the start")
clue = next(i for i in st["items"] if i["kind"] == "clue" and not i["allowed"])
prop = next(i for i in st["items"] if i["kind"] == "prop")
other = PLAN["A"]["items"][0]

check(call("/api/state?t=nope-nope-nope-nope")[0] == 404, "unknown token 404")
check(call("/api/state")[0] == 404, "no token 404")
check(call("/api/mark", {"t": TOK, "id": other, "m": {"t": "y", "nm": "n", "d": "n"}})[0] == 400,
      "an item dealt to another reader is refused")
check(call("/api/mark", {"t": TOK, "id": clue["id"], "m": {"t": "y"}})[0] == 400, "incomplete clause mark refused")
check(call("/api/mark", {"t": TOK, "id": clue["id"], "m": {"t": "x", "nm": "n", "d": "n"}})[0] == 400,
      "bad value refused")
check(call("/api/mark", {"t": TOK, "id": prop["id"], "m": {"ok": "y"}})[0] == 400, "incomplete question refused")

check(call("/api/mark", {"t": TOK, "id": clue["id"], "m": {"t": "?", "nm": "y", "d": "n", "c": "pun"}})[0] == 200,
      "a flagged clause saves")
check(call("/api/mark", {"t": TOK, "id": prop["id"], "m": {"ok": "y", "un": "n", "c": ""}})[0] == 200,
      "a flagged question saves")
m = call(f"/api/state?t={TOK}")[1]["marks"]
check(m[clue["id"]] == {"m": {"t": "?", "nm": "y", "d": "n", "c": "pun"}, "via": "row"}, "clause mark reads back")
check(m[prop["id"]]["m"] == {"ok": "y", "un": "n", "c": ""}, "question mark reads back")

card = [i["id"] for i in st["items"] if i.get("key") == clue["key"] and i["id"] != clue["id"]]
batch = [{"id": i, "m": {"t": "y", "nm": "n", "d": "n", "c": ""}} for i in card]
check(call("/api/bulk", {"t": TOK, "marks": batch + [{"id": other, "m": batch[0]["m"]}], "via": "card"})[0] == 400,
      "a batch with a foreign item is refused whole")
check(len(call(f"/api/state?t={TOK}")[1]["marks"]) == 2, "and nothing from it was written")
check(call("/api/bulk", {"t": TOK, "marks": batch, "via": "card"})[1].get("n") == len(card), "card batch saves")
m = call(f"/api/state?t={TOK}")[1]["marks"]
check(len(m) == 2 + len(card) and all(m[i]["via"] == "card" for i in card), "batch reads back as via card")

for i in [clue["id"], prop["id"]] + card:
    check(call("/api/mark", {"t": TOK, "id": i, "m": {}})[1].get("cleared"), f"un-mark {i}")
check(call(f"/api/state?t={TOK}")[1]["marks"] == {}, "the rig is clean again")
print(f"PASS {passed} checks")
