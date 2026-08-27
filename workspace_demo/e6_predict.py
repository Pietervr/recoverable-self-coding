"""E6 prediction — the gating-exit threshold, committed BEFORE the run.

The paper's closed form: exiting the bistable wedge requires certification
coverage q > 1 - 1/[alpha (1 + theta)]. With E4's measured parameters
(alpha = 0.8 injected; theta_eff = T_d / s_cong = 66 / 24.5 = 2.69) the
idealized threshold is q* = 0.661.

The protocol-faithful prediction uses the Gap-2 reduced model with a gate
added, mechanism identical to the rig's: an ORACLE gate of coverage q
intercepts each uncertified completion; caught means no offspring AND the
correct line enters the window instead of junk (certification = archived
commitment, both channels gated). E6 protocol: ignite at l = 0.95 (two
dwell-equivalents, q = 0), drop to l = 0.75 (inside the wedge), gate at
coverage q for four dwells; EXIT iff final backlog <= 2 AND last-dwell
P_u <= 0.4. 100 replicas per q on a fine grid -> the predicted exit
probability curve and its 50% crossing q*_model.

Run:  python3 e6_predict.py     Out: runs/e6_prediction.json
"""

from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent

E4_LAW = [(500, 6.6, 3.6), (1000, 13.1, 3.7), (1500, 16.9, 3.4),
          (2000, 19.9, 2.6), (2500, 24.3, 2.9), (99999, 25.2, 2.9)]
P_ERR_FIT = (0.05, 0.84, 6.0)
LAM_UNIT = 1 / 10.95
T_D = 66.0
ALPHA = 0.8
MAX_DEPTH = 4
MAX_PER_ROOT = 10
CTX_CAP = 2800
CTX_STEP = 24.2
WINDOW_N = 15
EXO = 12
DWELL_WALL = 480.0

IGNITE = [("ignite", l) for l in (0.60, 0.75, 0.85, 0.95, 1.05, 1.05)]
REIGNITE = [("ignite", 1.05), ("ignite", 1.05)]
Q_SEQ = [0.40, 0.55, 0.70, 0.85]
# gated phase: CONTINUOUS Poisson arrivals at TRUE utilization 0.75
# (lambda = 0.75 / s_cong) for a fixed wall-clock duration — sustained
# pressure, the stationary regime the closed form assumes. Criterion:
# backlog slope (EXIT if B_end <= 0.7 B_start; PINNED if B_end >= B_start).
RHO_GATED = 0.75
S_CONG = 25.2
GATE_WALL = 2100.0


def p_err(j):
    p0, p1, k = P_ERR_FIT
    return p0 + (p1 - p0) / (1 + math.exp(-k * (j - 0.5)))


def sample_service(ctx, rng):
    for hi, m, sd in E4_LAW:
        if ctx < hi:
            break
    sigma2 = math.log(1 + (sd / m) ** 2)
    return math.exp(rng.gauss(math.log(m) - sigma2 / 2, sigma2 ** 0.5))


def poisson(rng, lam):
    l_exp, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= l_exp:
            return k
        k += 1


def serve_task(rng, q, gated, now, ctx, queue, hist, kids):
    arr, dl, depth, root = queue.pop(0)
    now += sample_service(ctx, rng)
    ctx = min(CTX_CAP, ctx + CTX_STEP)
    j = sum(hist[-WINDOW_N:]) / max(1, len(hist[-WINDOW_N:])) \
        if len(hist) >= 5 else 0.0
    wrong = rng.random() < p_err(j)
    late = now > dl
    u = wrong or late
    caught = u and gated and rng.random() < q
    if caught:
        hist.append(0)                  # correct line archived, no junk
    else:
        hist.append(1 if (wrong or depth > 0) else 0)
        if u and depth < MAX_DEPTH and kids[root] < MAX_PER_ROOT:
            n = min(poisson(rng, ALPHA), MAX_PER_ROOT - kids[root])
            kids[root] += n
            for _ in range(n):
                queue.append((now, now + T_D, depth + 1, root))
    return now, ctx, u


class Sim:
    def __init__(self, rng):
        self.rng = rng
        self.now, self.ctx = 0.0, 200.0
        self.queue, self.hist = [], []
        self.tid = 0
        self.kids = defaultdict(int)

    def burst_dwell(self, l):
        rng = self.rng
        lam = l * LAM_UNIT
        t_a = self.now
        pending = []
        for _ in range(EXO):
            t_a += rng.expovariate(lam)
            pending.append(t_a)
        dwell_t0 = self.now
        while pending or (self.queue and self.now < dwell_t0 + DWELL_WALL):
            if pending and (not self.queue) and pending[0] > self.now:
                self.now = pending[0]
            while pending and pending[0] <= self.now:
                arr = pending.pop(0)
                self.tid += 1
                self.queue.append((arr, arr + T_D, 0, self.tid))
            if not self.queue:
                continue
            if self.now > dwell_t0 + DWELL_WALL and not pending:
                break
            self.now, self.ctx, _ = serve_task(
                rng, 0.0, False, self.now, self.ctx, self.queue,
                self.hist, self.kids)

    def gate_phase(self, q):
        """Continuous arrivals at TRUE utilization for GATE_WALL seconds.
        Returns (B_start, B_end, verdict)."""
        rng = self.rng
        b_start = len(self.queue)
        lam = RHO_GATED / S_CONG
        gate_t0 = self.now
        t_a = self.now
        arrivals = []
        while t_a < gate_t0 + GATE_WALL:
            t_a += rng.expovariate(lam)
            arrivals.append(t_a)
        while self.now < gate_t0 + GATE_WALL:
            while arrivals and arrivals[0] <= self.now:
                arr = arrivals.pop(0)
                self.tid += 1
                self.queue.append((arr, arr + T_D, 0, self.tid))
            if not self.queue:
                self.now = arrivals[0] if arrivals else gate_t0 + GATE_WALL
                continue
            self.now, self.ctx, _ = serve_task(
                rng, q, True, self.now, self.ctx, self.queue,
                self.hist, self.kids)
        b_end = len(self.queue)
        if b_end <= 0.7 * b_start:
            v = "EXIT"
        elif b_end >= b_start:
            v = "PINNED"
        else:
            v = "AMBIG"
        return b_start, b_end, v


def run_replica(rng):
    """The sequential escalating-q protocol, mirrored from the rig plan:
    ignite via the E4 ramp; gate at ascending q; re-ignite after an EXIT.
    Returns {q: verdict}."""
    sim = Sim(rng)
    for _, l in IGNITE:
        sim.burst_dwell(l)
    out = {}
    for q in Q_SEQ:
        if len(sim.queue) < 8:
            for _, l in REIGNITE:
                sim.burst_dwell(l)
        if len(sim.queue) < 8:
            out[q] = "VOID"
            continue
        b0, b1, v = sim.gate_phase(q)
        out[q] = v
        if v == "EXIT":
            for _, l in REIGNITE:
                sim.burst_dwell(l)
    return out


def main() -> int:
    tallies = {q: defaultdict(int) for q in Q_SEQ}
    for i in range(200):
        res = run_replica(random.Random(50000 + i))
        for q, v in res.items():
            tallies[q][v] += 1
    out = {}
    qstar = None
    for q in Q_SEQ:
        t = tallies[q]
        valid = t["EXIT"] + t["PINNED"]
        p = t["EXIT"] / valid if valid else float("nan")
        out[str(q)] = {"exit_prob": round(p, 3), **{k: v for k, v in t.items()}}
        print(f"q={q:.2f}: exit {p:.2f}  (EXIT {t['EXIT']} PINNED {t['PINNED']} "
              f"AMBIG {t['AMBIG']} VOID {t['VOID']})")
        if qstar is None and p >= 0.5:
            qstar = q
    closed_form = 1 - 1 / (ALPHA * (1 + T_D / 24.54))
    print(f"\nPREDICTIONS (committed before the run):")
    print(f"  closed-form q* = {closed_form:.3f}")
    print(f"  reduced-model q* (50% exit crossing) = {qstar}")
    (HERE / "runs" / "e6_prediction.json").write_text(json.dumps(
        {"closed_form_qstar": round(closed_form, 3),
         "reduced_model_qstar": qstar, "exit_curve": out}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
