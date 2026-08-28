"""E10 — lens-free loop-collapse replication on a SECOND MODEL FAMILY
(Llama-3.1-8B-Instruct q4, served by Ollama). Committed BEFORE the run.

Claim tested: the E4 collapse phenomenology is not a Qwen artifact.
No lens, no certification instrument — correctness (graded) + lateness
+ queue dynamics only, exactly the load-side observables.

Directional predictions (no reduced model is calibrated for Llama, so
these are structure-level, committed here):
  P1  the alpha = 0.8 arm collapses discontinuously at some l_c <= 1.05
      (a runaway dwell: P_u >= 0.9 with backlog growth, following dwells
      at moderate P_u);
  P2  hysteresis: after the runaway, down-branch dwells at l = 0.60 and
      0.40 stay pinned (backlog does not drain to < 8);
  P3  feedback-specificity: the alpha = 0 control arm shows NO runaway
      at any l <= 0.95 (continuous congestion at 1.05 allowed).
Falsifiers: no collapse anywhere on the feedback arm; or the control
arm collapses like the feedback arm; or down-branch drains freely.

Protocol (E4's shape, dimensionlessly calibrated to Llama):
  - calibrate: 8 empty-window tasks -> s_med_warm; LAM_UNIT = 1/s_med;
    T_d = 6.0 * s_med (E4: 66 s / 10.95 s = 6.03).
  - up-ramp burst dwells (EXO = 12, wall 480 s) at
    l = 0.40, 0.60, 0.75, 0.85, 0.95, 1.05; stop the ramp after a
    runaway dwell (P_u >= 0.9 and backlog > 5, or backlog >= 25).
  - down-branch dwells at l = 0.60, 0.40 (hysteresis probe).
  - arms: feedback (alpha = 0.8, spawn/depth/root caps as E4) then
    control (alpha = 0), fresh state per arm.
  - window 11000 chars, greedy decoding, 8-token answers, same battery
    and grading as E4 (single-token filtering skipped — lens-free).

Serving: Ollama /api/generate, stream=false, temperature 0,
num_predict 8, num_ctx 4096, keep_alive '2h'.

Run:  python3 e10_llama_loop.py [--seed 0]   (after the night chain —
      never concurrently with the jlens rig; both contend for the GPU)
Logs: runs/e10_llama.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import time
import urllib.request
from pathlib import Path

from harness.battery import graded, load_probe_swap
from harness.runlog import RunLog
from e7_precursors_dwell import Task, poisson

HERE = Path(__file__).parent

MODEL = "llama3.1:8b"
OLLAMA = "http://localhost:11434/api/generate"
MAX_DEPTH = 4
MAX_PER_ROOT = 10
WINDOW_CHARS = 11000
EXO = 12
DWELL_WALL = 480.0
UP_LS = [0.40, 0.60, 0.75, 0.85, 0.95, 1.05]
DOWN_LS = [0.60, 0.40]
THETA_WARM = 6.0
CAL_N = 8


def ollama_generate(prompt: str) -> str:
    body = json.dumps({
        "model": MODEL, "prompt": prompt, "stream": False,
        "keep_alive": "2h",
        "options": {"num_predict": 8, "temperature": 0, "num_ctx": 4096},
    }).encode()
    req = urllib.request.Request(
        OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())["response"]


class Rig:
    def __init__(self, items, seed, arm, alpha, log, lam_unit, t_d):
        self.items = items
        self.rng = random.Random(10000 + 100 * seed + (0 if alpha else 1))
        self.seed, self.arm, self.alpha = seed, arm, alpha
        self.log = log
        self.lam_unit, self.t_d = lam_unit, t_d
        self.window = ""
        self.queue: list[Task] = []
        self.tid = 0
        self.kids: dict[int, int] = {}
        self.phase = "up"

    def new_tid(self):
        self.tid += 1
        return self.tid

    def serve_one(self, task):
        prompt = (self.window + "\n" if self.window else "") + task.prompt()
        t0 = time.time()
        text = ollama_generate(prompt)
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
                    time.time() + self.t_d, root=task.root,
                    depth=task.depth + 1, prev_answer=first))
        self.window = (self.window + task.prompt() + first + "\n")[-WINDOW_CHARS:]
        self.log.write({
            "exp": "e10", "seed": self.seed, "arm": self.arm,
            "phase": self.phase, "tid": task.tid, "kind": task.kind,
            "depth": task.depth, "correct": ok, "late": late,
            "uncert": uncert, "service_s": round(dur, 2),
            "queue_after": len(self.queue), "text": first[:50],
        })
        return uncert

    def burst_dwell(self, l):
        rng = self.rng
        lam = l * self.lam_unit
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
                                       arr, arr + self.t_d))
            if not self.queue:
                if pending:
                    time.sleep(min(0.25, max(0.01, pending[0] - now)))
                continue
            if now > dwell_t0 + DWELL_WALL and not pending:
                break
            u += self.serve_one(self.queue.pop(0))
            n += 1
        pu = u / max(1, n)
        b = len(self.queue)
        self.log.write({"exp": "e10", "seed": self.seed, "arm": self.arm,
                        "dwell_done": True, "phase": self.phase, "l": l,
                        "served": n, "p_u": round(pu, 3), "backlog": b})
        print(f"  [{self.arm}/{self.phase}] l={l:.2f} served={n} "
              f"P_u={pu:.2f} backlog={b}", flush=True)
        return pu, b


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(HERE / "runs" / "e10_llama.jsonl"))
    args = ap.parse_args()

    items = load_probe_swap()
    print(f"battery {len(items)} (unfiltered, lens-free)", flush=True)
    log = RunLog(args.out)

    # calibration: empty-window warm service
    svcs = []
    rng_c = random.Random(10700 + args.seed)
    for _ in range(CAL_N):
        it = items[rng_c.randrange(len(items))]
        t0 = time.time()
        ollama_generate(it["prompt"].rstrip())
        svcs.append(time.time() - t0)
    s_med = sorted(svcs)[len(svcs) // 2]
    lam_unit = 1.0 / s_med
    t_d = round(THETA_WARM * s_med, 1)
    print(f"calibrated: s_med={s_med:.2f}s T_d={t_d:.1f}s", flush=True)
    log.write({"exp": "e10", "seed": args.seed, "calibration": True,
               "s_med": round(s_med, 2), "t_d": t_d,
               "services": [round(s, 2) for s in svcs]})

    for arm, alpha in [("feedback", 0.8), ("control", 0.0)]:
        print(f"=== E10 {arm.upper()} (alpha={alpha}) ===", flush=True)
        rig = Rig(items, args.seed, arm, alpha, log, lam_unit, t_d)
        runaway_at = None
        rig.phase = "up"
        for l in UP_LS:
            pu, b = rig.burst_dwell(l)
            if (pu >= 0.9 and b > 5) or b >= 25:
                runaway_at = l
                print(f"  RUNAWAY at l={l:.2f}", flush=True)
                break
        rig.phase = "down"
        for l in DOWN_LS:
            rig.burst_dwell(l)
        log.write({"exp": "e10", "seed": args.seed, "arm": arm,
                   "arm_done": True, "runaway_at": runaway_at,
                   "final_backlog": len(rig.queue)})
        print(f"  ARM DONE {arm}: runaway_at={runaway_at} "
              f"final_backlog={len(rig.queue)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
