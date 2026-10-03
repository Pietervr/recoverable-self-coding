"""Row 19 sharded route: plan and submit packed jobs of single-core per-index workers (run on the login node under t1py).

The plan is derived from evidence, never from memory: an index is DONE when its record file exists in the shard root,
IN FLIGHT when it is in the plan of a campaign-ledger 'shard' entry that is not settled and whose runner has not ended,
and MISSING otherwise. Missing indices are grouped per dataset rep into runs of `per_slot` (one worker = one rep = one
core), the groups are interleaved across the reps so every dataset advances, and each job takes `cores` groups.
Each job: reserve (kind shard, rep = the job number, cores x walltime) -> write the plan and the PBS script -> qsub -> bind.

    t1py chpc/row19_shard_submit.py --manifest chpc/row19_shard_manifest.json --jobs 9 [--dry-run]
"""
import os, sys, json, time, glob, argparse, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from row19_ledger import CampaignLedger, LIVE


def hms(seconds):
    s = int(round(seconds)); return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def evidence(man):
    """(done, in_flight) as {rep: set(indices)} from the record files and the live ledger entries' plans."""
    root, reps = man["storage"]["root"], [int(r) for r in man["datasets"]["reps"]]
    done = {r: {int(os.path.basename(p)[4:7]) for p in glob.glob(os.path.join(root, "records", f"rep{r}", "rec_*.json"))} for r in reps}
    flight = {r: set() for r in reps}
    led = os.path.join(man["storage"]["campaign"], "budget.json")
    entries = json.load(open(led))["entries"].values() if os.path.exists(led) else []
    used = set()
    for e in entries:
        if e.get("kind") != "shard":
            continue
        used.add(int(e["rep"]))
        if e.get("state") in LIVE and e.get("runner_exit") is None:
            pp = os.path.join(root, "plans", f"job_{int(e['rep'])}.json")
            if os.path.exists(pp):
                for s in json.load(open(pp)).get("slots", []):
                    flight[int(s["rep"])].update(int(i) for i in s["indices"])
    return done, flight, used


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
    left = sum(len(g) for r in reps for g in groups[r]) + sum(len(idx) for _, idx in order[len(jobs) * cores:])
    return jobs, left


def pbs_script(man, plan, token, walltime_s, queue, toolchain, clone, manifest_rel):
    root, cores = man["storage"]["root"], int(man["pbs"]["cores"])
    n = plan["job"]; reserve = int(float(man["pbs"]["deadline_reserve_s"]))
    L = ["#!/bin/bash", f"#PBS -N t1_shard_{n}", f"#PBS -P {man['pbs']['project']}", f"#PBS -q {queue}",
         f"#PBS -l select=1:ncpus={cores}:mpiprocs={cores}:mem={int(man['pbs']['mem_gb'])}gb:nodetype={man['pbs']['nodetype']}",
         f"#PBS -l walltime={hms(walltime_s)}", f"#PBS -o {toolchain}/jobs/row19_shard_{n}.out", f"#PBS -e {toolchain}/jobs/row19_shard_{n}.err",
         "#PBS -m ae", "#PBS -M pgwvanrooyen@sun.ac.za",
         f"# Ledger row 19, the sharded route (chpc/row19_shard.py): job {n}, {len(plan['slots'])} single-core workers, one resample index per record.",
         "ulimit -s unlimited", f"T={toolchain}", f"cd {clone}/workspace_demo/t1_access",
         "export NPROC=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONUNBUFFERED=1",
         "START=$(date +%s)", f"DEADLINE=$((START + {int(walltime_s)} - {reserve}))",
         'echo "host $(hostname)  $(grep -m1 \'model name\' /proc/cpuinfo)"',
         f'echo "code $(git rev-parse --short HEAD)  start $(date -u +%FT%TZ)  job $PBS_JOBID  shard job {n}"',
         f"PLAN={root}/plans/job_{n}.json",
         f"$T/t1py chpc/row19_shard.py job-start --manifest {manifest_rel} --plan $PLAN --job-id $PBS_JOBID --walltime-s {int(walltime_s)} --reservation-token {token}",
         "rc=$?", 'if [ $rc -ne 0 ]; then echo "exit $rc job $PBS_JOBID end $(date -u +%FT%TZ) (admission)"; exit $rc; fi',
         f"mkdir -p {root}/logs"]
    for s in plan["slots"]:
        idx = ",".join(str(i) for i in s["indices"])
        L.append(f"$T/t1py chpc/row19_shard.py worker --manifest {manifest_rel} --rep {s['rep']} --indices {idx} --slot {s['slot']} "
                 f"--job-id $PBS_JOBID --deadline-epoch $DEADLINE > {root}/logs/job$PBS_JOBID.slot{s['slot']}.log 2>&1 &")
    L += ["wait",
          f"$T/t1py chpc/row19_shard.py job-end --manifest {manifest_rel} --plan $PLAN --job-id $PBS_JOBID --reservation-token {token} --started-epoch $START",
          "rc=$?", 'echo "exit $rc job $PBS_JOBID end $(date -u +%FT%TZ)"', "exit $rc"]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--jobs", type=int, required=True, help="the most jobs to submit in this call")
    ap.add_argument("--per-slot", type=int, default=None)
    ap.add_argument("--queue", default=None); ap.add_argument("--walltime-h", type=float, default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); sh = man["shard"]
    per_slot = int(a.per_slot or sh["per_slot"]); queue = a.queue or man["pbs"]["queue"]
    walltime_s = float(a.walltime_h or man["pbs"]["walltime_h"]) * 3600.0
    toolchain, clone, root = sh["toolchain"], sh["clone"], man["storage"]["root"]
    manifest_rel = os.path.relpath(os.path.abspath(a.manifest), os.path.join(clone, "workspace_demo", "t1_access")) if not a.dry_run else a.manifest
    done, flight, used = evidence(man)
    jobs, left = plan_jobs(man, a.jobs, per_slot, done, flight, used)
    B = int(man["cfg"]["n_boot_refit"])
    for r in sorted(done):
        print(f"rep {r}: done {len(done[r])}/{B}, in flight {len(flight[r])}, missing {B - len(done[r] | flight[r])}")
    print(f"planned {len(jobs)} job(s), {sum(len(s['indices']) for j in jobs for s in j['slots'])} indices; {left} missing indices not in this call")
    if a.dry_run:
        for j in jobs:
            print(f"  job {j['job']}: " + "; ".join(f"slot {s['slot']} rep {s['rep']} {s['indices']}" for s in j["slots"][:4]) + (" ..." if len(j["slots"]) > 4 else ""))
        return 0
    L = CampaignLedger(man["storage"]["campaign"], man["budget"]["core_hours_cap"])
    os.makedirs(os.path.join(root, "plans"), exist_ok=True); os.makedirs(os.path.join(toolchain, "jobs"), exist_ok=True)
    for j in jobs:
        cores = int(man["pbs"]["cores"])
        token, t = L.reserve("shard", int(j["job"]), cores, walltime_s, root,
                             f"submitted by row19_shard_submit.py {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
        pp = os.path.join(root, "plans", f"job_{j['job']}.json")
        with open(pp, "w") as fh:
            json.dump(dict(j, queue=queue, walltime_s=walltime_s, token=token, created=time.time()), fh, indent=1)
        sp = os.path.join(toolchain, "jobs", f"row19_shard_{j['job']}.pbs")
        open(sp, "w").write(pbs_script(man, j, token, walltime_s, queue, toolchain, clone, manifest_rel))
        r = subprocess.run(["qsub", sp], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"job {j['job']}: qsub failed ({r.stderr.strip()[:200]}); reservation {token} stays reserved - settle it with a note"); return 1
        job_id = r.stdout.strip()
        L.bind(token, job_id)
        print(f"job {j['job']}: reserved {token} ({cores} x {walltime_s/3600:.0f} h = {cores*walltime_s/3600:.0f} core-h; spent {t['spent']:.0f}, live {t['live']:.0f} of {t['cap']:.0f}), "
              f"submitted {job_id} on {queue}, {sum(len(s['indices']) for s in j['slots'])} indices")
    return 0


if __name__ == "__main__":
    sys.exit(main())
