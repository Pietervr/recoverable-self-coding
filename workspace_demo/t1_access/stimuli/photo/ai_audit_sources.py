"""Image audit, step 1: fetch and pin every second-view candidate's SOURCE FILE (no model, no reader).

Framework §8.2; R052 rulings of 4 October 2026 (handoff 08f09009). Every candidate of the 32 lists in
second_view_candidates.json is fetched ONCE, here, before the audit package is reviewed, so that no later round of the
audit moves a bound input: the bytes go under captures/second_view_sources/ (git-ignored, like every capture) and are
pinned in ai_audit_sources.json (committed). `check` re-hashes every stored file against its pin; the audit's set
builder and the P = 2 manifest open only pinned bytes.

THE SOURCE FILE IS COMMONS' 1280-PIXEL STANDARD RENDERING, NOT THE ORIGINAL (4 October 2026). Bulk requests for the
originals (about 11 MB each) were refused by the Wikimedia upload servers with HTTP 429 and the instruction to use
thumbnails at the standard steps (20 ... 960, 1280, 1920, 3840 px; mediawiki.org "Common thumbnail sizes"). The
candidates are requested through the imageinfo API with iiurlwidth = 1280 (a standard step); a file narrower than that
is served at its own width. 1280 pixels is more than three times the 384-pixel canvas. Each pin records the rendering's
URL, width, height, bytes and sha256 AND the original's URL, size and Commons SHA-1 (the API's `sha1` of the original),
so the derivative stays tied to the file whose licence the per-image check reads. The resize from the original is
Commons' scaler, not ours; the canvas pipeline (§8.3) starts from the pinned rendering.

Rate: one API batch of up to 50 titles, then one file every 5 s; an HTTP 429 waits (60, 120, 300, 600 s) and retries;
a rate limit that outlasts the waits stops the run with nothing recorded (a re-run resumes); only a permanent
refusal (404, a missing imageinfo) records the candidate as unavailable.

Transmission scope (ruling 1e): an unaccepted candidate goes to the reader only as a restricted private use under its
file-level CC0/PD statement (recorded per candidate); the per-image check of framework §8.2 gates capture of the
ACCEPTED view.

    python3 stimuli/photo/ai_audit_sources.py fetch     # network: the Commons API and upload servers only
    python3 stimuli/photo/ai_audit_sources.py check
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDS = HERE / "second_view_candidates.json"
PINS = HERE / "ai_audit_sources.json"
STORE = HERE.parents[1] / "captures" / "second_view_sources"
API = "https://commons.wikimedia.org/w/api.php"
UA = "R084-T1-research/1.0 (Recoverable-Self-Coding; contact via repository owner)"
WIDTH = 1280
EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/tiff": ".tif", "image/gif": ".gif"}
WAITS = (60, 120, 300, 600)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def cand_id(concept: str, title: str) -> str:
    """Stable opaque id of a candidate (it names neither the concept nor the file in any delivered path)."""
    return sha(f"audit-cand|{concept}|{title}".encode())[:12]


def get(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for wait in WAITS + (None,):
        try:
            with urllib.request.urlopen(req, timeout=120) as f:
                return f.read(), f.headers.get("Content-Type", "").split(";")[0].strip()
        except urllib.error.HTTPError as e:
            if e.code != 429 or wait is None:
                raise
            print(f"  429: waiting {wait} s", flush=True)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def imageinfo(titles: list[str]) -> dict:
    q = {"action": "query", "format": "json", "titles": "|".join(titles), "prop": "imageinfo",
         "iiprop": "url|size|sha1|mime", "iiurlwidth": WIDTH}
    data, _ = get(API + "?" + urllib.parse.urlencode(q))
    d = json.loads(data)
    norm = {n["to"]: n["from"] for n in d["query"].get("normalized", [])}
    out = {}
    for p in d["query"]["pages"].values():
        ii = (p.get("imageinfo") or [None])[0]
        out[norm.get(p["title"], p["title"])] = ii
    return out


def fetch() -> int:
    cands = json.loads(CANDS.read_text())
    pins = json.loads(PINS.read_text()) if PINS.exists() else {
        "note": __doc__.split("\n\n")[0], "rendering_width_requested": WIDTH, "candidates_sha256": None, "items": {}}
    STORE.mkdir(parents=True, exist_ok=True)
    todo = [(k, rank, c) for k, v in cands["concepts"].items() for rank, c in enumerate(v["candidates"], 1)
            if not (pins["items"].get(cand_id(k, c["title"])) or {}).get("sha256")]
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        info = imageinfo([c["title"] for _, _, c in batch])
        for concept, rank, c in batch:
            cid = cand_id(concept, c["title"])
            ii = info.get(c["title"])
            rec = {"concept": concept, "rank": rank, "title": c["title"], "page_url": c["page_url"],
                   "licence_statement": c["basis"], "licence_short": c["licence"],
                   "original": {"url": (ii or {}).get("url"), "width": (ii or {}).get("width"),
                                "height": (ii or {}).get("height"), "commons_sha1": (ii or {}).get("sha1"),
                                "mime": (ii or {}).get("mime")}}
            url = (ii or {}).get("thumburl") or (ii or {}).get("url")
            try:
                if not ii or not url:
                    raise RuntimeError("no imageinfo for the title (deleted or renamed)")
                data, ctype = get(url)
                name = cid + EXT.get(ctype, ".bin")
                (STORE / name).write_bytes(data)
                rec.update(rendering_url=url, rendering_width=ii.get("thumbwidth") or ii.get("width"),
                           rendering_height=ii.get("thumbheight") or ii.get("height"), file=name, bytes=len(data),
                           sha256=sha(data), content_type=ctype,
                           fetched=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
            except (urllib.error.HTTPError, RuntimeError) as e:
                if isinstance(e, urllib.error.HTTPError) and e.code == 429:
                    raise SystemExit("stopped: the rate limit outlasted the waits; nothing recorded for this "
                                     "candidate - re-run fetch later (pinned candidates are kept)")
                rec.update(file=None, bytes=None, sha256=None, content_type=None,
                           unavailable=f"{type(e).__name__}: {e}",
                           fetched=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
            pins["items"][cid] = rec
            print(f"{concept:<11} {rank} {cid} {rec.get('bytes')} {rec.get('rendering_width')}x"
                  f"{rec.get('rendering_height')} {rec.get('unavailable', '')}", flush=True)
            PINS.write_text(json.dumps(pins, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
            time.sleep(5.0)
    pins["candidates_sha256"] = sha(CANDS.read_bytes())
    PINS.write_text(json.dumps(pins, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
    return check()


def load_pinned(cid: str) -> bytes:
    """The pinned source file's bytes, refused unless they hash to the pin."""
    rec = json.loads(PINS.read_text())["items"][cid]
    if not rec.get("sha256"):
        raise SystemExit(f"refused: candidate {cid} has no pinned source ({rec.get('unavailable')})")
    data = (STORE / rec["file"]).read_bytes()
    if sha(data) != rec["sha256"]:
        raise SystemExit(f"refused: the stored source of {cid} differs from its pin")
    return data


def check() -> int:
    pins = json.loads(PINS.read_text())
    if pins["candidates_sha256"] != sha(CANDS.read_bytes()):
        raise SystemExit("refused: second_view_candidates.json changed after the sources were pinned")
    cands = json.loads(CANDS.read_text())
    want = {cand_id(k, c["title"]) for k, v in cands["concepts"].items() for c in v["candidates"]}
    if set(pins["items"]) != want:
        raise SystemExit("refused: the pins do not cover exactly the candidate lists")
    bad = [cid for cid, r in pins["items"].items() if r.get("sha256") and
           sha((STORE / r["file"]).read_bytes()) != r["sha256"]]
    if bad:
        raise SystemExit(f"refused: stored sources differ from their pins: {bad}")
    missing = sorted((r["concept"], r["rank"], r["unavailable"]) for r in pins["items"].values()
                     if not r.get("sha256"))
    print(f"{len(pins['items'])} candidates pinned; unavailable: {missing or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit({"fetch": fetch, "check": check}[sys.argv[1]]())
