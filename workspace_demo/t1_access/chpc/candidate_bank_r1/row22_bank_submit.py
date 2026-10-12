"""Ledger row 22 (the omega = 1 reference bank): plan and submit packed jobs of single-core bank workers (login node, t1py).

ONE operator, one submitter at a time (a lock is held from the evidence to the last bind). The plan comes from evidence:
  DONE      = the record file exists AND is this bank's valid record of that dataset (row22_bank.read_record); any other
              file at a record path HOLDS the planner;
  IN FLIGHT = in the plan of a campaign-ledger 'bank' entry that is not settled and whose runner has not ended; such an
              entry WITHOUT its plan file HOLDS the planner;
  MISSING   = every other declared bank rep.
Missing reps go `per_slot` to a worker (one worker = one core), `cores` workers to a job.

THE SUBMISSION GATE:
  - a STOP file in the root refuses every submission;
  - the bank's seeds must pass row22_bank.seed_problems (no duplicate, nothing excluded, the declared list);
  - the FIRST bank job is the pilot: `--pilot`, exactly one job, only while the ledger holds no bank entry;
  - every later submission needs ALL of (revision 2, Codex RSC 97fc278: the first form checked only a path and a hash):
    (1) <root>/gate/qualified_bank_job1.json, written by row22_bank_status.py --qualify 1 on fresh production evidence with
        zero alarms, PARSED and its `bound` equal to what THIS process recomputes - the manifest's SHA-256, root, campaign,
        code pins, wrapper hash, the bank binding file's SHA-256, and job 1's PBS id, token and plan SHA-256 from the ledger
        and the root;
    (2) <root>/gate/bank_review.json, written by `--adopt-review <record> --max-job-number N` ONLY when (1) holds: the
        reviewer's record of the pilot's ACTUAL evidence, tracked by git in this clone and unmodified against HEAD, named by
        path and SHA-256, bound to the qualification's SHA-256 (which must still be the file in the gate) and to a highest
        job number; never overwritten. The first-pilot record (RSC 97fc278) must never be adopted here;
    (3) the newest <root>/gate/bank_watch_*.json: parsed, this schema, production, fresh, zero alarms, at most 2,700 s old,
        bound to the same values and to EVERY bank job the ledger holds now;
  - before any real submission the manifest's code pins are verified in the clone the jobs run from.
  REVISION B1 CANDIDATE (R052 12 Oct, bank job 11 wall-killed; NOT adopted): a receipt summary that carries `disposition`
  (kind bank-closed-no-record-1) is never taken on its word. disposition_problem() recomputes it HERE with
  row22_bank_dispo.closed_no_record (the status view's one implementation) from the CURRENT ledger, the live root and the PBS
  output on disk (<toolchain>/jobs/row22_bank_<n>.out), observed from the settlement note, and requires the receipt's
  disposition to be EXACTLY the recomputed one (settlement certificate, exit, token, PBS id, plan SHA-256, output SHA-256,
  uncompleted reps), the output bound in `bound.job_outputs`, and the summary to show zero ended/new/resumed/left with the
  plan's reps as uncompleted (origin plan). A replaced certificate, a changed output, a status or timing naming the job,
  an ADMISSION FAILED or a record at its reps that is not a later bound job's planned completion refuses until recollected.
  A terminal job in the receipt with an exit other than 0/75 and no disposition refuses. The disposed reps are MISSING to
  the planner (a settled entry is never in flight) and are planned first by rep order into the next job number, which the
  adopted review must cover.
  REPAIR R1 (Codex RSC 4295ed6): B1-2 a later completion at a disposed rep is recomputed against the verify document the
  receipt bound (gate/verify_*.json whose SHA-256 is bound.verify_sha256; its record SHA-256 must be the CURRENT record bytes')
  and the producer's timing contract on the CURRENT timing bytes with the task's seed; B1-3 the receipt's summaries, its
  bound jobs and the current ledger's bank jobs must be the same set, as typed mappings, before any job is validated;
  B1-4 a receipt (and the qualification's embedded receipt) is clean only with an explicit empty `alarms` list, `fresh` and
  `production` exactly true, and a finite non-boolean `time` (within the 2,700 s ceiling for the gate receipt).

    t1py chpc/row22_bank_submit.py --manifest chpc/row22_bank_manifest.json --pilot [--dry-run]
    t1py chpc/row22_bank_submit.py --manifest chpc/row22_bank_manifest.json --adopt-review reviews/<record>.md --max-job-number 17
    t1py chpc/row22_bank_submit.py --manifest chpc/row22_bank_manifest.json --jobs 4 [--dry-run]
"""
import os, sys, json, time, glob, math, fcntl, hashlib, argparse, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from row19_ledger import CampaignLedger, LIVE
import row22_bank_dispo as DP

REVIEW_SCHEMA = "row22-bank-review-2"
QUAL_SCHEMA = "row22-bank-qualification-1"
WATCH_SCHEMA = "row22-bank-watch-1"
CEILING_S = 2700.0
BOUND_KEYS = ("manifest_sha256", "root", "campaign", "code", "wrapper_sha256", "bank_binding_sha256")


def hms(seconds):
    s = int(round(seconds)); return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def evidence(man, validate=True):
    """(done, in_flight, used job numbers, problems). `problems` non-empty HOLDS the planner."""
    root = man["storage"]["root"]
    reps = [int(r) for r in man["datasets"]["reps"]]
    problems, done = [], set()
    B = None
    for p in sorted(glob.glob(os.path.join(root, "records", "b*.json"))):
        name = os.path.basename(p)
        try:
            r = int(name[1:4])
            if name != f"b{r:03d}.json" or r not in reps:
                raise ValueError("name")
        except ValueError:
            problems.append(f"{p}: not a bank record file name of a declared rep"); continue
        if validate:
            if B is None:
                import row22_bank as B
            try:
                B.read_record(p, B.SH.task(man, r), r)
            except ValueError as e:
                problems.append(str(e)); continue
        done.add(r)
    flight, used = set(), set()
    led = os.path.join(man["storage"]["campaign"], "budget.json")
    entries = list(json.load(open(led))["entries"].values()) if os.path.exists(led) else []
    for e in entries:
        if e.get("kind") != "bank":
            continue
        used.add(int(e["rep"]))
        if e.get("state") in LIVE and e.get("runner_exit") is None:
            pp = os.path.join(root, "plans", f"job_{int(e['rep'])}.json")
            if not os.path.exists(pp):
                problems.append(f"bank job {e['rep']} ({e.get('job_id')}) is live in the ledger but its plan {pp} is missing"); continue
            for s in json.load(open(pp)).get("slots", []):
                flight.update(int(r) for r in s["reps"])
    return done, flight, used, problems


def plan_jobs(man, n_jobs, per_slot, done, flight, used):
    cores = int(man["pbs"]["cores"])
    missing = [int(r) for r in man["datasets"]["reps"] if int(r) not in done and int(r) not in flight]
    groups = [missing[k:k + per_slot] for k in range(0, len(missing), per_slot)]
    jobs, n = [], (max(used) + 1 if used else 1)
    for k in range(0, len(groups), cores):
        if len(jobs) >= n_jobs:
            break
        jobs.append({"job": n, "slots": [{"slot": s, "reps": g} for s, g in enumerate(groups[k:k + cores])]})
        n += 1
    left = sum(len(g) for g in groups[len(jobs) * cores:])
    return jobs, left


def expected_bound(man, manifest_path):
    """What a qualification or receipt must be bound to, recomputed here from the manifest file, the root and the ledger."""
    root, campaign = man["storage"]["root"], man["storage"]["campaign"]
    led = json.load(open(os.path.join(campaign, "budget.json")))
    jobs = {}
    for e in led["entries"].values():
        if e.get("kind") != "bank":
            continue
        n = str(int(e["rep"])); pp = os.path.join(root, "plans", f"job_{n}.json")
        jobs[n] = dict(job_id=e.get("job_id"), token=e.get("token"), plan_sha256=sha_file(pp) if os.path.exists(pp) else None)
    bp = os.path.join(root, "bank_binding.json")
    return dict(manifest_sha256=sha_file(manifest_path), root=root, campaign=campaign, code=dict(man["code"]["files"]),
                wrapper_sha256=man.get("environment", {}).get("wrapper_sha256"),
                bank_binding_sha256=sha_file(bp) if os.path.exists(bp) else None, jobs=jobs)


def bound_problem(got, want, jobs):
    if not isinstance(got, dict):
        return "no `bound` object"
    for k in BOUND_KEYS:
        if got.get(k) != want[k]:
            return f"its `{k}` is not this bank's"
    gj = got.get("jobs")
    if not isinstance(gj, dict):
        return "no job bindings"
    if jobs == "all":
        if gj != want["jobs"]:
            return f"its jobs {sorted(gj)} (PBS id, token, plan hash) are not the ledger's {sorted(want['jobs'])} as they are now"
    else:
        for n in jobs:
            w = want["jobs"].get(n)
            if not w or None in w.values() or gj.get(n) != w:
                return f"its binding of job {n} is not the ledger's and the root's"
    return ""


def qualification_problem(man, manifest_path):
    q = os.path.join(man["storage"]["root"], "gate", "qualified_bank_job1.json")
    if not os.path.exists(q):
        return "no pilot qualification (gate/qualified_bank_job1.json; row22_bank_status.py --qualify 1)", None
    try:
        doc = json.load(open(q))
    except Exception as e:
        return f"the qualification is unreadable ({e})", None
    if not isinstance(doc, dict) or doc.get("schema") != QUAL_SCHEMA or doc.get("qualified_job") != 1 or isinstance(doc.get("qualified_job"), bool) \
            or doc.get("production") is not True or not finite_time(doc.get("time")):
        return "the qualification is not a production qualification of bank job 1 with a finite time", None
    why = clean_receipt_fields(doc.get("receipt"))
    if why:
        return f"the qualification's embedded receipt: {why}", None
    why = bound_problem(doc.get("bound"), expected_bound(man, manifest_path), ["1"])
    return (f"the qualification: {why}" if why else ""), sha_file(q)


def tracked_unmodified(rel):
    """True when `rel` (relative to workspace_demo/t1_access) is tracked by git in this clone and equal to HEAD."""
    try:
        a = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=T1, capture_output=True, text=True)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=T1, capture_output=True, text=True)
        return a.returncode == 0 and b.returncode == 0
    except Exception:
        return False


def finite_time(t):
    return isinstance(t, (int, float)) and not isinstance(t, bool) and math.isfinite(t) and t >= 0


def clean_receipt_fields(r, now=None):
    """B1-4: '' only for a parsed watch receipt with an explicit empty alarm list, fresh and production exactly true, and a finite
    non-boolean time (with `now`: no later than now + 60 s and no older than the 2,700 s ceiling)."""
    if not isinstance(r, dict) or r.get("schema") != WATCH_SCHEMA:
        return "not a watch receipt"
    if r.get("production") is not True or r.get("fresh") is not True:
        return "not a fresh production receipt"
    if not isinstance(r.get("alarms"), list):
        return "its alarms are not an explicit list"
    if r["alarms"] != []:
        return f"{len(r['alarms'])} alarm(s)"
    t = r.get("time")
    if not finite_time(t):
        return "its time is not finite"
    if now is not None and (t > now + 60 or now - t > CEILING_S):
        return f"not within {CEILING_S:.0f} s"
    return ""


def receipt_problem(man, manifest_path, now=None):
    now = time.time() if now is None else now
    gate = os.path.join(man["storage"]["root"], "gate")
    ps = sorted(glob.glob(os.path.join(gate, "bank_watch_*.json")))
    if not ps:
        return "no watch receipt in the gate"
    try:
        r = json.load(open(ps[-1]))
    except Exception as e:
        return f"the newest receipt is unreadable ({e})"
    why = clean_receipt_fields(r, now)
    if why:
        return f"the newest receipt: {why}"
    why = bound_problem(r.get("bound"), expected_bound(man, manifest_path), "all")
    if why:
        return f"the newest receipt: {why}"
    return dispositions_problem(man, r)


def disposition_problem(man, n, sj, bound):
    """REVISION B1: '' only when bank job n is closed-no-record on the CURRENT ledger, root and PBS output, and the receipt's
    disposition is exactly that recomputation."""
    n = str(int(n)); d = sj.get("disposition")
    if not isinstance(d, dict) or d.get("kind") != DP.DISPO_KIND:
        return f"job {n}: no closed-no-record disposition"
    root = man["storage"]["root"]
    try:
        led = json.load(open(os.path.join(man["storage"]["campaign"], "budget.json")))
    except Exception as ex:
        return f"job {n}: the ledger is unreadable ({ex})"
    entries = list(led["entries"].values())
    hits = [e for e in entries if e.get("kind") == "bank" and e.get("rep") == int(n)]
    if len(hits) != 1:
        return f"job {n}: {len(hits)} current ledger entries"
    e = hits[0]
    pp = os.path.join(root, "plans", f"job_{n}.json")
    try:
        plan = json.load(open(pp)); psha = sha_file(pp)
    except Exception:
        return f"job {n}: its plan is absent or unreadable"
    name = f"row22_bank_{n}.out"
    try:
        ob = open(os.path.join(man["bank"]["toolchain"], "jobs", name), "rb").read()
    except OSError:
        ob = None
    obs = dict(state="F", exit=DP.note_exit(e.get("settle_note")), source="ledger-settlement")
    vreps, why = bound_verification(man, bound)
    if why:
        return f"job {n}: {why}"
    mine, why = DP.closed_no_record(root, n, e, plan, psha, obs, entries, name, ob, vreps, man["datasets"]["reps"],
                                    lambda r: task_seed(man, r))
    if not mine:
        return f"job {n}: not closed-no-record on the current evidence ({why})"
    keys = [k for k in mine if k != "observation"]
    diff = [k for k in keys if d.get(k) != mine[k] or isinstance(d.get(k), bool)]
    if diff:
        return f"job {n}: the receipt's disposition differs from the current evidence on {diff}; recollect"
    bj = (bound.get("jobs") or {}).get(n) or {}
    if bj.get("job_id") != e.get("job_id") or bj.get("token") != e.get("token") or bj.get("plan_sha256") != psha:
        return f"job {n}: the receipt's binding is not the ledger's PBS id, token and plan"
    bo = (bound.get("job_outputs") or {}).get(n) or {}
    if bo != dict(file=name, sha256=mine["output_sha256"]):
        return f"job {n}: the receipt does not bind the disposed job's PBS output bytes"
    if sj.get("state") != "F" or sj.get("exit") != mine["scheduler_exit"] or any(sj.get(k) != 0 for k in ("ended", "new", "resumed", "left")) \
            or sj.get("exits") != {} or sj.get("partition") != dict(new=[], resumed=[], left=[], uncompleted=mine["uncompleted"], uncompleted_origin="plan"):
        return f"job {n}: the summary is not a closed job with no worker status and its plan's reps uncompleted"
    return ""


def task_seed(man, r):
    """The pinned task seed of bank rep r (row22_bank.SH.task, as evidence() and the producer verifier use it)."""
    import row22_bank as B
    return int(B.SH.task(man, int(r))["seed"])


def bound_verification(man, bound):
    """B1-2: ({rep: verdict} of the verify document the receipt bound, found in the gate by SHA-256) or (None, reason)."""
    want = bound.get("verify_sha256")
    if not isinstance(want, str) or len(want) != 64:
        return None, "the receipt binds no producer-runtime verification"
    for p in sorted(glob.glob(os.path.join(man["storage"]["root"], "gate", "verify_*.json")), reverse=True):
        try:
            b = open(p, "rb").read()
        except OSError:
            continue
        if hashlib.sha256(b).hexdigest() != want:
            continue
        try:
            doc = json.loads(b)
        except ValueError:
            return None, "the bound verification is not JSON"
        if not isinstance(doc, dict) or doc.get("schema") != "row22-bank-verify-1" or not isinstance(doc.get("reps"), dict):
            return None, "the bound verification is not a bank verify document"
        return doc["reps"], ""
    return None, "the verification the receipt bound is not in the gate"


def dispositions_problem(man, r):
    """REVISION B1: every disposition in the receipt revalidated; a terminal bad exit without one refuses; no stray output binding.
    R1 (B1-3): summaries, bound jobs and the current ledger's bank jobs are one typed, equal set first."""
    jobs, bound = r.get("jobs"), r.get("bound")
    if not isinstance(jobs, dict) or not isinstance(bound, dict) or not isinstance(bound.get("jobs"), dict) \
            or not isinstance(bound.get("job_outputs", {}), dict):
        return "the newest receipt: its job summaries or bindings are not mappings"
    try:
        led = json.load(open(os.path.join(man["storage"]["campaign"], "budget.json")))
        current = {str(int(e["rep"])) for e in led["entries"].values() if e.get("kind") == "bank"}
    except Exception as ex:
        return f"the newest receipt: the current ledger is unreadable ({ex})"
    if not (set(jobs) == set(bound["jobs"]) == current):
        return (f"the newest receipt: summaries {sorted(jobs)}, bound jobs {sorted(bound['jobs'])} and the ledger's "
                f"bank jobs {sorted(current)} are not one set")
    for n, sj in sorted(jobs.items(), key=lambda x: int(x[0])):
        if not isinstance(sj, dict):
            return f"the newest receipt: job {n} has no summary"
        if sj.get("disposition") is not None:
            why = disposition_problem(man, n, sj, bound)
            if why:
                return f"the newest receipt: {why}"
        elif sj.get("state") in ("F", "E", "X", "gone") and sj.get("exit") not in (0, 75):
            return f"the newest receipt: job {n} ended with exit {sj.get('exit')} and carries no disposition"
    stray = sorted(set(bound.get("job_outputs") or {}) - {n for n, sj in jobs.items() if isinstance(sj, dict) and sj.get("disposition")})
    if stray:
        return f"the newest receipt binds PBS outputs of jobs {stray} that carry no disposition"
    return ""


def review_problem(man, planned, manifest_path=None):
    """Why a non-pilot submission is not covered by an adopted review ('' when it is)."""
    p = os.path.join(man["storage"]["root"], "gate", "bank_review.json")
    if not os.path.exists(p):
        return "no adopted review of the pilot (gate/bank_review.json); run --adopt-review first"
    try:
        doc = json.load(open(p))
    except Exception as e:
        return f"gate/bank_review.json is unreadable ({e})"
    if doc.get("schema") != REVIEW_SCHEMA:
        return "gate/bank_review.json has another schema"
    full = os.path.join(T1, doc.get("record_path", ""))
    if not os.path.exists(full) or sha_file(full) != doc.get("record_sha256"):
        return "the adopted review record is not in this clone with the adopted SHA-256"
    if not isinstance(doc.get("max_job_number"), int) or any(int(j) > doc["max_job_number"] for j in planned):
        return f"the adopted review covers job numbers up to {doc.get('max_job_number')}, the plan reaches {max(planned) if planned else '-'}"
    if manifest_path is not None:
        why, qsha = qualification_problem(man, manifest_path)
        if why:
            return why
        if doc.get("qualification_sha256") != qsha:
            return "the adopted review names another qualification than the one in the gate"
        why = receipt_problem(man, manifest_path)
        if why:
            return why
    return ""


def adopt_review(man, record_rel, max_job_number, manifest_path=None):
    root = man["storage"]["root"]
    full = os.path.join(T1, record_rel)
    if not os.path.exists(full):
        return f"REFUSED: {record_rel} is not in this clone"
    if not tracked_unmodified(record_rel):
        return f"REFUSED: {record_rel} is not tracked by git in this clone, or differs from HEAD"
    qsha = None
    if manifest_path is not None:
        why, qsha = qualification_problem(man, manifest_path)
        if why:
            return f"REFUSED: {why}"
    if not isinstance(max_job_number, int) or max_job_number < 2:
        return "REFUSED: --max-job-number must be an integer of at least 2"
    os.makedirs(os.path.join(root, "gate"), exist_ok=True)
    p = os.path.join(root, "gate", "bank_review.json")
    if os.path.exists(p):
        return f"REFUSED: {p} exists; an adopted review is never overwritten (retire it by hand, recorded in ledger row 22)"
    doc = dict(schema=REVIEW_SCHEMA, by="R052", time=time.time(), record_path=record_rel, record_sha256=sha_file(full),
               qualification_sha256=qsha, max_job_number=int(max_job_number))
    tmp = p + f".tmp.{os.getpid()}"
    with open(tmp, "w") as fh:
        json.dump(doc, fh, indent=1, allow_nan=False); fh.flush(); os.fsync(fh.fileno())
    os.link(tmp, p); os.remove(tmp)
    return f"adopted: {record_rel} ({doc['record_sha256'][:16]}), job numbers up to {max_job_number}"


def gate_problem(man, used, pilot, n_jobs, planned, manifest_path=None):
    root = man["storage"]["root"]
    if os.path.exists(os.path.join(root, "STOP")):
        return "a STOP file is present in the bank root"
    import row22_bank as B
    why = B.seed_problems(man)
    if why:
        return why
    if pilot:
        if used:
            return f"--pilot is only for the first bank job; the ledger already holds bank job(s) {sorted(used)}"
        if n_jobs != 1:
            return "the pilot is exactly one job"
        return ""
    if not used:
        return "the first bank job is the pilot: say --pilot"
    return review_problem(man, planned, manifest_path)


def pin_problems(man, clone):
    bad = []
    for f, want in man["code"]["files"].items():
        p = os.path.join(clone, "workspace_demo", "t1_access", f)
        if not os.path.exists(p) or sha_file(p) != want:
            bad.append(f)
    return bad


def pbs_script(man, plan, token, walltime_s, queue, toolchain, clone, manifest_rel):
    root, cores = man["storage"]["root"], int(man["pbs"]["cores"])
    n = plan["job"]; reserve = int(float(man["pbs"]["deadline_reserve_s"]))
    end = (f"$T/t1py chpc/row22_bank.py job-end --manifest {manifest_rel} --plan $PLAN --job-id $PBS_JOBID --reservation-token {token} --started-epoch $START")
    L = ["#!/bin/bash", f"#PBS -N t1_bank_{n}", f"#PBS -P {man['pbs']['project']}", f"#PBS -q {queue}",
         f"#PBS -l select=1:ncpus={cores}:mpiprocs={cores}:mem={int(man['pbs']['mem_gb'])}gb:nodetype={man['pbs']['nodetype']}",
         f"#PBS -l walltime={hms(walltime_s)}", f"#PBS -o {toolchain}/jobs/row22_bank_{n}.out", f"#PBS -e {toolchain}/jobs/row22_bank_{n}.err",
         "#PBS -m ae", "#PBS -M pgwvanrooyen@sun.ac.za",
         f"# Ledger row 22, the omega = 1 reference bank (chpc/row22_bank.py): job {n}, {len(plan['slots'])} single-core workers, one original fit per record.",
         "ulimit -s unlimited", f"T={toolchain}", f"cd {clone}/workspace_demo/t1_access",
         "export NPROC=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONUNBUFFERED=1",
         "START=$(date +%s)", f"DEADLINE=$((START + {int(walltime_s)} - {reserve}))",
         'echo "host $(hostname)  $(grep -m1 \'model name\' /proc/cpuinfo)  mem $(grep MemTotal /proc/meminfo)"',
         f'echo "code $(git rev-parse --short HEAD)  start $(date -u +%FT%TZ)  job $PBS_JOBID  bank job {n}"',
         f"PLAN={root}/plans/job_{n}.json",
         f"$T/t1py chpc/row22_bank.py job-start --manifest {manifest_rel} --plan $PLAN --job-id $PBS_JOBID --walltime-s {int(walltime_s)} --reservation-token {token}",
         "rc=$?",
         'if [ $rc -ne 0 ]; then', f"  {end}", '  echo "exit $rc job $PBS_JOBID end $(date -u +%FT%TZ) (ADMISSION FAILED)"', "  exit $rc", "fi",
         f"mkdir -p {root}/logs"]
    for s in plan["slots"]:
        reps = ",".join(str(r) for r in s["reps"])
        L.append(f"$T/t1py chpc/row22_bank.py worker --manifest {manifest_rel} --reps {reps} --slot {s['slot']} "
                 f"--job-id $PBS_JOBID --deadline-epoch $DEADLINE > {root}/logs/job$PBS_JOBID.slot{s['slot']}.log 2>&1 &")
    L += ["wait", 'echo "node memory at the end: $(grep -E \'MemAvailable|MemFree\' /proc/meminfo | tr \'\\n\' \' \')"', end,
          "rc=$?", 'echo "exit $rc job $PBS_JOBID end $(date -u +%FT%TZ)"', "exit $rc"]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--jobs", type=int, default=None)
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--per-slot", type=int, default=None)
    ap.add_argument("--queue", default=None); ap.add_argument("--walltime-h", type=float, default=None)
    ap.add_argument("--adopt-review", default=None); ap.add_argument("--max-job-number", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); bk = man["bank"]
    if a.adopt_review is not None:
        out = adopt_review(man, a.adopt_review, a.max_job_number, a.manifest)
        print(out); return 0 if out.startswith("adopted") else 2
    n_jobs = 1 if a.pilot else a.jobs
    if not n_jobs or n_jobs < 1:
        print("say --pilot or --jobs N"); return 2
    per_slot = int(a.per_slot or bk["per_slot"]); queue = a.queue or man["pbs"]["queue"]
    walltime_s = float(a.walltime_h or man["pbs"]["walltime_h"]) * 3600.0
    toolchain, clone, root = bk["toolchain"], bk["clone"], man["storage"]["root"]
    os.makedirs(os.path.join(root, "plans"), exist_ok=True); os.makedirs(os.path.join(root, "gate"), exist_ok=True)
    manifest_rel = os.path.relpath(os.path.abspath(a.manifest), os.path.join(clone, "workspace_demo", "t1_access"))
    with open(os.path.join(root, "plans", ".submit.lock"), "a+") as lk:
        try:
            fcntl.flock(lk.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("HELD: another submitter holds the plan lock"); return 2
        done, flight, used, problems = evidence(man)
        print(f"bank: valid records {len(done)}/{len(man['datasets']['reps'])}, in flight {len(flight)}")
        if problems:
            print(f"HELD: {len(problems)} problem(s) in the evidence; nothing is planned:")
            for p in problems[:10]:
                print("   -", p)
            return 2
        jobs, left = plan_jobs(man, n_jobs, per_slot, done, flight, used)
        why = gate_problem(man, used, a.pilot, n_jobs, [j["job"] for j in jobs], a.manifest)
        pins = pin_problems(man, clone)
        if pins and not why:
            why = f"the manifest's pins do not hold in the clone the jobs run from: {pins}"
        print(f"planned {len(jobs)} job(s), {sum(len(s['reps']) for j in jobs for s in j['slots'])} datasets; {left} missing not in this call")
        if a.dry_run:
            print(f"DRY RUN; the gate {'would REFUSE: ' + why if why else 'would admit this submission'}")
            for j in jobs:
                print(f"  job {j['job']}: {len(j['slots'])} slots, reps {j['slots'][0]['reps']} ... {j['slots'][-1]['reps']}")
            return 0
        if why:
            print(f"REFUSED by the submission gate: {why}"); return 2
        L = CampaignLedger(man["storage"]["campaign"], man["budget"]["core_hours_cap"])
        os.makedirs(os.path.join(toolchain, "jobs"), exist_ok=True)
        for j in jobs:
            cores = int(man["pbs"]["cores"])
            token, t = L.reserve("bank", int(j["job"]), cores, walltime_s, root,
                                 f"submitted by row22_bank_submit.py {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
            pp = os.path.join(root, "plans", f"job_{j['job']}.json")
            with open(pp, "w") as fh:
                json.dump(dict(j, queue=queue, walltime_s=walltime_s, token=token, created=time.time()), fh, indent=1); fh.flush(); os.fsync(fh.fileno())
            sp = os.path.join(toolchain, "jobs", f"row22_bank_{j['job']}.pbs")
            open(sp, "w").write(pbs_script(man, j, token, walltime_s, queue, toolchain, clone, manifest_rel))
            r = subprocess.run(["qsub", sp], capture_output=True, text=True)
            if r.returncode != 0:
                print(f"job {j['job']}: qsub failed ({r.stderr.strip()[:200]}); reservation {token} stays reserved and unbound - record it in row 22"); return 1
            job_id = r.stdout.strip()
            L.bind(token, job_id)
            print(f"bank job {j['job']}: reserved {token} ({cores} x {walltime_s/3600:.0f} h; spent {t['spent']:.0f}, live {t['live']:.0f} of {t['cap']:.0f}), "
                  f"submitted {job_id} on {queue}, {len(j['slots'])} workers, {sum(len(s['reps']) for s in j['slots'])} datasets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
