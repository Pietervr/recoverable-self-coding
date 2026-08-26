"""E5 prediction — committed BEFORE the ramp runs (predict-then-measure).

The Gap-2 reduced-model machinery with E5's emergent mechanism and every
ingredient measured in advance:

  service    E4's context-dependent service curve scaled to the measured
             E5 double-pass congested mean (33.7 s vs E4's 25.2 s at cap;
             ratio applied across the curve), lognormal dispersion
  P_err(j)   E4's in-loop content-error law (p0=0.05, p1=0.84, k=6) — the
             run's window junk is self-generated, the in-loop regime;
             consistency anchor: the law at j~0 gives 0.09 vs the E5
             calibration's measured 0.07 clean
  veto       the calibrated kernel: P(veto | wrong) = 0.50 (flat),
             P(veto | correct) = 0.05 * j (0.00 clean -> 0.05 junk)
  policy     retry on veto, max 2 retries per root (the design policy);
             retries deposit junk (re-check lines), wrong answers deposit
             junk, late-but-correct answers do not
  protocol   E5's ramp verbatim: l = .40..1.05 up then down,
             lambda = l / 33.7 s, T_d = 101 s, 12 exo arrivals per dwell,
             dwell wall 480 s

200 replicas per arm (policy ON / OFF). Output: the predicted runaway
distribution (or sub-criticality), pinning statistics, and the P_u / veto
levels per dwell — the numbers the measured E5 ramp is then compared
against. Written to runs/e5_prediction.json and committed to git before
the ramp starts.

Run:  python3 e5_predict.py [--replicas 200]
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent

RAMP_UP = [0.40, 0.60, 0.75, 0.85, 0.95, 1.05]
EXO = 12
DWELL_WALL = 480.0
MAX_RETRIES = 2
CTX_CAP = 2800
WINDOW_N = 15

# E4's measured service curve (ctx_hi, mean, sd), to be scaled
E4_LAW = [(500, 6.6, 3.6), (1000, 13.1, 3.7), (1500, 16.9, 3.4),
          (2000, 19.9, 2.6), (2500, 24.3, 2.9), (99999, 25.2, 2.9)]
P_ERR_FIT = (0.05, 0.84, 6.0)   # E4 in-loop law
COVERAGE = 0.50                  # calibrated
FA_SLOPE = 0.05                  # false alarms = FA_SLOPE * j
CTX_STEP = 24.2


def p_err(j: float) -> float:
    p0, p1, k = P_ERR_FIT
    return p0 + (p1 - p0) / (1 + math.exp(-k * (j - 0.5)))


def sample_service(law, ctx, rng):
    for hi, m, sd in law:
        if ctx < hi:
            break
    sigma2 = math.log(1 + (sd / m) ** 2)
    mu = math.log(m) - sigma2 / 2
    return math.exp(rng.gauss(mu, sigma2 ** 0.5))


def run_replica(rng, law, t_d, lam_unit, policy_on):
    ramp = [("up", l) for l in RAMP_UP] + [("down", l) for l in RAMP_UP[-2::-1]]
    now, ctx = 0.0, 200.0
    queue = []          # (arrival, deadline, depth, root)
    hist = []
    tid = 0
    retries = defaultdict(int)
    out = []
    for branch, l in ramp:
        lam = l * lam_unit
        t_a = now
        pending = []
        for _ in range(EXO):
            t_a += rng.expovariate(lam)
            pending.append(t_a)
        dwell_t0 = now
        served = unc = vet = 0
        while pending or (queue and now < dwell_t0 + DWELL_WALL):
            if pending and (not queue) and pending[0] > now:
                now = pending[0]
            while pending and pending[0] <= now:
                arr = pending.pop(0)
                tid += 1
                queue.append((arr, arr + t_d, 0, tid))
            if not queue:
                continue
            if now > dwell_t0 + DWELL_WALL and not pending:
                break
            arr, dl, depth, root = queue.pop(0)
            now += sample_service(law, ctx, rng)
            ctx = min(CTX_CAP, ctx + CTX_STEP)
            j = sum(hist[-WINDOW_N:]) / max(1, len(hist[-WINDOW_N:])) \
                if len(hist) >= 5 else 0.0
            wrong = rng.random() < p_err(j)
            late = now > dl
            veto = rng.random() < (COVERAGE if wrong else FA_SLOPE * j)
            hist.append(1 if (wrong or depth > 0) else 0)
            served += 1
            unc += wrong or late
            vet += veto
            if veto and policy_on and retries[root] < MAX_RETRIES:
                retries[root] += 1
                queue.append((now, now + t_d, depth + 1, root))
        out.append({"branch": branch, "l": l, "P_u": unc / max(1, served),
                    "b_veto": vet / max(1, served), "q_end": len(queue)})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicas", type=int, default=200)
    args = ap.parse_args()
    cal = json.loads((HERE / "runs" / "e5_calibration.json").read_text())
    scale = cal["s_cong"] / E4_LAW[-1][1]
    law = [(hi, m * scale, sd * scale) for hi, m, sd in E4_LAW]
    t_d, lam_unit = cal["T_d"], 1.0 / cal["s_cong"]
    print(f"scaled service law (x{scale:.2f}); T_d={t_d:.0f}s")

    results = {}
    for policy_on, name in ((True, "policy_on"), (False, "policy_off")):
        runaways, pinned, dwell_acc = [], 0, defaultdict(list)
        for i in range(args.replicas):
            rng = random.Random(30000 + i)
            traj = run_replica(rng, law, t_d, lam_unit, policy_on)
            ra = next((d["l"] for d in traj
                       if d["branch"] == "up" and d["P_u"] >= 0.9
                       and d["q_end"] > 5), None)
            runaways.append(ra)
            if traj[-1]["P_u"] >= 0.9 and traj[-1]["q_end"] > 5:
                pinned += 1
            for d in traj:
                dwell_acc[(d["branch"], d["l"])].append((d["P_u"], d["b_veto"]))
        n_col = sum(1 for r in runaways if r is not None)
        dist = defaultdict(int)
        for r in runaways:
            dist[r] += 1
        med = sorted(r for r in runaways if r is not None)
        med = med[len(med) // 2] if med else None
        print(f"\n{name}: collapsed {n_col}/{args.replicas} "
              f"dist={dict(sorted(dist.items(), key=str))} median={med} "
              f"pinned_at_end={pinned}")
        per_dwell = {}
        for k in sorted(dwell_acc, key=str):
            vals = dwell_acc[k]
            per_dwell[str(k)] = {
                "P_u": round(sum(v[0] for v in vals) / len(vals), 3),
                "b_veto": round(sum(v[1] for v in vals) / len(vals), 3),
            }
            print(f"  {k}: P_u={per_dwell[str(k)]['P_u']:.2f} "
                  f"b_veto={per_dwell[str(k)]['b_veto']:.2f}")
        results[name] = {"collapsed": n_col,
                         "dist": {str(k): v for k, v in dist.items()},
                         "median": med, "pinned": pinned,
                         "per_dwell": per_dwell}
    (HERE / "runs" / "e5_prediction.json").write_text(
        json.dumps(results, indent=1))
    print("\nPrediction written; commit BEFORE the ramp runs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
