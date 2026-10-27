"""Mutate only a scratch copy to test the production module's loaded-source claims."""
import os
import sys
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
T = HERE.parents[2]
SNAP = HERE / "snapshot"
SNAP.mkdir(exist_ok=True)
(SNAP / "bounded").mkdir(exist_ok=True)
for f in ("models.py", "analyze.py", "simulate.py"):
    shutil.copyfile(T / f, SNAP / f)
for f in ("__init__.py", "members.py", "procedure.py", "generators.py", "calibrate.py", "run_point.py", "catalogue.json"):
    shutil.copyfile(T / "bounded" / f, SNAP / "bounded" / f)

CHILD = r'''
import hashlib, json, pathlib
from unittest.mock import patch
import numpy as np
from bounded import members as MB
member_path = pathlib.Path(MB.__file__)
loaded_member_sha = hashlib.sha256(member_path.read_bytes()).hexdigest()
member_path.write_text(member_path.read_text().replace("M3S_START_W = float(np.log(0.3))", "M3S_START_W = float(np.log(0.7))"))
from bounded import run_point as RP, generators as G
import models as M
out = dict(loaded_start_w=MB.M3S_START_W, claimed_member_sha=RP.LOADED_BOUNDED["members.py"],
           actual_loaded_member_sha=loaded_member_sha,
           member_file_sha=hashlib.sha256(member_path.read_bytes()).hexdigest())
def fit(name, train, fold, seed, layer, j=None):
    return M.FitResult(name, np.zeros(M.MEMBERS[name].n_params), -100., True, 8, 8)
with patch.object(MB, "fit_member", fit), patch.object(M, "concept_scores", lambda name, theta, te: np.full(te.n_concepts, -100.)):
    before = RP.run("G13", 0, "development")
    path = pathlib.Path(G.CATALOGUE_PATH)
    cat = json.loads(path.read_text())
    G.setting("G13", cat)["params"]["mu_low"] = -0.2
    path.write_text(json.dumps(cat))
    after = RP.run("G13", 0, "development")
out["catalogue_disk_edit"] = dict(hash_before=before["config_hash"], hash_after=after["config_hash"],
                                   before=before["params"], after=after["params"],
                                   claimed_sha=after["loaded_sources"]["bounded"]["catalogue.json"],
                                   used_sha=hashlib.sha256(path.read_bytes()).hexdigest())
print(json.dumps(out, indent=2, sort_keys=True))
'''
(HERE / "snapshot" / "child_probe.py").write_text(CHILD)
r = subprocess.run([sys.executable, "-B", str(SNAP / "child_probe.py")], cwd=SNAP,
                   env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", NPROC="1"), capture_output=True, text=True)
if r.returncode:
    raise RuntimeError(r.stderr)
(HERE / "provenance-probe.json").write_text(r.stdout)
print(r.stdout)
