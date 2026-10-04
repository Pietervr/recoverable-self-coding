"""Image audit, step 3: the bounded audit JOB executor - the admitted reader route of revision 17, REUSED, not
re-implemented (R052 ruling 1a, handoff 08f09009). The job brief is AI_AUDIT_JOB.md.

REUSE. This module imports the reviewed qualification executor (ai_reader_exec.py, unchanged, bound by its own 25-field
package) and runs its `Job` - the owned CLI, the deny-by-default allowlist, the per-attempt prompt-input receipt, the
exec-invocation receipt in every preflight, the gate, the watchdog, the journal with its recovery and holds, the clock
and its closure, the STOPPED receipt on every stop - with exactly three differences, each stated and fixtured:
  1. CONFIGURATION. `configure(k)` rebinds the executor module's eight path/limit names (SET, DELIVERY, IMAGES, JOB,
     RAW, GO, ATTEMPTS, LIMITS) to round k's audit files, directories and limits, in THIS process only; every Job method
     reads them at call time. The attempts root is /tmp/ra (the qualification's is /tmp/rq: a sweep never touches the
     other job's directories).
  2. ADMISSION. `AuditJob._admit` binds the go as row "aiaudit", stage "audit" against the AUDIT package (below), checks
     the pinned CLI version, re-derives round k's set and key from committed inputs (ai_audit_set.check) and checks the
     round's delivery (the reader's instruction pin, one image per request equal to the item file, the prompt
     rendered) - all inside the reviewed ADMIT_TIMEOUT_S deadline.
  3. THE PROMPT PER REQUEST. The qualification sent one prompt; the audit sends the request's own frozen prompt
     (`AuditJob.attempt` sets it before the reviewed `attempt`, which renders and compares the receipt for exactly
     that prompt - user text hash and prompt_rendered - before anything is sent).
Nothing else changes: one fresh, stateless, image-only request per question, never carrying a prior answer; a retry
only when no answer came back; an answer is final however wrong; the smoke rule on the first request; the holds.

LIMITS (AI_READER_JOB.md: "up to 400 reader turns, a separate job with its own frozen state and caps"). The whole
audit, all rounds: <= 400 attempts and <= 6 h. Round k: planned = its requests; max attempts = min(ceil(1.1 x
planned), 400 - attempts charged in rounds < k); clock = 6 h - seconds charged in rounds < k; 3 tries per request,
120 s per attempt, raw journal <= 20 MiB. The charged attempts and seconds of earlier rounds come from their COMMITTED
score files (ai_audit_score.py, which admits each round's journal and closed clock); a round refuses when its planned
requests exceed the attempts left.

    .venv-image/bin/python stimuli/photo/ai_audit_exec.py delivery 1   # renders round 1's inputs locally (no request)
    .venv-image/bin/python stimuli/photo/ai_audit_exec.py plan 1       # identity and boundary checks, no request
    .venv-image/bin/python stimuli/photo/ai_audit_exec.py package      # prints the audit package
    .venv-image/bin/python stimuli/photo/ai_audit_exec.py run 1        # only with AIAUDIT_GO.json bound
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ai_audit_set as S  # noqa: E402
import ai_reader_exec as E  # noqa: E402
import ai_reader_runtime as R  # noqa: E402
import stage_a_guard  # noqa: E402

GO = HERE / "AIAUDIT_GO.json"
ATTEMPTS = Path(tempfile.gettempdir()) / "ra"
CAPTURES = HERE.parents[1] / "captures"
TOTAL = {"max_attempts": 400, "job_clock_s": 6 * 3600}
PER_ROUND = {"max_tries_per_request": 3, "attempt_timeout_s": 120, "answer_chars": R.ANSWER_KEEP,
             "raw_bytes": 20 * 1024 * 1024}
ROW, STAGE = "aiaudit", "audit"
NEGATIVE: set[str] = set()
# The audit package: every file the audit's behaviour or its scoring depends on, by path relative to this directory.
BOUND_FILES = [
    # the audit's own code, brief, inputs and round-1 objects
    "ai_audit_exec.py", "ai_audit_set.py", "ai_audit_score.py", "ai_audit_sources.py", "AI_AUDIT_JOB.md",
    "second_view_candidates.json", "ai_audit_sources.json", "manifest_dev.json", "dev_pool.json", "dose.py",
    "ai_audit_set_r1.json", "ai_audit_key_r1.json", "ai_audit_delivery_r1.json",
    # the frozen audit freeze, map and scorer identity (audit_package.py pins)
    "../../audit_app/IMAGE_AUDIT_FREEZE.md", "audit_alias_map.json", "audit_alias_map.py", "audit_package.py",
    # the admitted reader route, reused unchanged
    "ai_reader_exec.py", "ai_reader_runtime.py", "ai_reader_journal.py", "ai_reader_score.py", "ai_reader_key.py",
    "ai_reader_qual_set.json", "ai_reader_delivery.json",
    "stage_a_guard.py", "enforce.py", "memprobe.py", "stage_a_watchdog.py",
]


def sha(b: bytes) -> str:
    return E.sha(b)


def _field(name: str) -> str:
    return Path(name).name.replace(".", "_") + "_sha256"


def delivery_path(k: int) -> Path:
    return HERE / f"ai_audit_delivery_r{k}.json"


def raw_path(k: int) -> Path:
    return HERE / f"ai_audit_raw_r{k}.jsonl"


def job_dir(k: int) -> Path:
    return CAPTURES / f"ai_audit_job_r{k}"


def package(read=None, codex: Path = R.CODEX) -> dict:
    """Every bound file's sha256, the binary and runtime fields (as the reader's package), the round-1 template and the
    reader's instruction pin; `package_digest` over all of it. `read(name)` returns a bound file's bytes (the working
    tree by default; the reviewed commit's blobs in `package_at_commit`)."""
    read = read or (lambda n: (HERE / n).read_bytes())
    p = {_field(n): sha(read(n)) for n in BOUND_FILES}
    qual = json.loads(read("ai_reader_qual_set.json"))
    deliv = json.loads(read("ai_reader_delivery.json"))
    p["things_definitions_sha256"] = sha(S.DEFS.read_bytes())
    p["codex_realpath"] = str(Path(codex).resolve())
    p["codex_sha256"] = E.sha_file(codex)
    p["codex_package_json_sha256"] = E.sha_file(Path(codex).resolve().parents[1] / "codex-package.json")
    p["codex_tree_sha256"] = R.tree_sha(Path(codex).resolve().parents[1])
    p["cli_version"] = subprocess.run([str(codex), "--version"], capture_output=True, text=True,
                                      env={"PATH": "/usr/bin:/bin"}, timeout=30).stdout.strip()
    p["sandbox_exec_sha256"] = E.sha_file(R.SANDBOX_EXEC)
    p["command_template_sha256"] = R.template_sha(qual["reader"], "<per-request frozen prompt>")
    p["instructions_sha256"] = deliv["instructions_sha256"]
    p["package_digest"] = sha(json.dumps(p, sort_keys=True).encode())
    return p


def package_at_commit(commit: str, repo: Path = stage_a_guard.RSC) -> dict:
    rel = HERE.relative_to(repo)

    def read(n: str) -> bytes:
        path = (rel / n).as_posix()
        parts = []
        for part in path.split("/"):                   # resolve '..' inside the repository path
            if part == "..":
                parts.pop()
            elif part not in ("", "."):
                parts.append(part)
        got = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{'/'.join(parts)}"], capture_output=True)
        if got.returncode != 0:
            raise SystemExit(f"refused: {n} is not in the reviewed commit {commit}")
        return got.stdout
    return package(read)


def prior_charges(k: int) -> dict:
    """Attempts and seconds charged by rounds < k, from their committed score files."""
    att, secs = 0, 0.0
    for j in range(1, k):
        sc = json.loads(S.score_path(j).read_text())
        att += int(sc["charged"]["attempts"])
        secs += float(sc["charged"]["seconds"])
    return {"attempts": att, "seconds": secs}


def limits(k: int, n_requests: int) -> dict:
    prior = prior_charges(k)
    left_att = TOTAL["max_attempts"] - prior["attempts"]
    left_s = TOTAL["job_clock_s"] - prior["seconds"]
    if n_requests <= 0 or n_requests > left_att:
        raise SystemExit(f"refused: round {k} plans {n_requests} requests with {left_att} of "
                         f"{TOTAL['max_attempts']} audit attempts left")
    if left_s <= E.FINAL_S + E.MIN_ATTEMPT_S:
        raise SystemExit(f"refused: round {k} has {left_s:.0f} s of the audit's six hours left")
    return {"planned": n_requests, "max_attempts": min(math.ceil(1.1 * n_requests), left_att),
            "job_clock_s": left_s, **PER_ROUND}


def configure(k: int) -> dict:
    """Rebind the reviewed executor's module configuration to audit round k (this process only)."""
    sset = json.loads(S.set_path(k).read_text())
    lim = limits(k, len(sset["requests"]))
    E.SET, E.DELIVERY, E.IMAGES = S.set_path(k), delivery_path(k), S.ITEMS
    E.JOB, E.RAW, E.GO, E.ATTEMPTS, E.LIMITS = job_dir(k), raw_path(k), GO, ATTEMPTS, lim
    return lim


def check_delivery(sset: dict, deliv: dict, pin: str) -> None:
    """A round's delivery: the reader's instruction pin, one entry per request with the item file's image digest (a
    re-encoding is recorded, never accepted silently) and a rendered prompt."""
    if deliv.get("instructions_sha256") != pin:
        raise SystemExit("refused: the round's delivery instructions differ from the reader's frozen pin")
    if sorted(deliv["requests"]) != sorted(r["request"] for r in sset["requests"]):
        raise SystemExit("refused: the delivery does not cover exactly the round's requests")
    for r in sset["requests"]:
        d = deliv["requests"][r["request"]]
        if d["file_sha256"] != r["sha256"] or (d["image_sha256"] != r["sha256"] and not d["reencoded"]) \
                or not d["prompt_rendered"] or d["prompt_sha256"] != sha(r["prompt"].encode()):
            raise SystemExit(f"refused: delivery entry {r['request']} does not match its request")


class AuditJob(E.Job):
    def __init__(self, k: int, fixture: dict | None = None):
        self.round = k
        super().__init__(fixture)

    def _admit(self) -> None:
        if self.fx:
            return super()._admit()
        with E.Deadline(E.ADMIT_TIMEOUT_S, "audit package and go admission"):
            self.sset = json.loads(E.SET.read_text())
            self.deliv = json.loads(E.DELIVERY.read_text())
            self.pkg = package()
            stage_a_guard.NEGATIVE_REVIEWS = stage_a_guard.NEGATIVE_REVIEWS | NEGATIVE
            stage_a_guard.require_go(GO, self.pkg, row=ROW, stage=STAGE, verify_at_commit=package_at_commit)
            S.check(self.round)
            check_delivery(self.sset, self.deliv, self.pkg["instructions_sha256"])
        if self.pkg["cli_version"] != self.sset["reader"]["cli_version"]:
            raise SystemExit("refused: the installed codex CLI is not the pinned version")
        self.digest = self.pkg["package_digest"]
        self.reqs = {r["request"]: r for r in self.sset["requests"]}
        self.order = self.sset["delivery_order"]

    def attempt(self, r: dict, timeout: float) -> dict:
        self.sset["prompt"] = r["prompt"]              # the request's own frozen prompt (difference 3)
        return super().attempt(r, timeout)


def delivery(k: int) -> dict:
    """Render every request of round k locally (no request): image digest, user text hash, prompt rendered."""
    configure(k)
    sset = json.loads(S.set_path(k).read_text())
    codex = [str(R.CODEX)]
    out, instr = {}, set()
    for r in sset["requests"]:
        data = (S.ITEMS / r["file"]).read_bytes()
        if sha(data) != r["sha256"]:
            raise SystemExit(f"refused: item {r['file']} differs from the set")
        with tempfile.TemporaryDirectory(dir=E.ensure_root()) as td:
            adir = Path(td) / "a"
            img = R.prepare(adir, data, r["file"])
            rc = R.prompt_input(codex, sset["reader"], adir, img, r["prompt"])
        if len(rc["images"]) != 1:
            raise SystemExit(f"refused: {r['request']}: {len(rc['images'])} images rendered")
        im = rc["images"][0]
        instr.add(rc["instructions_sha256"])
        out[r["request"]] = {"image_sha256": im["sha256"], "bytes": im["bytes"], "detail": im["detail"],
                             "mime": im["mime"], "file_sha256": r["sha256"], "reencoded": im["sha256"] != r["sha256"],
                             "user_text_sha256": rc["user_text_sha256"], "prompt_rendered": rc["prompt_rendered"],
                             "prompt_sha256": sha(r["prompt"].encode())}
    if len(instr) != 1:
        raise SystemExit(f"refused: the model-visible instructions differ between requests: {instr}")
    ih = instr.pop()
    pin = json.loads((HERE / "ai_reader_delivery.json").read_text())["instructions_sha256"]
    d = {"note": "Local renderings of each audit request's model-visible input by `codex debug prompt-input` with the "
                 "reader's flags, allowlist sandbox, environment and the request's prompt after '--' (no request was "
                 "sent).", "round": k, "cli_version": sset["reader"]["cli_version"], "instructions_sha256": ih,
         "instructions_equal_reader_pin": ih == pin,
         "reencoded": sum(v["reencoded"] for v in out.values()), "requests": out}
    check_delivery(sset, d, pin)
    delivery_path(k).write_text(json.dumps(d, indent=1, sort_keys=True) + "\n")
    return {k2: v for k2, v in d.items() if k2 != "requests"}


def plan(k: int) -> dict:
    lim = configure(k)
    S.check(k)
    sset = json.loads(S.set_path(k).read_text())
    check_delivery(sset, json.loads(delivery_path(k).read_text()),
                   json.loads((HERE / "ai_reader_delivery.json").read_text())["instructions_sha256"])
    codex = [str(R.CODEX)]
    with tempfile.TemporaryDirectory(dir=E.ensure_root()) as td:
        adir = Path(td) / "a"
        img = R.prepare(adir, E._synthetic_png(), "x.png")
        pre = E.preflight(codex, sset, adir, img)
    return {"dry_run": True, "round": k, "requests": len(sset["requests"]), "limits": lim, "preflight": pre,
            "package": package()}


def run(k: int, fixture: dict | None = None) -> dict:
    configure(k)
    return AuditJob(k, fixture).run()


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "package":
        print(json.dumps(package(), indent=1))
    else:
        k = int(sys.argv[2])
        print(json.dumps({"delivery": delivery, "plan": plan, "run": run}[cmd](k), indent=1, default=str))
