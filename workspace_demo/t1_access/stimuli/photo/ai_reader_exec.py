"""AI image-reader qualification, revision 6: the bounded READER JOB executor (the job brief is AI_READER_JOB.md; Codex
RSC b569f8a reader 1-4 through R052 handoff c39df47e; revision 5 answered RSC 1bf9890, revision 4 RSC 5a8d7ac).
Revision 6: a setup timer is armed before any accounting I/O; the cap guard runs until the run ends (closing the clock
does not stop it); the receipt and the clock's closure share ONE allowance and one timer; the closed clock names the
journal's sha256 and `admit_clock` admits a COMPLETE only with that finished closure. It is the orchestrator's half: it holds the key and the
scorer out of the reader's reach and sends the reader one image per fresh request.

    .venv-image/bin/python stimuli/photo/ai_reader_exec.py plan       # identity and boundary checks, no request
    .venv-image/bin/python stimuli/photo/ai_reader_exec.py delivery   # renders all 600 inputs locally, writes
                                                                      # ai_reader_delivery.json (no request)
    .venv-image/bin/python stimuli/photo/ai_reader_exec.py run        # only with AIREADER_GO.json bound (below)

APPROVAL AND IDENTITY (closure 1). `package()` hashes every bound file - the set, key, delivery receipt, this file, the
scorer, the runtime, the journal, the key/frame/set builders, the job brief, the design and the imported
stage_a_guard.py, enforce.py, memprobe.py and stage_a_watchdog.py - plus the actual executable (codex realpath and
sha256, its package manifest's sha256, its version string, sandbox-exec's sha256), the command template (argv with
placeholders, the allowlist profile, environment keys, the gate) and the model-visible instructions hash;
`package_digest` is the sha256 of all of it. `run` refuses unless the shared strict guard
`stage_a_guard.require_go(GO, package(), row="aireader", stage="qualification", verify_at_commit=package_at_commit)`
passes. The digest is in every journal record and the receipt.

ORDER OF A RUN. lock -> refuse lost or invalid accounting (a journal without clock.json, a clock below the journal's
charged time, or any non-finite, negative or mistyped clock field) -> the clock's durable session opens BEFORE anything
else, counted from the process's start; a BEAT thread persists every BEAT_S from a snapshot (no lock held while a
write blocks) and a GUARD thread with no file I/O enforces the cap - at cap - FINAL_S it kills a live worker group,
at the cap it ends the process (exit 75, no receipt) -> package and go (scientific; bounded by ADMIT_TIMEOUT_S) ->
journal: pending quarantine records, tail repair (one record per quarantine file), VALIDATION of the incomplete
journal -> reconstruction -> recovery of an open attempt: every live member of the recorded worker's group
(enumerated, anchored to its identity) and every recorded member killed and confirmed gone, the watchdog last ->
the abandoned-attempt sweep -> the durable HOLDS and the remaining time are checked HERE: a hold or an exhausted clock
goes straight to the STOPPED receipt, with no preflight and no new open record -> a FRESH preflight in the open
record -> the loop.

THE LOOP. Before EVERY attempt, from durable records only: the holds (a structural failure; the smoke over every
attempt of the first request - J.holds), then the request's 3-try limit (a third non-retained attempt -> final
no_response), the 660 cap, the clock (min(120 s, remaining - FINAL_S), none under MIN_ATTEMPT_S), the raw cap (three
records of MAX_RECORD must fit under 20 MiB - RAW_FINAL_BYTES) and the attempts-root cap. An attempt: its directory and
prompt-input receipt (instructions = pin, image = frozen delivered digest, user text = frozen per-request hash; a
mismatch - including the delivered image's size and detail - holds with nothing sent and the directory removed) ->
begin (fsync) -> worker started behind its gate in its own process group, its identity read (unreadable -> nothing
sent) -> a WATCHDOG (stage_a_watchdog.py) given the orchestrator's and the worker's identities and the members file,
which must answer ARMED (the orchestrator's death, a stale clock beat or the hard attempt deadline makes it kill the
whole group and the recorded members at once; a stale beat or the deadline also kills a blocked orchestrator) ->
dispatched (fsync, the worker's and watchdog's identities) -> the remaining time REFRESHED: too
little and the gate is closed unsent (not_dispatched, charged) -> 'GO' -> wait (exit seen by kqueue without reaping;
stdout, stderr and directory caps) -> final size check -> SIGTERM/grace/SIGKILL if alive -> the whole process group
and every recorded member killed and confirmed gone, also after an ordinary leader exit -> reap -> end (fsync).

STOPS. Every stop after the journal is admitted - a limit, a hold, a receipt mismatch, RawCap, a launch or pipe
failure, a receipt renderer timeout, an exception - first reconciles an open attempt (whole-group kill, recovered
+ end) and then writes the STOPPED receipt with counters, smoke status, limits, clock and journal hash. The receipt's
clock includes FINAL_WRITE_S for its own append and the clock's close, which a timer enforces (exit 75 past it). If
persistence itself fails, no receipt is claimed: the journal stays a valid incomplete journal and the next start
re-derives its holds.

FIXTURE MODE. `run(fixture=...)` replaces the binary, the directories and the sandbox for the mechanism tests; its
records are marked mode 'synthetic-fixture', the go is not consulted, and the scorer refuses that mode unless asked
explicitly, labelling the output as not a qualification result.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import signal
import select
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ai_reader_journal as J  # noqa: E402
import ai_reader_runtime as R  # noqa: E402
import memprobe  # noqa: E402
import stage_a_guard  # noqa: E402
from enforce import write_atomic, write_json_atomic  # noqa: E402
from stage_a_guard import TaskLock  # noqa: E402

SET = HERE / "ai_reader_qual_set.json"
DELIVERY = HERE / "ai_reader_delivery.json"
IMAGES = HERE.parents[1] / "captures" / "ai_reader_qual"
JOB = HERE.parents[1] / "captures" / "ai_reader_job"
RAW = HERE / "ai_reader_raw_responses.jsonl"          # the journal; committed before scoring
GO = HERE / "AIREADER_GO.json"
ATTEMPTS = Path(tempfile.gettempdir()) / "rq"         # outside the home; readable to an attempt only within its own dir
WATCHDOG = HERE / "stage_a_watchdog.py"
LIMITS = {"planned": 600, "max_tries_per_request": 3, "max_attempts": 660, "attempt_timeout_s": 120,
          "job_clock_s": 6 * 3600, "answer_chars": R.ANSWER_KEEP, "raw_bytes": 20 * 1024 * 1024}
FINAL_S, MIN_ATTEMPT_S, TAIL_S, TERM_GRACE_S, BEAT_S, STALE_S = 120.0, 30.0, 30.0, 3.0, 1.0, 10.0
RAW_FINAL_BYTES, TEMP_CAP, ROOT_CAP, GONE_S = 256 * 1024, 16 * 1024 * 1024, 256 * 1024 * 1024, 10.0
GUARD_S, CLOSE_WAIT_S, FINAL_WRITE_S, ADMIT_TIMEOUT_S = 0.2, 30.0, 60.0, 900.0
SETUP_S = 300.0
# FINAL_WRITE_S (revision 6): ONE allowance for the receipt's append AND the clock's closure, charged in the receipt
# and enforced by one timer; the cap guard stays alive through it. SETUP_S bounds everything before the clock exists.
# FINAL_WRITE_S: the receipt's clock includes this allowance for its own append and the clock's close, which a timer
# enforces (exit 75 past it, nothing more claimed); ADMIT_TIMEOUT_S bounds package/go hashing the same way.
BOUND_FILES = ["ai_reader_qual_set.json", "ai_reader_qual_key.json", "ai_reader_delivery.json", "ai_reader_exec.py",
               "ai_reader_score.py", "ai_reader_runtime.py", "ai_reader_journal.py", "ai_reader_key.py",
               "ai_reader_frame.py", "ai_reader_qual.py", "AI_READER_JOB.md", "AI_READER_DESIGN.md",
               "stage_a_guard.py", "enforce.py", "memprobe.py", "stage_a_watchdog.py"]
NEGATIVE = {"cf3e49e", "7048bb8", "5a8d7ac", "1bf9890"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
    return sha(Path(p).read_bytes())


def package(root: Path = HERE, codex: Path = R.CODEX) -> dict:
    sset = json.loads((root / "ai_reader_qual_set.json").read_text())
    deliv = json.loads((root / "ai_reader_delivery.json").read_text())
    p = {f"{n}_sha256": sha_file(root / n) for n in BOUND_FILES}
    p["codex_realpath"] = str(Path(codex).resolve())
    p["codex_sha256"] = sha_file(codex)
    p["codex_package_json_sha256"] = sha_file(Path(codex).resolve().parents[1] / "codex-package.json")
    p["cli_version"] = subprocess.run([str(codex), "--version"], capture_output=True, text=True,
                                      env={"PATH": "/usr/bin:/bin"}, timeout=30).stdout.strip()
    p["sandbox_exec_sha256"] = sha_file(R.SANDBOX_EXEC)
    p["command_template_sha256"] = R.template_sha(sset["reader"], sset["prompt"])
    p["instructions_sha256"] = deliv["instructions_sha256"]
    p["package_digest"] = sha(json.dumps(p, sort_keys=True).encode())
    return p


def package_at_commit(commit: str, repo: Path = stage_a_guard.RSC) -> dict:
    """The package re-derived from the reviewed commit's own blobs (the bound files) with the runtime fields measured
    now; require_go refuses unless it equals the package recomputed from the working tree."""
    rel = HERE.relative_to(repo)
    with tempfile.TemporaryDirectory() as td:
        for n in BOUND_FILES:
            got = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{rel / n}"], capture_output=True)
            if got.returncode != 0:
                raise SystemExit(f"refused: {n} is not in the reviewed commit {commit}")
            (Path(td) / n).write_bytes(got.stdout)
        return package(Path(td))


def clock_problems(rec) -> list[str]:
    """Strict, finite, non-negative, typed clock state (R4): checked before ANY work, so altered accounting (a NaN, a
    negative, a string, a bool) can never reach a budget comparison."""
    num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v >= 0  # noqa
    p = []
    if not isinstance(rec, dict) or not isinstance(rec.get("sessions"), list):
        return ["clock.json is not an object with a sessions list"]
    if not num(rec.get("seconds_total")):
        p.append("seconds_total")
    for k in ("seconds_total_live",):
        if k in rec and not num(rec[k]):
            p.append(k)
    for s in rec["sessions"]:
        if not isinstance(s, dict) or not num(s.get("live_s")) or ("charged_s" in s and not num(s["charged_s"])):
            p.append("sessions[]")
            break
    s = rec.get("open_session")
    if s is not None and (not isinstance(s, dict) or not isinstance(s.get("session"), str) or not num(s.get("live_s"))
                          or ("beat_wall" in s and not num(s["beat_wall"]))):
        p.append("open_session")
    return p


def _process_age_s() -> float:
    i = memprobe.proc_info(os.getpid())
    return max(0.0, time.time() - float(i["start"])) if i else 0.0


class Clock:
    """The job's wall clock across sessions (R4): validated strictly before any work; a durable session counted from
    the process's start (or `t0`); a BEAT thread persisting every BEAT_S from a snapshot (no lock is held while a write
    blocks; a write lock serialises writers and `close` waits for it only CLOSE_WAIT_S); a GUARD thread with no file
    I/O that enforces the cap whatever the main thread is doing - at cap - FINAL_S it kills a live worker group
    (`on_cap`), at the cap itself it ends the process (exit 75, no receipt claimed). A dead session is charged at the
    next start its last durable live time plus max(TAIL_S, its watchdog's interval from the last beat to the group's
    and the orchestrator's death); a watchdog that found the orchestrator blocked and could not see it die charges
    until now."""

    def __init__(self, path: Path, t0: float, cap: float, on_cap=None, pre_s: float = 0.0):
        self.path, self.t0, self.cap, self.on_cap, self.pre_s = path, t0, cap, on_cap, pre_s
        self.stop_guard = threading.Event()
        rec = json.loads(path.read_text()) if path.exists() else {"sessions": [], "seconds_total": 0.0,
                                                                   "open_session": None}
        bad = clock_problems(rec)
        if bad:
            raise SystemExit(f"refused: clock.json accounting invalid {bad}; the job holds")
        if rec["open_session"]:
            s = rec["open_session"]
            tail = TAIL_S
            for wp in sorted(path.parent.glob("watchdog_*.json")):
                try:
                    wd = json.loads(wp.read_text())
                except ValueError:
                    continue
                if wd.get("session") != s["session"] or not isinstance(s.get("beat_wall"), (int, float)):
                    continue
                ends = [wd.get(k) for k in ("group_gone_wall", "controller_gone_wall")
                        if isinstance(wd.get(k), (int, float)) and math.isfinite(wd[k])]
                if ends:
                    tail = max(tail, max(ends) - s["beat_wall"])
                if str(wd.get("reason", "")).startswith(("heartbeat stale", "hard deadline")) and \
                        wd.get("controller_gone_wall") is None:
                    tail = max(tail, time.time() - s["beat_wall"])
            charged = float(s["live_s"]) + tail
            rec["seconds_total"] += charged
            rec["sessions"].append({**s, "closed": "crashed", "charged_s": charged, "tail_s": tail})
        self.rec, self.base = rec, rec["seconds_total"]
        rec["open_session"] = {"session": uuid.uuid4().hex[:12], "pid": os.getpid(), "opened_wall": time.time(),
                               "live_s": 0.0, "beat_wall": time.time()}
        self.lock, self.wlock, self.stop_beat = threading.Lock(), threading.Lock(), threading.Event()
        self.base_ready = True
        self.wseq = self.done_seq = 0
        self.capped = False
        self.persist()
        self.thread = threading.Thread(target=self._beat, daemon=True)
        self.thread.start()
        self.guard = threading.Thread(target=self._guard, daemon=True)
        self.guard.start()

    @property
    def session(self) -> str:
        return self.rec["open_session"]["session"] if self.rec["open_session"] else ""

    def _beat(self) -> None:
        while not self.stop_beat.wait(BEAT_S):
            try:
                self.persist()
            except Exception:
                return                                   # the watchdog sees a stale beat and kills any worker

    def _guard(self) -> None:
        while not self.stop_guard.wait(GUARD_S):         # NOT stopped by close: alive until the run ends (R3)
            left = self.remaining()
            if left <= FINAL_S and not self.capped:
                self.capped = True
                if self.on_cap:
                    try:
                        self.on_cap()
                    except Exception:                    # noqa: BLE001
                        pass
            if left <= 0:
                sys.stderr.write("job clock: the six-hour cap was reached before the job finished; no receipt\n")
                sys.stderr.flush()
                os._exit(75)

    def elapsed(self) -> float:
        return self.base + self.pre_s + time.monotonic() - self.t0

    def remaining(self) -> float:
        return self.cap - self.elapsed()

    def persist(self) -> None:
        with self.lock:
            if self.rec["open_session"] is None:
                return
            self.rec["open_session"]["live_s"] = self.pre_s + time.monotonic() - self.t0
            self.rec["open_session"]["beat_wall"] = time.time()
            self.rec["seconds_total_live"] = self.elapsed()
            self.wseq += 1
            seq, snap = self.wseq, json.dumps(self.rec, indent=1, sort_keys=True).encode()
        with self.wlock:
            if seq > self.done_seq:
                write_atomic(self.path, snap)
                self.done_seq = seq

    def beat(self) -> None:
        pass                                              # the beat thread persists; kept for call sites

    def close(self, outcome: str, receipt_raw_sha256: str | None = None) -> None:
        self.stop_beat.set()                              # the beat stops; the cap guard does not
        with self.lock:
            s = dict(self.rec["open_session"], live_s=self.pre_s + time.monotonic() - self.t0, closed=outcome,
                     receipt_raw_sha256=receipt_raw_sha256)
            self.rec["sessions"].append(s)
            self.rec["seconds_total"] = self.elapsed()
            self.rec["open_session"] = None
            self.wseq += 1
            seq, snap = self.wseq, json.dumps(self.rec, indent=1, sort_keys=True).encode()
        if not self.wlock.acquire(timeout=CLOSE_WAIT_S):
            raise RuntimeError("clock: a blocked write holds the clock file; the session stays open (charged at the "
                               "next start)")
        try:
            write_atomic(self.path, snap)
            self.done_seq = seq
        finally:
            self.wlock.release()


def check_accounting(job: Path, raw: Path) -> None:
    """Refuse lost or inconsistent accumulated accounting instead of silently restarting the clock (strictly typed,
    finite, non-negative - R4)."""
    recs, _ = J.read(raw, cap=LIMITS["raw_bytes"]) if raw.exists() else ([], b"")
    cp = job / "clock.json"
    if recs and not cp.exists():
        raise SystemExit("refused: the journal has records but clock.json is missing - the accumulated time is lost")
    if cp.exists():
        c = json.loads(cp.read_text())
        bad = clock_problems(c)
        if bad:
            raise SystemExit(f"refused: clock.json accounting invalid {bad}; the job holds")
    if recs:
        charged = sum(float(r.get("seconds", 0.0)) for r in recs if r.get("t") == "end")
        total = c["seconds_total"] + (float(c["open_session"]["live_s"]) if c.get("open_session") else 0.0)
        if total + 1e-6 < charged:
            raise SystemExit(f"refused: clock.json ({total:.1f} s) is below the journal's charged attempt time "
                             f"({charged:.1f} s) - inconsistent accounting")


def read_capped(p: Path, cap: int) -> tuple[bytes, bool]:
    if not p.exists():
        return b"", False
    with open(p, "rb") as fh:
        b = fh.read(cap + 1)
    return b[:cap], len(b) > cap


def dir_bytes(d: Path) -> int:
    return sum(f.stat().st_size for f in d.rglob("*") if f.is_file() and not f.is_symlink()) if d.exists() else 0


def end_recorded(worker: dict | None, members: list[dict], watchdog: dict | None) -> dict:
    """Recovery of a crashed attempt (R3, shared with Stage A): every live member of the recorded worker's process
    group (enumerated, anchored to the leader's identity) and every recorded member identity killed and confirmed
    gone; only THEN the watchdog (the safeguard retires last). Nothing unidentified is signalled."""
    out = {"killed": [], "watchdog_killed": None}
    if memprobe.valid_ident(worker):
        try:
            out["killed"] = memprobe.end_group(worker, [m for m in members if memprobe.valid_ident(m)],
                                               limit=GONE_S)["killed"]
        except memprobe.Survivors as exc:
            raise SystemExit(f"refused: identified worker processes survive SIGKILL: {exc}; the job holds")
    if memprobe.valid_ident(watchdog) and memprobe.same_process(watchdog):
        try:
            os.kill(watchdog["pid"], signal.SIGKILL)
        except ProcessLookupError:
            pass
        t = time.monotonic()
        while memprobe.same_process(watchdog):
            if time.monotonic() - t > GONE_S:
                raise SystemExit("refused: identified worker processes survive SIGKILL (watchdog); the job holds")
            time.sleep(0.02)
        out["watchdog_killed"] = watchdog
    return out


def plan() -> dict:
    sset = json.loads(SET.read_text())
    reqs = {r["request"]: r for r in sset["requests"]}
    if sorted(sset["delivery_order"]) != sorted(reqs) or len(reqs) != LIMITS["planned"]:
        raise SystemExit("refused: the delivery order does not cover the 600 declared requests")
    for r in reqs.values():
        if sha_file(IMAGES / r["file"]) != r["sha256"]:
            raise SystemExit(f"refused: image {r['file']} differs from the set")
    codex = [str(R.CODEX)]
    with tempfile.TemporaryDirectory(dir=ensure_root()) as td:
        adir = Path(td) / "a"
        img = R.prepare(adir, _synthetic_png(), "x.png")
        pre = preflight(codex, sset, adir, img)
        extra = sorted(p.name for p in (adir / "codex_home").iterdir() if p.name != "auth.json")
        argv = R.exec_argv(codex, sset["reader"], adir, img, sset["prompt"])
    return {"dry_run": True, "requests": len(reqs), "images_verified": len(reqs), "limits": LIMITS,
            "preflight": pre, "codex_home_after_local_commands": extra, "command_template": argv,
            "package": package()}


def _synthetic_png() -> bytes:
    import struct
    import zlib
    raw = b"".join(b"\x00" + bytes([9]) * 8 for _ in range(8))

    def ch(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", 8, 8, 8, 0, 0, 0, 0)) + \
        ch(b"IDAT", zlib.compress(raw)) + ch(b"IEND", b"")


def preflight(codex: list[str], sset: dict, adir: Path, img: Path, *, sandbox: bool = True,
              invocation: bool = True) -> dict:
    """Fresh, no request: effective features, the auth route, and the exec-invocation receipt (network denied)."""
    feats = R.effective_features(codex, sset["reader"], adir, sandbox)
    route = R.auth_route(codex, adir, sandbox)
    inv = R.invocation_receipt(codex, sset["reader"], adir, img, sset["prompt"]) if invocation else \
        {"equivalent": None, "note": "synthetic fixture: no real binary"}
    if invocation and not inv["equivalent"]:
        raise SystemExit(f"refused: the exec invocation does not match its receipts: {inv}")
    if route != "Logged in using ChatGPT" and invocation:
        raise SystemExit(f"refused: auth route {route!r}")
    return {"effective_features": feats, "auth_route": route, "invocation_receipt": inv}


def ensure_root() -> Path:
    ATTEMPTS.mkdir(parents=True, exist_ok=True)
    return ATTEMPTS


def delivery() -> dict:
    """Render every request's model-visible input locally (no request) and freeze the delivered image digests and the
    normalised user text per request."""
    sset = json.loads(SET.read_text())
    codex = [str(R.CODEX)]
    out, instr = {}, set()
    for r in sset["requests"]:
        data = (IMAGES / r["file"]).read_bytes()
        if sha(data) != r["sha256"]:
            raise SystemExit(f"refused: image {r['file']} differs from the set")
        with tempfile.TemporaryDirectory(dir=ensure_root()) as td:
            adir = Path(td) / "a"
            img = R.prepare(adir, data, r["file"])
            rc = R.prompt_input(codex, sset["reader"], adir, img, sset["prompt"])
        if len(rc["images"]) != 1 or not rc["prompt_rendered"]:
            raise SystemExit(f"refused: {r['request']}: {len(rc['images'])} images, prompt rendered "
                             f"{rc['prompt_rendered']}")
        im = rc["images"][0]
        instr.add((rc["instructions_sha256"], tuple(rc["instruction_kinds"])))
        out[r["request"]] = {"image_sha256": im["sha256"], "bytes": im["bytes"], "detail": im["detail"],
                             "mime": im["mime"], "file_sha256": r["sha256"], "reencoded": im["sha256"] != r["sha256"],
                             "user_text_sha256": rc["user_text_sha256"]}
    if len(instr) != 1:
        raise SystemExit(f"refused: the model-visible instructions differ between requests: {instr}")
    (ih, kinds), = instr
    with tempfile.TemporaryDirectory(dir=ensure_root()) as td:
        adir = Path(td) / "a"
        img = R.prepare(adir, _synthetic_png(), "x.png")
        pre = preflight(codex, sset, adir, img)
    d = {"note": "Local renderings of each request's model-visible input by `codex debug prompt-input` with the job's "
                 "flags, allowlist sandbox, environment and the prompt after '--' (no request was sent). The reader "
                 "receives the delivered bytes.",
         "rendered": time.strftime("%Y-%m-%d"), "cli_version": sset["reader"]["cli_version"],
         "instructions_sha256": ih, "instruction_kinds": list(kinds), "preflight": pre,
         "reencoded": sum(v["reencoded"] for v in out.values()),
         "distinct_user_text": len({v["user_text_sha256"] for v in out.values()}), "requests": out}
    DELIVERY.write_text(json.dumps(d, indent=1, sort_keys=True) + "\n")
    return {k: v for k, v in d.items() if k != "requests"}


class Stop(Exception):
    pass


class Deadline:
    """A bounded step: past `seconds` the process ends (exit 75) - nothing after the step is claimed (R4)."""

    def __init__(self, seconds: float, what: str):
        self.t = threading.Timer(seconds, self._fire, args=(what,))
        self.t.daemon = True

    @staticmethod
    def _fire(what: str) -> None:
        sys.stderr.write(f"bounded step overran: {what}; exit 75, nothing claimed\n")
        sys.stderr.flush()
        os._exit(75)

    def __enter__(self):
        self.t.start()
        return self

    def __exit__(self, *exc):
        self.t.cancel()
        return False


class Job:
    def __init__(self, fixture: dict | None):
        self.t0 = time.monotonic()
        self.fx = fixture
        self.mode = "synthetic-fixture" if fixture else "scientific"
        if fixture:
            self.codex, self.sandbox = fixture["codex"], False
            self.images, self.job, self.raw = fixture["images"], fixture["job"], fixture["raw"]
            self.root = fixture["attempts"]
        else:
            self.codex, self.sandbox = [str(R.CODEX)], True
            self.images, self.job, self.raw, self.root = IMAGES, JOB, RAW, ATTEMPTS
        self.proc = self.wd = self.st = None
        self.worker_ident = None
        self.clock = None

    def crash(self, point: str, n) -> None:
        if self.fx and os.environ.get("AIRQ_CRASH") == f"{point}:{n}":
            os._exit(77)

    def rec(self, t: str, **kw) -> dict:
        r = {"t": t, "seq": self.st["seq"] + 1, "package_digest": self.digest, "mode": self.mode, **kw}
        J.append(self.raw, r, cap=LIMITS["raw_bytes"])
        J.apply(self.st, r)
        self.clock.persist()
        return r

    def stop(self, outcome: str, reason: str) -> dict:
        if self.st["open"]:
            self.reconcile_open(f"stop: {reason}")
        data = self.raw.read_bytes() if self.raw.exists() else b""
        # ONE deadline from here through the clock's closure (revision 6, R3): the receipt charges FINAL_WRITE_S for
        # its append AND the close; the timer covering both is cancelled only after the close in _run.
        self.final_deadline = Deadline(FINAL_WRITE_S, "the receipt and the clock's closure").__enter__()
        return self.rec("receipt", outcome=outcome, reason=reason[:2000], counts=J.counts(self.st),
                        journal_sha256=sha(data), raw_bytes_before=len(data),
                        seconds_total=self.clock.elapsed() + FINAL_WRITE_S, limits=LIMITS,
                        smoke=J.smoke_status(self.st, self.order[0]))

    def _cap_kill(self) -> None:
        """The clock guard's enforcement (no file I/O): a live worker group at cap - FINAL_S is killed."""
        w = self.worker_ident
        if self.proc is not None and w and memprobe.same_process(w):
            try:
                os.killpg(w["pgid"], signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass

    # ---- the run --------------------------------------------------------------------------------------------------
    def run(self) -> dict:
        setup = Deadline(SETUP_S, "setup before the clock exists").__enter__()   # armed before ANY accounting I/O
        self.job.mkdir(parents=True, exist_ok=True)
        lock = TaskLock(self.job)
        try:
            check_accounting(self.job, self.raw)
            self.clock = Clock(self.job / "clock.json", self.t0, LIMITS["job_clock_s"], on_cap=self._cap_kill,
                               pre_s=0.0 if self.fx else _process_age_s())
            setup.__exit__()                               # from here the clock's cap guard bounds the process
            try:
                return self._run()
            except BaseException:
                fd = getattr(self, "final_deadline", None)
                if fd is not None:
                    fd.__exit__()                          # the exception is reported; no timer outlives the run
                self._kill_live_worker()
                raise
            finally:
                if self.clock.rec["open_session"] is not None:
                    try:
                        with Deadline(FINAL_WRITE_S, "the clock close"):
                            self.clock.close("ended")
                    except Exception:
                        pass
                self.clock.stop_guard.set()
        finally:
            setup.__exit__()
            lock.release()

    def _admit(self) -> None:
        if self.fx:
            self.sset, self.deliv = self.fx["sset"], self.fx["delivery"]
            self.pkg = self.fx.get("package") or {"package_digest": "f" * 64}
        else:
            with Deadline(ADMIT_TIMEOUT_S, "package and go admission"):
                self.sset, self.deliv = json.loads(SET.read_text()), json.loads(DELIVERY.read_text())
                self.pkg = package()
                stage_a_guard.NEGATIVE_REVIEWS = stage_a_guard.NEGATIVE_REVIEWS | NEGATIVE
                stage_a_guard.require_go(GO, self.pkg, row="aireader", stage="qualification",
                                         verify_at_commit=package_at_commit)
            if self.pkg["cli_version"] != self.sset["reader"]["cli_version"]:
                raise SystemExit("refused: the installed codex CLI is not the pinned version")
        self.digest = self.pkg["package_digest"]
        self.reqs = {r["request"]: r for r in self.sset["requests"]}
        self.order = self.sset["delivery_order"]

    def _run(self) -> dict:
        self._admit()
        recs, _ = J.read(self.raw, cap=LIMITS["raw_bytes"])
        for r in recs:
            if r.get("package_digest") != self.digest or r.get("mode") != self.mode:
                raise SystemExit("refused: the journal was written under another package or mode "
                                 "(mixed resumed state)")
        self.st = J.reconstruct(recs)
        if self.st["receipt"]:
            raise SystemExit(f"refused: the job ended ({self.st['receipt']['outcome']}); nothing runs after a receipt")
        pend = J.pending_quarantine(self.job / "quarantine", recs)
        tail = J.repair_tail(self.raw, self.job / "quarantine")
        if tail and any(p["quarantine"] == tail["quarantine"] for p in pend):
            tail = None                                    # one quarantine, one record (crash before truncation; R6)
        recs, _ = J.read(self.raw, cap=LIMITS["raw_bytes"])
        if recs:
            J.validate(recs, self.sset, self.digest, require_complete=False, mode=self.mode, delivery=self.deliv,
                       instructions_sha256=self.deliv["instructions_sha256"], limits=LIMITS)
        self.st = J.reconstruct(recs)
        try:
            for p in pend + ([tail] if tail else []):
                self.rec("tail_repair", **p)
            if self.st["open"]:
                self.recover()
            self.sweep()
            h = J.holds(self.st, self.order[0]) if recs else None
            if h:                                          # a durable hold: straight to STOPPED, no preflight (R2)
                result = self.stop("STOPPED", h)
            elif self.clock.remaining() - FINAL_S < MIN_ATTEMPT_S:   # an exhausted resume: no preflight (R4)
                result = self.stop("STOPPED", f"job clock: {self.clock.remaining() - FINAL_S:.0f} s left after the "
                                              f"final reserve")
            else:
                pre = self._preflight()
                self.rec("open", session=self.clock.session, wall=time.time(), preflight=pre)
                result = self.loop()
        except (Stop, J.RawCap, subprocess.SubprocessError, OSError, SystemExit, ValueError, KeyError) as exc:
            if isinstance(exc, SystemExit) and str(exc.code).startswith("refused: identified worker"):
                raise                                      # an unkillable worker: hold, nothing more is written
            try:
                result = self.stop("STOPPED", f"{type(exc).__name__}: {exc}")
            except Exception:
                raise exc                                  # persistence failed: no receipt is claimed
        raw = self.raw.read_bytes() if self.raw.exists() else b""
        self.clock.close(result["outcome"], receipt_raw_sha256=sha(raw) if result.get("t") == "receipt" else None)
        fd = getattr(self, "final_deadline", None)
        if fd is not None:
            fd.__exit__()                                  # receipt + closure finished inside the one allowance
        return result

    def _preflight(self) -> dict:
        with tempfile.TemporaryDirectory(dir=ensure_dir(self.root)) as td:
            adir = Path(td) / "a"
            img = R.prepare(adir, _synthetic_png(), "x.png")
            return preflight(self.codex, self.sset, adir, img, sandbox=self.sandbox, invocation=not self.fx)

    def sweep(self) -> None:
        """Abandoned attempt directories of earlier sessions (no open attempt refers to them) are removed; the
        attempts root is bounded (ROOT_CAP) before every attempt."""
        if not Path(self.root).exists():
            return
        for d in Path(self.root).iterdir():
            if d.is_dir():
                shutil.rmtree(d, ignore_errors=True)

    def _kill_live_worker(self) -> None:
        """No worker outlives an orchestrator that is still alive: the whole group (enumerated) and every recorded
        member killed and confirmed gone, reap, and the watchdog ended."""
        if self.proc is not None:
            if self.proc.stdin and not self.proc.stdin.closed:
                try:
                    self.proc.stdin.close()
                except OSError:
                    pass
            self._clean_group(self.worker_ident or {"pid": self.proc.pid, "ppid": os.getpid(),
                                                    "pgid": self.proc.pid, "start": "0.000000"},
                              getattr(self, "members", {}))
            self.proc.wait()
            self.proc = None
        self._end_watchdog()

    def _end_watchdog(self) -> None:
        if self.wd is not None:
            try:
                self.wd.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self.wd.kill()
                self.wd.wait()
            if self.wd.stdout:
                self.wd.stdout.close()
            self.wd = None

    # ---- recovery -------------------------------------------------------------------------------------------------
    def _members_path(self, aid: str) -> Path:
        return self.job / f"members_{aid}.json"

    def reconcile_open(self, why: str) -> None:
        """Bring an open attempt to an end before any receipt: a live worker of THIS process is ended and its group
        cleaned; otherwise the recovery path (identity-verified)."""
        if self.proc is not None:
            self._kill_live_worker()
        self.recover(note=why)

    def recover(self, note: str = "") -> None:
        o, d = self.st["open"], self.st["open_dispatched"]
        adir = Path(o["adir"])
        killed = []
        if d:
            mp = self._members_path(o["attempt_id"])
            try:
                members = list(json.loads(mp.read_text()).values()) if mp.exists() else []
            except ValueError:
                members = []
            res = end_recorded(d.get("worker"), members, d.get("watchdog"))
            killed = res["killed"] + ([res["watchdog_killed"]] if res["watchdog_killed"] else [])
        ev = {}
        if adir.exists():
            for name, cap in (("stdout", R.EVENTS_KEEP), ("stderr", R.STDERR_KEEP), ("last.txt", R.ANSWER_KEEP)):
                b, more = read_capped(adir / name, 1 << 20)
                ev[name] = {**R.bounded(b, cap), "captured_prefix": True, "source_truncated": more}
        finding = "dispatched_no_end" if d else "not_dispatched"
        if not self.st["open_recovered"]:              # a crash during an earlier recovery already recorded it
            self.rec("recovered", attempt_id=o["attempt_id"], finding=finding, killed=killed, evidence=ev,
                     note=note[:500], rule="dispatched without end: interrupted, retained as a final error, never "
                                           "re-asked; never dispatched: charged, retry permitted")
            self.crash("recovery", o["attempt_no"])
        self.rec("end", attempt_id=o["attempt_id"], request=o["request"],
                 outcome="interrupted" if d else "not_dispatched", retained=bool(d), seconds=0.0, answer=None)
        if adir.exists():
            shutil.rmtree(adir.parent, ignore_errors=True)
        self._members_path(o["attempt_id"]).unlink(missing_ok=True)

    # ---- the loop -------------------------------------------------------------------------------------------------
    def loop(self) -> dict:
        for idx, rq in enumerate(self.order):
            if rq in self.st["final"]:
                continue
            r = self.reqs[rq]
            while True:
                h = J.holds(self.st, self.order[0])
                if h:
                    return self.stop("STOPPED", h)
                tries = self.st["tries"].get(rq, 0)
                if tries >= LIMITS["max_tries_per_request"]:
                    self.crash("final", self.st["attempts"])
                    self.rec("final", request=rq, outcome="no_response", tries=tries)
                    break
                if self.st["attempts"] >= LIMITS["max_attempts"]:
                    return self.stop("STOPPED", f"attempt cap {LIMITS['max_attempts']} reached")
                budget = self.clock.remaining() - FINAL_S
                if budget < MIN_ATTEMPT_S:
                    return self.stop("STOPPED", f"job clock: {budget:.0f} s left after the final reserve")
                size = self.raw.stat().st_size if self.raw.exists() else 0
                if size + 3 * J.MAX_RECORD > LIMITS["raw_bytes"] - RAW_FINAL_BYTES:
                    return self.stop("STOPPED", f"raw output {size} bytes: the next attempt might not fit")
                if dir_bytes(Path(self.root)) > ROOT_CAP:
                    return self.stop("STOPPED", f"attempts root over {ROOT_CAP} bytes")
                end = self.attempt(r, min(float(LIMITS["attempt_timeout_s"]), budget))
                if end["retained"]:
                    break
        h = J.holds(self.st, self.order[0])
        if h:
            return self.stop("STOPPED", h)
        return self.stop("COMPLETE", f"all {len(self.order)} requests final")

    def _clean_group(self, w: dict | None, members: dict) -> bool:
        """Every live member of the attempt's process group (enumerated; the unreaped leader keeps the group id ours)
        and every recorded member killed and confirmed gone."""
        if not w:
            return True
        try:
            memprobe.end_group(w, list(members.values()), limit=GONE_S, own_leader=True)
        except memprobe.Survivors as exc:
            raise SystemExit(f"refused: identified worker processes survive SIGKILL (group): {exc}; the job holds")
        return True

    def attempt(self, r: dict, timeout: float) -> dict:
        n, rq = self.st["attempts"] + 1, r["request"]
        tr = self.st["tries"].get(rq, 0) + 1
        data = (self.images / r["file"]).read_bytes()
        if sha(data) != r["sha256"]:
            raise Stop(f"image {r['file']} differs from the set (nothing sent)")
        base = Path(tempfile.mkdtemp(dir=ensure_dir(self.root)))
        adir = base / "a"
        try:
            img = R.prepare(adir, data, r["file"])
            rc = R.prompt_input(self.codex, self.sset["reader"], adir, img, self.sset["prompt"], self.sandbox)
            want = self.deliv["requests"][rq]
            im = rc["images"][0] if len(rc["images"]) == 1 else {}
            if rc["instructions_sha256"] != self.deliv["instructions_sha256"] or len(rc["images"]) != 1 or \
                    im.get("sha256") != want["image_sha256"] or im.get("bytes") != want.get("bytes") or \
                    im.get("detail") != want.get("detail") or rc["user_text_sha256"] != want.get("user_text_sha256") \
                    or not rc["prompt_rendered"]:
                raise Stop(f"prompt-input receipt for {rq} differs from the frozen delivery (nothing sent)")
        except BaseException:
            shutil.rmtree(base, ignore_errors=True)
            raise
        receipt = {"instructions_sha256": rc["instructions_sha256"], "image_sha256": im["sha256"],
                   "image_bytes": im["bytes"], "detail": im["detail"], "user_text_sha256": rc["user_text_sha256"]}
        self.crash("before_begin", n)
        aid = f"{n:03d}.{rq}.{tr}"
        self.rec("begin", **{"attempt_id": aid, "attempt_no": n, "request": rq, "try": tr, "item": r["item"],
                             "view": r["view"], "timeout_s": float(timeout), "receipt": receipt, "adir": str(adir),
                             "wall": time.time()})
        self.crash("after_begin", n)
        argv = R.gated(R.boxed(adir, R.exec_argv(self.codex, self.sset["reader"], adir, img, self.sset["prompt"]),
                               self.sandbox))
        self.members = {}
        with open(adir / "stdout", "wb") as so, open(adir / "stderr", "wb") as se:
            self.proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=so, stderr=se, env=R.env(adir),
                                         cwd=adir / "w", start_new_session=True)
        kq = memprobe.exit_watch(self.proc.pid)
        self.worker_ident = memprobe.proc_info(self.proc.pid)
        if not memprobe.valid_ident(self.worker_ident):            # fail closed before GO: nothing is sent
            raise Stop(f"{aid}: the worker's identity cannot be read before dispatch (nothing sent)")
        hard = time.monotonic() + timeout + TERM_GRACE_S + 5.0
        ctl = memprobe.proc_info(os.getpid())
        warg = {"controller": ctl, "leader": self.worker_ident, "session": self.clock.session,
                "beat_file": str(self.job / "clock.json"), "deadline_monotonic": hard, "stale_s": STALE_S,
                "record": str(self.job / f"watchdog_{aid}.json"), "members_file": str(self._members_path(aid)),
                "tick_fd": None, "tick_stale_s": 0.0}
        self.wd = subprocess.Popen([sys.executable, str(WATCHDOG), json.dumps(warg)], start_new_session=True,
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE)
        ready = select.select([self.wd.stdout], [], [], 10.0)[0]
        line = self.wd.stdout.readline() if ready else b""
        wd_ident = memprobe.proc_info(self.wd.pid)
        if line.strip() != b"ARMED" or not memprobe.valid_ident(wd_ident):
            raise Stop(f"{aid}: the watchdog did not arm (nothing sent)")
        t = time.monotonic()
        self.rec("dispatched", attempt_id=aid, pid=self.proc.pid, worker=self.worker_ident, watchdog=wd_ident,
                 wall=time.time())
        self.crash("after_dispatch", n)
        left = self.clock.remaining() - FINAL_S                  # refreshed immediately before GO
        if left < MIN_ATTEMPT_S:
            self.proc.stdin.close()                              # the gate exits 97: nothing is sent
            exited = False
            for _ in range(200):
                if memprobe.exited(kq):
                    exited = True
                    break
                time.sleep(0.01)
            self._finish_worker(kq, exited)
            self.rec("end", attempt_id=aid, request=rq, outcome="not_dispatched", retained=False,
                     seconds=time.monotonic() - t, answer=None, cause="not_sent")
            shutil.rmtree(base, ignore_errors=True)
            raise Stop(f"job clock: {left:.0f} s left before GO; the gate was closed unsent")
        timeout = min(timeout, left)
        self.proc.stdin.write(b"GO\n")
        self.proc.stdin.close()
        self.crash("after_go", n)
        deadline, timed_out, overflow, kill, exited = t + timeout, False, None, None, False
        last_members = 0.0
        while True:
            if memprobe.exited(kq):
                exited = True
                break
            if time.monotonic() >= deadline:
                timed_out = True
                break
            so_n, se_n = (adir / "stdout").stat().st_size, (adir / "stderr").stat().st_size
            if so_n > R.STDOUT_CAP or se_n > R.STDERR_CAP or dir_bytes(adir) > TEMP_CAP + len(data):
                overflow = f"stdout {so_n}, stderr {se_n} bytes"
                break
            if time.monotonic() - last_members >= BEAT_S:
                last_members = time.monotonic()
                for p, i in memprobe.task_processes([self.proc.pid], {self.proc.pid}).items():
                    self.members.setdefault(str(p), i)
                write_json_atomic(self._members_path(aid), self.members)
            time.sleep(0.05)
        seconds = time.monotonic() - t
        if exited:
            self.crash("after_leader_exit", n)
        if not exited:
            kill = self._term_kill(kq)
        so_n, se_n = (adir / "stdout").stat().st_size, (adir / "stderr").stat().st_size
        if not overflow and (so_n > R.STDOUT_CAP or se_n > R.STDERR_CAP or dir_bytes(adir) > TEMP_CAP + len(data)):
            overflow = f"stdout {so_n}, stderr {se_n} bytes (at exit)"         # a quick-exit overflow
        rcode = self._finish_worker(kq, True)
        self.crash("after_response", n)
        out, o1 = read_capped(adir / "stdout", R.STDOUT_CAP)
        err, o2 = read_capped(adir / "stderr", R.STDERR_CAP)
        last_b, o3 = read_capped(adir / "last.txt", 1 << 20)
        over = bool(overflow) or o1 or o2 or o3
        last = last_b.decode("utf-8", "replace") if (adir / "last.txt").exists() else None
        c = R.classify(out, err, last, rcode, timed_out=timed_out, overflow=over)
        end = self.rec("end", attempt_id=aid, request=rq, seconds=seconds, kill=kill,
                       overflow_detail=overflow, group_clean=True, **{k: v for k, v in c.items()})
        self.crash("after_end", n)
        self.clock.persist()
        self.crash("after_state", n)
        shutil.rmtree(base, ignore_errors=True)
        self._members_path(aid).unlink(missing_ok=True)
        return end

    def _term_kill(self, kq) -> dict:
        """SIGTERM to the group, TERM_GRACE_S for the leader's exit (seen by kqueue, not reaped), then SIGKILL."""
        t = time.monotonic()
        try:
            os.killpg(self.proc.pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
        how = "SIGKILL"
        while time.monotonic() - t < TERM_GRACE_S:
            if memprobe.exited(kq):
                how = "SIGTERM"
                break
            time.sleep(0.02)
        if how == "SIGKILL":
            try:
                os.killpg(self.proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        return {"how": how, "kill_to_reap_s": round(time.monotonic() - t, 3)}

    def _finish_worker(self, kq, exited: bool):
        """Whole-group cleanup (also after an ordinary leader exit), reap, end the watchdog."""
        self._clean_group(self.worker_ident, self.members)
        self.proc.wait()
        rcode = self.proc.returncode
        self.proc = None
        self._end_watchdog()
        return rcode


def admit_clock(clock_path: Path, raw_bytes: bytes, receipt: dict) -> dict:
    """A COMPLETE qualifies only together with a FINISHED clock (revision 6, R3): clock.json valid and closed, its last
    session closed on this receipt's outcome and naming the sha256 of exactly this journal, its total within the cap and
    not above the receipt's own charged total. A closure that never finished leaves the COMPLETE non-qualifying."""
    if not Path(clock_path).exists():
        raise SystemExit("refused: no clock record beside the journal")
    c = json.loads(Path(clock_path).read_text())
    bad = clock_problems(c)
    if bad:
        raise SystemExit(f"refused: clock record invalid {bad}")
    last = c["sessions"][-1] if c["sessions"] else {}
    if c.get("open_session") is not None or last.get("closed") != receipt.get("outcome") or \
            last.get("receipt_raw_sha256") != sha(raw_bytes):
        raise SystemExit("refused: the clock was not closed on this receipt (an unfinished closure does not qualify)")
    if c["seconds_total"] > LIMITS["job_clock_s"] or c["seconds_total"] > receipt.get("seconds_total", -1.0):
        raise SystemExit(f"refused: the closed clock ({c['seconds_total']:.1f} s) exceeds the cap or the receipt's "
                         f"charged total")
    return {"seconds_total": c["seconds_total"], "sessions": len(c["sessions"])}


def ensure_dir(p) -> Path:
    Path(p).mkdir(parents=True, exist_ok=True)
    return Path(p)


def run(*, fixture: dict | None = None) -> dict:
    return Job(fixture).run()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "plan"
    out = {"plan": plan, "delivery": delivery, "run": run}[cmd]()
    print(json.dumps(out, indent=1, default=str))
