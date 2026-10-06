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
  - every later submission needs <root>/gate/bank_review.json, written by `--adopt-review <record> --max-job-number N`: the
    reviewer's committed record of the pilot's actual evidence, named by path and SHA-256 (verified here, in this clone),
    bounded to a highest job number; never overwritten;
  - before any real submission the manifest's code pins are verified in the clone the jobs run from.

    t1py chpc/row22_bank_submit.py --manifest chpc/row22_bank_manifest.json --pilot [--dry-run]
    t1py chpc/row22_bank_submit.py --manifest chpc/row22_bank_manifest.json --adopt-review reviews/<record>.md --max-job-number 17
    t1py chpc/row22_bank_submit.py --manifest chpc/row22_bank_manifest.json --jobs 4 [--dry-run]
"""
import os, sys, json, time, glob, fcntl, hashlib, argparse, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from row19_ledger import CampaignLedger, LIVE

REVIEW_SCHEMA = "row22-bank-review-1"


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


def review_problem(man, planned):
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
    return ""


def adopt_review(man, record_rel, max_job_number):
    root = man["storage"]["root"]
    full = os.path.join(T1, record_rel)
    if not os.path.exists(full):
        return f"REFUSED: {record_rel} is not in this clone"
    if not isinstance(max_job_number, int) or max_job_number < 2:
        return "REFUSED: --max-job-number must be an integer of at least 2"
    os.makedirs(os.path.join(root, "gate"), exist_ok=True)
    p = os.path.join(root, "gate", "bank_review.json")
    if os.path.exists(p):
        return f"REFUSED: {p} exists; an adopted review is never overwritten (retire it by hand, recorded in ledger row 22)"
    doc = dict(schema=REVIEW_SCHEMA, by="R052", time=time.time(), record_path=record_rel, record_sha256=sha_file(full),
               max_job_number=int(max_job_number))
    tmp = p + f".tmp.{os.getpid()}"
    with open(tmp, "w") as fh:
        json.dump(doc, fh, indent=1, allow_nan=False); fh.flush(); os.fsync(fh.fileno())
    os.link(tmp, p); os.remove(tmp)
    return f"adopted: {record_rel} ({doc['record_sha256'][:16]}), job numbers up to {max_job_number}"


def gate_problem(man, used, pilot, n_jobs, planned):
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
    return review_problem(man, planned)


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
        out = adopt_review(man, a.adopt_review, a.max_job_number)
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
        why = gate_problem(man, used, a.pilot, n_jobs, [j["job"] for j in jobs])
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
