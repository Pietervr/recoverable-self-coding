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
PENDING; the pilot is qualified only with observed, equal parity for every dataset.
Revision 3 (Codex RSC 13a2fea): the later gate PARSES the qualification and the watch receipt and verifies them against
the manifest file's hash, the root, the campaign, the pins, the task identities and the pilot's PBS id / token / plan
hash; a non-production, foreign, malformed, non-finite or future-dated document is refused; the reviewer's verdict is a
required hash-bound record, never overwritten, bounded to a highest job number; the 2,700 s ceiling cannot be raised.
The view reconciles every worker status with its plan slot EXACTLY (assigned list, new / resumed / left partition, exit
against left, record and timing provenance by job and slot) and reports a deadline exit slot by slot."""
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
        json.dump({"time": time.time(), "fresh": True, "alarms": []}, open(os.path.join(gate, "watch_receipt.json"), "w"))
        # revision 3: the mere existence of a qualification and a recent zero-alarm receipt admits NOTHING
        assert "manifest's path" in SUB.gate_problems(man2, {1}, False, 8, 2700)
        assert "cannot be read" in SUB.gate_problems(man2, {1}, False, 8, 2700, manifest_path=mp)   # no bindings in this root
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


def _gate_fixture():
    """A finished pilot (job 1) over three datasets with sequential records for parity, viewed and qualified by the status
    view; its qualification and a watch receipt placed in the root's gate AS IF from production (the view under test
    switches marks them non-production; the fixture sets the two flags, nothing else)."""
    d, c = _dirs()
    man = _manifest(d, c, n_boot=10)
    for rep in (0, 1, 2):
        assert _run(d, man, "--job-id", f"j{rep}", "--segment", "2", rep=rep) == R19.RESUME
    man2, mp, root = _shard_manifest(c, n_boot=10, cores=4, mem_stop_gib=64.0)
    plan = {"job": 1, "slots": [{"slot": 0, "rep": 0, "indices": [0, 1, 7]}, {"slot": 1, "rep": 1, "indices": [0, 1]}, {"slot": 2, "rep": 2, "indices": [0, 1]}]}
    tok = _campaign_job(c, root, mp, plan, "sj1")
    pbs = {"sj1": {"state": "F", "exit": 0, "mem_kb": 2 * 2 ** 20}}
    _snapshot(d, c, root)
    rc, out = _view(mp, pbs, "--qualify", "1")
    assert rc == 0 and "QUALIFIED: job 1 on NON-PRODUCTION evidence" in out, out
    q = json.load(open(os.path.join(ST.RECEIPTS, "qualified_job1.json")))
    assert q["production"] is False and q["receipt"]["production"] is False and q["schema"] == ST.QUAL_SCHEMA
    return dict(d=d, c=c, man=man2, mp=mp, root=root, tok=tok, pbs=pbs, q=q)


def _install(fx, q=None, watch=None, age=0.0):
    """Write the qualification and a watch receipt into the root's gate as production documents."""
    gate = os.path.join(fx["root"], "gate"); os.makedirs(gate, exist_ok=True)
    q = copy.deepcopy(fx["q"] if q is None else q)
    if q.get("production") is False and "receipt" in q and q is not None and q.get("_keep") is None:
        q["production"] = True; q["receipt"]["production"] = True; q["receipt"]["fresh"] = True
    q.pop("_keep", None)
    json.dump(q, open(os.path.join(gate, "qualified_job1.json"), "w"))
    w = copy.deepcopy(q["receipt"]) if watch is None else copy.deepcopy(watch)
    if watch is None:
        w["time"] = time.time() - age
    json.dump(w, open(os.path.join(gate, "watch_receipt.json"), "w"))
    return os.path.join(gate, "qualified_job1.json"), os.path.join(gate, "watch_receipt.json")


def _gate(fx, planned=(2, 3), max_age=2700, used=(1,)):
    return SUB.gate_problems(fx["man"], set(used), False, len(planned), max_age, manifest_path=fx["mp"], planned=list(planned))


def _adopt(fx, max_job=9, name="reviews/pilot_review_record.md", text="the reviewer's verdict on the pilot evidence: yes\n"):
    full = os.path.join(fx["root"], "workspace_demo", "t1_access", name)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if not os.path.exists(full):
        open(full, "w").write(text)
    return SUB.adopt_review(fx["man"], fx["mp"], name, max_job)


def test_the_later_gate_is_bound_to_this_pilot_and_needs_the_adopted_review():
    with _Patched():
        fx = _gate_fixture()
        root, mp, man2 = fx["root"], fx["mp"], fx["man"]
        qp, wp = _install(fx)
        # a verified qualification and a fresh bound receipt are still NOT authority: the reviewer's verdict comes first
        assert "no adopted review" in _gate(fx)
        assert _adopt(fx, max_job=1).startswith("REFUSED") and "REFUSED" in SUB.adopt_review(man2, mp, "../outside.md", 9)
        assert "not in the clone" in SUB.adopt_review(man2, mp, "reviews/absent.md", 9)
        out = _adopt(fx, max_job=9)
        assert out.startswith("adopted"), out
        assert _gate(fx) == "" and _gate(fx, planned=range(2, 10)) == ""
        assert "exceed the highest job number 9" in _gate(fx, planned=(9, 10))
        assert "never overwritten" in _adopt(fx, max_job=20)                                      # the adopted review is not replaced
        rv = SUB.review_path(root); raw_rv = open(rv).read()
        # the watch receipt: age (the ceiling cannot be raised, only lowered), future, non-production, alarms, foreign jobs
        _install(fx, age=2701); assert "limit 2700 s" in _gate(fx, max_age=10 ** 6)
        _install(fx, age=700); assert _gate(fx) == "" and "limit 600 s" in _gate(fx, max_age=600)
        _install(fx, age=-300); assert "future" in _gate(fx)
        w = copy.deepcopy(fx["q"]["receipt"]); w.update(production=True, fresh=True, time=time.time())
        for mut, want in ((dict(production=False), "not fresh production evidence"), (dict(fresh=False), "not fresh production evidence"),
                          (dict(alarms=["x"]), "1 alarm"), (dict(schema="old"), "is not a row19-shard-watch-3"), (dict(time=None), "not a finite number")):
            _install(fx, watch=dict(w, **mut)); assert want in _gate(fx), (mut, _gate(fx))
        open(wp, "w").write(json.dumps(dict(w, time=1.0)).replace("1.0", "NaN")); assert "malformed" in _gate(fx)
        open(wp, "w").write("[1, 2]"); assert "malformed" in _gate(fx)
        os.remove(wp); assert "no watch receipt" in _gate(fx)
        for key, val, want in (("manifest_sha256", "0" * 64, "`manifest_sha256`"), ("root", "/elsewhere", "`root`"), ("campaign", "/other", "`campaign`"),
                               ("code", {}, "`code`"), ("identities", {"0": "x"}, "`identities`")):
            w2 = copy.deepcopy(w); w2["bound"][key] = val
            _install(fx, watch=w2); assert "watch receipt is refused" in _gate(fx) and want in _gate(fx)
        # a NEW shard job in the ledger that the receipt did not see: the receipt no longer covers the campaign
        L = CampaignLedger(fx["c"], 1500.0); tok2, _ = L.reserve("shard", 2, 4, 3600.0, root)
        _install(fx); assert "are not the ledger's" in _gate(fx, used=(1, 2), planned=(3,))
        led = json.load(open(L.path)); del led["entries"][tok2]; json.dump(led, open(L.path, "w"))
        _install(fx); assert _gate(fx) == ""
        # the qualification: malformed, old-schema, non-production, future, foreign, altered after the fact
        for text, want in (("{broken", "malformed"), ("[]", "malformed"), (json.dumps({"qualified_job": 1}), "is not a row19-shard-qualification-3")):
            open(qp, "w").write(text); assert "qualification is refused" in _gate(fx) and want in _gate(fx)
        q = copy.deepcopy(fx["q"]); q.update(production=True); q["receipt"].update(production=True, fresh=True)
        def refused(mutate, want):
            q2 = copy.deepcopy(q); mutate(q2); q2["_keep"] = True
            _install(fx, q=q2)
            got = _gate(fx)
            assert want in got, (want, got)
        refused(lambda x: x.update(production=False), "not written from production evidence")
        refused(lambda x: x.update(qualified_job=2), "not the pilot")
        refused(lambda x: x.update(qualified_job=True), "not the pilot")
        refused(lambda x: x.update(time=time.time() + 3600), "future")
        refused(lambda x: x.update(time=1.0), "predates the pilot's recorded end")
        refused(lambda x: x["bound"].update(manifest_sha256="0" * 64), "`manifest_sha256` is not this campaign's")
        refused(lambda x: x["bound"].update(root="/another/root"), "`root` is not this campaign's")
        refused(lambda x: x["bound"]["jobs"]["1"].update(job_id="another.sched01"), "binding of job 1")
        refused(lambda x: x["bound"]["jobs"]["1"].update(token="ffffffffffff"), "binding of job 1")
        refused(lambda x: x["bound"]["jobs"]["1"].update(plan_sha256="0" * 64), "binding of job 1")
        refused(lambda x: x["bound"]["identities"].update({"2": "0" * 64}), "`identities` is not this campaign's")
        refused(lambda x: x["receipt"].update(alarms=["x"]), "embedded receipt is refused")
        refused(lambda x: x["receipt"].update(fresh=False), "embedded receipt is refused")
        refused(lambda x: x["receipt"].update(time=x["time"] - 5), "not the view it was written from")
        refused(lambda x: x["receipt"]["bound"]["jobs"]["1"].update(job_id="x"), "embedded receipt is refused")
        refused(lambda x: x["receipt"]["jobs"]["1"].update(state="R"), "does not show the pilot finished")
        refused(lambda x: x["receipt"]["jobs"]["1"].update(pbs_exit=4), "does not show the pilot finished")
        refused(lambda x: x["receipt"]["jobs"]["1"].update(exits=[0, 0, 4]), "does not show the pilot finished")
        refused(lambda x: x["receipt"]["jobs"]["1"].update(ended=2), "does not show the pilot finished")
        refused(lambda x: x["receipt"]["jobs"]["1"].update(mem_kb=None), "memory observed")
        refused(lambda x: x["receipt"]["jobs"]["1"].update(mem_kb=119 * 2 ** 20), "memory observed")
        refused(lambda x: x["receipt"]["reps"]["2"].update(overlap=0, equal=0), "parity with complete evidence for rep 2")
        refused(lambda x: x["receipt"]["reps"]["1"].update(equal=1), "parity with complete evidence for rep 1")
        refused(lambda x: x["receipt"]["reps"]["0"].update(no_timing=1), "parity with complete evidence for rep 0")
        refused(lambda x: x["receipt"]["reps"].pop("2"), "parity with complete evidence for rep 2")
        # ANY change to the qualification after the review was adopted is another qualification (here: one harmless field)
        refused(lambda x: x.update(by="someone"), "another qualification")
        _install(fx); assert _gate(fx) == ""
        # the root and the ledger are the reference: a plan edited after the fact, a runner that did not end 0/75, a lost binding
        pp = os.path.join(root, "plans", "job_1.json"); raw_plan = open(pp).read()
        open(pp, "w").write(raw_plan + " "); assert "binding of job 1" in _gate(fx)
        open(pp, "w").write(raw_plan); assert _gate(fx) == ""
        led = json.load(open(L.path)); keep = copy.deepcopy(led)
        led["entries"][fx["tok"]]["runner_exit"] = 4; json.dump(led, open(L.path, "w"))
        assert "does not show the pilot's runner ended 0 or 75" in _gate(fx)
        json.dump(keep, open(L.path, "w")); assert _gate(fx) == ""
        t2 = os.path.join(root, "task_2.json"); raw_t2 = open(t2).read()
        os.remove(t2); assert "cannot be read" in _gate(fx)
        b = json.loads(raw_t2); b["binding"]["manifest_sha"] = "0" * 64; json.dump(b, open(t2, "w"))
        assert "names manifest" in _gate(fx)
        open(t2, "w").write(raw_t2); assert _gate(fx) == ""
        # a changed manifest is another campaign: its hash is in every binding and every receipt
        raw_m = open(mp).read(); open(mp, "w").write(raw_m + "\n")
        assert "names manifest" in _gate(fx)
        open(mp, "w").write(raw_m); assert _gate(fx) == ""
        # the review: its record changed in the clone, a malformed review, a future-dated one
        rec = os.path.join(root, "workspace_demo", "t1_access", "reviews", "pilot_review_record.md"); raw_rec = open(rec).read()
        open(rec, "w").write(raw_rec + "edited"); assert "not in the clone with the adopted SHA-256" in _gate(fx)
        open(rec, "w").write(raw_rec); assert _gate(fx) == ""
        v = json.loads(raw_rv)
        for mut, want in ((dict(schema="x"), "is not a row19-shard-pilot-review-1"), (dict(time=time.time() + 3600), "future"),
                          (dict(max_job_number=True), "no highest job number"), (dict(record_path="/abs/path.md"), "relative path"),
                          (dict(qualification_sha256="0" * 64), "another qualification")):
            json.dump(dict(v, **mut), open(rv, "w")); assert want in _gate(fx), (mut, _gate(fx))
        open(rv, "w").write("{"); assert "adopted review is unreadable" in _gate(fx)
        open(rv, "w").write(raw_rv); assert _gate(fx) == ""
        open(os.path.join(root, "STOP"), "w").write("stop"); assert "STOP" in _gate(fx)
        os.remove(os.path.join(root, "STOP"))
        # an adoption is refused while the qualification in the gate does not verify
        os.remove(rv); q3 = copy.deepcopy(q); q3["production"] = False; q3["_keep"] = True; _install(fx, q=q3)
        assert "does not verify" in SUB.adopt_review(man2, mp, "reviews/pilot_review_record.md", 9) and not os.path.exists(rv)
        # the pins: every pinned file must be in the clone the jobs run from, with the manifest's hash
        assert sorted(SUB.pin_problems(man2)) == sorted(man2["code"]["files"])
        base = os.path.join(root, "workspace_demo", "t1_access")
        for rel in man2["code"]["files"]:
            os.makedirs(os.path.dirname(os.path.join(base, rel)), exist_ok=True)
            shutil.copyfile(os.path.join(T1, rel), os.path.join(base, rel))
        bad = SUB.pin_problems(man2)
        assert bad == [r for r in sorted(man2["code"]["files"]) if SUB.sha_file(os.path.join(T1, r)) != man2["code"]["files"][r]]


def test_the_slot_reconciliation_is_exact_and_timing_is_traced_to_its_plan():
    with _Patched():
        fx = _gate_fixture()
        d, c, mp, root, pbs = fx["d"], fx["c"], fx["mp"], fx["root"], fx["pbs"]
        rc, out = _view(mp, pbs)
        assert rc == 0 and "slots: new 7, resumed 0, left 0 index(es)" in out, out
        q = fx["q"]; t0 = q["receipt"]["jobs"]["1"]["slot_table"][0]
        assert t0["assigned"] == [0, 1, 7] and t0["new"] == [0, 1, 7] and t0["left"] == [] and t0["exit"] == 0
        assert q["bound"]["jobs"]["1"]["job_id"] == "sj1" and q["bound"]["jobs"]["1"]["token"] == fx["tok"]
        assert q["bound"]["manifest_sha256"] == ST.sha_file(mp) and set(q["bound"]["identities"]) == {"0", "1", "2"}
        lr = os.path.join(ST.LIVE_DIR, "root")
        sp = os.path.join(lr, "status", "jobsj1.slot0.json")
        def case(mutate, *wants, reset=True):
            if reset:
                _snapshot(d, c, root)
            mutate()
            rc, out = _view(mp, pbs, "--qualify", "1")
            assert rc == 1 and "NOT QUALIFIED" in out, out
            for w in wants:
                assert w in out, (w, out)
        def status(**kw):
            s = json.load(open(sp)); s.update(kw); json.dump(s, open(sp, "w"))
        # a status announcing a SUBSET of the plan's list (the gap Codex named), and one in another order
        case(lambda: status(indices=[0, 1], new=[0, 1]), "assigned indices [0, 1] are not the plan's exact list [0, 1, 7]")
        case(lambda: status(indices=[7, 0, 1]), "are not the plan's exact list")
        case(lambda: status(left=[1]), "is not a partition of its indices")
        case(lambda: status(new=[0, 1], left=[7]), "exit 0 with indices left [7]", "index 7 is reported left but an accepted record with this job's timing exists")
        case(lambda: status(exit=75), "exit 75 with nothing left")
        case(lambda: status(new=[0, 1], resumed=[7]), "index 7 is reported resumed but its timing names this job")
        case(lambda: status(ident="0" * 64), "the status's identity is not the task binding's")
        case(lambda: status(new="all"), "`new` is not a list of integers")
        case(lambda: status(job="other"), "the status names job other")
        case(lambda: os.remove(os.path.join(lr, "records", "rep0", "rec_007.json")), "index 7 is reported new but has no accepted record")
        tp = os.path.join(lr, "timing", "rep0", "t_001.json")
        def timing(**kw):
            t = json.load(open(tp)); t.update(kw); json.dump(t, open(tp, "w"))
        case(lambda: timing(slot=2), "index 1 is reported new but its timing names job sj1 slot 2", "whose plan does not assign it")
        case(lambda: timing(job="elsewhere"), "which is not a shard job in the ledger with a plan")
        # a binding of another manifest in the root
        def other_manifest():
            p = os.path.join(lr, "task_1.json"); b = json.load(open(p)); b["binding"]["manifest_sha"] = "0" * 64; json.dump(b, open(p, "w"))
        case(other_manifest, "rep 1: the task binding")
        # the scheduler must show the job finished 0 or 75 for a qualification
        _snapshot(d, c, root)
        rc, out = _view(mp, {"sj1": {"state": "E", "mem_kb": 2 * 2 ** 20}}, "--qualify", "1")
        assert rc == 1 and "the scheduler does not show job 1 finished" in out
        # a deadline exit: reported slot by slot, consistent (no alarm), and the unfinished indices are named
        man2 = fx["man"]
        L = CampaignLedger(c, 1500.0); tok2, _ = L.reserve("shard", 2, 4, 3600.0, root)
        plan2 = {"job": 2, "slots": [{"slot": 0, "rep": 0, "indices": [2, 3]}, {"slot": 1, "rep": 1, "indices": [2, 3]}]}
        pp2 = os.path.join(root, "plans", "job_2.json"); json.dump(plan2, open(pp2, "w")); L.bind(tok2, "sj2")
        assert _job_start(mp, pp2, "sj2", "--reservation-token", tok2)[0] == SH.DONE
        assert _worker(mp, 0, [2, 3], slot=0, job="sj2", binding=True)[0] == SH.DONE
        assert _worker(mp, 1, [2, 3], slot=1, job="sj2", deadline=time.time() - 1, binding=True)[0] == SH.RESUME
        _call(["job-end", "--manifest", mp, "--plan", pp2, "--job-id", "sj2", "--reservation-token", tok2, "--started-epoch", str(time.time() - 5),
               "--skip-environment-check"])
        _snapshot(d, c, root)
        rc, out = _view(mp, dict(pbs, sj2={"state": "F", "exit": 75, "mem_kb": 2 ** 20}))
        assert rc == 0 and "exit 75 (slot, rep, left): [(1, 1, [2, 3])]" in out and "slots: new 2, resumed 0, left 2 index(es)" in out, out


def test_a_settled_kill_before_any_worker_is_dispositioned_not_alarmed():
    """8 Oct: job 5 (7523711) was killed by its node 76 s after start, before any worker status or record, and settled
    from qstat -xf. Its three alarms held every later zero-alarm receipt for good. A job that is terminal, SETTLED in the
    ledger, has no worker status, no unreadable status and no accepted record is reported DISPOSITIONED instead; an unsettled
    kill, or one with any status, keeps its alarms."""
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=10)
        for rep in (0, 1, 2):
            assert _run(d, man, "--job-id", f"j{rep}", "--segment", "2", rep=rep) == R19.RESUME
        man2, mp, root = _shard_manifest(c, n_boot=10, cores=4, mem_stop_gib=64.0)
        plan1 = {"job": 1, "slots": [{"slot": 0, "rep": 0, "indices": [0, 1, 7]}, {"slot": 1, "rep": 1, "indices": [0, 1]}, {"slot": 2, "rep": 2, "indices": [0, 1]}]}
        _campaign_job(c, root, mp, plan1, "sj1")
        plan2 = {"job": 2, "slots": [{"slot": 0, "rep": 0, "indices": [2, 3]}, {"slot": 1, "rep": 1, "indices": [2, 3]}]}
        _campaign_job(c, root, mp, plan2, "sj2", run_workers=False, end=False)
        pbs = {"sj1": {"state": "F", "exit": 0, "mem_kb": 2 * 2 ** 20}, "sj2": {"state": "F", "exit": 265, "mem_kb": 9 * 2 ** 20}}
        _snapshot(d, c, root)
        rc, out = _view(mp, pbs)                                                                  # killed, NOT settled: alarms
        assert rc == 1 and "job 2: ended (PBS F) with no terminal status" in out and "never recorded its end" in out
        assert "PBS Exit_status 265" in out and "DISPOSITIONED" not in out
        CampaignLedger(c, 1500.0).settle("sj2", 76.0, 4, note="qstat -xf Exit_status 265 after 76 s, no worker status")
        _snapshot(d, c, root)
        rc, out = _view(mp, pbs)                                                                  # settled, nothing written: a note
        assert rc == 0 and "DISPOSITIONED" in out and "never recorded its end" not in out and "Exit_status 265" in out
        assert "ALARMS" not in out and "PBS Exit_status 265" not in out
        st = os.path.join(ST.LIVE_DIR, "root", "status")                                          # any worker status: alarms again
        s = json.load(open(os.path.join(st, "jobsj1.slot0.json"))); s["job"] = "sj2"
        json.dump(s, open(os.path.join(st, "jobsj2.slot0.json"), "w"))
        rc, out = _view(mp, pbs)
        assert rc == 1 and "DISPOSITIONED" not in out and "no terminal status for slot(s) [1]" in out
