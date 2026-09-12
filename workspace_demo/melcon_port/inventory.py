#!/usr/bin/env python3
"""Inventory of ds006171 FROM THE EVENTS TABLES ONLY (no EEG is read) — writes INVENTORY.md,
results/trials_all.csv (one row per trial, all subjects × tasks) and results/inventory_by_file.csv.

Run:  python inventory.py            (a few seconds; needs only the events.tsv / participants.tsv files)
"""
from __future__ import annotations

import datetime as _dt
import os

import numpy as np
import pandas as pd

from common import (DATA_ROOT, RESULTS_DIR, SUBJECTS, TASKS, available, read_participants, trial_table)

pd.set_option("display.width", 250)


def contrast_quintiles(t: pd.DataFrame) -> pd.Series:
    """Quintile label 1..5 of the contrast among the present trials of one subject × task."""
    q = pd.Series(np.nan, index=t.index)
    pres = t.present & t.contrast.notna()
    if pres.sum() >= 5:
        q[pres] = pd.qcut(t.loc[pres, "contrast"].rank(method="first"), 5, labels=False) + 1
    return q


def per_file(t: pd.DataFrame) -> dict:
    pres = t[t.present]
    catch = t[t.catch]
    c = pres.contrast.dropna()
    d = dict(
        subject=t.subject.iloc[0], task=t.task.iloc[0], n_trials=len(t), n_present=len(pres), n_catch=len(catch),
        n_blocks=int(t.block.nunique()),
        contrast_min=c.min(), contrast_median=c.median(), contrast_max=c.max(),
        contrast_iqr=c.quantile(0.75) - c.quantile(0.25), contrast_cv=c.std(ddof=1) / c.mean() if c.mean() else np.nan,
        contrast_n_unique=int(c.round(6).nunique()),
        seen_rate=pres.seen.mean(), seen_rate_catch=catch.seen.mean(),
        n_seen_missing=int(t.seen.isna().sum()), n_seen_from_column=int((t.seen_source == "column").sum()),
        n_objective=int(t.objective.notna().sum()), objective_acc=pres.objective_correct.mean(),
        n_obj_from_column=int((t.objective_source == "column").sum()),
        seen_col_conflicts=int(t.seen_col_conflict.sum()), obj_col_conflicts=int(t.obj_col_conflict.sum()),
        n_left=int((pres.side == "left").sum()), n_right=int((pres.side == "right").sum()),
        n_vertical=int((pres.orientation == "vertical").sum()), n_horizontal=int((pres.orientation == "horizontal").sum()),
        n_pd_total=t.attrs["n_pd_total"], n_pd_used=t.attrs["n_pd_used"], n_pd_break=t.attrs["n_pd_break"],
        n_pd_break_interior=t.attrs["n_pd_break_interior"], block_source=t.attrs["block_source"],
        block_sizes=";".join(str(v) for v in t.block.value_counts().sort_index().tolist()),
        n_pd_uncorrected=int((~t.pd_corrected).sum()),
        pd_delay_ms_min=1000 * t.pd_delay.min(), pd_delay_ms_median=1000 * t.pd_delay.median(), pd_delay_ms_max=1000 * t.pd_delay.max(),
        cue_soa_s_min=t.cue_soa.min(), cue_soa_s_max=t.cue_soa.max(),
        rt_subj_s_median=t.rt_subjective.median(), rt_subj_s_p10=t.rt_subjective.quantile(0.10),
        stray_codes=";".join(map(str, t.attrs["stray_codes"])),
    )
    q = contrast_quintiles(t)
    for k in range(1, 6):
        d[f"seen_q{k}"] = pres.seen[q[pres.index] == k].mean()
    if t.task.iloc[0] == "noninformative":
        d["seen_vdig0"] = pres.seen[pres.validity_digit == 0].mean()
        d["seen_vdig1"] = pres.seen[pres.validity_digit == 1].mean()
        d["contrast_vdig0"] = pres.contrast[pres.validity_digit == 0].median()
        d["contrast_vdig1"] = pres.contrast[pres.validity_digit == 1].median()
    return d


def fmt(x, nd=3):
    return "—" if (x is None or (isinstance(x, float) and np.isnan(x))) else f"{x:.{nd}f}"


def contrast_validity(trials: pd.DataFrame) -> dict:
    """Does the contrast column behave as the online staircase's output for the trial it is on?
    Per task: per-subject corr(contrast, seen) on present trials; the same at lags -2..+2 (seen_i vs
    contrast_{i+lag}); the staircase rule (mean contrast change after an unseen vs a seen previous
    present trial); for the noninformative task the split by validity digit."""
    out = {}
    for task in TASKS:
        g = trials[(trials.task == task) & trials.present & trials.seen.notna()]
        r0, lags = [], {k: [] for k in (-2, -1, 0, 1, 2)}
        for s, x in g.groupby("subject"):
            x = x.sort_values("trial")
            c, y = x.contrast.values, x.seen.values
            r0.append(np.corrcoef(c, y)[0, 1])
            for lag in lags:
                a, b = (y[: len(y) - lag], c[lag:]) if lag >= 0 else (y[-lag:], c[: len(c) + lag])
                lags[lag].append(np.corrcoef(a, b)[0, 1])
        x = g.sort_values(["subject", "trial"]).copy()
        x["prev_seen"] = x.groupby("subject").seen.shift(1)
        x["dc"] = x.groupby("subject").contrast.diff()
        step = x.groupby("prev_seen").dc.mean()
        d = dict(r_median=float(np.median(r0)), r_min=float(np.min(r0)), r_max=float(np.max(r0)), n_pos=int(np.sum(np.array(r0) > 0)), n=len(r0),
                 lags={k: float(np.mean(v)) for k, v in lags.items()},
                 step_after_unseen=float(step.get(0.0, np.nan)), step_after_seen=float(step.get(1.0, np.nan)))
        if task == "noninformative":
            for dig in (0, 1):
                y = g[g.validity_digit == dig]
                rr = [np.corrcoef(xx.contrast, xx.seen)[0, 1] for _, xx in y.groupby("subject")]
                q = y.groupby("subject").contrast.transform(lambda c: pd.qcut(c.rank(method="first"), 5, labels=False) + 1)
                d[f"digit{dig}"] = dict(r_mean=float(np.mean(rr)), n_pos=int(np.sum(np.array(rr) > 0)), n=len(rr),
                                        seen_by_q=y.groupby(q).seen.mean().round(3).tolist())
        out[task] = d
    return out


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    pairs = available("events")
    tables, files = [], []
    for sub, task in pairs:
        t = trial_table(sub, task)
        t["contrast_quintile"] = contrast_quintiles(t)
        tables.append(t)
        files.append(per_file(t))
    trials = pd.concat(tables, ignore_index=True)
    trials.to_csv(os.path.join(RESULTS_DIR, "trials_all.csv"), index=False, float_format="%.6g")
    inv = pd.DataFrame(files)
    inv.to_csv(os.path.join(RESULTS_DIR, "inventory_by_file.csv"), index=False, float_format="%.6g")

    bdf = available("bdf")
    have = {(s, t) for s, t in pairs}
    missing = [(s, t) for s in SUBJECTS for t in TASKS if (s, t) not in have]
    parts = read_participants()

    L = []
    L.append("# ds006171 (Melcón et al. 2024) — inventory from the events tables\n")
    L.append(f"Generated {_dt.date.today().isoformat()} by `inventory.py` from `{os.path.relpath(DATA_ROOT, os.path.dirname(RESULTS_DIR))}` — "
             "**events.tsv / participants.tsv only; no EEG was read for this file.** Per-trial rows: `results/trials_all.csv`; "
             "per-file rows (every column below and more): `results/inventory_by_file.csv`. Code scheme and the photodiode rule: "
             "`common.py` docstring and README D1–D3.\n")
    L.append("## 1. What is on the server and on disk\n")
    L.append(f"* Subjects sub-01 … sub-36; tasks nocue / noninformative / informative; **{len(pairs)} of 108 subject × task recordings exist** "
             f"(BDF + sidecars). Missing on OpenNeuro: " + ", ".join(f"sub-{s:02d} {t}" for s, t in missing) + ".")
    L.append(f"* Events tables on disk: {len(pairs)}; BDF files on disk at generation time: {len(bdf)} (the download runs separately; see README).")
    L.append("* `participants.tsv` has **55 rows with ids `sub-001` … `sub-590`** (sex, age, handedness, `session1`, `late_ses1`, `session2`, `late_ses2`) "
             "that do not match the 36 EEG subject ids `sub-01` … `sub-36`, and the paper describes 36 *graduate students, 21.0 ± 6.2 years, 27 female, 30 right-handed*, "
             f"whereas this table has ages {parts.age.min()}–{parts.age.max()} (mean {parts.age.mean():.1f}), {int((parts.sex == 'F').sum())} F / {int((parts.sex == 'M').sum())} M, "
             f"{int((parts.handedness == 'left').sum())} left-handed, and two-session columns that the paradigm does not have. "
             "**I can't determine the mapping**, and the table is very likely from another study of the same laboratory; per-subject age and sex are therefore not available. "
             "What would settle it: the authors (dataset contact via OpenNeuro) or a corrected `participants.tsv` in a later dataset version.")
    L.append("* All 104 `events.json`, `eeg.json` and `channels.tsv` sidecars are byte-identical across files; `electrodes.tsv` is identical across subjects (a template montage, not digitised positions). "
             "The BDF headers disagree with the sidecars in two ways (`results/bdf_headers.csv`, from `verify_download.py`): nine recordings have 272 channels "
             "(sub-02 nocue/informative, sub-04 and sub-05 all tasks, sub-11 informative; README D12) and four were recorded at 2048 Hz "
             "(sub-35 informative/noninformative, sub-36 informative/nocue; README D13) — `eeg.json` says 128 + 4 + 1 channels and 1024 Hz for all.\n")

    L.append("## 2. Per task\n")
    for task in TASKS:
        g = inv[inv.task == task].sort_values("subject")
        L.append(f"### {task}  ({len(g)} subjects)\n")
        L.append("| sub | trials | present | catch | contrast min / median / max | contrast CV | seen rate | seen by contrast quintile 1→5 | seen on catch | objective n / acc | left / right | vert / horiz | 128s total / used / breaks | pd delay ms med (min–max) | seen missing | notes |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for _, r in g.iterrows():
            notes = []
            if r.n_seen_from_column:
                notes.append(f"{r.n_seen_from_column} seen from column")
            if r.n_obj_from_column:
                notes.append(f"{r.n_obj_from_column} obj from column")
            if r.obj_col_conflicts:
                notes.append(f"{r.obj_col_conflicts} obj column≠trigger")
            if r.n_pd_uncorrected:
                notes.append(f"{r.n_pd_uncorrected} trials without photodiode")
            if r.stray_codes:
                notes.append(f"stray code {r.stray_codes}")
            if r.n_trials != 400:
                notes.append(f"{r.n_trials} trials")
            L.append(f"| {r.subject:02d} | {r.n_trials} | {r.n_present} | {r.n_catch} | {fmt(r.contrast_min, 4)} / {fmt(r.contrast_median, 4)} / {fmt(r.contrast_max, 4)} | "
                     f"{fmt(r.contrast_cv, 2)} | {fmt(r.seen_rate, 2)} | {' '.join(fmt(r[f'seen_q{k}'], 2) for k in range(1, 6))} | {fmt(r.seen_rate_catch, 2)} | "
                     f"{r.n_objective} / {fmt(r.objective_acc, 2)} | {r.n_left} / {r.n_right} | {r.n_vertical} / {r.n_horizontal} | "
                     f"{r.n_pd_total} / {r.n_pd_used} / {r.n_pd_break} | {fmt(r.pd_delay_ms_median, 0)} ({fmt(r.pd_delay_ms_min, 0)}–{fmt(r.pd_delay_ms_max, 0)}) | "
                     f"{r.n_seen_missing} | {'; '.join(notes)} |")
        L.append("")
        tt = trials[trials.task == task]
        pres = tt[tt.present]
        L.append(f"**{task} totals:** {len(tt)} trials, {len(pres)} present, {int(tt.catch.sum())} catch; seen rate {pres.seen.mean():.3f} on present "
                 f"(subject range {g.seen_rate.min():.2f}–{g.seen_rate.max():.2f}), {tt[tt.catch].seen.mean():.3f} on catch (false alarms; range "
                 f"{g.seen_rate_catch.min():.2f}–{g.seen_rate_catch.max():.2f}); contrast median {pres.contrast.median():.4f} (subject medians "
                 f"{g.contrast_median.min():.4f}–{g.contrast_median.max():.4f}); within-subject contrast CV {g.contrast_cv.median():.2f} (range {g.contrast_cv.min():.2f}–{g.contrast_cv.max():.2f}); "
                 f"seen rate by contrast quintile (mean of subjects) {' / '.join(f'{g[f'seen_q{k}'].mean():.2f}' for k in range(1, 6))}; "
                 f"objective questions {int(g.n_objective.sum())} ({g.n_objective.mean():.1f} per subject), accuracy {pres.objective_correct.mean():.3f}; "
                 f"trials without a seen/unseen response {int(g.n_seen_missing.sum())}; "
                 f"photodiode delay median {g.pd_delay_ms_median.median():.0f} ms (file medians {g.pd_delay_ms_median.min():.0f}–{g.pd_delay_ms_median.max():.0f}); "
                 + (f"cue→Gabor SOA {tt.cue_soa.min():.3f}–{tt.cue_soa.max():.3f} s; " if task != "nocue" else "")
                 + f"subjective RT median {tt.rt_subjective.median():.2f} s (10th percentile {tt.rt_subjective.quantile(0.1):.2f} s).")
        if task == "noninformative":
            L.append(f"\nValidity classes (code digit 0 vs 1, assignment unknown — README D2): seen rate {g.seen_vdig0.mean():.3f} vs {g.seen_vdig1.mean():.3f} "
                     f"(paired across subjects: {int((g.seen_vdig0 > g.seen_vdig1).sum())} of {len(g)} have digit-0 > digit-1), "
                     f"median contrast {g.contrast_vdig0.mean():.4f} vs {g.contrast_vdig1.mean():.4f}.")
        L.append("")

    L.append("## 3. Totals and cross-checks\n")
    pres = trials[trials.present]
    L.append(f"* **{len(trials)} trials** in {len(pairs)} recordings ({len(pres)} Gabor-present, {int(trials.catch.sum())} catch); "
             f"{int(trials.seen.notna().sum())} with a seen/unseen response, {int(trials.objective.notna().sum())} with an orientation response.")
    L.append(f"* Seen rate on present trials: nocue {trials[(trials.task == 'nocue') & trials.present].seen.mean():.3f}, noninformative "
             f"{trials[(trials.task == 'noninformative') & trials.present].seen.mean():.3f}, informative {trials[(trials.task == 'informative') & trials.present].seen.mean():.3f}; "
             f"false-alarm rate on catch trials {trials[trials.catch].seen.mean():.3f} overall.")
    L.append(f"* Objective accuracy on present trials with an orientation response: {pres.objective_correct.mean():.3f} overall "
             f"(seen {pres[pres.seen == 1].objective_correct.mean():.3f}, n = {int(pres[pres.seen == 1].objective_correct.notna().sum())}; "
             f"unseen {pres[pres.seen == 0].objective_correct.mean():.3f}, n = {int(pres[pres.seen == 0].objective_correct.notna().sum())}).")
    col_empty = trials[(trials.seen_source == "trigger") & trials.seen_col.isna()]
    L.append(f"* Behaviour source: the `subjective_r` column agrees with the 124/125 triggers wherever both exist ({int(trials.seen_col_conflict.sum())} conflicts in "
             f"{int(((trials.seen_source == 'trigger') & trials.seen_col.notna()).sum())} trials); it is empty on {len(col_empty)} stimulus rows in "
             f"{col_empty.groupby(['subject', 'task']).ngroups} recordings that do have the triggers, so `seen` is taken from the triggers "
             f"({int(inv.n_seen_from_column.sum())} trials fall back to the column). `objective_r` vs the 121/122 triggers: "
             f"{int(trials.obj_col_conflict.sum())} conflicts, {int(inv.n_obj_from_column.sum())} trials with a column value but no trigger (column used), "
             f"{int(((trials.objective_source == 'trigger') & trials.objective_col.isna()).sum())} with a trigger but an empty column.")
    cue_d = trials.cue_pd_delay.dropna()
    L.append(f"* Photodiode: every cue / Gabor / catch trigger in every file is immediately followed by a 128 ({int(inv.n_pd_uncorrected.sum())} exceptions in "
             f"{int((inv.n_pd_uncorrected > 0).sum())} files, see notes); the remaining 128s are the start and break screens "
             f"({int(inv.n_pd_break.sum())} in total, 0–7 per recording). Delay trigger→photodiode: Gabor/catch median {trials.pd_delay.median() * 1000:.0f} ms, range "
             f"{trials.pd_delay.min() * 1000:.0f}–{trials.pd_delay.max() * 1000:.0f} ms; cue median {cue_d.median() * 1000:.0f} ms, range "
             f"{cue_d.min() * 1000:.0f}–{cue_d.max() * 1000:.0f} ms (n = {len(cue_d)}). The correction shifts every epoch by the measured "
             f"delay of its own trial; the 1024 Hz onsets in `events.tsv` reproduce the BDF Status channel exactly (checked in `load.py --verify`).")
    nb = inv[inv.block_source != "break_128"]
    L.append(f"* Blocks: the paradigm has 4 blocks of 100 trials with a break screen between them, and the break screen fires an unpaired 128. "
             f"In {int((inv.block_source == 'break_128').sum())} recordings exactly three such interior 128s are present and define the blocks "
             f"(block sizes {', '.join(sorted(set(inv[inv.block_source == 'break_128'].block_sizes)))}); in the other {len(nb)} "
             f"({', '.join(f'sub-{r.subject:02d} {r.task} ({r.n_pd_break_interior} interior break 128s)' for _, r in nb.iterrows())}) the blocks are "
             f"ceil(trial_number / 100) (`block_source`).")
    L.append("* Trigger codes, all files: nocue/informative 11 12 21 22 31 32 (+ 1 2 cues in informative), noninformative 1 2 98 99 101–104 111–114; responses 121 122 124 125; photodiode 128. "
             f"Stray single codes: {', '.join(f'sub-{r.subject:02d} {r.task} {r.stray_codes}' for _, r in inv[inv.stray_codes != ''].iterrows())} (one event each, ignored).")
    L.append("")
    L.append("## 4. Does the contrast column behave as the staircase output of its own trial?\n")
    cv = contrast_validity(trials)
    L.append("Per task, on present trials with a response (behaviour only): the per-subject correlation of contrast with the seen/unseen "
             "response, the same correlation with the contrast of neighbouring trials (a misaligned column would peak at a non-zero lag), "
             "and the staircase rule (the paper: contrast goes down after a run of seen responses and up after a run of unseen ones).\n")
    L.append("| task | corr(contrast, seen) per subject: median (min–max), n > 0 | mean corr at lag −2 / −1 / 0 / +1 / +2 | mean Δcontrast after an unseen / a seen trial |")
    L.append("|---|---|---|---|")
    for task in TASKS:
        d = cv[task]
        L.append(f"| {task} | {d['r_median']:.3f} ({d['r_min']:.3f}–{d['r_max']:.3f}), {d['n_pos']} of {d['n']} | "
                 f"{' / '.join(f'{d['lags'][k]:.3f}' for k in (-2, -1, 0, 1, 2))} | {d['step_after_unseen']:+.5f} / {d['step_after_seen']:+.5f} |")
    dn = cv["noninformative"]
    L.append("")
    L.append(f"In the **nocue** and **informative** tasks the column behaves as expected: the correlation peaks at lag 0, is positive in "
             f"{cv['nocue']['n_pos']}/{cv['nocue']['n']} and {cv['informative']['n_pos']}/{cv['informative']['n']} subjects, and the staircase "
             f"moves the contrast down after seen and up after unseen trials by ≈ 0.0005 per trial. In the **noninformative** task it does not: "
             f"the lag-0 correlation is {dn['lags'][0]:.3f} (no lag is better), only {dn['n_pos']} of {dn['n']} subjects are positive, and the "
             f"contrast changes by only {dn['step_after_unseen']:+.5f} / {dn['step_after_seen']:+.5f} after unseen / seen trials — a tenth of the "
             f"other tasks. Split by the undocumented validity digit: digit 0 r = {dn['digit0']['r_mean']:.3f} ({dn['digit0']['n_pos']}/{dn['digit0']['n']} positive; "
             f"seen by contrast quintile {dn['digit0']['seen_by_q']}), digit 1 r = {dn['digit1']['r_mean']:.3f} ({dn['digit1']['n_pos']}/{dn['digit1']['n']}; "
             f"{dn['digit1']['seen_by_q']}). Reading: the column in this task most likely records the staircase of the *cued* hemifield while the Gabor "
             "appeared in the other hemifield on the invalid half of the trials (which would make digit 0 the valid class), but even the digit-0 relation "
             "is a third of the other tasks' — **I can't determine the cause from the files**; the authors' presentation script would. "
             "**Consequence: the noninformative task has no usable trial-by-trial intensity covariate.**")
    L.append("")
    L.append("## 5. What limits the planned analysis (PREREG_secondary_melcon.md)\n")
    lim = []
    lim.append(f"1. **Catch trials are few: 40 per recording** (20 per side), of which some are 'seen' (false alarms, mean {trials[trials.catch].seen.mean():.2f}). "
               "A decoder trained on catch vs Gabor has at most 40 negative examples per subject × task — Sergent had ≈ 150 no-sound trials per session. "
               "Pooling the three tasks of a subject gives ≤ 120 catch trials, at the cost of mixing cue conditions.")
    pos = inv[inv.contrast_min > 0]
    ratio = pos.contrast_max / pos.contrast_min
    neg = trials[trials.contrast < 0]
    lim.append(f"2. **Contrast is a staircase output, not a designed level set**: within a recording it spans a factor of ≈ {ratio.median():.1f} "
               f"(median max/min; range {ratio.min():.1f}–{ratio.max():.1f}) with CV ≈ {inv.contrast_cv.median():.2f}, "
               f"and {int((inv.contrast_cv < 0.15).sum())} recordings have CV < 0.15. The staircase concentrates trials near threshold — good for the mixture question, "
               "poor for anchoring a 'high-intensity' state: the top quintile is only modestly above the median (seen rate in quintile 5 ≈ "
               f"{inv.seen_q5.mean():.2f} vs quintile 1 ≈ {inv.seen_q1.mean():.2f}, nocue and informative; flat in noninformative, §4). "
               f"{len(neg)} present trials carry a **negative** contrast ({', '.join(f'sub-{s:02d} {t}' for (s, t) in neg.groupby(['subject', 'task']).size().index)}; "
               f"min {neg.contrast.min():.4f}) — the staircase ran below zero; what was displayed on those trials cannot be determined from the files, and they are to be excluded.")
    lim.append("2b. **The noninformative task's contrast column is not a usable intensity covariate** (§4): it neither predicts the seen/unseen response nor follows "
               "the staircase rule in that task. That task can enter a report-conditioned (seen vs unseen) analysis only.")
    lim.append(f"3. **Missing recordings:** {', '.join(f'sub-{s:02d} {t}' for s, t in missing)} — so 32 subjects have all three tasks, 4 have two.")
    lim.append(f"4. **Missing responses:** {int(inv.n_seen_missing.sum())} trials without a seen/unseen response ({', '.join(f'sub-{r.subject:02d} {r.task} {r.n_seen_missing}' for _, r in inv[inv.n_seen_missing > 0].iterrows())}).")
    lim.append("5. **The subjective question appears 250–350 ms after Gabor offset** (paper) — i.e. 300–400 ms after Gabor onset — and is not marked by a trigger. "
               f"Responses follow at a median {trials.rt_subjective.median():.2f} s after Gabor onset (10th percentile {trials.rt_subjective.quantile(0.1):.2f} s). "
               "Any window later than ≈ 300 ms contains the (jittered) question display and response preparation; Sergent's bifurcation interval (250–700 ms) is not cleanly available.")
    lim.append("6. **No per-subject demographics** (participants.tsv mismatch, §1) and **no per-Gabor hemifield in the noninformative task** (README D2).")
    lim.append("7. **The paper's own exclusions** (5–6 subjects per task for > 45 % ocular-artefact trials, 1 for persistent contrast differences, 1–2 for data loss) are not "
               "encoded in the dataset; the pre-registration must define its own artefact rule.")
    L.extend(lim)
    L.append("")
    with open(os.path.join(os.path.dirname(RESULTS_DIR), "INVENTORY.md"), "w") as f:
        f.write("\n".join(L))
    print(f"{len(pairs)} recordings, {len(trials)} trials -> INVENTORY.md, results/trials_all.csv, results/inventory_by_file.csv")


if __name__ == "__main__":
    main()
