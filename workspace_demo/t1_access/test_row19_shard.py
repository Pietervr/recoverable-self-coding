"""The sharded route (chpc/row19_shard.py, owner 3 October 2026): a per-index worker's record equals the sequential
chain's record for the same index - identity, seed, B, draw, statistics, failure fields - and passes analyze._record_ok;
the shard records in index order ARE a sequential checkpoint (the sequential code restores all of them, computes none,
and aggregates to the same intervals); the copied source of `one` is pinned; an existing valid record is never
recomputed, an existing unacceptable one HOLDS; a past deadline or a STOP file ends the worker with exit 75 and nothing
computed; a second writer for one index is refused; a wrong declared identity, a foreign rep, a repeated or out-of-range
index HOLD; job-start admits only under a 'shard' reservation for this job number, cores and walltime, writes the task
binding in the runner's shape and refuses a different binding; job-end records the workers' exits."""
import os
os.environ.setdefault("NPROC", "1")
import json, tempfile, importlib.util, sys, time, io, contextlib, inspect, hashlib, copy
import numpy as np
import analyze as A

T1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(T1, "chpc"))
spec = importlib.util.spec_from_file_location("row19_shard", os.path.join(T1, "chpc", "row19_shard.py"))
SH = importlib.util.module_from_spec(spec); spec.loader.exec_module(SH)
from test_row19_slice import _manifest, _run, _dirs, _Patched
from test_row19_watch import R19
from row19_ledger import CampaignLedger

SCI = ("rep", "stats", "failed", "failed_reason", "chosen", "ident", "seed", "n_rep")


def _shard_manifest(seq_root, campaign, n_boot=10, cores=4):
    root = tempfile.mkdtemp()
    man = _manifest(root, campaign, n_boot=n_boot)
    man["pbs"] = dict(man["pbs"], cores=cores)
    man["shard"] = {"expect_layer_s": 0.0, "deadline_margin": 1.25}
    mp = os.path.join(root, "manifest.json"); json.dump(man, open(mp, "w"))
    return man, mp, root


def _worker(mp, rep, indices, slot=0, job="sj1", deadline=None, capture=True):
    argv = ["worker", "--manifest", mp, "--rep", str(rep), "--indices", ",".join(str(i) for i in indices), "--slot", str(slot),
            "--job-id", job, "--skip-environment-check"]
    if deadline is not None:
        argv += ["--deadline-epoch", str(deadline)]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = SH.main(argv)
    return rc, buf.getvalue()


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
        man2, mp, root = _shard_manifest(d, c)
        assert _worker(mp, 0, [7, 2, 9, 0, 4], slot=0)[0] == SH.DONE                         # any order, two workers
        assert _worker(mp, 0, [1, 3, 5, 6, 8], slot=1)[0] == SH.DONE
        t = SH.task(man2, 0)
        recs = {}
        for i in range(10):
            r = SH.read_record(SH.record_path(root, 0, i), t)
            assert r is not None and A._record_ok(r, t["ident"], t["seed"], t["n_rep"], t["idx"], t["bands"])
            assert all(r[k] == seq[i][k] for k in SCI), f"index {i}: shard record differs from the sequential one"
            recs[i] = r
        assert t["ident"] == seq[0]["ident"]
        # the shard records in index order are a sequential checkpoint: restored, none computed, same intervals
        merged = os.path.join(root, "merged.jsonl")
        open(merged, "w").write("".join(json.dumps(recs[i]) + "\n" for i in range(10)))
        rb = A.refit_bootstrap(t["ds"], t["cfg"], t["seed"], t["n_rep"], outer_folds=t["folds"], checkpoint_path=merged, strict_restore=True)
        rb_seq = A.refit_bootstrap(t["ds"], t["cfg"], t["seed"], t["n_rep"], outer_folds=t["folds"], checkpoint_path=ck, strict_restore=True)
        assert rb["n_resumed"] == 10 and rb["n_new"] == 0 and not rb["partial"] and rb["ident"] == t["ident"]
        assert json.dumps(rb["predictors"], sort_keys=True) == json.dumps(rb_seq["predictors"], sort_keys=True)
        # timing rows and status
        rows = [json.loads(l) for f in os.listdir(os.path.join(root, "timing")) for l in open(os.path.join(root, "timing", f))]
        assert sorted(r["index"] for r in rows) == list(range(10)) and all(r["rep"] == 0 for r in rows)
        st = json.load(open(os.path.join(root, "status", "jobsj1.slot0.json")))
        assert st["exit"] == SH.DONE and st["new"] == [7, 2, 9, 0, 4] and st["left"] == []


def test_resume_skips_valid_records_and_holds_on_an_unacceptable_one():
    d, c = _dirs()
    with _Patched():
        man2, mp, root = _shard_manifest(d, c)
        assert _worker(mp, 1, [0, 1, 2])[0] == SH.DONE
        before = {i: open(SH.record_path(root, 1, i)).read() for i in (0, 1, 2)}
        rc, out = _worker(mp, 1, [0, 1, 2, 3], job="sj2")
        assert rc == SH.DONE and "new [3] resumed [0, 1, 2]" in out
        assert all(open(SH.record_path(root, 1, i)).read() == before[i] for i in (0, 1, 2))      # never rewritten
        p = SH.record_path(root, 1, 1); r = json.loads(open(p).read()); r["stats"]["selection"]["ws"] += 1.0
        open(p, "w").write(json.dumps(r) + "\n")                                                # an edited statistic, stale checksum
        rc, out = _worker(mp, 1, [0, 1, 2, 3, 4], job="sj3")
        assert rc == SH.HELD and "cannot accept" in out and not os.path.exists(SH.record_path(root, 1, 4))
        open(p, "w").write("{not json")
        assert _worker(mp, 1, [1], job="sj4")[0] == SH.HELD
        # a record of ANOTHER rep placed at this rep's path is refused (identity)
        other = SH.resample_record(SH.task(man2, 2), 5)
        open(SH.record_path(root, 1, 5), "w").write(json.dumps(other) + "\n")
        assert _worker(mp, 1, [5], job="sj5")[0] == SH.HELD


def test_deadline_stop_and_second_writer():
    d, c = _dirs()
    with _Patched():
        man2, mp, root = _shard_manifest(d, c)
        rc, out = _worker(mp, 0, [0, 1], deadline=time.time() - 1.0)
        assert rc == SH.RESUME and "deadline" in out and not os.path.exists(SH.record_path(root, 0, 0))
        open(os.path.join(root, "STOP"), "w").write("stop")
        rc, out = _worker(mp, 0, [0, 1], job="sj2")
        assert rc == SH.RESUME and "stop requested" in out and not os.path.exists(SH.record_path(root, 0, 0))
        os.remove(os.path.join(root, "STOP"))
        # the deadline rule uses the longest resample seen: with a generous deadline both are computed
        assert _worker(mp, 0, [0, 1], job="sj3", deadline=time.time() + 3600)[0] == SH.DONE
        # a second writer for one index: the publish never replaces a record
        t = SH.task(man2, 0); rec = SH.resample_record(t, 0)
        try:
            SH.write_record(SH.record_path(root, 0, 0), rec); assert False
        except ValueError as e:
            assert "two writers" in str(e)


def test_identity_rep_and_index_guards():
    d, c = _dirs()
    with _Patched():
        man2, mp, root = _shard_manifest(d, c)
        assert _worker(mp, 0, [0, 0])[0] == SH.HELD                                             # repeated index
        assert _worker(mp, 0, [10])[0] == SH.HELD                                               # out of range (B = 10)
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
        man2, mp, root = _shard_manifest(d, c, cores=4)
        L = CampaignLedger(c, 1500.0)
        plan = {"job": 7, "slots": [{"slot": 0, "rep": 0, "indices": [0, 1]}, {"slot": 1, "rep": 2, "indices": [0, 1]}]}
        pp = os.path.join(root, "plan.json"); json.dump(plan, open(pp, "w"))
        def start(*extra, plan_path=pp):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = SH.main(["job-start", "--manifest", mp, "--plan", plan_path, "--job-id", "sj7", "--walltime-s", "3600",
                              "--skip-environment-check", *extra])
            return rc, buf.getvalue()
        assert start()[0] == SH.HELD                                                            # no reservation token
        tok, _ = L.reserve("shard", 7, 4, 3600.0, root)
        try:
            L.reserve("shard", 7, 4, 3600.0, root); assert False                                 # a job number is reserved once
        except RuntimeError:
            pass
        rc, out = start("--reservation-token", tok)
        assert rc == SH.DONE and "job 7 admitted: 2 slots, 4 indices" in out
        b = json.load(open(os.path.join(root, "task_0.json")))["binding"]
        assert sorted(b) == sorted(("manifest_sha", "rep", "ds_seed", "ident", "code_hash", "policy", "n_rep", "until", "ckpt", "orig", "numerical"))
        assert b["ident"] == SH.task(man2, 0)["ident"] and os.path.exists(os.path.join(root, "task_2.json"))
        # a plan with a repeated index, a foreign rep, too many slots: refused before anything is written
        for bad in ({"job": 8, "slots": [{"slot": 0, "rep": 0, "indices": [3]}, {"slot": 1, "rep": 0, "indices": [3]}]},
                    {"job": 8, "slots": [{"slot": 0, "rep": 5, "indices": [0]}]},
                    {"job": 8, "slots": [{"slot": s, "rep": 0, "indices": [s]} for s in range(5)]}):
            bp = os.path.join(root, "bad.json"); json.dump(bad, open(bp, "w"))
            assert start("--no-reservation", plan_path=bp)[0] == SH.HELD
        # a wrong walltime against the reservation
        tok9, _ = L.reserve("shard", 9, 4, 3600.0, root)
        p9 = os.path.join(root, "p9.json"); json.dump({"job": 9, "slots": [{"slot": 0, "rep": 1, "indices": [0]}]}, open(p9, "w"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = SH.main(["job-start", "--manifest", mp, "--plan", p9, "--job-id", "sj9", "--walltime-s", "7200",
                          "--skip-environment-check", "--reservation-token", tok9])
        assert rc == SH.HELD and "reservation" in buf.getvalue()
        # a different binding already in the root (another manifest): refused
        t0 = json.load(open(os.path.join(root, "task_0.json"))); t0["binding"]["ident"] = "0" * 64
        json.dump(t0, open(os.path.join(root, "task_0.json"), "w"))
        assert start("--reservation-token", tok)[0] == SH.HELD
        t0["binding"]["ident"] = b["ident"]; json.dump(t0, open(os.path.join(root, "task_0.json"), "w"))
        # the workers, then job-end: exit codes folded, the runner's end recorded in the ledger
        assert _worker(mp, 0, [0, 1], slot=0, job="sj7")[0] == SH.DONE
        assert _worker(mp, 2, [0, 1], slot=1, job="sj7", deadline=time.time() - 1)[0] == SH.RESUME
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = SH.main(["job-end", "--manifest", mp, "--plan", pp, "--job-id", "sj7", "--reservation-token", tok,
                          "--started-epoch", str(time.time() - 5), "--skip-environment-check"])
        assert rc == SH.RESUME
        e = json.load(open(L.path))["entries"][tok]
        assert e["runner_exit"] == SH.RESUME and e["state"] == "live" and e["kind"] == "shard" and e["rep"] == 7


spec3 = importlib.util.spec_from_file_location("row19_shard_submit", os.path.join(T1, "chpc", "row19_shard_submit.py"))
SUB = importlib.util.module_from_spec(spec3); spec3.loader.exec_module(SUB)
spec4 = importlib.util.spec_from_file_location("row19_shard_status", os.path.join(T1, "chpc", "row19_shard_status.py"))
ST = importlib.util.module_from_spec(spec4); spec4.loader.exec_module(ST)
_TEST_LIVE = tempfile.mkdtemp(prefix="row19_shard_test_")
ST.LIVE_DIR = os.path.join(_TEST_LIVE, "live"); ST.SLICE_LIVE = os.path.join(_TEST_LIVE, "slice_live")


def test_the_planner_assigns_only_missing_indices_disjointly():
    d, c = _dirs()
    with _Patched():
        man2, mp, root = _shard_manifest(d, c, n_boot=10, cores=4)
        man2["pbs"].update(project="P", queue="serial", nodetype="haswell_reg", mem_gb=56, walltime_h=48, deadline_reserve_s=1800)
        man2["shard"].update(per_slot=3, toolchain=root, clone=root)
        json.dump(man2, open(mp, "w"))
        assert _worker(mp, 0, [0, 1, 2])[0] == SH.DONE                                          # rep 0: 0..2 done
        L = CampaignLedger(c, 1500.0)
        tok, _ = L.reserve("shard", 1, 4, 3600.0, root)                                         # job 1 live with rep 1: 0..2 in flight
        os.makedirs(os.path.join(root, "plans"), exist_ok=True)
        json.dump({"job": 1, "slots": [{"slot": 0, "rep": 1, "indices": [0, 1, 2]}]}, open(os.path.join(root, "plans", "job_1.json"), "w"))
        done, flight, used = SUB.evidence(man2)
        assert done[0] == {0, 1, 2} and flight[1] == {0, 1, 2} and used == {1}
        jobs, left = SUB.plan_jobs(man2, 2, 3, done, flight, used)
        assert [j["job"] for j in jobs] == [2, 3] and all(len(j["slots"]) <= 4 for j in jobs)
        seen = set()
        for j in jobs:
            assert [s["slot"] for s in j["slots"]] == list(range(len(j["slots"])))
            for s in j["slots"]:
                for i in s["indices"]:
                    assert (s["rep"], i) not in seen and i not in done[s["rep"]] and i not in flight[s["rep"]]
                    seen.add((s["rep"], i))
        assert [s["rep"] for s in jobs[0]["slots"]] == [0, 1, 2, 0]                              # interleaved across the datasets
        assert jobs[0]["slots"][0]["indices"] == [3, 4, 5] and jobs[0]["slots"][1]["indices"] == [3, 4, 5] and jobs[0]["slots"][2]["indices"] == [0, 1, 2]
        assert len(seen) + left == 30 - 3 - 3
        # once job 1's runner has ended, its unfinished indices are missing again
        L.runner_start(tok, "sj1", "shard", 1, root, 4, 3600.0); L.runner_end(tok, 1.0, 75)
        done, flight, used = SUB.evidence(man2)
        assert flight[1] == set()
        text = SUB.pbs_script(man2, jobs[0], "TOKEN", 48 * 3600.0, "serial", root, root, "chpc/row19_shard_manifest.json")
        assert "#PBS -q serial" in text and "ncpus=4:mpiprocs=4:mem=56gb" in text and "walltime=48:00:00" in text
        assert text.count(" worker ") == 4 and text.count("&\n") == 4 and "\nwait\n" in text and "job-start" in text and "job-end" in text
        assert "DEADLINE=$((START + 172800 - 1800))" in text and "--indices 3,4,5" in text


def test_the_status_view_validates_every_record_and_checks_parity():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=10)
        assert _run(d, man, "--job-id", "j1", "--segment", "6") == R19.RESUME                   # the sequential chain: 0..5
        man2, mp, root = _shard_manifest(d, c, n_boot=10, cores=4)
        plan = {"job": 1, "slots": [{"slot": 0, "rep": 0, "indices": [0, 1, 2, 3, 7]}]}
        pp = os.path.join(root, "plan.json"); json.dump(plan, open(pp, "w"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            assert SH.main(["job-start", "--manifest", mp, "--plan", pp, "--job-id", "sj1", "--walltime-s", "3600",
                            "--skip-environment-check", "--no-reservation"]) == SH.DONE
        assert _worker(mp, 0, [0, 1, 2, 3, 7], job="sj1")[0] == SH.DONE
    import shutil
    def snapshot():
        shutil.rmtree(_TEST_LIVE, ignore_errors=True)
        shutil.copytree(root, os.path.join(ST.LIVE_DIR, "root")); shutil.copytree(c, os.path.join(ST.LIVE_DIR, "campaign"))
        shutil.copytree(d, os.path.join(ST.SLICE_LIVE, "row19_slice"), ignore=shutil.ignore_patterns("campaign"))
        CampaignLedger(os.path.join(ST.LIVE_DIR, "campaign"), 1500.0)                              # a ledger exists in the snapshot
    def view():
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = ST.main(["--manifest", mp, "--no-pull"])
        return rc, buf.getvalue()
    snapshot()
    rc, out = view()
    assert rc == 0 and "accepted 5/10" in out and "invalid 0" in out and "4 index(es) in both, 4 bitwise equal" in out and "LOCAL CACHE" in out
    # a valid shard record that differs from the sequential one: a parity alarm
    p = os.path.join(ST.LIVE_DIR, "root", "records", "rep0", "rec_001.json")
    r = json.load(open(p)); r["stats"]["selection"]["ws"] += 1.0; r["sha"] = A._record_sha(r); json.dump(r, open(p, "w"))
    rc, out = view()
    assert rc == 1 and "differ from the sequential chain" in out
    # an unacceptable record file, a record under another index's name, and a HELD worker: alarms
    snapshot()
    p = os.path.join(ST.LIVE_DIR, "root", "records", "rep0", "rec_002.json")
    r = json.load(open(p)); r["chosen"] = [-1]; r["sha"] = A._record_sha(r); json.dump(r, open(p, "w"))
    shutil.copyfile(os.path.join(ST.LIVE_DIR, "root", "records", "rep0", "rec_003.json"), os.path.join(ST.LIVE_DIR, "root", "records", "rep0", "rec_009.json"))
    rc, out = view()
    assert rc == 1 and "2 record file(s) rejected" in out and "accepted 4/10" in out
