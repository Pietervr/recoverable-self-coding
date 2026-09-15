"""A1, step 2: pairs, competitors, background lists, draws, packets and the manifest (§3, §12).

Inputs: concepts.json (step 1), the clue bank, carriers.json, instructions.json.
    --clues stimuli/clues.json      the audited bank; outputs go to stimuli/
    --clues stimuli/drafts          merged per-family drafts; outputs go to stimuli/draft_build/
                                    and are marked DRAFT (clues not audited)

Construction (every seed derived from build_concepts.SEED):
- Pairs: within each split (CAL, PILOT, CONF) a seeded perfect matching whose two members
  always come from different families; each member is the other's foil.
- Competitor: for each concept a seeded concept of the same split from a family that is neither
  its own nor its foil's.
- Draw (concept, carrier, d), d = 0..D-1 (CAL and PILOT D = 4; CONF built to D = 8, of which
  draws 0-3 form the D = 4 design): a slot permutation sigma of the 8 slots; a permutation pi of
  the 12 clue indices, applied to the target's clues and, in the controls, to the foil's and the
  competitor's; and the background list: for each of the 8 families, one of its BACKGROUND
  concepts and one of that concept's clauses, in a seeded order d_1..d_8, with d_j in slot
  sigma(j). Draws are keyed by concept: the target and its C1 foil packet share the background.
- Level k in {0,1,2,3,4,6,8}: slots sigma(1..k) hold t_pi(1..k); the other slots keep d_j.
- C1 (CONF, k in {2,3,4}, draw 0): slots sigma(1..k) hold the foil's f_pi(1..k); same background.
- C2 (CONF, k in {2,3,4}, draw 0): t_pi(1..k) in sigma(1..k), the competitor's c_pi(j) in
  sigma(j) for j > k; no background.
- CAL single-clue difficulty (§5; active only): clue i of each CAL concept alone in slot
  sigma(1) of draw 0 with d_2..d_8 in the other slots, every carrier (16 x 12 x 6 = 1,152).
- Conditions: active = instruction A + "\\nAnswer:" suffix; no-target-report = instruction B, no
  suffix. Positions are asserted identical in both.
- Prompt scan: each assembled prompt (instruction, carrier, slots, marker, suffix) is searched
  case-insensitively on word boundaries for the target's and the foil's surface forms. A hit
  regenerates the draw with the next attempt seed (recorded); after ten failed attempts the build
  stops (an exclusion would unpair a foil, so it goes to Entropy SI).
- Rejection, never truncation: a suffix or marker failure, more than 160 packet tokens (carrier
  open through carrier close, tokenized alone) or more than the capture limit stops the build.

Outputs: pairs.json, competitors.json, background.json, draws.json, manifest.csv (one row per
trial and condition, with token counts, positions, ids sha256 and scan result), build_log.json.

    workspace_demo/upstream/jlens-qwen36/.venv/bin/python workspace_demo/t1_access/stimuli/build_bank.py --clues workspace_demo/t1_access/stimuli/drafts
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from stimuli.build_concepts import FAMILIES, SNAPSHOT, derived_seed  # noqa: E402
from stimuli.check_clues import FAMILY_WORDS, word_re  # noqa: E402
from stimuli.packet import ANSWER_SUFFIX, build_ids, packet_text  # noqa: E402

LEVELS = [0, 1, 2, 3, 4, 6, 8]
CONTROL_LEVELS = [2, 3, 4]
DRAWS = {"CAL": 4, "PILOT": 4, "CONF": 8}
MAX_PACKET_TOKENS = 160
CAPTURE_LIMIT = 1024
MAX_ATTEMPTS = 10
N_CLUES = 12


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_clues(path: Path) -> tuple[dict, bool]:
    if path.is_dir():
        clues = {}
        for f in sorted(path.glob("clues_*.json")):
            clues.update(json.loads(f.read_text())["clues"])
        return clues, True
    return json.loads(path.read_text())["clues"], False


def pair_split(ids: list[str], fam: dict, split: str) -> list[list[str]]:
    rng = random.Random(derived_seed(split, "pairs"))
    for _ in range(10000):
        pool = sorted(ids)
        rng.shuffle(pool)
        pairs = []
        while pool:
            a = pool.pop(0)
            cands = [b for b in pool if fam[b] != fam[a]]
            if not cands:
                break
            b = cands[rng.randrange(len(cands))]
            pool.remove(b)
            pairs.append(sorted([a, b]))
        else:
            return sorted(pairs)
    raise RuntimeError(f"no cross-family matching found for {split}")


def make_draw(concept: str, carrier: int, d: int, attempt: int, background: dict) -> dict:
    rng = random.Random(derived_seed(concept, carrier, d, attempt, "draw"))
    sigma = rng.sample(range(8), 8)
    pi = rng.sample(range(N_CLUES), N_CLUES)
    bg = []
    for family in FAMILIES:
        bconcept = sorted(background[family])[rng.randrange(len(background[family]))]
        bg.append([bconcept, rng.randrange(N_CLUES)])
    rng.shuffle(bg)
    return {"attempt": attempt, "sigma": sigma, "pi": pi, "background": bg}


def slot_refs(kind: str, k: int, draw: dict, target: str, foil: str, comp: str, clue_i: int | None = None):
    """Clause references [concept, clue index] for slots 0..7."""
    sigma, pi, bg = draw["sigma"], draw["pi"], draw["background"]
    refs = [None] * 8
    for j in range(8):
        if kind == "primary":
            ref = [target, pi[j]] if j < k else bg[j]
        elif kind == "C1":
            ref = [foil, pi[j]] if j < k else bg[j]
        elif kind == "C2":
            ref = [target, pi[j]] if j < k else [comp, pi[j]]
        elif kind == "single":
            ref = [target, clue_i] if j == 0 else bg[j]
        else:
            raise ValueError(kind)
        refs[sigma[j]] = ref
    return refs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clues", required=True)
    ap.add_argument("--out", help="output directory (default stimuli/ or stimuli/draft_build/)")
    args = ap.parse_args()
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(str(SNAPSHOT))
    bank = json.loads((HERE / "concepts.json").read_text())
    clues, draft = load_clues(Path(args.clues))
    carriers = json.loads((HERE / "carriers.json").read_text())["carriers"]
    instr = json.loads((HERE / "instructions.json").read_text())
    out_dir = Path(args.out) if args.out else (HERE / "draft_build" if draft else HERE)
    out_dir.mkdir(parents=True, exist_ok=True)

    concepts = {c["id"]: c for c in bank["concepts"]}
    fam = {cid: c["family"] for cid, c in concepts.items()}
    missing = sorted(cid for cid in concepts if len(clues.get(cid, [])) != N_CLUES)
    if missing:
        print(f"STOP: {len(missing)} concepts lack {N_CLUES} clauses, e.g. {missing[:5]}")
        return 1
    forms = {cid: [word_re(f) for f in c["surface_forms"]] for cid, c in concepts.items()}
    all_forms = [(cid, rx) for cid, rxs in forms.items() for rx in rxs]
    family_res = [word_re(w) for ws in FAMILY_WORDS.values() for w in ws]
    for text in [t for pair in carriers for t in pair] + [instr["A"], instr["B"], ANSWER_SUFFIX]:
        hits = [cid for cid, rx in all_forms if rx.search(text)] + [rx.pattern for rx in family_res if rx.search(text)]
        if hits:
            print(f"STOP: frame text {text!r} contains {hits}")
            return 1

    split_ids = {s: sorted(cid for cid, c in concepts.items() if c["role"] == s) for s in DRAWS}
    background = {f: [cid for cid, c in concepts.items() if c["role"] == "BACKGROUND" and c["family"] == f]
                  for f in FAMILIES}
    pairs = {s: pair_split(ids, fam, s) for s, ids in split_ids.items()}
    foil = {a: b for s in pairs for p in pairs[s] for a, b in (p, p[::-1])}
    competitors = {}
    for s, ids in split_ids.items():
        for cid in ids:
            cands = sorted(o for o in ids if fam[o] not in (fam[cid], fam[foil[cid]]))
            competitors[cid] = cands[random.Random(derived_seed(cid, "competitor")).randrange(len(cands))]

    def clause(ref):
        return clues[ref[0]][ref[1]]

    def scan(text: str, cid: str) -> list[str]:
        return [f"{o}" for o in (cid, foil[cid]) for rx in forms[o] if rx.search(text)]

    rows, draws, bg_lists, attempts_log = [], {}, {}, []
    token_stats = Counter()

    def trial_texts(kind, k, draw, cid, ci, clue_i=None):
        refs = slot_refs(kind, k, draw, cid, foil[cid], competitors[cid], clue_i)
        slots = [clause(r) for r in refs]
        o, c = carriers[ci]
        return refs, slots, packet_text(instr["A"], o, slots, c), packet_text(instr["B"], o, slots, c), o, c

    for split in DRAWS:
        for cid in split_ids[split]:
            for ci in range(len(carriers)):
                for d in range(DRAWS[split]):
                    for attempt in range(MAX_ATTEMPTS):
                        draw = make_draw(cid, ci, d, attempt, background)
                        specs = [("primary", k, None) for k in LEVELS]
                        if d == 0 and split == "CONF":
                            specs += [("C1", k, None) for k in CONTROL_LEVELS] + [("C2", k, None) for k in CONTROL_LEVELS]
                        if d == 0 and split == "CAL":
                            specs += [("single", 1, i) for i in range(N_CLUES)]
                        built, hits = [], []
                        for kind, k, clue_i in specs:
                            refs, slots, pa, pb, o, c = trial_texts(kind, k, draw, cid, ci, clue_i)
                            h = scan(pa + ANSWER_SUFFIX, cid) + scan(pb, cid)
                            if h:
                                hits.append({"kind": kind, "k": k, "hits": h})
                            built.append((kind, k, clue_i, refs, slots, pa, pb, o, c))
                        if not hits:
                            break
                        attempts_log.append({"concept": cid, "carrier": ci, "draw": d, "attempt": attempt, "hits": hits})
                    else:
                        print(f"STOP: {cid} carrier {ci} draw {d} failed the prompt scan {MAX_ATTEMPTS} times")
                        return 1
                    key = f"{cid}|{ci}|{d}"
                    draws[key] = {"attempt": draw["attempt"], "sigma": draw["sigma"], "pi": draw["pi"]}
                    bg_lists[key] = [f"{b}#{i}" for b, i in draw["background"]]
                    for kind, k, clue_i, refs, slots, pa, pb, o, c in built:
                        a = build_ids(tok, pa, ANSWER_SUFFIX)
                        packet_tokens = len(tok.encode("\n".join([o, *("- " + s for s in slots), c]),
                                                       add_special_tokens=False))
                        token_stats[packet_tokens] += 1
                        if packet_tokens > MAX_PACKET_TOKENS or len(a["ids"]) > CAPTURE_LIMIT:
                            print(f"STOP: overlength {cid} {kind} k={k}: {packet_tokens} packet tokens")
                            return 1
                        conds = [("active", a)]
                        if kind != "single":
                            b = build_ids(tok, pb, None)
                            if b["ids"][len(tok.encode(instr["B"], add_special_tokens=False)):] != \
                                    a["ids"][len(tok.encode(instr["A"], add_special_tokens=False)):a["n_prefix"]] \
                                    or b["marker_positions"] != a["marker_positions"]:
                                print(f"STOP: condition positions differ for {cid} {kind} k={k}")
                                return 1
                            conds.append(("noreport", b))
                        for cond, ids in conds:
                            tid = f"{split}|{kind}|{cond}|{cid}|c{ci}|d{d}|k{k}" + (f"|i{clue_i}" if clue_i is not None else "")
                            rows.append({
                                "trial_id": tid, "split": split, "set": kind, "condition": cond,
                                "concept": cid, "family": fam[cid], "foil": foil[cid],
                                "competitor": competitors[cid], "carrier": ci, "draw": d, "k": k,
                                "clue": "" if clue_i is None else clue_i, "attempt": draw["attempt"],
                                "slots": ";".join(f"{r[0]}#{r[1]}" for r in refs),
                                "n_ids": len(ids["ids"]), "n_prefix": ids["n_prefix"],
                                "packet_tokens": packet_tokens, "readout_position": ids["readout_position"],
                                "marker_positions": " ".join(map(str, ids["marker_positions"])),
                                "ids_sha256": hashlib.sha256(json.dumps(ids["ids"]).encode()).hexdigest(),
                                "scan": "ok",
                            })

    (out_dir / "pairs.json").write_text(json.dumps(pairs, indent=1) + "\n")
    (out_dir / "competitors.json").write_text(json.dumps(competitors, indent=1) + "\n")
    (out_dir / "background.json").write_text(json.dumps(bg_lists) + "\n")
    (out_dir / "draws.json").write_text(json.dumps(draws) + "\n")
    with open(out_dir / "manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    counts = Counter((r["split"], r["set"], r["condition"]) for r in rows)
    log = {
        "status": "DRAFT (clues not audited)" if draft else "built from the audited clue bank",
        "clues_source": str(args.clues),
        "inputs_sha256": {"concepts.json": sha(HERE / "concepts.json"), "carriers.json": sha(HERE / "carriers.json"),
                          "instructions.json": sha(HERE / "instructions.json"),
                          "clues": hashlib.sha256(json.dumps(clues, sort_keys=True).encode()).hexdigest(),
                          "build_bank.py": sha(Path(__file__)), "packet.py": sha(HERE / "packet.py"),
                          "tokenizer.json": sha(SNAPSHOT / "tokenizer.json")},
        "levels": LEVELS, "control_levels": CONTROL_LEVELS, "draws": DRAWS,
        "counts": {"|".join(k): v for k, v in sorted(counts.items())},
        "packet_tokens": {"min": min(token_stats), "max": max(token_stats),
                          "mean": sum(k * v for k, v in token_stats.items()) / sum(token_stats.values())},
        "scan_regenerations": attempts_log,
    }
    (out_dir / "build_log.json").write_text(json.dumps(log, indent=1) + "\n")
    for k, v in sorted(counts.items()):
        print(f"{'|'.join(k):<30} {v:>6}")
    print(f"packet tokens {log['packet_tokens']}; scan regenerations {len(attempts_log)}; -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
