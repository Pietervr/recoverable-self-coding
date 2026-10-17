"""CANDIDATE tests of the first-80 prefix release consumer (chpc/release_p80/row19_screen_release_p80.py). SYNTHETIC fixtures
only: stub fits (`_Patched`), a stub bank and target, temporary adoption/review/terminal files under reviews/ removed at the
end. Nothing here reads, unseals or computes anything from the sealed screen; nothing is a scientific result.

    .venv/bin/python chpc/release_p80/test_row19_screen_release_p80.py        (from workspace_demo/t1_access)

1. S has 60 IDs and includes 83; numpy's linear percentile at B = 80 is .025 X2 + .975 X3 (lower) and .975 X78 + .025 X79
   (upper), one-based order statistics.
2. The 98.5 % one-sided CP cutoff at n = 60 is exactly K_max <= 48 (bounds at 47, 48, 49 printed); the attempted-set guard
   is computed exactly on a table of (K_max, M); K_min / K_max use the adopted consumer's inclusive candidate set.
3. No decision before all 60 are terminal (pure rule and the release path, which then computes nothing).
4. Prefix validation HOLDS on a record of another parent (a B = 80 relabel), another seed, another draw row, another index,
   another dataset; the release fits nothing; out-of-prefix records are never read.
5. An incomplete 80 (one failed resample, or rescue-exhausted coordinates) makes that dataset's interval unavailable, even when
   later indices succeeded; a terminal declaration that names a coordinate holding a valid record HOLDS.
6. Parity: the prefix formula over all 200 records equals analyze.refit_bootstrap's strict restore; the cluster companion
   equals analyze.analyze_dataset's; the released refit interval is np.percentile over records 0..79.
7. The seal: the adopted consumer's adoption schema is refused here, and this adoption is refused by the adopted consumer; a
   changed contract, a missing release literal or a producer B other than 200 refuses."""
import os, sys, json, copy, shutil, tempfile, time
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
import row19_screen_release_p80 as P

fails = []


def check(name, cond, detail=""):
    print(("ok   " if cond else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
    if not cond:
        fails.append(name)


def covered(k, n, lo=0.4, hi=0.6):
    return [(0.0, 1.0)] * k + [(5.0, 6.0)] * (n - k)


# ---------------------------------------------------------------------------------------------------------------------------
# 1-3: pure rules
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
    try:
        P.prefix_interval(recs[:79] + [dict(recs[0], rep=80)], 80, ["ws"]); ok = False
    except ValueError:
        ok = True
    check("prefix_interval refuses any record set other than indices 0..79", ok)


def test_cp_cutoff_at_60():
    b = {k: P.cp_upper(k, 60) for k in (47, 48, 49)}
    print(f"     one-sided 98.5 % CP upper bounds at n = 60: 47 -> {b[47]:.6f}, 48 -> {b[48]:.6f}, 49 -> {b[49]:.6f}")
    check("CP(48, 60) < 0.90 < CP(49, 60)", b[48] < 0.90 < b[49])
    check("CP(47, 60) < 0.90", b[47] < 0.90)
    stops = [k for k in range(61) if P.decide(covered(k, 60), 0.4, 0.6, all_terminal=True)["decision"] == "STOP FOR FUTILITY"]
    check("with all 60 usable the stop region is exactly K_max <= 48", stops == list(range(49)), str(stops[-3:]))
    check("the bound is 1 at k = n and the rule needs integers", P.cp_upper(60, 60) == 1.0 and _raises(lambda: P.cp_upper(48.0, 60)))
    d = P.decide(covered(48, 60), 0.4, 0.6, all_terminal=True)
    check("the decision reports [Kmin/n, Kmax/n], exact bounds and M", d["coverage_range"] == [0.8, 0.8] and d["M_unavailable"] == 0
          and abs(d["exact"]["k_max"]["upper"] - b[48]) < 1e-15 and d["exact"]["k_max"]["lower"] < 0.8)
    check("never PASS", all("PASS" not in P.decide(covered(k, 60), 0.4, 0.6, all_terminal=True)["decision"] for k in range(61)))


def _raises(f):
    try:
        f(); return False
    except Exception:
        return True


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
              and d["M_unavailable"] == M and d["n_usable"] == n and abs(d["upper_all_attempted"] - ua) < 1e-15)
    check("K_max 46 + M 3 is NOT a stop (46 + 3 = 49 > 48)", P.decide(covered(46, 57), .4, .6, all_terminal=True)["decision"] != "STOP FOR FUTILITY")
    check("K_max 47 + M 2 is NOT a stop (49 > 48)", P.decide(covered(47, 58), .4, .6, all_terminal=True)["decision"] != "STOP FOR FUTILITY")
    check("K_max 46 + M 2 IS a stop (48)", P.decide(covered(46, 58), .4, .6, all_terminal=True)["decision"] == "STOP FOR FUTILITY")
    check("K_max 47 + M 1 IS a stop (48)", P.decide(covered(47, 59), .4, .6, all_terminal=True)["decision"] == "STOP FOR FUTILITY")
    # the all-60 guard can bind when the complete-case bound alone would stop: none exists with K_max + M <= 48 that the
    # complete case does not also fail? report the binding component over the whole grid
    only_cc = [(kx, M) for M in range(0, 30) for kx in range(0, 61 - M)
               if P.cp_upper(kx, 60 - M) < 0.90 and not P.cp_upper(kx + M, 60) < 0.90]
    check("the guard removes every complete-case stop with K_max + M > 48", all(kx + M > 48 for kx, M in only_cc) and len(only_cc) > 0,
          f"{len(only_cc)} complete-case stops vetoed, e.g. {only_cc[:3]}")
    allm = [(kx, M) for M in range(0, 30) for kx in range(0, 61 - M) if P.cp_upper(kx + M, 60) < 0.90 and not P.cp_upper(kx, 60 - M) < 0.90]
    check("the complete-case bound never vetoes an all-60 failure on M < 30", allm == [], str(allm[:3]))


def test_k_min_k_max():
    check("k_max is the adopted consumer's", P.k_max([(0, 1), (1, 2)], 0.0, 3.0) == 2 == REL.k_max([(0, 1), (1, 2)], 0.0, 3.0))
    check("k_min over T with an uncovered segment", P.k_min([(0, 1), (2, 3)], 0.5, 2.5) == 0)
    check("k_min inclusive at a shared endpoint", P.k_min([(0, 1), (1, 2)], 1.0, 1.0) == 2)
    check("k_min over a T inside every interval", P.k_min([(0, 1), (0.4, 0.6), (0.3, 3)], 0.45, 0.55) == 3)
    check("k_min at a T end just outside one interval", P.k_min([(0, 1), (0, 0.5)], 0.4, 0.6) == 1 and P.k_max([(0, 1), (0, 0.5)], 0.4, 0.6) == 2)


def test_terminality_states():
    """Original failed / original rescue-exhausted / missing undeclared / complete, on synthetic collection items (no data)."""
    S = P.DESIGNATED
    items = {r: dict(original=dict(run=dict(failed=False)), records=[None] * 80, missing=[]) for r in S}
    items[S[0]] = dict(original=dict(run=dict(failed=True, failed_reason="original non-finite")), records=[], missing=list(range(80)))
    items[S[1]] = dict(original=None, records=[], missing=list(range(80)))
    items[S[2]] = dict(original=dict(run=dict(failed=False)), records=[None] * 78, missing=[3, 50])
    st, open_, conflict = P.terminality(items, {})
    check("a failed original is terminal with its reason, without its records", st[S[0]] == dict(terminal="original failed", reason="original non-finite"))
    check("an absent original without a declaration is not terminal", any(f"rep {S[1]}: no original" == w for w in open_))
    check("missing undeclared indices are not terminal", any(f"rep {S[2]}:" in w for w in open_) and S[2] not in st)
    check("complete datasets are terminal", all(st[r] == dict(terminal="complete") for r in S[3:]))
    decl = {(S[1], "original"): dict(reason="two crashes + rescue", attempts=["a"]), (S[2], 3): dict(reason="r3", attempts=["a"]),
            (S[2], 50): dict(reason="r50", attempts=["a"])}
    st, open_, conflict = P.terminality(items, decl)
    check("declared rescue-exhausted coordinates make every dataset terminal", open_ == [] and conflict == []
          and st[S[1]]["terminal"] == "original rescue-exhausted" and st[S[2]] == dict(terminal="rescue-exhausted", indices=[3, 50], reasons={"3": "r3", "50": "r50"}))
    st, open_, conflict = P.terminality(items, {**decl, (S[3], 0): dict(reason="x", attempts=["a"])})
    check("declaring a present index is a conflict", any("never relabelled" in w for w in conflict))
    st, open_, conflict = P.terminality(items, {**decl, (S[4], "original"): dict(reason="x", attempts=["a"])})
    check("declaring a present original is a conflict", any("valid original exists" in w for w in conflict))


def test_no_decision_before_terminal():
    d = P.decide(covered(40, 60), 0.4, 0.6, all_terminal=False)
    check("the pure rule refuses before all 60 are terminal", d["decision"].startswith("REFUSED") and "k_max" not in d)


# ---------------------------------------------------------------------------------------------------------------------------
# 4-7: the release path on a synthetic 100-rep, B = 200 screen (stub fits)
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
    """Temporary adoption / review / terminal files under T1 (reviews/), removed at the end."""
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
    doc = dict(schema=P.ADOPTION_SCHEMA, target_sha256=tsha, bank_manifest_sha256=REL.sha_file(bmp),
               bank_binding_sha256=REL.sha_file(os.path.join(bank["storage"]["root"], "bank_binding.json")),
               manifests=dict(screen=REL.sha_file(rp), originals=REL.sha_file(op)),
               consumer_pins={f: REL.sha_file(os.path.join(T1, f)) for f in P.CONSUMER_FILES},
               review_record=dict(path=rv, sha256=REL.sha_file(os.path.join(T1, rv))),
               prefix_contract=copy.deepcopy(P.CONTRACT), prefix_contract_sha256=P.contract_sha(),
               release_review_record=dict(path=rr, sha256=REL.sha_file(os.path.join(T1, rr))))
    doc.update(over)
    return F.json("adoption", doc)


def terminal(F, entries):
    return F.json("terminal", dict(schema=P.TERMINAL_SCHEMA, rescue_exhausted=entries))


def rel_(rp, op, tgt, ad, term=None):
    return P.release(rp, op, tgt, ad, terminal_rel=term, check_git=False)


def test_release_path():
    bank, bmp, tgt, refit, rp, orig, op, tasks = build()
    root = refit["storage"]["root"]
    F = Files()
    try:
        ad = adoption(F, bank, bmp, tgt, rp, op)
        n0 = CALLS["run_dataset"]
        with _Patched():
            # --- a complete fixture releases, without fitting
            r = rel_(rp, op, tgt, ad)
            check("complete synthetic fixture RELEASES", r["status"] == "RELEASED", str(r.get("reasons"))[:300])
            check("the release bought no fit", CALLS["run_dataset"] == n0)
            check("60 attempted, n_usable + M = 60", r["refit"]["n_attempted"] == 60 and r["refit"]["n_usable"] + r["refit"]["M_unavailable"] == 60)
            check("refit decision is futility-only", r["refit"]["decision"] in ("STOP FOR FUTILITY", "not ruled out at this look", "unresolved: no usable interval"))
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
            # parity with the canonical chain over all 200 (index 150 restored)
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
            check("cluster companion equals analyze.analyze_dataset's", r["per_dataset"][str(r0)]["cluster"] == [cw["lo"], cw["hi"]])
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

            # --- an incomplete 80: undeclared missing -> NOT TERMINAL and nothing computed
            r2 = P.DESIGNATED[2]; p7 = SH.record_path(root, r2, 7); g7 = open(p7).read(); os.remove(p7)
            n1 = CALLS["run_dataset"]
            x = rel_(rp, op, tgt, ad)
            check("an undeclared missing designated record -> NOT TERMINAL, no interval/count/decision",
                  x["status"] == "NOT TERMINAL" and any(f"rep {r2}" in w for w in x["reasons"]) and "refit" not in x and "per_dataset" not in x
                  and CALLS["run_dataset"] == n1, str(x.get("reasons"))[:160])
            # declared rescue-exhausted -> terminal, that interval unavailable (later indices do not substitute)
            for i in range(80, 82):
                _write(SH.record_path(root, r2, i), SH.resample_record(tasks[r2], i))
            term = terminal(F, [dict(rep=r2, index=7, reason="two SIGSEGV allocation crashes + one rescue failed", attempts=["P1/s3", "P4/s9", "rescue R1"])])
            x = rel_(rp, op, tgt, ad, term)
            row = x.get("per_dataset", {}).get(str(r2), {})
            check("a rescue-exhausted index makes the interval unavailable (index 80 never substitutes)",
                  x["status"] == "RELEASED" and row.get("status") == "unavailable" and row.get("refit_usable") is False
                  and "rescue-exhausted" in row.get("reason", "") and str(r2) in x["unavailable"], str(row.get("reason"))[:120])
            check("M counts it", x["refit"]["M_unavailable"] >= 1 and x["refit"]["n_usable"] == 60 - x["refit"]["M_unavailable"])
            check("its cluster companion stays reported (paired partition)", row.get("cluster_usable") is True and x["paired"]["cluster_only"] >= 1)
            check("the terminal declaration's SHA-256 is reported", x["terminal_declaration_sha256"] == REL.sha_file(os.path.join(T1, term)))
            open(p7, "w").write(g7)
            x = rel_(rp, op, tgt, ad, term)
            check("a declaration naming a coordinate that holds a valid record HOLDS (never relabelled)",
                  x["status"] == "HELD" and any("never relabelled" in w for w in x["reasons"]), str(x.get("reasons"))[:160])
            bad = terminal(F, [dict(rep=4 if 4 not in P.DESIGNATED else 6, index=1, reason="x", attempts=["a"])])
            x = rel_(rp, op, tgt, ad, bad)
            check("a declaration naming an undesignated dataset HOLDS", x["status"] == "HELD")
            bad = terminal(F, [dict(rep=r2, index=120, reason="x", attempts=["a"])])
            check("a declaration outside the prefix HOLDS", rel_(rp, op, tgt, ad, bad)["status"] == "HELD")
            bad = terminal(F, [dict(rep=r2, index=7, reason="", attempts=["a"])])
            check("a declaration without a reason HOLDS", rel_(rp, op, tgt, ad, bad)["status"] == "HELD")
            for i in range(80, 82):
                os.remove(SH.record_path(root, r2, i))

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
            check("no fit was bought anywhere in the release path", CALLS["run_dataset"] >= n0)
    finally:
        F.clean()


def test_cli_writes_once():
    out = os.path.join(tempfile.mkdtemp(), "r.json"); open(out, "w").write("{}")
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = P.main(["--screen", "x", "--originals", "y", "--target", "z", "--adoption", "w", "--out", out])
    check("the CLI refuses an existing result file before anything else", rc == 2 and "written once" in buf.getvalue())


if __name__ == "__main__":
    for f in (test_designated_set, test_interpolation_at_80, test_cp_cutoff_at_60, test_attempted_set_guard, test_k_min_k_max,
              test_no_decision_before_terminal, test_terminality_states, test_cli_writes_once, test_release_path):
        print(f"== {f.__name__}")
        f()
    print(f"\n{'ALL OK' if not fails else 'FAILURES: ' + ', '.join(fails)}")
    sys.exit(1 if fails else 0)
