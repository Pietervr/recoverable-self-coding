"""The launcher carries the declared interval method and B into the job's environment (review 3, finding 2), checked on
its real --dry-run branch: the printed request must hold INTERVAL and N_BOOT_REFIT, and the job-side Config built
from that environment must hash differently from the cluster default. No AWS call is made (--dry-run prints the
request instead of creating a job)."""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze as A
import simulate as S

py = sys.executable
out = subprocess.run([py, os.path.join(HERE, "launch_t1.py"), "--task", "power", "--run", "envtest", "--dry-run",
                      "--interval", "refit", "--n-boot-refit", "7", "--shards", "2", "--shard-end", "1"],
                     capture_output=True, text=True, env=dict(os.environ, INTERVAL="cluster", N_BOOT_REFIT="1"))
assert out.returncode == 0, out.stderr[-2000:]
spec = json.loads(out.stdout[out.stdout.index("{"):out.stdout.rindex("}") + 1])
env = spec["Environment"]
assert env["INTERVAL"] == "refit" and env["N_BOOT_REFIT"] == "7", env
assert "interval=refit B=7" in out.stdout
# the job builds its Config from exactly these variables (t1_job.py) — the same Config the launcher declared
cfg_job = A.Config(n_starts_inner=int(env["N_STARTS_INNER"]), interval=env["INTERVAL"], n_boot_refit=int(env["N_BOOT_REFIT"]))
assert S.config_hash(cfg_job, 4, (41,), 2026) != S.config_hash(A.Config(n_starts_inner=int(env["N_STARTS_INNER"])), 4, (41,), 2026)
out2 = subprocess.run([py, os.path.join(HERE, "launch_t1.py"), "--task", "power", "--run", "envtest", "--dry-run",
                       "--shards", "2", "--shard-end", "1"], capture_output=True, text=True, env=dict(os.environ, INTERVAL="refit"))
spec2 = json.loads(out2.stdout[out2.stdout.index("{"):out2.stdout.rindex("}") + 1])
assert spec2["Environment"]["INTERVAL"] == "cluster" and spec2["Environment"]["N_BOOT_REFIT"] == "200"   # the CLI, never the host shell
print("launcher: --interval/--n-boot-refit reach the job environment and its Config hash; the host shell's variables do not OK")
