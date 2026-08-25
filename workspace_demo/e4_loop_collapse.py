"""E4 — loop-level collapse with GENUINE load feedback (the decisive one).

E1/E2b/E2c established that no context-borne or in-pass drive can open the
collapse channel inside a single inference pass (recoverability there is
architecturally enforced), and E2 established that the CONTENT channel of
re-entry degrades with dose. The paper's closure (Sec. IV) models the LOAD
channel: each uncertified commitment consumed downstream as further work.
E4 closes that loop for real, on the pattern of the paper's instrumented
pipeline experiment (Sec. IV.F), with the LLM as the single worker and the
workspace lens as the per-commitment certification instrument:

  - Exogenous tasks (two-hop questions, ground truth known) arrive as a
    Poisson stream in WALL-CLOCK time at utilization l = lambda/mu_cong,
    ramped up in steps and then symmetrically down.
  - The single worker serves FIFO; service is genuine model compute
    (workspace slice + greedy answer on a sliding ~2.8k-token context
    window = the flux-borne operating state).
  - A task is UNCERTIFIED if its answer is wrong OR it completes past its
    wall-clock deadline T_d = theta * s_cong. On the feedback arm
    (alpha=0.8) an uncertified completion spawns Poisson(alpha) REPAIR
    tasks whose prompts literally re-consume the uncertified answer
    ("It was recorded that ... is <wrong>. In fact, ... is") -- real
    offspring work into the same queue, genealogy-tagged. The control arm
    (alpha=0) is identical with no offspring.
  - The QUEUE is the backlog (the theory's memory variable); the WINDOW is
    the trajectory-carried content. Both are logged per task, along with
    workspace certification (band top-10 of the item's intermediate,
    tail-160 readout), rank, correctness, lateness, service time, and
    genealogy.
  - After the down-ramp, the reset discriminator on the alpha arm, both
    cures probed under NORMAL operation (spawning on) at the low
    utilization: (a) context-clear with the queue INTACT; (b) queue-drain
    with the window kept DIRTY. If (b) recovers and (a) does not, the
    memory variable is the backlog, not the content.

Pre-registered predictions (P) and falsifiers (F), stated before the run:
  P1L collapse: the alpha=0.8 up-ramp shows a discontinuous transition --
      backlog runaway + uncertified fraction -> 1 at some l_c < 1 -- while
      the alpha=0 arm degrades continuously with no runaway below l ~ 1.
      F1L: the arms are indistinguishable -> load feedback adds nothing
      measurable at this scale.
  P2L hysteresis: the alpha=0.8 down-ramp stays collapsed below l_c while
      the backlog persists, recovering only at l_rec < l_c.
      F2L: recovery at the collapse point (no hysteresis) -- the E2
      negative extends to the loop level and the paper's LLM-pipeline
      claim is in real trouble. THIS is the decisive falsifier.
  P3L the memory variable: at the pinned collapsed state, context-clear
      alone (queue intact) does NOT restore certified operation;
      draining the queue does.
      F3L: context-clear alone cures -> the memory is content, not
      backlog -> the closure's mechanism is misidentified for LLM loops.
  P4L the SR channel: workspace certification (rate and/or determinant
      rank) degrades with congestion -- corrupted, error-laden context
      contesting the determinants -- the first regime where the
      mechanistic SR channel could open.
      F4L: certification stays at ceiling through full collapse -> the
      behavioral SR (uncertified fraction) carries the transition alone.
      Either way informative.
  P5L exploratory: offspring genealogies near collapse are heavy-tailed
      (no tau=3/2 claim at this n).

Runtime bounds (logged, never silent): offspring depth <= 4 and <= 10 per
root; dwell wall cap 8 min; arm wall cap 2.6 h (truncation logged).

Run:  python3 e4_loop_collapse.py [--alpha 0.8] [--seed 0]
Logs: runs/e4_loop.jsonl + per-dwell summary lines on the console.
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

THETA = 6.0            # deadline depth: T_d = THETA * mean congested service
RAMP_UP = [0.40, 0.60, 0.75, 0.85, 0.95, 1.05]
EXO_PER_DWELL = 12
WINDOW_CHARS = 11000   # ~2.8k tokens of flux-borne operating state
DWELL_WALL_MAX = 480.0
ARM_WALL_MAX = 9360.0
MAX_DEPTH = 4
MAX_OFFSPRING_PER_ROOT = 10
QLEN_NOTE = 60         # backlog level reported as collapsed (no behavior change)


def poisson(rng: random.Random, lam: float) -> int:
    if lam <= 0:
        return 0
    l_exp, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= l_exp:
            return k
        k += 1


def clause_of(item: dict) -> str:
    p = item["prompt"].strip()
    body = p[5:].strip() if p.lower().startswith("fact:") else p
    return body[0].lower() + body[1:]


class Task:
    __slots__ = ("tid", "kind", "item", "arrival", "deadline", "parent",
                 "root", "depth", "prev_answer", "text")

    def __init__(self, tid, kind, item, arrival, deadline,
                 parent=None, root=None, depth=0, prev_answer=None):
        self.tid, self.kind, self.item = tid, kind, item
        self.arrival, self.deadline = arrival, deadline
        self.parent, self.depth = parent, depth
        self.root = root if root is not None else tid
        self.prev_answer = prev_answer
        self.text = None

    def prompt(self) -> str:
        if self.kind == "exo":
            return self.item["prompt"].rstrip()
        cl = clause_of(self.item)
        if cl.endswith(" is"):
            cl = cl[:-3]
        return (
            f"Fact check: it was recorded that {cl} is"
            f"{self.prev_answer} That may be wrong. In fact, {cl} is"
        )


def serve(c, band, window, task, top_k=10):
    prompt = (window + "\n" if window else "") + task.prompt()
    t0 = time.time()
    sl = c.slice(prompt, top_n=top_k, max_seq_len=4096, tail=160)
    toks = sl["token_strs"]
    off = sl.get("pos_offset", 0)
    start = 0
    for i, t in enumerate(toks):
        if "Fact" in t:
            start = i
    view = {
        "cells": {
            layer: {"top_tokens": cell["top_tokens"][max(0, start - off):]}
            for layer, cell in sl["cells"].items()
        }
    }
    cert = certified(view, [task.item["intermediate"]], band, top_k)
    text = c.generate(prompt, max_tokens=8)
    dur = time.time() - t0
    ok = graded(task.item, text)
    first = " " + text.strip().split("\n")[0][:80] if text.strip() else " ..."
    return cert, ok, first, dur, sl["seq_len"]


def calibrate(c, band, items, rng) -> tuple[float, float]:
    def mean_service(window: str, n: int) -> float:
        durs = []
        for i in range(n):
            t = Task(-1, "exo", items[(7 * i) % len(items)], 0.0, 1e18)
            _, _, _, dur, _ = serve(c, band, window, t)
            durs.append(dur)
        return sum(durs) / len(durs)

    clean = mean_service("", 6)
    filler_items = [items[(3 * i) % len(items)] for i in range(60)]
    win = ""
    for it in filler_items:
        win += it["prompt"].rstrip() + " " + it["answer"] + ".\n"
        if len(win) >= WINDOW_CHARS:
            break
    win = win[-WINDOW_CHARS:]
    cong = mean_service(win, 6)
    return clean, cong


def run_arm(c, band, items, alpha: float, seed: int, log: RunLog,
            s_cong: float) -> None:
    rng = random.Random(4000 + seed)
    mu = 1.0 / s_cong
    t_d = THETA * s_cong
    ramp = [("up", l) for l in RAMP_UP] + [("down", l) for l in RAMP_UP[-2::-1]]
    window = ""
    queue: list[Task] = []
    tid = 0
    root_children: dict[int, int] = {}
    arm_t0 = time.time()
    truncated = False

    def log_task(task, branch, l, step, cert, ok, late, dur, ctx, qlen):
        log.write({
            "exp": "e4", "alpha": alpha, "seed": seed, "branch": branch,
            "step": step, "l": l, "tid": task.tid, "kind": task.kind,
            "item": task.item["name"], "depth": task.depth,
            "root": task.root, "parent": task.parent,
            "certified": cert["certified"], "rank": cert["best_rank"],
            "correct": ok, "late": late, "uncert": (late or not ok),
            "service_s": round(dur, 2), "wait_s": round(time.time() - task.arrival - dur, 1),
            "queue_after": qlen, "ctx_tokens": ctx,
            "text": (task.text or "")[:60],
        })

    def serve_one(task, branch, l, step, allow_spawn=True) -> bool:
        nonlocal window, tid
        cert, ok, first, dur, ctx = serve(c, band, window, task)
        late = time.time() > task.deadline
        uncert = late or not ok
        task.text = first  # logged: the re-entrant line (mode forensics)
        window = (window + task.prompt() + first + "\n")[-WINDOW_CHARS:]
        if uncert and allow_spawn and alpha > 0 and task.depth < MAX_DEPTH:
            have = root_children.get(task.root, 0)
            n = poisson(rng, alpha)
            if have + n > MAX_OFFSPRING_PER_ROOT:
                print(f"    [cap] root {task.root} offspring capped")
                n = MAX_OFFSPRING_PER_ROOT - have
            root_children[task.root] = have + n
            for _ in range(n):
                tid += 1
                queue.append(Task(tid, "repair", task.item, time.time(),
                                  time.time() + t_d, parent=task.tid,
                                  root=task.root, depth=task.depth + 1,
                                  prev_answer=first))
        log_task(task, branch, l, step, cert, ok, late, dur, ctx, len(queue))
        return uncert

    def run_dwell(branch, l, step, n_exo=EXO_PER_DWELL, spawn=True):
        """One dwell of NORMAL operation at utilization l: n_exo Poisson
        arrivals in wall-clock, FIFO service of whatever is in the queue
        (standing backlog first), spawning per the arm."""
        lam = l * mu
        dwell_t0 = time.time()
        t_a = dwell_t0
        pending = []
        for _ in range(n_exo):
            t_a += rng.expovariate(lam)
            pending.append(t_a)
        n_served = n_unc = 0
        while pending or (queue and time.time() < dwell_t0 + DWELL_WALL_MAX):
            now = time.time()
            while pending and pending[0] <= now:
                arr = pending.pop(0)
                tid_local = new_tid()
                queue.append(Task(tid_local, "exo",
                                  items[rng.randrange(len(items))],
                                  arr, arr + t_d))
            if not queue:
                if pending:
                    time.sleep(min(0.25, max(0.01, pending[0] - now)))
                continue
            if now > dwell_t0 + DWELL_WALL_MAX and not pending:
                break
            unc = serve_one(queue.pop(0), branch, l, step, allow_spawn=spawn)
            n_served += 1
            n_unc += unc
        note = " COLLAPSED" if len(queue) >= QLEN_NOTE else ""
        print(
            f"  a={alpha} {branch:>10} l={l:.2f} served={n_served} "
            f"P_u={n_unc / max(1, n_served):.2f} backlog={len(queue)} "
            f"dwell={time.time() - dwell_t0:.0f}s{note}"
        )

    def new_tid() -> int:
        nonlocal tid
        tid += 1
        return tid

    for step, (branch, l) in enumerate(ramp):
        if time.time() - arm_t0 > ARM_WALL_MAX:
            truncated = True
            print(f"  [TRUNCATED] arm wall cap at step {step} ({branch} l={l})")
            break
        run_dwell(branch, l, step)

    if alpha > 0:
        # Reset discriminator at the low operating point: two cures compared
        # under NORMAL operation (spawning on), differing only in what was
        # cleared. A: content cleared, backlog kept. B: backlog drained,
        # content kept dirty. If B recovers and A does not, the memory
        # variable is the backlog, not the content.
        l_probe = RAMP_UP[0]
        print(f"  reset A: context CLEARED, queue intact ({len(queue)})")
        window = ""
        run_dwell("reset_ctx", l_probe, 98, n_exo=10)
        print(f"  reset B: DRAIN (backlog {len(queue)}), window kept dirty")
        drain_t0 = time.time()
        while queue and time.time() - drain_t0 < 1200:
            serve_one(queue.pop(0), "drain", l_probe, 99)
        if queue:
            print(f"    [cap] drain wall cap hit with backlog {len(queue)}")
            queue.clear()
        run_dwell("reset_drain", l_probe, 100, n_exo=10)
    print(f"  arm alpha={alpha} done (truncated={truncated})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--alpha", type=float, default=None,
                    help="run only this arm (default: 0.8 then 0.0)")
    ap.add_argument("--out", default=str(HERE / "runs" / "e4_loop.jsonl"))
    args = ap.parse_args()

    c = JLensClient(port=args.port)
    c.require_n1000()
    sl = c.slice("Fact: The capital of France is", top_n=5)
    band = band_layers(sl["layers"])
    items, _ = filter_single_token(c, load_probe_swap())
    print(f"band {band[0]}..{band[-1]}; battery {len(items)} items")

    rng = random.Random(1)
    s_clean, s_cong = calibrate(c, band, items, rng)
    print(f"calibration: s_clean={s_clean:.2f}s s_cong={s_cong:.2f}s "
          f"T_d={THETA * s_cong:.0f}s")

    log = RunLog(args.out)
    done_arms = {r.get("alpha") for r in log.records() if r.get("branch") == "reset_drain"} | \
                {r.get("alpha") for r in log.records()
                 if r.get("alpha") == 0.0 and r.get("branch") == "down" and r.get("l") == RAMP_UP[0]}
    arms = [args.alpha] if args.alpha is not None else [0.8, 0.0]
    for a in arms:
        if a in done_arms:
            print(f"arm alpha={a} already complete; skipping")
            continue
        print(f"=== arm alpha={a} seed={args.seed} ===")
        run_arm(c, band, items, a, args.seed, log, s_cong)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
