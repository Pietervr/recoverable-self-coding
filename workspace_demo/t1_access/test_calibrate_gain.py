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
        return base(name, theta, seed, n_per_family, warm, 0.0095 if seed == 2526 else 0.0104, 0.0005, **kw)
    b = 0.03 * (scale / 0.86) ** 5.2
    return base(name, theta, seed, n_per_family, warm, b if scale < 0.684661 else b + 0.0029, 7e-4, **kw)

challenged = []
_base = base
def base(name, theta, seed, n_per_family, warm, gain, se=1e-4, **kw):   # records which calls carried the challenge
    challenged.append(bool(kw.get("challenge")))
    return _base(name, theta, seed, n_per_family, warm, gain, se)

# 1. continuous: resolved within tolerance, no jump, no re-evaluation; then the FINAL evaluation at the chosen scale
#    with the training-only challenge (it is the one gated and archived), then the check at seed + 1000 and 64 per
#    family, challenged too; the warm set carries every scale visited so far (newest first), the check included
S.expected_gain = lambda name, theta, seed=0, n_per_family=32, D=4, cfg=None, graded=G, warm=None, **kw: base(
    name, theta, seed, n_per_family, warm, 0.03 * float(np.exp(theta[2])) ** 5.2, **kw)
e = S.calibrate_gain("M3L", 0.01, {"pi0": 0.05}, seed=2026, cfg=None, D=4)
assert e["note"] == "" and e["gain_jump"] == 0.0 and not e["bracket_reevaluated"] and not e["fallback_remeasured"]
assert abs(e["gain"] - 0.01) <= 0.05 * 0.01 and e["gain_search"] == e["gain"], e
assert calls[-1][1] == 3026 and calls[-1][2] == 64 and all(c[1] == 2026 for c in calls[:-1])
assert calls[-2] == (round(e["scale"], 6), 2026, 32) and challenged[-2:] == [True, True] and not any(challenged[:-2])
assert e["calib_seed"] == 2026 and e["calib_n_per_family"] == 32 and e["check_seed"] == 3026
assert warms[0] is None and all(w["M2K"][0] == calls[i - 1][0] for i, w in enumerate(warms) if i > 0), warms[:3]
assert len(warms[-1]["M2K"]) == S.REF_MAX_CANDIDATES + 2, warms[-1]
assert e["calib_runs"] == {g: [] for g in G} and e["check_runs"] == {g: [] for g in G}, e["calib_runs"]
assert abs(e["check_theta"]["M2K"][0] - e["scale"]) < 1e-9 and abs(e["calib_theta"]["M2K"][0] - e["scale"]) < 1e-9
print(f"continuous gain: scale {e['scale']:.5f} in {len(calls) - 2} search evaluations + the challenged final, gain {e['gain']:.5f}, "
      f"warm candidates carried (capped at {S.REF_MAX_CANDIDATES + 2}) OK")

# 2. the jump: the bracket collapses (never within 5 %), both ends are re-evaluated with the warm set — lo, then hi,
#    then lo AGAIN because hi's evaluation added a basin to the warm set — still a jump; the scale is frozen at
#    0.68466, jump ≈ 0.0029 recorded, the gain re-measured at seed 2526 with 64 per family (the declared fallback,
#    which is the challenged final evaluation), the check at 3026, the gate passes
calls.clear(); warms.clear(); challenged.clear()
S.expected_gain = jumpy
e = S.calibrate_gain("M3L", 0.01, {"pi0": 0.05}, seed=2026, cfg=None, D=4)
assert e["note"] == "", e["note"]
assert abs(e["scale"] - 0.684661) < 0.684661 * 1e-3, e["scale"]
assert e["bracket_reevaluated"] and e["fallback_remeasured"] and abs(e["gain_jump"] - 0.0029) < 2e-4, e["gain_jump"]
assert e["gain"] == 0.0095 and e["gain_check"] == 0.0104 and e["calib_seed"] == 2526 and e["calib_n_per_family"] == 64
sc = round(e["scale"], 6)
assert calls[-1] == (sc, 3026, 64) and calls[-2] == (sc, 2526, 64) and challenged[-2:] == [True, True] and not any(challenged[:-2])
lo_c, hi_c = calls[-4], calls[-3]                 # the re-evaluated bracket ends at the calibration seed (both scales were
assert lo_c[1] == hi_c[1] == 2026 and lo_c[0] < sc < hi_c[0] and hi_c[0] / lo_c[0] - 1 < S.MIN_BRACKET_WIDTH   # visited before, so no new basin, no refresh)
n_bisect = len(calls) - 6
assert n_bisect < 20, n_bisect                       # 0.1 % bracket width from [0.02, 3] takes ≈ 14 steps, not 30
assert e["trace"][-1]["seed"] == 2526 and e["trace"][-1]["n_per_family"] == 64
N_COLLAPSE = len(calls) - 4                       # evaluations up to the collapse: 2 ends + the bisection steps
print(f"jump: scale frozen at {e['scale']:.6f} after {n_bisect} bisection steps + 2 re-evaluations, jump {e['gain_jump']:.5f}, "
      f"gain {e['gain']} check {e['gain_check']} — gate '{e['note'] or 'pass'}' OK")

# 2a. the upper endpoint's re-evaluation finds a basin the lower had not seen: the lower endpoint is refreshed
#     before the pair is read (review 3, finding 1, second half)
def new_basin_at_hi(name, theta, seed=0, n_per_family=32, D=4, cfg=None, graded=G, warm=None, **kw):
    r = jumpy(name, theta, seed, n_per_family, D, cfg, graded, warm, **kw)
    scale = float(np.exp(theta[2]))
    if seed == 2026 and len(calls) > N_COLLAPSE and scale >= 0.684661:
        r["candidates"] = {g: [[scale], [scale + 100.0]] for g in G}     # a second, new basin
    return r
calls.clear(); warms.clear(); challenged.clear()
S.expected_gain = new_basin_at_hi
e = S.calibrate_gain("M3L", 0.01, {"pi0": 0.05}, seed=2026, cfg=None, D=4)
tail = calls[N_COLLAPSE:]
assert [c[1] for c in tail] == [2026, 2026, 2026, 2526, 3026] and tail[0] == tail[2] and tail[0][0] < tail[1][0], tail
assert warms[N_COLLAPSE + 2]["M2K"][0] == round(tail[1][0] + 100.0, 6)     # the refreshed lo saw the new basin
assert e["fallback_remeasured"] and e["note"] == ""
print("new basin at the upper end: lower end refreshed with it before the jump is read OK")

# 2b. the LOWER endpoint wins the re-evaluation and its own final evaluation is not reproduced: the gate must read
#     the final evaluation at the chosen scale, not the last endpoint evaluated (review 3, finding 1)
def lower_wins(name, theta, seed=0, n_per_family=32, D=4, cfg=None, graded=G, warm=None, **kw):
    r = jumpy(name, theta, seed, n_per_family, D, cfg, graded, warm, **kw)
    scale = float(np.exp(theta[2]))
    if seed == 2026 and len(calls) > N_COLLAPSE and scale < 0.684661:
        r["gain"] = r["gain"] + 0.0009            # the lower end, re-evaluated: 0.01007, within tolerance
        if kw.get("challenge"):
            r.update(starts_at_best={g: 1 for g in G}, ref_reproduced=False)
    return r
calls.clear(); warms.clear(); challenged.clear()
S.expected_gain = lower_wins
e = S.calibrate_gain("M3L", 0.01, {"pi0": 0.05}, seed=2026, cfg=None, D=4)
assert e["scale"] < 0.684661 and e["bracket_reevaluated"] and not e["fallback_remeasured"]
assert "fewer than 2 starts in the calibration draw" in e["note"], e["note"]
assert e["calib_starts_at_best"]["M2K"] == 1 and challenged[-2:] == [True, True] and calls[-2] == (round(e["scale"], 6), 2026, 32)
print(f"lower endpoint wins: the challenged final evaluation at {e['scale']:.6f} is the one gated — '{e['note']}' OK")

# 3a. a jump that the re-evaluation heals AT the bracket end (the warm set finds the better basin there and its
#     value is within tolerance): resolved at that end, no fallback, no jump recorded
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
print(f"healed with escape: bracket widened from the visited scales, resolved at {e['scale']:.4f} after {len(calls) - 2} search evaluations OK")

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
assert S._starts_at_best(runs + [dict(converged=True, loglik=deep, source="challenge", theta=[1.0])]) == 2       # an independently seeded challenge discovery counts
same_x0 = [dict(converged=True, loglik=deep, source="cold", theta=[1.0], x0=[0.1, 0.2])] * 3 + [dict(converged=True, loglik=deep, source="extra", theta=[1.0], x0=[0.1, 0.2])]
assert S._starts_at_best(same_x0) == 1                                                   # one initial vector, however often it is run
assert S._starts_at_best(same_x0 + [dict(converged=True, loglik=deep, source="extra", theta=[1.0], x0=[0.3, 0.2])]) == 2
tagged = S._tag([dict(loglik=1.0, converged=True, theta=[0.0], nit=1)] * 2, "extra", np.array([[1.23456789, 2.0], [3.0, 4.0]]), batch="extra:1:3:1")
assert tagged[0]["x0"] == [1.23457, 2.0] and tagged[1]["batch"] == "extra:1:3:1" and tagged[0]["source"] == "extra"
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

# 9. the final training-only challenge batch (review 3, finding 6): for a skew member, four deliberately separated
#    starts at every sign combination of ±ALPHA_SEP in the alpha coordinates, then jittered starts at twice the
#    jitter, never the unjittered moment start; for a member without skew parameters, jittered starts only
_om, _sm = S.M.moments, S.M.start_from_moments
S.M.moments, S.M.start_from_moments, S.M.starts_from_moments = (lambda d: {}), (lambda n, m: moment.copy()), fake_starts
ch = S._challenge_starts("M2K", None, 8, np.random.default_rng(0))
assert ch.shape == (8, 8) and sorted(map(tuple, ch[:4, 6:].tolist())) == sorted([(a, b) for a in (2.0, -2.0) for b in (2.0, -2.0)])
assert np.all(ch[:4, :6] == moment[:6]) and not any(np.array_equal(r, moment) for r in ch[4:])
ch2 = S._challenge_starts("M2B", None, 5, np.random.default_rng(0))
assert ch2.shape[0] == 5 and not any(np.array_equal(r, moment) for r in ch2)
S.M.moments, S.M.start_from_moments, S.M.starts_from_moments = _om, _sm, _orig
print("helpers: distinct cold-start counting by initial vector and source, basin candidates, warm merge, extra batch without the "
      "moment start and skew-mirrored, challenge batch with separated skew starts OK")

# 10. the cold reference fit keeps every start's provenance through the §9 recovery chain (review 4, finding 3):
#     with the optimiser mocked so that no cold start converges and the recovery batch does, all twenty runs carry
#     their initial vector and batch id, and only the converged recovery discoveries count — as distinct vectors
import models as M
tiny = S.make_dataset("M2K", S.generator_theta("M2K", alpha=1.0), n_per_family=1, D=1, layers=(41,), rho=0.0, seed=3)
train = M.Trials.build(tiny.y[:, 0], tiny.k, tiny.concept, tiny.n_concepts)
batches = []
def fake_run_starts(name, data, starts, n_gh, options):
    batches.append(len(starts))
    conv = len(batches) > 1                       # the first (cold) batch fails to converge, the recovery batch converges
    return [dict(start=i, theta=np.asarray(x0, float), loglik=-100.0 - (0.0 if conv else 50.0), converged=conv, nfev=1, nit=1, message="")
            for i, x0 in enumerate(starts)]
_rs = S.M._run_starts
S.M._run_starts = fake_run_starts
runs, level, secs = S._fit_reference("M2K", train, 4, np.random.default_rng([2026, 7, 3]), 20, tag="t")
S.M._run_starts = _rs
assert level == 1 and batches == [4, 16] and len(runs) == 20
assert all(r.get("x0") is not None and len(r["x0"]) == 8 for r in runs)
assert [r["batch"] for r in runs[:4]] == ["cold:t"] * 4 and [r["batch"] for r in runs[4:]] == ["recovery1:t"] * 16
assert len({tuple(r["x0"]) for r in runs}) == 20
assert S._starts_at_best(runs) == 16 and S._starts_at_best(runs, sources=("cold",)) == 0
print("reference fit provenance: cold and recovery starts each carry their initial vector and batch; counts are of distinct vectors OK")
