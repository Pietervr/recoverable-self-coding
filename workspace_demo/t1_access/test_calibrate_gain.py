"""calibrate_gain after the 12 Sept 2026 correction and the Codex re-check, with expected_gain mocked: a continuous
gain resolves as before (5 % tolerance, no jump) with the basin candidates travelling as warm starts; a gain with a
jump across the target — the d4v12b failure — collapses the bracket, RE-EVALUATES both ends with the warm set, then
freezes the scale, re-measures at twice the concepts and a fresh seed (the declared fallback), records the jump, runs
the check and passes or fails on the gate; a jump that the re-evaluation heals resolves without the fallback; a target
outside the bracket is refused; the gate bounds the calibration side and requires the reference reproduced by
distinct cold starts. Then the pure helpers: distinct-start counting by source, the extra batch without the repeated
moment start and with the skew mirror, basin candidates, the warm merge."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import numpy as np
import simulate as S

G = S.M.FAMILY_G
CONV = {g: True for g in G}
REPRO = dict(starts_at_best={g: 3 for g in G}, warm_at_best={g: 0 for g in G}, ref_reproduced=True)
calls, warms = [], []

def base(name, theta, seed, n_per_family, warm, gain, se=1e-4):
    scale = float(np.exp(theta[2]))
    calls.append((round(scale, 6), seed, n_per_family))
    warms.append(None if warm is None else {g: [round(float(v[0]), 6) for v in warm[g]] for g in warm})   # copy: warm is updated in place
    return dict(gain=gain, se=se, best="M2K", gains={}, converged=CONV, candidates={g: [[scale]] for g in G},
                theta={g: [scale] for g in G}, runs={g: [] for g in G}, **REPRO)

def smooth(name, theta, seed=0, n_per_family=32, D=4, cfg=None, graded=G, warm=None, **kw):
    return base(name, theta, seed, n_per_family, warm, 0.03 * float(np.exp(theta[2])) ** 5.2)

def jumpy(name, theta, seed=0, n_per_family=32, D=4, cfg=None, graded=G, warm=None, **kw):
    """the trace of 12 Sept: 0.00806 just below scale 0.684661, 0.01097 just above, M2K kept on both sides"""
    scale = float(np.exp(theta[2]))
    if seed != 2026:                     # the fallback re-measurement (seed + 500) and the check (seed + 1000)
        return base(name, theta, seed, n_per_family, warm, 0.0095 if seed == 2526 else 0.0104, 0.0005)
    b = 0.03 * (scale / 0.86) ** 5.2
    return base(name, theta, seed, n_per_family, warm, b if scale < 0.684661 else b + 0.0029, 7e-4)

# 1. continuous: resolved within tolerance, no jump, no re-evaluation, check at seed + 1000 and 64 per family;
#    the warm set carries every scale visited so far (newest first), the check included
S.expected_gain = smooth
e = S.calibrate_gain("M3L", 0.01, {"pi0": 0.05}, seed=2026, cfg=None, D=4)
assert e["note"] == "" and e["gain_jump"] == 0.0 and not e["bracket_reevaluated"] and not e["fallback_remeasured"]
assert abs(e["gain"] - 0.01) <= 0.05 * 0.01, e
assert calls[-1][1] == 3026 and calls[-1][2] == 64 and all(c[1] == 2026 for c in calls[:-1])
assert warms[0] is None and all(w["M2K"][0] == calls[i - 1][0] for i, w in enumerate(warms) if i > 0), warms[:3]
assert len(warms[-1]["M2K"]) == S.REF_MAX_CANDIDATES + 2, warms[-1]
assert e["calib_runs"] == {g: [] for g in G} and e["check_runs"] == {g: [] for g in G}, e["calib_runs"]
assert abs(e["check_theta"]["M2K"][0] - e["scale"]) < 1e-9
print(f"continuous gain: scale {e['scale']:.5f} in {len(calls) - 1} evaluations, gain {e['gain']:.5f}, "
      f"warm candidates carried (capped at {S.REF_MAX_CANDIDATES + 2}) OK")

# 2. the jump: the bracket collapses (never within 5 %), both ends are re-evaluated with the warm set (still a jump),
#    the scale is frozen at 0.68466, jump ≈ 0.0029 recorded, the gain re-measured at seed 2526 with 64 per family
#    (the declared fallback), the check at 3026, the gate passes
calls.clear(); warms.clear()
S.expected_gain = jumpy
e = S.calibrate_gain("M3L", 0.01, {"pi0": 0.05}, seed=2026, cfg=None, D=4)
assert e["note"] == "", e["note"]
assert abs(e["scale"] - 0.684661) < 0.684661 * 1e-3, e["scale"]
assert e["bracket_reevaluated"] and e["fallback_remeasured"] and abs(e["gain_jump"] - 0.0029) < 2e-4, e["gain_jump"]
assert e["gain"] == 0.0095 and e["gain_check"] == 0.0104
sc = round(e["scale"], 6)
assert calls[-1] == (sc, 3026, 64) and calls[-2] == (sc, 2526, 64)
lo_c, hi_c = calls[-4], calls[-3]                 # the re-evaluated bracket ends, both at the calibration seed
assert lo_c[1] == hi_c[1] == 2026 and lo_c[0] < sc < hi_c[0] and hi_c[0] / lo_c[0] - 1 < S.MIN_BRACKET_WIDTH
n_bisect = len(calls) - 4
assert n_bisect < 20, n_bisect                       # 0.1 % bracket width from [0.02, 3] takes ≈ 14 steps, not 30
assert e["trace"][-1]["seed"] == 2526 and e["trace"][-1]["n_per_family"] == 64
print(f"jump: scale frozen at {e['scale']:.6f} after {n_bisect} bisection steps + 2 re-evaluations, jump {e['gain_jump']:.5f}, "
      f"gain {e['gain']} check {e['gain_check']} — gate '{e['note'] or 'pass'}' OK")

# 3a. a jump that the re-evaluation heals AT the bracket end (the warm set finds the better basin there and its
#     value is within tolerance): resolved at that end, no fallback, no jump recorded
N_COLLAPSE = len(calls) - 4                       # evaluations up to the collapse in the jumpy path (2 ends + bisection)
def healing_end(name, theta, seed=0, n_per_family=32, D=4, cfg=None, graded=G, warm=None, **kw):
    r = jumpy(name, theta, seed, n_per_family, D, cfg, graded, warm)
    scale = float(np.exp(theta[2]))
    if seed == 2026 and len(calls) > N_COLLAPSE and scale >= 0.684661:
        r["gain"] = r["gain"] - 0.0029 + 0.0009   # the carried basin: the true value at the upper end, 0.0101
    return r
calls.clear(); warms.clear()
S.expected_gain = healing_end
e = S.calibrate_gain("M3L", 0.01, {"pi0": 0.05}, seed=2026, cfg=None, D=4)
assert e["note"] == "" and e["bracket_reevaluated"] and not e["fallback_remeasured"] and e["gain_jump"] == 0.0, e["note"]
assert abs(e["gain"] - 0.01) <= 0.05 * 0.01 and abs(e["scale"] - 0.684661) < 1e-3 and calls[-1][1] == 3026 and calls[-2][1] == 2026
print(f"healed at the end: resolved at scale {e['scale']:.6f}, gain {e['gain']:.5f}, no fallback OK")

# 3b. a jump that the re-evaluation heals so that the target ESCAPES the collapsed bracket (both ends now below):
#     the bracket is widened upward from the scales already visited, nearest first, and the bisection resumes to
#     the scale where the healed function meets the target (0.6963 for this mock); no fallback, no jump
def healing_escape(name, theta, seed=0, n_per_family=32, D=4, cfg=None, graded=G, warm=None, **kw):
    r = jumpy(name, theta, seed, n_per_family, D, cfg, graded, warm)
    scale = float(np.exp(theta[2]))
    if seed == 2026 and len(calls) > N_COLLAPSE and scale >= 0.684661:
        r["gain"] = 0.03 * (scale / 0.86) ** 5.2  # the jump is gone: the lower branch everywhere
    return r
calls.clear(); warms.clear()
S.expected_gain = healing_escape
e = S.calibrate_gain("M3L", 0.01, {"pi0": 0.05}, seed=2026, cfg=None, D=4)
assert e["note"] == "" and e["bracket_reevaluated"] and not e["fallback_remeasured"] and e["gain_jump"] == 0.0, e["note"]
assert abs(e["gain"] - 0.01) <= 0.05 * 0.01 and abs(e["scale"] - 0.6963) < 0.01, (e["scale"], e["gain"])
assert all(c[1] == 2026 for c in calls[:-1]) and calls[-1][1] == 3026
print(f"healed with escape: bracket widened from the visited scales, resolved at {e['scale']:.4f} after {len(calls) - 1} evaluations OK")

# 4. the same jump with a fallback re-measurement outside 25 %: the gate refuses on the calibration side
def jumpy_bad(name, theta, seed=0, n_per_family=32, D=4, cfg=None, graded=G, warm=None, **kw):
    r = jumpy(name, theta, seed, n_per_family, D, cfg, graded, warm)
    if seed == 2526:
        r["gain"] = 0.0070
    return r
calls.clear(); warms.clear()
S.expected_gain = jumpy_bad
e = S.calibrate_gain("M3L", 0.01, {"pi0": 0.05}, seed=2026, cfg=None, D=4)
assert "calibration gain" in e["note"], e["note"]
print(f"jump with a bad re-measurement: gate says '{e['note']}' OK")

# 5. target outside the bracket is refused as before
S.expected_gain = lambda name, theta, seed=0, n_per_family=32, D=4, cfg=None, graded=G, warm=None, **kw: dict(
    gain=0.5, se=1e-4, best="M2K", gains={}, converged=CONV, **REPRO)
e = S.calibrate_gain("M3L", 0.01, {"pi0": 0.05}, seed=2026, cfg=None, D=4)
assert "outside the bracket" in e["note"] and not np.isfinite(e["scale"])
print("target outside the bracket refused OK")

# 6. a reference reached by one distinct cold start only (the d4v12b mechanism) is refused by the gate, in either draw
def lonely(name, theta, seed=0, n_per_family=32, D=4, cfg=None, graded=G, warm=None, **kw):
    r = smooth(name, theta, seed, n_per_family, D, cfg, graded, warm)
    if seed == 3026:
        r.update(starts_at_best={g: 1 for g in G}, warm_at_best={g: 1 for g in G}, ref_reproduced=False)
    return r
calls.clear(); warms.clear()
S.expected_gain = lonely
e = S.calibrate_gain("M3L", 0.01, {"pi0": 0.05}, seed=2026, cfg=None, D=4)
assert "fewer than 2 starts in the check draw" in e["note"], e["note"]
assert e["check_starts_at_best"]["M2K"] == 1 and e["check_warm_at_best"]["M2K"] == 1 and e["calib_starts_at_best"]["M2K"] == 3
print(f"reference reached by one cold start: gate says '{e['note']}' OK")

# 7. the helpers. _starts_at_best counts DISTINCT cold/extra runs within 0.5 nat of the best converged solution over
#    every source; a warm run never counts as a cold discovery (Codex, finding 1); an unconverged run never counts
deep, shallow = -44543.62, -44698.90
runs = [dict(converged=True, loglik=shallow, source="cold", theta=[0.0])] * 7 + [dict(converged=True, loglik=deep, source="cold", theta=[1.0])]
assert S._starts_at_best(runs) == 1
assert S._starts_at_best(runs + [dict(converged=True, loglik=deep - 0.3, source="extra", theta=[1.0])]) == 2
assert S._starts_at_best(runs + [dict(converged=True, loglik=deep, source="warm", theta=[1.0])]) == 1        # warm excluded
assert S._starts_at_best(runs + [dict(converged=True, loglik=deep, source="warm", theta=[1.0])], sources=("warm",)) == 1
assert S._starts_at_best(runs + [dict(converged=False, loglik=deep, source="cold", theta=[1.0])]) == 1        # unconverged excluded
only_shallow = runs[:7]
assert S._starts_at_best(only_shallow + [dict(converged=True, loglik=deep, source="warm", theta=[1.0])]) == 0   # cold runs do not reach the best combined solution
assert S._basin_candidates(runs + [dict(converged=True, loglik=shallow + 0.1, source="cold", theta=[0.5])]) == [[1.0], [0.5]]   # best run per cluster
w = {}
S._merge_warm(w, "M2K", [[1.0, 2.0]]); S._merge_warm(w, "M2K", [[1.00001, 2.0], [3.0, 4.0]])
assert w["M2K"] == [[3.0, 4.0], [1.0, 2.0]]                # deduplicated to 4 decimals, newest first
assert S._warm_list({"M2K": [1.0, 2.0]}, "M2K", 2)[0].tolist() == [1.0, 2.0] and S._warm_list({"M2K": [[1.0, 2.0], [3.0, float("nan")]]}, "M2K", 2).__len__() == 1
assert S._warm_list(None, "M2K", 2) == [] and S._warm_list({"M2K": [1.0]}, "M2K", 2) == []

# 8. the extra batch: never the unjittered moment start (the cold batch holds it), skew coordinates mirrored on
#    every second start; checked with the start generator mocked to a known array
moment = np.array([3.0, 1.5, 1.0, 0.1, 0.7, 1.0, 0.5, 0.25])
def fake_starts(name, data, n, rng, jitter_sd):
    out = np.tile(moment, (n, 1)); out[1:] += 0.01 * np.arange(1, n)[:, None]; return out
_orig = S.M.starts_from_moments
S.M.starts_from_moments = fake_starts
st = S._extra_starts("M2K", None, 6, np.random.default_rng(0))
S.M.starts_from_moments = _orig
assert st.shape == (6, 8) and not any(np.array_equal(r, moment) for r in st)
assert np.all(st[0::2, 6:] > 0) and np.all(st[1::2, 6:] < 0) and np.all(st[:, :6] > 0)     # alpha0, alpha1 mirrored on rows 1, 3, 5
print("helpers: distinct cold-start counting by source, basin candidates, warm merge, extra batch without the moment start and skew-mirrored OK")
