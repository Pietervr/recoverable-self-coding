"""prod_userdata.sh lifecycle tests (Codex 0483db4 V10-3, V10-7, V10-8), on the script text itself (bash >= 4; no AWS,
no science):
  V10-3  the bundle inventory command, extracted VERBATIM, is run on a synthetic instance tree; afterwards the mutable
         transport diagnostics are written exactly as the script does (userdata.log appended by tee, upload_verify.json,
         stop_seen.txt, spot_notice.json) and the Lengau ingestion's check_bundle must report no checksum or unlisted
         problem; a frozen file changed after hashing must still be caught.
  V10-8  `stop_seen` / `stop_before_start` run before job-start AND before the first worker; the poller's AWS calls are
         bounded (timeout 20) and its interval is 60 s; the S3 check fails closed on an answer that is neither 0 nor 1.
  V10-7  memory.txt is sampled in the supervision loop BEFORE the bundle is hashed (frozen evidence for the memory gate).
    python3 tests/test_prod_userdata.py"""
import json, os, re, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE); sys.path[:0] = [PKG, os.path.join(PKG, "..", "chpc")]
UD = open(os.path.join(PKG, "prod_userdata.sh")).read()
BASH = "/opt/homebrew/bin/bash" if os.path.exists("/opt/homebrew/bin/bash") else "bash"
ok = True
def check(n, c, x=""):
    global ok; ok &= bool(c); print(("PASS " if c else "FAIL ") + n + (f"  [{x}]" if x and not c else ""))

# --- V10-3: the real hashing command, then the real post-hash writers ---
start = UD.index("(cd $W && find root env -type f"); end = UD.index("|| echo \"bundle checksum list failed\"")
cmd = UD[start:end].rstrip().rstrip("\\").rstrip()
W = tempfile.mkdtemp()
for rel, body in (("root/records/rep3/rec_199.json", "{}"), ("root/timing/rep3/t_199.json", "{}"), ("root/status/jobX.slot0.json", "{}"),
                  ("root/task_3.json", "{}"), ("env/plan.json", "{}"), ("env/outcomes.json", "{}"), ("env/attest_B.json", "{}"),
                  ("env/memory.txt", "1 2 3 4\n"), ("env/userdata.log", "boot\n"), ("env/x.tmp.123", "partial")):
    p = os.path.join(W, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(body)
r = subprocess.run([BASH, "-c", f"set -uo pipefail; W={W}; {cmd}"], capture_output=True, text=True)
listed = [l.split("  ", 1)[1] for l in open(os.path.join(W, "BUNDLE_SHA256SUMS")).read().splitlines()] if r.returncode == 0 else []
check("the verbatim hashing command lists frozen evidence only", r.returncode == 0 and "env/userdata.log" not in listed and "env/memory.txt" in listed
      and not any(".tmp" in x for x in listed) and "root/records/rep3/rec_199.json" in listed, (r.stderr, listed))
# the script's own post-hash writers
open(os.path.join(W, "env", "userdata.log"), "a").write("end 2026-10-11T00:00:00Z\ntransfer disposition: verified=true\n")
json.dump({"transfer_verified": True}, open(os.path.join(W, "env", "upload_verify.json"), "w"))
open(os.path.join(W, "env", "stop_seen.txt"), "w").write("2026-10-11T00:00:00Z\n")
open(os.path.join(W, "env", "spot_notice.json"), "w").write("{}\n")
import row19_ec2_ingest as IG
probs = []
sums = os.path.join(W, "BUNDLE_SHA256SUMS")
listed_map = dict((l.split("  ", 1)[1], l.split("  ", 1)[0]) for l in open(sums).read().splitlines())
present = {os.path.relpath(os.path.join(dp, f), W) for dp, _, fs in os.walk(W) for f in fs if os.path.relpath(dp, W).split(os.sep)[0] in ("root", "env")}
unlisted = sorted(x for x in present - set(listed_map) if x not in IG.MUTABLE and ".tmp." not in x)
changed = [f for f, h in listed_map.items() if IG.sha_file(os.path.join(W, f)) != h]
check("after the post-hash writers: no unlisted frozen file and no checksum difference (V10-3 lifecycle)", unlisted == [] and changed == [], (unlisted, changed))
open(os.path.join(W, "env", "plan.json"), "w").write('{"changed": 1}')
check("a frozen file changed after hashing is still caught", any(IG.sha_file(os.path.join(W, f)) != h for f, h in listed_map.items()))

# --- V10-8: STOP checkpoints, bounded polling, fail closed ---
i_stop1 = UD.index('stop_seen && stop_before_start "before job-start"'); i_js = UD.index("chpc/row19_shard.py job-start")
i_stop2 = UD.index('stop_seen && stop_before_start "before the first worker"'); i_w = UD.index("while read slot rep idx; do")
check("STOP is checked before job-start and again before the first worker starts", i_stop1 < i_js < i_stop2 < i_w)
poll = UD[UD.index("( while true; do                         # common STOP"):UD.index('DECLARED=$(wc -l')]
check("the poller's S3 calls are bounded (timeout 20) at a 60 s interval, run and global keys",
      "timeout 20 aws s3 ls" in poll and "sleep 60" in poll and "aws_bench/$RUN/STOP" in poll and '"$B/code/t1_access/aws_bench/STOP"' in poll)
fn = UD[UD.index("stop_seen() {"):UD.index("stop_before_start() {")]
check("stop_seen fails closed on an S3 answer that is neither found (0) nor absent (1)", "[ $rc -eq 1 ] || die" in fn and "timeout 20 aws s3 ls" in fn)
# run stop_seen itself against a fake `aws` and `timeout` on PATH
B = tempfile.mkdtemp(); fake = os.path.join(B, "bin"); os.makedirs(fake)
open(os.path.join(fake, "timeout"), "w").write('#!/bin/bash\nshift; exec "$@"\n')
open(os.path.join(fake, "aws"), "w").write('#!/bin/bash\nexit "${AWS_RC:-1}"\n')
for f in ("timeout", "aws"):
    os.chmod(os.path.join(fake, f), 0o755)
def stop_seen(rc, root_stop=False):
    rl = tempfile.mkdtemp()
    if root_stop:
        open(os.path.join(rl, "STOP"), "w").write("x")
    s = f'set -uo pipefail; B=s3://b; RUN=r; ROOT_LIVE={rl}; die() {{ echo DIED; exit 9; }}\n{fn}\nstop_seen; echo "rc=$?"'
    p = subprocess.run([BASH, "-c", s], capture_output=True, text=True, env=dict(os.environ, PATH=f"{fake}:{os.environ['PATH']}", AWS_RC=str(rc)))
    return p.stdout.strip()
check("stop_seen: S3 absent (1) -> no STOP", stop_seen(1) == "rc=1", stop_seen(1))
check("stop_seen: S3 found (0) -> STOP", stop_seen(0) == "rc=0", stop_seen(0))
check("stop_seen: S3 error (255) -> dies (no fit starts on an unknown STOP state)", stop_seen(255) == "DIED", stop_seen(255))
check("stop_seen: the instance root STOP alone -> STOP", stop_seen(1, root_stop=True) == "rc=0")

# --- V10-7: memory sampled in the loop, before hashing ---
i_mem = UD.index('>> $W/env/memory.txt'); i_hash = UD.index("(cd $W && find root env -type f")
check("memory.txt is sampled in the supervision loop before the bundle is hashed", UD.index("while true; do\n  n=$(ls $W/exits") < i_mem < i_hash)
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
