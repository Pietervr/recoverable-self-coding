"""Read-only round-4 audit probes. Writes results only beside this script."""
import os
import sys
from pathlib import Path

os.environ["NPROC"] = "1"
sys.dont_write_bytecode = True
T = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(T))

import copy
import hashlib
import json
from collections import defaultdict
from unittest.mock import patch

import numpy as np
from bounded import generators as G, procedure as P, members as MB, calibrate as C, run_point as R
import models as M
import analyze as A

out = {"config_hash": R.config_hash(), "runtime": R.runtime()}
inputs = [T / "reviews/2026-10-27_method_repair_codex_record.md",
          T / "reviews/2026-10-27_interval_diagnosis_codex_record.md",
          T / "bounded/DESIGN_bounded_v1.md", T / "bounded/dev/smoke.json"]
inputs += [Path("/Users/pietervanrooyen/Unimog-Projects/papers/adaptive_agency_special_issue/sections") / f
           for f in ("methods.tex", "results.tex")]
out["input_sha256"] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
cat = G.load_catalogue()
ids = defaultdict(list)
for s in cat["settings"]:
    for ns in ("development", "calibration", "validation"):
        n = 1 if ns == "development" else s["attempts"][ns]
        for rep in range(n):
            ids[G.dataset_seed(ns, s["id"], rep)].append([ns, s["id"], rep])
out["seed_counts"] = {"identities": sum(map(len, ids.values())), "unique": len(ids)}
out["seed_collisions"] = {str(k): v for k, v in ids.items() if len(v) > 1}
excluded = set(range(271001, 271006)) | set(range(271010, 271313))
out["excluded_seed_hits"] = {str(k): v for k, v in ids.items() if k in excluded}

smoke = json.loads((T / "bounded/dev/smoke.json").read_text())
checks = []
cpu = []
for sid, entry in smoke["settings"].items():
    path = T / entry["row"]
    row = json.loads(path.read_text())
    res = P.assemble(row["logq"], row["n_c"], row["family"])
    checks.append({"setting": sid,
                   "file_hash_ok": hashlib.sha256(path.read_bytes()).hexdigest() == entry["row_sha256"],
                   "digest_ok": R.deterministic_digest(row) == row["deterministic_sha256"] == entry["deterministic_sha256"],
                   "config_ok": row["config_hash"] == R.config_hash(),
                   "sources_ok": row["loaded_sources"] == dict(bounded=R.LOADED_BOUNDED, **{f: A.LOADED_SOURCES[f] for f in ("models.py", "analyze.py", "simulate.py")}),
                   "seed_ok": row["dataset_seed"] == G.dataset_seed("development", sid, 0),
                   "T_difference": float(res["T"] - row["point"]["bounded"]),
                   "fit_count": len(row["fits"]),
                   "starts_ok": all(f["n_starts"] == (72 if f["member"] == "M2S" else 8) for f in row["fits"]),
                   "fold_sizes": list(map(len, row["folds"]))})
    cpu.append(entry["process_cpu_seconds"])
out["smoke_checks"] = checks
out["smoke_cpu"] = dict(total=sum(cpu), mean=np.mean(cpu), median=np.median(cpu), min=min(cpu), max=max(cpu))

# A complete 30-setting bank is not enforced: raw-vector core accepts one arbitrary bank.
art = C.calibrate({"G01": [0.001] * 500}, ["G01"])
out["incomplete_calibration_accepted"] = dict(n_settings=art["n_settings"], guarantees=art["guarantees"],
                                                source_keys=sorted(art.keys()))
out["wrong_cap_accepted_by_constructor"] = C.calibrate({"G01": [0.001] * 500}, ["G01"], cap=0.01)["cap"]

# Fake fitting keeps the probes cheap, while still exercising the production point and row assembly.
def fake_fit(name, train, fold, seed, layer, j=None):
    return M.FitResult(name, np.zeros(M.MEMBERS[name].n_params), -100., True, 8, 8)

def fake_score(name, theta, te):
    return np.full(te.n_concepts, -100.)

with patch.object(MB, "fit_member", fake_fit), patch.object(M, "concept_scores", fake_score):
    original = R.run("G13", 0, "development")
    amended = copy.deepcopy(cat)
    G.setting("G13", amended)["params"]["mu_low"] = -0.2
    changed = R.run("G13", 0, "development", cat=amended)
    out["runtime_catalogue_hash_probe"] = dict(hash_before=original["config_hash"], hash_after=changed["config_hash"],
                                               params_before=original["params"], params_after=changed["params"])
    uncertified = R.run("A13", 0, "calibration")
    premature_validation = R.run("G01", 0, "validation")
    out["qualification_gate_probe"] = dict(
        calibration_returned=uncertified["namespace"] == "calibration",
        alternative_gain_certified=G.setting("A13")["gain_certified"],
        catalogue_boundary_lambda=G.setting("G14")["params"]["lam"],
        validation_returned=premature_validation["namespace"] == "validation",
        frozen_interval_artifact_required=False)

th = G.make(G.setting("A14"), 12).meta["theta_m3s"]
out["generic_M3S_components_probe"] = dict(
    catch_occupancy=float(M.components("M3S", th, np.array([0.]), u=1.)["A"][0]),
    scale_at_u0=float(M.components("M3S", th, np.array([0.]), u=0.)["sigma_low"][0]),
    scale_at_u1=float(M.components("M3S", th, np.array([0.]), u=1.)["sigma_low"][0]))

def bad_ll_fit(name, train, fold, seed, layer, j=None):
    r = fake_fit(name, train, fold, seed, layer, j)
    r.loglik = -np.inf
    r.converged = False
    r.n_converged = 0
    r.recovery = 2
    return r

ds = G.make(G.setting("G01"), 21)
with patch.object(M, "concept_scores", fake_score):
    result = P.point_pipeline(ds.y[:, 0], ds.k, ds.concept, ds.family, 21,
                              members_G=("M2B",), members_X=("M3",), fit_member=bad_ll_fit)
out["nonfinite_loglik_probe"] = dict(unavailable=result["unavailable"], first_fit=result["fits"][0])

def raising_fit(*args, **kwargs):
    raise FloatingPointError("injected numerical failure")

try:
    P.point_pipeline(ds.y[:, 0], ds.k, ds.concept, ds.family, 21,
                     members_G=("M2B",), members_X=("M3",), fit_member=raising_fit)
except Exception as exc:
    out["numerical_exception_probe"] = dict(exception=type(exc).__name__, message=str(exc), unavailable_record=False)

(Path(__file__).parent / "audit_build.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: v for k, v in out.items() if k != "smoke_checks"}, indent=2, sort_keys=True))
print("smoke checks:", all(all(v for k, v in x.items() if k.endswith("_ok")) and x["T_difference"] == 0 for x in checks))
