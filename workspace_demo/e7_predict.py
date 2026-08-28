"""E7 prediction — fluctuation precursors near the fold, committed BEFORE
the rig run.

The paper's early-warning claim: approaching the fold, the order
parameter's fluctuations show rising variance and autocorrelation
(critical slowing down); away from the fold, no trend. The first attempt
on the E4 archive (e4_precursors.py) was honestly inconclusive: no power
(40-90 pre-runaway tasks) and a mean-drift confound. This is the
designed protocol.

Design history (model-tuned BEFORE commit, e7_scan.py):
  - low-rho "far" control rejected: over long horizons junk never clears,
    so even rho 0.30 ignites a nontrivial fraction — far-from-fold is
    horizon-dependent, and ctx-growth drift gives the control its own
    positive trend (more-vs-less, underpowered).
  - adopted control: ALPHA = 0 at the SAME load. Identical arrival
    process, identical window drift, but no feedback loop -> no fold.
    Presence-vs-absence of the mechanism at matched load.
  - PRE-FILLED clean window both arms (the E5 clean-FILLED trick):
    service starts on the congested law, no ctx-growth transient.
  - rho = 0.45 picked by scan: ignition 71%, censoring 17%, median
    pre-onset n = 68.

Protocol (mirrored exactly by the rig, e7_precursors_dwell.py):
  - pre-filled clean window; CONTINUOUS Poisson arrivals at
    lambda = 0.45 / s_cong for 3600 s wall-clock:
      FEEDBACK arm: alpha = 0.8 (spawning on, no gate)
      CONTROL arm:  alpha = 0   (no spawning; everything else identical)
  - primary order parameter: queue_after; secondary: junk indicator
  - pre-registered statistics: e7_stats.py (per-window linear detrend,
    residual variance + AC1, exact-unbiased Bernoulli excess variance,
    Kendall-tau trends; pre-onset segment = tasks before
    queue_after >= 12; censor below 40 tasks)

Falsifier: feedback-arm trends indistinguishable from control, or
negative.

Run:  python3 e7_predict.py     Out: runs/e7_prediction.json
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

import e6_predict
from e6_predict import CTX_CAP, S_CONG, T_D
from e7_stats import arm_summary

HERE = Path(__file__).parent

RHO = 0.45
WALL = 3600.0
ARMS = [("feedback", 0.8), ("control", 0.0)]
N_REP = 200
TAUS = ("tau_qvar", "tau_qac1", "tau_jxvar", "tau_jac1")


def run_arm(rng, rho: float, wall: float, alpha: float) -> dict:
    # e6_predict.serve_task reads module-global ALPHA; patched per arm
    # and restored (the control arm is alpha = 0).
    saved = e6_predict.ALPHA
    now, ctx = 0.0, float(CTX_CAP)
    queue, hist = [], [0.0] * 15
    kids = defaultdict(int)
    tid = 0
    t_a = 0.0
    lam = rho / S_CONG
    arrivals = []
    while t_a < wall:
        t_a += rng.expovariate(lam)
        arrivals.append(t_a)
    queue_after = []
    e6_predict.ALPHA = alpha
    try:
        while now < wall:
            while arrivals and arrivals[0] <= now:
                arr = arrivals.pop(0)
                tid += 1
                queue.append((arr, arr + T_D, 0, tid))
            if not queue:
                now = arrivals[0] if arrivals else wall
                continue
            now, ctx, _ = e6_predict.serve_task(
                rng, 0.0, False, now, ctx, queue, hist, kids)
            queue_after.append(len(queue))
    finally:
        e6_predict.ALPHA = saved
    return arm_summary([float(x) for x in hist], queue_after)


def main() -> int:
    out = {}
    per_arm = {}
    for name, alpha in ARMS:
        ign = cens = 0
        ns = []
        taus = {k: [] for k in TAUS}
        for i in range(N_REP):
            s = run_arm(random.Random(70000 + i), RHO, WALL, alpha)
            ign += s["ignited"]
            if s.get("censored"):
                cens += 1
                continue
            ns.append(s["n"])
            for k in TAUS:
                if s.get(k) is not None:
                    taus[k].append(s[k])
        per_arm[name] = taus
        out[name] = {
            "rho": RHO, "wall": WALL, "alpha": alpha, "replicas": N_REP,
            "ignited": ign, "censored": cens,
            "n_median": sorted(ns)[len(ns) // 2] if ns else 0,
            **{f"{k}_mean": (round(sum(v) / len(v), 3) if v else None)
               for k, v in taus.items()},
        }
        print(f"{name}: ignited {ign}/{N_REP} censored {cens} "
              f"n_med {out[name]['n_median']}")
        for k in TAUS:
            print(f"    {k}: {out[name][f'{k}_mean']}")
    pred = {}
    for k in TAUS:
        a = out["feedback"][f"{k}_mean"]
        b = out["control"][f"{k}_mean"]
        if a is not None and b is not None:
            pred[f"d_{k}"] = round(a - b, 3)
        na, nb = per_arm["feedback"][k], per_arm["control"][k]
        m = min(len(na), len(nb))
        if m:
            pred[f"p_sup_{k}"] = round(
                sum(na[i] > nb[i] for i in range(m)) / m, 3)
    out["prediction"] = {
        **pred,
        "direction": ("feedback > control on tau_qvar (primary) and "
                      "tau_qac1; control taus ~ 0"),
    }
    print("\nPREDICTION (feedback - control):")
    for k, v in pred.items():
        print(f"  {k}: {v:+.3f}" if isinstance(v, float) else f"  {k}: {v}")
    (HERE / "runs" / "e7_prediction.json").write_text(
        json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
