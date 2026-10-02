"""Controller mechanism fixtures, revision 5 (Codex RSC 1bf9890 A2, A3, A4, A5 and A7; revision 4 answered RSC 081f17b):
real subprocess workers and the real watchdog, synthetic, no model and no development input. Elapsed bounds and durable
records are asserted, not just exit codes. With RECORD_FIXTURES=1 the measured values are written to
stimuli/photo/controller_fixtures.json (the retained mechanism evidence).

    RECORD_FIXTURES=1 .venv-image/bin/python -m unittest discover -s stimuli/photo/tests -p 'test_controller.py' -v
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

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import memprobe  # noqa: E402
import stage_a_controller as C  # noqa: E402

PY = sys.executable
CARRY = 1808.73
MEASURED: dict = {}
OK = {"gates": "gates:ok", "instrumented": "ok:instrumented", "native": "ok:native", "report": "report:ok"}


def ctl(out: Path, modes: dict, **kw) -> C.Controller:
    m = {**OK, **modes}
    return C.Controller(out, carry_seconds=CARRY,
                        worker_cmd=lambda ph: [PY, str(HERE / "fake_worker.py"), str(out), m[ph]],
                        system_reader=kw.pop("system_reader", lambda: {"swap": 0, "pressure": 1}), **kw)


def terminal(out: Path) -> dict | None:
    p = out / "TERMINAL.json"
    return json.loads(p.read_text()) if p.exists() else None


def rec(out: Path) -> dict:
    return json.loads((out / "controller.json").read_text())


def alive(pid: int) -> bool:
    return memprobe.proc_info(pid) is not None


def new_out() -> Path:
    return Path(tempfile.mkdtemp()) / "o"


def worker_log(out: Path) -> list[dict]:
    p = out / "worker_log.jsonl"
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


DRIVER = ("import sys, json; sys.path.insert(0, {photo!r}); sys.path.insert(0, {tests!r})\n"
          "import stage_a_controller as C, test_controller as T\n"
          "from enforce import write_json_atomic\n"
          "from pathlib import Path\n"
          "{body}\n")


def driver(body: str) -> list[str]:
    return [PY, "-c", DRIVER.format(photo=str(HERE.parent), tests=str(HERE), body=body)]


def armed(out: Path, fault, normal):
    """A fault that fires only once the instrumented fake worker is running (marked by grandchild.pid): in the gates
    phase the same fault would be a refusal, which is tested separately."""
    return lambda *a: fault(*a) if (out / "grandchild.pid").exists() else normal(*a)


class Probe:
    """memprobe with selected functions replaced (sampler failure fixtures)."""

    def __init__(self, **over):
        self.over = over

    def __getattr__(self, k):
        return self.over.get(k) or getattr(memprobe, k)


def sleeper_with_child(out: Path, *, leader_exits: bool = False) -> tuple[subprocess.Popen, int]:
    """A process in its own session with a child in ITS group that no record names (an unrecorded member)."""
    code = ("import subprocess, sys, time; c = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)']);"
            f" open({str(out / 'unrecorded.pid')!r}, 'w').write(str(c.pid)); "
            + ("time.sleep(0.3)" if leader_exits else "time.sleep(600)"))
    p = subprocess.Popen([PY, "-c", code], start_new_session=True)
    for _ in range(200):
        if (out / "unrecorded.pid").exists() and (out / "unrecorded.pid").read_text():
            break
        time.sleep(0.02)
    time.sleep(0.1)
    return p, int((out / "unrecorded.pid").read_text())


def crashed_record(workers: list[dict]) -> dict:
    return {"carry_s": CARRY, "seconds_total": CARRY, "sessions": [], "stops": [], "reconciled": [],
            "workers": workers,
            "open_session": {"session": "dead", "pid": 1, "live_s": 1.0, "opened_wall": 0, "beat_wall": 1.0},
            "peaks": {"task_lifetime_sum": 0, "phase_aggregates": {}, "storage_bytes": 0, "max_iteration_s": {}},
            "swap_baseline": 0}


class Controller(unittest.TestCase):
    def setUp(self):
        self.out = new_out()

    def test_pass_sequential_lock_held_and_final_figures(self):
        t = time.monotonic()
        final = ctl(self.out, {}).run()
        self.assertEqual(final["outcome"], "PASS", final)
        log = worker_log(self.out)
        self.assertEqual([l["phase"] for l in log], ["instrumented", "native", "report"])
        self.assertTrue(all(l.get("lock_held_by_controller", True) for l in log))
        r = rec(self.out)
        self.assertEqual([w["phase"] for w in r["workers"]], ["gates", "instrumented", "native", "report"])
        for a, b in zip(r["workers"], r["workers"][1:]):
            self.assertGreaterEqual(b["spawned_total_s"], a["exited_total_s"])   # spawned only after reap
            self.assertTrue(a["reaped"] and a["group_clean"] and a["released"])
            self.assertTrue(memprobe.valid_ident(a["watchdog"]) and memprobe.valid_ident(a["leader"]))
        self.assertIsNone(r["open_session"])
        self.assertGreater(final["task_memory_aggregate"], 0)
        self.assertEqual(final["missing_measurements"], [])
        self.assertNotIn("storage_final_check", final)                         # the fixed point held exactly
        self.assertEqual(final["storage_final"], C.dir_bytes([self.out]))
        self.assertEqual(C.final_admitted(self.out), final)                    # admitted only with its marker
        self.assertGreaterEqual(r["sessions"][-1]["live_s"], C.FINAL_ALLOWANCE_S)   # the allowance is charged
        MEASURED["pass_run_seconds"] = round(time.monotonic() - t, 3)
        MEASURED["max_iteration_work_s"] = r["peaks"]["max_iteration_s"]

    def test_deadline_kills_a_worker_that_ignores_sigterm(self):
        cap = CARRY + C.TAIL_RESERVE_S + C.STOP_RESERVE_S + C.REPORT_RESERVE_S + 4.0
        t = time.monotonic()
        final = ctl(self.out, {"instrumented": "family"}, row_cap_s=cap).run()
        elapsed = time.monotonic() - t
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertIn("time limit", terminal(self.out)["first"]["reason"])
        w = rec(self.out)["workers"][1]
        self.assertEqual(w["how"], "SIGKILL")
        self.assertLessEqual(w["kill_to_reap_s"], 1.0)                       # prompt: no grace
        gpid = int((self.out / "grandchild.pid").read_text())
        self.assertFalse(alive(gpid), "the grandchild outlived the kill of its process group")
        self.assertTrue((self.out / "report/REPORT_RECEIPT.json").exists())  # the STOPPED report still ran
        MEASURED["deadline"] = {"kill_to_reap_s": round(w["kill_to_reap_s"], 3), "how": w["how"],
                                "run_seconds": round(elapsed, 3), "grandchild_killed": not alive(gpid)}

    def test_deadline_kills_a_worker_busy_in_metal(self):
        cap = CARRY + C.TAIL_RESERVE_S + C.STOP_RESERVE_S + C.REPORT_RESERVE_S + 6.0
        final = ctl(self.out, {"instrumented": "mlxblock"}, row_cap_s=cap).run()
        self.assertTrue((self.out / "mlx_started").exists())
        self.assertEqual(final["outcome"], "STOPPED")
        w = rec(self.out)["workers"][1]
        self.assertLessEqual(w["kill_to_reap_s"], 2.0)
        MEASURED["deadline_metal"] = {"kill_to_reap_s": round(w["kill_to_reap_s"], 3), "how": w["how"]}

    def test_memory_stop_is_whole_task(self):
        old = C.MEM_STOP
        C.MEM_STOP = 768 << 20
        try:
            final = ctl(self.out, {"instrumented": "alloc:1"}).run()
        finally:
            C.MEM_STOP = old
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertIn("task memory", terminal(self.out)["first"]["reason"])
        w = rec(self.out)["workers"][1]
        MEASURED["memory_stop"] = {"kill_to_reap_s": round(w["kill_to_reap_s"], 4), "how": w["how"]}

    def test_exit_peak_enters_the_task_aggregate(self):
        final = ctl(self.out, {"instrumented": "spike_exit"}).run()
        w = rec(self.out)["workers"][1]
        self.assertGreaterEqual(w["exit_peak"], 1 << 30)                     # the 1 GiB touched just before exit
        self.assertGreaterEqual(w["member_max"][f"{w['pid']}:{w['leader']['start']}"], 1 << 30)
        self.assertGreaterEqual(final["peaks"]["task_lifetime_sum"], 1 << 30)   # the aggregate, not a side field
        self.assertGreaterEqual(final["task_memory_aggregate"], 1 << 30)
        MEASURED["exit_peak_gib"] = round(w["exit_peak"] / (1 << 30), 3)

    def test_exit_spike_over_the_stop_stops(self):
        old = C.MEM_STOP
        C.MEM_STOP = 768 << 20
        try:
            final = ctl(self.out, {"instrumented": "spike_exit"}).run()
        finally:
            C.MEM_STOP = old
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertIn("task memory", terminal(self.out)["first"]["reason"])

    def test_missing_mandatory_measurements_refuse_pass(self):
        def no_exit_peak(pid):
            raise memprobe.Unavailable("fixture: exit peak unreadable")
        final = ctl(self.out, {}, probe=Probe(exit_peak=no_exit_peak)).run()
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertTrue(final["missing_measurements"])
        self.assertFalse(final["caps_ok_on_final_figures"]["memory"])
        me = os.getpid()

        def no_self(pid):
            if pid == me:
                raise memprobe.Unavailable("fixture: self sample unreadable")
            return memprobe.footprint(pid)
        out = new_out()
        final = ctl(out, {}, probe=Probe(footprint=no_self)).run()
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertTrue(any("controller final" in m for m in final["missing_measurements"]))

    def test_sampler_unavailable_slow_and_blocked(self):
        def gone(pids):
            raise memprobe.Unavailable("test")

        def slow(pids):
            time.sleep(0.7)
            return memprobe.task_sample(pids)
        for name, s, want in (("unavailable", gone, "unavailable"), ("slow", slow, "took")):
            with self.subTest(name):
                out = new_out()
                final = ctl(out, {"instrumented": "family"},
                            probe=Probe(task_sample=armed(out, s, memprobe.task_sample))).run()
                self.assertEqual(final["outcome"], "STOPPED")
                self.assertIn(want, terminal(out)["first"]["reason"])

    def test_hung_sampler_watchdog_kills_on_stale_ticks(self):
        """A sampler that hangs 25 s stops ticking; the watchdog kills the worker's group within TICK_STALE_S of the
        last tick, independent of the controller (whose I/O thread keeps beating)."""
        hang = {"n": 0}

        def blocked(pids):
            hang["n"] += 1
            if hang["n"] == 3:
                time.sleep(25)
            return memprobe.task_sample(pids)
        t = time.monotonic()
        final = ctl(self.out, {"instrumented": "family"},
                    probe=Probe(task_sample=armed(self.out, blocked, memprobe.task_sample))).run()
        self.assertEqual(final["outcome"], "STOPPED")
        wd = json.loads((self.out / f"watchdog_{final['session']}_instrumented.json").read_text())
        self.assertIn("sampler stale", wd["reason"])
        self.assertTrue(wd["group_gone"])
        self.assertIsNone(wd.get("controller_killed"))                      # a sampler stall does not kill it
        gpid = int((self.out / "grandchild.pid").read_text())
        self.assertFalse(alive(gpid))
        self.assertLessEqual(wd["group_gone_wall"] - wd["observed_wall"], 1.0)
        MEASURED["hung_sampler"] = {"observed_to_group_gone_s": round(wd["group_gone_wall"] - wd["observed_wall"], 4),
                                    "tick_stale_s": C.TICK_STALE_S, "run_seconds": round(time.monotonic() - t, 3)}

    def test_initial_resource_failure_is_terminal(self):
        def bad():
            raise C.ControllerStop("sysctl unavailable")
        r = ctl(self.out, {}, system_reader=bad).run()
        self.assertEqual(r["outcome"], "STOPPED")
        self.assertIn("sysctl unavailable", terminal(self.out)["first"]["reason"])
        self.assertEqual(rec(self.out)["workers"], [])                      # nothing was spawned

    def test_worker_crash_and_missing_record(self):
        for mode, want in (("exit:3", "exited 3"), ("norecord", "without its durable phase record")):
            with self.subTest(mode):
                out = new_out()
                final = ctl(out, {"instrumented": mode}).run()
                self.assertEqual(final["outcome"], "STOPPED")
                self.assertIn(want, terminal(out)["first"]["reason"])

    def test_terminal_holds_later_runs_but_report_runs(self):
        ctl(self.out, {"instrumented": "exit:3"}).run()
        first = terminal(self.out)["first"]
        final = ctl(self.out, {}).run()
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertEqual(terminal(self.out)["first"], first)               # the first reason stays first
        self.assertFalse((self.out / "INSTRUMENTED_DONE.json").exists())
        self.assertTrue(final["report_current"])

    def test_refusal_and_authorisation_hold_are_distinct(self):
        out = new_out()
        r = ctl(out, {"gates": "gates:refuse"}).run()
        self.assertEqual(r["outcome"], "REFUSED")
        self.assertEqual([w["phase"] for w in rec(out)["workers"]], ["gates"])
        r = ctl(self.out, {"gates": "gates:hold"}).run()
        self.assertEqual(r["outcome"], "HELD")
        self.assertIsNone(terminal(self.out))                              # a hold is not an integrity failure
        self.assertEqual([w["phase"] for w in rec(self.out)["workers"]], ["gates"])   # no work, no report
        self.assertFalse((self.out / C.FINAL).exists())
        r = ctl(self.out, {}).run()                                          # once authorised, the run resumes
        self.assertEqual(r["outcome"], "PASS")

    def test_leader_exit_with_surviving_child(self):
        final = ctl(self.out, {"instrumented": "orphanchild"}).run()
        child = int((self.out / "child.pid").read_text())
        self.assertFalse(alive(child), "a child survived its leader's exit")
        w = rec(self.out)["workers"][1]
        self.assertTrue(w["group_clean"])
        self.assertIn(str(child), w["members"])                              # sampled as a task member
        self.assertEqual(final["outcome"], "PASS")

    def test_escaped_child_killed_by_identity(self):
        final = ctl(self.out, {"instrumented": "escape"}).run()
        child = int((self.out / "child.pid").read_text())
        self.assertFalse(alive(child), "a member that left the process group survived")
        self.assertIn(str(child), rec(self.out)["workers"][1]["members"])
        self.assertEqual(final["outcome"], "PASS")

    def test_crash_tail_charge(self):
        self.out.mkdir(parents=True)
        base = crashed_record([{"phase": "instrumented", "session": "dead", "pid": 1, "watchdog_record": "wd.json",
                                "leader": {"pid": 999999, "ppid": 1, "pgid": 999999, "start": "1.000000"}}])
        base["seconds_total"] = CARRY + 100.0
        base["open_session"].update(live_s=10.0, beat_wall=1000.0)
        (self.out / "controller.json").write_text(json.dumps(base))
        for ph in ("instrumented", "native"):
            (self.out / f"{ph.upper()}_DONE.json").write_text("{}")
        final = ctl(self.out, {}).run()
        crashed = [s for s in rec(self.out)["sessions"] if s.get("closed") == "crashed"]
        self.assertEqual(crashed[0]["charged_s"], 10.0 + C.TAIL_RESERVE_S)          # no watchdog record: declared
        self.assertGreaterEqual(final["seconds_total"], CARRY + 100.0 + 10.0 + C.TAIL_RESERVE_S)
        out2 = new_out()
        out2.mkdir(parents=True)
        (out2 / "controller.json").write_text(json.dumps(base))
        (out2 / "wd.json").write_text(json.dumps({"reason": "controller died", "group_gone_wall": 1000.0 + 95.0,
                                                  "observed_wall": 1090.0, "controller_gone_wall": 1000.0 + 90.0}))
        ctl(out2, {"instrumented": "ok:instrumented"}).run()
        crashed = [s for s in rec(out2)["sessions"] if s.get("closed") == "crashed"]
        self.assertEqual(crashed[0]["charged_s"], 10.0 + 95.0)                      # the measured, longer tail
        out3 = new_out()                                                             # blocked, never seen to die
        out3.mkdir(parents=True)
        (out3 / "controller.json").write_text(json.dumps(base))
        (out3 / "wd.json").write_text(json.dumps({"reason": "heartbeat stale (10.2 s)", "group_gone_wall": 1015.0,
                                                  "observed_wall": 1011.0, "controller_gone_wall": None}))
        ctl(out3, {}).run()
        crashed = [s for s in rec(out3)["sessions"] if s.get("closed") == "crashed"]
        self.assertGreater(crashed[0]["tail_s"], time.time() - 1000.0 - 60.0)        # charged until the restart

    def test_controller_death_during_active_work(self):
        """SIGKILL the controller while its worker (and grandchild) run: the watchdog kills the group; the next
        controller reconciles by identity, charges the tail and continues."""
        p = subprocess.Popen(driver(f"T.ctl(Path({str(self.out)!r}), {{'instrumented': 'family'}}).run()"))
        for _ in range(200):
            if (self.out / "grandchild.pid").exists():
                break
            time.sleep(0.05)
        time.sleep(0.3)
        r0 = rec(self.out)
        w = r0["workers"][-1]
        gpid = int((self.out / "grandchild.pid").read_text())
        t = time.time()
        p.send_signal(signal.SIGKILL)
        p.wait()
        for _ in range(200):
            if not alive(w["pid"]) and not alive(gpid):
                break
            time.sleep(0.02)
        gone_s = time.time() - t
        self.assertFalse(alive(w["pid"]) or alive(gpid), "the worker or its child outlived the dead controller")
        self.assertLessEqual(gone_s, 2.0)
        for _ in range(100):                                                  # written after the group is gone
            if (self.out / w["watchdog_record"]).exists():
                break
            time.sleep(0.05)
        wd = json.loads((self.out / w["watchdog_record"]).read_text())
        self.assertEqual(wd["reason"], "controller died")
        final = ctl(self.out, {}).run()                                       # restart: reconcile, charge, go on
        crashed = [s for s in rec(self.out)["sessions"] if s.get("closed") == "crashed"]
        self.assertEqual(len(crashed), 1)
        self.assertGreaterEqual(crashed[0]["tail_s"], C.TAIL_RESERVE_S)
        self.assertEqual(final["outcome"], "PASS")
        MEASURED["controller_death"] = {"kill_to_group_gone_s": round(gone_s, 3), "how": wd["how"],
                                        "watchdog_observed_to_gone_s": round(wd["group_gone_wall"] -
                                                                             wd["observed_wall"], 4)}

    def test_stale_worker_reconciled_by_identity_only(self):
        """A recorded worker of a crashed session that is still alive is killed (identity verified); a live process
        whose pid matches a record but whose start time does not is NEVER signalled."""
        self.out.mkdir(parents=True)
        mine = subprocess.Popen([PY, "-c", "import time; time.sleep(600)"], start_new_session=True)
        other = subprocess.Popen([PY, "-c", "import time; time.sleep(600)"], start_new_session=True)
        time.sleep(0.2)
        ident = memprobe.proc_info(mine.pid)
        wrong = {**memprobe.proc_info(other.pid), "start": "1.000000"}
        base = crashed_record([{"phase": "instrumented", "session": "dead", "pid": mine.pid, "leader": ident,
                                "members": {str(other.pid): wrong}}])
        (self.out / "controller.json").write_text(json.dumps(base))
        ctl(self.out, {}).run()
        mine.wait(timeout=5)
        self.assertFalse(alive(mine.pid))
        self.assertTrue(alive(other.pid), "an unidentified process was signalled")
        other.kill()
        other.wait()
        killed = rec(self.out)["reconciled"][0]["groups"][0]["killed"]
        self.assertEqual([k["pid"] for k in killed], [mine.pid])

    def test_immediate_restart_kills_unrecorded_group_members(self):
        """Immediate restart (A2): the crashed worker's leader is alive with a child no record names, and its
        watchdog is alive - the child is found by enumerating the identity-anchored group, everything dies, and the
        watchdog is killed only after the group's verified extinction. Second variant: the leader already exited,
        only the unrecorded child holds the group."""
        for leader_exits in (False, True):
            with self.subTest(leader_exits=leader_exits):
                out = new_out()
                out.mkdir(parents=True)
                lead, child = sleeper_with_child(out, leader_exits=leader_exits)
                ident = memprobe.proc_info(lead.pid) or {"pid": lead.pid, "ppid": os.getpid(), "pgid": lead.pid,
                                                         "start": "0.000000"}
                wdp = subprocess.Popen([PY, "-c", "import time; time.sleep(600)"], start_new_session=True)
                time.sleep(0.1)
                wd = memprobe.proc_info(wdp.pid)
                if leader_exits:
                    lead.wait()                                               # reaped: only the child holds the group
                    self.assertTrue(alive(child))
                base = crashed_record([{"phase": "instrumented", "session": "dead", "pid": lead.pid,
                                        "leader": ident, "members": {}, "watchdog": wd}])
                (out / "controller.json").write_text(json.dumps(base))
                t = time.monotonic()
                ctl(out, {}).run()
                self.assertFalse(alive(child), "an unrecorded member of the crashed group survived the restart")
                self.assertFalse(alive(lead.pid))
                wdp.wait(timeout=5)
                self.assertFalse(alive(wdp.pid))
                r = rec(out)["reconciled"][0]
                self.assertIn(child, [k["pid"] for k in r["groups"][0]["killed"]])
                self.assertEqual(r["watchdogs_killed"][0]["pid"], wdp.pid)
                if not leader_exits:
                    lead.wait(timeout=5)
                MEASURED.setdefault("immediate_restart", {})[f"leader_exited_{leader_exits}"] = round(
                    time.monotonic() - t, 3)

    def test_persistence_failure_is_bounded(self):
        out = new_out()
        body = ("n={'k':0}\n"
                f"o=Path({str(out)!r})\n"
                "def w(p,ob,final=False):\n"
                "    if (o/'grandchild.pid').exists(): n['k']+=1\n"
                "    if n['k']>3: raise OSError('disk full (fixture)')\n"
                "    write_json_atomic(p,ob,final=final)\n"
                "T.ctl(o, {'instrumented': 'family'}, writer=w).run()\n")
        t = time.monotonic()
        p = subprocess.run(driver(body), capture_output=True, text=True, timeout=120)
        elapsed = time.monotonic() - t
        self.assertEqual(p.returncode, 75, p.stderr[-1500:])
        self.assertIn("persistence failure", terminal(out)["first"]["reason"])
        self.assertFalse((out / C.FINAL).exists())
        self.assertLessEqual(elapsed, 20.0)
        MEASURED["persistence_failure_seconds"] = round(elapsed, 3)

    def test_blocked_writer_watchdog_bounds_worker_and_controller(self):
        """The controller's record writer blocks forever: the controller is stuck; the watchdog kills the worker
        group within STALE_S of the last beat and then the blocked controller itself (identity verified)."""
        out = new_out()
        body = ("import time\n"
                f"o=Path({str(out)!r})\n"
                "def w(p,ob,final=False):\n"
                "    if (o/'grandchild.pid').exists(): time.sleep(600)\n"
                "    write_json_atomic(p,ob,final=final)\n"
                "T.ctl(o, {'instrumented': 'family'}, writer=w).run()\n")
        p = subprocess.Popen(driver(body))
        try:
            for _ in range(600):
                if list(out.glob("watchdog_*_instrumented.json")):
                    break
                time.sleep(0.1)
            wds = list(out.glob("watchdog_*_instrumented.json"))
            self.assertTrue(wds, "the watchdog did not act on a blocked controller")
            wd = json.loads(wds[0].read_text())
            self.assertIn("heartbeat stale", wd["reason"])
            self.assertTrue(wd["group_gone"] and wd["controller_killed"])
            self.assertFalse(alive(int((out / "grandchild.pid").read_text())))
            p.wait(timeout=5)
            self.assertEqual(p.returncode, -signal.SIGKILL)
            MEASURED["blocked_writer"] = {"observed_to_group_gone_s": round(wd["group_gone_wall"] - wd["observed_wall"],
                                                                            4),
                                          "observed_to_controller_gone_s": round(wd["controller_gone_wall"] -
                                                                                 wd["observed_wall"], 4)}
        finally:
            if p.poll() is None:
                p.kill()
                p.wait()


class Startup(unittest.TestCase):
    """A2: one cleanup owner from before the first spawn; nothing runs before the safeguard is armed and recorded."""

    def check_unreleased(self, out: Path, final: dict, want: str):
        self.assertIn(final["outcome"], ("STOPPED", "REFUSED"))
        self.assertIn(want, json.dumps(final) + json.dumps(terminal(out) or {}) + json.dumps(rec(out)["stops"]))
        w = [w for w in rec(out)["workers"] if w["phase"] == "instrumented"][0]
        self.assertFalse(w["released"])
        self.assertNotIn("instrumented", [l["phase"] for l in worker_log(out)])     # it ran nothing
        self.assertFalse((out / "INSTRUMENTED_DONE.json").exists())
        if "pid" in w:
            self.assertFalse(alive(w["pid"]))
            self.assertIn(w.get("returncode"), (-signal.SIGKILL, 97))      # killed, or its gate saw EOF: no GO

    def test_exit_watch_failure(self):
        n = {"k": 0}

        def ew(pid):
            n["k"] += 1
            if n["k"] == 2:                                           # the instrumented worker's
                raise OSError("fixture: kqueue registration failed")
            return memprobe.exit_watch(pid)
        out = new_out()
        final = ctl(out, {}, probe=Probe(exit_watch=ew)).run()
        self.check_unreleased(out, final, "kqueue registration failed")

    def test_watchdog_spawn_failure(self):
        out = new_out()
        real = str(HERE.parent / "stage_a_watchdog.py")
        cmd = [PY, "-c", "import sys, json, os; a = json.loads(sys.argv[1]); "
                         "sys.exit(5) if 'instrumented' in a['record'] else "
                         f"os.execv(sys.executable, [sys.executable, {real!r}, sys.argv[1]])"]
        final = ctl(out, {}, watchdog_cmd=cmd).run()
        self.check_unreleased(out, final, "did not arm")

    def test_first_persist_failure(self):
        out = new_out()
        body = ("n={'k':0}\n"
                f"o=Path({str(out)!r})\n"
                "def w(p,ob,final=False):\n"
                "    ws = ob.get('workers') if isinstance(ob, dict) else None\n"
                "    if ws and ws[-1].get('phase') == 'instrumented' and not ws[-1].get('released') and n['k'] == 0:\n"
                "        n['k'] = 1\n"
                "        raise OSError('first persist fails (fixture)')\n"
                "    write_json_atomic(p,ob,final=final)\n"
                "print(json.dumps(T.ctl(o, {}, writer=w).run()))\n")
        p = subprocess.run(driver(body), capture_output=True, text=True, timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr[-1500:])
        final = json.loads(p.stdout.strip().splitlines()[-1])
        self.check_unreleased(out, final, "first persist fails")

    def test_stale_handles_never_survive_into_the_next_phase(self):
        """A worker handle left by a failed phase is ended (whole group, reaped) before the next phase spawns."""
        out = new_out()
        c = ctl(out, {"instrumented": "exit:3"})
        real = c._phase

        def phase(ph, **kw):
            if ph == "report" and c.proc is None:
                c.proc = subprocess.Popen([PY, "-c", "import time; time.sleep(600)"], stdin=subprocess.PIPE,
                                          start_new_session=True)       # a leftover handle
                c.rec["workers"].append({"phase": "leftover", "session": c.session, "pid": c.proc.pid,
                                         "leader": memprobe.proc_info(c.proc.pid), "members": {}})
                c._exited_flag, c.kq = False, memprobe.exit_watch(c.proc.pid)
                c.leftover = c.proc.pid
            return real(ph, **kw)
        c._phase = phase
        c.run()
        self.assertFalse(alive(c.leftover))
        lw = [w for w in rec(out)["workers"] if w["phase"] == "leftover"][0]
        self.assertTrue(lw["reaped"] and lw["group_clean"])


class Finalisation(unittest.TestCase):
    """A5 and A7 on the controller: the strict current receipt, superseded PASS, final cap and counter edges, the
    completion marker and lost accounting."""

    def test_report_failure_modes_prevent_pass(self):
        for how in ("json_then_fail", "bad_receipt", "other_session", "fail", "trimmed", "extra_key",
                    "flag_mismatch"):
            with self.subTest(how):
                out = new_out()
                final = ctl(out, {"report": f"report:{how}"}).run()
                self.assertEqual(final["outcome"], "STOPPED", how)
                self.assertFalse(final["report_current"])

    def test_stale_pass_superseded(self):
        out = new_out()
        self.assertEqual(ctl(out, {}).run()["outcome"], "PASS")
        final = ctl(out, {"report": "report:json_then_fail"}).run()          # an old PASS JSON is on disk
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertTrue(list((out / "superseded").glob("STAGE_A_FINAL.*.json")))
        self.assertTrue(list((out / "superseded").glob("STAGE_A_FINAL.ADMITTED.*.json")))
        self.assertEqual(json.loads((out / C.FINAL).read_text())["outcome"], "STOPPED")
        self.assertEqual(C.final_admitted(out)["outcome"], "STOPPED")

    def test_over_limit_and_illegal_ledger(self):
        out = new_out()
        self.assertEqual(ctl(out, {}).run()["outcome"], "PASS")
        st = {"counters": {"row20": {"started": 201, "completed": 201, "failed": 0, "passes": 201},
                           "row21": {"started": 0, "completed": 0, "failed": 0, "passes": 0},
                           "aggregate": {"started": 201, "completed": 201, "failed": 0, "passes": 201}},
              "completed": {}, "attempts": {}, "carry_in": {"row20": {"completed": 201}}, "open_attempt": None,
              "interrupted": [], "recoveries_consumed": []}
        (out / "stage_a_state.json").write_text(json.dumps(st))
        final = ctl(out, {}).run()
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertFalse(final["caps_ok_on_final_figures"]["attempts"])

    def test_lost_and_invalid_accounting_refused(self):
        out = new_out()
        out.mkdir(parents=True)
        (out / "stage_a_state.json").write_text("{}")
        with self.assertRaisesRegex(SystemExit, "accumulated time is lost"):
            ctl(out, {}).run()
        for bad in ({"seconds_total": float("nan")}, {"seconds_total": -5.0}, {"carry_s": 0.0},
                    {"sessions": [{"live_s": "x"}]}):
            with self.subTest(str(bad)):
                out = new_out()
                self.assertEqual(ctl(out, {}).run()["outcome"], "PASS")
                r = {**rec(out), **bad}
                (out / "controller.json").write_text(json.dumps(r))
                with self.assertRaisesRegex(SystemExit, "accounting invalid"):
                    ctl(out, {}).run()

    def test_time_exhausted_spawns_no_work(self):
        out = new_out()
        r = ctl(out, {}, row_cap_s=CARRY + C.TAIL_RESERVE_S + C.STOP_RESERVE_S + C.REPORT_RESERVE_S - 1.0).run()
        self.assertEqual(r["outcome"], "REFUSED")                              # the gates already meet the line
        self.assertIn("time limit", r["reason"])
        self.assertFalse((out / "INSTRUMENTED_DONE.json").exists())

    def test_storage_cap_edges(self):
        out = new_out()
        cap = C.FINAL_RESERVE_BYTES + (4 << 20)
        final = ctl(out, {"instrumented": f"fill:{5 << 20}"}, storage_cap=cap).run()
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertIn("storage", terminal(out)["first"]["reason"])

    def run_driver(self, writer_body: str, pre: str = "") -> tuple[subprocess.CompletedProcess, Path, float]:
        out = new_out()
        body = (pre + f"o=Path({str(out)!r})\n" + "import time, os\n" + writer_body +
                "print(json.dumps(T.ctl(o, {}, writer=w).run()))\n")
        t = time.monotonic()
        p = subprocess.run(driver(body), capture_output=True, text=True, timeout=180)
        return p, out, time.monotonic() - t

    def test_failed_final_write_leaves_no_pass(self):
        p, out, _ = self.run_driver("def w(p,ob,final=False):\n"
                                    "    if p.name == 'STAGE_A_FINAL.json': raise OSError('final write fails')\n"
                                    "    write_json_atomic(p,ob,final=final)\n")
        self.assertEqual(p.returncode, 75, p.stderr[-800:])
        self.assertFalse((out / C.FINAL).exists())
        self.assertIsNone(C.final_admitted(out))

    def test_post_rename_failure_is_not_admitted(self):
        p, out, _ = self.run_driver("def w(p,ob,final=False):\n"
                                    "    write_json_atomic(p,ob,final=final)\n"
                                    "    if p.name == 'STAGE_A_FINAL.json': raise OSError('after the rename')\n")
        self.assertEqual(p.returncode, 75, p.stderr[-800:])
        self.assertEqual(json.loads((out / C.FINAL).read_text())["outcome"], "PASS")   # the bytes say PASS ...
        self.assertIsNone(C.final_admitted(out))                                     # ... and are not admitted

    def test_post_rename_block_is_bounded_and_not_admitted(self):
        p, out, el = self.run_driver("def w(p,ob,final=False):\n"
                                     "    write_json_atomic(p,ob,final=final)\n"
                                     "    if p.name == 'STAGE_A_FINAL.json': time.sleep(600)\n",
                                     pre="C.FINAL_ALLOWANCE_S = 4.0\n")
        self.assertEqual(p.returncode, 75, p.stderr[-800:])
        self.assertIsNone(C.final_admitted(out))
        self.assertLess(el, 60.0)
        MEASURED["post_rename_block_run_seconds"] = round(el, 3)

    def test_marker_failure_after_its_rename_unadmits(self):
        p, out, _ = self.run_driver("def w(p,ob,final=False):\n"
                                    "    write_json_atomic(p,ob,final=final)\n"
                                    "    if p.name == 'STAGE_A_FINAL.ADMITTED.json': raise OSError('marker fsync')\n")
        self.assertEqual(p.returncode, 75, p.stderr[-800:])
        self.assertFalse((out / C.ADMITTED).exists())
        self.assertIsNone(C.final_admitted(out))

    def test_size_mismatch_invalidates_completion(self):
        p, out, _ = self.run_driver("def w(p,ob,final=False):\n"
                                    "    write_json_atomic(p,ob,final=final)\n"
                                    "    if p.name == 'STAGE_A_FINAL.json': (o / 'stray.bin').write_bytes(b'x' * 100)\n")
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        final = json.loads(p.stdout.strip().splitlines()[-1])
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertIn("storage_final_check", final)
        self.assertEqual(json.loads((out / C.FINAL).read_text())["outcome"], "STOPPED")
        self.assertIsNone(C.final_admitted(out))


def tearDownModule():
    if os.environ.get("RECORD_FIXTURES") == "1":
        rec_ = {"recorded": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "python": sys.version.split()[0],
                "measured": MEASURED, "memory_fixture": memprobe.fixture(PY),
                "note": "synthetic workers and the real watchdog, no model, no development input"}
        (HERE.parent / "controller_fixtures.json").write_text(json.dumps(rec_, indent=1) + "\n")


if __name__ == "__main__":
    unittest.main()
