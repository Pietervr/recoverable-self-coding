"""Expected held-out log-density loss of each shared-noise construction on catch-like data: KL(N(mu, Sigma_gen[P]) ||
N(mu_hat, Sigma_hat)) averaged over 200 draws of n_catch training catch trials, for the 20 generator Sigmas.
Also the variance ratio along the zero-shift template.  Tells whether the oracle's 0.88 nat/trial is plain
estimation error and which construction is predictively best."""
import os, sys
sys.path.insert(0, "/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/sergent_port/jitter")
import numpy as np
import data as D, s2, simulate as S

P = D.PRIMARY_WINDOWS
rng = np.random.default_rng(0)
bases = s2.load_bases()


def kl(Sig, Sh, delta):
    Shi = np.linalg.inv(Sh)
    p = Sig.shape[0]
    return 0.5 * (np.trace(Shi @ Sig) - p + np.linalg.slogdet(Sh)[1] - np.linalg.slogdet(Sig)[1] + delta @ Shi @ delta)


print("S | n_catch(train~) | KL per trial: LW  sample  sample_scaled  diag | var ratio along template: LW sample diag | LW rho | cond(Sigma)")
acc = {k: [] for k in ("LW", "sample", "sample_scaled", "diag")}
for s in range(1, 21):
    cfg = s2.load_config(s, "G3")
    Sig = cfg.Sigma[np.ix_(P, P)]
    n_catch_total = int(np.sum(np.asarray(bases[str(s)]["levels"]) == 0))
    n = int(round(n_catch_total * 0.8))
    t0 = S.template_windows(cfg, np.zeros(1))[0, P]
    L = np.linalg.cholesky(Sig)
    res = {k: [] for k in acc}
    vr = {k: [] for k in ("LW", "sample", "diag")}
    p = Sig.shape[0]
    for rep in range(200):
        Xc = rng.standard_normal((n, p)) @ L.T
        mu_hat = Xc.mean(axis=0)
        X = Xc - mu_hat
        Smat = X.T @ X / n
        lw, rho = D.ledoit_wolf(X)
        cands = dict(LW=lw, sample=Smat, sample_scaled=Smat * (n - 1.0) / (n - p - 2.0),
                     diag=(1 - rho) * Smat + rho * np.diag(np.diag(Smat)))
        for k, Sh in cands.items():
            res[k].append(kl(Sig, Sh, -mu_hat))
        for k in vr:
            vr[k].append((t0 @ Sig @ t0) / (t0 @ cands[k] @ t0))
    for k in acc:
        acc[k].append(np.mean(res[k]))
    ev = np.linalg.eigvalsh(Sig)
    print(f"S{s:2d} | {n:3d} | {np.mean(res['LW']):.3f} {np.mean(res['sample']):.3f} {np.mean(res['sample_scaled']):.3f} {np.mean(res['diag']):.3f} | "
          f"{np.mean(vr['LW']):.3f} {np.mean(vr['sample']):.3f} {np.mean(vr['diag']):.3f} | {rho:.3f} | {ev[-1] / ev[0]:.0f}")
print("MEAN KL per trial:", {k: round(float(np.mean(v)), 3) for k, v in acc.items()})
