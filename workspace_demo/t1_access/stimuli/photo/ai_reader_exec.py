"""AI image-reader qualification, revision 4: the bounded READER JOB executor (the job brief is AI_READER_JOB.md; Codex
RSC 5a8d7ac closures 1, 3, 4, 5 and 6; R052 handoff 46125389). It is the orchestrator's half: it holds the key and the
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

ORDER OF A RUN. lock -> refuse lost accounting (a journal without clock.json, or a clock below the journal's charged
time) -> the clock's durable session opens BEFORE anything else and beats every BEAT_S from its own thread through
hashing, the go, receipts, recovery, attempts, cleanup and the final writes -> package and go (scientific) -> journal:
pending quarantine records, tail repair, VALIDATION of the incomplete journal (validate(require_complete=False) with the
package's instruction pin, the frozen delivery and the limits) -> reconstruction -> recovery of an open attempt by
VERIFIED IDENTITY (the recorded worker and members, pid and start time; nothing unidentified is signalled) -> the
abandoned-attempt sweep -> a FRESH preflight (effective features, auth route, the exec-invocation receipt) in the open
record -> the loop.

THE LOOP. Before EVERY attempt, from durable records only: the holds (a structural failure; the smoke over every
attempt of the first request - J.holds), then the request's 3-try limit (a third non-retained attempt -> final
no_response), the 660 cap, the clock (min(120 s, remaining - FINAL_S), none under MIN_ATTEMPT_S), the raw cap (three
records of MAX_RECORD must fit under 20 MiB - RAW_FINAL_BYTES) and the attempts-root cap. An attempt: its directory and
prompt-input receipt (instructions = pin, image = frozen delivered digest, user text = frozen per-request hash; a
mismatch holds with nothing sent and the directory removed) -> begin (fsync) -> worker started in its own process group
with a WATCHDOG (stage_a_watchdog.py: the orchestrator's death or a stale clock beat or the hard attempt deadline
kills the group) -> dispatched (fsync, the worker's and watchdog's identities) -> the remaining time REFRESHED: too
little and the gate is closed unsent (not_dispatched, charged) -> 'GO' -> wait (exit seen by kqueue without reaping;
stdout, stderr and directory caps) -> final size check -> SIGTERM/grace/SIGKILL if alive -> the whole process group
and every recorded member killed and confirmed gone, also after an ordinary leader exit -> reap -> end (fsync).

STOPS. Every stop after the journal is admitted - a limit, a hold, a receipt mismatch, RawCap, a launch or pipe
failure, a receipt renderer timeout, an exception - first reconciles an open attempt (identity-verified kill, recovered
+ end) and then writes the STOPPED receipt with counters, smoke status, limits, clock and journal hash. If persistence
itself fails, no receipt is claimed: the journal stays a valid incomplete journal and the next start re-derives its
holds.

FIXTURE MODE. `run(fixture=...)` replaces the binary, the directories and the sandbox for the mechanism tests; its
records are marked mode 'synthetic-fixture', the go is not consulted, and the scorer refuses that mode unless asked
explicitly, labelling the output as not a qualification result.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
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
from enforce import write_json_atomic  # noqa: E402
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
BOUND_FILES = ["ai_reader_qual_set.json", "ai_reader_qual_key.json", "ai_reader_delivery.json", "ai_reader_exec.py",
               "ai_reader_score.py", "ai_reader_runtime.py", "ai_reader_journal.py", "ai_reader_key.py",
               "ai_reader_frame.py", "ai_reader_qual.py", "AI_READER_JOB.md", "AI_READER_DESIGN.md",
               "stage_a_guard.py", "enforce.py", "memprobe.py", "stage_a_watchdog.py"]
NEGATIVE = {"cf3e49e", "7048bb8", "5a8d7ac"}


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


class Clock:
    """The job's wall clock across sessions (closure 5): a durable session from the first instant of `run`, a beat
    thread persisting every BEAT_S whatever the main thread is doing, and a dead session charged its last durable
    live time plus TAIL_S at the next start."""

    def __init__(self, path: Path, t0: float, cap: float):
        self.path, self.t0, self.cap = path, t0, cap
        rec = json.loads(path.read_text()) if path.exists() else {"sessions": [], "seconds_total": 0.0,
                                                                   "open_session": None}
        if rec["open_session"]:
            s = rec["open_session"]
            charged = float(s["live_s"]) + TAIL_S
            rec["seconds_total"] += charged
            rec["sessions"].append({**s, "closed": "crashed", "charged_s": charged})
        self.rec, self.base = rec, rec["seconds_total"]
        rec["open_session"] = {"session": uuid.uuid4().hex[:12], "pid": os.getpid(), "opened_wall": time.time(),
                               "live_s": 0.0}
        self.lock, self.stop_beat = threading.Lock(), threading.Event()
        self.persist()
        self.thread = threading.Thread(target=self._beat, daemon=True)
        self.thread.start()

    def _beat(self) -> None:
        while not self.stop_beat.wait(BEAT_S):
            try:
                self.persist()
            except Exception:
                return                                   # the watchdog sees a stale beat and kills any worker

    def elapsed(self) -> float:
        return self.base + time.monotonic() - self.t0

    def remaining(self) -> float:
        return self.cap - self.elapsed()

    def persist(self) -> None:
        with self.lock:
            if self.rec["open_session"] is None:
                return
            self.rec["open_session"]["live_s"] = time.monotonic() - self.t0
            self.rec["seconds_total_live"] = self.elapsed()
            write_json_atomic(self.path, self.rec)

    def beat(self) -> None:
        pass                                              # the beat thread persists; kept for call sites

    def close(self, outcome: str) -> None:
        self.stop_beat.set()
        self.thread.join(timeout=5)
        with self.lock:
            s = dict(self.rec["open_session"], live_s=time.monotonic() - self.t0, closed=outcome)
            self.rec["sessions"].append(s)
            self.rec["seconds_total"] = self.elapsed()
            self.rec["open_session"] = None
            write_json_atomic(self.path, self.rec)


def check_accounting(job: Path, raw: Path) -> None:
    """Refuse lost or inconsistent accumulated accounting instead of silently restarting the clock."""
    recs, _ = J.read(raw) if raw.exists() else ([], b"")
    cp = job / "clock.json"
    if recs and not cp.exists():
        raise SystemExit("refused: the journal has records but clock.json is missing - the accumulated time is lost")
    if recs:
        c = json.loads(cp.read_text())
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


def kill_identified(idents: list[dict], limit: float = GONE_S) -> list[dict]:
    """SIGKILL every process whose recorded identity (pid AND start time) is still the live process with that pid;
    confirm them gone. A pid now owned by another process is never signalled."""
    live = [i for i in idents if i and memprobe.same_process(i)]
    for i in live:
        try:
            os.kill(i["pid"], signal.SIGKILL)
        except ProcessLookupError:
            pass
    t = time.monotonic()
    while any(memprobe.same_process(i) for i in live):
        if time.monotonic() - t > limit:
            raise SystemExit(f"refused: identified worker processes survive SIGKILL: {live}; the job holds")
        time.sleep(0.05)
    return live


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
        return self.rec("receipt", outcome=outcome, reason=reason[:2000], counts=J.counts(self.st),
                        journal_sha256=sha(data), raw_bytes_before=len(data), seconds_total=self.clock.elapsed(),
                        limits=LIMITS, smoke=J.smoke_status(self.st, self.order[0]))

    # ---- the run --------------------------------------------------------------------------------------------------
    def run(self) -> dict:
        self.job.mkdir(parents=True, exist_ok=True)
        lock = TaskLock(self.job)
        try:
            check_accounting(self.job, self.raw)
            self.clock = Clock(self.job / "clock.json", self.t0, LIMITS["job_clock_s"])
            try:
                return self._run()
            except BaseException:
                self._kill_live_worker()
                raise
            finally:
                if self.clock.rec["open_session"] is not None:
                    try:
                        self.clock.close("ended")
                    except Exception:
                        pass
        finally:
            lock.release()

    def _admit(self) -> None:
        if self.fx:
            self.sset, self.deliv = self.fx["sset"], self.fx["delivery"]
            self.pkg = self.fx.get("package") or {"package_digest": "f" * 64}
        else:
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
        recs, _ = J.read(self.raw)
        for r in recs:
            if r.get("package_digest") != self.digest or r.get("mode") != self.mode:
                raise SystemExit("refused: the journal was written under another package or mode "
                                 "(mixed resumed state)")
        self.st = J.reconstruct(recs)
        if self.st["receipt"]:
            raise SystemExit(f"refused: the job ended ({self.st['receipt']['outcome']}); nothing runs after a receipt")
        pend = J.pending_quarantine(self.job / "quarantine", recs)
        tail = J.repair_tail(self.raw, self.job / "quarantine")
        recs, _ = J.read(self.raw)
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
            pre = self._preflight()
            self.rec("open", session=self.clock.rec["open_session"]["session"], wall=time.time(), preflight=pre)
            result = self.loop()
        except (Stop, J.RawCap, subprocess.SubprocessError, OSError, SystemExit, ValueError, KeyError) as exc:
            if isinstance(exc, SystemExit) and str(exc.code).startswith("refused: identified worker"):
                raise                                      # an unkillable worker: hold, nothing more is written
            try:
                result = self.stop("STOPPED", f"{type(exc).__name__}: {exc}")
            except Exception:
                raise exc                                  # persistence failed: no receipt is claimed
        self.clock.close(result["outcome"])
        return result

    def _preflight(self) -> dict:
        with tempfile.TemporaryDirectory(dir=self.root) as td:
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
        """No worker outlives an orchestrator that is still alive: SIGKILL the group, clean it by identity, reap, and
        end the watchdog."""
        if self.proc is not None:
            w = getattr(self, "worker_ident", None)
            if self.proc.stdin and not self.proc.stdin.closed:
                try:
                    self.proc.stdin.close()
                except OSError:
                    pass
            try:
                os.killpg(self.proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            self._clean_group(w, getattr(self, "members", {}))
            self.proc.wait()
            self.proc = None
        if self.wd is not None:
            try:
                self.wd.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self.wd.kill()
                self.wd.wait()
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
            members = list(json.loads(mp.read_text()).values()) if mp.exists() else []
            killed = kill_identified([d.get("worker"), d.get("watchdog")] + members)
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
        """SIGKILL the attempt's process group until no live member remains (an exited, unreaped leader answers
        EPERM), then every recorded member by identity; confirm all gone."""
        if not w:
            return True
        pgid, t = w["pgid"], time.monotonic()
        while True:
            try:
                os.killpg(pgid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            if not [p for p in memprobe.task_processes([], {pgid}) if p != w["pid"]]:
                break
            if time.monotonic() - t > GONE_S:
                raise SystemExit("refused: identified worker processes survive SIGKILL (group); the job holds")
            time.sleep(0.02)
        kill_identified([m for m in members.values() if m["pid"] != w["pid"]])
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
            if rc["instructions_sha256"] != self.deliv["instructions_sha256"] or len(rc["images"]) != 1 or \
                    rc["images"][0]["sha256"] != want["image_sha256"] or \
                    rc["user_text_sha256"] != want.get("user_text_sha256", rc["user_text_sha256"]) or \
                    not rc["prompt_rendered"]:
                raise Stop(f"prompt-input receipt for {rq} differs from the frozen delivery (nothing sent)")
        except BaseException:
            shutil.rmtree(base, ignore_errors=True)
            raise
        receipt = {"instructions_sha256": rc["instructions_sha256"], "image_sha256": rc["images"][0]["sha256"],
                   "image_bytes": rc["images"][0]["bytes"], "detail": rc["images"][0]["detail"],
                   "user_text_sha256": rc["user_text_sha256"]}
        self.crash("before_begin", n)
        aid = f"{n:03d}.{rq}.{tr}"
        self.rec("begin", **{"attempt_id": aid, "attempt_no": n, "request": rq, "try": tr, "item": r["item"],
                             "view": r["view"], "timeout_s": float(timeout), "receipt": receipt, "adir": str(adir),
                             "wall": time.time()})
        self.crash("after_begin", n)
        argv = R.gated(R.boxed(adir, R.exec_argv(self.codex, self.sset["reader"], adir, img, self.sset["prompt"]),
                               self.sandbox))
        with open(adir / "stdout", "wb") as so, open(adir / "stderr", "wb") as se:
            self.proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=so, stderr=se, env=R.env(adir),
                                         cwd=adir / "w", start_new_session=True)
        kq = memprobe.exit_watch(self.proc.pid)
        self.worker_ident = memprobe.proc_info(self.proc.pid) or {"pid": self.proc.pid, "pgid": self.proc.pid,
                                                                  "ppid": os.getpid(), "start": "unknown"}
        self.members = {}
        hard = time.monotonic() + timeout + TERM_GRACE_S + 5.0
        warg = {"controller_pid": os.getpid(), "pgid": self.proc.pid, "beat_file": str(self.job / "clock.json"),
                "deadline_monotonic": hard, "stale_s": STALE_S, "grace_s": TERM_GRACE_S,
                "record": str(self.job / f"watchdog_{aid}.json")}
        self.wd = subprocess.Popen([sys.executable, str(WATCHDOG), json.dumps(warg)], start_new_session=True,
                                   stdin=subprocess.DEVNULL)
        wd_ident = memprobe.proc_info(self.wd.pid) or {"pid": self.wd.pid, "pgid": self.wd.pid, "start": "unknown"}
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
        if self.wd is not None:
            try:
                self.wd.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self.wd.kill()
                self.wd.wait()
            self.wd = None
        return rcode


def ensure_dir(p) -> Path:
    Path(p).mkdir(parents=True, exist_ok=True)
    return Path(p)


def run(*, fixture: dict | None = None) -> dict:
    return Job(fixture).run()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "plan"
    out = {"plan": plan, "delivery": delivery, "run": run}[cmd]()
    print(json.dumps(out, indent=1, default=str))
