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

THE SUBMISSION GATE (enforced here, not only a policy):
  - a STOP file in the root refuses every submission;
  - the FIRST shard job is the pilot: `--pilot`, exactly one job, only while the ledger holds no shard entry;
  - every later submission needs <root>/gate/qualified_job1.json (written by row19_shard_status.py --qualify 1 from a
    fresh zero-alarm view of the pilot with production parity observed) AND a watch receipt <root>/gate/watch_receipt.json
    with zero alarms, fresh evidence, younger than `--receipt-max-age-s` (default 2,700 s).
Each job: reserve (kind shard, rep = the job number, cores x walltime) -> the plan -> the PBS script -> qsub -> bind; the
queue's limits and this user's jobs as the scheduler reports them at that moment are retained in <root>/gate/.

    t1py chpc/row19_shard_submit.py --manifest chpc/row19_shard_manifest.json --pilot            # job 1 alone
    t1py chpc/row19_shard_submit.py --manifest chpc/row19_shard_manifest.json --jobs 8 [--dry-run]
"""
import os, sys, json, time, glob, fcntl, argparse, subprocess

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


def gate_problems(man, used, pilot, n_jobs, max_age_s, now=None):
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
    r = os.path.join(root, "gate", "watch_receipt.json")
    if not os.path.exists(r):
        return f"no watch receipt ({r}): run row19_shard_status.py --publish-receipt on fresh evidence first"
    try:
        rc = json.load(open(r))
    except Exception as e:
        return f"the watch receipt is unreadable ({e})"
    if rc.get("alarms") != [] or rc.get("fresh") is not True:
        return f"the watch receipt is not a fresh zero-alarm view (fresh {rc.get('fresh')}, alarms {len(rc.get('alarms') or [])})"
    if not isinstance(rc.get("time"), (int, float)) or now - rc["time"] > max_age_s or rc["time"] > now + 60:
        return f"the watch receipt is {now - float(rc.get('time', 0)):.0f} s old (limit {max_age_s:.0f} s): take a fresh view"
    return ""


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
    ap.add_argument("--receipt-max-age-s", type=float, default=2700.0)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); sh = man["shard"]
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
        why = gate_problems(man, used, a.pilot, n_jobs, a.receipt_max_age_s)
        jobs, left = plan_jobs(man, n_jobs, per_slot, done, flight, used)
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
