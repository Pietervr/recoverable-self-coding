# The pinned T1 environment on CHPC Lengau (ledger row 18)

Written 25 September 2026 from what was measured on the cluster; the ledger is
`rsc_t1_simulation_design.md` §12 row 18 in the Unimog repository.

## Why the obvious route fails

Lengau is CentOS 7.9 with glibc 2.17, the login nodes have no internet, and the newest
Python module is 3.11.6. The pinned set — Python 3.12, jax 0.11.1, jaxlib 0.11.1,
numpy 2.4.6, scipy 1.18.0, pandas 3.0.5, joblib 1.5.3, the versions the AWS rows record —
ships only `manylinux_2_27`/`2_28` wheels for every compiled package (jaxlib 0.11.1 has no
glibc-2.17 wheel at all; under that constraint pip resolves jaxlib ≤ 0.7.0 and numpy ≤ 2.2.6).
Apptainer 1.2.3 (`/apps/chpc/bio/app/apptainer-1.2.3`) runs on login1 and login2 and can pull
an image, but cannot execute one: no setuid starter and no user namespaces on kernel 3.10.
The `chpc/singularity/3.5.3` module that runs containers exists on compute nodes only.

## The route that works, with no privileges

1. On the sanctioned transfer node `scp.chpc.ac.za` (= login1, which has internet and mounts
   Lustre): `apptainer pull docker://python:3.12.10-slim-bookworm` into
   `/mnt/lustre/users/pvanrooyen/t1_toolchain/`. Debian bookworm, glibc 2.36; 3.12.10 is the
   interpreter version the AWS sens600 rows record.
2. Unpack the image's root filesystem from the SIF (`apptainer sif dump` + `unsquashfs`, both
   plain file operations) into `t1_toolchain/rootfs`.
3. Run the image's Python under the image's own dynamic loader with `--library-path` pointing
   at the image's libraries: that is `t1_toolchain/t1py`, written by `t1_toolchain_setup.sh`.
   `LD_LIBRARY_PATH` is deliberately not exported — host binaries that Python spawns (pip runs
   `uname`) would otherwise load the image's libc under the host loader and crash.
4. Install the ten wheels offline into `t1_toolchain/t1site` with `--require-hashes` from
   `t1_cloudset_hashed.txt`, whose SHA-256s were measured on the Mac from the wheels pip
   downloaded for `manylinux_2_28_x86_64` / cp312.

Measured on login2 (E5-2690 v3 Haswell, AVX2, no AVX-512): python 3.12.10, jax 0.11.1,
jaxlib 0.11.1, numpy 2.4.6, scipy 1.18.0, pandas 3.0.5, joblib 1.5.3, ml_dtypes 0.6.0;
`jax.devices()` one CpuDevice; jit, grad, `jnp.linalg.norm` and scipy Nelder–Mead run.

## Files

- `t1_toolchain_setup.sh` — steps 2–4 and the two checks; idempotent (skips the unpack and the
  install when they exist). Run on login2: `sh /mnt/lustre/users/pvanrooyen/t1_toolchain/t1_toolchain_setup.sh`.
- `t1_cloudset_hashed.txt` — the hash-pinned requirements.
- `row18_bench.pbs` — the stage-1 benchmark job, one core on the shared `serial` queue, 3 h walltime,
  `bench.py --D 4 --layer` on the code of `f7e69b1` cloned to `t1_toolchain/rsc`. It sits at
  `t1_toolchain/jobs/row18_bench.pbs` on Lustre and is submitted only on the owner's go.
  Mac baseline for the same command (25 Sept, M4 Max, one core, the Mac venv's numpy 2.5.3 set):
  fit s M2B 0.04, M2H 9.70, M2S 5.90, M3H 50.46; nine refits 67.2 s; 1:12 wall.
- `results/` — the measured outputs (1 Oct 2026): `row18_bench_7513466.txt` (one Lengau core: nine refits
  315.8 s, one full layer 6,409 s), `row18_pack_7513470.txt` (24 packed copies: nine refits 424.5 s median,
  spread within 1 %), `mac_layer_2026-10-01.txt` (the Mac core, same command: nine refits 68.6 s, one layer
  1,370 s). Ratio: one Lengau core is 4.7x the Mac core; a packed node adds 1.3-1.5x.
- `row18_pack.pbs` + `pack_summary.py` — stage 1b, 24 pinned copies on one `smp` node.
- The wheelhouse itself (`wheels_cloudset/`, 148 MB) lives only on Lustre; it is
  reproducible with `pip download --only-binary=:all: --platform manylinux_2_28_x86_64
  --python-version 3.12 --implementation cp --abi cp312` on the row's pins.

## What this does not do

This file describes the environment only. It holds no job state: which jobs have run or are
running on Lengau, and the core-hours they used, are in the ledger (`rsc_t1_simulation_design.md`
§12, rows 6, 18 and 19) and in each campaign's `budget.json`. Everything on Lengau is under
`/mnt/lustre/users/pvanrooyen/t1_toolchain`; the home directory (15 GB per the CHPC wiki) holds
nothing.
