"""Photograph arm, Stage A (row 20): the WATCHDOG - revision 4 (Codex RSC 081f17b closure group 2; framework 8.4 (m)).
A separate, tiny, standard-library process the controller starts beside every worker, in its own session (outside the
worker's process group), so neither the worker nor a blocked controller can stop it. It holds three conditions the
controller's own loop could miss:

  CONTROLLER DEATH   kqueue NOTE_EXIT on the controller's pid (checked with its recorded start time), so a worker
                     cannot outlive a dead controller;
  HEARTBEAT LOSS     the controller's durable record (controller.json) not rewritten for STALE_S seconds - the
                     controller is alive but blocked (hashing, a hung call, an fsync), so its deadline path is stalled;
  HARD DEADLINE      a monotonic instant a little after the controller's own phase deadline (the controller normally
                     stops the worker first and records it; this fires only if it did not).

On any of them it sends SIGTERM to the worker's process group, waits GRACE_S, sends SIGKILL, waits until the group is
empty (killpg -> ESRCH) and writes watchdog_<session>_<phase>.json (reason, wall times of the observation, the kill
and the empty group) durably; the controller's next start charges the unseen interval from that record. It exits on
its own as soon as the worker's group is empty. It never signals anything but the worker's process group, whose id
cannot be reused while any member lives.

    stage_a_watchdog.py '<json: controller_pid, controller_start, pgid, deadline_monotonic, beat_file, stale_s,
                         grace_s, record>'
"""

import json
import os
import select
import signal
import sys
import time

POLL_S = 0.1


def group_alive(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:                        # only exited, unreaped members remain (measured: EPERM)
        return False


def write_record(path: str, rec: dict) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    dfd = os.open(os.path.dirname(path), os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


def main() -> int:
    a = json.loads(sys.argv[1])
    pgid, cpid = int(a["pgid"]), int(a["controller_pid"])
    kq = select.kqueue()
    try:
        kq.control([select.kevent(cpid, filter=select.KQ_FILTER_PROC, flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                                  fflags=select.KQ_NOTE_EXIT)], 0, 0)
        controller_gone = False
    except OSError:
        controller_gone = True                     # the controller is already gone
    reason = None
    while True:
        if not group_alive(pgid):
            return 0
        if controller_gone or kq.control(None, 1, 0):
            reason = "controller died"
        elif time.monotonic() >= float(a["deadline_monotonic"]):
            reason = "hard deadline"
        else:
            try:
                age = time.time() - os.stat(a["beat_file"]).st_mtime
            except FileNotFoundError:
                age = float("inf")
            if age > float(a["stale_s"]):
                reason = f"heartbeat stale ({age:.1f} s)"
        if reason:
            break
        time.sleep(POLL_S)
    observed = time.time()
    how = "SIGTERM"
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    t = time.monotonic()
    while group_alive(pgid) and time.monotonic() - t < float(a["grace_s"]):
        time.sleep(0.05)
    if group_alive(pgid):
        how = "SIGKILL"
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    killed = time.time()
    t = time.monotonic()
    while group_alive(pgid) and time.monotonic() - t < 10.0:
        time.sleep(0.02)
    gone = not group_alive(pgid)
    write_record(a["record"], {"reason": reason, "pgid": pgid, "how": how, "observed_wall": observed,
                               "killed_wall": killed, "group_gone_wall": time.time() if gone else None,
                               "group_gone": gone, "watchdog_pid": os.getpid()})
    return 3 if gone else 4


if __name__ == "__main__":
    sys.exit(main())
