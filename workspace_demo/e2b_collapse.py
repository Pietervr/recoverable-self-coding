"""E2b — the collapse boundary: interrogated load × depth × feedback closure.

The E1/E2 finding this answers: PASSIVE held-word load cannot displace the
live inference's determinants — certification stayed ≥0.98 at K≤48 and every
E2 error was certified-but-wrong. E2b makes the load LIABLE: the watch list
is actually interrogated (forced-choice queries at unpredictable steps), so
evicting it costs errors — the load now contests the inference path. Depth
adds a second axis: the official 2-hop probe-swap items vs constructed 3-hop
chains (landmark → city → country → language), certified PER intermediate.
Neither intermediate ever appears verbatim in any prompt (no echo).

Drive ladder within each session: watch-list size L = 0,2,4,6,8, the list
re-declared (replacing the old one) at each level. Per level: one 2-hop fact
step, one 3-hop fact step, and (L>0) one watch query. Arms exactly as E2:
alpha=1 raw re-entry vs alpha=0 gated + length-matched. Slices at top_n=25:
certified = best rank ≤ 10 (the unchanged E1/E2 criterion); ranks 11–25 are
logged so top-k CROWDING can be separated from genuine ABSENCE.

Pre-registered predictions (P) and falsifiers (F), stated before the run:
  P1  cert rate / best rank of fact-step determinants declines with L.
      F1: flat at ceiling → the boundary lies beyond interrogated L≤8.
  P2  the decline is earlier or steeper under alpha=1 (feedback raises R).
      F2: arms indistinguishable.
  P3  at high L, errors concentrate on uncertified fact steps (determinant
      absence predicts error — the E3 signature).
      F3: errors independent of certification (E2's regime persists).
  P4  watch-query accuracy declines once L exceeds the E1 capacity (~3).
      F4: flat → the interrogation failed to bind the load.

Watch-query steps are graded but their certification is NOT a determinant
measure (both options are echoed in the prompt); instead the rank
DIFFERENTIAL rank(held) vs rank(foil) is logged.

Calibration gate: each 3-hop item is run bare (no transcript, L=0) once and
pruned if the final answer is wrong — a baseline-wrong item measures the
model's knowledge, not the workspace. ≥8 survivors required to proceed.
Cached in runs/e2b_calibration.json.

Run:  python3 e2b_collapse.py [--sessions 10]
Logs: runs/e2b_collapse.jsonl + runs/e2b_summary.json
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from harness.battery import (
    LOAD_POOL,
    filter_single_token,
    graded,
    held_words,
    load_probe_swap,
)
from harness.certify import band_layers, certified, occupancy_of
from harness.client import JLensClient
from harness.runlog import RunLog

HERE = Path(__file__).parent

INSTR = (
    "A running list of quick facts and watch-list checks. Keep the current "
    "watch list in mind; you will be asked about it.\n\n"
)

FILLER = (
    " The weather report mentioned mild conditions with light wind and "
    "clear skies expected through the afternoon across the region."
)

LEVELS = [0, 2, 4, 6, 8]

# 3-hop chains: landmark -> city -> country -> language. The landmark text
# never contains the city or country string (no echo). Intermediates must
# both survive the single-token filter at runtime.
THREE_HOP_RAW = [
    ("eiffel", "Eiffel Tower", "Paris", "France", "French"),
    ("versailles", "Palace of Versailles", "Paris", "France", "French"),
    ("colosseum", "Colosseum", "Rome", "Italy", "Italian"),
    ("kremlin", "Kremlin", "Moscow", "Russia", "Russian"),
    ("stbasil", "Saint Basil's Cathedral", "Moscow", "Russia", "Russian"),
    ("bigben", "Big Ben", "London", "England", "English"),
    ("towerbridge", "Tower Bridge", "London", "England", "English"),
    ("sagrada", "Sagrada Familia", "Barcelona", "Spain", "Spanish"),
    ("brandenburg", "Brandenburg Gate", "Berlin", "Germany", "German"),
    ("acropolis", "Acropolis", "Athens", "Greece", "Greek"),
    ("giza", "Pyramids of Giza", "Cairo", "Egypt", "Arabic"),
    ("shibuya", "Shibuya Crossing", "Tokyo", "Japan", "Japanese"),
    ("forbidden", "Forbidden City", "Beijing", "China", "Chinese"),
    ("bluemosque", "Blue Mosque", "Istanbul", "Turkey", "Turkish"),
    ("mermaid", "Little Mermaid statue", "Copenhagen", "Denmark", "Danish"),
    ("wawel", "Wawel Castle", "Krakow", "Poland", "Polish"),
]


def three_hop_items() -> list[dict]:
    out = []
    for name, landmark, city, country, lang in THREE_HOP_RAW:
        out.append(
            {
                "name": f"3hop-{name}",
                "prompt": (
                    "Fact: The language spoken in the country containing "
                    f"the city that is home to the {landmark} is"
                ),
                "city": city,
                "country": country,
                "answer": lang,
            }
        )
    return out


def question_span_last(slice_resp: dict) -> tuple[int, int]:
    toks = slice_resp["token_strs"]
    start = 0
    for i, t in enumerate(toks):
        if "Fact" in t:
            start = i
    return start, len(toks)


def span_view(slice_resp: dict, start: int, end: int) -> dict:
    return {
        "cells": {
            layer: {"top_tokens": cell["top_tokens"][start:end]}
            for layer, cell in slice_resp["cells"].items()
        }
    }


def pad_to_tokens(c: JLensClient, text: str, n_target: int) -> str:
    while c.n_pieces(text) < n_target:
        text += FILLER
    return text


def single_token(c: JLensClient, w: str) -> bool:
    return any(c.n_pieces(f) == 1 for f in (f" {w}", w, f" {w.lower()}", w.lower()))


def calibrate_three_hop(c: JLensClient, items: list[dict], band, top_k) -> list[dict]:
    """Bare-baseline pass: prune items the model gets wrong with no load and
    no transcript. Cached across resumes."""
    cache = HERE / "runs" / "e2b_calibration.json"
    if cache.exists():
        keep_names = set(json.loads(cache.read_text())["keep"])
        return [it for it in items if it["name"] in keep_names]
    keep, detail = [], []
    for it in items:
        if not (single_token(c, it["city"]) and single_token(c, it["country"])):
            detail.append({"name": it["name"], "drop": "multi-token intermediate"})
            continue
        sl = c.slice(it["prompt"], top_n=25, max_seq_len=512, tail=160)
        off = sl.get("pos_offset", 0)
        qs, qe = question_span_last(sl)
        view = span_view(sl, max(0, qs - off), qe - off)
        c_city = certified(view, [it["city"]], band, 25)
        c_ctry = certified(view, [it["country"]], band, 25)
        text = c.generate(it["prompt"], max_tokens=8)
        ok = graded(it, text)
        detail.append(
            {
                "name": it["name"], "ok": ok,
                "rank_city": c_city["best_rank"], "rank_country": c_ctry["best_rank"],
                "text": text[:30],
            }
        )
        if ok:
            keep.append(it)
        print(
            f"cal {it['name']:>18} ok={int(ok)} city_r={c_city['best_rank']} "
            f"ctry_r={c_ctry['best_rank']} {text[:20]!r}"
        )
    cache.write_text(
        json.dumps({"keep": [it["name"] for it in keep], "detail": detail}, indent=1)
    )
    if len(keep) < 8:
        raise RuntimeError(f"3-hop calibration gate FAILED: {len(keep)} survivors")
    return keep


def declaration(words: list[str]) -> str:
    if not words:
        return "The watch list is now empty.\n"
    return (
        "New watch list (replaces any earlier list; you may be asked which "
        "words are on it): " + ", ".join(words) + ".\n"
    )


def run_session(
    c: JLensClient,
    alpha: int,
    session_id: int,
    two_hop: list[dict],
    three_hop: list[dict],
    log: RunLog,
    band: list[int],
    alpha1_lengths: dict[int, int] | None,
) -> dict[int, int]:
    rng = random.Random(7000 + session_id)
    s2 = two_hop[:]
    rng.shuffle(s2)
    s3 = three_hop[:]
    rng.shuffle(s3)
    transcript = INSTR
    lengths: dict[int, int] = {}
    t = 0
    i2 = i3 = 0

    for li, level in enumerate(LEVELS):
        watch = held_words(c, level, seed=hash((session_id, li)) & 0xFFFF)
        transcript += declaration(watch)
        kinds = ["fact2", "fact3"] + (["query"] if level else [])
        for kind in kinds:
            if kind == "fact2":
                item = s2[i2 % len(s2)]
                i2 += 1
                dets = {"det": item["intermediate"]}
            elif kind == "fact3":
                item = s3[i3 % len(s3)]
                i3 += 1
                dets = {"city": item["city"], "country": item["country"]}
            else:
                held = rng.choice(watch)
                foil = next(
                    w for w in rng.sample(LOAD_POOL, len(LOAD_POOL))
                    if w not in watch and single_token(c, w)
                )
                a, b = (held, foil) if rng.random() < 0.5 else (foil, held)
                item = {
                    "name": f"query-{held}",
                    "prompt": (
                        f"Fact: Of the words {a} and {b}, the one on the "
                        "current watch list is"
                    ),
                    "answer": held,
                }
                dets = {"held": held, "foil": foil}

            prompt = transcript + item["prompt"].rstrip()
            sl = c.slice(prompt, top_n=25, max_seq_len=4096, tail=160)
            off = sl.get("pos_offset", 0)
            qs, qe = question_span_last(sl)
            view = span_view(sl, max(0, qs - off), qe - off)

            rec: dict = {
                "exp": "e2b", "alpha": alpha, "session": session_id,
                "step": t, "level": level, "kind": kind, "item": item["name"],
                "ctx_tokens": sl["seq_len"],
            }
            if kind == "query":
                rh = certified(view, [dets["held"]], band, 25)
                rf = certified(view, [dets["foil"]], band, 25)
                rec["rank_held"] = rh["best_rank"]
                rec["rank_foil"] = rf["best_rank"]
                rec["certified"] = None  # echoed options: not a det measure
            else:
                ranks = {}
                all_cert = True
                for dk, dw in dets.items():
                    r = certified(view, [dw], band, 25)
                    ranks[dk] = r["best_rank"]
                    if r["best_rank"] is None or r["best_rank"] > 10:
                        all_cert = False
                rec["ranks"] = ranks
                rec["certified"] = all_cert
                rec["occupancy"] = (
                    occupancy_of(view, watch, band, 10) if watch else 0
                )

            text = c.generate(prompt, max_tokens=10)
            rec["correct"] = graded(item, text)
            rec["text"] = text[:40]

            raw = " " + text.strip().split("\n")[0][:120] if text.strip() else " ..."
            if alpha == 1:
                appended = raw
            else:
                appended = " " + item["answer"] + "."
                if alpha1_lengths and t in alpha1_lengths:
                    appended = pad_to_tokens(c, appended, alpha1_lengths[t])
            lengths[t] = c.n_pieces(appended)
            transcript = prompt + appended + "\n"

            log.write(rec)
            print(
                f"a={alpha} s={session_id} t={t:>2} L={level} {kind:>5} "
                f"ctx={sl['seq_len']:>4} cert={rec['certified']} "
                f"ok={int(rec['correct'])} {text[:22]!r}"
            )
            t += 1
    return lengths


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--sessions", type=int, default=10)
    ap.add_argument("--out", default=str(HERE / "runs" / "e2b_collapse.jsonl"))
    args = ap.parse_args()

    c = JLensClient(port=args.port)
    c.require_n1000()
    sl = c.slice("Fact: The capital of France is", top_n=5)
    band = band_layers(sl["layers"])
    print(f"band: {band[0]}..{band[-1]}")

    two_hop, _ = filter_single_token(c, load_probe_swap())
    three = calibrate_three_hop(c, three_hop_items(), band, 25)
    print(f"battery: {len(two_hop)} two-hop, {len(three)} three-hop survivors")

    n_steps = sum(2 + (1 if lv else 0) for lv in LEVELS)
    log = RunLog(args.out)
    counts: dict[tuple, int] = defaultdict(int)
    for r in log.records():
        counts[(r.get("alpha"), r.get("session"))] += 1
    done = {key for key, n in counts.items() if n >= n_steps}

    for s in range(args.sessions):
        lens_a1: dict[int, int] = {}
        if (1, s) not in done:
            lens_a1 = run_session(c, 1, s, two_hop, three, log, band, None)
        if (0, s) not in done:
            run_session(c, 0, s, two_hop, three, log, band, lens_a1 or None)

    # summary: per (alpha, level, kind), last record per step wins
    latest: dict[tuple, dict] = {}
    for r in log.records():
        if r.get("exp") == "e2b":
            latest[(r["alpha"], r["session"], r["step"])] = r
    agg: dict[tuple, list[dict]] = defaultdict(list)
    for r in latest.values():
        agg[(r["alpha"], r["level"], r["kind"])].append(r)
    summary = {}
    for key in sorted(agg, key=str):
        rs = agg[key]
        n = len(rs)
        cert = [r["certified"] for r in rs if r["certified"] is not None]
        summary[str(key)] = {
            "n": n,
            "cert_rate": round(sum(cert) / len(cert), 3) if cert else None,
            "accuracy": round(sum(r["correct"] for r in rs) / n, 3),
            "mean_ctx": round(sum(r["ctx_tokens"] for r in rs) / n, 0),
        }
    print("E2B SUMMARY (alpha, level, kind):")
    print(json.dumps(summary, indent=1))
    (HERE / "runs" / "e2b_summary.json").write_text(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
