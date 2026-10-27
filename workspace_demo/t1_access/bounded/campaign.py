"""bounded/campaign.py — the qualification gates and the attempted-set row ingestion (Codex round 4, B2).

The order-statistic arithmetic of bounded.calibrate is a mathematical helper for whatever banks it is given. This module
is the production boundary in front of it:

 1. Reserved identities. `reserved(namespace)` is the complete attempted set: calibration r = 0..499 for each of the 30
    settings; validation r = 0..399 (graded) or 0..999 (alternative). `ingest` requires exactly one TERMINAL record per
    reserved identity, with the right namespace and dataset seed, the full member/design profile, a deterministic digest
    that verifies, one identity (config hash and identity digest) and the admitted runtime; it rejects missing,
    duplicate, substituted, extra or mixed-identity inputs. Equal VALUES are legitimate ties; duplicate IDENTITIES are not.
 2. Gates. `admit` refuses every calibration/validation identity until the catalogue is SEALED: a finite certified
    boundary lambda with its certificate, all fourteen source-matched gain certificates, the final design/numerical
    policy and the benchmark admission receipt, each a receipt {path, sha256}, and `development_only` false. Validation
    also needs the frozen calibration artifact, which carries the digest of its input-row manifest; every validation row
    carries that artifact's digest and `ingest` checks the link.
 3. Unavailable and crashed attempts. An UNAVAILABLE terminal row (numerical) is an attempt like any other: it holds
    calibration artifact construction and counts as a failure in validation. A CRASHED record, or an attempt record with
    no terminal record, is a code/identity defect: `ingest` raises CampaignHold. Nothing is replaced or deleted.
 4. Attempted-set validation counts with futility stopping: inclusion failures > 21/400 or > 70/1000, graded positive-
    or-unavailable > 11/400, power failures > 160/1000 make that requirement UNATTAINABLE; a requirement PASSES only
    when every reserved attempt of its setting is in (no early success).
"""
from __future__ import annotations

import glob
import hashlib
import json
import os

import numpy as np

from . import calibrate as CB
from . import generators as GN
from . import members as MB
from . import procedure as P

with open(__file__, "rb") as _fh:
    LOADED_SOURCE_DIGEST = hashlib.sha256(_fh.read()).hexdigest()          # bound at this module's own import (B1)

TIMING_KEYS = ("timing", "cpu_seconds", "wall_seconds")
TERMINAL = ("available", "unavailable", "crashed")
SEAL_KEYS = ("boundary_lambda_certificate", "gain_certificates", "design_numerical_policy", "benchmark_admission_receipt")


class QualificationRefused(RuntimeError):
    """A gated identity was requested before its prerequisites are sealed."""


class CampaignHold(RuntimeError):
    """A code/identity defect: the campaign stops, every record is kept."""


class IngestRejected(ValueError):
    """The supplied records are not exactly the reserved attempted set under one identity."""


# ----------------------------------------------------------------------------------------------
# rows
# ----------------------------------------------------------------------------------------------
def strip_timing(v):
    if isinstance(v, dict):
        return {k: strip_timing(x) for k, x in v.items() if k not in TIMING_KEYS}
    if isinstance(v, list):
        return [strip_timing(x) for x in v]
    return v


def deterministic_digest(row: dict) -> str:
    body = strip_timing({k: v for k, v in row.items() if k != "deterministic_sha256"})
    return hashlib.sha256(json.dumps(body, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


# ----------------------------------------------------------------------------------------------
# gates
# ----------------------------------------------------------------------------------------------
def _receipt_ok(r) -> bool:
    if not (isinstance(r, dict) and isinstance(r.get("path"), str) and isinstance(r.get("sha256"), str)
            and len(r["sha256"]) == 64):
        return False
    path = r["path"] if os.path.isabs(r["path"]) else os.path.join(GN.T1, r["path"])
    if not os.path.exists(path):
        return False
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest() == r["sha256"]


def seal_problems(cat: dict) -> list:
    """Everything that keeps this catalogue from being the sealed qualification catalogue."""
    fz = cat.get("freeze") or {}
    out = []
    if fz.get("development_only", True):
        out.append("catalogue is development-only")
    for k in ("boundary_lambda_certificate", "design_numerical_policy", "benchmark_admission_receipt"):
        if not _receipt_ok(fz.get(k)):
            out.append(f"no verified receipt for {k}")
    alts = [s for s in cat["settings"] if s["kind"] == "alternative"]
    certs = fz.get("gain_certificates") or {}
    if len(alts) != 14:
        out.append(f"{len(alts)} alternatives, not 14")
    for s in alts:
        if not s.get("gain_certified") or not _receipt_ok(certs.get(s["id"])):
            out.append(f"{s['id']}: no source-matched gain certificate")
    for s in cat["settings"]:
        if s["generator"] == "boundary":
            lam = s["params"].get("lam")
            if lam is None or not np.isfinite(float(lam)):
                out.append(f"{s['id']}: boundary lambda not certified")
    return out


def require_sealed(cat: dict):
    probs = seal_problems(cat)
    if probs:
        raise QualificationRefused("catalogue not sealed: " + "; ".join(probs))


def admit(namespace: str, cat: dict, artifact: dict | None = None, setting: str | None = None):
    """The gate in front of every point. Development namespaces pass (development use only); calibration needs the sealed
    catalogue; validation needs it AND the frozen calibration artifact of this catalogue."""
    if namespace not in GN.NAMESPACES:
        raise QualificationRefused(f"unknown namespace {namespace!r}")
    if namespace in GN.DEVELOPMENT_NAMESPACES:
        if artifact is not None:
            raise QualificationRefused("a calibration artifact belongs to validation, not development")
        return
    require_sealed(cat)
    if namespace == "calibration":
        if artifact is not None:
            raise QualificationRefused("calibration points take no artifact")
        return
    if artifact is None:
        raise QualificationRefused("validation refused: no frozen calibration artifact")
    verify_artifact(artifact)


# ----------------------------------------------------------------------------------------------
# the attempted set
# ----------------------------------------------------------------------------------------------
def reserved(namespace: str, cat: dict | None = None) -> list:
    return GN.plan_identities(namespace, cat)


def load_records(rows_dir: str) -> tuple:
    """(terminal records, attempt records) from a rows directory: <id>.json terminal, <id>.json.attempt.json attempt."""
    terms, atts = [], []
    for p in sorted(glob.glob(os.path.join(rows_dir, "*.json"))):
        with open(p) as fh:
            rec = json.load(fh)
        rec["_path"] = p
        (atts if p.endswith(".attempt.json") else terms).append(rec)
    return terms, atts


def ingest(records: list, namespace: str, expected: dict, plan: list | None = None, attempts: list = (),
           partial: bool = False, artifact_sha256: str | None = None) -> dict:
    """Check that `records` are exactly the reserved attempted set under one admitted identity.

    expected = dict(config_hash, identity_sha256, runtime). `plan` defaults to reserved(namespace). `partial=True`
    (validation monitoring only) tolerates not-yet-landed identities, never extras, duplicates or mixing. Returns the
    keyed records and the input-row manifest with its digest. Raises CampaignHold on a crashed or orphaned attempt,
    IngestRejected on any other contract breach."""
    plan = reserved(namespace) if plan is None else [tuple(x) for x in plan]
    want = set(plan)
    probs, by, holds = [], {}, []
    for r in records:
        key = (r.get("setting"), r.get("replicate"))
        where = r.get("_path", f"{key}")
        if r.get("status") not in TERMINAL:
            probs.append(f"{where}: not a terminal record"); continue
        if r["status"] == "crashed":
            holds.append(f"{where}: crashed attempt ({(r.get('crash') or {}).get('type')})")
        if key not in want:
            probs.append(f"{where}: identity {key} is not reserved in {namespace} (extra or substituted)"); continue
        if key in by:
            probs.append(f"{where}: duplicate identity {key}"); continue
        by[key] = r
        if r.get("namespace") != namespace:
            probs.append(f"{where}: namespace {r.get('namespace')} != {namespace}")
        if r.get("dataset_seed") != GN.dataset_seed(namespace, key[0], key[1]):
            probs.append(f"{where}: dataset seed is not the reserved one")
        for k in ("config_hash", "identity_sha256", "runtime"):
            if r.get(k) != expected.get(k):
                probs.append(f"{where}: {k} differs from the admitted identity")
        if r["status"] != "crashed":
            d = r.get("design") or {}
            if (d.get("members_G") != list(MB.MEMBERS_G) or d.get("members_X") != list(MB.MEMBERS_X)
                    or d.get("family_counts") != list(P.FAMILY_COUNTS) or d.get("layer") != P.LAYER
                    or d.get("n_outer") != P.N_OUTER):
                probs.append(f"{where}: member/design profile is not the declared one")
        body = {k: v for k, v in r.items() if k != "_path"}
        if r.get("deterministic_sha256") != deterministic_digest(body):
            probs.append(f"{where}: deterministic digest does not verify")
        if artifact_sha256 is not None and r["status"] != "crashed" and r.get("calibration_artifact_sha256") != artifact_sha256:
            probs.append(f"{where}: not linked to the frozen calibration artifact")
    term_keys = set(by)
    for a in attempts:
        key = (a.get("setting"), a.get("replicate"))
        if key in want and key not in term_keys:
            holds.append(f"{a.get('_path', key)}: attempt started with no terminal record (crashed worker)")
    if holds:
        raise CampaignHold("; ".join(holds))
    missing = [k for k in plan if k not in by]
    if missing and not partial:
        probs.append(f"{len(missing)} reserved identities have no terminal record (first: {missing[:3]})")
    if probs:
        raise IngestRejected("; ".join(probs[:20]) + (f" (+{len(probs) - 20} more)" if len(probs) > 20 else ""))
    manifest = [[k[0], k[1], str(by[k]["dataset_seed"]), by[k]["status"], by[k]["deterministic_sha256"]]
                for k in plan if k in by]
    return dict(records=by, manifest=manifest, manifest_sha256=_sha(manifest), missing=missing)


# ----------------------------------------------------------------------------------------------
# calibration freeze and validation tally
# ----------------------------------------------------------------------------------------------
def freeze_calibration(records: list, expected: dict, out_path: str | None = None, plan: list | None = None,
                       attempts: list = (), cat: dict | None = None) -> dict:
    """Ingest the complete calibration attempted set, build the artifact, bind it to its inputs and identity."""
    cat = GN.CATALOGUE.data if cat is None else cat
    if plan is None:
        require_sealed(cat)
    ing = ingest(records, "calibration", expected, plan=plan, attempts=attempts)
    banks = {}
    for (sid, _rep), r in sorted(ing["records"].items()):
        banks.setdefault(sid, []).append(None if r["status"] != "available" else r["point"]["bounded"])
    graded = sorted({s["id"] for s in cat["settings"] if s["kind"] == "graded"} & set(banks))
    art = CB.calibrate(banks, graded)                 # raises (holds) on any unavailable attempt
    art.pop("artifact_sha256", None)
    art.update(input_manifest=ing["manifest"], input_manifest_sha256=ing["manifest_sha256"],
               config_hash=expected["config_hash"], identity_sha256=expected["identity_sha256"],
               runtime=expected["runtime"], catalogue_sha256=GN.CATALOGUE.sha256 if plan is None else None, frozen=True)
    art["artifact_sha256"] = _sha({k: v for k, v in art.items() if k != "artifact_sha256"})
    if out_path:
        if os.path.exists(out_path):
            raise CampaignHold(f"{out_path} exists: a frozen artifact is never overwritten")
        with open(out_path, "w") as fh:
            fh.write(json.dumps(art, sort_keys=True) + "\n")
    return art


def verify_artifact(art: dict) -> dict:
    if not art.get("frozen") or not art.get("input_manifest_sha256"):
        raise QualificationRefused("calibration artifact is not frozen with its input-row manifest")
    if _sha(art["input_manifest"]) != art["input_manifest_sha256"]:
        raise QualificationRefused("calibration artifact's input manifest does not match its digest")
    if _sha({k: v for k, v in art.items() if k != "artifact_sha256"}) != art.get("artifact_sha256"):
        raise QualificationRefused("calibration artifact digest does not verify")
    return art


def load_frozen_artifact(path: str) -> dict:
    with open(path) as fh:
        return verify_artifact(json.load(fh))


def futility_limits(cat: dict | None = None) -> dict:
    t = CB.validation_thresholds()
    return dict(graded_inclusion=t["graded_n"] - t["graded_inclusion_min"],              # 21 of 400
                alternative_inclusion=t["alternative_n"] - t["alternative_inclusion_min"],  # 70 of 1000
                graded_positive_or_unavailable=t["graded_positive_or_unavailable_max"],   # 11 of 400
                power=t["alternative_n"] - t["power_gate_min"])                           # 160 of 1000


def validation_tally(records: list, artifact: dict, expected: dict, plan: list | None = None, attempts: list = (),
                     cat: dict | None = None) -> dict:
    """Attempted-set counts per setting and requirement: UNATTAINABLE once failures exceed the limit, PASS only when every
    reserved attempt of the setting is in and failures are within it, otherwise PENDING. Unavailable = failure."""
    verify_artifact(artifact)
    cat = GN.CATALOGUE.data if cat is None else cat
    ing = ingest(records, "validation", expected, plan=plan, attempts=attempts, partial=True,
                 artifact_sha256=artifact["artifact_sha256"])
    plan = reserved("validation", cat) if plan is None else [tuple(x) for x in plan]
    lim = futility_limits()
    kinds = {s["id"]: s for s in cat["settings"]}
    out = {}
    for sid in sorted({k[0] for k in plan}):
        s = kinds[sid]
        reserved_n = sum(1 for k in plan if k[0] == sid)
        recs = [r for (k0, _), r in ing["records"].items() if k0 == sid]
        cell = artifact["cells"][sid]
        incl_fail = sum(not CB.includes_bracket(r.get("result") or {"status": "unavailable"}, cell) for r in recs)
        reqs = {}

        def judge(name, fails, limit):
            reqs[name] = dict(failures=int(fails), limit=int(limit), attempted=len(recs), reserved=reserved_n,
                              status=("unattainable" if fails > limit else ("pass" if len(recs) == reserved_n else "pending")))
        if s["kind"] == "graded":
            judge("inclusion", incl_fail, lim["graded_inclusion"])
            pos = sum((r.get("result") or {}).get("decision", "unavailable") in ("mixture preference", "unavailable") for r in recs)
            judge("positive_or_unavailable", pos, lim["graded_positive_or_unavailable"])
        else:
            judge("inclusion", incl_fail, lim["alternative_inclusion"])
            if s.get("power_gate"):
                miss = sum((r.get("result") or {}).get("decision") != "mixture preference" for r in recs)
                judge("power", miss, lim["power"])
        out[sid] = reqs
    return dict(settings=out, artifact_sha256=artifact["artifact_sha256"], manifest_sha256=ing["manifest_sha256"],
                any_unattainable=any(q["status"] == "unattainable" for r in out.values() for q in r.values()),
                all_pass=all(q["status"] == "pass" for r in out.values() for q in r.values()))
