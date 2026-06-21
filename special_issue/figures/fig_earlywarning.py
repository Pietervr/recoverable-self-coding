#!/usr/bin/env python3
"""Leg 4 (paper figure): critical-slowing-down early warning in real GitHub review queues.
(a) a representative crossing repo: weekly open-PR backlog with detrended-residual rolling
variance and lag-1 autocorrelation rising ahead of the crossing; (b) the Kendall-tau trend
of both indicators for crossing vs well-managed repos -- positive only where the boundary is
crossed. AR(1)-surrogate p-values are printed. -> figures/si_earlywarning.pdf
Reads pinned snapshots in /tmp/gh (override GH_DATA).
"""
import os, json
from datetime import datetime, timedelta
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

GH = os.environ.get("GH_DATA", "/tmp/gh")
BLOWUP = [("public-apis", "public-apis"), ("MunGell", "awesome-for-beginners"), ("vercel", "next.js")]
CONTROL = [("pallets", "flask"), ("cli", "cli")]
HERO = ("vercel", "next.js")
BLUE = "#1F4E79"; CYAN = "#0096C7"; RED = "#C00000"; GREEN = "#2E7D32"; GREY = "#666"
rng = np.random.RandomState(7)


def dt(iso):
    return datetime.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S") if iso else None


def weekly_backlog(o, n):
    prs = json.load(open(f"{GH}/{o}__{n}.json"))
    items = [(dt(p.get("createdAt")), dt(p.get("closedAt")) or dt(p.get("mergedAt")))
             for p in prs if p.get("createdAt")]
    c0 = min(c for c, _ in items)
    weeks, t, end = [], datetime(c0.year, c0.month, c0.day), datetime(2026, 6, 1)
    while t <= end:
        weeks.append(t); t += timedelta(weeks=1)
    L = [sum(1 for c, cl in items if c <= w + timedelta(weeks=1) and (cl is None or cl > w + timedelta(weeks=1)))
         for w in weeks]
    return np.array(weeks), np.array(L, float)


def detrend(y, bw):
    n = len(y); x = np.arange(n); tr = np.array([(np.exp(-0.5 * ((x - i) / bw) ** 2) /
                np.exp(-0.5 * ((x - i) / bw) ** 2).sum() * y).sum() for i in range(n)])
    return y - tr, tr


def indicators(r, win):
    n = len(r); var = np.full(n, np.nan); ac1 = np.full(n, np.nan)
    for i in range(win, n + 1):
        s = r[i - win:i]; var[i - 1] = s.var()
        a, b = s[:-1] - s[:-1].mean(), s[1:] - s[1:].mean()
        d = np.sqrt((a * a).sum() * (b * b).sum()); ac1[i - 1] = (a * b).sum() / d if d > 0 else np.nan
    return var, ac1


def ktau(y):
    ok = ~np.isnan(y); yy = y[ok]; m = len(yy)
    if m < 5:
        return float("nan")
    return sum(np.sign(yy[i + 1:] - yy[i]).sum() for i in range(m)) / (0.5 * m * (m - 1))


def ar1_surrogate_p(resid, win, tau_obs, nsur=400):
    """p = fraction of AR(1) surrogates with tau(AC1) >= observed (one-sided)."""
    x = resid[~np.isnan(resid)]
    a0, a1 = x[:-1] - x[:-1].mean(), x[1:] - x[1:].mean()
    phi = float(np.clip((a0 * a1).sum() / (a0 * a0).sum(), -0.99, 0.99))
    sig = np.std(x) * np.sqrt(max(1e-9, 1 - phi ** 2)); n = len(x); hits = 0
    for _ in range(nsur):
        s = np.empty(n); s[0] = rng.randn() * np.std(x)
        e = rng.randn(n) * sig
        for i in range(1, n):
            s[i] = phi * s[i - 1] + e[i]
        _, ac = indicators(s, win)
        if ktau(ac) >= tau_obs:
            hits += 1
    return (hits + 1) / (nsur + 1)


def analyze(o, n):
    wk, L = weekly_backlog(o, n); m = len(L)
    bw, win = max(6, int(0.08 * m)), max(40, int(0.30 * m))
    res, tr = detrend(np.log1p(L), bw); var, ac1 = indicators(res, win)  # log-backlog: variance not level-confounded
    return dict(wk=wk, L=L, tr=tr, var=var, ac1=ac1, res=res, win=win,
                tv=ktau(var), ta=ktau(ac1), label=f"{o}/{n}")


R = {(o, n): analyze(o, n) for o, n in BLOWUP + CONTROL}
print(f"{'repo':28s} {'tau(var)':>9s} {'tau(AC1)':>9s} {'p(AC1)':>8s}")
for grp in (BLOWUP, CONTROL):
    for o, n in grp:
        r = R[(o, n)]
        p = ar1_surrogate_p(r["res"], r["win"], r["ta"]) if (o, n) in BLOWUP else float("nan")
        r["p"] = p
        print(f"{r['label']:28s} {r['tv']:+9.2f} {r['ta']:+9.2f} {p:8.3f}")

# ---------- figure ----------
fig, (axA, axB) = plt.subplots(1, 2, figsize=(12.4, 4.5), gridspec_kw={"width_ratios": [1.35, 1]})
h = R[HERO]; wk = h["wk"]
axA.plot(wk, h["L"], color=BLUE, lw=1.8, label="open-PR backlog $L(t)$")
axA.set_ylabel("backlog $L$", color=BLUE); axA.tick_params(axis="y", labelcolor=BLUE)
axA.set_title(f"(a)  {HERO[0]}/{HERO[1]} — backlog and its early-warning indicators", fontsize=10.5, weight="bold")
ax2 = axA.twinx()
ax2.plot(wk, h["var"] / np.nanmax(h["var"]), color=RED, lw=2.0, label=f"variance ($\\tau$={h['tv']:+.2f})")
ax2.plot(wk, h["ac1"], color=CYAN, lw=2.0, label=f"lag-1 autocorr. ($\\tau$={h['ta']:+.2f})")
ax2.set_ylabel("early-warning indicator (rising)", color=GREY); ax2.set_ylim(0, 1.05)
l1, lb1 = axA.get_legend_handles_labels(); l2, lb2 = ax2.get_legend_handles_labels()
axA.legend(l1 + l2, lb1 + lb2, fontsize=8, loc="upper left")

# panel b: tau contrast
names = [R[r]["label"].split("/")[-1] for r in BLOWUP + CONTROL]
tv = [R[r]["tv"] for r in BLOWUP + CONTROL]; ta = [R[r]["ta"] for r in BLOWUP + CONTROL]
y = np.arange(len(names))[::-1]
axB.barh(y + 0.18, tv, height=0.34, color=RED, alpha=0.85, label="variance")
axB.barh(y - 0.18, ta, height=0.34, color=CYAN, alpha=0.95, label="lag-1 autocorr.")
axB.axvline(0, color="k", lw=0.8)
axB.set_yticks(y); axB.set_yticklabels(names, fontsize=9)
axB.set_xlabel(r"Kendall's $\tau$ trend of the indicator")
axB.set_title("(b)  rises only where the boundary is crossed", fontsize=10.5, weight="bold")
axB.axhspan(1.5, 4.5, color=RED, alpha=0.05); axB.axhspan(-0.5, 1.5, color=GREEN, alpha=0.05)
axB.text(0.97, 4.0, "crossing", color=RED, fontsize=8, ha="right", transform=axB.get_yaxis_transform())
axB.text(0.97, 0.5, "well-managed", color=GREEN, fontsize=8, ha="right", transform=axB.get_yaxis_transform())
axB.legend(fontsize=8, loc="lower right")
fig.tight_layout()
fig.savefig("si_earlywarning.pdf", bbox_inches="tight")
fig.savefig("/tmp/si_earlywarning_paper.png", dpi=120, bbox_inches="tight")
print("wrote figures/si_earlywarning.pdf")
