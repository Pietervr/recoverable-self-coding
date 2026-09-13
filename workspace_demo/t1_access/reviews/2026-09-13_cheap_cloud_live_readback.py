"""Read only: inspect the two already authorized R052 development runs."""
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path

import boto3

RUNS = ('refit_control_aac9f69', 'ref_m2s_omega2_aac9f69')
ROOT = Path(__file__).resolve().parents[1]
BUCKET = 'xtenure-cself-pvr'
sess = boto3.Session(profile_name='xtenure-read', region_name='eu-north-1')
sm, s3, logs = (sess.client(s) for s in ('sagemaker', 's3', 'logs'))

def job_read(j):
    name = j['TrainingJobName']
    d = sm.describe_training_job(TrainingJobName=name)
    env = d.get('Environment', {})
    if not any(env.get('RESULTS_URI', '').rstrip('/').endswith('/' + r) for r in RUNS):
        return None
    keep = ('TASK', 'N_REP', 'D', 'LAYERS', 'SEED', 'GENERATORS', 'POINTS', 'N_JOBS',
            'N_STARTS_INNER', 'INTERVAL', 'N_BOOT_REFIT', 'SHARD', 'N_SHARDS', 'RESULTS_URI',
            'NPROC', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS')
    out = dict(job=name, status=d['TrainingJobStatus'], secondary=d.get('SecondaryStatus'),
               created=d['CreationTime'], training_start=d.get('TrainingStartTime'),
               training_seconds=d.get('TrainingTimeInSeconds'), billable_seconds=d.get('BillableTimeInSeconds'),
               resource=d['ResourceConfig'], stopping=d['StoppingCondition'],
               spot=d.get('EnableManagedSpotTraining'), environment={k:env[k] for k in keep if k in env},
               checkpoints=d.get('CheckpointConfig'), failure=d.get('FailureReason'), logs=[])
    try:
        streams = logs.describe_log_streams(logGroupName='/aws/sagemaker/TrainingJobs',
                    logStreamNamePrefix=name, limit=50)['logStreams']
        for st in streams:
            ev = logs.get_log_events(logGroupName='/aws/sagemaker/TrainingJobs',
                  logStreamName=st['logStreamName'], startFromHead=True, limit=200)['events']
            out['logs'].extend(dict(timestamp=e['timestamp'], message=e['message']) for e in ev
                if any(t in e['message'] for t in ('t1_job', 'replicates to run', 'done,', 'Traceback', 'Error')))
    except Exception as e:
        out['log_error'] = str(e)
    return out

def run_read(run):
    prefix = f'results/t1_access/{run}/'
    objects=[]
    for p in s3.get_paginator('list_objects_v2').paginate(Bucket=BUCKET, Prefix=prefix):
        objects.extend(p.get('Contents', []))
    out = dict(run=run, code={}, objects=[], checkpoint_progress=[])
    for f in ('models.py', 'analyze.py', 'simulate.py', 't1_job.py', 'points_filter.py'):
        raw = s3.get_object(Bucket=BUCKET, Key=f'code/t1_access/{run}/{f}')['Body'].read()
        out['code'][f] = dict(sha256=hashlib.sha256(raw).hexdigest(),
                              matches_working_file=raw == (ROOT / f).read_bytes())
    for o in objects:
        key=o['Key']
        out['objects'].append(dict(key=key, size=o['Size'], modified=o['LastModified']))
        if key.endswith('.progress.json'):
            out.setdefault('row_progress', []).append(json.loads(s3.get_object(Bucket=BUCKET, Key=key)['Body'].read()))
        if key.endswith('.jsonl') and '/refit_ckpt/' in key:
            raw = s3.get_object(Bucket=BUCKET, Key=key)['Body'].read()
            rows=[]
            for line in raw.splitlines():
                try: rows.append(json.loads(line))
                except ValueError: pass
            out['checkpoint_progress'].append(dict(key=key, records=len(rows),
                 rep_indices=[r.get('rep') for r in rows],
                 fit_seconds=[r.get('fit_seconds') for r in rows],
                 failures=sum(bool(r.get('failed')) for r in rows),
                 identities=sorted(set(r.get('ident','') for r in rows))))
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out', required=True); a=ap.parse_args()
    jobs=[]
    for run_fragment in ('refit-contro', 'ref-m2s-omeg'):
        jobs.extend(sm.list_training_jobs(NameContains=run_fragment, SortBy='CreationTime',
                    SortOrder='Descending', MaxResults=100)['TrainingJobSummaries'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        js=[x for x in pool.map(job_read, jobs) if x]
        rs=list(pool.map(run_read, RUNS))
    out=dict(observed_at=dt.datetime.now(dt.timezone.utc).isoformat(), jobs=js, runs=rs)
    Path(a.out).write_text(json.dumps(out, indent=2, default=str)+'\n')
    for r in rs:
        subset=[j for j in js if j['environment']['RESULTS_URI'].rstrip('/').endswith('/'+r['run'])]
        print(r['run'], [(j['status'], j['training_seconds'], j['billable_seconds']) for j in subset])
        print('snapshot matches:', all(v['matches_working_file'] for v in r['code'].values()),
              'objects:',len(r['objects']), 'refit checkpoints:',[(x['records'],x['fit_seconds']) for x in r['checkpoint_progress']])
        print('row progress:',r.get('row_progress', []))
    print(a.out)

if __name__ == '__main__': main()
