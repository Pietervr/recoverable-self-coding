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
    man["datasets"] = {"seed_base": 20261003, "reps": list(reps), "n_attempted": len(reps), "excluded_resolved_seeds": [1] + list(extra_excluded),
                       "resolved_seeds_sha256": SA.seeds_sha256(sd), "bank_manifest": bank_mp, "bank_manifest_sha256": SA.sha_file(bank_mp)}
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
        m["budget"]["admission"] = bp; m["funding"]["campaigns"] = [refit["storage"]["campaign"], orig["storage"]["campaign"]]
    rp, op = os.path.join(root, "screen_manifest.json"), os.path.join(root, "orig_manifest.json")
    json.dump(refit, open(rp, "w")); json.dump(orig, open(op, "w"))
    return refit, rp, orig, op


def _produce(refit, rp, orig, op, skip=()):
    """Stub originals and every refit record for the screen."""
    with _Patched():
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
    m = copy.deepcopy(refit); m["datasets"]["excluded_resolved_seeds"] = [SA.seeds_of(refit)[3]]
    assert "excluded" in SA.seed_domain_problem(m)
    m = copy.deepcopy(refit); m["datasets"]["excluded_resolved_seeds"] = []
    assert "empty" in SA.seed_domain_problem(m)
    m = copy.deepcopy(refit); m["datasets"]["identities"].pop("5")
    assert "identity map" in SA.seed_domain_problem(m)
    m = copy.deepcopy(refit); m["datasets"]["bank_manifest_sha256"] = "0" * 64
    assert "bank manifest" in SA.seed_domain_problem(m)
    bank2 = copy.deepcopy(bank); bank2["datasets"]["seed_base"] = 20261003; bank2["datasets"]["reps"] = [3, 9]
    bank2["datasets"]["resolved_seeds_sha256"] = B22.seeds_sha256(B22.resolved_seeds(bank2))
    bp2 = os.path.join(tempfile.mkdtemp(), "b2.json"); json.dump(bank2, open(bp2, "w"))
    m = copy.deepcopy(refit); m["datasets"]["bank_manifest"] = bp2; m["datasets"]["bank_manifest_sha256"] = SA.sha_file(bp2)
    assert "bank seed" in SA.seed_domain_problem(m)                                                    # derived from the bank manifest, not a caller list
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
    L2 = SA.ledger_for(refit); L2.raise_cap(90000.0, "owner ruling for the test")
    st = json.load(open(os.path.join(refit["storage"]["campaign"], "budget.json")))
    assert st["cap_core_h"] == 90000.0 and st["cap_history"][-1]["old"] == 60000.0 and tok in st["entries"]
    assert SA.sha_file(rp) == before                                                                     # no binding can name a moved manifest
    assert SA.ledger_for(refit).reserve("shard", 2, 24, 108000.0, refit["storage"]["root"])[0]          # admitted under the raised cap
    assert SA.funding_problem(refit, 1000.0) == ""
    assert "allocation" in SA.funding_problem(refit, 99000.0)                                            # 720 + 720 live + 6 + 99,000 > 100,000


def test_the_release_refuses_before_any_aggregation():
    bank, bmp, tgt = _bank()
    refit, rp, orig, op = _screen(bmp)
    _produce(refit, rp, orig, op)
    rv = os.path.join("reviews", f"_test_target_review_{os.getpid()}.md"); ad = os.path.join("reviews", f"_test_adoption_{os.getpid()}.json")
    open(os.path.join(T1, rv), "w").write("adopts the target\n")
    tg = json.load(open(tgt))
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
    open(os.path.join(T1, rv), "w").write("adopts the target\n")
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


def test_later_admission_binds_only_started_tasks_and_refuses_stale_or_unadopted_evidence():
    bank, bmp, _ = _bank()
    refit, rp, orig, op = _screen(bmp, reps=list(range(3, 30)), B=4)
    root = refit["storage"]["root"]
    L = SA.ledger_for(refit); tok, _ = L.reserve("shard", 1, 24, 108000.0, root); L.bind(tok, "P1")
    jobs, _ = SA.plan_jobs(refit, "refit", 1, set(), set(), set())
    os.makedirs(os.path.join(root, "plans"), exist_ok=True); os.makedirs(os.path.join(root, "gate"), exist_ok=True)
    json.dump(dict(jobs[0], token=tok), open(os.path.join(root, "plans", "job_1.json"), "w"))
    for s in jobs[0]["slots"]:                                                                            # job-start binds only the started reps
        open(os.path.join(root, f"task_{s['rep']}.json"), "w").write(json.dumps({"binding": {"rep": s["rep"]}}))
    want = SA.expected_bound(refit, rp, "refit")
    assert sorted(int(k) for k in want["bindings"]) == list(range(3, 27))                                 # 24 bound; 27..29 pending, never fabricated
    q = os.path.join(root, "gate", "qualified_refit_job1.json")
    good_q = dict(schema=SA.QUAL_SCHEMA, role="refit", qualified_job=1, production=True, bound=dict(want, anchors_sha256="a"), receipt=dict(fresh=True, alarms=[]))
    json.dump(good_q, open(q, "w"))
    assert SA.qualification_problem(refit, rp, "refit")[0] == ""
    for bad, msg in ((dict(good_q, bound=dict(want, anchors_sha256=None)), "anchor"), (dict(good_q, role="orig"), "not a production"),
                     (dict(good_q, bound=dict(good_q["bound"], bindings={k: v for k, v in want["bindings"].items() if k != "3"})), "not bound")):
        json.dump(bad, open(q, "w"))
        assert msg in SA.qualification_problem(refit, rp, "refit")[0], msg
    json.dump(good_q, open(q, "w"))
    assert "no adopted review" in SA.review_problem(refit, rp, "refit", [2])
    tracked = "reviews/2026-10-06_stage2_screen_design_codex_record.md"
    assert SA.adopt_review(refit, rp, "refit", tracked, 9).startswith("adopted")
    assert "no watch receipt" in SA.review_problem(refit, rp, "refit", [2])
    r = os.path.join(root, "gate", f"watch_refit_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json")
    good_r = dict(schema=SA.WATCH_SCHEMA, role="refit", production=True, fresh=True, alarms=[], time=time.time(), bound=dict(want, anchors_sha256="a"))
    json.dump(dict(good_r, time=time.time() - 3000), open(r, "w"))
    assert "within 2700" in SA.review_problem(refit, rp, "refit", [2])
    json.dump(good_r, open(r, "w"))
    assert SA.review_problem(refit, rp, "refit", [2]) == ""
    assert "up to 9" in SA.review_problem(refit, rp, "refit", [10])
    open(os.path.join(root, "STOP"), "w").write("{}")
    assert "STOP" in SA.gate_problem(refit, rp, "refit", {1}, False, 1, [], 108000.0)


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
