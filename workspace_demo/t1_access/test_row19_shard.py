"""The sharded route (chpc/row19_shard.py, row19_shard_submit.py, row19_shard_status.py; owner 3 October 2026; Codex's
conditions RSC 395e49d). A per-index worker's record equals the sequential chain's record for the same index and passes
analyze._record_ok; the shard records in index order ARE a sequential checkpoint; the copied source of `one` is pinned.
Worker: a valid existing record OF THIS INDEX is never recomputed; an edited, non-JSON, foreign-task or WRONG-INDEX file
HOLDS; a fit exception still leaves a HELD status; the memory stop holds before a resample, after a published record
(evidence kept) and at the terminal check of a fully resumed worker; every record has its timing file, published first;
a past deadline or a STOP file ends with exit 75 and nothing computed; no worker runs without the task binding that
job-start publishes once (never rewritten; lost beside evidence -> HELD). Planner: DONE is a VALIDATED record, a damaged
record or a live job without its plan HOLDS, and the gate admits only the pilot first, then only a qualified pilot plus
a fresh zero-alarm receipt, never past a STOP. Status view: fails closed on runner exit 4, a terminal job with missing
or undeclared worker exits, a failed admission, a job that started without bindings, a vanished job, incomplete timing,
a memory breach, a rejected record, a parity difference (float bits) and absent sequential evidence; zero overlap is
PENDING; the pilot is qualified only with observed, equal parity for every dataset."""
import os
os.environ.setdefault("NPROC", "1")
import json, tempfile, importlib.util, sys, time, io, contextlib, inspect, hashlib, copy, shutil
import numpy as np
import analyze as A

T1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(T1, "chpc"))
def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(T1, "chpc", name + ".py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
SH, SUB, ST = _load("row19_shard"), _load("row19_shard_submit"), _load("row19_shard_status")
from test_row19_slice import _manifest, _run, _dirs, _Patched
from test_row19_watch import R19
from row19_ledger import CampaignLedger

SCI = ("rep", "stats", "failed", "failed_reason", "chosen", "ident", "seed", "n_rep")
_TEST_LIVE = tempfile.mkdtemp(prefix="row19_shard_test_")
ST.LIVE_DIR = os.path.join(_TEST_LIVE, "live"); ST.RECEIPTS = os.path.join(_TEST_LIVE, "receipts")


def _shard_manifest(campaign, n_boot=10, cores=4, mem_stop_gib=0):
    root = tempfile.mkdtemp()
    man = _manifest(root, campaign, n_boot=n_boot, mem_stop_gib=mem_stop_gib)
    man["pbs"] = dict(man["pbs"], cores=cores, project="P", queue="serial", nodetype="haswell_reg", mem_gb=120, walltime_h=48, deadline_reserve_s=1800)
    man["shard"] = {"expect_layer_s": 0.0, "deadline_margin": 1.25, "per_slot": 3, "toolchain": root, "clone": root,
                    "sequential_roots": ["/nonexistent/row19_slice"], "sequential_campaign": "/nonexistent/campaign"}
    mp = os.path.join(root, "manifest.json"); json.dump(man, open(mp, "w"))
    return man, mp, root


def _call(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        rc = SH.main(argv)
    return rc, buf.getvalue()


def _worker(mp, rep, indices, slot=0, job="sj1", deadline=None, binding=False):
    argv = ["worker", "--manifest", mp, "--rep", str(rep), "--indices", ",".join(str(i) for i in indices), "--slot", str(slot),
            "--job-id", job, "--skip-environment-check"] + ([] if binding else ["--no-binding-check"])
    if deadline is not None:
        argv += ["--deadline-epoch", str(deadline)]
    return _call(argv)


def _job_start(mp, plan_path, job, *extra, walltime="3600"):
    return _call(["job-start", "--manifest", mp, "--plan", plan_path, "--job-id", job, "--walltime-s", walltime, "--skip-environment-check", *extra])


def test_the_copied_source_of_one_is_the_pinned_one():
    src = inspect.getsource(A.refit_bootstrap)
    one = src[src.index("    def one(rep):"):src.index("    ident = dataset_identity")]
    assert hashlib.sha256(one.encode()).hexdigest() == SH.ONE_SOURCE_SHA256, "analyze.refit_bootstrap.one changed: re-verify resample_record"


def test_shard_records_are_the_sequential_records_and_form_a_sequential_checkpoint():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=10)
        assert _run(d, man, "--job-id", "j1") in (R19.DONE, R19.RESUME)                       # the sequential chain, all 10
        ck = os.path.join(d, "ckpt", [f for f in os.listdir(os.path.join(d, "ckpt")) if f.endswith(".jsonl")][0])
        seq = {r["rep"]: r for r in (json.loads(l) for l in open(ck).read().splitlines() if l.strip())}
        assert sorted(seq) == list(range(10))
        man2, mp, root = _shard_manifest(c)
        assert _worker(mp, 0, [7, 2, 9, 0, 4], slot=0)[0] == SH.DONE                         # any order, two workers
        assert _worker(mp, 0, [1, 3, 5, 6, 8], slot=1)[0] == SH.DONE
        t = SH.task(man2, 0)
        recs = {}
        for i in range(10):
            r = SH.read_record(SH.record_path(root, 0, i), t, i)
            assert r is not None and A._record_ok(r, t["ident"], t["seed"], t["n_rep"], t["idx"], t["bands"])
            assert all(r[k] == seq[i][k] for k in SCI) and ST.payload(r) == ST.payload(seq[i]), f"index {i}: shard record differs"
            tm = json.load(open(SH.timing_path(root, 0, i)))                                  # its timing, published before it
            assert tm["rep"] == 0 and tm["index"] == i and tm["ident"] == t["ident"] and tm["wall_s"] >= 0 and tm["maxrss"] > 0
            assert os.path.getmtime(SH.timing_path(root, 0, i)) <= os.path.getmtime(SH.record_path(root, 0, i)) + 1e-3
            recs[i] = r
        merged = os.path.join(root, "merged.jsonl")
        open(merged, "w").write("".join(json.dumps(recs[i]) + "\n" for i in range(10)))
        rb = A.refit_bootstrap(t["ds"], t["cfg"], t["seed"], t["n_rep"], outer_folds=t["folds"], checkpoint_path=merged, strict_restore=True)
        rb_seq = A.refit_bootstrap(t["ds"], t["cfg"], t["seed"], t["n_rep"], outer_folds=t["folds"], checkpoint_path=ck, strict_restore=True)
        assert rb["n_resumed"] == 10 and rb["n_new"] == 0 and not rb["partial"] and rb["ident"] == t["ident"]
        assert json.dumps(rb["predictors"], sort_keys=True) == json.dumps(rb_seq["predictors"], sort_keys=True)
        st = json.load(open(os.path.join(root, "status", "jobsj1.slot0.json")))
        assert st["exit"] == SH.DONE and st["new"] == [7, 2, 9, 0, 4] and st["left"] == []
    assert ST.payload({"stats": {"a": 0.0}}) != ST.payload({"stats": {"a": -0.0}})            # float bits, not ==


def test_resume_skips_valid_records_and_holds_on_any_other_file():
    d, c = _dirs()
    with _Patched():
        man2, mp, root = _shard_manifest(c)
        assert _worker(mp, 1, [0, 1, 2])[0] == SH.DONE
        before = {i: open(SH.record_path(root, 1, i)).read() for i in (0, 1, 2)}
        rc, out = _worker(mp, 1, [0, 1, 2, 3], job="sj2")
        assert rc == SH.DONE and "new [3] resumed [0, 1, 2]" in out
        assert all(open(SH.record_path(root, 1, i)).read() == before[i] for i in (0, 1, 2))      # never rewritten
        # a valid record of ANOTHER INDEX of the same task under this index's name: HOLD, nothing new
        shutil.copyfile(SH.record_path(root, 1, 0), SH.record_path(root, 1, 5))
        rc, out = _worker(mp, 1, [5, 6], job="sj2b")
        assert rc == SH.HELD and "not of index 5" in out and not os.path.exists(SH.record_path(root, 1, 6))
        os.remove(SH.record_path(root, 1, 5))
        try:
            SH.write_record(SH.record_path(root, 1, 5), json.loads(before[0]), 5); assert False    # nor published under a wrong index
        except ValueError as e:
            assert "refusing to publish" in str(e)
        p = SH.record_path(root, 1, 1); r = json.loads(open(p).read()); r["stats"]["selection"]["ws"] += 1.0
        open(p, "w").write(json.dumps(r) + "\n")                                                # an edited statistic, stale checksum
        rc, out = _worker(mp, 1, [0, 1, 2, 3, 4], job="sj3")
        assert rc == SH.HELD and "cannot accept" in out and not os.path.exists(SH.record_path(root, 1, 4))
        assert json.load(open(os.path.join(root, "status", "jobsj3.slot0.json")))["exit"] == SH.HELD
        open(p, "w").write("{not json")
        assert _worker(mp, 1, [1], job="sj4")[0] == SH.HELD
        other = SH.resample_record(SH.task(man2, 2), 7)                                         # another rep's record at this rep's path
        open(SH.record_path(root, 1, 7), "w").write(json.dumps(other) + "\n")
        assert _worker(mp, 1, [7], job="sj5")[0] == SH.HELD


def test_deadline_stop_second_writer_and_a_fit_exception():
    d, c = _dirs()
    with _Patched():
        man2, mp, root = _shard_manifest(c)
        rc, out = _worker(mp, 0, [0, 1], deadline=time.time() - 1.0)
        assert rc == SH.RESUME and "deadline" in out and not os.path.exists(SH.record_path(root, 0, 0))
        open(os.path.join(root, "STOP"), "w").write("stop")
        rc, out = _worker(mp, 0, [0, 1], job="sj2")
        assert rc == SH.RESUME and "stop requested" in out and not os.path.exists(SH.record_path(root, 0, 0))
        os.remove(os.path.join(root, "STOP"))
        assert _worker(mp, 0, [0, 1], job="sj3", deadline=time.time() + 3600)[0] == SH.DONE
        t = SH.task(man2, 0); rec = SH.resample_record(t, 0)
        try:
            SH.write_record(SH.record_path(root, 0, 0), rec, 0); assert False                     # the publish never replaces a record
        except ValueError as e:
            assert "already exists" in str(e)
        # a fit that raises: the worker still writes its status, HELD, and the job folds it
        keep = A.run_dataset
        def boom(*a_, **k_):
            raise RuntimeError("simulated failure inside a resample fit")
        A.run_dataset = boom
        try:
            rc, out = _worker(mp, 0, [2, 3], job="sj4")
        finally:
            A.run_dataset = keep
        st = json.load(open(os.path.join(root, "status", "jobsj4.slot0.json")))
        assert rc == SH.HELD and st["exit"] == SH.HELD and "exception: RuntimeError" in st["reason"] and st["left"] == [2, 3]


def test_the_memory_stop_before_after_and_at_the_terminal_check():
    d, c = _dirs()
    with _Patched():
        man2, mp, root = _shard_manifest(c, mem_stop_gib=1.0)
        keep = SH.maxrss_bytes
        try:
            SH.maxrss_bytes = lambda: 2 * 2 ** 30                                               # above the stop from the start
            rc, out = _worker(mp, 0, [0])
            assert rc == SH.HELD and "before index 0" in out and not os.path.exists(SH.record_path(root, 0, 0))
            calls = {"n": 0}
            def rising():                                                                      # crosses the stop during the LAST fit
                calls["n"] += 1
                return 2 ** 29 if calls["n"] <= 2 else 2 * 2 ** 30
            SH.maxrss_bytes = rising
            rc, out = _worker(mp, 0, [0], job="sj2")
            assert rc == SH.HELD and "after index 0 (its record is published and kept)" in out
            assert os.path.exists(SH.record_path(root, 0, 0)) and os.path.exists(SH.timing_path(root, 0, 0))   # the evidence is kept
            SH.maxrss_bytes = lambda: 2 * 2 ** 30                                               # a fully RESUMED worker is checked too
            rc, out = _worker(mp, 0, [0], job="sj3")
            assert rc == SH.HELD and "terminal check" in out
            assert json.load(open(os.path.join(root, "status", "jobsj3.slot0.json")))["resumed"] == [0]
        finally:
            SH.maxrss_bytes = keep


def test_identity_rep_index_and_binding_guards():
    d, c = _dirs()
    with _Patched():
        man2, mp, root = _shard_manifest(c)
        assert _worker(mp, 0, [0, 0])[0] == SH.HELD                                             # repeated index
        assert _worker(mp, 0, [10])[0] == SH.HELD                                               # out of range (B = 10)
        assert _worker(mp, 5, [0])[0] == SH.HELD                                                # not a declared dataset
        rc, out = _worker(mp, 0, [0], binding=True)
        assert rc == SH.HELD and "no task binding" in out                                       # a worker never runs without the binding
        t = SH.task(man2, 0)
        man3 = copy.deepcopy(man2); man3["shard"]["identities"] = {"0": "0" * 64}
        json.dump(man3, open(mp, "w"))
        rc, out = _worker(mp, 0, [0])
        assert rc == SH.HELD and "is not the manifest's" in out
        man3["shard"]["identities"] = {"0": t["ident"]}; json.dump(man3, open(mp, "w"))
        assert _worker(mp, 0, [0])[0] == SH.DONE
        man3["datasets"]["resolved_seeds"] = {"0": 1}; json.dump(man3, open(mp, "w"))
        assert _worker(mp, 0, [1])[0] == SH.HELD                                                # the resolved seed is not the declared one
        man3["datasets"].pop("resolved_seeds"); man3["code"]["files"]["analyze.py"] = "0" * 64; json.dump(man3, open(mp, "w"))
        rc, out = _worker(mp, 0, [1])
        assert rc == SH.HELD and "code hashes" in out                                           # the pins are checked by every worker


def test_job_start_and_end_under_a_shard_reservation():
    d, c = _dirs()
    with _Patched():
        man2, mp, root = _shard_manifest(c, cores=4)
        L = CampaignLedger(c, 1500.0)
        plan = {"job": 7, "slots": [{"slot": 0, "rep": 0, "indices": [0, 1]}, {"slot": 1, "rep": 2, "indices": [0, 1]}]}
        pp = os.path.join(root, "plan.json"); json.dump(plan, open(pp, "w"))
        assert _job_start(mp, pp, "sj7")[0] == SH.HELD                                          # no reservation token
        tok, _ = L.reserve("shard", 7, 4, 3600.0, root)
        try:
            L.reserve("shard", 7, 4, 3600.0, root); assert False                                 # a job number is reserved once
        except RuntimeError:
            pass
        rc, out = _job_start(mp, pp, "sj7", "--reservation-token", tok)
        assert rc == SH.DONE and "job 7 admitted: 2 slots, 4 indices" in out and "code pins verified" in out
        raw0 = open(os.path.join(root, "task_0.json")).read()
        b = json.loads(raw0)["binding"]
        assert sorted(b) == sorted(("manifest_sha", "rep", "ds_seed", "ident", "code_hash", "policy", "n_rep", "until", "ckpt", "orig", "numerical"))
        assert b["ident"] == SH.task(man2, 0)["ident"] and os.path.exists(os.path.join(root, "task_2.json"))
        assert _job_start(mp, pp, "sj7", "--reservation-token", tok)[0] == SH.DONE                # again: equal, and never rewritten
        assert open(os.path.join(root, "task_0.json")).read() == raw0
        for bad in ({"job": 8, "slots": [{"slot": 0, "rep": 0, "indices": [3]}, {"slot": 1, "rep": 0, "indices": [3]}]},
                    {"job": 8, "slots": [{"slot": 0, "rep": 5, "indices": [0]}]},
                    {"job": 8, "slots": [{"slot": s, "rep": 0, "indices": [s]} for s in range(5)]}):
            bp = os.path.join(root, "bad.json"); json.dump(bad, open(bp, "w"))
            assert _job_start(mp, bp, "sj8", "--no-reservation")[0] == SH.HELD
        tok9, _ = L.reserve("shard", 9, 4, 3600.0, root)
        p9 = os.path.join(root, "p9.json"); json.dump({"job": 9, "slots": [{"slot": 0, "rep": 1, "indices": [0]}]}, open(p9, "w"))
        rc, out = _job_start(mp, p9, "sj9", "--reservation-token", tok9, walltime="7200")
        assert rc == SH.HELD and "reservation" in out                                             # a wrong walltime against the reservation
        t0 = json.loads(raw0); t0["binding"]["ident"] = "0" * 64
        json.dump(t0, open(os.path.join(root, "task_0.json"), "w"))
        assert _job_start(mp, pp, "sj7", "--reservation-token", tok)[0] == SH.HELD                # a different binding in the root
        open(os.path.join(root, "task_0.json"), "w").write(raw0)
        # the workers under the binding, then job-end: exit codes folded, the runner's end recorded in the ledger
        assert _worker(mp, 0, [0, 1], slot=0, job="sj7", binding=True)[0] == SH.DONE
        assert _worker(mp, 2, [0, 1], slot=1, job="sj7", deadline=time.time() - 1, binding=True)[0] == SH.RESUME
        rc, out = _call(["job-end", "--manifest", mp, "--plan", pp, "--job-id", "sj7", "--reservation-token", tok,
                         "--started-epoch", str(time.time() - 5), "--skip-environment-check"])
        assert rc == SH.RESUME
        e = json.load(open(L.path))["entries"][tok]
        assert e["runner_exit"] == SH.RESUME and e["state"] == "live" and e["kind"] == "shard" and e["rep"] == 7
        # a binding lost beside existing evidence HOLDS; it is never recreated as new provenance
        os.remove(os.path.join(root, "task_0.json"))
        rc, out = _job_start(mp, pp, "sj7", "--reservation-token", tok)
        assert rc == SH.HELD and "without a task binding" in out
        # a job-end with a missing worker status folds to HELD
        tok10, _ = L.reserve("shard", 10, 4, 3600.0, root)
        p10 = os.path.join(root, "p10.json"); json.dump({"job": 10, "slots": [{"slot": 0, "rep": 1, "indices": [0]}]}, open(p10, "w"))
        rc, out = _call(["job-end", "--manifest", mp, "--plan", p10, "--job-id", "sj10", "--reservation-token", tok10,
                         "--started-epoch", str(time.time()), "--skip-environment-check"])
        assert rc == SH.HELD


def test_the_planner_validates_evidence_and_the_gate_is_enforced():
    d, c = _dirs()
    with _Patched():
        man2, mp, root = _shard_manifest(c, n_boot=10, cores=4)
        assert _worker(mp, 0, [0, 1, 2])[0] == SH.DONE                                          # rep 0: 0..2 done
        L = CampaignLedger(c, 1500.0)
        tok, _ = L.reserve("shard", 1, 4, 3600.0, root)                                         # job 1 live with rep 1: 0..2 in flight
        os.makedirs(os.path.join(root, "plans"), exist_ok=True)
        pj1 = os.path.join(root, "plans", "job_1.json")
        json.dump({"job": 1, "slots": [{"slot": 0, "rep": 1, "indices": [0, 1, 2]}]}, open(pj1, "w"))
        done, flight, used, problems = SUB.evidence(man2)
        assert done[0] == {0, 1, 2} and flight[1] == {0, 1, 2} and used == {1} and problems == []
        jobs, left = SUB.plan_jobs(man2, 2, 3, done, flight, used)
        assert [j["job"] for j in jobs] == [2, 3] and all(len(j["slots"]) <= 4 for j in jobs)
        seen = set()
        for j in jobs:
            for s in j["slots"]:
                for i in s["indices"]:
                    assert (s["rep"], i) not in seen and i not in done[s["rep"]] and i not in flight[s["rep"]]
                    seen.add((s["rep"], i))
        assert [s["rep"] for s in jobs[0]["slots"]] == [0, 1, 2, 0] and jobs[0]["slots"][0]["indices"] == [3, 4, 5]
        assert len(seen) + left == 30 - 3 - 3
        # damaged or misplaced evidence HOLDS the planner; so does a live job without its plan
        shutil.copyfile(SH.record_path(root, 0, 0), SH.record_path(root, 0, 8))                  # index 0's record under index 8's name
        assert any("not of index 8" in p for p in SUB.evidence(man2)[3])
        os.remove(SH.record_path(root, 0, 8))
        open(SH.record_path(root, 0, 9), "w").write("{broken")
        assert any("not JSON" in p for p in SUB.evidence(man2)[3])
        os.remove(SH.record_path(root, 0, 9))
        os.rename(pj1, pj1 + ".gone")
        assert any("plan" in p and "missing" in p for p in SUB.evidence(man2)[3])
        os.rename(pj1 + ".gone", pj1)
        assert SUB.evidence(man2)[3] == []
        # the gate: the pilot is the first job only; later submissions need the qualification and a fresh zero-alarm receipt
        assert SUB.gate_problems(man2, set(), True, 1, 2700) == ""
        assert "exactly one" in SUB.gate_problems(man2, set(), True, 2, 2700)
        assert "FIRST" in SUB.gate_problems(man2, {1}, True, 1, 2700)
        assert "pilot" in SUB.gate_problems(man2, set(), False, 8, 2700)
        assert "not qualified" in SUB.gate_problems(man2, {1}, False, 8, 2700)
        gate = os.path.join(root, "gate"); os.makedirs(gate, exist_ok=True)
        json.dump({"qualified_job": 1}, open(os.path.join(gate, "qualified_job1.json"), "w"))
        assert "no watch receipt" in SUB.gate_problems(man2, {1}, False, 8, 2700)
        rcp = os.path.join(gate, "watch_receipt.json")
        json.dump({"time": time.time(), "fresh": True, "alarms": ["x"]}, open(rcp, "w"))
        assert "zero-alarm" in SUB.gate_problems(man2, {1}, False, 8, 2700)
        json.dump({"time": time.time(), "fresh": False, "alarms": []}, open(rcp, "w"))
        assert "zero-alarm" in SUB.gate_problems(man2, {1}, False, 8, 2700)
        json.dump({"time": time.time() - 3000, "fresh": True, "alarms": []}, open(rcp, "w"))
        assert "old" in SUB.gate_problems(man2, {1}, False, 8, 2700)
        json.dump({"time": time.time(), "fresh": True, "alarms": []}, open(rcp, "w"))
        assert SUB.gate_problems(man2, {1}, False, 8, 2700) == ""
        open(os.path.join(root, "STOP"), "w").write("stop")
        assert "STOP" in SUB.gate_problems(man2, {1}, False, 8, 2700) and "STOP" in SUB.gate_problems(man2, set(), True, 1, 2700)
        os.remove(os.path.join(root, "STOP"))
        # once job 1's runner has ended, its unfinished indices are missing again
        L.runner_start(tok, "sj1", "shard", 1, root, 4, 3600.0); L.runner_end(tok, 1.0, 75)
        assert SUB.evidence(man2)[1][1] == set()
        text = SUB.pbs_script(man2, jobs[0], "TOKEN", 48 * 3600.0, "serial", root, root, "chpc/row19_shard_manifest.json")
        assert "#PBS -q serial" in text and "ncpus=4:mpiprocs=4:mem=120gb" in text and "walltime=48:00:00" in text
        assert text.count(" worker ") == 4 and text.count("&\n") == 4 and "\nwait\n" in text
        assert text.count("job-end") == 2 and "ADMISSION FAILED" in text                         # job-end also runs after a failed admission
        assert "DEADLINE=$((START + 172800 - 1800))" in text and "--indices 3,4,5" in text


def _campaign_job(c, root, mp, plan, job_id, run_workers=True, end=True):
    """A reserved, admitted shard job with its plan in the root, its workers run and its end recorded."""
    L = CampaignLedger(c, 1500.0)
    tok, _ = L.reserve("shard", int(plan["job"]), 4, 3600.0, root)
    os.makedirs(os.path.join(root, "plans"), exist_ok=True)
    pp = os.path.join(root, "plans", f"job_{plan['job']}.json"); json.dump(plan, open(pp, "w"))
    L.bind(tok, job_id)
    assert _job_start(mp, pp, job_id, "--reservation-token", tok)[0] == SH.DONE
    if run_workers:
        for s in plan["slots"]:
            assert _worker(mp, s["rep"], s["indices"], slot=s["slot"], job=job_id, binding=True)[0] == SH.DONE
    if end:
        _call(["job-end", "--manifest", mp, "--plan", pp, "--job-id", job_id, "--reservation-token", tok,
               "--started-epoch", str(time.time() - 5), "--skip-environment-check"])
    return tok


def _snapshot(seq_dir, c, root):
    shutil.rmtree(_TEST_LIVE, ignore_errors=True)
    shutil.copytree(root, os.path.join(ST.LIVE_DIR, "root")); shutil.copytree(c, os.path.join(ST.LIVE_DIR, "campaign"))
    shutil.copytree(c, os.path.join(ST.LIVE_DIR, "seq_campaign"))
    shutil.copytree(seq_dir, os.path.join(ST.LIVE_DIR, "seq", "row19_slice"), ignore=shutil.ignore_patterns("campaign"))
    os.makedirs(os.path.join(ST.LIVE_DIR, "jobs"), exist_ok=True)


def _view(mp, pbs, *extra):
    pf = os.path.join(_TEST_LIVE, "pbs.json"); os.makedirs(_TEST_LIVE, exist_ok=True); json.dump(pbs, open(pf, "w"))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = ST.main(["--manifest", mp, "--no-pull", "--no-upload", "--pbs-file", pf, *extra])
    return rc, buf.getvalue()


def test_the_status_view_fails_closed_and_qualifies_only_on_observed_parity():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=10)
        for rep in (0, 1):                                                                       # sequential records: reps 0 and 1 only
            assert _run(d, man, "--job-id", f"j{rep}", "--segment", "3", rep=rep) == R19.RESUME
        man2, mp, root = _shard_manifest(c, n_boot=10, cores=4, mem_stop_gib=64.0)
        plan = {"job": 1, "slots": [{"slot": 0, "rep": 0, "indices": [0, 1, 7]}, {"slot": 1, "rep": 1, "indices": [0, 1]}, {"slot": 2, "rep": 2, "indices": [0, 1]}]}
        _campaign_job(c, root, mp, plan, "sj1")
        ok = {"sj1": {"state": "F", "exit": 0, "mem_kb": 2 * 2 ** 20}}
        _snapshot(d, c, root)
        rc, out = _view(mp, ok)
        assert rc == 0 and "accepted 3/10" in out and "2 index(es) in both, 2 bit-equal" in out and "PENDING" in out and "LOCAL CACHE" in out
        assert "workers ended 3/3" in out and "records without a valid timing file: 0" in out and "PBS peak memory 2.0 GiB" in out
        # the pilot is NOT qualified while parity is pending for rep 2 (no sequential record yet)
        rc, out = _view(mp, ok, "--qualify", "1")
        assert rc == 1 and "NOT QUALIFIED" in out and "rep 2: production parity is not observed" in out
        with _Patched():
            assert _run(d, man, "--job-id", "j2", "--segment", "2", rep=2) == R19.RESUME
        _snapshot(d, c, root)
        rc, out = _view(mp, ok, "--qualify", "1")
        assert rc == 0 and "QUALIFIED: job 1" in out and os.path.exists(os.path.join(ST.RECEIPTS, "qualified_job1.json"))
        q = json.load(open(os.path.join(ST.RECEIPTS, "qualified_job1.json")))
        assert q["qualified_job"] == 1 and q["receipt"]["alarms"] == [] and q["receipt"]["reps"]["2"]["overlap"] == 2
        # a parity difference (a valid, re-hashed shard record with another statistic)
        p = os.path.join(ST.LIVE_DIR, "root", "records", "rep0", "rec_001.json")
        r = json.load(open(p)); r["stats"]["selection"]["ws"] += 1.0; r["sha"] = A._record_sha(r); json.dump(r, open(p, "w"))
        rc, out = _view(mp, ok, "--qualify", "1")
        assert rc == 1 and "differ from the sequential chain" in out and "NOT QUALIFIED" in out
        # rejected and misnamed records; a missing timing file; a worker peak above the stop
        _snapshot(d, c, root)
        lr = os.path.join(ST.LIVE_DIR, "root")
        p = os.path.join(lr, "records", "rep0", "rec_007.json"); r = json.load(open(p)); r["chosen"] = [-1]; r["sha"] = A._record_sha(r); json.dump(r, open(p, "w"))
        shutil.copyfile(os.path.join(lr, "records", "rep1", "rec_000.json"), os.path.join(lr, "records", "rep1", "rec_009.json"))
        os.remove(os.path.join(lr, "timing", "rep2", "t_001.json"))
        t = json.load(open(os.path.join(lr, "timing", "rep2", "t_000.json"))); t["maxrss"] = 100 * 2 ** 30
        json.dump(t, open(os.path.join(lr, "timing", "rep2", "t_000.json"), "w"))
        rc, out = _view(mp, ok)
        assert rc == 1 and "rep 0: 1 record file(s) rejected" in out and "rep 1: 1 record file(s) rejected" in out
        assert "INCOMPLETE MEASUREMENT - 1 accepted record(s)" in out and "exceeds the 64.00 GiB per-worker stop" in out
        # job reconciliation: runner exit 4; a terminal job with a missing status; a vanished job; a failed admission; high memory
        _snapshot(d, c, root)
        led = os.path.join(ST.LIVE_DIR, "campaign", "budget.json"); L = json.load(open(led))
        for e in L["entries"].values():
            if e.get("job_id") == "sj1":
                e["runner_exit"] = 4
        json.dump(L, open(led, "w"))
        os.remove(os.path.join(ST.LIVE_DIR, "root", "status", "jobsj1.slot2.json"))
        open(os.path.join(ST.LIVE_DIR, "jobs", "row19_shard_1.out"), "w").write("exit 4 job sj1 end ... (ADMISSION FAILED)\n")
        rc, out = _view(mp, {"sj1": {"state": "F", "exit": 4, "mem_kb": 119 * 2 ** 20}})
        assert rc == 1 and "job 1: runner exit 4" in out and "no terminal status for slot(s) [2]" in out and "FAILED ADMISSION" in out
        assert "PBS Exit_status 4" in out and "above 90% of the 120 GiB request" in out
        _snapshot(d, c, root)
        L = json.load(open(led))
        for e in L["entries"].values():
            if e.get("job_id") == "sj1":
                e.pop("runner_ended", None); e["runner_exit"] = None
        json.dump(L, open(led, "w"))
        rc, out = _view(mp, {"sj1": {"state": "gone"}})
        assert rc == 1 and "the runner never recorded its end" in out
        rc, out = _view(mp, {"sj1": {"state": "R"}})                                             # still running: missing end is normal
        assert "never recorded its end" not in out
        # a job that started without its bindings; an undeclared slot status; absent sequential evidence
        _snapshot(d, c, root)
        os.remove(os.path.join(ST.LIVE_DIR, "root", "task_2.json"))
        s = json.load(open(os.path.join(ST.LIVE_DIR, "root", "status", "jobsj1.slot0.json"))); s["slot"] = 9
        json.dump(s, open(os.path.join(ST.LIVE_DIR, "root", "status", "jobsj1.slot9.json"), "w"))
        shutil.rmtree(os.path.join(ST.LIVE_DIR, "seq_campaign"))
        rc, out = _view(mp, ok)
        assert rc == 1 and "rep 2: no task binding although" in out and "slot 9, which the plan does not have" in out
        assert "sequential slice's ledger is absent" in out
