"""Tests of the row-19 slice runner (chpc/row19_slice.py) and campaign ledger (chpc/row19_ledger.py) on a stub pipeline
whose output has run_dataset's REAL shape and containers (members a TUPLE as Config.members is, folds as arrays, params a
dict of stacked arrays, inner diagnostics (L, F, M), logq (L, M, C), selected one (G, X) pair per fold per layer);
analyze_dataset is never stubbed. Codex 523249d A-H, e44f804 R1-R7, 6d8a597 R2/R5/R6: the environment, code and task-
domain gates; request-linked, finite, cap-agreeing, terminal-state reservations; ownership, binding, fresh-versus-
recovering (a locked shared index under concurrent reps) and checkpoint preflight before the original; the per-record
watermark under an interrupted run; the lossless cache (every leaf compared, the real tuple accepted) and each
mutation reaching its own validator with both checksums recomputed; stop and memory at admission, the last fit,
aggregation and no-work boundaries under ONE unchanged binding with controlled peak observations; aggregation that
buys no fit and keeps the companion; the control target on fresh and resumed runs.

    NPROC=1 .venv/bin/python <runner> test_row19_slice
"""
import os
os.environ.setdefault("NPROC", "1")
import json, tempfile, importlib.util, sys, threading, time, math, io, contextlib, base64, platform
import numpy as np
import analyze as A
import jax, jaxlib, scipy, joblib

T1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(T1, "chpc"))
spec = importlib.util.spec_from_file_location("row19_slice", os.path.join(T1, "chpc", "row19_slice.py"))
R19 = importlib.util.module_from_spec(spec); spec.loader.exec_module(R19)
from row19_ledger import CampaignLedger

CALLS = {"run_dataset": 0, "raise_at": None, "fail_all": False}


def _stub_run_dataset(sub, cfg, seed, outer_folds=None, n_jobs=1):
    """A deterministic fake pipeline with run_dataset's real output structure and containers; never a fit."""
    CALLS["run_dataset"] += 1
    if CALLS["raise_at"] is not None and CALLS["run_dataset"] == CALLS["raise_at"]:
        raise RuntimeError("simulated crash inside a resample fit")
    rng = np.random.default_rng(seed)
    L, C = sub.layers.size, sub.n_concepts
    folds = outer_folds if outer_folds is not None else A.stratified_folds(sub.family, cfg.n_outer, seed)
    F = len(folds)
    members = cfg.members                                              # a TUPLE, as the real pipeline returns it
    Mn = len(members)
    is_resample = getattr(sub, "group", None) is not None
    return dict(layers=sub.layers, folds=[np.asarray(f) for f in folds], members=members,
                delta={p: rng.normal(size=(L, C)) for p in A.PREDICTORS},
                logq=rng.normal(size=(L, Mn, C)), n_c=np.bincount(sub.concept, minlength=C).astype(float), selected=[[(members[0], members[-1])] * F for _ in range(L)],
                converged=np.ones((L, F, Mn)), inner_conv=np.ones((L, F, Mn)), inner_nonfinite=np.zeros((L, F, Mn), dtype=bool),
                recovery=np.zeros((L, F, Mn)), failed=bool(CALLS["fail_all"] and is_resample),
                failed_reason=("stub failure" if (CALLS["fail_all"] and is_resample) else ""),
                params={m: rng.normal(size=(L, F, 3)) for m in members}, fit_seconds=0.01)


def _manifest(root, campaign, n_boot=10, cap=1500.0, walltime_h=1.0, mem_stop_gib=0, reps=(0, 1, 2), target=20):
    return {"setting": {"generator": "M2S", "grid": {"omega": 1.0}, "D": 2, "layers": [41], "rho": 0.0, "n_per_family": 4},
            "datasets": {"seed_base": 20261003, "reps": list(reps), "excluded_resolved_seeds": []},
            "cfg": {"start_policy": "", "interval": "refit", "n_boot_refit": n_boot, "n_starts": 2, "n_starts_inner": 2,
                    "refit_min_usable": 1.0, "n_outer": 3, "n_inner": 2},
            "code": {"files": {"analyze.py": None}},
            "environment": {"python": platform.python_version(), "jax": jax.__version__, "jaxlib": jaxlib.__version__, "numpy": np.__version__,
                            "scipy": scipy.__version__, "joblib": joblib.__version__, "machine": platform.machine()},
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


def _run(root, man, *args, reserve=True, kind="main", rep=0, walltime_s=3600.0, capture=False):
    mp = os.path.join(root, "manifest.json")
    json.dump(man, open(mp, "w"))
    extra = ["--no-reservation"]
    if reserve:
        tok, _ = CampaignLedger(man["storage"]["campaign"], man["budget"]["core_hours_cap"]).reserve(kind, rep, 1, max(walltime_s, 1.0), root)
        extra = ["--reservation-token", tok]
    argv = ["--manifest", mp, "--root", root, "--rep", str(rep), "--kind", kind, "--walltime-s", str(walltime_s), "--skip-environment-check", *extra, *args]
    if capture:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = R19.main(argv)
        return rc, buf.getvalue()
    return R19.main(argv)


def _dirs():
    d = tempfile.mkdtemp(); c = os.path.join(d, "campaign"); os.makedirs(c)
    return d, c


def _leaf_equal(x, y):
    if isinstance(x, np.ndarray):
        return isinstance(y, np.ndarray) and x.dtype == y.dtype and x.shape == y.shape and x.tobytes() == y.tobytes()
    if isinstance(x, dict):
        return isinstance(y, dict) and sorted(x) == sorted(y) and all(_leaf_equal(x[k], y[k]) for k in x)
    if isinstance(x, (list, tuple)):
        return isinstance(y, (list, tuple)) and len(x) == len(y) and all(_leaf_equal(a, b) for a, b in zip(x, y))
    return x == y and type(x) == type(y)


def _rehash(r):
    r["payload_sha"] = R19.payload_sha(r["run"]); r["meta_sha"] = R19.meta_sha(r)


def test_environment_and_code_gates_hold_before_anything():
    d, c = _dirs()
    with _Patched():
        bad_env = _manifest(d, c); bad_env["environment"]["jax"] = "0.0.0"
        mp = os.path.join(d, "manifest.json"); json.dump(bad_env, open(mp, "w"))
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
        rc, out = _run(d, man2, reserve=False, capture=True)
        assert rc == R19.HELD and "differs from the declared" in out
        assert not os.path.exists(os.path.join(d, "task_0.json")) and not os.path.exists(os.path.join(c, "budget.json"))


def test_reservation_binds_the_filled_request_and_valid_states():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c)
        mp = os.path.join(d, "manifest.json"); json.dump(man, open(mp, "w"))
        assert R19.main(["--manifest", mp, "--root", d, "--rep", "0", "--kind", "main", "--walltime-s", "3600",
                         "--skip-environment-check", "--job-id", "j1"]) == R19.HELD                            # no token
        L = CampaignLedger(c, 1500.0)
        tok, _ = L.reserve("main", 0, 1, 1.0, d)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = R19.main(["--manifest", mp, "--root", d, "--rep", "0", "--kind", "main", "--walltime-s", "3600", "--skip-environment-check",
                           "--job-id", "j1", "--reservation-token", tok])
        assert rc == R19.HELD and "core(s) x" in buf.getvalue()                                               # resource mismatch, runner branch
        tok2, _ = L.reserve("main", 0, 1, 3600.0, d)
        L.bind(tok2, "jOTHER")
        assert R19.main(["--manifest", mp, "--root", d, "--rep", "0", "--kind", "main", "--walltime-s", "3600", "--skip-environment-check",
                         "--job-id", "j1", "--reservation-token", tok2]) == R19.HELD                         # bound elsewhere
        tok3, _ = L.reserve("main", 1, 1, 3600.0, d)
        assert R19.main(["--manifest", mp, "--root", d, "--rep", "0", "--kind", "main", "--walltime-s", "3600", "--skip-environment-check",
                         "--job-id", "j2", "--reservation-token", tok3]) == R19.HELD                         # wrong rep
        man3 = _manifest(d, c, cap=2000.0); json.dump(man3, open(mp, "w"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = R19.main(["--manifest", mp, "--root", d, "--rep", "0", "--kind", "main", "--walltime-s", "3600", "--skip-environment-check",
                           "--job-id", "j3", "--reservation-token", tok3])
        assert rc == R19.HELD and "differs from the declared cap" in buf.getvalue()                           # cap disagreement, runner branch


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
    assert st["entries"][t1]["state"] == "reserved" and st["entries"][t0]["state"] == "live"
    L.settle("J0", 3600.0, 1, "qstat -xf: walltime 01:00:00, exit 75, ended normally")
    assert L.totals(json.load(open(L.path))) == (1.0, 40.0)
    L.settle("J0", 3600.0, 1, "qstat -xf: walltime 01:00:00, exit 75, ended normally")
    try:
        L.settle("J1x", 1.0, 1, ""); raise AssertionError("settlement without a note accepted")
    except RuntimeError:
        pass
    for call in (lambda: L.settle("J0", 7200.0, 1, "qstat -xf: a different accounting"), lambda: L.bind(t0, "J0x"), lambda: L.runner_start(t0, "J0", "main", 0, d, 1, 40 * 3600),
                 lambda: L.settle("J0", float("nan"), 1), lambda: L.settle("J0", -5.0, 1)):
        try:
            call(); raise AssertionError("terminal or invalid transition accepted")
        except RuntimeError:
            pass
    assert L.bind(t1, "J1")["job_id"] == "J1" and L.bind(t1, "J1")["job_id"] == "J1"
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
    st = json.load(open(L.path)); st["entries"][t1]["reserved_core_h"] = 500.0; json.dump(st, open(L.path, "w"))
    try:
        L.reserve("c3", 1, 1, 1.0, d); raise AssertionError("over-cap campaign admitted")
    except RuntimeError:
        pass
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


def test_lossless_original_cache_every_leaf_and_each_validator():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=4)
        CALLS["run_dataset"] = 0
        assert _run(d, man, "--job-id", "j1", "--segment", "2") == R19.RESUME                                # the real tuple is accepted
        p = os.path.join(d, "orig", [f for f in os.listdir(os.path.join(d, "orig")) if f.endswith(".json")][0])
        rec = json.load(open(p))
        run = R19.from_wire(rec["run"])
        import simulate as S
        cfg = A.Config(interval="refit", n_boot_refit=4, n_starts=2, n_starts_inner=2, n_outer=3, n_inner=2)
        seed = S.dataset_seed("M2S", {"omega": 1.0}, 0, 2, 20261003)
        ds = S.make_dataset("M2S", S.generator_theta("M2S", omega=1.0), n_per_family=4, D=2, layers=np.array([41]), rho=0.0, seed=seed)
        folds = A.stratified_folds(ds.family, cfg.n_outer, seed)
        CALLS["run_dataset"] = 0
        expect = _stub_run_dataset(ds, cfg, seed, outer_folds=folds)
        assert isinstance(expect["members"], tuple) and isinstance(run["members"], list) and _leaf_equal(expect, run)
        assert run["n_c"].dtype.kind == "f"                                              # the real pipeline's floating counts, kept
        assert run["converged"].shape == (1, 3, len(expect["members"])) and run["logq"].shape == (1, len(expect["members"]), ds.n_concepts)
        assert R19.payload_sha(rec["run"]) == rec["payload_sha"] and R19.meta_sha(rec) == rec["meta_sha"] and rec["schema"] == R19.ORIG_SCHEMA
        keep = open(p).read()
        def hold_after(mutate, reason):
            CALLS["run_dataset"] = 0
            r = json.loads(keep); mutate(r); open(p, "w").write(json.dumps(r))
            rc, out = _run(d, man, "--job-id", "jx", reserve=False, capture=True)
            assert rc == R19.HELD and CALLS["run_dataset"] == 0 and reason in out, (reason, out[-300:])
        hold_after(lambda r: r["run"].__setitem__("fit_seconds", 99.0), "payload checksum mismatch")
        def bad_meta(r):
            r["seconds"] = -1.0; r["meta_sha"] = R19.meta_sha(r)
        hold_after(bad_meta, "seconds is not finite and non-negative")
        def bad_rank(r):
            w = r["run"]["logq"]; w["shape"] = [w["shape"][0] * w["shape"][1], w["shape"][2]]; _rehash(r)
        hold_after(bad_rank, "logq is not an array of shape")
        def nonfinite(r):
            arr = np.frombuffer(base64.b64decode(r["run"]["delta"]["selection"]["b64"]), dtype=np.float64).copy(); arr[0] = np.nan
            r["run"]["delta"]["selection"]["b64"] = base64.b64encode(arr.tobytes()).decode(); _rehash(r)
        hold_after(nonfinite, "non-finite entries")
        def undecodable(r):
            r["run"]["logq"]["b64"] = "!!!!"; _rehash(r)
        hold_after(undecodable, "unreadable or undecodable")
        def bad_selected(r):
            r["run"]["selected"] = [None]; _rehash(r)
        hold_after(bad_selected, "selected[0] is not one (G, X) pair per fold")
        def foreign_member(r):
            r["run"]["selected"][0][0] = ["nobody", "M3H"]; _rehash(r)
        hold_after(foreign_member, "not two member names")
        def bad_nc(r):
            r["run"]["n_c"]["b64"] = base64.b64encode(np.zeros(len(expect["n_c"]), dtype=np.int64).tobytes()).decode(); _rehash(r)
        hold_after(bad_nc, "n_c is not positive integral counts")
        def half_nc(r):
            r["run"]["n_c"]["b64"] = base64.b64encode(np.full(len(expect["n_c"]), 2.5).tobytes()).decode(); _rehash(r)
        hold_after(half_nc, "n_c is not positive integral counts")
        def text_logq(r):
            w = r["run"]["logq"]; arr = np.full(tuple(w["shape"]), "x", dtype="<U1")
            w["__nd__"] = str(arr.dtype); w["b64"] = base64.b64encode(arr.tobytes()).decode(); _rehash(r)
        hold_after(text_logq, "logq is not a numeric array")
        open(p, "w").write("{not json")
        CALLS["run_dataset"] = 0
        rc, out = _run(d, man, "--job-id", "jy", reserve=False, capture=True)
        assert rc == R19.HELD and CALLS["run_dataset"] == 0 and "unreadable or undecodable" in out
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
        assert st["aggregation_seconds"] >= 0 and st["publication_seconds"] >= 0 and st["wall_seconds_main"] >= st["publication_seconds"]
        assert "excluded" in st["measurement_scope"] and st["exit"] == 0
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
        CALLS["run_dataset"] = 0; CALLS["raise_at"] = 1 + 3
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
        open(ck, "w").write(lines[0] + "\n")
        CALLS["run_dataset"] = 0
        assert _run(d, man, "--job-id", "j2") == R19.HELD and CALLS["run_dataset"] == 0
        open(ck, "w").write("\n".join(lines) + "\n")
        assert _run(d, man, "--job-id", "j3") == R19.DONE
        assert json.load(open(os.path.join(d, "status_0.json")))["n_resumed"] == 2


def test_concurrent_reps_keep_every_task_index_entry_and_a_lost_binding_still_holds():
    d, c = _dirs()
    import multiprocessing as mp_
    ctx = mp_.get_context("fork")
    with _Patched():
        man = _manifest(d, c, n_boot=3)
        mp = os.path.join(d, "manifest.json"); json.dump(man, open(mp, "w"))
        def worker(rep):
            os.environ["NPROC"] = "1"
            rc = R19.main(["--manifest", mp, "--root", d, "--rep", str(rep), "--kind", "main", "--walltime-s", "3600",
                           "--skip-environment-check", "--no-reservation", "--job-id", f"j{rep}"])
            os._exit(0 if rc == R19.DONE else 1)
        procs = [ctx.Process(target=worker, args=(r,)) for r in (0, 1, 2)]
        [p.start() for p in procs]; [p.join(180) for p in procs]
        assert all(p.exitcode == 0 for p in procs), [p.exitcode for p in procs]
        idx = json.load(open(os.path.join(d, "task_index.json")))
        assert sorted(idx) == ["0", "1", "2"]
        for f in ("task_0.json", "status_0.json", "timing_0.jsonl"):
            os.remove(os.path.join(d, f))
        man2 = _manifest(d, c, n_boot=5)                                   # identity B for rep 0; A's cache preserved
        CALLS["run_dataset"] = 0
        rc, out = _run(d, man2, "--job-id", "jB", reserve=False, capture=True)
        assert rc == R19.HELD and CALLS["run_dataset"] == 0 and "unexplained binding loss" in out


def test_missing_binding_beside_prior_evidence_holds():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=5)
        assert _run(d, man, "--job-id", "j1", "--segment", "2") == R19.RESUME
        os.remove(os.path.join(d, "task_0.json"))
        CALLS["run_dataset"] = 0
        assert _run(d, man, "--job-id", "j2") == R19.HELD and CALLS["run_dataset"] == 0
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
        assert st["n_done"] == 20 and st["target_complete"] and st["partial"] and "result" not in st and st["kind"] == "c1" and st["exit"] == 75
        d2, _ = _dirs(); man2 = _manifest(d2, c, n_boot=30)
        assert _run(d2, man2, "--job-id", "c2", "--until", "20", "--segment", "7", "--pbs-kill-control", kind="c2") == R19.RESUME
        assert _run(d2, man2, "--job-id", "c3", "--until", "20", kind="c3") == R19.RESUME
        st3 = json.load(open(os.path.join(d2, "status_0.json")))
        assert st3["n_done"] == 20 and st3["n_resumed"] == 7 and st3["n_new"] == 13 and st3["target_complete"] and st3["kind"] == "c3"
        ck = [f for f in os.listdir(os.path.join(d2, "ckpt")) if f.endswith(".jsonl")][0]
        reps = [json.loads(l)["rep"] for l in open(os.path.join(d2, "ckpt", ck)) if l.strip()]
        assert reps == list(range(20))
        assert _run(d2, man2, "--job-id", "c3b", "--until", "20", kind="c3") == R19.RESUME


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
        req2 = L.stop_request(None)
        CALLS["run_dataset"] = 0
        assert _run(d, man, "--job-id", "j3") == R19.RESUME and CALLS["run_dataset"] == 0
        ack = json.load(open(os.path.join(d, "STOP_ACK_rep0.json")))
        assert ack["request_id"] == req2["id"] and ack["scope"] == "all" and ack["n_done"] == 3
        os.remove(L.stop_path(None))
        assert _run(d, man, "--job-id", "j4") == R19.DONE


def test_stop_and_memory_at_the_last_fit_aggregation_and_no_work_under_one_binding():
    """ONE unchanged manifest (mem_stop_gib = 1, far above the process); the peak observation is controlled by patching the
    runner's sampler, and a stop request is raised from inside aggregation."""
    d, c = _dirs()
    keep_rss = R19.maxrss_bytes
    keep_agg = A.analyze_dataset
    try:
        with _Patched():
            man = _manifest(d, c, n_boot=4, mem_stop_gib=1.0)
            n = {"calls": 0}
            def rss_late():
                n["calls"] += 1
                return 2 * 2**30 if n["calls"] > 6 else 10 * 2**20
            R19.maxrss_bytes = rss_late
            rc, out = _run(d, man, "--job-id", "j1", capture=True)
            assert rc == R19.HELD and "memory stop" in out
            st = json.load(open(os.path.join(d, "status_0.json")))
            assert st["memory_breach"] and st["stop_reason"].get("memory") and st["exit"] == 4 and st["n_new"] < 4
            R19.maxrss_bytes = keep_rss
            d2, _ = _dirs(); man2 = _manifest(d2, c, n_boot=3, mem_stop_gib=1.0)
            def agg_with_breach(*args, **kw):
                R19.maxrss_bytes = lambda: 2 * 2**30
                return keep_agg(*args, **kw)
            A.analyze_dataset = agg_with_breach
            try:
                rc, out = _run(d2, man2, "--job-id", "j2", capture=True)
            finally:
                A.analyze_dataset = keep_agg; R19.maxrss_bytes = keep_rss
            st = json.load(open(os.path.join(d2, "status_0.json")))
            assert rc == R19.HELD and st["memory_breach"] and st["exit"] == 4 and "result" in st and st["phase"] == "final"
            d3, _ = _dirs(); man3 = _manifest(d3, c, n_boot=3)
            L3 = CampaignLedger(c, 1500.0)
            holder = {}
            def agg_with_stop(*args, **kw):
                holder["req"] = L3.stop_request(0)
                return keep_agg(*args, **kw)
            A.analyze_dataset = agg_with_stop
            try:
                rc = _run(d3, man3, "--job-id", "j3")
            finally:
                A.analyze_dataset = keep_agg
            ack = json.load(open(os.path.join(d3, "STOP_ACK_rep0.json")))
            st = json.load(open(os.path.join(d3, "status_0.json")))
            assert rc == R19.DONE and ack["request_id"] == holder["req"]["id"] and ack["boundary"] == "after aggregation" and st["stopped_by_request"]
            os.remove(L3.stop_path(0))
            d4, _ = _dirs(); man4 = _manifest(d4, c, n_boot=6, target=4)
            assert _run(d4, man4, "--job-id", "c1a", "--until", "4", kind="c1") == R19.RESUME
            keep_rb = A.refit_bootstrap
            def rb_with_stop(*args, **kw):                                      # the request lands after admission, on a no-work restore
                holder["req4"] = L3.stop_request(0)
                return keep_rb(*args, **kw)
            A.refit_bootstrap = rb_with_stop
            try:
                rc = _run(d4, man4, "--job-id", "c3a", "--until", "4", kind="c3")
            finally:
                A.refit_bootstrap = keep_rb
            ack = json.load(open(os.path.join(d4, "STOP_ACK_rep0.json")))
            assert rc == R19.RESUME and ack["request_id"] == holder["req4"]["id"] and ack["boundary"] == "no work bought"
            os.remove(L3.stop_path(0))
            # (e) a request landing during the publication writes is acknowledged 'at publication'
            d5, c5 = _dirs(); man5 = _manifest(d5, c5, n_boot=3); L5 = CampaignLedger(c5, 1500.0)
            keep_wa = R19.write_atomic
            def write_with_stop(path, obj):
                keep_wa(path, obj)
                if path.endswith("status_0.json") and obj.get("phase") == "final" and "req5" not in holder:
                    holder["req5"] = L5.stop_request(0)
            R19.write_atomic = write_with_stop
            try:
                rc = _run(d5, man5, "--job-id", "j5")
            finally:
                R19.write_atomic = keep_wa
            ack = json.load(open(os.path.join(d5, "STOP_ACK_rep0.json")))
            st = json.load(open(os.path.join(d5, "status_0.json")))
            assert rc == R19.DONE and ack["request_id"] == holder["req5"]["id"] and ack["boundary"] == "at publication" and st["stopped_by_request"]
            os.remove(L5.stop_path(0))
            # (f) a peak first crossing in the publication window: exit 4, never 0, result retained
            d6, c6 = _dirs(); man6 = _manifest(d6, c6, n_boot=3, mem_stop_gib=1.0)
            sp6 = os.path.join(d6, "status_0.json")
            def rss_at_publication():
                if os.path.exists(sp6) and json.load(open(sp6)).get("phase") == "final":
                    return 2 * 2**30
                return 10 * 2**20
            R19.maxrss_bytes = rss_at_publication
            try:
                rc = _run(d6, man6, "--job-id", "j6")
            finally:
                R19.maxrss_bytes = keep_rss
            st = json.load(open(sp6)); task6 = json.load(open(os.path.join(d6, "task_0.json")))
            assert rc == R19.HELD and st["memory_breach"] and st["exit"] == 4 and "result" in st and st["sampled_at"] == "terminal boundary"
            assert task6["runs"][-1]["exit"] == 4
    finally:
        R19.maxrss_bytes = keep_rss; A.analyze_dataset = keep_agg


def test_memory_stop_at_admission_buys_nothing():
    d, c = _dirs()
    with _Patched():
        man = _manifest(d, c, n_boot=4, mem_stop_gib=0.0001)
        CALLS["run_dataset"] = 0
        rc, out = _run(d, man, "--job-id", "j1", capture=True)
        assert rc == R19.HELD and CALLS["run_dataset"] == 0 and "memory at admission" in out


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
