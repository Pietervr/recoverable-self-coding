"""AI image-reader qualification, revision 2: the sampling frame and the draw (standard library only, shared by the key
builder `ai_reader_key.py` and the image builder `ai_reader_qual.py`). Framework §8.2 reader rule; Codex RSC cf3e49e;
R052 handoff 7f25830e repair 3.

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
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
THINGS = Path.home() / "things-plus"
SEED, N, EASY = 20261007, 300, 0.8


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def concept_names(c: dict, uid: str) -> set[str]:
    syn = {s.strip().replace("_", " ").lower() for s in c["WordNet Synonyms"].split(",") if s.strip()}
    return {c["Word"].strip().lower(), uid.replace("_", " ").lower()} | syn


def frame() -> tuple[list[dict], dict]:
    pool = json.loads((HERE / "dev_pool.json").read_text())
    exclude = {r["concept"] for f in pool["qualified"].values() for r in f}
    concepts = {r["uniqueID"]: r for r in csv.DictReader(open(THINGS / "_concepts-metadata_things.tsv",
                                                             encoding="utf-8", newline=""), delimiter="\t")}
    imgs = {r["image"]: r for r in csv.DictReader(open(THINGS / "_images-metadata_things.tsv", encoding="utf-8",
                                                       newline=""), delimiter="\t") if "/" not in r["image"]}
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
