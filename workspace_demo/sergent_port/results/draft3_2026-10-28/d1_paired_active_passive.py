"""D1 (R052 SI draft 3, deep-read decision D1, option C): descriptive paired active-minus-passive comparison.

For each participant and window, the two-state model's held-out advantage over the graded model is
    a = S_3 - S_2B   (the port's score: mean over five block folds of the held-out fold's summed log-likelihood,
                      llh_<session>.csv), and per trial a / n, n = the participant's mean held-out trials per fold.
The paired difference active minus passive is reported per window (315 ms and the 435-495 ms plateau) and for the
plateau average, with the mean, SD, a paired t across the 20 participants and the count with active > passive.

DESCRIPTIVE ONLY. The two sessions use separately trained decoders (the passive decoder for S11-S20 is trained on the
seventh level, -3 dB; the max6 variant trains it on the sixth, as the active decoder is), so the readout scales differ
and the paired t is not a test of a difference in the latent process. No refitting: saved tables only.

Reads: ../llh_active.csv, ../llh_passive.csv, ../llh_passive_max6.csv, ../fits_<...>.csv (n_test).
Writes: d1_paired_active_passive.csv and d1_paired_active_passive.txt beside this script.
"""
import os

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)
WINDOWS = [315, 435, 465, 495]
PLATEAU = [435, 465, 495]
lines = []


def say(s=""):
    print(s)
    lines.append(s)


def adv(tag):
    llh = pd.read_csv(os.path.join(RES, f"llh_{tag}.csv"))
    fits = pd.read_csv(os.path.join(RES, f"fits_{tag}.csv"))
    n = fits[fits.model == "model3"].groupby(["subject", "window"]).n_test.mean().rename("n").reset_index()
    d = llh.merge(n, on=["subject", "window"])
    d["adv_fold"] = d.model3 - d.model2B
    d["adv_trial"] = d.adv_fold / d.n
    return d[["subject", "t_ms", "adv_fold", "adv_trial", "n"]]


act = adv("active")
rows = []
for ptag in ["passive", "passive_max6"]:
    pas = adv(ptag)
    m = act.merge(pas, on=["subject", "t_ms"], suffixes=("_a", "_p"))
    say(f"=== active minus {ptag}: participants {m.subject.nunique()}")
    say(f"  {'window':>14} {'unit':>6} {'mean act':>9} {'mean pas':>9} {'mean diff':>10} {'SD diff':>8} "
        f"{'t(19)':>7} {'p two-sided':>11} {'act>pas':>8} {'act>0':>6} {'pas>0':>6}")
    for lab, sel in [(str(w), [w]) for w in WINDOWS] + [("435-495 mean", PLATEAU)]:
        g = m[m.t_ms.isin(sel)].groupby("subject")[["adv_fold_a", "adv_fold_p", "adv_trial_a", "adv_trial_p"]].mean()
        for unit in ["fold", "trial"]:
            a, p = g[f"adv_{unit}_a"].to_numpy(), g[f"adv_{unit}_p"].to_numpy()
            dlt = a - p
            t, pv = stats.ttest_rel(a, p)
            rows.append(dict(passive=ptag, window=lab, unit=unit, n=len(dlt), mean_active=a.mean(),
                             mean_passive=p.mean(), mean_diff=dlt.mean(), sd_diff=dlt.std(ddof=1), t=t, p=pv,
                             n_active_gt_passive=int((dlt > 0).sum()), n_active_pos=int((a > 0).sum()),
                             n_passive_pos=int((p > 0).sum())))
            fmt = ".3f" if unit == "fold" else ".5f"
            say(f"  {lab:>14} {unit:>6} {a.mean():>9{fmt}} {p.mean():>9{fmt}} {dlt.mean():>10{fmt}} "
                f"{dlt.std(ddof=1):>8{fmt}} {t:>7.2f} {pv:>11.4f} {int((dlt > 0).sum()):>8} {int((a > 0).sum()):>6} "
                f"{int((p > 0).sum()):>6}")
    say()

pd.DataFrame(rows).to_csv(os.path.join(HERE, "d1_paired_active_passive.csv"), index=False, float_format="%.6g")
with open(os.path.join(HERE, "d1_paired_active_passive.txt"), "w") as f:
    f.write("\n".join(lines) + "\n")
