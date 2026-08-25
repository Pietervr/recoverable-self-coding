"""E5 — EMERGENT alpha: the operating loop with a self-verification policy.

E4 injected the feedback kernel (Poisson(0.8) offspring), like the paper's
pipeline rig. E5 removes the injection: the deployment carries a realistic
RETRY POLICY, and the re-consumption rate emerges from the model's own
judgments. Per task:

  1. the worker answers (workspace slice + greedy completion), then
  2. SELF-CHECKS in a second pass: "is that answer correct? yes/no", then
  3. policy ON:  a rejection re-queues ONE retry (the flagged answer
     visible in the retry prompt — real re-consumption), max 2 retries
     per original task (a realistic bounded-retry policy);
     policy OFF: the check still runs and is logged (service-matched
     control), but nothing re-queues.

NOTHING sets alpha: the branching ratio b = P(reject) per served task is
an emergent, congestion-dependent property of the deployment — the
completion Sec. IV.F's scope paragraph calls for, at bench scale. The
self-check is simultaneously an ENDOGENOUS certification gate: with
ground truth known, its coverage q = P(reject | wrong) and false-alarm
rate P(reject | correct) are measured per congestion state — the
certifier-inherits-its-own-feasibility-constraint claim, instrumented.

Protocol otherwise mirrors E4: wall-clock Poisson arrivals at utilization
l ramped 0.40..1.05 up then down; FIFO; sliding ~2.8k-token window;
deadline T_d = theta * s_cong with theta = 3.0 (design constant, chosen
to match E4's effective tightness ~2.7; s_cong measured in calibration
over VARIED prefilled windows to avoid the warm-cache bias E4's
calibration suffered). Uncertified (physics bookkeeping) = wrong OR late,
as in E4; the VETO (the system's own signal) is logged separately.

PREDICT-THEN-MEASURE: before any ramp runs, the calibration mode
(--calibrate) measures the double-pass service law and the veto rates on
clean and junk-prefilled windows; the reduced-model machinery then
predicts the collapse point IN ADVANCE and the prediction is committed
to git before the ramp starts (e5_predict.py). Pre-registered:

  P1E b rises with congestion (the convex kernel, measured not imposed).
  P2E the committed reduced-model prediction brackets the measured
      runaway (or its absence) — theory computing an emergent system.
  P3E if the emergent policy is sub-critical (no collapse below l=1),
      that is reported as such: the closure then PREDICTS which retry
      policies are safe — a designable-safety statement, not a failure.
  P4E gate degradation: coverage q falls and/or false alarms rise with
      window contamination (the endogenous certifier degrades exactly
      when it is most needed).

Run:  python3 e5_emergent.py --calibrate          (then e5_predict.py)
      python3 e5_emergent.py [--seed 0]           (both arms, atomic resume)
Logs: runs/e5_loop.jsonl, runs/e5_calibration.json
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

THETA = 3.0
RAMP_UP = [0.40, 0.60, 0.75, 0.85, 0.95, 1.05]
EXO_PER_DWELL = 12
WINDOW_CHARS = 11000
DWELL_WALL = 480.0
ARM_WALL_MAX = 10800.0
MAX_RETRIES = 2


def clause_of(item: dict) -> str:
    p = item["prompt"].strip()
    body = p[5:].strip() if p.lower().startswith("fact:") else p
    return body[0].lower() + body[1:]


class Task:
    __slots__ = ("tid", "item", "arrival", "deadline", "root", "depth",
                 "prev_answer", "text", "veto")

    def __init__(self, tid, item, arrival, deadline, root=None, depth=0,
                 prev_answer=None):
        self.tid, self.item = tid, item
        self.arrival, self.deadline = arrival, deadline
        self.root = root if root is not None else tid
        self.depth = depth
        self.prev_answer = prev_answer
        self.text = None
        self.veto = None

    def prompt(self) -> str:
        if self.depth == 0:
            return self.item["prompt"].rstrip()
        cl = clause_of(self.item)
        return (f"Fact (re-check; an earlier answer{self.prev_answer} was "
                f"flagged as possibly wrong): {cl[0].upper() + cl[1:]}")


CHECK_FEWSHOT = (
    "Fact check: the claim that the capital of France is Paris is true.\n"
    "Fact check: the claim that the number of legs on a dog is 7 is false.\n"
)


def check_prompt(item: dict, answer: str) -> str:
    """Few-shot verdict elicitation — the empirically selected variant
    (12/12 parse under clean AND junk windows; probe 2026-08-25). The
    two exemplars carry the format regardless of the live window's mode."""
    cl = clause_of(item)
    if cl.endswith(" is"):
        cl = cl[:-3]
    a = answer[:-1] if answer.endswith(".") else answer
    return CHECK_FEWSHOT + f"Fact check: the claim that {cl} is{a} is"


NEG = {"false", "no", "incorrect", "wrong"}
POS = {"true", "yes", "correct", "right"}


def parse_verdict(text: str) -> tuple[bool, bool]:
    """(reject, parseable). Think tags stripped; unparseable -> accept."""
    t = text.replace("<think>", " ").replace("</think>", " ")
    for tok in t.strip().lower().replace(".", " ").replace(",", " ").split():
        if tok in NEG:
            return True, True
        if tok in POS:
            return False, True
    return False, False


def serve(c, band, window, task, top_k=10):
    prompt = (window + "\n" if window else "") + task.prompt()
    t0 = time.time()
    sl = c.slice(prompt, top_n=top_k, max_seq_len=4096, tail=160)
    toks = sl["token_strs"]
    off = sl.get("pos_offset", 0)
    start = 0
    for i, t in enumerate(toks):
        if "Fact" in t or "Check" in t:
            start = i
    view = {
        "cells": {
            layer: {"top_tokens": cell["top_tokens"][max(0, start - off):]}
            for layer, cell in sl["cells"].items()
        }
    }
    cert = certified(view, [task.item["intermediate"]], band, top_k)
    text = c.generate(prompt, max_tokens=8)
    first = " " + text.strip().split("\n")[0][:80] if text.strip() else " ..."
    ctext = c.generate(
        (window + "\n" if window else "") + check_prompt(task.item, first),
        max_tokens=6)
    reject, parseable = parse_verdict(ctext)
    dur = time.time() - t0
    ok = graded(task.item, text)
    return cert, ok, first, reject, parseable, ctext[:20], dur, sl["seq_len"]


def build_junk_window(items, rng) -> str:
    out = ""
    while len(out) < WINDOW_CHARS:
        it = items[rng.randrange(len(items))]
        cl = clause_of(it)
        if cl.endswith(" is"):
            cl = cl[:-3]
        out += (f"Fact (re-check; an earlier answer {it['swap_answer']} was "
                f"flagged as possibly wrong): {cl[0].upper() + cl[1:]} is "
                f"{it['swap_answer']}.\n")
    return out[-WINDOW_CHARS:]


def calibrate(c, band, items) -> dict:
    """Double-pass service on VARIED windows (12 distinct prefills) + veto
    rates on clean vs junk windows. Writes runs/e5_calibration.json."""
    rng = random.Random(11)
    out: dict = {"service": [], "clean": [], "junk": []}
    # service on varied filled windows
    for k in range(12):
        win = ""
        while len(win) < WINDOW_CHARS:
            it = items[rng.randrange(len(items))]
            win += it["prompt"].rstrip() + " " + it["answer"] + ".\n"
        win = win[-WINDOW_CHARS:]
        t = Task(-1, items[(13 * k) % len(items)], 0.0, 1e18)
        _, ok, first, reject, parseable, ctext, dur, _ = serve(c, band, win, t)
        out["service"].append(round(dur, 2))
        print(f"cal service {k}: {dur:.1f}s ok={int(ok)} veto={int(reject)}")
    # veto behavior, clean vs junk windows
    for label, win_builder in (("clean", None), ("junk", build_junk_window)):
        win = "" if win_builder is None else win_builder(items, rng)
        for k in range(30):
            t = Task(-1, items[(7 * k + 3) % len(items)], 0.0, 1e18)
            _, ok, first, reject, parseable, ctext, dur, _ = serve(
                c, band, win, t)
            out[label].append(
                {"ok": ok, "veto": reject, "parseable": parseable})
        n = len(out[label])
        veto = sum(r["veto"] for r in out[label]) / n
        acc = sum(r["ok"] for r in out[label]) / n
        cov = (sum(1 for r in out[label] if r["veto"] and not r["ok"])
               / max(1, sum(1 for r in out[label] if not r["ok"])))
        fa = (sum(1 for r in out[label] if r["veto"] and r["ok"])
              / max(1, sum(1 for r in out[label] if r["ok"])))
        parse = sum(r["parseable"] for r in out[label]) / n
        print(f"cal {label}: veto={veto:.2f} acc={acc:.2f} coverage={cov:.2f} "
              f"false_alarm={fa:.2f} parse={parse:.2f}")
        out[label + "_stats"] = {"veto": veto, "acc": acc, "coverage": cov,
                                 "false_alarm": fa, "parse": parse}
    s = out["service"]
    out["s_cong"] = sum(s) / len(s)
    out["T_d"] = THETA * out["s_cong"]
    print(f"s_cong={out['s_cong']:.1f}s  T_d={out['T_d']:.0f}s")
    (HERE / "runs" / "e5_calibration.json").write_text(json.dumps(out, indent=1))
    return out


def run_arm(c, band, items, policy_on: bool, seed: int, log: RunLog,
            t_d: float, mu: float) -> None:
    rng = random.Random(5000 + seed)
    ramp = [("up", l) for l in RAMP_UP] + [("down", l) for l in RAMP_UP[-2::-1]]
    window = ""
    queue: list[Task] = []
    tid = 0
    retries: dict[int, int] = {}
    arm_t0 = time.time()

    def new_tid() -> int:
        nonlocal tid
        tid += 1
        return tid

    def serve_one(task, branch, l, step) -> None:
        nonlocal window
        cert, ok, first, reject, parseable, ctext, dur, ctx = serve(
            c, band, window, task)
        late = time.time() > task.deadline
        window = (window + task.prompt() + first + "\n")[-WINDOW_CHARS:]
        if reject and policy_on and retries.get(task.root, 0) < MAX_RETRIES:
            retries[task.root] = retries.get(task.root, 0) + 1
            queue.append(Task(new_tid(), task.item, time.time(),
                              time.time() + t_d, root=task.root,
                              depth=task.depth + 1, prev_answer=first))
        log.write({
            "exp": "e5", "policy": int(policy_on), "seed": seed,
            "branch": branch, "step": step, "l": l, "tid": task.tid,
            "depth": task.depth, "root": task.root,
            "item": task.item["name"],
            "certified": cert["certified"], "rank": cert["best_rank"],
            "correct": ok, "late": late, "uncert": (late or not ok),
            "veto": reject, "parseable": parseable,
            "service_s": round(dur, 2), "queue_after": len(queue),
            "ctx_tokens": ctx, "text": first[:60], "check": ctext,
        })

    for step, (branch, l) in enumerate(ramp):
        if time.time() - arm_t0 > ARM_WALL_MAX:
            print(f"  [TRUNCATED] arm wall cap at step {step}")
            break
        lam = l * mu
        dwell_t0 = time.time()
        t_a = dwell_t0
        pending = []
        for _ in range(EXO_PER_DWELL):
            t_a += rng.expovariate(lam)
            pending.append(t_a)
        n_served = n_unc = n_veto = 0
        while pending or (queue and time.time() < dwell_t0 + DWELL_WALL):
            now = time.time()
            while pending and pending[0] <= now:
                arr = pending.pop(0)
                queue.append(Task(new_tid(),
                                  items[rng.randrange(len(items))],
                                  arr, arr + t_d))
            if not queue:
                if pending:
                    time.sleep(min(0.25, max(0.01, pending[0] - now)))
                continue
            if now > dwell_t0 + DWELL_WALL and not pending:
                break
            task = queue.pop(0)
            serve_one(task, branch, l, step)
            n_served += 1
        recs = [r for r in log.records()
                if r.get("policy") == int(policy_on) and r.get("seed") == seed
                and r.get("step") == step]
        pu = sum(r["uncert"] for r in recs) / max(1, len(recs))
        bv = sum(r["veto"] for r in recs) / max(1, len(recs))
        print(f"  p={int(policy_on)} {branch:>4} l={l:.2f} served={len(recs)} "
              f"P_u={pu:.2f} b_veto={bv:.2f} backlog={len(queue)} "
              f"dwell={time.time() - dwell_t0:.0f}s")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--out", default=str(HERE / "runs" / "e5_loop.jsonl"))
    args = ap.parse_args()

    c = JLensClient(port=args.port)
    c.require_n1000()
    sl = c.slice("Fact: The capital of France is", top_n=5)
    band = band_layers(sl["layers"])
    items, _ = filter_single_token(c, load_probe_swap())
    print(f"band {band[0]}..{band[-1]}; battery {len(items)} items")

    if args.calibrate:
        calibrate(c, band, items)
        return 0

    cal = json.loads((HERE / "runs" / "e5_calibration.json").read_text())
    t_d, mu = cal["T_d"], 1.0 / cal["s_cong"]
    print(f"T_d={t_d:.0f}s mu=1/{cal['s_cong']:.1f}s")

    log = RunLog(args.out)
    done = set()
    for r in log.records():
        key = (r.get("policy"), r.get("seed"))
        if r.get("branch") == "down" and r.get("l") == RAMP_UP[0]:
            done.add(key)
    for policy_on in (True, False):
        if (int(policy_on), args.seed) in done:
            print(f"arm policy={int(policy_on)} seed={args.seed} complete; skip")
            continue
        print(f"=== arm policy={'ON' if policy_on else 'OFF'} seed={args.seed} ===")
        run_arm(c, band, items, policy_on, args.seed, log, t_d, mu)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
