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
        MEASURED["memory_stop"] = {
            "previous_ok_reading_to_kill_s": round(w["stop_killed_mono"] - w["prev_ok_read_mono"], 4),
            "previous_ok_reading_to_leader_dead_s": round(w["stop_leader_dead_mono"] - w["prev_ok_read_mono"], 4),
            "previous_ok_reading_to_verified_extinction_s": round(w["extinction_verified_mono"] -
                                                                  w["prev_ok_read_mono"], 4),
            "deciding_reading_to_leader_dead_s": round(w["stop_leader_dead_mono"] - w["deciding_read_mono"], 4),
            "how": w["how"]}

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

    def test_sampler_unavailable_and_slow(self):
        def gone(pids):
            raise memprobe.Unavailable("test")

        def slow(pids):                                   # over the 50 ms work limit, inside the 150 ms tick staleness
            time.sleep(0.065)
            return memprobe.task_sample(pids)
        for name, s, want in (("unavailable", gone, "unavailable"), ("slow", slow, "took")):
            with self.subTest(name):
                out = new_out()
                final = ctl(out, {"instrumented": "family"},
                            probe=Probe(task_sample=armed(out, s, memprobe.task_sample))).run()
                self.assertEqual(final["outcome"], "STOPPED")
                self.assertIn(want, terminal(out)["first"]["reason"])
                w = rec(out)["workers"][1]
                self.assertIn("stop_observed_mono", w)              # killed by the sampler itself
                self.assertLess(w["stop_leader_dead_s"], 0.5)

    def never_returning_sample(self, nth: int) -> tuple:
        """Stage A 1-2: the instrumented phase's nth sample never returns (in a separate controller process). The
        watchdog's tick check is armed before release, so even the FIRST sample is guarded; a stalled sampler kills
        the worker group AND the controller - no controller outlives its safeguard."""
        out = new_out()
        body = (f"o=Path({str(out)!r})\n"
                "import memprobe, time\n"
                "n={'k':0}\n"
                "def ts(pids):\n"
                "    if ctlr.rec['workers'][-1]['phase'] == 'instrumented':\n"
                "        n['k'] += 1\n"
                f"        if n['k'] == {nth}: time.sleep(10**6)\n"
                "    return memprobe.task_sample(pids)\n"
                "ctlr = T.ctl(o, {'instrumented': 'family'}, probe=T.Probe(task_sample=ts))\n"
                "ctlr.run()\n")
        t = time.monotonic()
        p = subprocess.run(driver(body), capture_output=True, text=True, timeout=120)
        return p, out, time.monotonic() - t

    def test_never_returning_first_and_later_sample(self):
        for nth in (1, 3):
            with self.subTest(nth=nth):
                p, out, el = self.never_returning_sample(nth)
                self.assertEqual(p.returncode, -signal.SIGKILL, p.stderr[-800:])    # the controller is killed
                wd = json.loads(next(out.glob("watchdog_*_instrumented.json")).read_text())
                self.assertIn("sampler stale", wd["reason"])
                self.assertTrue(wd["group_gone"] and wd["controller_killed"])
                if (out / "grandchild.pid").exists():
                    self.assertFalse(alive(int((out / "grandchild.pid").read_text())))
                self.assertLess(el, 30.0)
                src = wd["last_tick_source_mono"]        # the last successful reading the tick reported
                MEASURED.setdefault("never_returning_sample", {})[f"sample_{nth}"] = {
                    "previous_ok_reading_to_tick_consumed_s": round(wd["last_tick_consumed_mono"] - src, 4),
                    "previous_ok_reading_to_watchdog_observation_s": round(wd["observed_mono"] - src, 4),
                    "previous_ok_reading_to_group_extinction_s": round(wd["group_gone_mono"] - src, 4),
                    "previous_ok_reading_to_controller_gone_s": round(wd["controller_gone_mono"] - src, 4)}
                ctl(out, {}).run()                                         # restart: charged the measured tail
                crashed = [x for x in rec(out)["sessions"] if x.get("closed") == "crashed"]
                self.assertGreaterEqual(crashed[0]["tail_s"], C.TAIL_RESERVE_S)

    def test_memory_stop_with_blocked_io_kills_first(self):
        """Stage A 1: the memory stop SIGKILLs the group from the sampler BEFORE any join or persist while the I/O
        thread is blocked forever. Measured end to end by this test, independent of the controller: the last
        admissible observation -> the worker gone."""
        out = new_out()
        body = (f"o=Path({str(out)!r})\n"
                "import time\n"
                "C.MEM_STOP = 768 << 20\n"
                "def w(p,ob,final=False):\n"
                "    ws = ob.get('workers') if isinstance(ob, dict) else None\n"
                "    if ws and ws[-1].get('phase') == 'instrumented' and ws[-1].get('released'): time.sleep(10**6)\n"
                "    write_json_atomic(p,ob,final=final)\n"
                "T.ctl(o, {'instrumented': 'alloc:1'}, writer=w).run()\n")
        p = subprocess.Popen(driver(body), stderr=subprocess.PIPE, text=True)
        try:
            observed = None
            for line in p.stderr:
                if "stop observed at monotonic" in line:
                    observed = float(line.split("monotonic ")[1].split(",")[0])
                    break
            self.assertIsNotNone(observed, "no stop observed")
            pid = [w for w in rec(out)["workers"] if w["phase"] == "instrumented"][0]["pid"]
            while alive(pid) and time.monotonic() - observed < 10:
                time.sleep(0.001)
            gone = time.monotonic() - observed
            self.assertFalse(alive(pid))
            self.assertLess(gone, 0.5)
            MEASURED["memory_stop_blocked_io_observation_to_gone_s"] = round(gone, 4)
        finally:
            p.kill()
            p.wait()
            p.stderr.close()

    def guarded_driver(self, body: str, timeout: float = 120) -> tuple:
        out = new_out()
        t = time.monotonic()
        p = subprocess.run(driver(f"o=Path({str(out)!r})\nimport time, pathlib\n" + body), capture_output=True,
                           text=True, timeout=timeout)
        return p, out, time.monotonic() - t

    def test_directory_stall_before_load_is_guarded(self):
        """Stage A A (c036c00): the output directory's creation blocks forever; the guardian, started before ANY file
        operation, kills the controller at its (shortened) setup deadline."""
        p, out, el = self.guarded_driver(
            "C.SETUP_DEADLINE_S = 2.0\n"
            "real = pathlib.Path.mkdir\n"
            "def mk(self, *a, **k):\n"
            "    if str(self) == str(o): time.sleep(10**6)\n"
            "    return real(self, *a, **k)\n"
            "pathlib.Path.mkdir = mk\n"
            "T.ctl(o, {}).run()\n")
        self.assertEqual(p.returncode, -signal.SIGKILL, p.stderr[-800:])
        g = json.loads(next(out.glob("guardian_*.json")).read_text())
        self.assertTrue(g["controller_killed"])
        self.assertLess(el, 20.0)
        MEASURED["setup_directory_stall_run_s"] = round(el, 3)

    def test_final_output_stall_is_guarded_and_charged(self):
        """Stage A A: the result's output blocks forever after a PASS; the guardian (deadline moved to the end of the
        charged closure at the close) kills the controller; the PASS stays admitted and its closed session's charge
        covers the death."""
        p, out, el = self.guarded_driver(
            "C.FINAL_ALLOWANCE_S, C.REVOKE_TIMEOUT_S, C.EXIT_MARGIN_S = 2.0, 1.0, 1.0\n"
            "C.CLOSE_CHARGE_S = 4.0\n"
            "T.ctl(o, {}).run(emit=lambda r: time.sleep(10**6))\n")
        self.assertEqual(p.returncode, -signal.SIGKILL, p.stderr[-800:])
        g = json.loads(next(out.glob("guardian_*.json")).read_text())
        s_ = rec(out)["sessions"][-1]
        self.assertEqual(s_["allowance_s"], 4.0)
        self.assertLessEqual(g["controller_gone_wall"], s_["guardian_deadline_wall"] + C.HARD_MARGIN_S)
        self.assertEqual(C.final_admitted(out)["outcome"], "PASS")
        MEASURED["final_output_stall_run_s"] = round(el, 3)

    def test_post_close_death_is_inside_the_charged_closure(self):
        """Stage A A: after the close, finalisation blocks and both revocations block; the process ends (bounded abort
        or guardian) and the closed session's charge - the whole closure - covers its death."""
        p, out, el = self.guarded_driver(
            "C.FINAL_ALLOWANCE_S, C.REVOKE_TIMEOUT_S, C.EXIT_MARGIN_S = 2.0, 1.0, 1.0\n"
            "C.CLOSE_CHARGE_S = 4.0\n"
            "C._unlink = lambda q: time.sleep(10**6)\n"
            "def w(q, ob, final=False):\n"
            "    if q.name in ('STAGE_A_FINAL.json', 'STAGE_A_FINAL.ABORTED.json'): time.sleep(10**6)\n"
            "    write_json_atomic(q, ob, final=final)\n"
            "T.ctl(o, {}, writer=w).run()\n")
        died = time.time()
        self.assertIn(p.returncode, (75, -signal.SIGKILL), p.stderr[-800:])
        s_ = rec(out)["sessions"][-1]
        self.assertIsNone(rec(out)["open_session"])
        self.assertLessEqual(died, s_["guardian_deadline_wall"] + C.HARD_MARGIN_S + 2.0)
        self.assertIsNone(C.final_admitted(out))
        MEASURED["post_close_death_run_s"] = round(el, 3)

    def test_guardian_in_the_task_aggregate(self):
        """Stage A B: the guardian is sampled, its final maximum read, and both counted; unreadable -> STOPPED."""
        out = new_out()
        final = ctl(out, {}).run()
        pk = final["peaks"]
        self.assertGreater(pk["guardian_lifetime_max"], 0)
        self.assertGreater(pk["guardian_final"], 0)
        self.assertGreaterEqual(final["task_memory_aggregate"], pk["guardian_final"] + pk["controller_final"])
        c = ctl(new_out(), {})
        real = memprobe.footprint

        def fp(pid):
            if getattr(c, "guard", None) is not None and pid == c.guard.pid:
                raise memprobe.Unavailable("fixture: guardian unreadable")
            return real(pid)
        c.probe = Probe(footprint=fp)
        final = c.run()
        self.assertEqual(final["outcome"], "STOPPED")
        self.assertTrue(any("guardian final" in m for m in final["missing_measurements"]))
        MEASURED["guardian_lifetime_max_mib"] = round(pk["guardian_lifetime_max"] / (1 << 20), 1)

    def test_persistence_after_the_watchdog_retired_is_bounded(self):
        """Stage A 2: a controller-only persist blocks forever after the gates' worker and watchdog are gone; the
        guardian kills the controller at the (shortened) cap + margin; the restart charges until that death."""
        out = new_out()
        cap = CARRY + 1 + 1 + 3 + 8
        body = (f"o=Path({str(out)!r})\n"
                "import time\n"
                "C.TAIL_RESERVE_S, C.STOP_RESERVE_S, C.REPORT_RESERVE_S, C.FINAL_ALLOWANCE_S = 1.0, 1.0, 3.0, 3.0\n"
                "C.CLOSE_CHARGE_S = 5.0\n"
                "def w(p,ob,final=False):\n"
                "    ws = ob.get('workers') if isinstance(ob, dict) else None\n"
                "    if ws and ws[-1].get('phase') == 'gates' and ws[-1].get('reaped'): time.sleep(10**6)\n"
                "    write_json_atomic(p,ob,final=final)\n"
                f"T.ctl(o, {{}}, writer=w, row_cap_s={cap}).run()\n")
        t = time.monotonic()
        p = subprocess.run(driver(body), capture_output=True, text=True, timeout=120)
        el = time.monotonic() - t
        self.assertEqual(p.returncode, -signal.SIGKILL, p.stderr[-800:])
        g = json.loads(next(out.glob("guardian_*.json")).read_text())
        self.assertEqual(g["reason"], "controller deadline")
        self.assertTrue(g["controller_killed"])
        self.assertLess(el, 8 + C.HARD_MARGIN_S + 15)
        MEASURED["guardian_blocked_persist_run_s"] = round(el, 3)
        ctl(out, {}, row_cap_s=cap + 3600).run()
        crashed = [x for x in rec(out)["sessions"] if x.get("closed") == "crashed"]
        self.assertGreaterEqual(crashed[0]["tail_s"], g["controller_gone_wall"] - crashed[0]["beat_wall"] - 1e-6)

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
        # Revision 7: same boot (the beat after kern.boottime) and no recorded controller death - the death evidence
        # is missing or late - so the tail runs until min(now, the guardian's deadline + margin).
        now = time.time()
        for name, dl, recs_, want in (("blocked, guardian deadline passed", now - 20, True, 180.0 + C.EXIT_MARGIN_S),
                                      ("no evidence at all, deadline ahead", now + 1000, False, 200.0)):
            with self.subTest(name):
                o = new_out()
                o.mkdir(parents=True)
                b3 = json.loads(json.dumps(base))
                b3["open_session"].update(beat_wall=now - 200, guardian_deadline_wall=dl)
                (o / "controller.json").write_text(json.dumps(b3))
                if recs_:
                    (o / "wd.json").write_text(json.dumps({"reason": "heartbeat stale (10.2 s)",
                                                           "group_gone_wall": now - 190, "observed_wall": now - 191,
                                                           "controller_gone_wall": None}))
                ctl(o, {}).run()
                crashed = [x for x in rec(o)["sessions"] if x.get("closed") == "crashed"]
                self.assertAlmostEqual(crashed[0]["tail_s"], want, delta=15.0)

    def test_failed_start_is_charged(self):
        """Revision 7: a start that died before its session's first durable record is charged from its pending-start
        record (same boot: until min(now, its setup deadline))."""
        out = new_out()
        self.assertEqual(ctl(out, {}).run()["outcome"], "PASS")
        now = time.time()
        (out / C.STARTING).write_text(json.dumps({"session": "deadstart", "start_wall": now - 40,
                                                  "deadline_wall": now - 40 + C.SETUP_DEADLINE_S}))
        before = rec(out)["seconds_total"]
        ctl(out, {}).run()
        fs = [x for x in rec(out)["sessions"] if x.get("closed") == "failed_start"]
        self.assertEqual(len(fs), 1)
        self.assertAlmostEqual(fs[0]["charged_s"], 40.0, delta=5.0)
        self.assertGreaterEqual(rec(out)["seconds_total"], before + 40.0)
        self.assertFalse((out / C.STARTING).exists())

    def test_pre_pending_stall_is_charged_at_restart(self):
        """Revision 8 (Codex 12a7f20, Stage A A1): the directory creation or the lock blocks before the pending-start
        record exists; the guardian kills the controller and records the start and the death; the next start charges
        that interval (a kill alone is not accounting)."""
        stalls = {"directory": ("real = pathlib.Path.mkdir\n"
                                "def mk(self, *a, **k):\n"
                                "    if str(self) == str(o): time.sleep(10**6)\n"
                                "    return real(self, *a, **k)\n"
                                "pathlib.Path.mkdir = mk\n"),
                  "lock": "import stage_a_guard\nstage_a_guard.TaskLock = lambda d: time.sleep(10**6)\n"}
        for name, patch in stalls.items():
            with self.subTest(name):
                p, out, el = self.guarded_driver("C.SETUP_DEADLINE_S = 2.0\n" + patch + "T.ctl(o, {}).run()\n")
                self.assertEqual(p.returncode, -signal.SIGKILL, p.stderr[-800:])
                self.assertFalse((out / C.STARTING).exists())        # it died before publishing a pending entry
                gp = next(out.glob("guardian_*.json"))
                g = json.loads(gp.read_text())
                self.assertTrue(C._num(g["started_wall"]))
                self.assertEqual(ctl(out, {}).run()["outcome"], "PASS")
                fs = [x for x in rec(out)["sessions"] if x.get("closed") == "failed_start_before_pending"]
                self.assertEqual([x["session"] for x in fs], [gp.stem[len("guardian_"):]])
                self.assertAlmostEqual(fs[0]["charged_s"], g["controller_gone_wall"] - g["started_wall"], delta=1e-6)
                self.assertGreaterEqual(fs[0]["charged_s"], 2.0)
                self.assertGreaterEqual(rec(out)["seconds_total"], CARRY + fs[0]["charged_s"])
                ctl(out, {}).run()                                       # charged once, not again
                self.assertEqual(len([x for x in rec(out)["sessions"]
                                      if x.get("closed") == "failed_start_before_pending"]), 1)
                MEASURED.setdefault("pre_pending_stall_charged_s", {})[name] = round(fs[0]["charged_s"], 3)

    def test_long_first_persist_with_an_existing_clock(self):
        """Revision 8 (Stage A A2): a closed controller.json exists; the next start's first persist blocks before its
        rename after the guardian was moved past the setup deadline. The longer deadline was durable in the pending
        entry first, so the restart charges until the recorded death - and, with the death record missing, until that
        durable deadline + margin (never only the setup interval)."""
        for missing_death in (False, True):
            with self.subTest(missing_death=missing_death):
                out = new_out()
                self.assertEqual(ctl(out, {}).run()["outcome"], "PASS")
                cap = rec(out)["seconds_total"] + 6.0
                body = (f"o=Path({str(out)!r})\nimport time\n"
                        "C.SETUP_DEADLINE_S, C.CLOSE_CHARGE_S = 1.0, 1.0\n"
                        "def w(p, ob, final=False):\n"
                        "    if p.name == 'controller.json':\n"           # this process's FIRST persist: before rename
                        "        time.sleep(10**6)\n"
                        "    write_json_atomic(p, ob, final=final)\n"
                        f"T.ctl(o, {{}}, writer=w, row_cap_s={cap}).run()\n")
                t = time.monotonic()
                p = subprocess.run(driver(body), capture_output=True, text=True, timeout=120)
                el = time.monotonic() - t
                self.assertEqual(p.returncode, -signal.SIGKILL, p.stderr[-800:])
                self.assertGreater(el, 5.0)                               # lived past the 1 s setup deadline
                pend = json.loads((out / C.STARTING).read_text())["pending"]
                mine = pend[-1]
                gp = out / f"guardian_{mine['session']}.json"
                g = json.loads(gp.read_text())
                self.assertGreaterEqual(mine["deadline_wall"] + C.EXIT_MARGIN_S, g["controller_gone_wall"])
                if missing_death:
                    gp.unlink()
                ctl(out, {}, row_cap_s=cap + 3600).run()
                fs = [x for x in rec(out)["sessions"] if x.get("session") == mine["session"]]
                self.assertEqual(len(fs), 1)
                self.assertEqual(fs[0]["closed"], "failed_start")
                self.assertGreaterEqual(fs[0]["charged_s"], g["controller_gone_wall"] - mine["start_wall"] - 1e-6)
                MEASURED.setdefault("long_first_persist_charged_s", {})[f"death_missing_{missing_death}"] = \
                    round(fs[0]["charged_s"], 3)

    def test_two_failures_during_pending_reconciliation(self):
        """Revision 8 (Stage A A3): S1's pending entry exists; S2 reads it, publishes S1 + S2 and dies while
        reconciling (before its first persist); S3 charges BOTH - repeated failed starts never erase startup time."""
        out = new_out()
        self.assertEqual(ctl(out, {}).run()["outcome"], "PASS")
        now = time.time()
        (out / C.STARTING).write_text(json.dumps({"session": "deadstart1", "start_wall": now - 40,
                                                  "deadline_wall": now - 40 + C.SETUP_DEADLINE_S}))
        before = rec(out)["seconds_total"]
        body = (f"o=Path({str(out)!r})\nimport os\n"
                "C.Controller._supersede = lambda self: os._exit(9)\n"     # dies after the load, before the persist
                "T.ctl(o, {}).run()\n")
        p = subprocess.run(driver(body), capture_output=True, text=True, timeout=120)
        self.assertEqual(p.returncode, 9, p.stderr[-800:])
        pend = json.loads((out / C.STARTING).read_text())["pending"]
        self.assertEqual([x["session"] for x in pend][0], "deadstart1")    # S1 survived S2's replacement
        self.assertEqual(rec(out)["seconds_total"], before)                 # nothing was absorbed yet
        s2 = pend[1]["session"]
        ctl(out, {}).run()
        fs = {x["session"]: x for x in rec(out)["sessions"] if x.get("closed") == "failed_start"}
        self.assertEqual(set(fs), {"deadstart1", s2})
        self.assertAlmostEqual(fs["deadstart1"]["charged_s"], 40.0, delta=5.0)
        self.assertGreater(fs[s2]["charged_s"], 0.0)
        self.assertGreaterEqual(rec(out)["seconds_total"], before + 40.0 + fs[s2]["charged_s"] - 1e-6)
        self.assertFalse((out / C.STARTING).exists())

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

    def test_post_marker_stall_and_blocked_revocation_are_bounded(self):
        """Stage A 3: the marker's write stalls after its rename; the allowance fires; revocation (tombstone +
        unlink) is itself bounded - also when the unlink blocks forever - and the process exits 75 in bounded time;
        the session is not admitted either way."""
        for blocked_unlink in (False, True):
            with self.subTest(blocked_unlink=blocked_unlink):
                pre = "C.FINAL_ALLOWANCE_S = 4.0\n" + ("C._unlink = lambda p: time.sleep(10**6)\n"
                                                        if blocked_unlink else "")
                p, out, el = self.run_driver("def w(p,ob,final=False):\n"
                                             "    write_json_atomic(p,ob,final=final)\n"
                                             "    if p.name == 'STAGE_A_FINAL.ADMITTED.json': time.sleep(10**6)\n",
                                             pre="import time\n" + pre)
                self.assertEqual(p.returncode, 75, p.stderr[-800:])
                self.assertLess(el, 4.0 + C.REVOKE_TIMEOUT_S + 20)
                self.assertIsNone(C.final_admitted(out))
                self.assertTrue((out / C.ABORTED).exists())
                self.assertEqual((out / C.ADMITTED).exists(), blocked_unlink)    # the marker survives only here
                MEASURED.setdefault("post_marker_abort_run_s", {})[f"unlink_blocked_{blocked_unlink}"] = round(el, 3)

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
