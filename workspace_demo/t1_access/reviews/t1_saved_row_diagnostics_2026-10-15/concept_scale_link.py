"""Is the concentration of saved_row_diagnostics.py caused by the concept random scale? (read-only; no fits)

The M2S generator draws each concept's log scale v_c ~ N(0, omega^2) as the first draw of a generator seeded by
simulate.dataset_seed(name, grid, rep, D, seed) (simulate.make_dataset: u_c is drawn before any noise). The draw is
regenerated here exactly, without simulating trials or fitting, at the CLI default base seed 2026. Whether 2026 is
the base seed d4v12b used is TESTED, not assumed: under a wrong seed the regenerated v_c are independent of the
saved per-concept scores, so the dominant concept would be the largest-v_c concept in about 1/64 of datasets and the
rank correlation would centre on zero.

Per M2S setting with omega > 0, over the 1,000 saved datasets (primary predictor, delta_per_concept):
  hit     share of datasets whose most negative Delta_c belongs to the concept with the largest v_c (chance 1/64)
  (No correlation over all 64 concepts is reported. Against v_c it came out positive, driven by the many
   small-scale concepts; against the S4 loss (s^2 - 1)/2 - log s with s = e^{v_c} it fell from 0.59 at omega 0.5 to
   0.00 at omega 2, because the fitted mixture scale adapts to the training concepts, so a concept's real scale
   mismatch is not e^{v_c}. The fitted scales are not saved, so the bulk relation is not modelled here; the tail
   claim of S4 is what the hit rate tests.)
  ext     for the 10 datasets with the most negative point estimate: the v_c of the dominant concept in units of
          omega, and its rank among the 64 (1 = largest)
Run: NPROC=1 <t1 venv>/python concept_scale_link.py   (writes concept_scale_link.output.txt beside it)
"""
import csv
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, T1)
import simulate as S   # noqa: E402  (imports models/analyze; nothing is fitted)

CAL = os.path.join(T1, "sim_results", "d4v12b", "calibration_D4.csv")
BASE_SEED, D, C = 2026, 4, 64
csv.field_size_limit(sys.maxsize)



def main():
    rows = {}
    with open(CAL, newline="") as fh:
        for r in csv.DictReader(fh):
            g = json.loads(r["grid"])
            if r["generator"] == "M2S" and g.get("omega", 0) > 0:
                rows.setdefault(g["omega"], []).append(
                    (int(r["rep"]), float(r["selection_ws_point"]),
                     np.asarray(json.loads(r["delta_per_concept"])["selection"], float).ravel()))
    out = [f"concept random scale v_c regenerated at base seed {BASE_SEED} (D = {D}); chance hit rate 1/64 = 0.016"]
    out.append(f"{'omega':>6} {'n':>5} {'hit':>7}   10 most negative datasets: v_c/omega of the dominant concept (rank)")
    for om in sorted(rows):
        theta = S.generator_theta("M2S", omega=om)
        sd = float(np.exp(theta[S.M.MEMBERS["M2S"].re_index]))
        hits, rec = 0, []
        for rep, pt, dc in rows[om]:
            seed = S.dataset_seed("M2S", {"omega": om}, rep, D, BASE_SEED)
            v = np.random.default_rng(seed).normal(0.0, sd, size=C)
            dom = int(np.argmin(dc))
            hits += dom == int(np.argmax(v))
            rec.append((pt, v[dom] / om, int(np.sum(v > v[dom])) + 1))
        rec.sort()
        ext = ", ".join(f"{z:+.2f} ({k})" for _, z, k in rec[:10])
        out.append(f"{om:>6g} {len(rows[om]):>5} {hits / len(rows[om]):>7.3f}   {ext}")
    text = "\n".join(out)
    print(text)
    with open(os.path.join(HERE, "concept_scale_link.output.txt"), "w") as fh:
        fh.write(text + "\n")


if __name__ == "__main__":
    main()
