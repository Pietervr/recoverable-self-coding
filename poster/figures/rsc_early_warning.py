#!/usr/bin/env python3
"""The real result: RSC reads the macrostate's fate from the microstates, in advance.
For CR<1 the curves rise (the early-warning fluctuation ~ (1-CR)^-2 FASTER than the mean
outcome ~ (1-CR)^-1, so it crosses the alarm first -- the lead time). Beyond Gamma (CR>=1)
there is no steady state: the backlog grows without bound, so BOTH signals saturate at the
'unrecoverable' ceiling -- that ceiling IS the Overload scenario (no action). The strip
locates the four rsc_scenarios panels on this CR axis: Levers 1-2 sub-critical; Overload
rides into the ceiling; Lever 3 alone reaches CR 1.8 yet stays recoverable (it acted in
the lead time). -> rsc_early_warning.pdf
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLUE = "#1F4E79"; RED = "#C00000"; GREEN = "#2E7D32"; AMBER = "#E8902A"; GREY = "#5b5b5b"
CYAN = "#0096C7"   # early-warning signal -- blue-family (a measurement), not red (danger)
plt.rcParams.update({"font.size": 13})

THR = 8.0
CEIL_R = 1.4e4         # early-warning saturates here beyond Gamma
CEIL_B = 6.0e3         # outcome (backlog) saturates here beyond Gamma
XMAX = 1.30
cr_warn = 1 - np.sqrt(0.25 / THR)   # EW crosses threshold (early)  ~0.823
cr_sr = 1 - 0.5 / THR               # SR crosses threshold (late)   ~0.9375

# sub-critical (CR<1): real scaling, smoothly capped at the ceilings
CRs = 1 - np.logspace(np.log10(0.5), -5, 700)     # 0.5 -> 0.99999, dense near 1
EWs = CEIL_R * np.tanh(0.25 / (1 - CRs) ** 2 / CEIL_R)
SRs = CEIL_B * np.tanh(0.5 / (1 - CRs) / CEIL_B)
CRr = np.linspace(1.0, XMAX, 40)                  # beyond Gamma: flat at the ceiling

fig = plt.figure(figsize=(11.8, 8.2))
gs = fig.add_gridspec(2, 1, height_ratios=[6.0, 1.8], hspace=0.07)
ax = fig.add_subplot(gs[0])
axs = fig.add_subplot(gs[1], sharex=ax)

# ---------- main plot ----------
ax.axvspan(cr_warn, 1.0, color=AMBER, alpha=0.10, zorder=0)
ax.axvspan(1.0, XMAX, color=RED, alpha=0.08, zorder=0)
for xcr in (0.70, 0.80):
    ax.plot([xcr, xcr], [0.5, THR], color=GREEN, ls=":", lw=1.5, zorder=1)

ax.semilogy(CRs, EWs, color=CYAN, lw=3.0,
            label=r"early warning: fluctuations / autocorrelation $\sim(1-\mathrm{CR})^{-2}$  (the microstates)")
ax.semilogy(CRr, np.full_like(CRr, CEIL_R), color=CYAN, lw=3.0)
ax.semilogy(CRs, SRs, color=BLUE, lw=3.0,
            label=r"outcome: mean stability ratio $\mathrm{SR}\sim(1-\mathrm{CR})^{-1}$  (the macrostate)")
ax.semilogy(CRr, np.full_like(CRr, CEIL_B), color=BLUE, lw=3.0)

ax.axhline(THR, color=GREY, ls=(0, (5, 4)), lw=1.6)
ax.text(0.505, THR * 1.2, "alarm threshold", fontsize=11, color=GREY)
ax.plot([cr_warn], [THR], 'o', color=CYAN, ms=11, zorder=6)
ax.plot([cr_sr], [THR], 'o', color=BLUE, ms=11, zorder=6)
ax.axvline(cr_warn, color=AMBER, lw=1.8, ls=":")
ax.axvline(1.0, color=RED, lw=2.4)

ax.annotate("RSC flags it here\n— from observable counts",
            xy=(cr_warn, THR), xytext=(cr_warn - 0.205, THR * 7),
            fontsize=11.5, color=CYAN, weight="bold", ha="center",
            arrowprops=dict(arrowstyle="-|>", color=CYAN, lw=1.8))
ax.text(1.01, 2.7e4, "Γ : CR = 1", fontsize=10.5, color=RED, weight="bold", ha="left", va="top")
ax.text(0.90, THR * 360, "LEAD TIME", fontsize=15, color=AMBER, weight="bold", ha="center")
ax.text(0.888, THR * 95, "★ act here\n(stage / flag / canary)", fontsize=10.5, color=AMBER, weight="bold", ha="center")

# beyond Gamma: both signals saturate at the ceiling = the Overload scenario (no action)
ax.text(1.285, CEIL_R, "early-warning (saturated)", fontsize=8.5, color=CYAN, ha="right", va="bottom")
ax.text(1.285, CEIL_B, "outcome → UNRECOVERABLE", fontsize=9, color=BLUE, weight="bold", ha="right", va="bottom")
ax.annotate("OVERLOAD\n(no action)", xy=(1.10, CEIL_B * 0.85), xytext=(1.10, 95),
            fontsize=10, color=RED, weight="bold", ha="center",
            arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.6))

ax.set_ylim(0.5, 3e4)
ax.set_ylabel("alarm level  (relative to baseline)", fontsize=12.5)
ax.set_title("RSC reads the macrostate before it forms — from the microstate fluctuations",
             fontsize=15, weight="bold", color=BLUE, pad=12)
ax.legend(loc="upper left", fontsize=10.3, framealpha=0.95)
ax.grid(alpha=0.25, which="both")
plt.setp(ax.get_xticklabels(), visible=False)

# ---------- scenario strip: where each of the four panels lives on this CR axis ----------
axs.axvspan(0.5, cr_warn, color=GREEN, alpha=0.10)
axs.axvspan(cr_warn, 1.0, color=AMBER, alpha=0.13)
axs.axvspan(1.0, XMAX, color=RED, alpha=0.10)
axs.set_ylim(0, 1); axs.set_yticks([]); axs.set_xlim(0.5, XMAX)
axs.text(0.50 + (cr_warn - 0.5) / 2, 0.9, "sub-critical — recoverable", ha="center", va="center",
         fontsize=9, color=GREEN, weight="bold")
axs.text((cr_warn + 1.0) / 2, 0.9, "lead time", ha="center", va="center", fontsize=9, color=AMBER, weight="bold")
axs.text((1.0 + XMAX) / 2, 0.9, "beyond Γ", ha="center", va="center", fontsize=9, color=RED, weight="bold")
axs.text(0.508, 0.58, "where the four\nscenarios live →", ha="left", va="center", fontsize=8.5,
         color="#444", style="italic")


def pin(x, color, lab):
    axs.plot([x], [0.64], 'o', color=color, ms=12, zorder=5)
    axs.text(x, 0.49, lab, ha="center", va="top", fontsize=8.4, color=color, weight="bold")


pin(0.70, GREEN, "Lever 1\nshape rate\nCR 0.7 ✓")
pin(0.80, GREEN, "Lever 2\ngrow cap.\nCR 0.8 ✓")
pin(1.09, RED, "Overload\nno action\nCR 1.8 ✗")
pin(1.21, AMBER, "Lever 3\nreversible\nCR 1.8 ↺")
axs.annotate("", xy=(1.21, 0.64), xytext=(1.09, 0.64), arrowprops=dict(arrowstyle="<->", color="#777", lw=1.2))
axs.text(1.15, 0.80, "same CR\nopposite outcome", ha="center", va="center", fontsize=7.6, color="#555")
axs.set_xlabel(r"approach to the boundary,  $\mathrm{CR}=R_{\rm self}/C_{\rm self}\to 1$  (and beyond)", fontsize=13)

fig.subplots_adjust(left=0.075, right=0.985, top=0.93, bottom=0.205, hspace=0.07)
fig.text(0.5, 0.03,
         "Beyond Γ (CR ≥ 1) there is no steady state: the backlog grows without bound, so BOTH signals saturate at the unrecoverable ceiling — that ceiling is the Overload scenario (no action).\n"
         "The early warning (microstate fluctuations) crosses the alarm first, opening the lead time;  Levers 1–2 keep you sub-critical;  Lever 3 alone reaches CR 1.8 yet stays recoverable — it preserved reversibility in the lead time.",
         ha="center", va="bottom", fontsize=9.8, color="#222")
fig.savefig("rsc_early_warning.pdf", bbox_inches="tight")
fig.savefig("rsc_early_warning.png", dpi=120, bbox_inches="tight")
print(f"cr_warn={cr_warn:.3f}  cr_sr={cr_sr:.3f}; wrote rsc_early_warning.pdf")
