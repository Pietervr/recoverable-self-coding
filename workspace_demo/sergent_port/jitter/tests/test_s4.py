"""Tests of jitter/s4.py's manifest completeness (Codex S3 review 24 Oct 2026, finding 11: an unfinished required
setting is PENDING and withholds the licence, never silently absent), of the DESIGN rev 7 §8 time-priority
deferral lever, and of the recovery battery's independence from the S4a file (25 Oct 2026: c₀ via results/s4/c0.json,
written in S4a stage 1, so a `--kind rec` host starts the moment stage 1 lands). Pure bookkeeping — no fit is run.
Run: ../../t1_access/.venv/bin/python tests/test_s4.py"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import s4  # noqa: E402


def _a(e1="CERTIFIED", t3="CERTIFIED", eps=0.01):
    return {"epsilon": eps, "c0": {"G": 3.0, "B": 3.1},
            "lambda": {"E1": dict(status=e1, lam=0.6), "T3": dict(status=t3, lam=0.8)}}


def _attempted(**over):
    att = {s: R for s, (R, _, _) in s4.MANIFEST.items()}
    att.update(over)
    return att


def _rec(**over):
    need = len(s4.SUBJECTS) * s4.R_RECOVERY
    rc = {k: need for k in s4.recovery_settings()}
    rc.update(over)
    return rc


def test_complete_manifest_is_final():
    m = s4.manifest_status(_a(), _attempted(), _rec())
    assert m["complete"] and m["pending"] == []
    assert all(v["state"] == "COMPLETE" for v in m["settings"].values())
    assert all(v["state"] == "COMPLETE" for v in m["recovery"].values())


def test_unfinished_setting_is_pending_never_absent():
    m = s4.manifest_status(_a(), _attempted(W3=37), _rec())
    assert not m["complete"] and m["settings"]["W3"]["state"] == "PENDING" and "W3" in m["pending"]
    att = _attempted()
    del att["O5"]                                              # no file of O5 at all: still PENDING, not absent
    m = s4.manifest_status(_a(), att, _rec())
    assert not m["complete"] and m["settings"]["O5"]["state"] == "PENDING" and m["settings"]["O5"]["attempted"] == 0


def test_uncertified_e1_or_t3_is_absent_by_declaration_and_does_not_block():
    m = s4.manifest_status(_a(e1="UNCERTIFIED"), _attempted(E1=0), _rec())
    assert m["complete"] and m["settings"]["E1"]["state"] == "ABSENT"
    m = s4.manifest_status(_a(t3="SEARCH FAILURE"), _attempted(T3=0), _rec())
    assert m["complete"] and m["settings"]["T3"]["state"] == "ABSENT"
    m = s4.manifest_status(_a(e1="CERTIFIED"), _attempted(E1=0), _rec())   # certified but not run: PENDING
    assert not m["complete"] and m["settings"]["E1"]["state"] == "PENDING"


def test_deferred_setting_is_declared_not_silent():
    m = s4.manifest_status(_a(), _attempted(T2=0), _rec(), deferred={"T2": "time-priority amendment"})
    assert m["complete"] and m["settings"]["T2"]["state"] == "DEFERRED"
    m = s4.manifest_status(_a(), _attempted(T2=0), _rec())
    assert not m["complete"] and m["settings"]["T2"]["state"] == "PENDING"


def test_recovery_short_is_pending():
    m = s4.manifest_status(_a(), _attempted(), _rec(**{"40|fitted": 499}))
    assert not m["complete"] and m["recovery"]["40|fitted"]["state"] == "PENDING" and "rec 40|fitted" in m["pending"]


def test_record_deferral_only_t2_t3_and_drops_their_s4b_tasks():
    old = s4.S4_DIR
    s4.S4_DIR = tempfile.mkdtemp()
    try:
        with open(os.path.join(s4.S4_DIR, "s4a.json"), "w") as f:
            json.dump(_a(), f)
        assert s4.deferred_settings() == {}
        try:
            s4.record_deferral(["W2"], "no")
            assert False, "W2 must not be deferrable"
        except ValueError:
            pass
        s4.record_deferral(["T2"], "test")
        assert s4.deferred_settings() == {"T2": "test"}
        settings = {t["setting"] for t in s4.s4b_tasks("cv")}
        assert "T2" not in settings and "T3" in settings and "E1" in settings and "W1" in settings
        s4.record_deferral(["T3"], "test 2")
        assert set(s4.deferred_settings()) == {"T2", "T3"}
        settings = {t["setting"] for t in s4.s4b_tasks("cv")}
        assert "T3" not in settings and "T1" in settings
    finally:
        s4.S4_DIR = old


def _fake_run_queue(tasks, workers, bases, c0=None, label=""):
    """Writes every task's file with deterministic fake content: EPS gives B0 − G0 = 0.03; a λ setting gives
    B3 − G3 = 0.03 λ (so ε = 0.01, λ_E1 ≈ 0.417, λ_T3 ≈ 0.667 by linear interpolation); c₀ tasks give a q0."""
    import hashlib
    for t in tasks:
        seed = int(hashlib.sha256(t["path"].encode()).hexdigest()[:8], 16)
        rng = __import__("numpy").random.default_rng(seed)
        if t["kind"] == "cv":
            s = t["setting"]
            if s == "EPS":
                sc = {"G0": -15.0, "B0": -15.0 + 0.03 + rng.normal(0, 5e-4)}
            else:
                lam = float(s.split("@")[1])
                sc = {"G3": -15.0, "B3": -15.0 + 0.03 * lam + rng.normal(0, 5e-4)}
            s4._write(t["path"], dict(scores=sc, m=t["m"], r=t["r"]))
        else:
            s4._write(t["path"], dict(q0=float(rng.chisquare(1)) * 0.5))
    return len(tasks)


def test_s4a_sharded_barriers_and_determinism():
    """Two hosts share one result prefix: each runs its hash shard of every S4a batch; a host with no waiting allowed
    raises Incomplete at a barrier whose other shard has not landed; the last host writes s4a.json; both compute
    the same ε, c₀ and λ."""
    old = (s4.S4_DIR, s4.run_queue, s4.load_bases)
    s4.S4_DIR = tempfile.mkdtemp()
    s4.run_queue = _fake_run_queue
    s4.load_bases = lambda session="active": {}
    try:
        for shard, stage in (("0/2", "stage 1"), ("1/2", "CERTE1"), ("0/2", "CERTT3")):
            try:
                s4.s4a(1, shard, 0.0)
                assert False, f"{shard} should have hit a barrier"
            except s4.Incomplete as e:
                assert stage in str(e), (shard, str(e))
            # c0.json is written the moment stage 1 is complete and c₀ computed — BEFORE any certification stage — so the
            # recovery battery (kind rec) can start while the certification hosts are still working; s4a.json not yet
            assert os.path.exists(s4.c0_path()) == (stage != "stage 1"), stage
            assert not os.path.exists(os.path.join(s4.S4_DIR, "s4a.json"))
        res = s4.s4a(1, "1/2", 0.0)                                   # every batch complete: writes s4a.json
        assert os.path.exists(os.path.join(s4.S4_DIR, "s4a.json"))
        with open(s4.c0_path()) as f:
            c0rec = json.load(f)
        assert c0rec["c0"] == res["c0"] and c0rec["c0_G"]["value"] == res["c0"]["G"] and "code_hash" in c0rec and "utc" in c0rec
        assert s4.load_c0() == res["c0"]                              # with s4a.json present, c₀ is read from it
        assert abs(res["epsilon"] - 0.01) < 1e-3
        assert res["lambda"]["E1"]["status"] == "CERTIFIED" and abs(res["lambda"]["E1"]["lam"] - 0.4167) < 0.02
        assert res["lambda"]["T3"]["status"] == "CERTIFIED" and abs(res["lambda"]["T3"]["lam"] - 0.6667) < 0.02
        res2 = s4.s4a(1, "0/2", 0.0)                                  # the other host, everything present: identical
        assert res2["epsilon"] == res["epsilon"] and res2["c0"] == res["c0"]
        assert res2["lambda"]["E1"]["lam"] == res["lambda"]["E1"]["lam"] and res2["lambda"]["T3"]["lam"] == res["lambda"]["T3"]["lam"]
        res3 = s4.s4a(1, None, 0.0)                                   # a single host never waits and finds everything
        assert res3["lambda"]["E1"]["lam"] == res["lambda"]["E1"]["lam"]
    finally:
        s4.S4_DIR, s4.run_queue, s4.load_bases = old


def test_rec_queue_needs_no_s4a_file_cv_still_does():
    """The recovery battery's task list is independent of the S4a file: `s4b-queue --kind rec` (s4b_tasks("rec")) lists all
    14 × 20 × R_RECOVERY tasks with no s4a.json present, while the decision manifest (cv, all) still needs it."""
    old = s4.S4_DIR
    s4.S4_DIR = tempfile.mkdtemp()
    try:
        tasks = s4.s4b_tasks("rec")
        assert len(tasks) == len(s4.recovery_settings()) * len(s4.SUBJECTS) * s4.R_RECOVERY == 14 * 20 * 25
        assert all(t["kind"] == "rec" for t in tasks) and len(s4.pending(tasks)) == len(tasks)
        for kind in ("cv", "all"):
            try:
                s4.s4b_tasks(kind)
                assert False, f"{kind} must still need s4a.json"
            except FileNotFoundError:
                pass
    finally:
        s4.S4_DIR = old


def test_c0_from_s4a_then_c0_json_then_shared_prefix():
    """c₀ for the recovery battery: from s4a.json when S4a has finished, else from c0.json, else — with S4_S3_RESULTS set —
    pulled from the shared prefix every C0_POLL_S seconds until it lands or the wait is up; without the prefix or after the
    wait a missing c₀ is an error, never a silent default."""
    old = (s4.S4_DIR, s4.s3_pull, s4.C0_POLL_S, os.environ.get("S4_S3_RESULTS"))
    s4.S4_DIR = tempfile.mkdtemp()
    os.environ.pop("S4_S3_RESULTS", None)
    calls = []

    def fake_pull():
        calls.append(1)
        if len(calls) == 2:                                            # the S4a hosts' c0.json lands on the second poll
            s4._write(s4.c0_path(), dict(c0={"G": 2.5, "B": 2.6}))
        return True

    try:
        try:
            s4.load_c0()
            assert False, "no c₀ anywhere and no shared prefix must be an error"
        except FileNotFoundError:
            pass
        s4._write(s4.c0_path(), dict(c0={"G": 2.0, "B": 2.1}))
        assert s4.load_c0() == {"G": 2.0, "B": 2.1}                    # c0.json alone suffices
        s4._write(os.path.join(s4.S4_DIR, "s4a.json"), _a())
        assert s4.load_c0() == {"G": 3.0, "B": 3.1}                    # s4a.json wins when present
        os.remove(os.path.join(s4.S4_DIR, "s4a.json"))
        os.remove(s4.c0_path())
        s4.s3_pull, s4.C0_POLL_S = fake_pull, 0.0
        os.environ["S4_S3_RESULTS"] = "s3://fake/prefix"
        try:
            s4.load_c0(wait_s=0.0)                                     # one pull, no c0.json yet, no time left
            assert False, "an exhausted wait must be an error"
        except FileNotFoundError:
            pass
        assert calls == [1]
        assert s4.load_c0(wait_s=60.0) == {"G": 2.5, "B": 2.6} and len(calls) == 2
    finally:
        s4.S4_DIR, s4.s3_pull, s4.C0_POLL_S = old[:3]
        if old[3] is None:
            os.environ.pop("S4_S3_RESULTS", None)
        else:
            os.environ["S4_S3_RESULTS"] = old[3]


def test_s4b_rec_runs_from_c0_json_and_cv_refuses_without_s4a():
    """`s4.py s4b --kind rec` with only c0.json present hands that c₀ to the queue; `--kind cv` still refuses without s4a.json."""
    old = (s4.S4_DIR, s4.run_queue, s4.load_bases)
    s4.S4_DIR = tempfile.mkdtemp()
    got = []

    def fake_queue(tasks, workers, bases, c0=None, label=""):
        got.append((len(tasks), c0, label))
        return len(tasks)

    s4.run_queue, s4.load_bases = fake_queue, (lambda session="active": {})
    try:
        s4._write(s4.c0_path(), dict(c0={"G": 2.0, "B": 2.1}))
        n = s4.s4b(4, "0/2", "rec")
        assert got[-1][1] == {"G": 2.0, "B": 2.1} and got[-1][0] == n and "rec" in got[-1][2]
        assert 0 < n < 14 * 20 * 25                                    # this host's hash shard of the 7,000 tasks
        try:
            s4.s4b(4, None, "cv")
            assert False, "cv must refuse without s4a.json"
        except FileNotFoundError:
            pass
        assert not os.path.exists(os.path.join(s4.S4_DIR, s4.AMENDMENT_NAME))
    finally:
        s4.S4_DIR, s4.run_queue, s4.load_bases = old


def test_run_record_written_once_and_a_mismatched_resume_refuses():
    """Codex S3 re-review finding 6: results/s4/run_config.json is written at the first start of S4 (the trial chunk in
    force, node counts, scale rule and threshold, profile starts, software versions, machine, CPU model, code hash, the
    sha256 of every generator asset) and its fingerprint is what every task record carries; a resumed S4 whose contract
    differs — another trial chunk, another generator asset, other runners — refuses with every difference named."""
    import fit as F
    import models as M
    old = (s4.S4_DIR, s4.GEN_DIR)
    s4.S4_DIR = tempfile.mkdtemp()
    gen = tempfile.mkdtemp()
    for fn in ("S1_active_G3.npz", "bases_W53_active.npz"):
        with open(os.path.join(gen, fn), "wb") as f:
            f.write(fn.encode())
    s4.GEN_DIR = gen
    old_lb = s4.load_bases
    s4.load_bases = lambda session="active": {}
    try:
        rec = s4.ensure_run_record("S4b test")
        path = os.path.join(s4.S4_DIR, F.RUN_CONFIG_NAME)
        with open(path) as f:
            disk = json.load(f)
        assert disk["fingerprint"] == rec["fingerprint"] == F.config_fingerprint(F.run_config(gen))
        assert disk["n_tau_nodes"] == 61 and disk["quad_g_rule"] == "17then33" and disk["profile_starts"] == 4
        assert disk["trial_chunk"] == M.TRIAL_CHUNK and set(disk["generators"]) == {"S1_active_G3.npz", "bases_W53_active.npz"}
        assert {"numpy", "scipy", "jax", "jaxlib"} <= set(disk["versions"]) and "machine" in disk and "cpu_model" in disk
        assert s4.ensure_run_record("S4b resume")["fingerprint"] == rec["fingerprint"]      # the same contract resumes
        assert F.run_fingerprint(gen) == rec["fingerprint"]
        # another trial chunk than the record (the hosts export 64; a resume without the export must refuse)
        old_chunk = M.TRIAL_CHUNK
        try:
            M.TRIAL_CHUNK = 64 if old_chunk != 64 else 0
            try:
                s4.ensure_run_record("S4b resume")
                assert False, "a resume under another trial chunk must refuse"
            except SystemExit as e:
                assert "refused" in str(e) and "trial_chunk" in str(e) and "JITTER_TRIAL_CHUNK" in str(e)
        finally:
            M.TRIAL_CHUNK = old_chunk
        # a changed generator asset
        with open(os.path.join(gen, "S1_active_G3.npz"), "wb") as f:
            f.write(b"changed")
        try:
            s4.ensure_run_record("S4b resume")
            assert False, "a resume with another generator asset must refuse"
        except SystemExit as e:
            assert "generator asset S1_active_G3.npz" in str(e)
        with open(os.path.join(gen, "S1_active_G3.npz"), "wb") as f:
            f.write(b"S1_active_G3.npz")
        disk["runner_hash"] = "000000000000"
        with open(path, "w") as f:
            json.dump(disk, f)
        try:
            s4.ensure_run_record("S4b resume")
            assert False, "other runners must refuse"
        except SystemExit as e:
            assert "runner_hash" in str(e)
    finally:
        s4.S4_DIR, s4.GEN_DIR = old
        s4.load_bases = old_lb


def test_s5_refuses_without_or_against_the_s4_record():
    """S5 fits only under the S4 contract (Codex finding 6: S4 and S5 on the same host type and pins): it refuses when
    results/s4/run_config.json is missing and when this process's fingerprint differs from it (here: another trial chunk);
    with the matching record it writes results/s5/run_config.json and proceeds."""
    import fit as F
    import models as M
    import s5
    old = (s4.S4_DIR, s4.GEN_DIR, s5.S5_DIR, s4.load_bases)
    s4.S4_DIR, s5.S5_DIR = tempfile.mkdtemp(), tempfile.mkdtemp()
    gen = tempfile.mkdtemp()
    with open(os.path.join(gen, "S1_active_G3.npz"), "wb") as f:
        f.write(b"x")
    s4.GEN_DIR = gen
    s4.load_bases = lambda session="active": {}
    try:
        try:
            s5.ensure_run_record("S5 cv")
            assert False, "S5 must refuse without the S4 record"
        except SystemExit as e:
            assert "missing" in str(e)
        s4.ensure_run_record("S4b")
        old_chunk = M.TRIAL_CHUNK
        try:
            M.TRIAL_CHUNK = 64 if old_chunk != 64 else 0
            try:
                s5.ensure_run_record("S5 full")
                assert False, "S5 must refuse under another trial chunk than S4's"
            except SystemExit as e:
                assert "S4 run record" in str(e) and "trial_chunk" in str(e)
            assert not os.path.exists(os.path.join(s5.S5_DIR, F.RUN_CONFIG_NAME))
        finally:
            M.TRIAL_CHUNK = old_chunk
        rec = s5.ensure_run_record("S5 cv")
        assert rec["s4_fingerprint"] == rec["fingerprint"] and os.path.exists(os.path.join(s5.S5_DIR, F.RUN_CONFIG_NAME))
    finally:
        s4.S4_DIR, s4.GEN_DIR, s5.S5_DIR, s4.load_bases = old


if __name__ == "__main__":
    import inspect
    import traceback
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and inspect.isfunction(fn):
            try:
                fn()
                print("ok  ", name)
            except Exception:  # noqa
                fails += 1
                print("FAIL", name)
                traceback.print_exc(limit=3)
    print("FAILED" if fails else "ALL OK", fails)
    sys.exit(1 if fails else 0)
