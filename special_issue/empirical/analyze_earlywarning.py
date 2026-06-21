#!/usr/bin/env python3
"""Leg 4 -- the critical-slowing-down EARLY WARNING on the real GitHub review queues.

Builds a weekly open-PR backlog series L(t) per repo. As a queue approaches its
stability boundary (CR -> 1), critical slowing down predicts that the detrended
backlog's ROLLING VARIANCE and LAG-1 AUTOCORRELATION should RISE *before* the
in-the-wild crossing (Scheffer 2009; van Nes & Scheffer 2007; Dakos 2012) --
the same precursor RSC derives analytically (fluctuations ~ (1-CR)^-2 vs mean
~ (1-CR)^-1). We test it on real data, with well-triaged repos as the control
(should show NO rising precursor). Trend strength = Kendall's tau of each
indicator over the run-up. -> prints tau table; writes si_earlywarning.pdf
"""
import json
from datetime import datetime, timedelta
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLOWUP = [("public-apis", "public-apis"), ("MunGell", "awesome-for-beginners"), ("vercel", "next.js")]
CONTROL = [("pallets", "flask"), ("cli", "cli")]
BLUE = "#1F4E79"; CYAN = "#0096C7"; RED = "#C00000"; GREEN = "#2E7D32"; GREY = "#666"


def dt(iso):
    return datetime.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S") if iso else None


def weekly_backlog(o, n):
    prs = json.load(open(f"/tmp/gh/{o}__{n}.json"))
    items = []
    for p in prs:
        c = dt(p.get("createdAt"))
        cl = dt(p.get("closedAt")) or dt(p.get("mergedAt"))
        if c:
            items.append((c, cl))
    c0 = min(c for c, _ in items)
    weeks = []
    t = datetime(c0.year, c0.month, c0.day)
    end = datetime(2026, 6, 1)
    while t <= end:
        weeks.append(t)
        t += timedelta(weeks=1)
    L = []
    for w in weeks:
        we = w + timedelta(weeks=1)
        L.append(sum(1 for c, cl in items if c <= we and (cl is None or cl > we)))
    return np.array(weeks), np.array(L, float)


def gauss_detrend(y, bw):
    n = len(y); x = np.arange(n); trend = np.empty(n)
    for i in range(n):
        w = np.exp(-0.5 * ((x - i) / bw) ** 2); w /= w.sum()
        trend[i] = (w * y).sum()
    return y - trend, trend


def rolling_indicators(resid, win):
    n = len(resid); var = np.full(n, np.nan); ac1 = np.full(n, np.nan)
    for i in range(win, n + 1):
        seg = resid[i - win:i]
        var[i - 1] = seg.var()
        a, b = seg[:-1], seg[1:]
        a = a - a.mean(); b = b - b.mean()
        den = np.sqrt((a * a).sum() * (b * b).sum())
        ac1[i - 1] = (a * b).sum() / den if den > 0 else np.nan
    return var, ac1


def kendall_tau(y):
    ok = ~np.isnan(y); yy = y[ok]; n = len(yy)
    if n < 5:
        return float("nan")
    num = 0
    for i in range(n):
        num += np.sign(yy[i + 1:] - yy[i]).sum()
    return num / (0.5 * n * (n - 1))


def analyze(o, n):
    weeks, L = weekly_backlog(o, n)
    m = len(L)
    bw = max(6, int(0.08 * m))        # Gaussian detrend bandwidth
    win = max(40, int(0.30 * m))      # rolling-indicator window
    resid, trend = gauss_detrend(L, bw)
    var, ac1 = rolling_indicators(resid, win)
    # evaluate trend over the run-up: from first valid indicator to the end
    return dict(weeks=weeks, L=L, trend=trend, resid=resid, var=var, ac1=ac1,
                tau_var=kendall_tau(var), tau_ac1=kendall_tau(ac1),
                Lmax=int(L.max()), label=f"{o}/{n}")


print(f"{'repo':28s} {'L0->Lmax':>12s}  {'tau(var)':>9s}  {'tau(AC1)':>9s}")
results = {}
for grp, repos in [("BLOW-UP", BLOWUP), ("CONTROL", CONTROL)]:
    print(f"--- {grp} ---")
    for o, n in repos:
        r = analyze(o, n)
        results[(o, n)] = r
        print(f"{r['label']:28s} {int(r['L'][0]):5d}->{r['Lmax']:5d}   {r['tau_var']:+9.2f}  {r['tau_ac1']:+9.2f}")

# ---- figure: 3 blow-up repos (backlog + rising variance + rising AC1) ----
fig, axes = plt.subplots(2, 3, figsize=(15, 6.4), gridspec_kw={"height_ratios": [1.25, 1]})
for j, (o, n) in enumerate(BLOWUP):
    r = results[(o, n)]; wk = r["weeks"]
    ax = axes[0, j]
    ax.plot(wk, r["L"], color=BLUE, lw=1.8, label="open-PR backlog $L(t)$")
    ax.plot(wk, r["trend"], color=GREY, lw=1.0, ls="--", label="trend")
    ax.set_title(f"{o}/{n}", fontsize=11, weight="bold", color=BLUE)
    ax.set_ylabel("backlog $L$", color=BLUE, fontsize=9)
    if j == 0:
        ax.legend(fontsize=7.5, loc="upper left")
    axv = axes[1, j]
    axv.plot(wk, r["var"] / np.nanmax(r["var"]), color=RED, lw=2.0, label=f"variance  ($\\tau$={r['tau_var']:+.2f})")
    axv.plot(wk, r["ac1"], color=CYAN, lw=2.0, label=f"lag-1 autocorr.  ($\\tau$={r['tau_ac1']:+.2f})")
    axv.set_ylim(0, 1.05); axv.set_ylabel("early-warning\nindicator", fontsize=9)
    axv.legend(fontsize=7.5, loc="upper left")
    axv.tick_params(axis="x", labelsize=7)
fig.suptitle("Leg 4 — critical-slowing-down early warning in the wild: detrended-backlog variance "
             "and autocorrelation rise before the GitHub review-queue crossing",
             y=1.0, fontsize=12.5, weight="bold", color=BLUE)
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig("/tmp/si_earlywarning.png", dpi=120, bbox_inches="tight")
fig.savefig("/tmp/si_earlywarning.pdf", bbox_inches="tight")
print("\nwrote /tmp/si_earlywarning.pdf  (+ .png)")
print(f"\nCONTROL means: tau(var)={np.mean([results[r]['tau_var'] for r in CONTROL]):+.2f}  "
      f"tau(AC1)={np.mean([results[r]['tau_ac1'] for r in CONTROL]):+.2f}")
print(f"BLOWUP  means: tau(var)={np.mean([results[r]['tau_var'] for r in BLOWUP]):+.2f}  "
      f"tau(AC1)={np.mean([results[r]['tau_ac1'] for r in BLOWUP]):+.2f}")
