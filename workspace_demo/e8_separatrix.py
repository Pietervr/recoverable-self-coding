"""E8 — the separatrix (basin boundary) on the rig, graded compound
shocks from the collapsed state. Prediction committed first in
e8_predict.py (sequential protocol, state carried between arms).

Protocol (the predictor verbatim):
  1. IGNITE via the E4 burst ramp (alpha = 0.8, T_d = 66), stop when
     backlog >= 25.
  2. Arms in ARM_SEQ order. Before each: re-ignite (two 1.05 bursts)
     if backlog < 8; HOLD 480 s continuous arrivals at rho = 0.35
     (deep in the wedge); VOID the arm if not collapsed after the hold.
  3. SHOCK: drop each queued task with prob f_b; replace the NEWEST
     f_j fraction of the window (the tail of the string) with clean
     battery lines.
  4. VERDICT: 1500 s continuous arrivals at rho = 0.35; E6 slope rule,
     base = max(8, B_after_shock): EXIT <= 0.7 base; PINNED >= base.

Committed prediction (200 sequential model replicas): P(EXIT|f)
0.21/0.18/0.31/0.55/0.95, separatrix f* = 0.75; ordering window_only
0.15 < backlog_only 0.61 < compound 0.95. Falsifier: no monotone
boundary, or an axis shock matching the compound.

Resume: arms with a verdict record in the log are skipped (the
re-ignite + hold re-establishes the collapsed state after a restart).

Run:  python3 e8_separatrix.py [--seed 0]
Logs: runs/e8_separatrix.jsonl + runs/e8_verdicts.json
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
from e7_precursors_dwell import Task, clause_of, clean_fill, poisson

HERE = Path(__file__).parent

T_D = 66.0
ALPHA = 0.8
MAX_DEPTH = 4
MAX_PER_ROOT = 10
WINDOW_CHARS = 11000
LAM_UNIT = 1 / 10.95
EXO = 12
DWELL_WALL = 480.0
S_CONG = 25.2
RHO_HOLD = 0.35
HOLD_S = 480.0
VERDICT_S = 1500.0
IGNITE_LS = [0.60, 0.75, 0.85, 0.95, 1.05, 1.05]
REIGNITE_LS = [1.05, 1.05]
ARM_SEQ = [("compound_0.00", 0.0, 0.0), ("compound_0.25", 0.25, 0.25),
           ("window_only", 0.0, 1.0), ("compound_0.50", 0.5, 0.5),
           ("compound_0.75", 0.75, 0.75), ("backlog_only", 1.0, 0.0),
           ("compound_1.00", 1.0, 1.0)]


class Rig:
    def __init__(self, c, band, items, seed, log):
        self.c, self.band, self.items = c, band, items
        self.rng = random.Random(8000 + seed)
        self.seed = seed
        self.log = log
        self.window = ""
        self.queue: list[Task] = []
        self.tid = 0
        self.kids: dict[int, int] = {}
        self.phase = "ignite"

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
        self.window = (self.window + task.prompt() + first + "\n")[-WINDOW_CHARS:]
        self.log.write({
            "exp": "e8", "seed": self.seed, "phase": self.phase,
            "tid": task.tid, "kind": task.kind, "depth": task.depth,
            "certified": cert["certified"], "rank": cert["best_rank"],
            "correct": ok, "late": late, "uncert": uncert,
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
        print(f"  [{self.phase}] l={l:.2f} served={n} "
              f"P_u={u / max(1, n):.2f} backlog={len(self.queue)}",
              flush=True)

    def continuous(self, wall):
        """Continuous Poisson arrivals at RHO_HOLD for wall seconds."""
        rng = self.rng
        lam = RHO_HOLD / S_CONG
        t0 = time.time()
        t_a = t0
        arrivals = []
        while t_a < t0 + wall:
            t_a += rng.expovariate(lam)
            arrivals.append(t_a)
        n = 0
        while time.time() < t0 + wall:
            now = time.time()
            while arrivals and arrivals[0] <= now:
                arr = arrivals.pop(0)
                self.queue.append(Task(self.new_tid(), "exo",
                                       self.items[rng.randrange(len(self.items))],
                                       arr, arr + T_D))
            if not self.queue:
                time.sleep(0.25)
                continue
            self.serve_one(self.queue.pop(0))
            n += 1
        return n

    def shock(self, f_b, f_j):
        if f_b > 0:
            self.queue = [t for t in self.queue
                          if self.rng.random() >= f_b]
        if f_j > 0:
            keep = int(len(self.window) * (1 - f_j))
            fill = clean_fill(self.items,
                              random.Random(8900 + self.seed + self.tid))
            self.window = (self.window[:keep]
                           + fill[:WINDOW_CHARS - keep])
        return len(self.queue)


def done_arms(path: Path, seed: int) -> set:
    done = set()
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (r.get("exp") == "e8" and r.get("seed") == seed
                    and r.get("verdict")):
                done.add(r["arm"])
    return done


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(HERE / "runs" / "e8_separatrix.jsonl"))
    args = ap.parse_args()

    c = JLensClient(port=args.port)
    c.require_n1000()
    sl = c.slice("Fact: The capital of France is", top_n=5)
    band = band_layers(sl["layers"])
    items, _ = filter_single_token(c, load_probe_swap())
    print(f"band {band[0]}..{band[-1]}; battery {len(items)}", flush=True)

    log = RunLog(args.out)
    skip = done_arms(Path(args.out), args.seed)
    rig = Rig(c, band, items, args.seed, log)
    print("=== IGNITION ===", flush=True)
    for l in IGNITE_LS:
        rig.phase = "ignite"
        rig.burst_dwell(l)
        if len(rig.queue) >= 25:
            break
    verdicts = {}
    for arm, f_b, f_j in ARM_SEQ:
        if arm in skip:
            print(f"=== {arm}: already done, skip ===", flush=True)
            continue
        if len(rig.queue) < 8:
            print("=== RE-IGNITION ===", flush=True)
            rig.phase = "ignite"
            for l in REIGNITE_LS:
                rig.burst_dwell(l)
        if len(rig.queue) < 8:
            verdicts[arm] = "VOID"
            log.write({"exp": "e8", "seed": args.seed, "arm": arm,
                       "verdict": "VOID", "why": "could not ignite"})
            continue
        rig.phase = f"hold_{arm}"
        rig.continuous(HOLD_S)
        if len(rig.queue) < 8:
            verdicts[arm] = "VOID"
            log.write({"exp": "e8", "seed": args.seed, "arm": arm,
                       "verdict": "VOID", "why": "not collapsed post-hold"})
            continue
        b_pre = len(rig.queue)
        b_shock = rig.shock(f_b, f_j)
        log.write({"exp": "e8", "seed": args.seed, "arm": arm,
                   "shock": True, "f_b": f_b, "f_j": f_j,
                   "b_pre": b_pre, "b_shock": b_shock})
        print(f"=== SHOCK {arm}: B {b_pre} -> {b_shock} ===", flush=True)
        rig.phase = f"verdict_{arm}"
        rig.continuous(VERDICT_S)
        b1 = len(rig.queue)
        base = max(8, b_shock)
        if b1 <= 0.7 * base:
            v = "EXIT"
        elif b1 >= base:
            v = "PINNED"
        else:
            v = "AMBIG"
        verdicts[arm] = v
        log.write({"exp": "e8", "seed": args.seed, "arm": arm,
                   "verdict": v, "b_shock": b_shock, "b_end": b1})
        print(f"  VERDICT {arm}: {v} (B {b_shock} -> {b1})", flush=True)
    print("\nE8 VERDICTS:", verdicts, flush=True)
    out_p = HERE / "runs" / "e8_verdicts.json"
    old = json.loads(out_p.read_text()) if out_p.exists() else {}
    old[str(args.seed)] = verdicts
    out_p.write_text(json.dumps(old, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
