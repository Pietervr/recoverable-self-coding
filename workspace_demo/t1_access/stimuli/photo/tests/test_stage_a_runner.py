"""Stage A runner tests on a fake instrument - no model is imported, loaded or run (R052 brief 2026-10-02).

    .venv-image/bin/python -m unittest discover -s stimuli/photo/tests -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fake_stage_a as F  # noqa: E402
import enforce  # noqa: E402
import stage_a  # noqa: E402
import stage_a_guard as G  # noqa: E402

PY = sys.executable
PLAN = json.loads(stage_a.PLAN.read_text())
N_INST = sum(a["phase"] == "instrumented" for a in PLAN["attempts"])


def sub(out: Path, faults: dict, kw: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([PY, str(HERE / "fake_stage_a.py"), str(out), json.dumps(faults), json.dumps(kw or {})],
                          capture_output=True, text=True, timeout=600)


def state(out: Path) -> dict:
    return json.loads((out / "stage_a_state.json").read_text())


class StageA(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "photo_stage_a"

    def tearDown(self):
        self.tmp.cleanup()

    def test_full_pass_and_report(self):
        s1 = stage_a.run_instrumented(F.make_ctx(self.out))
        self.assertEqual(s1["instrumented"], 158)
        s2 = stage_a.run_native(F.make_ctx(self.out))
        self.assertEqual(s2["native"], 20)
        c = state(self.out)["counters"]["row20"]
        self.assertEqual((c["started"], c["completed"], c["failed"], c["passes"]), (194, 193, 1, 194))
        self.assertGreater(c["seconds"], stage_a.ENGINEERING_CARRY["seconds"])
        r = stage_a.run_report(F.make_ctx(self.out))
        self.assertEqual(r["outcome"], "PASS")
        self.assertTrue(r["report_files_complete"])
        rep = json.loads((self.out / "report" / "stage_a_report.json").read_text())
        self.assertEqual(len(rep["bitwise_equal_to_plain"]), 120)
        self.assertEqual(rep["attempts_by_kind"]["diagnostic_mechanics"]["committed"], 16)
        self.assertIn("report", rep["phase_seconds"])         # the report's own cost is inside A
        self.assertIsNotNone(rep["stage_b"])

    def test_lock_contention(self):
        lock = G.TaskLock(self.out)
        try:
            with self.assertRaises(SystemExit) as e:
                stage_a.run_instrumented(F.make_ctx(self.out))
            self.assertIn("another Stage A process", str(e.exception))
        finally:
            lock.release()
        self.assertFalse((self.out / "TERMINAL.json").exists())

    def test_bitwise_failure_is_terminal_in_both_phases(self):
        with self.assertRaises(stage_a.StopCheck):
            stage_a.run_instrumented(F.make_ctx(self.out, {"differ": [3, "zero_swap"]}))
        t = json.loads((self.out / "TERMINAL.json").read_text())
        self.assertIn("bitwise parity failure", t["first"]["reason"])
        for run in (stage_a.run_instrumented, stage_a.run_native):
            with self.assertRaises(SystemExit) as e:
                run(F.make_ctx(self.out))
            self.assertIn("stopped terminally", str(e.exception))
        r = stage_a.run_report(F.make_ctx(self.out))             # the report still runs, and says STOPPED
        self.assertEqual(r["outcome"], "STOPPED")

    def test_native_parity_failure_is_terminal(self):
        stage_a.run_instrumented(F.make_ctx(self.out))
        with self.assertRaises(stage_a.StopCheck):
            stage_a.run_native(F.make_ctx(self.out, {"native_off": 5}))
        self.assertIn("native parity failed", json.loads((self.out / "TERMINAL.json").read_text())["first"]["reason"])

    def test_native_refused_before_instrumented(self):
        with self.assertRaises(SystemExit) as e:
            stage_a.run_native(F.make_ctx(self.out))
        self.assertIn("instrumented phase has not completed", str(e.exception))

    def test_crash_mid_attempt_needs_authorised_recovery_and_reloads_without_forward(self):
        p = sub(self.out, {"exit_at_call": 40})
        self.assertEqual(p.returncode, 9, p.stderr[-2000:])
        st = state(self.out)
        self.assertIsNotNone(st["open_attempt"])
        crashed = st["open_attempt"]["id"]
        self.assertEqual(len(st["completed"]), 39)
        with self.assertRaises(SystemExit) as e:                # restart: the interrupted attempt holds
            stage_a.run_instrumented(F.make_ctx(self.out))
        self.assertIn(f"RECOVERY_{crashed}.json", str(e.exception))
        self.assertFalse((self.out / "TERMINAL.json").exists())
        (self.out / f"RECOVERY_{crashed}.json").write_text(json.dumps(
            {"attempt_id": crashed, "owner": "test", "date": "2026-10-02", "reason": "test crash"}))
        ctx = F.make_ctx(self.out)
        calls = {}
        orig = ctx.instrument_factory

        def counting():
            inst = orig()
            calls["inst"] = inst
            return inst
        ctx.instrument_factory = counting
        stage_a.run_instrumented(ctx)
        self.assertEqual(calls["inst"].calls, N_INST - 39)      # the 39 committed were reloaded, not re-run
        st = state(self.out)
        self.assertEqual(st["counters"]["row20"]["started"], 16 + N_INST + 1)   # the crashed try stays counted
        self.assertEqual(len(st["recovered_sessions"]), 1)      # the crashed session, charged once
        self.assertTrue(any(s.get("closed") == "crashed" for s in st["sessions"]))

    def test_corrupt_committed_output_holds(self):
        stage_a.run_instrumented(F.make_ctx(self.out))
        victim = self.out / "passes" / "07-zero_ablate.residuals.npy"
        b = bytearray(victim.read_bytes())
        b[-1] ^= 0xFF
        victim.write_bytes(bytes(b))
        with self.assertRaises(stage_a.StopCheck) as e:
            stage_a.run_native(F.make_ctx(self.out))
        self.assertIn("hold for diagnosis", str(e.exception))

    def test_deadline_supervisor_stops_active_work(self):
        cap = stage_a.ENGINEERING_CARRY["seconds"] + 8.0
        p = sub(self.out, {"sleep_at_call": 2}, {"heartbeat_s": 0.25, "stop_grace_s": 5.0, "caps_row20_seconds": cap})
        self.assertNotEqual(p.returncode, 0)
        t = json.loads((self.out / "TERMINAL.json").read_text())
        self.assertIn("time cap", t["first"]["reason"])
        st = state(self.out)
        self.assertIsNone(st["open_attempt"])                   # the interrupted attempt was closed as failed
        self.assertEqual(st["counters"]["row20"]["failed"], 2)  # the carried one and this one


class Units(unittest.TestCase):
    def test_cases(self):
        self.assertIsNone(stage_a.edits_for(F.FakeCE(), "repeat", {}, {"marker_positions": [1, 2, 3]}, None))
        with self.assertRaises(ValueError):
            stage_a.edits_for(F.FakeCE(), "rescue", {}, {"marker_positions": [1, 2, 3]}, None)
        self.assertEqual(stage_a.CASES, ["plain", "empty", "zero_steer", "zero_ablate", "zero_swap", "self_patch",
                                         "repeat"])

    def test_memory_fail_closed(self):
        class BadMX:
            def get_active_memory(self):
                raise RuntimeError("counter gone")
        old = sys.modules.get("mlx.core")
        sys.modules["mlx.core"] = BadMX()
        try:
            with self.assertRaises(enforce.StopRun):
                enforce.memory_reading()
        finally:
            if old is None:
                del sys.modules["mlx.core"]
            else:
                sys.modules["mlx.core"] = old
        orig = enforce.phys_footprint
        enforce.phys_footprint = lambda: (_ for _ in ()).throw(enforce.StopRun("task_info failed"))
        try:
            with self.assertRaises(enforce.StopRun):
                enforce.memory_reading()
        finally:
            enforce.phys_footprint = orig

    def test_attempt_without_commit_fails_and_counts(self):
        with tempfile.TemporaryDirectory() as d:
            b = enforce.Budget(Path(d) / "s.json", "row20", "id", [Path(d)], "t")
            with self.assertRaises(enforce.StopRun):
                with b.attempt("a", "test"):
                    pass
            with self.assertRaises(enforce.StopRun):           # no retry of a failed id
                with b.attempt("a", "test"):
                    pass
            b.close("done")
            c = json.loads((Path(d) / "s.json").read_text())["counters"]["row20"]
            self.assertEqual((c["started"], c["failed"], c["completed"]), (1, 1, 0))

    def test_identity_mismatch_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            enforce.Budget(Path(d) / "s.json", "row20", "one", [Path(d)], "t").close("done")
            with self.assertRaises(enforce.StopRun):
                enforce.Budget(Path(d) / "s.json", "row20", "two", [Path(d)], "t")


class GoBinding(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        git = lambda *a: subprocess.run(["git", "-C", str(self.repo), *a], check=True, capture_output=True)
        git("init", "-q")
        git("config", "user.email", "t@t")
        git("config", "user.name", "t")
        (self.repo / "rev.md").write_text("Verdict: favourable. On board with launching row 20.\n")
        git("add", "rev.md")
        git("commit", "-q", "-m", "review")
        self.commit = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"], capture_output=True,
                                     text=True).stdout.strip()
        self.pkg = {"criteria_sha256": "a", "identity_sha256": "b", "plan_sha256": "c", "manifest_sha256": "d",
                    "budget_sha256": "e"}
        self.go = {"codex_row_review": {"verdict": "favourable", "commit": self.commit, "record_path": "rev.md",
                                        "record_sha256": G.sha_bytes((self.repo / "rev.md").read_bytes())},
                   "owner_go": {"by": "owner", "date": "2099-01-01", "words": "go"}, "package": dict(self.pkg)}
        self.path = Path(self.tmp.name) / "ROW20_GO.json"

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, go):
        self.path.write_text(json.dumps(go))
        return G.require_go(self.path, self.pkg, repo=self.repo)

    def test_good(self):
        self.check(self.go)

    def test_absent(self):
        with self.assertRaises(SystemExit):
            G.require_go(self.path, self.pkg, repo=self.repo)

    def test_mismatches(self):
        bad = []
        g = json.loads(json.dumps(self.go)); g["package"]["plan_sha256"] = "x"; bad.append(g)
        g = json.loads(json.dumps(self.go)); g["codex_row_review"]["verdict"] = "yes"; bad.append(g)
        g = json.loads(json.dumps(self.go)); g["codex_row_review"]["commit"] = "f9d2ef3"; bad.append(g)
        g = json.loads(json.dumps(self.go)); g["codex_row_review"]["record_sha256"] = "0" * 64; bad.append(g)
        g = json.loads(json.dumps(self.go)); g["owner_go"]["date"] = "2000-01-01"; bad.append(g)
        g = json.loads(json.dumps(self.go)); del g["owner_go"]["words"]; bad.append(g)
        g = json.loads(json.dumps(self.go)); g["package"]["extra"] = "z"; bad.append(g)
        for g in bad:
            with self.assertRaises(SystemExit):
                self.check(g)


if __name__ == "__main__":
    unittest.main()
