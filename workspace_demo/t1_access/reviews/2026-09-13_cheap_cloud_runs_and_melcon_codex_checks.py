"""Read-only calculations for the cloud/Melcon review; no fits or neural outcomes.

Reads landed simulation rows, the existing behavioural inventory and BDF headers only.
The filter check uses an artificial unit step, not EEG. Run with t1_access/.venv/bin/python.
"""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfiltfilt


T1 = Path(__file__).resolve().parents[1]
WORKSPACE = T1.parent
MELCON = WORKSPACE / "melcon_port"
csv.field_size_limit(10_000_000)


def read_csv(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def dataset_seed(name, kwargs, rep, seed):
    members = ("M0", "M2B", "M2H", "M2S", "M2K", "M3", "M3H", "M3V", "M3L")
    grid_tag = sum((i + 1) * int(round(1000 * float(kwargs.get(k, 0))))
                   for i, k in enumerate(("tau", "omega", "sep", "pi0", "alpha", "scale")))
    return int(np.random.default_rng([seed, members.index(name), grid_tag % (2**31 - 1), rep, 4]).integers(2**31))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    source = T1 / "sim_results/d4v12b/calibration_D4.csv"
    before = source.stat()
    groups = defaultdict(list)
    n_rows = 0
    old_seeds = []
    hashes = Counter()
    # Keep only small columns in memory: the source also contains all concept scores.
    with source.open(newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["generator"], row["grid"])
            n_rows += 1
            hashes[row["code_hash"]] += 1
            old_seeds.append(dataset_seed(key[0], json.loads(key[1]), int(row["rep"]), 2026))
            if key[0] == "M2B" or (key[0] == "M2S" and json.loads(key[1])["omega"] in (1, 2)):
                groups[key].append({k: float(row[k]) for k in
                    ("selection_ws_point", "failed", "fit_seconds", "wall_seconds")})
    after = source.stat()
    out = dict(calibration_source=str(source.relative_to(WORKSPACE)),
               calibration_sha256=digest(source), calibration_n=n_rows,
               calibration_hashes=dict(hashes),
               changed_while_reading=(before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns),
               references=[])
    for (name, grid), rows in sorted(groups.items()):
        valid = [r for r in rows if not r["failed"] and math.isfinite(r["selection_ws_point"])]
        x = np.sort([r["selection_ws_point"] for r in valid])
        n = len(x)
        sd = float(x.std(ddof=1))
        out["references"].append(dict(generator=name, grid=json.loads(grid), n=n,
            mean=float(x.mean()), sd=sd, mcse=sd / math.sqrt(n), median=float(np.median(x)),
            minimum=float(x[0]), mean_without_most_negative=float(x[1:].mean()),
            share_of_absolute_sum_from_worst_1pct=float(np.abs(x[:math.ceil(n * .01)]).sum() / np.abs(x).sum()),
            projections_assuming_observed_sd=[dict(extra_rows=extra,
                mcse=sd / math.sqrt(n + extra), normal_95_halfwidth=1.96 * sd / math.sqrt(n + extra))
                for extra in (0, 250, 500, 1000, 3000)],
            total_n_for_mcse_0_25=math.ceil((sd / .25)**2),
            old_cloud_mean_fit_seconds=float(np.mean([r["fit_seconds"] for r in rows])),
            old_cloud_mean_wall_seconds=float(np.mean([r["wall_seconds"] for r in rows]))))
    control = [dataset_seed("M2B", {}, rep, 2027) for rep in range(10)]
    probe = [dataset_seed("M2S", {"omega": omega}, rep, 2027)
             for omega in (1., 2.) for rep in range(20)]
    ref = [dataset_seed("M2S", {"omega": omega}, rep, 2028)
           for omega in (1., 2.) for rep in range(1000)]
    banks = dict(old=old_seeds, control=control, probe=probe, reference=ref)
    out["seeds"] = dict(sizes={k: len(v) for k, v in banks.items()},
        duplicates={k: len(v) - len(set(v)) for k, v in banks.items()},
        overlaps={f"{a}:{b}": len(set(banks[a]) & set(banks[b]))
                  for a in banks for b in banks if a < b})
    out["control_layout"] = [dict(shards=shards, datasets_per_shard=[
        sum(rep % shards == j for rep in range(10)) for j in range(shards)],
        simultaneous_dataset_workers=min(8, math.ceil(10 / shards)) * shards)
        for shards in (10, 2, 1)]
    out["control_cost_scenario_not_quote"] = dict(mac_core_hours=10 * 51 * 15.3 / 60,
        full_utilization_usd_equivalent=10 * 51 * 15.3 / 60 * .48,
        ten_single_worker_8vcpu_instances_at_same_per_vcpu_throughput_usd=10 * 51 * 15.3 / 60 * .48 * 8,
        two_five_worker_8vcpu_instances_at_same_per_vcpu_throughput_usd=10 * 51 * 15.3 / 60 * .48 * 8 / 5)

    trials_path = MELCON / "results/trials_all.csv"
    trials = read_csv(trials_path)
    by_recording = defaultdict(list)
    for row in trials:
        if row["task"] in ("nocue", "informative"):
            by_recording[(int(row["subject"]), row["task"])].append(row)
    records = []
    for (subject, task), rows in sorted(by_recording.items()):
        positive = [r for r in rows if r["present"] == "True" and float(r["contrast"]) > 0]
        contrasts = np.array([float(r["contrast"]) for r in positive])
        qs = np.quantile(np.log(contrasts), np.linspace(0, 1, 6))
        sides = {side: np.median([float(r["contrast"]) for r in positive if r["side"] == side])
                 for side in ("left", "right")}
        catch_by_block = Counter(int(r["block"]) for r in rows if r["catch"] == "True")
        records.append(dict(subject=subject, task=task, n=len(rows), positive_present=len(positive),
            missing_report=sum(r["seen"] == "" for r in rows),
            nonpositive_present=sum(r["present"] == "True" and float(r["contrast"]) <= 0 for r in rows),
            n_unique_contrasts=len(set(contrasts)), distinct_log_quintile_edges=len(set(qs)),
            left_right_median_contrast_ratio=float(max(sides.values()) / min(sides.values())),
            catch_per_block=dict(catch_by_block)))
    out["melcon_behaviour"] = dict(source=str(trials_path.relative_to(WORKSPACE)),
        sha256=digest(trials_path), total_trials_all_tasks=len(trials),
        recordings=len(records), subjects_by_task={task: sorted({r["subject"] for r in records if r["task"] == task})
                                                  for task in ("nocue", "informative")},
        common_subjects=len({r["subject"] for r in records if r["task"] == "nocue"} &
                            {r["subject"] for r in records if r["task"] == "informative"}),
        minimum_unique_positive_contrasts=min(r["n_unique_contrasts"] for r in records),
        minimum_distinct_log_quintile_edges=min(r["distinct_log_quintile_edges"] for r in records),
        side_median_ratio_median=float(np.median([r["left_right_median_contrast_ratio"] for r in records])),
        side_median_ratio_max=max(r["left_right_median_contrast_ratio"] for r in records),
        records=records)

    # BDF channel headers only, no sample data. Offsets follow the EDF/BDF fixed-width format.
    headers = read_csv(MELCON / "results/bdf_headers.csv")
    selected = [r for r in headers if int(r["samples_per_record"]) == 2048 or
                (r["subject"] == "sub-01" and r["task"] == "nocue")]
    bdf_checks = []
    for row in selected:
        sid, task = row["subject"], row["task"]
        path = WORKSPACE / "brain_data/melcon2024/ds006171" / sid / "eeg" / f"{sid}_task-{task}_eeg.bdf"
        with path.open("rb") as handle:
            fixed = handle.read(256)
            header_bytes = int(fixed[184:192])
            body = handle.read(header_bytes - 256)
        channels = int(fixed[252:256])
        prefilter_start = 136 * channels
        labels = [body[i * 16:(i + 1) * 16].decode("ascii", errors="replace").strip() for i in range(channels)]
        prefilters = [body[prefilter_start + i * 80:prefilter_start + (i + 1) * 80]
                      .decode("ascii", errors="replace").strip() for i in range(128)]
        bdf_checks.append(dict(subject=sid, task=task, n_channels=channels,
            first_label=labels[0], scalp_prefilter_descriptions=sorted(set(prefilters)),
            samples_per_record=int(row["samples_per_record"]), header_bytes_read=header_bytes,
            header_sha256=hashlib.sha256(fixed + body).hexdigest()))
    out["bdf_headers_only"] = bdf_checks

    # Exact version of the inherited projected-activity filter, with the new sampling rate.
    fs = 512.
    times = np.arange(-4 * 512, 4 * 512 + 1) / fs
    artificial_step = (times >= .3).astype(float)
    smooth = sosfiltfilt(butter(12, 10., btype="low", fs=fs, output="sos"), artificial_step)
    out["filter_step_check"] = dict(fs=fs, order=12, cutoff_hz=10,
        artificial_step_first_sample_ms=float(times[np.flatnonzero(artificial_step)[0]] * 1000),
        filtered_values_before_step=[dict(time_ms=float(times[j] * 1000), value=float(smooth[j]))
             for target in (.15, .20, .25, .28, .29)
             for j in [int(np.argmin(np.abs(times - target)))]],
        mean_in_270_to_300_ms=float(smooth[(times >= .27) & (times < .3)].mean()),
        note="Illustrates temporal leakage only; no EEG and no empirical effect size estimate.")
    out["window_geometry"] = dict(sixteen_samples_ms=1000 * 16 / 512,
        ten_nonoverlapping_sixteen_sample_windows_end_ms=1000 * 160 / 512,
        samples_in_exact_30ms_half_open_bins=[int(np.sum((times >= i * .03) & (times < (i + 1) * .03)))
                                             for i in range(10)])
    # llh_logisticB uses max(snrs) of EACH batch. A fixed x must have a fixed prediction instead.
    def inherited_mu(x, batch_max):
        return 2 / (1 + np.exp(-(x - 2))) - 2 / (1 + np.exp(-(batch_max - 2))) + 1
    out["graded_anchor_example"] = dict(x=1,
        same_parameters_prediction_with_batch_max_5=float(inherited_mu(1, 5)),
        same_parameters_prediction_with_batch_max_4=float(inherited_mu(1, 4)),
        note="Direct arithmetic from inherited llh_logisticB; continuous contrast requires a fixed anchor.")
    assert not out["changed_while_reading"]
    assert n_rows == 12000
    assert all(v == 0 for v in out["seeds"]["duplicates"].values())
    assert all(v == 0 for v in out["seeds"]["overlaps"].values())
    result = json.dumps(out, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(result)
    print(json.dumps({k: v for k, v in out.items() if k != "melcon_behaviour"}, indent=2))
    print(json.dumps({k: v for k, v in out["melcon_behaviour"].items() if k != "records"}, indent=2))


if __name__ == "__main__":
    main()
