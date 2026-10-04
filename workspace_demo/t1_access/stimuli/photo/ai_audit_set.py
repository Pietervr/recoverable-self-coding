"""Image audit, step 2: the frozen request SET and KEY of each audit round (no model, no reader).

Framework §8.2, audit_app/IMAGE_AUDIT_FREEZE.md, AI_AUDIT_JOB.md; R052 rulings of 4 October 2026 (handoff 08f09009).

WHAT IS ASKED. Every item is the clean grayscale canvas of framework §8.3 (dose pipeline, a = 1): a primary view's
canvas is byte-identical to manifest_dev.json's clean canvas (asserted); a candidate's is computed by the same `dose`
functions from its pinned original (ai_audit_sources.load_pinned). One fresh, stateless, image-only request per
question, never carrying a prior answer:
  name        the qualification's prompt, word for word (ai_reader_qual_set.json "prompt")      every item
  photograph  PROMPTS["photograph"]                                                              every item
  sense       PROMPTS["sense"] with the concept's name and THINGS definition                     every item
  distinct    PROMPTS["distinct"] on ONE side-by-side image: the primary's canvas on the left, the candidate's on
              the right, a 16-pixel 0.5-grey gap                                                  every candidate
A distinct-view question is the only request that shows two photographs, and it is ordered after both photographs'
blind names (within each block - round 1's pilot block, then the other 24 - every name precedes every other question
of that block; requests are stateless).

ORDER. Round 1: the PILOT block - the Stage A eight's primaries and their rank-1 candidates (names, then photograph,
sense and distinct questions) - then the same for the other 24 concepts. Within a block, by family then concept.
Round k >= 2 (`derive(k, chained)`): only the concepts whose audited candidates all failed in rounds < k and that still
have an unaudited candidate with a pinned source: their next candidate by rank, the four questions, names first. The
ADMITTED predecessor chain (ai_audit_exec.Chain: committed, re-admitted, re-scored predecessors) decides this
mechanically; derivation never reads a live score file; nobody chooses. A round is an integer 1..8 (require_round).

IDS. Item ids are opaque: a primary keeps the freeze's `sha256("audit-img|<concept>|v1")[:12]`, a candidate its
`ai_audit_sources.cand_id`, a distinct pair `sha256("audit-pair|<primary>|<candidate>")[:12]`; request ids hash the
round, item and question. Image files are named by their own sha256; neither a path nor an id names the concept. The
reader-side SET carries no concept, family, title or label (only the sense prompt names the concept, by design); the
KEY (orchestrator only, like the qualification's) maps items to concepts, roles and candidates.

    .venv-image/bin/python stimuli/photo/ai_audit_set.py build 1      # writes ai_audit_set_r1.json, ai_audit_key_r1.json
    .venv-image/bin/python stimuli/photo/ai_audit_set.py check 1      # re-derives and compares (what the executor does)
    (round k >= 2: build/check first admit the authenticated chain 1..k-1)
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ai_audit_sources as SRC  # noqa: E402
import dose  # noqa: E402

ITEMS = HERE.parents[1] / "captures" / "ai_audit_items"
THINGS = Path.home() / "things-plus"
DEFS = THINGS / "_concepts-metadata_things.tsv"
IMAGES_TSV = THINGS / "_images-metadata_things.tsv"
QUAL_SET = HERE / "ai_reader_qual_set.json"
GAP = 16
PROMPTS = {
    "photograph": "Is this picture a photograph? Answer with one word: yes, no or unsure.",
    "sense": 'Does this picture show "{name}" in this sense: "{definition}"? Answer with one word: yes, no or unsure.',
    "distinct": "These are two pictures side by side. Is the right picture a different photograph from the left one, "
                "not a crop or flip of it? Answer with one word: yes, no or unsure.",
}
QUESTION_ORDER = ("name", "photograph", "sense", "distinct")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def set_path(k: int) -> Path:
    return HERE / f"ai_audit_set_r{k}.json"


def key_path(k: int) -> Path:
    return HERE / f"ai_audit_key_r{k}.json"


def score_path(k: int) -> Path:
    return HERE / f"ai_audit_score_r{k}.json"


def definitions() -> dict:
    with open(DEFS, newline="", encoding="utf-8") as f:
        return {r["uniqueID"]: r["Definition (from WordNet, Google, or Wikipedia)"].strip()
                for r in csv.DictReader(f, delimiter="\t")}


def _canvas_rgb8(path_or_bytes) -> np.ndarray:
    if isinstance(path_or_bytes, (bytes, bytearray)):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".img") as t:
            t.write(path_or_bytes)
            t.flush()
            canvas, _ = dose.load_canvas(Path(t.name))
    else:
        canvas, _ = dose.load_canvas(Path(path_or_bytes))
    S = dose.signal(dose.luma(canvas))
    rgb8, _ = dose.quantise(dose.mix(S, S * 0.0, 1.0))
    return rgb8


def primary_png(role: dict, manifest: dict) -> bytes:
    png = dose.to_png(_canvas_rgb8(THINGS / "cc0" / "object_images_CC0" / role["thingsplus_image"]))
    if sha(png) != manifest[role["concept"]]["clean_canvas"]["png_sha256"]:
        raise SystemExit(f"refused: {role['concept']}: the primary canvas is not the manifest's clean canvas")
    return png


def candidate_png(cid: str) -> bytes:
    return dose.to_png(_canvas_rgb8(SRC.load_pinned(cid)))


def pair_png(primary: bytes, cand: bytes) -> bytes:
    from PIL import Image
    a = np.asarray(Image.open(io.BytesIO(primary)).convert("RGB"))
    b = np.asarray(Image.open(io.BytesIO(cand)).convert("RGB"))
    gap = np.full((a.shape[0], GAP, 3), 128, dtype=np.uint8)
    return dose.to_png(np.concatenate([a, gap, b], axis=1))


def _store(png: bytes, write: bool) -> tuple[str, str]:
    h = sha(png)
    name = f"{h[:16]}.png"
    if write:
        ITEMS.mkdir(parents=True, exist_ok=True)
        p = ITEMS / name
        if not p.exists() or sha(p.read_bytes()) != h:
            p.write_bytes(png)
    return name, h


def prior_outcomes(chained: dict) -> dict:
    """For each concept, the candidate ranks audited in rounds < k and whether a second view was selected - read ONLY
    from the admitted chain's authenticated predecessor scores (ai_audit_exec.Chain), never from live files."""
    out = {}
    for j in sorted(chained["priors"]):
        for concept, sv in chained["priors"][j]["second_views"].items():
            o = out.setdefault(concept, {"ranks": set(), "selected": None})
            o["ranks"] |= set(sv["audited_ranks"])
            if sv["status"] == "selected":
                o["selected"] = sv["candidate"]
    return out


def human_norms() -> dict:
    """THINGSplus per-image recognition norm of each primary (root image rows of the image table)."""
    with open(IMAGES_TSV, newline="", encoding="utf-8") as f:
        return {r["image"]: {"recognizability": float(r["recognizability"]),
                             "n_ratings": int(float(r["recognizability_N-ratings"])),
                             "n_correct": int(float(r["recognizability_N-correct"]))}
                for r in csv.DictReader(f, delimiter="\t") if "/" not in r["image"]}


def derive(k: int, chained: dict | None = None, write: bool = False) -> tuple[bytes, bytes]:
    """The round-k set and key as bytes, from committed inputs and (k >= 2) the admitted chain only."""
    import ai_audit_exec as A
    k = A.require_round(k)
    if k > 1 and (not chained or chained.get("round") != k):
        raise SystemExit(f"refused: round {k} is derived only from its admitted predecessor chain")
    pool = json.loads((HERE / "dev_pool.json").read_text())
    manifest = {r["concept"]: r for r in json.loads((HERE / "manifest_dev.json").read_text())["records"]}
    cands = json.loads(SRC.CANDS.read_text())
    pins = json.loads(SRC.PINS.read_text())
    if pins["candidates_sha256"] != sha(SRC.CANDS.read_bytes()):
        raise SystemExit("refused: second_view_candidates.json changed after the originals were pinned")
    qual = json.loads(QUAL_SET.read_text())
    defs = definitions()
    roles = {r["concept"]: r for r in pool["roles"]}
    prior = prior_outcomes(chained) if k > 1 else {}
    norms = human_norms()

    def next_rank(concept: str) -> int | None:
        done = prior.get(concept, {}).get("ranks", set())
        for rank, c in enumerate(cands["concepts"][concept]["candidates"], 1):
            if rank in done:
                continue
            if pins["items"][SRC.cand_id(concept, c["title"])].get("sha256"):
                return rank
        return None

    blocks = [[], []]                                  # [pilot (Stage A eight), the other 24]
    for concept, r in sorted(roles.items(), key=lambda kv: (kv[1]["family"], kv[0])):
        if k > 1 and (concept not in prior or prior[concept]["selected"]):
            continue
        rank = next_rank(concept)
        if k > 1 and rank is None:
            continue
        blocks[0 if r["stage_a_primary_view"] else 1].append((concept, rank))
    requests, order, key_items = [], [], {}

    def add(item: str, view: str, q: str, png: bytes, prompt: str) -> str:
        name, h = _store(png, write)
        rq = sha(f"audit-req|r{k}|{item}|{q}".encode())[:12]
        requests.append({"request": rq, "item": item, "view": view, "question": q, "file": name, "sha256": h,
                         "bytes": len(png), "prompt": prompt})
        return rq

    for block in blocks:
        per_q = {q: [] for q in QUESTION_ORDER}
        for concept, rank in block:
            r = roles[concept]
            sense = PROMPTS["sense"].format(name=r["name"].replace("_", " "), definition=defs[concept])
            prim = primary_png(r, manifest)
            pid = sha(f"audit-img|{concept}|v1".encode())[:12]
            if k == 1:
                key_items[pid] = {"concept": concept, "kind": "primary", "family": r["family"], "role": r["role"],
                                  "stage_a_primary_view": r["stage_a_primary_view"], "synset": r["synset"],
                                  "definition": defs[concept], "png_sha256": sha(prim),
                                  "human": norms[r["thingsplus_image"]]}
                per_q["name"].append(add(pid, "primary", "name", prim, qual["prompt"]))
                per_q["photograph"].append(add(pid, "primary", "photograph", prim, PROMPTS["photograph"]))
                per_q["sense"].append(add(pid, "primary", "sense", prim, sense))
            if rank is None:
                continue
            c = cands["concepts"][concept]["candidates"][rank - 1]
            cid = SRC.cand_id(concept, c["title"])
            cand = candidate_png(cid)
            pair = pair_png(prim, cand)
            prid = sha(f"audit-pair|{pid}|{cid}".encode())[:12]
            key_items[cid] = {"concept": concept, "kind": "candidate", "rank": rank, "title": c["title"],
                              "page_url": c["page_url"], "licence_statement": c["basis"], "family": r["family"],
                              "role": r["role"], "synset": r["synset"], "definition": defs[concept],
                              "source_sha256": pins["items"][cid]["sha256"],
                              "commons_original_sha1": pins["items"][cid]["original"]["commons_sha1"],
                              "png_sha256": sha(cand),
                              "pair": prid}
            key_items[prid] = {"concept": concept, "kind": "pair", "primary": pid, "candidate": cid,
                               "png_sha256": sha(pair)}
            per_q["name"].append(add(cid, "second", "name", cand, qual["prompt"]))
            per_q["photograph"].append(add(cid, "second", "photograph", cand, PROMPTS["photograph"]))
            per_q["sense"].append(add(cid, "second", "sense", cand, sense))
            per_q["distinct"].append(add(prid, "pair", "distinct", pair, PROMPTS["distinct"]))
        for q in QUESTION_ORDER:
            order += per_q[q]
    key = {"round": k, "note": "Orchestrator-side key of the image audit (the reader never reads it).",
           "items": key_items}
    key_b = (json.dumps(key, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode()
    sset = {"round": k, "note": "Reader-side record of one image-audit round: no labels; the key is "
                                f"{key_path(k).name} (orchestrator only).",
            "prompt": qual["prompt"], "prompts": PROMPTS, "reader": qual["reader"],
            "n_requests": len(requests), "requests": requests, "delivery_order": order,
            "key_sha256": sha(key_b), "inputs": {
                "second_view_candidates_sha256": sha(SRC.CANDS.read_bytes()),
                "ai_audit_sources_sha256": sha(SRC.PINS.read_bytes()),
                "manifest_dev_sha256": sha((HERE / "manifest_dev.json").read_bytes()),
                "dev_pool_sha256": sha((HERE / "dev_pool.json").read_bytes()),
                "things_definitions_sha256": sha(DEFS.read_bytes()),
                "things_images_metadata_sha256": sha(IMAGES_TSV.read_bytes()),
                "prior_rounds": {f"r{j}": v for j, v in sorted((chained or {}).get("evidence", {}).items())}}}
    set_b = (json.dumps(sset, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode()
    return set_b, key_b


def _chained(k: int) -> dict | None:
    if k == 1:
        return None
    import ai_audit_exec as A
    return A.scientific_chain().admit(k)


def build(k) -> int:
    import ai_audit_exec as A
    k = A.require_round(k)
    set_b, key_b = derive(k, _chained(k), write=True)
    if not json.loads(set_b)["requests"]:
        print(f"round {k}: nothing to ask (no concept awaits a further candidate)")
        return 0
    set_path(k).write_bytes(set_b)
    key_path(k).write_bytes(key_b)
    print(f"round {k}: {json.loads(set_b)['n_requests']} requests, set {sha(set_b)[:16]}, key {sha(key_b)[:16]}")
    return 0


def check(k, chained: dict | None) -> dict:
    """What the executor and scorer call: the committed round-k set and key equal their derivation from the ADMITTED
    chain, and every image file hashes to its request."""
    set_b, key_b = derive(k, chained, write=False)
    if set_path(k).read_bytes() != set_b or key_path(k).read_bytes() != key_b:
        raise SystemExit(f"refused: round {k}'s set or key differs from its mechanical derivation")
    for r in json.loads(set_b)["requests"]:
        if sha((ITEMS / r["file"]).read_bytes()) != r["sha256"]:
            raise SystemExit(f"refused: item file {r['file']} differs from its request")
    return {"round": k, "set_sha256": sha(set_b), "key_sha256": sha(key_b)}


if __name__ == "__main__":
    cmd, k = sys.argv[1], int(sys.argv[2])
    sys.exit(build(k) if cmd == "build" else (print(json.dumps(check(k, _chained(k)))) or 0))
