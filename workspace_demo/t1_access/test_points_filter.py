"""The POINTS grid filter of the cloud runner (13 Sept 2026, Codex's allocation for the reference bank): named points
are kept in the declared grid's order, a point not in the grid is an error, an empty or malformed selection is an
error, and the GENERATORS filter composes with it. The helper is uploaded with the job (launch_t1.CODE_FILES)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("NPROC", "1")
from points_filter import select_points, parse_points
import simulate as S
import launch_t1 as L

assert "points_filter.py" in L.CODE_FILES and "t1_job.py" in L.CODE_FILES
grid = S.null_points()
assert ("M2S", {"omega": 2.0}) in grid and ("M2B", {}) in grid
assert parse_points("M2S:omega=2.0,M2H:tau=0.5,M2B") == [("M2S", {"omega": 2.0}), ("M2H", {"tau": 0.5}), ("M2B", {})]
kept = select_points(grid, "M2S:omega=2.0,M2S:omega=1.0")
assert kept == [("M2S", {"omega": 1.0}), ("M2S", {"omega": 2.0})], kept        # grid order, not spec order
assert select_points(grid, "M2B") == [("M2B", {})]
assert select_points(grid, " M2S:omega=2 ") == [("M2S", {"omega": 2.0})]      # whitespace and 2 vs 2.0
for bad in ("M2S:omega=3.0", "M2Z", "M2S:omega=", "", ",", ":omega=2.0", "M2S:omega=2.0;tau=0.5"):
    try:
        select_points(grid, bad); raise AssertionError(f"accepted {bad!r}")
    except SystemExit:
        pass
sub = [p for p in grid if p[0] == "M2S"]                                          # GENERATORS=M2S then POINTS
assert select_points(sub, "M2S:omega=2.0") == [("M2S", {"omega": 2.0})]
try:
    select_points(sub, "M2B"); raise AssertionError("M2B accepted after GENERATORS=M2S")
except SystemExit:
    pass
print("points filter: grid order kept, unknown / empty / malformed rejected, composes with GENERATORS, uploaded with the job OK")
