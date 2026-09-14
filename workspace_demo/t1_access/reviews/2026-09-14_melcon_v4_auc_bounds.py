#!/usr/bin/env python3
"""Exact no-drift population AUC of the X1/X2 scalar latent, conditional on
the behavioural templates used by DRAFT v4. Stdlib only; no EEG, epochs,
decoder, fitting, or battery execution. See Continuation review 4.

For a present trial with occupancy L and right-hemifield flag h, its latent
against a fresh catch N(0,1) has AUC
  (1-L) Phi(.3*h/sqrt(2)) + L Phi((d+.3*h)/sqrt(2)).
The no-drift present density is a mixture of unit normals with nonnegative
means; its likelihood ratio against catch N(0,1) is nondecreasing. Thus latent
ranking gives the optimal population ROC. The epochs add label-independent
noise to a function of that latent, so cannot improve that population ROC.
This is not a deterministic upper bound on finite-sample measured AUC.
"""
import argparse
import ast
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median, stdev

PORT = Path(__file__).resolve().parents[2] / 'melcon_port'


def literal(name, filename):
    for node in ast.parse((PORT / filename).read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError((name, filename))


def phi(x):
    return .5 * (1 + math.erf(x / math.sqrt(2)))


def run():
    halves = literal('HALVES', 'decoder.py')
    min_half = literal('MIN_CATCH_HALF', 'decoder.py')
    min_catch = literal('MIN_CATCH', 'likelihood.py')
    min_side = literal('MIN_SIDE', 'likelihood.py')
    slope = literal('DOSE_SLOPE', 'synthetic.py')
    hemi = literal('HEMI_SHIFT', 'synthetic.py')
    n_cal = literal('N_CAL', 'battery.py')
    assert halves == ((1, 2), (3, 4)) and slope == 1.5 and hemi == .3
    path = PORT / 'results/trials_all.csv'
    with path.open(newline='') as f:
        raw = list(csv.DictReader(f))
    grouped = {}
    for row in raw:
        if row['task'] != 'nocue' or int(row['subject']) == 36:
            continue
        r = dict(row)
        for k in ('present', 'catch'):
            assert r[k] in ('True', 'False')
            r[k] = r[k] == 'True'
        assert r['present'] != r['catch']
        r['contrast'] = float(r['contrast']) if r['contrast'] else math.nan
        if r['present'] and not r['contrast'] > 0:
            continue
        r['block'] = int(r['block'])
        grouped.setdefault(int(r['subject']), []).append(r)
    selected = {}
    for subject, rows in sorted(grouped.items()):
        if sum(r['present'] for r in rows) < 250 or sum(r['catch'] for r in rows) < 25:
            continue
        blocks = sorted({r['block'] for r in rows})
        ok = blocks == [1, 2, 3, 4]
        for b in blocks:
            br = [r for r in rows if r['block'] == b]
            ok &= sum(r['catch'] for r in br) >= min_catch
            ok &= min(sum(r['present'] and r['side'] == side for r in br) for side in ('left', 'right')) >= min_side
        for half in halves:
            ok &= sum(r['catch'] for r in rows if r['block'] in half) >= min_half
        if ok:
            selected[subject] = sorted(rows, key=lambda r: float(r['onset_pd']))
    assert len(selected) == 34
    records = []
    for subject, rows in selected.items():
        logs = [math.log(r['contrast']) for r in rows if r['present']]
        m, s = mean(logs), stdev(logs)  # ddof=1 over the entire recording, exactly generate()
        out = {'subject': subject, 'n_trials': len(rows), 'log_contrast_mean': m, 'log_contrast_sd': s, 'halves': []}
        for half in halves:
            pres = [r for r in rows if r['block'] in half and r['present']]
            L = [1 / (1 + math.exp(-slope * ((math.log(r['contrast']) - m) / s))) for r in pres]
            h = [int(r['side'] == 'right') for r in pres]
            auc = {g: mean((1-l) * phi(hemi*side / math.sqrt(2)) + l * phi((d+hemi*side) / math.sqrt(2))
                           for l, side in zip(L, h)) for g, d in (('X1', 2.), ('X2', .8))}
            out['halves'].append({'blocks': half, 'n_present': len(pres), 'n_catch': sum(r['catch'] for r in rows if r['block'] in half),
                                  'mean_occupancy': mean(L), 'right_fraction': mean(h), 'population_auc': auc})
        out['recording_mean_auc'] = {g: mean(x['population_auc'][g] for x in out['halves']) for g in ('X1', 'X2')}
        records.append(out)
    calibrators = records[:n_cal]
    totals = {g: {'first_eight_median_of_half_means': median(r['recording_mean_auc'][g] for r in calibrators),
                  'all_34_median_of_half_means': median(r['recording_mean_auc'][g] for r in records),
                  'all_half_min': min(h['population_auc'][g] for r in records for h in r['halves']),
                  'all_half_max': max(h['population_auc'][g] for r in records for h in r['halves'])} for g in ('X1', 'X2')}
    for g in totals:
        assert totals[g]['first_eight_median_of_half_means'] < .77  # lower edge of target .8 +/- .03
    files = ['synthetic.py', 'battery.py', 'decoder.py', 'likelihood.py', 'results/trials_all.csv']
    return {'scope': 'behaviour-only exact population calculation; no epochs or fits',
            'calibration_match': 'population latent limit of mean over two held-out halves and ten main windows, then median over first eight templates; windows identical at the noiseless latent limit',
            'calibration_subjects': [r['subject'] for r in calibrators], 'n_templates': len(records),
            'equal_occupancy_no_hemifield': {g: .25 + .5*phi(d/math.sqrt(2)) for g, d in (('X1', 2.), ('X2', .8))},
            'summary': totals, 'records': records,
            'source_sha256': {f: hashlib.sha256((PORT / f).read_bytes()).hexdigest() for f in files}}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    result = run()
    if args.out:
        args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'records'}, indent=2))
