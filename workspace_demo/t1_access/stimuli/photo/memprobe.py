"""Out-of-process task memory for the Stage A controller (closure group 3): proc_pid_rusage(RUSAGE_INFO_V4) on another
process of the same user, no privilege needed. Fields used: ri_phys_footprint (the kernel's physical-footprint ledger
now) and ri_lifetime_max_phys_footprint (the kernel's own running maximum of that ledger over the process's life,
so a transient peak between two samples is still seen). `python memprobe.py fixture` runs the declared
non-development mixed-allocation fixture (no model): a child allocates host (numpy), MLX device arrays and MLX
cache simultaneously and disjointly, and the parent compares the ledger with the sum of what was allocated."""

from __future__ import annotations

import ctypes
import ctypes.util
import json
import os
import subprocess
import sys
import time

RUSAGE_INFO_V4 = 4
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


_LIBPROC = ctypes.CDLL(ctypes.util.find_library("proc") or "/usr/lib/libproc.dylib")
_LIBPROC.proc_pid_rusage.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]


class Unavailable(RuntimeError):
    pass


def footprint(pid: int) -> dict:
    ru = _RU4()
    rc = _LIBPROC.proc_pid_rusage(int(pid), RUSAGE_INFO_V4, ctypes.byref(ru))
    if rc != 0 or ru.ri_phys_footprint == 0:
        raise Unavailable(f"proc_pid_rusage({pid}) failed rc={rc} errno={ctypes.get_errno()}")
    return {"phys_footprint": int(ru.ri_phys_footprint), "lifetime_max": int(ru.ri_lifetime_max_phys_footprint),
            "resident": int(ru.ri_resident_size)}


_CHILD = r"""
import sys, time, json, numpy as np, mlx.core as mx
G = 1 << 30
step = sys.argv[1]
host = np.ones(G // 8, dtype=np.float64); host += 1          # 1 GiB host, touched
dev = mx.ones((G // 4,), dtype=mx.float32); mx.eval(dev)     # 1 GiB MLX array
def _cache():
    t = mx.ones((G // 4,), dtype=mx.float32); mx.eval(t)
_cache()                                                      # 1 GiB freed into the MLX cache
print(json.dumps({"ready": True, "mlx_active": mx.get_active_memory(), "mlx_cache": mx.get_cache_memory(),
                  "mlx_peak": mx.get_peak_memory()}), flush=True)
if step == "spike":
    s = np.ones(2 * G // 8, dtype=np.float64); s += 1; del s           # a 2 GiB transient host spike, released
    print(json.dumps({"spiked": True}), flush=True)
time.sleep(30)
"""


def fixture(python: str) -> dict:
    out = {}
    for step in ("steady", "spike"):
        p = subprocess.Popen([python, "-c", _CHILD, step], stdout=subprocess.PIPE, text=True)
        info = json.loads(p.stdout.readline())
        if step == "spike":
            json.loads(p.stdout.readline())
        time.sleep(1.0)
        t = time.monotonic()
        fp = footprint(p.pid)
        sample_s = time.monotonic() - t
        p.kill()
        p.wait()
        G = 1 << 30
        out[step] = {**{k: round(v / G, 3) for k, v in fp.items()},
                     "allocated_simultaneously_gib": round(1.0 + (info["mlx_active"] + info["mlx_cache"]) / G, 3),
                     "mlx_active_gib": round(info["mlx_active"] / G, 3), "mlx_cache_gib": round(info["mlx_cache"] / G, 3),
                     "sample_seconds": round(sample_s, 6)}
    out["expected_transient_peak_gib"] = round(out["spike"]["allocated_simultaneously_gib"] + 2.0, 3)
    return out


if __name__ == "__main__":
    print(json.dumps(fixture(sys.argv[2] if len(sys.argv) > 2 else sys.executable), indent=1))
