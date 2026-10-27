"""Round-2 development only: saved rows, no production edits or model fits.

All targets, fit dependence and decision counts refer to the saved algorithm.
The split is for internal development; these are already inspected datasets.
"""
from pathlib import Path
import csv, hashlib, json, time
from collections import defaultdict
import numpy as np
from scipy.stats import beta, binom, skew

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
csv.field_size_limit(10**9)
started = time.process_time()

def read(rel):
    path = ROOT / rel
    groups = defaultdict(list)
    with path.open() as f:
        for r in csv.DictReader(f):
            d = json.loads(r['delta_per_concept'])
            groups[r['generator']+' '+r['grid']].append((int(r['rep']), d, r))
    return groups, {'path':str(path), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

nulls, hash_null = read('sim_results/d4v12b/calibration_D4.csv')
alts, hash_alt = read('sim_results/sens600/power_D4.csv')

def stat(d, cap):
    z = np.clip(d, -cap, cap) if cap is not None else d
    # All inputs here have one layer and eight strata of size eight.
    T = z.mean(axis=1)
    s = np.sqrt(z.reshape(-1,8,8).var(axis=2,ddof=1).sum(axis=1)/512)
    return T, np.maximum(s, 1e-6)

def cp(k,n,side):
    if side=='lo': return 0. if k==0 else float(beta.ppf(.05,k,n-k+1))
    return 1. if k==n else float(beta.ppf(.95,k+1,n-k))

def tolerance_upper(z,p,delta):
    # P(F(Z_(k)) >= p) >= 1-delta; k is one-based.
    n=len(z)
    valid=[k for k in range(1,n+1) if binom.cdf(k-1,n,p)>=1-delta]
    if not valid: return float('inf'), n+1
    k=valid[0]
    return float(np.sort(z)[k-1]), k

def eb_mean(t, cap, delta):
    # Maurer--Pontil empirical Bernstein mean interval, known range 2*cap.
    n=len(t); log=np.log(4/delta)
    half=np.sqrt(2*t.var(ddof=1)*log/n)+7*(2*cap)*log/(3*(n-1))
    return float(max(-cap,t.mean()-half)),float(min(cap,t.mean()+half)),float(half)

report={'inputs':[hash_null,hash_alt], 'split_seed':2026102702,
        'split_sizes':{'reference':400,'calibration':300,'assessment':300},'candidates':[]}
cache={}
for pred in ('selection','ensemble','historical'):
    for cap in (.03,.1,.3,1.,None):
        key=f'{pred}:cap={cap}'
        rec={'key':key,'predictor':pred,'cap':cap,'nulls':[],'alternatives':[]}
        records=[]; lower_critical=[]; upper_critical=[]; lower_eb=[]; upper_eb=[]
        for name,rows in nulls.items():
            rows=sorted(rows)
            d=np.asarray([x[1][pred][0] for x in rows])
            T,s=stat(d,cap)
            perm=np.random.default_rng(2026102702).permutation(len(T))
            ir,ic,iv=perm[:400],perm[400:700],perm[700:]
            mu=float(T[ir].mean()); err=(T[ic]-mu)/s[ic]
            # Directional 97.5% error quantiles, simultaneous across twelve cells and both tails.
            qp,k=tolerance_upper(err,.975,.05/24)
            qm,km=tolerance_upper(-err,.975,.05/24)
            lower_critical.append(qm); upper_critical.append(qp)
            eb=None
            if cap is not None:
                ml,mh,hh=eb_mean(T[ir],cap,.025/12)
                qpe,_=tolerance_upper((T[ic]-ml)/s[ic],.975,.025/24)
                qme,_=tolerance_upper((mh-T[ic])/s[ic],.975,.025/24)
                upper_eb.append(qpe);lower_eb.append(qme)
                eb={'lo':ml,'hi':mh,'half':hh}
            records.append((name,T,s,iv,mu))
            fixed_lo=T-1.96*s;fixed_hi=T+1.96*s
            rec['nulls'].append({'setting':name,'reference':mu,'all_mean':float(T.mean()),
                'sd':float(T.std(ddof=1)),'skew':float(skew(T)),
                'max_concept_mean_influence': None if cap is None else 2*cap/64,
                'fixed_corrected_normal_inclusion':float(np.mean((fixed_lo<=T.mean())&(T.mean()<=fixed_hi))),
                'q_minus':qm,'q_plus':qp,'order_k':k,'reference_eb':eb})
        qm=max(lower_critical);qp=max(upper_critical)
        qme=max(lower_eb) if lower_eb else None;qpe=max(upper_eb) if upper_eb else None
        rec['critical']={'q_minus':qm,'q_plus':qp,'eb_q_minus':qme,'eb_q_plus':qpe}
        for entry,(name,T,s,iv,mu) in zip(rec['nulls'],records):
            L=T[iv]-qp*s[iv];H=T[iv]+qm*s[iv]
            K=int(np.sum((L<=mu)&(mu<=H)))
            entry.update(assessment_n=len(iv),inclusion=K/len(iv),inclusion_cp95_lo=cp(K,len(iv),'lo'),
                         mixture_calls=int(np.sum(L>0)),graded_calls=int(np.sum(H<0)),
                         median_width=float(np.median(H-L)))
            if qme is not None:
                LE=T[iv]-qpe*s[iv];HE=T[iv]+qme*s[iv]
                entry.update(eb_inclusion=float(np.mean((LE<=mu)&(mu<=HE))),
                             eb_mixture_calls=int(np.sum(LE>0)),eb_graded_calls=int(np.sum(HE<0)))
        for name,rows in alts.items():
            d=np.asarray([x[1][pred][0] for x in sorted(rows)])
            T,s=stat(d,cap);L=T-qp*s;H=T+qm*s
            entry={'setting':name,'n':len(T),'mean':float(T.mean()),
                   'mixture_calls':int(np.sum(L>0)),'graded_calls':int(np.sum(H<0)),
                   'own_bank_inclusion':float(np.mean((L<=T.mean())&(T.mean()<=H)))}
            if qme is not None:entry['eb_mixture_calls']=int(np.sum(T-qpe*s>0))
            rec['alternatives'].append(entry)
        report['candidates'].append(rec)
        print(key,'q',round(qm,3),round(qp,3),'incl',min(x['inclusion'] for x in rec['nulls']),
              'alt',sum(x['mixture_calls'] for x in rec['alternatives']),
              'EB',None if qme is None else (round(qme,3),round(qpe,3),sum(x['eb_mixture_calls'] for x in rec['alternatives'])),flush=True)
        cache[key]=records

# The external omega2 bank's compact CSV cannot be robustly rescored: no concept scores.
bank=ROOT/'reviews/t1_omega2_bank_2026-09-15/omega2_figure_data.csv'
with bank.open() as f:
    reader=csv.DictReader(f);report['external_bank_columns']=reader.fieldnames
report['external_bank_sha256']=hashlib.sha256(bank.read_bytes()).hexdigest()
report['cpu_seconds']=time.process_time()-started
(OUT/'repair_development.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print('Saved',OUT/'repair_development.json','CPU seconds',report['cpu_seconds'],flush=True)
