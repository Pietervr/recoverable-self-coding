"""Implementation provenance is bound at load (Codex, 12 Sept 2026, reviews 6 and 7): the checkpoint identity, the row /
gain-file code hash and the numerical snapshot name the code that was actually loaded. Checked with REAL disk edits in
a temporary copy of the three modules: after import, every file is edited on disk — the loaded implementation's
identity, hash and snapshot do not move; a fresh interpreter loading the edited files gets other values; models.py
binds its own digest at its own import (no later disk fallback). Nothing is fitted."""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PROBE = r'''
import json, os, sys
sys.path.insert(0, sys.argv[1])
import models as M
import analyze as A
import simulate as S
import numpy as np
def state():
    cfg = A.Config()
    ds = A.Dataset(y=np.zeros((8 * 6 * 7, 1)), k=np.tile(np.repeat(np.arange(7.0), 6), 8), concept=np.repeat(np.arange(8), 42),
                   family=np.arange(8), layers=np.array([41]))
    folds = A.stratified_folds(ds.family, 5, 1)
    return dict(models=M.LOADED_SOURCE_DIGEST, snapshot=A.numerical_snapshot()["files"], hash=S.config_hash(cfg, 4, (41,), 1),
                ident=A.dataset_identity(ds, cfg, 1, 3, folds))
before = state()
for f in ("models.py", "analyze.py", "simulate.py"):          # edit every file ON DISK after loading
    with open(os.path.join(sys.argv[1], f), "a") as fh:
        fh.write("\n# edited on disk after loading\n")
after = state()
print(json.dumps(dict(before=before, after=after)))
'''
with tempfile.TemporaryDirectory() as d:
    for f in ("models.py", "analyze.py", "simulate.py"):
        shutil.copy(os.path.join(HERE, f), os.path.join(d, f))
    env = dict(os.environ, NPROC="1")
    r1 = subprocess.run([sys.executable, "-c", PROBE, d], capture_output=True, text=True, env=env, cwd=d)
    assert r1.returncode == 0, r1.stderr[-3000:]
    import json
    out1 = json.loads(r1.stdout.strip().splitlines()[-1])
    b, a = out1["before"], out1["after"]
    assert a == b, "a disk edit after loading moved the loaded implementation's identity"
    assert set(b["snapshot"]) == {"models.py", "analyze.py", "simulate.py"} and b["snapshot"]["models.py"] == b["models"]
    # a fresh interpreter loads the edited files: every provenance value differs
    r2 = subprocess.run([sys.executable, "-c", PROBE, d], capture_output=True, text=True, env=env, cwd=d)
    assert r2.returncode == 0, r2.stderr[-3000:]
    out2 = json.loads(r2.stdout.strip().splitlines()[-1])["before"]
    assert out2["models"] != b["models"] and out2["hash"] != b["hash"] and out2["ident"] != b["ident"]
    assert all(out2["snapshot"][f] != b["snapshot"][f] for f in b["snapshot"])
    # models.py bound at its own load: import models, edit it on disk, THEN import analyze — analyze reports the loaded digest
    probe2 = r'''
import os, sys
sys.path.insert(0, sys.argv[1])
import models as M
d0 = M.LOADED_SOURCE_DIGEST
with open(os.path.join(sys.argv[1], "models.py"), "a") as fh:
    fh.write("\n# edited between the two imports\n")
import analyze as A
print(A.LOADED_SOURCES["models.py"] == d0, A.loaded_source_digest(M.__file__) != d0)
'''
    r3 = subprocess.run([sys.executable, "-c", probe2, d], capture_output=True, text=True, env=env, cwd=d)
    assert r3.returncode == 0 and r3.stdout.strip().splitlines()[-1] == "True True", (r3.stdout, r3.stderr[-2000:])
print("loaded provenance: disk edits after loading move nothing; a fresh load differs in digest, hash and identity; "
      "models binds its own digest before analyze can look OK")
