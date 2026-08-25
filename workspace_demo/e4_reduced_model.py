"""Gap 2, done right — the protocol-faithful reduced model of E4.

The static mean-field fold (e4_closure.py) is the stationary skeleton; the
experiment, however, runs 12-arrival dwell TRANSIENTS with a service law
that depends on window fill. This script simulates E4's exact protocol
with every ingredient measured from a statistic disjoint from the
collapse itself:

  s(ctx)     service time vs context tokens — piecewise from the measured
             per-task (ctx_tokens, service_s) records, with the measured
             per-bucket dispersion (lognormal)
  ctx(n)     window-fill trajectory — measured tokens-per-served-task
             growth to the cap
  P_err(u)   content-error law — the logistic fit of wrongness vs recent
             uncertified fraction (e4_closure.py fit, both arms)
  spawning   the DESIGN rules verbatim: Poisson(0.8) per uncertified,
             depth <= 4, <= 10 offspring per root
  protocol   the E4 ramp verbatim: l = .40 .60 .75 .85 .95 1.05 up, mirror
             down; lambda = l / 10.95 s (the calibration constant the
             experiment actually used); 12 exo arrivals per dwell; dwell
             wall cap 480 s; T_d = 66 s; backlog carried between dwells

Nothing is fitted to the collapse. 200 replicas per arm -> the predicted
distribution of runaway points (first l with P_u >= 0.9 and backlog > 5)
against the measured E4 runaways [0.60, 0.85, 0.85, 0.95], plus the
control-arm prediction (no runaway) and down-branch pinning statistics.

Run:  python3 e4_reduced_model.py [--replicas 200]
Out:  runs/e4_reduced_model.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
LOG = HERE / "runs" / "e4_loop.jsonl"

RAMP_UP = [0.40, 0.60, 0.75, 0.85, 0.95, 1.05]
LAM_UNIT = 1 / 10.95      # the experiment's calibration constant
T_D = 66.0
DWELL_WALL = 480.0
EXO = 12
ALPHA = 0.8
MAX_DEPTH = 4
MAX_PER_ROOT = 10
CTX_CAP = 2800
WINDOW_N = 15


def load() -> list[dict]:
    latest: dict[tuple, dict] = {}
    for line in LOG.read_text().splitlines():
        r = json.loads(line)
        if r.get("exp") == "e4":
            latest[(r["alpha"], r.get("seed", 0), r["tid"])] = r
    return list(latest.values())


def fit_service(recs) -> tuple[list[tuple[float, float, float]], float]:
    """Bucketed (ctx_hi, mean, sd) service law, pooled arms."""
    buckets = [(0, 500), (500, 1000), (1000, 1500), (1500, 2000),
               (2000, 2500), (2500, 99999)]
    law = []
    for lo, hi in buckets:
        xs = [r["service_s"] for r in recs if lo <= r["ctx_tokens"] < hi]
        if len(xs) < 8:
            continue
        m = sum(xs) / len(xs)
        sd = (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5
        law.append((hi, m, sd))
    return law, 0.0


def sample_service(law, ctx: float, rng: random.Random) -> float:
    for hi, m, sd in law:
        if ctx < hi:
            break
    # lognormal with matched mean/sd
    if sd <= 0:
        return m
    sigma2 = math.log(1 + (sd / m) ** 2)
    mu = math.log(m) - sigma2 / 2
    return math.exp(rng.gauss(mu, sigma2 ** 0.5))


def fit_ctx_growth(recs) -> float:
    """Mean context tokens added per served task (pre-cap)."""
    deltas = []
    for alpha in (0.8, 0.0):
        for seed in {r.get("seed", 0) for r in recs}:
            arm = sorted((r for r in recs if r["alpha"] == alpha
                          and r.get("seed", 0) == seed),
                         key=lambda r: r["tid"])
            for a, b2 in zip(arm, arm[1:]):
                d = b2["ctx_tokens"] - a["ctx_tokens"]
                if 0 < d < 200 and b2["ctx_tokens"] < CTX_CAP - 100:
                    deltas.append(d)
    return sum(deltas) / len(deltas)


def p_err(fit, u: float) -> float:
    p0, p1, k = fit
    return p0 + (p1 - p0) / (1 + math.exp(-k * (u - 0.5)))


def poisson(rng, lam):
    l_exp, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= l_exp:
            return k
        k += 1


def run_replica(rng, law, ctx_step, perr_fit, feedback: bool):
    ramp = [("up", l) for l in RAMP_UP] + [("down", l) for l in RAMP_UP[-2::-1]]
    now = 0.0
    ctx = 200.0
    queue = []          # (arrival, deadline, depth, root)
    hist = []
    tid = 0
    root_kids = defaultdict(int)
    out = []
    for branch, l in ramp:
        lam = l * LAM_UNIT
        t_a = now
        pending = []
        for _ in range(EXO):
            t_a += rng.expovariate(lam)
            pending.append(t_a)
        dwell_t0 = now
        served = unc_n = 0
        while pending or (queue and now < dwell_t0 + DWELL_WALL):
            if pending and (not queue) and pending[0] > now:
                now = pending[0]
            while pending and pending[0] <= now:
                arr = pending.pop(0)
                tid += 1
                queue.append((arr, arr + T_D, 0, tid))
            if not queue:
                continue
            if now > dwell_t0 + DWELL_WALL and not pending:
                break
            arr, dl, depth, root = queue.pop(0)
            s = sample_service(law, ctx, rng)
            now += s
            ctx = min(CTX_CAP, ctx + ctx_step)
            u_rec = sum(hist[-WINDOW_N:]) / max(1, len(hist[-WINDOW_N:])) \
                if len(hist) >= 5 else 0.0
            wrong = rng.random() < p_err(perr_fit, u_rec)
            late = now > dl
            unc = wrong or late
            # junk deposit: wrong answers and repair lines contaminate the
            # window; a late-but-correct answer leaves no junk
            hist.append(1 if (wrong or depth > 0) else 0)
            served += 1
            unc_n += unc
            if unc and feedback and depth < MAX_DEPTH \
                    and root_kids[root] < MAX_PER_ROOT:
                n = min(poisson(rng, ALPHA), MAX_PER_ROOT - root_kids[root])
                root_kids[root] += n
                for _ in range(n):
                    queue.append((now, now + T_D, depth + 1, root))
        out.append({"branch": branch, "l": l,
                    "P_u": unc_n / max(1, served), "q_end": len(queue)})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicas", type=int, default=200)
    args = ap.parse_args()
    recs = load()
    law, _ = fit_service(recs)
    ctx_step = fit_ctx_growth(recs)
    perr_fit = tuple(json.loads(
        (HERE / "runs" / "e4_closure.json").read_text())["p_err_fit"])
    print("service law (ctx_hi, mean, sd):",
          [(h, round(m, 1), round(s, 1)) for h, m, s in law])
    print(f"ctx growth/task: {ctx_step:.1f} tokens;  P_err fit: {perr_fit}")

    results = {}
    for feedback, name in ((True, "alpha=0.8"), (False, "alpha=0")):
        runaways = []
        pinned = 0
        down04 = []
        for i in range(args.replicas):
            rng = random.Random(20000 + i)
            traj = run_replica(rng, law, ctx_step, perr_fit, feedback)
            ra = None
            for d in traj:
                if d["branch"] == "up" and d["P_u"] >= 0.9 and d["q_end"] > 5:
                    ra = d["l"]
                    break
            runaways.append(ra)
            last = traj[-1]
            if last["P_u"] >= 0.9 and last["q_end"] > 5:
                pinned += 1
            down04.append(last["P_u"])
        n_col = sum(1 for r in runaways if r is not None)
        dist = defaultdict(int)
        for r in runaways:
            dist[r] += 1
        med = sorted(r for r in runaways if r is not None)
        med = med[len(med) // 2] if med else None
        print(f"\n{name}: collapsed {n_col}/{args.replicas}"
              f"  runaway distribution {dict(sorted(dist.items(), key=str))}"
              f"  median {med}")
        print(f"  down-branch end (l=0.40): pinned {pinned}/{args.replicas}; "
              f"mean P_u {sum(down04) / len(down04):.2f}")
        results[name] = {"collapsed": n_col, "runaway_dist": {str(k): v for k, v in dist.items()},
                         "median": med, "pinned_at_040": pinned}
    print("\nMEASURED (E4): runaways 0.60, 0.85, 0.85, 0.95 (median 0.85); "
          "pinned at l=0.40: 4/4; control collapsed: 0/4")
    (HERE / "runs" / "e4_reduced_model.json").write_text(
        json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
