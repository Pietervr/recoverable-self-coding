"""Scratch prototype; production models and pipeline are never modified on disk."""
import os
for k in ('NPROC','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[k]='1'
from pathlib import Path
import sys, time, json, hashlib
sys.dont_write_bytecode=True
import numpy as np
from scipy.special import logsumexp

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import models as M
import analyze as A
import simulate as S
import jax.numpy as jnp

def ll_m3s(theta,y,k,u,floor):
    low,high,logA,log1mA=M._ordered(theta,k,0.)
    sigma=jnp.exp(theta[6]+u)
    lnlo=M._log_norm(y,low,sigma)
    mix=jnp.logaddexp(log1mA+lnlo,logA+M._log_norm(y,high,sigma))
    return jnp.where(k==M.K_CATCH,lnlo,mix)

M.MEMBERS['M3S']=M.Member('M3S','X',('mu_low','d0','d1','kA','kh','x0','s','w'),ll_m3s,re_index=7,mixture=True)
old_start=M.start_from_moments
def start(name,mom):
    if name=='M3S':
        th=old_start('M3H',mom);th[7]=np.log(.3);return th
    return old_start(name,mom)
M.start_from_moments=start

family=np.repeat(np.arange(3),[27,22,15])
G=M.FAMILY_G;X=M.FAMILY_X+('M3S',)
begin_cpu=time.process_time();begin_wall=time.monotonic()
res={'plan':str(OUT/'repair_local_plan.json'),'source_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ('models.py','analyze.py','simulate.py')},
     'prototype_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'datasets':[]}

def checkpoint():
    res.update(cpu_seconds=time.process_time()-begin_cpu,wall_seconds=time.monotonic()-begin_wall)
    (OUT/'repair_local.json').write_text(json.dumps(res,indent=2,allow_nan=False)+'\n')

for name,kwargs,seed in [('M2H',{'tau':.5},271001),('M2S',{'omega':1.},271002),('M3S',{'omega':1.,'sep':2.},271003)]:
    if time.process_time()-begin_cpu>6500:break
    if name!='M3S':
        th=S.generator_theta(name,**kwargs)
        ds=S.make_dataset(name,th,D=4,layers=(41,),seed=seed)
    else:
        th=S.generator_theta('M3H',tau=1.,sep=2.)
        base=S.make_dataset('M3H',S.generator_theta('M3H',tau=0.,sep=2.),D=4,layers=(41,),seed=seed)
        rng=np.random.default_rng(seed);u=rng.normal(0,1,64)
        k=base.k;lo,hi,la,l1=M._ordered(th,jnp.asarray(k),0.)
        state=rng.uniform(size=len(k))<np.asarray(jnp.exp(la));state[k==0]=False
        mu=np.where(state,np.asarray(hi),float(lo));sigma=np.exp(th[6]+u[base.concept])
        base.y[:,0]=mu+sigma*rng.normal(size=len(k));ds=base
    ds.family=family.copy()
    folds=A.stratified_folds(family,5,seed)
    scores={m:np.full(64,np.nan) for m in G+X}
    item={'generator':name,'kwargs':kwargs,'seed':seed,'family_counts':[27,22,15],'fits':[],'complete':False}
    res['datasets'].append(item);t0=time.process_time()
    for f,test_c in enumerate(folds):
        train_c=np.setdiff1d(np.arange(64),test_c)
        floor=float(np.std(ds.y[np.isin(ds.concept,train_c),0],ddof=1))
        tr=A._subset(ds.y[:,0],ds.k,ds.concept,train_c,floor)
        te=A._subset(ds.y[:,0],ds.k,ds.concept,test_c,floor)
        for j,m in enumerate(G+X):
            if time.process_time()-begin_cpu>6960:
                item['stop']='CPU budget';checkpoint();sys.exit(0)
            tic=time.process_time()
            fit=M.fit(m,tr,n_starts=8,rng=np.random.default_rng([seed,f,j]))
            sc=M.concept_scores(m,fit.theta,te)
            scores[m][test_c]=sc
            item['fits'].append({'fold':f,'member':m,'cpu_seconds':time.process_time()-tic,
                                 'fit_wall_seconds':fit.seconds,'converged':fit.converged,
                                 'n_starts':fit.n_starts,'loglik':fit.loglik,
                                 'theta':fit.theta.tolist(),'heldout_logq':sc.tolist()})
            print(name,'fold',f,m,'cpu',round(item['fits'][-1]['cpu_seconds'],2),flush=True)
            checkpoint()
    n=168
    gg=logsumexp(np.stack([scores[m] for m in G]),axis=0)-np.log(len(G))
    for label,xx in [('old',M.FAMILY_X),('with_m3s',X)]:
        xs=logsumexp(np.stack([scores[m] for m in xx]),axis=0)-np.log(len(xx))
        delta=(xs-gg)/n
        item[label]={'raw_point':float(delta.mean()),'bounded_point_cap03':float(np.clip(delta,-.03,.03).mean()),
                     'min_delta':float(delta.min()),'max_delta':float(delta.max()),'delta':delta.tolist()}
    item['complete']=True;item['cpu_seconds']=time.process_time()-t0
    checkpoint()
    print('COMPLETE',name,item['cpu_seconds'],item['old']['raw_point'],item['with_m3s']['raw_point'],flush=True)
checkpoint()
