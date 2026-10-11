"""Ledger row 22, the omega = 1 reference bank (chpc/row22_bank.py, row22_bank_submit.py, row22_target.py; 6 Oct 2026).
The bank's record of a dataset is the SLICE RUNNER's original fit of that dataset (bit-equal band statistics against the
slice's validated original cache); a valid record is never recomputed and any other file at a record path HOLDS; every
record has its timing, published first; STOP and a past deadline end with 75 and nothing computed; no worker runs without
the binding job-start publishes once, and evidence without a binding HOLDS; the seeds gate refuses duplicates, an excluded
seed or a list that is not declared; job-start reserves the 'bank' kind and job-end records the runner's end. Planner: DONE
is a validated record, a live job without its plan HOLDS, the gate admits the pilot alone first, then only under an adopted
review bounded to a job number, never past a STOP. Target: RESOLVED on a clean bank; UNRESOLVED on too many unusable
records, a heavy tail (the trimmed mean outside T) or an unstable split; INCOMPLETE before every record exists; the frozen
document is never overwritten. Evaluator: refuses an unresolved target, another binding, a different setting, cfg, code
pin or numerical snapshot, overlapping seeds, or missing bank seeds."""
import os
os.environ.setdefault("NPROC", "1")
import json, tempfile, importlib.util, sys, time, io, contextlib, hashlib, copy, math
import numpy as np
import analyze as A

T1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(T1, "chpc"))
def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(T1, "chpc", name + ".py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
B, SUB, TG, STV = _load("row22_bank"), _load("row22_bank_submit"), _load("row22_target"), _load("row22_bank_status")
_TEST_LIVE = tempfile.mkdtemp(prefix="row22_status_test_")
STV.LIVE_DIR = os.path.join(_TEST_LIVE, "live"); STV.RECEIPTS = os.path.join(_TEST_LIVE, "receipts")
from test_row19_slice import _manifest, _run, _dirs, _Patched, R19
from row19_ledger import CampaignLedger


def _bank_manifest(n=6, cores=4, excluded=()):
    root = tempfile.mkdtemp(); campaign = os.path.join(root, "campaign"); os.makedirs(campaign)
    man = _manifest(root, campaign, n_boot=10)
    man["datasets"] = {"seed_base": 777, "reps": list(range(n)), "excluded_resolved_seeds": list(excluded)}
    man["datasets"]["resolved_seeds_sha256"] = B.seeds_sha256(B.resolved_seeds(man))
    man["pbs"] = dict(man["pbs"], cores=cores, project="P", queue="serial", nodetype="haswell_reg", mem_gb=120, walltime_h=36,
                      deadline_reserve_s=1800, expect_original_s=0.0, deadline_margin=1.25)
    man["bank"] = {"toolchain": root, "clone": root, "per_slot": 1}
    man["storage"] = {"root": os.path.join(root, "bank"), "campaign": campaign}
    man["budget"] = {"core_hours_cap": 15000.0}
    man["target"] = {"level": 0.99, "max_unusable_fraction": 0.01, "trim_fraction": 0.005, "stability_z": 3.0,
                     "primary_predictor": "selection", "primary_band": "ws"}
    mp = os.path.join(root, "bank_manifest.json"); json.dump(man, open(mp, "w"))
    return man, mp


def _call(mod, argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        rc = mod.main(argv)
    return rc, buf.getvalue()


def _plan(man, job, slots):
    p = os.path.join(man["storage"]["root"], "plans", f"job_{job}.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump({"job": job, "slots": [{"slot": i, "reps": r} for i, r in enumerate(slots)]}, open(p, "w"))
    return p


def _start(mp, plan, job="bj1", *extra):
    return _call(B, ["job-start", "--manifest", mp, "--plan", plan, "--job-id", job, "--walltime-s", "3600", "--skip-environment-check", *extra])


def _worker(mp, reps, slot=0, job="bj1", deadline=None, binding=True):
    argv = ["worker", "--manifest", mp, "--reps", ",".join(str(r) for r in reps), "--slot", str(slot), "--job-id", job, "--skip-environment-check"]
    argv += [] if binding else ["--no-binding-check"]
    if deadline is not None:
        argv += ["--deadline-epoch", str(deadline)]
    return _call(B, argv)


def test_the_bank_record_is_the_slice_runners_original_bit_for_bit():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=10)
        assert _run(d, man, "--job-id", "j1", "--segment", "1") in (R19.DONE, R19.RESUME)       # the slice computes and caches rep 0's original
        t = B.SH.task(man, 0)
        orig, why = R19.read_orig(os.path.join(d, "orig", f"orig_{t['ident'][:24]}.json"), t["ident"], t["code_hash"], t["ds"], t["cfg"], t["folds"])
        assert orig is not None, why
        want = {p: A._band_stats(np.asarray(orig["run"]["delta"][p], dtype=float), t["masks"]) for p in A.PREDICTORS}
        rec = B.original_record(t, 0)
    for p in A.PREDICTORS:
        for b, v in want[p].items():
            assert np.float64(rec["stats"][p][b]).tobytes() == np.float64(v).tobytes(), (p, b)
    assert B.record_ok(rec, t, 0) and rec["seed"] == t["seed"] and rec["ident"] == t["ident"] and rec["policy"] == t["cfg"].start_policy
    bad = dict(rec, seed=rec["seed"] + 1)
    assert not B.record_ok(bad, t, 0) and not B.record_ok(rec, t, 1)


def test_worker_publishes_once_never_recomputes_and_holds_on_a_foreign_file():
    man, mp = _bank_manifest()
    with _Patched():
        rc, out = _worker(mp, [0])
        assert rc == B.HELD and "no bank binding" in out                                        # job-start publishes the binding, never a worker
        plan = _plan(man, 1, [[0, 1], [2]])
        rc, out = _start(mp, plan, "bj1", "--no-reservation")
        assert rc == B.DONE, out
        rc, out = _worker(mp, [0, 1])
        assert rc == B.DONE, out
        root = man["storage"]["root"]
        for r in (0, 1):
            assert os.path.exists(B.record_path(root, r)) and os.path.exists(B.timing_path(root, r))
        from test_row19_slice import CALLS
        n0 = CALLS["run_dataset"]
        rc, out = _worker(mp, [0, 1])
        assert rc == B.DONE and CALLS["run_dataset"] == n0 and "resumed [0, 1]" in out             # nothing recomputed
        p = B.record_path(root, 1); d = json.load(open(p)); d["stats"]["selection"]["ws"] += 1.0
        json.dump(d, open(p, "w"))
        rc, out = _worker(mp, [1])
        assert rc == B.HELD and "cannot accept" in out                                              # an edited record holds
        rc, out = _start(mp, plan, "bj1", "--no-reservation")
        assert rc == B.DONE                                                                         # the binding is equal: admitted again
        json.dump(dict(json.load(open(os.path.join(root, "bank_binding.json"))), seed_base=1), open(os.path.join(root, "bank_binding.json"), "w"))
        rc, out = _worker(mp, [2])
        assert rc == B.HELD and "differs" in out
        st = json.load(open(os.path.join(root, "status", "jobbj1.slot0.json")))
        assert st["exit"] == B.HELD and st["reps"] == [2]


def test_stop_deadline_and_seed_gate():
    man, mp = _bank_manifest()
    with _Patched():
        plan = _plan(man, 1, [[0], [1]])
        assert _start(mp, plan, "bj1", "--no-reservation")[0] == B.DONE
        root = man["storage"]["root"]
        open(os.path.join(root, "STOP"), "w").write("{}")
        rc, out = _worker(mp, [0])
        assert rc == B.RESUME and "stop requested" in out and not os.path.exists(B.record_path(root, 0))
        os.remove(os.path.join(root, "STOP"))
        rc, out = _worker(mp, [0], deadline=time.time() - 10)
        assert rc == B.RESUME and "deadline" in out and not os.path.exists(B.record_path(root, 0))
    seeds = B.resolved_seeds(man)
    man2, mp2 = _bank_manifest(excluded=[seeds[3]])
    assert "excluded" in B.seed_problems(man2)
    man3 = copy.deepcopy(man); man3["datasets"]["resolved_seeds_sha256"] = "0" * 64
    assert "not the manifest" in B.seed_problems(man3)
    json.dump(man3, open(mp, "w"))
    rc, out = _start(mp, _plan(man3, 2, [[0]]), "bj2", "--no-reservation")
    assert rc == B.HELD and "not the manifest" in out


def test_evidence_without_binding_holds_and_job_start_end_use_the_bank_kind():
    man, mp = _bank_manifest()
    root = man["storage"]["root"]
    os.makedirs(os.path.join(root, "records"), exist_ok=True)
    open(B.record_path(root, 0), "w").write("{}")
    rc, out = _start(mp, _plan(man, 1, [[1]]), "bj1", "--no-reservation")
    assert rc == B.HELD and "without a bank binding" in out
    man, mp = _bank_manifest()
    with _Patched():
        L = CampaignLedger(man["storage"]["campaign"], 15000.0)
        tok, _ = L.reserve("bank", 1, 4, 3600.0, man["storage"]["root"])
        plan = _plan(man, 1, [[0]])
        rc, out = _start(mp, plan, "bj1", "--reservation-token", tok)
        assert rc == B.DONE and "bank job 1" in out, out
        assert _worker(mp, [0])[0] == B.DONE
        rc, out = _call(B, ["job-end", "--manifest", mp, "--plan", plan, "--job-id", "bj1", "--reservation-token", tok, "--started-epoch", str(time.time() - 5)])
        assert rc == B.RESUME or rc == B.DONE
        e = json.load(open(os.path.join(man["storage"]["campaign"], "budget.json")))["entries"][tok]
        assert e["kind"] == "bank" and e["state"] == "live" and e["runner_exit"] in (0, 75)
    try:
        L.reserve("bank", 1, 4, 3600.0, man["storage"]["root"])
        assert False, "a bank job number is reserved once"
    except RuntimeError:
        pass


def test_planner_and_gate():
    man, mp = _bank_manifest(n=10, cores=4)
    root = man["storage"]["root"]
    done, flight, used, problems = SUB.evidence(man)
    assert not done and not flight and not used and not problems
    jobs, left = SUB.plan_jobs(man, 2, 1, done, flight, used)
    assert [len(j["slots"]) for j in jobs] == [4, 4] and left == 2 and jobs[0]["job"] == 1
    assert SUB.gate_problem(man, used, True, 1, [1]) == ""
    assert "the pilot is exactly one job" in SUB.gate_problem(man, used, True, 2, [1, 2])
    assert "say --pilot" in SUB.gate_problem(man, used, False, 1, [1])
    L = CampaignLedger(man["storage"]["campaign"], 15000.0)
    tok, _ = L.reserve("bank", 1, 4, 3600.0, root); L.bind(tok, "p1")
    done, flight, used, problems = SUB.evidence(man)
    assert problems and "plan" in problems[0]                                                      # a live job without its plan HOLDS
    _plan(man, 1, [[0], [1], [2], [3]])
    done, flight, used, problems = SUB.evidence(man)
    assert not problems and flight == {0, 1, 2, 3} and used == {1}
    jobs, left = SUB.plan_jobs(man, 5, 1, done, flight, used)
    assert jobs[0]["job"] == 2 and jobs[0]["slots"][0]["reps"] == [4]
    assert "--pilot is only for the first" in SUB.gate_problem(man, used, True, 1, [2])
    assert "no adopted review" in SUB.gate_problem(man, used, False, 1, [2])
    rec = os.path.join("reviews", f"_test_bank_review_{os.getpid()}.md")
    open(os.path.join(T1, rec), "w").write("favourable\n")
    try:
        assert "not tracked by git" in SUB.adopt_review(man, rec, 3)                                  # an untracked file is no review
    finally:
        os.remove(os.path.join(T1, rec))
    tracked = "reviews/2026-10-06_row22_bank_codex_record.md"                                          # committed, unmodified
    assert SUB.adopt_review(man, tracked, 3).startswith("adopted")
    assert SUB.adopt_review(man, tracked, 9).startswith("REFUSED")                                     # never overwritten
    assert SUB.gate_problem(man, used, False, 1, [2]) == ""
    assert "up to 3" in SUB.gate_problem(man, used, False, 2, [2, 4])
    open(os.path.join(root, "STOP"), "w").write("{}")
    assert "STOP" in SUB.gate_problem(man, used, False, 1, [2])
    os.makedirs(os.path.join(root, "records"), exist_ok=True)
    open(B.record_path(root, 5), "w").write("{}")
    assert any("cannot accept" in p for p in SUB.evidence(man)[3])                                    # a bad record HOLDS the planner
    script = SUB.pbs_script(man, jobs[0], "tok", 3600.0, "serial", root, root, "chpc/row22_bank_manifest.json")
    assert "row22_bank.py worker" in script and "--reps 4" in script and "job-start" in script and "job-end" in script


def _recs(values, failed=()):
    return [None if i in failed else v for i, v in enumerate(values)]


def test_target_rules():
    R = TG.rules({"target": {}})
    rng = np.random.default_rng(1)
    x = list(rng.normal(-0.9, 0.36, size=408)); reps = list(range(408))
    s = TG.summarise(x, reps, R, 408)
    assert s["status"] == "RESOLVED" and s["lo"] < -0.9 < s["hi"] and abs((s["hi"] - s["lo"]) / 2 - 2.59 * 0.36 / math.sqrt(408)) < 0.01
    s = TG.summarise(x[:400], reps[:400], R, 408)
    assert s["status"] == "INCOMPLETE"
    s = TG.summarise(_recs(x, failed=range(10)), reps, R, 408)
    assert s["status"] == "UNRESOLVED" and "unusable fraction" in s["reasons"][0]
    y = list(x); y[0] = -2650.0                                                                       # the omega = 2 kind of dataset
    s = TG.summarise(y, reps, R, 408)
    assert s["status"] == "UNRESOLVED" and any("tail" in r for r in s["reasons"])
    w = [v * 3.0 for v in x]                                                                       # resolved but too wide to adjudicate
    s = TG.summarise(w, reps, R, 408)
    assert s["status"] == "UNRESOLVED" and any("precision" in r for r in s["reasons"])
    z = [v + (0.5 if r % 2 else 0.0) for r, v in zip(reps, x)]
    s = TG.summarise(z, reps, R, 408)
    assert s["status"] == "UNRESOLVED" and any("stability" in r for r in s["reasons"])


def test_freeze_and_evaluator():
    man, mp = _bank_manifest(n=6)
    with _Patched():
        plan = _plan(man, 1, [[0, 1, 2], [3, 4, 5]])
        assert _start(mp, plan, "bj1", "--no-reservation")[0] == B.DONE
        assert _worker(mp, [0, 1, 2, 3, 4, 5])[0] == B.DONE
        out = os.path.join(man["storage"]["root"], "gate", "target.json")
        msg = TG.freeze(man, mp, out)
        assert msg.startswith("frozen"), msg
        assert TG.freeze(man, mp, out).startswith("REFUSED")
    doc = json.load(open(out)); bp = os.path.join(man["storage"]["root"], "bank_binding.json"); bb = json.load(open(bp))
    assert doc["primary"] == "selection/ws" and doc["bank_binding_sha256"] == TG.sha_file(bp)
    doc_ok = dict(doc, status="RESOLVED")
    # the screen manifest: its own seed base and reps, naming THIS bank manifest (the reviewed seed-domain checker is injected:
    # its exclusion contract needs the history manifests, tested in the screen admission's own suite)
    smp = os.path.join(os.path.dirname(mp), "screen_manifest.json")
    sman = dict(setting=man["setting"], datasets=dict(seed_base=int(man["datasets"]["seed_base"]) + 7, reps=[3, 4, 5],
                                                      bank_manifest_sha256=TG.sha_file(mp)))
    json.dump(sman, open(smp, "w"))
    ok_check = lambda m: ""
    screen = dict(setting=bb["setting"], cfg=dict(bb["cfg"], n_boot_refit=200), code=dict(bb["code"]), numerical=bb["numerical"],
                  manifest_sha256=TG.sha_file(smp))
    C = lambda d=doc_ok, b=bb, bs=None, sc=None, bm=mp, sm=smp, chk=ok_check: TG.compatible(d, b, TG.sha_file(bp) if bs is None else bs,
                                                                                         screen if sc is None else sc, bm, sm, chk)
    assert C() == [], C()
    assert any("RESOLVED" in w for w in C(d=dict(doc, status="UNRESOLVED")))
    assert any("another bank binding" in w for w in C(bs="0" * 64))
    assert any("setting" in w for w in C(sc=dict(screen, setting=dict(bb["setting"], D=8))))
    assert any("cfg" in w for w in C(sc=dict(screen, cfg=dict(screen["cfg"], start_policy="old"))))
    assert any("code pins" in w for w in C(sc=dict(screen, code=dict(screen["code"], **{"models.py": "x"}))))
    assert any("numerical" in w for w in C(sc=dict(screen, numerical={})))
    bank_seeds = sorted(B.resolved_seeds(man).values())
    # Codex's static counterexample: a bank seed offered as a screen seed with bank_seeds=[] - the lists are never trusted
    assert any("foreign" in w for w in C(sc=dict(screen, seeds=[bank_seeds[0]], bank_seeds=[])))
    assert any("foreign" in w for w in C(sc=dict(screen, bank_seeds=bank_seeds[:-1])))
    assert C(sc=dict(screen, bank_seeds=bank_seeds)) == []                       # a correct supplied list is only compared
    # real overlap: a screen manifest whose seed base reproduces the bank's seeds
    omp = os.path.join(os.path.dirname(mp), "screen_overlap.json")
    json.dump(dict(sman, datasets=dict(sman["datasets"], seed_base=int(man["datasets"]["seed_base"]), reps=[0, 1])), open(omp, "w"))
    assert any("bank seed(s) are screen seeds" in w for w in C(sm=omp, sc=dict(screen, manifest_sha256=TG.sha_file(omp))))
    assert any("screen seed domain fails" in w for w in C(chk=lambda m: "a screen seed is in the excluded set"))
    empty = os.path.join(os.path.dirname(mp), "screen_empty.json")
    json.dump(dict(sman, datasets=dict(sman["datasets"], reps=[])), open(empty, "w"))
    assert any("screen seed domain is empty" in w for w in C(sm=empty, sc=dict(screen, manifest_sha256=TG.sha_file(empty))))
    assert any("screen manifest is missing" in w for w in C(sm=None))
    assert any("bank manifest is missing" in w for w in C(bm=None))
    assert any("another screen manifest" in w for w in C(sc=dict(screen, manifest_sha256=None)))
    fmp = os.path.join(os.path.dirname(mp), "screen_foreign_bank.json")
    json.dump(dict(sman, datasets=dict(sman["datasets"], bank_manifest_sha256="0" * 64)), open(fmp, "w"))
    assert any("names another bank manifest" in w for w in C(sm=fmp, sc=dict(screen, manifest_sha256=TG.sha_file(fmp))))
    assert any("frozen from another bank manifest" in w for w in C(d=dict(doc_ok, manifest_sha256="0" * 64)))
    assert any("binding names another bank manifest" in w for w in C(b=dict(bb, manifest_sha="0" * 64)))
    assert any("not the one the bank binding records" in w for w in C(b=dict(bb, seeds_sha256="0" * 64)))

def _status_snapshot(man, slots_status, verify_reps, ledger_entries):
    """A constructed local snapshot for row22_bank_status (no pull): plans, statuses and the ledger, plus a verify document."""
    shutil_root = os.path.join(STV.LIVE_DIR, "root")
    import shutil
    shutil.rmtree(STV.LIVE_DIR, ignore_errors=True)
    os.makedirs(os.path.join(shutil_root, "plans")); os.makedirs(os.path.join(shutil_root, "status")); os.makedirs(os.path.join(STV.LIVE_DIR, "campaign"))
    json.dump({"job": 1, "slots": [{"slot": 0, "reps": [0]}, {"slot": 1, "reps": [1]}]}, open(os.path.join(shutil_root, "plans", "job_1.json"), "w"))
    for slot, st in slots_status.items():
        json.dump(st, open(os.path.join(shutil_root, "status", f"jobP1.slot{slot}.json"), "w"))
    json.dump({"cap_core_h": 15000.0, "entries": ledger_entries}, open(os.path.join(STV.LIVE_DIR, "campaign", "budget.json"), "w"))
    vp = os.path.join(_TEST_LIVE, "verify.json")
    json.dump({"schema": "row22-bank-verify-1", "reps": verify_reps, "seed_problem": "", "environment_bad": [], "code_bad": [], "binding_equal": True}, open(vp, "w"))
    return vp


def _st(reps, new, resumed, left, exit_):
    return dict(job="P1", reps=reps, new=new, resumed=resumed, left=left, exit=exit_, wall_s=10.0, cpu_s=9.0, maxrss=1.0e9)


def _vrep(job="P1", slot=0, ok=True):
    return {"declared": True, "record": {"ok": ok, "sha": "x", "failed": False} if ok else {"ok": False, "reason": "bad"},
            "timing": {"ok": True, "job": job, "slot": slot, "wall_s": 5.0, "maxrss": 1.0, "failed": False}}


def test_status_reconciles_slots_records_timing_and_scheduler():
    man, mp = _bank_manifest(n=4)
    led = {"t1": {"kind": "bank", "rep": 1, "job_id": "P1", "token": "t1", "state": "live", "reserved_core_h": 96.0, "runner_exit": 0}}
    pbs = os.path.join(_TEST_LIVE, "pbs.json")
    json.dump({"P1": {"state": "F", "exit": 0, "mem_kb": 1000}}, open(pbs, "w"))
    vp = _status_snapshot(man, {0: _st([0], [0], [], [], 0), 1: _st([1], [1], [], [], 0)}, {"0": _vrep(slot=0), "1": _vrep(slot=1)}, led)
    rc, out = _call(STV, ["--manifest", mp, "--no-pull", "--verify-file", vp, "--pbs-file", pbs])
    assert "ALARMS" not in out and "workers ended 2/2" in out, out
    rc, out = _call(STV, ["--manifest", mp, "--no-pull", "--verify-file", vp, "--pbs-file", pbs, "--qualify", "1"])
    assert rc == 1 and "not fresh production evidence" in out                                       # a test snapshot never qualifies
    cases = [
        ({0: _st([0], [0], [], [], 0)}, {"0": _vrep(slot=0), "1": _vrep(slot=1)}, "no worker status after the job ended"),
        ({0: _st([0], [0], [0], [], 0), 1: _st([1], [1], [], [], 0)}, {"0": _vrep(slot=0), "1": _vrep(slot=1)}, "not a partition"),
        ({0: _st([0], [0], [], [], 4), 1: _st([1], [1], [], [], 0)}, {"0": _vrep(slot=0), "1": _vrep(slot=1)}, "worker exit 4"),
        ({0: _st([0], [0], [], [], 0), 1: _st([1], [1], [], [], 0)}, {"0": _vrep(slot=0), "1": _vrep(slot=0)}, "timing names job"),
        ({0: _st([0], [0], [], [], 0), 1: _st([1], [1], [], [], 0)}, {"0": _vrep(slot=0), "1": _vrep(slot=1, ok=False)}, "no valid record"),
        ({0: _st([0], [0], [], [], 0), 1: _st([1], [1], [], [], 0)}, {"0": _vrep(slot=0), "1": _vrep(slot=1), "3": _vrep(slot=0)}, "foreign evidence"),
        ({0: _st([0], [], [], [0], 0), 1: _st([1], [1], [], [], 0)}, {"0": _vrep(slot=0), "1": _vrep(slot=1)}, "exit 0 with reps left"),
    ]
    for sts, vr, msg in cases:
        vp = _status_snapshot(man, sts, vr, led)
        rc, out = _call(STV, ["--manifest", mp, "--no-pull", "--verify-file", vp, "--pbs-file", pbs])
        assert rc == 1 and msg in out, (msg, out[-600:])
    vp = _status_snapshot(man, {0: _st([0], [0], [], [], 0), 1: _st([1], [1], [], [], 0)}, {"0": _vrep(slot=0), "1": _vrep(slot=1)},
                          {"t1": dict(led["t1"], runner_exit=None)})
    rc, out = _call(STV, ["--manifest", mp, "--no-pull", "--verify-file", vp, "--pbs-file", pbs])
    assert rc == 1 and "no runner end in the ledger" in out
    json.dump({"P1": {"state": "F", "exit": 271, "mem_kb": 1000}}, open(pbs, "w"))
    vp = _status_snapshot(man, {0: _st([0], [0], [], [], 0), 1: _st([1], [1], [], [], 0)}, {"0": _vrep(slot=0), "1": _vrep(slot=1)}, led)
    rc, out = _call(STV, ["--manifest", mp, "--no-pull", "--verify-file", vp, "--pbs-file", pbs])
    assert rc == 1 and "exit 271" in out


def test_a_failed_scheduler_call_is_a_failed_observation_whatever_its_stdout():
    keep = STV.sh
    try:
        STV.sh = lambda cmd, timeout=600: (1, "Job Id: P1\n    job_state = F\n", "error")
        obs, why = STV.pbs_observe(["P1"])
        assert obs is None and "qstat failed" in why
        STV.sh = lambda cmd, timeout=600: (0, "Job Id: P1\n    job_state = R\n", "")
        obs, why = STV.pbs_observe(["P1", "P2"])
        assert obs is None and "did not describe" in why
        obs, why = STV.pbs_observe(["P1"])
        assert obs["P1"]["state"] == "R" and why == ""
    finally:
        STV.sh = keep


def test_later_jobs_need_a_bound_qualification_and_a_fresh_receipt():
    man, mp = _bank_manifest(n=10, cores=4)
    root = man["storage"]["root"]; os.makedirs(os.path.join(root, "gate"), exist_ok=True)
    L = CampaignLedger(man["storage"]["campaign"], 15000.0)
    tok, _ = L.reserve("bank", 1, 4, 3600.0, root); L.bind(tok, "P1")
    _plan(man, 1, [[0], [1], [2], [3]])
    json.dump({"binding": 1}, open(os.path.join(root, "bank_binding.json"), "w"))
    want = SUB.expected_bound(man, mp)
    tracked = "reviews/2026-10-06_row22_bank_codex_record.md"
    assert "no pilot qualification" in SUB.adopt_review(man, tracked, 17, mp)
    q = os.path.join(root, "gate", "qualified_bank_job1.json")
    good_q = dict(schema=SUB.QUAL_SCHEMA, qualified_job=1, production=True, bound=want, receipt=dict(fresh=True, alarms=[]))
    for bad in (dict(good_q, production=False), dict(good_q, receipt=dict(fresh=True, alarms=["x"])),
                dict(good_q, bound=dict(want, manifest_sha256="0" * 64)), dict(good_q, bound=dict(want, jobs={"1": dict(want["jobs"]["1"], token="other")}))):
        json.dump(bad, open(q, "w"))
        assert SUB.adopt_review(man, tracked, 17, mp).startswith("REFUSED"), bad
    json.dump(good_q, open(q, "w"))
    assert SUB.adopt_review(man, tracked, 17, mp).startswith("adopted")
    assert "no watch receipt" in SUB.review_problem(man, [2], mp)
    r = os.path.join(root, "gate", f"bank_watch_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json")
    good_r = dict(schema=SUB.WATCH_SCHEMA, production=True, fresh=True, alarms=[], time=time.time(), bound=want)
    json.dump(dict(good_r, time=time.time() - 3000), open(r, "w"))
    assert "within 2700" in SUB.review_problem(man, [2], mp)
    json.dump(dict(good_r, alarms=["a"]), open(r, "w"))
    assert "alarm" in SUB.review_problem(man, [2], mp)
    json.dump(good_r, open(r, "w"))
    assert SUB.review_problem(man, [2], mp) == ""
    tok2, _ = L.reserve("bank", 2, 4, 3600.0, root); L.bind(tok2, "P2"); _plan(man, 2, [[4]])
    assert "not the ledger's" in SUB.review_problem(man, [3], mp)                                       # the receipt must bind every job now
    json.dump(dict(good_q, production=True), open(q, "w")); open(q, "a").write(" ")
    assert "another qualification" in SUB.review_problem(man, [3], mp) or "not the ledger's" in SUB.review_problem(man, [3], mp)
