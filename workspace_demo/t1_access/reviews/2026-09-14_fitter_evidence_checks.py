"""Independent stdlib audit of the delivered PC CSVs; no model imports or fitting.

Run from any directory. Output is review evidence beside this script.
The optional checkpoint archive is read when delivered; never regenerated.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics as st
import zipfile

HERE = Path(__file__).resolve().parent
PKG = HERE / 'pc_audit_2026-09-14'
G = ('M2B', 'M2H', 'M2S', 'M2K')
X = ('M3', 'M3H', 'M3V', 'M3L')
KEY = ('generator', 'grid', 'rep', 'size', 'member')
RECIPES = ('cold only', '+8 @0.25', '+8 @0.25 (seed B)', '+8 @0.50', '+8 mixed',
           '+16 @0.25', '+16 @0.25 (seed B)', '+16 @0.50', '+16 mixed', '+32 @0.25', '+64 @0.25')


def read_csv(path):
    with path.open(newline='') as f:
        rows = list(csv.DictReader(f))
    text_columns = set(KEY) | {'recipe', 'pipeline_source', 'strong_source', 'strong_batch',
                              'pipeline_theta', 'strong_theta'}
    for row in rows:
        row['rep'] = int(row['rep'])
        for k in row.keys() - text_columns:
            if row[k] != '':
                row[k] = float(row[k])
    return rows


def key(row):
    return tuple(row[k] for k in KEY)


def group(rows, fields):
    out = defaultdict(list)
    for r in rows:
        out[tuple(r[f] for f in fields)].append(r)
    return out


def stats(rows, heldout='heldout_change'):
    gap = [r['gap'] for r in rows if math.isfinite(r['gap'])]
    h = [r[heldout] for r in rows if math.isfinite(r[heldout])]
    return dict(n=len(rows), misses=int(sum(r['miss'] for r in rows)),
                miss_rate=st.mean(r['miss'] for r in rows),
                nonfinite_gap=len(rows)-len(gap), nonfinite_heldout=len(rows)-len(h),
                mean_gap=st.mean(gap), max_gap=max(gap), mean_heldout=st.mean(h),
                min_heldout=min(h), max_heldout=max(h),
                worse_than_reference_by_001=sum(v > .001 for v in h),
                better_than_reference_by_001=sum(v < -.001 for v in h))


def proxy(rows, score):
    families = [max(r[score] for r in rows if r['member'] in fam) for fam in (G, X)]
    return (families[1]-families[0])/rows[0]['n_heldout_trials']


def sign(v):
    return (v > 0) - (v < 0)


def paired(rows, first, second):
    pairs = group([r for r in rows if r['recipe'] in (first, second)], KEY)
    transitions = Counter()
    differences = []
    for rs in pairs.values():
        lookup = {r['recipe']: r for r in rs}
        a, b = lookup[first], lookup[second]
        transitions[f"{int(a['miss'])}->{int(b['miss'])}"] += 1
        differences.append(b['heldout_change']-a['heldout_change'])
    return dict(first=first, second=second, n=len(pairs), miss_transitions=dict(transitions),
                second_minus_first_mean_heldout_loss=st.mean(differences))


def git_blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def main():
    result = {}
    hashes = {}
    for line in (PKG/'SHA256SUMS').read_text().splitlines():
        expected, relative = line.split(maxsplit=1)
        relative = relative.lstrip('*')
        raw = (PKG/relative).read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        assert actual == expected, relative
        hashes[relative] = dict(sha256=actual, git_blob=git_blob(raw), bytes=len(raw))
    result['files'] = hashes
    raw = (PKG/'audit_fits.py').read_bytes()
    start = raw.index(b'    # ---- the two batches are not the same size')
    end = raw.index(b'    # --------------------------------------------- is there a cheap data-side trigger?')
    reconstructed = raw[:start] + raw[end:]
    result['producer_reconstruction'] = dict(
        removed_lines=raw[start:end].count(b'\n'), git_blob=git_blob(reconstructed),
        expected_blob='025f4ec859cef9f83ace65d7033cf4cbfe0f2e21')
    assert git_blob(reconstructed) == '025f4ec859cef9f83ace65d7033cf4cbfe0f2e21'

    audit = read_csv(PKG/'results/audit_fits.csv')
    prefix = read_csv(PKG/'results/prefix_scoring.csv')
    assert len(audit) == len({key(r) for r in audit}) == 1536
    assert len(prefix) == len({key(r)+(r['recipe'],) for r in prefix}) == 12320
    amap = {key(r): r for r in audit}
    for r in audit:
        r['heldout_change'] = (r['strong_heldout']-r['pipeline_heldout'])/r['n_heldout_trials']
        assert math.isclose(r['gap'], r['strong_loglik']-r['pipeline_loglik'], abs_tol=1e-8)
        assert r['miss'] == int(r['gap'] > .5)
        assert r['n_starts_pipeline'] == (8 if r['size'] == 'outer' else 4)
        assert r['n_starts_strong'] == r['n_starts_pipeline']+80
    result['audit'] = stats(audit)
    result['audit']['units'] = len(group(audit, KEY[:3]))
    result['audit']['pipeline_nonconverged'] = sum(not r['pipeline_converged'] for r in audit)
    result['audit']['strong_no_converged_start'] = sum(not r['strong_n_converged'] for r in audit)
    result['audit']['rows_without_archived_count'] = sum(r['n_archived'] == '' for r in audit)
    result['audit_by_member_size'] = {f'{m}/{s}': stats(rs) for (m,s),rs in group(audit, ('member','size')).items()}
    effects = []
    for u, rs in group([r for r in audit if r['size'] == 'outer'], KEY[:3]).items():
        dp, ds = proxy(rs, 'pipeline_heldout'), proxy(rs, 'strong_heldout')
        effects.append(dict(unit=u, pipeline=dp, strong=ds, diff=ds-dp))
    result['audit_proxy'] = dict(units=len(effects), flips=sum(sign(r['pipeline']) != sign(r['strong']) for r in effects),
        changes_gt_001=sum(abs(r['diff']) > .001 for r in effects),
        mean_abs_change=st.mean(abs(r['diff']) for r in effects), max_abs_change=max(abs(r['diff']) for r in effects),
        by_setting={str(u):dict(mean_pipeline=st.mean(r['pipeline'] for r in effects if r['unit'][:2] == u),
             mean_strong=st.mean(r['strong'] for r in effects if r['unit'][:2] == u),
             mean_diff=st.mean(r['diff'] for r in effects if r['unit'][:2] == u))
             for u in sorted({r['unit'][:2] for r in effects})})

    rounding = []
    for r in prefix:
        a = amap[key(r)]
        assert math.isclose(r['gap'], r['ref_loglik']-r['prefix_loglik'], abs_tol=1e-8)
        assert r['miss'] == int(r['gap'] > .5)
        assert r['n_cold'] == a['n_starts_pipeline']
        assert r['n_archived'] == a['n_starts_strong']
        assert r['ref_loglik'] == round(a['strong_loglik'], 6)
        assert math.isclose(r['heldout_change'], (r['ref_heldout']-r['heldout'])/r['n_heldout_trials'], abs_tol=1e-12)
        if r['recipe'] == 'cold only':
            assert r['prefix_loglik'] == round(a['pipeline_loglik'], 6)
            rounding.append(dict(unit=key(r),
                cold=(r['heldout']-a['pipeline_heldout'])/r['n_heldout_trials'],
                reference=(r['ref_heldout']-a['strong_heldout'])/r['n_heldout_trials']))
    result['rounded_theta_comparison'] = dict(
        max_abs_cold=max(rounding, key=lambda r: abs(r['cold'])),
        max_abs_reference=max(rounding, key=lambda r: abs(r['reference'])))
    bal = [r for r in prefix if r['rep'] in (2,3,4,5)]
    assert len(group(bal, KEY[:3])) == 64
    assert all(len(v) == 4 for v in group([r for r in bal if r['recipe'] == 'cold only'], ('generator','grid','size','member')).values())
    result['prefix'] = dict(rows=len(prefix), units=len(group(prefix, KEY[:3])), balanced_units=64,
        recipes=list(RECIPES), nonfinite_gaps=sum(not math.isfinite(r['gap']) for r in prefix))
    result['balanced_pooled'] = {rec:stats([r for r in bal if r['recipe'] == rec and r['member'] != 'M2K']) for rec in RECIPES}
    result['balanced_member_size'] = {f'{m}/{size}/{rec}':stats(rs)
        for (m,size,rec),rs in group(bal, ('member','size','recipe')).items()}
    result['balanced_member_setting'] = {f'{m}/{size}/{gen}/{grid}/{rec}':stats(rs)
        for (m,size,gen,grid,rec),rs in group(bal, ('member','size','generator','grid','recipe')).items()
        if m in ('M3H','M2H') and rec in ('+16 @0.50','+64 @0.25')}
    result['paired'] = {f'{m}/{s}':paired([r for r in bal if r['member'] == m and r['size'] == s], '+16 @0.50', '+64 @0.25')
        for m in G+X for s in ('outer','inner')}
    result['M3H_seed_control'] = {s:paired([r for r in bal if r['member'] == 'M3H' and r['size'] == s],
        '+16 @0.25', '+16 @0.25 (seed B)') for s in ('outer','inner')}
    result['prefix_proxy_flips'] = {}
    for rec in RECIPES:
        flips = 0
        for _, rs in group([r for r in bal if r['recipe'] == rec and r['size'] == 'outer'], KEY[:3]).items():
            flips += sign(proxy(rs, 'heldout')) != sign(proxy(rs, 'ref_heldout'))
        result['prefix_proxy_flips'][rec] = flips

    timing = {}
    for label, rows in (('full_96',audit), ('archived_70',[r for r in audit if r['rep'] >= 2 or (key(r) in {key(p) for p in prefix})]),
                        ('balanced_64',[r for r in audit if r['rep'] >= 2])):
        tab = {}
        for (m,size), rs in group(rows, ('member','size')).items():
            cold = st.mean(r['seconds_pipeline'] for r in rs)
            per = st.mean(r['seconds_strong'] for r in rs)/80
            added = 16 if m == 'M3H' else 64 if m == 'M2H' else 80
            tab[f'{m}/{size}'] = dict(n=len(rs), cold_seconds=cold, added_seconds_per_start=per,
                candidate_seconds=cold+added*per, uniform64_seconds=cold+64*per)
        pair = [tab[f'{m}/outer'] for m in ('M3H','M2H')]
        cold = sum(r['cold_seconds'] for r in pair)
        proposed = sum(r['candidate_seconds'] for r in pair)
        timing[label] = dict(table=tab, outer_pair=dict(cold=cold, candidate=proposed,
            ratio=proposed/cold, uniform64=sum(r['uniform64_seconds'] for r in pair)),
            outer_all=dict(cold=sum(tab[f'{m}/outer']['cold_seconds'] for m in G+X),
                candidate=sum(tab[f'{m}/outer']['candidate_seconds'] for m in G+X)),
            nested_one_layer={col:5*sum(4*tab[f'{m}/inner'][col]+tab[f'{m}/outer'][col] for m in G+X)
                              for col in ('cold_seconds','candidate_seconds','uniform64_seconds')})
    result['timing_extrapolations_not_new_benchmarks'] = timing
    archive_root = PKG/'archive'
    for line in (archive_root/'SHA256SUMS').read_text().splitlines():
        expected, relative = line.split(maxsplit=1)
        assert hashlib.sha256((archive_root/relative.lstrip('*')).read_bytes()).hexdigest() == expected
    expected_members = {line.split(maxsplit=1)[1].lstrip('*').removeprefix('./'):line.split()[0]
                        for line in (archive_root/'SHA256SUMS_members.txt').read_text().splitlines()}
    pmap = {key(r)+(r['recipe'],):r for r in prefix}
    archives = starts = scored = 0
    coverage = Counter()
    failures = Counter()
    theta_selection_differences = Counter()

    def choose(runs):
        finite = [x for x in runs if x['loglik'] is not None and math.isfinite(x['loglik'])]
        converged = [x for x in finite if x['converged']]
        return max(converged or finite, key=lambda x:x['loglik'])

    with zipfile.ZipFile(archive_root/'audit_fits_checkpoint.zip') as z:
        assert len(z.namelist()) == len(expected_members) == 96
        for name in z.namelist():
            raw_unit = z.read(name)
            assert hashlib.sha256(raw_unit).hexdigest() == expected_members[Path(name).name]
            unit = json.loads(raw_unit)
            assert len(unit) == 16
            coverage[f"rep{unit[0]['rep']}/{'archive' if unit[0].get('starts_archive') else 'no_archive'}"] += 1
            for row in unit:
                arch = row.get('starts_archive')
                if not arch:
                    continue
                archives += 1
                starts += len(arch)
                batches = {b:sorted([x for x in arch if x['batch'] == b], key=lambda x:x['i'])
                           for b in ('cold','extra','challenge')}
                cold, extra, wide = (batches[b] for b in ('cold','extra','challenge'))
                assert (len(cold),len(extra),len(wide)) == (8 if row['size']=='outer' else 4,64,16)
                assert all([x['i'] for x in b] == list(range(len(b))) for b in batches.values())
                for x in arch:
                    failures['nonfinite_start'] += x['loglik'] is None
                    failures['nonconverged_start'] += not x['converged']
                reference = choose(arch)
                if reference['theta'] != row['strong_theta']:
                    theta_selection_differences['reference'] += 1
                if choose(cold)['theta'] != row['pipeline_theta']:
                    theta_selection_differences['cold'] += 1
                if row['member'] == 'M2K':
                    assert [x['x0'][-2:] for x in wide[:4]] == [[2.,2.],[2.,-2.],[-2.,2.],[-2.,-2.]]
                for rec in RECIPES:
                    if rec == 'cold only':
                        chosen = cold
                    else:
                        count = int(rec.split()[0][1:])
                        more = (extra[16:16+count] if 'seed B' in rec else
                                extra[:count//2]+wide[:count//2] if 'mixed' in rec else
                                wide[:count] if '@0.50' in rec else extra[:count])
                        chosen = cold+more
                    best = choose(chosen)
                    p = pmap[key(row)+(rec,)]
                    assert p['n_starts'] == len(chosen)
                    assert p['prefix_loglik'] == best['loglik']
                    assert p['ref_loglik'] == reference['loglik']
                    assert p['miss'] == int(reference['loglik']-best['loglik'] > .5)
                    scored += 1
    assert archives == 1120 and starts == 96320 and scored == 12320
    result['archive_selection_reproduction'] = dict(member_files_verified=96, coverage=dict(coverage),
        member_fits=archives, starts=starts, prefixes_reproduced=scored, start_failures=dict(failures),
        rounded_tie_theta_differences=dict(theta_selection_differences),
        heldout_evaluation_reexecuted=False)
    path = HERE/'2026-09-14_fitter_evidence_checks.json'
    path.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('producer_reconstruction','archive_selection_reproduction','rounded_theta_comparison')},indent=2))
    for label, t in timing.items():
        print(label, json.dumps({k:v for k,v in t.items() if k != 'table'}))
    print('Evidence saved:', path)


if __name__ == '__main__':
    main()
