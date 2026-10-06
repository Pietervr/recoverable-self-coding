"""Ledger row 19, STAGE 2 (the screen): plan, gate and submit packed jobs for BOTH screen roles (login node, through t1py).
Codex RSC 9202e8b items 1, 5 and 7.

ROLES (`--role`):
  refit  the declared resample indices of the 100 fresh datasets, by the UNCHANGED row19_shard.py worker (one index per
         worker, per_slot 1); ledger kind "shard" in the screen campaign; plan slots {slot, rep, indices}.
  orig   the 100 lossless originals, by row19_screen_orig.py (one dataset per worker); ledger kind "orig" in the originals
         campaign; plan slots {slot, reps}.
Each role has its own manifest (the screen manifest and the originals manifest: the same datasets, identities, cfg and pins,
their own root and campaign), its own pilot and its own later admission.

EVIDENCE (never memory or names): DONE = a record (refit: row19_shard.read_record against the screen task; orig: a valid
lossless cache read back by row19_slice.read_orig) of a declared rep and index; any other file HOLDS. IN FLIGHT = the plan of
a live ledger entry of the role's kind whose runner has not ended; a live entry without its plan HOLDS. MISSING = the rest.
Nothing outside the screen's own roots is ever DONE: the development datasets 0-2 are external parity anchors only.

PLAN: refit - index-major round robin over the declared reps (index 0 of reps 3..102, then index 1, ...), `cores` slots a
job, so the screen's first job is exactly reps 3..26 at index 0; orig - the missing reps in order, `cores` a job.

THE GATE (all must hold; the reason is printed):
  - no STOP file in the role's root; the manifest's code pins hold in the clone the jobs run from;
  - the seed domain: the 100 resolved seeds recomputed and equal to the declared SHA-256, unique, disjoint from the
    manifest's excluded set (historical, the three development datasets) AND from the bank manifest's 408 seeds
    recomputed from that manifest (no caller-supplied list); the declared identity map complete for all 100 reps and,
    for every PLANNED rep, equal to what this runtime computes;
  - FUNDING: settled + live reservations of EVERY declared campaign ledger (slice, shard, bank, screen, originals) + the
    declared settled charges outside them + this submission's full reservations <= the programme allocation;
  - the first job of a role is its pilot (`--pilot`, alone, only while the ledger holds no entry of the role's kind);
  - every later job: (1) <root>/gate/qualified_<role>_job1.json, written by row19_screen_status.py --qualify, parsed and
    bound to what THIS process recomputes (manifest SHA-256, root, campaign, code pins, wrapper, job 1's PBS id, token and
    plan SHA-256, the task bindings of job 1's reps, and the anchor verdict's SHA-256); (2) <root>/gate/review_<role>.json
    from `--adopt-review` ONLY with (1) holding: a git-tracked, unmodified review record, its SHA-256, the qualification's
    SHA-256 and a highest job number, never overwritten; (3) the newest <root>/gate/watch_<role>_*.json: fresh, production,
    zero alarms, <= 2,700 s old, bound to the same values and to EVERY job of the role the ledger holds now.
THE CAP (item 7): the scientific manifests declare `budget.core_hours_cap: null`, so the unchanged runner never compares a
cap and the manifests' SHA-256 (named by every binding) never moves. The live cap lives in the campaign ledger, created at
the initial phase of chpc/row19_screen_budget.json and raised only by `--raise-cap NEW --note "<owner's ruling>"`, which
records old, new, note and time in the ledger's cap_history (row19_ledger.raise_cap) and appends the phase to the budget file.
No spent hour is reset, no binding rewritten. The allocation stays the hard stop.

    t1py chpc/row19_screen_admit.py --manifest chpc/row19_screen_manifest.json --role refit --pilot [--dry-run]
    t1py chpc/row19_screen_admit.py --manifest chpc/row19_screen_orig_manifest.json --role orig --pilot [--dry-run]
    t1py chpc/row19_screen_admit.py --manifest M --role R --adopt-review reviews/<record>.md --max-job-number N
    t1py chpc/row19_screen_admit.py --manifest M --role R --jobs K [--dry-run]
    t1py chpc/row19_screen_admit.py --manifest M --role R --raise-cap NEW --note "<owner ruling>"
"""
import os, sys, json, time, glob, fcntl, hashlib, argparse, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, ".."))
for p in (T1, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
from row19_ledger import CampaignLedger, LIVE

ROLES = {"refit": "shard", "orig": "orig"}
REVIEW_SCHEMA = "row19-screen-review-1"
QUAL_SCHEMA = "row19-screen-qualification-1"
WATCH_SCHEMA = "row19-screen-watch-1"
CEILING_S = 2700.0
BOUND_KEYS = ("manifest_sha256", "root", "campaign", "code", "wrapper_sha256")


def hms(seconds):
    s = int(round(seconds)); return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def seeds_of(man):
    import simulate as S
    st = man["setting"]; kw = dict(st["grid"])
    return {int(r): int(S.dataset_seed(st["generator"], kw, int(r), int(st["D"]), int(man["datasets"]["seed_base"]))) for r in man["datasets"]["reps"]}


def seeds_sha256(seeds):
    return hashlib.sha256(json.dumps([[int(r), int(s)] for r, s in sorted(seeds.items())]).encode()).hexdigest()


def seed_domain_problem(man):
    """'' when the declared screen seed domain is complete, unique, the declared one and disjoint from every exclusion and from
    the bank's seeds recomputed from the bank manifest named here."""
    reps = [int(r) for r in man["datasets"]["reps"]]
    if len(reps) != int(man["datasets"].get("n_attempted", -1)) or len(set(reps)) != len(reps):
        return f"the declared reps are not exactly {man['datasets'].get('n_attempted')} distinct ids"
    seeds = seeds_of(man)
    if len(set(seeds.values())) != len(seeds):
        return "two screen datasets resolve to the same seed"
    if seeds_sha256(seeds) != man["datasets"].get("resolved_seeds_sha256"):
        return "the recomputed screen seed list is not the declared one"
    excl = {int(x) for x in man["datasets"].get("excluded_resolved_seeds", [])}
    if not excl:
        return "the excluded seed set is empty"
    if set(seeds.values()) & excl:
        return "a screen seed is in the excluded set"
    bp = os.path.join(T1, man["datasets"]["bank_manifest"])
    if not os.path.exists(bp) or sha_file(bp) != man["datasets"]["bank_manifest_sha256"]:
        return "the bank manifest named by the screen is absent or not the declared bytes"
    bank = json.load(open(bp)); bseeds = seeds_of(bank)
    if seeds_sha256(bseeds) != bank["datasets"].get("resolved_seeds_sha256") or len(bseeds) != len(bank["datasets"]["reps"]) or not bseeds:
        return "the bank's seed domain does not recompute to its declared list"
    if set(seeds.values()) & set(bseeds.values()):
        return "a screen seed is a bank seed"
    idents = man["datasets"].get("identities", {})
    if sorted(int(k) for k in idents) != sorted(reps) or any(not isinstance(v, str) or len(v) != 64 for v in idents.values()):
        return "the declared identity map is not complete for every screen rep"
    return ""


def identity_problem(man, reps):
    import row19_shard as SH
    for r in reps:
        t = SH.task(man, r)
        if man["datasets"]["identities"].get(str(r)) != t["ident"]:
            return f"rep {r}: this runtime computes identity {t['ident'][:16]}, the manifest declares {str(man['datasets']['identities'].get(str(r)))[:16]}"
    return ""


def ledger_for(man):
    """The campaign ledger, created at the initial budget phase when absent, otherwise read at its own (possibly raised) cap."""
    camp = man["storage"]["campaign"]
    if os.path.exists(os.path.join(camp, "budget.json")):
        return CampaignLedger(camp, None)
    phases = json.load(open(os.path.join(T1, man["budget"]["admission"])))["phases"]
    return CampaignLedger(camp, float(phases[0]["cap_core_h"]))


def funding_problem(man, proposed_core_h):
    """Settled + live of every declared campaign + declared other charges + the proposal, against the allocation."""
    f = man["funding"]; total = float(f.get("other_settled_core_h", 0.0)); seen = []
    for camp in f["campaigns"]:
        p = os.path.join(camp, "budget.json")
        if not os.path.exists(p):
            seen.append(f"{os.path.basename(camp)} 0"); continue
        try:
            led = json.load(open(p))
        except Exception as e:
            return f"the ledger of {camp} is unreadable ({e}); funding cannot be established"
        s = sum(float(e.get("settled_core_h", 0) or 0) for e in led["entries"].values() if e.get("state") == "settled")
        l = sum(float(e["reserved_core_h"]) for e in led["entries"].values() if e.get("state") != "settled")
        total += s + l; seen.append(f"{os.path.basename(camp)} {s + l:.0f}")
    if total + proposed_core_h > float(f["allocation_core_h"]) + 1e-9:
        return (f"funding: {total:.0f} committed ({', '.join(seen)}) + {proposed_core_h:.0f} proposed > the {f['programme']} "
                f"allocation of {f['allocation_core_h']:.0f}")
    return ""


def evidence(man, role, validate=True):
    root = man["storage"]["root"]; reps = [int(r) for r in man["datasets"]["reps"]]
    problems = []; done = set()
    if role == "refit":
        import row19_shard as SH
        B = int(man["cfg"]["n_boot_refit"])
        for d in glob.glob(os.path.join(root, "records", "rep*")):
            r = os.path.basename(d)[3:]
            if not r.isdigit() or int(r) not in reps:
                problems.append(f"{d}: records of an undeclared rep"); continue
            r = int(r); t = SH.task(man, r) if validate else None
            for p in sorted(glob.glob(os.path.join(d, "rec_*.json"))):
                name = os.path.basename(p)
                try:
                    i = int(name[4:7])
                    if name != f"rec_{i:03d}.json" or not 0 <= i < B:
                        raise ValueError
                except ValueError:
                    problems.append(f"{p}: not a record file name"); continue
                if validate:
                    try:
                        SH.read_record(p, t, i)
                    except ValueError as e:
                        problems.append(str(e)); continue
                done.add((r, i))
    else:
        import row19_screen_orig as O
        files = glob.glob(os.path.join(root, "orig", "orig_*.json"))
        by_prefix = {man["datasets"]["identities"][str(r)][:24]: r for r in reps}
        for p in files:
            pre = os.path.basename(p)[5:-5]
            if pre not in by_prefix:
                problems.append(f"{p}: a cache of no declared identity"); continue
            r = by_prefix[pre]
            if validate:
                try:
                    got, _ = O.read_cache(root, O.task_checked(man, r))
                except ValueError as e:
                    problems.append(str(e)); continue
            done.add(r)
    led = os.path.join(man["storage"]["campaign"], "budget.json")
    entries = list(json.load(open(led))["entries"].values()) if os.path.exists(led) else []
    flight, used = set(), set()
    for e in entries:
        if e.get("kind") != ROLES[role]:
            continue
        used.add(int(e["rep"]))
        if e.get("state") in LIVE and e.get("runner_exit") is None:
            pp = os.path.join(root, "plans", f"job_{int(e['rep'])}.json")
            if not os.path.exists(pp):
                problems.append(f"{role} job {e['rep']} ({e.get('job_id')}) is live but its plan is missing"); continue
            for s in json.load(open(pp)).get("slots", []):
                if role == "refit":
                    flight.update((int(s["rep"]), int(i)) for i in s["indices"])
                else:
                    flight.update(int(r) for r in s["reps"])
    return done, flight, used, problems


def plan_jobs(man, role, n_jobs, done, flight, used):
    cores = int(man["pbs"]["cores"]); reps = [int(r) for r in man["datasets"]["reps"]]
    if role == "refit":
        B = int(man["cfg"]["n_boot_refit"])
        order = [(r, [i]) for i in range(B) for r in reps if (r, i) not in done and (r, i) not in flight]
    else:
        order = [r for r in reps if r not in done and r not in flight]
    jobs, n = [], (max(used) + 1 if used else 1)
    for k in range(0, len(order), cores):
        if len(jobs) >= n_jobs:
            break
        chunk = order[k:k + cores]
        if role == "refit":
            jobs.append({"job": n, "slots": [{"slot": s, "rep": r, "indices": idx} for s, (r, idx) in enumerate(chunk)]})
        else:
            jobs.append({"job": n, "slots": [{"slot": s, "reps": [r]} for s, r in enumerate(chunk)]})
        n += 1
    return jobs, len(order) - sum(len(j["slots"]) for j in jobs)


def planned_reps(job):
    return sorted({int(s["rep"]) for s in job["slots"]} if "rep" in job["slots"][0] else {int(r) for s in job["slots"] for r in s["reps"]})


def expected_bound(man, manifest_path, role):
    root, campaign = man["storage"]["root"], man["storage"]["campaign"]
    led = json.load(open(os.path.join(campaign, "budget.json")))
    jobs = {}
    for e in led["entries"].values():
        if e.get("kind") != ROLES[role]:
            continue
        n = str(int(e["rep"])); pp = os.path.join(root, "plans", f"job_{n}.json")
        jobs[n] = dict(job_id=e.get("job_id"), token=e.get("token"), plan_sha256=sha_file(pp) if os.path.exists(pp) else None)
    bindings = {}
    if role == "refit":
        for p in sorted(glob.glob(os.path.join(root, "task_*.json"))):
            bindings[os.path.basename(p)[5:-5]] = sha_file(p)
    return dict(manifest_sha256=sha_file(manifest_path), root=root, campaign=campaign, code=dict(man["code"]["files"]),
                wrapper_sha256=man.get("environment", {}).get("wrapper_sha256"), jobs=jobs, bindings=bindings)


def bound_problem(got, want, jobs):
    if not isinstance(got, dict):
        return "no `bound` object"
    for k in BOUND_KEYS:
        if got.get(k) != want[k]:
            return f"its `{k}` is not this campaign's"
    if not isinstance(got.get("jobs"), dict):
        return "no job bindings"
    if jobs == "all":
        if got["jobs"] != want["jobs"]:
            return f"its jobs {sorted(got['jobs'])} are not the ledger's {sorted(want['jobs'])} as they are now"
    else:
        for n in jobs:
            w = want["jobs"].get(n)
            if not w or None in w.values() or got["jobs"].get(n) != w:
                return f"its binding of job {n} is not the ledger's and the root's"
    for k, v in (got.get("bindings") or {}).items():
        if want["bindings"].get(k) != v:
            return f"its task binding of rep {k} is not the root's"
    if not isinstance(got.get("anchors_sha256"), str):
        return "no anchor verdict is bound"
    return ""


def tracked_unmodified(rel):
    try:
        a = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=T1, capture_output=True, text=True)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=T1, capture_output=True, text=True)
        return a.returncode == 0 and b.returncode == 0
    except Exception:
        return False


def qualification_problem(man, manifest_path, role):
    q = os.path.join(man["storage"]["root"], "gate", f"qualified_{role}_job1.json")
    if not os.path.exists(q):
        return f"no pilot qualification (gate/qualified_{role}_job1.json)", None
    try:
        doc = json.load(open(q))
    except Exception as e:
        return f"the qualification is unreadable ({e})", None
    if doc.get("schema") != QUAL_SCHEMA or doc.get("role") != role or doc.get("qualified_job") != 1 or doc.get("production") is not True:
        return f"the qualification is not a production qualification of {role} job 1", None
    rec = doc.get("receipt") or {}
    if rec.get("alarms") or rec.get("fresh") is not True:
        return "the qualification's embedded receipt has alarms or is not fresh", None
    want = expected_bound(man, manifest_path, role)
    why = bound_problem(doc.get("bound"), want, ["1"])
    if not why and role == "refit":
        p1 = json.load(open(os.path.join(man["storage"]["root"], "plans", "job_1.json")))
        missing = [r for r in planned_reps(p1) if str(r) not in (doc["bound"].get("bindings") or {})]
        if missing:
            why = f"the task bindings of job 1's reps {missing[:5]} are not bound"
    return (f"the qualification: {why}" if why else ""), sha_file(q)


def receipt_problem(man, manifest_path, role, now=None):
    now = time.time() if now is None else now
    ps = sorted(glob.glob(os.path.join(man["storage"]["root"], "gate", f"watch_{role}_*.json")))
    if not ps:
        return "no watch receipt in the gate"
    try:
        r = json.load(open(ps[-1]))
    except Exception as e:
        return f"the newest receipt is unreadable ({e})"
    if r.get("schema") != WATCH_SCHEMA or r.get("role") != role or r.get("production") is not True or r.get("fresh") is not True:
        return "the newest receipt is not a fresh production receipt of this role"
    if r.get("alarms"):
        return f"the newest receipt has {len(r['alarms'])} alarm(s)"
    t = r.get("time")
    if not isinstance(t, (int, float)) or t > now + 60 or now - t > CEILING_S:
        return f"the newest receipt is not within {CEILING_S:.0f} s"
    why = bound_problem(r.get("bound"), expected_bound(man, manifest_path, role), "all")
    return f"the newest receipt: {why}" if why else ""


def review_problem(man, manifest_path, role, planned):
    p = os.path.join(man["storage"]["root"], "gate", f"review_{role}.json")
    if not os.path.exists(p):
        return "no adopted review of the pilot's actual evidence; run --adopt-review first"
    doc = json.load(open(p))
    if doc.get("schema") != REVIEW_SCHEMA or doc.get("role") != role:
        return "the adopted review has another schema or role"
    full = os.path.join(T1, doc.get("record_path", ""))
    if not os.path.exists(full) or sha_file(full) != doc.get("record_sha256") or not tracked_unmodified(doc.get("record_path", "")):
        return "the adopted review record is not tracked and unmodified in this clone with the adopted SHA-256"
    if not isinstance(doc.get("max_job_number"), int) or any(int(j) > doc["max_job_number"] for j in planned):
        return f"the adopted review covers job numbers up to {doc.get('max_job_number')}"
    why, qsha = qualification_problem(man, manifest_path, role)
    if why:
        return why
    if doc.get("qualification_sha256") != qsha:
        return "the adopted review names another qualification than the one in the gate"
    return receipt_problem(man, manifest_path, role)


def adopt_review(man, manifest_path, role, record_rel, max_job_number):
    full = os.path.join(T1, record_rel)
    if not os.path.exists(full) or not tracked_unmodified(record_rel):
        return f"REFUSED: {record_rel} is not tracked by git in this clone, or differs from HEAD"
    if not isinstance(max_job_number, int) or max_job_number < 2:
        return "REFUSED: --max-job-number must be an integer of at least 2"
    why, qsha = qualification_problem(man, manifest_path, role)
    if why:
        return f"REFUSED: {why}"
    p = os.path.join(man["storage"]["root"], "gate", f"review_{role}.json")
    if os.path.exists(p):
        return f"REFUSED: {p} exists; an adopted review is never overwritten"
    doc = dict(schema=REVIEW_SCHEMA, role=role, by="R052", time=time.time(), record_path=record_rel, record_sha256=sha_file(full),
               qualification_sha256=qsha, max_job_number=int(max_job_number))
    tmp = p + f".tmp.{os.getpid()}"
    with open(tmp, "w") as fh:
        json.dump(doc, fh, indent=1, allow_nan=False); fh.flush(); os.fsync(fh.fileno())
    os.link(tmp, p); os.remove(tmp)
    return f"adopted: {record_rel} ({doc['record_sha256'][:16]}) for {role}, qualification {qsha[:16]}, job numbers up to {max_job_number}"


def pin_problems(man, clone):
    bad = []
    for f, want in man["code"]["files"].items():
        p = os.path.join(clone, "workspace_demo", "t1_access", f)
        if not os.path.exists(p) or sha_file(p) != want:
            bad.append(f)
    return bad


def gate_problem(man, manifest_path, role, used, pilot, n_jobs, jobs, walltime_s):
    root = man["storage"]["root"]
    if os.path.exists(os.path.join(root, "STOP")):
        return "a STOP file is present in the role's root"
    why = seed_domain_problem(man)
    if why:
        return why
    reps = sorted({r for j in jobs for r in planned_reps(j)}) if jobs else []
    why = identity_problem(man, reps)
    if why:
        return why
    why = funding_problem(man, len(jobs) * int(man["pbs"]["cores"]) * walltime_s / 3600.0)
    if why:
        return why
    if pilot:
        if used:
            return f"--pilot is only for the role's first job; the ledger already holds job(s) {sorted(used)}"
        return "" if n_jobs == 1 else "the pilot is exactly one job"
    if not used:
        return "the role's first job is its pilot: say --pilot"
    return review_problem(man, manifest_path, role, [j["job"] for j in jobs])


def refit_pbs_script(man, plan, token, walltime_s, queue, toolchain, clone, manifest_rel):
    """The packed refit job: the UNCHANGED row19_shard.py job-start / worker / job-end, with the screen's own job and file names
    (row19_screen_refit_<n>) so nothing of the development shard route's jobs/ files is ever overwritten."""
    root, cores = man["storage"]["root"], int(man["pbs"]["cores"])
    n = plan["job"]; reserve = int(float(man["pbs"]["deadline_reserve_s"]))
    end = f"$T/t1py chpc/row19_shard.py job-end --manifest {manifest_rel} --plan $PLAN --job-id $PBS_JOBID --reservation-token {token} --started-epoch $START"
    L = ["#!/bin/bash", f"#PBS -N t1_screen_{n}", f"#PBS -P {man['pbs']['project']}", f"#PBS -q {queue}",
         f"#PBS -l select=1:ncpus={cores}:mpiprocs={cores}:mem={int(man['pbs']['mem_gb'])}gb:nodetype={man['pbs']['nodetype']}",
         f"#PBS -l walltime={hms(walltime_s)}", f"#PBS -o {toolchain}/jobs/row19_screen_refit_{n}.out", f"#PBS -e {toolchain}/jobs/row19_screen_refit_{n}.err",
         "#PBS -m ae", "#PBS -M pgwvanrooyen@sun.ac.za",
         f"# Ledger row 19 stage 2: screen refit job {n}, {len(plan['slots'])} single-core workers, one resample index per record (row19_shard.py unchanged).",
         "ulimit -s unlimited", f"T={toolchain}", f"cd {clone}/workspace_demo/t1_access",
         "export NPROC=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONUNBUFFERED=1",
         "START=$(date +%s)", f"DEADLINE=$((START + {int(walltime_s)} - {reserve}))",
         'echo "host $(hostname)  $(grep -m1 \'model name\' /proc/cpuinfo)"',
         f'echo "code $(git rev-parse --short HEAD)  start $(date -u +%FT%TZ)  job $PBS_JOBID  screen refit job {n}"',
         f"PLAN={root}/plans/job_{n}.json",
         f"$T/t1py chpc/row19_shard.py job-start --manifest {manifest_rel} --plan $PLAN --job-id $PBS_JOBID --walltime-s {int(walltime_s)} --reservation-token {token}",
         "rc=$?", 'if [ $rc -ne 0 ]; then', f"  {end}", '  echo "exit $rc job $PBS_JOBID end $(date -u +%FT%TZ) (ADMISSION FAILED)"', "  exit $rc", "fi",
         f"mkdir -p {root}/logs"]
    for s in plan["slots"]:
        L.append(f"$T/t1py chpc/row19_shard.py worker --manifest {manifest_rel} --rep {s['rep']} --indices {','.join(str(i) for i in s['indices'])} "
                 f"--slot {s['slot']} --job-id $PBS_JOBID --deadline-epoch $DEADLINE > {root}/logs/job$PBS_JOBID.slot{s['slot']}.log 2>&1 &")
    L += ["wait", end, "rc=$?", 'echo "exit $rc job $PBS_JOBID end $(date -u +%FT%TZ)"', "exit $rc"]
    return "\n".join(L) + "\n"


def orig_pbs_script(man, plan, token, walltime_s, queue, toolchain, clone, manifest_rel):
    root, cores = man["storage"]["root"], int(man["pbs"]["cores"])
    n = plan["job"]; reserve = int(float(man["pbs"]["deadline_reserve_s"]))
    end = f"$T/t1py chpc/row19_screen_orig.py job-end --manifest {manifest_rel} --plan $PLAN --job-id $PBS_JOBID --reservation-token {token} --started-epoch $START"
    L = ["#!/bin/bash", f"#PBS -N t1_sorig_{n}", f"#PBS -P {man['pbs']['project']}", f"#PBS -q {queue}",
         f"#PBS -l select=1:ncpus={cores}:mpiprocs={cores}:mem={int(man['pbs']['mem_gb'])}gb:nodetype={man['pbs']['nodetype']}",
         f"#PBS -l walltime={hms(walltime_s)}", f"#PBS -o {toolchain}/jobs/row19_screen_orig_{n}.out", f"#PBS -e {toolchain}/jobs/row19_screen_orig_{n}.err",
         "#PBS -m ae", "#PBS -M pgwvanrooyen@sun.ac.za",
         f"# Ledger row 19 stage 2: screen original job {n}, {len(plan['slots'])} single-core workers, one lossless original each.",
         "ulimit -s unlimited", f"T={toolchain}", f"cd {clone}/workspace_demo/t1_access",
         "export NPROC=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONUNBUFFERED=1",
         "START=$(date +%s)", f"DEADLINE=$((START + {int(walltime_s)} - {reserve}))",
         'echo "host $(hostname)  $(grep -m1 \'model name\' /proc/cpuinfo)"',
         f'echo "code $(git rev-parse --short HEAD)  start $(date -u +%FT%TZ)  job $PBS_JOBID  screen original job {n}"',
         f"PLAN={root}/plans/job_{n}.json",
         f"$T/t1py chpc/row19_screen_orig.py job-start --manifest {manifest_rel} --plan $PLAN --job-id $PBS_JOBID --walltime-s {int(walltime_s)} --reservation-token {token}",
         "rc=$?", 'if [ $rc -ne 0 ]; then', f"  {end}", '  echo "exit $rc job $PBS_JOBID end $(date -u +%FT%TZ) (ADMISSION FAILED)"', "  exit $rc", "fi",
         f"mkdir -p {root}/logs"]
    for s in plan["slots"]:
        L.append(f"$T/t1py chpc/row19_screen_orig.py worker --manifest {manifest_rel} --reps {','.join(str(r) for r in s['reps'])} --slot {s['slot']} "
                 f"--job-id $PBS_JOBID --deadline-epoch $DEADLINE > {root}/logs/job$PBS_JOBID.slot{s['slot']}.log 2>&1 &")
    L += ["wait", end, "rc=$?", 'echo "exit $rc job $PBS_JOBID end $(date -u +%FT%TZ)"', "exit $rc"]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True); ap.add_argument("--role", required=True, choices=sorted(ROLES))
    ap.add_argument("--jobs", type=int, default=None); ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--adopt-review", default=None); ap.add_argument("--max-job-number", type=int, default=None)
    ap.add_argument("--raise-cap", type=float, default=None); ap.add_argument("--note", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); role = a.role
    if man.get("role") != role:
        print(f"REFUSED: {a.manifest} is the {man.get('role')} manifest, not {role}"); return 2
    if a.adopt_review is not None:
        out = adopt_review(man, a.manifest, role, a.adopt_review, a.max_job_number); print(out)
        return 0 if out.startswith("adopted") else 2
    if a.raise_cap is not None:
        if not a.note or len(a.note.strip()) < 8:
            print("REFUSED: a cap raise needs the owner's ruling as --note"); return 2
        L = ledger_for(man); new = L.raise_cap(a.raise_cap, a.note)
        bp = os.path.join(T1, man["budget"]["admission"]); b = json.load(open(bp))
        b["phases"].append(dict(cap_core_h=new, note=a.note, t=time.time(), campaign=man["storage"]["campaign"]))
        json.dump(b, open(bp, "w"), indent=1)
        print(f"cap raised to {new:.0f} (ledger cap_history and {man['budget']['admission']} updated; commit the budget file)"); return 0
    n_jobs = 1 if a.pilot else a.jobs
    if not n_jobs or n_jobs < 1:
        print("say --pilot or --jobs N"); return 2
    queue = man["pbs"]["queue"]; walltime_s = float(man["pbs"]["walltime_h"]) * 3600.0
    toolchain, clone, root = man["shard"]["toolchain"], man["shard"]["clone"], man["storage"]["root"]
    os.makedirs(os.path.join(root, "plans"), exist_ok=True); os.makedirs(os.path.join(root, "gate"), exist_ok=True)
    manifest_rel = os.path.relpath(os.path.abspath(a.manifest), os.path.join(clone, "workspace_demo", "t1_access"))
    with open(os.path.join(root, "plans", ".submit.lock"), "a+") as lk:
        try:
            fcntl.flock(lk.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("HELD: another submitter holds the plan lock"); return 2
        done, flight, used, problems = evidence(man, role)
        print(f"{role}: done {len(done)}, in flight {len(flight)}")
        if problems:
            print(f"HELD: {len(problems)} problem(s) in the evidence:"); [print("   -", p) for p in problems[:10]]; return 2
        jobs, left = plan_jobs(man, role, n_jobs, done, flight, used)
        why = gate_problem(man, a.manifest, role, used, a.pilot, n_jobs, jobs, walltime_s)
        pins = pin_problems(man, clone)
        if pins and not why:
            why = f"the manifest's pins do not hold in the clone the jobs run from: {pins}"
        print(f"planned {len(jobs)} job(s), {sum(len(s.get('indices', s.get('reps', []))) for j in jobs for s in j['slots'])} units; {left} not in this call")
        for j in jobs[:3]:
            print(f"  job {j['job']}: " + "; ".join(f"slot {s['slot']} " + (f"rep {s['rep']} {s['indices']}" if role == 'refit' else f"reps {s['reps']}") for s in j["slots"][:4]) + " ...")
        if a.dry_run:
            print(f"DRY RUN; the gate {'would REFUSE: ' + why if why else 'would admit this submission'}"); return 0
        if why:
            print(f"REFUSED by the screen gate: {why}"); return 2
        L = ledger_for(man)
        os.makedirs(os.path.join(toolchain, "jobs"), exist_ok=True)
        for j in jobs:
            cores = int(man["pbs"]["cores"])
            token, t = L.reserve(ROLES[role], int(j["job"]), cores, walltime_s, root, f"row19_screen_admit {role} {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
            pp = os.path.join(root, "plans", f"job_{j['job']}.json")
            with open(pp, "w") as fh:
                json.dump(dict(j, queue=queue, walltime_s=walltime_s, token=token, created=time.time()), fh, indent=1); fh.flush(); os.fsync(fh.fileno())
            sp = os.path.join(toolchain, "jobs", f"row19_screen_{role}_{j['job']}.pbs")
            script = (refit_pbs_script(man, j, token, walltime_s, queue, toolchain, clone, manifest_rel) if role == "refit"
                      else orig_pbs_script(man, j, token, walltime_s, queue, toolchain, clone, manifest_rel))
            open(sp, "w").write(script)
            r = subprocess.run(["qsub", sp], capture_output=True, text=True)
            if r.returncode != 0:
                print(f"{role} job {j['job']}: qsub failed ({r.stderr.strip()[:200]}); reservation {token} stays reserved and unbound"); return 1
            job_id = r.stdout.strip(); L.bind(token, job_id)
            print(f"{role} job {j['job']}: reserved {token} ({cores} x {walltime_s/3600:.0f} h; spent {t['spent']:.0f}, live {t['live']:.0f} of {t['cap']:.0f}), submitted {job_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
