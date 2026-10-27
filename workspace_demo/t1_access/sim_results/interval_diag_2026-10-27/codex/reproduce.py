"""Independent saved-score checks only. No model fitting or remote operations.

Run with repository .venv/bin/python. Writes only beside this file.
"""
from pathlib import Path
import csv
import hashlib
import json
import ast
from collections import Counter, defaultdict
import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'sim_results/d4v12b/calibration_D4.csv'
csv.field_size_limit(10**9)
sets = defaultdict(list)
fields = None
with SOURCE.open() as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    for r in reader:
        sets[(r['generator'], r['grid'])].append(r)

corr = np.sqrt(8/7)
report = {'input_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'fields': fields, 'settings': []}
trim_rng = np.random.default_rng(20261027)
trim_indices = (trim_rng.integers(0, 8, size=(1000,8,8)) + np.arange(8)[None,:,None]*8).reshape(1000,64)

# Execute only the resampling/fold helpers from analyze.py, avoiding all imports,
# fitting, JAX compilation, and side effects.
tree = ast.parse((ROOT/'analyze.py').read_text())
names = {'stratified_resample', 'stratified_folds', 'grouped_stratified_folds'}
helpers = ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names], type_ignores=[])
scope = {'np':np}
exec(compile(helpers, 'analyze_helpers', 'exec'), scope)
fam = np.repeat(np.arange(8),8)
draws = scope['stratified_resample'](fam, 100000, np.random.default_rng(61))
unique_per_stratum = [np.unique(row[:8]).size for row in draws]
report['resampling'] = {'mean_unique_per_stratum': float(np.mean(unique_per_stratum)),
                        'theory_unique_per_stratum': 8*(1-(7/8)**8),
                        'theory_unique_total':64*(1-(7/8)**8)}

print('setting n original F1 F1x1.2 misses_below_above skew k SE_ratio trimmed_normal trimmed_percentile median_normal')
for (name, grid), rows in sets.items():
    pt, lo, hi, se = [np.array([float(r['selection_ws_'+x]) for r in rows]) for x in ('point','lo','hi','se')]
    d = np.array([json.loads(r['delta_per_concept'])['selection'][0] for r in rows])
    theta = pt.mean()
    inc = (lo<=theta)&(theta<=hi)
    exact_var = np.sum(d.reshape(-1,8,8).var(axis=2,ddof=1),axis=1)/512
    exact_se = np.sqrt(exact_var)
    pooled_se = d.std(axis=1,ddof=1)/8
    dom = np.max(np.abs(d),axis=1)/np.sum(np.abs(d),axis=1)
    def incl(factor):
        return float(np.mean((pt+factor*(lo-pt)<=theta)&(theta<=pt+factor*(hi-pt))))
    def cov(L,H,ref):
        return float(np.mean((L<=ref)&(ref<=H)))
    G = Counter(); X = Counter(); pairs = Counter()
    for r in rows:
        selected = json.loads(r['selected'])
        G[tuple(sorted(k for k in selected if k.startswith('M2')))] += 1
        X[tuple(sorted(k for k in selected if k.startswith('M3')))] += 1
        pairs[tuple(sorted(selected.items()))] += 1
    # This exactly repeats diag_fix's seed, B and stratum order, and ALSO
    # computes a percentile interval for the changed trimmed statistic.
    robust = {}
    for stat in ('trim', 'median'):
        p=[]; L=[]; H=[]; PL=[]; PH=[]
        for a in d:
            fn = (lambda z: stats.trim_mean(z,.1,axis=-1)) if stat=='trim' else (lambda z:np.median(z,axis=-1))
            point=float(fn(a)); bs=fn(a[trim_indices]); sd=bs.std(ddof=1)*corr
            p.append(point); L.append(point-1.96*sd); H.append(point+1.96*sd)
            q=np.quantile(bs,[.025,.975]); PL.append(point+corr*(q[0]-point)); PH.append(point+corr*(q[1]-point))
        p=np.array(p); L=np.array(L); H=np.array(H)
        robust[stat]={'normal':cov(L,H,p.mean()), 'percentile':cov(np.array(PL),np.array(PH),p.mean()),
                      'k':float(p.std(ddof=1)/np.median((H-L)/3.92)), 'reference':float(p.mean())}
    k=pt.std(ddof=1)/np.median(se)
    basic_lo=2*pt-hi; basic_hi=2*pt-lo
    # A variance diagnostic, NOT an independent-components decomposition:
    # all pairwise covariance of the 64 labelled OOF scores across datasets.
    full_cov=np.cov(d,rowvar=False)
    diag_term=np.trace(full_cov)/64**2
    cross_term=(full_cov.sum()-np.trace(full_cov))/64**2
    normal_lo=pt-1.96*exact_se; normal_hi=pt+1.96*exact_se
    record={'setting':name+' '+grid,'n':len(rows),'reference':float(theta),
        'reference_mcse':float(pt.std(ddof=1)/np.sqrt(len(rows))), 'point_sd':float(pt.std(ddof=1)),
        'point_skew':float(stats.skew(pt,bias=True)), 'original':float(inc.mean()),
        'miss_reference_below':int(np.sum(theta<lo)),'miss_reference_above':int(np.sum(theta>hi)),
        'F1':incl(corr),'F1_times_1p1':incl(corr*1.1),'F1_times_1p2':incl(corr*1.2),
        'k_sd_over_median_se':float(k),'oracle_rescaled':incl(k),
        'median_claimed_se':float(np.median(se)), 'median_exact_unbiased_stratified_se':float(np.median(exact_se)),
        'median_claimed_over_exact_boot_se':float(np.median(se/(exact_se/corr))),
        'median_claimed_over_pooled_se':float(np.median(se/pooled_se)),
        'point_vs_delta_mean_max_error':float(np.max(np.abs(pt-d.mean(axis=1)))),
        'basic':cov(basic_lo,basic_hi,theta),'basic_F1':cov(pt+corr*(basic_lo-pt),pt+corr*(basic_hi-pt),theta),
        'normal_exact_stratified':cov(normal_lo,normal_hi,theta),
        'dominance_median_hits':float(np.median(dom[inc])), 'dominance_median_misses':float(np.median(dom[~inc])),
        'dominance_gt_half':int(np.sum(dom>.5)), 'selected_G':repr(G),'selected_X':repr(X),
        'covariance_diagonal_term':float(diag_term),'covariance_cross_term':float(cross_term),
        'replicate_variance':float(pt.var(ddof=1)),
        'valid_reps':len({int(r['rep']) for r in rows}), 'hashes':sorted(set(r['code_hash'] for r in rows)),
        'robust':robust,
        'max_endpoint':float(hi.max()),
        'primary_decisions':dict(Counter(r['selection_decision'] for r in rows)),
        'historical_decisions':dict(Counter(r['historical_decision'] for r in rows))}
    report['settings'].append(record)
    print(record['setting'],len(rows),f'{inc.mean():.3f}',f'{incl(corr):.3f}',f'{incl(corr*1.2):.3f}',
          record['miss_reference_below'],record['miss_reference_above'],f'{record["point_skew"]:.2f}',f'{k:.2f}',
          f'{record["median_claimed_over_exact_boot_se"]:.4f}',
          robust['trim']['normal'],robust['trim']['percentile'],robust['median']['normal'],flush=True)

(OUT/'reproduced.json').write_text(json.dumps(report,indent=2)+'\n')
print('Wrote',OUT/'reproduced.json',flush=True)
