"""Aggregate local development results and source identities, without production writes."""
from pathlib import Path
import json,hashlib,subprocess,sys,importlib.metadata
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
d=json.loads((OUT/'repair_local.json').read_text())
out={'cpu_seconds':d['cpu_seconds'],'wall_seconds':d['wall_seconds'],'datasets':[]}
out['runtime']={'python':sys.version,**{p:importlib.metadata.version(p) for p in ('jax','numpy','scipy')}}
for r in d['datasets']:
    x={'generator':r['generator'],'complete':r['complete'],'n_fits':len(r['fits']),
       'n_converged':sum(f['converged'] for f in r['fits'])}
    if r['complete']:
        x.update(cpu_seconds=r['cpu_seconds'],old_raw=r['old']['raw_point'],new_raw=r['with_m3s']['raw_point'],
            old_bounded=r['old']['bounded_point_cap03'],new_bounded=r['with_m3s']['bounded_point_cap03'])
    out['datasets'].append(x)
workers=[]
for path in sorted(OUT.glob('repair_starts_setting*.json')):
    workers.append(json.loads(path.read_text()))
if len(workers)==4:
    pairs=[p for w in workers for p in w['pairs']]
    byseed={};folds_byseed={}
    for p in pairs:
        byseed[p['seed']]=byseed.get(p['seed'],0)+p['ensemble_T_change_bound_contribution']
        folds_byseed.setdefault(p['seed'],set()).add(p['fold'])
    sm={'n_pairs':len(pairs),'max_training_gain':max(p['training_gap'] for p in pairs),
        'max_abs_heldout_change_per_trial':max(p['max_abs_heldout_change_per_trial'] for p in pairs),
        'max_complete_dataset_ensemble_T_change_bound':max(v for g,v in byseed.items() if len(folds_byseed[g])==5),
        'max_observed_fold_sum_T_change_bound':max(byseed.values()),
        'all_converged':all(p['cold_converged'] and p['expanded_converged'] for p in pairs),
        'cpu_seconds':sum(w['cpu_seconds'] for w in workers),'complete':all(w['complete'] for w in workers)}
    sm['development_accept_cold']=sm['complete'] and sm['max_training_gain']<.5 and sm['max_abs_heldout_change_per_trial']<.001 and sm['max_complete_dataset_ensemble_T_change_bound']<.001 and sm['all_converged']
    out['paired_starts']=sm
    (OUT/'repair_starts.json').write_text(json.dumps({'summary':sm,'pairs':pairs},indent=2)+'\n')
quad=OUT/'repair_quadrature.json'
if quad.exists():out['quadrature']=json.loads(quad.read_text())
primary=OUT/'repair_primary_local.json'
if primary.exists():
    pp=json.loads(primary.read_text())
    selected={k:pp[k] for k in ('budget_cpu_seconds','cpu_seconds','wall_seconds','prototype_sha256')}
    selected['datasets']=[]
    for r in pp['datasets']:
        v={'generator':r['generator'],'seed':r['seed'],'complete':r['complete'],'n_fits':len(r['fits']),
           'n_converged':sum(x['converged'] for x in r['fits']),
           'M2S_start_counts':[x['n_starts'] for x in r['fits'] if x['member']=='M2S']}
        if r['complete']:v.update(cpu_seconds=r['cpu_seconds'],old_raw=r['old']['raw_point'],new_raw=r['with_m3s']['raw_point'],old_bounded=r['old']['bounded_point_cap03'],new_bounded=r['with_m3s']['bounded_point_cap03'])
        selected['datasets'].append(v)
    out['selected_primary']=selected
    if 'paired_starts' in out:
        out['combined_measured_local_cpu_seconds']=d['cpu_seconds']+out['paired_starts']['cpu_seconds']+pp['cpu_seconds']
        out['combined_cpu_with_interruption_and_check_allowance']=out['combined_measured_local_cpu_seconds']+450
pq=OUT/'repair_primary_quadrature.json'
if pq.exists():out['selected_primary_quadrature']=json.loads(pq.read_text())
out['git_heads']={str(p):subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip() for p in (ROOT.parents[1],Path('/Users/pietervanrooyen/Unimog-Projects'))}
files=[ROOT/'models.py',ROOT/'analyze.py',ROOT/'simulate.py',ROOT/'PREREGISTRATION_T1_model.md',
       ROOT/'sim_results/d4v12b/calibration_D4.csv',ROOT/'sim_results/sens600/power_D4.csv']
paper=Path('/Users/pietervanrooyen/Unimog-Projects/papers/adaptive_agency_special_issue')
files += [paper/'si_submission.tex',paper/'si_supplementary.tex']+sorted((paper/'sections').glob('*.tex'))
out['source_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
out['model_sources_unchanged_since_local_import']=all(out['source_sha256'][str(ROOT/f)]==h for f,h in d['source_sha256'].items())
# Save an exact copy of the prototype as it was read at launch; the sole subsequent
# change was disabling future bytecode-cache writes, which does not affect fits.
src=(OUT/'repair_local.py').read_text().replace('sys.dont_write_bytecode=True\n','',1)
out['as_run_source_reconstructed_matches']=hashlib.sha256(src.encode()).hexdigest()==d['prototype_sha256']
if out['as_run_source_reconstructed_matches']:(OUT/'repair_local_as_run.py').write_text(src)
(OUT/'repair_finish.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('source_sha256','quadrature')},indent=2))
