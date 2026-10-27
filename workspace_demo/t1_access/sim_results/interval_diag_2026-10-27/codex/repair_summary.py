"""Read-only follow-up arithmetic, external-bank rescoring, and a diagnostic figure."""
from pathlib import Path
import csv,json,hashlib,time
import numpy as np
from scipy.stats import skew
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
csv.field_size_limit(10**9)
rank=json.loads((OUT/'repair_rank.json').read_text())
a=rank['additive_null_development']['a'];b=rank['additive_null_development']['b']
out={'a':a,'b':b,'alternatives':[],'external_bank':{},'inputs':[]}
groups={}
with (ROOT/'sim_results/sens600/power_D4.csv').open() as f:
    for r in csv.DictReader(f):
        key=r['generator']+' '+r['grid']
        groups.setdefault(key,[]).append((int(r['rep']),float(np.clip(np.array(json.loads(r['delta_per_concept'])['ensemble'][0]),-.03,.03).mean())))
for name,rows in groups.items():
    t=np.array([t for _,t in sorted(rows)])
    out['alternatives'].append({'setting':name,'n':len(t),'positive_interval_calls':int(np.sum(t-a>0)),
                                 'reference':float(t.mean()),'own_reference_inclusion':float(np.mean((t-a<=t.mean())&(t.mean()<=t+b)))})

points=[];bounded=[];has_scores=None;columns=None
for path in sorted((ROOT/'sim_results/ref_m2s_omega2_aac9f69/final_2026-09-15').glob('calibration_D4.shard*of010.csv')):
    out['inputs'].append({'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    with path.open() as f:
        reader=csv.DictReader(f);columns=reader.fieldnames;has_scores='delta_per_concept' in columns
        for r in reader:
            points.append(float(r['selection_ws_point']))
            if has_scores:
                d=json.loads(r['delta_per_concept'])
                bounded.append((int(r['rep']),float(np.clip(np.array(d['ensemble'][0]),-.03,.03).mean())))
x=np.array(points)
out['external_bank']={'columns':columns,'has_concept_scores':has_scores,'n':len(x),'raw_selection_mean':float(x.mean()),
                      'raw_selection_mcse':float(x.std(ddof=1)/np.sqrt(len(x))),'raw_min':float(x.min())}
if bounded:
    t=np.array([v for _,v in sorted(bounded)])
    out['external_bank'].update(bounded_ensemble_mean=float(t.mean()),bounded_mcse=float(t.std(ddof=1)/np.sqrt(len(t))),
        bounded_skew=float(skew(t)),remove_min_mean=float(np.sort(t)[1:].mean()),
        include_own_mean=float(np.mean((t-a<=t.mean())&(t.mean()<=t+b))))
else:t=None
repro=json.loads((OUT/'reproduced.json').read_text())
orig=[q['original'] for q in repro['settings']];f1=[q['F1'] for q in repro['settings']]
names=['B','H0','H.5','H1','H2','S0','S.5','S1','S2','K0','K1','K3']
calls=[r['positive_interval_calls']/r['n'] for r in out['alternatives']]
out['figure_data']={'original_inclusion':orig,'F1_inclusion':f1,'null_assessment_inclusion':[1.]*12,
                    'null_names':names,'sensitivity_positive_fraction':calls,
                    'alternative_names':['3/L','3/M','3/H','H/L','H/M','H/H','V/L','V/M','V/H','L/L','L/M','L/H']}
(OUT/'repair_summary.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'alternatives':out['alternatives'],'external_bank':{k:v for k,v in out['external_bank'].items() if k!='columns'}},indent=2))
