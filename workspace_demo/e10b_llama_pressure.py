"""E10b — Llama second-architecture test under SUSTAINED pressure,
committed BEFORE the run. Follow-up to E10 attempt 4 (f80a06f), which
scored P1 FAILED at the pre-registered burst coordinates and localized
the mechanism: post-cap exo tasks serve uncached (~6.2 s) but REPAIR
OFFSPRING ride Ollama's prefix cache (sub-second) — the cascade's
re-entrant work is nearly free, so its branching stays subcritical and
bursts drain even at burst-rho ~1.2. The control arm never left the
cached regime (0.35 s flat; its window never capped), so the burst
protocol's load comparison was regime-confounded.

Protocol (E6/E7-style continuous phases; both arms pre-capped):
  - PRE-FILL both arms' windows to the char cap with clean battery
    lines (both arms start in the uncached-exo regime — removes the
    attempt-4 confound).
  - in-loop anchor: 12-task probe at rho ~0.5 on the pre-filled window
    -> s_anchor = median measured service; T_d = 2.62 * s_anchor.
  - phases: continuous Poisson arrivals, 1500 s each, ascending
    rho in {0.60, 0.80, 0.95}; verdict per phase from backlog slope
    (queue at phase end vs start) + P_u.
  - arms: feedback (alpha = 0.8) then control (alpha = 0).

Committed two-branch prediction (the experiment is decisive either way):
  BRANCH A (collapse transfers): the feedback arm shows runaway backlog
    growth (B_end >= 25) at rho <= 0.95 while the control stays bounded
    — the E4 physics on a second architecture.
  BRANCH B (the cache mitigation holds): even under sustained
    supra-threshold pressure the repair discount keeps the cascade
    subcritical — feedback tracks control on backlog (both bounded
    below rho ~1), and the boundary-condition finding hardens:
    collapse transfer requires the serving stack to charge full price
    for re-entrant work (prefix caching = a load-side gate, the dual
    of certification on the content side).
  Scored by: whether feedback B_end >= 25 in any phase with control
  bounded (< 12) at the same rho.

Run:  python3 e10b_llama_pressure.py [--seed 0]
Logs: runs/e10b_llama.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

from harness.battery import graded, load_probe_swap
from harness.runlog import RunLog
from e7_precursors_dwell import Task, clean_fill, poisson
from e10_llama_loop import ollama_generate, MAX_DEPTH, MAX_PER_ROOT, WINDOW_CHARS

HERE = Path(__file__).parent

THETA = 2.62
PROBE_N = 12
PHASES = [0.60, 0.80, 0.95]
PHASE_WALL = 1500.0
RUNAWAY_B = 25
BOUNDED_B = 12


class Rig:
    def __init__(self, items, seed, arm, alpha, log, lam_unit, t_d):
        self.items = items
        self.rng = random.Random(11000 + 100 * seed + (0 if alpha else 1))
        self.seed, self.arm, self.alpha = seed, arm, alpha
        self.log = log
        self.lam_unit, self.t_d = lam_unit, t_d
        self.window = clean_fill(items, random.Random(11900 + seed))
        self.queue: list[Task] = []
        self.tid = 0
        self.kids: dict[int, int] = {}
        self.phase = "probe"

    def new_tid(self):
        self.tid += 1
        return self.tid

    def serve_one(self, task):
        prompt = self.window + "\n" + task.prompt()
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
            "exp": "e10b", "seed": self.seed, "arm": self.arm,
            "phase": self.phase, "tid": task.tid, "kind": task.kind,
            "depth": task.depth, "correct": ok, "late": late,
            "uncert": uncert, "service_s": round(dur, 2),
            "queue_after": len(self.queue), "text": first[:50],
        })
        return dur, uncert

    def pressure_phase(self, rho, wall):
        rng = self.rng
        lam = rho * self.lam_unit
        t0 = time.time()
        t_a = t0
        arrivals = []
        while t_a < t0 + wall:
            t_a += rng.expovariate(lam)
            arrivals.append(t_a)
        b0 = len(self.queue)
        n = u = 0
        while time.time() < t0 + wall:
            now = time.time()
            while arrivals and arrivals[0] <= now:
                arr = arrivals.pop(0)
                self.queue.append(Task(self.new_tid(), "exo",
                                       self.items[rng.randrange(len(self.items))],
                                       arr, arr + self.t_d))
            if not self.queue:
                time.sleep(0.2)
                continue
            _, uc = self.serve_one(self.queue.pop(0))
            u += uc
            n += 1
            if len(self.queue) >= RUNAWAY_B:
                break                      # runaway; stop the phase early
        b1 = len(self.queue)
        self.log.write({"exp": "e10b", "seed": self.seed, "arm": self.arm,
                        "phase_done": True, "rho": rho, "served": n,
                        "p_u": round(u / max(1, n), 3),
                        "b_start": b0, "b_end": b1})
        print(f"  [{self.arm}] rho={rho:.2f} served={n} "
              f"P_u={u / max(1, n):.2f} B {b0}->{b1}", flush=True)
        return b1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(HERE / "runs" / "e10b_llama.jsonl"))
    args = ap.parse_args()

    items = load_probe_swap()
    log = RunLog(args.out)
    print(f"battery {len(items)}", flush=True)

    for arm, alpha in [("feedback", 0.8), ("control", 0.0)]:
        rig = Rig(items, args.seed, arm, alpha, log, 0.0, 60.0)
        # in-loop anchor probe: serve PROBE_N tasks back-to-back on the
        # pre-filled window (uncached-exo regime), median -> s_anchor
        svcs = []
        rng_p = random.Random(11700 + args.seed)
        rig.phase = "probe"
        for _ in range(PROBE_N):
            it = items[rng_p.randrange(len(items))]
            t = Task(rig.new_tid(), "exo", it, time.time(),
                     time.time() + 600.0)
            dur, _ = rig.serve_one(t)
            svcs.append(dur)
        s_anchor = sorted(svcs)[len(svcs) // 2]
        rig.lam_unit = 1.0 / s_anchor
        rig.t_d = round(THETA * s_anchor, 1)
        print(f"=== E10b {arm.upper()} anchored s={s_anchor:.2f}s "
              f"T_d={rig.t_d:.1f}s ===", flush=True)
        log.write({"exp": "e10b", "seed": args.seed, "arm": arm,
                   "anchor": True, "s_anchor": round(s_anchor, 2),
                   "t_d": rig.t_d})
        runaway = None
        for rho in PHASES:
            rig.phase = f"rho{rho:.2f}"
            b1 = rig.pressure_phase(rho, PHASE_WALL)
            if b1 >= RUNAWAY_B:
                runaway = rho
                print(f"  RUNAWAY at rho={rho:.2f}", flush=True)
                break
        log.write({"exp": "e10b", "seed": args.seed, "arm": arm,
                   "arm_done": True, "runaway_at": runaway,
                   "final_backlog": len(rig.queue)})
        print(f"  ARM DONE {arm}: runaway_at={runaway}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
