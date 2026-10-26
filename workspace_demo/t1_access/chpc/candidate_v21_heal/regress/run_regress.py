"""Regression for the controls v21 CANDIDATE (the funding route): run an EXISTING, unmodified test file with the v21 candidate
modules substituted for their namesakes - programme_gate (REVISION 5) and row19_screen_admit (REVISION 21) - whether the test
imports them by name or loads them from an explicit path (importlib.util.spec_from_file_location is redirected by module name AND
file basename, so a test that loads e.g. chpc/candidate_v20_handback/row19_screen_admit.py gets the v21 bytes). Nothing is copied
over a live or candidate file. The candidate_v20_handback runner pattern.

    python3 chpc/candidate_v21_heal/regress/run_regress.py <test file> [args...]     (from workspace_demo/t1_access)
    python3 chpc/candidate_v21_heal/regress/run_regress.py --v20 <test file>         (the LIVE v20 modules substituted the same way)
    python3 chpc/candidate_v21_heal/regress/run_regress.py --live <test file>        (no substitution)"""
import importlib.abc, importlib.util, os, runpy, sys

CAND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = {"programme_gate": os.path.join(CAND, "programme_gate.py"),
       "row19_screen_admit": os.path.join(CAND, "row19_screen_admit.py")}
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
V20 = {"programme_gate": os.path.join(T1, "chpc", "programme_gate.py"),
       "row19_screen_admit": os.path.join(T1, "chpc", "row19_screen_admit.py")}


def main():
    global MAP, BASENAMES
    args = sys.argv[1:]
    live = args[:1] == ["--live"]
    if args[:1] == ["--v20"]:                     # the baseline: the LIVE v20 modules substituted the same way
        MAP = dict(V20); BASENAMES = {os.path.basename(p): p for p in MAP.values()}
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
