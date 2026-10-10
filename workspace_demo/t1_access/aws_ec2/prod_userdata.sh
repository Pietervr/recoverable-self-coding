#!/bin/bash
# Row 19 screen on EC2 - PRODUCTION instance (stage 2; Codex RSC f3dd3d7). Derived from the reviewed row-23 instance
# contract (bench_userdata.sh) with ONE profile: B_full (A's baseline XLA flags + --xla_cpu_max_isa=AVX2,
# OPENBLAS_CORETYPE=Haswell, numpy dispatch above X86_V3 masked) - the only profile whose datasets reproduce Lengau's
# identities (row 23 attempt 4). B_nomask is refused here (no fallback). The plan (76 slots: work coordinates from the EC2
# partition block + sentinel coordinates Lengau completed) comes from the claim authority; every output is listed in a
# bundle SHA256SUMS for crash-safe ingestion on Lengau (chpc/row19_ec2_ingest.py).
set -uo pipefail
RUN=__RUN__; ATTEMPT=__ATTEMPT__; LIFETIME_S=__LIFETIME_S__; ATTEMPT_ID=__ATTEMPT_ID__
B=s3://xtenure-cself-pvr-usw2
CODE=$B/code/t1_access/aws_bench/$RUN/attempt_$ATTEMPT
OUT=$B/results/t1_access/aws_bench/$RUN/attempt_$ATTEMPT
W=/mnt/bench; mkdir -p $W/env $W/logs $W/exits
export AWS_DEFAULT_REGION=us-west-2      # every aws call on the instance is S3 against the Oregon bucket (EC2 runs elsewhere)
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
( while true; do                         # spot interruption notice (2-minute warning): record it and push everything now
    TK=$(curl -s -m 2 -X PUT http://169.254.169.254/latest/api/token -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
    if curl -s -f -m 2 -H "X-aws-ec2-metadata-token: $TK" http://169.254.169.254/latest/meta-data/spot/instance-action > $W/env/spot_notice.json 2>/dev/null; then
      date -u +%FT%TZ >> $W/env/spot_notice.json; timeout 100 aws s3 sync $W $OUT --only-show-errors --exclude "*.tmp.*"; break
    fi; rm -f $W/env/spot_notice.json; sleep 5; done ) &

T=/mnt/lustre/users/pvanrooyen/t1_toolchain; mkdir -p $T
cat > $W/env/SHA256SUMS <<'SUMS'
__SUMS__
SUMS
for f in t1_toolchain_lengau.tgz manifest_prod.json plan.json attest.py; do
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
[ "$PROFILE_B" = B_full ] || die "numpy refused the dispatch mask: production runs B_full only"
(cd $C && env "${ARM_B[@]}" $T/t1py $W/env/attest.py B_full $W/env/attest_B.json) || die "B_full attestation"
(cd $C && env "${ARM_B[@]}" $T/t1py chpc/row19_shard.py job-start --manifest $W/env/manifest_prod.json --plan $W/env/plan.json \
    --job-id $ATTEMPT_ID --walltime-s $((WORKER_DEADLINE - $(date +%s))) --no-reservation > $W/env/job_start.log 2>&1) \
    || die "job-start refused (see job_start.log)"
timeout 300 aws s3 sync $W $OUT --only-show-errors --exclude "*.tmp.*"

declare -A PIDS
set -m   # job control: every background job below is its own process group (pgid = its pid), so cleanup reaches children
run() {  # run <name> <cwd> <cmd...>: one declared process; its exit code is published atomically (temp + rename)
  local name=$1 cwd=$2; shift 2
  echo $name >> $W/env/declared.txt
  ( cd $cwd && "$@" > $W/logs/$name.log 2>&1; c=$?; echo $c > $W/exits/.$name.tmp && mv $W/exits/.$name.tmp $W/exits/$name.code ) &
  PIDS[$name]=$!
}
python3 -c "import json; [print(s['slot'], s['rep'], s['indices'][0]) for s in json.load(open('$W/env/plan.json'))['slots']]" > $W/env/slots.txt \
  || die "plan unreadable"
while read slot rep idx; do
  run w_slot$slot $C env "${ARM_B[@]}" $T/t1py chpc/row19_shard.py worker --manifest $W/env/manifest_prod.json \
      --rep $rep --indices $idx --slot $slot --job-id $ATTEMPT_ID --deadline-epoch $WORKER_DEADLINE
done < $W/env/slots.txt
DECLARED=$(wc -l < $W/env/declared.txt | tr -d ' ')
ROOT_LIVE=$(cd $C && $T/t1py -c 'import json; print(json.load(open("'$W'/env/manifest_prod.json"))["storage"]["root"])')
echo "launched $DECLARED declared processes at $(date -u +%FT%TZ)"
LAST_SYNC=$(date +%s)
while true; do
  n=$(ls $W/exits | wc -l | tr -d ' ')
  echo "$(date +%s) $((DECLARED - n)) $(cut -d' ' -f1-3 /proc/loadavg)" >> $W/env/occupancy.txt
  [ "$n" -ge $DECLARED ] && break
  [ "$(date +%s)" -ge $UPLOAD_AT ] && break
  if [ $(( $(date +%s) - LAST_SYNC )) -ge 600 ]; then
    mkdir -p $W/root; cp -r $ROOT_LIVE/records $ROOT_LIVE/timing $ROOT_LIVE/status $W/root/ 2>/dev/null
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
ROOT=$(cd $C && $T/t1py -c 'import json; print(json.load(open("'$W'/env/manifest_prod.json"))["storage"]["root"])')
mkdir -p $W/root; cp -r $ROOT/records $ROOT/timing $ROOT/status $W/root/ 2>/dev/null; cp $ROOT/task_*.json $W/root/ 2>/dev/null
(cd $W && find root env -type f ! -name "*.tmp*" ! -name "BUNDLE_SHA256SUMS" ! -name upload_verify.json | LC_ALL=C sort | xargs sha256sum > BUNDLE_SHA256SUMS) \
  || echo "bundle checksum list failed" > $W/env/BUNDLE_FAILED
echo "end $(date -u +%FT%TZ)"
final_upload
shutdown -h now
