"""E7 — fluctuation precursors on the rig (the designed long-dwell
protocol; predictions committed first in e7_predict.py / runs/
e7_prediction.json).

Two arms per seed, identical except the feedback channel:
  FEEDBACK: alpha = 0.8 spawning (no gate)
  CONTROL:  alpha = 0 (no spawning; same load, same drift, no fold)
Both arms: window PRE-FILLED with clean battery lines to the char cap
(service starts on the congested law), then CONTINUOUS Poisson exo
arrivals at lambda = 0.45 / 25.2 s for 3600 s wall-clock.

Order parameters logged per served task: queue_after (primary), the
junk-deposit indicator (secondary). Analysis = e7_stats.arm_summary
(pre-registered): per-window linear detrend, residual variance + AC1,
exact-unbiased Bernoulli excess variance, Kendall-tau trends; pre-onset
segment = tasks before queue_after >= 12; censor below 40 tasks.

Prediction: feedback tau_qvar ~ +0.30 and tau_qac1 ~ +0.14 vs control
~ 0; control should not ignite. Falsifier: arms indistinguishable, or
negative trends.

Run:  python3 e7_precursors_dwell.py [--seed 0]
Logs: runs/e7_precursors.jsonl (+ arm_done summary records)
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
from e7_stats import arm_summary

HERE = Path(__file__).parent

T_D = 66.0
ALPHA_FEEDBACK = 0.8
MAX_DEPTH = 4
MAX_PER_ROOT = 10
WINDOW_CHARS = 11000
RHO = 0.45
S_CONG = 25.2
WALL = 3600.0
ARMS = [("feedback", ALPHA_FEEDBACK), ("control", 0.0)]


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


def clean_fill(items, rng) -> str:
    """Pre-fill: clean 'Fact: ... answer.' lines to the window cap."""
    order = list(range(len(items)))
    rng.shuffle(order)
    lines = []
    total = 0
    i = 0
    while total < WINDOW_CHARS + 200:
        it = items[order[i % len(order)]]
        ln = f"{it['prompt'].rstrip()} {it['answer']}.\n"
        lines.append(ln)
        total += len(ln)
        i += 1
    return ("".join(lines))[-WINDOW_CHARS:]


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


def exo_schedule(items, seed):
    """Pre-generated (arrival_offset, item_index) schedule, shared by BOTH
    arms of a seed (paired design: identical exo stream)."""
    rng = random.Random(7800 + seed)
    lam = RHO / S_CONG
    t, out = 0.0, []
    while t < WALL:
        t += rng.expovariate(lam)
        out.append((t, rng.randrange(len(items))))
    return out


class Rig:
    def __init__(self, c, band, items, seed, arm, alpha, log):
        self.c, self.band, self.items = c, band, items
        self.rng = random.Random(7000 + 100 * seed + (0 if alpha else 1))
        self.seed, self.arm, self.alpha = seed, arm, alpha
        self.log = log
        self.window = clean_fill(items, random.Random(7900 + seed))
        self.queue: list[Task] = []
        self.tid = 0
        self.kids: dict[int, int] = {}
        self.junk: list[float] = []
        self.queue_after: list[int] = []

    def new_tid(self):
        self.tid += 1
        return self.tid

    def serve_one(self, task):
        c = self.c
        prompt = self.window + "\n" + task.prompt()
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
        if (uncert and self.alpha > 0 and task.depth < MAX_DEPTH
                and self.kids.get(task.root, 0) < MAX_PER_ROOT):
            n = min(poisson(self.rng, self.alpha),
                    MAX_PER_ROOT - self.kids.get(task.root, 0))
            self.kids[task.root] = self.kids.get(task.root, 0) + n
            for _ in range(n):
                self.queue.append(Task(
                    self.new_tid(), "repair", task.item, time.time(),
                    time.time() + T_D, root=task.root,
                    depth=task.depth + 1, prev_answer=first))
        self.window = (self.window + task.prompt() + first + "\n")[-WINDOW_CHARS:]
        self.junk.append(1.0 if (not ok or task.depth > 0) else 0.0)
        self.queue_after.append(len(self.queue))
        self.log.write({
            "exp": "e7", "seed": self.seed, "arm": self.arm,
            "tid": task.tid, "kind": task.kind, "depth": task.depth,
            "certified": cert["certified"], "rank": cert["best_rank"],
            "correct": ok, "late": late, "uncert": uncert,
            "service_s": round(dur, 2), "queue_after": len(self.queue),
            "ctx_tokens": sl["seq_len"], "text": first[:50],
        })

    def dwell(self, schedule):
        t0 = time.time()
        pending = [(t0 + dt, idx) for dt, idx in schedule]
        n = 0
        while time.time() < t0 + WALL:
            now = time.time()
            while pending and pending[0][0] <= now:
                arr, idx = pending.pop(0)
                self.queue.append(Task(self.new_tid(), "exo",
                                       self.items[idx], arr, arr + T_D))
            if not self.queue:
                time.sleep(0.25)
                continue
            self.serve_one(self.queue.pop(0))
            n += 1
            if n % 20 == 0:
                print(f"  [{self.arm} s{self.seed}] served={n} "
                      f"q={len(self.queue)} "
                      f"t={time.time() - t0:.0f}/{WALL:.0f}s", flush=True)
        return n


def done_arms(path: Path) -> set:
    done = set()
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("exp") == "e7" and r.get("arm_done"):
                done.add((r["seed"], r["arm"]))
    return done


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(HERE / "runs" / "e7_precursors.jsonl"))
    args = ap.parse_args()

    c = JLensClient(port=args.port)
    c.require_n1000()
    sl = c.slice("Fact: The capital of France is", top_n=5)
    band = band_layers(sl["layers"])
    items, _ = filter_single_token(c, load_probe_swap())
    print(f"band {band[0]}..{band[-1]}; battery {len(items)}")

    log = RunLog(args.out)
    skip = done_arms(Path(args.out))
    schedule = exo_schedule(items, args.seed)
    print(f"exo schedule: {len(schedule)} arrivals over {WALL:.0f}s (paired)")
    for arm, alpha in ARMS:
        if (args.seed, arm) in skip:
            print(f"=== {arm.upper()} seed {args.seed}: already done, skip ===")
            continue
        print(f"=== E7 {arm.upper()} seed {args.seed} "
              f"(alpha={alpha}, rho={RHO}, wall={WALL:.0f}s) ===")
        rig = Rig(c, band, items, args.seed, arm, alpha, log)
        n = rig.dwell(schedule)
        summ = arm_summary(rig.junk, rig.queue_after)
        log.write({"exp": "e7", "seed": args.seed, "arm": arm,
                   "arm_done": True, "served": n, **summ})
        print(f"  ARM SUMMARY {arm} s{args.seed}: {summ}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
