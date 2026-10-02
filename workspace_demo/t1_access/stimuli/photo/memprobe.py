"""Out-of-process task memory and process identity for the Stage A controller and the AI-reader job - revision 5 (Codex
RSC 1bf9890 A2, A3, R3): `end_group` kills a whole process group by enumeration, anchored to the recorded leader
identity (a group id whose pid now belongs to another process is extinct; nothing unidentified is signalled), plus the
recorded member identities outside it, and confirms all gone; `valid_ident` is the strict identity schema. The
fixture adds the multi-thread growth rate and the SIGKILL overshoot used by the memory-margin statement. Revision 4
answered RSC 081f17b groups 2 and 3. Standard library and libproc through ctypes; no privilege needed for processes of the same user.

FOOTPRINT (`footprint`): proc_pid_rusage(RUSAGE_INFO_V4) - ri_phys_footprint (the kernel's physical-footprint ledger of
ONE task now) and ri_lifetime_max_phys_footprint (that task's running maximum of it). Per Apple's XNU
(gather_rusage_info) both describe the one task; the child_* fields are time and page-in counters, not footprint, so
children are NOT included - the whole task is measured by summing over its processes (`task_sample`). On an exited
process that has not been reaped (a zombie) the call still succeeds: the current footprint reads 0 and the lifetime
maximum is retained (measured: a child that touched 2 GiB and exited read lifetime 2.06 GiB before its reap), so the
controller takes the final peak BEFORE it reaps (`exit_peak`). Validated: lifetime > 0 and, for a live process,
current > 0; the kernel updates the maximum lazily (measured once above it just after exec), so the reading used is
max(lifetime, current) and the lag is flagged, never trusted downward.

PROCESS IDENTITY (`proc_info`, `task_processes`): libproc PROC_PIDTBSDINFO gives pid, parent, process group and the
start time (seconds, microseconds); a process is identified by (pid, start time), so a recorded identity never
matches an unrelated process that later reuses the pid. `task_processes(roots, pgids)` lists every live process in the
given process groups or descended (by parent chain) from the given roots.

SYSTEM (`swap_used`, `pressure_level`): sysctlbyname("vm.swapusage") and ("kern.memorystatus_vm_pressure_level")
in-process, about 50 us - no subprocess and no timeout path in the sampling loop.

`python memprobe.py fixture <python>` runs the declared non-development fixture (no model): host + MLX active + a
NONZERO MLX free-buffer cache allocated simultaneously and compared with the ledger; the same with the MLX cache
disabled (set_cache_limit(0)); a transient spike that falls before sampling (retention after a fall); the exit peak
read from an unreaped child; and the fastest footprint growth a synthetic writer achieves (for the stop margin).
"""

from __future__ import annotations

import ctypes
import ctypes.util
import json
import os
import select
import subprocess
import sys
import time

RUSAGE_INFO_V4 = 4
PROC_PIDTBSDINFO = 3
_FIELDS = ["ri_user_time", "ri_system_time", "ri_pkg_idle_wkups", "ri_interrupt_wkups", "ri_pageins",
           "ri_wired_size", "ri_resident_size", "ri_phys_footprint", "ri_proc_start_abstime", "ri_proc_exit_abstime",
           "ri_child_user_time", "ri_child_system_time", "ri_child_pkg_idle_wkups", "ri_child_interrupt_wkups",
           "ri_child_pageins", "ri_child_elapsed_abstime", "ri_diskio_bytesread", "ri_diskio_byteswritten",
           "ri_cpu_time_qos_default", "ri_cpu_time_qos_maintenance", "ri_cpu_time_qos_background",
           "ri_cpu_time_qos_utility", "ri_cpu_time_qos_legacy", "ri_cpu_time_qos_user_initiated",
           "ri_cpu_time_qos_user_interactive", "ri_billed_system_time", "ri_serviced_system_time",
           "ri_logical_writes", "ri_lifetime_max_phys_footprint", "ri_instructions", "ri_cycles",
           "ri_billed_energy", "ri_serviced_energy", "ri_interval_max_phys_footprint", "ri_runnable_time"]


class _RU4(ctypes.Structure):
    _fields_ = [("ri_uuid", ctypes.c_uint8 * 16)] + [(f, ctypes.c_uint64) for f in _FIELDS]


class _BSD(ctypes.Structure):
    _fields_ = [("pbi_flags", ctypes.c_uint32), ("pbi_status", ctypes.c_uint32), ("pbi_xstatus", ctypes.c_uint32),
                ("pbi_pid", ctypes.c_uint32), ("pbi_ppid", ctypes.c_uint32), ("pbi_uid", ctypes.c_uint32),
                ("pbi_gid", ctypes.c_uint32), ("pbi_ruid", ctypes.c_uint32), ("pbi_rgid", ctypes.c_uint32),
                ("pbi_svuid", ctypes.c_uint32), ("pbi_svgid", ctypes.c_uint32), ("rfu_1", ctypes.c_uint32),
                ("pbi_comm", ctypes.c_char * 16), ("pbi_name", ctypes.c_char * 32), ("pbi_nfiles", ctypes.c_uint32),
                ("pbi_pgid", ctypes.c_uint32), ("pbi_pjobc", ctypes.c_uint32), ("e_tdev", ctypes.c_uint32),
                ("e_tpgid", ctypes.c_uint32), ("pbi_nice", ctypes.c_int32), ("pbi_start_tvsec", ctypes.c_uint64),
                ("pbi_start_tvusec", ctypes.c_uint64)]


_LIBPROC = ctypes.CDLL(ctypes.util.find_library("proc") or "/usr/lib/libproc.dylib", use_errno=True)
_LIBPROC.proc_pid_rusage.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
_LIBPROC.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
_LIBPROC.proc_listallpids.argtypes = [ctypes.c_void_p, ctypes.c_int]
_LIBC = ctypes.CDLL(None, use_errno=True)
_LIBC.sysctlbyname.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p,
                               ctypes.c_size_t]


class Unavailable(RuntimeError):
    pass


def footprint(pid: int) -> dict:
    ru = _RU4()
    rc = _LIBPROC.proc_pid_rusage(int(pid), RUSAGE_INFO_V4, ctypes.byref(ru))
    if rc != 0:
        raise Unavailable(f"proc_pid_rusage({pid}) failed rc={rc} errno={ctypes.get_errno()}")
    exited = ru.ri_proc_exit_abstime != 0
    cur, life = int(ru.ri_phys_footprint), int(ru.ri_lifetime_max_phys_footprint)
    if life == 0 or (cur == 0 and not exited):
        raise Unavailable(f"proc_pid_rusage({pid}) implausible: current {cur}, lifetime {life}, exited {exited}")
    # The kernel updates the lifetime maximum lazily: just after exec the current ledger was measured ABOVE it
    # (4,112,816 > 4,096,432 bytes). The larger of the two is taken, so a lagging maximum can never understate.
    return {"phys_footprint": cur, "lifetime_max": max(life, cur), "resident": int(ru.ri_resident_size),
            "exited": exited, "lifetime_lagged": life < cur}


def proc_info(pid: int) -> dict | None:
    """{pid, ppid, pgid, start} of a live process, or None when it does not exist (or is a reaped/zombie pid)."""
    b = _BSD()
    n = _LIBPROC.proc_pidinfo(int(pid), PROC_PIDTBSDINFO, 0, ctypes.byref(b), ctypes.sizeof(b))
    if n != ctypes.sizeof(b):
        return None
    return {"pid": int(b.pbi_pid), "ppid": int(b.pbi_ppid), "pgid": int(b.pbi_pgid),
            "start": f"{b.pbi_start_tvsec}.{b.pbi_start_tvusec:06d}"}


def same_process(ident: dict) -> bool:
    """True when the process recorded as ident (pid and start time) is still the live process with that pid."""
    now = proc_info(ident["pid"])
    return now is not None and now["start"] == ident["start"]


def all_pids() -> list[int]:
    n = _LIBPROC.proc_listallpids(None, 0)
    buf = (ctypes.c_int * (n + 256))()
    m = _LIBPROC.proc_listallpids(buf, ctypes.sizeof(buf))
    if m <= 0:
        raise Unavailable("proc_listallpids failed")
    return [p for p in buf[:m] if p > 0]


def task_processes(roots: list[int], pgids: set[int]) -> dict[int, dict]:
    """Every live process in the process groups `pgids` or descended from a pid in `roots` (parent chain)."""
    info = {p: i for p in all_pids() if (i := proc_info(p)) is not None}
    out = {}
    for p, i in info.items():
        if i["pgid"] in pgids or p in roots:
            out[p] = i
            continue
        q, seen = i["ppid"], set()
        while q > 1 and q not in seen:
            if q in roots:
                out[p] = i
                break
            seen.add(q)
            q = info[q]["ppid"] if q in info else 0
    return out


def task_sample(pids) -> dict:
    """Sum over the task's processes: current footprint and the sum of lifetime maxima (an upper bound on the task's
    simultaneous peak, since each process's maximum may fall at a different time). A process that vanished between
    listing and reading is skipped; one that cannot be read otherwise raises Unavailable."""
    cur = life = 0
    per = {}
    for p in pids:
        try:
            f = footprint(p)
        except Unavailable:
            if proc_info(p) is None and not _is_zombie(p):
                continue                                   # gone between listing and reading
            raise
        per[p] = f["lifetime_max"]
        cur += f["phys_footprint"]
        life += f["lifetime_max"]
    return {"current": cur, "lifetime_sum": life, "per_pid_lifetime": per}


def _is_zombie(pid: int) -> bool:
    ru = _RU4()
    return _LIBPROC.proc_pid_rusage(int(pid), RUSAGE_INFO_V4, ctypes.byref(ru)) == 0 and ru.ri_proc_exit_abstime != 0


def exit_watch(pid: int) -> select.kqueue:
    """A kqueue that reports the pid's exit WITHOUT reaping it, so its final peak can be read first."""
    kq = select.kqueue()
    kq.control([select.kevent(pid, filter=select.KQ_FILTER_PROC, flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                              fflags=select.KQ_NOTE_EXIT)], 0, 0)
    return kq


def exited(kq: select.kqueue) -> bool:
    return bool(kq.control(None, 1, 0))


def exit_peak(pid: int) -> int:
    """The lifetime maximum of an exited, unreaped process (raises Unavailable if it cannot be read)."""
    f = footprint(pid)
    if not f["exited"]:
        raise Unavailable(f"{pid} has not exited")
    return f["lifetime_max"]


# ---- whole-group extinction, anchored to identity (revision 5; Codex RSC 1bf9890 A2 / R3) -------------------------
# A process-group id is the leader's pid. XNU never hands out a pid that is still in use as a process-group id, so
# while ANY member of the group lives (or while its leader is an unreaped zombie of ours) the id names only that
# group. Once the group is empty the pid may be reused - then a live process holds the pid with ANOTHER start time,
# and the recorded group is known to be extinct. Nothing unidentified is ever signalled.
class Survivors(RuntimeError):
    pass


def group_reused(leader: dict) -> bool:
    """True when a live process now holds the recorded leader's pid with another start time (the group is gone)."""
    now = proc_info(leader["pgid"])
    return now is not None and leader["pgid"] == leader["pid"] and now["start"] != leader["start"]


def end_group(leader: dict, members=(), limit: float = 10.0, *, own_leader: bool = False) -> dict:
    """SIGKILL every live member of the leader's process group (enumerated, not only the recorded ones) and every
    recorded member identity outside it, until none remains; raise Survivors past `limit`. own_leader: the caller
    is the leader's unreaped parent, so killpg is safe for the whole loop. Returns what was killed and the time."""
    pgid, t, killed = int(leader["pgid"]), time.monotonic(), {}
    members = [m for m in members if m]
    while True:
        live = {} if (not own_leader and group_reused(leader)) else task_processes([], {pgid})
        if own_leader or same_process(leader):
            try:
                os.killpg(pgid, 9)
            except (ProcessLookupError, PermissionError):
                pass
        for p, i in live.items():
            if same_process(i):
                try:
                    os.kill(p, 9)
                    killed[str(p)] = i
                except ProcessLookupError:
                    pass
        out_of_group = [m for m in members if same_process(m)]
        for m in out_of_group:
            try:
                os.kill(m["pid"], 9)
                killed[str(m["pid"])] = m
            except ProcessLookupError:
                pass
        if not live and not out_of_group:
            return {"killed": list(killed.values()), "seconds": round(time.monotonic() - t, 4)}
        if time.monotonic() - t > limit:
            raise Survivors(f"process group {pgid}: {sorted(live)} and members "
                            f"{[m['pid'] for m in out_of_group]} survive SIGKILL after {limit} s")
        time.sleep(0.02)


IDENT_KEYS = {"pid", "ppid", "pgid", "start"}


def valid_ident(i) -> bool:
    """A recorded identity: exactly pid, ppid, pgid (positive ints, never bool) and the start time 'sec.usec'."""
    import re
    return (isinstance(i, dict) and set(i) == IDENT_KEYS and
            all(isinstance(i[k], int) and not isinstance(i[k], bool) and i[k] >= 0 for k in ("pid", "ppid", "pgid"))
            and i["pid"] > 0 and i["pgid"] > 0 and isinstance(i["start"], str) and
            re.fullmatch(r"\d+\.\d{6}", i["start"]) is not None)


def _sysctl(name: str, obj) -> None:
    n = ctypes.c_size_t(ctypes.sizeof(obj))
    if _LIBC.sysctlbyname(name.encode(), ctypes.byref(obj), ctypes.byref(n), None, 0) != 0:
        raise Unavailable(f"sysctlbyname({name}) errno {ctypes.get_errno()}")


class _XSW(ctypes.Structure):
    _fields_ = [("total", ctypes.c_uint64), ("avail", ctypes.c_uint64), ("used", ctypes.c_uint64),
                ("pagesize", ctypes.c_uint32), ("encrypted", ctypes.c_bool)]


def swap_used() -> int:
    x = _XSW()
    _sysctl("vm.swapusage", x)
    return int(x.used)


def pressure_level() -> int:
    v = ctypes.c_int()
    _sysctl("kern.memorystatus_vm_pressure_level", v)
    return int(v.value)


# ---- the fixture (synthetic; no model, no development input) ---------------------------------------------------
_CHILD = r"""
import gc, sys, time, json, numpy as np, mlx.core as mx
G = 1 << 30
step = sys.argv[1]
if step == "nocache":
    mx.set_cache_limit(0)
host = np.ones(G // 8, dtype=np.float64); host += 1                     # 1 GiB host, touched
dev = mx.ones((G // 4,), dtype=mx.float32); mx.eval(dev)                # 1 GiB MLX active
t = mx.random.normal((G // 4,)); mx.eval(t); u = t * 2; mx.eval(u)      # 2 GiB of temporaries ...
del t, u; gc.collect()                                                   # ... freed into the MLX cache
if step == "spike":
    s = np.ones(2 * G // 8, dtype=np.float64); s += 1; del s            # a 2 GiB transient host spike, released
print(json.dumps({"mlx_active": mx.get_active_memory(), "mlx_cache": mx.get_cache_memory()}), flush=True)
time.sleep(30)
"""
_RATE = r"""
import time, json, numpy as np
G = 1 << 30
t = time.monotonic(); a = np.ones(8 * G // 8, dtype=np.float64); a += 1; dt = time.monotonic() - t
print(json.dumps({"bytes": 8 * G, "seconds": dt}), flush=True)
"""
_EXIT = r"""
import numpy as np, time
a = np.ones(2 * (1 << 30) // 8); a += 1; del a; time.sleep(0.1)
"""
_RATE_MT = r"""
import time, json, threading, numpy as np
G, N = 1 << 30, int(__import__("sys").argv[1])
def touch():
    a = np.empty(2 * G // 8, dtype=np.float64); a.fill(1.0)
ts = [threading.Thread(target=touch) for _ in range(N)]
t = time.monotonic()
for x in ts: x.start()
for x in ts: x.join()
print(json.dumps({"bytes": 2 * G * N, "seconds": time.monotonic() - t}), flush=True)
"""
_GROW = r"""
import numpy as np, sys
G = 1 << 30
print("ready", flush=True); sys.stdin.readline()
a = np.empty(16 * G // 8, dtype=np.float64); a.fill(1.0)
"""


def fixture(python: str) -> dict:
    G = 1 << 30
    out = {}
    for step in ("steady", "nocache", "spike"):
        p = subprocess.Popen([python, "-c", _CHILD, step], stdout=subprocess.PIPE, text=True)
        info = json.loads(p.stdout.readline())
        time.sleep(1.0)
        t = time.monotonic()
        fp = footprint(p.pid)
        sample_s = time.monotonic() - t
        p.kill()
        p.wait()
        out[step] = {"phys_footprint_gib": round(fp["phys_footprint"] / G, 3),
                     "lifetime_max_gib": round(fp["lifetime_max"] / G, 3),
                     "host_gib": 1.0, "mlx_active_gib": round(info["mlx_active"] / G, 3),
                     "mlx_cache_gib": round(info["mlx_cache"] / G, 3),
                     "allocated_now_gib": round(1.0 + (info["mlx_active"] + info["mlx_cache"]) / G, 3),
                     "sample_seconds": round(sample_s, 6)}
    p = subprocess.Popen([python, "-c", _EXIT])
    kq = exit_watch(p.pid)
    kq.control(None, 1, 30)
    peak = exit_peak(p.pid)
    p.wait()
    out["exit_peak_before_reap_gib"] = round(peak / G, 3)
    r = subprocess.run([python, "-c", _RATE], capture_output=True, text=True, timeout=120)
    rate = json.loads(r.stdout)
    out["max_growth_gib_per_s"] = round(rate["bytes"] / rate["seconds"] / G, 2)
    mt = {}
    for n in (2, 4, 8):                                  # several threads touching at once (the margin's rate)
        r = subprocess.run([python, "-c", _RATE_MT, str(n)], capture_output=True, text=True, timeout=180)
        d = json.loads(r.stdout)
        mt[str(n)] = round(d["bytes"] / d["seconds"] / G, 2)
    out["growth_gib_per_s_threads"] = mt
    # SIGKILL delivery overshoot: a writer growing as fast as it can is sampled every 20 ms and killed the instant a
    # reading crosses 4 GiB; the exit peak (unreaped) minus that reading is the growth between observation and death.
    p = subprocess.Popen([python, "-c", _GROW], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    p.stdout.readline()
    kq = exit_watch(p.pid)
    p.stdin.write("go\n")
    p.stdin.flush()
    seen, t0 = 0, time.monotonic()
    while seen < 4 * G and time.monotonic() - t0 < 30:
        seen = footprint(p.pid)["lifetime_max"]
        if seen >= 4 * G:
            t1 = time.monotonic()
            os.kill(p.pid, 9)
            break
        time.sleep(0.02)
    kq.control(None, 1, 10)
    dead = exit_peak(p.pid)
    p.wait()
    out["sigkill_overshoot"] = {"observed_gib": round(seen / G, 3), "exit_peak_gib": round(dead / G, 3),
                                "overshoot_gib": round((dead - seen) / G, 3),
                                "kill_to_exit_s": round(time.monotonic() - t1, 4)}
    t = time.monotonic()
    for _ in range(1000):
        task_processes([os.getpid()], {os.getpgrp()})
    out["task_listing_seconds"] = round((time.monotonic() - t) / 1000, 6)
    return out


if __name__ == "__main__":
    print(json.dumps(fixture(sys.argv[2] if len(sys.argv) > 2 else sys.executable), indent=1))
