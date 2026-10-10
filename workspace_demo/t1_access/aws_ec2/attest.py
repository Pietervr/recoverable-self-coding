"""Ledger row 23: attest one arm's EFFECTIVE numerical environment, as a worker would see it (run under t1py from the
screen tree's t1_access directory with the arm's environment). Imports models.py first, exactly as the worker's import
chain does, so the XLA_FLAGS setdefault has applied. Writes one JSON object to argv[2]; exit 3 when the profile named
in argv[1] is not what is in effect (fail closed)."""
import os, sys, json, ctypes, platform
profile, out = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.getcwd())
import models  # noqa: F401  (applies the XLA/thread setdefaults, as in the worker)
import numpy, scipy, jax
from numpy._core._multiarray_umath import __cpu_features__ as feats
try:
    from numpy._core._multiarray_umath import __cpu_dispatch__ as dispatch
except Exception:
    dispatch = None


def openblas_core():
    libs = sorted({l.split()[-1] for l in open("/proc/self/maps") if "openblas" in l.lower() and l.split()[-1].startswith("/")})
    got = {}
    for lib in libs:
        h = ctypes.CDLL(lib)
        for name in ("scipy_openblas_get_corename64_", "scipy_openblas_get_corename", "openblas_get_corename64_", "openblas_get_corename"):
            f = getattr(h, name, None)
            if f is not None:
                f.restype = ctypes.c_char_p
                got[os.path.basename(lib)] = f().decode()
                break
        else:
            got[os.path.basename(lib)] = None
    return got


import scipy.linalg  # noqa: F401  (loads scipy's OpenBLAS too)
x = jax.numpy.ones(8).sum()  # initialise the XLA CPU backend
rec = dict(profile=profile, python=sys.version.split()[0], jax=jax.__version__, numpy=numpy.__version__, scipy=scipy.__version__,
           machine=platform.machine(), backend=jax.default_backend(),
           XLA_FLAGS=os.environ.get("XLA_FLAGS"), OPENBLAS_CORETYPE=os.environ.get("OPENBLAS_CORETYPE"),
           NPY_DISABLE_CPU_FEATURES=os.environ.get("NPY_DISABLE_CPU_FEATURES"),
           threads={k: os.environ.get(k) for k in ("NPROC", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
           numpy_avx512_active=sorted(k for k, v in feats.items() if v and k.startswith("AVX512")),   # hardware flags (informational)
           numpy_dispatch=dispatch if isinstance(dispatch, (list, tuple)) else None,
           numpy_dispatch_active=sorted(x for x in (dispatch or []) if feats.get(x)),
           openblas_core=openblas_core())
base = "--xla_cpu_multi_thread_eigen=false --xla_cpu_parallel_codegen_split_count=1"
bad = []
if not (rec["XLA_FLAGS"] or "").startswith(base):
    bad.append("XLA baseline flags missing")
if any(v != "1" for v in rec["threads"].values()):
    bad.append("a thread cap is not 1")
if profile.startswith("B"):
    if "--xla_cpu_max_isa=AVX2" not in (rec["XLA_FLAGS"] or ""):
        bad.append("ISA ceiling missing")
    if rec["OPENBLAS_CORETYPE"] != "Haswell":
        bad.append("OPENBLAS_CORETYPE not Haswell")
    if profile == "B_full" and any(x not in ("X86_V2", "X86_V3") for x in rec["numpy_dispatch_active"]):
        bad.append(f"numpy dispatch above X86_V3 still active under B_full: {rec['numpy_dispatch_active']}")
    if not rec["openblas_core"]:
        bad.append("no loaded OpenBLAS library found: the BLAS core is unavailable, not certified")
    for lib, c in rec["openblas_core"].items():
        if c is None:
            bad.append(f"{lib}: OpenBLAS core unavailable (no corename symbol), not certified")
        elif "haswell" not in c.lower():
            bad.append(f"{lib}: OpenBLAS reports core {c}, not Haswell")
rec["problems"] = bad
json.dump(rec, open(out, "w"), indent=1)
print(json.dumps(rec))
sys.exit(3 if bad else 0)
