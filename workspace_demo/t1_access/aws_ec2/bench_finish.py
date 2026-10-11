"""Row 23: finish one benchmark attempt in one command, and test it against the success criterion recorded before any
result (R052 log, 10 Oct ~20:40Z).

    python3 aws_ec2/bench_finish.py --run b2 --attempt 5 [--declare]

  1. download s3://xtenure-cself-pvr-usw2/results/t1_access/aws_bench/<run>/attempt_<n>/ (read profile)
  2. stream it to Lengau aws_bench/<run>a<n>/attempt_<n>/ (tar over ssh, ControlPath=none) with this tree's bench_compare.py
  3. run bench_compare.py there under t1py from the controller tree (counts and deviations only - never a value)
  4. pull the report to runs/<run>/bench_report_attempt<n>.json and evaluate the criterion:
       report valid; profile_B == B_full; arm B stage 1 exact 12/12 with identical decisions and failed flags;
       arm B stage 2: 36 validated records, 36 valid timing pairs, payload_exact 36, no non-finite disagreement;
       arm A either refused at job-start (typed, a44f5aa) or fully validated.
  5. --declare (only when every criterion holds): set ec2_release_state.json row23 = declared_success with the report's
     path and sha256 - an evidence gate, which qualification still needs a favourable reviewed record behind.
Exit 0 success, 3 not success (reasons printed), 2 a transport step failed."""
import argparse, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bench_launch as L

BUCKET = "s3://xtenure-cself-pvr-usw2/results/t1_access/aws_bench"
T = "/mnt/lustre/users/pvanrooyen/t1_toolchain"
SSH = ["ssh", "-o", "ControlPath=none", "-o", "ConnectTimeout=30", "-o", "BatchMode=yes", "lengau"]
REL = os.path.join(HERE, "ec2_release_state.json")


def criterion(rep):
    why = []
    if rep.get("valid") is not True:
        why.append(f"report not valid ({len(rep.get('problems', []))} problem(s))")
    if rep.get("profile_B") != "B_full":
        why.append(f"profile_B {rep.get('profile_B')!r}, not B_full")
    s1 = (rep.get("stage1") or {}).get("B") or {}
    if not (s1.get("exact_quantities") == "12/12" and s1.get("decisions_identical") is True and s1.get("failed_flags_identical") is True):
        why.append(f"arm B row 6 not exact ({s1.get('exact_quantities')}, decisions {s1.get('decisions_identical')}, failed {s1.get('failed_flags_identical')})")
    s2 = (rep.get("stage2") or {}).get("B") or {}
    for k in ("validated_records", "valid_timing_pairs", "payload_exact"):
        if s2.get(k) != 36:
            why.append(f"arm B {k} {s2.get(k)} of 36")
    if s2.get("nonfinite_disagreements", 1) != 0:
        why.append(f"arm B non-finite disagreements {s2.get('nonfinite_disagreements')}")
    a = (rep.get("stage2") or {}).get("A") or {}
    if not (a.get("refused_at_job_start") is True or a.get("validated_records") == 36):
        why.append("arm A neither refused at job-start nor fully validated")
    return why


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="b2"); ap.add_argument("--attempt", type=int, required=True); ap.add_argument("--declare", action="store_true")
    a = ap.parse_args()
    name = f"attempt_{a.attempt}"; local = os.path.join(HERE, "runs", a.run, "fetched", name)
    remote = f"/home/pvanrooyen/lustre/aws_bench/{a.run}a{a.attempt}"
    try:
        subprocess.run(["aws", "--profile", "xtenure-read", "--region", "us-west-2", "s3", "sync", "--only-show-errors",
                        f"{BUCKET}/{a.run}/{name}/", local + "/"], check=True, timeout=3600)
        subprocess.run(SSH + ["mkdir", "-p", remote], check=True, timeout=120)
        tar = subprocess.Popen(["tar", "-C", os.path.dirname(local), "-cf", "-", name], stdout=subprocess.PIPE)
        subprocess.run(SSH + [f"cd {remote} && rm -rf {name}.new && mkdir {name}.new && tar -xf - -C {name}.new && rm -rf {name} && mv {name}.new/{name} {name} && rmdir {name}.new"],
                       stdin=tar.stdout, check=True, timeout=3600)
        tar.stdout.close()
        if tar.wait() != 0:
            raise subprocess.CalledProcessError(tar.returncode, "tar")
        subprocess.run(["scp", "-o", "ControlPath=none", "-q", os.path.join(HERE, "bench_compare.py"), f"lengau:{remote}/bench_compare.py"], check=True, timeout=300)
        cmd = (f"cd {remote} && {T}/t1py bench_compare.py --tree {T}/rsc_screen_ctl/workspace_demo/t1_access --ec2 {remote}/{name} "
               f"--lengau-root {T}/row19_screen --row6-ref {T}/jobs --out {remote}/report_{name}.json > {remote}/compare_{name}.out 2>&1; echo rc=$?")
        r = subprocess.run(SSH + [cmd], capture_output=True, text=True, timeout=7200)
        print(r.stdout.strip())
        out = os.path.join(HERE, "runs", a.run, f"bench_report_{name}.json")
        subprocess.run(["scp", "-o", "ControlPath=none", "-q", f"lengau:{remote}/report_{name}.json", out], check=True, timeout=300)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"TRANSPORT FAILED: {e}"); return 2
    rep = json.load(open(out))
    for p in rep.get("problems", []):
        print("INVALID:", p)
    why = criterion(rep)
    if why:
        print("NOT SUCCESS:"); [print("  -", w) for w in why]
        return 3
    print(f"ROW 23 SUCCESS: {name} meets the recorded criterion ({out})")
    if a.declare:
        rel = json.load(open(REL))
        rel["row23"] = dict(declared_success=True, report_path=os.path.relpath(out, HERE), report_sha256=L.sha256(out),
                            criterion="valid report; B_full; arm B row 6 exact 12/12; arm B 36/36 validated, timed, payload-exact; "
                                      "arm A refused at job-start or fully validated (recorded 10 Oct ~20:40Z before results)")
        tmp = REL + ".tmp"; json.dump(rel, open(tmp, "w"), indent=1); open(tmp, "a").write("\n"); os.replace(tmp, REL)
        print("declared in ec2_release_state.json row23")
    return 0


if __name__ == "__main__":
    sys.exit(main())
