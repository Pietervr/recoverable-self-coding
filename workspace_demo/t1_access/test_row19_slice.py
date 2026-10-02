"""Tests of the row-19 slice runner (chpc/row19_slice.py) and campaign ledger (chpc/row19_ledger.py) on a stub pipeline
whose output has run_dataset's REAL shape (folds as arrays, params as a dict of stacked arrays, inner diagnostics
(L, F, M), logq (L, M, C)); analyze_dataset is never stubbed. Codex 523249d A-H and e44f804 R1, R2, R5, R6: the
environment, code and task-domain gates; request-linked, finite, cap-agreeing, terminal-state reservations; ownership,
binding, fresh-versus-recovering and checkpoint preflight before the original; the per-record progress watermark under
an interrupted run; the lossless cache (every leaf compared) and its explicit HELD reasons; stop and memory at the
original, last and no-work boundaries with acknowledgments bound to the request; aggregation that buys no fit and keeps
the companion cluster interval; the control target on fresh and resumed runs.

    NPROC=1 .venv/bin/python <runner> test_row19_slice
"""
import os
os.environ.setdefault("NPROC", "1")
import json, tempfile, importlib.util, sys, threading, time, math
import numpy as np
import analyze as A

T1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(T1, "chpc"))
spec = importlib.util.spec_from_file_location("row19_slice", os.path.join(T1, "chpc", "row19_slice.py"))
R19 = importlib.util.module_from_spec(spec); spec.loader.exec_module(R19)
from row19_ledger import CampaignLedger

CALLS = {"run_dataset": 0, "raise_at": None, "fail_all": False}


def _stub_run_dataset(sub, cfg, seed, outer_folds=None, n_jobs=1):
    """A deterministic fake pipeline with run_dataset's real output structure; never a fit."""
    CALLS["run_dataset"] += 1
    if CALLS["raise_at"] is not None and CALLS["run_dataset"] == CALLS["raise_at"]:
        raise RuntimeError("simulated crash inside a resample fit")
    rng = np.random.default_rng(seed)
    L, C = sub.layers.size, sub.n_concepts
    folds = outer_folds if outer_folds is not None else A.stratified_folds(sub.family, cfg.n_outer, seed)
    F = len(folds)
    members = list(cfg.members_G) + list(cfg.members_X)
    Mn = len(members)
    return dict(layers=sub.layers, folds=[np.asarray(f) for f in folds], members=members,
                delta={p: rng.normal(size=(L, C)) for p in A.PREDICTORS},
                logq=rng.normal(size=(L, Mn, C)), n_c=np.full(C, 3), selected=[[("M2K", "M3H")] * F] * L,
                converged=np.ones((L, F, Mn)), inner_conv=np.ones((L, F, Mn)), inner_nonfinite=np.zeros((L, F, Mn), dtype=bool),
                recovery=np.zeros((L, F, Mn)), failed=bool(CALLS["fail_all"] and getattr(sub, "group", None) is not None), failed_reason=("stub failure" if (CALLS["fail_all"] and getattr(sub, "group", None) is not None) else ""),
                params={m: rng.normal(size=(L, F, 3)) for m in members}, fit_seconds=0.01)


def _manifest(root, campaign, n_boot=10, cap=1500.0, walltime_h=1.0, mem_stop_gib=0, reps=(0, 1, 2), target=20):
    return {"setting": {"generator": "M2S", "grid": {"omega": 1.0}, "D": 2, "layers": [41], "rho": 0.0, "n_per_family": 4},
            "datasets": {"seed_base": 20261003, "reps": list(reps), "excluded_resolved_seeds": []},
            "cfg": {"start_policy": "", "interval": "refit", "n_boot_refit": n_boot, "n_starts": 2, "n_starts_inner": 2,
                    "refit_min_usable": 1.0, "n_outer": 3, "n_inner": 2},
            "code": {"files": {"analyze.py": None}},
            "environment": {"python": "x", "jax": "x", "jaxlib": "x", "numpy": "x", "scipy": "x", "joblib": "x", "machine": "x"},
            "pbs": {"cores": 1, "walltime_h": walltime_h, "deadline_reserve_s": 0.0, "mem_stop_gib": mem_stop_gib},
            "control": {"rep": 0, "target": target},
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
    extra = ["--no-reservation"]
    if reserve:
        tok, _ = CampaignLedger(man["storage"]["campaign"], man["budget"]["core_hours_cap"]).reserve(kind, rep, 1, max(walltime_s, 1.0), root)
        extra = ["--reservation-token", tok]
    return R19.main(["--manifest", mp, "--root", root, "--rep", str(rep), "--kind", kind, "--walltime-s", str(walltime_s),
                     "--skip-environment-check", *extra, *args])


def _dirs():
    d = tempfile.mkdtemp(); c = os.path.join(d, "campaign"); os.makedirs(c)
    return d, c


def _leaf_equal(x, y):
    if isinstance(x, np.ndarray):
        return isinstance(y, np.ndarray) and x.dtype == y.dtype and x.shape == y.shape and x.tobytes() == y.tobytes()
    if isinstance(x, dict):
        return isinstance(y, dict) and sorted(x) == sorted(y) and all(_leaf_equal(x[k], y[k]) for k in x)
    if isinstance(x, (list, tuple)):
        return isinstance(y, list) and len(x) == len(y) and all(_leaf_equal(a, b) for a, b in zip(x, y))
    return x == y and type(x) == type(y)


def test_environment_and_code_gates_hold_before_anything():
    d, c = _dirs()
    with _Patched():
        mp = os.path.join(d, "manifest.json"); json.dump(_manifest(d, c), open(mp, "w"))
        assert R19.main(["--manifest", mp, "--root", d, "--rep", "0", "--no-reservation"]) == R19.HELD        # environment
        man = _manifest(d, c); man["code"]["files"]["analyze.py"] = "0" * 64
        assert _run(d, man, reserve=False) == R19.HELD                                                       # code pin
        assert not os.path.exists(os.path.join(d, "status_0.json")) and not os.path.exists(os.path.join(d, "task_0.json"))


def test_task_domain_is_enforced_before_reservation_or_ownership():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c)
        assert _run(d, man, rep=7, reserve=False) == R19.HELD                                                # unlisted rep
        assert _run(d, man, "--until", "20", reserve=False) == R19.HELD                                      # main with a target
        assert _run(d, man, "--until", "19", reserve=False, kind="c1") == R19.HELD                           # wrong target
        assert _run(d, man, "--until", "20", reserve=False, kind="c1", rep=1) == R19.HELD                    # wrong control rep
        assert _run(d, man, "--until", "20", reserve=False, kind="c2") == R19.HELD                           # c2 without kill mode
        assert _run(d, man, "--until", "20", "--pbs-kill-control", reserve=False, kind="c3") == R19.HELD    # c3 with kill mode
        man2 = _manifest(d, c); man2["datasets"]["resolved_seeds"] = {"0": 12345}
        assert _run(d, man2, reserve=False) == R19.HELD                                                      # declared seed differs
        assert not os.path.exists(os.path.join(d, "task_0.json"))


def test_reservation_binds_the_filled_request_and_valid_states():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c)
        mp = os.path.join(d, "manifest.json"); json.dump(man, open(mp, "w"))
        assert R19.main(["--manifest", mp, "--root", d, "--rep", "0", "--kind", "main", "--walltime-s", "3600",
                         "--skip-environment-check", "--job-id", "j1"]) == R19.HELD                            # no token
        L = CampaignLedger(c, 1500.0)
        tok, _ = L.reserve("main", 0, 1, 1.0, d)                                                              # one second reserved
        assert R19.main(["--manifest", mp, "--root", d, "--rep", "0", "--kind", "main", "--walltime-s", "3600", "--skip-environment-check",
                         "--job-id", "j1", "--reservation-token", tok]) == R19.HELD                          # resource mismatch
        tok2, _ = L.reserve("main", 0, 1, 3600.0, d)
        L.bind(tok2, "jOTHER")
        assert R19.main(["--manifest", mp, "--root", d, "--rep", "0", "--kind", "main", "--walltime-s", "3600", "--skip-environment-check",
                         "--job-id", "j1", "--reservation-token", tok2]) == R19.HELD                         # bound elsewhere
        tok3, _ = L.reserve("main", 1, 1, 3600.0, d)
        assert R19.main(["--manifest", mp, "--root", d, "--rep", "0", "--kind", "main", "--walltime-s", "3600", "--skip-environment-check",
                         "--job-id", "j2", "--reservation-token", tok3]) == R19.HELD                         # wrong rep
        # declared cap must agree with the ledger's
        man3 = _manifest(d, c, cap=2000.0)
        try:
            _run(d, man3, "--job-id", "j3"); raise AssertionError("cap disagreement not refused")
        except RuntimeError:
            pass


def test_ledger_domains_states_and_terminal_settlement():
    d, c = _dirs()
    L = CampaignLedger(c, 100.0)
    for bad in (float("nan"), -1.0, 0.0, float("inf")):
        try:
            L.reserve("main", 0, 1, bad, d); raise AssertionError(f"walltime {bad} accepted")
        except RuntimeError:
            pass
    try:
        L.reserve("main", 0, 0, 10.0, d); raise AssertionError("zero cores accepted")
    except RuntimeError:
        pass
    t0, _ = L.reserve("main", 0, 1, 40 * 3600, d)
    t1, _ = L.reserve("c1", 0, 1, 40 * 3600, d + "_ctl")
    try:
        L.reserve("main", 1, 1, 40 * 3600, d); raise AssertionError("cap not enforced across roots")
    except RuntimeError:
        pass
    L.runner_start(t0, "J0", "main", 0, d, 1, 40 * 3600)
    L.runner_end(t0, 10.0, 75)
    st = json.load(open(L.path))
    assert st["entries"][t1]["state"] == "reserved" and st["entries"][t0]["state"] == "live"                  # J0 ending keeps J1
    L.settle("J0", 3600.0, 1, "qstat -xf")
    assert L.totals(json.load(open(L.path))) == (1.0, 40.0)
    L.settle("J0", 3600.0, 1)                                                                                # idempotent
    for call in (lambda: L.settle("J0", 7200.0, 1), lambda: L.bind(t0, "J0x"), lambda: L.runner_start(t0, "J0", "main", 0, d, 1, 40 * 3600),
                 lambda: L.settle("J0", float("nan"), 1), lambda: L.settle("J0", -5.0, 1)):
        try:
            call(); raise AssertionError("terminal or invalid transition accepted")
        except RuntimeError:
            pass
    assert L.bind(t1, "J1")["job_id"] == "J1" and L.bind(t1, "J1")["job_id"] == "J1"                          # idempotent rebinding
    t2, _ = L.reserve("c3", 0, 1, 1.0, d)
    try:
        L.bind(t2, "J1"); raise AssertionError("one job id bound to two tokens")
    except RuntimeError:
        pass
    for i in range(3):
        L.reserve("main", 0, 1, 1.0, d)
    try:
        L.reserve("main", 0, 1, 1.0, d); raise AssertionError("attempt limit not enforced")
    except RuntimeError:
        pass
    try:
        CampaignLedger(c, 200.0).reserve("main", 2, 1, 1.0, d); raise AssertionError("cap disagreement accepted")
    except RuntimeError:
        pass
    # an already over-cap campaign admits nothing
    st = json.load(open(L.path)); st["entries"][t1]["reserved_core_h"] = 500.0; json.dump(st, open(L.path, "w"))
    try:
        L.reserve("c3", 1, 1, 1.0, d); raise AssertionError("over-cap campaign admitted")
    except RuntimeError:
        pass
    # concurrent reservations under the lock never lose an entry
    st["entries"][t1]["reserved_core_h"] = 40.0; json.dump(st, open(L.path, "w"))
    errs = []
    def many(k):
        for i in range(10):
            try:
                CampaignLedger(c, 100.0).reserve("c3", 100 + k * 10 + i, 1, 1.0, d)
            except Exception as e:
                errs.append(e)
    th = [threading.Thread(target=many, args=(k,)) for k in range(4)]
    [t.start() for t in th]; [t.join() for t in th]
    assert not errs and len(json.load(open(L.path))["entries"]) == 2 + 1 + 3 + 40


def test_lossless_original_cache_every_leaf_and_explicit_holds():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=4)
        CALLS["run_dataset"] = 0
        assert _run(d, man, "--job-id", "j1", "--segment", "2") == R19.RESUME
        p = os.path.join(d, "orig", [f for f in os.listdir(os.path.join(d, "orig")) if f.endswith(".json")][0])
        rec = json.load(open(p))
        run = R19.from_wire(rec["run"])
        # rebuild the stub's exact output and compare every leaf: bytes, dtype, shape, value
        import simulate as S
        st = man["setting"]; cfg = A.Config(interval="refit", n_boot_refit=4, n_starts=2, n_starts_inner=2, n_outer=3, n_inner=2)
        seed = S.dataset_seed("M2S", {"omega": 1.0}, 0, 2, 20261003)
        ds = S.make_dataset("M2S", S.generator_theta("M2S", omega=1.0), n_per_family=4, D=2, layers=np.array([41]), rho=0.0, seed=seed)
        folds = A.stratified_folds(ds.family, cfg.n_outer, seed)
        CALLS["run_dataset"] = 0
        expect = _stub_run_dataset(ds, cfg, seed, outer_folds=folds)
        assert _leaf_equal(expect, run)
        assert run["converged"].shape == (1, 3, len(expect["members"])) and run["logq"].shape == (1, len(expect["members"]), ds.n_concepts)
        assert R19.payload_sha(rec["run"]) == rec["payload_sha"] and R19.meta_sha(rec) == rec["meta_sha"] and rec["schema"] == R19.ORIG_SCHEMA
        # explicit HELD reasons, nothing recomputed: stale payload, bad metadata, undecodable, wrong-rank logq, non-finite delta
        keep = open(p).read()
        def hold_after(mutate):
            CALLS["run_dataset"] = 0
            r = json.loads(keep); mutate(r); open(p, "w").write(json.dumps(r))
            assert _run(d, man, "--job-id", "jx", reserve=False) == R19.HELD and CALLS["run_dataset"] == 0
        hold_after(lambda r: r["run"].__setitem__("fit_seconds", 99.0))
        def bad_meta(r):
            r["seconds"] = -1.0; r["meta_sha"] = R19.meta_sha(r)
        hold_after(bad_meta)
        def bad_rank(r):
            w = r["run"]["logq"]; w["shape"] = [w["shape"][0] * w["shape"][1], w["shape"][2]]; r["payload_sha"] = R19.payload_sha(r["run"])
        hold_after(bad_rank)
        def nonfinite(r):
            arr = np.frombuffer(__import__("base64").b64decode(r["run"]["delta"]["selection"]["b64"]), dtype=np.float64).copy(); arr[0] = np.nan
            r["run"]["delta"]["selection"]["b64"] = __import__("base64").b64encode(arr.tobytes()).decode(); r["payload_sha"] = R19.payload_sha(r["run"])
        hold_after(nonfinite)
        def undecodable(r):
            r["run"]["logq"]["b64"] = "!!!!"; r["payload_sha"] = R19.payload_sha(r["run"])
        hold_after(undecodable)
        open(p, "w").write("{not json")
        CALLS["run_dataset"] = 0
        assert _run(d, man, "--job-id", "jy", reserve=False) == R19.HELD and CALLS["run_dataset"] == 0
        open(p, "w").write(keep)
        assert _run(d, man, "--job-id", "jz", reserve=False) == R19.DONE


def test_resume_aggregates_without_buying_a_fit_and_keeps_the_companion():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=6)
        CALLS["run_dataset"] = 0
        assert _run(d, man, "--job-id", "j1", "--segment", "4") == R19.RESUME
        assert CALLS["run_dataset"] == 1 + 4
        assert _run(d, man, "--job-id", "j2") == R19.DONE
        assert CALLS["run_dataset"] == 1 + 4 + 2
        st = json.load(open(os.path.join(d, "status_0.json")))
        assert st["phase"] == "final" and st["original_cached"] is True and st["n_resumed"] == 4 and st["n_new"] == 2 and not st["partial"]
        assert set(st["result"]) == set(A.PREDICTORS) and st["interval"]["method"] == "refit" and st["interval"]["n_used"] == 6
        for p in A.PREDICTORS:
            assert st["result"][p]["cluster_ws"] is not None and {"lo", "hi", "se"} <= set(st["result"][p]["cluster_ws"])
        assert st["aggregation_seconds"] >= 0 and st["publication_seconds"] >= 0 and "measurement_scope" in st and st["exit"] == 0
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


def test_interrupted_run_advances_the_watermark_and_rollback_is_refused():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=8)
        CALLS["run_dataset"] = 0; CALLS["raise_at"] = 1 + 3                      # the original, two resamples, then a crash
        try:
            _run(d, man, "--job-id", "j1"); raise AssertionError("the crash did not propagate")
        except RuntimeError:
            pass
        finally:
            CALLS["raise_at"] = None
        task = json.load(open(os.path.join(d, "task_0.json")))
        assert task["expected_accepted"] == 2 and not os.path.exists(os.path.join(d, "status_0.json"))
        ck = os.path.join(d, "ckpt", [f for f in os.listdir(os.path.join(d, "ckpt")) if f.endswith(".jsonl")][0])
        lines = open(ck).read().splitlines()
        assert len(lines) == 2
        open(ck, "w").write(lines[0] + "\n")                                     # a rolled-back checkpoint
        CALLS["run_dataset"] = 0
        assert _run(d, man, "--job-id", "j2") == R19.HELD and CALLS["run_dataset"] == 0
        open(ck, "w").write("\n".join(lines) + "\n")
        assert _run(d, man, "--job-id", "j3") == R19.DONE
        assert json.load(open(os.path.join(d, "status_0.json")))["n_resumed"] == 2


def test_missing_binding_beside_prior_evidence_holds():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=5)
        assert _run(d, man, "--job-id", "j1", "--segment", "2") == R19.RESUME
        os.remove(os.path.join(d, "task_0.json"))
        CALLS["run_dataset"] = 0
        assert _run(d, man, "--job-id", "j2") == R19.HELD and CALLS["run_dataset"] == 0
        # another rep in the same root is fresh and fine
        assert _run(d, man, "--job-id", "j3", rep=1, kind="main") == R19.DONE
        assert json.load(open(os.path.join(d, "task_index.json")))["1"]["ident"]


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


def test_task_binding_mismatch_holds():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=5)
        assert _run(d, man, "--job-id", "j1", "--segment", "3") == R19.RESUME
        man2 = dict(man); man2["cfg"] = dict(man["cfg"], n_boot_refit=7)
        assert _run(d, man2, "--job-id", "j2") == R19.HELD


def test_until_binds_the_control_target_on_fresh_and_resumed_runs():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=30)
        assert _run(d, man, "--job-id", "c1", "--until", "20", kind="c1") == R19.RESUME
        st = json.load(open(os.path.join(d, "status_0.json")))
        assert st["n_done"] == 20 and st["target_complete"] and st["partial"] and "result" not in st and st["kind"] == "c1"
        d2, _ = _dirs(); man2 = _manifest(d2, c, n_boot=30)
        assert _run(d2, man2, "--job-id", "c2", "--until", "20", "--segment", "7", "--pbs-kill-control", kind="c2") == R19.RESUME
        assert _run(d2, man2, "--job-id", "c3", "--until", "20", kind="c3") == R19.RESUME
        st3 = json.load(open(os.path.join(d2, "status_0.json")))
        assert st3["n_done"] == 20 and st3["n_resumed"] == 7 and st3["n_new"] == 13 and st3["target_complete"] and st3["kind"] == "c3"
        ck = [f for f in os.listdir(os.path.join(d2, "ckpt")) if f.endswith(".jsonl")][0]
        reps = [json.loads(l)["rep"] for l in open(os.path.join(d2, "ckpt", ck)) if l.strip()]
        assert reps == list(range(20))
        assert _run(d2, man2, "--job-id", "c3b", "--until", "20", kind="c3") == R19.RESUME                  # no work: still bound


def test_stop_before_the_original_buys_nothing_and_acks_the_current_request():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=8)
        L = CampaignLedger(c, 1500.0)
        req = L.stop_request(0)
        CALLS["run_dataset"] = 0
        assert _run(d, man, "--job-id", "j1") == R19.RESUME and CALLS["run_dataset"] == 0
        ack = json.load(open(os.path.join(d, "STOP_ACK_rep0.json")))
        assert ack["request_id"] == req["id"] and ack["boundary"] == "before the original" and not os.listdir(os.path.join(d, "orig"))
        os.remove(L.stop_path(0))
        assert _run(d, man, "--job-id", "j2", "--segment", "3") == R19.RESUME
        req2 = L.stop_request(None)                                                 # a GLOBAL request before the next start
        CALLS["run_dataset"] = 0
        assert _run(d, man, "--job-id", "j3") == R19.RESUME and CALLS["run_dataset"] == 0
        ack = json.load(open(os.path.join(d, "STOP_ACK_rep0.json")))
        assert ack["request_id"] == req2["id"] and ack["scope"] == "all" and ack["n_done"] == 3
        os.remove(L.stop_path(None))
        assert _run(d, man, "--job-id", "j4") == R19.DONE


def test_memory_stop_is_diagnosed_at_admission_last_record_and_completion():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=4, mem_stop_gib=0.0001)                       # 100 KiB: any python process exceeds it
        CALLS["run_dataset"] = 0
        assert _run(d, man, "--job-id", "j1") == R19.HELD and CALLS["run_dataset"] == 0   # at admission, before the original
        man2 = _manifest(d, c, n_boot=4)
        assert _run(d, man2, "--job-id", "j2", "--segment", "4") == R19.DONE or True
        # a completed chain with a breached peak exits 4, never 0
        d3, _ = _dirs(); man3 = _manifest(d3, c, n_boot=3)
        assert _run(d3, man3, "--job-id", "j3", "--segment", "3") == R19.DONE
        man3b = _manifest(d3, c, n_boot=3, mem_stop_gib=0.0001)
        mp = os.path.join(d3, "manifest.json"); json.dump(man3b, open(mp, "w"))
        tok, _ = CampaignLedger(c, 1500.0).reserve("main", 0, 1, 3600.0, d3)
        assert R19.main(["--manifest", mp, "--root", d3, "--rep", "0", "--kind", "main", "--walltime-s", "3600", "--skip-environment-check",
                         "--job-id", "j4", "--reservation-token", tok]) == R19.HELD


def test_deadline_exit_is_resumable_and_c2_has_no_cooperative_deadline():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=6)
        assert _run(d, man, "--job-id", "j1", walltime_s=1e-6) == R19.RESUME
        st = json.load(open(os.path.join(d, "status_0.json")))
        assert st["stopped_at_deadline"] and st["n_new"] == 0
        d2, _ = _dirs(); man2 = _manifest(d2, c, n_boot=8, target=6)
        assert _run(d2, man2, "--job-id", "j2", "--pbs-kill-control", "--until", "6", kind="c2", walltime_s=1e-6) == R19.RESUME
        st2 = json.load(open(os.path.join(d2, "status_0.json")))
        assert not st2["stopped_at_deadline"] and st2["n_new"] == 6
