"""calibrate_gain after the 12 Sept 2026 correction, with expected_gain mocked: a continuous gain resolves as
before (5 % tolerance, no jump); a gain with a jump across the target — the d4v12b failure — collapses the
bracket, freezes the scale, re-measures at twice the concepts and a fresh seed, records the jump, runs the
check and passes or fails on the gate; a target outside the bracket is refused; the gate now bounds the
calibration side too."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import numpy as np
import simulate as S

CONV = {g: True for g in S.M.FAMILY_G}
REPRO = dict(starts_at_best={g: 3 for g in S.M.FAMILY_G}, ref_reproduced=True)
calls = []

warms = []

def smooth(name, theta, seed=0, n_per_family=32, D=4, cfg=None, graded=S.M.FAMILY_G, warm=None, **kw):
    scale = float(np.exp(theta[2]))
    calls.append((round(scale, 6), seed, n_per_family))
    warms.append(None if warm is None else {g: round(float(v[0]), 6) for g, v in warm.items()})   # a copy: warm is updated in place
    return dict(gain=0.03 * scale ** 5.2, se=1e-4, best="M2K", gains={}, converged=CONV,
                theta={g: [scale] for g in graded}, **REPRO)

def jumpy(name, theta, seed=0, n_per_family=32, D=4, cfg=None, graded=S.M.FAMILY_G, warm=None, **kw):
    """the trace of 12 Sept: 0.00806 just below scale 0.684661, 0.01097 just above, M2K kept on both sides"""
    scale = float(np.exp(theta[2]))
    calls.append((round(scale, 6), seed, n_per_family))
    if seed != 2026:                     # the re-measurement (seed + 500) and the check (seed + 1000)
        return dict(gain=0.0095 if seed == 2526 else 0.0104, se=0.0005, best="M2K", gains={}, converged=CONV, **REPRO)
    base = 0.03 * (scale / 0.86) ** 5.2
    return dict(gain=base if scale < 0.684661 else base + 0.0029, se=7e-4, best="M2K", gains={}, converged=CONV, **REPRO)

# 1. continuous: resolved within tolerance, no jump, check at seed + 1000 and 64 per family
S.expected_gain = smooth
e = S.calibrate_gain("M3L", 0.01, {"pi0": 0.05}, seed=2026, cfg=None, D=4)
assert e["note"] == "" and e["gain_jump"] == 0.0 and abs(e["gain"] - 0.01) <= 0.05 * 0.01, e
assert calls[-1][1] == 3026 and calls[-1][2] == 64 and all(c[1] == 2026 for c in calls[:-1])
assert warms[0] is None and all(w is not None and w["M2K"] == calls[i - 1][0] for i, w in enumerate(warms) if i > 0), warms[:3]
print(f"continuous gain: scale {e['scale']:.5f} in {len(calls) - 1} evaluations, gain {e['gain']:.5f}, "
      f"warm starts carried along the path (check included) OK")

# 2. the jump: bracket collapses (never within 5 %), scale frozen at 0.68466, jump ≈ 0.0029 recorded,
#    the gain re-measured at seed 2526 with 64 per family, the check at 3026, the gate passes
calls.clear()
S.expected_gain = jumpy
e = S.calibrate_gain("M3L", 0.01, {"pi0": 0.05}, seed=2026, cfg=None, D=4)
assert e["note"] == "", e["note"]
assert abs(e["scale"] - 0.684661) < 0.684661 * 1e-3, e["scale"]
assert abs(e["gain_jump"] - 0.0029) < 2e-4, e["gain_jump"]
assert e["gain"] == 0.0095 and e["gain_check"] == 0.0104
assert calls[-2] == (round(e["scale"], 6), 2526, 64) and calls[-1] == (round(e["scale"], 6), 3026, 64)
n_bisect = len(calls) - 2
assert n_bisect < 20, n_bisect                       # 0.1 % bracket width from [0.02, 3] takes ≈ 14 steps, not 30
assert e["trace"][-1]["seed"] == 2526 and e["trace"][-1]["n_per_family"] == 64
print(f"jump: scale frozen at {e['scale']:.6f} after {n_bisect} bisection steps, jump {e['gain_jump']:.5f}, "
      f"gain {e['gain']} check {e['gain_check']} — gate '{e['note'] or 'pass'}' OK")

# 3. the same jump with a re-measurement outside 25 %: the gate refuses on the calibration side
def jumpy_bad(name, theta, seed=0, n_per_family=32, D=4, cfg=None, graded=S.M.FAMILY_G, **kw):
    r = jumpy(name, theta, seed, n_per_family, D, cfg, graded)
    if seed == 2526:
        r["gain"] = 0.0070
    return r
calls.clear()
S.expected_gain = jumpy_bad
e = S.calibrate_gain("M3L", 0.01, {"pi0": 0.05}, seed=2026, cfg=None, D=4)
assert "calibration gain" in e["note"], e["note"]
print(f"jump with a bad re-measurement: gate says '{e['note']}' OK")

# 4. target outside the bracket is refused as before
S.expected_gain = lambda name, theta, seed=0, n_per_family=32, D=4, cfg=None, graded=S.M.FAMILY_G, **kw: dict(
    gain=0.5, se=1e-4, best="M2K", gains={}, converged=CONV, **REPRO)
e = S.calibrate_gain("M3L", 0.01, {"pi0": 0.05}, seed=2026, cfg=None, D=4)
assert "outside the bracket" in e["note"] and not np.isfinite(e["scale"])
print("target outside the bracket refused OK")

# 5. a reference optimum reached by one start only (the d4v12b mechanism) is refused by the gate, in either draw
def lonely(name, theta, seed=0, n_per_family=32, D=4, cfg=None, graded=S.M.FAMILY_G, **kw):
    r = smooth(name, theta, seed, n_per_family, D, cfg, graded)
    if seed == 3026:
        r.update(starts_at_best={g: 1 for g in graded}, ref_reproduced=False)
    return r
calls.clear()
S.expected_gain = lonely
e = S.calibrate_gain("M3L", 0.01, {"pi0": 0.05}, seed=2026, cfg=None, D=4)
assert "fewer than 2 starts in the check draw" in e["note"], e["note"]
assert e["check_starts_at_best"]["M2K"] == 1 and e["calib_starts_at_best"]["M2K"] == 3
print(f"reference reached by one start: gate says '{e['note']}' OK")

# 6. _starts_at_best on a FitResult shaped like the 12 Sept diagnostic: 1 of 8 at the deep optimum
class _F:
    loglik = -44543.62
    runs = [dict(converged=True, loglik=-44698.90)] * 7 + [dict(converged=True, loglik=-44543.62)]
assert S._starts_at_best(_F()) == 1
_F.runs = _F.runs + [dict(converged=True, loglik=-44543.9), dict(converged=False, loglik=-44543.62)]
assert S._starts_at_best(_F()) == 2                # within 0.5 nat counts; an unconverged run does not
shallow = _F(); shallow.loglik = -44698.90; shallow.runs = [dict(converged=True, loglik=-44698.90)] * 8
assert S._starts_at_best(shallow, extra_runs=[dict(converged=True, loglik=-44543.62)]) == 1   # a warm start that beats them all
print("_starts_at_best counts converged runs within 0.5 nat of the best, warm-start runs included OK")
