"""Independent dense numpy quadrature for representative held-out M3S concepts."""
import os,sys
for k in ('NPROC','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
sys.dont_write_bytecode=True
from pathlib import Path
import json,time
import numpy as np
from scipy.special import expit,log_expit,logsumexp
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import models as M
import simulate as S
import analyze as A
import jax.numpy as jnp
data=json.loads((OUT/'repair_primary_local.json').read_text())
assert len(data['datasets'])==2 and all(d['complete'] for d in data['datasets'])
start=time.process_time();records=[]
family=np.repeat(np.arange(3),[27,22,15])
for d in data['datasets']:
    name=d['generator'];kw=d['kwargs'];seed=d['seed']
    if name!='M3S':ds=S.make_dataset(name,S.generator_theta(name,**kw),D=4,layers=(41,),seed=seed)
    else:
        th=S.generator_theta('M3H',tau=1.,sep=2.)
        ds=S.make_dataset('M3H',S.generator_theta('M3H',tau=0.,sep=2.),D=4,layers=(41,),seed=seed)
        rng=np.random.default_rng(seed);uc=rng.normal(0,1,64);k=ds.k
        lo,hi,la,l1=M._ordered(th,jnp.asarray(k),0.)
        state=rng.uniform(size=len(k))<np.asarray(jnp.exp(la));state[k==0]=False
        ds.y[:,0]=np.where(state,np.asarray(hi),float(lo))+np.exp(th[6]+uc[ds.concept])*rng.normal(size=len(k))
    folds=A.stratified_folds(family,3,seed)
    for fit in d['fits']:
        if fit['member']!='M3S':continue
        th=np.array(fit['theta']);w=np.exp(th[7]);us=np.linspace(-8*w,8*w,16385)
        weights=np.ones(len(us));weights[[0,-1]]=.5
        test=folds[fit['fold']];saved=np.array(fit['heldout_logq'])
        chosen=sorted(set([int(np.argmax(np.abs(saved))),len(test)//2]))
        for j in chosen:
            c=test[j];m=ds.concept==c;y=ds.y[m,0];k=ds.k[m]
            hi=th[0]+np.exp(th[1])+np.exp(th[2])*expit(th[4]*(k-th[5]))
            la=log_expit(th[3]*(k-th[5]));lm=log_expit(-th[3]*(k-th[5]))
            sig=np.exp(th[6]+us[:,None])
            low=-.5*((y[None,:]-th[0])/sig)**2-np.log(sig)-.5*np.log(2*np.pi)
            high=-.5*((y[None,:]-hi[None,:])/sig)**2-np.log(sig)-.5*np.log(2*np.pi)
            ll=np.where(k[None,:]==0,low,np.logaddexp(lm[None,:]+low,la[None,:]+high)).sum(axis=1)
            lp=ll-.5*(us/w)**2-np.log(w)-.5*np.log(2*np.pi)
            dense=float(logsumexp(lp+np.log(weights))+np.log(us[1]-us[0]))
            records.append({'generator':name,'seed':seed,'fold':fit['fold'],'concept':int(c),
                            'saved_logq':float(saved[j]),'dense_logq':dense,'difference':dense-float(saved[j])})
out={'n_points':16385,'prior_halfwidth_sd':8,'records':records,'max_absolute_joint_logq_error':max(abs(r['difference']) for r in records),
     'cpu_seconds':time.process_time()-start}
(OUT/'repair_primary_quadrature.json').write_text(json.dumps(out,indent=2)+'\n')
print('Checked',len(records),'concepts; maximum joint logq error',out['max_absolute_joint_logq_error'],'CPU',out['cpu_seconds'],flush=True)
