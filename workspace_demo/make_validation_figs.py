"""Figures for the 2026-08-28/29 validation program (E7-E11), from the
committed run logs. Style matches make_paper_figs.py.

  val_precursors   E7: sliding detrended queue variance, feedback vs
                   matched control, onset marked; tau summary bars
  val_separatrix   E8: committed P(EXIT|f) curve + measured verdicts,
                   axis shocks separated (two-component memory)
  val_cuspmap      E9: l_up/l_down vs alpha per T_d, wedge shaded,
                   the four rig spots at TRUE coordinates
  val_secondmodel  E10b: backlog trajectories, Llama feedback runaway
                   at true rho 0.79 vs control clean through 0.84
  val_production   E11: service law, feedback kernel, cascade tail

Run:  uv run --with matplotlib python3 make_validation_figs.py
Out:  figs/*.pdf + *.png
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from e7_stats import ONSET_QUEUE, queue_series_stats, pre_onset_len

HERE = Path(__file__).parent
RUNS = HERE / "runs"
FIGS = HERE / "figs"
FIGS.mkdir(exist_ok=True)

C1 = "#B4432F"  # feedback / drive
C0 = "#2E5E8C"  # control / gated
CG = "#6B6B6B"  # grey reference
CA = "#D99A2B"  # ambig / accent


def jload(name):
    return json.loads((RUNS / name).read_text())


def jsonl(name):
    out = []
    for line in (RUNS / name).read_text().splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def save(fig, stem):
    for ext in ("pdf", "png"):
        fig.savefig(FIGS / f"{stem}.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote figs/{stem}.pdf/.png")


# ---------------------------------------------------------------- E7
def fig_precursors():
    recs = jsonl("e7_precursors.jsonl")
    series = defaultdict(lambda: ([], []))       # (seed, arm) -> (qa, junk)
    for r in recs:
        if r.get("arm") in ("feedback", "control") and "queue_after" in r:
            qa, _ = series[(r["seed"], r["arm"])]
            qa.append(r["queue_after"])
    taus = {}
    for r in recs:
        if r.get("arm_done") and r.get("tau_qvar") is not None:
            taus[(r["seed"], r["arm"])] = r["tau_qvar"]

    fig, axs = plt.subplots(1, 3, figsize=(9.6, 2.9))
    for ax, seed in zip(axs[:2], (0, 2)):
        for arm, c in (("feedback", C1), ("control", C0)):
            qa = series[(seed, arm)][0]
            if not qa:
                continue
            cut = pre_onset_len(qa)
            st = queue_series_stats(qa[:cut])
            xs = list(range(len(st)))
            ax.plot(xs, [s[0] for s in st], color=c, lw=1.4,
                    label=f"{arm} (τ={taus.get((seed, arm), 0):+.2f})")
            if cut < len(qa):
                ax.axvline(len(st) - 1, color=c, ls=":", lw=1)
        ax.set_title(f"seed {seed}: sliding queue variance "
                     f"(detrended, w=25)", fontsize=8)
        ax.set_xlabel("window index (pre-onset)", fontsize=8)
        ax.set_ylabel("residual variance", fontsize=8)
        ax.legend(fontsize=7, frameon=False)
        ax.tick_params(labelsize=7)
    ax = axs[2]
    pairs = [(0, "feedback"), (0, "control"), (2, "feedback"),
             (2, "control")]
    xs = range(len(pairs))
    vals = [taus.get(p, 0.0) for p in pairs]
    cols = [C1 if a == "feedback" else C0 for _, a in pairs]
    ax.bar(xs, vals, color=cols)
    ax.axhline(0.296, color=C1, ls="--", lw=1)
    ax.axhline(-0.052, color=C0, ls="--", lw=1)
    ax.text(3.55, 0.30, "model fb", fontsize=6, color=C1, va="bottom")
    ax.text(3.55, -0.09, "model ctrl", fontsize=6, color=C0, va="top")
    ax.set_xticks(list(xs))
    ax.set_xticklabels(["s0 fb", "s0 ctl", "s2 fb", "s2 ctl"], fontsize=7)
    ax.set_ylabel(r"Kendall $\tau$ (queue variance)", fontsize=8)
    ax.set_title("trend statistic vs committed model", fontsize=8)
    ax.tick_params(labelsize=7)
    fig.suptitle("E7 — fluctuation precursors on the approach to the "
                 "fold (seed-2 control drift-attributed: ρ 0.39→0.62)",
                 fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    save(fig, "val_precursors")


# ---------------------------------------------------------------- E8
def fig_separatrix():
    pred = jload("e8_prediction.json")
    verd = jload("e8_verdicts.json")["0"]
    fs = [0.0, 0.25, 0.5, 0.75, 1.0]
    ps = [pred[f"compound_{f:.2f}"]["p_exit"] for f in fs]
    fig, ax = plt.subplots(figsize=(4.6, 3.1))
    ax.plot(fs, ps, "-o", color=CG, lw=1.4, ms=4,
            label="committed model P(EXIT|f)")
    ax.axhline(0.5, color=CG, ls=":", lw=0.8)
    vc = {"PINNED": C0, "AMBIG": CA, "EXIT": C1, "VOID": "#BBBBBB"}
    for f in fs:
        v = verd[f"compound_{f:.2f}"]
        ax.scatter([f], [1.06], marker="v", s=70, color=vc[v], zorder=5)
        ax.text(f, 1.12, v, fontsize=6, ha="center", color=vc[v])
    # both single-axis shocks have magnitude 1.0 — plotted at f = 1
    # (slightly offset) to show them underperforming the compound
    ax.scatter([0.94], [pred["window_only"]["p_exit"]], marker="s", s=45,
               color=C0)
    ax.text(0.90, pred["window_only"]["p_exit"],
            f"window-only (meas. {verd['window_only']})  ",
            fontsize=6.5, color=C0, ha="right", va="center")
    ax.scatter([0.97], [pred["backlog_only"]["p_exit"]], marker="s", s=45,
               color=CA)
    ax.text(0.93, pred["backlog_only"]["p_exit"],
            f"backlog-only (meas. {verd['backlog_only']})  ",
            fontsize=6.5, color=CA, ha="right", va="center")
    ax.set_xlabel("compound shock size f (backlog dropped + window "
                  "cleaned)", fontsize=8)
    ax.set_ylabel("model P(EXIT)", fontsize=8)
    ax.set_ylim(-0.05, 1.2)
    ax.set_title("E8 — the separatrix: committed curve vs measured "
                 "verdicts (▼)", fontsize=9)
    ax.legend(fontsize=7, frameon=False, loc="center left")
    ax.tick_params(labelsize=7)
    save(fig, "val_separatrix")


# ---------------------------------------------------------------- E9
def fig_cuspmap():
    m = jload("e9_cusp_map.json")
    tds = [33, 66, 132]
    fig, axs = plt.subplots(1, 3, figsize=(9.6, 2.9), sharey=True)
    for ax, td in zip(axs, tds):
        alphas, ups, dns = [], [], []
        for a in (0.15, 0.2, 0.3, 0.4, 0.55, 0.8, 1.2, 1.6):
            row = m.get(f"td{td}_a{a}")
            if not row:
                continue
            alphas.append(a)
            ups.append(row["l_up"])
            dns.append(row["l_down"])
        au = [(a, u) for a, u in zip(alphas, ups) if u is not None]
        ad = [(a, d) for a, d in zip(alphas, dns) if d is not None]
        ax.plot(*zip(*au), "-o", color=C1, ms=3.5, lw=1.3,
                label=r"$l_{up}$ (ignition)")
        ax.plot(*zip(*ad), "-o", color=C0, ms=3.5, lw=1.3,
                label=r"$l_{down}$ (drain)")
        both = {a for a, _ in au} & {a for a, _ in ad}
        af = sorted(both)
        ax.fill_between(af,
                        [dict(ad)[a] for a in af],
                        [dict(au)[a] for a in af],
                        color=CA, alpha=0.25, label="bistable wedge")
        astar = 1 / (1 + td / 25.2)
        ax.axvline(astar, color=CG, ls="--", lw=1)
        ax.text(astar, 1.08, r"$\alpha^*$ mean-field", fontsize=6,
                color=CG, ha="center")
        ax.set_title(f"$T_d$ = {td} s (θ = {td / 25.2:.2f})", fontsize=8)
        ax.set_xlabel(r"$\alpha$", fontsize=8)
        ax.set_xscale("log")
        ax.set_xticks([0.15, 0.3, 0.55, 0.8, 1.6])
        ax.set_xticklabels(["0.15", "0.3", "0.55", "0.8", "1.6"],
                           fontsize=7)
        ax.minorticks_off()
        ax.tick_params(labelsize=7)
    spots = [(66, 0.8, 0.70, "S1✓", C1), (132, 0.8, 0.70, "S2✗", C1),
             (66, 0.2, 0.72, "S3?", C0), (66, 0.8, 0.54, "S4✓", C0)]
    for td, a, rho, lab, c in spots:
        ax = axs[{33: 0, 66: 1, 132: 2}[td]]
        ax.scatter([a], [rho], marker="*", s=90, color=c, zorder=6)
        ax.text(a * 1.1, rho, lab, fontsize=7, va="center")
    axs[0].set_ylabel(r"true utilization $\rho$", fontsize=8)
    axs[0].legend(fontsize=6.5, frameon=False, loc="lower left")
    fig.suptitle("E9 — the rig-horizon cusp map (2100 s, reduced model) "
                 "with the four rig spots at TRUE coordinates",
                 fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    save(fig, "val_cuspmap")


# --------------------------------------------------------------- E10b
def fig_secondmodel():
    recs = jsonl("e10b_llama.jsonl")
    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    for arm, c in (("feedback", C1), ("control", C0)):
        qa = [r["queue_after"] for r in recs
              if r.get("arm") == arm and r.get("phase", "").startswith("rho")
              and "queue_after" in r]
        ax.plot(range(len(qa)), qa, color=c, lw=1.4, label=arm)
    bounds = []
    n = 0
    for r in recs:
        if r.get("arm") == "control" and r.get("phase_done"):
            bounds.append((n, r["rho"]))
        if (r.get("arm") == "control"
                and r.get("phase", "").startswith("rho")
                and "queue_after" in r):
            n += 1
    for x, rho in bounds:
        ax.axvline(x, color=CG, ls=":", lw=0.8)
    ax.text(20, 24, "feedback: runaway in phase 1\n"
            r"(exo-only true $\rho$ = 0.79; offspring drive it to ~1.4)",
            fontsize=7, color=C1)
    ax.text(260, 3.5, r"control clean through true $\rho$ = 0.84",
            fontsize=7, color=C0, ha="center")
    ax.set_xlabel("served task index", fontsize=8)
    ax.set_ylabel("backlog", fontsize=8)
    ax.set_title("E10b — second architecture (Llama-3.1-8B, lens-free): "
                 "sub-capacity feedback-specific collapse", fontsize=8.5)
    ax.legend(fontsize=7, frameon=False, loc="upper right")
    ax.tick_params(labelsize=7)
    save(fig, "val_secondmodel")


# ---------------------------------------------------------------- E11
def fig_production():
    p1 = jload("e11_production.json")
    p2 = jload("e11b_production.json")
    fig, axs = plt.subplots(1, 3, figsize=(9.6, 2.8))
    ax = axs[0]
    xs = [b / 1000 for b in p2["bins_ctx_upper"]]
    ys = p2["I2p_llm_latency_median_s"]
    pts = [(x, y) for x, y in zip(xs, ys) if y is not None]
    ax.plot(*zip(*pts), "-o", color=C0, ms=4, lw=1.4)
    ax.set_xlabel("context (k tokens, bin upper edge)", fontsize=8)
    ax.set_ylabel("median LLM step latency (s)", fontsize=8)
    ax.set_title("the service law in production", fontsize=8)
    ax = axs[1]
    ax.bar([0, 1], [p1["I3_p_err_after_ok"], p1["I3_p_err_after_err"]],
           color=[C0, C1])
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["after success", "after error"], fontsize=7.5)
    ax.set_ylabel("P(next tool call errors)", fontsize=8)
    ax.set_title("the feedback kernel (3.7×)", fontsize=8)
    ax = axs[2]
    ks = sorted(int(k) for k in p1["I4_run_len_observed"])
    obs = [p1["I4_run_len_observed"][str(k)] for k in ks]
    exp = [p1["I4_run_len_geometric_null"].get(str(k), 0.1) for k in ks]
    ax.semilogy(ks, obs, "o-", color=C1, ms=4, lw=1.2, label="observed")
    ax.semilogy(ks, [max(e, 0.05) for e in exp], "s--", color=CG, ms=3.5,
                lw=1.1, label="geometric (iid) null")
    ax.set_xlabel("error-run length", fontsize=8)
    ax.set_ylabel("count", fontsize=8)
    ax.set_title("cascades vs the iid null", fontsize=8)
    ax.legend(fontsize=7, frameon=False)
    for ax in axs:
        ax.tick_params(labelsize=7)
    fig.suptitle("E11 — RSC ingredient curves in production Claude Code "
                 "traces (16 sessions, 22,792 tool calls)", fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    save(fig, "val_production")


if __name__ == "__main__":
    fig_precursors()
    fig_separatrix()
    fig_cuspmap()
    fig_secondmodel()
    fig_production()
