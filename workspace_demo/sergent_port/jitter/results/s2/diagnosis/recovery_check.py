"""Latency recovery under the repaired construction against the oracle Sigma (the open question of 24 Oct):
G3 (and B3) FULL-DATA fits on W2-type data from the generators of S2, S4, S13, S20, S10 (strong and moderate
jitter), R replicates each, under (a) 'em' = scaled catch Sigma start + within-model EM, (b) 'oracle' = the
generator's own Sigma fixed, (c) 'scaled' fixed. Reports the fitted s_tau / s_g against the truth.
Usage: recovery_check.py <R> <workers> [subjects...]   (development seeds, setting tag 'REC')"""
import os, sys, json, time
os.environ.setdefault("NPROC", "1")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))  # the jitter root, wherever the tree lives (the AWS closure of 24 Oct failed on a Mac-only path)
import numpy as np

R = int(sys.argv[1]) if len(sys.argv) > 1 else 5
WORKERS = int(sys.argv[2]) if len(sys.argv) > 2 else 12
SUBJECTS = [int(v) for v in sys.argv[3:]] if len(sys.argv) > 3 else [2, 4, 13, 20, 10]
# 'oracle' = the generator's own mu0 AND Sigma (an oracle baseline/covariance comparison); 'oracle_sigma' = the generator's
# Sigma with the ESTIMATED training-catch mu0, so that Sigma's contribution is isolated (Codex S3 review 24 Oct, finding 5)
VARIANTS = ("em", "oracle", "oracle_sigma", "scaled")
OUT = os.path.dirname(os.path.abspath(__file__))
TAG = os.environ.get("RECOVERY_TAG", "")           # e.g. 'final' -> recovery_check_final.json (provenance kept per run)


def task(subject, rep, variant):
    os.environ.setdefault("NPROC", "1")
    import data as D, fit as F, models as M, simulate as S, s2
    t0 = time.time()
    cfg = s2.load_config(subject, "G3")
    bases = s2.load_bases()
    b = bases[str(subject)]
    seed = S.seed_for("development", "REC", rep, subject)
    syn = S.generate(cfg, np.asarray(b["levels"]), np.asarray(b["blocks"]), seed, "W")
    p = syn.participant(subject=900000 + 100 * subject + rep)
    sp_ = D.span("primary")
    P = D.PRIMARY_WINDOWS
    Y = p.W53[:, sp_.windows]
    if variant == "oracle":
        wh = D.whitening_from_sigma(cfg.mu0[P], cfg.Sigma[np.ix_(P, P)], 0.0, int(np.sum(p.levels == 0)))
        ds = D.make_dataset(Y, p.levels, sp_, wh, f"{p.data_id}/primary/oracle/full")
        cache = F.FitCache(em=False)
    elif variant == "oracle_sigma":
        mu0_est = Y[p.levels == 0].mean(axis=0)                     # the training-catch anchor every scoring fit uses
        wh = D.whitening_from_sigma(mu0_est, cfg.Sigma[np.ix_(P, P)], 0.0, int(np.sum(p.levels == 0)))
        ds = D.make_dataset(Y, p.levels, sp_, wh, f"{p.data_id}/primary/oracle_sigma/full")
        cache = F.FitCache(em=False)
    else:
        ds = D.make_dataset(Y, p.levels, sp_, None, f"{p.data_id}/primary/{variant}/full", "scaled")
        cache = F.FitCache(em=(variant == "em"))
    res = F.fit_all_models(ds, cache, "primary", ("G3", "B3"))
    out = dict(subject=subject, rep=rep, variant=variant, true_s_tau=cfg.s_tau_ms, true_s_g=cfg.s_g, seconds=time.time() - t0,
               data_id=p.data_id, code_hash=M.code_hash())
    for sel in ("G3", "B3", "G2", "G3+", "B2", "B3+"):
        r = res[sel]
        if r.available:
            Pp = M.unpack(F.selected_spec(sel, r, "primary"), r.theta)
            out[sel] = dict(selection=r.selection, status=r.status, s_tau=Pp.s_tau_ms, s_g=Pp.s_g, loglik=r.loglik,
                            em=r.em_iterations, n_starts=len(r.starts), n_converged=r.n_converged,
                            chain_notes=[n for n in r.notes if "stopped" in n or "accepted" in n or "chain" in n or "retried" in n],
                            A=None if Pp.A is None else [float(v) for v in Pp.A[1:]], bounds=r.bounds_hit)
        else:
            out[sel] = dict(selection="UNAVAILABLE", status=r.status, notes=r.notes[-3:])
    return out


def main():
    from joblib import Parallel, delayed
    jobs = [(s, rep, v) for v in VARIANTS for s in SUBJECTS for rep in range(R)]
    t0 = time.time()
    rows = Parallel(n_jobs=WORKERS, backend="loky")(delayed(task)(s, rep, v) for s, rep, v in jobs)
    import models as M
    name = f"recovery_check{('_' + TAG) if TAG else ''}.json"
    json.dump(dict(code_hash=M.code_hash(), R=R, subjects=SUBJECTS, variants=list(VARIANTS),
                   utc=time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()), rows=rows),
              open(os.path.join(OUT, name), "w"), indent=1)
    print(f"{len(rows)} fits in {time.time() - t0:.0f} s; code {M.code_hash()}; written {name}")
    print("subject | true s_tau s_g | variant | G3 s_tau per replicate (sel) | median | G3 s_g median | B3 s_tau median | B3 A5 median")
    for s in SUBJECTS:
        for v in VARIANTS:
            rr = [r for r in rows if r["subject"] == s and r["variant"] == v]
            st = [r["G3"].get("s_tau", np.nan) for r in rr]
            sg = [r["G3"].get("s_g", np.nan) for r in rr]
            bt = [r["B3"].get("s_tau", np.nan) for r in rr]
            a5 = [r["B3"]["A"][4] if r["B3"].get("A") else np.nan for r in rr]
            sel = "".join(r["G3"]["selection"][0] for r in rr)
            print(f"S{s:2d} | {rr[0]['true_s_tau']:5.1f} {rr[0]['true_s_g']:.2f} | {v:7s} | {np.round(st, 1)} ({sel}) | {np.nanmedian(st):6.1f} | "
                  f"{np.nanmedian(sg):.2f} | {np.nanmedian(bt):6.1f} | {np.nanmedian(a5):.2f}")


if __name__ == "__main__":
    main()
