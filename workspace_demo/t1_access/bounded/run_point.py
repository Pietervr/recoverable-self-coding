#!/usr/bin/env python3
"""bounded/run_point.py — one (setting, replicate, namespace) of the qualification catalogue -> one JSON row.

    cd workspace_demo/t1_access
    NPROC=1 .venv/bin/python -m bounded.run_point --setting G03 --replicate 0 --namespace development --out row.json

The row: the setting and its parameters, the dataset seed, the outer folds, the bounded statistic T and the unbounded
mean U, per-concept d_c and z_c, every member's held-out joint log score per concept (full precision), per-fit
convergence / starts / recovery / log-likelihood / parameters / CPU, the unavailable flag and reason, the configuration
hash and the runtime. Deterministic given (setting, replicate, namespace): every field outside `timing` and the per-fit
`cpu_seconds` / `wall_seconds` is a function of those three and the hashed code; `deterministic_sha256` is the SHA-256
of the row's canonical JSON with those timing fields removed, so two runs of one identity carry the same digest (the
determinism test compares those bytes).

Configuration hash (12 hex): SHA-256 over the bytes, as loaded at import, of bounded/{__init__, members, procedure,
calibrate, generators, run_point}.py and bounded/catalogue.json, plus the loaded-source digests of models.py, analyze.py
and simulate.py (analyze.LOADED_SOURCES, bound by those modules at their own import), and the start recipe table. The
runtime is recorded beside the hash, not in it. Tests (test_*.py) and dev/ drivers are not hashed: they never run inside
a point.
"""
from __future__ import annotations

import os
import sys

for _k in ("NPROC", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_k] = "1"                                   # before jax is imported, whatever the shell says
os.environ.setdefault("JAX_PLATFORMS", "cpu")
sys.dont_write_bytecode = True
_HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(_HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(_HERE))

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import platform  # noqa: E402
import resource  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402

from bounded import members as MB  # noqa: E402
from bounded import procedure as P  # noqa: E402
from bounded import generators as GN  # noqa: E402
from bounded import calibrate as CB  # noqa: F401,E402  (hashed; imported so the hash names loaded code)
import analyze as A  # noqa: E402

SCHEMA = "bounded-row-v1"
HASHED_FILES = ("__init__.py", "members.py", "procedure.py", "calibrate.py", "generators.py", "run_point.py", "catalogue.json")
TIMING_KEYS = ("timing", "cpu_seconds", "wall_seconds")


def _loaded_bytes() -> dict:
    out = {}
    for f in HASHED_FILES:
        with open(os.path.join(_HERE, f), "rb") as fh:
            out[f] = hashlib.sha256(fh.read()).hexdigest()
    return out


LOADED_BOUNDED = _loaded_bytes()                           # bound once, at import


def config_hash() -> str:
    h = hashlib.sha256()
    for f in HASHED_FILES:
        h.update(f"bounded/{f}:{LOADED_BOUNDED[f]}".encode())
    for f in ("models.py", "analyze.py", "simulate.py"):
        if f not in A.LOADED_SOURCES:
            raise RuntimeError(f"no loaded-source digest for {f}")
        h.update(f"{f}:{A.LOADED_SOURCES[f]}".encode())
    h.update(json.dumps(MB.recipe_table(), sort_keys=True).encode())
    return h.hexdigest()[:12]


def runtime() -> dict:
    import jax
    import scipy
    return dict(python=platform.python_version(), jax=jax.__version__, numpy=np.__version__, scipy=scipy.__version__,
                machine=platform.machine(), system=platform.system())


def _clean(v):
    if isinstance(v, dict):
        return {str(k): _clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    if isinstance(v, np.ndarray):
        return _clean(v.tolist())
    if isinstance(v, (np.floating, float)):
        return float(v) if np.isfinite(v) else None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    return v


def _strip_timing(v):
    if isinstance(v, dict):
        return {k: _strip_timing(x) for k, x in v.items() if k not in TIMING_KEYS}
    if isinstance(v, list):
        return [_strip_timing(x) for x in v]
    return v


def deterministic_digest(row: dict) -> str:
    body = _strip_timing({k: v for k, v in row.items() if k != "deterministic_sha256"})
    return hashlib.sha256(json.dumps(body, sort_keys=True, allow_nan=False).encode()).hexdigest()


def run(setting_id: str, replicate: int, namespace: str, lam: float | None = None, cat: dict | None = None,
        members_G=MB.MEMBERS_G, members_X=MB.MEMBERS_X, on_fit=None) -> dict:
    """One row. `lam` is the development boundary value when the catalogue's lambda is not frozen; `members_G/X`
    exist for the quick test tier only (a production row always uses the full member sets)."""
    c0, w0 = time.process_time(), time.monotonic()
    cat = GN.load_catalogue() if cat is None else cat
    s = GN.setting(setting_id, cat)
    seed = GN.dataset_seed(namespace, setting_id, replicate)
    if s["generator"] == "boundary" and s["params"].get("lam") is None and lam is None:
        raise SystemExit("G14 boundary: lambda is not frozen in the catalogue; pass --lam (development namespace only)")
    if lam is not None and namespace != "development":
        raise SystemExit("--lam is a development-only override")
    ds = GN.make(s, seed, lam=lam)
    res = P.point_pipeline(ds.y[:, 0], ds.k, ds.concept, ds.family, seed, members_G=members_G, members_X=members_X,
                           on_fit=on_fit, check_profile=True)
    unavailable = bool(res["unavailable"])
    row = dict(schema=SCHEMA, setting=setting_id, kind=s["kind"], generator=s["generator"], params=s["params"],
               replicate=int(replicate), namespace=namespace, namespace_value=GN.NAMESPACES[namespace], dataset_seed=int(seed),
               boundary_lambda_used=(None if s["generator"] != "boundary" else float(lam if s["params"].get("lam") is None else s["params"]["lam"])),
               config_hash=config_hash(), loaded_sources=dict(bounded=LOADED_BOUNDED, **{f: A.LOADED_SOURCES[f] for f in ("models.py", "analyze.py", "simulate.py")}),
               runtime=runtime(), design=dict(family_counts=list(P.FAMILY_COUNTS), layer=P.LAYER, n_outer=P.N_OUTER, cap=P.CAP,
                                             members_G=list(members_G), members_X=list(members_X), recipe=MB.recipe_table()),
               unavailable=unavailable, unavailable_reason=res.get("reason", ""),
               point=dict(bounded=(None if unavailable else res["T"]), unbounded=(None if unavailable else res["unbounded"]),
                          family_bounded_means=res.get("family_bounded_means"), family_unbounded_means=res.get("family_unbounded_means"),
                          n_clipped_low=res.get("n_clipped_low"), n_clipped_high=res.get("n_clipped_high")),
               folds=res["folds"], n_c=res["n_c"], family=P.family_labels(),
               delta=(None if unavailable else res["delta"]), z=(None if unavailable else res["z"]),
               logq={m: res["logq"][m] for m in tuple(members_G) + tuple(members_X)},
               fits=res["fits"],
               fit_summary=dict(n_fits=len(res["fits"]), n_converged=sum(f["converged"] for f in res["fits"]),
                                n_recovery=sum(f["recovery"] > 0 for f in res["fits"]),
                                starts_by_member={m: sorted({f["n_starts"] for f in res["fits"] if f["member"] == m})
                                                  for m in tuple(members_G) + tuple(members_X)}))
    ru = resource.getrusage(resource.RUSAGE_SELF)
    row["timing"] = dict(point_cpu_seconds=time.process_time() - c0, point_wall_seconds=time.monotonic() - w0,
                         fit_cpu_seconds=float(sum(f["cpu_seconds"] for f in res["fits"])),
                         process_cpu_seconds_total=float(ru.ru_utime + ru.ru_stime),
                         fit_cpu_by_member={m: float(sum(f["cpu_seconds"] for f in res["fits"] if f["member"] == m))
                                            for m in tuple(members_G) + tuple(members_X)},
                         loadavg_at_end=list(os.getloadavg()))
    row = _clean(row)
    row["deterministic_sha256"] = deterministic_digest(row)
    return row


def write_row(row: dict, path: str):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        fh.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--setting", required=True)
    ap.add_argument("--replicate", type=int, required=True)
    ap.add_argument("--namespace", choices=sorted(GN.NAMESPACES), required=True)
    ap.add_argument("--lam", type=float, default=None, help="development-only boundary lambda while the catalogue's is unfrozen")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    row = run(a.setting, a.replicate, a.namespace, lam=a.lam)
    write_row(row, a.out)
    print(f"{a.setting} r{a.replicate} {a.namespace}: T={row['point']['bounded']} U={row['point']['unbounded']} "
          f"unavailable={row['unavailable']} cpu={row['timing']['process_cpu_seconds_total']:.1f}s hash={row['config_hash']}",
          flush=True)


if __name__ == "__main__":
    main()
