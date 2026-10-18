"""Scale-up review evidence for the first v16 new-order job (46 = 7545616.sched01). Read-only; prints one JSON document.
Scheduler facts are selected fields of qstat -xf only (the raw capture is never kept)."""
import json, os, hashlib, subprocess, statistics

ROOT = "/mnt/lustre/users/pvanrooyen/t1_toolchain/row19_screen"
JOBS = "/mnt/lustre/users/pvanrooyen/t1_toolchain/jobs"
JID = "7545616.sched01"
N = 46


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


plan_p = os.path.join(ROOT, "plans", f"job_{N}.json")
plan = json.load(open(plan_p))
out = dict(job=N, job_id=JID, plan_path=f"plans/job_{N}.json", plan_sha256=sha(plan_p),
           plan=dict(order=plan["order"], queue=plan["queue"], walltime_s=plan["walltime_s"], envelope=plan["envelope"],
                     designated_sha256=plan["designated_sha256"], slots=plan["slots"]))

keep = ["job_state", "Exit_status", "queue", "exec_host", "Resource_List.ncpus", "Resource_List.mem",
        "Resource_List.walltime", "Resource_List.select", "resources_used.cpupercent", "resources_used.cput",
        "resources_used.mem", "resources_used.vmem", "resources_used.ncpus", "resources_used.walltime", "stime", "mtime"]
x = subprocess.run(["qstat", "-xf", JID], stdout=subprocess.PIPE, universal_newlines=True).stdout
sched = {}
for line in x.splitlines():
    if " = " in line:
        k, v = line.strip().split(" = ", 1)
        if k in keep:
            sched[k] = v
out["scheduler"] = sched

slots = []
for s in plan["slots"]:
    p = os.path.join(ROOT, "status", f"job{JID}.slot{s['slot']}.json")
    st = json.load(open(p)) if os.path.exists(p) else None
    row = dict(slot=s["slot"], rep=s["rep"], indices=s["indices"], status_sha256=sha(p) if st else None)
    if st:
        row.update({k: st.get(k) for k in ("exit", "host", "wall_s", "cpu_s", "maxrss", "new", "resumed", "left", "reason")})
        row["maxrss_gib"] = round(st["maxrss"] / 2**30, 3) if st.get("maxrss") else None
    recs = []
    for i in s["indices"]:
        rp = os.path.join(ROOT, "records", f"rep{s['rep']}", f"rec_{i:03d}.json")
        tp = os.path.join(ROOT, "timing", f"rep{s['rep']}", f"t_{i:03d}.json")
        recs.append(dict(index=i, record_sha256=sha(rp) if os.path.exists(rp) else None,
                         timing_sha256=sha(tp) if os.path.exists(tp) else None,
                         timing=json.load(open(tp)) if os.path.exists(tp) else None))
    row["coordinates"] = recs
    slots.append(row)
out["slots"] = slots

w = [r["wall_s"] for r in slots if r.get("wall_s")]
m = [r["maxrss"] for r in slots if r.get("maxrss")]
out["summary"] = dict(
    slots=len(slots), statuses=sum(1 for r in slots if r.get("exit") is not None),
    exit0=sum(1 for r in slots if r.get("exit") == 0),
    records=sum(1 for r in slots for c in r["coordinates"] if c["record_sha256"]),
    timings=sum(1 for r in slots for c in r["coordinates"] if c["timing_sha256"]),
    wall_s_min=min(w), wall_s_median=statistics.median(w), wall_s_max=max(w),
    maxrss_gib_min=round(min(m) / 2**30, 3), maxrss_gib_median=round(statistics.median(m) / 2**30, 3),
    maxrss_gib_max=round(max(m) / 2**30, 3), maxrss_gib_sum=round(sum(m) / 2**30, 3))
for f in (f"row19_screen_refit_{N}.out", f"row19_screen_refit_{N}.err"):
    p = os.path.join(JOBS, f)
    out.setdefault("pbs_output_sha256", {})[f] = sha(p) if os.path.exists(p) else None
print(json.dumps(out, indent=1))
