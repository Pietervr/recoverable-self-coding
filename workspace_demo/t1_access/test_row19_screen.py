"""Row 19 stage 2, the screen (Codex RSC 9202e8b acceptance contracts 1-5): the lossless original producer, the admission
controller, the producer-runtime verifier's anchor rule, the status view, and the SEALED release. Stub fits only (`_Patched`),
tiny B; nothing here is a scientific result.
1. A seed collision, a wrong identity, a damaged or conflicting cache HOLD; the producer's cache IS the slice runner's original
   cache (read back by row19_slice.read_orig, bit-equal full run), is never overwritten, and a failed original is kept.
2. A complete chain with an absent, unadopted, changed or unresolved target - or a changed bank, record set, consumer pin or
   manifest - is refused BEFORE any refit-percentile, cluster, decision or coverage call; a missing original or record
   HOLDS and buys no fit; the release itself can never fit.
3. Qualification binds only the started tasks; a failed or unparseable scheduler query, a missing or differing anchor, a
   stale receipt, an unadopted review, a too-high job number or STOP refuses.
4. The refit planner's first job is exactly reps 3..26 at index 0; the originals planner fills 20-slot jobs; a cap raise keeps
   the manifest's SHA-256 and the ledger's spent/live history; the funding gate refuses beyond the allocation.
5. K_max is the whole-T inclusive containment maximum; the decision uses the actual usable n (83 of 100 only at n = 100)."""
import os
os.environ.setdefault("NPROC", "1")
import json, tempfile, importlib.util, sys, time, io, contextlib, hashlib, copy, shutil, math
import numpy as np
import analyze as A

T1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(T1, "chpc"))
def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(T1, "chpc", name + ".py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); sys.modules[name] = m; return m
O, SA, REL, SV = _load("row19_screen_orig"), _load("row19_screen_admit"), _load("row19_screen_release"), _load("row19_screen_status")
B22, TG = _load("row22_bank"), _load("row22_target")
import row19_shard as SH
from test_row19_slice import _manifest, _run, _dirs, _Patched, R19, CALLS
from row19_ledger import CampaignLedger
_LIVE = tempfile.mkdtemp(prefix="row19_screen_test_"); SV.LIVE_DIR = os.path.join(_LIVE, "live"); SV.RECEIPTS = os.path.join(_LIVE, "receipts"); SV.BASE = _LIVE
PG = SA.PG
PG.programme_funding = lambda man: dict(man["funding"], lock=os.path.join(_LIVE, "programme.lock"))   # tests: the manifest's own test programme
PG.tracked_unmodified = lambda rel: True                                                          # tests: stands in for committed files
CTL_P = os.path.join(T1, "chpc", "row19_screen_controls.json")


def _adopt_controls(controls_path=CTL_P):
    """A test-only controls adoption of the CURRENT controls bytes (the real one is written only on a favourable review)."""
    sha = SA.sha_file(controls_path); ver = json.load(open(controls_path))["versions"][-1]["version"]
    rv = os.path.join(_LIVE, "controls_review.md"); open(rv, "w").write(f"verdict\nADOPT row19-screen-controls sha256={sha} version={ver}\n")
    ad = os.path.join(_LIVE, "controls_adoption.json")
    json.dump(dict(controls_sha256=sha, review_record=dict(path=rv, sha256=SA.sha_file(rv))), open(ad, "w"))
    PG.CONTROLS_ADOPTION = ad; SA.CONTROLS_ADOPTION = ad
    return ad


_adopt_controls()


def _call(mod, argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        rc = mod.main(argv)
    return rc, buf.getvalue()


def _bank(n=4):
    root = tempfile.mkdtemp(); camp = os.path.join(root, "campaign"); os.makedirs(camp)
    man = _manifest(root, camp, n_boot=4)
    man["datasets"] = {"seed_base": 777, "reps": list(range(n)), "excluded_resolved_seeds": []}
    man["datasets"]["resolved_seeds_sha256"] = B22.seeds_sha256(B22.resolved_seeds(man))
    man["pbs"] = dict(man["pbs"], cores=4, project="P", queue="serial", nodetype="h", mem_gb=120, walltime_h=36, deadline_reserve_s=1800,
                      expect_original_s=0.0, deadline_margin=1.25)
    man["storage"] = {"root": os.path.join(root, "bank"), "campaign": camp}
    man["budget"] = {"core_hours_cap": 15000.0}
    man["target"] = {"level": 0.99, "max_unusable_fraction": 0.5, "trim_fraction": 0.0, "stability_z": 100.0, "max_halfwidth": 1e6}
    mp = os.path.join(root, "bank_manifest.json"); json.dump(man, open(mp, "w"))
    with _Patched():
        os.makedirs(os.path.join(man["storage"]["root"], "plans"), exist_ok=True)
        plan = os.path.join(man["storage"]["root"], "plans", "job_1.json")
        json.dump({"job": 1, "slots": [{"slot": 0, "reps": list(range(n))}]}, open(plan, "w"))
        assert _call(B22, ["job-start", "--manifest", mp, "--plan", plan, "--job-id", "b1", "--walltime-s", "3600", "--skip-environment-check", "--no-reservation"])[0] == 0
        assert _call(B22, ["worker", "--manifest", mp, "--reps", ",".join(map(str, range(n))), "--slot", "0", "--job-id", "b1", "--skip-environment-check"])[0] == 0
    tgt = os.path.join(root, "target.json"); assert TG.freeze(man, mp, tgt).startswith("frozen")
    return man, mp, tgt


def _screen(bank_mp, reps=(3, 4, 5), B=4, extra_excluded=()):
    root = tempfile.mkdtemp(); camp = os.path.join(root, "campaign"); os.makedirs(camp)
    man = _manifest(root, camp, n_boot=B)
    sd = SA.seeds_of(dict(man, datasets={"seed_base": 20261003, "reps": list(reps)}))
    man["datasets"] = {"seed_base": 20261003, "reps": list(reps), "n_attempted": len(reps), "excluded_resolved_seeds": [],
                       "resolved_seeds_sha256": SA.seeds_sha256(sd), "bank_manifest": bank_mp, "bank_manifest_sha256": SA.sha_file(bank_mp)}
    man["datasets"]["excluded_resolved_seeds"] = sorted(SA.exclusion_contract(man)) + list(extra_excluded)
    man["datasets"]["identities"] = {str(r): SH.task(man, r)["ident"] for r in reps}
    man["shard"] = {"toolchain": root, "clone": root, "per_slot": 1, "expect_layer_s": 0.0, "deadline_margin": 1.25,
                    "identities": man["datasets"]["identities"], "sequential_roots": [], "sequential_campaign": camp}
    man["pbs"] = dict(man["pbs"], cores=24, project="P", queue="serial", nodetype="h", mem_gb=120, walltime_h=30, deadline_reserve_s=1800, mem_stop_gib=0)
    man["budget"] = {"core_hours_cap": None, "admission": None}
    man["funding"] = {"programme": "P", "allocation_core_h": 100000.0, "other_settled_core_h": 6.0, "campaigns": []}
    refit = dict(copy.deepcopy(man), role="refit", storage={"root": os.path.join(root, "screen"), "campaign": os.path.join(root, "screen_campaign")})
    orig = dict(copy.deepcopy(man), role="orig", originals={"expect_original_s": 0.0, "deadline_margin": 1.25},
                storage={"root": os.path.join(root, "orig"), "campaign": os.path.join(root, "orig_campaign")})
    for m in (refit, orig):
        os.makedirs(m["storage"]["campaign"], exist_ok=True)
        bp = os.path.join(root, f"budget_{m['role']}.json"); json.dump({"phases": [{"cap_core_h": 60000.0, "note": "test"}]}, open(bp, "w"))
        m["budget"]["admission"] = bp
        m["funding"]["campaigns"] = [dict(path=refit["storage"]["campaign"], may_be_absent=True, root=refit["storage"]["root"]),
                                     dict(path=orig["storage"]["campaign"], may_be_absent=True, root=orig["storage"]["root"])]
    rp, op = os.path.join(root, "screen_manifest.json"), os.path.join(root, "orig_manifest.json")
    json.dump(refit, open(rp, "w")); json.dump(orig, open(op, "w"))
    return refit, rp, orig, op


def _produce(refit, rp, orig, op, skip=(), wrap=None):
    """Stub originals and every refit record for the screen; `wrap(stub)` may replace the stub fit inside the patch."""
    with _Patched():
        if wrap is not None:
            A.run_dataset = wrap(A.run_dataset)
        reps = refit["datasets"]["reps"]
        rc, out = _call(O, ["worker", "--manifest", op, "--reps", ",".join(map(str, reps)), "--slot", "0", "--job-id", "o1", "--skip-environment-check"])
        assert rc == 0, out
        for r in reps:
            idx = [i for i in range(int(refit["cfg"]["n_boot_refit"])) if (r, i) not in skip]
            rc, out = _call(SH, ["worker", "--manifest", rp, "--rep", str(r), "--indices", ",".join(map(str, idx)), "--slot", "0", "--job-id", "s1",
                                 "--skip-environment-check", "--no-binding-check"])
            assert rc == 0, out


def test_the_lossless_original_is_the_slice_runners_cache_never_overwritten_and_holds_on_damage():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=10)
        assert _run(d, man, "--job-id", "j1", "--segment", "1") in (R19.DONE, R19.RESUME)       # the slice's own original cache, rep 0
        t = SH.task(man, 0)
        slice_orig, why = R19.read_orig(os.path.join(d, "orig", f"orig_{t['ident'][:24]}.json"), t["ident"], t["code_hash"], t["ds"], t["cfg"], t["folds"])
        assert slice_orig is not None, why
        run = A.run_dataset(t["ds"], t["cfg"], t["seed"], outer_folds=t["folds"])
    rec = O.build_cache(run, t, 1.0)
    root = tempfile.mkdtemp(); O.publish_cache(O.orig_path(root, t["ident"]), rec)
    got, _ = O.read_cache(root, t)
    assert R19.to_wire(got["run"]) == R19.to_wire(slice_orig["run"])                               # bit-equal full run, every RUN_KEYS field
    try:
        O.publish_cache(O.orig_path(root, t["ident"]), rec); assert False, "a cache is never overwritten"
    except ValueError as e:
        assert "already exists" in str(e)
    p = O.orig_path(root, t["ident"]); d2 = json.load(open(p)); d2["seconds"] = 2.0; json.dump(d2, open(p, "w"))
    try:
        O.read_cache(root, t); assert False
    except ValueError as e:
        assert "cannot accept" in str(e)


def test_the_producer_holds_on_a_wrong_identity_and_keeps_a_failed_original():
    bank, bmp, _ = _bank()
    refit, rp, orig, op = _screen(bmp)
    bad = copy.deepcopy(orig); bad["datasets"]["identities"]["3"] = "0" * 64; json.dump(bad, open(op, "w"))
    with _Patched():
        rc, out = _call(O, ["worker", "--manifest", op, "--reps", "3", "--slot", "0", "--job-id", "o1", "--skip-environment-check"])
    assert rc == O.HELD and "declares" in out
    json.dump(orig, open(op, "w"))
    with _Patched():
        stub = A.run_dataset                                                                             # the stub, never a real fit
        def failing(ds, cfg, seed, outer_folds=None, n_jobs=1):
            r = stub(ds, cfg, seed, outer_folds=outer_folds); r["failed"] = True; r["failed_reason"] = "stub original failure"; return r
        A.run_dataset = failing
        rc, out = _call(O, ["worker", "--manifest", op, "--reps", "4", "--slot", "1", "--job-id", "o1", "--skip-environment-check"])
    assert rc == 0, out
    st = json.load(open(os.path.join(orig["storage"]["root"], "status", "jobo1.slot1.json")))
    assert st["failed_originals"] and st["failed_originals"][0]["rep"] == 4                          # reported, kept, never retried
    got, _ = O.read_cache(orig["storage"]["root"], O.task_checked(orig, 4))
    assert got["run"]["failed"] is True


def test_seed_domain_and_identity_checks():
    bank, bmp, _ = _bank()
    refit, rp, orig, op = _screen(bmp)
    assert SA.seed_domain_problem(refit) == ""
    m = copy.deepcopy(refit); m["datasets"]["excluded_resolved_seeds"] = refit["datasets"]["excluded_resolved_seeds"] + [SA.seeds_of(refit)[3]]
    assert "excluded" in SA.seed_domain_problem(m)
    m = copy.deepcopy(refit); m["datasets"]["excluded_resolved_seeds"] = []
    assert "empty" in SA.seed_domain_problem(m)
    m = copy.deepcopy(refit); m["datasets"]["excluded_resolved_seeds"] = refit["datasets"]["excluded_resolved_seeds"][:-10]
    assert "not exactly the contract" in SA.seed_domain_problem(m)                                       # a truncated exclusion list refuses
    m = copy.deepcopy(refit); m["datasets"]["identities"].pop("5")
    assert "identity map" in SA.seed_domain_problem(m)
    m = copy.deepcopy(refit); m["datasets"]["bank_manifest_sha256"] = "0" * 64
    assert "bank manifest" in SA.seed_domain_problem(m)
    bank2 = copy.deepcopy(bank); bank2["datasets"]["seed_base"] = 20261003; bank2["datasets"]["reps"] = [3, 9]
    bank2["datasets"]["resolved_seeds_sha256"] = B22.seeds_sha256(B22.resolved_seeds(bank2))
    bp2 = os.path.join(tempfile.mkdtemp(), "b2.json"); json.dump(bank2, open(bp2, "w"))
    m = copy.deepcopy(refit); m["datasets"]["bank_manifest"] = bp2; m["datasets"]["bank_manifest_sha256"] = SA.sha_file(bp2)
    assert "bank seed" in SA.seed_domain_problem(m) or "not exactly the contract" in SA.seed_domain_problem(m)                                                    # derived from the bank manifest, not a caller list
    m = copy.deepcopy(refit); m["datasets"]["identities"]["4"] = "1" * 64
    assert "declares" in SA.identity_problem(m, [4]) and SA.identity_problem(refit, [3, 4, 5]) == ""


def test_planner_cap_lineage_and_funding():
    bank, bmp, _ = _bank()
    reps = list(range(3, 103))
    refit, rp, orig, op = _screen(bmp, reps=reps, B=200)
    done, flight, used, problems = SA.evidence(refit, "refit", validate=False)
    jobs, left = SA.plan_jobs(refit, "refit", 2, done, flight, used)
    assert [(s["rep"], s["indices"]) for s in jobs[0]["slots"]] == [(r, [0]) for r in range(3, 27)]     # exactly reps 3..26 at index 0
    assert [(s["rep"], s["indices"]) for s in jobs[1]["slots"]][:2] == [(27, [0]), (28, [0])]
    o = copy.deepcopy(orig); o["pbs"]["cores"] = 20
    oj, oleft = SA.plan_jobs(o, "orig", 10, set(), set(), set())
    assert [len(j["slots"]) for j in oj] == [20] * 5 and oleft == 0
    L = SA.ledger_for(refit); tok, _ = L.reserve("shard", 1, 24, 108000.0, refit["storage"]["root"])
    before = SA.sha_file(rp)
    rc, out = _call(SA, ["--manifest", rp, "--role", "refit", "--raise-cap", "90000", "--note", "owner ruling for the test"])
    assert rc == 0, out
    st = json.load(open(os.path.join(refit["storage"]["campaign"], "budget.json")))
    assert st["cap_core_h"] == 90000.0 and st["cap_history"][-1]["old"] == 60000.0 and tok in st["entries"]
    assert SA.sha_file(rp) == before and SA.cap_problem(refit) == ""                                    # no binding can name a moved manifest
    bp = refit["budget"]["admission"]; b = json.load(open(bp))
    b["phases"].append(dict(cap_core_h=120000.0, note="interrupted", pending=True, campaign=refit["storage"]["campaign"])); json.dump(b, open(bp, "w"))
    assert "interrupted" in SA.cap_problem(refit)                                                        # refused until reconciled
    SA.ledger_for(refit).raise_cap(120000.0, "the ledger step that was interrupted")
    assert SA.cap_problem(refit) == "" and json.load(open(bp))["phases"][-1]["pending"] is False         # reconciled, nothing reset
    SA.ledger_for(refit).raise_cap(130000.0, "a raise outside the protocol")
    assert "not the latest budget phase" in SA.cap_problem(refit)
    assert SA.ledger_for(refit).reserve("shard", 2, 24, 108000.0, refit["storage"]["root"])[0]          # admitted under the raised cap
    assert SA.funding_problem(refit, 1000.0) == ""
    assert "allocation" in SA.funding_problem(refit, 99000.0)                                            # 720 + 720 live + 6 + 99,000 > 100,000


def test_the_release_refuses_before_any_aggregation():
    bank, bmp, tgt = _bank()
    refit, rp, orig, op = _screen(bmp)
    _produce(refit, rp, orig, op)
    rv = os.path.join("reviews", f"_test_target_review_{os.getpid()}.md"); ad = os.path.join("reviews", f"_test_adoption_{os.getpid()}.json")
    tg = json.load(open(tgt))
    open(os.path.join(T1, rv), "w").write(f"adopts the target\nADOPT row19-numerical-target target={REL.sha_file(tgt)} bank_records={tg['records_sha256']} verdict=FAVOURABLE\n")
    good = dict(schema=REL.ADOPTION_SCHEMA, target_sha256=REL.sha_file(tgt), bank_manifest_sha256=REL.sha_file(bmp),
                bank_binding_sha256=REL.sha_file(os.path.join(bank["storage"]["root"], "bank_binding.json")),
                manifests=dict(screen=REL.sha_file(rp), originals=REL.sha_file(op)),
                consumer_pins={f: REL.sha_file(os.path.join(T1, f)) for f in REL.CONSUMER_FILES},
                review_record=dict(path=rv, sha256=REL.sha_file(os.path.join(T1, rv))))
    keep = (A.refit_bootstrap, A.analyze_dataset)
    def boom(*a, **k):
        raise AssertionError("an aggregation helper was called before the seal")
    try:
        A.refit_bootstrap = boom; A.analyze_dataset = boom
        def refused(doc, target=tgt, check_git=False):
            if target != tgt:                                                                             # the review adopts THIS target, so the
                t2 = json.load(open(target))                                                              # case reaches the check it is about
                open(os.path.join(T1, rv), "w").write(f"ADOPT row19-numerical-target target={REL.sha_file(target)} bank_records={t2.get('records_sha256')} verdict=FAVOURABLE\n")
                doc = dict(doc, review_record=dict(path=rv, sha256=REL.sha_file(os.path.join(T1, rv))))
            json.dump(doc, open(os.path.join(T1, ad), "w"))
            r = REL.release(rp, op, target, ad, check_git=check_git)
            assert r["status"] in ("REFUSED", "HELD"), r
            return " ".join(r["reasons"])
        assert "not git-tracked" in refused(good, check_git=True)                                        # an untracked adoption is no authority
        assert "not the adopted bytes" in refused(dict(good, target_sha256="0" * 64))
        unres = os.path.join(_LIVE, "unresolved.json"); json.dump(dict(tg, status="UNRESOLVED"), open(unres, "w"))
        assert "not RESOLVED" in refused(dict(good, target_sha256=REL.sha_file(unres)), target=unres)
        assert "review record" in refused(dict(good, review_record=dict(path=rv, sha256="0" * 64)))
        assert "consumer's pins" in refused(dict(good, consumer_pins=dict(good["consumer_pins"], **{"analyze.py": "0" * 64})))
        assert "screen manifest" in refused(dict(good, manifests=dict(good["manifests"], screen="0" * 64)))
        assert "bank binding" in refused(dict(good, bank_binding_sha256="0" * 64))
        moved = dict(tg, records_sha256="0" * 64); mp_ = os.path.join(_LIVE, "moved.json"); json.dump(moved, open(mp_, "w"))
        assert "record set" in refused(dict(good, target_sha256=REL.sha_file(mp_)), target=mp_)
        shifted = copy.deepcopy(tg); shifted["targets"]["selection/ws"]["lo"] -= 1.0; sp = os.path.join(_LIVE, "shifted.json"); json.dump(shifted, open(sp, "w"))
        assert "does not reproduce" in refused(dict(good, target_sha256=REL.sha_file(sp)), target=sp)
        half = copy.deepcopy(tg); half["targets"]["selection/ws"]["status"] = "UNRESOLVED"; hp = os.path.join(_LIVE, "half.json"); json.dump(half, open(hp, "w"))
        assert "both RESOLVED" in refused(dict(good, target_sha256=REL.sha_file(hp)), target=hp)        # a RESOLVED label over an UNRESOLVED primary
        open(os.path.join(T1, rv), "w").write("adopts the target, no line\n")
        assert "ADOPT line" in refused(dict(good, review_record=dict(path=rv, sha256=REL.sha_file(os.path.join(T1, rv)))))
        other = dict(json.load(open(rp)), cfg=dict(json.load(open(rp))["cfg"], n_starts=12)); op2 = os.path.join(_LIVE, "screen_n12.json"); json.dump(other, open(op2, "w"))
        oo = dict(json.load(open(op)), cfg=other["cfg"]); oo2 = os.path.join(_LIVE, "orig_n12.json"); json.dump(oo, open(oo2, "w"))
        json.dump(dict(good, manifests=dict(screen=REL.sha_file(op2), originals=REL.sha_file(oo2))), open(os.path.join(T1, ad), "w"))
        r = REL.release(op2, oo2, tgt, ad, check_git=False)
        assert r["status"] == "REFUSED" and any("effective cfg" in w for w in r["reasons"]), r                # a bank of another procedure
    finally:
        A.refit_bootstrap, A.analyze_dataset = keep
        for f in (rv, ad):
            if os.path.exists(os.path.join(T1, f)):
                os.remove(os.path.join(T1, f))


def test_an_incomplete_screen_holds_and_a_complete_one_releases_without_fitting():
    bank, bmp, tgt = _bank()
    refit, rp, orig, op = _screen(bmp)
    _produce(refit, rp, orig, op, skip={(4, 2)})
    rv = os.path.join("reviews", f"_test_target_review_{os.getpid()}.md"); ad = os.path.join("reviews", f"_test_adoption_{os.getpid()}.json")
    tg = json.load(open(tgt))
    open(os.path.join(T1, rv), "w").write(f"ADOPT row19-numerical-target target={REL.sha_file(tgt)} bank_records={tg['records_sha256']} verdict=FAVOURABLE\n")
    doc = dict(schema=REL.ADOPTION_SCHEMA, target_sha256=REL.sha_file(tgt), bank_manifest_sha256=REL.sha_file(bmp),
               bank_binding_sha256=REL.sha_file(os.path.join(bank["storage"]["root"], "bank_binding.json")),
               manifests=dict(screen=REL.sha_file(rp), originals=REL.sha_file(op)),
               consumer_pins={f: REL.sha_file(os.path.join(T1, f)) for f in REL.CONSUMER_FILES},
               review_record=dict(path=rv, sha256=REL.sha_file(os.path.join(T1, rv))))
    json.dump(doc, open(os.path.join(T1, ad), "w"))
    try:
        with _Patched():
            n0 = CALLS["run_dataset"]
            r = REL.release(rp, op, tgt, ad, check_git=False)
            assert r["status"] == "HELD" and any("resample 2 missing" in w for w in r["reasons"]) and CALLS["run_dataset"] == n0
            rc, out = _call(SH, ["worker", "--manifest", rp, "--rep", "4", "--indices", "2", "--slot", "0", "--job-id", "s2",
                                 "--skip-environment-check", "--no-binding-check"])
            n1 = CALLS["run_dataset"]
            r = REL.release(rp, op, tgt, ad, check_git=False)
            assert r["status"] == "RELEASED", r.get("reasons")
            assert CALLS["run_dataset"] == n1                                                             # not one fit bought by the release
            assert r["refit"]["n_attempted"] == 3 and set(r["paired"]) == {"both", "refit_only", "cluster_only", "neither"}
            assert r["refit"]["decision"] in ("STOP FOR FUTILITY", "not ruled out at this look", "unresolved: no usable interval")
            assert isinstance(r["failed_originals"], dict) and isinstance(r["refit_unusable"], dict)
            keep_agg = REL._aggregate
            def swap_then_aggregate(items, screen):                                                       # the target is replaced mid-release
                out = keep_agg(items, screen); bad = json.load(open(tgt)); bad["targets"]["selection/ws"]["lo"] = -1e9
                json.dump(bad, open(tgt, "w")); return out
            REL._aggregate = swap_then_aggregate
            try:
                r2 = REL.release(rp, op, tgt, ad, check_git=False)
            finally:
                REL._aggregate = keep_agg
            assert r2["status"] == "RELEASED" and r2["target"]["lo"] == r["target"]["lo"]                   # decided on the bytes read once
    finally:
        for f in (rv, ad):
            if os.path.exists(os.path.join(T1, f)):
                os.remove(os.path.join(T1, f))


def test_k_max_and_the_decision_rule():
    assert REL.k_max([(0, 1), (2, 3)], 0.5, 2.5) == 1
    assert REL.k_max([(0, 1), (1, 2)], 0.0, 3.0) == 2                                                   # inclusive tie at an endpoint
    assert REL.k_max([(0, 1), (0.4, 0.6), (0.5, 3)], 0.45, 0.55) == 3                                    # a segment inside T
    assert REL.k_max([(5, 6)], 0.0, 1.0) == 0
    covered = lambda k, n: [(0.0, 1.0)] * k + [(5.0, 6.0)] * (n - k)
    assert REL.decide(covered(83, 100), 100, 0.4, 0.6)["decision"] == "STOP FOR FUTILITY"
    assert REL.decide(covered(84, 100), 100, 0.4, 0.6)["decision"] == "not ruled out at this look"
    assert abs(REL.cp_upper(83, 100) - 0.897735) < 1e-5 and abs(REL.cp_upper(84, 100) - 0.905690) < 1e-5
    d = REL.decide(covered(80, 95), 100, 0.4, 0.6)                                                       # usable n 95: the exact bound at 95
    assert d["n_usable"] == 95 and (d["decision"] == "STOP FOR FUTILITY") == (REL.cp_upper(80, 95) < 0.90)
    half = [(0.0, 0.5)] * 50 + [(0.5, 1.0)] * 50
    assert REL.decide(half, 100, 0.0, 1.0)["k_max"] == 100                                                # the most favourable theta in T counts


def test_status_anchor_rules_and_a_failed_scheduler_query():
    good = {"reps": {str(r): {"required": [0], "compared": [0], "equal": [0], "differ": [], "missing": [], "invalid": []} for r in (0, 1, 2)}}
    assert SV.anchor_alarms({"anchors": good}) == []
    for mut, msg in ((lambda g: g["reps"].pop("2"), "not all three"), (lambda g: g["reps"]["1"].update(differ=[0], equal=[]), "DIFFERS"),
                     (lambda g: g["reps"]["0"].update(missing=[0]), "required overlap"), (lambda g: g.update(problem="absent"), "absent")):
        g = copy.deepcopy(good); mut(g)
        assert any(msg in a for a in SV.anchor_alarms({"anchors": g})), msg
    keep = SV.sh
    try:
        SV.sh = lambda cmd, timeout=600: (1, "Job Id: X\n job_state = F\n", "err")
        assert SV.pbs_observe(["X"])[0] is None
        SV.sh = lambda cmd, timeout=600: (0, "Job Id: X\n    job_state = R\n", "")
        assert SV.pbs_observe(["X", "Y"])[0] is None and SV.pbs_observe(["X"])[0]["X"]["state"] == "R"
    finally:
        SV.sh = keep


ANCHORS = {"problem": "", "reps": {str(a): {"required": [0], "compared": [0], "equal": [0], "differ": [], "missing": [], "invalid": [], "conflict": []} for a in (0, 1, 2)}}
ADIG = hashlib.sha256(json.dumps(ANCHORS, sort_keys=True).encode()).hexdigest()


def _summary(slots=24, **kw):
    d = dict(job_id="P1", state="F", exit=0, runner_exit=0, slots=slots, ended=slots, exits={"0": slots}, left=0, new=slots, resumed=0,
             mem_kb=1.0e7, max_worker_maxrss=2.5e9)
    d.update(kw); return d


def _verify_doc(refit, root, bindings, name, units=None):
    """A retained verifier document of the LATEST controller generation with the EXACT reviewed digests, as written to the gate."""
    latest = SA.controls()["versions"][-1]
    v = dict(schema="row19-screen-verify-1", role="refit", time=time.time(), manifest_sha256=None, anchors=ANCHORS, units=units or {},
             environment_bad=[], code_bad=[],
             bindings={k: dict(ok=True, sha256=h, declared_ident_equal=True) for k, h in bindings.items()},
             generation=dict(version=latest["version"], latest=latest["version"], controls_problem="",
                             verify_sha256=latest["files"]["chpc/row19_screen_verify.py"], controls_sha256=SA.sha_file(CTL_P)))
    return v


def _units(plan, job_id):
    return {f"{s['rep']}/{i}": dict(record=dict(ok=True, sha="s"), timing=dict(ok=True, job=job_id, slot=s["slot"])) for s in plan["slots"] for i in s["indices"]}


def _write_verify(refit, rp, root, bindings, name, units=None, mutate=None):
    v = _verify_doc(refit, root, bindings, name, units); v["manifest_sha256"] = SA.sha_file(rp)
    if mutate:
        mutate(v)
    p = os.path.join(root, "gate", name); json.dump(v, open(p, "w")); return SA.sha_file(p)


def _pilot_setup(n_reps=60):
    bank, bmp, _ = _bank()
    refit, rp, orig, op = _screen(bmp, reps=list(range(3, 3 + n_reps)), B=4)
    root = refit["storage"]["root"]
    os.makedirs(os.path.join(root, "plans"), exist_ok=True); os.makedirs(os.path.join(root, "gate"), exist_ok=True)
    L = SA.ledger_for(refit); tok, _ = L.reserve("shard", 1, 24, 108000.0, root); L.bind(tok, "P1"); L.runner_end(tok, 10.0, 0)
    jobs, _ = SA.plan_jobs(refit, "refit", 2, set(), set(), set())
    json.dump(dict(jobs[0], token=tok), open(os.path.join(root, "plans", "job_1.json"), "w"))
    for sl in jobs[0]["slots"]:
        open(os.path.join(root, f"task_{sl['rep']}.json"), "w").write(json.dumps({"binding": {"rep": sl["rep"]}}))
    want = SA.expected_bound(refit, rp, "refit")
    vsha = _write_verify(refit, rp, root, want["bindings"], "verify_q.json", units=_units(jobs[0], "P1"))
    q = os.path.join(root, "gate", "qualified_refit_job1.json")
    rec = dict(schema=SA.WATCH_SCHEMA, role="refit", time=time.time(), fresh=True, production=True, alarms=[], jobs={"1": _summary()})
    good_q = dict(schema=SA.QUAL_SCHEMA, role="refit", qualified_job=1, production=True, time=time.time(),
                  bound=dict(want, anchors_sha256=ADIG, verify_file="verify_q.json", verify_file_sha256=vsha), receipt=rec, anchors=ANCHORS)
    json.dump(good_q, open(q, "w"))
    return refit, rp, root, L, jobs, want, good_q, q


def _adopt(refit, rp, q, max_job=9):
    qsha = SA.sha_file(q); rv = os.path.join("reviews", f"_test_pilot_review_{os.getpid()}.md")
    open(os.path.join(T1, rv), "w").write(f"verdict\nADOPT row19-screen-pilot role=refit qualification={qsha} max_job={max_job}\n")
    return rv


def _receipt(refit, rp, root, jobs_summ, name="verify_r.json", bindings=None, units=None, mutate=None, **override):
    want = SA.expected_bound(refit, rp, "refit")
    if bindings is not None:
        want = dict(want, bindings=bindings)
    if units is None:
        units = _units(json.load(open(os.path.join(root, "plans", "job_1.json"))), "P1")
    vsha = _write_verify(refit, rp, root, override.pop("verify_bindings", want["bindings"]), name, units=units, mutate=mutate)
    r = os.path.join(root, "gate", f"watch_refit_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json")
    doc = dict(schema=SA.WATCH_SCHEMA, role="refit", production=True, fresh=True, alarms=[], time=time.time(),
               bound=dict(want, anchors_sha256=ADIG, verify_file=name, verify_file_sha256=vsha), anchors=ANCHORS, jobs=jobs_summ)
    doc.update(override); json.dump(doc, open(r, "w")); return r, doc


def test_later_admission_binds_only_started_tasks_and_refuses_stale_or_unadopted_evidence():
    refit, rp, root, L, jobs, want, good_q, q = _pilot_setup()
    assert sorted(int(k) for k in want["bindings"]) == list(range(3, 27))                                 # 24 bound; the rest pending, never fabricated
    assert SA.qualification_problem(refit, rp, "refit")[0] == ""
    bad_anchor = copy.deepcopy(ANCHORS); bad_anchor["reps"]["2"]["equal"] = []
    bdig = hashlib.sha256(json.dumps(bad_anchor, sort_keys=True).encode()).hexdigest()
    for bad, msg in ((dict(good_q, bound=dict(good_q["bound"], anchors_sha256="a" * 64)), "not the bound one"),
                     (dict(good_q, role="orig"), "not a production"),
                     (dict(good_q, bound=dict(good_q["bound"], bindings={k: v for k, v in want["bindings"].items() if k != "3"})), "not exactly the root's"),
                     (dict(good_q, anchors=bad_anchor, bound=dict(good_q["bound"], anchors_sha256=bdig)), "anchor 2"),
                     (dict(good_q, receipt=dict(good_q["receipt"], jobs={"1": _summary(state="E")})), "terminal F"),
                     (dict(good_q, receipt=dict(good_q["receipt"], jobs={"1": _summary(runner_exit=4)})), "terminal F"),
                     (dict(good_q, receipt=dict(good_q["receipt"], jobs={"1": _summary(mem_kb=None)})), "memory"),
                     (dict(good_q, receipt=dict(good_q["receipt"], jobs={"1": _summary(mem_kb=-1.0)})), "memory"),
                     (dict(good_q, receipt=dict(good_q["receipt"], jobs={"1": _summary(exits={"0": 23, "4": 1})})), "0/75"),
                     (dict(good_q, receipt=dict(good_q["receipt"], jobs={"1": _summary(slots=0, ended=0, exits={})})), "workers did not all end"),
                     (dict(good_q, receipt=dict(good_q["receipt"], jobs={"1": _summary(slots=True)})), "workers did not all end"),
                     (dict(good_q, receipt=dict(good_q["receipt"], schema="other")), "another schema"),
                     (dict(good_q, bound=dict(good_q["bound"], verify_file="absent.json")), "absent"),
                     (dict(good_q, bound=dict(good_q["bound"], verify_file_sha256="0" * 64)), "not the bound bytes"),
                     (dict(good_q, time=True), "finite past time")):
        json.dump(bad, open(q, "w"))
        assert msg in SA.qualification_problem(refit, rp, "refit")[0], (msg, SA.qualification_problem(refit, rp, "refit")[0])
    v = json.load(open(os.path.join(root, "gate", "verify_q.json"))); v["generation"]["version"] = 1
    json.dump(v, open(os.path.join(root, "gate", "verify_q.json"), "w"))
    json.dump(dict(good_q, bound=dict(good_q["bound"], verify_file_sha256=SA.sha_file(os.path.join(root, "gate", "verify_q.json")))), open(q, "w"))
    assert "generation 1" in SA.qualification_problem(refit, rp, "refit")[0]                               # evidence of an older verifier
    refit, rp, root, L, jobs, want, good_q, q = _pilot_setup()
    for mut, msg in ((lambda v: v["generation"].update(verify_sha256="0" * 64), "verifier pin"),
                     (lambda v: v["generation"].update(controls_sha256="0" * 64), "adopted controls"),
                     (lambda v: v["generation"].pop("controls_problem"), "explicitly clean"),
                     (lambda v: v.update(environment_bad=["numpy"]), "environment or code"),
                     (lambda v: v.update(units={}), "valid unit"),
                     (lambda v: v["bindings"]["3"].update(declared_ident_equal=False), "not clean")):
        vsha = _write_verify(refit, rp, root, want["bindings"], "verify_q.json", units=_units(jobs[0], "P1"), mutate=mut)
        json.dump(dict(good_q, bound=dict(good_q["bound"], verify_file_sha256=vsha)), open(q, "w"))
        assert msg in SA.qualification_problem(refit, rp, "refit")[0], (msg, SA.qualification_problem(refit, rp, "refit")[0])
    refit, rp, root, L, jobs, want, good_q, q = _pilot_setup()
    tracked = "reviews/2026-10-06_stage2_screen_design_codex_record.md"
    assert "does not contain the line" in SA.adopt_review(refit, rp, "refit", tracked, 9)
    rv = _adopt(refit, rp, q); keep_t = SA.tracked_unmodified
    try:
        assert "not tracked" in SA.adopt_review(refit, rp, "refit", rv, 9)
        SA.tracked_unmodified = lambda rel: True
        assert "does not contain the line" in SA.adopt_review(refit, rp, "refit", rv, 12)
        assert SA.adopt_review(refit, rp, "refit", rv, 9).startswith("adopted")
        assert "no watch receipt" in SA.review_problem(refit, rp, "refit", [2])
        r, doc = _receipt(refit, rp, root, {"1": _summary()}, time=float("nan"))
        assert "within 2700" in SA.review_problem(refit, rp, "refit", [2])
        r, doc = _receipt(refit, rp, root, {"1": _summary()})
        assert SA.review_problem(refit, rp, "refit", [2]) == ""
        assert "up to 9" in SA.review_problem(refit, rp, "refit", [10])
        # R1 lifecycle: job 2 starts reps 27-50; the frozen job-1 qualification still serves; the receipt binds ALL started tasks
        tok2, _ = L.reserve("shard", 2, 24, 108000.0, root); L.bind(tok2, "P2")
        json.dump(dict(jobs[1], token=tok2), open(os.path.join(root, "plans", "job_2.json"), "w"))
        for sl in jobs[1]["slots"]:
            open(os.path.join(root, f"task_{sl['rep']}.json"), "w").write(json.dumps({"binding": {"rep": sl["rep"]}}))
        assert SA.qualification_problem(refit, rp, "refit")[0] == ""                                       # job 1's own scope is unchanged
        r, doc = _receipt(refit, rp, root, {"1": _summary(), "2": dict(_summary(), state="R", job_id="P2")})
        assert SA.review_problem(refit, rp, "refit", [3]) == ""                                            # job 3 admissible
        want_all = SA.expected_bound(refit, rp, "refit")
        omitted = {k: v for k, v in want_all["bindings"].items() if k != "40"}
        r, doc = _receipt(refit, rp, root, {"1": _summary(), "2": dict(_summary(), state="R", job_id="P2")}, bindings=omitted, verify_bindings=omitted)
        assert "not exactly the root's" in SA.review_problem(refit, rp, "refit", [3])                      # an omitted later binding refuses
        open(os.path.join(root, "task_40.json"), "w").write("{\"changed\": 1}")
        r, doc = _receipt(refit, rp, root, {"1": _summary(), "2": dict(_summary(), state="R", job_id="P2")}, verify_bindings=want_all["bindings"])
        assert "retained verifier's digests" in SA.review_problem(refit, rp, "refit", [3])                 # a changed binding refuses
        open(os.path.join(root, "task_40.json"), "w").write(json.dumps({"binding": {"rep": 40}}))
        # R2: a terminal follow-on job with a bad runner exit or no memory refuses
        for bad in (dict(_summary(), runner_exit=4), dict(_summary(), mem_kb=None), dict(_summary(), state="E")):
            r, doc = _receipt(refit, rp, root, {"1": _summary(), "2": bad})
            assert "job 2" in SA.review_problem(refit, rp, "refit", [3]), bad
        r, doc = _receipt(refit, rp, root, {"1": _summary()})
        assert "every job" in SA.review_problem(refit, rp, "refit", [3])                                  # a receipt must cover every job
        r, doc = _receipt(refit, rp, root, {"1": _summary(), "2": dict(_summary(), state="R", job_id="P2")})
        assert SA.review_problem(refit, rp, "refit", [3]) == ""
        L.runner_end(tok2, 10.0, 4)                                                                       # C1: job 2 fails after the receipt saw it R
        assert "has ended" in SA.review_problem(refit, rp, "refit", [3])
        L.runner_end(tok2, 10.0, 0)
        assert "has ended" in SA.review_problem(refit, rp, "refit", [3])                                   # even a clean end needs recollected evidence
        u2 = dict(_units(json.load(open(os.path.join(root, "plans", "job_1.json"))), "P1"))
        p2 = json.load(open(os.path.join(root, "plans", "job_2.json")))
        u2.update({f"{s['rep']}/{i}": dict(record=dict(ok=True), timing=dict(ok=True, job="P2", slot=s["slot"])) for s in p2["slots"][:20] for i in s["indices"]})
        j2 = dict(_summary(), job_id="P2", exits={"0": 20, "75": 4}, left=4, new=20)
        r, doc = _receipt(refit, rp, root, {"1": _summary(), "2": j2}, units=u2)
        assert SA.review_problem(refit, rp, "refit", [3]) == ""                                            # a deadline stop with work left is legitimate
        r, doc = _receipt(refit, rp, root, {"1": _summary(), "2": dict(j2, new=22)}, units=u2)
        assert "summary claims 22" in SA.review_problem(refit, rp, "refit", [3])                           # units must agree with the summary
        bad_t = copy.deepcopy(u2); k0 = next(k for k, u in bad_t.items() if u["timing"]["job"] == "P2"); bad_t[k0]["timing"]["ok"] = False
        r, doc = _receipt(refit, rp, root, {"1": _summary(), "2": j2}, units=bad_t)
        assert "invalid, unplanned" in SA.review_problem(refit, rp, "refit", [3])                         # C2: timing.ok is honoured
        r, doc = _receipt(refit, rp, root, {"1": _summary(), "2": dict(j2, job_id="P1")}, units=u2)
        assert "names PBS id P1" in SA.review_problem(refit, rp, "refit", [3])                             # C2: the summary's id is the bound one
        wrong = copy.deepcopy(u2); moved = [k for k, u in wrong.items() if u["timing"]["job"] == "P2"][:2]
        for k in moved:
            wrong[k]["timing"]["slot"] = 23                                                                   # same totals, wrong slots
        r, doc = _receipt(refit, rp, root, {"1": _summary(), "2": j2}, units=wrong)
        assert "invalid, unplanned" in SA.review_problem(refit, rp, "refit", [3])
        foreign = copy.deepcopy(u2); kf = moved[0]; uf = foreign.pop(kf); foreign["99/0"] = uf             # an unplanned coordinate, same count
        r, doc = _receipt(refit, rp, root, {"1": _summary(), "2": j2}, units=foreign)
        assert "invalid, unplanned" in SA.review_problem(refit, rp, "refit", [3])
        for bad in (dict(j2, runner_exit=False), dict(j2, exits={"0": 25, "75": -1}), dict(j2, left=-1)):
            r, doc = _receipt(refit, rp, root, {"1": _summary(), "2": bad}, units=u2)
            assert "job 2" in SA.review_problem(refit, rp, "refit", [3]), bad                             # strict typing
        open(os.path.join(root, "STOP"), "w").write("{}")
        assert "STOP" in SA.gate_problem(refit, rp, "refit", {1}, False, 1, [], 108000.0)
    finally:
        SA.tracked_unmodified = keep_t
        if os.path.exists(os.path.join(T1, rv)):
            os.remove(os.path.join(T1, rv))


def test_status_alarms_every_bad_terminal_job_and_foreign_statuses():
    bank, bmp, _ = _bank()
    refit, rp, orig, op = _screen(bmp, reps=list(range(3, 30)), B=4)
    live = os.path.join(_LIVE, "st"); root = os.path.join(live, "root")
    os.makedirs(os.path.join(root, "plans")); os.makedirs(os.path.join(root, "status"))
    plan = {"job": 1, "slots": [{"slot": 0, "rep": 3, "indices": [0]}]}
    json.dump(plan, open(os.path.join(root, "plans", "job_1.json"), "w"))
    st = dict(job="P1", slot=0, rep=3, indices=[0], ident=refit["datasets"]["identities"]["3"], new=[0], resumed=[], left=[], exit=0, wall_s=5.0, maxrss=1e9)
    json.dump(st, open(os.path.join(root, "status", "jobP1.slot0.json"), "w"))
    led = {"entries": {"t": {"kind": "shard", "rep": 1, "job_id": "P1", "token": "t", "state": "live", "reserved_core_h": 720.0, "runner_exit": 0}}}
    verify = {"units": {"3/0": {"record": {"ok": True}, "timing": {"ok": True, "job": "P1", "slot": 0}}}, "bindings": {"3": {"ok": True, "declared_ident_equal": True, "sha256": "x"}}}
    al, summ, jobs = SV.reconcile(refit, "refit", verify, {"P1": {"state": "F", "exit": 0, "mem_kb": 100}}, led, live)
    assert al == [], al
    for obs, ledmod, msg in (({"P1": {"state": "F", "exit": 0, "mem_kb": 100}}, dict(runner_exit=4), "runner exit 4"),
                             ({"P1": {"state": "F", "exit": 0}}, {}, "scheduler memory"),
                             ({"P1": {"state": "E", "exit": 0, "mem_kb": 100}}, {}, "F with 0/75")):
        l2 = copy.deepcopy(led); l2["entries"]["t"].update(ledmod)
        al, _, _ = SV.reconcile(refit, "refit", verify, obs, l2, live)
        assert any(msg in a for a in al), (msg, al)
    json.dump(dict(st, job="FOREIGN"), open(os.path.join(root, "status", "jobFOREIGN.slot0.json"), "w"))
    al, _, _ = SV.reconcile(refit, "refit", verify, {"P1": {"state": "F", "exit": 0, "mem_kb": 100}}, led, live)
    assert any("no planned job and slot" in a for a in al)
    os.remove(os.path.join(root, "status", "jobFOREIGN.slot0.json"))
    json.dump(dict(st, wall_s=None), open(os.path.join(root, "status", "jobP1.slot0.json"), "w"))
    al, _, _ = SV.reconcile(refit, "refit", verify, {"P1": {"state": "F", "exit": 0, "mem_kb": 100}}, led, live)
    assert any("wall time" in a for a in al)


def test_cap_phases_are_strict_durable_and_recoverable_through_the_cli():
    bank, bmp, _ = _bank()
    refit, rp, orig, op = _screen(bmp)
    L = SA.ledger_for(refit); L.reserve("shard", 1, 24, 108000.0, refit["storage"]["root"])
    bp = refit["budget"]["admission"]
    rc, out = _call(SA, ["--manifest", rp, "--role", "refit", "--raise-cap", "50000", "--note", "a lower cap is no raise"])
    assert rc == 2 and "not finite and above" in out and not any(x.get("pending") for x in json.load(open(bp))["phases"])   # validated BEFORE publishing
    b = json.load(open(bp)); b["phases"].append(dict(cap_core_h=90000.0, note="interrupted before the ledger", pending=True, campaign=refit["storage"]["campaign"]))
    json.dump(b, open(bp, "w"))
    assert "interrupted" in SA.cap_problem(refit)
    rc, out = _call(SA, ["--manifest", rp, "--role", "refit", "--raise-cap", "90000", "--note", "resume the owner's raise"])
    assert rc == 0 and "resumed" in out, out
    assert SA.cap_problem(refit) == "" and json.load(open(os.path.join(refit["storage"]["campaign"], "budget.json")))["cap_core_h"] == 90000.0
    b = json.load(open(bp)); b["phases"].append(dict(cap_core_h=95000.0, note="never applied", pending=True, campaign=refit["storage"]["campaign"]))
    json.dump(b, open(bp, "w"))
    rc, out = _call(SA, ["--manifest", rp, "--role", "refit", "--retire-pending", "--note", "owner withdrew this raise"])
    assert rc == 0 and "retired" in out and SA.cap_problem(refit) == ""
    src = open(bp).read(); assert '"cap_core_h": 90000.0' in src                                         # read BEFORE truncating
    open(bp, "w").write(src.replace('"cap_core_h": 90000.0', '"cap_core_h": NaN', 1))
    assert "malformed" in SA.cap_problem(refit) and "non-finite" in SA.cap_problem(refit)                 # a NaN phase never passes
    open(bp, "w").write(src)
    b = json.load(open(bp)); b["phases"].append(dict(cap_core_h=92000.0, note="stale pending", pending=True, campaign=refit["storage"]["campaign"]))
    json.dump(b, open(bp, "w")); SA.ledger_for(refit).raise_cap(120000.0, "an out-of-protocol raise above the phase")
    rc, out = _call(SA, ["--manifest", rp, "--role", "refit", "--raise-cap", "92000", "--note", "resume attempt"])
    assert rc == 2 and "does not certify" in out and json.load(open(bp))["phases"][-1]["pending"] is True   # C4: no false success
    rc, out = _call(SA, ["--manifest", rp, "--role", "refit", "--retire-pending", "--note", "retire attempt over a conflicting ledger"])
    assert rc == 2 and "does not certify" in out and json.load(open(bp))["phases"][-1]["pending"] is True   # nor a false retirement


def test_a_pending_raise_is_applied_only_over_a_certified_predecessor():
    bank, bmp, _ = _bank()
    refit, rp, orig, op = _screen(bmp)
    SA.ledger_for(refit).reserve("shard", 1, 24, 108000.0, refit["storage"]["root"])
    bp = refit["budget"]["admission"]; camp = refit["storage"]["campaign"]
    b = json.load(open(bp)); b["phases"].append(dict(cap_core_h=90000.0, note="owner raise", pending=True, campaign=camp)); json.dump(b, open(bp, "w"))
    SA.ledger_for(refit).raise_cap(70000.0, "an out-of-protocol step to an unexpected lower predecessor")
    rc, out = _call(SA, ["--manifest", rp, "--role", "refit", "--raise-cap", "90000", "--note", "resume over an uncertified predecessor"])
    assert rc == 2 and "does not certify" in out
    led = json.load(open(os.path.join(camp, "budget.json"))); assert led["cap_core_h"] == 70000.0                # nothing changed
    rc, out = _call(SA, ["--manifest", rp, "--role", "refit", "--retire-pending", "--note", "retire over an uncertified predecessor"])
    assert rc == 2 and "does not certify" in out
    bank2, bmp2, _ = _bank()
    refit2, rp2, _, _ = _screen(bmp2)
    SA.ledger_for(refit2).reserve("shard", 1, 24, 108000.0, refit2["storage"]["root"])
    bp2 = refit2["budget"]["admission"]; camp2 = refit2["storage"]["campaign"]
    b = json.load(open(bp2)); b["phases"].append(dict(cap_core_h=90000.0, note="owner raise", pending=True, campaign=camp2)); json.dump(b, open(bp2, "w"))
    st = json.load(open(os.path.join(camp2, "budget.json"))); st["cap_core_h"] = 90000.0; json.dump(st, open(os.path.join(camp2, "budget.json"), "w"))
    rc, out = _call(SA, ["--manifest", rp2, "--role", "refit", "--raise-cap", "90000", "--note", "a matching cap without its history"])
    assert rc == 2 and "does not certify" in out                                                            # the pending cap without a history entry
    st["cap_core_h"] = 60000.0; json.dump(st, open(os.path.join(camp2, "budget.json"), "w"))
    rc, out = _call(SA, ["--manifest", rp2, "--role", "refit", "--raise-cap", "90000", "--note", "the ordinary pre-ledger recovery"])
    assert rc == 0, out                                                                                     # the certified predecessor recovers


def test_the_controls_file_is_trusted_only_through_its_adoption():
    assert PG.controls_authority_problem() == "" and SA.controls_problem() == ""
    tmp = os.path.join(_LIVE, "mutated_controls.json"); d = json.load(open(CTL_P)); d["programme"]["lock"] = "/tmp/another.lock"
    json.dump(d, open(tmp, "w"))
    keep = PG.CONTROLS
    try:
        PG.CONTROLS = tmp                                                                                 # a controls-only edit, code untouched
        assert "not the adopted bytes" in PG.controls_authority_problem()
        assert "not the adopted bytes" in PG.lineage_problem()
    finally:
        PG.CONTROLS = keep
    ad = json.load(open(PG.CONTROLS_ADOPTION)); rv = ad["review_record"]["path"]
    open(rv, "w").write("verdict without the line\n"); ad["review_record"]["sha256"] = SA.sha_file(rv); json.dump(ad, open(PG.CONTROLS_ADOPTION, "w"))
    assert "does not carry" in PG.controls_authority_problem()
    keep_t = PG.tracked_unmodified
    try:
        PG.tracked_unmodified = lambda rel: False
        _adopt_controls()
        assert "not git-tracked" in PG.controls_authority_problem()
    finally:
        PG.tracked_unmodified = keep_t
    _adopt_controls()
    assert PG.controls_authority_problem() == ""


def test_the_release_reports_raw_chain_failures_also_for_a_failed_original():
    bank, bmp, tgt = _bank()
    refit, rp, orig, op = _screen(bmp)
    seed4 = SH.task(refit, 4)["seed"]
    def wrap(stub):
        def failing(ds, cfg, seed, outer_folds=None, n_jobs=1):
            r = stub(ds, cfg, seed, outer_folds=outer_folds)
            if getattr(ds, "group", None) is None and seed == seed4:
                r["failed"] = True; r["failed_reason"] = "stub original failure"
            return r
        return failing
    CALLS["fail_all"] = True                                                                             # every stub RESAMPLE flagged failed
    try:
        _produce(refit, rp, orig, op, wrap=wrap)
    finally:
        CALLS["fail_all"] = False
    tg = json.load(open(tgt)); rv = os.path.join("reviews", f"_test_target_review_{os.getpid()}.md"); ad = os.path.join("reviews", f"_test_adoption_{os.getpid()}.json")
    open(os.path.join(T1, rv), "w").write(f"ADOPT row19-numerical-target target={REL.sha_file(tgt)} bank_records={tg['records_sha256']} verdict=FAVOURABLE\n")
    json.dump(dict(schema=REL.ADOPTION_SCHEMA, target_sha256=REL.sha_file(tgt), bank_manifest_sha256=REL.sha_file(bmp),
                   bank_binding_sha256=REL.sha_file(os.path.join(bank["storage"]["root"], "bank_binding.json")),
                   manifests=dict(screen=REL.sha_file(rp), originals=REL.sha_file(op)),
                   consumer_pins={f: REL.sha_file(os.path.join(T1, f)) for f in REL.CONSUMER_FILES},
                   review_record=dict(path=rv, sha256=REL.sha_file(os.path.join(T1, rv)))), open(os.path.join(T1, ad), "w"))
    try:
        with _Patched():
            r = REL.release(rp, op, tgt, ad, check_git=False)
        assert r["status"] == "RELEASED", r.get("reasons")
        assert "4" in r["failed_originals"] and r["raw_chains"]["4"]["unit_status"].startswith("original failed")
        B = int(refit["cfg"]["n_boot_refit"])
        assert r["raw_chains"]["4"]["per_predictor"]["selection"]["n_failed"] == B                       # the restored chain's own counts, not zeros
        assert len(r["raw_chains"]["4"]["failed_reasons"]) == B
    finally:
        for f in (rv, ad):
            if os.path.exists(os.path.join(T1, f)):
                os.remove(os.path.join(T1, f))


def test_unicode_digit_aliases_are_not_canonical():
    SVF = _load("row19_screen_verify")
    assert SVF.canonical_index("rec_000.json") == 0
    assert SVF.canonical_index("rec_\u0660\u0660\u0660.json") is None                                    # Arabic-Indic zeros
    assert SVF.canonical_index("rec_\uff10\uff10\uff10.json") is None                                    # full-width zeros
    assert SVF.canonical_index("rec_000_extra.json") is None and SVF.canonical_index("rec_0000.json") is None
    assert SVF.REPDIR.match("rep3") and not SVF.REPDIR.match("rep03") and not SVF.REPDIR.match("rep\u0663")


def test_the_wrapper_derives_its_proposal_and_checks_the_lineage():
    bank, bmp, _ = _bank()
    refit, rp, orig, op = _screen(bmp)
    assert PG.lineage_problem() == ""
    rc, out = _call(PG, ["run", "--manifest", rp, "--jobs", "1", "--cores", "24", "--walltime-h", "30", "--", "true"])
    assert rc == 0, out
    rc, out = _call(PG, ["run", "--manifest", rp, "--jobs", "200", "--cores", "24", "--walltime-h", "30", "--", "true"])
    assert rc == 2 and "allocation" in out                                                               # 144,000 derived core-hours refused
    log = os.path.join(_LIVE, "programme_admissions.jsonl")
    kinds = [json.loads(l)["kind"] for l in open(log)]
    assert "admission" in kinds and "refused" in kinds


def test_the_programme_count_is_strict():
    bank, bmp, _ = _bank()
    refit, rp, orig, op = _screen(bmp)
    f = PG.programme_funding(refit)
    assert PG.committed_core_h(f)[0] == 6.0                                                              # both ledgers absent, never started
    os.makedirs(os.path.join(refit["storage"]["root"], "plans"), exist_ok=True); open(os.path.join(refit["storage"]["root"], "plans", "job_1.json"), "w").write("{}")
    assert "holds plans" in PG.funding_problem(f, 10.0)                                                  # a started campaign without its ledger
    L = SA.ledger_for(refit); tok, _ = L.reserve("shard", 1, 24, 108000.0, refit["storage"]["root"])
    assert PG.funding_problem(f, 10.0) == ""
    lp = os.path.join(refit["storage"]["campaign"], "budget.json")
    for mut, msg in ((lambda e: e.update(reserved_core_h=True), "finite non-negative reservation"), (lambda e: e.update(reserved_core_h=-5.0), "finite non-negative"),
                     (lambda e: e.update(state="settled", settled_core_h=None), "settled entry"), (lambda e: e.update(state="odd"), "undeclared state")):
        st = json.load(open(lp)); mut(st["entries"][tok]); json.dump(st, open(lp, "w"))
        assert msg in PG.funding_problem(f, 10.0), msg
        L2 = json.load(open(lp)); L2["entries"][tok] = dict(L2["entries"][tok], state="live", reserved_core_h=720.0, settled_core_h=0.0); json.dump(L2, open(lp, "w"))
    src = open(lp).read(); assert '"reserved_core_h": 720.0' in src                                     # read BEFORE truncating the file
    open(lp, "w").write(src.replace('"reserved_core_h": 720.0', '"reserved_core_h": NaN'))
    assert "non-finite NaN" in PG.funding_problem(f, 10.0)
    assert "listed twice" in PG.funding_problem(dict(f, campaigns=f["campaigns"] + [f["campaigns"][0]]), 10.0)
    assert "expected but missing" in PG.funding_problem(dict(f, campaigns=["/nonexistent/campaign"]), 10.0)
    assert "finite positive" in PG.funding_problem(f, float("nan"))


def test_verifier_canonical_names_and_conflicting_duplicates():
    SVF = _load("row19_screen_verify")
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=10)
        assert _run(d, man, "--job-id", "j1", "--segment", "1") in (R19.DONE, R19.RESUME)
        sroot = tempfile.mkdtemp(); sman = dict(copy.deepcopy(man), storage={"root": sroot, "campaign": c})
        smp = os.path.join(sroot, "shard_manifest.json"); json.dump(sman, open(smp, "w"))
        assert _call(SH, ["worker", "--manifest", smp, "--rep", "0", "--indices", "0", "--slot", "0", "--job-id", "x", "--skip-environment-check", "--no-binding-check"])[0] == 0
    screen = {"anchors": {"reps": [0], "shard_manifest": smp, "shard_manifest_sha256": SVF.sha_file(smp), "sequential_root": d, "required_overlap": {"0": [0]}}}
    assert SVF.anchors(screen)["reps"]["0"]["equal"] == [0]
    shutil.copy(SH.record_path(sroot, 0, 0), os.path.join(sroot, "records", "rep0", "rec_000_extra.json"))
    v = SVF.anchors(screen)["reps"]["0"]
    assert any("non-canonical" in x for x in v["invalid"])                                              # an alias is reported, not parsed
    t = SH.task(man, 0); ck = os.path.join(d, "ckpt", f"refit_{t['ident'][:24]}.jsonl")
    line = open(ck).read().splitlines()[0]; rec = json.loads(line); rec["stats"]["selection"]["ws"] += 1e-9; rec["sha"] = A._record_sha(rec)
    open(ck, "a").write(json.dumps(rec) + "\n")
    v = SVF.anchors(screen)["reps"]["0"]
    assert v["conflict"] == [0] and 0 not in v["equal"]                                                 # a differing duplicate cannot hide
    assert any("conflicting" in a for a in SV.anchor_alarms({"anchors": {"problem": "", "reps": {"0": v, "1": v, "2": v}}}))


def test_the_verifier_compares_anchors_under_their_own_contract():
    SVF = _load("row19_screen_verify")
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=10)
        assert _run(d, man, "--job-id", "j1", "--segment", "2") in (R19.DONE, R19.RESUME)                # sequential records 0 and 1 of rep 0
        sroot = tempfile.mkdtemp()
        sman = dict(copy.deepcopy(man), storage={"root": sroot, "campaign": c})
        smp = os.path.join(sroot, "shard_manifest.json"); json.dump(sman, open(smp, "w"))
        rc, out = _call(SH, ["worker", "--manifest", smp, "--rep", "0", "--indices", "0,1", "--slot", "0", "--job-id", "x",
                             "--skip-environment-check", "--no-binding-check"])
        assert rc == 0, out
    screen = {"anchors": {"reps": [0], "shard_manifest": smp, "shard_manifest_sha256": SVF.sha_file(smp), "sequential_root": d,
                          "required_overlap": {"0": [0]}}}
    v = SVF.anchors(screen)
    assert v["problem"] == "" and v["reps"]["0"]["equal"] == [0, 1] and not v["reps"]["0"]["differ"] and not v["reps"]["0"]["missing"]
    p = SH.record_path(sroot, 0, 1); rec = json.load(open(p)); rec["stats"]["selection"]["ws"] = rec["stats"]["selection"]["ws"] + 1e-12
    rec["sha"] = A._record_sha(rec); json.dump(rec, open(p, "w"))
    v = SVF.anchors(screen)
    assert v["reps"]["0"]["differ"] == [1]                                                               # one float bit apart is a difference
    os.remove(SH.record_path(sroot, 0, 0))
    v = SVF.anchors(screen)
    assert v["reps"]["0"]["missing"] == [0]
    screen["anchors"]["shard_manifest_sha256"] = "0" * 64
    assert "not the declared bytes" in SVF.anchors(screen)["problem"]


def test_a_settled_job_without_a_runner_end_invalidates_a_running_receipt():
    refit, rp, root, L, jobs, want, good_q, q = _pilot_setup()
    rv = _adopt(refit, rp, q); keep_t = SA.tracked_unmodified
    try:
        SA.tracked_unmodified = lambda rel: True
        assert SA.adopt_review(refit, rp, "refit", rv, 9).startswith("adopted")
        tok2, _ = L.reserve("shard", 2, 24, 108000.0, root); L.bind(tok2, "P2")
        json.dump(dict(jobs[1], token=tok2), open(os.path.join(root, "plans", "job_2.json"), "w"))
        for sl in jobs[1]["slots"]:
            open(os.path.join(root, f"task_{sl['rep']}.json"), "w").write(json.dumps({"binding": {"rep": sl["rep"]}}))
        r, doc = _receipt(refit, rp, root, {"1": _summary(), "2": dict(_summary(), state="R", job_id="P2")})
        assert SA.review_problem(refit, rp, "refit", [3]) == ""
        L.settle("P2", 76.0, 24, "killed by the node after 76 s; no runner end; settled from qstat -xf")      # no runner_end at all
        assert "SETTLED" in SA.review_problem(refit, rp, "refit", [3])                                       # C1: refused within the window
    finally:
        SA.tracked_unmodified = keep_t
        if os.path.exists(os.path.join(T1, rv)):
            os.remove(os.path.join(T1, rv))
