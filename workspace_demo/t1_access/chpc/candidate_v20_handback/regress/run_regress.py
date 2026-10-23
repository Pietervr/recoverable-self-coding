"""Regression for the controls v20 CANDIDATE: run an EXISTING, unmodified test file with the v20 candidate modules substituted for
their namesakes - row19_partition (REVISION 7), row19_screen_admit (REVISION 20) and prod_authority (REVISION 10) - whether the
test imports them by name or loads them from an explicit path (importlib.util.spec_from_file_location is redirected by module
name AND file basename, so a test that loads e.g. chpc/candidate_v19_oploss/row19_screen_admit.py gets the v20 bytes). Nothing
is copied over a live or candidate file.

    python3 chpc/candidate_v20_handback/regress/run_regress.py <test file> [args...]     (from workspace_demo/t1_access)
    python3 chpc/candidate_v20_handback/regress/run_regress.py --live <test file>         (the same runner without substitution)"""
import importlib.abc, importlib.util, os, runpy, sys

CAND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = {"row19_partition": os.path.join(CAND, "row19_partition.py"),
       "row19_screen_admit": os.path.join(CAND, "row19_screen_admit.py"),
       "prod_authority": os.path.join(CAND, "aws_ec2", "prod_authority.py")}
BASENAMES = {os.path.basename(p): p for p in MAP.values()}


class CandidateFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name in MAP:
            return _orig(name, MAP[name])
        return None


_orig = importlib.util.spec_from_file_location


def _redirect(name, location=None, *a, **k):
    if location is not None and (name in MAP or os.path.basename(str(location)) in BASENAMES):
        tgt = MAP.get(name) or BASENAMES[os.path.basename(str(location))]
        if os.path.basename(str(location)) == os.path.basename(tgt):
            return _orig(name, tgt, *a, **k)
    return _orig(name, location, *a, **k)


T1 = os.path.dirname(os.path.dirname(CAND))
V19 = {"row19_partition": os.path.join(T1, "chpc", "row19_partition.py"),
       "row19_screen_admit": os.path.join(T1, "chpc", "row19_screen_admit.py"),
       "prod_authority": os.path.join(T1, "aws_ec2", "prod_authority.py")}


def main():
    global MAP, BASENAMES
    args = sys.argv[1:]
    live = args[:1] == ["--live"]
    if args[:1] == ["--v19"]:                     # the baseline: the LIVE v19 modules substituted the same way
        MAP = dict(V19); BASENAMES = {os.path.basename(p): p for p in MAP.values()}
        args = args[1:]
        sys.meta_path.insert(0, CandidateFinder())
        importlib.util.spec_from_file_location = _redirect
    elif live:
        args = args[1:]
    else:
        sys.meta_path.insert(0, CandidateFinder())
        importlib.util.spec_from_file_location = _redirect
    test = os.path.abspath(args[0])
    sys.argv = [test] + args[1:]
    sys.path.insert(0, os.path.dirname(test))
    print(f"# regress: {os.path.relpath(test)} with {'LIVE (no substitution)' if live else 'modules ' + ', '.join(sorted(MAP.values()))}", flush=True)
    runpy.run_path(test, run_name="__main__")


if __name__ == "__main__":
    main()
