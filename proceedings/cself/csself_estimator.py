#!/usr/bin/env python3
"""C_self / R_self / CR / SR estimated from a longitudinal lab stream.

Physiological homeostasis is treated as a self-decoder: an analyte crossing
outside its reference band is a candidate commitment, its return in-range is a
certification, and the restoration rate is the integrative capacity.

Estimator (v2 — CR/SR commensurable). Per patient the whole panel is one
certification system whose "number in system" N(t) = # analytes simultaneously
out of range:

    excursion : a value crosses outside [ref_low, ref_high] (a fresh crossing;
                a leading out-of-range run is left-censored, not an onset). It
                restores at the next in-range reading, else is right-censored at
                the end of the series (NO Delta t cap).

    R_self = lambda = onsets / total observation time            (arrival rate)
    C_self = mu     = #restored / system-busy time               (service rate,
                      censoring-aware: busy time includes unresolved tails)
    CR     = R_self / C_self = lambda/mu = load rho              [FROM RATES]
    SR     = mean number in system L = (integral N(t) dt) / T    [FROM OCCUPANCY]
           = sum of excursion durations / T

CR is read from rates and SR from occupancy, so their agreement with the
queueing law SR = CR/(1-CR) is a genuine test of M/M/1-like structure, not an
algebraic identity (overlapping excursions push L above the load; independent
ones do not).

Why v2: the earlier SR = N_uncert/N_cert evaluated at a fixed horizon Delta t is
a survival ratio ~ exp(-mu*Delta t)/(1-...), i.e. Delta-t dependent and not
commensurable with CR, so the identity could never hold. Delta t is retained
only as a separate clinical readout (recovered-within-horizon).

Used by:
  synthea_to_cself.py   -> per-unit metrics behind proceedings Figure 1
  mimic_demo_cself.py   -> the real-physiology estimates reported in Section 3
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

YEAR = 365.25


def load_table(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.suffix in (".parquet", ".pq"):
        return pd.read_parquet(p)
    return pd.read_csv(p)


def excursion_intervals(t: np.ndarray, v: np.ndarray, lo: float, hi: float):
    """One series. Return (intervals, n_restored), where intervals is a list of
    (onset_t, restore_eff_t): restore_eff is the next in-range reading, or the
    series' last time if the excursion is still unresolved (right-censored).
    n_restored counts the uncensored ones."""
    in_range = (v >= lo) & (v <= hi)
    n = len(v)
    last_t = float(t[-1]) if n else 0.0
    intervals: list[tuple[float, float]] = []
    n_restored = 0
    i = 0
    while i < n:
        if not ((not in_range[i]) and (i > 0 and in_range[i - 1])):
            i += 1
            continue
        t0 = float(t[i])
        j = i + 1
        restore = None
        while j < n:
            if in_range[j]:
                restore = float(t[j])
                break
            j += 1
        if restore is not None:
            n_restored += 1
            intervals.append((t0, restore))
            i = j + 1
        else:
            intervals.append((t0, last_t))   # right-censored to series end
            i = n
    return intervals, n_restored


def _union_length(intervals: list[tuple[float, float]]) -> float:
    """Total length of the union of [a, b] intervals (system-busy time)."""
    if not intervals:
        return 0.0
    iv = sorted(intervals)
    total = 0.0
    cs, ce = iv[0]
    for a, b in iv[1:]:
        if a > ce:
            total += ce - cs
            cs, ce = a, b
        else:
            ce = max(ce, b)
    return total + (ce - cs)


def per_patient_metrics(labs: pd.DataFrame, events: pd.DataFrame, cfg: dict,
                        keep_pid: bool = False) -> pd.DataFrame:
    """Per-unit (CR, SR, R_self, C_self). `labs` columns: pid, code, t (days),
    value, ref_low, ref_high. `events` columns: pid, chronic (bool) — used only
    for the comorbidity covariate, and may be empty."""
    panel = {p["code"]: (float(p["ref_low"]), float(p["ref_high"])) for p in cfg["panel"]}
    delta_t = float(cfg.get("delta_t_days", 0) or 0)   # clinical readout only
    min_len = int(cfg["min_series_length"])

    labs = labs[labs["code"].isin(panel)].sort_values(["pid", "code", "t"])
    chronic = events[events["chronic"] == True] if len(events) else events  # noqa: E712

    rows = []
    for pid, pdf in labs.groupby("pid", sort=False):
        intervals: list[tuple[float, float]] = []
        n_onset = n_restored = within_dt = 0
        tmin, tmax = float(pdf["t"].min()), float(pdf["t"].max())
        for code, cdf in pdf.groupby("code", sort=False):
            if len(cdf) < min_len:
                continue
            lo, hi = panel[code]
            ivs, nres = excursion_intervals(
                cdf["t"].to_numpy(), cdf["value"].to_numpy(), lo, hi)
            intervals.extend(ivs)
            n_onset += len(ivs)
            n_restored += nres
            within_dt += sum(1 for (o, r) in ivs[:nres] if (r - o) <= delta_t and delta_t > 0)
        if n_onset < max(min_len, 2) or n_restored == 0:
            continue
        span = max(tmax - tmin, 1.0)
        busy = _union_length(intervals)                       # system-busy time (union)
        if busy <= 0:
            continue
        occupancy_time = sum(r - o for (o, r) in intervals)   # integral of N(t)
        r_self = n_onset / span * YEAR                        # lambda: onsets / yr
        c_self = n_restored / busy * YEAR                     # mu: restorations / yr
        cr = r_self / c_self                                  # load, FROM RATES
        sr = occupancy_time / span                            # occupancy L, FROM OCCUPANCY
        chronic_load = int((chronic["pid"] == pid).sum()) if len(chronic) else 0
        row = dict(CR=cr, SR=sr, R_self=r_self, C_self=c_self,
                   chronic_load=chronic_load, n_onset=n_onset,
                   censored=n_onset - n_restored,
                   clinical_recovery_within_dt=within_dt)
        if keep_pid:
            row["pid"] = pid
        rows.append(row)
    return pd.DataFrame(rows)


def suppressed_hist(x: np.ndarray, bins: int, thresh: int) -> pd.DataFrame:
    x = x[np.isfinite(x)]
    counts, edges = np.histogram(x, bins=bins)
    counts = np.where(counts < thresh, 0, counts)   # small-cell suppression
    centers = (edges[:-1] + edges[1:]) / 2
    return pd.DataFrame({"bin_center": centers, "count": counts})


def write_aggregates(m: pd.DataFrame, labs: pd.DataFrame, cfg: dict, out: Path,
                     config_text: str) -> None:
    """Aggregate-only outputs (distributions, binned regime scatter, summary).
    Emits no per-unit identifiers; small cells are suppressed."""
    out.mkdir(parents=True, exist_ok=True)
    bins = int(cfg["aggregation"]["histogram_bins"])
    thresh = int(cfg["aggregation"]["suppress_cell_below"])

    dist_frames = []
    for col in ["CR", "SR", "R_self", "C_self"]:
        h = suppressed_hist(m[col].to_numpy(), bins, thresh)
        h.insert(0, "quantity", col)
        dist_frames.append(h)
    pd.concat(dist_frames).to_csv(out / "csself_distributions.csv", index=False)

    cr, sr = m["CR"].to_numpy(), m["SR"].to_numpy()
    H, xe, ye = np.histogram2d(cr, sr, bins=bins)
    H = np.where(H < thresh, 0, H)
    xc, yc = (xe[:-1] + xe[1:]) / 2, (ye[:-1] + ye[1:]) / 2
    scat = [(xc[i], yc[j], int(H[i, j]))
            for i in range(len(xc)) for j in range(len(yc)) if H[i, j] > 0]
    pd.DataFrame(scat, columns=["CR_bin", "SR_bin", "count"]).to_csv(
        out / "regime_scatter.csv", index=False)

    summary = dict(
        cohort_n=int(len(m)),
        censored_fraction=float((m["censored"].sum()) / max(m["n_onset"].sum(), 1)),
        CR_median=float(m["CR"].median()), SR_median=float(m["SR"].median()),
        config_sha=hashlib.sha256(config_text.encode()).hexdigest()[:12],
        suppress_cell_below=thresh,
    )
    (out / "csself_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"[csself] units placed on the regime map: {len(m)}  ->  {out}")


def main() -> None:
    """CLI for a pre-normalized labs/events pair plus a YAML config."""
    import yaml   # only needed for the CLI path

    ap = argparse.ArgumentParser(description="C_self/R_self/CR/SR from labs + events")
    ap.add_argument("--labs", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default="outputs")
    a = ap.parse_args()

    config_text = Path(a.config).read_text()
    cfg = yaml.safe_load(config_text)
    m = per_patient_metrics(load_table(a.labs), load_table(a.events), cfg)
    if m.empty:
        raise SystemExit("[csself] no units placeable on the regime map — check config/inputs")
    labs = load_table(a.labs)
    write_aggregates(m, labs[labs["code"].isin({p["code"] for p in cfg["panel"]})],
                     cfg, Path(a.out), config_text)


if __name__ == "__main__":
    main()
