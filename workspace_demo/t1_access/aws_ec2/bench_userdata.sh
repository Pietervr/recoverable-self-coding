#!/bin/bash
# Ledger row 23 (rsc_t1_simulation_design.md section 12): the EC2 parity and timing benchmark, run as the instance's
# user-data on ONE spot c7a.24xlarge (us-west-2, 96 physical Zen 4 cores, 192 GiB). It installs the Lengau toolchain
# BYTES at the Lengau path (so the pinned wrapper t1py and its sha256 are identical), then runs two arms side by side:
#   A native  - exactly the Lengau runtime (thread caps 1, JAX_PLATFORMS=cpu), Zen 4 code paths free (AVX-512);
#   B pinned  - A plus XLA_FLAGS=--xla_cpu_max_isa=AVX2, OPENBLAS_CORETYPE=Haswell and numpy's AVX-512 dispatch disabled,
#               the attempt to reproduce Lengau's Haswell float bits.
# Stage 1 (~75 min): the row 6 panel (3 sens600 datasets, code f7e69b1) per arm; Lengau's rows are the reference.
# Stage 2 (~20 h): the screen's refit worker (rsc_screen, row19_shard.py unchanged) on reps 3..38 at index 0 per arm -
# coordinates whose Lengau records already exist; the comparison runs on the Mac (bench_compare.py). Nothing here enters
# any screen root, ledger or denominator: these are qualification duplicates.
# Hard ceilings: shutdown -h at 23.5 h (instance-initiated shutdown = terminate); the spot max price is set by the launcher.
set -u
RUN=__RUN__
B=s3://xtenure-cself-pvr-usw2
CODE=$B/code/t1_access/aws_bench/$RUN
OUT=$B/results/t1_access/aws_bench/$RUN
TGZ_SHA=__TGZ_SHA__
shutdown -h +1410
ulimit -s unlimited
W=/mnt/bench; mkdir -p $W/env $W/logs; exec > >(tee -a $W/env/userdata.log) 2>&1
echo "start $(date -u +%FT%TZ) run $RUN"
sync_out() { aws s3 sync $W $OUT --only-show-errors --exclude "*.tmp.*"; }

T=/mnt/lustre/users/pvanrooyen/t1_toolchain; mkdir -p $T
aws s3 cp $CODE/t1_toolchain_lengau.tgz /mnt/t1.tgz --only-show-errors
echo "$TGZ_SHA  /mnt/t1.tgz" | sha256sum -c || { echo "TARBALL CHECKSUM FAILED"; sync_out; shutdown -h now; exit 1; }
tar -xzf /mnt/t1.tgz -C $T && rm /mnt/t1.tgz
sha256sum $T/t1py | tee $W/env/t1py.sha256
lscpu > $W/env/lscpu.txt; free -g > $W/env/free.txt; uname -a > $W/env/uname.txt

ARM_A=(NPROC=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 JAX_PLATFORMS=cpu)
AVX512=$(env "${ARM_A[@]}" $T/t1py -c 'from numpy._core._multiarray_umath import __cpu_features__ as f; print(" ".join(k for k,v in f.items() if v and k.startswith("AVX512")))')
echo "numpy AVX-512 features on this CPU: $AVX512" | tee $W/env/numpy_avx512.txt
ARM_B=("${ARM_A[@]}" XLA_FLAGS=--xla_cpu_max_isa=AVX2 OPENBLAS_CORETYPE=Haswell)
if [ -n "$AVX512" ]; then
  if env "${ARM_B[@]}" "NPY_DISABLE_CPU_FEATURES=$AVX512" $T/t1py -c 'import numpy' > $W/env/npy_disable_check.txt 2>&1; then
    ARM_B+=("NPY_DISABLE_CPU_FEATURES=$AVX512")
  else
    echo "NPY_DISABLE_CPU_FEATURES refused by numpy; arm B runs without it (see npy_disable_check.txt)"
  fi
fi
printf '%s\n' "${ARM_B[@]}" > $W/env/arm_B_env.txt
for arm in A B; do
  if [ $arm = A ]; then E=("${ARM_A[@]}"); else E=("${ARM_B[@]}"); fi
  env "${E[@]}" $T/t1py -c '
import os, sys, numpy, scipy, jax, platform
from numpy._core._multiarray_umath import __cpu_features__ as f
print("arm", sys.argv[1], "python", sys.version.split()[0], "jax", jax.__version__, "numpy", numpy.__version__, "scipy", scipy.__version__, platform.machine())
print("numpy AVX512 active:", [k for k, v in f.items() if v and k.startswith("AVX512")])
print("XLA_FLAGS", os.environ.get("XLA_FLAGS"), "OPENBLAS_CORETYPE", os.environ.get("OPENBLAS_CORETYPE"))
numpy.show_config()' $arm > $W/env/arm_$arm.txt 2>&1
done
sync_out

# Stage 1: the row 6 panel, 3 reps x 2 arms, one process each (cwd = the f7e69b1 tree, as in the Lengau PBS job)
aws s3 cp $CODE/row6_lengau_panel.py $W/env/row6_lengau_panel.py --only-show-errors
echo "76e5670f348032193cd4425b188be09aef8037af69c5ac5b9af8198e6e2e3327  $W/env/row6_lengau_panel.py" | sha256sum -c || echo "ROW6 PANEL SCRIPT CHECKSUM FAILED"
for arm in A B; do
  mkdir -p $W/row6_$arm
  if [ $arm = A ]; then E=("${ARM_A[@]}"); else E=("${ARM_B[@]}"); fi
  for rep in 0 20 40; do
    ( cd $T/rsc/workspace_demo/t1_access && env "${E[@]}" $T/t1py $W/env/row6_lengau_panel.py $W/row6_$arm/row6_rows_rep$rep.csv $rep \
        > $W/row6_$arm/rep$rep.log 2>&1 ) &
  done
done

# Stage 2: the screen refit worker, reps 3..38 at index 0, per arm (36 + 36 workers); arm A through job-start's admission
C=$T/rsc_screen/workspace_demo/t1_access
DL=$(( $(date +%s) + 82800 ))
python3 -c "import json; json.dump({'job': 0, 'slots': [{'slot': i, 'rep': 3 + i, 'indices': [0]} for i in range(36)]}, open('$W/env/plan.json', 'w'))"
( cd $C && env "${ARM_A[@]}" $T/t1py chpc/row19_shard.py job-start --manifest chpc/row19_screen_manifest.json --plan $W/env/plan.json \
    --job-id ec2A --walltime-s 82800 --no-reservation > $W/env/job_start_A.log 2>&1 )
ROOT_A=$(cd $C && $T/t1py -c 'import json; print(json.load(open("chpc/row19_screen_manifest.json"))["storage"]["root"])')
ROOT_B=$W/root_B; mkdir -p $ROOT_B
for i in $(seq 0 35); do
  rep=$((3 + i))
  ( cd $C && env "${ARM_A[@]}" $T/t1py chpc/row19_shard.py worker --manifest chpc/row19_screen_manifest.json --rep $rep --indices 0 \
      --slot $i --job-id ec2A --deadline-epoch $DL > $W/logs/A_slot$i.log 2>&1 ) &
  ( cd $C && env "${ARM_B[@]}" $T/t1py chpc/row19_shard.py worker --manifest chpc/row19_screen_manifest.json \
      --root $ROOT_B --no-binding-check --rep $rep --indices 0 --slot $i --job-id ec2B --deadline-epoch $DL > $W/logs/B_slot$i.log 2>&1 ) &
done
copy_a() { mkdir -p $W/root_A; cp -r $ROOT_A/records $ROOT_A/timing $ROOT_A/status $W/root_A/ 2>/dev/null; cp $ROOT_A/task_*.json $W/root_A/ 2>/dev/null; }
( while true; do sleep 1800; copy_a; uptime > $W/env/uptime.txt; free -g > $W/env/free_now.txt; sync_out; done ) &
SYNCER=$!
for p in $(jobs -p); do [ "$p" = "$SYNCER" ] || wait $p; done
kill $SYNCER 2>/dev/null
copy_a
echo "end $(date -u +%FT%TZ)"; sync_out
shutdown -h now
