"""Ledger row 19: read the qualification slice LIVE from the Mac, so a wrong run is caught in its first hours and not
after two weeks (owner, 2 Oct: "evaluate as the results come in"). Pulls the slice root's timing, status, budget and
live-log files from Lustre over the sanctioned transfer node, then prints per dataset: resamples recorded, the rate,
the projected chain time left, failures, the original fit, utilisation and peak memory, plus the budget ledger.
Read-only: nothing on Lustre is written or changed. Nothing scientific is read or printed: a status file's `result`
and `interval` entries (present only when a chain completes) are never loaded into the view.

    python chpc/row19_watch.py [--root /mnt/lustre/users/pvanrooyen/t1_toolchain/row19_slice] [--no-pull]
                               [--expect-fit-s LO HI]   # flag a resample whose fit time lies outside this range
Exit 1 when an alarm is raised, else 0.
"""
import argparse, glob, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL = os.path.join(HERE, "results", "row19_slice", "live")
HOST = "chpc-scp"
NEVER_SHOWN = ("result", "interval")


def pull(root):
    os.makedirs(LOCAL, exist_ok=True)
    cmd = ["scp", "-q", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes",
           f"{HOST}:{root}/status_*.json", f"{HOST}:{root}/timing_*.jsonl", f"{HOST}:{root}/budget.json",
           f"{HOST}:{root}/live_*.log", LOCAL + "/"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 and "No such file" not in r.stderr:
        print("pull failed:", r.stderr.strip()[:300])
    return r.returncode


def timing(rep):
    p = os.path.join(LOCAL, f"timing_{rep}.jsonl")
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in open(p) if l.strip()]


def status(rep):
    p = os.path.join(LOCAL, f"status_{rep}.json")
    if not os.path.exists(p):
        return {}
    st = json.load(open(p))
    for k in NEVER_SHOWN:
        st.pop(k, None)
    return st


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/mnt/lustre/users/pvanrooyen/t1_toolchain/row19_slice")
    ap.add_argument("--no-pull", action="store_true")
    ap.add_argument("--expect-fit-s", nargs=2, type=float, default=None)
    a = ap.parse_args(argv)
    if not a.no_pull:
        pull(a.root)
    now = time.time()
    print(f"ROW 19 SLICE, live view at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))}  (root {a.root})")
    reps = sorted({os.path.basename(p)[7:-6] for p in glob.glob(os.path.join(LOCAL, "timing_*.jsonl"))}
                  | {os.path.basename(p)[7:-5] for p in glob.glob(os.path.join(LOCAL, "status_*.json"))}, key=int)
    alarms = []
    for rep in reps:
        st, rows = status(rep), timing(rep)
        n_rep = st.get("n_rep", 200)
        done = max(st.get("n_done", 0), len(rows))
        fits = [r["fit_seconds"] for r in rows if not r.get("failed")]
        fails = [r["rep"] for r in rows if r.get("failed")]
        rate_h = None
        if len(rows) >= 2:
            span = rows[-1]["t"] - rows[0]["t"]
            rate_h = (len(rows) - 1) / span * 3600 if span > 0 else None
        left = max(0, n_rep - done)
        eta = f"{left / rate_h:.1f} h of chain time left" if rate_h else "rate unknown"
        print(f"\n  dataset rep {rep}: {done}/{n_rep} resamples recorded"
              + (f"  (last job {st.get('job')}: new {st.get('n_new')} resumed {st.get('n_resumed')} tail-repaired "
                 f"{st.get('n_tail_repaired')} damaged {st.get('n_damaged')} partial={st.get('partial')} "
                 f"stopped_at_deadline={st.get('stopped_at_deadline')})" if st else "  (no job has ended yet)"))
        if st:
            print(f"    original fit {st.get('original_seconds', 0):.0f} s (cached={st.get('original_cached')})  "
                  f"utilisation {st.get('utilisation', 0):.2f}  maxrss {st.get('maxrss_bytes', 0)/2**30:.2f} GiB  "
                  f"job wall {st.get('wall_seconds', 0)/3600:.2f} h")
        if fits:
            fs = sorted(fits)
            print(f"    fit seconds: n {len(fits)}  min {fs[0]:.0f}  median {fs[len(fs)//2]:.0f}  max {fs[-1]:.0f}"
                  + (f"  rate {rate_h:.2f}/h  -> {eta}" if rate_h else f"  -> {eta}"))
        if rows:
            age = (now - rows[-1]["t"]) / 60
            print(f"    last record {age:.0f} min ago")
            if age > 240 and done < n_rep and not st.get("partial") is False:
                alarms.append(f"rep {rep}: no record for {age:.0f} min while unfinished")
        if fails:
            alarms.append(f"rep {rep}: {len(fails)} failed resample(s) {fails[:10]}")
        if a.expect_fit_s and fits:
            lo, hi = a.expect_fit_s
            out = [f for f in fits if f < lo or f > hi]
            if out:
                alarms.append(f"rep {rep}: {len(out)} fit(s) outside [{lo:.0f}, {hi:.0f}] s, e.g. {[round(x) for x in out[:5]]}")
        if st.get("n_damaged"):
            alarms.append(f"rep {rep}: damaged checkpoint records {st['n_damaged']}")
    bp = os.path.join(LOCAL, "budget.json")
    if os.path.exists(bp):
        b = json.load(open(bp))
        jobs = b.get("jobs", {})
        spent = sum(j.get("spent_core_h", 0.0) for j in jobs.values() if j.get("state") == "ended")
        live = sum(j.get("reserved_core_h", 0.0) for j in jobs.values() if j.get("state") == "live")
        print(f"\n  budget: spent {spent:.1f} core-h, live reserved {live:.1f}, cap {b.get('cap')}  ({len(jobs)} job records)")
        if spent + live > float(b.get("cap", 0)) + 1e-9:
            alarms.append("budget: spent + live reserved exceeds the cap")
    for lp in sorted(glob.glob(os.path.join(LOCAL, "live_*.log"))):
        tail = open(lp, errors="replace").read().splitlines()[-2:]
        print(f"\n  {os.path.basename(lp)}: " + " | ".join(t[:150] for t in tail))
    print("\n  ALARMS:" if alarms else "\n  no alarms")
    for x in alarms:
        print("   -", x)
    return 1 if alarms else 0


if __name__ == "__main__":
    sys.exit(main())
