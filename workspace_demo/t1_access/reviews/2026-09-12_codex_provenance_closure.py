"""Full review 8: gain-wrapper provenance across two real interpreter processes.

All numerical gain entries are mocked. Only temporary copies are edited; the
actual job reader uses a fake download client. No optimizer, response simulation
or AWS operation runs.
"""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parents[1]
FAKE_GAIN = """
def _one_gain(name, target, seed, cfg, D):
    return dict(generator=name, kwargs=GAIN_KWARGS[name], target=target, D=D,
                scale=0.5, gain=target, gain_check=target, gain_check_se=target/10,
                calib_converged=True, check_converged=True,
                calib_ref_reproduced=True, check_ref_reproduced=True, note='')
"""
PROBE = r'''
from pathlib import Path
import ast
import json
import os
import sys
from types import SimpleNamespace
from unittest.mock import patch
from botocore.exceptions import ClientError

import analyze as A
import models as M
import simulate as S

root = Path(__file__).resolve().parent
raw = root / "gain_calibration_D4.json"
cfg = A.Config(n_starts_inner=4)
with patch.object(M, "minimize", side_effect=AssertionError("Unexpected optimizer")), \
        patch.object(M, "sample", side_effect=AssertionError("Unexpected response simulation")):
    if sys.argv[1] == "producer":
        before = S.config_hash(cfg, 4, (41,), 2026)
        snapshot = A.numerical_snapshot()
        path = root / "simulate.py"
        source = path.read_text()
        assert source.count("scale=0.5, gain=target,") == 1
        # The current process keeps its loaded gain implementation while another file version appears.
        path.write_text(source.replace("scale=0.5, gain=target,", "scale=0.75, gain=target,"))
        result = S.calibrate_all_gains(2026, cfg)
        assert result["code_hash"] == before == S.config_hash(cfg, 4, (41,), 2026)
        assert A.numerical_snapshot() == snapshot
        assert len(result["entries"]) == 12 and {e["scale"] for e in result["entries"]} == {0.5}
        raw.write_text(json.dumps(result))
        print(json.dumps(dict(producer_retained_hash=True, old_pairs=12, old_scale=0.5)))
    else:
        old_result = json.loads(raw.read_text())
        new_result = S.calibrate_all_gains(2026, cfg)
        assert new_result["code_hash"] != old_result["code_hash"]
        assert len(new_result["entries"]) == 12 and {e["scale"] for e in new_result["entries"]} == {0.75}

        def absent(bucket, key, local):
            raise ClientError({"Error": {"Code": "NoSuchKey", "Message": "mock absence"}}, "GetObject")
        logs = []
        namespace = dict(os=os, D=4, SEED=2026, WORK=str(root), TASK="power",
                         RESULTS_URI="s3://fixture/run/", _bucket="fixture", _prefix="run/",
                         log=logs.append, s3=SimpleNamespace(download_file=absent))
        tree = ast.parse((root / "t1_job.py").read_text())
        for name in ("s3_fetch", "gain_file"):
            fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
            exec(compile(ast.Module(body=[fn], type_ignores=[]), "t1_job.py", "exec"), namespace)
        try:
            namespace["gain_file"](cfg, S, (41,))
        except RuntimeError as error:
            assert "precompute and validate" in str(error)
            assert any(old_result["code_hash"] in line for line in logs)
        else:
            raise AssertionError("The new job accepted the older implementation's gain artefact")
        print(json.dumps(dict(new_hash_differs=True, new_scale=0.75, new_job_refused_old_artefact=True)))
'''
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    for name in ("models.py", "analyze.py", "simulate.py", "t1_job.py"):
        (root / name).write_bytes((HERE / name).read_bytes())
    path = root / "simulate.py"
    path.write_text(path.read_text() + FAKE_GAIN)
    probe = root / "probe.py"
    probe.write_text(PROBE)
    environment = dict(os.environ, NPROC="1")
    for mode in ("producer", "consumer"):
        result = subprocess.run([sys.executable, str(probe), mode], capture_output=True,
                                text=True, cwd=root, env=environment)
        assert result.returncode == 0, result.stderr
        output = json.loads(result.stdout.strip().splitlines()[-1])
        print(mode + ": " + json.dumps(output, sort_keys=True))
