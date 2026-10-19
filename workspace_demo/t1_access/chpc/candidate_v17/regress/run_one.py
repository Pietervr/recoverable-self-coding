"""Controls v17 CANDIDATE regression harness: run ONE existing, unmodified test file with the v17 module set substituted for
the live modules (the pattern of chpc/candidate_e2/regress/run_regress.py and chpc/candidate_e2q/regress/run_regress.py).

    python3 chpc/candidate_v17/regress/run_one.py [--live] <test file> [args...]          (from workspace_demo/t1_access)

The v17 module set is exactly what controls v17 pins (chpc/candidate_v17/v17_promotion_map.json, group pin) plus the Mac
modules the promotion carries (group mac): a meta-path finder maps each NAME to its candidate source when (and only when) the
test imports it by name. Explicit load paths in a test file are redirected in memory, never on disk:
  - the candidate_v16 admission  -> chpc/candidate_v17/row19_screen_admit.py (test_e2_partition.py loads it by path);
  - candidate_e2's Mac modules   -> the candidate_e2q copies (run_e2_tests.py's substitution).
`row19_screen_admit` is NOT mapped by name: the live controllers resolve their T1 and controls from their own folder, so a
by-name substitution would change the lineage paths, not the code (see DESIGN_v17.md s.4). `--live` runs the same file with no
substitution at all (the BEFORE column)."""
import importlib.abc, importlib.util, json, os, sys

V17 = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); CHPC = os.path.dirname(V17); T1 = os.path.dirname(CHPC)
PM = json.load(open(os.path.join(V17, "v17_promotion_map.json")))
MAP = {os.path.splitext(os.path.basename(r["promoted"]))[0]: os.path.join(T1, r["source"])
       for r in PM["rows"] if r["group"] in ("pin", "mac") and r["promoted"].endswith(".py") and not r["promoted"].endswith("row19_screen_admit.py")}
E2Q = os.path.join(CHPC, "candidate_e2q")
SUBST = {'os.path.join(CHPC, "candidate_v16", "row19_screen_admit.py")': repr(os.path.join(V17, "row19_screen_admit.py")),
         'os.path.join(CAND, "aws_ec2", "prod_authority.py")': repr(os.path.join(E2Q, "aws_ec2", "prod_authority.py")),
         'os.path.join(CAND, "aws_ec2", "prod_launch.py")': repr(os.path.join(E2Q, "aws_ec2", "prod_launch.py"))}


class V17Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        return importlib.util.spec_from_file_location(name, MAP[name]) if name in MAP else None


def main():
    args = sys.argv[1:]
    live = args[:1] == ["--live"]
    if live:
        args = args[1:]
    test = os.path.abspath(args[0])
    src = open(test).read()
    n = {}
    if not live:
        sys.meta_path.insert(0, V17Finder())
        for k, v in SUBST.items():
            n[k.split('"')[-2]] = src.count(k); src = src.replace(k, v)
    sys.argv = [test] + args[1:]
    sys.path.insert(0, os.path.dirname(test))
    print(f"# run_one: {os.path.relpath(test, T1)} with {'LIVE modules' if live else 'v17 modules ' + ','.join(sorted(MAP)) + f' subst {n}'}", flush=True)
    exec(compile(src, test, "exec"), {"__file__": test, "__name__": "__main__"})


if __name__ == "__main__":
    main()
