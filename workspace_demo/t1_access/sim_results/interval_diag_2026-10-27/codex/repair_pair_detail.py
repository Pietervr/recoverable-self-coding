import os,sys
for k in ('NPROC','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
sys.dont_write_bytecode=True
from pathlib import Path
import json,time
import numpy as np
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import models as M
import simulate as S
import analyze as A
start=time.process_time()
pairs=json.loads((OUT/'repair_starts.json').read_text())['pairs']
p=max(pairs,key=lambda p:p['training_gap'])
ds=S.make_dataset(p['generator'],S.generator_theta(p['generator'],**p['kwargs']),D=4,layers=(41,),seed=p['seed'])
ds.family=np.repeat(np.arange(3),[27,22,15])
test=A.stratified_folds(ds.family,5,p['seed'])[p['fold']]
train=np.setdiff1d(np.arange(64),test)
floor=float(np.std(ds.y[np.isin(ds.concept,train),0],ddof=1))
te=A._subset(ds.y[:,0],ds.k,ds.concept,test,floor)
s0=M.concept_scores('M2S',np.array(p['cold_theta']),te)
s1=M.concept_scores('M2S',np.array(p['expanded_theta']),te)
change=(s1-s0)/168
out={'seed':p['seed'],'fold':p['fold'],'training_gain':p['training_gap'],'concepts':test.tolist(),
     'expanded_minus_cold_member_heldout_per_trial':change.tolist(),
     'mean_heldout_change_per_trial':float(change.mean()),'max_change':float(change.max()),'min_change':float(change.min()),
     'cpu_seconds':time.process_time()-start}
(OUT/'repair_pair_detail.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
