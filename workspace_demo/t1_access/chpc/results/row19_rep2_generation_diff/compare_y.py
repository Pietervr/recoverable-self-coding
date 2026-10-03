"""Compare the Mac-generated and Lengau-generated response arrays for reps 1 and 2: differing elements, max |delta|, ULPs."""
import numpy as np, os
S = os.path.dirname(os.path.abspath(__file__))
for rep in (1, 2):
    a = np.load(os.path.join(S, f"mac_rep{rep}_y.npy")).ravel(); b = np.load(os.path.join(S, f"lengau_rep{rep}_y.npy")).ravel()
    d = a != b
    print(f"rep {rep}: n {a.size} differing {int(d.sum())} max|delta| {float(np.max(np.abs(a - b)))!r} max rel {float(np.max(np.abs(a - b) / np.maximum(np.abs(a), 1e-300)))!r}")
    if d.any():
        idx = np.where(d)[0][:6]
        for i in idx:
            ulps = abs(a[i].view(np.int64) - b[i].view(np.int64))
            print(f"   i {int(i)} mac {a[i]!r} lengau {b[i]!r} ulps {int(ulps)}")
