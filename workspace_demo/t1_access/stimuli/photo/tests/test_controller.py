"""Controller mechanism fixtures (closure groups 2, 3, 4, 6): real subprocess workers, synthetic, no model and no
development input. Elapsed bounds and durable counters are asserted, not just exit codes. With RECORD_FIXTURES=1 the
measured values are written to stimuli/photo/controller_fixtures.json (the retained mechanism evidence).

    RECORD_FIXTURES=1 .venv-image/bin/python -m unittest discover -s stimuli/photo/tests -p 'test_controller.py' -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import memprobe  # noqa: E402
import stage_a_controller as C  # noqa: E402

PY = sys.executable
CARRY = 1808.73
MEASURED: dict = {}


def ctl(out: Path, modes: dict, **kw) -> C.Controller:
    return C.Controller(out, carry_seconds=CARRY,
                        worker_cmd=lambda ph: [PY, str(HERE / "fake_worker.py"), str(out), modes[ph]],
                        system_reader=kw.pop("system_reader", lambda: {"swap": 0, "pressure": 1}), **kw)


def terminal(out: Path) -> dict | None:
    p = out / "TERMINAL.json"
    return json.loads(p.read_text()) if p.exists() else None


OK = {"instrumented": "ok:instrumented", "native": "ok:native", "report": "ok:report"}


class Controller(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp()) / "o"

    def test_pass_sequential_and_lock_held(self):
        t = time.monotonic()
        final = ctl(self.out, OK).run()
        self.assertEqual(final["outcome"], "PASS")
        log = [json.loads(l) for l in (self.out / "worker_log.jsonl").read_text().splitlines()]
        self.assertEqual([l["phase"] for l in log], ["instrumented", "native", "report"])
        self.assertTrue(all(l["lock_held_by_controller"] for l in log))
        rec = json.loads((self.out / "controller.json").read_text())
        w = rec["workers"]
        for a, b in zip(w, w[1:]):
            self.assertGreaterEqual(b["spawned_total_s"], a["exited_total_s"])   # spawned only after reap
        self.assertIsNone(rec["open_session"])
        self.assertGreater(final["seconds_total"], CARRY)
        self.assertGreater(final["peaks"]["lifetime_max_phys_footprint"], 0)
        c2 = ctl(Path(tempfile.mkdtemp()) / "o", OK, gates=lambda: None)
        c2.run()
        self.assertTrue(c2.gates_ok)                                         # passed gates mark the report run
        MEASURED["pass_run_seconds"] = round(time.monotonic() - t, 3)

    def test_deadline_kills_a_worker_that_ignores_sigterm(self):
        cap = CARRY + C.TAIL_RESERVE_S + C.STOP_RESERVE_S + C.REPORT_RESERVE_S + 3.0
        t = time.monotonic()
        final = ctl(self.out, {**OK, "instrumented": "family"}, row_cap_s=cap).run()
        elapsed = time.monotonic() - t
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertIn("time limit", terminal(self.out)["first"]["reason"])
        w = json.loads((self.out / "controller.json").read_text())["workers"][0]
        self.assertEqual(w["how"], "SIGKILL")
        self.assertLessEqual(w["kill_to_reap_s"], C.TERM_GRACE_S + 1.0)
        gpid = int((self.out / "grandchild.pid").read_text())
        time.sleep(0.2)
        alive = subprocess.run(["ps", "-p", str(gpid)], capture_output=True).returncode == 0
        self.assertFalse(alive, "the grandchild outlived the kill of its process group")
        self.assertLessEqual(elapsed, 3.0 + C.TERM_GRACE_S + 4.0)           # deadline + grace + report + slack
        self.assertTrue((self.out / "report/stage_a_report.json").exists())  # the STOPPED report still ran
        MEASURED["deadline"] = {"kill_to_reap_s": round(w["kill_to_reap_s"], 3), "how": w["how"],
                                "run_seconds": round(elapsed, 3), "grandchild_killed": not alive}

    def test_deadline_kills_a_worker_busy_in_metal(self):
        cap = CARRY + C.TAIL_RESERVE_S + C.STOP_RESERVE_S + C.REPORT_RESERVE_S + 6.0
        t = time.monotonic()
        final = ctl(self.out, {**OK, "instrumented": "mlxblock"}, row_cap_s=cap).run()
        elapsed = time.monotonic() - t
        self.assertTrue((self.out / "mlx_started").exists())
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertIn("time limit", terminal(self.out)["first"]["reason"])
        w = json.loads((self.out / "controller.json").read_text())["workers"][0]
        self.assertLessEqual(w["kill_to_reap_s"], C.TERM_GRACE_S + 2.0)
        MEASURED["deadline_metal"] = {"kill_to_reap_s": round(w["kill_to_reap_s"], 3), "how": w["how"],
                                      "run_seconds": round(elapsed, 3)}

    def test_memory_stop(self):
        old = C.MEM_STOP
        C.MEM_STOP = 512 << 20
        try:
            t = time.monotonic()
            final = ctl(self.out, {**OK, "instrumented": "alloc:1"}).run()
        finally:
            C.MEM_STOP = old
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertIn("task memory", terminal(self.out)["first"]["reason"])
        MEASURED["memory_stop_seconds"] = round(time.monotonic() - t, 3)

    def test_sampler_unavailable_and_slow(self):
        def gone(pid):
            raise memprobe.Unavailable("test")

        def slow(pid):
            time.sleep(1.2)
            return memprobe.footprint(pid)
        for name, s, want in (("unavailable", gone, "unavailable"), ("slow", slow, "took")):
            with self.subTest(name):
                out = Path(tempfile.mkdtemp()) / "o"
                final = ctl(out, {**OK, "instrumented": "block"}, sampler=s).run()
                self.assertEqual(final["outcome"], "STOPPED")
                self.assertIn(want, terminal(out)["first"]["reason"])

    def test_initial_resource_failure_is_terminal(self):
        def bad():
            raise C.ControllerStop("sysctl unavailable")
        final = ctl(self.out, OK, system_reader=bad).run()
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertIn("sysctl unavailable", terminal(self.out)["first"]["reason"])
        self.assertFalse((self.out / "INSTRUMENTED_DONE.json").exists())

    def test_worker_crash_and_missing_record(self):
        for mode, want in (("exit:3", "exited 3"), ("norecord", "without its durable phase record")):
            with self.subTest(mode):
                out = Path(tempfile.mkdtemp()) / "o"
                final = ctl(out, {**OK, "instrumented": mode}).run()
                self.assertEqual(final["outcome"], "STOPPED")
                self.assertIn(want, terminal(out)["first"]["reason"])

    def test_terminal_holds_later_runs_but_report_runs(self):
        ctl(self.out, {**OK, "instrumented": "exit:3"}).run()
        first = terminal(self.out)["first"]
        final = ctl(self.out, OK).run()
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertEqual(terminal(self.out)["first"], first)               # the first reason stays first
        self.assertFalse((self.out / "INSTRUMENTED_DONE.json").exists())

    def test_crash_tail_charge(self):
        self.out.mkdir(parents=True)
        (self.out / "controller.json").write_text(json.dumps({
            "carry_s": CARRY, "seconds_total": CARRY + 100.0, "sessions": [], "stops": [], "workers": [],
            "open_session": {"session": "dead", "pid": 1, "live_s": 10.0, "opened_wall": 0},
            "peaks": {"lifetime_max_phys_footprint": 0, "by_phase": {}, "storage_bytes": 0}, "swap_baseline": 0}))
        for ph in ("instrumented", "native"):
            (self.out / f"{ph.upper()}_DONE.json").write_text("{}")
        final = ctl(self.out, OK).run()
        rec = json.loads((self.out / "controller.json").read_text())
        crashed = [s for s in rec["sessions"] if s.get("closed") == "crashed"]
        self.assertEqual(crashed[0]["charged_s"], 10.0 + C.TAIL_RESERVE_S)
        self.assertGreaterEqual(final["seconds_total"], CARRY + 100.0 + 10.0 + C.TAIL_RESERVE_S)

    def test_persistence_failure_is_bounded(self):
        """In a subprocess: the controller's writer fails after its first writes; the worker must be killed and
        the controller must exit 75 with the first reason durable."""
        out = Path(tempfile.mkdtemp()) / "o"
        script = (f"import sys,json; sys.path.insert(0,{str(HERE.parent)!r}); sys.path.insert(0,{str(HERE)!r})\n"
                  "import stage_a_controller as C, test_controller as T\n"
                  "from enforce import write_json_atomic\n"
                  "n={'k':0}\n"
                  "def w(p,o):\n"
                  "    n['k']+=1\n"
                  "    if n['k']>3: raise OSError('disk full (fixture)')\n"
                  "    write_json_atomic(p,o)\n"
                  f"T.ctl(__import__('pathlib').Path({str(out)!r}), dict(T.OK, instrumented='block'), writer=w).run()\n")
        t = time.monotonic()
        p = subprocess.run([PY, "-c", script], capture_output=True, text=True, timeout=120)
        elapsed = time.monotonic() - t
        self.assertEqual(p.returncode, 75, p.stderr[-1500:])
        self.assertIn("persistence failure", terminal(out)["first"]["reason"])
        self.assertLessEqual(elapsed, 15.0)
        MEASURED["persistence_failure_seconds"] = round(elapsed, 3)


def tearDownModule():
    if os.environ.get("RECORD_FIXTURES") == "1":
        rec = {"recorded": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "python": sys.version.split()[0],
               "measured": MEASURED, "memory_fixture": memprobe.fixture(PY),
               "note": "synthetic workers, no model, no development input"}
        (HERE.parent / "controller_fixtures.json").write_text(json.dumps(rec, indent=1) + "\n")


if __name__ == "__main__":
    unittest.main()
