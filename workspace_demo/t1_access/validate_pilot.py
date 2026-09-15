"""A4: PILOT validation of the frozen instrument (PREREGISTRATION_T1_model.md §5, §6.1, §6.3, §9).

    workspace_demo/t1_access/.venv-decode/bin/python workspace_demo/t1_access/validate_pilot.py \
        --decoders <CAL run name> --run <PILOT capture run name>

Reads the frozen decoders (decoders/<CAL run>/decoders.npz) and a PILOT capture run (both conditions, primary set).
Reports, and decides nothing about outcomes:
- R1 per trial and layer: z = (w . (x - mean)/scale + b - z_mean) / z_sd, written for every PILOT trial
  (scores.npz: the variance inputs §10 takes from PILOT, including the cross-layer residual correlation);
- held-out-concept accuracy at k = 8 vs k = 0 (decision >= 0 means k = 8) per layer and per family, active
  condition; the no-target-report condition under the transferred decoder is descriptive;
- the §9 technical-failure line: accuracy below 0.75 in more than a third of the band layers 23-57;
- R3 (§6.3 as amended 15 Sept): correct = the target's frozen id has the highest logit among the 128 bank ids
  (chance 1/128), with its margin; the rate by level against the §5 rule (below 0.5 at k = 1, at least 0.5 at
  k = 4). If the rule fails, one interior level moves by §5, and that move is decided and recorded by Entropy SI;
- descriptive: the open-vocabulary target log-probability and the variant-maximum reading.
Outputs go to validation/<PILOT run>/ (report.json, scores.npz, figures), all committed.
"""

from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from capture import CAPTURES  # noqa: E402
from decode_cal import load_layer, parse_trial_id  # noqa: E402

BAND = list(range(23, 58))
LEVELS = [0, 1, 2, 3, 4, 6, 8]
ACC_LINE = 0.75


def load_answer_arrays(run_dir: Path, records: list[dict], name: str) -> np.ndarray:
    maps: dict[int, np.ndarray] = {}
    rows = []
    for r in records:
        if r["shard"] not in maps:
            maps[r["shard"]] = np.load(run_dir / f"{name}_{r['shard']:05d}.npy", mmap_mode="r")
        rows.append(np.asarray(maps[r["shard"]][r["index"]]))
    return np.stack(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--decoders", required=True)
    ap.add_argument("--run", required=True)
    args = ap.parse_args()

    dec = np.load(HERE / "decoders" / args.decoders / "decoders.npz")
    run_dir = CAPTURES / args.run
    header = json.loads((run_dir / "run_header.json").read_text())
    bank = json.loads((HERE / "stimuli" / "concepts.json").read_text())
    token_of = {c["id"]: c["token_id"] for c in bank["concepts"]}
    variants_of = {c["id"]: sorted({v["ids"][0] for v in c["variants"].values() if v["single_token"]})
                   for c in bank["concepts"]}
    answer_ids = header["identity"]["answer_ids"]
    variant_ids = header["identity"]["variant_ids"]
    records = []
    for line in (run_dir / "trials.jsonl").read_text().splitlines():
        t = json.loads(line)
        meta = parse_trial_id(t["trial_id"])
        if meta["split"] == "PILOT" and meta["set"] == "primary":
            records.append({**t, **meta})
    if not records:
        print("STOP: no PILOT primary trials in this run")
        return 1
    layers = dec["layers"].tolist()
    k = np.array([r["k"] for r in records])
    cond = np.array([r["condition"] for r in records])
    fam = np.array([r["family"] for r in records])

    z = np.zeros((len(records), len(layers)))
    raw = np.zeros_like(z)
    for j, l in enumerate(layers):
        X = load_layer(run_dir, records, l).astype(np.float64)
        d = ((X - dec["scaler_mean"][j]) / dec["scaler_scale"][j]) @ dec["coef"][j] + dec["intercept"][j]
        raw[:, j] = d
        z[:, j] = (d - dec["z_mean"][j]) / dec["z_sd"][j]

    def accuracy(mask):
        sel = mask & np.isin(k, [0, 8])
        return (((raw[sel] >= 0) == (k[sel, None] == 8)).mean(axis=0)).tolist()

    acc = {c: accuracy(cond == c) for c in ("active", "noreport")}
    acc_family = {f: accuracy((cond == "active") & (fam == f)) for f in sorted(set(fam))}
    band_idx = [layers.index(l) for l in BAND if l in layers]
    below = [layers[i] for i in band_idx if acc["active"][i] < ACC_LINE]
    technical_failure = len(below) > len(band_idx) / 3

    active = [i for i, r in enumerate(records) if r["condition"] == "active"]
    alog = load_answer_arrays(run_dir, [records[i] for i in active], "answer_logits")
    vlog = load_answer_arrays(run_dir, [records[i] for i in active], "variant_logits")
    target_pos = np.array([answer_ids.index(token_of[records[i]["concept"]]) for i in active])
    rows = np.arange(len(active))
    t_logit = alog[rows, target_pos]
    others = alog.copy()
    others[rows, target_pos] = -np.inf
    closed_correct = np.argmax(alog, axis=1) == target_pos
    margin = t_logit - others.max(axis=1)
    lse = np.array([records[i]["logsumexp"] for i in active])
    all_logits = np.concatenate([alog, vlog], axis=1)
    all_ids = answer_ids + variant_ids
    col = {t: c for c, t in enumerate(all_ids)}
    variant_max = np.array([all_logits[n, [col[t] for t in variants_of[records[i]["concept"]]]].max()
                            for n, i in enumerate(active)])
    ka = k[active]
    by_level = {str(lv): {"n": int(np.sum(ka == lv)), "closed_correct_rate": float(closed_correct[ka == lv].mean()),
                          "median_margin": float(np.median(margin[ka == lv])),
                          "median_target_logprob": float(np.median((t_logit - lse)[ka == lv])),
                          "median_variant_max_logprob": float(np.median((variant_max - lse)[ka == lv]))}
                for lv in LEVELS}
    dose_rule = by_level["1"]["closed_correct_rate"] < 0.5 <= by_level["4"]["closed_correct_rate"]

    out = HERE / "validation" / args.run
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / "scores.npz", z=z.astype(np.float32), layers=np.array(layers),
                        trial_ids=np.array([r["trial_id"] for r in records]), k=k, condition=cond,
                        concept=np.array([r["concept"] for r in records]), family=fam,
                        carrier=np.array([r["carrier"] for r in records]), draw=np.array([r["draw"] for r in records]))
    active_z = z[cond == "active"][:, band_idx]
    band_corr = (float((np.corrcoef(active_z, rowvar=False).sum() - len(band_idx)) / (len(band_idx) ** 2 - len(band_idx)))
                 if len(band_idx) > 1 else None)
    report = {
        "decoders": args.decoders, "run": args.run,
        "decoders_sha256": hashlib.sha256((HERE / "decoders" / args.decoders / "decoders.npz").read_bytes()).hexdigest(),
        "trials_sha256": hashlib.sha256((run_dir / "trials.jsonl").read_bytes()).hexdigest(),
        "n_trials": len(records), "layers": layers,
        "accuracy_k8_vs_k0": acc, "accuracy_by_family_active": acc_family,
        "band_layers_below_0.75": below, "technical_assay_failure": technical_failure,
        "r3_closed_set_by_level": by_level, "chance": 1 / len(answer_ids), "dose_rule_passes": dose_rule,
        "band_score_correlation_mean_offdiagonal": band_corr,
    }
    (out / "report.json").write_text(json.dumps(report, indent=1) + "\n")
    figures(out, layers, acc, acc_family, by_level, len(answer_ids))
    print(json.dumps({k2: report[k2] for k2 in ("technical_assay_failure", "band_layers_below_0.75",
                                                "dose_rule_passes")}, indent=1))
    print(f"-> {out}")
    return 0


def figures(out: Path, layers, acc, acc_family, by_level, n_answer) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    ax = axes[0]
    ax.axvspan(23, 57, color="0.92", label="workspace band 23-57")
    ax.plot(layers, acc["active"], color="black", lw=2, label="active (all families)")
    ax.plot(layers, acc["noreport"], color="0.5", lw=1.5, ls="--", label="no-target-report (transfer)")
    for f, a in acc_family.items():
        ax.plot(layers, a, lw=0.7, alpha=0.6, label=f)
    ax.axhline(ACC_LINE, color="crimson", lw=1, label="§9 line 0.75")
    ax.set(xlabel="layer", ylabel="held-out accuracy, k = 8 vs k = 0", ylim=(0.4, 1.01),
           title="PILOT: frozen R1 decoder")
    ax.legend(fontsize=6, ncol=2, loc="lower right")
    ax = axes[1]
    lv = [int(x) for x in by_level]
    ax.plot(lv, [by_level[str(x)]["closed_correct_rate"] for x in lv], "o-", color="black")
    ax.axhline(0.5, color="crimson", lw=1, label="§5 crossing 0.5")
    ax.axhline(1 / n_answer, color="0.5", lw=1, ls=":", label=f"chance 1/{n_answer}")
    ax.axvspan(1, 4, color="0.92", label="crossing window k = 1..4")
    ax.set(xlabel="dose k (target clauses of 8)", ylabel="closed-set correct rate (active)", ylim=(-0.02, 1.02),
           title="PILOT: R3 by dose")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out / "pilot_validation.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    sys.exit(main())
