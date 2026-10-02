"""AI-reader revision 4, closures 3 and 5: HARD-KILL fixtures. The executor runs as a real subprocess in fixture mode (fake
codex, synthetic images, no model) and dies by os._exit(77) at each crash window, or by an external SIGKILL while its
worker is alive; a second process then recovers from the journal alone. Asserted every time: the journal validates,
the counters are exact, no request is dispatched again after a durable answer, an attempt that may have been answered
is retained as INTERRUPTED and never re-asked, an attempt never dispatched sends nothing, the crashed session's
time is charged, a worker never outlives its dead orchestrator beyond the watchdog's bound, and the smoke hold of the
first request is rebuilt from the journal after a crash in any of its windows.

    .venv-image/bin/python -m unittest discover -s stimuli/photo/tests -p 'test_ai_reader_crash.py' -v
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS.parent))
sys.path.insert(0, str(TESTS))
import ai_reader_exec as X  # noqa: E402
import ai_reader_journal as J  # noqa: E402
import airq_fixture as A  # noqa: E402
import memprobe  # noqa: E402

DRIVER = TESTS / "airq_fixture.py"


def drive(root: Path, crash: str | None = None, timeout: float = 120) -> subprocess.CompletedProcess:
    env = {**os.environ, "AIRQ_CRASH": crash} if crash else {k: v for k, v in os.environ.items() if k != "AIRQ_CRASH"}
    return subprocess.run([sys.executable, str(DRIVER), str(root)], capture_output=True, text=True, env=env,
                          timeout=timeout)


class HardKill(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(dir=X.ensure_root()))

    def build(self, plan=None):
        self.b = A.build(self.root, plan or {"rq1c": ["slow_ok:1:thing"]})
        return self.b

    def journal(self):
        recs, tail = J.read(self.b["fixture"]["raw"])
        return recs, tail

    def finish_and_check(self) -> list[dict]:
        p = drive(self.root)
        self.assertEqual(p.returncode, 0, p.stderr[-2000:])
        self.assertEqual(json.loads(p.stdout.strip().splitlines()[-1])["outcome"], "COMPLETE")
        recs, tail = self.journal()
        self.assertEqual(tail, b"")
        v = J.validate(recs, self.b["sset"], A.DIGEST, raw_bytes=self.b["fixture"]["raw"].read_bytes(),
                       mode="synthetic-fixture", delivery=self.b["fixture"]["delivery"],
                       instructions_sha256=self.b["fixture"]["delivery"]["instructions_sha256"], limits=X.LIMITS)
        self.assertEqual(v["final"], 6)
        # no dispatch after a durable answer for the same request
        answered_at = {}
        for r in recs:
            if r["t"] == "end" and r["retained"]:
                answered_at.setdefault(r["request"], r["seq"])
        disp_reqs = [d["request"] for d in A.dispatches(self.root)]
        begins = [r for r in recs if r["t"] == "begin"]
        for rq in answered_at:
            later = [r for r in begins if r["request"] == rq and r["seq"] > answered_at[rq]]
            self.assertEqual(later, [], f"{rq} begun again after a retained outcome")
        self.assertLessEqual(len(disp_reqs), len(begins))
        clock = json.loads((self.b["fixture"]["job"] / "clock.json").read_text())
        crashed = [s for s in clock["sessions"] if s.get("closed") == "crashed"]
        return recs, crashed

    def crash_at(self, point: str, n: int):
        p = drive(self.root, f"{point}:{n}")
        self.assertEqual(p.returncode, 77, p.stderr[-2000:])

    def test_before_begin(self):
        self.build()
        self.crash_at("before_begin", 2)
        recs, crashed = self.finish_and_check()
        self.assertEqual(len(crashed), 1)
        self.assertGreaterEqual(crashed[0]["charged_s"], X.TAIL_S)
        self.assertFalse([r for r in recs if r["t"] == "recovered"])     # nothing was open

    def test_after_begin_not_dispatched(self):
        self.build()
        self.crash_at("after_begin", 2)
        recs, _ = self.finish_and_check()
        rv = [r for r in recs if r["t"] == "recovered"]
        self.assertEqual(rv[0]["finding"], "not_dispatched")
        self.assertEqual([d["request"] for d in A.dispatches(self.root)].count("rq1c"), 1)  # sent once, by the retry
        tries = [r for r in recs if r["t"] == "begin" and r["request"] == "rq1c"]
        self.assertEqual(len(tries), 2)                                    # the lost try stays charged

    def test_after_dispatch_record_before_go(self):
        self.build()
        self.crash_at("after_dispatch", 2)                                # the gate gets EOF: nothing is sent
        time.sleep(0.5)
        recs, _ = self.finish_and_check()
        self.assertEqual([d["request"] for d in A.dispatches(self.root)].count("rq1c"), 0)
        e = next(r for r in recs if r["t"] == "end" and r["request"] == "rq1c")
        self.assertEqual(e["outcome"], "interrupted")                     # conservative: dispatched => interrupted

    def wait_dispatch(self, rq):
        for _ in range(400):
            if any(d["request"] == rq for d in A.dispatches(self.root)):
                break
            time.sleep(0.05)
        return next(d["pid"] for d in A.dispatches(self.root) if d["request"] == rq)

    def worker_pid(self, rq):
        """The worker's pid from the journal's durable dispatched record (the fake may be killed before it logs)."""
        recs, _ = self.journal()
        aid = next(r["attempt_id"] for r in recs if r["t"] == "begin" and r["request"] == rq)
        return next(r["worker"]["pid"] for r in recs if r["t"] == "dispatched" and r["attempt_id"] == aid)

    def wait_gone(self, pid, limit):
        t = time.monotonic()
        while memprobe.proc_info(pid) is not None and time.monotonic() - t < limit:
            time.sleep(0.05)
        return time.monotonic() - t

    def test_after_go_worker_killed_by_the_watchdog(self):
        self.build({"rq1c": ["slow_ok:30:thing"]})
        self.crash_at("after_go", 2)
        pid = self.worker_pid("rq1c")
        gone = self.wait_gone(pid, 15)                                    # the orchestrator is dead: the watchdog acts
        self.assertIsNone(memprobe.proc_info(pid))
        self.assertLessEqual(gone, X.TERM_GRACE_S + 3.0)
        recs, _ = self.finish_and_check()
        rv = next(r for r in recs if r["t"] == "recovered")
        self.assertEqual(rv["finding"], "dispatched_no_end")
        self.assertLessEqual([d["request"] for d in A.dispatches(self.root)].count("rq1c"), 1)   # never re-asked

    def test_after_response_answer_lost(self):
        self.build()
        self.crash_at("after_response", 2)
        recs, _ = self.finish_and_check()
        rv = next(r for r in recs if r["t"] == "recovered")
        self.assertEqual(rv["evidence"]["last.txt"]["text"], "thing")    # the evidence is kept for audit
        e = next(r for r in recs if r["t"] == "end" and r["request"] == "rq1c")
        self.assertEqual((e["outcome"], e["retained"], e["answer"]), ("interrupted", True, None))
        self.assertEqual([d["request"] for d in A.dispatches(self.root)].count("rq1c"), 1)

    def test_after_end_answer_durable(self):
        self.build()
        self.crash_at("after_end", 2)
        recs, _ = self.finish_and_check()
        e = next(r for r in recs if r["t"] == "end" and r["request"] == "rq1c")
        self.assertEqual((e["outcome"], e["answer"]), ("ok", "thing"))
        self.assertEqual([d["request"] for d in A.dispatches(self.root)].count("rq1c"), 1)

    def test_after_state(self):
        self.build()
        self.crash_at("after_state", 2)
        recs, _ = self.finish_and_check()
        self.assertEqual([d["request"] for d in A.dispatches(self.root)].count("rq1c"), 1)

    def test_terminal_no_response(self):
        self.build({"rq1c": ["fail"]})
        self.crash_at("final", 4)                                        # three failures done, final not yet written
        recs, _ = self.finish_and_check()
        self.assertEqual(len([r for r in recs if r["t"] == "final"]), 1)
        self.assertEqual([d["request"] for d in A.dispatches(self.root)].count("rq1c"), 3)

    def test_recovery_persistence(self):
        self.build({"rq1c": ["slow_ok:30:thing"]})
        self.crash_at("after_go", 2)
        self.crash_at("recovery", 2)                                     # dies after 'recovered', before 'end'
        recs, _ = self.finish_and_check()
        self.assertEqual(len([r for r in recs if r["t"] == "recovered"]), 1)
        self.assertEqual(len([r for r in recs if r["t"] == "end" and r["outcome"] == "interrupted"]), 1)

    def test_incomplete_tail_quarantined(self):
        self.build()
        self.crash_at("after_state", 2)
        with open(self.b["fixture"]["raw"], "ab") as fh:
            fh.write(b'{"t": "end", "seq": 99, "answ')                     # a write cut by a crash
        recs, _ = self.finish_and_check()
        tr = [r for r in recs if r["t"] == "tail_repair"]
        self.assertEqual(len(tr), 1)
        self.assertTrue((self.b["fixture"]["job"] / "quarantine" / tr[0]["quarantine"]).exists())

    def test_external_sigkill_with_live_worker(self):
        """The orchestrator is SIGKILLed with its worker running: the watchdog kills the worker group within its
        bound (no independent deadline gap); recovery then finds the identities gone and records the attempt."""
        self.build({"rq1c": ["slow_ok:30:thing"]})
        env = {k: v for k, v in os.environ.items() if k != "AIRQ_CRASH"}
        p = subprocess.Popen([sys.executable, str(DRIVER), str(self.root)], env=env, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        pid = self.wait_dispatch("rq1c")
        time.sleep(0.3)
        p.send_signal(signal.SIGKILL)
        p.wait()
        p.stdout.close()
        p.stderr.close()
        gone = self.wait_gone(pid, 15)
        self.assertIsNone(memprobe.proc_info(pid), "the worker outlived its dead orchestrator")
        self.assertLessEqual(gone, X.TERM_GRACE_S + 3.0)
        for _ in range(100):                                              # written once the group is gone
            wd = list((self.b["fixture"]["job"]).glob("watchdog_*.json"))
            if wd:
                break
            time.sleep(0.05)
        self.assertTrue(wd and json.loads(wd[0].read_text())["reason"] == "controller died")
        recs, crashed = self.finish_and_check()
        self.assertEqual(next(r for r in recs if r["t"] == "recovered")["finding"], "dispatched_no_end")
        self.assertEqual(len(crashed), 1)

    # ---- attempt 1: the smoke's crash windows -------------------------------------------------------------------
    def stopped_check(self, want: str):
        p = drive(self.root)
        self.assertEqual(p.returncode, 0, p.stderr[-2000:])
        out = json.loads(p.stdout.strip().splitlines()[-1])
        self.assertEqual(out["outcome"], "STOPPED")
        self.assertIn(want, out["reason"])
        recs, _ = self.journal()
        J.validate(recs, self.b["sset"], A.DIGEST, raw_bytes=self.b["fixture"]["raw"].read_bytes(),
                   mode="synthetic-fixture", delivery=self.b["fixture"]["delivery"],
                   instructions_sha256=self.b["fixture"]["delivery"]["instructions_sha256"], limits=X.LIMITS,
                   require_complete=False)
        self.assertLessEqual({d["request"] for d in A.dispatches(self.root)}, {"rq0c"})   # nothing after the hold
        return recs

    def test_attempt1_answer_durable_then_crash_holds(self):
        self.build({"rq0c": ["noimage"]})
        self.crash_at("after_end", 1)                                    # the end is durable, no receipt yet
        recs = self.stopped_check("no image")
        self.assertEqual(recs[-1]["smoke"]["state"], "held")

    def test_attempt1_uncertain_smoke_never_passes(self):
        self.build({"rq0c": ["slow_ok:30:thing"]})
        self.crash_at("after_go", 1)
        self.wait_gone(self.worker_pid("rq0c"), 15)
        recs = self.stopped_check("uncertain smoke")
        self.assertEqual(next(r for r in recs if r["t"] == "end")["outcome"], "interrupted")

    def test_attempt1_not_dispatched_retries(self):
        self.build({"rq0c": ["ok:thing"]})
        self.crash_at("after_begin", 1)
        recs, _ = self.finish_and_check()
        self.assertEqual(next(r for r in recs if r["t"] == "recovered")["finding"], "not_dispatched")

    def test_first_request_retry_crash_holds(self):
        self.build({"rq0c": ["fail", "noimage"]})
        self.crash_at("after_end", 2)                                    # try 2 of the FIRST request answered
        recs = self.stopped_check("no image")
        self.assertEqual([r["try"] for r in recs if r["t"] == "begin"], [1, 2])


if __name__ == "__main__":
    unittest.main()
