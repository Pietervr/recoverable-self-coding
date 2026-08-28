"""E9 — cusp-map spot-checks on the rig (overnight). Predictions
committed first: runs/e9_spots_prediction.json (modal verdicts IGNITED /
CALM / EXIT / PINNED at 81-87%).

Four phases, fresh rig state per spot (independent, as the predictor):
  S1 up   T_d=33  alpha=0.8 rho=0.65 clean-prefilled  -> IGNITED
  S2 up   T_d=132 alpha=0.8 rho=0.65 clean-prefilled  -> CALM
  S3 down T_d=66  ignite at alpha 0.8, then QUENCH alpha to 0.2,
          rho=0.55, 2100 s                            -> EXIT
  S4 down T_d=66  ignite at alpha 0.8, keep alpha 0.8,
          rho=0.55, 2100 s                            -> PINNED

Up spots: IGNITED iff backlog ever >= 25 (early stop); CALM otherwise
after 2100 s. Down spots: E6 slope verdict on the measurement phase.
Resume: spots with a verdict record are skipped.

Run:  python3 e9_rig_spots.py [--seed 0]
Logs: runs/e9_spots.jsonl + runs/e9_spots_verdicts.json
"""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

from harness.battery import filter_single_token, graded, load_probe_swap
from harness.certify import band_layers, certified
from harness.client import JLensClient
from harness.runlog import RunLog
from e7_precursors_dwell import Task, clean_fill, poisson

HERE = Path(__file__).parent

MAX_DEPTH = 4
MAX_PER_ROOT = 10
WINDOW_CHARS = 11000
LAM_UNIT = 1 / 10.95
EXO = 12
DWELL_WALL = 480.0
S_CONG = 25.2
WALL = 2100.0
IGNITE_Q = 25
IGNITE_LS = [0.60, 0.75, 0.85, 0.95, 1.05, 1.05]
SPOTS = [
    ("S1_up_td33", "up", 33.0, 0.8, 0.65),
    ("S2_up_td132", "up", 132.0, 0.8, 0.65),
    ("S3_down_quench02", "down", 66.0, 0.2, 0.55),
    ("S4_down_a08", "down", 66.0, 0.8, 0.55),
]


class Rig:
    def __init__(self, c, band, items, seed, spot, td, log, prefill):
        self.c, self.band, self.items = c, band, items
        self.rng = random.Random(9100 + seed)
        self.seed, self.spot, self.td = seed, spot, td
        self.log = log
        self.alpha = 0.8
        self.phase = "init"
        self.window = (clean_fill(items, random.Random(9200 + seed))
                       if prefill else "")
        self.queue: list[Task] = []
        self.tid = 0
        self.kids: dict[int, int] = {}

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
        if (uncert and self.alpha > 0 and task.depth < MAX_DEPTH
                and self.kids.get(task.root, 0) < MAX_PER_ROOT):
            n = min(poisson(self.rng, self.alpha),
                    MAX_PER_ROOT - self.kids.get(task.root, 0))
            self.kids[task.root] = self.kids.get(task.root, 0) + n
            for _ in range(n):
                self.queue.append(Task(
                    self.new_tid(), "repair", task.item, time.time(),
                    time.time() + self.td, root=task.root,
                    depth=task.depth + 1, prev_answer=first))
        self.window = (self.window + task.prompt() + first + "\n")[-WINDOW_CHARS:]
        self.log.write({
            "exp": "e9", "seed": self.seed, "spot": self.spot,
            "phase": self.phase, "tid": task.tid, "kind": task.kind,
            "depth": task.depth, "certified": cert["certified"],
            "rank": cert["best_rank"], "correct": ok, "late": late,
            "uncert": uncert, "service_s": round(dur, 2),
            "queue_after": len(self.queue), "ctx_tokens": sl["seq_len"],
            "text": first[:50],
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
                                       arr, arr + self.td))
            if not self.queue:
                if pending:
                    time.sleep(min(0.25, max(0.01, pending[0] - now)))
                continue
            if now > dwell_t0 + DWELL_WALL and not pending:
                break
            u += self.serve_one(self.queue.pop(0))
            n += 1
        print(f"  [{self.spot}/{self.phase}] l={l:.2f} served={n} "
              f"P_u={u / max(1, n):.2f} backlog={len(self.queue)}",
              flush=True)

    def continuous(self, rho, wall, stop_on_ignite=False):
        rng = self.rng
        lam = rho / S_CONG
        t0 = time.time()
        t_a = t0
        arrivals = []
        while t_a < t0 + wall:
            t_a += rng.expovariate(lam)
            arrivals.append(t_a)
        while time.time() < t0 + wall:
            now = time.time()
            while arrivals and arrivals[0] <= now:
                arr = arrivals.pop(0)
                self.queue.append(Task(self.new_tid(), "exo",
                                       self.items[rng.randrange(len(self.items))],
                                       arr, arr + self.td))
            if not self.queue:
                time.sleep(0.25)
                continue
            self.serve_one(self.queue.pop(0))
            if stop_on_ignite and len(self.queue) >= IGNITE_Q:
                return "IGNITED"
        return None


def done_spots(path: Path, seed: int) -> set:
    done = set()
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (r.get("exp") == "e9" and r.get("seed") == seed
                    and r.get("verdict")):
                done.add(r["spot"])
    return done


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(HERE / "runs" / "e9_spots.jsonl"))
    args = ap.parse_args()

    c = JLensClient(port=args.port)
    c.require_n1000()
    sl = c.slice("Fact: The capital of France is", top_n=5)
    band = band_layers(sl["layers"])
    items, _ = filter_single_token(c, load_probe_swap())
    print(f"band {band[0]}..{band[-1]}; battery {len(items)}", flush=True)

    log = RunLog(args.out)
    skip = done_spots(Path(args.out), args.seed)
    verdicts = {}
    for spot, kind, td, alpha, rho in SPOTS:
        if spot in skip:
            print(f"=== {spot}: already done, skip ===", flush=True)
            continue
        print(f"=== E9 {spot} (kind={kind} T_d={td:.0f} alpha={alpha} "
              f"rho={rho}) ===", flush=True)
        rig = Rig(c, band, items, args.seed, spot, td, log,
                  prefill=(kind == "up"))
        if kind == "up":
            rig.alpha = alpha
            rig.phase = "up"
            v = rig.continuous(rho, WALL, stop_on_ignite=True) or "CALM"
        else:
            rig.alpha = 0.8
            rig.phase = "ignite"
            for l in IGNITE_LS:
                rig.burst_dwell(l)
                if len(rig.queue) >= IGNITE_Q:
                    break
            if len(rig.queue) < 8:
                v = "VOID"
            else:
                rig.alpha = alpha
                rig.phase = "measure"
                b0 = len(rig.queue)
                rig.continuous(rho, WALL)
                b1 = len(rig.queue)
                if b1 <= 0.7 * b0:
                    v = "EXIT"
                elif b1 >= b0:
                    v = "PINNED"
                else:
                    v = "AMBIG"
        verdicts[spot] = v
        log.write({"exp": "e9", "seed": args.seed, "spot": spot,
                   "verdict": v})
        print(f"  VERDICT {spot}: {v}", flush=True)
    print("\nE9 SPOT VERDICTS:", verdicts, flush=True)
    print("PREDICTED: S1 IGNITED / S2 CALM / S3 EXIT / S4 PINNED",
          flush=True)
    out_p = HERE / "runs" / "e9_spots_verdicts.json"
    old = json.loads(out_p.read_text()) if out_p.exists() else {}
    old[str(args.seed)] = verdicts
    out_p.write_text(json.dumps(old, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
