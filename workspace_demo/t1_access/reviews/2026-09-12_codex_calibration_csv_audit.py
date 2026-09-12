"""Read existing d4v12b rows only. No repo imports, fits, or simulations."""
import csv
import hashlib
import json
import math
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

p = Path('/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/t1_access/sim_results/d4v12b/calibration_D4.csv')
csv.field_size_limit(10_000_000)
groups = defaultdict(list)
seen = Counter()
hashes = Counter()
details = {}
stat_before = p.stat()
for row in csv.DictReader(p.open(newline='')):
    key = (row['generator'], row['grid'])
    seen[(key, row['rep'], row['D'], row['n_layers'])] += 1
    hashes[row['code_hash']] += 1
    r = {'rep':int(row['rep']), 'failed':int(row['failed']), 'conv':float(row['convergence']),
         'inner_conv':float(row['inner_convergence']), 'inner_nonfinite':int(row['inner_nonfinite']),
         'selected':json.loads(row['selected']), 'fit_seconds':float(row['fit_seconds'])}
    for pred in ('selection', 'ensemble', 'historical'):
        r[pred] = {f:float(row[pred+'_ws_'+f]) for f in ('point','lo','hi','se')}
        r[pred]['decision'] = row[pred+'_decision']
    if key[0] == 'M2S' and json.loads(key[1]).get('omega') == 2:
        r['details'] = {f:json.loads(row[f]) for f in ('delta_per_concept','logq_per_concept','heldout','selected_per_layer_fold')}
    groups[key].append(r)
stat_after = p.stat()
print(json.dumps({'file':str(p), 'rows':sum(seen.values()), 'unique':len(seen), 'duplicates':sum(x-1 for x in seen.values()),
                  'hashes':hashes, 'changed_while_reading':(stat_before.st_size,stat_before.st_mtime_ns)!=(stat_after.st_size,stat_after.st_mtime_ns),
                  'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))

def q(vals, ps=(.0,.01,.1,.25,.5,.75,.9,.99,1.)):
    vals=sorted(vals)
    def one(p):
        idx=p*(len(vals)-1); lo=math.floor(idx); hi=math.ceil(idx)
        return vals[lo]+(idx-lo)*(vals[hi]-vals[lo])
    return {str(p):one(p) for p in ps}

for key, rows in sorted(groups.items()):
    selected=Counter()
    for r in rows: selected.update(r['selected'])
    print(json.dumps({'group':key,'n':len(rows),'rep_range':[min(r['rep'] for r in rows),max(r['rep'] for r in rows)],
                      'missing_rep':sorted(set(range(1000))-{r['rep'] for r in rows}),
                      'fail':sum(r['failed'] for r in rows),'inner_nonfinite':sum(r['inner_nonfinite'] for r in rows),
                      'min_conv':min(r['conv'] for r in rows),'min_inner_conv':min(r['inner_conv'] for r in rows),
                      'selected':selected}))
    for pred in ('selection','ensemble','historical'):
        rs=[r[pred] for r in rows if not r['failed']]
        points=[r['point'] for r in rs]
        n=len(rs); mean=st.mean(points); sd=st.stdev(points); mcse=sd/math.sqrt(n)
        cover=lambda truth:sum(r['lo']<=truth<=r['hi'] for r in rs)/n
        print(json.dumps({'pred':pred,'mean':mean,'SD':sd,'MCSE_mean':mcse,
                          'coverage':cover(mean), 'coverage_at_mean_pm2MCSE':[cover(mean-2*mcse),cover(mean+2*mcse)],
                          'mean_SE':st.mean(r['se'] for r in rs), 'rms_SE':math.sqrt(st.mean(r['se']**2 for r in rs)),
                          'miss_interval_above_truth':sum(r['lo']>mean for r in rs)/n,
                          'miss_interval_below_truth':sum(r['hi']<mean for r in rs)/n,
                          'decisions':Counter(r['decision'] for r in rs),
                          'one_sided_95_FPR_upper_if_zero':1-.05**(1/n)}))
    if key[0]=='M2S' and json.loads(key[1]).get('omega')==2:
        rs=sorted(rows,key=lambda r:r['selection']['point'])
        points=[r['selection']['point'] for r in rs]
        print(json.dumps({'omega2_point_quantiles':q(points),'SE_quantiles':q([r['selection']['se'] for r in rs]),
                          'mean_excluding_most_negative':[st.mean(points[m:]) for m in (1,5,10)],
                          'bottom_1_5_10_sum_fraction':[sum(points[:m])/sum(points) for m in (1,5,10)],
                          'means_by_rep_quartile':[st.mean(r['selection']['point'] for r in rows if low<=r['rep']<low+250) for low in (0,250,500,750)]}))
        for r in rs[:5]+rs[len(rs)//2:len(rs)//2+1]:
            d=r['details']; vals=d['delta_per_concept']['selection'][0]
            print(json.dumps({'extreme_rep':r['rep'],'selection':r['selection'],'ensemble':r['ensemble'],
                              'delta_quantiles':q(vals),'worst_concepts':sorted(enumerate(vals),key=lambda x:x[1])[:4],
                              'heldout':d['heldout'],'selected':r['selected'], 'per_fold':d['selected_per_layer_fold']}))
