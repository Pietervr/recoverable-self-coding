#!/bin/sh
# Row 18 (rsc_t1_simulation_design.md section 12): the pinned T1 environment on Lengau, without a container runtime.
# Lengau is CentOS 7.9 (glibc 2.17); every compiled wheel of the pinned set is manylinux_2_27/2_28. Apptainer on the
# login and transfer nodes can pull an image but not execute it (no setuid starter, no user namespaces on kernel
# 3.10), and the singularity module is compute-only. So the python:3.12.10-slim-bookworm image (glibc 2.36, the
# interpreter version the AWS rows record) is unpacked from its SIF onto Lustre and its own dynamic loader runs
# python. No privileges are needed and nothing is installed outside /mnt/lustre/users/pvanrooyen/t1_toolchain.
set -e
T=/mnt/lustre/users/pvanrooyen/t1_toolchain
A=/apps/chpc/bio/app/apptainer-1.2.3/bin/apptainer
SIF=python-3.12.10-slim-bookworm.sif
R=$T/rootfs
cd $T

if [ ! -d $R ]; then
  ID=$($A sif list $SIF | awk '/FS/ && /Squashfs/ {print $1; exit}')
  echo "== squashfs descriptor $ID"
  $A sif dump $ID $SIF > root.squashfs
  unsquashfs -d $R root.squashfs > unsquash.log 2>&1 || true
  tail -2 unsquash.log
fi

echo "== runtime libraries in the image"
ls $R/usr/lib/x86_64-linux-gnu/ | grep -E 'libstdc\+\+|libgcc_s|libgomp' || echo "MISSING libstdc++ (slim image)"

cat > $T/t1py <<EOF
#!/bin/sh
# python 3.12.10 from the unpacked python:3.12.10-slim-bookworm image, run under that image's loader and
# libraries; the pinned packages live in $T/t1site. Usage: t1py [python args]
R=$R
export PYTHONHOME=\$R/usr/local
export PYTHONPATH=$T/t1site\${PYTHONPATH:+:\$PYTHONPATH}
# --library-path only: an exported LD_LIBRARY_PATH would make host binaries that python spawns (uname, for pip)
# load the image's libc under the host loader and crash.
LP=\$R/lib/x86_64-linux-gnu:\$R/usr/lib/x86_64-linux-gnu:\$R/usr/local/lib
exec \$R/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 --library-path \$LP \$R/usr/local/bin/python3.12 "\$@"
EOF
chmod +x $T/t1py

echo "== interpreter under the image loader"
$T/t1py -c 'import sys, platform; print(sys.version.split()[0], platform.libc_ver(), platform.machine())'

if [ ! -d $T/t1site/jaxlib ]; then
  echo "== offline, hash-pinned install of the cloud set"
  $T/t1py -m pip install --quiet --no-index --find-links $T/wheels_cloudset --require-hashes --no-deps \
      -r $T/t1_cloudset_hashed.txt --target $T/t1site 2>&1 | grep -v -i "warning" | tail -3 || true
fi

echo "== versions (row 18 gate: every one must match the cloud set)"
NPROC=1 $T/t1py -c '
import sys, platform
import jax, jaxlib, numpy, scipy, pandas, joblib, ml_dtypes, opt_einsum
print("python", sys.version.split()[0], "jax", jax.__version__, "jaxlib", jaxlib.__version__,
      "numpy", numpy.__version__, "scipy", scipy.__version__, "pandas", pandas.__version__,
      "joblib", joblib.__version__, "ml_dtypes", ml_dtypes.__version__, platform.machine())
'
echo "== JAX on this CPU"
NPROC=1 $T/t1py -c '
import jax, jax.numpy as jnp
from jax import jit, grad
print("devices", jax.devices())
x = jnp.arange(100000, dtype=jnp.float32)
print("norm", float(jnp.linalg.norm(x)))
f = jit(lambda a: jnp.sum(jnp.sin(a) ** 2))
print("jit", float(f(x)))
print("grad", float(grad(lambda a: jnp.sum(a ** 2))(jnp.ones(3))[0]))
import scipy.optimize, numpy as np
print("scipy minimize", scipy.optimize.minimize(lambda p: (p[0]-1)**2 + (p[1]+2)**2, np.zeros(2), method="Nelder-Mead").x.round(3))
jax.print_environment_info()
'
grep -m1 "model name" /proc/cpuinfo
