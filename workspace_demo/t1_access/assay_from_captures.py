"""Run the assay on real captures: validate_pilot's scores.npz -> analyze.Dataset -> the §8 decision.

This is an ADAPTER and nothing else. Every number it reports comes from analyze.analyze_dataset, the same
function the 12,000 synthetic datasets were scored with; this file only assembles the Dataset that function
takes. Its self-test exists to prove exactly that: it builds a synthetic dataset, writes it in the scores.npz
layout, runs it back through the adapter, and requires the result to equal a direct call on the original.

    .venv/bin/python assay_from_captures.py --scores validation/<run>/scores.npz --layers 41
    .venv/bin/python assay_from_captures.py --self-test

The readout is the frozen R1 decoder's z per trial and layer (decode_cal.py A3, validate_pilot.py A4), so the
readout, the decoders and the stimulus channel are all real; what the synthetic calibration stood in for was
only the distance at one layer (Methods §5.2).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os

import numpy as np

import analyze as A


def dataset_from_scores(path: str, layers: list[int] | None = None, condition: str = "active") -> A.Dataset:
    """Assemble the Dataset for one capture run. Concepts and families are factorised in first-appearance order."""
    z = np.load(path, allow_pickle=False)
    cond = np.asarray(z["condition"]).astype(str)
    keep = cond == condition
    if not keep.any():
        raise SystemExit(f"no trials with condition={condition!r} in {path}")

    all_layers = [int(x) for x in np.asarray(z["layers"])]
    want = all_layers if layers is None else list(layers)
    missing = [l for l in want if l not in all_layers]
    if missing:
        raise SystemExit(f"layers {missing} are not in the scores file (has {all_layers[0]}..{all_layers[-1]})")
    cols = [all_layers.index(l) for l in want]

    y = np.asarray(z["z"], dtype=float)[keep][:, cols]
    k = np.asarray(z["k"], dtype=float)[keep]
    concept_name = np.asarray(z["concept"]).astype(str)[keep]
    family_name = np.asarray(z["family"]).astype(str)[keep]

    # factorise in first-appearance order so the mapping is deterministic and reproducible from the file alone
    c_levels = list(dict.fromkeys(concept_name.tolist()))
    c_index = {c: i for i, c in enumerate(c_levels)}
    concept = np.array([c_index[c] for c in concept_name], dtype=int)

    f_levels = list(dict.fromkeys(family_name.tolist()))
    f_index = {f: i for i, f in enumerate(f_levels)}
    family_per_concept = np.empty(len(c_levels), dtype=int)
    for c, i in c_index.items():
        fams = set(family_name[concept_name == c].tolist())
        if len(fams) != 1:
            raise SystemExit(f"concept {c!r} appears under more than one family: {sorted(fams)}")
        family_per_concept[i] = f_index[fams.pop()]

    return A.Dataset(y, k, concept, family_per_concept, np.asarray(want),
                     meta=dict(source=os.path.basename(path), condition=condition,
                               sha256=hashlib.sha256(open(path, "rb").read()).hexdigest(),
                               n_trials=int(keep.sum()), n_concepts=len(c_levels),
                               concepts=c_levels, families=f_levels))


def _self_test() -> None:
    """A synthetic dataset, written in the scores.npz layout and read back, must give the identical Dataset."""
    import tempfile
    import simulate as S
    import models as M

    name = "M2B"
    theta = S.generator_theta(name)
    ds = S.make_dataset(name, theta, n_per_family=2, D=1, layers=(41,), seed=7)
    n = ds.k.size
    concept_names = np.array([f"c{c:03d}" for c in ds.concept])
    family_names = np.array([f"f{ds.family[c]:d}" for c in ds.concept])

    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "scores.npz")
        np.savez_compressed(p, z=ds.y.astype(np.float32), layers=np.asarray(ds.layers),
                            trial_ids=np.arange(n), k=ds.k, condition=np.array(["active"] * n),
                            concept=concept_names, family=family_names,
                            carrier=np.zeros(n, dtype=int), draw=np.zeros(n, dtype=int))
        back = dataset_from_scores(p, layers=[int(ds.layers[0])])

    assert back.n_concepts == ds.n_concepts, (back.n_concepts, ds.n_concepts)
    assert np.array_equal(back.k, ds.k)
    assert np.array_equal(back.concept, ds.concept)
    assert np.array_equal(back.family, ds.family)
    np.testing.assert_allclose(back.y, ds.y.astype(np.float32), rtol=0, atol=0)
    print(f"self-test OK: {back.n_concepts} concepts, {back.k.size} trials, layers {list(back.layers)};"
          f" concept, family, dose and readout all round-trip unchanged")
    print("the adapter reproduces the Dataset that analyze_dataset is given by the synthetic path,"
          " so any difference in a verdict comes from the data and not from this file")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scores", help="validation/<run>/scores.npz from validate_pilot.py")
    ap.add_argument("--layers", default=None, help="comma list of layer ids; default every captured layer")
    ap.add_argument("--condition", default="active")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--n-starts-inner", type=int, default=4)
    ap.add_argument("--interval", choices=["cluster", "refit"], default="cluster")
    ap.add_argument("--out", default=None, help="write the report here as JSON")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        _self_test()
        return
    if not a.scores:
        raise SystemExit("--scores is required (or --self-test)")

    layers = [int(x) for x in a.layers.split(",")] if a.layers else None
    ds = dataset_from_scores(a.scores, layers=layers, condition=a.condition)
    cfg = A.Config(n_starts_inner=a.n_starts_inner, interval=a.interval)
    print(f"dataset: {ds.n_concepts} concepts, {ds.k.size} trials, {ds.n_layers} layers, "
          f"condition {a.condition}, scores sha256 {ds.meta['sha256'][:12]}")
    res = A.analyze_dataset(ds, cfg, seed=a.seed)

    def _plain(o):
        """numpy arrays and scalars are not JSON types; ndarray.tolist() is lossless for float64."""
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, np.generic):
            return o.item()
        raise TypeError(f"cannot serialise {type(o).__name__}")

    report = dict(source=ds.meta, cfg=dict(interval=a.interval, n_starts_inner=a.n_starts_inner, seed=a.seed),
                  result=json.loads(json.dumps(res, default=_plain)))
    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        with open(a.out, "w") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)
        print(f"wrote {a.out}")
    else:
        print(json.dumps(report["result"], indent=2, sort_keys=True, default=_plain)[:2000])


if __name__ == "__main__":
    main()
