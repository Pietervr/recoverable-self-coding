#!/usr/bin/env python3
"""The Phase 1 diagnostic panel manifest — DEVPLAN_v7.md rev 1 §2.1 (RSC 9cbcc0a). Read-only over the failed v6 battery
(results/battery/v6-ebaddf98807b/); no fit, no generated recording, no EEG. Writes results/devpanel_v7/panel_manifest.json,
committed before any regeneration.

Recording statistic: G_rec = the worst main-window graded loss relative to null, in nat per trial,
  G_rec = max over the 10 main windows of 4 (evidence_null - evidence_graded) / n_trials,
from the stored v6 `evidence` (held-out sum / 4) and `n_trials`. A window where null or graded is unavailable is skipped;
a recording whose status is not 'ok', or with no usable main window, is unrankable and never selected.

Per cell (generator x strength x drift; 3 replicates x 34 templates, up to 102 recordings), two recordings:
  worst   the largest G_rec;
  median  the rankable recording whose G_rec is closest to the cell's numpy median (even count: the mean of the two middle
          values), distinct from the worst.
Ties in either rule go to the lower replicate, then the lower subject. Rank 1 is the largest G_rec under the same tie order.

Every parent result is loaded through battery.load_verified against the manifest rebuilt from the namespace identity and its
calibration entry (payload SHA-256, sidecar, manifest digest, schema). The selection uses v6 held-out values: declared
development selection that enriches extreme graded losses for a mechanism diagnosis; no fit's start is ever chosen by it.

Usage:  ../../.venv/bin/python devpanel_select.py [--self-test] [--check]
  (default) select and write the manifest; an existing manifest is never overwritten
  --check   recompute and compare with the saved manifest (everything but created_utc)
"""
from __future__ import annotations

import os

THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")
for _v in THREAD_VARS:
    os.environ[_v] = "1"

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402

import battery as BT  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT_NAMESPACE = "v6-ebaddf98807b"
PARENT_IDENTITY = "ebaddf98807b3a06642e35315b67be74cc101382240a45d4d1fdc01072a8d021"
OUT_DIR = os.path.join(HERE, "results", "devpanel_v7")
OUT_PATH = os.path.join(OUT_DIR, "panel_manifest.json")
PLAN = "DEVPLAN_v7.md rev 1 §2.1 (RSC 9cbcc0a)"
STATISTIC = ("G_rec = max over the 10 main windows of 4 (evidence_null - evidence_graded) / n_trials, nat per trial; "
             "windows with null or graded unavailable skipped; status not ok or no usable window = unrankable")
SELECTION = ("per cell: worst = largest G_rec; median = rankable recording with G_rec closest to numpy median of the cell's "
             "rankable G_rec, distinct from the worst; ties to the lower replicate, then the lower subject")


def _sha_file(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def g_rec(res: dict) -> dict:
    """The recording statistic of one stored v6 result: dict(value, window, per_window) or dict(unrankable=reason)."""
    if res["status"] != "ok":
        return dict(unrankable=f"status: {res['status']}")
    pos = BT.main_positions(res["windows"])
    mi_null, mi_graded = res["models"].index("null"), res["models"].index("graded")
    ev = np.asarray(res["evidence"], dtype=float)[pos]
    n = np.asarray(res["n_trials"], dtype=float)[pos]
    loss = np.full(len(pos), np.nan)
    ok = np.isfinite(ev[:, mi_null]) & np.isfinite(ev[:, mi_graded]) & (n > 0)
    loss[ok] = 4.0 * (ev[ok, mi_null] - ev[ok, mi_graded]) / n[ok]
    if not ok.any():
        return dict(unrankable="no usable main window")
    j = int(np.nanargmax(loss))                                           # first of equal maxima (window order)
    return dict(value=float(loss[j]), window=int(res["windows"][pos[j]]),
                per_window=[None if not np.isfinite(v) else float(v) for v in loss])


def select(entries: list) -> dict:
    """entries: dicts with replicate, subject and value (rankable only). Returns worst, median, cell median and ranks."""
    order = sorted(entries, key=lambda e: (-e["value"], e["replicate"], e["subject"]))
    rank = {(e["replicate"], e["subject"]): i + 1 for i, e in enumerate(order)}
    worst = order[0]
    med = float(np.median([e["value"] for e in entries]))
    rest = [e for e in entries if (e["replicate"], e["subject"]) != (worst["replicate"], worst["subject"])]
    median = min(rest, key=lambda e: (abs(e["value"] - med), e["replicate"], e["subject"]))
    return dict(worst=worst, median=median, cell_median=med, rank=rank)


def self_test() -> None:
    e = lambda r, s, v: dict(replicate=r, subject=s, value=v)                    # noqa: E731
    # ties for the worst go to the lower replicate, then the lower subject
    out = select([e(1, 3, 5.0), e(0, 9, 5.0), e(0, 4, 5.0), e(2, 1, 1.0)])
    assert (out["worst"]["replicate"], out["worst"]["subject"]) == (0, 4), out["worst"]
    assert out["rank"][(0, 9)] == 2 and out["rank"][(1, 3)] == 3 and out["rank"][(2, 1)] == 4
    # even count: median = mean of the two middle values (5.0, 5.0 -> 5.0); closest distinct from the worst -> (0, 9)
    assert out["cell_median"] == 5.0 and (out["median"]["replicate"], out["median"]["subject"]) == (0, 9)
    # odd count: the middle value; the worst is never the median pick
    out = select([e(0, 1, 3.0), e(0, 2, 2.0), e(1, 1, 4.0)])
    assert out["cell_median"] == 3.0 and (out["worst"]["replicate"], out["worst"]["subject"]) == (1, 1)
    assert (out["median"]["replicate"], out["median"]["subject"]) == (0, 1)
    out = select([e(2, 5, 10.0), e(1, 7, 1.0), e(0, 8, 3.0), e(0, 2, 5.0)])       # median 4.0: 3.0 and 5.0 tie at 1.0
    assert (out["median"]["replicate"], out["median"]["subject"]) == (0, 2)
    # the statistic: worst window, unavailable windows skipped, status and all-unavailable unrankable
    windows = list(range(40))[10:30]
    ev = np.zeros((20, 3))
    ev[10:, 0] = -100.0
    ev[10:, 1] = -100.0
    ev[13, 1] = -150.0                                                    # main window 23: 4 * 50 / 200 = 1.0
    ev[15, 1] = np.nan                                                    # unavailable graded, skipped
    res = dict(status="ok", windows=windows, models=["null", "graded", "twostate"], evidence=ev, n_trials=np.full(20, 200))
    g = g_rec(res)
    assert g["value"] == 1.0 and g["window"] == 23 and g["per_window"][5] is None, g
    assert "unrankable" in g_rec(dict(res, status="excluded: x"))
    ev2 = ev.copy()
    ev2[10:, 0] = np.nan
    assert g_rec(dict(res, evidence=ev2)) == dict(unrankable="no usable main window")
    print("self-test PASS")


def build() -> dict:
    run_dir = os.path.join(BT.OUT_DIR, PARENT_NAMESPACE)
    manifest_path = os.path.join(run_dir, "manifest.json")
    with open(manifest_path) as fh:
        saved = json.load(fh)
    ident = BT.digest(saved)
    if ident != PARENT_IDENTITY:
        raise SystemExit(f"parent namespace identity {ident} differs from {PARENT_IDENTITY}")
    changed = sorted(f for f in BT.CODE_FILES if saved["code"][f] != BT.LOADED_CODE[f])
    if changed:
        raise SystemExit(f"v6 covered modules differ on disk from the parent identity: {changed}")
    subjects = BT.templates()
    if subjects != saved["templates"]:
        raise SystemExit("the template list differs from the parent identity")
    cal = BT.load_calibration(run_dir)
    cells, panel = [], []
    n_windows_worse_1 = n_windows = 0
    for g in BT.SY.GENERATORS:
        for si, st in enumerate(BT.STRENGTHS):
            for di in range(len(BT.DRIFTS)):
                rankable, unrankable, info = [], [], {}
                for r in range(BT.N_REP):
                    for s in subjects:
                        path = BT.cell_path(run_dir, g, si, di, r, s)
                        man = BT.recording_manifest(ident, g, si, di, r, s, cal[(g, st)])
                        res = BT.load_verified(path, man)
                        with open(path + ".sha256") as fh:
                            side = json.load(fh)
                        stat = g_rec(res)
                        info[(r, s)] = dict(path=os.path.relpath(path, HERE), manifest=res["manifest"], sidecar=side,
                                            sidecar_file_sha256=_sha_file(path + ".sha256"), stat=stat)
                        if "unrankable" in stat:
                            unrankable.append(dict(replicate=r, subject=s, reason=stat["unrankable"]))
                            continue
                        rankable.append(dict(replicate=r, subject=s, value=stat["value"]))
                        pw = np.array([np.nan if v is None else v for v in stat["per_window"]])
                        n_windows += int(np.isfinite(pw).sum())
                        n_windows_worse_1 += int((pw[np.isfinite(pw)] > 1.0).sum())
                sel = select(rankable)
                cell = dict(generator=g, strength=st, drift=bool(BT.DRIFTS[di]), drift_index=di,
                            n_recordings=BT.N_REP * len(subjects), n_rankable=len(rankable), unrankable=unrankable,
                            cell_median=sel["cell_median"], g_rec_max=sel["worst"]["value"],
                            g_rec_min=min(e["value"] for e in rankable))
                cells.append(cell)
                for role in ("worst", "median"):
                    e = sel[role]
                    key = (e["replicate"], e["subject"])
                    it = info[key]
                    panel.append(dict(role=role, generator=g, strength=st, drift=bool(BT.DRIFTS[di]), drift_index=di,
                                      replicate=e["replicate"], subject=e["subject"], path=it["path"],
                                      g_rec=e["value"], g_rec_window=it["stat"]["window"],
                                      g_rec_per_main_window=it["stat"]["per_window"], g_rec_rank=sel["rank"][key],
                                      n_rankable=len(rankable), cell_median=sel["cell_median"],
                                      distance_to_median=abs(e["value"] - sel["cell_median"]),
                                      parent_recording_manifest=it["manifest"], parent_sidecar=it["sidecar"],
                                      parent_sidecar_file_sha256=it["sidecar_file_sha256"]))
                print(f"{g} {st:<6} d{di}: rankable {len(rankable)}/{cell['n_recordings']}, median {sel['cell_median']:.4f}; "
                      f"worst r{sel['worst']['replicate']} sub-{sel['worst']['subject']:02d} {sel['worst']['value']:.4f}; "
                      f"median pick r{sel['median']['replicate']} sub-{sel['median']['subject']:02d} "
                      f"{sel['median']['value']:.4f} (rank {sel['rank'][(sel['median']['replicate'], sel['median']['subject'])]})",
                      flush=True)
    if len({p["path"] for p in panel}) != 40:
        raise SystemExit("the panel does not hold 40 distinct recordings")
    head = subprocess.run(["git", "-C", HERE, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    return dict(plan=PLAN, statistic=STATISTIC, selection=SELECTION,
                declared="development selection on v6 held-out values; mechanism diagnosis only (no frequency, no typical "
                         "fold behaviour, no group decision, no two-state failure sampling); no start is chosen by these values",
                selection_script=os.path.basename(__file__), selection_script_sha256=_sha_file(os.path.abspath(__file__)),
                parent_namespace=PARENT_NAMESPACE, parent_identity=ident, parent_manifest_sha256=_sha_file(manifest_path),
                parent_calibration_sha256=_sha_file(os.path.join(run_dir, "calibration.json")),
                parent_code=saved["code"], templates=subjects, repository_head=head, runtime=BT.runtime(),
                crosscheck=dict(main_windows_usable=n_windows, graded_more_than_1_nat_per_trial_below_null=n_windows_worse_1,
                                note="stage_c_catastrophe.output.txt (RSC 66e4b16) reports 1898 of 20400"),
                cells=cells, panel=panel, created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    self_test()
    if a.self_test:
        return
    if not a.check and os.path.exists(OUT_PATH):
        sys.exit(f"{OUT_PATH} exists; the panel manifest is never overwritten (use --check)")
    out = BT._jsonable(build())
    print(json.dumps(out["crosscheck"]))
    if a.check:
        with open(OUT_PATH) as fh:
            saved = json.load(fh)
        drop = ("created_utc", "repository_head")
        diff = sorted(k for k in set(saved) | set(out) if k not in drop and saved.get(k) != out.get(k))
        sys.exit(f"panel manifest differs in {diff}" if diff else "panel manifest reproduces")
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_PATH + ".tmp", "w") as fh:
        json.dump(out, fh, indent=1)
    os.replace(OUT_PATH + ".tmp", OUT_PATH)
    print(f"wrote {OUT_PATH} (sha256 {_sha_file(OUT_PATH)})")


if __name__ == "__main__":
    main()
