"""Photograph arm, desk gate ask 4: the enforcement mechanism of framework §8.6, for ledger rows 20 and 21.

Every forward attempt runs inside `Budget.attempt()`, which persists the counters ATOMICALLY (write a temp file,
fsync, os.replace) BEFORE the attempt starts and AFTER it ends, and checks every stop condition at both points.

COUNTERS, cumulative and never reset: attempts started / completed / failed, including warmups, native references,
diagnostics, retries and any internal duplicate pass (the caller declares how many model passes an attempt makes);
computation seconds; new output plus temporaries on disk. Per row and aggregate across rows 20 and 21, from one state
file: row 20 <= 200 attempts, <= 4 h, <= 1 GiB; row 21 <= 1,856, <= 4 h, <= 8 GiB; aggregate <= 2,056, <= 8 h,
<= 9 GiB. A crash mid-attempt is recovered conservatively: the interrupted attempt stays counted as started and its
time up to its last heartbeat is charged.

MEMORY, bound to documented physical measures, read together:
  phys_footprint   the macOS kernel's physical footprint of this process (task_info TASK_VM_INFO, the figure
                   Activity Monitor reports as Memory), which on Apple silicon includes the GPU-mapped memory MLX's
                   Metal buffers live in - the PRIMARY bound;
  MLX active / cache / peak   mx.get_active_memory(), mx.get_cache_memory(), mx.get_peak_memory();
  RSS              resident set size (ps), reported, not used as a bound: on unified memory it is not one;
  rss_plus_mlx     RSS + MLX active + MLX cache, reported as a cross-check only. It is NOT an upper bound: measured
                   1 Oct 2026 with a 256 MiB MLX array live, RSS was 0.08 GiB (it does not see the Metal buffer),
                   RSS + MLX was 0.33 GiB and phys_footprint 0.47 GiB - the sum misses the Metal runtime's own
                   memory, so phys_footprint is the bound and the sum must never be used as one.
Enforced task memory = max(phys_footprint, MLX peak). The cap is 48 GiB; 128 GiB of hw.memsize is capacity, not
a footprint.

STOPS: any cap reached; swap in use above the level recorded at start (sysctl vm.swapusage); kernel memory pressure
at warn or worse (sysctl kern.memorystatus_vm_pressure_level >= 2); an execution identity different from the one the
state file was opened with; an attempt id already completed (no silent replay). A budget change is prospective and
needs a new authorised row - this code has no reset.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import json
import os
import re
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

GiB = 1 << 30
CAPS = {"row20": {"attempts": 200, "seconds": 4 * 3600, "bytes": 1 * GiB},
        "row21": {"attempts": 1856, "seconds": 4 * 3600, "bytes": 8 * GiB},
        "aggregate": {"attempts": 2056, "seconds": 8 * 3600, "bytes": 9 * GiB}}
MEMORY_CAP = 48 * GiB


class StopRun(RuntimeError):
    """A declared stop condition. The caller archives and stops; it never retries past one."""


class _TaskVMInfo(ctypes.Structure):
    # Leading fields of task_vm_info_data_t (mach/task_info.h); phys_footprint is the 19th 64-bit-or-int field.
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


def phys_footprint() -> int:
    libc = ctypes.CDLL(ctypes.util.find_library("c"))
    info = _TaskVMInfo()
    count = ctypes.c_uint32(ctypes.sizeof(info) // 4)
    task = libc.mach_task_self()
    TASK_VM_INFO = 22
    rc = libc.task_info(task, TASK_VM_INFO, ctypes.byref(info), ctypes.byref(count))
    if rc != 0:
        raise StopRun(f"task_info failed ({rc}): the memory bound is unenforceable")
    return int(info.phys_footprint)


def _sysctl(name: str) -> str:
    return subprocess.run(["sysctl", "-n", name], capture_output=True, text=True, check=True).stdout.strip()


def swap_used_bytes() -> int:
    m = re.search(r"used = ([\d.]+)([MG])", _sysctl("vm.swapusage"))
    return int(float(m.group(1)) * (1 << (20 if m.group(2) == "M" else 30))) if m else 0


def pressure_level() -> int:
    return int(_sysctl("kern.memorystatus_vm_pressure_level"))


def memory_reading() -> dict:
    out = {"phys_footprint": phys_footprint(),
           "rss": int(subprocess.run(["ps", "-o", "rss=", "-p", str(os.getpid())], capture_output=True,
                                     text=True).stdout.strip() or 0) * 1024}
    try:
        import mlx.core as mx
        out.update(mlx_active=mx.get_active_memory(), mlx_cache=mx.get_cache_memory(), mlx_peak=mx.get_peak_memory())
    except Exception:                                   # MLX not imported in this process
        out.update(mlx_active=0, mlx_cache=0, mlx_peak=0)
    out["enforced"] = max(out["phys_footprint"], out["mlx_peak"])
    out["rss_plus_mlx"] = out["rss"] + out["mlx_active"] + out["mlx_cache"]   # cross-check, not a bound
    out["swap_used"] = swap_used_bytes()
    out["pressure_level"] = pressure_level()
    return out


def dir_bytes(path: Path) -> int:
    return sum(p.stat().st_size for p in Path(path).rglob("*") if p.is_file()) if Path(path).exists() else 0


def _write_atomic(path: Path, obj: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    dfd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


class Budget:
    """The persisted counters for one row, checked against that row's caps and the aggregate."""

    def __init__(self, state_path: Path, row: str, identity: str, output_dirs: list[Path]):
        if row not in ("row20", "row21"):
            raise ValueError(row)
        self.path, self.row, self.identity, self.output_dirs = Path(state_path), row, identity, output_dirs
        if self.path.exists():
            self.state = json.loads(self.path.read_text())
            if self.state["identities"].get(row) not in (None, identity):
                raise StopRun(f"identity mismatch for {row}: state has {self.state['identities'][row]}, "
                              f"this execution is {identity} - recovery refuses a changed identity")
            open_attempt = self.state.get("open_attempt")
            if open_attempt:                          # crashed mid-attempt: keep it counted, charge its time
                charged = open_attempt["heartbeat"] - open_attempt["started"]
                for key in (open_attempt["row"], "aggregate"):
                    self.state["counters"][key]["seconds"] += max(0.0, charged)
                    self.state["counters"][key]["failed"] += 1
                self.state["recovered"].append({**open_attempt, "charged_seconds": charged})
                self.state["open_attempt"] = None
        else:
            zero = {"started": 0, "completed": 0, "failed": 0, "passes": 0, "seconds": 0.0}
            self.state = {"identities": {}, "counters": {"row20": dict(zero), "row21": dict(zero),
                                                         "aggregate": dict(zero)},
                          "completed_ids": [], "recovered": [], "open_attempt": None,
                          "swap_baseline": swap_used_bytes(), "caps": CAPS, "memory_cap": MEMORY_CAP}
        self.state["identities"][row] = identity
        _write_atomic(self.path, self.state)

    def _check(self, about_to_start: int = 0) -> dict:
        reading = memory_reading()
        c = self.state["counters"]
        for key in (self.row, "aggregate"):
            cap = CAPS[key]
            if c[key]["passes"] + about_to_start > cap["attempts"]:
                raise StopRun(f"{key}: attempt cap {cap['attempts']} would be exceeded")
            if c[key]["seconds"] >= cap["seconds"]:
                raise StopRun(f"{key}: time cap {cap['seconds']} s reached")
        used = sum(dir_bytes(d) for d in self.output_dirs)
        if used > CAPS[self.row]["bytes"] or used > CAPS["aggregate"]["bytes"]:
            raise StopRun(f"output+temporaries {used} bytes over the cap")
        if reading["enforced"] > MEMORY_CAP:
            raise StopRun(f"task memory {reading['enforced']} bytes over 48 GiB")
        if reading["swap_used"] > self.state["swap_baseline"]:
            raise StopRun(f"swap in use rose from {self.state['swap_baseline']} to {reading['swap_used']} bytes")
        if reading["pressure_level"] >= 2:
            raise StopRun(f"kernel memory pressure level {reading['pressure_level']}")
        reading["output_bytes"] = used
        return reading

    def heartbeat(self) -> None:
        if self.state.get("open_attempt"):
            self.state["open_attempt"]["heartbeat"] = time.time()
            _write_atomic(self.path, self.state)

    @contextmanager
    def attempt(self, attempt_id: str, kind: str, passes: int = 1):
        """One counted attempt of `passes` model passes. kind: instrumented | native_reference | warmup | diagnostic."""
        if attempt_id in self.state["completed_ids"]:
            raise StopRun(f"{attempt_id} already completed: no silent replay")
        before = self._check(about_to_start=passes)
        now = time.time()
        self.state["open_attempt"] = {"id": attempt_id, "kind": kind, "row": self.row, "passes": passes,
                                      "started": now, "heartbeat": now}
        for key in (self.row, "aggregate"):
            self.state["counters"][key]["started"] += 1
            self.state["counters"][key]["passes"] += passes
        _write_atomic(self.path, self.state)          # persisted BEFORE the attempt runs
        ok = False
        try:
            yield before
            ok = True
        finally:
            elapsed = time.time() - now
            for key in (self.row, "aggregate"):
                self.state["counters"][key]["seconds"] += elapsed
                self.state["counters"][key]["completed" if ok else "failed"] += 1
            if ok:
                self.state["completed_ids"].append(attempt_id)
            self.state["open_attempt"] = None
            self.state.setdefault("log", []).append({"id": attempt_id, "kind": kind, "passes": passes,
                                                     "ok": ok, "seconds": elapsed})
            _write_atomic(self.path, self.state)      # persisted AFTER the attempt, success or not
        self._check()


if __name__ == "__main__":
    import mlx.core as mx
    a = mx.ones((1 << 26,), dtype=mx.float32)          # 256 MiB, to show the MLX counters move
    mx.eval(a)
    r = memory_reading()
    print(json.dumps({k: (f"{v / GiB:.3f} GiB" if isinstance(v, int) and k not in ("pressure_level",) else v)
                      for k, v in r.items()}, indent=1))
