"""Read-only v6 stage-C audit. No generation, decoder, fitting, or run-file writes.

Use the RSC venv, preferably nice 10. The only output is the adjacent review JSON.
Group decisions use the production seed and 1,000,000 draws, including its common
cohort comparison. The saved result files do not contain fold parameters.
"""
import os
import sys

for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
            'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
sys.dont_write_bytecode = True

import hashlib
import json
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PORT = REPO / 'workspace_demo/melcon_port'
sys.path.insert(0, str(PORT))
import battery as BT
import group as G
import likelihood as LK
import recording as RC
import synthetic as SY

RUN = PORT / 'results/battery/v6-ebaddf98807b'
DIAG = HERE / 'melcon_v6_stage_c_diagnostics'
EXPECTED = 'ebaddf98807b3a06642e35315b67be74cc101382240a45d4d1fdc01072a8d021'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree_digest(path):
    entries = [(str(p.relative_to(path)), sha(p)) for p in sorted(path.rglob('*')) if p.is_file()]
    return {'files': len(entries), 'sha256': BT.digest(entries)}


def plain(x):
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, dict):
        return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    return x


def longest(flags):
    best = current = 0
    for flag in flags:
        current = current + 1 if flag else 0
        best = max(best, current)
    return best


def forbidden(*args, **kwargs):
    raise AssertionError('Audit attempted generation, decoder execution, fitting, or a production write')


started = time.monotonic()
before = {v: tree_digest(PORT / 'results/battery' / v) for v in ('v5-7fcb46729408', RUN.name)}
source_paths = [PORT / f for f in (*BT.CODE_FILES, 'PREREG_secondary_melcon.md', 'README.md')]
source_paths += [Path(BT.BMS_PATH), Path(SY.TRIALS_CSV)]
sources = {str(p.relative_to(REPO)): sha(p) for p in source_paths}
identity = BT.verify_runtime(str(RUN))
assert identity == EXPECTED
assert BT.namespace_path(BT.config_identity()) == str(RUN)
for mod, names in ((SY, ('generate',)), (BT.DEC, ('split_half',)),
                   (RC, ('recording_scores',)), (LK, ('fit', 'fold_scores', 'legacy_fold_scores')),
                   (BT, ('run_directory', 'write_result', 'run_recording', 'main'))):
    for name in names:
        setattr(mod, name, forbidden)

cal = BT.load_calibration(str(RUN))
reach = BT.load_store(str(RUN), 'reach')
assert len(cal) == 10 and all(e['accepted'] for e in cal.values()) and len(reach) == 5
subjects = BT.templates()
assert len(subjects) == 34
csv = pd.read_csv(RUN / 'replicates.csv')
assert len(csv) == 60 and not csv.duplicated(['generator', 'strength', 'drift', 'replicate']).any()
saved_diag = {r['cell']: r for r in json.loads((DIAG / 'stage_c_diag.json').read_text())}
saved_verdicts = json.loads((RUN / 'verdicts.json').read_text())
assert len(saved_diag) == 60 and len(saved_verdicts) == 20
outcomes, replicates, cells, extremes, paths = {}, [], [], [], []
arithmetic_error = 0.0
window_entries = 0
for g in SY.GENERATORS:
    for si, strength in enumerate(BT.STRENGTHS):
        for di, drift in enumerate(BT.DRIFTS):
            per_rec, gn_rec, tn_rec, all_gn, all_tn, all_delta = [], [], [], [], [], []
            key = (g, strength, di)
            outcomes[key] = []
            for rep in range(BT.N_REP):
                results = []
                for subject in subjects:
                    path = BT.cell_path(str(RUN), g, si, di, rep, subject)
                    manifest = BT.recording_manifest(identity, g, si, di, rep, subject, cal[(g, strength)])
                    result = BT.load_verified(path, manifest)
                    paths.append(Path(path))
                    assert result['status'] == 'ok' and result['subject'] == subject and result['task'] == 'nocue'
                    assert result['models'] == list(LK.PRIMARY) and result['windows'] == list(RC.WINDOWS)
                    ev = np.asarray(result['evidence'])
                    n = np.asarray(result['n_trials'])
                    assert np.all(n == len(SY.template(subject, 'nocue')))
                    avail = np.asarray(result['available'])
                    valid = avail[:, 1] & avail[:, 2]
                    error = np.abs((ev[:, 2] - ev[:, 1]) * 4 / n - result['delta'])[valid]
                    arithmetic_error = max(arithmetic_error, float(error.max()))
                    np.testing.assert_allclose((ev[:, 2] - ev[:, 1]) * 4 / n,
                                               result['delta'], rtol=1e-13, atol=1e-13, equal_nan=True)
                    pos = BT.main_positions(result['windows'])
                    assert np.all(avail[pos]) and np.all(np.isfinite(ev[pos]))
                    assert np.all(np.isfinite(result['auc'][pos]))
                    assert np.all((result['auc'][pos] >= 0) & (result['auc'][pos] <= 1))
                    dl = np.asarray(result['delta'])[pos]
                    gn = (ev[pos, 1] - ev[pos, 0]) * 4 / n[pos]
                    tn = (ev[pos, 2] - ev[pos, 0]) * 4 / n[pos]
                    per_rec.append(float(np.median(dl)))
                    gn_rec.append(float(np.median(gn)))
                    tn_rec.append(float(np.median(tn)))
                    all_gn.extend(gn); all_tn.extend(tn); all_delta.extend(dl)
                    w = int(np.argmax(dl))
                    extremes.append((float(dl[w]), g, strength, di, rep, subject, pos[w]))
                    window_entries += len(pos)
                    results.append(result)
                decision = G.decide(results, pos, 34, nsamp=G.BMS_NSAMP)
                assert decision['n_windows_eligible'] == 10
                assert len(decision['common_cohort']) == 34
                assert decision['common_cohort_runs'] == decision['runs']
                outcomes[key].append(decision['outcome'])
                row = csv[(csv.generator == g) & (csv.strength == strength) & (csv.drift == drift) & (csv.replicate == rep)].iloc[0]
                assert row.outcome == decision['outcome'] and row.n_missing == 0 and row.n_windows_eligible == 10
                assert row.calibration_usable and np.isclose(row.calibration_target, cal[(g, strength)]['target'])
                assert np.isclose(row.calibration_check, cal[(g, strength)]['check'])
                assert np.isclose(row.median_auc_main, np.median(decision['median_auc']))
                for outkey, inkey in (('twostate_min_gap', 'twostate_min_gap_median'),
                                      ('twostate_full_gap', 'twostate_full_gap_median'),
                                      ('occupancy_abs_error', 'occupancy_abs_error_median'),
                                      ('readout_highlow_contrast_unadjusted', 'readout_highlow_contrast_unadjusted_median'),
                                      ('readout_latent_corr', 'readout_latent_corr_median')):
                    values = np.asarray([r[inkey] for r in results], float)
                    median = float(np.median(values[np.isfinite(values)])) if np.isfinite(values).any() else np.nan
                    assert np.isclose(row[outkey], median, equal_nan=True), (key, rep, outkey)
                pxp = np.array([w['pxp'] for w in decision['windows']])
                delta_by_w = np.mean([r['delta'][pos] for r in results], axis=0)
                diag = dict(cell=f'{g} {strength} d{di} r{rep}', outcome=decision['outcome'], runs=decision['runs'],
                            pxp_median=[round(float(x), 3) for x in np.median(pxp, axis=0)],
                            pxp_max=[round(float(x), 3) for x in np.max(pxp, axis=0)],
                            argmax_counts=np.bincount(np.argmax(pxp, axis=1), minlength=3).tolist(),
                            longest_run_095={m: longest(pxp[:, i] >= G.PXP_THRESHOLD) for i, m in enumerate(LK.PRIMARY)},
                            delta_mean=round(float(np.mean(delta_by_w)), 5),
                            delta_min=round(float(np.min(delta_by_w)), 5), delta_max=round(float(np.max(delta_by_w)), 5))
                assert diag == saved_diag[diag['cell']], diag['cell']
                replicates.append(dict(diag, pxp_full_precision=pxp, median_auc=decision['median_auc']))
            gn, tn, dl = np.asarray(all_gn), np.asarray(all_tn), np.asarray(all_delta)
            catastrophic = (gn < -1) | (tn < -1)
            cells.append(dict(generator=g, strength=strength, drift=drift, n=len(dl),
                              graded_below_null_1=int((gn < -1).sum()), twostate_below_null_1=int((tn < -1).sum()),
                              graded_below_null_01=int((gn < -.1).sum()), twostate_below_null_01=int((tn < -.1).sum()),
                              median_recording_delta=float(np.median(per_rec)), delta_iqr=np.percentile(per_rec, [25, 75]),
                              fraction_recording_delta_positive=float(np.mean(np.asarray(per_rec) > 0)),
                              median_recording_gn=float(np.median(gn_rec)), median_recording_tn=float(np.median(tn_rec)),
                              mean_delta=float(np.mean(dl)), trimmed_descriptive_delta=float(np.mean(dl[~catastrophic]))))
            print(f'Verified {len(paths)}/2040 recordings; {len(replicates)}/60 full group decisions', flush=True)

verdicts = BT.cell_verdicts(outcomes, {k: bool(v['accepted']) for k, v in cal.items()}, list(outcomes))
encoded = {f'{g}|{st}|{BT.DRIFTS[di]}': dict(outcomes=outcomes[(g, st, di)], verdict=v)
           for (g, st, di), v in verdicts.items()}
assert encoded == saved_verdicts
assert set(paths) == set((RUN / 'recordings').glob('*.npy')) and len(paths) == 2040
assert len(list((RUN / 'recordings').glob('*.sha256'))) == 2040
assert not list(RUN.rglob('*.tmp'))
extremes.sort(reverse=True)

# Structural dose support only: no readout, generator call, fitted parameter, or EEG.
support = []
for subject in subjects:
    table = SY.template(subject, 'nocue')
    for btr, bte in ((1, 2), (2, 1), (3, 4), (4, 3)):
        for side in ('all', 'left', 'right'):
            tr = table[(table.block == btr) & table.present]
            te = table[(table.block == bte) & table.present]
            if side != 'all':
                tr, te = tr[tr.side == side], te[te.side == side]
            lc, lc_te = np.log(tr.contrast.to_numpy(float)), np.log(te.contrast.to_numpy(float))
            mean, sd = np.mean(lc), np.std(lc, ddof=1)
            xte = (lc_te - mean) / sd
            support.append(dict(subject=subject, train=btr, test=bte, side=side, n_train=len(lc), n_test=len(lc_te),
                                train_catch=int(table[(table.block == btr)]['catch'].sum()),
                                train_logc_range=[float(lc.min()), float(lc.max())],
                                test_logc_range=[float(lc_te.min()), float(lc_te.max())],
                                test_scaled_range=[float(xte.min()), float(xte.max())],
                                test_below_train=int((lc_te < lc.min()).sum()),
                                test_above_train=int((lc_te > lc.max()).sum())))

after = {v: tree_digest(PORT / 'results/battery' / v) for v in before}
assert after == before
assert sources == {str(p.relative_to(REPO)): sha(p) for p in source_paths}
assert BT.verify_runtime(str(RUN)) == EXPECTED
summary = dict(recordings=2040, main_recording_windows=window_entries, replicate_outcomes=Counter(r['outcome'] for r in replicates),
               verdict_counts=Counter(verdicts.values()), graded_below_null_1=sum(c['graded_below_null_1'] for c in cells),
               twostate_below_null_1=sum(c['twostate_below_null_1'] for c in cells), arithmetic_max_abs_error=arithmetic_error,
               matched_saved_diagnostics=60, unchanged_sources=True, unchanged_v5_v6=True)
evidence = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),
                audited_head=subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip(),
                audit_script_sha256=sha(__file__), identity=identity, runtime=BT.runtime(),
                source_sha256=sources, namespace_fingerprints=before,
                diagnostic_sha256={p.name: sha(p) for p in sorted(DIAG.iterdir()) if p.is_file()},
                elapsed_seconds=time.monotonic() - started, summary=summary, verdicts=encoded, cells=cells,
                replicates=replicates, largest_recording_maxima=extremes[:8], dose_support=support)
Path(__file__).with_suffix('.json').write_text(json.dumps(plain(evidence), indent=2, allow_nan=False) + '\n')
print(json.dumps(plain(summary), indent=2), flush=True)
