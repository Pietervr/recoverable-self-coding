"""Photograph arm, Stage A (row 20) and the AI-reader job: the WATCHDOG - revision 5 (Codex RSC 1bf9890 A2, A3, A4 and
R3; framework 8.4 (m)). A separate, small process the controller (or the reader's orchestrator) starts beside every
worker, in its own session (outside the worker's process group), so neither the worker nor a blocked controller can
stop it. Standard library plus memprobe (ctypes/libproc, in-process).

ARMING. It first checks the controller it was given by IDENTITY (pid AND start time) and the worker leader's identity,
registers kqueue NOTE_EXIT on the controller, and only then prints `ARMED` on stdout; the controller releases the
worker (its start gate) only after reading that line. If the controller is already gone or is not the recorded process,
the watchdog acts at once.

CONDITIONS (any one fires):
  CONTROLLER DEATH   kqueue NOTE_EXIT on the controller (or its identity no longer live);
  HEARTBEAT LOSS     the controller's durable beat file not rewritten for stale_s - the controller is alive but blocked;
  SAMPLER LOSS       (optional, Stage A) the controller's sampler stopped ticking on the tick pipe for tick_stale_s
                     after its first tick - the memory observation is stalled; a tick byte 'E' disarms it when the
                     controller has seen the worker's exit and is cleaning up itself;
  HARD DEADLINE      a monotonic instant a little after the controller's own deadline.

ACTION. SIGKILL at once (no grace: a resource stop must be prompt), then every live member of the worker's process group
- enumerated and anchored to the recorded leader identity (memprobe.end_group) - and every recorded member identity in
the members file (escaped descendants), until none remains. On HEARTBEAT LOSS or HARD DEADLINE the controller is alive
but not acting: it is then killed too, by identity, after the group (a blocked controller's time is bounded and its
death time recorded for the crash charge). The record watchdog_<...>.json (reason, session, the wall times of the
observation, the kill, the group's extinction and the controller's death) is written durably. It exits when the group
and the recorded members are gone and its controller has finished with it (an ordinary, controller-led end: the group
is gone and no condition fired -> exit 0, no record).

    stage_a_watchdog.py '<json: controller {pid,ppid,pgid,start}, leader {pid,ppid,pgid,start}, session, beat_file,
                         stale_s, deadline_monotonic, record, members_file|null, tick_fd|null, tick_stale_s>'
"""

import json
import os
import select
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memprobe  # noqa: E402

POLL_S = 0.01


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


def members(path) -> list[dict]:
    if not path:
        return []
    try:
        d = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return []
    vals = d.values() if isinstance(d, dict) else d
    return [m for m in vals if memprobe.valid_ident(m)]


def group_live(leader: dict) -> bool:
    if memprobe.same_process(leader):
        return True
    return (not memprobe.group_reused(leader)) and bool(memprobe.task_processes([], {leader["pgid"]}))


def main() -> int:
    a = json.loads(sys.argv[1])
    ctl, leader = a["controller"], a["leader"]
    kq = select.kqueue()
    reason = None
    if not memprobe.same_process(ctl):
        reason = "controller died (not the recorded process at arming)"
    else:
        try:
            kq.control([select.kevent(ctl["pid"], filter=select.KQ_FILTER_PROC,
                                      flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT, fflags=select.KQ_NOTE_EXIT)], 0, 0)
        except OSError:
            reason = "controller died (before arming)"
    tick_fd = a.get("tick_fd")
    if tick_fd is not None:
        os.set_blocking(int(tick_fd), False)
    sys.stdout.write("ARMED\n")
    sys.stdout.flush()
    last_tick, ticking, eof = None, False, False
    while reason is None:
        if not group_live(leader):
            return 0
        if kq.control(None, 1, 0) or not memprobe.same_process(ctl):
            reason = "controller died"
            break
        if time.monotonic() >= float(a["deadline_monotonic"]):
            reason = "hard deadline"
            break
        try:
            age = time.time() - os.stat(a["beat_file"]).st_mtime
        except FileNotFoundError:
            age = float("inf")
        if age > float(a["stale_s"]):
            reason = f"heartbeat stale ({age:.1f} s)"
            break
        if tick_fd is not None and not eof:
            try:
                b = os.read(int(tick_fd), 4096)
                if b == b"":
                    eof = True
                elif b"E" in b:
                    ticking = False
                    eof = True                          # disarmed: the controller handles the exited worker itself
                else:
                    last_tick, ticking = time.monotonic(), True
            except BlockingIOError:
                pass
            if ticking and time.monotonic() - last_tick > float(a["tick_stale_s"]):
                reason = f"sampler stale ({time.monotonic() - last_tick:.3f} s)"
                break
        time.sleep(POLL_S)
    observed = time.time()
    rec = {"reason": reason, "session": a.get("session"), "pgid": leader["pgid"], "how": "SIGKILL",
           "observed_wall": observed, "watchdog_pid": os.getpid()}
    try:
        res = memprobe.end_group(leader, members(a.get("members_file")), limit=10.0)
        rec.update(killed_wall=time.time(), group_gone=True, group_gone_wall=time.time(),
                   killed=[k["pid"] for k in res["killed"]])
    except memprobe.Survivors as exc:
        rec.update(killed_wall=time.time(), group_gone=False, group_gone_wall=None, survivors=str(exc))
    if reason.startswith(("heartbeat stale", "hard deadline")) and memprobe.same_process(ctl):
        try:
            os.kill(ctl["pid"], signal.SIGKILL)
        except ProcessLookupError:
            pass
        t = time.monotonic()
        while memprobe.same_process(ctl) and time.monotonic() - t < 10.0:
            time.sleep(0.02)
        rec["controller_killed"] = not memprobe.same_process(ctl)
    rec["controller_gone_wall"] = time.time() if not memprobe.same_process(ctl) else None
    write_record(a["record"], rec)
    return 3 if rec["group_gone"] else 4


if __name__ == "__main__":
    sys.exit(main())
