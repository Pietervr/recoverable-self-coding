"""AI image-reader qualification, revision 3: the sampling frame and the draw (standard library only, shared by the key
builder `ai_reader_key.py` and the image builder `ai_reader_qual.py`). Framework §8.2 reader rule; Codex RSC cf3e49e
and 7048bb8; R052 handoffs 7f25830e repair 3 and 742146ad group 2.

SOURCE PINS (group 2). The construction inputs are pinned by sha256 and checked before anything is read
(`check_sources`): both metadata tables and the norm description (hashes reproduced by Codex, RSC 7048bb8 section 2).
The WordNet corpus is pinned in the key builder.

FRAME INVARIANT (group 2), asserted on every retained frame row, never used to exclude or redraw
(`check_frame_invariant`): the image row of '<concept>.jpg' carries uniqueID == <concept> and the concept's Word; the
proportions are finite and in [0, 1]; N_ratings and N_correct are integers with 0 <= N_correct <= N_ratings and
N_ratings > 0; no concept id or root image row is duplicated, and none is missing. The release has 20 filename/uniqueID
mismatches among its 1,854 root rows; none survives the frame (they are homonym or anomaly exclusions), so the
invariant holds and the verified redraw stands. Mutation fixtures: tests `FrameInvariant`.

FRAME: the 1,854 THINGSplus concepts minus the 121 qualified development-pool concepts, minus homonyms ('Number of
word meanings in list' > 1), minus concepts without a parseable image norm, and minus SOURCE-NORM ANOMALIES - the
prospective, documented exclusion of repair 3, applied to every candidate by the source's own definitions
(image-level_description.txt: "recognizability score computed as N_correct / N_ratings"; "recognizability-close ...
also considering as correct if the correct label was part of the chosen label", so close >= exact):
  A1  |N_correct / N_ratings - recognizability| > 1e-6          (e.g. hot-water_bottle: 7/15 recorded as 0.294)
  A2  recognizability_close < recognizability                    (e.g. roadsweeper: close 0 below exact 0.385)
  A3  the image's display label (before any parenthesis) is not a name of the concept - its Word, its id or a
      WordNet synonym THINGS lists (e.g. hot-water_bottle's image row says 'hot tub': rows of alphabetical
      neighbours are interchanged in the release's image table)
A concept flagged by any rule leaves the frame; no image norm is repaired by hand. Measured 2 Oct 2026 before any
answer: 12 A1, 5 A2, 15 A3 over 1,677 candidates (the two anomalies Codex found, q047 and q140 of revision 1, are among
them). The draw is then made on the cleaned frame with revision 1's seed and procedure, so the 300 differ from
revision 1's; no answer existed for either.

DRAW: candidates sorted by concept id, shuffled by seed 20261007; tercile cuts at the 1/3 and 2/3 order statistics of
the frame's recognizability; the first 100 of each tercile in shuffled order. Easy = recognizability >= 0.8.
OPAQUE IDS: item = sha256("airq|<seed>|<concept>")[:10]; request (one per item and view) =
sha256("airq-req|<item>|<view>")[:12], so a colour and a grayscale request cannot be paired by name.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
THINGS = Path.home() / "things-plus"
SEED, N, EASY = 20261007, 300, 0.8
SOURCE_PINS = {"_concepts-metadata_things.tsv": "3f05b6b748d1e1b685e15130d2487bff63f86e1f4da94a2a5d9e7dec073a48eb",
               "_images-metadata_things.tsv": "fd5b17635f0f6528f58decaf5a089587593708862d4ee7a2a72cd8aa57ce013c",
               "image-level_description.txt": "e6e9bf63304978460b9556ab965a1cd462041c724dee6fa92a386d31ef81252d"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def concept_names(c: dict, uid: str) -> set[str]:
    syn = {s.strip().replace("_", " ").lower() for s in c["WordNet Synonyms"].split(",") if s.strip()}
    return {c["Word"].strip().lower(), uid.replace("_", " ").lower()} | syn


def check_sources(root: Path = THINGS) -> dict:
    got = {n: sha((root / n).read_bytes()) for n in SOURCE_PINS}
    bad = {n: h for n, h in got.items() if h != SOURCE_PINS[n]}
    if bad:
        raise SystemExit(f"refused: construction sources differ from the pinned hashes: {sorted(bad)}")
    return got


def read_tables(root: Path = THINGS) -> tuple[dict, dict]:
    """(concepts by uniqueID, root image rows by filename); a duplicate id or root image row is a refusal."""
    concepts, imgs = {}, {}
    with open(root / "_concepts-metadata_things.tsv", encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["uniqueID"] in concepts:
                raise SystemExit(f"refused: duplicate concept row {r['uniqueID']}")
            concepts[r["uniqueID"]] = r
    with open(root / "_images-metadata_things.tsv", encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if "/" in r["image"]:
                continue
            if r["image"] in imgs:
                raise SystemExit(f"refused: duplicate root image row {r['image']}")
            imgs[r["image"]] = r
    return concepts, imgs


def _finite01(v) -> bool:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return False
    return math.isfinite(f) and 0.0 <= f <= 1.0


def _count(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return int(f) if math.isfinite(f) and f.is_integer() else None


def check_frame_invariant(rows: list[dict], concepts: dict, imgs: dict) -> int:
    """Raise on the first violation among the retained rows; return how many rows were checked."""
    seen = set()
    for x in rows:
        uid, im, c = x["concept"], x["im"], x["c"]
        if uid in seen:
            raise SystemExit(f"invariant: concept {uid} retained twice")
        seen.add(uid)
        if uid not in concepts or imgs.get(f"{uid}.jpg") != im:
            raise SystemExit(f"invariant: {uid} has no concept row or no root image row of its own")
        if im["uniqueID"] != uid or im["image"] != f"{uid}.jpg":
            raise SystemExit(f"invariant: image row {im['image']} carries uniqueID {im['uniqueID']}, not {uid}")
        if im["Word"].strip().lower() != c["Word"].strip().lower():
            raise SystemExit(f"invariant: image row of {uid} carries Word {im['Word']!r}, concept says {c['Word']!r}")
        if not (_finite01(im["recognizability"]) and _finite01(im["recognizability_close"])):
            raise SystemExit(f"invariant: {uid} has a proportion that is not finite in [0, 1]")
        nr, nc = _count(im["recognizability_N-ratings"]), _count(im["recognizability_N-correct"])
        if nr is None or nc is None or not (nr > 0 and 0 <= nc <= nr):
            raise SystemExit(f"invariant: {uid} counts are not integers with 0 <= N_correct <= N_ratings, N_ratings > 0")
        if (x["n_ratings"], x["n_correct"]) != (nr, nc) or x["rec"] != float(im["recognizability"]):
            raise SystemExit(f"invariant: {uid} retained norm differs from its source row")
    return len(seen)


def frame(root: Path = THINGS) -> tuple[list[dict], dict]:
    check_sources(root)
    pool = json.loads((HERE / "dev_pool.json").read_text())
    exclude = {r["concept"] for f in pool["qualified"].values() for r in f}
    concepts, imgs = read_tables(root)
    out, excl = [], {"pool": [], "homonym": [], "no_norm": [], "A1": [], "A2": [], "A3": []}
    for uid, c in concepts.items():
        im = imgs.get(f"{uid}.jpg")
        if uid in exclude:
            excl["pool"].append(uid)
            continue
        if im is None or c["Number of word meanings in list"].strip() not in ("1", "1.0"):
            excl["homonym" if im is not None else "no_norm"].append(uid)
            continue
        try:
            rec, close = float(im["recognizability"]), float(im["recognizability_close"])
            nr, nc = float(im["recognizability_N-ratings"]), float(im["recognizability_N-correct"])
        except ValueError:
            excl["no_norm"].append(uid)
            continue
        flags = []
        if abs(nc / nr - rec) > 1e-6:
            flags.append("A1")
        if close < rec - 1e-9:
            flags.append("A2")
        if im["display_label"].split("(")[0].strip().lower() not in concept_names(c, uid):
            flags.append("A3")
        for f in flags:
            excl[f].append(uid)
        if flags:
            continue
        out.append({"concept": uid, "c": c, "im": im, "rec": rec, "close": close, "n_ratings": int(nr),
                    "n_correct": int(nc)})
    check_frame_invariant(out, concepts, imgs)
    return out, excl


def draw() -> dict:
    cand, excl = frame()
    n_frame = len(cand)
    cand.sort(key=lambda x: x["concept"])
    rng = random.Random(SEED)
    rng.shuffle(cand)
    cut = sorted(x["rec"] for x in cand)
    t1, t2 = cut[len(cut) // 3], cut[2 * len(cut) // 3]
    terc = {0: [], 1: [], 2: []}
    for x in cand:
        terc[0 if x["rec"] < t1 else 1 if x["rec"] < t2 else 2].append(x)
    chosen = terc[0][:N // 3] + terc[1][:N // 3] + terc[2][:N - 2 * (N // 3)]
    for x in chosen:
        x["stratum"] = 0 if x["rec"] < t1 else 1 if x["rec"] < t2 else 2
        x["item"] = sha(f"airq|{SEED}|{x['concept']}".encode())[:10]
        x["requests"] = {v: sha(f"airq-req|{x['item']}|{v}".encode())[:12] for v in ("colour", "gray")}
        x["easy"] = x["rec"] >= EASY
    assert len({x["item"] for x in chosen}) == N
    assert len({r for x in chosen for r in x["requests"].values()}) == 2 * N
    return {"chosen": chosen, "cuts": [t1, t2], "n_frame": n_frame,
            "stratum_frame_sizes": {k: len(v) for k, v in terc.items()},
            "exclusions": {k: sorted(v) for k, v in excl.items()},
            "exclusion_counts": {k: len(v) for k, v in excl.items()}}
