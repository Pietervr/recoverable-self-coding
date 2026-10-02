"""Photograph arm, Stage A (row 20): the INDEPENDENT CONTROLLER - revision 3, Codex RSC 69539bb closure groups 2, 3,
4 and 6. A separate process that owns the task lock, the clock, the resource limits, the deadline, termination and
reaping; each phase runs as a WORKER subprocess it spawns, watches from outside and reaps.

    .venv-image/bin/python stimuli/photo/stage_a_controller.py run      # instrumented -> native -> report

ORDER: lock (held until the controller exits, across every phase) -> terminal gate -> go/attestation/package ->
fresh execution identity -> positions receipt -> controller record -> per phase: spawn, watch, reap, verify the
phase record -> next phase only after the previous worker has EXITED AND BEEN REAPED (process separation, group 3).
The report phase always runs at the end, also after a stop, inside its own reserve.

CLOCK (group 2). Row 20's time = carried 1,808.73 s + every controller session's live monotonic seconds, written
durably every HEARTBEAT_S = 1 s. A controller that dies is charged at restart with its last durable live time plus
TAIL_RESERVE_S = 60 s - above the longest unseen tail the loop admits (a 1 s beat, sampler and sysctl calls bounded
by 2 s timeouts, an fsync) - and the charge is logged. RESERVES INSIDE THE 4 h CAP: TAIL 60 s, STOP 60 s (detection,
SIGTERM, 3 s grace, SIGKILL, reap, terminal write - measured bound in the fixtures), REPORT 600 s; the work phases are
killed at cap - 720 s and the report at cap - 60 s. Caps are never reset.

MEMORY (group 3). Every MEM_SAMPLE_S = 0.25 s the controller reads the worker's physical-footprint ledger and the
kernel's lifetime maximum of it (memprobe.footprint, proc_pid_rusage V4) - measured to include host and MLX/Metal
allocations additively and to retain transient peaks between samples (memprobe fixture, controller_fixtures.json).
Stop at a lifetime maximum >= MEM_STOP = 44 GiB (4 GiB headroom under the 48 GiB task cap for growth within one
sample); a reading that fails, returns nothing or takes > 1 s stops. Swap above the level at the controller's start
and kernel pressure >= 2 are read every 2 s (sysctl, 2 s timeout); failure stops. The worker is the only task process
besides the controller; its children are counted by the kernel in the process group killed at a stop.

STORAGE (group 4). Every task path - the output tree (which now holds the hash-free identity, state, controller
record, terminal, phase records, parity and report) - is summed every 2 s; the work phases stop at cap - 64 MiB, the
finalisation reserve for the terminal, phase, parity and report writes; the report must finish under the full cap.

STOP. Any limit, sampler failure, worker crash, non-zero exit or persistence failure -> TERMINAL.json (first reason
kept) -> SIGTERM to the worker's process group -> 3 s -> SIGKILL -> waitpid; elapsed is recorded. A failure to write
the controller record or the terminal record kills the worker the same way and exits 75; the next start finds the
record stale and charges the tail. RECOVERY: a worker attempt interrupted by a crash holds every later run until the
owner writes RECOVERY_<id>__<session>__<try>.json naming exactly that attempt, session and try; the worker consumes it
once (enforce.Budget.authorise_recovery); it cannot be reused for a later crash.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import memprobe  # noqa: E402
from enforce import CAPS, MEMORY_CAP as CAPS_MEMORY, GiB, MiB, dir_bytes, write_json_atomic  # noqa: E402

HEARTBEAT_S, MEM_SAMPLE_S, SYS_SAMPLE_S, SYSCTL_TIMEOUT_S = 1.0, 0.25, 2.0, 2.0
TAIL_RESERVE_S, STOP_RESERVE_S, REPORT_RESERVE_S, TERM_GRACE_S = 60.0, 60.0, 600.0, 3.0
MEM_STOP = 44 * GiB
FINAL_RESERVE_BYTES = 64 * MiB
PHASES = ["instrumented", "native"]


class ControllerStop(RuntimeError):
    pass


def sysctl(name: str) -> str:
    out = subprocess.run(["sysctl", "-n", name], capture_output=True, text=True, timeout=SYSCTL_TIMEOUT_S, check=True)
    if not out.stdout.strip():
        raise ControllerStop(f"sysctl {name} returned nothing")
    return out.stdout.strip()


def swap_used() -> int:
    import re
    m = re.search(r"used = ([\d.]+)([KMG])", sysctl("vm.swapusage"))
    if not m:
        raise ControllerStop("vm.swapusage unparseable")
    return int(float(m.group(1)) * (1 << {"K": 10, "M": 20, "G": 30}[m.group(2)]))


class Controller:
    def __init__(self, out: Path, *, carry_seconds: float, worker_cmd, gates=None, row_cap_s: float | None = None,
                 storage_cap: int | None = None, sampler=memprobe.footprint, system_reader=None, writer=write_json_atomic,
                 clock=time.monotonic):
        self.out, self.worker_cmd, self.gates = Path(out), worker_cmd, gates
        self.cap_s = row_cap_s if row_cap_s is not None else CAPS["row20"]["seconds"]
        self.cap_b = storage_cap if storage_cap is not None else CAPS["row20"]["bytes"]
        self.carry, self.sampler, self.writer, self.clock = carry_seconds, sampler, writer, clock
        self.system_reader = system_reader or (lambda: {"swap": swap_used(),
                                                        "pressure": int(sysctl("kern.memorystatus_vm_pressure_level"))})
        self.path = self.out / "controller.json"
        self.session = uuid.uuid4().hex[:12]

    # ---- record ---------------------------------------------------------------------------------------------------
    def _load(self) -> dict:
        if self.path.exists():
            rec = json.loads(self.path.read_text())
            s = rec.get("open_session")
            if s:                                     # the last controller died: charge its unseen tail
                charged = float(s["live_s"]) + TAIL_RESERVE_S
                rec["seconds_total"] += charged           # its durable live time plus the unseen-tail reserve
                rec["sessions"].append({**s, "closed": "crashed", "charged_s": charged})
                rec["open_session"] = None
            return rec
        return {"carry_s": self.carry, "seconds_total": self.carry, "sessions": [], "open_session": None,
                "peaks": {"lifetime_max_phys_footprint": 0, "by_phase": {}, "storage_bytes": 0},
                "stops": [], "workers": [], "swap_baseline": None}

    def _persist(self) -> None:
        live = self.clock() - self.t0
        self.rec["open_session"]["live_s"] = live
        self.rec["seconds_total_live"] = self.base + live
        try:
            self.writer(self.path, self.rec)
        except Exception as exc:
            raise ControllerStop(f"persistence failure: {exc!r}") from exc

    def elapsed_total(self) -> float:
        return self.base + (self.clock() - self.t0)

    # ---- the run --------------------------------------------------------------------------------------------------
    def run(self, phases=PHASES) -> dict:
        from stage_a_guard import TaskLock, check_terminal, set_terminal
        self.out.mkdir(parents=True, exist_ok=True)
        lock = TaskLock(self.out)
        try:
            self.rec = self._load()
            self.base = self.rec["seconds_total"]
            self.t0 = self.clock()
            self.rec["open_session"] = {"session": self.session, "pid": os.getpid(), "live_s": 0.0,
                                        "opened_wall": time.time()}
            try:
                self._persist()
                self.gates_ok = False
                if self.gates:
                    self.gates()                      # go/attestation, identity, receipt: a refusal holds, no spawn
                    self.gates_ok = True              # the report is admissible only after this, in this run
            except BaseException:                     # any gate failure holds: nothing is spawned
                self._close("refused")
                raise
            terminal = (self.out / "TERMINAL.json").exists()
            try:
                if self.rec["swap_baseline"] is None:
                    self.rec["swap_baseline"] = self.system_reader()["swap"]
                if not terminal:
                    check_terminal(self.out)
                    for ph in phases:
                        if (self.out / f"{ph.upper()}_DONE.json").exists():
                            continue
                        self._phase(ph, deadline=self.cap_s - TAIL_RESERVE_S - STOP_RESERVE_S - REPORT_RESERVE_S,
                                    storage_limit=self.cap_b - FINAL_RESERVE_BYTES)
            except (ControllerStop, Exception) as exc:
                self._stop(set_terminal, "controller", f"{type(exc).__name__}: {exc}")
            # the report: always, inside its reserve (STOPPED after a stop)
            try:
                self._phase("report", deadline=self.cap_s - TAIL_RESERVE_S, storage_limit=self.cap_b, report=True)
            except Exception as exc:
                self.rec["stops"].append({"phase": "report", "reason": f"{type(exc).__name__}: {exc}"})
            self._close("terminal" if (self.out / "TERMINAL.json").exists() else "completed")
            return self._finalise()
        finally:
            lock.release()

    def _close(self, outcome: str) -> None:
        live = self.clock() - self.t0
        s = dict(self.rec["open_session"], live_s=live, closed=outcome)
        self.rec["sessions"].append(s)
        self.rec["seconds_total"] = self.base + live
        self.rec["open_session"] = None
        self.rec["storage_final"] = dir_bytes([self.out])
        try:
            self.writer(self.path, self.rec)
        except Exception:
            os._exit(75)

    def _finalise(self) -> dict:
        """The completed durable record (group 6): written AFTER the report worker has exited and the session has
        closed, so cost, peaks and final bytes include report generation, its writes and closure. PASS is accepted
        here only if the report's validator passed AND, re-checked now, there is no terminal record and every
        cap holds on the final figures."""
        rp = self.out / "report" / "stage_a_report.json"
        rep = json.loads(rp.read_text()) if rp.exists() else {}
        terminal = (self.out / "TERMINAL.json").exists()
        caps_ok = {"time": self.rec["seconds_total"] <= self.cap_s,
                   "storage": self.rec["storage_final"] <= self.cap_b,
                   "memory": self.rec["peaks"]["lifetime_max_phys_footprint"] < CAPS_MEMORY}
        final = {"outcome": "PASS" if rep.get("validator_pass") and not terminal and all(caps_ok.values())
                 else "STOPPED", "validator_pass": bool(rep.get("validator_pass")), "terminal": terminal,
                 "caps_ok_on_final_figures": caps_ok, "seconds_total": self.rec["seconds_total"],
                 "carry_s": self.rec["carry_s"], "stage_a_seconds": self.rec["seconds_total"] - self.rec["carry_s"],
                 "peaks": self.rec["peaks"], "storage_final": self.rec["storage_final"],
                 "report_sha256": __import__("hashlib").sha256(rp.read_bytes()).hexdigest() if rp.exists() else None,
                 "controller_sha256": __import__("hashlib").sha256(self.path.read_bytes()).hexdigest(),
                 "stops": self.rec["stops"], "workers": self.rec["workers"]}
        self.writer(self.out / "STAGE_A_FINAL.json", final)
        return final

    def _stop(self, set_terminal, phase: str, reason: str) -> None:
        self.rec["stops"].append({"phase": phase, "reason": reason, "at_total_s": self.elapsed_total()})
        try:
            set_terminal(self.out, phase, reason)
        except Exception:
            self._kill_current("terminal write failed")
            os._exit(75)

    def _kill_current(self, why: str) -> dict:
        p = getattr(self, "proc", None)
        if p is None or p.poll() is not None:
            return {"killed": False}
        t = self.clock()
        try:
            os.killpg(p.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            p.wait(timeout=TERM_GRACE_S)
            how = "SIGTERM"
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
            how = "SIGKILL"
        out = {"killed": True, "how": how, "why": why, "kill_to_reap_s": self.clock() - t}
        self.rec["workers"][-1].update(out)
        return out

    def _phase(self, phase: str, *, deadline: float, storage_limit: int, report: bool = False) -> None:
        env = {**os.environ, "STAGE_A_CONTROLLER_PID": str(os.getpid()), "STAGE_A_SESSION": self.session,
               "STAGE_A_STORAGE_LIMIT": str(storage_limit), "STAGE_A_GATES_OK": "1" if self.gates_ok else "0"}
        self.proc = subprocess.Popen(self.worker_cmd(phase), env=env, start_new_session=True)
        w = {"phase": phase, "pid": self.proc.pid, "spawned_total_s": self.elapsed_total()}
        self.rec["workers"].append(w)
        last_beat = last_sys = 0.0
        try:
            while True:
                now = self.clock()
                if self.proc.poll() is not None:
                    break
                if self.elapsed_total() >= deadline:
                    raise ControllerStop(f"{phase}: time limit {deadline:.0f} s reached (row cap {self.cap_s:.0f} s "
                                         f"less reserves)")
                t = self.clock()
                try:
                    fp = self.sampler(self.proc.pid)
                except memprobe.Unavailable:
                    if self.proc.poll() is not None:
                        break                         # exited between the poll and the sample
                    raise ControllerStop(f"{phase}: memory reading unavailable")
                if self.clock() - t > 1.0:
                    raise ControllerStop(f"{phase}: memory reading took {self.clock() - t:.2f} s")
                pk = self.rec["peaks"]
                pk["lifetime_max_phys_footprint"] = max(pk["lifetime_max_phys_footprint"], fp["lifetime_max"])
                pk["by_phase"][phase] = max(pk["by_phase"].get(phase, 0), fp["lifetime_max"])
                if fp["lifetime_max"] >= MEM_STOP:
                    raise ControllerStop(f"{phase}: task memory {fp['lifetime_max']} >= {MEM_STOP}")
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
                    self._persist()
                time.sleep(MEM_SAMPLE_S)
        except BaseException as exc:
            k = self._kill_current(str(exc))
            w.update(exited_total_s=self.elapsed_total(), returncode=self.proc.returncode, stop=str(exc), **k)
            self._persist()
            raise
        w.update(exited_total_s=self.elapsed_total(), returncode=self.proc.returncode)
        self._persist()
        if self.proc.returncode != 0:
            raise ControllerStop(f"{phase}: worker exited {self.proc.returncode}")
        if not report and not (self.out / f"{phase.upper()}_DONE.json").exists():
            raise ControllerStop(f"{phase}: worker exited 0 without its durable phase record")


def default_worker_cmd(phase: str) -> list[str]:
    return [sys.executable, str(HERE / "stage_a.py"), "worker", phase]


def main() -> int:
    import stage_a
    c = Controller(stage_a.OUT, carry_seconds=stage_a.ENGINEERING_CARRY["seconds"], worker_cmd=default_worker_cmd,
                   gates=lambda: stage_a.desk_gates(stage_a.Ctx()))
    print(json.dumps(c.run(), indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
