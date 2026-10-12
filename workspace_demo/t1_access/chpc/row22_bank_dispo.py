"""Ledger row 22, bank REVISION B1 CANDIDATE (R052 12 Oct; NOT adopted): the CLOSED-NO-RECORD DISPOSITION of a bank job,
ported from the refit design Codex found favourable (RSC a86debe, verdict 1; implemented for the screen as status/admission
REVISION 8, row19_screen_status.closed_no_record and row19_screen_admit.disposition_problem).

Trigger: bank job 11 (7531003.sched01, cnode0359, reps 240-263) killed by PBS at its 36 h wall on 12 Oct 07:23Z: F, Exit_status
271, 0/24 worker statuses, the PBS output stops after "admitted", settled 864.76 core-h. Every receipt since alarms on it
(bad exit, no runner end, 24 slots without status), which holds bank admission indefinitely, including the retry of its reps.

ONE implementation, imported by the Mac status view (row22_bank_status.py, on its fresh snapshot of the root) and by the
login-node admission (row22_bank_submit.py, on the live root and the PBS output on disk). It needs no JAX and imports nothing
pinned. closed_no_record() returns (disposition, '') only when ALL hold; otherwise (None, reason) and every alarm stays:
  - the observation is state F with an observed integer exit, and the settlement note carries that same Exit_status;
  - the ledger entry is SETTLED with settlement evidence (finite non-negative charge and time, a technical note) and has no
    runner-end field (runner_exit, runner_ended, runner_wall_s): job-end never ran;
  - the plan is this entry's token and job number;
  - no status file is scoped to its PBS id (by name, any slot, planned or not; by a parsed `job`) and no status file is
    unreadable without a job named in its name;
  - no timing file anywhere names its PBS id, is unreadable, or is not a published .json (a temporary file); when the
    producer-runtime verify document is given, no rep's timing names it either;
  - no temporary or non-canonical record/timing file exists for a planned rep; a planned rep that HAS a record or a timing is
    accepted only as a LATER bound job's completion: valid timing naming a ledger bank job with a higher number and a PBS id,
    whose plan put that rep in the timing's slot (with verify: the record valid and its current bytes the verified ones);
  - its PBS output was retrieved, names its PBS id ("job <id>") and carries no "ADMISSION FAILED".
The disposition keeps the loss: actual exit, charge, settlement certificate, plan SHA-256, the output's SHA-256, zero worker
statuses, zero attributed reps, and the planned reps as `uncompleted` with origin "plan". It is a charged failed attempt with
no completion and no restart or recovery credit; its reps return to the planner as MISSING (the planner already ignores a
settled entry). A dispositioned job never qualifies.

REPAIR R1 (Codex RSC 4295ed6, B1-1 and B1-2):
  - B1-1 STRICT INVENTORY: every entry of records/ and timing/ must be exactly b<rrr>.json (three digits) of a DECLARED rep;
    anything else (b0240.json, a directory, a temporary file, an undeclared rep) holds - it is never mapped onto another rep.
  - B1-2 LATER COMPLETION ON CURRENT BYTES: the current timing bytes must meet the producer's timing contract
    (row22_bank_verify.timing_check: this rep, this seed when the caller knows it, finite non-negative wall_s, fit_seconds,
    maxrss and t, a job string and an integer slot), and a verify document is REQUIRED: its record must be valid with the
    CURRENT record bytes' SHA-256 and its timing valid with the same job and slot. The admission passes the verify document
    the receipt bound (published to the gate beside the receipt) and the task seed.

REPAIR R2 (Codex RSC 82b7253): every name test is a FULL match of an ASCII pattern (Python's `$` admits a final newline, and
`\\d` admits non-ASCII digits that int() accepts), and an evidence name must also equal its reconstruction b<rep:03d>.json."""
import os, re, json, glob, math, hashlib

DISPO_KIND = "bank-closed-no-record-1"
RUNNER_END = ("runner_exit", "runner_ended", "runner_wall_s")
STATUS_NAME = re.compile(r"job([!-~]+)\.slot([0-9]+)\.json", re.ASCII)
TIMING_NAME = re.compile(r"b([0-9]{3})\.json", re.ASCII)
RECORD_NAME = TIMING_NAME


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha_bytes(open(p, "rb").read())


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def note_exit(note):
    m = re.search(r"Exit_status (-?\d+)\b", note) if isinstance(note, str) else None
    return int(m.group(1)) if m else None


def settlement_problem(e):
    """'' when the ledger entry is SETTLED with settlement evidence and no runner end; otherwise the reason."""
    if e.get("state") != "settled" or not (_num(e.get("settled_core_h")) and e["settled_core_h"] >= 0) \
            or not (_num(e.get("settled_at")) and e["settled_at"] >= 0) \
            or not (isinstance(e.get("settle_note"), str) and len(e["settle_note"].strip()) >= 8):
        return "the ledger entry is not SETTLED with settlement evidence (charge, note, non-negative time)"
    if any(e.get(f) is not None for f in RUNNER_END):
        return "the ledger records a runner end"
    return ""


def status_scoped(root, jid):
    """Status files scoped to PBS job jid: by name (any slot, planned or not), by parsed `job`, or unreadable with no job name."""
    hits = []
    for p in sorted(glob.glob(os.path.join(root, "status", "*"))):
        b = os.path.basename(p)
        if b.startswith(f"job{jid}."):
            hits.append(b); continue
        try:
            d = json.load(open(p))
        except Exception:
            if not STATUS_NAME.fullmatch(b):
                hits.append(f"{b} (unreadable, no job named)")
            continue
        if not isinstance(d, dict) or d.get("job") == jid:
            hits.append(b)
    return hits


def timing_scan(root, jid):
    """Timing files anywhere under the root that name jid, cannot be read, or are not a published b<rrr>.json."""
    hits = []
    for p in sorted(glob.glob(os.path.join(root, "timing", "**", "*"), recursive=True)):
        if os.path.isdir(p):
            continue
        rel = os.path.relpath(p, root)
        if canonical_name(os.path.basename(p)) is None or os.path.dirname(rel) != "timing":
            hits.append(f"{rel} (not a published timing)"); continue
        try:
            d = json.load(open(p))
        except Exception:
            hits.append(f"{rel} (unreadable)"); continue
        if not isinstance(d, dict) or d.get("job") == jid:
            hits.append(rel)
    return hits


def canonical_name(b):
    """R2: the rep of an exact evidence name b<rrr>.json (full ASCII match AND equal to its reconstruction), else None."""
    m = RECORD_NAME.fullmatch(b)
    if not m:
        return None
    r = int(m.group(1))
    return r if b == f"b{r:03d}.json" else None


def inventory_problem(root, declared):
    """B1-1: '' only when every entry under records/ and timing/ is exactly b<rrr>.json of a declared rep."""
    bad = []
    for sub in ("records", "timing"):
        for p in sorted(glob.glob(os.path.join(root, sub, "**", "*"), recursive=True) + glob.glob(os.path.join(root, sub, ".*"))):
            rel = os.path.relpath(p, root); r = canonical_name(os.path.basename(p))
            if os.path.isdir(p) or os.path.dirname(rel) != sub or r is None or r not in declared:
                bad.append(rel)
    return f"non-canonical bank evidence files {bad[:3]}" if bad else ""


def timing_contract(d, r, seed=None):
    """B1-2: row22_bank_verify.timing_check's contract applied to current bytes; '' or the reason."""
    if not isinstance(d, dict) or d.get("bank_rep") != int(r) or isinstance(d.get("bank_rep"), bool):
        return "the timing names another rep"
    if seed is not None and (d.get("seed") != seed or isinstance(d.get("seed"), bool)):
        return "the timing carries another seed"
    for k in ("wall_s", "fit_seconds", "maxrss", "t"):
        if not (_num(d.get(k)) and d[k] >= 0):
            return f"the timing's {k} is not finite and non-negative"
    if not isinstance(d.get("job"), str) or not _int(d.get("slot")):
        return "the timing names no job string and integer slot"
    return ""


def rep_files(root, r):
    """(exact files present, temporary/non-canonical files) for bank rep r's record and timing."""
    files, odd = [], []
    for sub, pre in (("records", "b"), ("timing", "b")):
        exact = f"{pre}{int(r):03d}.json"
        for p in glob.glob(os.path.join(root, sub, f"{pre}{int(r):03d}*")):
            (files if os.path.basename(p) == exact else odd).append(p)
    return files, odd


def plan_slot_of(root, m):
    """{rep: slot} of bank job m's plan in this root ({} when absent or unreadable)."""
    try:
        plan = json.load(open(os.path.join(root, "plans", f"job_{int(m)}.json")))
        return {int(r): int(s["slot"]) for s in plan.get("slots", []) for r in s["reps"]}
    except Exception:
        return {}


def later_completion(root, r, n, entries, verify_reps, seed=None):
    """'' when rep r holds a record whose valid timing names a bound bank job LATER than n that planned r in that slot, on the
    CURRENT bytes and the given verify document (B1-2)."""
    tp, rp = os.path.join(root, "timing", f"b{int(r):03d}.json"), os.path.join(root, "records", f"b{int(r):03d}.json")
    if not (os.path.isfile(tp) and os.path.isfile(rp)):
        return "a record or timing without its partner"
    try:
        t = json.load(open(tp))
    except Exception:
        return "its timing is unreadable"
    why = timing_contract(t, r, seed)
    if why:
        return why
    num_of = {x.get("job_id"): int(x["rep"]) for x in entries if x.get("kind") == "bank" and x.get("job_id")}
    m = num_of.get(t["job"])
    if m is None or m <= int(n) or plan_slot_of(root, m).get(int(r)) != t["slot"]:
        return f"its timing names {t['job']} slot {t['slot']}, not a later bound bank job that planned it there"
    if not isinstance(verify_reps, dict):
        return "no producer-runtime verification to accept a later completion against"
    v = verify_reps.get(str(int(r))) or {}
    rec, tim = v.get("record") or {}, v.get("timing") or {}
    if not (rec.get("ok") is True and tim.get("ok") is True and tim.get("job") == t["job"] and tim.get("slot") == t["slot"]
            and rec.get("file_sha256") == sha_file(rp)):
        return "the producer runtime does not verify its current record and timing"
    return ""


def closed_no_record(root, n, e, plan, plan_sha256, obs, entries, out_name, out_bytes, verify_reps, declared, seed_of=None):
    """(disposition, '') when bank job n is closed, settled and record-free on this evidence; (None, reason) otherwise.
    `obs` = the observation {state, exit, source}; `entries` = every current ledger entry; `out_bytes` = the job's PBS output
    as retrieved in this observation (None when retrieval failed); `verify_reps` = the producer-runtime verify document's reps
    (None when there is none: then no later completion can be accepted); `declared` = the declared bank reps; `seed_of(r)` =
    the task seed of rep r when the caller can compute it."""
    o = obs or {}
    if o.get("state") != "F" or not _int(o.get("exit")):
        return None, "the observation is not state F with an observed integer exit"
    why = settlement_problem(e)
    if why:
        return None, why
    if note_exit(e["settle_note"]) != o["exit"]:
        return None, f"the settlement note's Exit_status is not the observed exit {o['exit']}"
    j = e.get("job_id")
    if not j or not e.get("token") or not isinstance(plan, dict) or plan.get("token") != e["token"] or plan.get("job") != int(n):
        return None, "the plan is not this entry's token and job"
    sc = status_scoped(root, j)
    if sc:
        return None, f"status evidence scoped to {j}: {sc[:3]}"
    why = inventory_problem(root, set(int(x) for x in declared))
    if why:
        return None, why
    ts = timing_scan(root, j)
    if ts:
        return None, f"timing evidence naming {j} or of unknown attribution: {ts[:3]}"
    if verify_reps is not None:
        named = sorted(k for k, v in verify_reps.items() if ((v or {}).get("timing") or {}).get("job") == j)
        if named:
            return None, f"verified rep(s) {named[:3]} carry timing naming {j}"
    reps = sorted(int(r) for s in plan.get("slots", []) for r in s["reps"])
    if not reps:
        return None, "the plan assigns no reps"
    for r in reps:
        files, odd = rep_files(root, r)
        if odd:
            return None, f"bank rep {r}: temporary or non-canonical files {[os.path.basename(p) for p in odd][:3]}"
        if files or (isinstance(verify_reps, dict) and (verify_reps.get(str(r)) or {}).get("record") is not None):
            why = later_completion(root, r, n, entries, verify_reps, seed_of(r) if seed_of else None)
            if why:
                return None, f"bank rep {r} holds output that is not a later bound job's planned completion ({why})"
    if out_bytes is None:
        return None, "its PBS output was not retrieved in this observation (absence of an admission failure is not proven)"
    txt = out_bytes.decode("utf-8", errors="replace")
    if "ADMISSION FAILED" in txt:
        return None, "its PBS output reports ADMISSION FAILED"
    if f"job {j}" not in txt:
        return None, f"its PBS output does not name {j}"
    return dict(kind=DISPO_KIND, scheduler_state="F", scheduler_exit=o["exit"], observation=o.get("source"),
                settled_core_h=e["settled_core_h"], settle_note=e["settle_note"], settled_at=e["settled_at"], token=e["token"],
                job_id=j, plan_sha256=plan_sha256, output_file=out_name, output_sha256=sha_bytes(out_bytes),
                status_files=0, attributed_reps=0, uncompleted=reps, uncompleted_origin="plan",
                note="a charged failed attempt: no completion, no restart or recovery credit; its reps return to the planner"), ""
