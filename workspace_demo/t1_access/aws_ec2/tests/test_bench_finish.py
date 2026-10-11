"""Tests of bench_finish.criterion: the row-23 success rule recorded before results. No AWS, no ssh.
    python3 tests/test_bench_finish.py"""
import copy, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import bench_finish as BF
ok = True
def check(n, c, x=""):
    global ok; ok &= bool(c); print(("PASS " if c else "FAIL ") + n + (f"  [{x}]" if x and not c else ""))
good = dict(valid=True, problems=[], profile_B="B_full",
            stage1=dict(B=dict(exact_quantities="12/12", decisions_identical=True, failed_flags_identical=True)),
            stage2=dict(A=dict(refused_at_job_start=True, reason="HELD: ..."),
                        B=dict(validated_records=36, valid_timing_pairs=36, payload_exact=36, nonfinite_disagreements=0)))
check("the recorded success shape passes", BF.criterion(good) == [])
def bad(path, v):
    r = copy.deepcopy(good); d = r
    for k in path[:-1]:
        d = d[k]
    d[path[-1]] = v; return BF.criterion(r)
check("an invalid report fails", bad(["valid"], False))
check("B_nomask fails", bad(["profile_B"], "B_nomask"))
check("row 6 11/12 fails", bad(["stage1", "B", "exact_quantities"], "11/12"))
check("a decision difference at row 6 fails", bad(["stage1", "B", "decisions_identical"], False))
check("35 exact payloads fail", bad(["stage2", "B", "payload_exact"], 35))
check("35 timing pairs fail", bad(["stage2", "B", "valid_timing_pairs"], 35))
check("a non-finite disagreement fails", bad(["stage2", "B", "nonfinite_disagreements"], 1))
check("a missing arm-B stage 2 fails", bad(["stage2", "B"], {}))
check("arm A neither refused nor validated fails", bad(["stage2", "A"], dict(validated_records=12)))
check("arm A fully validated passes", bad(["stage2", "A"], dict(validated_records=36)) == [])
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
