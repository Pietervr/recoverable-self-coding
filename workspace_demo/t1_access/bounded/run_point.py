#!/usr/bin/env python3
"""bounded/run_point.py — one (setting, replicate, namespace) of the qualification catalogue -> one terminal record.

    cd workspace_demo/t1_access
    NPROC=1 .venv/bin/python -m bounded.run_point --setting G03 --replicate 0 --namespace development --out row.json

The row: the setting and its resolved parameters, the dataset seed, the outer folds, the bounded statistic T and the
unbounded mean U, per-concept d_c and z_c, every member's held-out joint log score per concept (full precision), per-fit
convergence / starts / recovery / log-likelihood / parameters / CPU, the status (available | unavailable | crashed) and
reason, the identity and the configuration hash. Deterministic given (setting, replicate, namespace) under one
identity: every field outside `timing` and the per-fit `cpu_seconds` / `wall_seconds` is a function of those;
`deterministic_sha256` is the SHA-256 of the row's canonical JSON with those timing fields removed. That is equality on
the same frozen runtime, not a promise across numerical environments.

Identity (B1, Codex round 4). `identity()` is assembled at CALL time from values bound at each module's OWN import:
  * every bounded module's LOADED_SOURCE_DIGEST (__init__, members, procedure, calibrate, generators, campaign, run_point),
  * the catalogue's digest - the SHA-256 of the very bytes that generators parsed at import (generators.CATALOGUE),
  * the audited files' loaded digests and the EFFECTIVE numerical settings and runtime, analyze.numerical_snapshot()
    (model globals read at call time, so a live change of a numerical global changes the identity),
  * the bounded procedure's effective constants (cap, folds, layer, strata, members, start recipe, seed rule),
  * the machine and system.
`config_hash` = the first 12 hex of the SHA-256 of that identity's canonical JSON. A disk edit after import changes
nothing that runs and nothing reported; a new process loading edited files gets a new identity. There is no catalogue
override in the production API.

Gates (B2): calibration and validation identities are refused until the catalogue is sealed (bounded.campaign.admit);
validation also needs the frozen calibration artifact (`--artifact`), whose digest every validation row carries.
Attempts (B2.3): `attempt()` writes `<out>.attempt.json` durably BEFORE the point starts; the terminal record replaces
nothing and is written to `<out>`. A known numerical exception (FloatingPointError, numpy LinAlgError) is an
UNAVAILABLE terminal row; any other exception is a CRASHED terminal record (a code/identity defect: the campaign
assembler holds on it) and the process exits 2. Tests (test_*.py) and dev/ drivers are not in the identity.
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
import traceback  # noqa: E402

import numpy as np  # noqa: E402

import bounded as BPKG  # noqa: E402
from bounded import members as MB  # noqa: E402
from bounded import procedure as P  # noqa: E402
from bounded import generators as GN  # noqa: E402
from bounded import calibrate as CB  # noqa: E402
from bounded import campaign as CP  # noqa: E402
import analyze as A  # noqa: E402

with open(__file__, "rb") as _fh:
    LOADED_SOURCE_DIGEST = hashlib.sha256(_fh.read()).hexdigest()          # bound at this module's own import (B1)

SCHEMA = "bounded-row-v2"
KNOWN_NUMERICAL = (FloatingPointError, np.linalg.LinAlgError)
deterministic_digest = CP.deterministic_digest
_strip_timing = CP.strip_timing


def identity() -> dict:
    """The point implementation's identity, assembled now from import-bound digests and effective settings."""
    snap = A.numerical_snapshot()
    return dict(
        schema=SCHEMA,
        bounded_sources={"__init__.py": BPKG.LOADED_SOURCE_DIGEST, "members.py": MB.LOADED_SOURCE_DIGEST,
                         "procedure.py": P.LOADED_SOURCE_DIGEST, "calibrate.py": CB.LOADED_SOURCE_DIGEST,
                         "generators.py": GN.LOADED_SOURCE_DIGEST, "campaign.py": CP.LOADED_SOURCE_DIGEST,
                         "run_point.py": LOADED_SOURCE_DIGEST},
        catalogue_sha256=GN.CATALOGUE.sha256,
        numerical=snap,
        procedure=dict(cap=P.CAP, n_outer=P.N_OUTER, layer=P.LAYER, family_counts=list(P.FAMILY_COUNTS),
                       members_G=list(MB.MEMBERS_G), members_X=list(MB.MEMBERS_X), recipe=MB.recipe_table(),
                       seed_rule=GN.SEED_RULE, namespaces=dict(GN.NAMESPACES)),
        platform=dict(machine=platform.machine(), system=platform.system()))


def identity_sha256(ident: dict | None = None) -> str:
    ident = identity() if ident is None else ident
    return hashlib.sha256(json.dumps(ident, sort_keys=True, default=str).encode()).hexdigest()


def config_hash(ident: dict | None = None) -> str:
    return identity_sha256(ident)[:12]


def runtime() -> dict:
    return dict(A.numerical_snapshot()["runtime"], machine=platform.machine(), system=platform.system())


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


def _base(setting_id, replicate, namespace, s, seed, ident, lam_used, members_G, members_X, artifact) -> dict:
    return dict(schema=SCHEMA, setting=setting_id, kind=s["kind"], generator=s["generator"], params=s["params"],
                resolved=s.get("resolved"), replicate=int(replicate), namespace=namespace,
                namespace_value=GN.NAMESPACES[namespace], dataset_seed=int(seed), boundary_lambda_used=lam_used,
                config_hash=config_hash(ident), identity_sha256=identity_sha256(ident), identity=ident, runtime=runtime(),
                design=dict(family_counts=list(P.FAMILY_COUNTS), layer=P.LAYER, n_outer=P.N_OUTER, cap=P.CAP,
                            members_G=list(members_G), members_X=list(members_X), recipe=MB.recipe_table()),
                calibration_artifact_sha256=(artifact["artifact_sha256"] if artifact else None))


def _finish(row: dict, c0: float, w0: float, fits=()) -> dict:
    ru = resource.getrusage(resource.RUSAGE_SELF)
    row["timing"] = dict(point_cpu_seconds=time.process_time() - c0, point_wall_seconds=time.monotonic() - w0,
                         fit_cpu_seconds=float(sum(f["cpu_seconds"] for f in fits)),
                         process_cpu_seconds_total=float(ru.ru_utime + ru.ru_stime),
                         fit_cpu_by_member={m: float(sum(f["cpu_seconds"] for f in fits if f["member"] == m))
                                            for m in sorted({f["member"] for f in fits})},
                         loadavg_at_end=list(os.getloadavg()))
    row = _clean(row)
    row["deterministic_sha256"] = deterministic_digest(row)
    return row


def _prepare(setting_id, replicate, namespace, lam, members_G, members_X, artifact):
    s = GN.setting(setting_id)
    CP.admit(namespace, GN.CATALOGUE.data, artifact=artifact, setting=setting_id)
    reduced = (tuple(members_G), tuple(members_X)) != (MB.MEMBERS_G, MB.MEMBERS_X)
    if reduced and namespace not in GN.DEVELOPMENT_NAMESPACES:
        raise CP.QualificationRefused("reduced member sets are a development test hook only")
    if lam is not None and namespace not in GN.DEVELOPMENT_NAMESPACES:
        raise CP.QualificationRefused("--lam is a development-only override")
    if s["generator"] == "boundary" and s["params"].get("lam") is None and lam is None:
        raise CP.QualificationRefused("G14 boundary: lambda is not frozen in the catalogue; pass --lam (development only)")
    lam_used = None if s["generator"] != "boundary" else float(lam if s["params"].get("lam") is None else s["params"]["lam"])
    return s, GN.dataset_seed(namespace, setting_id, replicate), lam_used


def run(setting_id: str, replicate: int, namespace: str, lam: float | None = None, artifact: dict | None = None,
        members_G=MB.MEMBERS_G, members_X=MB.MEMBERS_X, on_fit=None) -> dict:
    """One terminal row (available or unavailable). Raises QualificationRefused before any work when gated; a known
    numerical exception becomes an UNAVAILABLE row; any other exception propagates (attempt() records it as CRASHED)."""
    c0, w0 = time.process_time(), time.monotonic()
    ident = identity()
    s, seed, lam_used = _prepare(setting_id, replicate, namespace, lam, members_G, members_X, artifact)
    row = _base(setting_id, replicate, namespace, s, seed, ident, lam_used, members_G, members_X, artifact)
    try:
        ds = GN.make(s, seed, lam=lam)
        res = P.point_pipeline(ds.y[:, 0], ds.k, ds.concept, ds.family, seed, members_G=members_G, members_X=members_X,
                               on_fit=on_fit, check_profile=True)
    except KNOWN_NUMERICAL as e:
        row.update(status="unavailable", unavailable=True, unavailable_reason=f"numerical exception {type(e).__name__}: {e}",
                   point=dict(bounded=None, unbounded=None))
        return _finish(row, c0, w0)
    unavailable = bool(res["unavailable"])
    row.update(status="unavailable" if unavailable else "available", unavailable=unavailable,
               unavailable_reason=res.get("reason", ""),
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
    if artifact is not None:
        row["result"] = CB.apply(None if unavailable else res["T"], artifact, available=not unavailable)
    return _finish(row, c0, w0, res["fits"])


def _durable_write(obj: dict, path: str):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        fh.write(json.dumps(obj, sort_keys=True, allow_nan=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


write_row = _durable_write


def attempt(setting_id: str, replicate: int, namespace: str, out: str, lam: float | None = None,
            artifact: dict | None = None, **kw) -> dict:
    """Run one identity with a durable attempt record. Returns the terminal record (also written to `out`)."""
    if os.path.exists(out) or os.path.exists(out + ".attempt.json"):
        raise CP.CampaignHold(f"{out}: this identity already has an attempt; never re-run or replace an attempt")
    seed = GN.dataset_seed(namespace, setting_id, replicate)
    _durable_write(dict(schema=SCHEMA, kind="attempt", status="started", setting=setting_id, replicate=int(replicate),
                        namespace=namespace, dataset_seed=int(seed), config_hash=config_hash(),
                        started=time.strftime("%Y-%m-%dT%H:%M:%S%z"), pid=os.getpid()), out + ".attempt.json")
    c0, w0 = time.process_time(), time.monotonic()
    try:
        row = run(setting_id, replicate, namespace, lam=lam, artifact=artifact, **kw)
    except CP.QualificationRefused:
        os.remove(out + ".attempt.json")              # refused before any work: not an attempt
        raise
    except Exception as e:                            # a code or identity defect: CRASHED, the campaign holds
        ident = identity()
        row = dict(schema=SCHEMA, setting=setting_id, replicate=int(replicate), namespace=namespace,
                   dataset_seed=int(seed), config_hash=config_hash(ident), identity_sha256=identity_sha256(ident),
                   runtime=runtime(), status="crashed", unavailable=True,
                   crash=dict(type=type(e).__name__, message=str(e), traceback=traceback.format_exc()))
        row = _finish(row, c0, w0)
        _durable_write(row, out)
        return row
    _durable_write(row, out)
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--setting", required=True)
    ap.add_argument("--replicate", type=int, required=True)
    ap.add_argument("--namespace", choices=sorted(GN.NAMESPACES), required=True)
    ap.add_argument("--lam", type=float, default=None, help="development-only boundary lambda while the catalogue's is unfrozen")
    ap.add_argument("--artifact", default=None, help="the frozen calibration artifact (validation only)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    art = CP.load_frozen_artifact(a.artifact) if a.artifact else None
    try:
        row = attempt(a.setting, a.replicate, a.namespace, a.out, lam=a.lam, artifact=art)
    except CP.QualificationRefused as e:
        print(f"REFUSED: {e}", file=sys.stderr, flush=True)
        sys.exit(3)
    print(f"{a.setting} r{a.replicate} {a.namespace}: status={row['status']} T={row.get('point', {}).get('bounded')} "
          f"cpu={row['timing']['process_cpu_seconds_total']:.1f}s hash={row['config_hash']}", flush=True)
    sys.exit(2 if row["status"] == "crashed" else 0)


if __name__ == "__main__":
    main()
