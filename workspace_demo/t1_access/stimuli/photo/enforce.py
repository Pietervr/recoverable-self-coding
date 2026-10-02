"""Photograph arm: the enforcement mechanism of framework §8.6 for ledger rows 20 and 21, revised for row 20's repairs
(Codex record RSC f9d2ef3; R052 brief 2026-10-02 repairs 8, 10, 11, 12; framework §8.4 (k), (m), (n), (o)).

ONE STATE FILE per task, cumulative and never reset. A `Budget` is a SESSION of the task: it is opened before any
model is imported or loaded, so startup, compile, loads, preprocessing, forwards, writes, comparisons and the report
all lie inside the clock. Every session of every phase adds its live time to the same counters.

CLOCK. Live time is time.monotonic() since the session opened. A supervisor thread wakes every HEARTBEAT_S seconds,
writes the session's live seconds durably (temp file, fsync, os.replace, directory fsync) and checks every stop. A
crashed session is charged at restart with its last durable live seconds PLUS one heartbeat interval (the unobserved
tail is at most that), and the charge is logged. At the time cap the supervisor stops active work: it records the
stop durably, calls the registered on_stop hook (the runner's terminal gate), interrupts the main thread, and if the
main thread has not exited within STOP_GRACE_S - a Metal kernel cannot be interrupted from Python - ends the process
with os._exit(STOP_EXIT). Memory, swap, pressure and storage breaches stop the same way.

ATTEMPTS. `attempt(id, kind, passes)` counts the attempt and its model passes durably BEFORE the forward. It yields an
`Attempt`; the caller writes the outputs, checksums and validates them, then calls `commit(outputs)` with
{path: sha256}. Only a committed attempt is complete. An exception, or leaving the block without commit, records the
attempt as failed (it stays in the counters). An attempt open at a crash stays counted as started and failed and is
listed in `interrupted`; it is never silently re-run - `authorise_recovery(id)` is the explicit crash-recovery route
and the runner calls it only for an id named in an owner's recovery file. On restart `completed(id)` returns the
committed output map; the runner re-verifies every checksum and reloads the outputs WITHOUT a forward; a missing or
corrupt committed output is a hold for diagnosis (StopRun), never a re-run.

CAPS (per row and aggregate, from this one state file): row 20 <= 200 attempts, <= 4 h, <= 1 GiB; row 21 <= 1,856,
<= 4 h, <= 8 GiB; aggregate <= 2,056, <= 8 h, <= 9 GiB. Attempts are counted as model passes (an attempt declares
how many it makes). `carry_in` adds already-spent work to a row when its state file is created (row 20: the sixteen
engineering attempts with a recorded allowance for their unmeasured time - framework §8.4).

MEMORY - 48 GiB is a whole-task limit. The task is one process at a time (the runner's exclusive lock and its strictly
sequential phases); this process spawns only the short-lived sysctl/ps readers. Each sample reads:
  phys_footprint  task_info(TASK_VM_INFO).phys_footprint: the kernel's physical-footprint ledger for the task -
                  dirty anonymous memory (internal), compressed pages, and IOKit-mapped memory attributed to the task,
                  which on Apple silicon includes the Metal buffers MLX allocates in unified memory. Measured 1 Oct
                  2026 (enforce_reading.json): a live 256 MiB MLX array raised phys_footprint to 0.471 GiB while RSS
                  stayed 0.083 GiB, so the Metal allocation is in this figure and not in RSS. A page is counted once
                  in it, whether the CPU or the GPU touches it, so there is no host/Metal double count inside it.
  MLX             mx.get_active_memory() + mx.get_cache_memory() (the allocator's live + cached buffer bytes) and
                  mx.get_peak_memory(); read only when mlx.core is imported in this process.
  RSS             reported only: on unified memory it misses Metal buffers.
Enforced figure per sample = max(phys_footprint, MLX active + cache, MLX peak). The maximum - never a sum - is used
because the two measure overlapping memory (MLX's buffers are inside phys_footprint): the sum would double count; the
maximum covers either one under-attributing. The task peak is the maximum over all samples of all sessions, persisted.
FAIL CLOSED: any measurement that raises or returns nothing - task_info, ps, sysctl, or MLX's counters once mlx.core
is imported - is a stop, never a zero. Stops also on swap above the level at the state file's creation and on kernel
memory pressure >= 2 (warn).

STORAGE. Every task directory (outputs, temporaries, the state file's own directory) is summed. `reserve(n)` must
pass before a write of n bytes: used + n + headroom (2 x n, for the temp-file/rename overlap) within the row and
aggregate caps. `final_size()` checks the durable total at the end of a phase. Existing weights and the lens are
outside the task directories, as specified.
"""

from __future__ import annotations

import _thread
import ctypes
import ctypes.util
import json
import os
import re
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

GiB = 1 << 30
CAPS = {"row20": {"attempts": 200, "seconds": 4 * 3600, "bytes": 1 * GiB},
        "row21": {"attempts": 1856, "seconds": 4 * 3600, "bytes": 8 * GiB},
        "aggregate": {"attempts": 2056, "seconds": 8 * 3600, "bytes": 9 * GiB}}
MEMORY_CAP = 48 * GiB
HEARTBEAT_S = 2.0
STOP_GRACE_S = 20.0
STOP_EXIT = 70


class StopRun(RuntimeError):
    """A declared stop condition. The caller archives and stops; it never retries past one."""


class _TaskVMInfo(ctypes.Structure):
    # Leading fields of task_vm_info_data_t (mach/task_info.h) up to phys_footprint.
    _fields_ = [("virtual_size", ctypes.c_uint64), ("region_count", ctypes.c_int32), ("page_size", ctypes.c_int32),
                ("resident_size", ctypes.c_uint64), ("resident_size_peak", ctypes.c_uint64),
                ("device", ctypes.c_uint64), ("device_peak", ctypes.c_uint64),
                ("internal", ctypes.c_uint64), ("internal_peak", ctypes.c_uint64),
                ("external", ctypes.c_uint64), ("external_peak", ctypes.c_uint64),
                ("reusable", ctypes.c_uint64), ("reusable_peak", ctypes.c_uint64),
                ("purgeable_volatile_pmap", ctypes.c_uint64), ("purgeable_volatile_resident", ctypes.c_uint64),
                ("purgeable_volatile_virtual", ctypes.c_uint64), ("compressed", ctypes.c_uint64),
                ("compressed_peak", ctypes.c_uint64), ("compressed_lifetime", ctypes.c_uint64),
                ("phys_footprint", ctypes.c_uint64)]


_LIBC = ctypes.CDLL(ctypes.util.find_library("c"))


def phys_footprint() -> int:
    info = _TaskVMInfo()
    count = ctypes.c_uint32(ctypes.sizeof(info) // 4)
    rc = _LIBC.task_info(_LIBC.mach_task_self(), 22, ctypes.byref(info), ctypes.byref(count))   # TASK_VM_INFO
    if rc != 0 or info.phys_footprint == 0:
        raise StopRun(f"task_info failed ({rc}): the memory bound is unenforceable")
    return int(info.phys_footprint)


def _sysctl(name: str) -> str:
    try:
        out = subprocess.run(["sysctl", "-n", name], capture_output=True, text=True, check=True, timeout=10).stdout
    except Exception as exc:
        raise StopRun(f"sysctl {name} unavailable ({exc!r}): fail closed") from exc
    if not out.strip():
        raise StopRun(f"sysctl {name} returned nothing: fail closed")
    return out.strip()


def swap_used_bytes() -> int:
    m = re.search(r"used = ([\d.]+)([KMG])", _sysctl("vm.swapusage"))
    if not m:
        raise StopRun("vm.swapusage unparseable: fail closed")
    return int(float(m.group(1)) * (1 << {"K": 10, "M": 20, "G": 30}[m.group(2)]))


def pressure_level() -> int:
    return int(_sysctl("kern.memorystatus_vm_pressure_level"))


def memory_reading() -> dict:
    try:
        rss_kb = subprocess.run(["ps", "-o", "rss=", "-p", str(os.getpid())], capture_output=True, text=True,
                                check=True, timeout=10).stdout.strip()
        rss = int(rss_kb) * 1024
    except Exception as exc:
        raise StopRun(f"ps rss unavailable ({exc!r}): fail closed") from exc
    out = {"phys_footprint": phys_footprint(), "rss": rss, "mlx_loaded": "mlx.core" in sys.modules}
    if out["mlx_loaded"]:
        try:
            mx = sys.modules["mlx.core"]
            out.update(mlx_active=int(mx.get_active_memory()), mlx_cache=int(mx.get_cache_memory()),
                       mlx_peak=int(mx.get_peak_memory()))
        except Exception as exc:
            raise StopRun(f"MLX memory counters unavailable ({exc!r}): fail closed") from exc
        out["enforced"] = max(out["phys_footprint"], out["mlx_active"] + out["mlx_cache"], out["mlx_peak"])
    else:
        out.update(mlx_active=None, mlx_cache=None, mlx_peak=None)     # no MLX allocator in this process
        out["enforced"] = out["phys_footprint"]
    out["swap_used"] = swap_used_bytes()
    out["pressure_level"] = pressure_level()
    return out


def dir_bytes(path: Path) -> int:
    p = Path(path)
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) if p.exists() else 0


def write_atomic(path: Path, data: bytes) -> None:
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    dfd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


def write_json_atomic(path: Path, obj) -> None:
    write_atomic(path, json.dumps(obj, indent=1, sort_keys=True).encode())


def _zero() -> dict:
    return {"started": 0, "completed": 0, "failed": 0, "passes": 0, "seconds": 0.0}


class Attempt:
    def __init__(self, budget: "Budget", attempt_id: str):
        self.budget, self.id, self.outputs = budget, attempt_id, None

    def commit(self, outputs: dict[str, str]) -> None:
        """Mark complete: call only after every output is written durably, checksummed and validated."""
        if self.outputs is not None:
            raise RuntimeError(f"{self.id} committed twice")
        self.outputs = dict(outputs)


class Budget:
    """One session of a task's persisted counters, checked against its row's caps and the aggregate."""

    def __init__(self, state_path: Path, row: str, identity: str, task_dirs: list[Path], phase: str, *,
                 carry_in: dict | None = None, on_stop=None, heartbeat_s: float = HEARTBEAT_S,
                 stop_grace_s: float = STOP_GRACE_S, caps: dict | None = None, memory_cap: int = MEMORY_CAP):
        if row not in ("row20", "row21"):
            raise ValueError(row)
        self.path, self.row, self.identity, self.phase = Path(state_path), row, identity, phase
        self.task_dirs = [Path(d) for d in task_dirs]
        self.caps, self.memory_cap = caps or CAPS, memory_cap
        self.on_stop, self.heartbeat_s, self.stop_grace_s = on_stop, heartbeat_s, stop_grace_s
        self._lock = threading.RLock()
        self._t0 = time.monotonic()
        self._stop_reason: str | None = None
        self._closed = False
        if self.path.exists():
            self.state = json.loads(self.path.read_text())
            if self.state["identities"].get(row) not in (None, identity):
                raise StopRun(f"identity mismatch for {row}: state has {self.state['identities'][row]}, "
                              f"this execution is {identity} - recovery refuses a changed identity")
            self._recover()
        else:
            self.state = {"identities": {}, "counters": {"row20": _zero(), "row21": _zero(), "aggregate": _zero()},
                          "completed": {}, "attempts": {}, "interrupted": [], "recovered_sessions": [],
                          "authorised_recoveries": [], "sessions": [], "open_session": None, "open_attempt": None,
                          "swap_baseline": swap_used_bytes(), "caps": self.caps, "memory_cap": self.memory_cap,
                          "peaks": {"enforced": 0, "phys_footprint": 0, "mlx_peak": 0, "output_bytes": 0},
                          "carry_in": {}, "log": []}
            if carry_in:
                for key in (row, "aggregate"):
                    c = self.state["counters"][key]
                    for k in ("started", "completed", "failed", "passes"):
                        c[k] += int(carry_in.get(k, 0))
                    c["seconds"] += float(carry_in["seconds"])
                self.state["carry_in"][row] = carry_in
        self.state["identities"][row] = identity
        self._base_seconds = {k: v["seconds"] for k, v in self.state["counters"].items()}
        self.state["open_session"] = {"phase": phase, "row": row, "pid": os.getpid(),
                                      "opened_wall": time.time(), "live_seconds": 0.0}
        self._persist()
        self.check()
        self._thread = threading.Thread(target=self._supervise, name="budget-supervisor", daemon=True)
        self._thread.start()

    # ---- persistence -------------------------------------------------------------------------------------------
    def _live(self) -> float:
        return time.monotonic() - self._t0

    def _persist(self) -> None:
        with self._lock:
            live = self._live()
            self.state["open_session"]["live_seconds"] = live
            for key in (self.row, "aggregate"):
                self.state["counters"][key]["seconds"] = self._base_seconds[key] + live
            write_json_atomic(self.path, self.state)

    def _recover(self) -> None:
        s = self.state.get("open_session")
        if s:                                              # a session died: charge its last live time + one beat
            charged = float(s.get("live_seconds", 0.0)) + self.heartbeat_s
            for key in (s["row"], "aggregate"):
                self.state["counters"][key]["seconds"] += charged - float(s.get("live_seconds", 0.0))
            self.state["recovered_sessions"].append({**s, "charged_seconds": charged,
                                                     "charge_rule": "last durable live seconds + one heartbeat"})
            self.state["sessions"].append({**s, "closed": "crashed", "charged_seconds": charged})
            self.state["open_session"] = None
        a = self.state.get("open_attempt")
        if a:                                              # an attempt died mid-flight: stays started, now failed
            for key in (a["row"], "aggregate"):
                self.state["counters"][key]["failed"] += 1
            self.state["attempts"][a["id"]]["status"] = "interrupted"
            self.state["interrupted"].append(a["id"])
            self.state["open_attempt"] = None

    # ---- stops -------------------------------------------------------------------------------------------------
    def check(self, about_to_start: int = 0) -> dict:
        reading = memory_reading()
        with self._lock:
            c = self.state["counters"]
            live = self._live()
            for key in (self.row, "aggregate"):
                cap = self.caps[key]
                if c[key]["passes"] + about_to_start > cap["attempts"]:
                    raise StopRun(f"{key}: attempt cap {cap['attempts']} would be exceeded")
                if self._base_seconds[key] + live >= cap["seconds"]:
                    raise StopRun(f"{key}: time cap {cap['seconds']} s reached")
            used = self.used_bytes()
            if used > self.caps[self.row]["bytes"] or used > self.caps["aggregate"]["bytes"]:
                raise StopRun(f"task output+temporaries {used} bytes over the cap")
            pk = self.state["peaks"]
            pk["enforced"] = max(pk["enforced"], reading["enforced"])
            pk["phys_footprint"] = max(pk["phys_footprint"], reading["phys_footprint"])
            pk["mlx_peak"] = max(pk["mlx_peak"], reading["mlx_peak"] or 0)
            pk["output_bytes"] = max(pk["output_bytes"], used)
            pk.setdefault("by_phase", {})[self.phase] = max(pk.get("by_phase", {}).get(self.phase, 0),
                                                            reading["enforced"])
        if reading["enforced"] > self.memory_cap:
            raise StopRun(f"task memory {reading['enforced']} bytes over {self.memory_cap}")
        if reading["swap_used"] > self.state["swap_baseline"]:
            raise StopRun(f"swap in use rose from {self.state['swap_baseline']} to {reading['swap_used']} bytes")
        if reading["pressure_level"] >= 2:
            raise StopRun(f"kernel memory pressure level {reading['pressure_level']}")
        reading["output_bytes"] = used
        return reading

    def used_bytes(self) -> int:
        seen, total = set(), 0
        for d in self.task_dirs:
            for f in (d.rglob("*") if d.exists() else []):
                if f.is_file() and f.resolve() not in seen:
                    seen.add(f.resolve())
                    total += f.stat().st_size
        return total

    def _supervise(self) -> None:
        while not self._closed:
            time.sleep(self.heartbeat_s)
            if self._closed:
                return
            try:
                self._persist()
                self.check()
            except StopRun as exc:
                self._hard_stop(str(exc))
                return
            except Exception as exc:                      # an unmeasurable state is a stop too
                self._hard_stop(f"supervisor failure: {exc!r}")
                return

    def _hard_stop(self, reason: str) -> None:
        with self._lock:
            self._stop_reason = reason
            self.state["log"].append({"supervisor_stop": reason, "phase": self.phase, "live": self._live()})
            try:
                self._persist()
            except Exception:
                pass
        if self.on_stop:
            try:
                self.on_stop(reason)
            except Exception:
                pass
        _thread.interrupt_main()
        deadline = time.monotonic() + self.stop_grace_s
        while time.monotonic() < deadline:
            if self._closed:
                return
            time.sleep(0.2)
        os._exit(STOP_EXIT)                                # active work could not be interrupted from Python

    @property
    def stop_reason(self) -> str | None:
        return self._stop_reason

    # ---- storage -----------------------------------------------------------------------------------------------
    def reserve(self, nbytes: int) -> None:
        used = self.used_bytes()
        need = used + 3 * int(nbytes)                      # the bytes, plus 2x headroom for temp + rename overlap
        for key in (self.row, "aggregate"):
            if need > self.caps[key]["bytes"]:
                raise StopRun(f"{key}: reserving {nbytes} bytes would exceed the storage cap ({used} used)")

    def final_size(self) -> int:
        used = self.used_bytes()
        for key in (self.row, "aggregate"):
            if used > self.caps[key]["bytes"]:
                raise StopRun(f"{key}: final durable size {used} over the cap")
        with self._lock:
            self.state["peaks"]["output_bytes"] = max(self.state["peaks"]["output_bytes"], used)
            self.state.setdefault("final_bytes", {})[self.phase] = used
        self._persist()
        return used

    # ---- attempts ----------------------------------------------------------------------------------------------
    def completed(self, attempt_id: str) -> dict | None:
        rec = self.state["completed"].get(attempt_id)
        return dict(rec["outputs"]) if rec else None

    def status(self, attempt_id: str) -> str | None:
        rec = self.state["attempts"].get(attempt_id)
        return rec["status"] if rec else None

    def authorise_recovery(self, attempt_id: str, authority: dict) -> None:
        if attempt_id not in self.state["interrupted"]:
            raise StopRun(f"{attempt_id} was not interrupted; there is nothing to recover")
        with self._lock:
            self.state["interrupted"].remove(attempt_id)
            self.state["authorised_recoveries"].append({"id": attempt_id, "authority": authority})
            self.state["attempts"][attempt_id]["status"] = "interrupted, recovery authorised"
        self._persist()

    @contextmanager
    def attempt(self, attempt_id: str, kind: str, passes: int = 1):
        """One counted attempt of `passes` model passes. Complete only if the block calls `commit`."""
        if attempt_id in self.state["completed"]:
            raise StopRun(f"{attempt_id} already completed: reload its outputs, never replay it")
        prior = self.state["attempts"].get(attempt_id)
        if prior and prior["status"] != "interrupted, recovery authorised":
            raise StopRun(f"{attempt_id} already attempted ({prior['status']}): no retry")
        self.check(about_to_start=passes)
        with self._lock:
            self.state["open_attempt"] = {"id": attempt_id, "kind": kind, "row": self.row, "passes": passes,
                                          "phase": self.phase, "live_at_start": self._live()}
            self.state["attempts"][attempt_id] = {"kind": kind, "passes": passes, "status": "open",
                                                  "tries": (prior or {}).get("tries", 0) + 1}
            for key in (self.row, "aggregate"):
                self.state["counters"][key]["started"] += 1
                self.state["counters"][key]["passes"] += passes
        self._persist()                                    # durable BEFORE the forward
        att = Attempt(self, attempt_id)
        t = time.monotonic()
        try:
            yield att
        except BaseException as exc:
            self._close_attempt(att, kind, passes, time.monotonic() - t, f"failed: {exc!r}"[:500])
            raise
        if att.outputs is None:
            self._close_attempt(att, kind, passes, time.monotonic() - t, "failed: left without commit")
            raise StopRun(f"{attempt_id}: attempt left without a validated commit")
        self._close_attempt(att, kind, passes, time.monotonic() - t, "completed")
        self.check()

    def _close_attempt(self, att: Attempt, kind: str, passes: int, seconds: float, status: str) -> None:
        with self._lock:
            ok = status == "completed"
            for key in (self.row, "aggregate"):
                self.state["counters"][key]["completed" if ok else "failed"] += 1
            if ok:
                self.state["completed"][att.id] = {"kind": kind, "outputs": att.outputs, "phase": self.phase}
            self.state["attempts"][att.id]["status"] = status
            self.state["open_attempt"] = None
            self.state["log"].append({"id": att.id, "kind": kind, "passes": passes, "status": status,
                                      "seconds_in_block": seconds, "phase": self.phase})
        self._persist()

    # ---- session end -------------------------------------------------------------------------------------------
    def close(self, outcome: str) -> None:
        if self._closed:
            return
        self._closed = True
        with self._lock:
            s = dict(self.state["open_session"], closed=outcome, live_seconds=self._live())
            self.state["sessions"].append(s)
            for key in (self.row, "aggregate"):
                self.state["counters"][key]["seconds"] = self._base_seconds[key] + s["live_seconds"]
            self.state["open_session"] = None
            write_json_atomic(self.path, self.state)


if __name__ == "__main__":
    import mlx.core as mx
    a = mx.ones((1 << 26,), dtype=mx.float32)          # 256 MiB, to show the MLX counters move
    mx.eval(a)
    r = memory_reading()
    print(json.dumps({k: (f"{v / GiB:.3f} GiB" if isinstance(v, int) and not isinstance(v, bool)
                          and k != "pressure_level" else v) for k, v in r.items()}, indent=1))
