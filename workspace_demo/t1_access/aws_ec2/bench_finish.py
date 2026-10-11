"""Row 23: finish one benchmark attempt in one command, and test it against the success criterion recorded before the
completed row-23 parity/refit results (R052 owner conditional go ~20:40Z 10 Oct, committed Unimog 7c6626e6 at 21:16:38Z;
the arm-A job-start refusal rule a44f5aa was committed 20:08:19Z, after arm-A identity observations existed).

    python3 aws_ec2/bench_finish.py --run b2 --attempt 5 [--declare]

Every invocation is FRESH (Codex 3f67eaf F-2): a new local staging directory per invocation (s3 sync into an empty
directory, so no destination-only file survives), a new remote directory and a unique report name; the comparator's exit
status is propagated through ssh (0 complete+valid, 3 complete-but-invalid, anything else = the comparator failed); the
report is bound (binding_<name>_<stamp>.json) to run, attempt, stamp, the comparator's sha256 (local = remote), the
controller-tree pins it imported, and the bundle digest computed on the Mac and recomputed on Lengau.

  criterion (bench_finish.criterion): report valid; profile_B == B_full; arm B stage 1 exact 12/12 with identical decisions
  and failed flags; arm B stage 2: 36 validated records, 36 valid timing pairs, payload_exact 36, no non-finite disagreement;
  arm A refused at job-start (typed, verified against its pin and job-start evidence) or fully validated.
  Float-bit parity may include agreeing failed fits: it is reproduction, not usable coverage or scientific success.
  --declare (only when the comparator exited 0 on THIS invocation's fresh report and every criterion holds): set
  ec2_release_state.json row23 with the report and binding paths + sha256. An evidence gate only.
Exit 0 success, 3 not success (reasons printed), 2 a transport or comparator step failed (nothing declared)."""
import argparse, hashlib, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bench_launch as L

BUCKET = "s3://xtenure-cself-pvr-usw2/results/t1_access/aws_bench"
T = "/mnt/lustre/users/pvanrooyen/t1_toolchain"
CTL = f"{T}/rsc_screen_ctl/workspace_demo/t1_access"
TREE_PINS = ("chpc/row19_shard.py", "chpc/row19_screen_verify.py", "chpc/row19_screen_manifest.json", "analyze.py", "models.py", "simulate.py")
REL = os.path.join(HERE, "ec2_release_state.json")
CRITERION_TEXT = ("valid report; B_full; arm B row 6 exact 12/12; arm B 36/36 validated, timed, payload-exact, no non-finite "
                  "disagreement; arm A refused at job-start (verified) or fully validated - recorded before the completed row-23 "
                  "parity/refit results (owner go committed Unimog 7c6626e6, 10 Oct 21:16:38Z)")


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


def bundle_digest(root):
    """sha256 over the sorted (relative path, file sha256) list of every regular file under root."""
    items = []
    for d, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(d, f)
            items.append([os.path.relpath(p, root), hashlib.sha256(open(p, "rb").read()).hexdigest()])
    return hashlib.sha256(json.dumps(sorted(items)).encode()).hexdigest(), len(items)


REMOTE_DIGEST = ("import hashlib,json,os,sys\nr=sys.argv[1];it=[]\nfor d,_,fs in os.walk(r):\n for f in fs:\n  p=os.path.join(d,f)\n"
                 "  it.append([os.path.relpath(p,r),hashlib.sha256(open(p,'rb').read()).hexdigest()])\n"
                 "print(hashlib.sha256(json.dumps(sorted(it)).encode()).hexdigest(),len(it))\n")


class Lengau:
    """Transport: S3 download, ssh/scp to Lengau (ControlPath=none). Tests substitute their own."""
    SSH = ["ssh", "-o", "ControlPath=none", "-o", "ConnectTimeout=30", "-o", "BatchMode=yes", "lengau"]

    def fetch(self, run, name, dest):
        os.makedirs(dest)                                              # must be new: no destination-only file can survive
        subprocess.run(["aws", "--profile", "xtenure-read", "--region", "us-west-2", "s3", "sync", "--only-show-errors",
                        f"{BUCKET}/{run}/{name}/", dest + "/"], check=True, timeout=3600)

    def ssh(self, cmd, stdin=None, timeout=7200):
        return subprocess.run(self.SSH + [cmd], stdin=stdin, capture_output=True, text=stdin is None, timeout=timeout)

    def push_tree(self, local_parent, name, remote_dir):
        r = subprocess.run(self.SSH + [f"mkdir {remote_dir}"], capture_output=True, text=True, timeout=120)
        if r.returncode:
            raise RuntimeError(f"remote staging directory not new: {r.stderr.strip()}")
        tar = subprocess.Popen(["tar", "-C", local_parent, "-cf", "-", name], stdout=subprocess.PIPE)
        r = subprocess.run(self.SSH + [f"tar -xf - -C {remote_dir}"], stdin=tar.stdout, capture_output=True, timeout=3600)
        tar.stdout.close()
        if tar.wait() != 0 or r.returncode != 0:
            raise RuntimeError("bundle transfer failed")

    def put(self, src, dst):
        subprocess.run(["scp", "-o", "ControlPath=none", "-q", src, f"lengau:{dst}"], check=True, timeout=300)

    def get(self, src, dst):
        subprocess.run(["scp", "-o", "ControlPath=none", "-q", f"lengau:{src}", dst], check=True, timeout=300)


def finish(tr, run, attempt, declare=False, stamp=None, log=print):
    name = f"attempt_{attempt}"; stamp = stamp or time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    stage = os.path.join(HERE, "runs", run, "fetched", f"{name}.{stamp}")
    remote = f"/home/pvanrooyen/lustre/aws_bench/{run}a{attempt}/{stamp}"
    report_rel = os.path.join("runs", run, f"bench_report_{name}_{stamp}.json")
    binding_rel = os.path.join("runs", run, f"bench_binding_{name}_{stamp}.json")
    report, binding = os.path.join(HERE, report_rel), os.path.join(HERE, binding_rel)
    comparator = os.path.join(HERE, "bench_compare.py"); csha = L.sha256(comparator)
    try:
        tr.fetch(run, name, os.path.join(stage, name))
        digest, nfiles = bundle_digest(os.path.join(stage, name))
        tr.push_tree(stage, name, remote)
        tr.put(comparator, f"{remote}/bench_compare.py")
        dg = os.path.join(stage, "bundle_digest.py"); open(dg, "w").write(REMOTE_DIGEST)
        tr.put(dg, f"{remote}/bundle_digest.py")
        r = tr.ssh(f"cd {remote} && sha256sum bench_compare.py && python3 bundle_digest.py {remote}/{name}"
                   f" && cd {CTL} && sha256sum {' '.join(TREE_PINS)}")
        if r.returncode:
            raise RuntimeError(f"remote pin/digest step failed: {r.stderr.strip()[:300]}")
        lines = r.stdout.split("\n")
        rcsha = lines[0].split()[0]; rdigest, rn = lines[1].split()
        pins = {ln.split()[1]: ln.split()[0] for ln in lines[2:] if ln.strip()}
        if rcsha != csha or rdigest != digest or int(rn) != nfiles or sorted(pins) != sorted(TREE_PINS):
            raise RuntimeError("the Lengau copy is not the staged bundle / comparator (digest, count or pins differ)")
        r = tr.ssh(f"cd {remote} && {T}/t1py bench_compare.py --tree {CTL} --ec2 {remote}/{name} --lengau-root {T}/row19_screen "
                   f"--row6-ref {T}/jobs --out {remote}/report.json > {remote}/compare.out 2>&1")
        rc = r.returncode
        log(f"comparator exit {rc}")
        if rc not in (0, 3):
            raise RuntimeError(f"the comparator failed (exit {rc}); no report is used")
        tr.get(f"{remote}/report.json", report)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, RuntimeError, ValueError, IndexError, OSError) as e:
        log(f"TRANSPORT OR COMPARATOR FAILED: {e}"); return 2
    bind = dict(schema="row23-bench-report-binding-1", run=run, attempt=attempt, stamp=stamp, comparator_exit=rc,
                comparator_sha256=csha, controller_tree=CTL, tree_pins=pins, bundle_sha256=digest, bundle_files=nfiles,
                remote_dir=remote, report_path=report_rel, report_sha256=L.sha256(report))
    json.dump(bind, open(binding, "w"), indent=1)
    rep = json.load(open(report))
    for p in rep.get("problems", []):
        log(f"INVALID: {p}")
    why = criterion(rep) + ([] if rc == 0 else [f"comparator exit {rc} (incomplete or invalid panel)"])
    if why:
        log("NOT SUCCESS:"); [log(f"  - {w}") for w in why]
        return 3
    log(f"ROW 23 SUCCESS: {name} meets the recorded criterion ({report_rel})")
    if declare:
        rel = json.load(open(REL))
        rel["row23"] = dict(declared_success=True, report_path=report_rel, report_sha256=bind["report_sha256"],
                            binding_path=binding_rel, binding_sha256=L.sha256(binding), criterion=CRITERION_TEXT)
        tmp = REL + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(rel, fh, indent=1); fh.write("\n")
        os.replace(tmp, REL)
        log("declared in ec2_release_state.json row23")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="b2"); ap.add_argument("--attempt", type=int, required=True); ap.add_argument("--declare", action="store_true")
    a = ap.parse_args()
    return finish(Lengau(), a.run, a.attempt, a.declare)


if __name__ == "__main__":
    sys.exit(main())
