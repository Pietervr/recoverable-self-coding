"""Controls v17 CANDIDATE: every regression suite BEFORE (the v16 state: live modules / the candidate folders as reviewed) and
AFTER (the v17 module set, regress/run_one.py), with pass/fail counts and the FAIL lines that differ.

    python3 chpc/candidate_v17/regress/run_v17_regress.py [--only <substring>]        (from workspace_demo/t1_access)

The three admission suites (candidate_v16/test_designated_r16.py and the REVISION 13/14 regress copies) run in three
configurations:
  BEFORE       chpc/candidate_v16 (the adopted v16 admission/status/controls), live modules;
  AFTER-code   a transient world chpc/.v17_world_<pid>_code/ = the v17 admission + the unchanged status + the v16 controls,
               with the v17 module set: the pure code comparison (only the admission changed);
  AFTER-v17    the same world with the v17 controls: the controls-dependent differences, each explained in test_results.txt.
The world folders sit directly under chpc/ so the admission resolves T1 exactly as chpc/candidate_v16's does; they hold copies
only and are removed at the end. Nothing else is written."""
import os, re, shutil, subprocess, sys

V17 = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); CHPC = os.path.dirname(V17); T1 = os.path.dirname(CHPC)
RUN = os.path.join(V17, "regress", "run_one.py")
V16 = os.path.join(CHPC, "candidate_v16")
PLAIN = ["test_row19_partition.py", "test_row19_ec2_ingest.py", "test_row19_ec2_qualify.py", "test_row19_ec2_status.py",
         "aws_ec2/tests/test_prod_authority.py", "aws_ec2/tests/test_prod_launch.py", "aws_ec2/tests/test_ec2_sync.py",
         "chpc/candidate_e2/test_e2_partition.py", "chpc/candidate_e2/test_e2_authority.py", "chpc/candidate_e2/test_e2_ingest.py",
         "chpc/candidate_e2/test_e2_rules.py", "chpc/candidate_e2q/test_e2q_contracts.py", "chpc/candidate_e2q/test_e2q_qualify.py",
         "chpc/candidate_e2q/test_e2q_release.py"]
ADMIT = ["test_designated_r16.py", "regress_pbs_settled_r13.py", "regress_crashed_slot_r14.py"]
OKRE, FAILRE = re.compile(r"^(ok|PASS)\b"), re.compile(r"^FAIL\b")


def run(cmd, env=None):
    p = subprocess.run(cmd, cwd=T1, capture_output=True, text=True, env=dict(os.environ, **(env or {})), timeout=3600)
    lines = (p.stdout + p.stderr).splitlines()
    oks = sum(1 for l in lines if OKRE.match(l)); fails = [l for l in lines if FAILRE.match(l)]
    tail = "" if p.returncode in (0, 1) and (oks or fails) else (p.stdout + p.stderr)[-600:]
    return dict(rc=p.returncode, ok=oks, fail=len(fails), fails=fails, tail=tail)


def world(tag, controls):
    w = os.path.join(CHPC, f".v17_world_{os.getpid()}_{tag}")
    os.makedirs(w)
    shutil.copyfile(os.path.join(V17, "row19_screen_admit.py"), os.path.join(w, "row19_screen_admit.py"))
    for n in ("row19_screen_status.py", "row19_screen_designated.json", "test_designated_r16.py"):
        shutil.copyfile(os.path.join(V16, n), os.path.join(w, n))
    shutil.copyfile(controls, os.path.join(w, "row19_screen_controls.json"))
    return w


def admit_cmd(name, d, live):
    test = os.path.join(d, name) if name == "test_designated_r16.py" else os.path.join(V16, "regress", name)
    return [sys.executable, RUN] + (["--live"] if live else []) + [test], {"R19_UNDER_TEST": d}


def show(label, r):
    print(f"{label:<70} rc {r['rc']:>2}  {r['ok']:>3} pass / {r['fail']} fail", flush=True)
    for l in r["fails"]:
        print(f"      {l[:180]}")
    if r["tail"]:
        print("      [output tail] " + r["tail"].replace("\n", "\n      "))


def main():
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else ""
    print("# BEFORE = v16 state (live modules; candidate folders as reviewed); AFTER = the v17 module set (run_one.py)")
    for t in PLAIN:
        if only and only not in t:
            continue
        b, a = run([sys.executable, RUN, "--live", t]), run([sys.executable, RUN, t])
        show(f"{t}  BEFORE", b); show(f"{t}  AFTER ", a)
        if sorted(b["fails"]) != sorted(a["fails"]) or b["ok"] != a["ok"]:
            print("      >>> BEFORE and AFTER differ")
    wc = world("code", os.path.join(V16, "row19_screen_controls.json"))
    wv = world("v17", os.path.join(V17, "row19_screen_controls.json"))
    try:
        for n in ADMIT:
            if only and only not in n:
                continue
            res = {}
            for label, d, live in (("BEFORE    ", V16, True), ("AFTER-code", wc, False), ("AFTER-v17 ", wv, False)):
                cmd, env = admit_cmd(n, d, live)
                res[label] = run(cmd, env); show(f"{n}  {label}", res[label])
            if sorted(res["BEFORE    "]["fails"]) != sorted(res["AFTER-code"]["fails"]) or res["BEFORE    "]["ok"] != res["AFTER-code"]["ok"]:
                print("      >>> BEFORE and AFTER-code differ")
    finally:
        shutil.rmtree(wc, ignore_errors=True); shutil.rmtree(wv, ignore_errors=True)


if __name__ == "__main__":
    main()
