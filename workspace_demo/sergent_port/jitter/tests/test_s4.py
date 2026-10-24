"""Tests of jitter/s4.py's manifest completeness (Codex S3 review 24 Oct 2026, finding 11: an unfinished required
setting is PENDING and withholds the licence, never silently absent) and of the DESIGN rev 7 §8 time-priority
deferral lever. Pure bookkeeping — no fit is run.
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
        res = s4.s4a(1, "1/2", 0.0)                                   # every batch complete: writes s4a.json
        assert os.path.exists(os.path.join(s4.S4_DIR, "s4a.json"))
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
