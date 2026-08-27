"""E6 — the gating-exit threshold on the rig (the closed-form design rule).

The paper's sharpest untested closed-form prediction: exiting the bistable
wedge requires certification coverage q > 1 - 1/[alpha(1+theta)]. The rig
protocol (predictions committed first — see e6_predict.py and commit
2ac26c2):

  1. IGNITE: the proven E4 ramp (burst dwells at nominal
     l = 0.60, 0.75, 0.85, 0.95, 1.05, 1.05; alpha = 0.8 spawning, no
     gate) until the loop is collapsed.
  2. GATE, ascending q in {0.40, 0.55, 0.70, 0.85}: continuous Poisson
     arrivals at TRUE utilization 0.75 (lambda = 0.75 / 25.2 s) for
     2100 s wall-clock per phase, with an ORACLE certification gate of
     coverage q: each uncertified completion is caught with probability
     q — caught means NO offspring spawn and the CORRECT line enters the
     window instead of the junk (certification = archived commitment;
     alpha_eff = (1-q) alpha exactly as the theory defines).
  3. Verdict per phase from the backlog slope: EXIT if B_end <= 0.7
     B_start; PINNED if B_end >= B_start; else AMBIG. After an EXIT,
     re-ignite (two 1.05 dwells) before the next q.

Committed predictions: closed form q* = 0.661; reduced model crossing
~0.78 with PINNED/PINNED/PINNED-or-slow/EXIT at the four points. The rig
adjudicates between the theory levels.

Run:  python3 e6_gating.py [--seed 0]
Logs: runs/e6_gating.jsonl + console verdicts.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path

from harness.battery import filter_single_token, graded, load_probe_swap
from harness.certify import band_layers, certified
from harness.client import JLensClient
from harness.runlog import RunLog

HERE = Path(__file__).parent

T_D = 66.0
LAM_UNIT = 1 / 10.95
ALPHA = 0.8
MAX_DEPTH = 4
MAX_PER_ROOT = 10
WINDOW_CHARS = 11000
EXO = 12
DWELL_WALL = 480.0
IGNITE_LS = [0.60, 0.75, 0.85, 0.95, 1.05, 1.05]
REIGNITE_LS = [1.05, 1.05]
Q_SEQ = [0.40, 0.55, 0.70, 0.85]
RHO_GATED = 0.75
S_CONG = 25.2
GATE_WALL = 2100.0


def poisson(rng, lam):
    l_exp, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= l_exp:
            return k
        k += 1


def clause_of(item):
    p = item["prompt"].strip()
    body = p[5:].strip() if p.lower().startswith("fact:") else p
    return body[0].lower() + body[1:]


class Task:
    __slots__ = ("tid", "kind", "item", "arrival", "deadline", "root",
                 "depth", "prev_answer")

    def __init__(self, tid, kind, item, arrival, deadline, root=None,
                 depth=0, prev_answer=None):
        self.tid, self.kind, self.item = tid, kind, item
        self.arrival, self.deadline = arrival, deadline
        self.root = root if root is not None else tid
        self.depth = depth
        self.prev_answer = prev_answer

    def prompt(self):
        if self.kind == "exo":
            return self.item["prompt"].rstrip()
        cl = clause_of(self.item)
        if cl.endswith(" is"):
            cl = cl[:-3]
        return (f"Fact check: it was recorded that {cl} is"
                f"{self.prev_answer} That may be wrong. In fact, {cl} is")


class Rig:
    def __init__(self, c, band, items, seed, log):
        self.c, self.band, self.items = c, band, items
        self.rng = random.Random(6000 + seed)
        self.seed = seed
        self.log = log
        self.window = ""
        self.queue: list[Task] = []
        self.tid = 0
        self.kids: dict[int, int] = {}
        self.phase = "ignite"
        self.q = 0.0

    def new_tid(self):
        self.tid += 1
        return self.tid

    def serve_one(self, task):
        c = self.c
        prompt = (self.window + "\n" if self.window else "") + task.prompt()
        t0 = time.time()
        sl = c.slice(prompt, top_n=10, max_seq_len=4096, tail=160)
        toks = sl["token_strs"]
        off = sl.get("pos_offset", 0)
        start = 0
        for i, t in enumerate(toks):
            if "Fact" in t:
                start = i
        view = {"cells": {
            layer: {"top_tokens": cell["top_tokens"][max(0, start - off):]}
            for layer, cell in sl["cells"].items()}}
        cert = certified(view, [task.item["intermediate"]], self.band, 10)
        text = c.generate(prompt, max_tokens=8)
        dur = time.time() - t0
        ok = graded(task.item, text)
        first = " " + text.strip().split("\n")[0][:80] if text.strip() else " ..."
        late = time.time() > task.deadline
        uncert = late or not ok
        caught = (uncert and self.phase.startswith("gate")
                  and self.rng.random() < self.q)
        if caught:
            appended = " " + task.item["answer"] + "."   # archived, no junk
        else:
            appended = first
            if (uncert and task.depth < MAX_DEPTH
                    and self.kids.get(task.root, 0) < MAX_PER_ROOT):
                n = min(poisson(self.rng, ALPHA),
                        MAX_PER_ROOT - self.kids.get(task.root, 0))
                self.kids[task.root] = self.kids.get(task.root, 0) + n
                for _ in range(n):
                    self.queue.append(Task(
                        self.new_tid(), "repair", task.item, time.time(),
                        time.time() + T_D, root=task.root,
                        depth=task.depth + 1, prev_answer=first))
        self.window = (self.window + task.prompt() + appended + "\n")[-WINDOW_CHARS:]
        self.log.write({
            "exp": "e6", "seed": self.seed, "phase": self.phase,
            "q": self.q, "tid": task.tid, "kind": task.kind,
            "depth": task.depth, "certified": cert["certified"],
            "rank": cert["best_rank"], "correct": ok, "late": late,
            "uncert": uncert, "caught": caught,
            "service_s": round(dur, 2), "queue_after": len(self.queue),
            "ctx_tokens": sl["seq_len"], "text": first[:50],
        })
        return uncert

    def burst_dwell(self, l):
        rng = self.rng
        lam = l * LAM_UNIT
        t_a = time.time()
        pending = []
        for _ in range(EXO):
            t_a += rng.expovariate(lam)
            pending.append(t_a)
        dwell_t0 = time.time()
        n = u = 0
        while pending or (self.queue and time.time() < dwell_t0 + DWELL_WALL):
            now = time.time()
            while pending and pending[0] <= now:
                arr = pending.pop(0)
                self.queue.append(Task(self.new_tid(), "exo",
                                       self.items[rng.randrange(len(self.items))],
                                       arr, arr + T_D))
            if not self.queue:
                if pending:
                    time.sleep(min(0.25, max(0.01, pending[0] - now)))
                continue
            if now > dwell_t0 + DWELL_WALL and not pending:
                break
            u += self.serve_one(self.queue.pop(0))
            n += 1
        print(f"  [{self.phase}] l={l:.2f} served={n} P_u={u / max(1, n):.2f} "
              f"backlog={len(self.queue)}")

    def gate_phase(self, q):
        rng = self.rng
        self.q = q
        self.phase = f"gate{q:.2f}"
        b_start = len(self.queue)
        lam = RHO_GATED / S_CONG
        gate_t0 = time.time()
        t_a = gate_t0
        arrivals = []
        while t_a < gate_t0 + GATE_WALL:
            t_a += rng.expovariate(lam)
            arrivals.append(t_a)
        n = u = 0
        while time.time() < gate_t0 + GATE_WALL:
            now = time.time()
            while arrivals and arrivals[0] <= now:
                arr = arrivals.pop(0)
                self.queue.append(Task(self.new_tid(), "exo",
                                       self.items[rng.randrange(len(self.items))],
                                       arr, arr + T_D))
            if not self.queue:
                time.sleep(0.25)
                continue
            u += self.serve_one(self.queue.pop(0))
            n += 1
        b_end = len(self.queue)
        if b_end <= 0.7 * b_start:
            v = "EXIT"
        elif b_end >= b_start:
            v = "PINNED"
        else:
            v = "AMBIG"
        print(f"  VERDICT q={q:.2f}: {v}  (B {b_start} -> {b_end}, "
              f"served={n}, P_u={u / max(1, n):.2f})")
        self.q = 0.0
        self.phase = "ignite"
        return v


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(HERE / "runs" / "e6_gating.jsonl"))
    args = ap.parse_args()

    c = JLensClient(port=args.port)
    c.require_n1000()
    sl = c.slice("Fact: The capital of France is", top_n=5)
    band = band_layers(sl["layers"])
    items, _ = filter_single_token(c, load_probe_swap())
    print(f"band {band[0]}..{band[-1]}; battery {len(items)}")

    log = RunLog(args.out)
    rig = Rig(c, band, items, args.seed, log)
    print("=== IGNITION ===")
    for l in IGNITE_LS:
        rig.burst_dwell(l)
        if len(rig.queue) >= 25:
            break
    verdicts = {}
    need_reignite = False
    for q in Q_SEQ:
        # mirror the predictor exactly: re-ignite after every EXIT (or a
        # weak backlog), so each gate phase starts from a collapsed state.
        # Seed 0 deviated here (re-ignited only when backlog < 8) — fixed
        # after the mid-run review; the deviation is recorded in RESULTS.
        if need_reignite or len(rig.queue) < 8:
            print("=== RE-IGNITION ===")
            for l in REIGNITE_LS:
                rig.burst_dwell(l)
        if len(rig.queue) < 8:
            verdicts[q] = "VOID"
            print(f"  VERDICT q={q:.2f}: VOID (could not ignite)")
            continue
        verdicts[q] = rig.gate_phase(q)
        need_reignite = verdicts[q] == "EXIT"
    print("\nE6 VERDICTS:", verdicts)
    print("PREDICTED:  0.40 PINNED / 0.55 PINNED / 0.70 PINNED-or-slow / "
          "0.85 EXIT   (closed form q*=0.661; model crossing ~0.78)")
    (HERE / "runs" / "e6_verdicts.json").write_text(json.dumps(
        {str(k): v for k, v in verdicts.items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
