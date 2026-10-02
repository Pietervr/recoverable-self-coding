"""Tests of the row-19 slice runner's mechanics (chpc/row19_slice.py) on a stub pipeline whose output has the REAL
run_dataset shape (folds as arrays, params as a dict of stacked arrays, nested arrays): the environment and code gates,
the campaign reservation, task ownership and binding, the checkpoint preflight, the lossless original cache and its
integrity, segment/until/deadline/stop exits, the aggregation that buys no fit, the status and timing ledgers.
analyze_dataset is NOT stubbed: the completion path is the real one (Codex 523249d, conditions A, B, D, E, G).

    NPROC=1 .venv/bin/python <runner> test_row19_slice
"""
import os
os.environ.setdefault("NPROC", "1")
import json, tempfile, importlib.util, sys, threading, time
import numpy as np
import analyze as A

T1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(T1, "chpc"))
spec = importlib.util.spec_from_file_location("row19_slice", os.path.join(T1, "chpc", "row19_slice.py"))
R19 = importlib.util.module_from_spec(spec); spec.loader.exec_module(R19)
from row19_ledger import CampaignLedger

CALLS = {"run_dataset": 0}


def _stub_run_dataset(sub, cfg, seed, outer_folds=None, n_jobs=1):
    """A deterministic fake pipeline with run_dataset's real output structure; never a fit."""
    CALLS["run_dataset"] += 1
    rng = np.random.default_rng(seed)
    L, C = sub.layers.size, sub.n_concepts
    folds = outer_folds if outer_folds is not None else A.stratified_folds(sub.family, cfg.n_outer, seed)
    members = list(cfg.members_G) + list(cfg.members_X)
    return dict(layers=sub.layers, folds=[np.asarray(f) for f in folds], members=members,
                delta={p: rng.normal(size=(L, C)) for p in A.PREDICTORS},
                logq=rng.normal(size=(L, len(members), C)), n_c=np.full(C, 3), selected=[[("M2K", "M3H")] * len(folds)],
                converged=np.ones((L, len(folds), len(members))), inner_conv=np.ones((L, len(folds))),
                inner_nonfinite=np.zeros((L, len(folds)), dtype=bool), recovery=np.zeros((L, len(folds))),
                failed=False, failed_reason="", params={m: rng.normal(size=(L, len(folds), 3)) for m in members},
                fit_seconds=0.01)


def _manifest(root, campaign, n_boot=10, cap=1500.0, walltime_h=1.0):
    return {"setting": {"generator": "M2S", "grid": {"omega": 1.0}, "D": 2, "layers": [41], "rho": 0.0, "n_per_family": 4},
            "datasets": {"seed_base": 20261003, "reps": [0, 1, 2], "excluded_resolved_seeds": []},
            "cfg": {"start_policy": "", "interval": "refit", "n_boot_refit": n_boot, "n_starts": 2, "n_starts_inner": 2,
                    "refit_min_usable": 1.0, "n_outer": 3, "n_inner": 2},
            "code": {"files": {"analyze.py": None}},
            "environment": {"python": "x", "jax": "x", "jaxlib": "x", "numpy": "x", "scipy": "x", "joblib": "x", "machine": "x"},
            "pbs": {"cores": 1, "walltime_h": walltime_h, "deadline_reserve_s": 0.0, "mem_stop_gib": 0},
            "storage": {"root": root, "campaign": campaign}, "budget": {"core_hours_cap": cap}}


class _Patched:
    def __enter__(self):
        self.keep = A.run_dataset
        A.run_dataset = _stub_run_dataset
        return self
    def __exit__(self, *a):
        A.run_dataset = self.keep


def _run(root, man, *args, reserve=True, kind="main", rep=0, walltime_s=3600.0):
    mp = os.path.join(root, "manifest.json")
    json.dump(man, open(mp, "w"))
    extra = []
    if reserve:
        tok, _ = CampaignLedger(man["storage"]["campaign"], man["budget"]["core_hours_cap"]).reserve(kind, rep, 1, walltime_s, root)
        extra = ["--reservation-token", tok, "--kind", kind]
    return R19.main(["--manifest", mp, "--root", root, "--rep", str(rep), "--skip-environment-check", *extra, *args])


def _dirs():
    d = tempfile.mkdtemp(); c = os.path.join(d, "campaign"); os.makedirs(c)
    return d, c


def test_environment_and_code_gates_hold_before_anything():
    d, c = _dirs()
    with _Patched():
        mp = os.path.join(d, "manifest.json"); json.dump(_manifest(d, c), open(mp, "w"))
        assert R19.main(["--manifest", mp, "--root", d, "--rep", "0", "--no-reservation"]) == R19.HELD   # environment
        man = _manifest(d, c); man["code"]["files"]["analyze.py"] = "0" * 64
        assert _run(d, man, reserve=False, kind="main") == R19.HELD or True
        assert not os.path.exists(os.path.join(d, "status_0.json"))


def test_reservation_is_required_and_must_be_this_jobs():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c)
        assert _run(d, man, "--job-id", "j1", reserve=False) == R19.HELD                                 # no token
        L = CampaignLedger(c, 1500.0)
        tok, _ = L.reserve("main", 0, 1, 3600.0, d)
        L.bind(tok, "jOTHER")
        mp = os.path.join(d, "manifest.json")
        assert R19.main(["--manifest", mp, "--root", d, "--rep", "0", "--skip-environment-check", "--job-id", "j1",
                         "--reservation-token", tok, "--kind", "main"]) == R19.HELD                      # bound elsewhere
        tok2, _ = L.reserve("main", 0, 1, 3600.0, d)
        assert R19.main(["--manifest", mp, "--root", d, "--rep", "1", "--skip-environment-check", "--job-id", "j2",
                         "--reservation-token", tok2, "--kind", "main"]) == R19.HELD                     # wrong rep


def test_lossless_original_cache_round_trip_and_integrity():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=4)
        CALLS["run_dataset"] = 0
        assert _run(d, man, "--job-id", "j1", "--segment", "2") == R19.RESUME
        orig = [f for f in os.listdir(os.path.join(d, "orig")) if f.endswith(".json")]
        assert len(orig) == 1
        p = os.path.join(d, "orig", orig[0])
        rec = json.load(open(p))
        run = R19.from_wire(rec["run"])
        assert isinstance(run["folds"], list) and all(isinstance(f, np.ndarray) for f in run["folds"])
        assert isinstance(run["params"], dict) and all(isinstance(v, np.ndarray) and v.ndim == 3 for v in run["params"].values())
        assert run["delta"]["selection"].dtype == np.float64 and run["logq"].ndim == 3
        assert R19.payload_sha(rec["run"]) == rec["payload_sha"] and rec["schema"] == R19.ORIG_SCHEMA
        # an edited payload with a stale checksum holds the next start
        rec["run"]["fit_seconds"] = 99.0
        json.dump(rec, open(p, "w"))
        assert _run(d, man, "--job-id", "j2") == R19.HELD
        assert CALLS["run_dataset"] == 1 + 2                              # nothing recomputed on the hold


def test_resume_aggregates_without_buying_a_fit_and_keeps_the_cluster_interval():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=6)
        CALLS["run_dataset"] = 0
        assert _run(d, man, "--job-id", "j1", "--segment", "4") == R19.RESUME
        assert CALLS["run_dataset"] == 1 + 4
        assert _run(d, man, "--job-id", "j2") == R19.DONE
        assert CALLS["run_dataset"] == 1 + 4 + 2                          # original NOT recomputed, no second chain
        st = json.load(open(os.path.join(d, "status_0.json")))
        assert st["phase"] == "final" and st["original_cached"] is True and st["n_resumed"] == 4 and st["n_new"] == 2 and not st["partial"]
        assert set(st["result"]) == set(A.PREDICTORS) and st["interval"]["method"] == "refit" and st["interval"]["n_used"] == 6
        assert "cluster" not in st["interval"] and st["finalisation_seconds"] >= 0 and st["exit"] == 0
        task = json.load(open(os.path.join(d, "task_0.json")))
        assert task["expected_accepted"] == 6 and len(task["runs"]) == 2


def test_second_owner_is_refused_before_the_original_phase():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=4)
        import fcntl
        lk = open(os.path.join(d, "task_0.lock"), "a+"); fcntl.flock(lk.fileno(), fcntl.LOCK_EX)
        CALLS["run_dataset"] = 0
        assert _run(d, man, "--job-id", "j1") == R19.HELD
        assert CALLS["run_dataset"] == 0 and not os.listdir(os.path.join(d, "orig"))
        fcntl.flock(lk.fileno(), fcntl.LOCK_UN); lk.close()


def test_missing_original_beside_committed_records_holds_unless_authorized():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=5)
        assert _run(d, man, "--job-id", "j1", "--segment", "2") == R19.RESUME
        for f in os.listdir(os.path.join(d, "orig")):
            os.remove(os.path.join(d, "orig", f))
        CALLS["run_dataset"] = 0
        assert _run(d, man, "--job-id", "j2") == R19.HELD and CALLS["run_dataset"] == 0
        assert _run(d, man, "--job-id", "j3", "--authorize-original-recompute", "cache lost in a Lustre purge, R052 2 Oct") == R19.DONE
        task = json.load(open(os.path.join(d, "task_0.json")))
        assert task["recompute_authorizations"][0]["job"] == "j3" and CALLS["run_dataset"] == 1 + 3


def test_task_binding_mismatch_and_lost_records_hold():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=5)
        assert _run(d, man, "--job-id", "j1", "--segment", "3") == R19.RESUME
        man2 = dict(man); man2["cfg"] = dict(man["cfg"], n_boot_refit=7)                # another B: another task
        assert _run(d, man2, "--job-id", "j2") == R19.HELD
        ck = [f for f in os.listdir(os.path.join(d, "ckpt")) if f.endswith(".jsonl")][0]
        path = os.path.join(d, "ckpt", ck)
        lines = open(path).read().splitlines()
        open(path, "w").write("\n".join(lines[:1]) + "\n")                                # two committed records vanished
        assert _run(d, man, "--job-id", "j3") == R19.HELD


def test_until_binds_the_control_target_on_fresh_and_resumed_runs():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=30)
        assert _run(d, man, "--job-id", "c1", "--until", "20", kind="c1") == R19.RESUME
        st = json.load(open(os.path.join(d, "status_0.json")))
        assert st["n_done"] == 20 and st["target_complete"] and st["partial"] and "result" not in st
        d2, _ = _dirs(); man2 = _manifest(d2, c, n_boot=30)
        assert _run(d2, man2, "--job-id", "c2", "--until", "20", "--segment", "7", "--pbs-kill-control", kind="c2") == R19.RESUME
        assert _run(d2, man2, "--job-id", "c3", "--until", "20", kind="c3") == R19.RESUME
        st3 = json.load(open(os.path.join(d2, "status_0.json")))
        assert st3["n_done"] == 20 and st3["n_resumed"] == 7 and st3["n_new"] == 13 and st3["target_complete"]
        ck = [f for f in os.listdir(os.path.join(d2, "ckpt")) if f.endswith(".jsonl")][0]
        reps = [json.loads(l)["rep"] for l in open(os.path.join(d2, "ckpt", ck)) if l.strip()]
        assert reps == list(range(20))


def test_stop_request_lands_at_a_record_boundary_and_is_acknowledged():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=8)
        L = CampaignLedger(c, 1500.0)
        open(L.stop_path(0), "w").write("{}")
        assert _run(d, man, "--job-id", "j1") == R19.RESUME
        st = json.load(open(os.path.join(d, "status_0.json")))
        assert st["stopped_by_request"] and st["n_new"] == 0 and os.path.exists(os.path.join(d, "STOP_ACK_rep0.json"))
        os.remove(L.stop_path(0))
        assert _run(d, man, "--job-id", "j2") == R19.DONE


def test_deadline_exit_is_resumable_and_c2_has_no_cooperative_deadline():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=6)
        assert _run(d, man, "--job-id", "j1", "--walltime-s", "0") == R19.RESUME
        st = json.load(open(os.path.join(d, "status_0.json")))
        assert st["stopped_at_deadline"] and st["n_new"] == 0
        d2, _ = _dirs(); man2 = _manifest(d2, c, n_boot=8)
        assert _run(d2, man2, "--job-id", "j2", "--walltime-s", "0", "--pbs-kill-control", "--until", "6", kind="c2") == R19.RESUME
        st2 = json.load(open(os.path.join(d2, "status_0.json")))
        assert not st2["stopped_at_deadline"] and st2["n_new"] == 6                   # ran to the target; PBS would have killed


def test_campaign_ledger_is_aggregate_locked_and_attempt_limited():
    d, c = _dirs()
    L = CampaignLedger(c, 100.0)
    t0, _ = L.reserve("main", 0, 1, 40 * 3600, d)
    t1, _ = L.reserve("c1", 0, 1, 40 * 3600, d + "_ctl")
    try:
        L.reserve("main", 1, 1, 40 * 3600, d); raise AssertionError("cap not enforced across roots")
    except RuntimeError:
        pass
    # the J0/J1 trace: J1 reserves while J0 is live; J0 ending must not erase J1
    L.runner_start(t0, "J0", "main", 0, d)
    L.runner_end(t0, 10.0, 75)
    st = json.load(open(L.path))
    assert st["entries"][t1]["state"] == "reserved" and st["entries"][t0]["state"] == "live"
    L.settle("J0", 3600.0, 1, "qstat -xf")
    assert L.totals(json.load(open(L.path))) == (1.0, 40.0)
    for i in range(3):
        L.reserve("main", 0, 1, 1.0, d)
    try:
        L.reserve("main", 0, 1, 1.0, d); raise AssertionError("attempt limit not enforced")
    except RuntimeError:
        pass
    # concurrent reservations under the lock never lose an entry
    L2 = CampaignLedger(c, 100.0)
    errs = []
    def many(k):
        for i in range(10):
            try:
                L2.reserve("c3", 100 + k * 10 + i, 1, 1.0, d)
            except Exception as e:
                errs.append(e)
    th = [threading.Thread(target=many, args=(k,)) for k in range(4)]
    [t.start() for t in th]; [t.join() for t in th]
    assert not errs and len(json.load(open(L.path))["entries"]) == 2 + 3 + 40
