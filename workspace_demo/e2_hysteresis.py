"""E2 — hysteresis under feedback closure (design doc §4, the headline).

A session is a growing transcript of quick factual Q/A steps. The drive is a
held-words ramp k(t): up 0->K_max, then symmetrically down. The feedback
closure is the arm:

  alpha=1 : the model's RAW greedy output for each step is appended to the
            transcript (errors and junk re-enter as standing load).
  alpha=0 : the CORRECT answer is appended instead (a fully gated
            certification channel), PADDED with neutral filler to match the
            alpha=1 arm's per-step appended token count — so both arms have
            identical context LENGTH at every step and differ only in
            re-entrant CONTENT.

After the down-ramp both arms get a probe block at k=probe_k, then a RESET
(transcript cleared to the standing instruction) and the same probe block
again — "reset restores only what is archived."

Predictions (stated pre-run, design doc §8): down-branch < up-branch at
matched k in the alpha=1 arm; no (or much smaller) gap in the length-matched
alpha=0 arm; post-reset probe ≈ up-branch. Refutation of any of these is a
reportable negative result.

Per step: certification of the current item's intermediate (question span),
occupancy of the current held words, graded correctness, context length.

Run:  python3 e2_hysteresis.py [--sessions 3] [--kmax 48] [--kstep 8]
Logs: runs/e2_hysteresis.jsonl + runs/e2_summary.json
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from harness.battery import (
    filter_single_token,
    graded,
    held_words,
    load_probe_swap,
)
from harness.certify import band_layers, certified, occupancy_of
from harness.client import JLensClient
from harness.runlog import RunLog

HERE = Path(__file__).parent

# Flat fact-stream framing: bare completions, no Q/A labels. The Q/A chat
# shape provoked Qwen3.6 <think> blocks on every step (caught by the sanity
# gate, 2026-08-24 04:19); the "Fact: ... is" completion surface used by
# P0/P1/E1 does not.
INSTR = (
    "A running list of quick facts. Keep earlier lines in mind; they may "
    "be referenced again.\n\n"
)

FILLER = (
    " The weather report mentioned mild conditions with light wind and "
    "clear skies expected through the afternoon across the region."
)


def ramp_profile(kmax: int, kstep: int) -> list[tuple[str, int]]:
    """[(branch, k)]: up 0..kmax, down kmax-kstep..0."""
    up = list(range(0, kmax + 1, kstep))
    down = list(range(kmax - kstep, -1, -kstep))
    return [("up", k) for k in up] + [("down", k) for k in down]


def step_question(item: dict, words: list[str]) -> str:
    q = ""
    if words:
        q += "Hold these words in mind: " + ", ".join(words) + ".\n"
    q += item["prompt"].rstrip()  # ends with "... is" — bare completion form
    return q


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
    """Append neutral filler until text tokenizes to >= n_target pieces,
    then no trimming (approximate match is sufficient; we log exact
    context length per step)."""
    while c.n_pieces(text) < n_target:
        text += FILLER
    return text


def run_session(
    c: JLensClient,
    alpha: int,
    session_id: int,
    items: list[dict],
    profile: list[tuple[str, int]],
    probe_k: int,
    log: RunLog,
    band: list[int],
    top_k: int,
    alpha1_lengths: dict[int, int] | None,
) -> dict[int, int]:
    """One session. Returns per-step appended-token counts (for the
    alpha=0 arm to length-match). alpha1_lengths: the counts from the
    matched alpha=1 session (None for the alpha=1 arm itself)."""
    rng = random.Random(1000 + session_id)
    stream = items[:]
    rng.shuffle(stream)
    transcript = INSTR
    lengths: dict[int, int] = {}

    steps: list[tuple[str, int]] = profile + [("probe", probe_k)] * 3
    reset_at = len(steps)
    steps = steps + [("reset_probe", probe_k)] * 3

    for t, (branch, k) in enumerate(steps):
        if t == reset_at:
            transcript = INSTR  # THE RESET: context cleared, weights intact
        item = stream[t % len(stream)]
        words = held_words(c, k, seed=hash((session_id, t)) & 0xFFFF)
        q = step_question(item, words)
        prompt = transcript + q

        sl = c.slice(prompt, top_n=top_k, max_seq_len=4096)
        qs, qe = question_span_last(sl)
        view = span_view(sl, qs, qe)
        cert = certified(view, [item["intermediate"]], band, top_k)
        occ = occupancy_of(view, words, band, top_k) if words else 0
        text = c.generate(prompt, max_tokens=10)
        ok = graded(item, text)

        # feedback closure: what re-enters the transcript as the fact line's
        # completion
        raw = " " + text.strip().split("\n")[0][:120] if text.strip() else " ..."
        if alpha == 1:
            appended = raw
        else:
            appended = " " + item["answer"] + "."
            if alpha1_lengths and t in alpha1_lengths:
                appended = pad_to_tokens(c, appended, alpha1_lengths[t])
        lengths[t] = c.n_pieces(appended)
        transcript = prompt + appended + "\n"

        log.write(
            {
                "exp": "e2",
                "alpha": alpha,
                "session": session_id,
                "step": t,
                "branch": branch,
                "k": k,
                "item": item["name"],
                "certified": cert["certified"],
                "best_rank": cert["best_rank"],
                "occupancy": occ,
                "correct": ok,
                "ctx_tokens": sl["seq_len"],
                "text": text[:40],
            }
        )
        print(
            f"a={alpha} s={session_id} t={t:>2} {branch:>11} k={k:>2} "
            f"ctx={sl['seq_len']:>4} cert={int(cert['certified'])} occ={occ} "
            f"ok={int(ok)} {text[:24]!r}"
        )
    return lengths


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--sessions", type=int, default=3)
    ap.add_argument("--kmax", type=int, default=48)
    ap.add_argument("--kstep", type=int, default=8)
    ap.add_argument("--probe-k", type=int, default=16)
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--out", default=str(HERE / "runs" / "e2_hysteresis.jsonl"))
    args = ap.parse_args()

    c = JLensClient(port=args.port)
    c.require_n1000()
    items = load_probe_swap()
    kept, _ = filter_single_token(c, items)

    # band from a throwaway slice
    sl = c.slice("Fact: The capital of France is", top_n=5)
    band = band_layers(sl["layers"])
    print(f"band: {band[0]}..{band[-1]}")

    profile = ramp_profile(args.kmax, args.kstep)
    print(f"profile: {profile} + probes(k={args.probe_k}) + reset probes")

    log = RunLog(args.out)
    done = {(r.get("alpha"), r.get("session")) for r in log.records()}

    for s in range(args.sessions):
        if (1, s) not in done:
            lens_a1 = run_session(
                c, 1, s, kept, profile, args.probe_k, log, band, args.top_k, None
            )
        else:
            # rebuild lengths from the log for the alpha=0 match
            lens_a1 = {}
            print(f"alpha=1 session {s} already logged; alpha=0 will pad approximately")
        if (0, s) not in done:
            run_session(
                c, 0, s, kept, profile, args.probe_k, log, band, args.top_k,
                lens_a1 or None,
            )

    # summary: per (alpha, branch, k)
    agg: dict[tuple, list[dict]] = defaultdict(list)
    for r in log.records():
        if r.get("exp") == "e2":
            agg[(r["alpha"], r["branch"], r["k"])].append(r)
    summary = {}
    for key in sorted(agg, key=str):
        rs = agg[key]
        n = len(rs)
        summary[str(key)] = {
            "n": n,
            "cert_rate": round(sum(r["certified"] for r in rs) / n, 3),
            "accuracy": round(sum(r["correct"] for r in rs) / n, 3),
            "mean_occ": round(sum(r["occupancy"] for r in rs) / n, 2),
            "mean_ctx": round(sum(r["ctx_tokens"] for r in rs) / n, 0),
        }
    print("E2 SUMMARY (alpha, branch, k):")
    print(json.dumps(summary, indent=1))
    (HERE / "runs" / "e2_summary.json").write_text(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
