"""Independent read-only v6 calibration audit; stdlib only, no generation or fits."""
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PORT = ROOT / 'workspace_demo/melcon_port'
RUN = PORT / 'results/battery/v6-ebaddf98807b'
EXPECTED = {
    'manifest.json': '6dd1414b6c8d34625efe4554f158e8a383ced6771c15965bd6a296409d2063f3',
    'reach.json': 'bbcdf173e523d4954cead3643dccc318051a95a9a975df978b5c8f947f359396',
    'calibration.json': 'efbf3f82c127c23c43b8dfb33d295bbe50b7fdb596c88cf845b1092c4ebc6c1f',
}
GENS = ['G1', 'G2', 'G3', 'X1', 'X2']
SUBS = list(range(1, 35))
GRID = [0.2, 0.4, 0.7, 1.0, 1.5, 2.2, 3.2, 6.4]
TOL = 0.03

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()

def close(a, b):
    assert math.isclose(a, b, rel_tol=0, abs_tol=2e-14), (a, b)

def sealed(entry):
    assert entry['sha256'] == digest({k: v for k, v in entry.items() if k != 'sha256'})

stats = []
def statistic(st, g, phase, index, amplitude):
    assert st['generator'] == g and st['phase'] == phase and st['index'] == index
    close(st['amplitude'], amplitude)
    assert st['tags_pattern'] == [{'reach': 4, 'calibration': 5, 'check': 6}[phase], GENS.index(g), index]
    assert st['complete'] is True and st['failures'] == []
    assert st['n_recordings_expected'] == st['n_recordings_decoded'] == 34
    assert st['n_auc_expected'] == st['n_auc_finite'] == 680
    assert set(st['auc']) == set(st['per_template']) == {str(s) for s in SUBS}
    means = []
    for s in SUBS:
        a = st['auc'][str(s)]
        assert len(a) == 2 and all(len(row) == 10 for row in a)
        vals = [v for row in a for v in row]
        assert all(math.isfinite(v) and 0 <= v <= 1 for v in vals)
        m = statistics.fmean(vals)
        close(m, st['per_template'][str(s)])
        means.append(m)
    close(statistics.median(means), st['value'])
    assert st['n_jobs'] == 1
    stats.append(st)

def main():
    hashes = {name: sha(RUN / name) for name in EXPECTED}
    assert hashes == EXPECTED
    manifest = json.loads((RUN / 'manifest.json').read_text())
    identity = digest(manifest)
    assert RUN.name == 'v6-' + identity[:12]
    assert manifest['templates'] == SUBS and manifest['q'] == {'weak': 0.5, 'strong': 0.8}
    assert manifest['cal_grid'] == GRID and manifest['cal_tol'] == TOL
    assert manifest['seed_phases'] == {'stage_c': 1, 'benchmark': 3, 'reach': 4, 'calibration': 5, 'check': 6, 'terminal': 7}
    source_hashes = {f: sha(PORT / f) for f in manifest['code']}
    assert source_hashes == manifest['code']
    assert sha(PORT / '../sergent_port/bms.py') == manifest['runtime']['bms_sha256']
    assert sha(PORT / 'results/trials_all.csv') == manifest['events_table']
    rr = json.loads((RUN / 'reach.json').read_text())
    cc = json.loads((RUN / 'calibration.json').read_text())
    assert len(rr) == 5 and len(cc) == 10
    reach = {r['generator']: r for r in rr}
    cal = {(c['generator'], c['strength']): c for c in cc}
    assert len(reach) == 5 and len(cal) == 10
    cells = []
    for g in GENS:
        r = reach[g]
        sealed(r)
        assert r['subjects'] == SUBS and r['usable'] and r['unusable_reason'] is None
        assert len(r['draws']) == 2 and r['reach'] > 0.5
        for i, d in enumerate(r['draws']):
            statistic(d, g, 'reach', i, 6.4)
        vals = [d['value'] for d in r['draws']]
        assert vals == r['values']
        close(statistics.fmean(vals), r['reach'])
        close(abs(vals[1] - vals[0]), r['disagreement'])
        for i, strength in enumerate(('weak', 'strong')):
            c = cal[(g, strength)]
            sealed(c)
            assert c['subjects'] == SUBS and c['reach_sha256'] == r['sha256']
            close(c['reach'], r['reach'])
            target = 0.5 + (0.5 if i == 0 else 0.8) * (r['reach'] - 0.5)
            close(c['target'], target)
            close(r['targets'][strength], target)
            assert [d['amplitude'] for d in c['grid']] == GRID
            for d in c['grid']:
                statistic(d, g, 'calibration', i, d['amplitude'])
                close(c['curve'][str(d['amplitude'])], d['value'])
            v = [d['value'] for d in c['grid']]
            assert all(x <= y for x, y in zip(v, v[1:])) and not c['nonmonotone']
            assert v[0] < target
            j = next(j for j in range(1, 7) if v[j] >= target)
            lo, hi = GRID[j-1], GRID[j]
            amplitude = lo + (target - v[j-1]) * (hi - lo) / (v[j] - v[j-1])
            b = c['first_bracket']
            assert b['usable'] and b['lo'] == lo and b['hi'] == hi < 6.4
            close(b['s_lo'], v[j-1]); close(b['s_hi'], v[j])
            close(b['amplitude'], amplitude); close(c['amplitude'], amplitude)
            chk = c['first_check']
            statistic(chk['statistic'], g, 'check', i, amplitude)
            close(chk['amplitude'], amplitude); close(c['check'], chk['statistic']['value'])
            assert abs(c['check'] - target) <= TOL and chk['within_tolerance']
            assert c['accepted'] and c['unusable_reason'] is None
            assert c['refinement'] is None and c['terminal_check'] is None and c['statistics_drawn'] == 9
            cells.append(dict(generator=g, strength=strength, target=target, amplitude=amplitude,
                              check=c['check'], error=c['check']-target, bracket=[lo, hi]))
    assert len(stats) == 100
    flags = json.loads((RUN / 'strengths.json').read_text())
    comparisons = {}
    for g in GENS:
        w, s = cal[(g, 'weak')], cal[(g, 'strong')]
        gap, diff = s['target']-w['target'], s['check']-w['check']
        close(flags[g]['target_gap'], gap); close(flags[g]['achieved_difference'], diff)
        assert flags[g]['bands_overlap'] == (gap <= 2*TOL)
        assert flags[g]['reversal'] == (diff <= 0)
        assert flags[g]['resolved'] == (gap > 2*TOL and diff > 0)
        values64 = [d['value'] for d in reach[g]['draws']] + [w['grid'][-1]['value'], s['grid'][-1]['value']]
        offsets = [b['value']-a['value'] for a, b in zip(w['grid'], s['grid'])]
        comparisons[g] = dict(target_gap=gap, check_difference=diff, amplitude_difference=s['amplitude']-w['amplitude'],
                              values_at_6_4=values64, range_at_6_4=max(values64)-min(values64),
                              sample_sd_at_6_4=statistics.stdev(values64),
                              strong_minus_weak_curve=offsets, resolved=flags[g]['resolved'])
    receipt_path = RUN / 'stage_c_receipt_2026-09-15T053505Z.json'
    receipt = json.loads(receipt_path.read_text())
    assert receipt['identity_digest'] == identity and receipt['runtime'] == manifest['runtime']
    assert receipt['generators'] == GENS and receipt['n_jobs'] == 2 and receipt['dry_run']
    assert receipt['covered_modules_uncommitted'] == [] and receipt['not_run'] == []
    assert receipt['strength_resolution'] == flags
    for g in GENS:
        assert receipt['reach'][g]['sha256'] == reach[g]['sha256']
        for s in ('weak', 'strong'):
            assert receipt['calibration'][g+'|'+s]['sha256'] == cal[(g, s)]['sha256']
    v5 = PORT / 'results/battery/v5-7fcb46729408'
    v5_expected = {'manifest.json': '5ea038c7e7349e9cd9f8d5fcd133c960fff6bf357aa9074aee58057c245cfb2f',
                   'calibration.json': '87c96314af0f590880e447f26d103c216f579181993c0404ff00c83ea6fbeba3'}
    assert {n: sha(v5/n) for n in v5_expected} == v5_expected
    benchmark = json.loads((PORT / 'results/battery/benchmark.json').read_text())
    seconds = benchmark['generate_s'] + benchmark['pipeline_s']
    output = dict(review='v6 calibration before stage C', repository_head=subprocess.check_output(
        ['git','-C',str(ROOT),'rev-parse','HEAD'], text=True).strip(),
        identity_digest=identity, input_sha256={**hashes, 'strengths.json':sha(RUN/'strengths.json'),
        receipt_path.name:sha(receipt_path)}, source_sha256=source_hashes,
        statistics=100, generated_decoder_calls=3400, auc_entries_checked=68000,
        cells=cells, comparisons=comparisons, runtime=manifest['runtime'],
        v5_hashes_preserved=True, existing_stage_c_payloads=len(list((RUN/'recordings').glob('*.npy'))),
        timing=dict(median_decoder_seconds_per_call=statistics.median(d['seconds']['decoder']/34 for d in stats),
                    maximum_peak_rss_mb=max(d['peak_rss_mb'] for d in stats),
                    wall_outliers=[dict(generator=d['generator'], phase=d['phase'], index=d['index'],
                                        amplitude=d['amplitude'],seconds=d['seconds']) for d in stats if d['seconds']['wall']>1000],
                    benchmark_generated_pipeline_seconds=seconds, stage_c_hours_one_worker=2040*seconds/3600,
                    stage_c_ideal_hours_two_workers=2040*seconds/7200),
        limits='No decoder, generator, family fit, EEG or stage C run. Timing fields are wall measurements, including sleep.')
    path = HERE / '2026-09-15_melcon_v6_calibration_checks.json'
    path.write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()
