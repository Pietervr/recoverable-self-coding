"""D12 (R052 SI draft 3, deep-read decision D12): sensitivity of the reproduced pxp curve to the score scale.

The port keeps the authors' convention: a participant's evidence for a model at a window is the MEAN over the five
block folds of the held-out fold's summed log-likelihood (README step 3; llh_<session>.csv). The random-effects
posterior of spm_BMS depends on the absolute scale of these scores (Rigoux et al. 2014), so this script reruns the
group Bayesian model selection on the fold-SUMMED held-out log-likelihood (five times the fold mean when all five
folds are present) and reports, at every window and in particular at 315 ms and 435-495 ms:
  - the three-model (null, unimodal non-linear 2B, bifurcation 3) pxp, xp and Bayesian omnibus risk (BOR);
  - the two-model (2B vs 3) pxp, xp and BOR;
for both scales, plus the first window with pxp(3) > 0.95, the first run of three, and the windows above 0.95.

Tie: the fold-mean three-model run reproduces results/bms_<session>.csv (same rng seed 0 sequence, 1e6 samples) and
the two-model run reproduces results/bms_two_model_<session>.csv; the fold sums are recomputed from fits_<session>.csv
(test_llh per fold) and their mean is checked against llh_<session>.csv.

Reads: ../fits_<session>.csv, ../llh_<session>.csv, ../bms_<session>.csv, ../bms_two_model_<session>.csv.
Writes: d12_fold_sum_bms_<session>.csv and d12_fold_sum_bms.txt beside this script.
"""
import os, sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)
sys.path.insert(0, os.path.dirname(RES))
from bms import simes_threshold, spm_bms  # noqa: E402

M3 = ["model0", "model2B", "model3"]
KEY = [255, 285, 315, 345, 375, 405, 435, 465, 495, 525, 555, 585, 615, 645]
lines = []


def say(s=""):
    print(s)
    lines.append(s)


def first_run(t, mask, k=3):
    for i in range(len(mask) - k + 1):
        if mask[i:i + k].all():
            return int(t[i])
    return None


for session in ["active", "passive"]:
    fits = pd.read_csv(os.path.join(RES, f"fits_{session}.csv"))
    llh = pd.read_csv(os.path.join(RES, f"llh_{session}.csv"))
    nfold = fits.groupby(["subject", "window", "model"]).fold.nunique()
    fsum = fits.groupby(["subject", "window", "model"]).test_llh.sum().unstack("model").reset_index()
    fmean = fits.groupby(["subject", "window", "model"]).test_llh.mean().unstack("model").reset_index()
    chk = llh.merge(fmean, on=["subject", "window"], suffixes=("", "_re"))
    tie_llh = max(float(np.max(np.abs(chk[m] - chk[m + "_re"]))) for m in M3)
    say(f"=== {session}: folds per (subject, window, model) min {nfold.min()} max {nfold.max()}; "
        f"fold-mean recomputed vs llh_{session}.csv max |diff| {tie_llh:.2e} (saved tables written to six significant figures)")
    subjects = np.sort(llh.subject.unique())
    windows = np.sort(llh.window.unique())
    tms = llh.groupby("window").t_ms.first()

    rows = []
    rng_mean, rng_sum = np.random.default_rng(0), np.random.default_rng(0)
    for w in windows:
        dm = llh[llh.window == w].set_index("subject").loc[subjects][M3].to_numpy()
        ds = fsum[fsum.window == w].set_index("subject").loc[subjects][M3].to_numpy()
        r3m = spm_bms(dm, rng=rng_mean)
        r3s = spm_bms(ds, rng=rng_sum)
        r2m = spm_bms(dm[:, 1:])
        r2s = spm_bms(ds[:, 1:])
        rows.append(dict(window=w, t_ms=float(tms[w]),
                         pxp3_mean=r3m["pxp"][2], xp3_mean=r3m["xp"][2], bor3_mean=r3m["bor"],
                         pxp2B_mean=r3m["pxp"][1], pxp0_mean=r3m["pxp"][0],
                         pxp3_sum=r3s["pxp"][2], xp3_sum=r3s["xp"][2], bor3_sum=r3s["bor"],
                         pxp2B_sum=r3s["pxp"][1], pxp0_sum=r3s["pxp"][0],
                         two_pxp3_mean=r2m["pxp"][1], two_xp3_mean=r2m["xp"][1], two_bor_mean=r2m["bor"],
                         two_pxp3_sum=r2s["pxp"][1], two_xp3_sum=r2s["xp"][1], two_bor_sum=r2s["bor"],
                         n_m3_wins=int(np.sum(ds[:, 2] > ds[:, 1]))))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(HERE, f"d12_fold_sum_bms_{session}.csv"), index=False, float_format="%.6g")

    pub3 = pd.read_csv(os.path.join(RES, f"bms_{session}.csv"))
    pub2 = pd.read_csv(os.path.join(RES, f"bms_two_model_{session}.csv"))
    say(f"tie three-model fold-mean pxp3 vs bms_{session}.csv: max |diff| "
        f"{np.max(np.abs(out.pxp3_mean - pub3.pxp_model3)):.2e}; BOR {np.max(np.abs(out.bor3_mean - pub3.bor)):.2e}")
    say(f"tie two-model fold-mean pxp3 vs bms_two_model_{session}.csv: max |diff| "
        f"{np.max(np.abs(out.two_pxp3_mean - pub2.pxp_model3)):.2e}; BOR {np.max(np.abs(out.two_bor_mean - pub2.bor)):.2e}")

    t = out.t_ms.to_numpy()
    for lab, col in [("three-model, fold mean", "pxp3_mean"), ("three-model, fold sum", "pxp3_sum"),
                     ("two-model, fold mean", "two_pxp3_mean"), ("two-model, fold sum", "two_pxp3_sum")]:
        m = out[col].to_numpy() > 0.95
        first = int(t[m][0]) if m.any() else None
        say(f"  {lab:<24} first pxp3 > 0.95: {first}; first run of three: {first_run(t, m)}; "
            f"windows > 0.95: {t[m].astype(int).tolist()}")
    # The paper's Table tab:human summaries for the three-model curve, on both scales: the first run of at least three
    # consecutive windows in which M3 has the HIGHEST pxp at any value (RESULTS_sergent.md definition, not the > 0.95 run
    # above), the Simes set (strict '<' of the authors' plotting code, and BH '<='), and the first window after the
    # plateau at which the graded model is again highest.
    for lab, sfx in [("fold mean", "mean"), ("fold sum", "sum")]:
        p0, p2, p3 = (out[f"pxp{m}_{sfx}"].to_numpy() for m in ("0", "2B", "3"))
        hi3 = (p3 > p2) & (p3 > p0)
        hi2 = (p2 > p3) & (p2 > p0)
        thr, bh = simes_threshold(1 - p3)
        strict = (1 - p3 < thr) if not np.isnan(thr) else np.zeros(len(p3), dtype=bool)
        back = [int(x) for x, h in zip(t, hi2) if h and x > 555]
        say(f"  three-model, {lab:<10} first run of three with M3 highest (any value): {first_run(t, hi3)}; "
            f"Simes strict: {t[strict].astype(int).tolist()}; BH: {t[bh].astype(int).tolist()}; "
            f"first window after 555 ms with M2B highest: {back[0] if back else None}")
    say(f"  {'t_ms':>5} {'pxp3 mean':>10} {'BOR mean':>9} {'pxp3 sum':>9} {'BOR sum':>9} {'xp3 sum':>8} | "
        f"{'2m pxp3 mean':>12} {'2m BOR mean':>11} {'2m pxp3 sum':>11} {'2m BOR sum':>10} {'2m xp3 sum':>10} {'M3>2B':>6}")
    for tm in KEY:
        r = out[np.isclose(out.t_ms, tm)].iloc[0]
        say(f"  {tm:>5} {r.pxp3_mean:>10.3f} {r.bor3_mean:>9.3g} {r.pxp3_sum:>9.3f} {r.bor3_sum:>9.3g} {r.xp3_sum:>8.3f} | "
            f"{r.two_pxp3_mean:>12.3f} {r.two_bor_mean:>11.3f} {r.two_pxp3_sum:>11.3f} {r.two_bor_sum:>10.3f} "
            f"{r.two_xp3_sum:>10.3f} {int(r.n_m3_wins):>6}")
    say()

with open(os.path.join(HERE, "d12_fold_sum_bms.txt"), "w") as f:
    f.write("\n".join(lines) + "\n")
