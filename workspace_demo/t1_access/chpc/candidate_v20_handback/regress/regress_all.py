"""Run every regression suite twice - the LIVE v19 modules (--v19) and the v20 CANDIDATE modules (run_regress.py) - and tabulate pass/fail counts and
the names of checks whose outcome differs. Writes regress_results.txt beside itself.

    python3 chpc/candidate_v20_handback/regress/regress_all.py            (from workspace_demo/t1_access)"""
import os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SUITES = ["aws_ec2/tests/test_prod_authority.py", "aws_ec2/tests/test_prod_launch.py", "aws_ec2/tests/test_ec2_sync.py",
          "chpc/candidate_e2/test_e2_partition.py", "chpc/candidate_e2/test_e2_authority.py",
          "chpc/candidate_e2q/test_e2q_release.py", "chpc/candidate_e2q/test_e2q_contracts.py",
          "chpc/candidate_v16/test_designated_r16.py", "chpc/candidate_v19_oploss/test_v19_oploss.py",
          "chpc/candidate_v19_oploss/test_v19_e2q3.py"]
PAT = re.compile(r"^(PASS|FAIL|ok|FAIL:?)\s+(.*)$")


def run(suite, live):
    cmd = [sys.executable, os.path.join(HERE, "run_regress.py")] + (["--v19"] if live else []) + [os.path.join(T1, suite)]
    t = time.time(); p = subprocess.run(cmd, cwd=T1, capture_output=True, text=True, timeout=3600)
    res = {}
    for line in p.stdout.splitlines():
        m = PAT.match(line.strip())
        if m:
            res[m.group(2).strip()[:160]] = m.group(1).startswith("PASS") or m.group(1) == "ok"
    return res, p.returncode, time.time() - t, p.stdout[-600:] + p.stderr[-600:]


out = []
for s in SUITES:
    a, rca, ta, tail_a = run(s, True)
    b, rcb, tb, tail_b = run(s, False)
    diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    line = (f"{s}: v19 {sum(a.values())} pass / {sum(1 for v in a.values() if not v)} fail (rc {rca}, {ta:.0f} s); "
            f"v20 {sum(b.values())} pass / {sum(1 for v in b.values() if not v)} fail (rc {rcb}, {tb:.0f} s)")
    print(line, flush=True); out.append(line)
    for k in diff:
        x = f"    DIFFERS: {k}  (v19 {a.get(k)}, v20 {b.get(k)})"; print(x); out.append(x)
    if not a and not b:
        out.append("    (no parsable check lines) v19 tail: " + tail_a.replace("\n", " | ")[-300:])
        out.append("    v20 tail: " + tail_b.replace("\n", " | ")[-300:])
open(os.path.join(HERE, "regress_results.txt"), "w").write("\n".join(out) + "\n")
