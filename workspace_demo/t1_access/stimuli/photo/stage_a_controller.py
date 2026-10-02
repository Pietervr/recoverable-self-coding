"""Photograph arm, Stage A (row 20): the INDEPENDENT CONTROLLER - revision 4, Codex RSC 081f17b closure groups 2, 3, 4
and 6. A separate process that owns the task lock, the clock, the resource limits, termination and reaping; every
phase - the desk gates included - runs as a WORKER subprocess it spawns, watches from outside and reaps, with a
WATCHDOG process (stage_a_watchdog.py) beside it that the worker cannot stop and a blocked controller cannot delay.

    .venv-image/bin/python stimuli/photo/stage_a_controller.py run      # gates -> instrumented -> native -> report

ORDER: lock (held until the controller exits) -> load the durable record; if the last controller died, RECONCILE its
workers by verified identity (pid + start time: leader, every recorded member, its watchdog) - kill and confirm gone,
never signalling an unidentified process - and charge its tail -> supersede any earlier STAGE_A_FINAL.json and report
receipt -> open the session -> the GATES worker (go/attestation/package, fresh execution identity, positions receipt,
crash reconciliation of an open attempt, recovery files) -> per work phase: spawn, watch, final peak, whole-group
cleanup, reap, verify its phase record -> the report worker (always, also after a stop; never after a refusal or a
hold) -> close -> finalise.

OUTCOMES. REFUSED: the gates refused (package, go, identity, receipt) - nothing else was spawned. HELD: an interrupted
try lacks the owner's recovery file - an AUTHORISATION HOLD, distinct from an integrity failure: no TERMINAL record, no
work, no report; the run resumes once the file exists. STOPPED / PASS: from STAGE_A_FINAL.json (below).

CLOCK. Row 20's time = carried 1,808.73 s + every session's live monotonic seconds, written durably every
HEARTBEAT_S = 1 s together with the wall time of that beat. A controller that dies is charged at restart with its last
durable live time plus its tail: max(TAIL_RESERVE_S = 60 s, the interval its watchdog measured from the last beat to
the worker group's death). The bound behind the 60 s (fixtures, controller_fixtures.json): the watchdog kills the
worker group within STALE_S = 10 s of the last beat if the controller is alive but blocked, and within its 0.1 s poll
of the controller's death otherwise, plus TERM_GRACE_S = 3 s and the measured reap. RESERVES INSIDE THE 4 h CAP:
TAIL 60 s, STOP 60 s, REPORT 600 s; work phases end at cap - 720 s, the report at cap - 60 s; the watchdog's hard
deadline is HARD_MARGIN_S = 5 s after the controller's. Caps are never reset.

OBSERVATION. Each loop iteration (sleep MEM_SAMPLE_S = 0.1 s): the worker's exit (kqueue, which does NOT reap), the
deadline, the watchdog's liveness, the task's processes and their memory, every SYS_SAMPLE_S = 1 s swap, pressure
(sysctlbyname, in-process) and storage, every HEARTBEAT_S the durable record. The full iteration time is measured and
its maximum recorded per phase (`max_iteration_s`); a sample slower than SAMPLE_LIMIT_S = 0.5 s stops.

WHOLE-TASK MEMORY (group 3). The task = the controller itself, the watchdog, the worker and every process in the
worker's group or descended from it (memprobe.task_processes); the measure is the SUM of their lifetime maxima
(ri_lifetime_max_phys_footprint per task, which per Apple's XNU covers one task only; the sum bounds the
simultaneous peak from above). It is sampled through the gates, load, execution and the report; at a worker's exit the
leader's final lifetime maximum is read from the exited, unreaped process (exit_peak) BEFORE the reap; the controller
samples itself again at finalisation. Stop at MEM_STOP = 44 GiB; a reading that fails, is implausible (lifetime <
current, or zero) or is slower than the limit stops. The MLX free-buffer cache is covered: a nonzero 2 GiB cache is
counted in the ledger (memprobe fixture).

STORAGE (group 4). Every writer reserves (enforce.configure_storage): work writes under cap - 64 MiB, finalisation
writes (state, terminal, phase records, parity, report, controller, gates, final) under the full cap; the controller
sums the output tree every SYS_SAMPLE_S and stops a work phase over its operational limit. STAGE_A_FINAL.json's
storage figure includes its own bytes (a fixed point checked after the write).

STOP. Any limit, sampler failure, worker crash, non-zero exit, watchdog loss or persistence failure -> TERMINAL.json
(first reason kept) -> SIGTERM to the worker's group -> TERM_GRACE_S -> the leader's final peak -> SIGKILL to the
group -> every recorded member confirmed gone by identity -> reap. A write failure of the controller or terminal
record exits 75 after the kill; no PASS can exist then (the previous FINAL was superseded at session start).

FINAL (group 6). PASS only if, in THIS session, the report worker exited 0, wrote report/REPORT_RECEIPT.json last
naming this session, the gates' package and identity and the sha256 of every report output, every one of which
matches on disk; its validator passed and it was admissible; no TERMINAL record; and every cap holds on the final
figures - time, storage (including the final record), whole-task memory, and the attempt counters per row and in
aggregate, re-read from the ledger. The Stage B prediction is recomputed here from the completed A seconds and bytes.
"""

from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import memprobe  # noqa: E402
from enforce import (CAPS, MEMORY_CAP as CAPS_MEMORY, GiB, MiB, configure_storage, dir_bytes,  # noqa: E402
                     write_json_atomic)

HEARTBEAT_S, MEM_SAMPLE_S, SYS_SAMPLE_S, SAMPLE_LIMIT_S = 1.0, 0.1, 1.0, 0.5
TAIL_RESERVE_S, STOP_RESERVE_S, REPORT_RESERVE_S, TERM_GRACE_S = 60.0, 60.0, 600.0, 3.0
STALE_S, HARD_MARGIN_S, GROUP_GONE_S, FINAL_WRITE_TIMEOUT_S = 10.0, 5.0, 10.0, 30.0
MEM_STOP = 44 * GiB
FINAL_RESERVE_BYTES = 64 * MiB
PHASES = ["instrumented", "native"]
B_PLANNED_ATTEMPTS, B_RESERVE = 1856, 1.25
EXIT_HOLD = 4


class ControllerStop(RuntimeError):
    pass


def _sha_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def default_system_reader() -> dict:
    try:
        return {"swap": memprobe.swap_used(), "pressure": memprobe.pressure_level()}
    except memprobe.Unavailable as exc:
        raise ControllerStop(str(exc)) from exc


class Controller:
    def __init__(self, out: Path, *, carry_seconds: float, worker_cmd, gates: bool = True,
                 row_cap_s: float | None = None, storage_cap: int | None = None, probe=memprobe,
                 system_reader=None, writer=write_json_atomic, clock=time.monotonic, watchdog: bool = True):
        self.out, self.worker_cmd, self.use_gates = Path(out), worker_cmd, gates
        self.cap_s = row_cap_s if row_cap_s is not None else CAPS["row20"]["seconds"]
        self.cap_b = storage_cap if storage_cap is not None else CAPS["row20"]["bytes"]
        self.carry, self.probe, self.writer, self.clock = carry_seconds, probe, writer, clock
        self.system_reader = system_reader or default_system_reader
        self.use_watchdog = watchdog
        self.path = self.out / "controller.json"
        self.session = uuid.uuid4().hex[:12]
        self.proc = self.wd = None
        self._exited_flag = False
        self.gates_rec = None

    # ---- the durable record ---------------------------------------------------------------------------------------
    def _write(self, path: Path, obj) -> None:
        self.writer(path, obj, final=True)

    def _load(self) -> dict:
        if not self.path.exists():
            return {"carry_s": self.carry, "seconds_total": self.carry, "sessions": [], "open_session": None,
                    "peaks": {"task_lifetime_sum": 0, "by_phase": {}, "storage_bytes": 0, "max_iteration_s": {}},
                    "stops": [], "workers": [], "swap_baseline": None, "reconciled": []}
        rec = json.loads(self.path.read_text())
        s = rec.get("open_session")
        if s:                                         # the last controller died
            rec["reconciled"].append(self._reconcile(rec, s["session"]))
            tail, wd = TAIL_RESERVE_S, None
            for w in rec["workers"]:
                if w.get("session") == s["session"] and w.get("watchdog_record"):
                    p = self.out / w["watchdog_record"]
                    if p.exists():
                        wd = json.loads(p.read_text())
                        if wd.get("group_gone_wall") and s.get("beat_wall"):
                            tail = max(tail, wd["group_gone_wall"] - s["beat_wall"])
            charged = float(s["live_s"]) + tail
            rec["seconds_total"] += charged
            rec["sessions"].append({**s, "closed": "crashed", "charged_s": charged, "tail_s": tail,
                                    "watchdog": wd})
            rec["open_session"] = None
        return rec

    def _reconcile(self, rec: dict, session: str) -> dict:
        """Kill and confirm gone every still-live process of the crashed session's workers, identified by pid AND
        start time (leader, recorded members, watchdog). An unidentified process is never signalled."""
        out = {"session": session, "killed": [], "already_gone": 0}
        idents = []
        for w in rec["workers"]:
            if w.get("session") != session or w.get("reaped"):
                continue
            idents += [i for i in [w.get("leader"), w.get("watchdog")] + list((w.get("members") or {}).values())
                       if i]
        live = [i for i in idents if memprobe.same_process(i)]
        out["already_gone"] = len(idents) - len(live)
        for i in live:
            try:
                os.kill(i["pid"], signal.SIGKILL)
                out["killed"].append(i)
            except ProcessLookupError:
                pass
        t = time.monotonic()
        while any(memprobe.same_process(i) for i in live):
            if time.monotonic() - t > GROUP_GONE_S:
                raise SystemExit(f"refused: processes of the crashed session {session} survive SIGKILL: "
                                 f"{[i for i in live if memprobe.same_process(i)]}; the run holds")
            time.sleep(0.05)
        return out

    def _persist(self) -> None:
        live = self.clock() - self.t0
        self.rec["open_session"]["live_s"] = live
        self.rec["open_session"]["beat_wall"] = time.time()
        self.rec["seconds_total_live"] = self.base + live
        try:
            self._write(self.path, self.rec)
        except Exception as exc:
            raise ControllerStop(f"persistence failure: {exc!r}") from exc

    def elapsed_total(self) -> float:
        return self.base + (self.clock() - self.t0)

    def _supersede(self) -> None:
        """No earlier PASS survives into this session: the previous final record and report receipt move aside."""
        sup = self.out / "superseded"
        for p in (self.out / "STAGE_A_FINAL.json", self.out / "report" / "REPORT_RECEIPT.json"):
            if p.exists():
                sup.mkdir(exist_ok=True)
                os.replace(p, sup / f"{p.stem}.{self.session}{p.suffix}")

    # ---- the run --------------------------------------------------------------------------------------------------
    def run(self, phases=PHASES) -> dict:
        from stage_a_guard import TaskLock, set_terminal
        self.out.mkdir(parents=True, exist_ok=True)
        lock = TaskLock(self.out)
        try:
            configure_storage([self.out], self.cap_b, self.cap_b - FINAL_RESERVE_BYTES)
            self.rec = self._load()
            self._supersede()
            self.base = self.rec["seconds_total"]
            self.t0 = self.clock()
            self.rec["open_session"] = {"session": self.session, "pid": os.getpid(), "live_s": 0.0,
                                        "opened_wall": time.time(), "beat_wall": time.time()}
            self._persist()
            if self.rec["swap_baseline"] is None:
                try:
                    self.rec["swap_baseline"] = self.system_reader()["swap"]
                except Exception as exc:              # no observation, no work: terminal, nothing spawned
                    self._stop(set_terminal, "controller", f"initial system reading failed: {exc}")
                    self._close("terminal")
                    return {"outcome": "STOPPED", "reason": "initial system reading failed", "session": self.session}
            if self.use_gates:
                g = self._gates()
                if g["outcome"] != "PASSED":
                    self._close(g["outcome"].lower())
                    return {"outcome": g["outcome"], "reason": g["reason"], "session": self.session}
            terminal = (self.out / "TERMINAL.json").exists()
            try:
                if not terminal:
                    for ph in phases:
                        if (self.out / f"{ph.upper()}_DONE.json").exists():
                            continue
                        self._phase(ph, deadline=self.cap_s - TAIL_RESERVE_S - STOP_RESERVE_S - REPORT_RESERVE_S,
                                    storage_limit=self.cap_b - FINAL_RESERVE_BYTES)
            except (ControllerStop, Exception) as exc:
                self._stop(set_terminal, "controller", f"{type(exc).__name__}: {exc}")
            try:                                       # the report: always, inside its reserve (STOPPED after a stop)
                self._phase("report", deadline=self.cap_s - TAIL_RESERVE_S, storage_limit=self.cap_b, report=True)
            except Exception as exc:
                self.rec["stops"].append({"phase": "report", "session": self.session,
                                          "reason": f"{type(exc).__name__}: {exc}"})
            self._close("terminal" if (self.out / "TERMINAL.json").exists() else "completed")
            return self._finalise()
        finally:
            lock.release()

    def _gates(self) -> dict:
        """The desk gates as a supervised worker (hashing and git cannot block the controller's loop)."""
        gp = self.out / "GATES.json"
        if gp.exists():
            os.replace(gp, self.out / f"GATES.prev.json")
        try:
            self._phase("gates", deadline=self.cap_s - TAIL_RESERVE_S - STOP_RESERVE_S - REPORT_RESERVE_S,
                        storage_limit=self.cap_b - FINAL_RESERVE_BYTES, gates=True)
        except ControllerStop as exc:
            w = self.rec["workers"][-1]
            if w.get("returncode") == EXIT_HOLD and gp.exists():
                g = json.loads(gp.read_text())
                if g.get("session") == self.session and g.get("hold"):
                    self.gates_rec = g
                    return {"outcome": "HELD", "reason": g["hold_reason"]}
            return {"outcome": "REFUSED", "reason": str(exc)}
        g = json.loads(gp.read_text()) if gp.exists() else {}
        if g.get("session") != self.session or g.get("passed") is not True:
            return {"outcome": "REFUSED", "reason": "the gates worker exited 0 without a passing record for this "
                                                    "session"}
        self.gates_rec = g
        return {"outcome": "PASSED", "reason": ""}

    def _close(self, outcome: str) -> None:
        self._self_sample()
        live = self.clock() - self.t0
        s = dict(self.rec["open_session"], live_s=live, closed=outcome)
        self.rec["sessions"].append(s)
        self.rec["seconds_total"] = self.base + live
        self.rec["open_session"] = None
        self.rec["storage_before_close"] = dir_bytes([self.out])
        try:
            self._write(self.path, self.rec)
        except Exception:
            os._exit(75)

    def _self_sample(self) -> None:
        try:
            f = self.probe.footprint(os.getpid())
        except memprobe.Unavailable:
            return
        pk = self.rec["peaks"]
        pk["controller_lifetime_max"] = max(pk.get("controller_lifetime_max", 0), f["lifetime_max"])

    # ---- final (group 6) ------------------------------------------------------------------------------------------
    def _report_ok(self) -> dict:
        """The CURRENT report: worker of this session exited 0, no report stop this session, a receipt naming this
        session and the gates' package/identity, every listed output present with its sha256."""
        why = []
        ws = [w for w in self.rec["workers"] if w.get("session") == self.session and w["phase"] == "report"]
        if not ws or ws[-1].get("returncode") != 0 or ws[-1].get("stop"):
            why.append("the report worker of this session did not exit 0")
        if any(s.get("phase") == "report" and s.get("session") == self.session for s in self.rec["stops"]):
            why.append("a report stop in this session")
        rp = self.out / "report" / "REPORT_RECEIPT.json"
        rc = json.loads(rp.read_text()) if rp.exists() else None
        if rc is None:
            why.append("no report receipt")
        else:
            g = self.gates_rec or {}
            if rc.get("session") != self.session:
                why.append("the report receipt names another session")
            if self.use_gates and (rc.get("package") != g.get("package") or rc.get("identity") != g.get("identity")):
                why.append("the report receipt's package or identity differs from this session's gates")
            for rel, h in (rc.get("outputs") or {}).items():
                p = self.out / rel
                if not p.exists() or _sha_file(p) != h:
                    why.append(f"report output {rel} missing or changed")
            if "report/stage_a_report.json" not in (rc.get("outputs") or {}):
                why.append("the receipt does not bind the machine report")
        rep = json.loads((self.out / "report/stage_a_report.json").read_text()) if not why else {}
        return {"ok": not why, "why": why, "receipt": rc, "report": rep}

    def _counters_ok(self) -> dict:
        st = json.loads((self.out / "stage_a_state.json").read_text()) if (self.out / "stage_a_state.json").exists() \
            else None
        if st is None:
            return {"ok": True, "detail": "no attempts"}
        c, caps = st["counters"], CAPS
        checks = {}
        for key in ("row20", "aggregate"):
            k = c[key]
            checks[key] = (k["passes"] <= caps[key]["attempts"] and k["started"] <= caps[key]["attempts"] and
                           k["started"] == k["completed"] + k["failed"] + (1 if st.get("open_attempt") else 0) and
                           k["passes"] >= k["started"])
        checks["completed_ids"] = len(st["completed"]) + st["carry_in"].get("row20", {}).get("completed", 0) == \
            c["row20"]["completed"]
        return {"ok": all(checks.values()), "detail": checks}

    def _finalise(self) -> dict:
        rok = self._report_ok()
        rep = rok["report"]
        terminal = (self.out / "TERMINAL.json").exists()
        cnt = self._counters_ok()
        st = json.loads((self.out / "stage_a_state.json").read_text()) if (self.out / "stage_a_state.json").exists() \
            else {"attempts": {}}
        mem_peak = self.rec["peaks"]["task_lifetime_sum"]
        final = {"outcome": "STOPPED", "session": self.session, "report_current": rok["ok"],
                 "report_problems": rok["why"], "validator_pass": bool(rep.get("validator_pass")),
                 "admissible": bool(rep.get("admissible")), "terminal": terminal, "counters": cnt,
                 "seconds_total": self.rec["seconds_total"], "carry_s": self.rec["carry_s"],
                 "stage_a_seconds": self.rec["seconds_total"] - self.rec["carry_s"],
                 "peaks": self.rec["peaks"], "report_receipt_sha256": _sha_file(self.out / "report/REPORT_RECEIPT.json")
                 if rok["receipt"] is not None else None,
                 "controller_sha256": _sha_file(self.path), "stops": self.rec["stops"],
                 "time_scope": "seconds_total ends at the close of this session's record; the final record's own "
                               "write (measured in the fixtures) lies inside the 60 s tail reserve within the cap"}
        unique = sum(1 for _ in st.get("attempts", {}))
        final["stage_b_prediction"] = None
        size0 = dir_bytes([self.out])
        for _ in range(4):                            # a fixed point: the figure includes this record's own bytes
            final["storage_final"] = size0 + len(json.dumps(final, indent=1, sort_keys=True).encode())
            if unique:
                ps = final["stage_a_seconds"] / unique * B_PLANNED_ATTEMPTS
                pb = final["storage_final"] / unique * B_PLANNED_ATTEMPTS
                cap21 = CAPS["row21"]
                final["stage_b_prediction"] = {
                    "unique_attempts": unique, "seconds_per_unique_attempt": final["stage_a_seconds"] / unique,
                    "bytes_per_unique_attempt": final["storage_final"] / unique, "predicted_seconds": ps,
                    "predicted_bytes": pb, "limit_seconds": cap21["seconds"] / B_RESERVE,
                    "limit_bytes": cap21["bytes"] / B_RESERVE, "time_ok": ps <= cap21["seconds"] / B_RESERVE,
                    "storage_ok": pb <= cap21["bytes"] / B_RESERVE, "basis": "completed whole-stage rates"}
            caps_ok = {"time": self.rec["seconds_total"] <= self.cap_s, "storage": final["storage_final"] <= self.cap_b,
                       "memory": 0 < mem_peak < CAPS_MEMORY, "attempts": cnt["ok"]}
            final["caps_ok_on_final_figures"] = caps_ok
            final["outcome"] = "PASS" if (rok["ok"] and rep.get("validator_pass") is True and rep.get("admissible")
                                          is True and not terminal and all(caps_ok.values())) else "STOPPED"
            if len(json.dumps(final, indent=1, sort_keys=True).encode()) + size0 == final["storage_final"]:
                break
        fp = self.out / "STAGE_A_FINAL.json"
        err: list = []
        th = threading.Thread(target=lambda: self._final_write(fp, final, err), daemon=True)
        th.start()
        th.join(FINAL_WRITE_TIMEOUT_S)
        if th.is_alive() or err:                      # no final record: a truthful hold, never a promised PASS
            sys.stderr.write(f"final record not written: {err or 'timeout'}\n")
            os._exit(75)
        after = dir_bytes([self.out])
        if after != final["storage_final"]:
            final["storage_final_check"] = {"declared": final["storage_final"], "measured_after": after}
        return final

    def _final_write(self, fp: Path, final: dict, err: list) -> None:
        try:
            self._write(fp, final)
        except Exception as exc:
            err.append(repr(exc))

    # ---- stops and process cleanup --------------------------------------------------------------------------------
    def _stop(self, set_terminal, phase: str, reason: str) -> None:
        self.rec["stops"].append({"phase": phase, "session": self.session, "reason": reason,
                                  "at_total_s": self.elapsed_total()})
        try:
            set_terminal(self.out, phase, reason)
        except Exception:
            self._kill_current("terminal write failed")
            os._exit(75)

    def _final_peak(self, w: dict) -> None:
        """The leader's lifetime maximum read from the exited, UNREAPED process (before proc.wait)."""
        try:
            peak = self.probe.exit_peak(self.proc.pid)
        except memprobe.Unavailable as exc:
            w["exit_peak_error"] = str(exc)
            return
        w["exit_peak"] = peak
        pk = self.rec["peaks"]
        pk["by_phase"][w["phase"]] = max(pk["by_phase"].get(w["phase"], 0), peak)

    def _clean_group(self, w: dict) -> None:
        """SIGKILL the worker's whole process group until no LIVE member remains (the exited leader is still a group
        member until it is reaped, and killpg then answers EPERM - measured), then every recorded member outside the
        group by identity (pid + start time); confirm all gone, else stop."""
        pgid, leader = w["leader"]["pgid"], w["leader"]["pid"]
        t = time.monotonic()
        while True:
            try:
                os.killpg(pgid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            live = [p for p in self.probe.task_processes([], {pgid}) if p != leader]
            if not live:
                break
            if time.monotonic() - t > GROUP_GONE_S:
                raise ControllerStop(f"{w['phase']}: members {live} of process group {pgid} survive SIGKILL")
            time.sleep(0.02)
        others = [m for m in (w.get("members") or {}).values() if m["pid"] != leader]
        for m in others:
            if memprobe.same_process(m):
                try:
                    os.kill(m["pid"], signal.SIGKILL)
                except ProcessLookupError:
                    pass
        while any(memprobe.same_process(m) for m in others):
            if time.monotonic() - t > GROUP_GONE_S:
                raise ControllerStop(f"{w['phase']}: a member of the worker's task survives SIGKILL")
            time.sleep(0.02)
        w["group_clean"] = True

    def _end_worker(self, w: dict, why: str | None) -> dict:
        """Stop (if why) or finish the current worker: SIGTERM -> grace -> SIGKILL -> the leader's final peak read
        from the exited, unreaped process -> whole-group SIGKILL and members confirmed gone -> reap -> watchdog ended."""
        p, out = self.proc, {}
        if p is None:
            return out
        t = self.clock()
        if why and not self._leader_exited():
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
            dl = time.monotonic() + TERM_GRACE_S
            while time.monotonic() < dl and not self._leader_exited():
                time.sleep(0.02)
            out["how"] = "SIGTERM" if self._leader_exited() else "SIGKILL"
        if not self._leader_exited():
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            self._wait_leader_exit(GROUP_GONE_S)
        self._final_peak(w)
        self._clean_group(w)
        p.wait()
        w["returncode"], w["reaped"] = p.returncode, True
        if why:
            out.update(killed=True, why=why, kill_to_reap_s=self.clock() - t)
        if self.wd is not None:
            try:
                self.wd.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self.wd.kill()
                self.wd.wait()
            w["watchdog_exit"] = self.wd.returncode
            self.wd = None
        w.update(out)
        self.proc = None
        return out

    def _leader_exited(self) -> bool:
        if not self._exited_flag and memprobe.exited(self.kq):
            self._exited_flag = True
        return self._exited_flag

    def _wait_leader_exit(self, limit: float) -> None:
        dl = time.monotonic() + limit
        while not self._leader_exited():
            if time.monotonic() > dl:
                raise ControllerStop("the worker leader survives SIGKILL")
            time.sleep(0.02)

    def _kill_current(self, why: str) -> dict:
        if self.proc is None:
            return {"killed": False}
        return self._end_worker(self.rec["workers"][-1], why)

    def _phase(self, phase: str, *, deadline: float, storage_limit: int, report: bool = False,
               gates: bool = False) -> None:
        env = {**os.environ, "STAGE_A_CONTROLLER_PID": str(os.getpid()), "STAGE_A_SESSION": self.session,
               "STAGE_A_STORAGE_LIMIT": str(storage_limit), "STAGE_A_STORAGE_CAP": str(self.cap_b),
               "STAGE_A_GATES": json.dumps(self.gates_rec or {})}
        self.proc = subprocess.Popen(self.worker_cmd(phase), env=env, start_new_session=True)
        self._exited_flag = False
        self.kq = memprobe.exit_watch(self.proc.pid)
        leader = memprobe.proc_info(self.proc.pid) or {"pid": self.proc.pid, "ppid": os.getpid(),
                                                         "pgid": self.proc.pid, "start": "unknown"}
        w = {"phase": phase, "session": self.session, "pid": self.proc.pid, "leader": leader, "members": {},
             "spawned_total_s": self.elapsed_total()}
        self.rec["workers"].append(w)
        if self.use_watchdog:
            rel = f"watchdog_{self.session}_{phase}.json"
            arg = {"controller_pid": os.getpid(), "pgid": self.proc.pid, "beat_file": str(self.path),
                   "deadline_monotonic": self.t0 + (deadline - self.base) + HARD_MARGIN_S, "stale_s": STALE_S,
                   "grace_s": TERM_GRACE_S, "record": str(self.out / rel)}
            self.wd = subprocess.Popen([sys.executable, str(HERE / "stage_a_watchdog.py"), json.dumps(arg)],
                                       start_new_session=True)
            w["watchdog"] = memprobe.proc_info(self.wd.pid)
            w["watchdog_record"] = rel
        self._persist()
        last_beat = last_sys = 0.0
        max_iter = 0.0
        try:
            while True:
                it0 = time.monotonic()
                now = self.clock()
                if self._leader_exited():
                    break
                if self.elapsed_total() >= deadline:
                    raise ControllerStop(f"{phase}: time limit {deadline:.0f} s reached (row cap {self.cap_s:.0f} s "
                                         f"less reserves)")
                if self.wd is not None and self.wd.poll() is not None:
                    if self._leader_exited():
                        break
                    raise ControllerStop(f"{phase}: watchdog exited ({self.wd.returncode})")
                t = time.monotonic()
                try:
                    procs = self.probe.task_processes([self.proc.pid], {self.proc.pid})
                    for p, i in procs.items():
                        w["members"].setdefault(str(p), i)
                    pids = set(procs) | {os.getpid()} | ({self.wd.pid} if self.wd is not None else set())
                    smp = self.probe.task_sample(pids)
                except memprobe.Unavailable as exc:
                    if self._leader_exited():
                        break                         # exited between the check and the sample
                    raise ControllerStop(f"{phase}: memory reading unavailable ({exc})")
                if time.monotonic() - t > SAMPLE_LIMIT_S:
                    raise ControllerStop(f"{phase}: memory reading took {time.monotonic() - t:.2f} s")
                pk = self.rec["peaks"]
                pk["task_lifetime_sum"] = max(pk["task_lifetime_sum"], smp["lifetime_sum"])
                pk["by_phase"][phase] = max(pk["by_phase"].get(phase, 0), smp["lifetime_sum"])
                if smp["lifetime_sum"] >= MEM_STOP:
                    raise ControllerStop(f"{phase}: task memory {smp['lifetime_sum']} >= {MEM_STOP}")
                if now - last_sys >= SYS_SAMPLE_S:
                    last_sys = now
                    sysr = self.system_reader()
                    if sysr["swap"] > self.rec["swap_baseline"]:
                        raise ControllerStop(f"swap rose from {self.rec['swap_baseline']} to {sysr['swap']}")
                    if sysr["pressure"] >= 2:
                        raise ControllerStop(f"kernel memory pressure {sysr['pressure']}")
                    used = dir_bytes([self.out])
                    pk["storage_bytes"] = max(pk["storage_bytes"], used)
                    if used > storage_limit:
                        raise ControllerStop(f"{phase}: task storage {used} over {storage_limit}")
                if now - last_beat >= HEARTBEAT_S:
                    last_beat = now
                    pk["max_iteration_s"][phase] = max(pk["max_iteration_s"].get(phase, 0.0), max_iter)
                    self._persist()
                time.sleep(MEM_SAMPLE_S)
                max_iter = max(max_iter, time.monotonic() - it0)
        except BaseException as exc:
            k = self._end_worker(w, str(exc))
            w.update(exited_total_s=self.elapsed_total(), stop=str(exc), **k)
            self.rec["peaks"]["max_iteration_s"][phase] = max(self.rec["peaks"]["max_iteration_s"].get(phase, 0.0),
                                                               max_iter)
            self._persist()
            raise
        self._end_worker(w, None)
        rc = w["returncode"]
        w["exited_total_s"] = self.elapsed_total()
        self.rec["peaks"]["max_iteration_s"][phase] = max(self.rec["peaks"]["max_iteration_s"].get(phase, 0.0),
                                                           max_iter)
        self._persist()
        if rc != 0:
            raise ControllerStop(f"{phase}: worker exited {rc}")
        if not (report or gates) and not (self.out / f"{phase.upper()}_DONE.json").exists():
            raise ControllerStop(f"{phase}: worker exited 0 without its durable phase record")


def default_worker_cmd(phase: str) -> list[str]:
    return [sys.executable, str(HERE / "stage_a.py"), "worker", phase]


def main() -> int:
    import stage_a
    c = Controller(stage_a.OUT, carry_seconds=stage_a.ENGINEERING_CARRY["seconds"], worker_cmd=default_worker_cmd)
    out = c.run()
    print(json.dumps(out, indent=1, default=str))
    return {"REFUSED": 2, "HELD": EXIT_HOLD}.get(out["outcome"], 0)


if __name__ == "__main__":
    sys.exit(main())
