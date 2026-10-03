"""Read-only diagnosis of the Stage A native records: per native record, the requested-logit differences against its
instrumented plain record, and the bfloat16 spacing at each logit's magnitude. Nothing is written."""
import json
import math
from pathlib import Path

import numpy as np

O = Path.home() / "Recoverable-Self-Coding/workspace_demo/t1_access/captures/photo_stage_a/passes"


def bf16_ulp(x: float) -> float:
    if x == 0:
        return 2 ** -133
    return 2.0 ** (math.floor(math.log2(abs(x))) - 7)


for p in sorted(O.glob("*-native.json")):
    rec = json.loads(p.read_text())
    i = rec["index"]
    plain = json.loads((O / f"{i:02d}-plain.json").read_text())
    li = np.array([q["logit"] for q in plain["requested"]], dtype=np.float64)
    ln = np.asarray(rec["requested_logits"], dtype=np.float64)
    d = np.abs(li - ln)
    k = int(d.argmax())
    nz = int((d > 0).sum())
    ulps = [d[j] / bf16_ulp(li[j]) for j in range(len(d)) if d[j] > 0]
    print(f"{rec['id']}: n={len(d)} nonzero={nz} max={d.max():.4g} at logit {li[k]:.4g} (bf16 ulp there "
          f"{bf16_ulp(li[k]):.4g}); diffs in ulps {sorted(set(round(u, 3) for u in ulps))}; "
          f"argmax {int(li.argmax())}/{int(ln.argmax())}; inputs_embeds_equal {rec['inputs_embeds_equal_instrumented_merge']}")
