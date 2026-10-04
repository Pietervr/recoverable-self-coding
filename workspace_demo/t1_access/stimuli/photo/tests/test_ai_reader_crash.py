"""AI-reader revision 5 (Codex RSC 1bf9890 R2, R3, R4, R6; revision 4 closures 3 and 5): HARD-KILL fixtures. The executor runs as a real subprocess in fixture mode (fake
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
import ai_reader_runtime as R  # noqa: E402
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


class Rev5Recovery(HardKill):
    """R2, R3, R4 and R6 across a real process death."""

    def valid_stopped(self, want: str) -> list[dict]:
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
        return recs

    def test_structural_after_end_first_and_later_request(self):
        """R2: a durable structural end, then a crash before STOPPED: the restart goes straight to a valid STOPPED -
        no preflight, no new open record, nothing dispatched."""
        for rq, n in (("rq0c", 1), ("rq1c", 2)):
            with self.subTest(rq):
                self.root = Path(tempfile.mkdtemp(dir=X.ensure_root()))
                self.build({rq: ["structural"]})
                self.crash_at("after_end", n)
                before = len(A.dispatches(self.root))
                recs = self.valid_stopped("structural")
                ends = [i for i, r in enumerate(recs) if r["t"] == "end" and r["outcome"] == "structural_failure"]
                self.assertEqual([r["t"] for r in recs[ends[0] + 1:]], ["receipt"])
                self.assertEqual(len([r for r in recs if r["t"] == "open"]), 1)
                self.assertEqual(len(A.dispatches(self.root)), before)

    def test_immediate_restart_kills_unrecorded_members(self):
        """R3: a crashed attempt whose recorded worker is alive with a child NO record names, and whose watchdog is
        alive: recovery enumerates the identity-anchored group, kills and confirms everything, and only then the
        watchdog."""
        self.build({"rq1c": ["ok:thing"]})
        self.crash_at("after_begin", 2)
        pidf = self.root / "unrecorded.pid"
        lead = subprocess.Popen([sys.executable, "-c",
                                 "import subprocess, sys, time; c = subprocess.Popen([sys.executable, '-c', "
                                 f"'import time; time.sleep(600)']); open({str(pidf)!r}, 'w').write(str(c.pid)); "
                                 "time.sleep(600)"], start_new_session=True)
        wdp = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"], start_new_session=True)
        for _ in range(200):
            if pidf.exists() and pidf.read_text():
                break
            time.sleep(0.02)
        child = int(pidf.read_text())
        recs, _ = self.journal()
        b = recs[-1]
        self.assertEqual(b["t"], "begin")
        J.append(self.b["fixture"]["raw"], {"t": "dispatched", "seq": b["seq"] + 1, "package_digest": A.DIGEST,
                                            "mode": "synthetic-fixture", "attempt_id": b["attempt_id"],
                                            "pid": lead.pid, "worker": memprobe.proc_info(lead.pid),
                                            "watchdog": memprobe.proc_info(wdp.pid), "wall": time.time()})
        recs, crashed = self.finish_and_check()
        lead.wait(timeout=5)
        wdp.wait(timeout=5)
        self.assertIsNone(memprobe.proc_info(child), "an unrecorded member of the crashed group survived")
        rv = next(r for r in recs if r["t"] == "recovered")
        self.assertEqual(rv["finding"], "dispatched_no_end")
        self.assertIn(child, [k["pid"] for k in rv["killed"]])
        self.assertEqual(rv["killed"][-1]["pid"], wdp.pid)                  # the safeguard retired last

    def test_exhausted_resume_stops_before_preflight(self):
        """R4: a resume with too little time left records the recovery and goes straight to STOPPED."""
        self.build()
        self.crash_at("after_begin", 2)
        cp = self.b["fixture"]["job"] / "clock.json"
        c = json.loads(cp.read_text())
        c["seconds_total"] = X.LIMITS["job_clock_s"] - X.FINAL_S - 10.0 - c["open_session"]["live_s"] - X.TAIL_S
        cp.write_text(json.dumps(c))
        recs = self.valid_stopped("job clock")
        self.assertEqual(len([r for r in recs if r["t"] == "open"]), 1)        # no fresh preflight/open
        self.assertEqual([r["t"] for r in recs[-3:]], ["recovered", "end", "receipt"])

    def test_quarantine_crash_before_truncation_one_record(self):
        """R6: the quarantine file exists but the journal still holds the tail (a crash between the two): one
        quarantine, one record."""
        self.build()
        self.crash_at("after_state", 2)
        raw = self.b["fixture"]["raw"]
        tail = b'{"t": "end", "seq": 99, "answ'
        with open(raw, "ab") as fh:
            fh.write(tail)
        recs, _ = self.journal()
        q = self.b["fixture"]["job"] / "quarantine"
        q.mkdir(parents=True, exist_ok=True)
        (q / f"tail_{len(recs) + 1:06d}_{J.sha(tail)[:12]}.bin").write_bytes(tail)
        recs, _ = self.finish_and_check()
        self.assertEqual(len([r for r in recs if r["t"] == "tail_repair"]), 1)


class Rev6(HardKill):
    """Codex RSC b569f8a, reader 1 and 3, across a real process death."""

    def test_watchdog_does_not_retire_while_a_recorded_escaped_member_lives(self):
        """Reader 1: the leader exits, its recorded child has left the group, and the orchestrator dies before its
        own cleanup: the watchdog must not retire on the empty group - it kills the recorded member."""
        self.build({"rq1c": ["escape:thing"]})
        p = drive(self.root, "after_leader_exit:2")
        self.assertEqual(p.returncode, 77, p.stderr[-2000:])
        child = int((self.root / "escaped.pid").read_text())
        t = time.monotonic()
        while memprobe.proc_info(child) is not None and time.monotonic() - t < 10:
            time.sleep(0.02)
        self.assertIsNone(memprobe.proc_info(child), "the recorded escaped child outlived the dead orchestrator")
        wd = [json.loads(x.read_text()) for x in self.b["fixture"]["job"].glob("watchdog_*.json")]
        self.assertTrue(any(w["reason"] == "controller died" and child in w.get("killed", []) for w in wd))
        recs, _ = self.finish_and_check()

    def slow_close_run(self, allowance: float, slow_receipt: float, slow_close: float) -> tuple:
        self.root = Path(tempfile.mkdtemp(dir=X.ensure_root()))
        self.build({})
        env = {**{k: v for k, v in os.environ.items() if k != "AIRQ_CRASH"}, "AIRQ_FINAL_WRITE_S": str(allowance),
               "AIRQ_SLOW_RECEIPT": str(slow_receipt), "AIRQ_SLOW_CLOSE": str(slow_close)}
        t = time.monotonic()
        p = subprocess.run([sys.executable, str(DRIVER), str(self.root)], capture_output=True, text=True, env=env,
                           timeout=180)
        return p, time.monotonic() - t

    def test_slow_receipt_and_slow_close_share_one_deadline(self):
        """Reader 3, made deterministic (reader revision 16, Codex 431f072/478196f): with a 3 s allowance the stop's ONE
        timer is 3 - 2 x 0.5 = 2 s, armed before the receipt write. The old fixture slept 2 s before the receipt AND 2 s
        before the close - the receipt's wake and the timer coincided, a race with no margin. Now three distinct
        controls, each 2 s clear of the timer: (1) a receipt stall of 4 s -> exit 75, no durable receipt, nothing
        qualifies; (2) an instant receipt and a 4 s close -> exit 75, the receipt durable but the clock never closed on
        it, so it does not qualify; (3) both 0.3 s -> exit 0 and the closed clock names this journal. Production
        closure bounds unchanged."""
        p, _ = self.slow_close_run(3.0, 4.0, 0.0)                                   # (1) the receipt stalls
        self.assertEqual(p.returncode, 75, p.stderr[-1500:])
        recs, _ = self.journal()
        self.assertNotEqual(recs[-1]["t"], "receipt")                                # never durable
        p, _ = self.slow_close_run(3.0, 0.0, 4.0)                                   # (2) durable receipt, slow close
        self.assertEqual(p.returncode, 75, p.stderr[-1500:])
        recs, _ = self.journal()
        self.assertEqual((recs[-1]["t"], recs[-1]["outcome"]), ("receipt", "COMPLETE"))
        raw = self.b["fixture"]["raw"].read_bytes()
        with self.assertRaisesRegex(SystemExit, "no closure marker|not closed on this receipt"):
            X.admit_clock(self.b["fixture"]["job"] / "clock.json", raw, recs[-1])
        p, _ = self.slow_close_run(3.0, 0.3, 0.3)                                   # (3) inside the allowance
        self.assertEqual(p.returncode, 0, p.stderr[-1500:])
        recs, _ = self.journal()
        ok = X.admit_clock(self.b["fixture"]["job"] / "clock.json", self.b["fixture"]["raw"].read_bytes(), recs[-1])
        self.assertLessEqual(ok["seconds_total"], recs[-1]["seconds_total"])

    def test_setup_before_the_clock_is_bounded(self):
        """Reader 3: a stall in check_accounting, before the clock (and its guard) exists, ends at the setup timer."""
        self.build({})
        env = {**{k: v for k, v in os.environ.items() if k != "AIRQ_CRASH"}, "AIRQ_SETUP_S": "1.0",
               "AIRQ_SLOW_ACCOUNTING": "30"}
        t = time.monotonic()
        p = subprocess.run([sys.executable, str(DRIVER), str(self.root)], capture_output=True, text=True, env=env,
                           timeout=60)
        self.assertEqual(p.returncode, 75, p.stderr[-800:])
        self.assertLess(time.monotonic() - t, 10.0)


class Rev16(unittest.TestCase):
    """Reader revision 16 (Codex 478196f P2): a crash right after the MARKED durable end (U+3000 x 683, 2,049 bytes)
    and before STOPPED - the restart validates that journal, derives the hold, writes STOPPED and dispatches nothing.
    (HardKill's helpers are borrowed, not inherited, so its own cases are not run twice.)"""

    setUp, build, journal, crash_at = HardKill.setUp, HardKill.build, HardKill.journal, HardKill.crash_at

    def test_crash_after_the_marked_end_then_restart(self):
        for kind in ("capacity:w683", "capacity_structural:w683",                   # revision 16
                     "capacity:w349526", "capacity_structural:w349526"):             # revision 17: the 1 MiB cut
            with self.subTest(kind):
                self.root = Path(tempfile.mkdtemp(dir=X.ensure_root()))
                self.build({"rq1c": ["ok:thing"], "rq2c": [kind, "ok:thing"], "rq3c": ["ok:thing"]})
                self.crash_at("after_end", 3)                       # rq0c, rq1c, then rq2c
                recs, _ = self.journal()
                self.assertEqual(recs[-1]["t"], "end")
                self.assertEqual(recs[-1]["isolation_events"][-1], R.CAPACITY_UNPROVEN)
                before = [d["request"] for d in A.dispatches(self.root)]
                p = drive(self.root)
                self.assertEqual(p.returncode, 0, p.stderr[-2000:])
                last = json.loads(p.stdout.strip().splitlines()[-1])
                self.assertEqual(last["outcome"], "STOPPED")
                self.assertIn("incomplete -o evidence", last["reason"])
                self.assertEqual([d["request"] for d in A.dispatches(self.root)], before)   # no next dispatch
                recs, _ = self.journal()
                J.validate(recs, self.b["sset"], A.DIGEST, require_complete=False, mode="synthetic-fixture",
                           delivery=self.b["fixture"]["delivery"],
                           instructions_sha256=self.b["fixture"]["delivery"]["instructions_sha256"], limits=X.LIMITS)


class Rev7(HardKill):
    """Codex RSC c036c00, reader A and B, across real process exits."""

    def run_env(self, plan=None, **env) -> subprocess.CompletedProcess:
        self.root = Path(tempfile.mkdtemp(dir=X.ensure_root()))
        self.build(plan or {})
        e = {**{k: v for k, v in os.environ.items() if k != "AIRQ_CRASH"}, **env}
        return subprocess.run([sys.executable, str(DRIVER), str(self.root)], capture_output=True, text=True, env=e,
                              timeout=180)

    def admitted(self) -> dict:
        recs, _ = self.journal()
        return X.admit_clock(self.b["fixture"]["job"] / "clock.json", self.b["fixture"]["raw"].read_bytes(), recs[-1])

    def test_post_rename_clock_failure_and_stall_do_not_qualify(self):
        """Reader A: the closed clock is renamed into place, then its directory fsync fails (or stalls): the COMPLETE
        receipt is durable and the closed clock readable, but there is no closure marker - not admitted."""
        for mode, codes in (("error", (1,)), ("stall", (75,))):
            with self.subTest(mode):
                p = self.run_env(AIRQ_CLOSE_FAIL=mode, AIRQ_FINAL_WRITE_S="4")
                self.assertIn(p.returncode, codes, p.stderr[-800:])
                recs, _ = self.journal()
                self.assertEqual((recs[-1]["t"], recs[-1]["outcome"]), ("receipt", "COMPLETE"),
                                 f"{recs[-1].get('reason')!r} | {p.stderr[-1500:]}")
                c = json.loads((self.b["fixture"]["job"] / "clock.json").read_text())
                self.assertIsNone(c["open_session"])                      # the renamed snapshot says 'closed' ...
                with self.assertRaisesRegex(SystemExit, "no closure marker"):
                    self.admitted()                                       # ... and does not qualify

    def test_marker_failure_after_its_rename_is_removed(self):
        """Reader A (revision 8 path): the marker's write fails before its commit - no marker, not admitted."""
        p = self.run_env(AIRQ_MARKER_FAIL="error")
        self.assertEqual(p.returncode, 1, p.stderr[-800:])
        self.assertFalse((self.b["fixture"]["job"] / "clock.closed.json").exists())
        with self.assertRaisesRegex(SystemExit, "no closure marker"):
            self.admitted()

    def pending(self) -> list:
        return sorted(self.b["fixture"]["job"].glob("clock.starting*.json"))

    def test_failed_start_is_charged_at_the_next_start(self):
        """Reader B: a start killed by its setup timer before the clock's first persist is charged next time."""
        p = self.run_env(AIRQ_SETUP_S="1.0", AIRQ_SLOW_ACCOUNTING="30")
        self.assertEqual(p.returncode, 75, p.stderr[-800:])
        self.assertEqual(len(self.pending()), 1)
        p = drive(self.root)
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        c = json.loads((self.b["fixture"]["job"] / "clock.json").read_text())
        fs = [x for x in c["sessions"] if x.get("closed") == "failed_start"]
        self.assertEqual(len(fs), 1)
        self.assertGreater(fs[0]["charged_s"], 0.5)
        self.assertEqual(self.pending(), [])
        self.admitted()                                                   # coherent totals with the charge included

    def test_coherent_undercharge_refused(self):
        """Reader B: an alternate clock - total 0, one closed session of 0 s naming the journal, marker consistent -
        is below the journal's charged attempt seconds; a sum-consistent but under-charged total too."""
        p = self.run_env({"rq1c": ["slow_ok:1:thing"]})
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        recs, _ = self.journal()
        raw = self.b["fixture"]["raw"].read_bytes()
        cp = self.b["fixture"]["job"] / "clock.json"
        c = json.loads(cp.read_text())
        last = dict(c["sessions"][-1], live_s=0.0)
        alt = {"sessions": [last], "seconds_total": 0.0, "open_session": None}
        b_ = json.dumps(alt, indent=1, sort_keys=True).encode()
        cp.write_bytes(b_)
        (self.b["fixture"]["job"] / "clock.closed.json").write_text(json.dumps(
            {"session": last["session"], "raw_sha256": J.sha(raw), "clock_sha256": J.sha(b_)}))
        with self.assertRaisesRegex(SystemExit, "below the journal's charged attempt time"):
            X.admit_clock(cp, raw, recs[-1])
        alt = {"sessions": [dict(last, live_s=5.0)], "seconds_total": 99.0, "open_session": None}
        b_ = json.dumps(alt, indent=1, sort_keys=True).encode()
        cp.write_bytes(b_)
        (self.b["fixture"]["job"] / "clock.closed.json").write_text(json.dumps(
            {"session": last["session"], "raw_sha256": J.sha(raw), "clock_sha256": J.sha(b_)}))
        with self.assertRaisesRegex(SystemExit, "not the sum of its sessions"):
            X.admit_clock(cp, raw, recs[-1])


class Rev8(Rev7):
    """Codex RSC 12a7f20, reader A and B, across real process exits."""

    def again(self, **env) -> subprocess.CompletedProcess:
        e = {**{k: v for k, v in os.environ.items() if k != "AIRQ_CRASH"}, **env}
        return subprocess.run([sys.executable, str(DRIVER), str(self.root)], capture_output=True, text=True, env=e,
                              timeout=180)

    def clock(self) -> dict:
        return json.loads((self.b["fixture"]["job"] / "clock.json").read_text())

    def test_marker_commit_stall_does_not_qualify(self):
        """Reader A: the marker's commit stalls before its rename, or the rename takes effect but does not return;
        the final deadline fires (exit 75): the tombstone names the session and any marker is removed - the durable
        COMPLETE and the readable closed clock do not qualify."""
        for mode in ("stall_before_rename", "stall_after_rename"):
            with self.subTest(mode):
                p = self.run_env(AIRQ_MARKER_FAIL=mode, AIRQ_FINAL_WRITE_S="4")
                self.assertEqual(p.returncode, 75, p.stderr[-800:])
                recs, _ = self.journal()
                self.assertEqual((recs[-1]["t"], recs[-1]["outcome"]), ("receipt", "COMPLETE"))
                self.assertIsNone(self.clock()["open_session"])
                job = self.b["fixture"]["job"]
                self.assertEqual(json.loads((job / X.CLOSE_TOMBSTONE).read_text())["session"],
                                 self.clock()["sessions"][-1]["session"])
                self.assertFalse((job / X.CLOSED_MARKER).exists())
                with self.assertRaisesRegex(SystemExit, "no closure marker|tombstone"):
                    self.admitted()
        p = self.run_env(AIRQ_FINAL_WRITE_S="4")                          # the control: an ordinary close qualifies
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        self.assertFalse((self.b["fixture"]["job"] / X.CLOSE_TOMBSTONE).exists())
        self.admitted()

    def test_marker_present_beside_its_tombstone_is_refused(self):
        """Reader A: a marker that survives (its removal blocked) beside the tombstone naming its session is refused."""
        p = self.run_env()
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        self.admitted()
        job = self.b["fixture"]["job"]
        mk = json.loads((job / X.CLOSED_MARKER).read_text())
        (job / X.CLOSE_TOMBSTONE).write_text(json.dumps({"session": mk["session"]}))
        with self.assertRaisesRegex(SystemExit, "tombstone"):
            self.admitted()
        (job / X.CLOSE_TOMBSTONE).write_text(json.dumps({"session": "another"}))
        self.admitted()                                                   # another session's tombstone: no effect

    def test_two_failed_starts_then_recovery(self):
        """Reader B: S1 and S2 both die before the clock's first persist; S3 charges BOTH (each start publishes its
        own pending file and none replaces another's)."""
        p = self.run_env(AIRQ_SETUP_S="1.0", AIRQ_SLOW_ACCOUNTING="30")
        self.assertEqual(p.returncode, 75, p.stderr[-800:])
        p = self.again(AIRQ_SETUP_S="1.0", AIRQ_SLOW_ACCOUNTING="30")
        self.assertEqual(p.returncode, 75, p.stderr[-800:])
        ids = sorted(json.loads(x.read_text())["start"] for x in self.pending())
        self.assertEqual(len(ids), 2)
        p = drive(self.root)
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        fs = {x["session"]: x for x in self.clock()["sessions"] if x.get("closed") == "failed_start"}
        self.assertEqual(sorted(fs), ids)
        for x in fs.values():
            self.assertGreater(x["charged_s"], 0.5)
        self.assertEqual(self.pending(), [])
        self.admitted()

    def test_elapsed_setup_is_charged_and_holds_at_the_cap(self):
        """Reader B: with 3 s of the allowance left, the old clock's read takes 5 s: the start HOLDS (no fresh
        allowance), and its pending entry - from the process's own start - charges the whole setup next time."""
        p = self.run_env()
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        used = self.clock()["seconds_total"]
        t = time.time()
        p = self.again(AIRQ_JOB_CLOCK_S=str(used + 3.0), AIRQ_SLOW_CLOCK_READ="5")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("allowance is used up", p.stderr)
        (pp,) = self.pending()
        st = json.loads(pp.read_text())
        self.assertLessEqual(st["start_wall"], t + 1.0)
        p = self.again()
        c = self.clock()
        fs = [x for x in c["sessions"] if x.get("session") == st["start"]]
        self.assertEqual(len(fs), 1, p.stderr[-800:])
        self.assertEqual(fs[0]["closed"], "failed_start")
        self.assertGreaterEqual(fs[0]["charged_s"], 5.0)

    def test_crash_after_first_persist_is_charged_once(self):
        """Reader B: the pending entry and the clock session share one id; a crash after the clock's first persist and
        before the pending file's removal is charged once (as the crashed session), never also as a failed start."""
        p = self.run_env(AIRQ_CRASH="after_clock_persist:1")
        self.assertEqual(p.returncode, 77, p.stderr[-800:])
        (pp,) = self.pending()
        sid = json.loads(pp.read_text())["start"]
        self.assertEqual(self.clock()["open_session"]["session"], sid)
        p = drive(self.root)
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        mine = [x for x in self.clock()["sessions"] if x.get("session") == sid]
        self.assertEqual([x["closed"] for x in mine], ["crashed"])
        self.admitted()

    def test_journal_session_without_its_clock_session_is_refused(self):
        """Reader B: a valid two-session COMPLETE; dropping the earlier (crashed) clock session, the total reduced to
        the sum of the rest and the marker rehashed, is refused - the journal's session has no clock session."""
        self.root = Path(tempfile.mkdtemp(dir=X.ensure_root()))
        self.build({})
        p = drive(self.root, crash="before_begin:1")
        self.assertEqual(p.returncode, 77, p.stderr[-800:])
        p = drive(self.root)
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        self.admitted()
        recs, _ = self.journal()
        opened = [r["session"] for r in recs if r["t"] == "open"]
        self.assertGreaterEqual(len(opened), 2)
        raw = self.b["fixture"]["raw"].read_bytes()
        cp = self.b["fixture"]["job"] / "clock.json"
        c = self.clock()
        keep = [x for x in c["sessions"] if x.get("session") != opened[0]]
        total = sum(x["live_s"] if x.get("closed") not in ("crashed", "failed_start") else x["charged_s"]
                    for x in keep)
        alt = {**c, "sessions": keep, "seconds_total": total}
        b_ = json.dumps(alt, indent=1, sort_keys=True).encode()
        cp.write_bytes(b_)
        (self.b["fixture"]["job"] / X.CLOSED_MARKER).write_text(json.dumps(
            {"session": keep[-1]["session"], "raw_sha256": J.sha(raw), "clock_sha256": J.sha(b_)}))
        with self.assertRaisesRegex(SystemExit, "no clock session that ran"):
            X.admit_clock(cp, raw, recs[-1])
        dup_s = c["sessions"] + [c["sessions"][-1]]               # sum-consistent: only the uniqueness is wrong
        dup = {**c, "sessions": dup_s, "seconds_total": sum(
            x["live_s"] if x.get("closed") not in ("crashed", "failed_start") else x["charged_s"] for x in dup_s)}
        b_ = json.dumps(dup, indent=1, sort_keys=True).encode()
        cp.write_bytes(b_)
        (self.b["fixture"]["job"] / X.CLOSED_MARKER).write_text(json.dumps(
            {"session": c["sessions"][-1]["session"], "raw_sha256": J.sha(raw), "clock_sha256": J.sha(b_)}))
        with self.assertRaisesRegex(SystemExit, "names a session twice"):
            X.admit_clock(cp, raw, recs[-1])


class Rev9(Rev8):
    """Codex RSC 7fdb937, reader A (late return) and B1-B3, across real process exits."""

    def test_late_rename_after_an_early_unlink_does_not_qualify(self):
        """Reader A: the commit is released only after the deadline fired and the revocation's first unlink found no
        marker; the tombstone writer blocks (or not, the control). The late rename is undone (and the revocation keeps
        unlinking until the exit): no marker survives; without a tombstone it is still not admitted."""
        for block in (True, False):
            with self.subTest(tombstone_blocked=block):
                env = {"AIRQ_MARKER_FAIL": "late_release", "AIRQ_FINAL_WRITE_S": "4"}
                if block:
                    env["AIRQ_TOMBSTONE_BLOCK"] = "1"
                p = self.run_env(**env)
                self.assertIn(p.returncode, (75, 1), p.stderr[-800:])
                recs, _ = self.journal()
                self.assertEqual((recs[-1]["t"], recs[-1]["outcome"]), ("receipt", "COMPLETE"))
                job = self.b["fixture"]["job"]
                time.sleep(0.2)
                self.assertFalse((job / X.CLOSED_MARKER).exists(), p.stderr[-800:])
                self.assertEqual((job / X.CLOSE_TOMBSTONE).exists(), not block)
                with self.assertRaisesRegex(SystemExit, "no closure marker|tombstone"):
                    self.admitted()

    def test_readable_incomplete_pending_publication_is_charged(self):
        """Reader B1: the initial pending write's temporary is written and fsynced, the rename never comes, the setup
        timer kills the start; the next start reads that temporary and charges the start."""
        p = self.run_env(AIRQ_PENDING_STALL="1", AIRQ_SETUP_S="1.0")
        self.assertEqual(p.returncode, 75, p.stderr[-800:])
        job = self.b["fixture"]["job"]
        self.assertEqual(self.pending(), [])                              # no completed pending file ...
        (tp,) = sorted(job.glob("clock.starting*.json.tmp"))              # ... only its readable temporary
        sid = json.loads(tp.read_text())["start"]
        p = drive(self.root)
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        fs = [x for x in self.clock()["sessions"] if x.get("session") == sid]
        self.assertEqual([x["closed"] for x in fs], ["failed_start"])
        self.assertGreater(fs[0]["charged_s"], 0.5)
        self.assertEqual(sorted(job.glob("clock.starting*.json.tmp")), [])
        self.admitted()

    def test_near_cap_recovery_bounds_the_blocked_first_persist(self):
        """Reader B2: the saved base leaves ample time, but the recovered open session (live + 30 s tail) leaves about
        3 s; the first persist blocks: the setup bound (20 s here) is shortened to the RECOVERED remainder and the
        process ends within it (exit 75), not at the 20 s setup timer."""
        self.root = Path(tempfile.mkdtemp(dir=X.ensure_root()))
        self.build({})
        p = drive(self.root, crash="before_begin:1")
        self.assertEqual(p.returncode, 77, p.stderr[-800:])
        c = self.clock()
        self.assertIsNotNone(c["open_session"])
        cap = c["seconds_total"] + c["open_session"]["live_s"] + X.TAIL_S + 3.0
        t = time.monotonic()
        p = self.again(AIRQ_JOB_CLOCK_S=str(cap), AIRQ_SETUP_S="20", AIRQ_BLOCK_FIRST_PERSIST="1")
        el = time.monotonic() - t
        self.assertEqual(p.returncode, 75, p.stderr[-800:])
        self.assertLess(el, 12.0)
        self.assertIn("recovered remaining allowance", p.stderr)

    def test_undeclared_closed_state_is_refused(self):
        """Reader B3: a valid two-session COMPLETE; the earlier crashed session rewritten to an undeclared state, the
        total reduced by its tail and the marker rehashed - refused; a crashed session stripped of its tail too."""
        self.root = Path(tempfile.mkdtemp(dir=X.ensure_root()))
        self.build({})
        self.assertEqual(drive(self.root, crash="before_begin:1").returncode, 77)
        self.assertEqual(drive(self.root).returncode, 0)
        self.admitted()
        recs, _ = self.journal()
        raw = self.b["fixture"]["raw"].read_bytes()
        cp = self.b["fixture"]["job"] / "clock.json"
        c = self.clock()
        i = next(k for k, x in enumerate(c["sessions"]) if x.get("closed") == "crashed")
        for name, fn in (("undeclared state", lambda x: {**{k: v for k, v in x.items() if k not in ("charged_s",
                                                                                                  "tail_s")},
                                                       "closed": "resumed"}),
                         ("crashed without its tail", lambda x: {**x, "tail_s": 0.0, "charged_s": x["live_s"]})):
            with self.subTest(name):
                ss = [dict(x) for x in c["sessions"]]
                ss[i] = fn(ss[i])
                total = sum(x["live_s"] if x.get("closed") not in ("crashed", "failed_start") else x["charged_s"]
                            for x in ss)
                b_ = json.dumps({**c, "sessions": ss, "seconds_total": total}, indent=1, sort_keys=True).encode()
                cp.write_bytes(b_)
                (self.b["fixture"]["job"] / X.CLOSED_MARKER).write_text(json.dumps(
                    {"session": ss[-1]["session"], "raw_sha256": J.sha(raw), "clock_sha256": J.sha(b_)}))
                with self.assertRaisesRegex(SystemExit, "undeclared closed state|tail of at least"):
                    X.admit_clock(cp, raw, recs[-1])


class Rev10(Rev9):
    """Codex RSC dda950b, the reader's live foreign start before the lock, across real processes."""

    def test_live_foreign_start_before_the_lock(self):
        """S1 publishes its pending record (final, or only its readable temporary) and stays ALIVE, stalled before
        the task lock, its setup timer healthy (60 s); S2 recovers while S1 lives: it ends S1 by its retained identity,
        confirms the death, charges start -> confirmed end, and only then removes the pending evidence; admitted."""
        for mode in ("final", "temporary"):
            with self.subTest(mode):
                self.root = Path(tempfile.mkdtemp(dir=X.ensure_root()))
                self.build({})
                env = {**{k: v for k, v in os.environ.items() if k != "AIRQ_CRASH"}, "AIRQ_SETUP_S": "60",
                       "AIRQ_LOCK_STALL" if mode == "final" else "AIRQ_PENDING_STALL": "1"}
                s1 = subprocess.Popen([sys.executable, str(DRIVER), str(self.root)], stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL, env=env)
                job = self.b["fixture"]["job"]
                try:
                    pat = "clock.starting.*.json" if mode == "final" else "clock.starting.*.json.tmp"
                    for _ in range(600):
                        got = sorted(job.glob(pat)) if job.exists() else []
                        if got and got[0].stat().st_size:
                            break
                        time.sleep(0.025)
                    time.sleep(0.3)
                    st = json.loads(got[0].read_text())
                    self.assertIsNone(s1.poll())                          # S1 is alive when S2 recovers
                    self.assertTrue(memprobe.same_process(st["process"]))
                    t_rec = time.time()
                    p = drive(self.root)                                  # S2
                    self.assertEqual(p.returncode, 0, p.stderr[-800:])
                    self.assertFalse(memprobe.same_process(st["process"]))   # S1 was ended by identity
                    self.assertEqual(s1.wait(timeout=10), -signal.SIGKILL)
                finally:
                    if s1.poll() is None:
                        s1.kill()
                        s1.wait()
                fs = [x for x in self.clock()["sessions"] if x.get("session") == st["start"]]
                self.assertEqual([x["closed"] for x in fs], ["failed_start"])
                self.assertGreaterEqual(fs[0]["charged_s"], t_rec - st["start_wall"])   # at least to S2's recovery
                self.assertLess(fs[0]["charged_s"], 60.0)                 # the confirmed end, not the 60 s bound
                self.assertEqual(sorted(job.glob("clock.starting*")), [])
                self.admitted()


class Rev11(Rev10):
    """The 2 October run (reader), across a real process: the CLI churns its own arg0 helper during an attempt."""

    def test_job_completes_while_the_cli_churns_its_helpers(self):
        p = self.run_env({"rq1c": ["arg0churn:3:thing"]})
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        recs, _ = self.journal()
        self.assertEqual((recs[-1]["t"], recs[-1]["outcome"]), ("receipt", "COMPLETE"), recs[-1].get("reason"))
        self.admitted()


for _name in [n for n in dir(HardKill) if n.startswith("test_")]:
    setattr(Rev6, _name, None)
    setattr(Rev7, _name, None)
for _name in [n for n in dir(Rev7) if n.startswith("test_")]:
    setattr(Rev8, _name, None)                     # Rev7's (and HardKill's) tests are not collected again
for _name in [n for n in dir(Rev8) if n.startswith("test_")]:
    setattr(Rev9, _name, None)
for _name in [n for n in dir(Rev9) if n.startswith("test_")]:
    setattr(Rev10, _name, None)
for _name in [n for n in dir(Rev10) if n.startswith("test_")]:
    setattr(Rev11, _name, None)
for _name in [n for n in dir(HardKill) if n.startswith("test_")]:
    setattr(Rev5Recovery, _name, None)             # helpers inherited, HardKill's own tests not collected twice

if __name__ == "__main__":
    unittest.main()
