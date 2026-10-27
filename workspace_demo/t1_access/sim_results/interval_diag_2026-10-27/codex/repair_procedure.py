"""Small reproducible interval/decision core. Inputs are full-pipeline simulation points.

Proposed method only. No fitting, production dispatch, or file IO in this module.
The complete frozen catalogue is necessary; performance outside it is not certified.
"""
import numpy as np
from scipy.stats import binom

CAP=.03

def point(delta, family, weights=None):
    """One concept vector after the fixed layer summary; preserve fixed-stratum weights."""
    delta=np.asarray(delta,float);family=np.asarray(family)
    if delta.ndim!=1 or delta.shape!=family.shape or delta.size==0:raise ValueError('bad concept map')
    if not np.all(np.isfinite(delta)):raise ValueError('unavailable concept score')
    strata=np.unique(family)
    if weights is None:weights=np.asarray([np.mean(family==h) for h in strata])
    if not np.isclose(np.sum(weights),1):raise ValueError('weights must sum to one')
    return float(sum(w*np.mean(np.clip(delta[family==h],-CAP,CAP)) for w,h in zip(weights,strata)))

def eb_mean(x,delta):
    """Two-sided Maurer--Pontil theorem 4, after scaling [-CAP,CAP] to [0,1]."""
    x=np.asarray(x,float);n=len(x)
    if n<2 or not np.all(np.isfinite(x)) or np.any(np.abs(x)>CAP+1e-12):raise ValueError('bad calibration bank')
    a=np.log(4/delta)
    half=np.sqrt(2*np.var(x,ddof=1)*a/n)+7*2*CAP*a/(3*(n-1))
    return max(-CAP,float(x.mean()-half)),min(CAP,float(x.mean()+half))

def upper_tolerance(x,p,delta):
    """Order-statistic upper tolerance quantile, no asymptotic normal approximation."""
    x=np.sort(np.asarray(x,float));n=len(x)
    k=next((j for j in range(1,n+1) if binom.cdf(j-1,n,p)>=1-delta),None)
    if k is None:raise ValueError('insufficient calibration rows for requested tolerance')
    return float(x[k-1]),k

def median_bracket(x,delta):
    """Exact conservative binomial CI for a distribution median (ties conservative)."""
    x=np.sort(np.asarray(x,float));n=len(x)
    j=max((j for j in range(1,n//2+1) if binom.cdf(j-1,n,.5)<=delta/2),default=0)
    return (-CAP,CAP,0,n+1) if j==0 else (float(x[j-1]),float(x[n-j]),j,n-j+1)

def calibrate(banks,graded_names,target='median'):
    """99%-confidence calibration event, conditional interval content >=96%.

    Union: target brackets fail with prob <=.005, two tolerance tails <=.005.
    On that event, every catalogue setting has interval inclusion >=.96.
    Thus unconditional inclusion >= .99*.96 = .9504, before validation.
    Structural graded critical values use the same tolerance bounds at .95.
    """
    J=len(banks)
    if J==0 or not set(graded_names).issubset(banks) or not graded_names:raise ValueError('bad catalogue')
    a=0.;b=0.;critical=0.;cells={}
    for name,raw in banks.items():
        x=np.asarray(raw,float)
        if x.ndim!=1 or len(x)<2 or not np.all(np.isfinite(x)) or np.any(np.abs(x)>CAP+1e-12):
            raise ValueError('unavailable or invalid calibration point; do not omit it')
        if target=='median':ml,mh,jl,ju=median_bracket(x,.005/J)
        elif target=='mean':ml,mh=eb_mean(x,.005/J);jl=ju=None
        else:raise ValueError('unknown target')
        qu,ku=upper_tolerance(x,.98,.005/(2*J))
        minus_ql,kl=upper_tolerance(-x,.98,.005/(2*J));ql=-minus_ql
        a=max(a,qu-ml);b=max(b,mh-ql)
        if name in graded_names:
            # Re-use the .98 tolerance quantile: conditional false call <=.02,
            # hence also <=.05. No additional calibration confidence budget.
            critical=max(critical,qu)
        cells[name]=dict(mu_lo=ml,mu_hi=mh,target_lower_rank=jl,target_upper_rank=ju,
                         accept_lo=ql,accept_hi=qu,lower_order=kl,upper_order=ku)
    return dict(target=target,a=float(a),b=float(b),graded_critical=float(critical),cells=cells,
                cap=CAP,calibration_counts={g:len(x) for g,x in banks.items()},
                interval_nominal_unconditional=.9504,calibration_good_probability=.99,
                interval_content_on_good_event=.96)

def apply(t,artifact,available=True):
    if not available or not np.isfinite(t):return dict(status='unavailable')
    if abs(t)>CAP+1e-12 or artifact.get('cap')!=CAP or not all(np.isfinite(artifact[k]) and artifact[k]>=0 for k in ('a','b','graded_critical')):
        raise ValueError('invalid point or interval artifact')
    lo=max(-CAP,t-artifact['a']);hi=min(CAP,t+artifact['b'])
    call='mixture' if lo>0 and t>artifact['graded_critical'] else ('negative contrast' if hi<0 else 'inconclusive')
    return dict(status='available',point=float(t),lo=float(lo),hi=float(hi),decision=call)
