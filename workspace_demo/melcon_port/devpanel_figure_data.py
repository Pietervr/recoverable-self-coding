#!/usr/bin/env python3
"""Paper figure data for Phase 1 of the Melcón v7 development plan (read-only over devpanel_analyze.py's tables).

Writes, beside the manuscript's figure scripts:
  melcon_v7_phase1_units.csv  the panel's main-window graded and two-state fold units (40 recordings x 4 folds x 10 windows
                              x 2 families): role, generator, loss against null per trial, test present trials below /
                              within / above the training dose range, catch trials, the summed per-trial loss on each, the
                              kept graded r at its lower bound (-ln 10), the graded SD minima at within-support and
                              extrapolated test doses;
  melcon_v7_phase1_ideal.csv  the 272 idealized-readout recordings: generator, drift, subject, family with the highest
                              evidence, Delta, graded minus null per trial.
Usage: ../../.venv/bin/python devpanel_figure_data.py
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ANALYSIS = os.path.join(HERE, "results", "devpanel_v7", "run-5d74bc1d6a11", "analysis")
FIG = "/Users/pietervanrooyen/Unimog-Projects/papers/adaptive_agency_special_issue/figures"

units = [r for r in csv.DictReader(open(os.path.join(ANALYSIS, "units_panel.csv"), newline=""))
         if r["main"] == "True" and r["model"] in ("graded", "twostate")]
assert len(units) == 40 * 4 * 10 * 2, len(units)
keep = ("role", "generator", "strength", "drift", "replicate", "subject", "half", "fold", "window", "model", "n_test", "n_below",
        "n_above", "loss_vs_null", "severe", "dll_extrap", "dll_within", "dll_catch", "worst_trial_label", "r_at_lower",
        "within_sd_min_S", "extrap_sd_min_S")
rows = [{k: u.get(k, "") for k in keep} for u in units]
with open(os.path.join(FIG, "melcon_v7_phase1_units.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(keep))
    w.writeheader()
    w.writerows(rows)

ideal = list(csv.DictReader(open(os.path.join(ANALYSIS, "recordings_ideal.csv"), newline="")))
assert len(ideal) == 272
with open(os.path.join(FIG, "melcon_v7_phase1_ideal.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["generator", "drift", "subject", "preferred", "delta", "graded_minus_null_per_trial"])
    w.writeheader()
    w.writerows({k: r[k] for k in w.fieldnames} for r in ideal)

for fam in ("graded", "twostate"):
    sev = [u for u in units if u["model"] == fam and u["severe"] == "True"]
    n_ext = sum(int(u["n_below"]) + int(u["n_above"]) for u in sev)
    n_all = sum(int(u["n_test"]) for u in sev)
    print(fam, dict(severe_units=len(sev), extrapolated_trial_share=n_ext / n_all if n_all else None))
print("wrote", os.path.join(FIG, "melcon_v7_phase1_units.csv"), "and melcon_v7_phase1_ideal.csv")
