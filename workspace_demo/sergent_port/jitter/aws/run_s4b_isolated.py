"""Execution harness for S4b on an AWS host (25 Oct 2026): the same task list and the same frozen task function as
`s4.py s4b` (s4.ensure_run_record, s4.pending(s4.s4b_tasks(kind), shard), s4.run_task), but each task runs in a FRESH
process (concurrent.futures ProcessPoolExecutor, spawn, max_tasks_per_child=1).

Why: the first S4b recovery hosts (rec shards 2-4, 13:07-14:13Z) died with rc 1 after about an hour. Their memory rose by
about 7 GB every 5 min while tasks completed (142 of 184 GB at the last sample): each long-lived loky worker keeps every
compiled function it has seen, and full-data datasets differ in trial count, so the cache grows with every task. One
process per task bounds the memory to one task's footprint; JAX start-up and compilation cost tens of seconds against tasks
of an hour. A task that raises is logged and the queue continues (its result file stays absent, so the manifest shows it
PENDING), where joblib's Parallel stopped the whole host. Not part of the scientific code: s2/s4/s5 and the five hashed
modules are untouched, so the run record (fingerprint, runner hash) is unchanged.

    python run_s4b_isolated.py --workers 96 --shard i/K --kind rec|cv [--wait-h H]      (from the jitter directory)
"""
import argparse
import multiprocessing as mp
import os
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, os.getcwd())
import s4  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=96)
    ap.add_argument("--shard", default=None)
    ap.add_argument("--kind", required=True, choices=["cv", "rec", "all"])
    ap.add_argument("--wait-h", type=float, default=0.0)
    a = ap.parse_args()
    s4.ensure_run_record(f"S4b {a.kind}")
    bases = s4.load_bases()
    c0 = s4.load_c0(a.wait_h * 3600.0) if a.kind == "rec" else s4.load_s4a()["c0"]
    todo = s4.pending(s4.s4b_tasks(a.kind), a.shard)
    label = f"S4b {a.kind} shard {a.shard or '1/1'} (isolated)"
    print(f"[s4] {label}: {len(todo)} tasks on {a.workers} workers, one process per task, start "
          f"{time.strftime('%H:%M:%SZ', time.gmtime())}", flush=True)
    t0, done, failed = time.time(), 0, []
    with ProcessPoolExecutor(max_workers=a.workers, mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex:
        futs = {ex.submit(s4.run_task, t, bases, c0): t for t in todo}
        for f in as_completed(futs):
            t = futs[f]
            try:
                f.result()
                done += 1
            except Exception:  # noqa: BLE001 - logged, the queue continues
                failed.append(t["path"])
                print(f"[s4] TASK FAILED {t['path']}:\n{traceback.format_exc()}", flush=True)
            if (done + len(failed)) % 50 == 0:
                print(f"[s4] {label}: {done} done, {len(failed)} failed of {len(todo)} at {time.time() - t0:.0f} s", flush=True)
    print(f"[s4] {label}: done {done} tasks, {len(failed)} failed, in {time.time() - t0:.0f} s", flush=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
