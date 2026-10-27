"""Direct Monte Carlo decision and interval inversion; development catalogue only."""
from pathlib import Path
import csv,json,hashlib,time
from collections import defaultdict
import numpy as np
from scipy.stats import beta,binom
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
csv.field_size_limit(10**9)
begin=time.process_time();cap=.03
groups=defaultdict(list);hashes={}
for source,rel in [('null','sim_results/d4v12b/calibration_D4.csv'),('alt','sim_results/sens600/power_D4.csv')]:
    path=ROOT/rel;hashes[rel]=hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open() as f:
        for row in csv.DictReader(f):
            d=np.asarray(json.loads(row['delta_per_concept'])['ensemble'][0])
            groups[(source,row['generator']+' '+row['grid'])].append((int(row['rep']),float(np.clip(d,-cap,cap).mean()),row))

def eb(x,delta):
    n=len(x);a=np.log(4/delta)
    h=np.sqrt(2*x.var(ddof=1)*a/n)+7*2*cap*a/(3*(n-1))
    return max(-cap,float(x.mean()-h)),min(cap,float(x.mean()+h)),float(h)

def order_bounds(x,alpha):
    n=len(x);x=np.sort(x)
    kl=int(np.floor((n+1)*alpha/2));ku=int(np.ceil((n+1)*(1-alpha/2)))
    return (float(x[kl-1]) if kl>=1 else -float('inf'),float(x[ku-1]) if ku<=n else float('inf'),kl,ku)

catalog=[];assess=[];ncat=len(groups)
for (source,name),rows in groups.items():
    rows=sorted(rows);T=np.asarray([x[1] for x in rows])
    perm=np.random.default_rng(2026102703).permutation(len(T))
    ncal=700 if source=='null' else 40
    cal=T[perm[:ncal]];test=T[perm[ncal:]]
    lo,hi,kl,ku=order_bounds(cal,.04)
    # total interval noncoverage <= .04 (rank acceptance) + .01 (all mean brackets).
    ml,mh,eh=eb(cal,.01/ncat)
    catalog.append({'source':source,'setting':name,'cal':cal,'lo':lo,'hi':hi,'kl':kl,'ku':ku,'mu_lo':ml,'mu_hi':mh})
    assess.append((source,name,test,float(T.mean())))

alpha=.05;critical=[]
for c in catalog:
    if c['source']=='null':
        x=np.sort(c['cal']);n=len(x);k=int(np.ceil((n+1)*(1-alpha)))
        threshold=float(x[k-1]) if k<=n else float('inf')
        # Conservative 95%-confidence conditional type-I tolerance bound per null.
        kval=[j for j in range(1,n+1) if binom.cdf(j-1,n,.95)>=1-.05/12]
        tolerance=float(x[kval[0]-1]) if kval else float('inf')
        critical.append({'setting':c['setting'],'rank_k':k,'threshold':threshold,'conditional_tolerance_threshold':tolerance})
cutoff=max(0.,max(c['threshold'] for c in critical))
cutoff_tol=max(0.,max(c['conditional_tolerance_threshold'] for c in critical))
out={'cap':cap,'input_sha256':hashes,'seed':2026102703,'catalogue_size':ncat,
     'null_calibration_n':700,'alt_calibration_n':40,'alpha_rank_interval':.04,'mean_bracket_failure_budget':.01,
     'critical_by_null':critical,'mixture_cutoff':cutoff,'tolerance_mixture_cutoff':cutoff_tol,'settings':[]}
for source,name,T,ref in assess:
    # Hull inversion of the full catalogue, with an explicit empty-set diagnostic.
    L=[];H=[];empty=0;accepted_n=[]
    for t in T:
        kept=[c for c in catalog if c['lo']<=t<=c['hi']]
        accepted_n.append(len(kept))
        if not kept:
            empty+=1;L.append(-cap);H.append(cap)
        else:
            L.append(min(c['mu_lo'] for c in kept));H.append(max(c['mu_hi'] for c in kept))
    L=np.asarray(L);H=np.asarray(H);K=int(np.sum((L<=ref)&(ref<=H)))
    out['settings'].append({'source':source,'setting':name,'n':len(T),'reference_all_rows':ref,
         'interval_inclusion':K/len(T),'interval_cp95_lo':0. if K==0 else float(beta.ppf(.05,K,len(T)-K+1)),
         'empty_catalogue':empty,'median_interval_width':float(np.median(H-L)),
         'mixture_calls':int(np.sum(T>cutoff)),'tolerance_mixture_calls':int(np.sum(T>cutoff_tol)),
         'all_alternative_mixture_calls':int(np.sum(np.asarray([r[1] for r in sorted(groups[(source,name)])])>cutoff)) if source=='alt' else None})
out['catalogue']=[{k:v for k,v in c.items() if k!='cal'} for c in catalog]
nc=[c for c in catalog if c['source']=='null']
# A useful additive interval, calibrated ONLY on graded rows in this development screen.
# With fresh full-catalogue calibration the same construction includes alternatives.
a=max(c['hi']-c['mu_lo'] for c in nc)
b=max(c['mu_hi']-c['lo'] for c in nc)
out['additive_null_development']={'a':a,'b':b,'settings':[]}
for source,name,T,ref in assess:
    L=np.maximum(-cap,T-a);H=np.minimum(cap,T+b)
    out['additive_null_development']['settings'].append({'source':source,'setting':name,'n':len(T),
        'inclusion':float(np.mean((L<=ref)&(ref<=H))),
        'positive_interval_and_test':int(np.sum((L>0)&(T>cutoff))),
        'negative_intervals':int(np.sum(H<0)),'median_width':float(np.median(H-L))})
out['cpu_seconds']=time.process_time()-begin
# Infinity in small alternative acceptance ranges is represented explicitly, never hidden.
def finite(z):
    if isinstance(z,dict):return {k:finite(v) for k,v in z.items()}
    if isinstance(z,list):return [finite(v) for v in z]
    if isinstance(z,float) and not np.isfinite(z):return str(z)
    return z
(OUT/'repair_rank.json').write_text(json.dumps(finite(out),indent=2)+'\n')
print('cutoffs',cutoff,cutoff_tol,'catalogue',ncat,flush=True)
for r in out['settings']:print(r['source'],r['setting'],'n',r['n'],'inclusion',r['interval_inclusion'],'empty',r['empty_catalogue'],'calls',r['mixture_calls'],flush=True)
print('alternative calls all',sum(r['all_alternative_mixture_calls'] or 0 for r in out['settings']),'CPU',out['cpu_seconds'],flush=True)
print('additive',a,b,flush=True)
for r in out['additive_null_development']['settings']:print('ADDITIVE',r,flush=True)
