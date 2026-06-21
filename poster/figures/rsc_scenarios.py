#!/usr/bin/env python3
"""Poster strip, information-theory-framed: the CERTIFICATION CHANNEL under AI load.
Shannon-law banner; gate = a channel of capacity C_self; CR=R_self/C_self; panel 0 shows
the accuracy/recoverability DECOUPLING (queueing has no such notion). Panels 1-3 = the
three structural levers. -> rsc_scenarios.pdf
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

BLUE = "#1F4E79"; RED = "#C00000"; GREEN = "#2E7D32"; AMBER = "#E8902A"; GREY = "#6b6b6b"
plt.rcParams.update({"font.size": 12})


def pr(ax, x, y, fc, ec, mark="", s=0.46):
    ax.add_patch(FancyBboxPatch((x - s/2, y - s/2), s, s, boxstyle="round,pad=0.02,rounding_size=0.07",
                                fc=fc, ec=ec, lw=1.5, zorder=4))
    if mark:
        ax.text(x, y, mark, ha="center", va="center", fontsize=11, color=ec, zorder=5, weight="bold")


def arrow(ax, x0, y0, x1, y1, color, lw=2.4):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=17,
                                 color=color, lw=lw, zorder=3))


def panel(ax, title, lever, inflow, cap, backlog, cert, uncert, reversible,
          cr, cr_col, outcome, out_col, throttle=False, plusCI=False, keylever=False):
    ax.set_xlim(0, 11); ax.set_ylim(0, 10); ax.axis("off")
    ax.text(5.5, 9.55, title, ha="center", va="center", fontsize=14.5, weight="bold", color=out_col)
    ax.text(5.5, 8.8, lever, ha="center", va="center", fontsize=11, color=GREY, style="italic")

    # AI source
    ax.add_patch(FancyBboxPatch((0.25, 4.5), 1.55, 1.9, boxstyle="round,pad=0.05,rounding_size=0.12",
                                fc="#EAF0F6", ec=BLUE, lw=2, zorder=4))
    ax.text(1.02, 5.45, "AI\nagent", ha="center", va="center", fontsize=11, weight="bold", color=BLUE, zorder=7)

    # inflow = induced information rate R_self
    n = 4 if inflow == "heavy" else 2
    for i in range(n):
        y = 5.45 + (i - (n-1)/2) * 0.6
        arrow(ax, 1.9, y, 3.0, y, BLUE, lw=2.8 if inflow == "heavy" else 2.0)
    ax.text(2.45, 7.15, r"$R_{\rm self}$", ha="center", fontsize=12.5, color=BLUE, weight="bold")
    ax.text(2.45, 6.62, "induced rate", ha="center", fontsize=8.5, color=BLUE, style="italic")
    if throttle:
        ax.add_patch(plt.Circle((2.45, 5.45), 0.38, fc="white", ec=AMBER, lw=2.8, zorder=6))
        ax.text(2.45, 5.45, "✂", ha="center", va="center", fontsize=14, color=AMBER, zorder=7)
        ax.text(2.05, 4.35, "throttle\n/ batch", ha="center", va="top", fontsize=9.5, color=AMBER, weight="bold")

    # uncertified backlog before the channel -- bigger PR squares; top two = overflow past the deadline
    qx, nb = 3.35, min(backlog, 4)
    for i in range(nb):
        red = nb >= 4 and i >= nb - 2
        pr(ax, qx, 3.25 + i * 0.64, "#F6D9D9" if red else "#DCE6F2", RED if red else BLUE,
           "PR" if i == 0 else "", s=0.64)

    # the certification channel (capacity C_self, deadline inside). Title case fits the box width
    # available between the queue (left) and the outputs (right) with clear margin.
    gh = 2.4 if cap == 1 else 3.6
    cx = 5.4
    ax.add_patch(FancyBboxPatch((4.0, 5.45 - gh/2), 2.8, gh, boxstyle="round,pad=0.05,rounding_size=0.1",
                                fc="#FFF6E9" if plusCI else "#EEF3F8", ec=GREEN if plusCI else BLUE, lw=2.6, zorder=4))
    ax.text(cx, 5.45, "Certification\nChannel\n" + r"$(\leq\!\Delta t)$", ha="center", va="center", fontsize=9.5,
            weight="bold", color=GREEN if plusCI else BLUE, zorder=7)
    cap_lab = (r"capacity $C_{\rm self}\!\uparrow$" if cap == 2 else r"capacity $C_{\rm self}$")
    ax.text(cx, 5.45 - gh/2 - 0.3, cap_lab, ha="center", va="top",
            fontsize=9.5, color=GREEN if plusCI else BLUE)
    if plusCI:
        ax.text(cx, 5.45 - gh/2 - 0.94, "+reviewers / CI", ha="center", va="top", fontsize=9, color=GREEN, weight="bold")

    # certified outputs (top) -- shifted right to clear the widened channel box
    for i in range(cert):
        pr(ax, 7.35 + i*0.56, 6.85, "#DDF0DD", GREEN, "✓")
    if cert:
        ax.text(7.35 + (cert-1)*0.28, 7.7, "certified\n= recoverable", ha="center", va="bottom",
                fontsize=10, color=GREEN, weight="bold")
    # uncertified / reversible outputs (bottom) + labels (bounded to the panel)
    for i in range(uncert):
        ec, fc, mk = (AMBER, "#FCE9D6", "↺") if reversible else (RED, "#F6D2D2", "✗")
        pr(ax, 7.35, 3.65 - i*0.52, fc, ec, mk)
    if uncert and not reversible:   # THE DECOUPLING: accuracy holds (green), recoverability fails (red)
        ax.text(7.85, 3.95, "still accurate ✓", ha="left", va="center", fontsize=9.5, color=GREEN, weight="bold")
        ax.text(7.85, 3.45, "yet unrecoverable ✗", ha="left", va="center", fontsize=9.5, color=RED, weight="bold")
        ax.text(7.85, 2.85, "(it works — you\ncan't undo it)", ha="left", va="center", fontsize=8.3, color=GREY)
    elif uncert and reversible:
        ax.text(7.85, 3.7, "uncertified ✗", ha="left", va="center", fontsize=9.5, color=GREY, weight="bold")
        ax.text(7.85, 3.2, "— but undoable ↺", ha="left", va="center", fontsize=9.5, color=AMBER, weight="bold")
        ax.text(7.85, 2.7, "(flag / canary)", ha="left", va="center", fontsize=9, color=AMBER)

    arrow(ax, 6.8, 6.0, 7.35, 6.7, GREEN, lw=2.2)
    if uncert:
        arrow(ax, 6.8, 4.9, 7.35, 3.8, AMBER if reversible else RED, lw=2.2)

    # the non-obvious lever: stay above capacity, yet stay recoverable by design
    if keylever:
        ax.text(0.4, 2.68, "★ The fast lever:", ha="left", va="center", fontsize=8.5, color=AMBER, weight="bold")
        ax.text(0.4, 2.44, "Levers 1–2 pull CR below 1;", ha="left", va="center", fontsize=8, color="#333")
        ax.text(0.4, 2.20, "this leaves CR > 1 — full speed —", ha="left", va="center", fontsize=8, color="#333")
        ax.text(0.4, 1.96, "yet every commit stays undoable.", ha="left", va="center", fontsize=8, color="#333")

    # CR = R_self / C_self badge + outcome (kept inside the panel)
    ax.add_patch(FancyBboxPatch((1.9, 0.85), 7.2, 1.0, boxstyle="round,pad=0.04,rounding_size=0.2",
                                fc=cr_col, ec="none", zorder=4, alpha=0.16))
    ax.text(5.5, 1.33, cr, ha="center", va="center", fontsize=12.5, weight="bold", color=cr_col, zorder=5)
    ax.text(5.5, 0.35, outcome, ha="center", va="center", fontsize=12, weight="bold", color=out_col)


fig = plt.figure(figsize=(21, 6.9))
gs = fig.add_gridspec(2, 4, height_ratios=[1.5, 5.4], hspace=0.13, wspace=0.07)
axb = fig.add_subplot(gs[0, :]); axb.axis("off"); axb.set_xlim(0, 1); axb.set_ylim(0, 1)
axb.add_patch(FancyBboxPatch((0.01, 0.06), 0.98, 0.9, boxstyle="round,pad=0.01,rounding_size=0.015",
                             fc="#EAF0F6", ec=BLUE, lw=2.2))
axb.text(0.5, 0.74, "Shannon's law, for action — recoverability is the new reliability",
         ha="center", va="center", fontsize=17, weight="bold", color=BLUE)
axb.text(0.5, 0.42,
         r"Reliable decoding needs information rate $R<$ channel capacity $C$.   "
         r"RSC: an irreversible action stays $\bf{recoverable}$ only while $R_{\rm self}<C_{\rm self}$,",
         ha="center", va="center", fontsize=12.5, color="#222")
axb.text(0.5, 0.18,
         r"the capacity of its $\bf{certification\ channel}$.   "
         r"$\mathrm{CR}=R_{\rm self}/C_{\rm self}$ — the boundary $\mathrm{CR}=1$ is that limit.",
         ha="center", va="center", fontsize=12.5, color="#222")

axes = [fig.add_subplot(gs[1, i]) for i in range(4)]
panel(axes[0], "Above capacity — the decoupling", "AI issues commitments faster than the channel certifies",
      "heavy", 1, 5, 1, 4, False, r"$\mathrm{CR}=R_{\rm self}/C_{\rm self}=1.8>1$", RED, "recoverability lost", RED)
panel(axes[1], "Lever 1 — shape the rate", r"throttle / batch  ($R_{\rm self}\!\downarrow$)",
      "light", 1, 2, 3, 0, False, r"$\mathrm{CR}=0.7<1$", GREEN, "recoverable", GREEN, throttle=True)
panel(axes[2], "Lever 2 — grow capacity", r"widen the channel ($C_{\rm self}\!\uparrow$): +reviewers / CI",
      "heavy", 2, 2, 3, 0, False, r"$\mathrm{CR}=0.8<1$", GREEN, "recoverable", GREEN, plusCI=True)
panel(axes[3], "Lever 3 — preserve reversibility", "ship behind feature flags / canary",
      "heavy", 1, 5, 1, 4, True, r"$\mathrm{CR}=1.8$, yet…", AMBER, "still recoverable", AMBER, keylever=True)

fig.savefig("rsc_scenarios.pdf", bbox_inches="tight")
fig.savefig("rsc_scenarios.png", dpi=115, bbox_inches="tight")
print("wrote rsc_scenarios.pdf / .png")
