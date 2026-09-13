"""Refitting-bootstrap coverage probe at chosen null points (13 Sept 2026, Mac; method development, not validation).

Runs the complete per-layer procedure (simulate.run_points -> one_replicate -> analyze.analyze_dataset) with
Config(interval="refit") on NEW seeds at a few graded null points, so that the coverage of the refitting
interval can be compared with the cluster interval's at the two settings where it failed (M2S omega 1 and 2,
coverage 0.780 / 0.216 in run d4v12b) and at a control. Small counts by design: the question is whether the
refitting interval moves coverage at those settings at all, which decides whether the funded validation is
worth running. Rows have the standard schema (interval_* columns, settings, code hash) and summarize() reads
them; every completed refit resample is checkpointed under --out/ckpt so an interrupted run resumes.

Usage (from t1_access, NPROC=1 before import so JAX pins one thread per worker):
  NPROC=1 nohup .venv/bin/python probe_refit.py --points M2S:omega=2.0,M2S:omega=1.0 --n-rep 20 \
      --n-boot-refit 50 --seed 2027 --layers 41 --n-jobs 11 --out sim_results/refit_probe_<code>/ > .../probe.log 2>&1 &
"""
import argparse, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze as A
import models as M
import simulate as S


def parse_points(spec: str) -> list:
    pts = []
    for item in spec.split(","):
        name, _, kv = item.partition(":")
        kw = {}
        if kv:
            for pair in kv.split(";"):
                k, v = pair.split("=")
                kw[k] = float(v)
        if name not in M.MEMBERS:
            raise SystemExit(f"unknown member {name}")
        pts.append((name, kw))
    return pts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--points", required=True, help="comma list of member[:key=value[;key=value]] null points")
    ap.add_argument("--n-rep", type=int, default=20)
    ap.add_argument("--D", type=int, default=4)
    ap.add_argument("--layers", default="41")
    ap.add_argument("--rho", type=float, default=S.RHO_LAYERS)
    ap.add_argument("--n-jobs", type=int, default=11)
    ap.add_argument("--n-starts-inner", type=int, default=4)
    ap.add_argument("--n-boot-refit", type=int, default=50)
    ap.add_argument("--n-gh", type=int, default=M.GH_NODES_DEFAULT)
    ap.add_argument("--seed", type=int, required=True, help="a NEW seed (d4v12b used 2026)")
    ap.add_argument("--out", required=True, help="output directory; rows go to <out>/refit_probe_D<D>.csv")
    a = ap.parse_args()
    if a.seed == 2026:
        raise SystemExit("seed 2026 is the d4v12b seed; the probe must use new datasets")
    os.makedirs(os.path.join(a.out, "ckpt"), exist_ok=True)
    cfg = A.Config(n_starts_inner=a.n_starts_inner, n_gh=a.n_gh, interval="refit", n_boot_refit=a.n_boot_refit,
                   refit_checkpoint_dir=os.path.join(a.out, "ckpt"))
    layers = tuple(int(x) for x in a.layers.split(","))
    points = parse_points(a.points)
    out_csv = os.path.join(a.out, f"refit_probe_D{a.D}.csv")
    print(f"probe: points {points} n_rep {a.n_rep} D {a.D} layers {layers} n_boot_refit {a.n_boot_refit} "
          f"n_starts_inner {a.n_starts_inner} seed {a.seed} n_jobs {a.n_jobs} code {S.config_hash(cfg, a.D, layers, a.seed)}",
          flush=True)
    t0 = time.time()

    def on_chunk(path, n_done, n_total, elapsed):
        print(f"[{time.strftime('%H:%M:%S')}] {n_done}/{n_total} replicates written, {elapsed / 3600:.2f} h", flush=True)

    S.run_points(points, a.n_rep, a.D, layers, a.rho, cfg, a.seed, a.n_jobs, out_csv, None, chunk=a.n_jobs, on_chunk=on_chunk)
    print(f"probe done in {(time.time() - t0) / 3600:.2f} h", flush=True)
    print(S.summarize(out_csv).to_string(), flush=True)


if __name__ == "__main__":
    main()
