"""Exercise the proposed interval core on a saved-row development subset."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import csv,json
from collections import defaultdict
import numpy as np
from repair_procedure import calibrate,apply,CAP
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
csv.field_size_limit(10**9)
nulls=defaultdict(list);alts=defaultdict(list)
for rel,groups in [('sim_results/d4v12b/calibration_D4.csv',nulls),('sim_results/sens600/power_D4.csv',alts)]:
    with (ROOT/rel).open() as f:
        for r in csv.DictReader(f):
            d=np.array(json.loads(r['delta_per_concept'])['ensemble'][0])
            groups[r['generator']+' '+r['grid']].append((int(r['rep']),float(np.clip(d,-CAP,CAP).mean())))
banks={};tests={}
for name,rows in nulls.items():
    t=np.array([v for _,v in sorted(rows)]);p=np.random.default_rng(2026102703).permutation(len(t))
    banks[name]=t[p[:700]];tests[name]=t[p[700:]]
artifact=calibrate(banks,set(banks))
out={'scope':'Development: old outer-fit ensembles without M3S; twelve graded calibration cells only. Not full-catalogue qualification.',
     'artifact':artifact,'nulls':[],'alternatives':[]}
for name,t in tests.items():
    rr=[apply(x,artifact) for x in t]
    target=np.median([v for _,v in sorted(nulls[name])]);M=artifact['cells'][name]
    out['nulls'].append({'setting':name,'n':len(t),'all_row_reference':target,
        'reference_bracket':[M['mu_lo'],M['mu_hi']],
        'point_reference_inclusion':float(np.mean([r['lo']<=target<=r['hi'] for r in rr])),
        'entire_reference_bracket_inclusion':float(np.mean([r['lo']<=M['mu_lo'] and M['mu_hi']<=r['hi'] for r in rr])),
        'mixture_calls':sum(r['decision']=='mixture' for r in rr),
        'negative_contrasts':sum(r['decision']=='negative contrast' for r in rr),
        'median_width':float(np.median([r['hi']-r['lo'] for r in rr]))})
for name,rows in alts.items():
    t=np.array([v for _,v in sorted(rows)]);rr=[apply(x,artifact) for x in t]
    out['alternatives'].append({'setting':name,'n':len(t),'positive_calls':sum(r['decision']=='mixture' for r in rr),
        'own_median_reference_inclusion':float(np.mean([r['lo']<=np.median(t)<=r['hi'] for r in rr]))})
(OUT/'repair_evidence.json').write_text(json.dumps(out,indent=2)+'\n')
ma=calibrate(banks,set(banks),target='mean')
mo={'artifact':ma,'alternatives':[]}
for name,rows in alts.items():
    rr=[apply(v,ma) for _,v in sorted(rows)]
    mo['alternatives'].append({'setting':name,'n':len(rr),'positive_calls':sum(r['decision']=='mixture' for r in rr)})
(OUT/'repair_mean_evidence.json').write_text(json.dumps(mo,indent=2)+'\n')
print('a b critical',artifact['a'],artifact['b'],artifact['graded_critical'])
for r in out['nulls']+out['alternatives']:print(r,flush=True)
