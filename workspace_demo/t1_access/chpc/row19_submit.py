"""Ledger row 19: the operator's one-command submission for one job - reserve in the campaign ledger, fill the template, qsub,
bind the job id (chpc/ROW19_LAUNCH.md sections 1-3). Run on the login node under t1py from the clone's t1_access directory.
Never runs without a reservation; prints every step; --dry-run fills the file and reserves nothing.

    t1py chpc/row19_submit.py --kind main --rep 1 --attempt 1
    t1py chpc/row19_submit.py --kind c1
    t1py chpc/row19_submit.py --kind c2 --walltime-s 9540        # W_int from C1's timings (ROW19_LAUNCH.md section 2)
    t1py chpc/row19_submit.py --kind c3
"""
import os, sys, json, argparse, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from row19_ledger import CampaignLedger

TOOLCHAIN = "/mnt/lustre/users/pvanrooyen/t1_toolchain"
ROOTS = {"main": "row19_slice", "c1": "row19_slice_ctl_normal", "c2": "row19_slice_ctl_interrupted", "c3": "row19_slice_ctl_interrupted"}
MODES = {"c1": "normal", "c2": "interrupted", "c3": "resume"}
WALL = {"main": 144 * 3600, "c1": 48 * 3600, "c3": 48 * 3600}


def hms(seconds):
    s = int(round(seconds)); return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", required=True, choices=("main", "c1", "c2", "c3"))
    ap.add_argument("--rep", type=int, default=0)
    ap.add_argument("--attempt", type=int, default=1, help="main: the attempt number (1-4), names the PBS output files")
    ap.add_argument("--walltime-s", type=float, default=None, help="c2: W_int (required); others default to the declared walltime")
    ap.add_argument("--manifest", default=os.path.join(HERE, "row19_slice_manifest.json"))
    ap.add_argument("--toolchain", default=TOOLCHAIN)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest))
    if a.kind == "c2" and a.walltime_s is None:
        print("c2 needs --walltime-s W_int from C1's original and first three resamples (ROW19_LAUNCH.md section 2)"); return 2
    wall = float(a.walltime_s) if a.walltime_s is not None else float(WALL[a.kind])
    if a.kind == "c2" and not (0 < wall < 48 * 3600):
        print("W_int must lie inside (0, 48 h)"); return 2
    if a.kind == "main" and a.rep not in man["datasets"]["reps"]:
        print(f"rep {a.rep} is not declared"); return 2
    rep = a.rep if a.kind == "main" else int(man["control"]["rep"])
    root = os.path.join(a.toolchain, ROOTS[a.kind])
    campaign = man["storage"]["campaign"]
    tmpl = os.path.join(HERE, "row19_slice_rep.pbs.template" if a.kind == "main" else "row19_slice_control.pbs.template")
    text = open(tmpl).read()
    token = "DRYRUN"
    if not a.dry_run:
        L = CampaignLedger(campaign, man["budget"]["core_hours_cap"])
        token, t = L.reserve(a.kind, rep, int(man["pbs"]["cores"]), wall, root, f"submitted by row19_submit.py {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
        print(f"reserved {token}: {a.kind} rep {rep} attempt {t['attempt']}, {wall/3600:.2f} h; spent {t['spent']:.1f}, live {t['live']:.1f} of {t['cap']:.0f}")
    if a.kind == "main":
        text = text.replace("__REP__", str(rep)).replace("__ATTEMPT__", str(a.attempt)).replace("__TOKEN__", token)
        name = f"row19_slice_rep{rep}.{a.attempt}.pbs"
    else:
        text = (text.replace("__MODE__", MODES[a.kind]).replace("__KIND__", a.kind).replace("__KILL_FLAG__", "--pbs-kill-control" if a.kind == "c2" else "")
                .replace("__WALLTIME_S__", str(int(wall))).replace("__WALLTIME__", hms(wall)).replace("__ROOT__", ROOTS[a.kind]).replace("__TOKEN__", token))
        name = f"row19_ctl_{a.kind}.pbs"
    if "__" in text.replace("__init__", ""):
        left = sorted(set(w for w in text.split() if w.startswith("__") and w.endswith("__")))
        if left:
            print("unfilled placeholders:", left); return 2
    jobs = os.path.join(a.toolchain, "jobs")
    os.makedirs(jobs, exist_ok=True)
    path = os.path.join(jobs, name)
    open(path, "w").write(text)
    print(f"wrote {path}")
    if a.dry_run:
        print(text); return 0
    r = subprocess.run(["qsub", path], capture_output=True, text=True)
    if r.returncode != 0:
        print("qsub FAILED:", r.stderr.strip()[:300], "- the reservation", token, "stays live; settle or diagnose it"); return 1
    job = r.stdout.strip()
    L.bind(token, job)
    print(f"submitted {job} ({a.kind} rep {rep}, {wall/3600:.2f} h) bound to {token}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
