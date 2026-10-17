"""CANDIDATE tests of the first-80 prefix release consumer (chpc/release_p80/row19_screen_release_p80.py). SYNTHETIC fixtures
only: stub fits (`_Patched`), a stub bank and target, temporary adoption/review/certificate/controller files under reviews/
removed at the end, a synthetic ledger / plans / gate receipts in the fixture's temporary campaign. Nothing here reads, unseals
or computes anything from the sealed screen; nothing is a scientific result.

    .venv/bin/python chpc/release_p80/test_row19_screen_release_p80.py        (from workspace_demo/t1_access)

1. S has 60 IDs and includes 83; numpy's linear percentile at B = 80 is .025 X2 + .975 X3 (lower) and .975 X78 + .025 X79
   (upper), one-based order statistics.
2. The 98.5 % one-sided CP cutoff at n = 60 is exactly K_max <= 48 (bounds at 47, 48, 49 printed); the attempted-set guard
   is computed exactly on a table of (K_max, M).
3. B4: K_min / K_max by the exact sweep - adjacent floats, touching endpoints, large finite values, exact-rational brute force.
4. B2: only the valid sandwich and attempted-set corners are reported; Codex's deterministic [0,0]/[1,1] counterexample.
5. B3: the cluster companion carries no decision.
6. No decision before all 60 are terminal (pure rule and the release path, which then computes nothing).
7. Prefix validation HOLDS on a record of another parent (a B = 80 relabel), another seed, another draw row, another index,
   another dataset; the release fits nothing; out-of-prefix records are never read.
8. B1: a missing coordinate is terminal only under an exact, review-bound terminal certificate verified against the v16
   controller's ledger / plans / receipts; refusals for invented attempts, free-form / foreign / changed / unreviewed
   certificates, still-live or ambiguous ownership, too few or other-envelope crashes, mismatched settlement or exhaustion
   evidence, a disabled rescue route, the v15 controller; one accepted certificate per branch.
9. Parity: the prefix formula over all 200 records equals analyze.refit_bootstrap's strict restore; the cluster companion
   equals analyze.analyze_dataset's; the released refit interval is np.percentile over records 0..79.
10. The seal: the adopted consumer's adoption schema is refused here, and this adoption is refused by the adopted consumer; a
   changed contract, a missing release literal or a producer B other than 200 refuses."""
import os, sys, json, copy, glob, math, shutil, tempfile, time, random, importlib.util
from fractions import Fraction
os.environ.setdefault("NPROC", "1")

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (T1, os.path.join(T1, "chpc"), HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
os.chdir(T1)
import numpy as np
import analyze as A
import test_row19_screen as TS                          # the adopted screen tests' fixtures (bank, target, manifests, stubs)
from test_row19_slice import _Patched, CALLS
import row19_shard as SH
import row19_screen_orig as O
import row19_screen_release as REL
import row19_screen_admit as SA_LIVE                    # the live (v15) controller, imported BEFORE the candidate is loaded
import row19_screen_release_p80 as P

# The v16 candidate controller (the representation the certificate is verified against), loaded under its own name; its
# directory is removed from sys.path again so `import row19_screen_admit` keeps resolving to the live file.
CAND_DIR = os.path.join(T1, "chpc", "candidate_v16")
_spec = importlib.util.spec_from_file_location("r19_admit_v16_candidate", os.path.join(CAND_DIR, "row19_screen_admit.py"))
CAND = importlib.util.module_from_spec(_spec); sys.modules["r19_admit_v16_candidate"] = CAND; _spec.loader.exec_module(CAND)
while CAND_DIR in sys.path:
    sys.path.remove(CAND_DIR)
assert sys.modules["row19_screen_admit"] is SA_LIVE
E48 = dict(queue="serial", cores=24, walltime_s=172800.0, mem_gb=120, nodetype="haswell_reg", deadline_reserve_s=1800)
E30 = dict(E48, walltime_s=108000.0)
ENV = {"of": lambda n: E48}
CAND.resolve_envelope = lambda man, mp, role, n: (ENV["of"](int(n)), "")      # synthetic envelope (the pinned policy is not read)

fails = []
PASSED = [0]
RELEASE_FITS = [0]                                       # analyze.run_dataset calls made INSIDE release calls (must stay 0)


def check(name, cond, detail=""):
    print(("ok   " if cond else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
    if not cond:
        fails.append(name)
    else:
        PASSED[0] += 1


def covered(k, n, lo=0.4, hi=0.6):
    return [(0.0, 1.0)] * k + [(5.0, 6.0)] * (n - k)


def _raises(f):
    try:
        f(); return False
    except Exception:
        return True


# ---------------------------------------------------------------------------------------------------------------------------
# 1-6: pure rules
# ---------------------------------------------------------------------------------------------------------------------------
def test_designated_set():
    S = P.DESIGNATED
    check("S has 60 IDs within 3..102", len(S) == 60 and min(S) == 3 and max(S) <= 102)
    check("S includes rep 83", 83 in S)
    check("S is the ID rule only", S == tuple(r for r in range(3, 103) if (r - 3) % 5 in (0, 1, 2)) and S[:6] == (3, 4, 5, 8, 9, 10))


def test_interpolation_at_80():
    rng = np.random.default_rng(1)
    for trial in range(20):
        v = rng.normal(size=80); X = np.sort(v)                        # X[k-1] is the one-based X_k
        lo, hi = np.percentile(v, 2.5), np.percentile(v, 97.5)
        check_lo = abs(lo - (0.025 * X[1] + 0.975 * X[2])) < 1e-12
        check_hi = abs(hi - (0.975 * X[77] + 0.025 * X[78])) < 1e-12
        if not (check_lo and check_hi):
            check(f"interpolation trial {trial}", False, f"{lo} {hi}"); return
    check("np.percentile(., 2.5) at B = 80 is .025 X2 + .975 X3 (one-based), 20 random draws", True)
    check("np.percentile(., 97.5) at B = 80 is .975 X78 + .025 X79 (one-based), 20 random draws", True)
    recs = [dict(rep=i, failed=False, stats={p: {"ws": float(x)} for p in A.PREDICTORS}) for i, x in enumerate(v)]
    pi = P.prefix_interval(recs, 80, ["ws"])
    check("prefix_interval uses the same rule", pi["selection"]["bands"]["ws"]["lo"] == float(np.percentile(v, 2.5))
          and pi["selection"]["bands"]["ws"]["hi"] == float(np.percentile(v, 97.5)) and pi["selection"]["usable"])
    check("prefix_interval refuses any record set other than indices 0..79",
          _raises(lambda: P.prefix_interval(recs[:79] + [dict(recs[0], rep=80)], 80, ["ws"])))


def test_cp_cutoff_at_60():
    b = {k: P.cp_upper(k, 60) for k in (47, 48, 49)}
    print(f"     one-sided 98.5 % CP upper bounds at n = 60: 47 -> {b[47]:.6f}, 48 -> {b[48]:.6f}, 49 -> {b[49]:.6f}")
    check("CP(48, 60) < 0.90 < CP(49, 60)", b[48] < 0.90 < b[49])
    check("CP(47, 60) < 0.90", b[47] < 0.90)
    check("CP values at 47 / 48 / 49 are .887187 / .899615 / .911749",
          (round(b[47], 6), round(b[48], 6), round(b[49], 6)) == (0.887187, 0.899615, 0.911749))
    stops = [k for k in range(61) if P.decide(covered(k, 60), 0.4, 0.6, all_terminal=True)["decision"] == "STOP FOR FUTILITY"]
    check("with all 60 usable the stop region is exactly K_max <= 48", stops == list(range(49)), str(stops[-3:]))
    check("the bound is 1 at k = n and the rule needs integers", P.cp_upper(60, 60) == 1.0 and _raises(lambda: P.cp_upper(48.0, 60)))
    d = P.decide(covered(48, 60), 0.4, 0.6, all_terminal=True)
    check("the decision reports [Kmin/n, Kmax/n], the valid sandwich and M", d["coverage_range"] == [0.8, 0.8] and d["M_unavailable"] == 0
          and abs(d["sandwich"]["upper_at_k_max"] - b[48]) < 1e-15 and d["sandwich"]["lower_at_k_min"] == P.cp_lower(48, 60) < 0.8
          and d["upper"] == d["sandwich"]["upper_at_k_max"])
    check("never PASS", all("PASS" not in P.decide(covered(k, 60), 0.4, 0.6, all_terminal=True)["decision"] for k in range(61)))


def test_attempted_set_guard():
    """(K_max, M) -> stop?, computed exactly: both the complete-case bound at (K_max, 60 - M) and the all-60 bound at
    (K_max + M, 60) must be below 0.90."""
    table = [(46, 3), (47, 2), (46, 2), (47, 1), (48, 1), (45, 3), (40, 8), (30, 20), (48, 0), (49, 0)]
    for kx, M in table:
        n = 60 - M
        d = P.decide(covered(kx, n), 0.4, 0.6, all_terminal=True)
        u, ua = P.cp_upper(kx, n), P.cp_upper(kx + M, 60)
        want = (u < 0.90 and ua < 0.90)
        print(f"     K_max {kx:2d}, M {M:2d}: CP({kx},{n}) = {u:.6f}, CP({kx + M},60) = {ua:.6f} -> {d['decision']}")
        check(f"guard K_max {kx} + M {M}", d["decision"] == ("STOP FOR FUTILITY" if want else "not ruled out at this look")
              and d["M_unavailable"] == M and d["n_usable"] == n and abs(d["upper_all_attempted"] - ua) < 1e-15
              and d["attempted_envelope"]["upper_at_k_max_plus_M"] == ua and d["attempted_envelope"]["lower_at_k_min"] == P.cp_lower(kx, 60))
    check("K_max 46 + M 3 is NOT a stop (46 + 3 = 49 > 48)", P.decide(covered(46, 57), .4, .6, all_terminal=True)["decision"] != "STOP FOR FUTILITY")
    check("K_max 47 + M 2 is NOT a stop (49 > 48)", P.decide(covered(47, 58), .4, .6, all_terminal=True)["decision"] != "STOP FOR FUTILITY")
    check("K_max 46 + M 2 IS a stop (48)", P.decide(covered(46, 58), .4, .6, all_terminal=True)["decision"] == "STOP FOR FUTILITY")
    check("K_max 47 + M 1 IS a stop (48)", P.decide(covered(47, 59), .4, .6, all_terminal=True)["decision"] == "STOP FOR FUTILITY")
    only_cc = [(kx, M) for M in range(0, 30) for kx in range(0, 61 - M)
               if P.cp_upper(kx, 60 - M) < 0.90 and not P.cp_upper(kx + M, 60) < 0.90]
    check("the guard removes every complete-case stop with K_max + M > 48", all(kx + M > 48 for kx, M in only_cc) and len(only_cc) > 0,
          f"{len(only_cc)} complete-case stops vetoed, e.g. {only_cc[:3]}")
    allm = [(kx, M) for M in range(0, 30) for kx in range(0, 61 - M) if P.cp_upper(kx + M, 60) < 0.90 and not P.cp_upper(kx, 60 - M) < 0.90]
    check("the complete-case bound never vetoes an all-60 failure on M < 30", allm == [], str(allm[:3]))
    check("n_usable 0 is unresolved, never a stop", P.decide([], .4, .6, all_terminal=True)["decision"] == "unresolved: no usable interval")


def _old_midpoint_k_min(intervals, lo, hi):
    """The superseded candidate-set minimum (midpoints), kept here ONLY to show the B4 defect it had."""
    pts = sorted({lo, hi} | {x for a, b in intervals for x in (a, b) if lo <= x <= hi})
    cand = list(pts) + [(pts[k] + pts[k + 1]) / 2.0 for k in range(len(pts) - 1)]
    return min(sum(1 for a, b in intervals if a <= th <= b) for th in cand)


def _exact_brute(intervals, lo, hi):
    """(K_min, K_max) by exact rational evaluation at every point and the exact rational midpoint of every segment."""
    F = [(Fraction(a), Fraction(b)) for a, b in intervals]; L, H = Fraction(lo), Fraction(hi)
    pts = sorted({L, H} | {x for a, b in F for x in (a, b) if L <= x <= H})
    cand = pts + [(pts[k] + pts[k + 1]) / 2 for k in range(len(pts) - 1)]
    cnt = [sum(1 for a, b in F if a <= th <= b) for th in cand]
    return min(cnt), max(cnt)


def test_k_min_k_max_exact():
    up = math.nextafter(1.0, math.inf)
    iv = [(0.0, 1.0), (up, 2.0)]
    gap = Fraction(1) + Fraction(1, 2 ** 53)
    check("B4 adjacent floats: the real 1 + 2^-53 lies strictly between 1.0 and nextafter(1.0) and in neither interval",
          Fraction(1.0) < gap < Fraction(up) and not any(Fraction(a) <= gap <= Fraction(b) for a, b in iv))
    check("B4 adjacent floats [(0,1), (nextafter(1),2)], T = [0,2]: K_min = 0 (the superseded midpoint code gave 1)",
          P.k_min(iv, 0.0, 2.0) == 0 and _old_midpoint_k_min(iv, 0.0, 2.0) == 1 and P.k_max(iv, 0.0, 2.0) == 1)
    check("touching endpoints [(0,1),(1,2)], T = [0,2]: K_max 2 (inclusive at 1), K_min 1",
          P.k_max([(0.0, 1.0), (1.0, 2.0)], 0.0, 2.0) == 2 and P.k_min([(0.0, 1.0), (1.0, 2.0)], 0.0, 2.0) == 1)
    check("touching endpoints, T = [1,1] (a single point): K_min = K_max = 2", P.k_min([(0, 1), (1, 2)], 1.0, 1.0) == 2 == P.k_max([(0, 1), (1, 2)], 1.0, 1.0))
    check("a degenerate interval [1,1] touching T's end counts inclusively", P.k_max([(1.0, 1.0)], 0.0, 1.0) == 1 and P.k_min([(1.0, 1.0)], 0.0, 1.0) == 0)
    big = sys.float_info.max
    ivb = [(-big, big), (0.5 * big, big)]
    check("large finite values: [(-max, max), (max/2, max)], T = [-max, max]: K_min 1, K_max 2, no overflow "
          "(the superseded midpoint overflowed to inf and gave 0)",
          P.k_min(ivb, -big, big) == 1 and P.k_max(ivb, -big, big) == 2 and _old_midpoint_k_min(ivb, -big, big) == 0)
    rnd = random.Random(19)
    ok_all, ok_adopted = True, True
    for _ in range(300):
        iv = []
        for _k in range(rnd.randint(1, 7)):
            a, b = sorted(rnd.choice([rnd.randint(-4, 4) / 2.0, math.nextafter(rnd.randint(-2, 2) / 1.0, math.inf)]) for _j in range(2))
            iv.append((a, b))
        lo, hi = sorted(rnd.randint(-5, 5) / 2.0 for _j in range(2))
        if (P.k_min(iv, lo, hi), P.k_max(iv, lo, hi)) != _exact_brute(iv, lo, hi):
            ok_all = False
        if P.k_max(iv, lo, hi) != REL.k_max(iv, lo, hi):
            ok_adopted = False
    check("the sweep equals exact rational brute force on 300 random cases (half-integers and adjacent floats)", ok_all)
    check("the sweep's K_max equals the adopted consumer's k_max (K_max is attained at a closed point)", ok_adopted)
    check("k_min over T with an uncovered segment", P.k_min([(0, 1), (2, 3)], 0.5, 2.5) == 0)
    check("k_min over a T inside every interval", P.k_min([(0, 1), (0.4, 0.6), (0.3, 3)], 0.45, 0.55) == 3)
    check("k_min at a T end just outside one interval", P.k_min([(0, 1), (0, 0.5)], 0.4, 0.6) == 1 and P.k_max([(0, 1), (0, 0.5)], 0.4, 0.6) == 2)
    check("no interval: K_min = K_max = 0", P.k_min([], 0.0, 1.0) == 0 == P.k_max([], 0.0, 1.0))
    check("non-finite or unordered input is refused", _raises(lambda: P.k_min([(0.0, float("nan"))], 0, 1)) and _raises(lambda: P.k_min([(1.0, 0.0)], 0, 1))
          and _raises(lambda: P.k_min([(0.0, math.inf)], 0, 1)) and _raises(lambda: P.k_max([(0.0, 1.0)], 1.0, 0.0)))


def test_sandwich_counterexample():
    """B2, Codex's deterministic counterexample: 60 independent intervals, each [0,0] or [1,1] with probability 1/2, T = [0,1],
    true target 0 (coverage .5). Exact binomial sums, no simulation."""
    from scipy.stats import binom
    n = 60
    pmf = [float(binom.pmf(x, n, 0.5)) for x in range(n + 1)]
    ivs = lambda x: [(0.0, 0.0)] * x + [(1.0, 1.0)] * (n - x)
    km = [P.k_max(ivs(x), 0.0, 1.0) for x in range(n + 1)]; kn = [P.k_min(ivs(x), 0.0, 1.0) for x in range(n + 1)]
    check("selected counts: K_max = max(x, 60 - x), K_min = 0 (the open segment (0,1)) for every mixture",
          km == [max(x, n - x) for x in range(n + 1)] and kn == [0] * (n + 1))
    p_bad_lower = sum(pmf[x] for x in range(n + 1) if P.cp_lower(km[x], n) > 0.5)
    print(f"     P(L_CP(K_max, 60) > .5) = {p_bad_lower:.8f}; U_CP(K_min = 0, 60) = {P.cp_upper(0, n):.8f}")
    check("the opposite corner L_CP(K_max, 60) exceeds the true .5 with probability .02734013 > .015 (no guarantee)",
          abs(p_bad_lower - 0.02734013) < 5e-9 and p_bad_lower > 0.015)
    check("the opposite corner U_CP(K_min, 60) = .06760160 < .5 always (no guarantee)", abs(P.cp_upper(0, n) - 0.06760160) < 5e-9)
    miss = sum(pmf[x] for x in range(n + 1) if not (P.cp_lower(kn[x], n) <= 0.5 <= P.cp_upper(km[x], n)))
    check("the reported sandwich L_CP(K_min, 60) .. U_CP(K_max, 60) misses .5 with probability <= .03", miss <= 0.03, f"{miss}")
    d = P.describe(ivs(31), 0.0, 1.0)
    flat = json.dumps(d)
    check("only the valid sandwich and attempted-set corners are reported (no opposite corner, no 'exact' block)",
          "exact" not in d and "upper_at_k_min" not in flat and "lower_at_k_max" not in flat
          and set(d["sandwich"]) >= {"lower_at_k_min", "upper_at_k_max"} and set(d["attempted_envelope"]) >= {"lower_at_k_min", "upper_at_k_max_plus_M"})
    check("the sandwich is labelled one-sided 98.5 % each, two-sided 97 % conditional on theta_g in T, bank error separate",
          d["sandwich"]["one_sided_conf_each"] == 0.985 and d["sandwich"]["two_sided_conf"] == 0.97
          and d["sandwich"]["conditional_on"] == "theta_g in T" and "4 %" in d["sandwich"]["note"])
    check("sandwich values: lower at K_min = 0 is 0, upper at K_max = 31 is CP(31, 60)",
          d["sandwich"]["lower_at_k_min"] == 0.0 and d["sandwich"]["upper_at_k_max"] == P.cp_upper(31, n))


def _keys_named(obj, name):
    if isinstance(obj, dict):
        return name in obj or any(_keys_named(v, name) for v in obj.values())
    return isinstance(obj, list) and any(_keys_named(v, name) for v in obj)


def test_cluster_companion():
    lo, hi = 0.4, 0.6
    per = {3: dict(refit=[0.0, 1.0], cluster=[0.5, 0.55], refit_usable=True, cluster_usable=True),
           4: dict(refit=[0.0, 0.45], cluster=[0.7, 0.8], refit_usable=True, cluster_usable=True),
           5: dict(refit=[None, None], cluster=[0.0, 1.0], refit_usable=False, cluster_usable=True),
           8: dict(refit=[0.0, 1.0], cluster=[None, None], refit_usable=True, cluster_usable=False),
           9: dict(refit=[None, None], cluster=[None, None], refit_usable=False, cluster_usable=False)}
    cc = P.cluster_companion(per, lo, hi, n_attempted=5)
    flat = json.dumps(cc)
    check("B3: the cluster companion carries no decision key and no STOP/PASS outcome anywhere",
          not _keys_named(cc, "decision") and "STOP FOR FUTILITY" not in flat and "not ruled out" not in flat and "COMPANION REPORT ONLY" in cc["role"])
    check("companion paired availability", cc["paired"] == dict(both=2, refit_only=1, cluster_only=1, neither=1))
    t = cc["containment"]["table"]
    check("companion containment cross table (refit rows x cluster columns, both usable)",
          t["contains T"]["meets T"] == 1 and t["meets T"]["misses T"] == 1 and sum(sum(r.values()) for r in t.values()) == 2
          and cc["containment"]["cluster_alone"] == {"contains T": 1, "meets T": 1, "misses T": 1})
    check("companion descriptive counts and sandwich over its 3 usable", cc["n_usable"] == 3 and cc["M_unavailable"] == 2
          and cc["k_max"] == 2 and "sandwich" in cc)


def test_terminality_states():
    """Original failed / original absent / missing uncertified / certified / complete, on synthetic collection items."""
    S = P.DESIGNATED
    items = {r: dict(original=dict(run=dict(failed=False)), records=[None] * 80, missing=[]) for r in S}
    items[S[0]] = dict(original=dict(run=dict(failed=True, failed_reason="original non-finite")), records=[], missing=list(range(80)))
    items[S[1]] = dict(original=None, records=[], missing=list(range(80)))
    items[S[2]] = dict(original=dict(run=dict(failed=False)), records=[None] * 78, missing=[3, 50])
    st, open_, conflict = P.terminality(items, {})
    check("a failed original is terminal with its reason, without its records", st[S[0]] == dict(terminal="original failed", reason="original non-finite"))
    check("an absent original is not terminal (no certificate route)", any(f"rep {S[1]}: no original" in w for w in open_))
    check("missing uncertified indices are not terminal", any(f"rep {S[2]}:" in w for w in open_) and S[2] not in st)
    check("complete datasets are terminal", all(st[r] == dict(terminal="complete") for r in S[3:]))
    cert = {(S[2], 3): dict(branch="rescue-failed"), (S[2], 50): dict(branch="allowance-exhausted")}
    st, open_, conflict = P.terminality(items, cert)
    check("certified missing coordinates make that dataset terminal", conflict == [] and S[2] in st
          and st[S[2]] == dict(terminal="certified missing", indices=[3, 50], branches={"3": "rescue-failed", "50": "allowance-exhausted"})
          and open_ == [f"rep {S[1]}: no original (an absent original has no certificate route)"])
    st, open_, conflict = P.terminality(items, {**cert, (S[3], 0): dict(branch="rescue-failed")})
    check("certifying a present index is a conflict", any("never relabelled" in w for w in conflict))
    st, open_, conflict = P.terminality(items, {**cert, (S[0], 4): dict(branch="rescue-failed")})
    check("certifying a coordinate of a failed-original dataset is a conflict", any("absent or failed" in w for w in conflict))


def test_no_decision_before_terminal():
    d = P.decide(covered(40, 60), 0.4, 0.6, all_terminal=False)
    check("the pure rule refuses before all 60 are terminal", d["decision"].startswith("REFUSED") and "k_max" not in d)


def test_snapshot_git():
    b, s, w = P.snapshot("chpc/row19_screen_release.py", check_git=True)
    check("snapshot: a tracked unmodified file is one read, hashed from those bytes", w == "" and s == REL.sha_file(os.path.join(T1, "chpc/row19_screen_release.py")))
    rel = os.path.join("reviews", f"_test_p80_{os.getpid()}_untracked.json"); open(os.path.join(T1, rel), "w").write("{}\n")
    try:
        b, s, w = P.snapshot(rel, check_git=True)
        check("snapshot: an untracked file is refused under check_git", b is None and "not git-tracked" in w)
    finally:
        os.remove(os.path.join(T1, rel))
    check("snapshot: an absent file is refused", P.snapshot("reviews/_absent_p80_.json", check_git=False)[2] != "")


# ---------------------------------------------------------------------------------------------------------------------------
# 7-10: the release path on a synthetic 100-rep, B = 200 screen (stub fits)
# ---------------------------------------------------------------------------------------------------------------------------
def _write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(json.dumps(obj) + "\n")


def build():
    t0 = time.time()
    bank, bmp, tgt = TS._bank()
    refit, rp, orig, op = TS._screen(bmp, reps=tuple(range(3, 103)), B=200)
    with _Patched():
        rc, out = TS._call(O, ["worker", "--manifest", op, "--reps", ",".join(map(str, P.DESIGNATED)), "--slot", "0", "--job-id", "o1",
                               "--skip-environment-check"])
        assert rc == 0, out
        tasks = {r: SH.task(refit, r) for r in P.DESIGNATED}
        for r in P.DESIGNATED:
            for i in range(P.PREFIX):
                _write(SH.record_path(refit["storage"]["root"], r, i), SH.resample_record(tasks[r], i))
    print(f"     fixture: 60 designated datasets x 80 stub records, {time.time() - t0:.1f} s")
    return bank, bmp, tgt, refit, rp, orig, op, tasks


class Files:
    """Temporary adoption / review / certificate / controller files under T1 (reviews/), removed at the end."""
    def __init__(self):
        self.made = []

    def path(self, name):
        rel = os.path.join("reviews", f"_test_p80_{os.getpid()}_{len(self.made)}_{name}"); self.made.append(rel); return rel        # unique per call

    def text(self, name, s):
        rel = self.path(name); open(os.path.join(T1, rel), "w").write(s); return rel

    def json(self, name, obj):
        rel = self.path(name + ".json"); json.dump(obj, open(os.path.join(T1, rel), "w")); return rel

    def clean(self):
        for rel in self.made:
            if os.path.exists(os.path.join(T1, rel)):
                os.remove(os.path.join(T1, rel))


def adoption(F, bank, bmp, tgt, rp, op, **over):
    tg = json.load(open(tgt)); tsha = REL.sha_file(tgt)
    rv = F.text("target_review.md", f"ADOPT row19-numerical-target target={tsha} bank_records={tg['records_sha256']} verdict=FAVOURABLE\n")
    rr = F.text("release_review.md", over.pop("release_text", P.release_literal(tsha) + "\n"))
    pins = {f: REL.sha_file(os.path.join(T1, f)) for f in P.CONSUMER_FILES}
    pins.update({f: REL.sha_file(os.path.join(T1, f)) for f in P.CONTROLLER_FILES.values() if os.path.exists(os.path.join(T1, f))})
    doc = dict(schema=P.ADOPTION_SCHEMA, target_sha256=tsha, bank_manifest_sha256=REL.sha_file(bmp),
               bank_binding_sha256=REL.sha_file(os.path.join(bank["storage"]["root"], "bank_binding.json")),
               manifests=dict(screen=REL.sha_file(rp), originals=REL.sha_file(op)),
               consumer_pins=pins,
               review_record=dict(path=rv, sha256=REL.sha_file(os.path.join(T1, rv))),
               prefix_contract=copy.deepcopy(P.CONTRACT), prefix_contract_sha256=P.contract_sha(),
               release_review_record=dict(path=rr, sha256=REL.sha_file(os.path.join(T1, rr))))
    doc.update(over)
    return F.json("adoption", doc)


def rel_(rp, op, tgt, ad, term=None, review=None, C=None):
    n = CALLS["run_dataset"]
    try:
        return P.release(rp, op, tgt, ad, terminal_rel=term, terminal_review_rel=review, check_git=False,
                         controller_module=CAND if C is None else C)
    finally:
        RELEASE_FITS[0] += CALLS["run_dataset"] - n


# ---- B1 fixture: the controller's representation (ledger, plans, gate receipts) in the synthetic campaign ----------------
def sdisp(jid, crashed):
    return {"slot_disposition": {"kind": CAND.CRASH_KIND, "job_id": jid,
                                  "slots": [dict(slot=k, rep=r, indices=[i], signal="Segmentation fault") for k, (r, i) in enumerate(crashed)]}}


def entry(n, state="settled"):
    e = dict(kind="shard", rep=n, job_id=f"{n}.s", token=f"t{n}", state=state, reserved_core_h=1152.0, attempt=1)
    if state == "settled":
        e.update(settled_core_h=1000.0 + n, settled_at=1.7e9 + n, settle_note=f"qstat -xf {n}.s", runner_exit=4)
    else:
        e.update(runner_exit=None)
    return e


class Ops:
    """Writes one scenario's ledger / plans / receipts / register (replacing the previous one)."""
    def __init__(self, refit):
        self.root, self.camp = refit["storage"]["root"], refit["storage"]["campaign"]

    def write(self, ledger, plans, receipts, register=None):
        for d in ("plans", "gate", "ec2"):
            shutil.rmtree(os.path.join(self.root, d), ignore_errors=True)
        json.dump({"cap_core_h": 81000.0, "entries": {e["token"]: e for e in ledger}}, open(os.path.join(self.camp, "budget.json"), "w"))
        for n, pl in plans.items():
            _write(os.path.join(self.root, "plans", f"job_{n}.json"), pl)
        out = []
        for stamp, jobs in receipts:
            rel = f"gate/watch_refit_{stamp}.json"
            _write(os.path.join(self.root, rel), dict(schema=CAND.WATCH_SCHEMA, role="refit", production=True, fresh=True, alarms=[], jobs=jobs))
            out.append(dict(path=rel, sha256=REL.sha_file(os.path.join(self.root, rel))))
        if register is not None:
            _write(os.path.join(self.root, "ec2", "register.json"), register)
        return out

    def clean(self):
        for d in ("plans", "gate", "ec2"):
            shutil.rmtree(os.path.join(self.root, d), ignore_errors=True)
        if os.path.exists(os.path.join(self.camp, "budget.json")):
            os.remove(os.path.join(self.camp, "budget.json"))


def plan(*coords, route=None):
    d = {"slots": [{"slot": k, "rep": r, "indices": [i]} for k, (r, i) in enumerate(coords)]}
    if route:
        d["route"] = route
    return d


def att(n, env=E48):
    return dict(job=n, job_id=f"{n}.s", signal="Segmentation fault", envelope=list(CAND.env_key(env)))


def settle(*ns):
    return {str(n): {k: entry(n)[k] for k in P.SETTLEMENT_FIELDS} for n in ns}


def controller_files(F, rescue_on):
    """(designated, controls) for the test controller: the candidate v16 bytes, or a synthetic rescue-enabled declaration
    with a controls copy whose latest version pins it."""
    cd, cc = "chpc/candidate_v16/row19_screen_designated.json", "chpc/candidate_v16/row19_screen_controls.json"
    if not rescue_on:
        return cd, cc
    d = json.load(open(os.path.join(T1, cd))); d["rescue"] = dict(d["rescue"], enabled=True, resources={"cores": 12, "note": "synthetic"})
    dr = F.json("designated_on", d)
    c = json.load(open(os.path.join(T1, cc))); c["versions"][-1]["files"][CAND.DESIGNATED] = REL.sha_file(os.path.join(T1, dr))
    return dr, F.json("controls_on", c)


def certificate(F, refit, rp, op, tgt, receipts, missing, settlements, rescue_allowance=None, review=True, review_text=None, **over):
    ctl = P.CONTROLLER_FILES
    c = json.load(open(os.path.join(T1, ctl["controls"])))
    cert = dict(schema=P.TERMINAL_SCHEMA, campaign=refit["storage"]["campaign"], root=refit["storage"]["root"],
                screen_manifest_sha256=REL.sha_file(rp), originals_manifest_sha256=REL.sha_file(op), contract_sha256=P.contract_sha(),
                target_sha256=REL.sha_file(tgt),
                controller=dict(admit_sha256=REL.sha_file(os.path.join(T1, ctl["admit"])), controls_sha256=REL.sha_file(os.path.join(T1, ctl["controls"])),
                                controls_version=c["versions"][-1]["version"], designated_sha256=REL.sha_file(os.path.join(T1, ctl["designated"]))),
                receipts=receipts, missing=missing, settlements=settlements)
    if rescue_allowance is not None:
        cert["rescue_allowance"] = rescue_allowance
    cert.update(over)
    cr = F.json("terminal_cert", cert)
    if not review:
        return cr, None
    lit = P.terminal_literal(REL.sha_file(os.path.join(T1, cr)), REL.sha_file(rp), REL.sha_file(tgt),
                             REL.sha_file(os.path.join(T1, ctl["controls"])))
    return cr, F.text("terminal_review.md", (review_text if review_text is not None else f"Reviewed.\n{lit}\n"))


def test_release_path():
    bank, bmp, tgt, refit, rp, orig, op, tasks = build()
    root = refit["storage"]["root"]
    F = Files(); ops = Ops(refit); keep_ctl = dict(P.CONTROLLER_FILES)
    try:
        ad = adoption(F, bank, bmp, tgt, rp, op)
        n0 = CALLS["run_dataset"]
        with _Patched():
            # --- a complete fixture releases, without fitting and without any certificate
            r = rel_(rp, op, tgt, ad)
            check("complete synthetic fixture RELEASES with no certificate", r["status"] == "RELEASED" and r["terminal_certificate_sha256"] is None,
                  str(r.get("reasons"))[:300])
            check("the release bought no fit", CALLS["run_dataset"] == n0)
            check("60 attempted, n_usable + M = 60", r["refit"]["n_attempted"] == 60 and r["refit"]["n_usable"] + r["refit"]["M_unavailable"] == 60)
            check("refit decision is futility-only", r["refit"]["decision"] in ("STOP FOR FUTILITY", "not ruled out at this look", "unresolved: no usable interval"))
            check("B3: only refit is decided; the cluster is a companion without a decision",
                  "cluster" not in r and not _keys_named(r["cluster_companion"], "decision") and "COMPANION REPORT ONLY" in r["cluster_companion"]["role"])
            check("B2: the released refit report carries only the valid sandwich and attempted-set corners",
                  "exact" not in r["refit"] and "upper_at_k_min" not in json.dumps(r["refit"]) and "lower_at_k_max" not in json.dumps(r["refit"]))
            r0 = P.DESIGNATED[0]; t = tasks[r0]
            recs = [SH.read_record(SH.record_path(root, r0, i), t, i) for i in range(80)]
            v = [s["stats"]["selection"]["ws"] for s in recs]
            check("released refit interval = np.percentile over records 0..79 (selection/ws)",
                  r["per_dataset"][str(r0)]["refit"] == [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))])

            # --- out-of-prefix records are never read, never credited
            for i in range(80, 200):
                _write(SH.record_path(root, r0, i), SH.resample_record(t, i))
            open(SH.record_path(root, r0, 150), "w").write("garbage, not JSON\n")
            r_b = rel_(rp, op, tgt, ad)
            check("an out-of-prefix record (even garbage at 150) changes nothing", r_b["status"] == "RELEASED"
                  and r_b["per_dataset"][str(r0)]["refit"] == r["per_dataset"][str(r0)]["refit"])
            _write(SH.record_path(root, r0, 150), SH.resample_record(t, 150))
            all200 = [SH.read_record(SH.record_path(root, r0, i), t, i) for i in range(200)]
            ck = os.path.join(tempfile.mkdtemp(), "chain.jsonl")
            open(ck, "w").write("".join(open(SH.record_path(root, r0, i)).read() for i in range(200)))
            keep = A.run_dataset; A.run_dataset = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no fit"))
            try:
                rb = A.refit_bootstrap(t["ds"], t["cfg"], t["seed"], n_rep=200, outer_folds=t["folds"], min_usable=1.0, checkpoint_path=ck, strict_restore=True)
                got, _ = O.read_cache(orig["storage"]["root"], t)
                res = A.analyze_dataset(t["ds"], t["cfg"], t["seed"], outer_folds=t["folds"], run=got["run"], interval_result=rb)
            finally:
                A.run_dataset = keep
            mine = P.prefix_interval(all200, 200, t["bands"])
            check("prefix formula at n = 200 equals analyze.refit_bootstrap's strict restore (every predictor and band)",
                  all(mine[p]["bands"][b] == rb["predictors"][p]["bands"][b] and mine[p]["n_used"] == rb["predictors"][p]["n_used"]
                      for p in A.PREDICTORS for b in t["bands"]))
            cw = res["predictors"]["selection"]["cluster"]["ws"]
            check("cluster companion interval equals analyze.analyze_dataset's", r["per_dataset"][str(r0)]["cluster"] == [cw["lo"], cw["hi"]])
            for i in range(80, 200):
                os.remove(SH.record_path(root, r0, i))

            # --- prefix validation HOLDS on a wrong parent / seed / draw / index / dataset
            r1 = P.DESIGNATED[1]; p4 = SH.record_path(root, r1, 4); good = open(p4).read()
            m80 = copy.deepcopy(refit); m80["cfg"]["n_boot_refit"] = 80
            t80 = SH.task(m80, r1)
            def held_with(obj, label):
                _write(p4, obj)
                n1 = CALLS["run_dataset"]
                x = rel_(rp, op, tgt, ad)
                open(p4, "w").write(good)
                check(f"HOLDS: {label}", x["status"] == "HELD" and any(f"rep {r1}" in w for w in x["reasons"]) and "refit" not in x
                      and CALLS["run_dataset"] == n1, str(x.get("reasons"))[:160])
            held_with(SH.resample_record(t80, 4), "a record of the B = 80 relabelled task (other parent identity, n_rep and draw)")
            d = json.loads(good); d["seed"] += 1; d["sha"] = A._record_sha(d); held_with(d, "another seed, checksum recomputed")
            d = json.loads(good); d["chosen"] = [int(c) for c in tasks[r1]["idx"][5]]; d["sha"] = A._record_sha(d)
            held_with(d, "another draw row (index 5's), checksum recomputed")
            d = json.loads(good); d["n_rep"] = 80; d["sha"] = A._record_sha(d); held_with(d, "n_rep relabelled to 80, checksum recomputed")
            d = json.loads(good); d["stats"]["selection"]["ws"] = 0.0; held_with(d, "a payload edit (checksum mismatch)")
            held_with(json.loads(open(SH.record_path(root, r1, 5)).read()), "index 5's record under index 4's name")
            held_with(json.loads(open(SH.record_path(root, P.DESIGNATED[2], 4)).read()), "another dataset's record")

            # --- an incomplete 80: a missing designated record without a certificate -> NOT TERMINAL and nothing computed
            r2 = P.DESIGNATED[2]; p7 = SH.record_path(root, r2, 7); g7 = open(p7).read(); os.remove(p7)
            n1 = CALLS["run_dataset"]
            x = rel_(rp, op, tgt, ad)
            check("an uncertified missing designated record -> NOT TERMINAL, no interval/count/decision",
                  x["status"] == "NOT TERMINAL" and any(f"rep {r2}" in w for w in x["reasons"]) and "refit" not in x and "per_dataset" not in x
                  and CALLS["run_dataset"] == n1, str(x.get("reasons"))[:160])
            for i in range(80, 82):                                          # later indices exist: they never substitute
                _write(SH.record_path(root, r2, i), SH.resample_record(tasks[r2], i))
            test_certificates(F, ops, bank, bmp, tgt, refit, rp, orig, op, r2, keep_ctl)
            open(p7, "w").write(g7)
            for i in range(80, 82):
                os.remove(SH.record_path(root, r2, i))
            P.CONTROLLER_FILES.clear(); P.CONTROLLER_FILES.update(keep_ctl); ops.clean()

            # --- one failed resample inside the 80 -> unavailable with the recorded reason; never the first 80 successes
            r3 = P.DESIGNATED[3]; p9 = SH.record_path(root, r3, 9); g9 = open(p9).read()
            CALLS["fail_all"] = True
            try:
                _write(p9, SH.resample_record(tasks[r3], 9))
            finally:
                CALLS["fail_all"] = False
            _write(SH.record_path(root, r3, 80), SH.resample_record(tasks[r3], 80))
            x = rel_(rp, op, tgt, ad)
            row = x["per_dataset"][str(r3)]
            check("one failed designated resample -> interval unavailable (79 of 80), index 80 not used",
                  row["status"] == "unavailable" and "79 of 80" in row["reason"] and "stub failure" in row["reason"]
                  and row["raw_prefix"]["selection"]["n_failed"] == 1, row["reason"][:120])
            open(p9, "w").write(g9); os.remove(SH.record_path(root, r3, 80))

            # --- the seal
            x = rel_(rp, op, tgt, adoption(F, bank, bmp, tgt, rp, op, schema=REL.ADOPTION_SCHEMA))
            check("the adopted consumer's adoption schema is refused here", x["status"] == "REFUSED" and any("schema" in w for w in x["reasons"]))
            x = REL.release(rp, op, tgt, ad, check_git=False)
            check("this adoption is refused by the adopted B = 200 consumer", x["status"] == "REFUSED" and any("schema" in w for w in x["reasons"]), str(x.get("status")) + str(x.get("reasons"))[:300])
            c2 = dict(copy.deepcopy(P.CONTRACT), prefix=79)
            x = rel_(rp, op, tgt, adoption(F, bank, bmp, tgt, rp, op, prefix_contract=c2))
            check("a changed prefix contract is refused", x["status"] == "REFUSED" and any("prefix_contract" in w for w in x["reasons"]))
            x = rel_(rp, op, tgt, adoption(F, bank, bmp, tgt, rp, op, release_text="reviewed, looks fine\n"))
            check("a release review without the ADOPT row19-p80-release literal is refused", x["status"] == "REFUSED"
                  and any("row19-p80-release" in w for w in x["reasons"]))
            pins = {f: REL.sha_file(os.path.join(T1, f)) for f in P.CONSUMER_FILES}; pins[P.SELF_REL] = "0" * 64
            x = rel_(rp, op, tgt, adoption(F, bank, bmp, tgt, rp, op, consumer_pins=pins))
            check("a wrong pin of this consumer is refused", x["status"] == "REFUSED" and any("pins" in w for w in x["reasons"]))
            check("the adopted consumer's schema/pins are restored after the seal", REL.ADOPTION_SCHEMA == "row19-target-adoption-1"
                  and P.SELF_REL not in REL.CONSUMER_FILES)
            s2 = copy.deepcopy(refit); s2["cfg"]["n_boot_refit"] = 80
            check("a producer B other than 200 is refused by the contract", any("parent B 200" in w for w in P.contract_problems(s2)))
            s3 = copy.deepcopy(refit); s3["cfg"]["refit_min_usable"] = 0.95
            check("refit_min_usable other than 1.0 is refused by the contract", any("refit_min_usable" in w for w in P.contract_problems(s3)))
            s4 = copy.deepcopy(refit); s4["datasets"]["reps"] = [r for r in s4["datasets"]["reps"] if r != 83]
            check("a manifest without rep 83 is refused by the contract", any("83" in w for w in P.contract_problems(s4)))
        check("no release call fitted anything (fits counted inside release calls only)", RELEASE_FITS[0] == 0, str(RELEASE_FITS[0]))
    finally:
        P.CONTROLLER_FILES.clear(); P.CONTROLLER_FILES.update(keep_ctl)
        ops.clean(); F.clean()


def test_certificates(F, ops, bank, bmp, tgt, refit, rp, orig, op, r2, keep_ctl):
    """B1 on the synthetic screen with rep r2 index 7 missing (later indices 80, 81 present)."""
    c = (r2, 7)
    root = refit["storage"]["root"]

    def setup(rescue_on=True):
        dr, cr = controller_files(F, rescue_on)
        P.CONTROLLER_FILES.clear(); P.CONTROLLER_FILES.update(admit="chpc/candidate_v16/row19_screen_admit.py", controls=cr, designated=dr)
        return adoption(F, bank, bmp, tgt, rp, op)

    def held(x, needle, label):
        ok = x["status"] == "HELD" and any(needle in w for w in x["reasons"]) and "refit" not in x
        check(f"B1 refuses: {label}", ok, str(x.get("reasons"))[:220])

    std_ledger = [entry(1), entry(2), entry(3)]
    std_plans = {1: plan(c, (3, 0)), 2: plan(c), 3: plan(c, route=P.RESCUE_ROUTE)}
    std_jobs = {"1": dict(sdisp("1.s", [c]), state="F"), "2": dict(sdisp("2.s", [c]), state="F"), "3": dict(state="F", exit=0)}
    std_missing = lambda **o: [dict(dict(rep=r2, index=7, branch="rescue-failed", crashes=[att(1), att(2)], rescue=dict(job=3, job_id="3.s")), **o)]

    # ---- the accepted exact certificate, rescue-failed branch
    ad = setup(True)
    rc = ops.write(std_ledger, std_plans, [("20261101T000000Z", std_jobs)])
    cr, rv = certificate(F, refit, rp, op, tgt, rc, std_missing(), settle(1, 2, 3))
    x = rel_(rp, op, tgt, ad, cr, rv)
    row = x.get("per_dataset", {}).get(str(r2), {})
    check("B1 ACCEPTS an exact review-bound certificate (two same-envelope crashes + a settled rescue-route attempt)",
          x["status"] == "RELEASED" and x["terminal_certificate_sha256"] == REL.sha_file(os.path.join(T1, cr))
          and x["terminal_certified"] == {f"{r2}/7": dict(branch="rescue-failed", crash_jobs=[1, 2], rescue_job=3)}, str(x.get("reasons"))[:300])
    check("a certified coordinate makes the interval unavailable (index 80 never substitutes), M counts it",
          row.get("status") == "unavailable" and row.get("refit_usable") is False and "certified missing" in row.get("reason", "")
          and str(r2) in x["unavailable"] and x["refit"]["M_unavailable"] >= 1 and x["refit"]["n_usable"] == 60 - x["refit"]["M_unavailable"])
    check("its cluster companion stays reported (paired partition)", row.get("cluster_usable") is True and x["cluster_companion"]["paired"]["cluster_only"] >= 1)

    # ---- refusals (each certificate is otherwise exact and reviewed, so only the named defect differs)
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, std_missing(crashes=["one invented attempt"]), settle(1, 2, 3))
    held(rel_(rp, op, tgt, ad, cr2, rv2), "invented or missing attempts", "Codex's invented attempt string")
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, std_missing(crashes=[att(1), att(2), att(9)]), settle(1, 2, 3))
    held(rel_(rp, op, tgt, ad, cr2, rv2), "invented or missing attempts", "an extra fabricated attempt (job 9)")
    fr = F.json("free_form", dict(schema="row19-p80-terminal-1", rescue_exhausted=[dict(rep=r2, index=7, reason="declare terminal now", attempts=["one invented attempt"])]))
    held(rel_(rp, op, tgt, ad, fr, F.text("ff_review.md", P.terminal_literal(REL.sha_file(os.path.join(T1, fr)), REL.sha_file(rp), REL.sha_file(tgt), REL.sha_file(os.path.join(T1, P.CONTROLLER_FILES["controls"]))) + "\n")),
         "free-form declaration", "the superseded free-form declaration (Codex's synthetic reproduction), even with a literal")
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, std_missing(), settle(1, 2, 3), campaign="/elsewhere/row19_screen_campaign")
    held(rel_(rp, op, tgt, ad, cr2, rv2), "foreign or stale", "a foreign campaign")
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, std_missing(), settle(1, 2, 3), target_sha256="0" * 64)
    held(rel_(rp, op, tgt, ad, cr2, rv2), "foreign or stale", "another target")
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, std_missing(), settle(1, 2, 3), contract_sha256="0" * 64)
    held(rel_(rp, op, tgt, ad, cr2, rv2), "foreign or stale", "another contract")
    ctl_bad = json.load(open(os.path.join(T1, cr))); ctl_bad["controller"]["controls_version"] = 15
    cr2 = F.json("cert_v15", ctl_bad)
    rv2 = F.text("v15_review.md", P.terminal_literal(REL.sha_file(os.path.join(T1, cr2)), REL.sha_file(rp), REL.sha_file(tgt), REL.sha_file(os.path.join(T1, P.CONTROLLER_FILES["controls"]))) + "\n")
    held(rel_(rp, op, tgt, ad, cr2, rv2), "foreign or stale", "another controller identity (controls version)")
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, std_missing(), settle(1, 2, 3))
    d = json.load(open(os.path.join(T1, cr2))); d["missing"][0]["branch"] = "allowance-exhausted"; json.dump(d, open(os.path.join(T1, cr2), "w"))
    held(rel_(rp, op, tgt, ad, cr2, rv2), "unreviewed or changed", "a certificate changed after its review")
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, std_missing(), settle(1, 2, 3), review_text="reviewed, looks fine\n")
    held(rel_(rp, op, tgt, ad, cr2, rv2), "unreviewed or changed", "a review record without the ADOPT row19-p80-terminal literal")
    cr2, _ = certificate(F, refit, rp, op, tgt, rc, std_missing(), settle(1, 2, 3), review=False)
    held(rel_(rp, op, tgt, ad, cr2, None), "separate tracked review record", "a certificate without any review record")
    ad_nopin = adoption(F, bank, bmp, tgt, rp, op); dd = json.load(open(os.path.join(T1, ad_nopin))); del dd["consumer_pins"][P.CONTROLLER_FILES["designated"]]
    json.dump(dd, open(os.path.join(T1, ad_nopin), "w"))
    held(rel_(rp, op, tgt, ad_nopin, cr, rv), "does not pin the controller", "an adoption that does not pin the controller's designated declaration")
    held(rel_(rp, op, tgt, ad, cr, rv, C=SA_LIVE), "no terminal representation", "the live v15 controller (no crash/ownership representation)")

    # still-live / ambiguous ownership
    ops.write(std_ledger + [entry(4, state="live")], {**std_plans, 4: plan(c)}, [("20261101T000000Z", std_jobs)])
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, std_missing(), settle(1, 2, 3))
    held(rel_(rp, op, tgt, ad, cr2, rv2), "still owns it", "a coordinate a live job still owns")
    ops.write(std_ledger, {**std_plans, 5: plan(c)}, [("20261101T000000Z", std_jobs)])
    held(rel_(rp, op, tgt, ad, cr2, rv2), "ownership ambiguous", "a coordinate in a plan without a ledger entry")
    ops.write(std_ledger, std_plans, [("20261101T000000Z", std_jobs)], register={"attempts": {"a1": {"state": "launched", "coordinates": {f"{r2}/7": {}}}}})
    held(rel_(rp, op, tgt, ad, cr2, rv2), "EC2 register", "a coordinate named by an EC2 register attempt")
    led_unsettled = [entry(1), entry(2, state="live"), entry(3)]
    ops.write(led_unsettled, std_plans, [("20261101T000000Z", std_jobs)])
    held(rel_(rp, op, tgt, ad, cr2, rv2), "still owns it", "a crash attempt whose job is not settled")
    ec2_c = (24, 3)
    rc_e = ops.write([entry(1), entry(2)], {1: plan((3, 0)), 2: plan((3, 1))}, [("20261101T000000Z", {"1": dict(state="F", exit=0)})])
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc_e, [dict(rep=24, index=3, branch="allowance-exhausted", crashes=[])], {},
                           rescue_allowance=dict(allowance_core_h=2304.0, rescue_jobs={}, full_reservation_core_h=1152.0))
    held(rel_(rp, op, tgt, ad, cr2, rv2), "outside Lengau's scope", "an unclaimed EC2-designated coordinate (waits for the EC2 epoch)")

    # crash-rule evidence
    rc1 = ops.write([entry(1), entry(3)], {1: plan(c), 3: plan(c, route=P.RESCUE_ROUTE)},
                    [("20261101T000000Z", {"1": dict(sdisp("1.s", [c]), state="F"), "3": dict(state="F", exit=0)})])
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc1, std_missing(crashes=[att(1)]), settle(1, 3))
    held(rel_(rp, op, tgt, ad, cr2, rv2), "same-envelope fatal crashes", "only one fatal crash")
    rc = ops.write(std_ledger, std_plans, [("20261101T000000Z", std_jobs)])
    ENV["of"] = lambda n: E30 if n <= 2 else E48
    try:
        cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, std_missing(crashes=[att(1, E30), att(2, E30)]), settle(1, 2, 3))
        held(rel_(rp, op, tgt, ad, cr2, rv2), "same-envelope fatal crashes", "two crashes in another envelope than the next ordinary job's")
    finally:
        ENV["of"] = lambda n: E48
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, std_missing(crashes=[dict(att(1), signal="Bus error"), att(2)]), settle(1, 2, 3))
    held(rel_(rp, op, tgt, ad, cr2, rv2), "invented or missing attempts", "an attempt whose signal differs from the receipt's")
    rc_b = list(rc); rc_b[0] = dict(rc_b[0], sha256="0" * 64)
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc_b, std_missing(), settle(1, 2, 3))
    held(rel_(rp, op, tgt, ad, cr2, rv2), "not the certified bytes", "a bound receipt whose bytes changed")
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, std_missing(), settle(1, 2, 3))
    _write(os.path.join(root, "gate", "watch_refit_20261102T000000Z.json"),
           dict(schema=CAND.WATCH_SCHEMA, role="refit", production=True, fresh=True, alarms=[], jobs=dict(std_jobs, **{"4": dict(sdisp("4.s", [c]), state="F")})))
    held(rel_(rp, op, tgt, ad, cr2, rv2), "newest gate receipt", "a newer receipt carrying a further attempt")
    rc = ops.write(std_ledger, std_plans, [("20261101T000000Z", std_jobs)])
    bad_settle = settle(1, 2, 3); bad_settle["2"]["settled_core_h"] = 1.0
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, std_missing(), bad_settle)
    held(rel_(rp, op, tgt, ad, cr2, rv2), "settlement receipts", "a settlement receipt that is not the ledger's")
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, std_missing(), settle(1, 2))
    held(rel_(rp, op, tgt, ad, cr2, rv2), "settlement receipts", "the rescue job's settlement not bound")

    # mismatched exhaustion evidence
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, [dict(rep=r2, index=7, branch="allowance-exhausted", crashes=[att(1), att(2)])], settle(1, 2),
                           rescue_allowance=dict(allowance_core_h=2304.0, rescue_jobs={"3": 1152.0}, full_reservation_core_h=1152.0))
    held(rel_(rp, op, tgt, ad, cr2, rv2), "its branch is rescue-failed", "allowance-exhausted while a rescue attempt held the coordinate")
    rc = ops.write([entry(1), entry(2), entry(3)], {1: plan(c), 2: plan(c), 3: plan((3, 0), route=P.RESCUE_ROUTE)},
                   [("20261101T000000Z", {"1": std_jobs["1"], "2": std_jobs["2"]})])
    ex_missing = [dict(rep=r2, index=7, branch="allowance-exhausted", crashes=[att(1), att(2)])]
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, ex_missing, settle(1, 2),
                           rescue_allowance=dict(allowance_core_h=2304.0, rescue_jobs={"3": 1152.0}, full_reservation_core_h=1152.0))
    held(rel_(rp, op, tgt, ad, cr2, rv2), "not exhausted", "an allowance with a full reservation left")
    rc = ops.write([entry(1), entry(2), entry(3), entry(4)], {1: plan(c), 2: plan(c), 3: plan((3, 0), route=P.RESCUE_ROUTE), 4: plan((3, 1), route=P.RESCUE_ROUTE)},
                   [("20261101T000000Z", {"1": std_jobs["1"], "2": std_jobs["2"]})])
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, ex_missing, settle(1, 2),
                           rescue_allowance=dict(allowance_core_h=2304.0, rescue_jobs={"3": 1152.0}, full_reservation_core_h=1152.0))
    held(rel_(rp, op, tgt, ad, cr2, rv2), "rescue-allowance evidence", "exhaustion evidence that omits a rescue job")
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, std_missing(), settle(1, 2, 3))
    held(rel_(rp, op, tgt, ad, cr2, rv2), "not the one rescue-route plan", "a rescue-failed claim naming a rescue job that never held it")
    # ---- the accepted exact certificate, allowance-exhausted branch (two settled full rescue reservations used elsewhere)
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, ex_missing, settle(1, 2),
                           rescue_allowance=dict(allowance_core_h=2304.0, rescue_jobs={"3": 1152.0, "4": 1152.0}, full_reservation_core_h=1152.0))
    x = rel_(rp, op, tgt, ad, cr2, rv2)
    check("B1 ACCEPTS an exact allowance-exhausted certificate (two crashes; the finite 2,304 core-h allowance fully reserved and settled)",
          x["status"] == "RELEASED" and x["terminal_certified"] == {f"{r2}/7": dict(branch="allowance-exhausted", crash_jobs=[1, 2], rescue_job=None)},
          str(x.get("reasons"))[:300])
    # a disabled rescue route (the actual candidate v16 declaration)
    ad_off = setup(False)
    rc = ops.write([entry(1), entry(2)], {1: plan(c), 2: plan(c)}, [("20261101T000000Z", {"1": std_jobs["1"], "2": std_jobs["2"]})])
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, std_missing(), settle(1, 2))
    held(rel_(rp, op, tgt, ad_off, cr2, rv2), "rescue route is disabled", "rescue-failed under the v16 declaration (rescue DISABLED)")
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, ex_missing, settle(1, 2),
                           rescue_allowance=dict(allowance_core_h=2304.0, rescue_jobs={}, full_reservation_core_h=1152.0))
    held(rel_(rp, op, tgt, ad_off, cr2, rv2), "not exhausted", "allowance-exhausted under the v16 declaration (nothing spent: disabled is a hold, not exhaustion)")
    # a certificate naming a coordinate that holds a valid record HOLDS (terminality conflict)
    ad = setup(True)
    rc = ops.write([entry(1), entry(2), entry(3)], {1: plan((r2, 8)), 2: plan((r2, 8)), 3: plan((r2, 8), route=P.RESCUE_ROUTE)},
                   [("20261101T000000Z", {"1": dict(sdisp("1.s", [(r2, 8)]), state="F"), "2": dict(sdisp("2.s", [(r2, 8)]), state="F")})])
    cr2, rv2 = certificate(F, refit, rp, op, tgt, rc, [dict(rep=r2, index=8, branch="rescue-failed", crashes=[att(1), att(2)], rescue=dict(job=3, job_id="3.s"))],
                           settle(1, 2, 3))
    x = rel_(rp, op, tgt, ad, cr2, rv2)
    check("B1: a certificate naming a coordinate that holds a valid record HOLDS (never relabelled)",
          x["status"] == "HELD" and any("never relabelled" in w for w in x["reasons"]), str(x.get("reasons"))[:200])


def test_cli_writes_once():
    out = os.path.join(tempfile.mkdtemp(), "r.json"); open(out, "w").write("{}")
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = P.main(["--screen", "x", "--originals", "y", "--target", "z", "--adoption", "w", "--out", out])
    check("the CLI refuses an existing result file before anything else", rc == 2 and "written once" in buf.getvalue())


if __name__ == "__main__":
    for f in (test_designated_set, test_interpolation_at_80, test_cp_cutoff_at_60, test_attempted_set_guard, test_k_min_k_max_exact,
              test_sandwich_counterexample, test_cluster_companion, test_no_decision_before_terminal, test_terminality_states,
              test_snapshot_git, test_cli_writes_once, test_release_path):
        print(f"== {f.__name__}")
        f()
    print(f"\n{PASSED[0]} / {PASSED[0] + len(fails)} ok; {'ALL OK' if not fails else 'FAILURES: ' + ', '.join(fails)}")
    sys.exit(1 if fails else 0)
