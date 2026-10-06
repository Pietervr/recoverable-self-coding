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
B, SUB, TG = _load("row22_bank"), _load("row22_bank_submit"), _load("row22_target")
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
        assert SUB.adopt_review(man, rec, 3).startswith("adopted")
        assert SUB.adopt_review(man, rec, 9).startswith("REFUSED")                                   # never overwritten
        assert SUB.gate_problem(man, used, False, 1, [2]) == ""
        assert "up to 3" in SUB.gate_problem(man, used, False, 2, [2, 4])
        open(os.path.join(T1, rec), "a").write("edited\n")
        assert "not in this clone with the adopted" in SUB.gate_problem(man, used, False, 1, [2])
    finally:
        os.remove(os.path.join(T1, rec))
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
    screen = dict(setting=bb["setting"], cfg=dict(bb["cfg"], n_boot_refit=200), code=dict(bb["code"]), numerical=bb["numerical"],
                  seeds=[1, 2, 3], bank_seeds=list(B.resolved_seeds(man).values()))
    assert TG.compatible(doc_ok, bb, TG.sha_file(bp), screen) == []
    assert any("RESOLVED" in w for w in TG.compatible(dict(doc, status="UNRESOLVED"), bb, TG.sha_file(bp), screen))
    assert any("another bank binding" in w for w in TG.compatible(doc_ok, bb, "0" * 64, screen))
    assert any("setting" in w for w in TG.compatible(doc_ok, bb, TG.sha_file(bp), dict(screen, setting=dict(bb["setting"], D=8))))
    assert any("cfg" in w for w in TG.compatible(doc_ok, bb, TG.sha_file(bp), dict(screen, cfg=dict(screen["cfg"], start_policy="old"))))
    assert any("code pins" in w for w in TG.compatible(doc_ok, bb, TG.sha_file(bp), dict(screen, code=dict(screen["code"], **{"models.py": "x"}))))
    assert any("numerical" in w for w in TG.compatible(doc_ok, bb, TG.sha_file(bp), dict(screen, numerical={})))
    assert any("screen seeds" in w for w in TG.compatible(doc_ok, bb, TG.sha_file(bp), dict(screen, seeds=[screen["bank_seeds"][0]])))
    assert any("not supplied" in w for w in TG.compatible(doc_ok, bb, TG.sha_file(bp), dict(screen, bank_seeds=None)))
