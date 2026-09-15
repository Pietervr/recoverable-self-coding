"""A3: the per-layer R1 decoders from CAL captures, frozen (PREREGISTRATION_T1_model.md §5, §6.1).

Environment (scikit-learn pinned in requirements_decode.txt):
    uv venv --python 3.12 workspace_demo/t1_access/.venv-decode
    uv pip install --python workspace_demo/t1_access/.venv-decode/bin/python -r workspace_demo/t1_access/requirements_decode.txt
    workspace_demo/t1_access/.venv-decode/bin/python workspace_demo/t1_access/decode_cal.py --run <CAL capture run>

Per layer l (every captured layer; 0-62 are analysed, 63 is descriptive):
- data: CAL primary active-condition trials at k = 8 (y = 1) and k = 0 (y = 0); X = the post-layer residual at
  the readout position, as exact float32 values of the stored bfloat16 bits;
- C_l from 9 values log-spaced over [1e-3, 1e1] by 5-fold concept-disjoint cross-validation: folds are a seeded
  assignment of the 16 CAL concepts, balanced across families (sizes 4, 3, 3, 3, 3); a StandardScaler is fitted
  inside each training fold; LogisticRegression(penalty="l2", C, solver="lbfgs", tol=1e-6, max_iter=5000);
  selection = mean held-out log-loss over the five folds; ties go to the smaller C;
- the scaler and decoder are refitted on all CAL k in {0, 8} trials with C_l and frozen; the z-scaling constants
  are the mean and SD of the refitted decision function over those same training trials.

Output (committed): decoders/<run>/decoders.npz (per layer: coef, intercept, scaler mean and scale, C, z mean and
SD) and decoders/<run>/decode_cal.json (CV log-loss and accuracy per C and layer, chosen C, convergence flags,
counts, fold assignment, versions, identity of the input run). Convergence failures are recorded, never hidden.
"""

from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import hashlib
import json
import random
import sys
import time
import warnings
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from capture import CAPTURES, bf16_to_float32  # noqa: E402

C_GRID = np.logspace(-3, 1, 9)
N_FOLDS = 5
FOLD_SEED = "t1-cal-folds-20260915"
LR_KW = dict(penalty="l2", solver="lbfgs", tol=1e-6, max_iter=5000)


def parse_trial_id(tid: str) -> dict:
    parts = tid.split("|")
    out = {"split": parts[0], "set": parts[1], "condition": parts[2], "concept": parts[3],
           "carrier": int(parts[4][1:]), "draw": int(parts[5][1:]), "k": int(parts[6][1:])}
    out["family"] = out["concept"].split("/")[0]
    return out


def concept_folds(concepts: list[str], n_folds: int = N_FOLDS, seed: str = FOLD_SEED) -> dict[str, int]:
    """Seeded concept-disjoint folds, interleaving families so each fold mixes them."""
    rng = random.Random(int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16))
    by_family: dict[str, list[str]] = {}
    for c in sorted(concepts):
        by_family.setdefault(c.split("/")[0], []).append(c)
    families = sorted(by_family)
    rng.shuffle(families)
    for f in families:
        rng.shuffle(by_family[f])
    order = []
    depth = max(len(v) for v in by_family.values())
    for i in range(depth):
        order += [by_family[f][i] for f in families if i < len(by_family[f])]
    return {c: i % n_folds for i, c in enumerate(order)}


def fit_one(X: np.ndarray, y: np.ndarray, C: float):
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler().fit(X)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        clf = LogisticRegression(C=float(C), **LR_KW).fit(scaler.transform(X), y)
    converged = not any(issubclass(w.category, ConvergenceWarning) for w in caught) and \
        int(np.max(clf.n_iter_)) < LR_KW["max_iter"]
    other = sorted({str(w.message)[:160] for w in caught if not issubclass(w.category, ConvergenceWarning)})
    return scaler, clf, converged, other


def fit_layer(X: np.ndarray, y: np.ndarray, concepts: np.ndarray, folds: dict[str, int]) -> dict:
    """Cross-validated C selection, refit and z-scaling for one layer."""
    from sklearn.metrics import log_loss

    fold_of = np.array([folds[c] for c in concepts])
    cv = {"log_loss": [], "accuracy": [], "converged": []}
    for C in C_GRID:
        losses, accs, conv = [], [], []
        for f in range(N_FOLDS):
            tr, te = fold_of != f, fold_of == f
            scaler, clf, ok, _ = fit_one(X[tr], y[tr], C)
            p = clf.predict_proba(scaler.transform(X[te]))[:, 1]
            losses.append(float(log_loss(y[te], p, labels=[0, 1])))
            accs.append(float(np.mean((p >= 0.5) == (y[te] == 1))))
            conv.append(ok)
        cv["log_loss"].append(float(np.mean(losses)))
        cv["accuracy"].append(float(np.mean(accs)))
        cv["converged"].append(all(conv))
    losses = np.array(cv["log_loss"])
    best = int(np.flatnonzero(losses <= losses.min() + 1e-12)[0])  # C_GRID ascending: first = smallest C
    scaler, clf, ok, other = fit_one(X, y, C_GRID[best])
    score = clf.decision_function(scaler.transform(X))
    return {
        "C": float(C_GRID[best]), "C_index": best, "cv": cv, "refit_converged": ok, "warnings": other,
        "coef": clf.coef_[0].astype(np.float64), "intercept": float(clf.intercept_[0]),
        "scaler_mean": scaler.mean_.astype(np.float64), "scaler_scale": scaler.scale_.astype(np.float64),
        "z_mean": float(np.mean(score)), "z_sd": float(np.std(score, ddof=0)),
        "train_accuracy": float(np.mean((score >= 0) == (y == 1))),
    }


def load_layer(run_dir: Path, records: list[dict], layer: int) -> np.ndarray:
    maps: dict[int, np.ndarray] = {}
    rows = []
    for r in records:
        if r["shard"] not in maps:
            maps[r["shard"]] = np.load(run_dir / f"res_{r['shard']:05d}.npy", mmap_mode="r")
        rows.append(np.asarray(maps[r["shard"]][r["index"], layer]))
    return bf16_to_float32(np.stack(rows))


def apply_decoders(dec, run_dir: Path, records: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """Frozen R1 for trials: (raw decision function, z-scaled score), each [n trials, n decoder layers] (§6.1)."""
    layers = dec["layers"].tolist()
    raw = np.zeros((len(records), len(layers)))
    for j, l in enumerate(layers):
        X = load_layer(run_dir, records, l).astype(np.float64)
        raw[:, j] = ((X - dec["scaler_mean"][j]) / dec["scaler_scale"][j]) @ dec["coef"][j] + dec["intercept"][j]
    z = (raw - dec["z_mean"][None, :]) / dec["z_sd"][None, :]
    return raw, z


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="CAL capture run name under captures/")
    ap.add_argument("--n-jobs", type=int, default=4)
    ap.add_argument("--layers", default=None, help="comma list (default: every captured layer)")
    args = ap.parse_args()
    import sklearn
    from joblib import Parallel, delayed

    run_dir = CAPTURES / args.run
    header = json.loads((run_dir / "run_header.json").read_text())
    records = []
    for line in (run_dir / "trials.jsonl").read_text().splitlines():
        t = json.loads(line)
        meta = parse_trial_id(t["trial_id"])
        if meta["split"] == "CAL" and meta["set"] == "primary" and meta["condition"] == "active" and meta["k"] in (0, 8):
            records.append({**t, **meta})
    concepts = sorted({r["concept"] for r in records})
    counts = {k: sum(r["k"] == k for r in records) for k in (0, 8)}
    if len(concepts) != 16 or counts[0] != counts[8] or counts[0] != 16 * 6 * 4:
        print(f"STOP: expected 16 CAL concepts with 384 trials at each of k = 0 and 8, got {len(concepts)} and {counts}")
        return 1
    folds = concept_folds(concepts)
    y = np.array([1 if r["k"] == 8 else 0 for r in records])
    groups = np.array([r["concept"] for r in records])
    n_layers = header["provenance"]["server"]["n_layers"]
    layers = [int(x) for x in args.layers.split(",")] if args.layers else list(range(n_layers))

    t0 = time.time()
    results = Parallel(n_jobs=args.n_jobs, verbose=5)(
        delayed(fit_layer)(load_layer(run_dir, records, l), y, groups, folds) for l in layers)
    out_dir = HERE / "decoders" / args.run
    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez(out_dir / "decoders.npz", layers=np.array(layers),
             **{f"{key}": np.stack([r[key] for r in results]) for key in ("coef", "scaler_mean", "scaler_scale")},
             **{f"{key}": np.array([r[key] for r in results]) for key in ("intercept", "C", "z_mean", "z_sd")})
    summary = {
        "run": args.run,
        "run_identity_sha256": hashlib.sha256(json.dumps(header["identity"], sort_keys=True).encode()).hexdigest(),
        "trials_sha256": hashlib.sha256((run_dir / "trials.jsonl").read_bytes()).hexdigest(),
        "decode_cal_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "versions": {"sklearn": sklearn.__version__, "numpy": np.__version__, "python": sys.version.split()[0]},
        "lr_kwargs": LR_KW, "C_grid": C_GRID.tolist(), "n_folds": N_FOLDS, "fold_seed": FOLD_SEED, "folds": folds,
        "counts": counts, "wall_s": round(time.time() - t0, 1),
        "layers": {str(l): {k: r[k] for k in ("C", "C_index", "cv", "refit_converged", "warnings", "z_mean", "z_sd",
                                              "train_accuracy", "intercept")} for l, r in zip(layers, results)},
        "not_converged": [l for l, r in zip(layers, results) if not r["refit_converged"] or not all(r["cv"]["converged"])],
    }
    (out_dir / "decode_cal.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(f"decoders for {len(layers)} layers -> {out_dir}; not converged: {summary['not_converged']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
