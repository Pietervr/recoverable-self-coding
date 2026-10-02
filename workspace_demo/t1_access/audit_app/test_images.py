"""Executable spec for the image part (local rig only; cleans up after itself).

    wrangler --cwd . pages dev --port 8797 --ip 127.0.0.1    # after push.py --local with image_items.json
    python3 test_images.py
"""
import json
import secrets
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8797"
HERE = Path(__file__).resolve().parent
TOKEN = json.loads((HERE / "readers.local.json").read_text())["I"]["token"]
ITEMS = json.loads((HERE / "image_items.json").read_text())["items"]
ok = 0


def call(path, body=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req) as f:
            return f.status, (json.load(f) if "json" in f.headers.get("content-type", "") else f.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def check(cond, what):
    global ok
    if not cond:
        print("FAIL:", what)
        sys.exit(1)
    ok += 1


sid = secrets.token_urlsafe(18)
s, st = call(f"/api/state?t={TOKEN}&s={sid}")
check(s == 200 and [i["id"] for i in st["items"]] and len(st["items"]) == len(ITEMS), "state lists every image item")
check({i["id"] for i in st["items"]} == {i["id"] for i in ITEMS}, "exactly the image items, no clauses")
check(all(i["kind"] == "image" and i["definition"] and i["img"].startswith("/img/") for i in st["items"]), "item body")
s, png = call(st["items"][0]["img"])
check(s == 200 and png[:8] == b"\x89PNG\r\n\x1a\n", "the stimulus PNG is served")
import hashlib
check(hashlib.sha256(png).hexdigest() == st["items"][0]["png_sha256"], "served bytes are the manifest's canvas")
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None
try:
    with urllib.request.build_opener(NoRedirect).open(BASE + f"/i/{TOKEN}") as f:
        s, page = f.status, f.read()
except urllib.error.HTTPError as e:
    s, page = e.code, b""
check(s == 200 and b"Picture Check" in page, "/i/<token> serves the image page in place (no redirect: the token stays)")
iid = st["items"][0]["id"]
check(call("/api/mark", {"t": TOKEN, "s": sid, "id": iid, "m": {"ph": "y", "sense": "y"}})[0] == 400, "incomplete refused")
check(call("/api/mark", {"t": TOKEN, "s": sid, "id": iid, "m": {"ph": "y", "sense": "x", "name": "y"}})[0] == 400,
      "bad value refused")
check(call("/api/mark", {"t": TOKEN, "s": sid, "id": "c-crow-1", "m": {"ph": "y", "sense": "y", "name": "y"}})[0]
      == 400, "a clause id is not in the image part")
check(call("/api/mark", {"t": TOKEN, "s": sid, "id": iid, "m": {"ph": "y", "sense": "?", "name": "n", "c": "dim"}})
      == (200, {"ok": True}), "complete mark saved")
s, st2 = call(f"/api/state?t={TOKEN}&s={sid}")
check(st2["marks"][iid]["m"] == {"ph": "y", "sense": "?", "name": "n", "c": "dim"}, "mark read back")
s, other = call(f"/api/state?t={TOKEN}&s={secrets.token_urlsafe(18)}")
check(iid not in other["marks"], "another session does not see it")
check(call("/api/mark", {"t": TOKEN, "s": sid, "id": iid, "m": {}})[1].get("cleared"), "un-mark deletes (cleanup)")
check(call(f"/api/state?t=AAAAAAAAAAAAAAAAAAAAAA&s={sid}")[0] == 404, "unknown token refused")
print(f"{ok} checks passed")
