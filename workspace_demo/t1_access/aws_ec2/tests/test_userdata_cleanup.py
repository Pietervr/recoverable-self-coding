"""Synthetic test of bench_userdata.sh's run()/cleanup blocks, extracted verbatim (bash >= 4; no AWS, no science):
a normal process, one that ignores TERM, and one with a child; the cleanup must finish inside its global bound, leave no
survivor, publish the normal exit code atomically and list the others as censored. python3 tests/test_userdata_cleanup.py"""
import os, re, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__)); UD = open(os.path.join(os.path.dirname(HERE), "bench_userdata.sh")).read()
BASH = "/opt/homebrew/bin/bash" if os.path.exists("/opt/homebrew/bin/bash") else "bash"
run_def = UD[UD.index("declare -A PIDS"):UD.index("for arm in A B; do\n  if [ $arm = A ]; then E=(\"${ARM_A[@]}\"); else E=(\"${ARM_B[@]}\"); fi\n  mkdir -p $W/row6_$arm")]
cleanup = UD[UD.index('for n in "${!PIDS[@]}"; do [ -f $W/exits/$n.code ] || echo $n; done'):UD.index('python3 - $W <<\'PY\'')]
cleanup = cleanup.replace("CLEAN_END=$(( $(date +%s) + 120 ))", "CLEAN_END=$(( $(date +%s) + 12 ))")   # shortened bound for the test
W = tempfile.mkdtemp()
script = f"""set -uo pipefail
W={W}; mkdir -p $W/exits $W/logs $W/env
{run_def}
run good /tmp true
run stubborn /tmp bash -c 'trap "" TERM; sleep 1000'
run parent /tmp bash -c 'sleep 1000 & wait'
sleep 2
{cleanup}
"""
t = time.time(); p = subprocess.run([BASH, "-c", script], capture_output=True, text=True, timeout=60); dt = time.time() - t
cens = open(os.path.join(W, "env", "censored.txt")).read().split(); unres = open(os.path.join(W, "env", "unresolved.txt")).read().split()
good = open(os.path.join(W, "exits", "good.code")).read().strip() if os.path.exists(os.path.join(W, "exits", "good.code")) else None
stray = subprocess.run(["pgrep", "-f", "sleep 1000"], capture_output=True, text=True).stdout.split()
tmpfiles = [f for f in os.listdir(os.path.join(W, "exits")) if f.startswith(".")]
ok = (good == "0" and sorted(cens) == ["parent", "stubborn"] and not unres and not stray and dt < 20 and not tmpfiles)
print(p.stdout.strip().splitlines()[-1] if p.stdout.strip() else p.stderr[-300:])
print(f"{'PASS' if ok else 'FAIL'} cleanup: good={good} censored={cens} unresolved={unres} stray={stray} {dt:.1f} s (bound 12 s + poll)")
sys.exit(0 if ok else 1)
