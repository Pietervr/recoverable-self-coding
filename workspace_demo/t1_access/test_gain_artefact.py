"""ONE accepted gain artefact for the revalidation writer (spotcheck.revalidate, the REAL writer), the job
(t1_job.gain_file's contract, simulate.accepted_gain_artefact) and the monitor (spotcheck.gain_file_for) — Codex,
review 4 finding 2. The new checks and the S3 upload are mocked; nothing is fitted or sent."""
import contextlib
import io
import json
import os
import sys
import tempfile
import types
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import simulate as S
import spotcheck as C

H = "abcdefabcdef"
def entries_ok():
    return [dict(generator=n, kwargs={}, target=t, D=4, scale=0.5, gain=t, gain_check=0.95 * t, gain_check_se=0.05 * t,
                 calib_converged=True, check_converged=True, calib_ref_reproduced=True, check_ref_reproduced=True, note="", trace=[])
            for n in S.M.FAMILY_X for t in S.GAINS]
FAIL = {"on": False}
def fake_reval(entries, seed, cfg, D=4, n_jobs=1):
    out = []
    for e in entries:
        e = dict(e)
        e.update(gain_check=(0.5 if FAIL["on"] else 0.97) * e["target"], gain_check_se=0.05 * e["target"],
                 check_ref_reproduced=True, check_theta={"M2K": [2.0]}, check_runs={}, check_loglik={})
        e["note"] = S.gain_gate(e, float(e["target"]))
        out.append(e)
    return out
S.revalidate_gain_entries = fake_reval
C.boto3 = types.SimpleNamespace(Session=lambda **k: types.SimpleNamespace(client=lambda s: types.SimpleNamespace(upload_file=lambda *a, **k: None)))
quiet = lambda: contextlib.redirect_stdout(io.StringIO())

with tempfile.TemporaryDirectory() as d:
    raw, rev = os.path.join(d, "gain_calibration_D4.json"), os.path.join(d, "gain_calibration_D4.revalidated.json")
    with open(raw, "w") as fh:
        json.dump(dict(code_hash=H, D=4, seed=2026, entries=entries_ok()), fh)
    # 1. the job-written file alone: accepted by the job's contract with the hash, and by the monitor without it;
    #    another run's hash accepts nothing
    p, info = S.accepted_gain_artefact(raw, rev, 4, H)
    assert p == raw and info["accepted"] == "raw"
    assert C.gain_file_for(d, 4) == raw
    assert S.accepted_gain_artefact(raw, rev, 4, "other")[0] is None
    # 2. the REAL revalidation writer, passing: the revalidated file carries the run's hash, D, the source digest, the
    #    revalidation identity and the scales; both readers accept it; power_points and check_gain_file pass
    with quiet():
        C.revalidate("run", 4, d, "profile", seed=1, n_jobs=1)
    with open(rev) as fh:
        cal = json.load(fh)
    assert cal["code_hash"] == H and cal["D"] == 4 and cal["source_digest"] == S.file_digest(raw) and cal["revalidated_with"]
    assert "M3L@0.01" in cal["scales"] and cal["problems"] == []
    p, info = S.accepted_gain_artefact(raw, rev, 4, H)
    assert p == rev and info["accepted"] == "revalidated" and info["problems"] == []
    assert C.gain_file_for(d, 4) == rev
    assert len(S.power_points(rev)[0]) == 12
    with quiet():
        assert C.check_gain_file(rev) == []
    print("writer -> job and monitor: a passing revalidation is the accepted artefact for both OK")
    # 3. the REAL writer, FAILING revalidation: still the accepted artefact for both — and both refuse it (the job holds)
    FAIL["on"] = True
    with quiet():
        C.revalidate("run", 4, d, "profile", seed=1, n_jobs=1)
    p, info = S.accepted_gain_artefact(raw, rev, 4, H)
    assert p == rev and info["problems"], info
    try:
        S.power_points(rev); raise AssertionError("a failing revalidation was accepted for power")
    except SystemExit:
        pass
    with quiet():
        assert C.check_gain_file(rev)
    assert C.gain_file_for(d, 4) == rev
    print("writer -> job and monitor: a failing revalidation holds the job and fails the monitor alike OK")
    # 4. the job-written file changes under the revalidation: not authenticated -> the job holds, the monitor accepts nothing
    with open(raw, "w") as fh:
        json.dump(dict(code_hash=H, D=4, seed=2026, entries=entries_ok()[:11]), fh)
    try:
        S.accepted_gain_artefact(raw, rev, 4, H); raise AssertionError("mismatched source digest accepted")
    except ValueError as e:
        assert "source digest" in str(e)
    with quiet():
        assert C.gain_file_for(d, 4) is None
    # 5. wrong hash, wrong D, malformed, absent
    cal["code_hash"] = cal["source_code_hash"] = "zzz"
    with open(rev, "w") as fh:
        json.dump(cal, fh)
    try:
        S.accepted_gain_artefact(None, rev, 4, H); raise AssertionError("another run's revalidation accepted")
    except ValueError as e:
        assert "not this run" in str(e)
    cal["code_hash"] = cal["source_code_hash"] = H; cal["D"] = 8
    with open(rev, "w") as fh:
        json.dump(cal, fh)
    try:
        S.accepted_gain_artefact(None, rev, 4, H); raise AssertionError("another D accepted")
    except ValueError as e:
        assert "D=8" in str(e)
    with open(rev, "w") as fh:
        fh.write("{not json")
    try:
        S.accepted_gain_artefact(raw, rev, 4, H); raise AssertionError("malformed revalidation accepted")
    except ValueError as e:
        assert "malformed" in str(e)
    os.remove(rev); os.remove(raw)
    assert S.accepted_gain_artefact(raw, rev, 4, H)[0] is None
    print("mismatched, foreign, wrong-D, malformed and absent artefacts: held or nothing accepted OK")
