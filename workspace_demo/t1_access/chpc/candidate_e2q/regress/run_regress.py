"""Regression for the epoch-2 QUALIFICATION candidate (chpc/candidate_e2q/): run an EXISTING, unmodified test file with the
candidate modules substituted for their live namesakes - the e2q copies where this package changed a module
(row19_ec2_state, row19_ec2_qualify, prod_authority, prod_launch, make_prod_manifest, qual_permit) and the new
row19_ec2_e2qual, otherwise the reviewed chpc/candidate_e2/ modules (row19_partition, row19_ec2_ingest, row19_ec2_e2rules).
The pattern is chpc/candidate_e2/regress/run_regress.py: a meta-path finder maps those names when (and only when) the test
imports them, so tests that stub row19_shard before importing the ingestion keep working. Nothing is copied over the live
files.

    python3 chpc/candidate_e2q/regress/run_regress.py <test file> [args...]     (from workspace_demo/t1_access)
    python3 chpc/candidate_e2q/regress/run_regress.py --live <test file>         (the same runner without substitution)"""
import importlib.abc, importlib.util, os, runpy, sys

Q = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E2 = os.path.join(os.path.dirname(Q), "candidate_e2")
MAP = {"row19_partition": os.path.join(E2, "row19_partition.py"),
       "row19_ec2_ingest": os.path.join(E2, "row19_ec2_ingest.py"),
       "row19_ec2_e2rules": os.path.join(E2, "row19_ec2_e2rules.py"),
       "row19_ec2_state": os.path.join(Q, "row19_ec2_state.py"),
       "row19_ec2_qualify": os.path.join(Q, "row19_ec2_qualify.py"),
       "row19_ec2_e2qual": os.path.join(Q, "row19_ec2_e2qual.py"),
       "prod_authority": os.path.join(Q, "aws_ec2", "prod_authority.py"),
       "prod_launch": os.path.join(Q, "aws_ec2", "prod_launch.py"),
       "make_prod_manifest": os.path.join(Q, "aws_ec2", "make_prod_manifest.py"),
       "qual_permit": os.path.join(Q, "aws_ec2", "qual_permit.py")}


class CandidateFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name in MAP:
            return importlib.util.spec_from_file_location(name, MAP[name])
        return None


def main():
    args = sys.argv[1:]
    live = args[:1] == ["--live"]
    if live:
        args = args[1:]
    else:
        sys.meta_path.insert(0, CandidateFinder())
    test = os.path.abspath(args[0])
    sys.argv = [test] + args[1:]
    sys.path.insert(0, os.path.dirname(test))
    print(f"# regress: {os.path.relpath(test)} with {'LIVE modules' if live else 'CANDIDATE modules ' + ', '.join(sorted(MAP))}", flush=True)
    runpy.run_path(test, run_name="__main__")


if __name__ == "__main__":
    main()
