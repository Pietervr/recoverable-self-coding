"""Dense M3S checks at the smoke run's saved cross-fitted parameters; no refitting."""
import os
import sys
from pathlib import Path
import json
import time

os.environ["NPROC"] = "1"
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
T = HERE.parents[2]
sys.path.insert(0, str(T))
import numpy as np
from bounded import generators as G, procedure as P
from bounded.test_bounded import dense_m3s_scores
import analyze as A
import models as M

start = time.process_time()
out = {}
for sid in ("A14", "G09", "G14", "G13", "G16", "A13"):
    row = json.loads((T / f"bounded/dev/smoke_rows/{sid}_r0.json").read_text())
    s = G.setting(sid)
    ds = G.make(s, row["dataset_seed"], lam=row["boundary_lambda_used"])
    qdense = np.empty(64)
    qprod = np.asarray(row["logq"]["M3S"])
    diagnostics = []
    for fit in row["fits"]:
        if fit["member"] != "M3S":
            continue
        f = fit["fold"]
        tec = np.asarray(row["folds"][f])
        trc = np.setdiff1d(np.arange(64), tec)
        floor = float(np.std(ds.y[np.isin(ds.concept, trc), 0], ddof=1))
        te = A._subset(ds.y[:, 0], ds.k, ds.concept, tec, floor)
        th = np.asarray(fit["theta"])
        qs = M.concept_scores("M3S", th, te)
        np.testing.assert_array_equal(qs, qprod[tec])
        dense = dense_m3s_scores(th, te)
        qdense[tec] = dense
        diagnostics.append(dict(fold=f, omega=float(np.exp(th[7])),
                                max_error=float(np.max(np.abs(qs-dense))),
                                max_v_over_omega=float(np.max(np.abs(ds.meta.get("v_c", np.zeros(64)))) / np.exp(th[7]))))
    qnew = {m: np.asarray(v) for m, v in row["logq"].items()}
    qnew["M3S"] = qdense
    new = P.assemble(qnew, row["n_c"], row["family"])
    out[sid] = dict(max_concept_error=float(np.max(np.abs(qprod-qdense))),
                    T_original=row["point"]["bounded"], T_dense_M3S=new["T"],
                    T_difference=new["T"]-row["point"]["bounded"], fits=diagnostics)
    print(sid, json.dumps(out[sid]), flush=True)
out["cpu_seconds"] = time.process_time()-start
(HERE / "dense-saved-audit.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
