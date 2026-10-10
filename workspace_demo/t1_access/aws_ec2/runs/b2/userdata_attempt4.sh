#!/bin/bash
# Ledger row 23 (rsc_t1_simulation_design.md section 12), revision 2 after Codex RSC 2cc26ee: the EC2 parity and timing
# benchmark as the instance's user-data on ONE spot c7a.24xlarge (us-west-2). The Lengau toolchain BYTES are installed at
# the Lengau path (t1py sha256 f9c3ff02 = the manifest's wrapper pin). Two arms run side by side, each through its own
# BENCHMARK-ONLY operational manifest (bench/manifest_{A,B}.json: only root, campaign, cores 36, expect_layer_s 68,400
# differ from the production 43b75f94), each admitted by the unchanged row19_shard.py job-start (bindings published):
#   A          the Lengau runtime; models.py's XLA baseline flags by its own setdefault; Zen 4 dispatch free;
#   B_full     A's baseline XLA flags PLUS --xla_cpu_max_isa=AVX2, OPENBLAS_CORETYPE=Haswell, numpy AVX-512 masked;
#   B_nomask   the distinctly named fallback when numpy refuses the mask (never reported as B_full).
# Stage 1: row 6 panel (3 sens600 datasets, f7e69b1) per arm. Stage 2: worker at index 0 of reps 3..38 per arm.
# Every prerequisite fails closed (FAILED file, bounded upload, shutdown). Every declared process gets a recorded outcome
# (exit code, or censored at the upload deadline). Costed window: HARD = boot + 77400 s; two independent timers
# are installed and checked first; the Mac-side reaper (bench_reaper.py) terminates from launch + lifetime + 900 s.
set -uo pipefail
RUN=b2; ATTEMPT=4; LIFETIME_S=77400
B=s3://xtenure-cself-pvr-usw2
CODE=$B/code/t1_access/aws_bench/$RUN
OUT=$B/results/t1_access/aws_bench/$RUN/attempt_$ATTEMPT
W=/mnt/bench; mkdir -p $W/env $W/logs $W/exits
exec > >(tee -a $W/env/userdata.log) 2>&1

UP=$(cut -d. -f1 /proc/uptime); NOW=$(date +%s); BOOT=$((NOW - UP)); HARD=$((BOOT + LIFETIME_S))
UPLOAD_AT=$((HARD - 2700)); WORKER_DEADLINE=$((UPLOAD_AT - 300))
MIN=$(( (HARD - NOW) / 60 ))
T1OK=0; T2OK=0
shutdown -h +$MIN && T1OK=1
systemd-run --unit=t1-hard-stop --on-active=$((HARD - NOW))s /usr/sbin/poweroff && T2OK=1
echo "boot $BOOT hard $HARD upload_at $UPLOAD_AT worker_deadline $WORKER_DEADLINE timers shutdown=$T1OK systemd=$T2OK"
echo "{\"boot\": $BOOT, \"hard\": $HARD, \"upload_at\": $UPLOAD_AT, \"worker_deadline\": $WORKER_DEADLINE, \"timer_shutdown\": $T1OK, \"timer_systemd\": $T2OK}" > $W/env/window.json
[ $T1OK = 1 ] || [ $T2OK = 1 ] || { echo "NO STOP TIMER COULD BE INSTALLED"; poweroff; exit 1; }

final_upload() {  # bounded transfer with a CHECKED disposition, inside the hard deadline (never waived for salvage)
  local tries=0 rc nloc nrem ok=false
  while :; do
    tries=$((tries + 1))
    timeout 900 aws s3 sync $W $OUT --only-show-errors --exclude "*.tmp.*" --exclude "env/upload_verify.json"; rc=$?
    nloc=$(cd $W && find . -type f ! -name "*.tmp.*" ! -name ".*" ! -path "./env/upload_verify.json" | wc -l | tr -d ' ')
    nrem=$(timeout 120 aws s3 ls --recursive $OUT/ | grep -v "env/upload_verify.json" | wc -l | tr -d ' ')
    if [ $rc -eq 0 ] && [ "$nrem" -ge "$nloc" ] && [ "$nloc" -gt 0 ]; then ok=true; break; fi
    [ $tries -ge 2 ] && break
    [ $(( $(date +%s) + 1200 )) -ge $HARD ] && break
  done
  echo "{\"transfer_verified\": $ok, \"tries\": $tries, \"sync_rc\": $rc, \"local_files\": $nloc, \"remote_objects\": $nrem, \"at\": $(date +%s)}" > $W/env/upload_verify.json
  timeout 120 aws s3 cp $W/env/upload_verify.json $OUT/env/upload_verify.json --only-show-errors
  echo "transfer disposition: verified=$ok (local $nloc, remote $nrem, sync rc $rc, tries $tries)"
}
die() { echo "FAILED: $*"; echo "$* (at $(date -u +%FT%TZ))" > $W/env/FAILED; final_upload; shutdown -h now; exit 1; }

T=/mnt/lustre/users/pvanrooyen/t1_toolchain; mkdir -p $T
cat > $W/env/SHA256SUMS <<'SUMS'
ec799aafe4347c3e20aedcced23d255a85afb763d24352dfed62705ac5dd4da2  t1_toolchain_lengau.tgz
824837ee54af3f5fe43d67427cfdd335afc99e2f6d846333eb030b0e559053fa  manifest_A.json
08e498c447341dee9f462f10a5570eda4ef58e3c5ad9e418dfc7bc8a4b061955  manifest_B.json
a67e2e1ce9c9c98455ee7946ec8f141ab50a5a8a473178b89aeaa12957d456d5  plan.json
d3851d1d143802e6031af064d68c4b761c02204aff7199453bf54cf19a1c0437  attest.py
76e5670f348032193cd4425b188be09aef8037af69c5ac5b9af8198e6e2e3327  row6_lengau_panel.py
SUMS
for f in t1_toolchain_lengau.tgz manifest_A.json manifest_B.json plan.json attest.py row6_lengau_panel.py; do
  timeout 900 aws s3 cp $CODE/$f $W/env/$f --only-show-errors || die "download $f"
done
(cd $W/env && sha256sum -c SHA256SUMS) || die "a code or toolchain checksum differs"
tar -xzf $W/env/t1_toolchain_lengau.tgz -C $T || die "toolchain extraction"
rm -f $W/env/t1_toolchain_lengau.tgz
echo "f9c3ff028982d04e9186b62bed8e63da999348c584491bd67f1d79071bad926c  $T/t1py" | sha256sum -c || die "t1py is not the pinned wrapper"
lscpu > $W/env/lscpu.txt; free -g > $W/env/free.txt; uname -a > $W/env/uname.txt
C=$T/rsc_screen/workspace_demo/t1_access; R6=$T/rsc/workspace_demo/t1_access

BASE="--xla_cpu_multi_thread_eigen=false --xla_cpu_parallel_codegen_split_count=1"
ARM_A=(NPROC=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 JAX_PLATFORMS=cpu)
# numpy's runtime mask applies to its DISPATCH targets only (numpy 2.4: X86_V3, X86_V4, AVX512_ICL, AVX512_SPR); hardware
# feature names such as AVX512F are ignored. Mask every active dispatch target above X86_V3 (Haswell = X86_V3).
AVX512=$(env "${ARM_A[@]}" $T/t1py -c 'from numpy._core._multiarray_umath import __cpu_features__ as f, __cpu_dispatch__ as d; print(" ".join(x for x in d if f.get(x) and x not in ("X86_V2", "X86_V3")))') || die "numpy dispatch probe"
ARM_B=("${ARM_A[@]}" "XLA_FLAGS=$BASE --xla_cpu_max_isa=AVX2" OPENBLAS_CORETYPE=Haswell)
PROFILE_B=B_nomask
if [ -n "$AVX512" ] && env "${ARM_B[@]}" "NPY_DISABLE_CPU_FEATURES=$AVX512" $T/t1py -c 'import numpy' > $W/env/npy_mask_check.txt 2>&1; then
  ARM_B+=("NPY_DISABLE_CPU_FEATURES=$AVX512"); PROFILE_B=B_full
fi
echo "$PROFILE_B" > $W/env/profile_B.txt
(cd $C && env "${ARM_A[@]}" $T/t1py $W/env/attest.py A $W/env/attest_A.json) || die "arm A attestation"
(cd $C && env "${ARM_B[@]}" $T/t1py $W/env/attest.py $PROFILE_B $W/env/attest_B.json) || die "arm B attestation ($PROFILE_B)"
# Job-start per arm. Arm A (native Zen 4) refusing is itself a parity OUTCOME - attempt 3 found the native dataset identity
# differs from Lengau's, so the unchanged production guards can never accept its records - recorded in ARM_A_REFUSED, its
# stage-2 workers skipped, its row-6 panel still run. Arm B refusing remains fatal (die): it is the arm under test.
STAGE2_ARMS="A B"
for arm in A B; do
  if [ $arm = A ]; then E=("${ARM_A[@]}"); else E=("${ARM_B[@]}"); fi
  if ! (cd $C && env "${E[@]}" $T/t1py chpc/row19_shard.py job-start --manifest $W/env/manifest_$arm.json --plan $W/env/plan.json \
      --job-id ec2$arm --walltime-s $((WORKER_DEADLINE - $(date +%s))) --no-reservation > $W/env/job_start_$arm.log 2>&1); then
    [ $arm = B ] && die "job-start arm B refused (see job_start_B.log)"
    tail -3 $W/env/job_start_A.log > $W/env/ARM_A_REFUSED; STAGE2_ARMS="B"
    echo "arm A job-start refused (recorded as its outcome): $(tail -1 $W/env/job_start_A.log)"
  fi
done
timeout 300 aws s3 sync $W $OUT --only-show-errors --exclude "*.tmp.*"

declare -A PIDS
set -m   # job control: every background job below is its own process group (pgid = its pid), so cleanup reaches children
run() {  # run <name> <cwd> <cmd...>: one declared process; its exit code is published atomically (temp + rename)
  local name=$1 cwd=$2; shift 2
  echo $name >> $W/env/declared.txt
  ( cd $cwd && "$@" > $W/logs/$name.log 2>&1; c=$?; echo $c > $W/exits/.$name.tmp && mv $W/exits/.$name.tmp $W/exits/$name.code ) &
  PIDS[$name]=$!
}
for arm in A B; do
  if [ $arm = A ]; then E=("${ARM_A[@]}"); else E=("${ARM_B[@]}"); fi
  mkdir -p $W/row6_$arm
  for rep in 0 20 40; do
    run row6_${arm}_rep$rep $R6 env "${E[@]}" $T/t1py $W/env/row6_lengau_panel.py $W/row6_$arm/row6_rows_rep$rep.csv $rep
  done
  echo " $STAGE2_ARMS " | grep -q " $arm " || continue
  for i in $(seq 0 35); do
    run w_${arm}_slot$i $C env "${E[@]}" $T/t1py chpc/row19_shard.py worker --manifest $W/env/manifest_$arm.json \
        --rep $((3 + i)) --indices 0 --slot $i --job-id ec2$arm --deadline-epoch $WORKER_DEADLINE
  done
done
DECLARED=$(wc -l < $W/env/declared.txt | tr -d ' ')
echo "launched $DECLARED declared processes at $(date -u +%FT%TZ)"
LAST_SYNC=$(date +%s)
while true; do
  n=$(ls $W/exits | wc -l | tr -d ' ')
  echo "$(date +%s) $((DECLARED - n)) $(cut -d' ' -f1-3 /proc/loadavg)" >> $W/env/occupancy.txt
  [ "$n" -ge $DECLARED ] && break
  [ "$(date +%s)" -ge $UPLOAD_AT ] && break
  if [ $(( $(date +%s) - LAST_SYNC )) -ge 1800 ]; then
    timeout 600 aws s3 sync $W $OUT --only-show-errors --exclude "*.tmp.*"; LAST_SYNC=$(date +%s)
  fi
  sleep 60
done
for n in "${!PIDS[@]}"; do [ -f $W/exits/$n.code ] || echo $n; done | sort > $W/env/censored.txt
# bounded cleanup on ONE global deadline (never an unbounded wait): TERM every group, poll, then KILL, poll, record survivors
CLEAN_END=$(( $(date +%s) + 120 ))
alive() { for n in "${!PIDS[@]}"; do kill -0 -- -${PIDS[$n]} 2>/dev/null && echo $n; done; }   # any member of the group
for n in $(alive); do kill -TERM -- -${PIDS[$n]} 2>/dev/null; done
while [ -n "$(alive)" ] && [ $(date +%s) -lt $((CLEAN_END - 30)) ]; do sleep 2; done
for n in $(alive); do kill -KILL -- -${PIDS[$n]} 2>/dev/null; done
while [ -n "$(alive)" ] && [ $(date +%s) -lt $CLEAN_END ]; do sleep 1; done
alive | sort > $W/env/unresolved.txt
echo "cleanup: censored $(wc -l < $W/env/censored.txt), unresolved after KILL $(wc -l < $W/env/unresolved.txt)"
python3 - $W <<'PY'
import json, os, sys, time
W = sys.argv[1]
names = open(os.path.join(W, "env", "declared.txt")).read().split()
censored = set(open(os.path.join(W, "env", "censored.txt")).read().split())
unresolved = set(open(os.path.join(W, "env", "unresolved.txt")).read().split())
out = {}
for n in names:
    if n in censored:
        out[n] = "censored at the upload deadline"
        continue
    v = open(os.path.join(W, "exits", n + ".code")).read().strip()
    out[n] = int(v)
assert len(out) == len(names) == len(set(names))
json.dump(dict(at=time.time(), declared=len(names), outcomes=out, unresolved_after_kill=sorted(unresolved)), open(os.path.join(W, "env", "outcomes.json"), "w"), indent=1)
PY
[ $? -eq 0 ] && [ -s $W/env/outcomes.json ] || { echo "OUTCOMES CERTIFICATE FAILED"; echo "outcomes certificate failed $(date -u +%FT%TZ)" > $W/env/OUTCOMES_FAILED; }
echo "end $(date -u +%FT%TZ)"
final_upload
shutdown -h now
