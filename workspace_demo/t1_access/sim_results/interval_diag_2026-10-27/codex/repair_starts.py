"""Paired M2S start comparison, bounded by the combined two-hour local CPU cap."""
import os,sys
for k in ('NPROC','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
sys.dont_write_bytecode=True
from pathlib import Path
import json,time
import numpy as np
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import models as M
import analyze as A
import simulate as S
initial=json.loads((OUT/'repair_local.json').read_text())
assert len(initial['datasets'])==3 and all(r['complete'] for r in initial['datasets'])
cap=7200-initial['cpu_seconds']-300
which=int(sys.argv[1])
dest=OUT/f'repair_starts_setting{which}.json'
start=time.process_time();out={'setting_index':which,'cap_cpu_seconds':cap,'initial_cpu_seconds':initial['cpu_seconds'],'pairs':[],'complete':False}
family=np.repeat(np.arange(3),[27,22,15])
def save():
    out['cpu_seconds']=time.process_time()-start
    dest.write_text(json.dumps(out,indent=2)+'\n')
points=[('M2H',{'tau':.5}),('M2S',{'omega':.5}),('M2S',{'omega':1.}),('M2S',{'omega':2.})]
for s,(name,kw) in enumerate(points):
    if s!=which:continue
    for rep in range(3):
        seed=271010+100*s+rep
        ds=S.make_dataset(name,S.generator_theta(name,**kw),D=4,layers=(41,),seed=seed);ds.family=family.copy()
        folds=A.stratified_folds(family,5,seed)
        for f,test in enumerate(folds):
            spent=time.process_time()-start
            for other in OUT.glob('repair_starts_setting*.json'):
                if other==dest:continue
                try:spent+=json.loads(other.read_text())['cpu_seconds']
                except (ValueError,KeyError):pass
            if spent>cap-480:
                out['stop']='combined CPU cap';save();sys.exit(0)
            train=np.setdiff1d(np.arange(64),test)
            floor=float(np.std(ds.y[np.isin(ds.concept,train),0],ddof=1))
            tr=A._subset(ds.y[:,0],ds.k,ds.concept,train,floor)
            te=A._subset(ds.y[:,0],ds.k,ds.concept,test,floor)
            tic=time.process_time()
            cold=M.fit('M2S',tr,n_starts=8,rng=np.random.default_rng([seed,f,2]))
            more=M.fit('M2S',tr,n_starts=8,rng=np.random.default_rng([seed,f,2]),
                       policy_key=(M.SIZE_OUTER,f,(seed,41)),policy={'M2S':((64,.25),)})
            sc0=M.concept_scores('M2S',cold.theta,te);sc1=M.concept_scores('M2S',more.theta,te)
            p={'generator':name,'kwargs':kw,'seed':seed,'fold':f,'n_test':len(test),
               'training_gap':float(more.loglik-cold.loglik),'cold_converged':cold.converged,
               'expanded_converged':more.converged,'cold_recovery':cold.recovery,'expanded_recovery':more.recovery,
               'max_abs_heldout_change_per_trial':float(np.max(np.abs(sc1-sc0))/168),
               'ensemble_T_change_bound_contribution':float(np.sum(np.abs(sc1-sc0))/168/64),
               'cold_cpu_wall_seconds':cold.seconds,'expanded_cpu_wall_seconds':more.seconds,
               'cpu_seconds':time.process_time()-tic,'cold_theta':cold.theta.tolist(),'expanded_theta':more.theta.tolist()}
            out['pairs'].append(p);save()
            print(name,kw,'rep',rep,'fold',f,'gap',p['training_gap'],'heldout',p['max_abs_heldout_change_per_trial'],'CPU',p['cpu_seconds'],flush=True)
out['complete']=True
byseed={}
for p in out['pairs']:byseed[p['seed']]=byseed.get(p['seed'],0)+p['ensemble_T_change_bound_contribution']
out['summary']={'n_pairs':len(out['pairs']),'max_training_gain':max(p['training_gap'] for p in out['pairs']),
    'max_abs_heldout_change_per_trial':max(p['max_abs_heldout_change_per_trial'] for p in out['pairs']),
    'max_complete_dataset_ensemble_T_change_bound':max(byseed.values()),
    'all_converged':all(p['cold_converged'] and p['expanded_converged'] for p in out['pairs'])}
q=out['summary'];out['development_accept_cold']=q['max_training_gain']<.5 and q['max_abs_heldout_change_per_trial']<.001 and q['max_complete_dataset_ensemble_T_change_bound']<.001 and q['all_converged']
save();print(out['summary'],'ACCEPT_COLD',out['development_accept_cold'],flush=True)
