from pathlib import Path
import csv, json
from collections import defaultdict
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).parent
csv.field_size_limit(10**9)
rows=defaultdict(list)
with (ROOT/'sim_results/d4v12b/calibration_D4.csv').open() as f:
    for r in csv.DictReader(f): rows[(r['generator'],r['grid'])].append(r)
extra=[]
for (name,grid),R in rows.items():
    pt,lo,hi=[np.array([float(r['selection_ws_'+x]) for r in R]) for x in ('point','lo','hi')]
    theta=pt.mean()
    need=np.where(theta>=pt,(theta-pt)/(hi-pt),(pt-theta)/(pt-lo))
    rec={'setting':name+' '+grid,'factor_to_reach_0p9_in_this_bank':float(np.sort(need)[899]),
         'points_outside_interval':int(np.sum((pt<lo)|(pt>hi)))}
    if name in ('M2H','M2S') and grid!='{}':
        # Recreate only the concept effects from original deterministic seeds.
        # simulate.dataset_seed: single-coordinate grid path and base SEED 2026.
        kw=json.loads(grid); key=list(kw)[0]; val=kw[key]
        pos={'tau':1,'omega':2}[key]
        member_index={'M2H':2,'M2S':3}[name]
        agree=[]; maxes=[]; dom=[]
        for r in R:
            seed=int(np.random.default_rng([2026,member_index,pos*round(1000*val),int(r['rep']),4]).integers(2**31))
            effect=np.random.default_rng(seed).normal(0,max(val,1e-8),size=64)
            d=np.array(json.loads(r['delta_per_concept'])['selection'][0])
            agree.append(int(np.argmax(np.abs(d))==np.argmax(effect)))
            dom.append(np.max(np.abs(d))/np.sum(np.abs(d)))
            maxes.append(effect.max())
        rec['dominant_matches_largest_drawn_effect']=float(np.mean(agree))
        if name=='M2S' and val==2:
            bottom=np.argsort(pt)[:10]
            rec['top10_dominance_median']=float(np.median(np.array(dom)[bottom]))
            rec['top10_max_effect_over_omega']=(np.array(maxes)[bottom]/val).tolist()
    extra.append(rec)
    print(rec,flush=True)
R=rows[('M2S','{"omega": 2.0}')]
lo,hi=[np.array([float(r['selection_ws_'+x]) for r in R]) for x in ('lo','hi')]
with (ROOT/'reviews/t1_omega2_bank_2026-09-15/omega2_figure_data.csv').open() as f:
    bank=np.array([float(r['point']) for r in csv.DictReader(f) if r['source']=='bank'])
bank.sort()
bs={'n':len(bank),'mean':float(bank.mean()),'mcse':float(bank.std(ddof=1)/np.sqrt(len(bank))),
    'median':float(np.median(bank)),'min':float(bank.min()),'drop1_mean':float(bank[1:].mean()),
    'drop10_mean':float(bank[10:].mean())}
bs['inclusions']={name:float(np.mean((lo<=v)&(v<=hi))) for name,v in [
    ('mean',bank.mean()),('drop1_mean',bank[1:].mean()),('median',np.median(bank))]}
print('BANK',bs)
(OUT/'additional.json').write_text(json.dumps({'settings':extra,'independent_bank':bs},indent=2)+'\n')
