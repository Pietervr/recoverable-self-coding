"""Row 19 sharded route: plan and submit packed jobs of single-core per-index workers (run on the login node under t1py).

ONE operator, one submitter at a time (a lock is held from the evidence to the last bind). The plan is derived from
evidence, never from memory or file names:
  DONE      = the record file exists AND is this task's valid record of that index (analyze._record_ok + the index);
              any other file at a record path HOLDS the planner (nothing is planned over unexamined evidence);
  IN FLIGHT = in the plan of a campaign-ledger 'shard' entry that is not settled and whose runner has not ended;
              such an entry WITHOUT its plan file HOLDS the planner (its indices are unknown, not missing);
  MISSING   = everything else.
Missing indices are grouped per dataset rep into runs of `per_slot` (one worker = one rep = one core), the groups are
interleaved across the reps, and each job takes `cores` groups.

THE SUBMISSION GATE (enforced here, not only a policy; revision 3 answers Codex RSC 13a2fea):
  - a STOP file in the root refuses every submission;
  - the FIRST shard job is the pilot: `--pilot`, exactly one job, only while the ledger holds no shard entry;
  - every later submission needs ALL of:
    (1) <root>/gate/qualified_job1.json (row19_shard_status.py --qualify 1), PARSED and VERIFIED: its schema, job 1,
        production evidence, finite time not in the future and not before the pilot's recorded end; its `bound` equal to
        what THIS process recomputes - the manifest file's SHA-256, the root, the campaign, the manifest's code pins and
        wrapper hash, the task identities in the root's bindings (each naming this manifest), and the pilot's PBS id,
        reservation token and plan-file SHA-256 from the campaign ledger and the root; its embedded watch receipt fresh,
        production, zero-alarm, bound to the same values, with the pilot ended in the scheduler (F, exit 0 or 75), every
        planned worker ended 0 or 75, memory observed under 90% of the request, and parity observed and equal with no
        rejected record and no missing timing for every dataset;
    (2) <root>/gate/pilot_review.json - the operator's record of the REVIEWER's verdict on the actual pilot evidence
        (`--adopt-review`): it names the review record committed in this clone by path and SHA-256 (verified here),
        the SHA-256 of the qualification it reviewed (must be the file in the gate now), and the highest shard job
        number that may be submitted under it. A qualification alone never admits a job. The verdict's wording is the
        reviewer's and is not machine-checked: the hash makes the claim auditable, it does not make it true;
    (3) <root>/gate/watch_receipt.json: parsed, this schema, fresh, production, zero alarms, a finite time not in the
        future and at most 2,700 s old (`--receipt-max-age-s` may only LOWER that ceiling), bound to the same manifest,
        root, campaign, pins and identities and to EVERY shard job the ledger holds now (PBS id, token, plan hash);
  - before any real submission the code pins of the manifest are verified against the clone the jobs will run from, and
    the wrapper's hash against the manifest's.
Each job: reserve (kind shard, rep = the job number, cores x walltime) -> the plan -> the PBS script -> qsub -> bind; the
queue's limits and this user's jobs as the scheduler reports them at that moment are retained in <root>/gate/.

    t1py chpc/row19_shard_submit.py --manifest chpc/row19_shard_manifest.json --pilot            # job 1 alone
    t1py chpc/row19_shard_submit.py --manifest chpc/row19_shard_manifest.json --adopt-review reviews/<record>.md --max-job-number 9
    t1py chpc/row19_shard_submit.py --manifest chpc/row19_shard_manifest.json --jobs 8 [--dry-run]
"""
import os, sys, json, math, time, glob, fcntl, hashlib, argparse, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from row19_ledger import CampaignLedger, LIVE


def hms(seconds):
    s = int(round(seconds)); return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def evidence(man, validate=True):
    """(done, in_flight, used job numbers, problems). `problems` non-empty HOLDS the planner."""
    root, reps = man["storage"]["root"], [int(r) for r in man["datasets"]["reps"]]
    problems, done = [], {r: set() for r in reps}
    SH = None
    for r in reps:
        files = sorted(glob.glob(os.path.join(root, "records", f"rep{r}", "rec_*.json")))
        if files and validate:
            if SH is None:
                import row19_shard as SH
            t = SH.task(man, r)
        for p in files:
            name = os.path.basename(p)
            try:
                i = int(name[4:7])
                if name != f"rec_{i:03d}.json":
                    raise ValueError("name")
            except ValueError:
                problems.append(f"{p}: not a record file name"); continue
            if validate:
                try:
                    SH.read_record(p, t, i)
                except ValueError as e:
                    problems.append(str(e)); continue
            done[r].add(i)
    flight = {r: set() for r in reps}
    led = os.path.join(man["storage"]["campaign"], "budget.json")
    entries = list(json.load(open(led))["entries"].values()) if os.path.exists(led) else []
    used = set()
    for e in entries:
        if e.get("kind") != "shard":
            continue
        used.add(int(e["rep"]))
        if e.get("state") in LIVE and e.get("runner_exit") is None:
            pp = os.path.join(root, "plans", f"job_{int(e['rep'])}.json")
            if not os.path.exists(pp):
                problems.append(f"shard job {e['rep']} ({e.get('job_id')}) is live in the ledger but its plan {pp} is missing: its indices are unknown")
                continue
            for s in json.load(open(pp)).get("slots", []):
                flight[int(s["rep"])].update(int(i) for i in s["indices"])
    return done, flight, used, problems


def plan_jobs(man, n_jobs, per_slot, done, flight, used):
    B, cores = int(man["cfg"]["n_boot_refit"]), int(man["pbs"]["cores"])
    reps = [int(r) for r in man["datasets"]["reps"]]
    groups = {}
    for r in reps:
        missing = [i for i in range(B) if i not in done[r] and i not in flight[r]]
        groups[r] = [missing[k:k + per_slot] for k in range(0, len(missing), per_slot)]
    order = []
    while any(groups[r] for r in reps):
        for r in reps:
            if groups[r]:
                order.append((r, groups[r].pop(0)))
    jobs, n = [], (max(used) + 1 if used else 1)
    for k in range(0, len(order), cores):
        if len(jobs) >= n_jobs:
            break
        chunk = order[k:k + cores]
        jobs.append({"job": n, "slots": [{"slot": s, "rep": r, "indices": idx} for s, (r, idx) in enumerate(chunk)]})
        n += 1
    left = sum(len(idx) for _, idx in order[len(jobs) * cores:])
    return jobs, left


CEILING_S = 2700.0
WATCH_SCHEMA = "row19-shard-watch-3"
QUAL_SCHEMA = "row19-shard-qualification-3"
REVIEW_SCHEMA = "row19-shard-pilot-review-1"
OK_EXITS = (0, 75)


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def strict_json(path):
    """A JSON OBJECT with no NaN / Infinity constants; anything else raises."""
    def bad(x):
        raise ValueError(f"non-finite constant {x}")
    obj = json.loads(open(path).read(), parse_constant=bad)
    if not isinstance(obj, dict):
        raise ValueError("not a JSON object")
    return obj


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _hex64(x):
    return isinstance(x, str) and len(x) == 64 and all(c in "0123456789abcdef" for c in x)


def expected_bound(man, manifest_path):
    """(bound, shard ledger entries by job number): what a receipt must be bound to, recomputed from THIS manifest file,
    the root's bindings and plans, and the campaign ledger as they are now. Raises when any of it cannot be read."""
    root, campaign = man["storage"]["root"], man["storage"]["campaign"]
    led = strict_json(os.path.join(campaign, "budget.json"))
    jobs, entries = {}, {}
    for e in led["entries"].values():
        if e.get("kind") != "shard":
            continue
        n = str(int(e["rep"]))
        if n in jobs:
            raise ValueError(f"two ledger entries for shard job {n}")
        pp = os.path.join(root, "plans", f"job_{n}.json")
        jobs[n] = dict(job_id=e.get("job_id"), token=e.get("token"), plan_sha256=sha_file(pp) if os.path.exists(pp) else None)
        entries[n] = e
    idents, bsha = {}, {}
    for r in man["datasets"]["reps"]:
        b = strict_json(os.path.join(root, f"task_{int(r)}.json")).get("binding") or {}
        idents[str(int(r))] = b.get("ident"); bsha[str(int(r))] = b.get("manifest_sha")
    bound = dict(manifest_sha256=sha_file(manifest_path), root=root, campaign=campaign, code=dict(man["code"]["files"]),
                 wrapper_sha256=man.get("environment", {}).get("wrapper_sha256"), identities=idents, binding_manifest_sha=bsha, jobs=jobs)
    return bound, entries


def bound_problem(got, want, jobs):
    """Why a receipt's `bound` is not this campaign's. `jobs`: the job numbers that must match exactly ('all' = the whole map)."""
    if not isinstance(got, dict):
        return "it carries no `bound` object"
    for k in ("manifest_sha256", "root", "campaign", "code", "wrapper_sha256", "identities", "binding_manifest_sha"):
        if got.get(k) != want[k]:
            return f"its `{k}` is not this campaign's"
    gj = got.get("jobs")
    if not isinstance(gj, dict):
        return "it carries no job bindings"
    if jobs == "all":
        if gj != want["jobs"]:
            return f"its jobs {sorted(gj)} (PBS id, token, plan hash) are not the ledger's {sorted(want['jobs'])} as they are now"
    else:
        for n in jobs:
            if n not in want["jobs"] or gj.get(n) != want["jobs"][n] or None in (want["jobs"][n] or {}).values():
                return f"its binding of job {n} (PBS id, token, plan hash) is not the ledger's and the root's"
    return ""


def campaign_problem(man, want):
    """Why the root's own bindings do not belong to this manifest ('' when they do)."""
    for r, v in want["binding_manifest_sha"].items():
        if v != want["manifest_sha256"]:
            return f"the task binding of rep {r} names manifest {str(v)[:12]}, not this manifest ({want['manifest_sha256'][:12]})"
    declared = man.get("shard", {}).get("identities")
    if declared and {str(k): v for k, v in declared.items()} != want["identities"]:
        return "the identities in the root's bindings are not the manifest's declared identities"
    if any(not _hex64(v) for v in want["identities"].values()):
        return "a task binding carries no identity"
    return ""


def receipt_problem(rc, want, man, jobs):
    """Why a watch receipt (stand-alone or embedded in the qualification) is not a production zero-alarm view of this campaign."""
    if not isinstance(rc, dict) or rc.get("schema") != WATCH_SCHEMA:
        return f"it is not a {WATCH_SCHEMA} receipt"
    if rc.get("fresh") is not True or rc.get("production") is not True:
        return f"it is not fresh production evidence (fresh {rc.get('fresh')}, production {rc.get('production')})"
    if rc.get("alarms") != []:
        return f"it carries {len(rc.get('alarms') or []) if isinstance(rc.get('alarms'), list) else 'malformed'} alarm(s)"
    if not _num(rc.get("time")):
        return "its time is not a finite number"
    return bound_problem(rc.get("bound"), want, jobs)


def qualification_problem(q_path, want, entries, man, now):
    """Why <root>/gate/qualified_job1.json does not qualify THIS pilot ('' when it does)."""
    try:
        q = strict_json(q_path)
    except Exception as e:
        return f"it is unreadable or malformed ({e})"
    if q.get("schema") != QUAL_SCHEMA:
        return f"it is not a {QUAL_SCHEMA} document"
    if q.get("qualified_job") != 1 or isinstance(q.get("qualified_job"), bool):
        return f"it qualifies job {q.get('qualified_job')!r}, not the pilot (job 1)"
    if q.get("production") is not True:
        return "it was not written from production evidence"
    if not _num(q.get("time")) or q["time"] > now + 60:
        return "its time is not a finite number or lies in the future"
    e = entries.get("1")
    if e is None:
        return "the campaign ledger holds no shard job 1"
    if not _num(e.get("runner_ended")) or e.get("runner_exit") not in OK_EXITS or isinstance(e.get("runner_exit"), bool):
        return f"the ledger does not show the pilot's runner ended 0 or 75 (ended {e.get('runner_ended')}, exit {e.get('runner_exit')})"
    if q["time"] < e["runner_ended"] - 60:
        return "it predates the pilot's recorded end"
    why = bound_problem(q.get("bound"), want, ["1"])
    if why:
        return why
    rc = q.get("receipt")
    why = receipt_problem(rc, want, man, ["1"])
    if why:
        return "its embedded receipt is refused: " + why
    if rc.get("bound") != q.get("bound") or rc.get("time") != q.get("time"):
        return "its embedded receipt is not the view it was written from (bound or time differ)"
    j = (rc.get("jobs") or {}).get("1")
    if not isinstance(j, dict):
        return "its receipt does not describe job 1"
    exits = j.get("exits")
    if (j.get("job_id") != want["jobs"]["1"]["job_id"] or j.get("state") != "F" or j.get("pbs_exit") not in OK_EXITS or j.get("terminal") is not True
            or j.get("runner_exit") not in OK_EXITS or not isinstance(exits, list) or not _num(j.get("slots")) or j.get("ended") != j.get("slots")
            or len(exits) != j.get("slots") or any(c not in OK_EXITS or isinstance(c, bool) for c in exits)):
        return "its receipt does not show the pilot finished in the scheduler (F, exit 0 or 75) with every planned worker ended 0 or 75"
    if not _num(j.get("mem_kb")) or j["mem_kb"] <= 0 or j["mem_kb"] / 2 ** 20 > 0.9 * float(man["pbs"]["mem_gb"]):
        return "its receipt does not show scheduler-accounted memory observed and under 90% of the request"
    reps = rc.get("reps") or {}
    for r in man["datasets"]["reps"]:
        v = reps.get(str(int(r)))
        if (not isinstance(v, dict) or not _num(v.get("overlap")) or v["overlap"] < 1 or v.get("equal") != v["overlap"]
                or v.get("rejected") != 0 or v.get("no_timing") != 0):
            return f"its receipt does not show observed, equal production parity with complete evidence for rep {int(r)}"
    return ""


def review_path(root):
    return os.path.join(root, "gate", "pilot_review.json")


def review_problem(man, q_path, planned, now):
    """Why the reviewer's verdict on the pilot evidence is not on record for THIS qualification and these job numbers."""
    p = review_path(man["storage"]["root"])
    if not os.path.exists(p):
        return (f"no adopted review ({p}): the reviewer's verdict on the actual pilot evidence comes first "
                f"(--adopt-review <record> --max-job-number N after the review record is committed in the clone)")
    try:
        v = strict_json(p)
    except Exception as e:
        return f"the adopted review is unreadable or malformed ({e})"
    if v.get("schema") != REVIEW_SCHEMA:
        return f"the adopted review is not a {REVIEW_SCHEMA} document"
    if not _num(v.get("time")) or v["time"] > now + 60:
        return "the adopted review's time is not a finite number or lies in the future"
    rp = v.get("record_path")
    if not isinstance(rp, str) or not rp or os.path.isabs(rp) or ".." in rp.split("/") or not _hex64(v.get("record_sha256")):
        return "the adopted review does not name a record by a relative path and a SHA-256"
    full = os.path.join(man["shard"]["clone"], "workspace_demo", "t1_access", rp)
    if not os.path.isfile(full) or sha_file(full) != v["record_sha256"]:
        return f"the review record {rp} is not in the clone with the adopted SHA-256"
    if v.get("qualification_sha256") != sha_file(q_path):
        return "the adopted review is of another qualification than the one in the gate now"
    m = v.get("max_job_number")
    if isinstance(m, bool) or not isinstance(m, int) or m < 2:
        return "the adopted review names no highest job number"
    over = [n for n in (planned or []) if int(n) > m]
    if over:
        return f"job number(s) {over} exceed the highest job number {m} the adopted review covers"
    return ""


def pin_problems(man):
    """The manifest's code pins against the clone the jobs will run from, and the wrapper's hash against the manifest's."""
    base = os.path.join(man["shard"]["clone"], "workspace_demo", "t1_access")
    bad = []
    for rel, pin in sorted(man["code"]["files"].items()):
        p = os.path.join(base, rel)
        if not os.path.isfile(p) or sha_file(p) != pin:
            bad.append(rel)
    w = man.get("environment", {}).get("wrapper_sha256")
    wp = os.path.join(man["shard"]["toolchain"], "t1py")
    if w and (not os.path.isfile(wp) or sha_file(wp) != w):
        bad.append("t1py (the pinned wrapper)")
    return bad


def gate_problems(man, used, pilot, n_jobs, max_age_s, now=None, manifest_path=None, planned=None):
    """Why this submission is refused ('' when admitted)."""
    root = man["storage"]["root"]; now = time.time() if now is None else now
    if os.path.exists(os.path.join(root, "STOP")):
        return "a STOP file is in the root: diagnose, record it in ledger row 19, remove it, then submit"
    if pilot:
        if used:
            return f"--pilot is the FIRST shard job only; the ledger already holds shard job(s) {sorted(used)}"
        if n_jobs != 1:
            return "--pilot submits exactly one job"
        return ""
    if not used:
        return "no shard job exists yet: the first job is the pilot (--pilot)"
    q = os.path.join(root, "gate", "qualified_job1.json")
    if not os.path.exists(q):
        return f"the pilot is not qualified ({q} absent): run row19_shard_status.py --qualify 1 on fresh zero-alarm evidence with production parity"
    if not manifest_path:
        return "the gate needs the manifest's path: every receipt is verified against the manifest file's hash"
    try:
        want, entries = expected_bound(man, manifest_path)
    except Exception as e:
        return f"the campaign ledger, a plan or a task binding cannot be read to verify the receipts ({e})"
    why = campaign_problem(man, want)
    if why:
        return why
    why = qualification_problem(q, want, entries, man, now)
    if why:
        return f"the pilot's qualification is refused: {why}"
    why = review_problem(man, q, planned, now)
    if why:
        return why
    r = os.path.join(root, "gate", "watch_receipt.json")
    if not os.path.exists(r):
        return f"no watch receipt ({r}): run row19_shard_status.py --publish-receipt on fresh evidence first"
    try:
        rc = strict_json(r)
    except Exception as e:
        return f"the watch receipt is unreadable or malformed ({e})"
    why = receipt_problem(rc, want, man, "all")
    if why:
        return f"the watch receipt is refused: {why}"
    limit = min(float(max_age_s), CEILING_S) if _num(max_age_s) and max_age_s > 0 else CEILING_S
    if rc["time"] > now + 60:
        return "the watch receipt's time lies in the future"
    if now - rc["time"] > limit:
        return f"the watch receipt is {now - rc['time']:.0f} s old (limit {limit:.0f} s; the ceiling is {CEILING_S:.0f} s): take a fresh view"
    return ""


def adopt_review(man, manifest_path, record_rel, max_job_number, now=None):
    """Write <root>/gate/pilot_review.json: the operator's record that the reviewer's verdict on the pilot evidence is the
    committed record `record_rel` (relative to the clone's workspace_demo/t1_access), for the qualification now in the
    gate. Refused unless that qualification itself passes the gate's verification."""
    now = time.time() if now is None else now
    root = man["storage"]["root"]
    q = os.path.join(root, "gate", "qualified_job1.json")
    if not os.path.exists(q):
        return f"REFUSED: no qualification in the gate ({q})"
    try:
        want, entries = expected_bound(man, manifest_path)
    except Exception as e:
        return f"REFUSED: the campaign ledger, a plan or a task binding cannot be read ({e})"
    why = campaign_problem(man, want) or qualification_problem(q, want, entries, man, now)
    if why:
        return f"REFUSED: the qualification in the gate does not verify: {why}"
    if isinstance(max_job_number, bool) or not isinstance(max_job_number, int) or max_job_number < 2:
        return "REFUSED: --max-job-number must be an integer of at least 2"
    if not isinstance(record_rel, str) or not record_rel or os.path.isabs(record_rel) or ".." in record_rel.split("/"):
        return "REFUSED: the record is named by a path relative to the clone's workspace_demo/t1_access"
    full = os.path.join(man["shard"]["clone"], "workspace_demo", "t1_access", record_rel)
    if not os.path.isfile(full):
        return f"REFUSED: the review record {full} is not in the clone (commit it and update the clone first)"
    p = review_path(root)
    if os.path.exists(p):
        return f"REFUSED: {p} exists; an adopted review is never overwritten (retire it by hand, recorded in ledger row 19)"
    doc = dict(schema=REVIEW_SCHEMA, by="R052", time=now, record_path=record_rel, record_sha256=sha_file(full),
               qualification_sha256=sha_file(q), max_job_number=int(max_job_number), manifest_sha256=want["manifest_sha256"],
               pilot=want["jobs"]["1"])
    tmp = p + f".tmp.{os.getpid()}"
    with open(tmp, "w") as fh:
        json.dump(doc, fh, indent=1, allow_nan=False); fh.flush(); os.fsync(fh.fileno())
    os.link(tmp, p); os.remove(tmp)
    return f"adopted: {record_rel} ({doc['record_sha256'][:16]}) for qualification {doc['qualification_sha256'][:16]}, job numbers up to {max_job_number}"


def pbs_script(man, plan, token, walltime_s, queue, toolchain, clone, manifest_rel):
    root, cores = man["storage"]["root"], int(man["pbs"]["cores"])
    n = plan["job"]; reserve = int(float(man["pbs"]["deadline_reserve_s"]))
    end = (f"$T/t1py chpc/row19_shard.py job-end --manifest {manifest_rel} --plan $PLAN --job-id $PBS_JOBID --reservation-token {token} --started-epoch $START")
    L = ["#!/bin/bash", f"#PBS -N t1_shard_{n}", f"#PBS -P {man['pbs']['project']}", f"#PBS -q {queue}",
         f"#PBS -l select=1:ncpus={cores}:mpiprocs={cores}:mem={int(man['pbs']['mem_gb'])}gb:nodetype={man['pbs']['nodetype']}",
         f"#PBS -l walltime={hms(walltime_s)}", f"#PBS -o {toolchain}/jobs/row19_shard_{n}.out", f"#PBS -e {toolchain}/jobs/row19_shard_{n}.err",
         "#PBS -m ae", "#PBS -M pgwvanrooyen@sun.ac.za",
         f"# Ledger row 19, the sharded route (chpc/row19_shard.py): job {n}, {len(plan['slots'])} single-core workers, one resample index per record.",
         "ulimit -s unlimited", f"T={toolchain}", f"cd {clone}/workspace_demo/t1_access",
         "export NPROC=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONUNBUFFERED=1",
         "START=$(date +%s)", f"DEADLINE=$((START + {int(walltime_s)} - {reserve}))",
         'echo "host $(hostname)  $(grep -m1 \'model name\' /proc/cpuinfo)  mem $(grep MemTotal /proc/meminfo)"',
         f'echo "code $(git rev-parse --short HEAD)  start $(date -u +%FT%TZ)  job $PBS_JOBID  shard job {n}"',
         f"PLAN={root}/plans/job_{n}.json",
         f"$T/t1py chpc/row19_shard.py job-start --manifest {manifest_rel} --plan $PLAN --job-id $PBS_JOBID --walltime-s {int(walltime_s)} --reservation-token {token}",
         "rc=$?",
         'if [ $rc -ne 0 ]; then', f"  {end}", '  echo "exit $rc job $PBS_JOBID end $(date -u +%FT%TZ) (ADMISSION FAILED)"', "  exit $rc", "fi",
         f"mkdir -p {root}/logs"]
    for s in plan["slots"]:
        idx = ",".join(str(i) for i in s["indices"])
        L.append(f"$T/t1py chpc/row19_shard.py worker --manifest {manifest_rel} --rep {s['rep']} --indices {idx} --slot {s['slot']} "
                 f"--job-id $PBS_JOBID --deadline-epoch $DEADLINE > {root}/logs/job$PBS_JOBID.slot{s['slot']}.log 2>&1 &")
    L += ["wait", 'echo "node memory at the end: $(grep -E \'MemAvailable|MemFree\' /proc/meminfo | tr \'\\n\' \' \')"', end,
          "rc=$?", 'echo "exit $rc job $PBS_JOBID end $(date -u +%FT%TZ)"', "exit $rc"]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--jobs", type=int, default=None, help="the most jobs to submit in this call")
    ap.add_argument("--pilot", action="store_true", help="the first shard job, alone")
    ap.add_argument("--per-slot", type=int, default=None)
    ap.add_argument("--queue", default=None); ap.add_argument("--walltime-h", type=float, default=None)
    ap.add_argument("--receipt-max-age-s", type=float, default=CEILING_S, help="may only LOWER the 2,700 s ceiling")
    ap.add_argument("--adopt-review", default=None, help="the reviewer's committed record of the pilot evidence, relative to workspace_demo/t1_access")
    ap.add_argument("--max-job-number", type=int, default=None, help="with --adopt-review: the highest shard job number the review covers")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); sh = man["shard"]
    if a.adopt_review is not None:
        out = adopt_review(man, a.manifest, a.adopt_review, a.max_job_number)
        print(out); return 0 if out.startswith("adopted") else 2
    n_jobs = 1 if a.pilot else a.jobs
    if not n_jobs or n_jobs < 1:
        print("say --pilot or --jobs N"); return 2
    per_slot = int(a.per_slot or sh["per_slot"]); queue = a.queue or man["pbs"]["queue"]
    walltime_s = float(a.walltime_h or man["pbs"]["walltime_h"]) * 3600.0
    toolchain, clone, root = sh["toolchain"], sh["clone"], man["storage"]["root"]
    os.makedirs(os.path.join(root, "plans"), exist_ok=True); os.makedirs(os.path.join(root, "gate"), exist_ok=True)
    manifest_rel = os.path.relpath(os.path.abspath(a.manifest), os.path.join(clone, "workspace_demo", "t1_access"))
    with open(os.path.join(root, "plans", ".submit.lock"), "a+") as lk:
        try:
            fcntl.flock(lk.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("HELD: another submitter holds the plan lock"); return 2
        done, flight, used, problems = evidence(man)
        B = int(man["cfg"]["n_boot_refit"])
        for r in sorted(done):
            print(f"rep {r}: valid records {len(done[r])}/{B}, in flight {len(flight[r])}, missing {B - len(done[r] | flight[r])}")
        if problems:
            print(f"HELD: {len(problems)} problem(s) in the evidence; nothing is planned:")
            for p in problems[:10]:
                print("   -", p)
            return 2
        jobs, left = plan_jobs(man, n_jobs, per_slot, done, flight, used)
        why = gate_problems(man, used, a.pilot, n_jobs, a.receipt_max_age_s, manifest_path=a.manifest, planned=[j["job"] for j in jobs])
        pins = pin_problems(man)
        if pins and not why:
            why = f"the manifest's pins do not hold in the clone the jobs run from: {pins}"
        print(f"planned {len(jobs)} job(s), {sum(len(s['indices']) for j in jobs for s in j['slots'])} indices; {left} missing indices not in this call")
        if a.dry_run:
            print(f"DRY RUN; the gate {'would REFUSE: ' + why if why else 'would admit this submission'}")
            for j in jobs:
                print(f"  job {j['job']}: {len(j['slots'])} slots: " + "; ".join(f"slot {s['slot']} rep {s['rep']} {s['indices']}" for s in j["slots"][:4]) + (" ..." if len(j["slots"]) > 4 else ""))
            return 0
        if why:
            print(f"REFUSED by the submission gate: {why}"); return 2
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        lim = []
        for cmd in (["qstat", "-Qf", queue], ["qstat", "-u", os.environ.get("USER", "")], ["qmgr", "-c", "print server"]):
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                lim.append(f"$ {' '.join(cmd)}\n{r.stdout}{r.stderr}")
            except Exception as e:
                lim.append(f"$ {' '.join(cmd)}\nFAILED: {e}")
        open(os.path.join(root, "gate", f"limits_{stamp}.txt"), "w").write("\n".join(lim))
        L = CampaignLedger(man["storage"]["campaign"], man["budget"]["core_hours_cap"])
        os.makedirs(os.path.join(toolchain, "jobs"), exist_ok=True)
        for j in jobs:
            cores = int(man["pbs"]["cores"])
            token, t = L.reserve("shard", int(j["job"]), cores, walltime_s, root,
                                 f"submitted by row19_shard_submit.py {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
            pp = os.path.join(root, "plans", f"job_{j['job']}.json")
            with open(pp, "w") as fh:
                json.dump(dict(j, queue=queue, walltime_s=walltime_s, token=token, created=time.time()), fh, indent=1); fh.flush(); os.fsync(fh.fileno())
            sp = os.path.join(toolchain, "jobs", f"row19_shard_{j['job']}.pbs")
            open(sp, "w").write(pbs_script(man, j, token, walltime_s, queue, toolchain, clone, manifest_rel))
            r = subprocess.run(["qsub", sp], capture_output=True, text=True)
            if r.returncode != 0:
                print(f"job {j['job']}: qsub failed ({r.stderr.strip()[:200]}); reservation {token} stays reserved and unbound - record it in row 19 and "
                      f"reconcile it by token before any further submission"); return 1
            job_id = r.stdout.strip()
            L.bind(token, job_id)
            print(f"job {j['job']}: reserved {token} ({cores} x {walltime_s/3600:.0f} h = {cores*walltime_s/3600:.0f} core-h; spent {t['spent']:.0f}, live {t['live']:.0f} of {t['cap']:.0f}), "
                  f"submitted {job_id} on {queue}, {len(j['slots'])} workers, {sum(len(s['indices']) for s in j['slots'])} indices")
    return 0


if __name__ == "__main__":
    sys.exit(main())
