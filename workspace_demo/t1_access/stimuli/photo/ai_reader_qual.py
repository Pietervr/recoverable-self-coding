"""Qualifying an AI image reader against existing human norms, so the image and sense audit needs no new human
readers (owner, 2 Oct 2026: a human-gated audit would stall as the text audit did). PROPOSED to R052 and Codex;
nothing here calls a model.

WHY THIS WORKS FOR PICTURES. THINGSplus published, for every one of its 1,854 images, a human recognition norm:
about 15 to 17 raters each chose the object's name from the 1,854 THINGS labels (`recognizability` = share
correct; `recognizability_close` also accepts a label containing the right one). Those raters are the human
reference; the reader is qualified by agreeing with them on images OUTSIDE the development pool.

THE SET (`build`): N = 300 THINGSplus images drawn by a frozen seed from the 1,854 concepts minus the 121 qualified
pool concepts (so no image the instrument may ever use) and minus homonym concepts (`Number of word meanings in
list` > 1), stratified by human recognizability tercile. For each: the colour original (as the raters saw it) and
our grayscale clean canvas (dose pipeline, a = 1, as the audit shows it), written to captures/ai_reader_qual/
(git-ignored), with hashes, the human norm and the accepted-answer set recorded in ai_reader_qual_set.json.

THE READER TASK (`prompt`): per image, one word naming the main object, or "unclear". The reader never sees the
concept, the THINGS label list, or any other image's answer; images are shown one per request.

SCORING (`score <answers.csv>`): an answer is correct when, lower-cased and singularised, it equals the concept
word, its THINGS display label, a WordNet synonym listed by THINGS, or (the 'close' score, as THINGS'
recognizability-close) contains the concept word or is contained in a multi-word concept name. Reported:
reader accuracy on colour and on grayscale, human mean recognizability on the same images, per-tercile rows, and
the item list where reader and humans disagree.

PROPOSED THRESHOLD (for Codex's review, fixed before any answer exists):
  Q1  colour accuracy (close)  >=  the mean human recognizability-close on the same 300 images
      - the reader names them at least as well as the average rater;
  Q2  on images the raters found easy (recognizability >= 0.8), colour accuracy >= 0.90;
  Q3  grayscale accuracy is reported against colour accuracy (no human grayscale norm exists); in the audit, an
      item where the reader fails on grayscale but humans succeed in colour goes to the owner.
A reader that fails Q1 or Q2 is not qualified, and the audit falls back to the owner (one sitting, about 15 minutes
for 64 pictures).

    .venv-image/bin/python stimuli/photo/ai_reader_qual.py build
    .venv-image/bin/python stimuli/photo/ai_reader_qual.py score answers.csv     # columns: id, view, answer
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dose  # noqa: E402

THINGS = Path.home() / "things-plus"
OUT = HERE.parents[1] / "captures" / "ai_reader_qual"
SEED, N = 20261007, 300
PROMPT = ("Look at this picture. What is the main object in it? Answer with ONE English word (a noun), "
          "or the word 'unclear' if you cannot tell. Answer with the word only.")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def norm(w: str) -> str:
    w = w.strip().lower().strip(".,;:!\"'")
    for suf, rep in (("ies", "y"), ("ses", "s"), ("es", "e"), ("s", "")):
        if w.endswith(suf) and len(w) > 3 and not w.endswith("ss"):
            return w[: -len(suf)] + rep
    return w


def build() -> int:
    pool = json.loads((HERE / "dev_pool.json").read_text())
    exclude = {r["concept"] for f in pool["qualified"].values() for r in f}
    concepts = {r["uniqueID"]: r for r in csv.DictReader(open(THINGS / "_concepts-metadata_things.tsv",
                                                             encoding="utf-8", newline=""), delimiter="\t")}
    imgs = {r["image"]: r for r in csv.DictReader(open(THINGS / "_images-metadata_things.tsv", encoding="utf-8",
                                                       newline=""), delimiter="\t") if "/" not in r["image"]}
    cand = []
    for uid, c in concepts.items():
        im = imgs.get(f"{uid}.jpg")
        if uid in exclude or im is None or c["Number of word meanings in list"].strip() not in ("1", "1.0"):
            continue
        try:
            rec = float(im["recognizability"])
            close = float(im["recognizability_close"])
        except ValueError:
            continue
        cand.append((uid, c, im, rec, close))
    cand.sort(key=lambda x: x[0])
    rng = random.Random(SEED)
    rng.shuffle(cand)
    cut = sorted(x[3] for x in cand)
    t1, t2 = cut[len(cut) // 3], cut[2 * len(cut) // 3]
    terc = {0: [], 1: [], 2: []}
    for x in cand:
        terc[0 if x[3] < t1 else 1 if x[3] < t2 else 2].append(x)
    chosen = terc[0][:N // 3] + terc[1][:N // 3] + terc[2][:N - 2 * (N // 3)]
    OUT.mkdir(parents=True, exist_ok=True)
    items = []
    for i, (uid, c, im, rec, close) in enumerate(chosen):
        src = THINGS / "cc0" / "object_images_CC0" / f"{uid}.jpg"
        raw = src.read_bytes()
        canvas, _ = dose.load_canvas(src)
        S = dose.signal(dose.luma(canvas))
        rgb8, _ = dose.quantise(dose.mix(S, S * 0.0, 1.0))
        png = dose.to_png(rgb8)
        qid = f"q{i:03d}"
        (OUT / f"{qid}_colour.jpg").write_bytes(raw)
        (OUT / f"{qid}_gray.png").write_bytes(png)
        syn = [s.strip().replace("_", " ") for s in c["WordNet Synonyms"].split(",") if s.strip()]
        accept = sorted({norm(c["Word"]), norm(im["display_label"].split("(")[0]), *(norm(s) for s in syn)})
        items.append({"id": qid, "concept": uid, "word": c["Word"], "display_label": im["display_label"],
                      "accept": accept, "recognizability": rec, "recognizability_close": close,
                      "n_ratings": int(float(im["recognizability_N-ratings"])),
                      "most_common_label": im["recognizability_most-common-label"],
                      "tercile": 0 if rec < t1 else 1 if rec < t2 else 2,
                      "colour_sha256": sha(raw), "gray_sha256": sha(png)})
    meta = {"seed": SEED, "n": len(items), "excluded": "the 121 qualified pool concepts and homonym concepts",
            "tercile_cuts": [t1, t2], "prompt": PROMPT, "prompt_sha256": sha(PROMPT.encode()),
            "human_mean_recognizability": float(np.mean([x["recognizability"] for x in items])),
            "human_mean_recognizability_close": float(np.mean([x["recognizability_close"] for x in items])),
            "items": items}
    (HERE / "ai_reader_qual_set.json").write_text(json.dumps(meta, indent=1) + "\n")
    print(len(items), "images; human mean recognizability", round(meta["human_mean_recognizability"], 3),
          "close", round(meta["human_mean_recognizability_close"], 3), "tercile cuts", [round(t1, 3), round(t2, 3)])
    return 0


def score(path: str) -> int:
    meta = json.loads((HERE / "ai_reader_qual_set.json").read_text())
    by = {x["id"]: x for x in meta["items"]}
    ans = {(r["id"], r["view"]): r["answer"] for r in csv.DictReader(open(path, newline=""))}

    def correct(x, a, close):
        w = norm(a)
        if w in x["accept"]:
            return True
        return close and any(k in w or (w and w in k and " " in k) for k in x["accept"])

    out = {}
    for view in ("colour", "gray"):
        got = [x for x in meta["items"] if (x["id"], view) in ans]
        if not got:
            continue
        acc = float(np.mean([correct(x, ans[(x["id"], view)], False) for x in got]))
        accc = float(np.mean([correct(x, ans[(x["id"], view)], True) for x in got]))
        easy = [x for x in got if x["recognizability"] >= 0.8]
        out[view] = {"n": len(got), "accuracy": acc, "accuracy_close": accc,
                     "easy_n": len(easy), "easy_accuracy_close": float(np.mean(
                         [correct(x, ans[(x["id"], view)], True) for x in easy])) if easy else None,
                     "by_tercile": {t: float(np.mean([correct(x, ans[(x["id"], view)], True) for x in got
                                                      if x["tercile"] == t])) for t in (0, 1, 2)}}
    h = meta["human_mean_recognizability_close"]
    c = out.get("colour", {})
    out["threshold"] = {"Q1_colour_close_vs_human": [c.get("accuracy_close"), h],
                        "Q1_pass": c.get("accuracy_close") is not None and c["accuracy_close"] >= h,
                        "Q2_easy": c.get("easy_accuracy_close"),
                        "Q2_pass": c.get("easy_accuracy_close") is not None and c["easy_accuracy_close"] >= 0.90}
    out["qualified"] = out["threshold"]["Q1_pass"] and out["threshold"]["Q2_pass"]
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    sys.exit(build() if cmd == "build" else score(sys.argv[2]))
