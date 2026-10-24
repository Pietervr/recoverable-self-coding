#!/usr/bin/env python3
"""jitter/recost_rev7.py — the §8 cost of DESIGN rev 7 from a bench.py json, counted per FIT and per PARTICIPANT-DATASET.

bench.py's own `cost_projection` multiplies the rev 6 manifest's START counts (80 per participant-dataset) by the mean
seconds of an archived start. Under the rev 7 fitter every fit archives its EM steps and warm/re-seed chains as starts
(11-20 per fit), so that product understates the cost by the ratio of archived starts to the rev 6 four. This script
takes the same measurements and counts what the manifest actually fits:

  decision batch       23,000 participant-datasets × 5 folds × {G2, B2, G3+, B3+}          (S4b) + the S4a sets
  epsilon benchmark     50 sets × 20 datasets × 5 folds × {G0, B0}
  pilots/certification  (5 × 20 + 2 × 50) sets × 20 datasets of the decision batch, + 50 sets re-certification
  c0 batch              2 families × 500 datasets × (reduced + positive full-data fit)
  recovery              26 settings × 25 × 20 = 13,000 full-data datasets × the eight models
  profiles              13,000 datasets × 2 families × 15 constrained fits (2-start; 4-start extra)
  inherited pipeline    15.1 M Nelder-Mead runs + 50,350 BMS calls (unchanged)

Per-fit seconds come from the bench's per-spec start statistics (n_starts × seconds_mean = the archived solve time of
the 5 CV fits or the 1 full-data fit of that spec) and the profile wall times (per constrained fit). The parallel
efficiency and the development block's measured wall rate (600 s per participant-dataset on 12 workers, W2 sets 0-9,
24 Oct 2026) give the Mac wall time.

    recost_rev7.py results/bench/bench_<ts>.json [--dev-seconds 600]
"""
import argparse
import json
import os

DECISION = ("G2", "B2", "G3+", "B3+")
EPS = ("G0", "B0")
ALL8 = ("G0", "G1+", "G2", "G3+", "B0", "B1+", "B2", "B3+")
N = dict(
    s4b_decision_datasets=23_000,          # 9 × 100 + 3 × 50 + 100 sets × 20
    s4a_eps_datasets=50 * 20,
    s4a_pilot_cert_datasets=(5 * 20 + 2 * 50) * 20,
    s4a_recert_datasets=50 * 20,
    s4a_c0_datasets=2 * 500,
    s4b_recovery_datasets=26 * 25 * 20,
    s4b_profile_fits=26 * 25 * 20 * 2 * 15,
    s4b_nm_runs=15_105_000, s4b_bms_calls=50_350,
    s2_decision_datasets=3 * 25 * 20, s2_profile_fits=2 * 100 * 13, s2_misc_datasets=250,
    real_cv_datasets=20 * 2, real_generators=20, real_full_datasets=20, real_profile_fits=20 * 2 * 15,
    real_sensitivity_datasets=4 * 20 * 2,
)


def spec_seconds(per_spec: dict, names) -> float:
    """Archived solve seconds of the fits of `names` in one batch entry (5 CV fits or 1 full-data fit per spec)."""
    return float(sum(per_spec[n]["n_starts"] * per_spec[n]["seconds_mean"] for n in names))


def recost(d: dict, dev_seconds: float | None) -> dict:
    cv = d["cv_sequential"]["per_spec"]
    full = d["full_W2"]["per_spec"]
    t_dec = spec_seconds(cv, DECISION)                      # per participant-dataset, 5 folds, sequential
    t_eps = spec_seconds(cv, EPS)
    t_cv8 = spec_seconds(cv, ALL8)
    t_rec = spec_seconds(full, ALL8)                        # one full-data dataset, eight models
    t_c0 = spec_seconds(full, ("G2", "G3+"))                # one c0 pair (graded; the B pair costs more, averaged below)
    t_c0 = 0.5 * (t_c0 + spec_seconds(full, ("B2", "B3+")))
    p2, p4 = d["profile2"], d["profile4"]
    t_prof2 = 0.5 * sum(p2[f]["wall_s"] / p2[f]["n_constrained_fits"] for f in ("G", "B"))
    t_prof4 = 0.5 * sum(p4[f]["wall_s"] / p4[f]["n_constrained_fits"] for f in ("G", "B"))
    t_gen = d["generator"]["wall_s"]
    inh = d["inherited"]
    sec = dict(
        S4a=N["s4a_eps_datasets"] * t_eps + N["s4a_pilot_cert_datasets"] * t_dec + N["s4a_c0_datasets"] * t_c0,
        S4a_recertification_contingency=N["s4a_recert_datasets"] * t_dec,
        S4b_decision=N["s4b_decision_datasets"] * t_dec,
        S4b_recovery=N["s4b_recovery_datasets"] * t_rec,
        S4b_profiles_2start=N["s4b_profile_fits"] * t_prof2,
        S4b_profiles_4start_extra=N["s4b_profile_fits"] * (t_prof4 - t_prof2),
        S4b_inherited=N["s4b_nm_runs"] * inh["nm_s_per_run"] + N["s4b_bms_calls"] * inh["bms_s_per_call"],
        S2=N["s2_decision_datasets"] * t_dec + N["s2_profile_fits"] * t_prof4 + N["s2_misc_datasets"] * t_rec,
        real=N["real_cv_datasets"] * t_cv8 + N["real_generators"] * t_gen + N["real_full_datasets"] * t_rec
             + N["real_profile_fits"] * t_prof2 + N["real_sensitivity_datasets"] * t_cv8,
    )
    ch = {k: v / 3600.0 for k, v in sec.items()}
    base = ch["S4a"] + ch["S4b_decision"] + ch["S4b_recovery"] + ch["S4b_profiles_2start"] + ch["S4b_inherited"]
    worst = base + ch["S4a_recertification_contingency"] + ch["S4b_profiles_4start_extra"]
    par = d.get("parallel")
    eff = None
    if par:
        eff = par["starts_per_s"] / (par["workers"] * d["cv_sequential"]["starts_per_s"])
    out = dict(per_unit_seconds=dict(decision_dataset=t_dec, epsilon_dataset=t_eps, cv_all8_dataset=t_cv8,
                                     recovery_dataset=t_rec, c0_pair=t_c0, profile_fit_2start=t_prof2,
                                     profile_fit_4start=t_prof4, generator=t_gen),
               core_hours=ch, S4_core_hours_base=base, S4_core_hours_worst=worst, parallel_efficiency=eff,
               dev_block_seconds_per_dataset=dev_seconds)
    if dev_seconds:
        # the development block's measured 12-way task seconds per decision dataset scale the decision-batch lines
        f = dev_seconds / t_dec
        out["decision_scaled_by_dev_block"] = dict(factor=f, S4b_decision_core_h=ch["S4b_decision"] * f,
                                                   S4_base_core_h=base - ch["S4b_decision"] + ch["S4b_decision"] * f)
    return out


def markdown(d: dict, r: dict, path: str) -> str:
    u = r["per_unit_seconds"]; c = r["core_hours"]
    L = [f"# §8 re-cost (rev 7, per fit) from {os.path.basename(path)} — {d['utc']} S{d['subject']} ({d['machine'].get('chip', d['machine'])})", "",
         "Per-unit seconds (sequential, one XLA thread): "
         f"decision participant-dataset (5 folds × G2/B2/G3+/B3+) {u['decision_dataset']:.1f}; ε dataset (G0/B0) {u['epsilon_dataset']:.2f}; "
         f"recovery full-data dataset (8 models) {u['recovery_dataset']:.1f}; c0 pair {u['c0_pair']:.1f}; "
         f"constrained profile fit {u['profile_fit_2start']:.1f} (2-start) / {u['profile_fit_4start']:.1f} (4-start); generator fit {u['generator']:.0f}.", "",
         "| category | core-hours |", "|---|---|"]
    for k in ("S4a", "S4a_recertification_contingency", "S4b_decision", "S4b_recovery", "S4b_profiles_2start",
              "S4b_profiles_4start_extra", "S4b_inherited", "S2", "real"):
        L.append(f"| {k} | {c[k]:.0f} |")
    L.append(f"| **S4 total** | **{r['S4_core_hours_base']:.0f} base, {r['S4_core_hours_worst']:.0f} worst** |")
    if r.get("parallel_efficiency") is not None:
        eff = r["parallel_efficiency"]
        L.append("")
        L.append(f"12-way efficiency measured in the short parallel batch {eff:.2f}; the development block's long batches ran at about 0.8.")
        for e, lab in ((eff, "short-batch"), (0.8, "long-batch")):
            L.append(f"Mac wall at {lab} efficiency {e:.2f}: S4 base {r['S4_core_hours_base'] / (12 * e) / 24:.1f} days, worst {r['S4_core_hours_worst'] / (12 * e) / 24:.1f} days.")
    if "decision_scaled_by_dev_block" in r:
        s = r["decision_scaled_by_dev_block"]
        L.append("")
        L.append(f"Cross-check against the development block (W2 sets 0-9, 24 Oct: {r['dev_block_seconds_per_dataset']:.0f} task-seconds per decision dataset on 12 workers): "
                 f"factor {s['factor']:.2f} on the sequential rate → S4b decision {s['S4b_decision_core_h']:.0f} core-h, S4 base {s['S4_base_core_h']:.0f} core-h under 12-way contention.")
    L.append("")
    L.append("bench.py's own cost table multiplies rev 6 START counts by per-start seconds and understates the rev 7 cost; this table supersedes it.")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("--dev-seconds", type=float, default=None)
    ap.add_argument("--write", action="store_true", help="write recost_rev7_<utc>.md/.json beside the bench json")
    a = ap.parse_args()
    d = json.load(open(a.json))
    r = recost(d, a.dev_seconds)
    md = markdown(d, r, a.json)
    print(md)
    if a.write:
        base = os.path.join(os.path.dirname(a.json), f"recost_rev7_{d['utc']}")
        with open(base + ".md", "w") as f:
            f.write(md)
        with open(base + ".json", "w") as f:
            json.dump(r, f, indent=1)
        print("written", base + ".md")


if __name__ == "__main__":
    main()
