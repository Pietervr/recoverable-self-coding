"""Row 23 attempt 5: stage 1 (row-6 panel) only, via bench_compare.stage1. Prints counts, flags and |delta| - no values."""
import json, sys
sys.argv = [sys.argv[0], "--tree", sys.argv[1]] + sys.argv[2:]
import bench_compare as B
ec2, ref = sys.argv[3], sys.argv[4]
problems = []
out = B.stage1(ec2, ref, problems)
print(json.dumps(dict(stage1=out, problems=problems), indent=1))
