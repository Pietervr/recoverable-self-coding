"""Regression for the epoch-2 CANDIDATE: run an EXISTING, unmodified test file with the candidate modules substituted for
their live namesakes (row19_partition, row19_ec2_ingest, row19_ec2_qualify, prod_authority, prod_launch; and the
candidate-only row19_ec2_e2rules, REVISION 6). A meta-path finder
maps those names to chpc/candidate_e2/ when (and only when) the test imports them, so tests that stub row19_shard before
importing the ingestion keep working. Nothing is copied over the live files.

    python3 chpc/candidate_e2/regress/run_regress.py <test file> [args...]     (from workspace_demo/t1_access)
    python3 chpc/candidate_e2/regress/run_regress.py --live <test file>         (the same runner without substitution)"""
import importlib.abc, importlib.util, os, runpy, sys

CAND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = {"row19_partition": os.path.join(CAND, "row19_partition.py"),
       "row19_ec2_ingest": os.path.join(CAND, "row19_ec2_ingest.py"),
       "row19_ec2_qualify": os.path.join(CAND, "row19_ec2_qualify.py"),
       "row19_ec2_e2rules": os.path.join(CAND, "row19_ec2_e2rules.py"),     # REVISION 6: candidate-only shared rules
       "prod_authority": os.path.join(CAND, "aws_ec2", "prod_authority.py"),
       "prod_launch": os.path.join(CAND, "aws_ec2", "prod_launch.py")}


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
