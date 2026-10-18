"""Regression of the reviewed epoch-2 CANDIDATE's own tests (chpc/candidate_e2/test_e2_*.py) with this package's changed
modules substituted: the test file is read UNMODIFIED from disk, its two explicit load paths of the Mac modules
(`os.path.join(CAND, "aws_ec2", "prod_authority.py")` and `... "prod_launch.py"`) are redirected in memory to
chpc/candidate_e2q/aws_ec2/, and the meta-path finder of run_regress.py maps every plain import (row19_ec2_state and the
rest) as there. It runs with the test's own __file__, so its paths resolve exactly as when run directly.

    python3 chpc/candidate_e2q/regress/run_e2_tests.py chpc/candidate_e2/test_e2_authority.py   (from workspace_demo/t1_access)"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); Q = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import run_regress as RR

SUBST = {'os.path.join(CAND, "aws_ec2", "prod_authority.py")': repr(os.path.join(Q, "aws_ec2", "prod_authority.py")),
         'os.path.join(CAND, "aws_ec2", "prod_launch.py")': repr(os.path.join(Q, "aws_ec2", "prod_launch.py"))}


def main():
    test = os.path.abspath(sys.argv[1])
    src = open(test).read()
    n = {k: src.count(k) for k in SUBST}
    for k, v in SUBST.items():
        src = src.replace(k, v)
    sys.meta_path.insert(0, RR.CandidateFinder())
    sys.argv = [test] + sys.argv[2:]
    sys.path.insert(0, os.path.dirname(test))
    print(f"# regress: {os.path.relpath(test)} with the e2q Mac modules ({n}) and the e2q finder", flush=True)
    g = {"__file__": test, "__name__": "__main__"}
    exec(compile(src, test, "exec"), g)


if __name__ == "__main__":
    main()
