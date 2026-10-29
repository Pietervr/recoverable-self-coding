"""Descriptive facts for REPORT.md: the two-state generators' component separation in noise-SD units at the declared
levels (a design fact of the frozen generators, read from the assets), the T1-vs-E1 variance profiles, the REAL and O5
rows, and the per-setting medians. Reads outputs; computes no new test."""
import json
import os
import sys

import numpy as np
import pandas as pd

JIT = os.path.expanduser("~/Recoverable-Self-Coding/workspace_demo/sergent_port/jitter")
OUT = os.path.join(JIT, "reviews", "brain_side_alt_tests_2026-10-28")
sys.path.insert(0, JIT)
sys.path.insert(0, os.path.dirname(JIT))
os.environ.setdefault("NPROC", "1")
import s4  # noqa: E402
import models as M  # noqa: E402
import data as D  # noqa: E402

np.set_printoptions(precision=2, suppress=True, linewidth=160)
b = M.basis("whole")
# T~ at zero shift on the 53 windows: mean over each window's 16 sample times of the spline
import simulate as S  # noqa: E402
rows = []
for s in s4.SUBJECTS:
    cfg = s4.load_config(s, "B3")
    T = S.template_windows(cfg, np.zeros(1))[0]                     # (53,)
    Tp = T[D.PRIMARY_WINDOWS]
    sd = np.sqrt(np.diag(cfg.Sigma))[D.PRIMARY_WINDOWS]
    w = int(np.argmax(np.abs(Tp)))
    for k in (2, 3, 4):
        mH = cfg.a[k] / cfg.A[k]
        rows.append(dict(S=s, k=k, A=cfg.A[k], sep_peak_sd=abs(mH * Tp[w]) / sd[w], sep_mean_sd=float(np.mean(np.abs(mH * Tp) / sd)),
                         sep_peak_sd_T2=abs(cfg.a[k] / (cfg.A[k] / 2) * Tp[w]) / sd[w]))
df = pd.DataFrame(rows)
print("B3 generators: high-branch separation m_H(k) * T~(w) in units of the noise SD at that window")
for k in (2, 3, 4):
    d = df[df.k == k]
    print(f" level {k}: A median {d.A.median():.2f}; separation at the template's peak primary window: median {d.sep_peak_sd.median():.2f}, "
          f"range {d.sep_peak_sd.min():.2f}-{d.sep_peak_sd.max():.2f}; mean over the 16 windows: median {d.sep_mean_sd.median():.2f}; "
          f"T2 (occupancy halved) peak: median {d.sep_peak_sd_T2.median():.2f}, range {d.sep_peak_sd_T2.min():.2f}-{d.sep_peak_sd_T2.max():.2f}")
tot = json.load(open(os.path.join(OUT, "totals.json")))
for s in ("T1", "E1", "O5", "REAL", "W1", "W2", "W3", "W4", "T2"):
    t = tot[s]
    print(s, "V_raw", np.array(t["V_level_mean_raw"]), "kstar", t["kstar_hist_raw"], "bic10 nwin med", t["bic10_nwin_median"],
          "burst nwin med", t["burst_nwin_median"], "dbic max med/max %.0f/%.0f" % (t["dbic_max_declared_median"], t["dbic_max_declared_max"]),
          "dip min p %.3f" % t["dip_min_p_declared_min"])
sets = pd.read_csv(os.path.join(OUT, "sets.csv"))
real = sets[sets.setting == "REAL"].iloc[0]
print("REAL:", {k: real[k] for k in ("dip_run3", "dip_any", "bic10_run3", "bic10_nwin", "bic10_run3_s", "bic10_nwin_s", "bic0_run3_s", "burst_run3", "burst_nwin",
                                     "burst_run3_s", "burst_m0_nwin", "burst_kstar_hist", "burst_kstar_hist_s", "dip_min_p_declared", "dbic_max_declared",
                                     "dbic_max_declared_s", "V_level_mean", "V_level_mean_s", "n_trials")})
for s in ("T1", "E1"):
    sub = sets[sets.setting == s]
    print(s, "burst_any", int(sub.burst_any.sum()), "burst_run3", int(sub.burst_run3.sum()), "burst_nwin mean %.2f" % sub.burst_nwin.mean(),
          "burst_m0_any", int(sub.burst_m0_any.sum()), "scaled: bic10_run3_s", int(sub.bic10_run3_s.sum()), "bic10_any_s", int(sub.bic10_any_s.sum()),
          "dbic_max_declared_s median %.1f max %.1f" % (sub.dbic_max_declared_s.median(), sub.dbic_max_declared_s.max()))
# per-window burst rate by window for T1 and E1 (which windows)
win = pd.read_csv(os.path.join(OUT, "windows.csv"), usecols=["setting", "r", "window", "level", "V_raw", "dbic_raw", "dbic_scaled", "dip_p_raw", "mu_lo_scaled", "mu_hi_scaled", "w_min_scaled"])
for s in ("T1", "E1", "W1", "O5"):
    w = win[(win.setting == s)]
    V = w.pivot_table(index=["r", "window"], columns="level", values="V_raw").values.reshape(-1, 16, 6)
    kstar = V.argmax(axis=2)
    ends = np.maximum(V[:, :, 0], V[:, :, 5])
    peak = V[np.arange(V.shape[0])[:, None], np.arange(16)[None, :], kstar]
    ratio = peak / ends
    print(s, "V(k*)/max(V0,V5) over sets x windows: median %.3f p90 %.3f p99 %.3f max %.3f; share >= 1.10: %.3f; interior share %.3f" %
          (np.median(ratio), np.quantile(ratio, 0.9), np.quantile(ratio, 0.99), ratio.max(), np.mean(ratio >= 1.10), np.mean((kstar >= 1) & (kstar <= 4))))
# scaled GMM on T2 vs T1: component separation found
for s in ("T1", "T2", "W2", "O5"):
    w = win[(win.setting == s) & (win.level == 3)]
    print(s, "level 3 scaled GMM: |mu_hi-mu_lo| median %.2f, w_min median %.2f, dbic_scaled median %.1f; dbic_raw median %.1f" %
          (np.median(w.mu_hi_scaled - w.mu_lo_scaled), np.median(w.w_min_scaled), np.median(w.dbic_scaled), np.median(w.dbic_raw)))
