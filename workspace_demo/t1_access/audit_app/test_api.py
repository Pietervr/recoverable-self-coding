"""Executable spec for the audit API, against the LOCAL rig only (python3 push.py --local, then
wrangler --cwd <this dir> pages dev --port 8797 --ip 127.0.0.1). Never point it at production: it writes.

    python3 test_api.py [base]      # default http://127.0.0.1:8797

It uses part D's link with three test sessions and removes every answer it made, so the rig ends as it began.
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
S1, S2, S3 = "test-session-one-0001", "test-session-two-0002", "test-session-three-003"
FINE = {"t": "y", "nm": "n", "d": "n", "c": ""}
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


def state(sid):
    return call(f"/api/state?t={TOK}&s={sid}")


def check(cond, what):
    global passed
    assert cond, what
    passed += 1


s, st = state(S1)
check(s == 200, "state 200")
ids = [i["id"] for i in st["items"]]
check(sorted(ids) == sorted(PLAN["D"]["items"]), "exactly part D's items")
check(sum(i["kind"] == "clue" for i in st["items"]) == 384, "384 clauses")
check(sum(i["kind"] == "prop" for i in st["items"]) == 25, "25 questions")
check(all(i["kind"] == "prop" for i in st["items"][-25:]), "the questions come last")
keys = []
for i in st["items"]:
    k = i.get("key", "questions")
    if not keys or keys[-1] != k:
        keys.append(k)
check(len(keys) == len(set(keys)) == 33, "each card's items are contiguous (32 cards + questions)")
check(st["marks"] == {}, "a new session starts empty")
check(state("short")[0] == 400, "a malformed session is refused")
check(call(f"/api/state?t={TOK}")[0] == 400, "no session is refused")
check(call("/api/state?t=nope-nope-nope-nope&s=" + S1)[0] == 404, "unknown token 404")

first = keys[0]
card = [i["id"] for i in st["items"] if i.get("key") == first]
clue = next(i for i in st["items"] if i.get("key") == first and not i["allowed"])
prop = next(i for i in st["items"] if i["kind"] == "prop")
other = PLAN["A"]["items"][0]

s, e = call("/api/mark", {"t": TOK, "id": clue["id"], "m": FINE})
check(s == 400 and "reload" in e.get("error", ""), "a save without a session asks the page to reload")
check(call("/api/mark", {"t": TOK, "s": S1, "id": other, "m": FINE})[0] == 400, "another part's item is refused")
check(call("/api/mark", {"t": TOK, "s": S1, "id": clue["id"], "m": {"t": "y"}})[0] == 400, "incomplete mark refused")
check(call("/api/mark", {"t": TOK, "s": S1, "id": prop["id"], "m": {"ok": "y"}})[0] == 400, "incomplete question refused")

check(call("/api/mark", {"t": TOK, "s": S1, "id": clue["id"],
                         "m": {"t": "?", "nm": "y", "d": "n", "c": "pun"}})[0] == 200, "session 1 flags a clause")
check(call("/api/mark", {"t": TOK, "s": S2, "id": clue["id"], "m": FINE})[0] == 200, "session 2 passes the same clause")
m1, m2 = state(S1)[1]["marks"], state(S2)[1]["marks"]
check(m1[clue["id"]]["m"] == {"t": "?", "nm": "y", "d": "n", "c": "pun"}, "session 1 keeps its own answer")
check(m2[clue["id"]]["m"] == FINE, "session 2 keeps its own answer")
check(len(m1) == 1 and len(m2) == 1, "neither session sees the other's answers")

batch = [{"id": i, "m": FINE} for i in card if i != clue["id"]]
check(call("/api/bulk", {"t": TOK, "s": S1, "marks": batch + [{"id": other, "m": FINE}], "via": "card"})[0] == 400,
      "a batch with a foreign item is refused whole")
check(len(state(S1)[1]["marks"]) == 1, "and nothing from it was written")
check(call("/api/bulk", {"t": TOK, "marks": batch, "via": "card"})[0] == 400, "a batch without a session is refused")
check(call("/api/bulk", {"t": TOK, "s": S1, "marks": batch, "via": "card"})[1].get("n") == len(batch), "card batch saves")
m1 = state(S1)[1]["marks"]
check(len(m1) == len(card) and all(m1[i]["via"] == "card" for i in card if i != clue["id"]), "batch reads back")

# The card two sessions have touched must no longer come first for a third visitor.
keys3 = []
for i in state(S3)[1]["items"]:
    k = i.get("key", "questions")
    if not keys3 or keys3[-1] != k:
        keys3.append(k)
check(keys3.index(first) > 0 and keys3[-1] == "questions", "a read card moves back for a new visitor")
check(keys3.index(first) >= 31, "and behind every unread card")

for sid, ids_ in [(S1, card), (S2, [clue["id"]])]:
    for i in ids_:
        check(call("/api/mark", {"t": TOK, "s": sid, "id": i, "m": {}})[1].get("cleared"), f"un-mark {sid} {i}")
check(state(S1)[1]["marks"] == {} and state(S2)[1]["marks"] == {}, "the rig is clean again")
print(f"PASS {passed} checks")
