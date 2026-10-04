"""Photograph arm, Stage A (row 20): the INDEPENDENT CONTROLLER - revision 12 (Codex 5eb51a8: a gates hold is durable; the
watchdog-gone wait keeps every live control); revision 11 (the 2 October run: a watchdog gone
before a confirmed leader exit waits for it, else HOLDS; the owner's terminal release); revision 10 (Codex RSC dda950b: a foreign start still alive
before the lock is ended by its retained identity before its charge is final); revision 9 (Codex RSC 7fdb937 A1: every
guardian record of an unnamed start is charged - armed, exited, released or killed, a temporary included);
revision 8 (Codex RSC 12a7f20 Stage A A: pending
starts accumulate and are removed only once absorbed; a longer deadline is durable before the guardian moves to
it; a start that died before publishing its pending entry is charged from its guardian's record); revision 5 (Codex RSC 1bf9890 A2, A3, A4, A5 and A7;
revision 4 answered RSC 081f17b). A separate process that owns the task lock, the clock, the resource limits,
termination and reaping; every phase - the desk gates included - runs as a WORKER subprocess it spawns, watches from
outside and reaps, with a WATCHDOG process (stage_a_watchdog.py) beside it that the worker cannot stop and a blocked
controller cannot delay.

    .venv-image/bin/python stimuli/photo/stage_a_controller.py run      # gates -> instrumented -> native -> report
    .venv-image/bin/python stimuli/photo/stage_a_controller.py supplement   # revision 16: the row-20 OS bridge

REVISION 16 (the row-20 OS-bridge supplement, Codex b0db0f9): the file and phase names became class attributes
(Controller.NAMES, GATES_PHASE, REPORT_PHASE, set_terminal_fn, terminal_active_fn) with Stage A's values unchanged;
SupplementController runs the same mechanism in captures/photo_stage_a_supplement under SUPPLEMENT_NAMES, with row
20's carried seconds and remaining storage, its own terminal record and receipt check. Nothing below changes for Stage A.

ORDER: clock from the process's own start -> lock -> load and VALIDATE the durable record (finite, non-negative
accounting; an absent controller.json beside any existing task output is lost accounting and refuses) -> if the last
controller died, RECONCILE its workers: every live member of each recorded worker's process group (enumerated, anchored
to the leader's identity), every recorded member identity, and only then the watchdog - SIGKILL and verified extinction
before the safeguard retires; charge its tail -> supersede any earlier STAGE_A_FINAL.json, its admission marker and
the report receipt -> the GATES worker -> per work phase: guarded start, sample, cleanup, reap, verify -> the report
worker (always, also after a stop; never after a refusal or a hold) -> close and finalise under one bounded allowance.

GUARDED START (A2). One cleanup owner from before the first spawn: the worker is spawned behind a start gate (a shell
that execs the worker only after reading 'GO' on stdin; EOF -> exit 97, nothing ran); the exit watch is registered;
the worker's identity (pid, start) is read; the watchdog is spawned with the controller's and the leader's identities
and must answer 'ARMED' within ARM_TIMEOUT_S, its own identity read; the record holding both identities is persisted
durably; only then is 'GO' written. A failure at any of these steps ends the gated worker - which has run nothing - and
reaps it. A phase never starts while an earlier worker or watchdog handle exists: that worker is ended first.

OBSERVATION (A3). The main thread is the SAMPLER and does no file I/O: each iteration (sleep MEM_SAMPLE_S = 0.02 s)
reads the worker's exit (kqueue, not reaping), the deadline, the watchdog's liveness, the task's processes and their
memory, every SYS_SAMPLE_S swap and pressure (sysctl, in-process), and writes one tick byte to the watchdog; an
iteration whose work exceeds SAMPLE_LIMIT_S = 0.05 s stops. A separate I/O thread persists the record and the members
file every HEARTBEAT_S and sums the output tree; a failure there stops the run through the sampler. The watchdog kills
the worker group if no tick's source reading is newer than TICK_STALE_S = 0.15 s (a hung sampler), and kills the
group AND the controller if
the durable beat is STALE_S = 10 s old (a blocked controller) or the hard deadline passes.

WHOLE-TASK MEMORY (A3). The task = the controller, the watchdog, the worker and every process in its group or descended
from it. Each sampled process's lifetime maximum is kept BY IDENTITY (pid + start); a worker's exit maximum is read
from the exited, unreaped leader (exit_peak) before the reap and folded in. The task aggregate = max over the session's
phases of (the sum of that phase's member maxima) + the controller's lifetime maximum read at finalisation (or the
live sampled sum, if larger). A phase whose aggregate reaches MEM_STOP at exit stops. PASS needs 0 < aggregate < 48 GiB
AND every mandatory measurement: each worker's exit peak and the controller's final self sample - a missing one is
STOPPED. Stop at MEM_STOP = 44 GiB.

PROMPT STOPS AND THE MARGIN. Every controller stop SIGKILLs the worker's group at once (no SIGTERM grace). The
configured observation interval from the previous successful reading is the gap between two readings of a process (two
iterations of at most SAMPLE_LIMIT_S each plus one MEM_SAMPLE_S sleep: 0.12 s) or, with a hung sampler, that reading's
own time + TICK_STALE_S + the watchdog's 10 ms poll (0.16 s); the kill's delivery is measured, not bounded. The 4 GiB
margin between the stop and the cap holds for growth below 4 GiB / (that interval + delivery); the measured endpoints
and synthetic rates are in controller_fixtures.json and STAGE_A_CRITERIA.md §00 states where the margin holds and where
it does not.

CLOCK (A4). Row 20's time = carried 1,808.73 s + every session's live seconds counted from the controller process's
own start (before configuration, recovery and superseding), durable every HEARTBEAT_S with the wall time of the beat.
Closing a session charges, at the close, the whole bounded closure CLOSE_CHARGE_S = FINAL_ALLOWANCE_S 50 + revocation
5 + exit/output 5 = 60 s and moves the guardian's deadline to its end; a timer ends the process (exit 75, nothing
admitted) if finalisation overruns its allowance. A dead OPEN session is charged at restart its live time + a tail: to
a recorded controller death; without one, on the same boot, until min(now, the guardian's deadline + 5 s); after a
reboot the declared 60 s; the tail is never less than TAIL_RESERVE_S = 60 s. A FAILED START (an accumulated entry of
controller.starting.json, or a guardian record of a start that died before publishing one) is charged from its start
to its recorded death; without one, on the same boot, until min(now, its last durable deadline + 5 s), which can be
below 60 s; after a reboot or for an unreadable entry, 60 s. RESERVES INSIDE THE 4 h
CAP: TAIL 60 s, STOP 60 s, REPORT 600 s; work phases end at cap - 720 s, the report at cap - 60 s; the watchdog's hard
deadline is HARD_MARGIN_S = 5 s after the controller's. Caps are never reset.

STORAGE. Every writer reserves (enforce.configure_storage): work writes under cap - 64 MiB, finalisation writes under the
full cap; the I/O thread sums the output tree and stops a work phase over its limit. STAGE_A_FINAL.json's storage figure
includes its own bytes and its admission marker's (a fixed point checked after the write).

DURABLE COMPLETION (A5). STAGE_A_FINAL.json is written first; then, only if the tree's size equals the declared figure,
STAGE_A_FINAL.ADMITTED.json names the final record's sha256 and session. `final_admitted()` admits a final record only
with that marker. A failure or block after the final record's rename leaves no marker; a failure after the marker's
rename removes the marker before the exit 75; a size mismatch rewrites the record STOPPED with no marker.

FINAL (A7). PASS only if, in THIS session, the report worker exited 0 and wrote report/REPORT_RECEIPT.json last with
exactly the receipt schema, naming this session, the gates' package and identity and the sha256 of EXACTLY the four
report outputs (both SVG figures, the Markdown, the machine JSON), every one matching on disk, and the machine JSON's
session, admissibility and validator flags equal to the receipt's; its validator passed and it was admissible; no
TERMINAL record; the ledger's legal domains hold (enforce.check_ledger); every mandatory measurement exists; and every
cap holds on the final figures.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import select
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
from enforce import (CAPS, MEMORY_CAP as CAPS_MEMORY, GiB, MiB, check_ledger, configure_storage, dir_bytes,  # noqa: E402
                     write_json_atomic)

HEARTBEAT_S, MEM_SAMPLE_S, SYS_SAMPLE_S, SAMPLE_LIMIT_S, TICK_STALE_S = 1.0, 0.02, 1.0, 0.05, 0.15
# TICK_STALE_S (rev 7): staleness is measured from a tick's SOURCE reading time; the longest legitimate gap between two
# readings' ticks is 2 x 50 ms work + 20 ms sleep = 0.12 s, so 0.15 s; stalled: 0.15 + the 10 ms poll = 0.16 s.
TAIL_RESERVE_S, STOP_RESERVE_S, REPORT_RESERVE_S, FINAL_ALLOWANCE_S = 60.0, 60.0, 600.0, 50.0
STALE_S, HARD_MARGIN_S, GROUP_GONE_S, ARM_TIMEOUT_S = 10.0, 5.0, 10.0, 10.0
SETUP_DEADLINE_S, REVOKE_TIMEOUT_S, EXIT_MARGIN_S = 300.0, 5.0, 5.0
CLOSE_CHARGE_S = FINAL_ALLOWANCE_S + REVOKE_TIMEOUT_S + EXIT_MARGIN_S   # the whole bounded closure (= TAIL_RESERVE_S)
STARTING = "controller.starting.json"
MEM_STOP = 44 * GiB
FINAL_RESERVE_BYTES = 64 * MiB
PHASES = ["instrumented", "native"]
B_PLANNED_ATTEMPTS, B_RESERVE = 1856, 1.25
EXIT_HOLD = 4
GATE = ["/bin/sh", "-c", 'IFS= read -r go || exit 97; [ "$go" = GO ] || exit 97; exec "$@" </dev/null', "stagea"]
WATCHDOG = [sys.executable, str(HERE / "stage_a_watchdog.py")]
FINAL, ADMITTED, ABORTED = "STAGE_A_FINAL.json", "STAGE_A_FINAL.ADMITTED.json", "STAGE_A_FINAL.ABORTED.json"
_unlink = os.unlink                                   # module-level so a fixture can make revocation block
REPORT_OUTPUTS = {"report/rel_l2_by_layer.svg", "report/logit_max_abs.svg", "report/STAGE_A_REPORT.md",
                  "report/stage_a_report.json"}
RECEIPT_KEYS = {"session", "package", "identity", "date", "outputs", "admissible", "validator_pass"}
HEX64 = re.compile(r"[0-9a-f]{64}")
# Revision 16 (the row-20 OS-bridge supplement, Codex b0db0f9): the controller's file and phase names are class
# attributes so that SupplementController runs under its OWN names in its own output tree and never supersedes,
# rewrites or reports over the accepted Stage A bundle. Stage A's values are unchanged.
STAGE_A_NAMES = {"final": FINAL, "admitted": ADMITTED, "aborted": ABORTED, "gates": "GATES.json",
                 "receipt": "report/REPORT_RECEIPT.json"}
SUPPLEMENT_NAMES = {"final": "SUPPLEMENT_FINAL.json", "admitted": "SUPPLEMENT_FINAL.ADMITTED.json",
                    "aborted": "SUPPLEMENT_FINAL.ABORTED.json", "gates": "SUPPLEMENT_GATES.json",
                    "receipt": "supplement/SUPPLEMENT_RECEIPT.json"}
SUPPLEMENT_PHASES = ["supplement_instrumented", "supplement_native"]
SUPPLEMENT_TERMINAL = "SUPPLEMENT_TERMINAL.json"
SUPPLEMENT_RECEIPT_KEYS = {"session", "package", "identity", "date", "outcome", "admissible", "reasons", "input",
                           "attempts", "comparisons", "counters", "compatibility", "outputs"}


def supplement_set_terminal(out: Path, phase: str, reason: str) -> None:
    """The supplement's own terminal record (revision 16): a failure STOPS this version. Same schema as Stage A's
    TERMINAL.json, a different file in the supplement's tree, and NO release path - a stopped supplement is never
    resumed (no retry, no tolerance revision, no next input)."""
    p = Path(out) / SUPPLEMENT_TERMINAL
    entry = {"phase": phase, "reason": str(reason)[:4000], "wall": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
             "pid": os.getpid()}
    t = json.loads(p.read_text()) if p.exists() else None
    if t:
        t.setdefault("later", []).append(entry)
    else:
        t = {"first": entry}
    write_json_atomic(p, t, final=True)


def supplement_terminal_active(out: Path) -> bool:
    return (Path(out) / SUPPLEMENT_TERMINAL).exists()


class ControllerStop(RuntimeError):
    pass


class ControllerHold(RuntimeError):
    """Revision 11: an unresolved control state that is not an integrity failure of the task - the run HOLDS (no
    terminal record, no report) for the owner's review."""


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha_file(p: Path) -> str:
    return _sha(Path(p).read_bytes())


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v >= 0


def default_system_reader() -> dict:
    try:
        return {"swap": memprobe.swap_used(), "pressure": memprobe.pressure_level()}
    except memprobe.Unavailable as exc:
        raise ControllerStop(str(exc)) from exc


def final_admitted(out: Path, names: dict | None = None) -> dict | None:
    """The final record, only when its admission marker names exactly its bytes and session (A5). `names` (revision
    16): the supplement's own final/marker/abort file names (SUPPLEMENT_NAMES); default Stage A's."""
    names = names or STAGE_A_NAMES
    FINAL, ADMITTED, ABORTED = names["final"], names["admitted"], names["aborted"]   # noqa: N806
    f, m = Path(out) / FINAL, Path(out) / ADMITTED
    if not (f.exists() and m.exists()):
        return None
    try:
        mk, fb = json.loads(m.read_text()), f.read_bytes()
        fin = json.loads(fb)
    except (OSError, ValueError):
        return None
    if not isinstance(mk, dict) or set(mk) != {"final_sha256", "session"} or mk["final_sha256"] != _sha(fb) or \
            not isinstance(fin, dict) or fin.get("session") != mk["session"]:
        return None
    ab = Path(out) / ABORTED                           # an abort of that session revokes it, whatever the marker says
    if ab.exists():
        try:
            if json.loads(ab.read_text()).get("session") == mk["session"]:
                return None
        except (OSError, ValueError):
            return None
    return fin


def _say(text: str) -> None:
    """A diagnostic that can never delay a kill or an abort: written by a daemon thread (revision 7)."""
    def w():
        try:
            sys.stderr.write(text + "\n")
            sys.stderr.flush()
        except Exception:                             # noqa: BLE001
            pass
    threading.Thread(target=w, daemon=True).start()


def _process_age_s() -> float:
    """Seconds since this process started (libproc start time), so the session clock includes interpreter start-up
    and imports (A4)."""
    i = memprobe.proc_info(os.getpid())
    return max(0.0, time.time() - float(i["start"])) if i else 0.0


def _guard_set_terminal(out: Path, phase: str, reason: str) -> None:
    from stage_a_guard import set_terminal
    set_terminal(out, phase, reason)


def _guard_terminal_active(out: Path) -> bool:
    from stage_a_guard import terminal_active
    return terminal_active(out)


class Controller:
    NAMES = STAGE_A_NAMES                              # revision 16: overridden by SupplementController only
    GATES_PHASE, REPORT_PHASE = "gates", "report"
    set_terminal_fn = staticmethod(_guard_set_terminal)
    terminal_active_fn = staticmethod(_guard_terminal_active)

    def __init__(self, out: Path, *, carry_seconds: float, worker_cmd, gates: bool = True,
                 row_cap_s: float | None = None, storage_cap: int | None = None, probe=memprobe,
                 system_reader=None, writer=write_json_atomic, clock=time.monotonic, watchdog_cmd=None,
                 from_process_start: bool = False):
        self.out, self.worker_cmd, self.use_gates = Path(out), worker_cmd, gates
        self.cap_s = row_cap_s if row_cap_s is not None else CAPS["row20"]["seconds"]
        self.cap_b = storage_cap if storage_cap is not None else CAPS["row20"]["bytes"]
        self.carry, self.probe, self.writer, self.clock = carry_seconds, probe, writer, clock
        self.system_reader = system_reader or default_system_reader
        self.watchdog_cmd = watchdog_cmd or WATCHDOG
        self.from_process_start = from_process_start      # main(): the clock counts from the process's own start
        self.path = self.out / "controller.json"
        self.session = uuid.uuid4().hex[:12]
        self.proc = self.wd = self.kq = None
        self.tick_w = None
        self._exited_flag = False
        self.gates_rec = None
        self.lock, self.wlock = threading.RLock(), threading.Lock()
        self.io_stop = None
        self.io_run = False

    # ---- the durable record ---------------------------------------------------------------------------------------
    def _write(self, path: Path, obj) -> None:
        self.writer(path, obj, final=True)

    def live(self) -> float:
        return (self.clock() - self.t0) + self.pre_s

    def elapsed_total(self) -> float:
        return self.base + self.live()

    def _load(self) -> dict:
        if not self.path.exists():
            others = [p.name for p in self.out.iterdir() if p.name not in ("LOCK", STARTING) and
                      not p.name.startswith("guardian_")] if self.out.exists() else []
            if others:
                raise SystemExit(f"refused: controller.json is absent beside existing task output {sorted(others)[:6]} "
                                 f"- the accumulated time is lost; the run holds")
            rec = {"carry_s": self.carry, "seconds_total": self.carry, "sessions": [], "open_session": None,
                   "peaks": {"task_lifetime_sum": 0, "phase_aggregates": {}, "storage_bytes": 0,
                             "max_iteration_s": {}},
                   "stops": [], "workers": [], "swap_baseline": None, "reconciled": []}
            self._charge_failed_start(rec)
            return rec
        rec = json.loads(self.path.read_text())
        self._validate_accounting(rec)
        self._charge_failed_start(rec)
        s = rec.get("open_session")
        if s:                                         # the last controller died
            rec["reconciled"].append(self._reconcile(rec, s["session"]))
            wds = [json.loads((self.out / w["watchdog_record"]).read_text()) for w in rec["workers"]
                   if w.get("session") == s["session"] and w.get("watchdog_record") and
                   (self.out / w["watchdog_record"]).exists()]
            gp = self.out / f"guardian_{s['session']}.json"
            g = json.loads(gp.read_text()) if gp.exists() else None
            tail = self._crash_tail(s, wds + ([g] if g else []))
            charged = float(s["live_s"]) + tail
            rec["seconds_total"] += charged
            rec["sessions"].append({**s, "closed": "crashed", "charged_s": charged, "tail_s": tail,
                                    "watchdog": wds[-1] if wds else None, "guardian": g})
            rec["open_session"] = None
        return rec

    @staticmethod
    def _crash_tail(s: dict, records: list) -> float:
        """The unseen tail of a dead session (revision 7, Stage A A). A recorded controller death (guardian or watchdog)
        ends it. Without one: if the machine stayed up since the last beat (kern.boottime earlier than the beat), the
        controller lived at most until its guardian's deadline - charged until min(now, that deadline); after a
        reboot or power loss the declared 60 s rule applies. Never less than TAIL_RESERVE_S."""
        beat = s.get("beat_wall")
        tail = TAIL_RESERVE_S
        if not _num(beat):
            return tail
        deaths = [r["controller_gone_wall"] for r in records if _num(r.get("controller_gone_wall"))]
        groups = [r["group_gone_wall"] for r in records if _num(r.get("group_gone_wall"))]
        if deaths or groups:
            tail = max(tail, max(deaths + groups) - beat)
        try:
            same_boot = memprobe.boot_time() < beat
        except memprobe.Unavailable:
            same_boot = True                               # unknown: the conservative branch
        if same_boot and not deaths:
            dl = s.get("guardian_deadline_wall")
            end = min(time.time(), dl + EXIT_MARGIN_S) if _num(dl) else time.time()
            tail = max(tail, end - beat)
        return tail

    def _read_pending(self) -> list:
        """Every pending start not yet absorbed (revision 8). Unreadable -> one conservative unknown entry."""
        sp = self.out / STARTING
        if not sp.exists():
            return []
        try:
            d = json.loads(sp.read_text())
        except ValueError:
            return [{"session": None, "start_wall": None}]
        items = d.get("pending") if isinstance(d, dict) and "pending" in d else [d]
        if not isinstance(items, list):
            return [{"session": None, "start_wall": None}]
        return [x if isinstance(x, dict) else {"session": None, "start_wall": None} for x in items]

    def _write_pending(self) -> None:
        write_json_atomic(self.out / STARTING, {"pending": [*self.prior_starts, self.my_start]}, final=True)

    @staticmethod
    def _end_foreign(ident) -> float | None:
        """Revision 10 (Codex dda950b): a foreign protected start whose record names no end may still be ALIVE before
        the task lock. Holding the lock, this start ends it by its retained identity (SIGKILL), confirms the death and
        returns that time, so the charge is start -> confirmed end, never a provisional start -> now. Not alive: None.
        Alive and not confirmed dead within GROUP_GONE_S: the run holds (nothing is charged or removed)."""
        if not isinstance(ident, dict) or not isinstance(ident.get("pid"), int) or not memprobe.same_process(ident):
            return None
        try:
            os.kill(ident["pid"], signal.SIGKILL)
        except ProcessLookupError:
            return time.time()
        t = time.monotonic()
        while memprobe.same_process(ident):
            if time.monotonic() - t > GROUP_GONE_S:
                raise SystemExit(f"refused: a foreign Stage A start (pid {ident['pid']}) is still alive and could not be "
                                 f"ended; the run holds")
            time.sleep(0.01)
        return time.time()

    def _failed_start_charge(self, st: dict) -> float:
        """One failed start's charge: from its start to its guardian's recorded controller death if there is one;
        else, on the same boot, until min(now, its last durable deadline + EXIT_MARGIN_S); else (a reboot, or an
        unreadable entry) the declared TAIL_RESERVE_S. A same-boot start that died early is charged its actual
        interval, which can be below 60 s."""
        start = st.get("start_wall")
        if not _num(start):
            return TAIL_RESERVE_S
        g = None
        if isinstance(st.get("session"), str):
            gp = self.out / f"guardian_{st['session']}.json"
            try:
                g = json.loads(gp.read_text()) if gp.exists() else None
            except ValueError:
                g = None
        if g and _num(g.get("controller_gone_wall")):
            return max(0.0, g["controller_gone_wall"] - start)
        ended = self._end_foreign((g or {}).get("controller"))   # revision 10: alive -> ended first
        if ended is not None:
            return max(0.0, ended - start)
        try:
            same_boot = memprobe.boot_time() < start
        except memprobe.Unavailable:
            same_boot = True
        dl = st.get("deadline_wall")
        if same_boot:
            end = min(time.time(), dl + EXIT_MARGIN_S) if _num(dl) else time.time()
            return max(0.0, end - start)
        return TAIL_RESERVE_S

    def _charge_failed_start(self, rec: dict) -> None:
        """Starts that died before their session's first durable record (revision 8, Stage A A): every accumulated
        pending entry, and every guardian death record of a start that died before it could publish its pending
        entry (directory creation, the lock), not yet charged, is charged once and named in the sessions."""
        known = {x.get("session") for x in rec.get("sessions") or []} | {(rec.get("open_session") or {}).get("session")}
        known.discard(None)
        pending = list(getattr(self, "prior_starts", None) or [])
        for st in pending:
            sid = st.get("session")
            if sid == self.session or (isinstance(sid, str) and sid in known):
                continue
            charged = self._failed_start_charge(st)
            rec["seconds_total"] += charged
            rec["sessions"].append({"session": sid, "live_s": 0.0, "closed": "failed_start", "charged_s": charged,
                                    "start_wall": st.get("start_wall"), "deadline_wall": st.get("deadline_wall")})
            if isinstance(sid, str):
                known.add(sid)
        if not self.out.exists():
            return
        recs = {gp.name[len("guardian_"):-len(".json")]: gp for gp in self.out.glob("guardian_*.json")}
        for tp in self.out.glob("guardian_*.json.tmp"):   # a record still being published (revision 9)
            recs.setdefault(tp.name[len("guardian_"):-len(".json.tmp")], tp)
        for sid in sorted(recs):
            if sid == self.session or sid in known:
                continue
            try:
                g = json.loads(recs[sid].read_text())
            except (ValueError, OSError):
                g = {}
            charged = self._guardian_charge(g if isinstance(g, dict) else {})
            rec["seconds_total"] += charged
            rec["sessions"].append({"session": sid, "live_s": 0.0, "closed": "failed_start_before_pending",
                                    "charged_s": charged, "start_wall": g.get("started_wall") if isinstance(g, dict)
                                    else None, "guardian": g or None, "guardian_file": recs[sid].name})
            known.add(sid)

    @classmethod
    def _guardian_charge(cls, g: dict) -> float:
        """A protected start that died before publishing its pending entry (revision 9, Stage A A1): from its start
        to the guardian's recorded end (the controller's death - observed or caused - or its release); a record that
        names no end (the controller died while the guardian was still publishing, or the record stopped at 'armed') is
        charged on the same boot until min(now, its setup deadline + EXIT_MARGIN_S); unreadable or after a reboot,
        TAIL_RESERVE_S."""
        st = g.get("started_wall")
        if not _num(st):
            return TAIL_RESERVE_S
        end = g.get("controller_gone_wall") if _num(g.get("controller_gone_wall")) else g.get("released_wall")
        if _num(end):
            return max(0.0, end - st)
        ended = cls._end_foreign(g.get("controller"))   # revision 10: a live protected start is ended first
        if ended is not None:
            return max(0.0, ended - st)
        try:
            same_boot = memprobe.boot_time() < st
        except memprobe.Unavailable:
            same_boot = True
        if not same_boot:
            return TAIL_RESERVE_S
        dl = g.get("deadline_wall")
        return max(0.0, (min(time.time(), dl + EXIT_MARGIN_S) if _num(dl) else time.time()) - st)

    def _validate_accounting(self, rec) -> None:
        """Finite, non-negative, typed accounting before any use (A4)."""
        bad = []
        if not isinstance(rec, dict):
            raise SystemExit("refused: controller.json is not an object")
        for k in ("carry_s", "seconds_total"):
            if not _num(rec.get(k)):
                bad.append(k)
        if _num(rec.get("carry_s")) and abs(rec["carry_s"] - self.carry) > 1e-9:
            bad.append("carry_s differs from the declared carry")
        if _num(rec.get("seconds_total")) and _num(rec.get("carry_s")) and rec["seconds_total"] < rec["carry_s"]:
            bad.append("seconds_total below the carry")
        for k, ty in (("sessions", list), ("workers", list), ("stops", list), ("reconciled", list), ("peaks", dict)):
            if not isinstance(rec.get(k), ty):
                bad.append(k)
        for s in rec.get("sessions") or []:
            if not isinstance(s, dict) or not _num(s.get("live_s")) or \
                    ("charged_s" in s and not _num(s["charged_s"])):
                bad.append("sessions[]")
                break
        s = rec.get("open_session")
        if s is not None and (not isinstance(s, dict) or not isinstance(s.get("session"), str) or
                              not _num(s.get("live_s")) or not _num(s.get("beat_wall"))):
            bad.append("open_session")
        if bad:
            raise SystemExit(f"refused: controller.json accounting invalid: {bad}; the run holds")

    def _reconcile(self, rec: dict, session: str) -> dict:
        """Every recorded worker group of the crashed session: all its LIVE members (enumerated, anchored to the
        recorded leader identity - a group whose id now belongs to another process is extinct), every recorded member
        identity, killed and confirmed gone; only then its watchdog (the safeguard retires last)."""
        out = {"session": session, "groups": [], "watchdogs_killed": []}
        for w in rec["workers"]:
            if w.get("session") != session or w.get("reaped"):
                continue
            leader = w.get("leader")
            members = [m for m in (w.get("members") or {}).values() if memprobe.valid_ident(m)]
            if memprobe.valid_ident(leader):
                try:
                    res = memprobe.end_group(leader, members, limit=GROUP_GONE_S)
                except memprobe.Survivors as exc:
                    raise SystemExit(f"refused: processes of the crashed session {session} survive SIGKILL: {exc}; "
                                     f"the run holds")
                out["groups"].append({"phase": w.get("phase"), "pgid": leader["pgid"], **res})
            wd = w.get("watchdog")
            if memprobe.valid_ident(wd) and memprobe.same_process(wd):
                try:
                    os.kill(wd["pid"], signal.SIGKILL)
                except ProcessLookupError:
                    pass
                t = time.monotonic()
                while memprobe.same_process(wd):
                    if time.monotonic() - t > GROUP_GONE_S:
                        raise SystemExit(f"refused: the crashed session's watchdog {wd['pid']} survives SIGKILL")
                    time.sleep(0.02)
                out["watchdogs_killed"].append(wd)
        return out

    def _persist(self) -> None:
        live = self.live()
        with self.lock:
            self.rec["open_session"]["live_s"] = live
            self.rec["open_session"]["beat_wall"] = time.time()
            self.rec["seconds_total_live"] = self.base + live
            snap = json.loads(json.dumps(self.rec))
            w = self.rec["workers"][-1] if self.rec["workers"] and self.proc is not None else None
            mem = (w.get("members_file"), dict(w.get("members") or {})) if w and w.get("members_file") else None
        try:
            with self.wlock:
                self._write(self.path, snap)
                if mem:
                    self._write(self.out / mem[0], mem[1])
        except Exception as exc:
            raise ControllerStop(f"persistence failure: {exc!r}") from exc

    def _supersede(self) -> None:
        """No earlier PASS survives into this session: the previous final record, its admission marker and the report
        receipt move aside."""
        sup = self.out / "superseded"
        n = self.NAMES
        for p in (self.out / n["admitted"], self.out / n["aborted"], self.out / n["final"], self.out / n["receipt"]):
            if p.exists():
                sup.mkdir(exist_ok=True)
                os.replace(p, sup / f"{p.stem}.{self.session}{p.suffix}")

    # ---- the run --------------------------------------------------------------------------------------------------
    def run(self, phases=PHASES, emit=None) -> dict:
        """emit: called with the result while the guardian still bounds the process (main prints through it)."""
        self.t0 = self.clock()                         # the clock starts with the process (A4)
        self.pre_s = _process_age_s() if self.from_process_start else 0.0
        self.run_start_wall = time.time() - self.pre_s   # what a failed start is charged from (revision 8)
        from stage_a_guard import TaskLock
        self._start_guardian()                         # before ANY file operation (revision 7, Stage A A)
        try:
            self.out.mkdir(parents=True, exist_ok=True)
            lock = TaskLock(self.out)
        except BaseException:
            self._stop_guardian()
            raise
        try:
            result = self._run(phases)
            if emit is not None:
                emit(result)                           # inside the guardian's charged closure window
            return result
        finally:
            lock.release()
            self._stop_guardian()

    def _run(self, phases) -> dict:
        set_terminal, terminal_active = self.set_terminal_fn, self.terminal_active_fn
        if True:
            configure_storage([self.out], self.cap_b, self.cap_b - FINAL_RESERVE_BYTES)
            self.start_wall = self.run_start_wall
            # Pending starts (revision 8, Stage A A): the file ACCUMULATES every start not yet absorbed into
            # controller.json - it is only ever replaced by a superset, and removed only after the first persist that
            # charges all of them - so a start that dies while reconciling an earlier failed start loses nothing.
            self.prior_starts = self._read_pending()
            self.my_start = {"session": self.session, "start_wall": self.start_wall,
                             "deadline_wall": self.guard_deadline_wall}
            self._write_pending()                     # durable before any load
            self.base = 0.0
            self.rec = self._load()
            self._supersede()
            self.base = self.rec["seconds_total"]
            mono = max(time.monotonic() + (self.cap_s - self.elapsed_total()) + HARD_MARGIN_S,
                       time.monotonic() + CLOSE_CHARGE_S)
            # the longer deadline is durable in this start's pending entry BEFORE the guardian is moved to it
            self.my_start["deadline_wall"] = time.time() + (mono - time.monotonic())
            self._write_pending()
            self._guardian_deadline(mono)
            self.ident = memprobe.proc_info(os.getpid())
            self.rec["open_session"] = {"session": self.session, "pid": os.getpid(), "live_s": 0.0,
                                        "opened_wall": time.time(), "beat_wall": time.time(),
                                        "controller": self.ident, "guardian": self.guard_ident,
                                        "guardian_deadline_wall": self.guard_deadline_wall}
            self._persist()
            self.session_durable = True               # controller.json names this session from here (revision 9)
            (self.out / STARTING).unlink(missing_ok=True)   # controller.json now carries every pending start's charge
            if self.rec["swap_baseline"] is None:
                try:
                    self.rec["swap_baseline"] = self.system_reader()["swap"]
                except Exception as exc:              # no observation, no work: terminal, nothing spawned
                    self._stop(set_terminal, "controller", f"initial system reading failed: {exc}")
                    self._bounded(lambda: self._close("terminal"))
                    return {"outcome": "STOPPED", "reason": "initial system reading failed", "session": self.session}
            if self.use_gates:
                try:
                    g = self._gates()
                except ControllerHold as exc:           # revision 12 (A2): the gates path holds durably too
                    return self._hold(str(exc))
                if g["outcome"] != "PASSED":
                    self._bounded(lambda: self._close(g["outcome"].lower()))
                    return {"outcome": g["outcome"], "reason": g["reason"], "session": self.session}
            terminal = terminal_active(self.out)          # rev 11: an owner-released terminal record lets work resume
            try:
                if not terminal:
                    for ph in phases:
                        if (self.out / f"{ph.upper()}_DONE.json").exists():
                            continue
                        self._phase(ph, deadline=self.cap_s - TAIL_RESERVE_S - STOP_RESERVE_S - REPORT_RESERVE_S,
                                    storage_limit=self.cap_b - FINAL_RESERVE_BYTES)
            except ControllerHold as exc:               # revision 11: a hold, not an integrity failure - no terminal
                return self._hold(str(exc))
            except (ControllerStop, Exception) as exc:
                self._stop(set_terminal, "controller", f"{type(exc).__name__}: {exc}")
            try:                                       # the report: always, inside its reserve (STOPPED after a stop)
                self._phase(self.REPORT_PHASE, deadline=self.cap_s - TAIL_RESERVE_S, storage_limit=self.cap_b,
                            report=True)
            except ControllerHold as exc:
                return self._hold(str(exc))
            except Exception as exc:
                self.rec["stops"].append({"phase": self.REPORT_PHASE, "session": self.session,
                                          "reason": f"{type(exc).__name__}: {exc}"})
            outcome = "terminal" if terminal_active(self.out) else "completed"
            return self._bounded(lambda: (self._close(outcome), self._finalise())[1])

    def _hold(self, reason: str) -> dict:
        """Revision 11: the run HOLDS - the reason recorded, the session closed and charged as usual, no terminal record,
        no report; the owner's review decides the resumption (a resumed run reloads the committed phase records through
        their full independent predicates)."""
        self.rec["stops"].append({"phase": "controller", "session": self.session, "reason": f"HELD: {reason}",
                                  "hold": True, "at_total_s": self.elapsed_total()})
        self._bounded(lambda: self._close("held"))
        return {"outcome": "HELD", "reason": reason, "session": self.session}

    # ---- the guardian: an independent bound on the controller process (Stage A 2) ----------------------------------
    def _start_guardian(self) -> None:
        """A watchdog in GUARDIAN mode, started before any load: it SIGKILLs this controller (by identity) at an absolute
        deadline - first SETUP_DEADLINE_S, then the session's cap + HARD_MARGIN_S - whatever the controller is doing
        (blocked I/O, a hung sample, cleanup, finalisation). Its kill/exit path depends on no observation or
        persistence of the controller's."""
        self.guard_w = None
        r, w = os.pipe()
        ident = memprobe.proc_info(os.getpid())
        arg = {"mode": "guardian", "controller": ident, "session": self.session, "control_fd": r,
               "started_wall": getattr(self, "run_start_wall", time.time()),
               "deadline_wall": time.time() + SETUP_DEADLINE_S,
               "deadline_monotonic": time.monotonic() + SETUP_DEADLINE_S,
               "record": str(self.out / f"guardian_{self.session}.json")}
        try:
            self.guard = subprocess.Popen(self.watchdog_cmd + [json.dumps(arg)], stdout=subprocess.PIPE,
                                          stdin=subprocess.DEVNULL, start_new_session=True, pass_fds=(r,))
        finally:
            os.close(r)
        self.guard_w = w
        self.guard_deadline_wall = time.time() + SETUP_DEADLINE_S
        ready = select.select([self.guard.stdout], [], [], ARM_TIMEOUT_S)[0]
        if not ready or self.guard.stdout.readline().strip() != b"ARMED":
            self._stop_guardian()
            raise SystemExit("refused: the controller's guardian did not arm; nothing was loaded")
        self.guard_ident = memprobe.proc_info(self.guard.pid)

    def _guardian_deadline(self, mono: float) -> None:
        """Move the guardian's deadline; its wall-clock value goes into the open session at the next persist, so a
        restart can bound a dead session's tail without the guardian's own record (revision 7)."""
        if self.guard_w is not None:
            os.write(self.guard_w, f"D {mono:.6f}\n".encode())
            self.guard_deadline_wall = time.time() + (mono - time.monotonic())
            if getattr(self, "rec", None) and self.rec.get("open_session"):
                self.rec["open_session"]["guardian_deadline_wall"] = self.guard_deadline_wall

    def _stop_guardian(self) -> None:
        g = getattr(self, "guard", None)
        if g is None:
            return
        if g.poll() is None and self.guard_w is not None:
            try:                                   # revision 9: X - a durable session, nothing more to record;
                os.write(self.guard_w, b"X\n" if getattr(self, "session_durable", False) else b"E\n")   # E - record
                g.wait(timeout=2.0)
            except (OSError, subprocess.TimeoutExpired):
                pass
        if g.poll() is None:
            try:
                g.terminate()
            except ProcessLookupError:
                pass
        try:
            g.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            g.kill()
            g.wait()
        if g.stdout:
            g.stdout.close()
        if self.guard_w is not None:
            os.close(self.guard_w)
            self.guard_w = None
        self.guard = None

    def _bounded(self, fn):
        """Close and finalisation run under one allowance FINAL_ALLOWANCE_S, charged at the close: past it the process
        ends (exit 75) after removing any admission marker of this session - nothing is admitted (A4/A5)."""
        res, err = {}, []

        def body():
            try:
                res["r"] = fn()
            except BaseException as exc:           # noqa: BLE001 - reported below, then exit 75
                err.append(exc)
        th = threading.Thread(target=body, daemon=True)
        th.start()
        th.join(FINAL_ALLOWANCE_S)
        if th.is_alive() or err:
            _say(f"finalisation did not complete: {(repr(err[0]) if err else 'allowance exceeded')}")
            self._abort_exit()
        return res.get("r")

    def _abort_exit(self) -> None:
        """The abort path, itself bounded (Stage A 3): revocation - an abort tombstone naming this session and the
        removal of this session's admission marker - runs in its own threads for at most REVOKE_TIMEOUT_S; then the
        process ends with exit 75 whatever they did. `final_admitted` refuses a session with a tombstone. The tombstone
        write is file-, rename- and directory-fsynced (enforce.write_atomic) when it returns; the marker's unlink is
        not followed by a directory fsync, so that removal's durability across a power loss is limited; if both block
        or fail, a marker can survive an exit 75 - reviewed as an abort, never a completed transaction."""
        threads = [threading.Thread(target=self._revoke_tombstone, daemon=True),
                   threading.Thread(target=self._unadmit, daemon=True)]
        for t in threads:
            t.start()
        dl = time.monotonic() + REVOKE_TIMEOUT_S
        for t in threads:
            t.join(max(0.0, dl - time.monotonic()))
        os._exit(75)

    def _revoke_tombstone(self) -> None:
        try:
            self._write(self.out / self.NAMES["aborted"], {"session": self.session, "wall": time.time()})
        except Exception:                             # noqa: BLE001
            pass

    def _unadmit(self) -> None:
        try:
            m = self.out / self.NAMES["admitted"]
            if m.exists() and json.loads(m.read_text()).get("session") == self.session:
                _unlink(m)
        except Exception:                             # noqa: BLE001 - best effort; the exit status says no PASS
            pass

    def _gates(self) -> dict:
        """The desk gates as a supervised worker (hashing and git cannot block the controller's loop)."""
        gp = self.out / self.NAMES["gates"]
        if gp.exists():
            os.replace(gp, gp.with_name(gp.stem + ".prev.json"))
        try:
            self._phase(self.GATES_PHASE, deadline=self.cap_s - TAIL_RESERVE_S - STOP_RESERVE_S - REPORT_RESERVE_S,
                        storage_limit=self.cap_b - FINAL_RESERVE_BYTES, gates=True)
        except ControllerStop as exc:
            w = self.rec["workers"][-1] if self.rec["workers"] else {}
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
        """Revision 7: the close charges the WHOLE bounded closure - finalisation (50 s), revocation (5 s) and the
        exit/output margin (5 s) = CLOSE_CHARGE_S - and moves the guardian's deadline to the end of that window, so
        nothing after the close can outlive its charge: a post-close death is inside the charged total."""
        self._self_sample()
        before = dir_bytes([self.out])
        self._guardian_deadline(time.monotonic() + CLOSE_CHARGE_S)
        live = self.live() + CLOSE_CHARGE_S
        with self.lock:
            s = dict(self.rec["open_session"], live_s=live, closed=outcome, allowance_s=CLOSE_CHARGE_S,
                     guardian_deadline_wall=self.guard_deadline_wall)
            self.rec["sessions"].append(s)
            self.rec["seconds_total"] = self.base + live
            self.rec["open_session"] = None
            self.rec["storage_before_close"] = before
            snap = json.loads(json.dumps(self.rec))
        with self.wlock:
            self._write(self.path, snap)

    def _self_sample(self) -> None:
        pk = self.rec["peaks"]
        try:
            f = self.probe.footprint(os.getpid())
        except memprobe.Unavailable as exc:
            pk["controller_final_error"] = str(exc)
            return
        pk["controller_final"] = f["lifetime_max"]
        pk["controller_lifetime_max"] = max(pk.get("controller_lifetime_max", 0), f["lifetime_max"])
        g = getattr(self, "guard", None)              # the guardian is part of the task (revision 7, Stage A B)
        try:
            if g is None:
                raise memprobe.Unavailable("no guardian")
            gf = self.probe.footprint(g.pid)
            pk["guardian_final"] = gf["lifetime_max"]
            pk["guardian_lifetime_max"] = max(pk.get("guardian_lifetime_max", 0), gf["lifetime_max"])
        except memprobe.Unavailable as exc:
            pk["guardian_final_error"] = str(exc)

    # ---- memory aggregate (A3) ------------------------------------------------------------------------------------
    def _key(self, pid: int, procs: dict) -> str:
        if pid == os.getpid():
            return "controller"
        if getattr(self, "guard", None) is not None and pid == self.guard.pid:
            return "guardian"
        i = procs.get(pid) or (self.wd_ident if self.wd is not None and pid == self.wd.pid else None)
        return f"{pid}:{i['start']}" if i else f"{pid}:?"

    def _fold(self, w: dict, procs: dict, smp: dict) -> None:
        mm = w.setdefault("member_max", {})
        for p, life in smp["per_pid_lifetime"].items():
            k = self._key(p, procs)
            if k in ("controller", "guardian"):
                pk = self.rec["peaks"]
                pk[f"{k}_lifetime_max"] = max(pk.get(f"{k}_lifetime_max", 0), life)
            else:
                mm[k] = max(mm.get(k, 0), life)
        self._aggregate(w)

    def _aggregate(self, w: dict) -> int:
        pk = self.rec["peaks"]
        a = sum((w.get("member_max") or {}).values()) + pk.get("controller_lifetime_max", 0) + \
            pk.get("guardian_lifetime_max", 0)
        w["aggregate"] = a
        key = f"{w['session']}:{w['phase']}:{len(self.rec['workers'])}"
        agg = pk.setdefault("phase_aggregates", {})
        agg[key] = max(agg.get(key, 0), a)
        pk["task_lifetime_sum"] = max(pk.get("task_lifetime_sum", 0), a)
        return a

    def _task_aggregate(self) -> int:
        """Final: max over this session's workers of (member maxima) + the controller's FINAL lifetime maximum."""
        pk = self.rec["peaks"]
        c = max(pk.get("controller_final", 0), pk.get("controller_lifetime_max", 0)) + \
            max(pk.get("guardian_final", 0), pk.get("guardian_lifetime_max", 0))
        ws = [sum((w.get("member_max") or {}).values()) for w in self.rec["workers"] if w.get("session") == self.session]
        return max([pk["task_lifetime_sum"]] + [s + c for s in ws])

    def _missing_measurements(self) -> list[str]:
        miss = [f"{w['phase']}: no exit peak ({w.get('exit_peak_error', 'not read')})" for w in self.rec["workers"]
                if w.get("session") == self.session and w.get("released") and not
                (isinstance(w.get("exit_peak"), int) and w["exit_peak"] > 0)]
        if not (isinstance(self.rec["peaks"].get("controller_final"), int) and self.rec["peaks"]["controller_final"] > 0):
            miss.append(f"controller final self sample ({self.rec['peaks'].get('controller_final_error', 'absent')})")
        if not (isinstance(self.rec["peaks"].get("guardian_final"), int) and self.rec["peaks"]["guardian_final"] > 0):
            miss.append(f"guardian final sample ({self.rec['peaks'].get('guardian_final_error', 'absent')})")
        return miss

    # ---- final (A5, A7) -------------------------------------------------------------------------------------------
    def _report_ok(self) -> dict:
        """The CURRENT report: worker of this session exited 0, no report stop this session, a receipt with exactly
        the receipt schema naming this session and the gates' package/identity and EXACTLY the four report outputs,
        each present with its sha256; the machine report agreeing with the receipt."""
        why = []
        ws = [w for w in self.rec["workers"] if w.get("session") == self.session and w["phase"] == "report"]
        if not ws or ws[-1].get("returncode") != 0 or ws[-1].get("stop"):
            why.append("the report worker of this session did not exit 0")
        if any(s.get("phase") == "report" and s.get("session") == self.session for s in self.rec["stops"]):
            why.append("a report stop in this session")
        rp = self.out / "report" / "REPORT_RECEIPT.json"
        try:
            rc = json.loads(rp.read_text()) if rp.exists() else None
        except ValueError:
            rc, _ = None, why.append("the report receipt is not JSON")
        rep = {}
        if rc is None:
            why.append("no report receipt")
        elif not isinstance(rc, dict) or set(rc) != RECEIPT_KEYS:
            why.append(f"the report receipt's fields are not exactly {sorted(RECEIPT_KEYS)}")
        else:
            g = self.gates_rec or {}
            outs = rc["outputs"]
            if rc["session"] != self.session:
                why.append("the report receipt names another session")
            if not (isinstance(rc["date"], str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", rc["date"])):
                why.append("the report receipt's date is not YYYY-MM-DD")
            if not (isinstance(rc["admissible"], bool) and isinstance(rc["validator_pass"], bool)):
                why.append("the report receipt's flags are not booleans")
            if self.use_gates and (rc["package"] != g.get("package") or rc["identity"] != g.get("identity")):
                why.append("the report receipt's package or identity differs from this session's gates")
            if not isinstance(outs, dict) or set(outs) != REPORT_OUTPUTS or \
                    not all(isinstance(h, str) and HEX64.fullmatch(h) for h in outs.values()):
                why.append(f"the receipt does not bind exactly the four report outputs {sorted(REPORT_OUTPUTS)}")
            else:
                for rel, h in outs.items():
                    p = self.out / rel
                    if not p.exists() or _sha_file(p) != h:
                        why.append(f"report output {rel} missing or changed")
            if not why:
                rep = json.loads((self.out / "report/stage_a_report.json").read_text())
                if not isinstance(rep, dict) or rep.get("session") != rc["session"] or \
                        rep.get("admissible") is not rc["admissible"] or \
                        rep.get("validator_pass") is not rc["validator_pass"]:
                    why.append("the machine report's session or flags differ from the receipt")
                    rep = {}
        return {"ok": not why, "why": why, "receipt": rc, "report": rep}

    def _counters_ok(self) -> dict:
        st = json.loads((self.out / "stage_a_state.json").read_text()) if (self.out / "stage_a_state.json").exists() \
            else None
        if st is None:
            return {"ok": True, "detail": "no attempts"}
        problems = check_ledger(st, witness_dir=self.out)
        c = st.get("counters", {}) if isinstance(st, dict) else {}
        for key in ("row20", "aggregate"):
            k = c.get(key, {})
            if not (isinstance(k.get("passes"), int) and k["passes"] <= CAPS[key]["attempts"] and
                    k.get("started", 1 << 30) <= CAPS[key]["attempts"]):
                problems.append(f"{key}: over its attempt cap")
        return {"ok": not problems, "detail": problems}

    def _finalise(self) -> dict:
        rok = self._report_ok()
        rep = rok["report"]
        from stage_a_guard import terminal_active, terminal_release
        terminal = terminal_active(self.out)
        cnt = self._counters_ok()
        st = json.loads((self.out / "stage_a_state.json").read_text()) if (self.out / "stage_a_state.json").exists() \
            else {"attempts": {}}
        mem_peak = self._task_aggregate()
        missing = self._missing_measurements()
        final = {"outcome": "STOPPED", "session": self.session, "report_current": rok["ok"],
                 "report_problems": rok["why"], "validator_pass": bool(rep.get("validator_pass")),
                 "admissible": bool(rep.get("admissible")), "terminal": terminal,
                 "terminal_release": terminal_release(self.out), "counters": cnt,
                 "seconds_total": self.rec["seconds_total"], "carry_s": self.rec["carry_s"],
                 "stage_a_seconds": self.rec["seconds_total"] - self.rec["carry_s"],
                 "task_memory_aggregate": mem_peak, "missing_measurements": missing,
                 "peaks": self.rec["peaks"], "report_receipt_sha256": _sha_file(self.out / "report/REPORT_RECEIPT.json")
                 if rok["receipt"] is not None else None,
                 "controller_sha256": _sha_file(self.path), "stops": self.rec["stops"],
                 "time_scope": f"seconds_total includes this session's whole bounded closure ({CLOSE_CHARGE_S:.0f} s "
                               f"= finalisation {FINAL_ALLOWANCE_S:.0f} + revocation {REVOKE_TIMEOUT_S:.0f} + exit/output "
                               f"{EXIT_MARGIN_S:.0f}), charged at the close; finalisation is enforced by its timer and "
                               f"the whole closure by the guardian"}
        unique = sum(1 for _ in st.get("attempts", {}))
        final["stage_b_prediction"] = None
        size0 = dir_bytes([self.out])
        mlen = len(json.dumps({"final_sha256": "0" * 64, "session": self.session}, indent=1, sort_keys=True).encode())
        for _ in range(4):                            # a fixed point: the figure includes this record and its marker
            final["storage_final"] = size0 + mlen + len(json.dumps(final, indent=1, sort_keys=True).encode())
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
                       "memory": 0 < mem_peak < CAPS_MEMORY and not missing, "attempts": cnt["ok"]}
            final["caps_ok_on_final_figures"] = caps_ok
            final["outcome"] = "PASS" if (rok["ok"] and rep.get("validator_pass") is True and rep.get("admissible")
                                          is True and not terminal and all(caps_ok.values())) else "STOPPED"
            if size0 + mlen + len(json.dumps(final, indent=1, sort_keys=True).encode()) == final["storage_final"]:
                break
        fp = self.out / FINAL
        self._write(fp, final)                        # a failure or block here leaves no marker (A5)
        after = dir_bytes([self.out])
        if after + mlen != final["storage_final"]:   # invalidate a mismatching completion on disk
            final.update(outcome="STOPPED", storage_final_check={"declared": final["storage_final"],
                                                                 "measured_after": after + mlen})
            self._write(fp, final)
            return final
        marker = {"final_sha256": _sha_file(fp), "session": self.session}
        self._write(self.out / ADMITTED, marker)      # the commit point; a failure after it -> _bounded's abort
        return final

    def _final_write(self, fp: Path, final: dict, err: list) -> None:  # kept for fixtures that patch the writer
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
        """The leader's lifetime maximum read from the exited, UNREAPED process (before proc.wait), folded into the
        member maxima by identity."""
        try:
            peak = self.probe.exit_peak(self.proc.pid)
        except memprobe.Unavailable as exc:
            w["exit_peak_error"] = str(exc)
            return
        w["exit_peak"] = peak
        ld = w.get("leader") or {}
        k = f"{self.proc.pid}:{ld.get('start', '?')}"
        with self.lock:
            mm = w.setdefault("member_max", {})
            mm[k] = max(mm.get(k, 0), peak)
            self._aggregate(w)

    def _tick(self, b: bytes = b".") -> None:
        if self.tick_w is not None:
            try:
                os.write(self.tick_w, b)
            except (BlockingIOError, BrokenPipeError, OSError):
                pass

    def _end_worker(self, w: dict, why: str | None) -> dict:
        """Stop (if why) or finish the current worker: SIGKILL to the group at once -> the leader's final peak read
        from the exited, unreaped process -> every live group member (enumerated) and recorded member killed and
        confirmed gone -> reap -> watchdog ended."""
        p, out = self.proc, {}
        if p is None:
            self._end_watchdog(w)
            return out
        self._tick(b"E\n")
        t = self.clock()
        try:
            if p.stdin and not p.stdin.closed:
                p.stdin.close()
        except OSError:
            pass
        if not self._leader_exited():
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            out["how"] = "SIGKILL"
            self._wait_leader_exit(GROUP_GONE_S)
        self._final_peak(w)
        leader = w.get("leader") or {"pid": p.pid, "ppid": os.getpid(), "pgid": p.pid, "start": "0.000000"}
        try:
            res = memprobe.end_group(leader, list((w.get("members") or {}).values()), limit=GROUP_GONE_S,
                                     own_leader=True)
        except memprobe.Survivors as exc:
            raise ControllerStop(f"{w['phase']}: {exc}")
        w["group_clean"], w["group_killed"] = True, len(res["killed"])
        if "stop_observed_mono" in w:                  # end to end: last admissible observation -> verified extinction
            w["extinction_verified_mono"] = time.monotonic()
            w["observation_to_extinction_s"] = w["extinction_verified_mono"] - w["stop_observed_mono"]
        p.wait()
        w["returncode"], w["reaped"] = p.returncode, True
        if why:
            out.update(killed=True, why=why, kill_to_reap_s=self.clock() - t)
        self._end_watchdog(w)
        w.update(out)
        self.proc = None
        return out

    def _end_watchdog(self, w: dict) -> None:
        if self.tick_w is not None:
            try:
                os.close(self.tick_w)
            except OSError:
                pass
            self.tick_w = None
        if self.wd is not None:
            try:
                self.wd.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self.wd.kill()
                self.wd.wait()
            w["watchdog_exit"] = self.wd.returncode
            if self.wd.stdout:
                self.wd.stdout.close()
            self.wd = None

    def _leader_exited(self) -> bool:
        if not self._exited_flag:
            if self.kq is not None:
                self._exited_flag = memprobe.exited(self.kq)
            elif self.proc is not None:
                self._exited_flag = memprobe.proc_info(self.proc.pid) is None   # zombie or gone (never reaped here)
        return self._exited_flag

    def _wait_leader_exit(self, limit: float) -> None:
        dl = time.monotonic() + limit
        while not self._leader_exited():
            if time.monotonic() > dl:
                raise ControllerStop("the worker leader survives SIGKILL")
            time.sleep(0.01)

    def _kill_current(self, why: str) -> dict:
        if self.proc is None:
            return {"killed": False}
        return self._end_worker(self.rec["workers"][-1], why)

    def _arm_watchdog(self, w: dict, phase: str, deadline: float) -> None:
        rel = f"watchdog_{self.session}_{phase}.json"
        mfile = f"members_{self.session}_{phase}.json"
        r, wfd = os.pipe()
        try:
            arg = {"controller": self.ident, "leader": w["leader"], "session": self.session,
                   "beat_file": str(self.path), "stale_s": STALE_S, "record": str(self.out / rel),
                   "deadline_monotonic": time.monotonic() + (deadline - self.elapsed_total()) + HARD_MARGIN_S,
                   "members_file": str(self.out / mfile), "tick_fd": r, "tick_stale_s": TICK_STALE_S}
            self.wd = subprocess.Popen(self.watchdog_cmd + [json.dumps(arg)], stdout=subprocess.PIPE,
                                       stdin=subprocess.DEVNULL, start_new_session=True, pass_fds=(r,))
        finally:
            os.close(r)
        self.tick_w = wfd
        os.set_blocking(wfd, False)
        ready = select.select([self.wd.stdout], [], [], ARM_TIMEOUT_S)[0]
        line = self.wd.stdout.readline() if ready else b""
        if line.strip() != b"ARMED":
            raise ControllerStop(f"{phase}: the watchdog did not arm ({line[:80]!r}, exit {self.wd.poll()})")
        self.wd_ident = memprobe.proc_info(self.wd.pid)
        if not memprobe.valid_ident(self.wd_ident):
            raise ControllerStop(f"{phase}: the watchdog's identity cannot be read")
        w.update(watchdog=self.wd_ident, watchdog_record=rel, members_file=mfile)

    def _phase(self, phase: str, *, deadline: float, storage_limit: int, report: bool = False,
               gates: bool = False) -> None:
        if self.proc is not None or self.wd is not None:   # never let an earlier worker survive into a new phase
            self._end_worker(self.rec["workers"][-1], f"an earlier worker still present at the start of {phase}")
        if self.elapsed_total() >= deadline:
            raise ControllerStop(f"{phase}: time limit {deadline:.0f} s reached (row cap {self.cap_s:.0f} s "
                                 f"less reserves) before the start")
        env = {**os.environ, "STAGE_A_CONTROLLER_PID": str(os.getpid()), "STAGE_A_SESSION": self.session,
               "STAGE_A_STORAGE_LIMIT": str(storage_limit), "STAGE_A_STORAGE_CAP": str(self.cap_b),
               "STAGE_A_GATES": json.dumps(self.gates_rec or {})}
        w = {"phase": phase, "session": self.session, "members": {}, "member_max": {},
             "spawned_total_s": self.elapsed_total(), "released": False}
        with self.lock:
            self.rec["workers"].append(w)
        self._exited_flag, self.kq, self.wd_ident = False, None, None
        max_work = 0.0
        try:
            self.proc = subprocess.Popen(GATE + self.worker_cmd(phase), stdin=subprocess.PIPE, env=env,
                                         start_new_session=True)
            w["pid"] = self.proc.pid
            self.kq = self.probe.exit_watch(self.proc.pid)
            leader = memprobe.proc_info(self.proc.pid)
            if not memprobe.valid_ident(leader):
                raise ControllerStop(f"{phase}: the worker's identity cannot be read before its release")
            w["leader"] = leader
            self._arm_watchdog(w, phase, deadline)
            self._persist()                            # durable identities BEFORE the worker may run anything
            self._tick(f"{time.monotonic():.6f}\n".encode())   # liveness armed BEFORE release (from this instant)
            self.proc.stdin.write(b"GO\n")
            self.proc.stdin.close()
            w["released"], w["released_total_s"] = True, self.elapsed_total()
            max_work = self._sample(w, phase, deadline, storage_limit)
        except BaseException as exc:
            try:
                k = self._end_worker(w, str(exc))
            except ControllerStop as exc2:
                k = {"cleanup_failure": str(exc2)}
                exc = exc2
            w.update(exited_total_s=self.elapsed_total(), stop=str(exc), **k)
            self._iter(phase, max_work)
            try:
                self._persist()
            except ControllerStop as exc3:
                w["persist_after_stop"] = str(exc3)
            raise exc
        self._end_worker(w, None)
        rc = w["returncode"]
        w["exited_total_s"] = self.elapsed_total()
        self._iter(phase, max_work)
        self._persist()
        if self._aggregate(w) >= MEM_STOP:
            raise ControllerStop(f"{phase}: task memory {w['aggregate']} >= {MEM_STOP} at the worker's exit")
        if rc != 0:
            raise ControllerStop(f"{phase}: worker exited {rc}")
        if not (report or gates) and not (self.out / f"{phase.upper()}_DONE.json").exists():
            raise ControllerStop(f"{phase}: worker exited 0 without its durable phase record")

    def _iter(self, phase: str, work: float) -> None:
        mi = self.rec["peaks"]["max_iteration_s"]
        mi[phase] = max(mi.get(phase, 0.0), work)

    def _io(self, storage_limit: int, phase: str) -> None:
        """The I/O thread: the durable beat (record + members file) and the storage sum every HEARTBEAT_S; a failure
        or an over-limit sum is handed to the sampler as a stop."""
        while self.io_run and self.io_stop is None:
            try:
                used = dir_bytes([self.out])
                with self.lock:
                    pk = self.rec["peaks"]
                    pk["storage_bytes"] = max(pk["storage_bytes"], used)
                if used > storage_limit:
                    self.io_stop = f"{phase}: task storage {used} over {storage_limit}"
                    return
                self._persist()
            except ControllerStop as exc:
                self.io_stop = str(exc)
                return
            except Exception as exc:                 # noqa: BLE001
                self.io_stop = f"{phase}: I/O failure {exc!r}"
                return
            t = time.monotonic()
            while self.io_run and time.monotonic() - t < HEARTBEAT_S:
                time.sleep(0.05)

    def _kill_now(self, w: dict, observed: float, exc: BaseException) -> None:
        """The stop's kill, sent by the sampler itself: the group SIGKILLed the instant the stop is decided (we are the
        unreaped leader's parent, so the group id is ours). `stop_observed_mono` is the start of the iteration whose
        observation decided it - the last admissible observation."""
        w["stop_observed_mono"], w["how"] = observed, "SIGKILL"
        w["deciding_read_mono"] = getattr(self, "t_read_last", observed)
        try:
            os.killpg(self.proc.pid, signal.SIGKILL)
            w["stop_killed_mono"] = time.monotonic()
        except (ProcessLookupError, PermissionError):
            pass
        t = time.monotonic()                           # the leader's death, seen by kqueue (no reap, no file I/O)
        while not self._leader_exited() and time.monotonic() - t < 1.0:
            time.sleep(0.001)
        if self._leader_exited():
            w["stop_leader_dead_mono"] = time.monotonic()
            w["stop_leader_dead_s"] = w["stop_leader_dead_mono"] - observed
        _say(f"stage_a_controller: stop observed at monotonic {observed:.6f}, previous successful reading at "
             f"{w.get('prev_ok_read_mono', float('nan')):.6f}, SIGKILL sent at "
             f"{w.get('stop_killed_mono', float('nan')):.6f}: {str(exc)[:200]}")

    def _sample(self, w: dict, phase: str, deadline: float, storage_limit: int) -> float:
        """The sampler (main thread, no file I/O). Returns the largest iteration work time."""
        self.io_stop, self.io_run = None, True
        io = threading.Thread(target=self._io, args=(storage_limit, phase), daemon=True)
        io.start()
        last_sys, max_work = 0.0, 0.0
        it0 = time.monotonic()
        pid = self.proc.pid
        wd_gone_t = None                               # revision 12 (A3): when the watchdog was first seen gone
        try:
            while True:
                it0 = time.monotonic()
                if self._leader_exited():
                    break
                if self.io_stop:
                    raise ControllerStop(self.io_stop)
                if self.elapsed_total() >= deadline:
                    raise ControllerStop(f"{phase}: time limit {deadline:.0f} s reached (row cap {self.cap_s:.0f} s "
                                         f"less reserves)")
                wd_gone = self.wd is not None and self.wd.poll() is not None
                if wd_gone:
                    # Revision 11/12 (the 2 October run; Codex 5eb51a8 A3): a watchdog gone before this controller saw
                    # the leader's exit. The leader's confirmed exit (kqueue, checked at the top of every iteration)
                    # is awaited for at most GROUP_GONE_S WITHOUT suspending any control: this loop keeps sampling
                    # memory, swap and pressure and checking the phase deadline, the I/O stop and the iteration limit
                    # (any breach is the ordinary stop, the group killed first); with no confirmed exit by then the
                    # group is killed and the run HOLDS. The retired watchdog gives no tick check meanwhile.
                    wd_gone_t = it0 if wd_gone_t is None else wd_gone_t
                    if it0 - wd_gone_t > GROUP_GONE_S:
                        raise ControllerHold(f"{phase}: watchdog exited ({self.wd.returncode}) and the leader's exit "
                                             f"was not confirmed within {GROUP_GONE_S:.0f} s")
                try:
                    procs = self.probe.task_processes([pid], {pid})
                    pids = set(procs) | {os.getpid()} | ({self.wd.pid} if self.wd is not None and not wd_gone
                                                         else set()) | \
                        ({self.guard.pid} if getattr(self, "guard", None) is not None else set())
                    t_read = self.t_read_last = time.monotonic()   # this reading's observation instant (rev 7)
                    smp = self.probe.task_sample(pids)
                except memprobe.Unavailable as exc:
                    if self._leader_exited():
                        break                         # exited between the check and the sample
                    raise ControllerStop(f"{phase}: memory reading unavailable ({exc})")
                with self.lock:
                    for p, i in procs.items():
                        w["members"].setdefault(str(p), i)
                    self._fold(w, procs, smp)
                if smp["lifetime_sum"] >= MEM_STOP or w["aggregate"] >= MEM_STOP:
                    raise ControllerStop(f"{phase}: task memory {max(smp['lifetime_sum'], w['aggregate'])} >= "
                                         f"{MEM_STOP}")
                now = time.monotonic()
                if now - last_sys >= SYS_SAMPLE_S:
                    last_sys = now
                    sysr = self.system_reader()
                    if sysr["swap"] > self.rec["swap_baseline"]:
                        raise ControllerStop(f"swap rose from {self.rec['swap_baseline']} to {sysr['swap']}")
                    if sysr["pressure"] >= 2:
                        raise ControllerStop(f"kernel memory pressure {sysr['pressure']}")
                work = time.monotonic() - it0
                max_work = max(max_work, work)
                if work > SAMPLE_LIMIT_S:
                    raise ControllerStop(f"{phase}: a sampling iteration took {work:.3f} s (limit {SAMPLE_LIMIT_S} s)")
                w["prev_ok_read_mono"] = self.prev_ok = t_read   # the last successful below-stop reading
                self._tick(f"{t_read:.6f}\n".encode())    # the tick carries its source observation time
                time.sleep(MEM_SAMPLE_S)
        except BaseException as exc:
            self._kill_now(w, it0, exc)               # SIGKILL FIRST - before any join, persist or record (Stage A 1)
            raise
        finally:
            self._tick(b"E\n")                        # the group is already killed (or the leader exited)
            self.io_run = False
            io.join(timeout=2 * HEARTBEAT_S)
        return max_work


class SupplementController(Controller):
    """Revision 16: the row-20 OS-bridge supplement (Codex b0db0f9 §"Prospective row21 OS bridge"; STAGE_A_SUPPLEMENT_
    CRITERIA.md). The same controller - guardian, lock, guarded starts, watchdog, sampler, whole-task memory, durable
    clock, bounded closure, durable completion - in its OWN output tree (captures/photo_stage_a_supplement) under its
    OWN names (SUPPLEMENT_NAMES): it supersedes only its own final, marker, abort and receipt; its phases are
    supplement_gates -> supplement_instrumented -> supplement_native -> supplement_receipt (always, also after a stop);
    its terminal record is SUPPLEMENT_TERMINAL.json (no release); it never touches captures/photo_stage_a.

    REVISION 2 (Codex 478196f P1): one session from the first start - `_supersede` refuses after an admitted PASS and
    terminalises after any start without one (a STOPPED, held, crashed or interrupted earlier session), `_hold` and a
    STOPPED `_finalise` after a start terminalise at once, and `_missing_measurements` spans every session.
    REVISION 4 (Codex 410b580 P2): any durable endpoint worker record is start evidence and needs its exit peak,
    whatever its `released` flag (the record is persisted before GO; released=True only after it).
    REVISION 3 (Codex 1abb851 P1): the stop is DERIVED from the records (`_prior_start_evidence`), not from the terminal
    file: any prior start without an admitted PASS sets a refusal before supersede, gates, any worker, receipt or final
    (the terminal file is only its record; a failed write still refuses); a PASS needs both endpoints from THIS session.

    ROW 20'S ENVELOPE, NOT A NEW ONE: carry_seconds is the accepted Stage A's controller seconds_total (pinned in the
    supplement plan and re-checked at the gates), so time continues against row 20's 4 h; storage_cap is row 20's
    1 GiB less the frozen Stage A tree's bytes (pinned); memory is per task as before (stop 44 GiB, cap 48 GiB); the
    attempt counters carry Stage A's 194/193/1/194 into the supplement ledger (stage_a.supplement_open).

    FINAL: PASS only if, in THIS session, the receipt worker exited 0 and wrote supplement/SUPPLEMENT_RECEIPT.json last
    with exactly SUPPLEMENT_RECEIPT_KEYS, naming this session and the gates' package and identity, outcome PASS and
    admissible, every bound output present with its sha256; no supplement terminal record; the supplement ledger legal
    (check_ledger, row 20 <= 200); every mandatory measurement present; every cap holding on the final figures."""
    NAMES = SUPPLEMENT_NAMES
    GATES_PHASE, REPORT_PHASE = "supplement_gates", "supplement_receipt"
    set_terminal_fn = staticmethod(supplement_set_terminal)
    terminal_active_fn = staticmethod(supplement_terminal_active)

    def run(self, phases=SUPPLEMENT_PHASES, emit=None) -> dict:
        return super().run(phases=phases, emit=emit)

    # ---- revisions 2-3 (Codex 478196f, 1abb851 P1): one session from the first start; the stop is DERIVED ----------
    _refusal: str | None = None

    def _post_start(self) -> bool:
        return bool(self._prior_start_evidence())

    def _prior_start_evidence(self) -> list[str]:
        """Revision 3: every durable trace that a supplement start happened, read from the records themselves - the
        ledger's attempts (or an unreadable ledger), a released endpoint worker in controller.json, an endpoint phase
        record, a pass output, a comparison receipt, the terminal record. Never decided by SUPPLEMENT_TERMINAL.json
        alone."""
        found = []
        sp = self.out / "stage_a_state.json"
        try:
            if sp.exists() and json.loads(sp.read_text()).get("attempts"):
                found.append("ledger attempts")
        except (OSError, ValueError):
            found.append("an unreadable ledger")
        # revision 4 (Codex 410b580 P2): ANY durable endpoint worker record, released or not - the base _phase persists
        # the record (released=False) BEFORE it sends GO and marks it released only afterwards, so released=False is a
        # pre-GO snapshot, not proof that GO was never delivered. Before that persist no GO can have been sent, so a
        # durable record is exactly the boundary of a possible start.
        if any(w.get("phase") in SUPPLEMENT_PHASES for w in (getattr(self, "rec", None) or {}).get("workers", [])):
            found.append("a durable endpoint worker record")
        for name in ("SUPPLEMENT_INSTRUMENTED_DONE.json", "SUPPLEMENT_NATIVE_DONE.json", SUPPLEMENT_TERMINAL):
            if (self.out / name).exists():
                found.append(name)
        if (self.out / "passes").exists() and any((self.out / "passes").iterdir()):
            found.append("pass outputs")
        if (self.out / "supplement").exists() and list((self.out / "supplement").glob("comparison_*.json")):
            found.append("comparison receipts")
        return found

    def _terminalise(self, reason: str) -> bool:
        """Best effort durable RECORD of a stop that is already decided; returns whether it is on disk."""
        try:
            if not supplement_terminal_active(self.out):
                supplement_set_terminal(self.out, "controller", reason)
            return True
        except Exception as exc:                       # noqa: BLE001 - recorded; the decision does not depend on it
            self.rec["stops"].append({"phase": "controller", "session": self.session,
                                      "reason": f"terminal write failed: {exc!r}"})
            return False

    def _supersede(self) -> None:
        """Revisions 2-3. Before anything is moved or spawned: (1) an ADMITTED PASS of this version is final - nothing
        runs again; (2) ANY prior start without an admitted PASS (_prior_start_evidence) makes this session REFUSE: the
        refusal is set here, nothing is superseded, the gates return REFUSED before any worker (so no endpoint, receipt
        or final), and the session closes charged. SUPPLEMENT_TERMINAL.json is written as a RECORD of that state; if
        the write fails the session still refuses (exit 2) and says so. Otherwise only this tree's own names move."""
        fin = final_admitted(self.out, self.NAMES)
        if fin is not None and fin.get("outcome") == "PASS":
            raise SystemExit(f"refused: this supplement version already PASSED (session {fin.get('session')}); a PASS "
                             f"is never superseded or regenerated and nothing runs again")
        found = self._prior_start_evidence()
        if found:
            self._refusal = (f"refused: a prior supplement start without an admitted PASS ({', '.join(found)}): this "
                             f"version never runs again - no endpoint, receipt or final")
            if not self._terminalise(self._refusal):
                self._refusal += "; the terminal record could not be written (the refusal does not depend on it)"
            return
        super()._supersede()

    def _gates(self) -> dict:
        if self._refusal:                              # revision 3: refused before any worker
            return {"outcome": "REFUSED", "reason": self._refusal}
        return super()._gates()

    def _phase(self, phase: str, **kw) -> None:
        if self._refusal:                              # revision 3: no worker of any phase after a refusal
            raise SystemExit(self._refusal)
        return super()._phase(phase, **kw)

    def _endpoints_this_session(self) -> bool:
        """Revision 3: a PASS needs BOTH endpoints committed in the supplement ledger by THIS session."""
        import stage_a
        try:
            st = json.loads((self.out / "stage_a_state.json").read_text())
        except (OSError, ValueError):
            return False
        return all((st.get("completed") or {}).get(i, {}).get("session") == self.session
                   for i in (stage_a.SUPP_INST, stage_a.SUPP_NAT))

    def _hold(self, reason: str) -> dict:
        """Revision 2: a hold after a start is terminal for the supplement (no resumption)."""
        if self._post_start():
            self._terminalise(f"held after a start ({reason}): this version stops")
        return super()._hold(reason)

    def _missing_measurements(self) -> list[str]:
        """Revision 2: every released worker of EVERY session of this tree must have its exit peak - a mandatory
        measurement lost in an earlier session is never forgotten by a later one."""
        miss = [f"{w['phase']} (session {w.get('session')}): no exit peak ({w.get('exit_peak_error', 'not read')})"
                for w in self.rec["workers"] if (w.get("released") or w.get("phase") in SUPPLEMENT_PHASES) and
                not (isinstance(w.get("exit_peak"), int) and w["exit_peak"] > 0)]     # rev 4: any endpoint record
        pk = self.rec["peaks"]
        if not (isinstance(pk.get("controller_final"), int) and pk["controller_final"] > 0):
            miss.append(f"controller final self sample ({pk.get('controller_final_error', 'absent')})")
        if not (isinstance(pk.get("guardian_final"), int) and pk["guardian_final"] > 0):
            miss.append(f"guardian final sample ({pk.get('guardian_final_error', 'absent')})")
        return miss

    def _report_ok(self) -> dict:
        why = []
        ws = [w for w in self.rec["workers"] if w.get("session") == self.session and w["phase"] == self.REPORT_PHASE]
        if not ws or ws[-1].get("returncode") != 0 or ws[-1].get("stop"):
            why.append("the receipt worker of this session did not exit 0")
        if any(s.get("phase") == self.REPORT_PHASE and s.get("session") == self.session for s in self.rec["stops"]):
            why.append("a receipt stop in this session")
        rp = self.out / self.NAMES["receipt"]
        try:
            rc = json.loads(rp.read_text()) if rp.exists() else None
        except ValueError:
            rc, _ = None, why.append("the supplement receipt is not JSON")
        if rc is None:
            why.append("no supplement receipt")
        elif not isinstance(rc, dict) or set(rc) != SUPPLEMENT_RECEIPT_KEYS:
            why.append(f"the supplement receipt's fields are not exactly {sorted(SUPPLEMENT_RECEIPT_KEYS)}")
        else:
            g = self.gates_rec or {}
            if rc["session"] != self.session:
                why.append("the supplement receipt names another session")
            if not (isinstance(rc["date"], str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", rc["date"])):
                why.append("the supplement receipt's date is not YYYY-MM-DD")
            if rc["outcome"] not in ("PASS", "STOPPED") or not isinstance(rc["admissible"], bool):
                why.append("the supplement receipt's outcome or admissibility is malformed")
            if self.use_gates and (rc["package"] != g.get("package") or rc["identity"] != g.get("identity")):
                why.append("the supplement receipt's package or identity differs from this session's gates")
            outs = rc["outputs"]
            if not isinstance(outs, dict) or not outs or \
                    not all(isinstance(h, str) and HEX64.fullmatch(h) for h in outs.values()):
                why.append("the supplement receipt binds no outputs, or a malformed hash")
            else:
                for rel, h in outs.items():
                    p = self.out / rel
                    if not p.exists() or _sha_file(p) != h:
                        why.append(f"supplement output {rel} missing or changed")
        return {"ok": not why, "why": why, "receipt": rc, "report": {}}

    def _finalise(self) -> dict:
        if self._refusal:                              # revision 3: a refused session never writes a final
            raise SystemExit(self._refusal)
        rok = self._report_ok()
        rc = rok["receipt"] if isinstance(rok["receipt"], dict) else {}
        if not self._endpoints_this_session():         # revision 3: both endpoints made by THIS session
            rok = {**rok, "ok": False, "why": rok["why"] + ["the endpoints were not both committed in this session"]}
        cnt = self._counters_ok()
        mem_peak = self._task_aggregate()
        missing = self._missing_measurements()
        provisional = rok["ok"] and rc.get("outcome") == "PASS" and rc.get("admissible") is True and not missing \
            and cnt["ok"] and 0 < mem_peak < CAPS_MEMORY and self.rec["seconds_total"] <= self.cap_s
        if not provisional and self._post_start():     # revision 2: a STOPPED final after a start is terminal first
            self._terminalise("the final record after a start is STOPPED: " +
                              "; ".join((rok["why"] + missing + ([] if cnt["ok"] else ["ledger"]))[:4] or
                                        [f"receipt outcome {rc.get('outcome')}"]))
        terminal = supplement_terminal_active(self.out)
        n = self.NAMES
        final = {"outcome": "STOPPED", "kind": "stage_a_supplement", "session": self.session,
                 "receipt_current": rok["ok"], "receipt_problems": rok["why"],
                 "receipt_outcome": rc.get("outcome"), "admissible": rc.get("admissible") is True,
                 "terminal": terminal, "counters": cnt, "seconds_total": self.rec["seconds_total"],
                 "carry_s": self.rec["carry_s"], "supplement_seconds": self.rec["seconds_total"] - self.rec["carry_s"],
                 "task_memory_aggregate": mem_peak, "missing_measurements": missing, "peaks": self.rec["peaks"],
                 "receipt_sha256": _sha_file(self.out / n["receipt"]) if rok["receipt"] is not None else None,
                 "controller_sha256": _sha_file(self.path), "stops": self.rec["stops"],
                 "storage_carry_bytes": CAPS["row20"]["bytes"] - self.cap_b,
                 "time_scope": f"seconds_total = the accepted Stage A's row-20 total (carry) + this tree's sessions, "
                               f"each including its whole bounded closure ({CLOSE_CHARGE_S:.0f} s)"}
        size0 = dir_bytes([self.out])
        mlen = len(json.dumps({"final_sha256": "0" * 64, "session": self.session}, indent=1, sort_keys=True).encode())
        for _ in range(4):                            # a fixed point: the figure includes this record and its marker
            final["storage_final"] = size0 + mlen + len(json.dumps(final, indent=1, sort_keys=True).encode())
            final["row20_storage_final"] = final["storage_final"] + final["storage_carry_bytes"]
            caps_ok = {"time": self.rec["seconds_total"] <= self.cap_s, "storage": final["storage_final"] <= self.cap_b,
                       "memory": 0 < mem_peak < CAPS_MEMORY and not missing, "attempts": cnt["ok"]}
            final["caps_ok_on_final_figures"] = caps_ok
            final["outcome"] = "PASS" if (rok["ok"] and rc.get("outcome") == "PASS" and rc.get("admissible") is True
                                          and not terminal and all(caps_ok.values())) else "STOPPED"
            if size0 + mlen + len(json.dumps(final, indent=1, sort_keys=True).encode()) == final["storage_final"]:
                break
        fp = self.out / n["final"]
        self._write(fp, final)                        # a failure or block here leaves no marker (A5)
        after = dir_bytes([self.out])
        if after + mlen != final["storage_final"]:
            final.update(outcome="STOPPED", storage_final_check={"declared": final["storage_final"],
                                                                 "measured_after": after + mlen})
            self._write(fp, final)
            return final
        self._write(self.out / n["admitted"], {"final_sha256": _sha_file(fp), "session": self.session})
        return final


def default_worker_cmd(phase: str) -> list[str]:
    return [sys.executable, str(HERE / "stage_a.py"), "worker", phase]


def supplement_controller(**kw) -> SupplementController:
    """The supplement's controller with row 20's carried figures read from the reviewed supplement plan (the gates
    re-check them against the frozen Stage A tree before anything is spawned)."""
    import stage_a
    sp = json.loads(stage_a.SUPP_PLAN.read_text())
    env = sp["envelope"]
    return SupplementController(stage_a.SUPP_OUT, carry_seconds=env["seconds_carry"], worker_cmd=default_worker_cmd,
                                storage_cap=env["cap_bytes"] - env["storage_carry_bytes"], **kw)


def main() -> int:
    import stage_a
    emit = lambda r: (print(json.dumps(r, indent=1, default=str)), sys.stdout.flush())   # noqa: E731
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "supplement":                            # revision 16: the row-20 OS-bridge supplement
        out = supplement_controller(from_process_start=True).run(emit=emit)
        return {"REFUSED": 2, "HELD": EXIT_HOLD}.get(out["outcome"], 0)
    if cmd != "run":
        raise SystemExit(f"unknown command {cmd!r}: run | supplement")
    c = Controller(stage_a.OUT, carry_seconds=stage_a.ENGINEERING_CARRY["seconds"], worker_cmd=default_worker_cmd,
                   from_process_start=True)
    out = c.run(emit=emit)
    return {"REFUSED": 2, "HELD": EXIT_HOLD}.get(out["outcome"], 0)


if __name__ == "__main__":
    sys.exit(main())
