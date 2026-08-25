"""Generate the two arXiv-v4 figures from the committed run logs.

Fig 1 (workspace_sequential.pdf): sequential drives —
  (A) E1 passive-load statics: occupancy saturation vs certification ceiling
  (B) E2 feedback closure: the alpha content effect and exact reset convergence
  (C) E2b liable load: perfect on-demand recall, near-zero standing occupancy

Fig 2 (workspace_serial.pdf): in-pass demand —
  (A) E2c span certification & accuracy flat vs the 1/M serial-staging law
  (B) staged-per-trial pinned at ~1 (the width of the commitment stage)
  (C) what is staged: the imminent slot (94% slot 1)

Run:  uv run --with matplotlib python3 make_paper_figs.py --out <figures dir>
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).parent
RUNS = HERE / "runs"

C1 = "#B4432F"  # alpha=1 / drive
C0 = "#2E5E8C"  # alpha=0 / gated
CG = "#6B6B6B"  # grey reference


def load(name: str) -> list[dict]:
    out: dict[tuple, dict] = {}
    for line in (RUNS / name).read_text().splitlines():
        r = json.loads(line)
        key = tuple(r.get(k) for k in ("alpha", "session", "step", "m", "trial", "slot", "item", "level"))
        out[key] = r
    return list(out.values())


def sem(p: float, n: int) -> float:
    return math.sqrt(max(p * (1 - p), 1e-9) / n)


def panel_e1(ax) -> None:
    recs = load("e1v2_statics.jsonl")
    levels = sorted({r["level"] for r in recs})
    occ, cert = [], []
    for k in levels:
        rs = [r for r in recs if r["level"] == k]
        occ.append(sum(r["occupancy"] for r in rs) / len(rs))
        cert.append(sum(r["certified"] for r in rs) / len(rs))
    ax.plot([0, 8.5], [0, 8.5], "--", color=CG, lw=1)
    ax.text(7.6, 5.6, "perfect\nretention", fontsize=7, color=CG,
            ha="left", va="top")
    ax.plot(levels, occ, "o-", color=C1, lw=1.5, ms=5, label="occupancy")
    ax.axhline(3, color=CG, lw=0.8, ls=":")
    ax.text(18, 3.3, r"$\approx 3$", ha="center", fontsize=8, color=CG)
    ax2 = ax.twinx()
    ax2.plot(levels, cert, "s-", color=C0, lw=1.5, ms=4,
             label="certification")
    ax2.set_ylim(0, 1.05)
    ax2.set_ylabel("certification rate", color=C0, fontsize=9)
    ax2.tick_params(axis="y", labelcolor=C0, labelsize=8)
    ax.set_ylim(0, 8)
    ax.set_xlabel(r"held concepts $K$ (passive)", fontsize=9)
    ax.set_ylabel("band occupancy (concepts)", color=C1, fontsize=9)
    ax.tick_params(labelsize=8)
    ax.tick_params(axis="y", labelcolor=C1)
    ax.set_title("(A)  passive load: occupancy saturates,\ncertification does not move",
                 fontsize=9)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=7, loc="center right", frameon=False)


def panel_e2(ax) -> None:
    recs = load("e2_hysteresis.jsonl")
    groups = [
        ("all steps", lambda r: True),
        ("probe\n(loaded ctx)", lambda r: r["branch"] == "probe"),
        ("probe\n(after reset)", lambda r: r["branch"] == "reset_probe"),
    ]
    width = 0.36
    for gi, (label, sel) in enumerate(groups):
        for ai, (a, color, name) in enumerate(
            [(1, C1, r"$\alpha=1$ (raw re-entry)"), (0, C0, r"$\alpha=0$ (gated)")]
        ):
            rs = [r for r in recs if r["alpha"] == a and sel(r)]
            p = sum(r["correct"] for r in rs) / len(rs)
            ax.bar(gi + (ai - 0.5) * width, p, width * 0.92, color=color,
                   yerr=sem(p, len(rs)), capsize=2, error_kw={"lw": 0.8},
                   label=name if gi == 0 else None)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([g[0] for g in groups], fontsize=8)
    ax.set_ylim(0.5, 1.09)
    ax.set_ylabel("accuracy", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.annotate(r"$p\approx0.013$", xy=(0, 0.897), ha="center", fontsize=7.5)
    ax.annotate("identical\n(0.767, 0.767)", xy=(2, 0.83), ha="center", fontsize=7.5)
    ax.set_title("(B)  feedback closure: content poisoning;\nreset restores the archived baseline",
                 fontsize=9)
    ax.legend(fontsize=7, loc="upper left", frameon=False)


def panel_e2b(ax) -> None:
    recs = load("e2b_collapse.jsonl")
    levels = [2, 4, 6, 8]
    qacc, occfrac, cert = [], [], []
    for L in levels:
        qs = [r for r in recs if r["kind"] == "query" and r["level"] == L]
        qacc.append(sum(r["correct"] for r in qs) / len(qs))
        fs = [r for r in recs if r["kind"] in ("fact2", "fact3") and r["level"] == L]
        occfrac.append(sum(r["occupancy"] for r in fs) / len(fs) / L)
        cert.append(sum(r["certified"] for r in fs) / len(fs))
    ax.plot(levels, qacc, "o-", color=C0, lw=1.5, ms=5,
            label="watch-query accuracy")
    ax.plot(levels, cert, "s", color=C1, ms=8, mfc="none", mew=1.4,
            label="fact-step certification")
    ax.bar(levels, occfrac, 0.9, color=CG, alpha=0.55,
           label="standing occupancy / $L$")
    ax.set_ylim(0, 1.1)
    ax.set_xticks(levels)
    ax.set_xlabel(r"liable watch-list size $L$", fontsize=9)
    ax.set_ylabel("rate", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title("(C)  liable load: perfect on-demand recall,\nnear-zero standing occupancy",
                 fontsize=9)
    ax.legend(fontsize=7, loc="center left", frameon=False)


def fig_sequential(out: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.1))
    panel_e1(axes[0])
    panel_e2(axes[1])
    panel_e2b(axes[2])
    fig.tight_layout(w_pad=2.2)
    fig.savefig(out / "workspace_sequential.pdf")
    plt.close(fig)


def fig_serial(out: Path) -> None:
    recs = load("e2c_parallel_v2.jsonl")
    ms = sorted({r["m"] for r in recs})
    span, commit, acc, staged_pt = [], [], [], []
    for m in ms:
        rs = [r for r in recs if r["m"] == m]
        span.append(sum(r["certified"] for r in rs) / len(rs))
        commit.append(sum(r["commit_staged"] for r in rs) / len(rs))
        acc.append(sum(r["correct"] for r in rs) / len(rs))
        per_trial = defaultdict(int)
        for r in rs:
            per_trial[r["trial"]] += r["commit_staged"]
        staged_pt.append(sum(per_trial.values()) / len(per_trial))

    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.1))

    ax = axes[0]
    ax.plot(ms, span, "s-", color=C0, lw=1.5, ms=4,
            label="span certification")
    ax.plot(ms, acc, "^-", color="#3C7A45", lw=1.5, ms=4, label="slot accuracy")
    ax.plot(ms, commit, "o-", color=C1, lw=1.5, ms=5,
            label="commitment-position staging")
    ax.plot(ms, [1 / m for m in ms], "--", color=CG, lw=1,
            label=r"$1/M$ (serial, width 1)")
    ax.set_ylim(0, 1.08)
    ax.set_xticks(ms)
    ax.set_xlabel(r"simultaneous chains $M$", fontsize=9)
    ax.set_ylabel("rate", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title("(A)  encoding parallel, commitment serial:\nstaging follows the $1/M$ law",
                 fontsize=9)
    ax.legend(fontsize=7, loc="center right", frameon=False)

    ax = axes[1]
    ax.plot(ms, staged_pt, "o-", color=C1, lw=1.5, ms=5)
    ax.axhline(1, color=CG, lw=0.8, ls="--")
    ax.axhline(3, color=CG, lw=0.8, ls=":")
    ax.text(5.9, 3.1, "passive capacity (E1)", ha="right", fontsize=7.5, color=CG)
    ax.text(5.9, 1.1, "width 1", ha="right", fontsize=7.5, color=CG)
    ax.set_ylim(0, 6.2)
    ax.set_xticks(ms)
    ax.set_xlabel(r"simultaneous chains $M$", fontsize=9)
    ax.set_ylabel("chains staged at commitment / trial", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title("(B)  the commitment stage holds\n$\\approx$ one live chain, independent of $M$",
                 fontsize=9)

    ax = axes[2]
    by_slot = defaultdict(lambda: [0, 0])
    for r in recs:
        if r["m"] >= 2:
            by_slot[r["slot"]][0] += r["commit_staged"]
            by_slot[r["slot"]][1] += 1
    slots = sorted(by_slot)
    rates = [by_slot[s][0] / by_slot[s][1] for s in slots]
    ax.bar(slots, rates, 0.65, color=[C1] + [CG] * (len(slots) - 1))
    ax.set_xticks(slots)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("answer slot", fontsize=9)
    ax.set_ylabel("commitment-staging rate", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.annotate("the imminent\ncommitment", xy=(1, 0.94), xytext=(2.4, 0.8),
                fontsize=7.5, arrowprops={"arrowstyle": "->", "lw": 0.8})
    ax.set_title("(C)  what is staged: the next\ncommitment, not the task set",
                 fontsize=9)

    fig.tight_layout(w_pad=2.2)
    fig.savefig(out / "workspace_serial.pdf")
    plt.close(fig)


def load_e4() -> list[dict]:
    """Complete (alpha, seed) arms only — an in-flight seed must not pool."""
    latest: dict[tuple, dict] = {}
    for line in (RUNS / "e4_loop.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r.get("exp") == "e4":
            latest[(r["alpha"], r.get("seed", 0), r["tid"])] = r
    recs = list(latest.values())
    complete = {(r["alpha"], r.get("seed", 0)) for r in recs
                if r["branch"] == "reset_drain"} | \
               {(r["alpha"], r.get("seed", 0)) for r in recs
                if r["alpha"] == 0.0 and r["branch"] == "down" and r["l"] == 0.4}
    return [r for r in recs if (r["alpha"], r.get("seed", 0)) in complete]


def fig_loop(out: Path) -> None:
    recs = load_e4()
    seeds = sorted({r.get("seed", 0) for r in recs})

    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.1))

    # (A) the hysteresis loop, pooled over seeds; faint per-seed up-branches
    # show the individual discontinuous steps the pooling smooths over
    ax = axes[0]
    for s in seeds:
        pts = defaultdict(list)
        for r in recs:
            if (r["alpha"] == 0.8 and r.get("seed", 0) == s
                    and r["branch"] == "up"):
                pts[r["l"]].append(r["uncert"])
        xs = sorted(pts)
        ax.plot(xs, [sum(pts[l]) / len(pts[l]) for l in xs], "-",
                color=C1, lw=0.7, alpha=0.35)
    for a, color, lab in ((0.8, C1, r"$\alpha=0.8$"), (0.0, C0, r"$\alpha=0$")):
        for br, ls, mk, mfc in (("up", "-", "o", None), ("down", "--", "o", "none")):
            pts = defaultdict(list)
            for r in recs:
                if r["alpha"] == a and r["branch"] == br:
                    pts[r["l"]].append(r["uncert"])
            ls_x = sorted(pts)
            ls_y = [sum(pts[l]) / len(pts[l]) for l in ls_x]
            ax.plot(ls_x, ls_y, ls, marker=mk, color=color, ms=5, lw=1.4,
                    mfc=mfc or color,
                    label=lab if br == "up" else None)
    ax.annotate("", xy=(0.66, 0.62), xytext=(0.56, 0.30),
                arrowprops={"arrowstyle": "->", "color": C1, "lw": 1})
    ax.annotate("", xy=(0.55, 0.985), xytext=(0.75, 0.985),
                arrowprops={"arrowstyle": "->", "color": C1, "lw": 1})
    ax.set_xlabel(r"utilization $\ell$", fontsize=9)
    ax.set_ylabel(r"uncertified fraction $P_{\mathrm{u}}$", fontsize=9)
    ax.set_ylim(-0.04, 1.08)
    ax.tick_params(labelsize=8)
    ax.set_title(f"(A)  the loop-level hysteresis cycle\n({len(seeds)} seed"
                 f"{'s' if len(seeds) > 1 else ''}, pooled; solid up, dashed down)",
                 fontsize=9)
    ax.legend(fontsize=7, loc="center left", frameon=False)

    # (B) one realization end-to-end: backlog trajectory incl. resets
    ax = axes[1]
    s0 = sorted((r for r in recs if r["alpha"] == 0.8 and r.get("seed", 0) == seeds[0]),
                key=lambda r: r["tid"])
    ys = [r["queue_after"] for r in s0]
    ax.plot(range(len(s0)), ys, "-", color=C1, lw=1.2)
    marks = {}
    for i, r in enumerate(s0):
        marks.setdefault(r["branch"], i)
    for j, (br, lab) in enumerate((("up", "ramp up"), ("down", "ramp down"),
                                   ("reset_ctx", "ctx clear"),
                                   ("drain", "drain"),
                                   ("reset_drain", "probe"))):
        if br in marks:
            ax.axvline(marks[br], color=CG, lw=0.6, ls=":")
            ax.text(marks[br] + 2, max(ys) * (1.0 - 0.08 * (j % 2)), lab,
                    fontsize=6.5, color=CG, va="top")
    ax.set_xlabel(f"served tasks (seed {seeds[0]}, whole protocol)", fontsize=9)
    ax.set_ylabel("backlog (queued tasks)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title("(B)  backlog as the memory: growth,\npinning, and the failed partial cures",
                 fontsize=9)

    # (C) mechanism: static state vs closed loop
    ax = axes[2]
    fx = json.loads((RUNS / "e4_forensics.json").read_text())
    # "closed loop" = exo accuracy in post-runaway up-branch dwells,
    # aligned per seed (runaway = first l with P_u >= 0.9 and q_end > 5)
    inloop = []
    for s in seeds:
        srecs = [r for r in recs if r["alpha"] == 0.8
                 and r.get("seed", 0) == s and r["branch"] == "up"]
        by_l = defaultdict(list)
        for r in srecs:
            by_l[r["l"]].append(r)
        runaway = None
        for l in sorted(by_l):
            rs = by_l[l]
            pu = sum(r["uncert"] for r in rs) / len(rs)
            if pu >= 0.9 and rs[-1]["queue_after"] > 5:
                runaway = l
                break
        if runaway is not None:
            inloop += [r for r in srecs
                       if r["l"] >= runaway and r["kind"] == "exo"]
    inloop_acc = sum(r["correct"] for r in inloop) / len(inloop)
    labels = ["clean\nwindow", "repair fmt\n(correct)", "repair fmt\n(wrong)",
              "the closed\nloop"]
    vals = [fx["clean"]["accuracy"], fx["fmt"]["accuracy"],
            fx["poison"]["accuracy"], inloop_acc]
    colors = [CG, CG, CG, C1]
    ax.bar(range(4), vals, 0.62, color=colors)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.025, f"{v:.2f}", ha="center", fontsize=7.5)
    ax.set_xticks(range(4))
    ax.set_xticklabels(labels, fontsize=7.5)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("two-hop accuracy", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title("(C)  static corruption is nearly harmless;\nthe instability lives in the re-entry",
                 fontsize=9)

    fig.tight_layout(w_pad=2.2)
    fig.savefig(out / "workspace_loop.pdf")
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.size": 9, "axes.linewidth": 0.8,
        "font.family": "serif", "mathtext.fontset": "cm",
        "pdf.fonttype": 42,
    })
    fig_sequential(out)
    fig_serial(out)
    fig_loop(out)
    print(f"wrote workspace_sequential.pdf, workspace_serial.pdf, "
          f"workspace_loop.pdf to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
