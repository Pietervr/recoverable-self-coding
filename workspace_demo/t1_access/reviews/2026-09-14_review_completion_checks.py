#!/usr/bin/env python3
"""Read-only stdlib evidence for the two requested R052 review completions.

Reads saved JSON/CSV and source bytes; imports no model, generates no data, and
runs no optimizer or decoder. Writes only the adjacent review evidence JSON.
The earlier full fitter verifier is not re-executed here.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import zipfile

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[1]
MELCON = WORKSPACE / 'melcon_port'
V5 = MELCON / 'results/battery/v5-7fcb46729408'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    calibration_path = V5 / 'calibration.json'
    entries = json.loads(calibration_path.read_text())
    manifest = json.loads((V5 / 'manifest.json').read_text())
    benchmark = json.loads((MELCON / 'results/battery/benchmark.json').read_text())
    identity = hashlib.sha256(json.dumps(manifest, sort_keys=True, default=str).encode()).hexdigest()
    assert V5.name == 'v5-' + identity[:12]
    source_matches = {name: sha(MELCON / name) == expected for name, expected in manifest['code'].items()}
    assert all(source_matches.values())
    expected_keys = {(g, s) for g in ('G1', 'G2', 'G3', 'X1', 'X2') for s in ('weak', 'strong')}
    assert len(entries) == 10 and {(e['generator'], e['strength']) for e in entries} == expected_keys
    cells = []
    for e in sorted(entries, key=lambda e: (e['generator'], e['strength'])):
        assert e['subjects'] == list(range(1, 9))
        assert e['headroom'] == {'weak': .5, 'strong': .9}[e['strength']]
        assert math.isclose(e['target'], .5 + e['headroom'] * (e['population_limit'] - .5), abs_tol=1e-14)
        values = [*e['grid'].values(), *e['refinement'].values(), e['check'], e['first']['check']]
        assert all(math.isfinite(x) and 0 <= x <= 1 for x in values)
        assert e['accepted'] == (abs(e['check'] - e['target']) <= e['tolerance'])
        assert e['grid_reaches_target'] == (max([*e['grid'].values(), *e['refinement'].values()]) >= e['target'])
        assert e['refined'] == (abs(e['first']['check'] - e['target']) > e['tolerance'])
        cells.append({k: e[k] for k in ('generator', 'strength', 'population_limit', 'target', 'amplitude',
                                       'check', 'accepted', 'grid_reaches_target', 'refined')}
                     | dict(check_minus_target=e['check'] - e['target'], at_6_4=e['grid']['6.4']))
    refs = {}
    for g in ('G1', 'G2', 'G3', 'X1', 'X2'):
        pair = [e for e in entries if e['generator'] == g]
        values = [e['grid']['6.4'] for e in pair]
        r = statistics.mean(values)
        refs[g] = dict(v5_eight_template_values=values, empirical_reference=r,
                       absolute_two_draw_difference=abs(values[1] - values[0]),
                       illustrative_v6_weak=.5 + .5 * (r - .5),
                       illustrative_v6_strong=.5 + .8 * (r - .5),
                       target_separation=.3 * (r - .5),
                       plus_minus_003_band_overlap=max(0, .06 - .3 * (r - .5)))
    unusable = sorted(f"{e['generator']} {e['strength']}" for e in entries if not e['accepted'])
    edge = sorted(f"{e['generator']} {e['strength']}" for e in entries if e['accepted'] and not e['grid_reaches_target'])
    assert unusable == ['X1 strong', 'X2 weak']
    assert edge == ['G2 strong', 'G3 strong', 'X2 strong']
    calls = dict(reach=5 * 2 * 34, base=5 * 2 * 34 + 10 * (8 + 1) * 34,
                 maximum=5 * 2 * 34 + 10 * (8 + 5 + 2) * 34,
                 one_extra_all_cell_draw=10 * 34)
    costs = dict(calls=calls, assumed_seconds_per_generated_decoder_call=11.6,
                 projected_core_hours={k: n * 11.6 / 3600 for k, n in calls.items()},
                 ideal_wall_hours={str(n): {k: calls[k] * 11.6 / 3600 / n for k in ('base', 'maximum')}
                                   for n in (2, 3)}, benchmark=benchmark)
    assert math.isclose(benchmark['projected_stage_c_core_hours'],
                        benchmark['recordings_stage_c'] * (benchmark['generate_s'] + benchmark['pipeline_s']) / 3600)

    package = HERE / 'pc_audit_2026-09-14'
    with (package / 'results/audit_fits.csv').open(newline='') as stream:
        audit = list(csv.DictReader(stream))
    m2s = [r for r in audit if r['member'] == 'M2S' and float(r['miss']) == 1]
    assert len(m2s) == 1
    miss = m2s[0]
    kfields = ('generator', 'grid', 'rep', 'size', 'member')
    matched = []
    with zipfile.ZipFile(package / 'archive/audit_fits_checkpoint.zip') as archive:
        for name in archive.namelist():
            for row in json.loads(archive.read(name)):
                if all(str(row[k]) == miss[k] for k in kfields):
                    matched.append((name, row))
    assert len(matched) == 1
    filename, row = matched[0]
    selected = {k: miss[k] for k in miss if k not in ('pipeline_theta', 'strong_theta')}
    selected['archive_filename'] = filename
    selected['per_start_archive_available'] = bool(row.get('starts_archive'))
    selected['heldout_gain_nat_per_trial'] = (float(miss['strong_heldout']) - float(miss['pipeline_heldout'])) / float(miss['n_heldout_trials'])
    with (package / 'results/prefix_scoring.csv').open(newline='') as stream:
        selected['prefixes'] = [{k: r[k] for k in ('recipe', 'n_selected', 'gap', 'miss', 'heldout_change') if k in r}
                               for r in csv.DictReader(stream) if all(r[k] == miss[k] for k in kfields)]
    selected['archived_near_best_starts'] = [dict(batch=x['batch'], index=x['i'], loglik=x['loglik'], converged=x['converged'])
                                           for x in row.get('starts_archive', [])
                                           if x['loglik'] is not None and float(miss['strong_loglik'])-x['loglik'] <= .5]
    previous = json.loads((HERE / '2026-09-14_fitter_evidence_checks.json').read_text())
    times = previous['timing_extrapolations_not_new_benchmarks']['full_96']
    table = times['table']
    without_m2s_outer = times['outer_all']['candidate'] - 80 * table['M2S/outer']['added_seconds_per_start']
    without_m2s_nested = times['nested_one_layer']['candidate_seconds'] - 5 * 80 * (
        4 * table['M2S/inner']['added_seconds_per_start'] + table['M2S/outer']['added_seconds_per_start'])
    output = dict(scope=__doc__, input_sha256={str(p.relative_to(WORKSPACE)): sha(p) for p in (
        calibration_path, V5 / 'manifest.json', MELCON / 'results/battery/benchmark.json',
        MELCON / 'battery.py', MELCON / 'synthetic.py', MELCON / 'PREREG_secondary_melcon.md',
        package / 'results/audit_fits.csv', HERE / '2026-09-14_fitter_evidence_checks.json')},
        melcon=dict(namespace=V5.name, identity_sha256=identity, v5_source_matches=source_matches,
                    accepted_count=len(entries)-len(unusable), unusable=unusable,
                    accepted_without_grid_crossing=edge, cells=cells,
                    illustrative_references_not_measured_v6=refs, cost_projection=costs),
        fitter=dict(single_full_audit_m2s_miss=selected,
                    provisional_cold_m2s_candidate_extrapolation=dict(outer_seconds=without_m2s_outer,
                        nested_one_layer_seconds=without_m2s_nested,
                        nested_ratio_to_cold=without_m2s_nested/times['nested_one_layer']['cold_seconds'],
                        basis='PC pooled batch timings; not a measured full pipeline or Mac forecast')))
    target = HERE / '2026-09-14_review_completion_checks.json'
    target.write_text(json.dumps(output, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(dict(evidence=str(target), accepted=8, unusable=unusable, accepted_without_crossing=edge,
                          empirical_reference_examples={g: refs[g] for g in ('X1', 'X2')},
                          m2s_miss=selected, cost_projection=costs), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
