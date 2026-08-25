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
    print(f"wrote {out}/workspace_sequential.pdf and {out}/workspace_serial.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
