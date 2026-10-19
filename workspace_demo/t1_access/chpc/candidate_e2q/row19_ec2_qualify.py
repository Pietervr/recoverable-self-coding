"""Row 19 screen on EC2: evaluate the PREDECLARED qualification (aws_ec2/QUALIFICATION_PLAN.md; Codex RSC 0483db4 V10-7) and
write its certificate. Lengau login node, t1py, controller tree; read-only on the screen root (the replay runs in a sandbox).

    t1py chpc/row19_ec2_qualify.py --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e1.json \
        --authority <inventory.json> --q1-key qual-Q1/1 --q1-bundle <dir> --q1-opmanifest <op Q1> \
        --q2-key qual-Q2/1 --q2-bundle <dir> --q2-opmanifest <op Q2> --s-manifest chpc/row19_qual_S_manifest.json --sandbox <scratch> --out cert.json

Every bundle first passes the ingestion's own checks (row19_ec2_ingest.check_bundle + plan_units: frozen inventory, plan
contract, typed outcomes, effective B_full attestation, complete worker statuses, records valid against the frozen task).
Then the rule, all float-bit (row19_screen_verify.payload: stats, failed, failed_reason, chosen, identity, seed, B):
  R1  Q1's 24 Lengau duplicates (index 1, 2 of reps 3..14) equal the Lengau screen records;
  R2  Q1's 48 block coordinates (index 199, 198 of reps 3..26) equal S's isolated shadow references;
  R3  Q2's 24 repeats (index 199 of reps 3..26) equal Q1's AND S's;
  R4  Q1's 4 sentinels equal Lengau; memory at Q1's 76-worker packing: >= 10 host samples, peak host use (MemTotal -
      MemAvailable) <= 184 GiB of 192, every worker's maxrss under the 4.5 GiB stop (checked by the status contract);
  R5  ingestion recovery on Q1's actual bundle in a SANDBOX root: a forced stop after the first published pair, then a
      replay, ends 'ingested' with every published file the register's bytes; a second replay re-validates.
COVERAGE (declared before any result): R1, R2 and R3 each need >= 75 % of their coordinates fitted successfully (failed
False) on BOTH sides - 18/24, 36/48, 18/24. Failed fits are compared like any other payload (flag and reason must match)
and reported apart; they never count as successes and are never replaced or chosen by outcome.
OUTCOME: NO_RELEASE on any difference or invalid evidence (production stays shut; report and stop); else INCONCLUSIVE when
coverage is short (no release, no replacement panel bought without a new owner decision); else RELEASE, naming Q1 as the
released attempt (its 48 block coordinates may then be ingested as production; Q2, S and the duplicates stay evidence).
The certificate binds the sha256 of the code, manifests, plans, bundles, inventory, shadow records and replay evidence;
ec2_release_state.json may name it only with a separate actual-result review.

REVISION 2 (Codex RSC 3dc0daf R1-4, R1-6):
  finite     a coordinate counts as SUCCESSFUL only when both sides are not failed AND every frozen predictor-band statistic
             is finite (the procedure's own usable predicate, analyze.refit_bootstrap / bench_compare.usable); agreeing
             failed and agreeing non-finite paths are counted apart (failed_both, nonfinite_both) and never reach coverage.
  S          the S references are consumed as PRODUCER evidence, not record bodies alone: the isolated manifest is the exact
             derivation (row19_ec2_state.isolated_S_problem); its root holds exactly the fixed plans job_1/job_2 of
             aws_ec2/qual_S_plan.json; the isolated campaign ledger holds kind-shard entries for jobs 1 and 2 only, each job's
             producing entry settled with a bound PBS id and a finite charge, every attempt kept; every slot has a complete
             terminal worker status of that PBS id; every record's timing names that producer. All of it is bound.
  memory     the Q1 memory samples are chronological and each is joined (same minute) to the occupancy line written in the
             same producer iteration; >= 10 samples must be taken while ALL planned workers (76 for Q1) were running, and
             the peak host use over every sample is <= 184 GiB. Too few full-packing samples is NO_RELEASE.
  recovery   R5 is stated with its exact scope (`replay.scope`): an interrupted INGESTION PUBLICATION on a relocated,
             re-bound sandbox copy of Q1's actual bundle, then a replay and a second replay. It does NOT demonstrate producer
             process/host restart or interrupted-transfer recovery, and its sandbox plan hash differs from the canonical
             plan, so it says nothing about the Mac acknowledgement of the canonical attempt.

REVISION 3 (Codex RSC 299f4b7 R2-2, R2-4):
  controls   in mode canonical the controls are read only through row19_partition.adopted_controls (the current adopted bytes).
  S decl     the S evidence is accepted only for THE S campaign the current controls declare (latest version's
             `qualification_S`): --s-manifest must be the declared manifest bytes, its root and campaign the declared ones,
             and the fixed S plan the declared plan bytes - another exact isolated derivation is refused.
  S bound    the certificate binds, beyond the manifest, ledger, plans, statuses and records: every validated timing file,
             every S task binding (root/task_<rep>.json, checked equal to row19_shard.binding_for under the S manifest), the
             producing ledger entries (token, PBS id, reservation, settlement) and the controls declaration itself.
             PROVENANCE CONDITION (stated, cooperative): these files are written by the unchanged worker and the S admission
             on the single-user Lengau filesystem; nothing signs them. The bound digests make any later change detectable;
             they do not prove who wrote the original bytes beyond the ledger's reservation/PBS-id binding.
  replay     the sandbox replay installs its inventory with a SANDBOX root identity (its acknowledgement can never release
             a canonical attempt).

REVISION 4 - CANDIDATE, not adopted (EC2 provider epoch 2). The qualifier reads a row19-provider-partition-2 declaration
through row19_partition REVISION 5 (load, activation lineage) and REFUSES to certify it with this panel: the predeclared
Q1/Q2/S panel qualifies the epoch-1 route only (its block coordinates are indices 198/199, retired under epoch 2). An
epoch-2 release needs the epoch-2 panel of chpc/candidate_e2/QUALIFICATION_E2.md - a plan, not built - and its own
certificate schema. Q1/Q2/S remain evidence for the mechanical route to their demonstrated scope only (Codex design s.3,
s.5). Paths resolve t1_access by name (runs from chpc/ and chpc/candidate_e2/).

REVISION 5 - CANDIDATE, not adopted (EC2 provider epoch 2 QUALIFICATION, chpc/candidate_e2q/DESIGN_e2q.md;
chpc/candidate_e2/QUALIFICATION_E2.md s.2-s.3). The epoch-1 path above is unchanged (`main`). The epoch-2 path is a separate
command writing the SCHEMA-3 certificate:

    t1py chpc/row19_ec2_qualify.py e2 --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e2.json \
        --authority <installed inventory> --key qual-E2Q1/1 --bundle <dir> --opmanifest aws_ec2/prod/manifest_e2q1_e2.json \
        --prod-opmanifest aws_ec2/prod/manifest_production_e2.json --panel aws_ec2/prod/panel_e2q_e2.json \
        --funding aws_ec2/e2_funding.json --sandbox <scratch> --out cert_e2q1.json

  inputs  the schema-2 epoch-2 partition the adopted controls pin, with its canonical activation; the installed inventory;
          the DECLARED panel (row19_ec2_e2qual.panel_problem: regenerated from the partition and its bound claims snapshot);
          the attempt = a reconciled qualification attempt of run qual-E2Q1/qual-E2Q2 whose work/duplicates are exactly the
          panel's, 4 sentinels outside the duplicates; the E2Q operational manifest and the production one, each the exact
          derivation at the funded 22 h lifetime and the exact maker bytes; the funding declaration (bound; the Mac release
          branch rederives it from the pinned Q2 ledger attempt).
  bundle  ingestion's own checks under the schema-2 partition (check_bundle with the per-slot outcomes, unproduced_problems
          - the three qualifying kinds, the present-status rules, the 7/3 bounds - and plan_units on every produced slot);
          every work slot owned by epoch 2; R4' at most 3 non-completed slots of ALL roles
          (row19_ec2_e2rules.qualification_unproduced_problem). An unproduced slot is reported (slot, role, coordinate, exit,
          kind, status presence) and is NEVER turned into a failed-fit record: it is simply not compared and not counted.
  R1'     the 20 duplicates equal the Lengau screen records float-bit (row19_screen_verify.payload); coverage >= 15/20
          finite successful on both sides (the procedure's usable predicate); failed / non-finite agreeing paths are
          reported apart and never count; an unproduced duplicate is reported as such and does not count.
  R2'     every produced work record is a valid record of its frozen task (no reference exists: a limitation, not parity).
  R3'     not performed (QUALIFICATION_E2.md proposes none; Codex ruling 12).
  R4'     memory/occupancy at the concentrated packing: >= 10 chronological samples with all 76 planned workers running, peak
          host use <= 184 GiB, every produced worker's maxrss under the stop (status contract); the plan's 76 slots carry
          >= 61 workers on one replicate; the produced sentinels equal Lengau; <= 3 non-completions, each of a qualifying kind.
  R5'     sandbox replay of the ACTUAL bundle under a sandbox schema-2 epoch with its predecessor activated, the attempt
          presented deliberately as class production (ingestion's per-slot branch runs only for schema-2 production):
          forced stop after the first published pair, replay, second replay, ending 'ingested' with every published file the
          register's bytes; plus the per-slot branch - an actual unproduced WORK slot as it is, otherwise one CONSISTENT
          synthetic fatal-signal non-completion of the first produced work slot (outcome 139, its record, timing and status
          all removed, checksums regenerated, every changed file labelled SYNTHETIC with its original and modified sha256)
          ingested in a second sandbox: listed unproduced, fenced, failure evidence journaled, released by the `ack` rule; and
          the modified bundle replayed against the unmodified journal must HOLD. Scope: ingestion publication recovery only.
  outcome NO_RELEASE on any problem; INCONCLUSIVE when only R1' coverage is short; RELEASE otherwise, naming the E2Q attempt.
The certificate binds the exact code set (row19_ec2_e2qual.CODE, resolved to the files actually used), the manifest, the
partition and its owned digest, the activation, the inventory, the panel, the claims snapshot, the funding bytes, both
operational manifests and the lifetime, the bundle's BUNDLE_SHA256SUMS, the plan and the replay evidence. Release needs
prod_authority.py release-adopt (its epoch-2 branch) and a FAVOURABLE actual-result review with the epoch-2 literal.

REVISION 6 - CANDIDATE, not adopted (Codex review reviews/2026-10-19_e2_adoption_codex_review.md B2 and "Before one paid E2Q1";
replaces the reviewed REVISION 5 bytes 73f912b8, which stay in git at RSC 92a62f6).
  resources  memory() validates every memory/occupancy field by kind (unsigned integers; unsigned finite decimals for the load
             averages) and physical domain (MemTotal > 0, 0 <= MemAvailable <= MemTotal, worker RSS >= 0, running workers
             0..planned) BEFORE any calculation; a malformed or impossible observation is a failed evidence verdict (a problem,
             hence NO_RELEASE), never an exception and never a release. Both timelines must be strictly increasing in time and
             each occupancy line joins at most one memory sample, so the >= 10 full-packing observations are distinct ordered
             producer samples (12 copies of one timestamp are one observation, refused). The occupancy match, the peak over
             ALL samples, the 184 GiB ceiling and the produced-worker status limits are unchanged. This repairs the method
             inherited from epoch 1 and so applies to the epoch-1 `main` path as well; it does not reopen any old result.
  snapshot   the reviewed panel (aws_ec2/prod/panel_e2q_e2.json, f04a5e43) records its claims snapshot at
             chpc/e2_final/claims_snapshot_e2.json, while the promotion map deploys it to chpc/claims_snapshot_e2.json. The
             panel is NOT edited: the reviewed qualification command passes the deployed copy explicitly, and the derivation
             refuses it unless its sha256 and claims digest are the ones the partition binds (31cc268f):
    t1py chpc/row19_ec2_qualify.py e2 --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e2.json \
        --authority <installed inventory> --key qual-E2Q1/1 --bundle <dir> --opmanifest aws_ec2/prod/manifest_e2q1_e2.json \
        --prod-opmanifest aws_ec2/prod/manifest_production_e2.json --panel aws_ec2/prod/panel_e2q_e2.json \
        --snapshot chpc/claims_snapshot_e2.json --funding aws_ec2/e2_funding.json --sandbox <scratch> --out cert_e2q1.json
  R5'        the sandbox still presents the attempt as class production (ruling 12, reviewed); since ingestion REVISION 8 the
             canonical route for a RELEASED E2Q1/E2Q2 is the same per-slot branch under its real qualification class (tested
             in chpc/candidate_e2q/test_e2q_ingest.py), so R5' and the canonical ingestion exercise one branch.
  content    the certificate binds file CONTENT ({promoted path: sha256}, code_bound); byte-identical candidate and promoted
             copies yield the same map, so a location change alone does not invalidate a certificate (DESIGN_e2q choice 8)."""
import os, sys, re, json, glob, copy, shutil, hashlib, argparse, time

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = HERE
while os.path.basename(T1) != "t1_access":
    if os.path.dirname(T1) == T1:
        raise RuntimeError(f"{HERE} is not inside a t1_access tree")
    T1 = os.path.dirname(T1)
CHPC = os.path.join(T1, "chpc")
CANDIDATE = os.path.abspath(HERE) != os.path.abspath(CHPC)          # REVISION 5: a pre-promotion candidate run
_PATH = [T1, CHPC] + ([os.path.join(CHPC, "candidate_e2")] if CANDIDATE else []) + [HERE]
for p in _PATH:                                                     # HERE last inserted = first searched
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)
import row19_shard as SH
import row19_screen_verify as V
import row19_ec2_state as ES                                        # REVISION 5: first, so every later import shares it (E2Q contracts)
import row19_ec2_e2rules as E2R
import row19_partition as RP
import row19_ec2_ingest as IG
import row19_ec2_e2qual as EQ
for p in _PATH:                                                     # the ingestion re-orders sys.path for itself; restore ours
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)

Q1_LENGAU = [(r, i) for r in range(3, 15) for i in (1, 2)]
CONTROLS = os.path.join(CHPC, "row19_screen_controls.json")
MODE = "canonical"                                        # tests alone set "sandbox"
PREDICTORS = None                                         # analyze.PREDICTORS unless a test sets it
CERT_SCHEMA = "row19-ec2-qualification-certificate-2"
REPLAY_SCOPE = ("ingestion-publication interruption on a relocated, re-bound sandbox copy of Q1's actual bundle, replay and "
                "second replay; NOT producer process/host restart, NOT interrupted-transfer recovery, NOT the canonical Mac ACK")
Q1_BLOCK = [(r, i) for i in (199, 198) for r in range(3, 27)]
Q2_REPEAT = [(r, 199) for r in range(3, 27)]
COVERAGE = {"R1": 18, "R2": 36, "R3": 18}
MEM_HOST_LIMIT_GIB, MEM_MIN_SAMPLES = 184.0, 10
CODE = ["chpc/row19_ec2_qualify.py", "chpc/row19_ec2_ingest.py", "chpc/row19_ec2_state.py", "chpc/row19_partition.py",
        "chpc/row19_ec2_root.py", "chpc/row19_ec2_shadow.py", "chpc/row19_shard.py", "chpc/row19_screen_verify.py",
        "aws_ec2/qual_S_plan.json", "chpc/row19_qual_S_manifest.json", "analyze.py", "models.py"]   # = prod_authority.RELEASE_CODE


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def load_bundle(man, inv, key, bundle, opp, psha, actsha, problems):
    att = inv["attempts"].get(key)
    if att is None or att.get("class") != "qualification" or att.get("state") != "reconciled":
        problems.append(f"{key}: not a reconciled qualification attempt in the inventory"); return {}, None
    opman = json.load(open(opp)); opsha = sha(opp)
    why = ES.operational_problem(opman, man, sha_manifest(man))
    if why or opman["ec2_production"]["contract"] != att["contract"]:
        problems.append(f"{key}: {why or 'operational manifest of another contract'}"); return {}, None
    p0 = len(problems)
    plan, _ = IG.check_bundle(bundle, att, (psha, opsha, actsha), problems)
    units = IG.plan_units(bundle, man, opman, opsha, att, plan, problems) if len(problems) == p0 else {}
    return units, plan


_MSHA = {}
def sha_manifest(man):
    return _MSHA["sha"]


def _preds():
    global PREDICTORS
    if PREDICTORS is None:
        import analyze
        PREDICTORS = list(analyze.PREDICTORS)
    return PREDICTORS


def finite_ok(rec, bands):
    """The procedure's usable predicate: not failed and every frozen predictor-band statistic finite."""
    import math
    if rec.get("failed"):
        return False
    try:
        return all(math.isfinite(float(rec["stats"][p][b])) for p in _preds() for b in bands)
    except (KeyError, TypeError, ValueError):
        return False


def compare(name, coords, mine, ref_of, problems, out, man=None):
    n_ok = failed_both = nonfinite_both = 0
    for c in coords:
        u = mine.get(c)
        if u is None:
            problems.append(f"{name} {c}: no validated record"); continue
        ref = ref_of(c)
        if ref is None:
            problems.append(f"{name} {c}: no reference record"); continue
        if V.payload(ref) != V.payload(u["rec"]):
            problems.append(f"{name} {c}: payload differs (float.hex, failed flag/reason included)"); continue
        bands = SH.task(man, c[0])["bands"]
        if u["rec"]["failed"] or ref["failed"]:
            failed_both += 1
        elif finite_ok(u["rec"], bands) and finite_ok(ref, bands):
            n_ok += 1
        else:
            nonfinite_both += 1
    out[name] = dict(coordinates=len(coords), successful_both=n_ok, failed_both=failed_both, nonfinite_both=nonfinite_both)


_UINT = re.compile(r"[0-9]+")                              # REVISION 6 (B2): an unsigned decimal integer, nothing else
_UDEC = re.compile(r"[0-9]+(\.[0-9]+)?")                   # an unsigned finite decimal (the /proc/loadavg fields)
MEM_KINDS, OCC_KINDS = "uuuu", "uuddd"                     # memory.txt: t MemTotal_kB MemAvailable_kB worker_rss_kB;
                                                           # occupancy.txt: t running_workers load1 load5 load15 (prod_userdata.sh)


def _timeline(p, width, kinds=None):
    """The rows of one producer timeline. REVISION 6 (B2): each field must be of its declared kind (`kinds`: u = unsigned
    integer, d = unsigned decimal) BEFORE any calculation, and time must be STRICTLY increasing - a repeated timestamp is the
    same observation, never a further producer sample (one sample per producer iteration, 60 s apart). Raises ValueError."""
    rows, prev = [], None
    for n, line in enumerate(open(p), 1):
        f = line.split()
        if len(f) != width:
            raise ValueError(f"line {n}: malformed line {line!r}")
        for x, k in zip(f, kinds or "u" + "?" * (width - 1)):
            if k == "u" and not _UINT.fullmatch(x) or k == "d" and not _UDEC.fullmatch(x):
                raise ValueError(f"line {n}: field {x!r} is not an unsigned {'integer' if k == 'u' else 'decimal'}")
        t = int(f[0])
        if prev is not None and t <= prev:
            raise ValueError(f"line {n}: time {'repeats' if t == prev else 'goes backwards'} at {line!r}: not a distinct ordered "
                             "producer sample")
        prev = t; rows.append(f)
    return rows


def resource_observation_problems(mem, occ, workers):
    """REVISION 6 (B2): the physical domains of every observation, checked before any calculation: MemTotal > 0, 0 <=
    MemAvailable <= MemTotal, worker RSS >= 0 (unsigned by kind), running workers within 0..`workers` (the producer counts
    declared processes not yet exited), load averages unsigned finite (by kind). [] when every observation is possible."""
    bad = []
    for f in mem:
        total, avail = int(f[1]), int(f[2])
        if total <= 0:
            bad.append(f"memory t={f[0]}: MemTotal {total} kB is not positive")
        elif not 0 <= avail <= total:
            bad.append(f"memory t={f[0]}: MemAvailable {avail} kB is outside [0, MemTotal {total} kB]")
    for o in occ:
        if not 0 <= int(o[1]) <= workers:
            bad.append(f"occupancy t={o[0]}: {o[1]} running workers outside 0..{workers}")
    return bad


def memory(bundle, problems, workers, label="Q1"):
    """R4 memory (R1-6): chronological samples joined to the occupancy line of the same producer iteration (<= 60 s apart);
    >= MEM_MIN_SAMPLES taken at the full planned packing (`workers` running); peak host use <= the limit over ALL samples.
    REVISION 5: `label` names the attempt in the problem text (E2Q1 / E2Q2 for R4'); the rule is unchanged.
    REVISION 6 (B2): every field is validated by kind and physical domain BEFORE any calculation (a malformed or impossible
    observation is a failed evidence verdict, never an exception and never a release); the timelines must be strictly
    increasing; each occupancy line joins at most one memory sample, so the >= MEM_MIN_SAMPLES qualifying observations are
    distinct ordered producer samples; the occupancy match, the peak over ALL samples, the 184 GiB ceiling and the
    produced-worker status limits are unchanged."""
    try:
        mem = _timeline(os.path.join(bundle, "env", "memory.txt"), 4, MEM_KINDS)
        occ = _timeline(os.path.join(bundle, "env", "occupancy.txt"), 5, OCC_KINDS)
    except Exception as e:
        problems.append(f"{label} memory/occupancy timeline unreadable or invalid ({e})"); return None
    bad = resource_observation_problems(mem, occ, workers)
    if bad:
        problems.append(f"{label} memory/occupancy observations are physically impossible ({len(bad)}): {bad[:3]}")
        return dict(valid=False, invalid_observations=bad[:10], samples=len(mem), workers=workers, limit_gib=MEM_HOST_LIMIT_GIB)
    import bisect
    ot = [int(o[0]) for o in occ]
    peak = peak_full = worker_rss_peak = 0.0; full = unmatched = 0; joined = set()
    for f in mem:
        t, used = int(f[0]), (int(f[1]) - int(f[2])) / 2 ** 20
        peak = max(peak, used); worker_rss_peak = max(worker_rss_peak, int(f[3]) / 2 ** 20)
        k = bisect.bisect_right(ot, t) - 1
        if k < 0 or t - ot[k] > 60 or k in joined:                 # REVISION 6: one occupancy line, one memory sample
            unmatched += 1; continue
        joined.add(k)
        if int(occ[k][1]) == workers:
            full += 1; peak_full = max(peak_full, used)
    if full < MEM_MIN_SAMPLES or peak > MEM_HOST_LIMIT_GIB:
        problems.append(f"{label} memory gate: {full} samples at the full {workers}-worker packing (need >= {MEM_MIN_SAMPLES}), "
                        f"peak host use {peak:.1f} GiB (limit {MEM_HOST_LIMIT_GIB})")
    return dict(samples=len(mem), samples_at_full_packing=full, unmatched_samples=unmatched, workers=workers,
                peak_host_used_gib=peak, peak_at_full_packing_gib=peak_full, peak_worker_rss_gib=worker_rss_peak, limit_gib=MEM_HOST_LIMIT_GIB)


def s_declaration(ctl):
    q = ((ctl or {}).get("versions") or [{}])[-1].get("qualification_S")
    return q if isinstance(q, dict) else None


def s_evidence(man, sman_path, problems, ctl=None):
    """R1-4/R2-4: S's producer evidence (see the module text), for THE declared S campaign only. Returns (references
    {(rep, index): record}, report, bound)."""
    import row19_ec2_shadow as SHD
    sman = json.load(open(sman_path)); why = ES.isolated_S_problem(sman, man, sha_manifest(man))
    if why:
        problems.append(f"S: {why}"); return {}, None, None
    root, camp = sman["storage"]["root"], sman["storage"]["campaign"]
    decl = s_declaration(ctl)
    if decl is None:
        problems.append("S: the current controls declare no qualification_S"); return {}, None, None
    if (decl.get("root"), decl.get("campaign")) != (root, camp) or decl.get("manifest_sha256") != sha(sman_path) \
            or decl.get("plan_sha256") != sha(SHD.S_PLAN):
        problems.append("S: the supplied S manifest/root/campaign/plan are not the ones the current controls declare"); return {}, None, None
    mem_stop = float(sman["pbs"].get("mem_stop_gib", 0) or 0) * 2 ** 30
    refs, rep, statuses, timings, bindings = {}, {}, {}, {}, {}
    try:
        led = json.load(open(os.path.join(camp, "budget.json")))
    except Exception as e:
        problems.append(f"S: the isolated campaign ledger is unreadable ({type(e).__name__})"); return {}, None, None
    entries = list(led.get("entries", {}).values())
    if any(e.get("kind") != "shard" or e.get("rep") not in (1, 2) for e in entries):
        problems.append("S: the isolated ledger holds an entry that is not kind shard for job 1 or 2")
    plans = sorted(f for f in os.listdir(os.path.join(root, "plans")) if f.startswith("job_")) if os.path.isdir(os.path.join(root, "plans")) else []
    if plans != ["job_1.json", "job_2.json"]:
        problems.append(f"S: the isolated root holds plans {plans}, not exactly job_1/job_2")
    for n in (1, 2):
        want = SHD.s_job(n)
        try:
            got = json.load(open(os.path.join(root, "plans", f"job_{n}.json")))
        except Exception:
            problems.append(f"S job {n}: no plan"); continue
        if any(got.get(k) != want[k] for k in ("job", "label", "role", "s_plan_sha256", "slots")):
            problems.append(f"S job {n}: the plan is not the declared fixed plan"); continue
        mine = [e for e in entries if e.get("rep") == n]
        prod_e = [e for e in mine if e.get("state") == "settled" and e.get("job_id") and e.get("token") == got.get("token")]
        if len(prod_e) != 1 or not isinstance(prod_e[0].get("settled_core_h"), (int, float)) or not 0 <= prod_e[0]["settled_core_h"] < float("inf"):
            problems.append(f"S job {n}: no single settled producing entry with a bound PBS id and finite charge"); continue
        jid = prod_e[0]["job_id"]
        rep[str(n)] = dict(label=want["label"], job_id=jid, attempts=len(mine), settled_core_h=prod_e[0]["settled_core_h"],
                           reserved_core_h=sum(float(e["reserved_core_h"]) for e in mine))
        for sl in want["slots"]:
            r, i = sl["rep"], sl["indices"][0]
            sp = os.path.join(root, "status", f"job{jid}.slot{sl['slot']}.json")
            try:
                why = ES.status_problem(json.load(open(sp)), jid, sl["slot"], r, i, SH.task(man, r)["ident"], mem_stop)
                statuses[os.path.relpath(sp, root)] = sha(sp)
            except Exception as e:
                why = f"status missing or unreadable ({type(e).__name__})"
            if why:
                problems.append(f"S job {n} slot {sl['slot']} ({r}, {i}): {why}"); continue
            try:
                rec = SH.read_record(SH.record_path(root, r, i), SH.task(man, r), i)
                why = V.timing_ok(json.load(open(SH.timing_path(root, r, i))), rep=r, index=i, ident=SH.task(man, r)["ident"], job=jid, slot=sl["slot"])
            except Exception as e:
                rec, why = None, f"record/timing unreadable ({type(e).__name__}: {e})"
            if rec is None or why:
                problems.append(f"S job {n} ({r}, {i}): {why or 'no record'}"); continue
            timings[f"{r}/{i}"] = sha(SH.timing_path(root, r, i))
            if r not in bindings:
                tp = os.path.join(root, f"task_{r}.json")
                try:
                    got_b = json.load(open(tp))["binding"]
                    want_b = json.loads(json.dumps(SH.binding_for(sman, sha(sman_path), root, r, SH.task(sman, r)), default=str))
                    if got_b != want_b:
                        raise ValueError("not the binding row19_shard.binding_for gives under the S manifest")
                    bindings[r] = sha(tp)
                except Exception as e:
                    problems.append(f"S job {n}: task binding task_{r}.json ({type(e).__name__}: {e})"); continue
            refs[(r, i)] = rec
    bound = dict(manifest_sha256=sha(sman_path), ledger_sha256=sha(os.path.join(camp, "budget.json")),
                 plans={p_: sha(os.path.join(root, "plans", p_)) for p_ in plans},
                 statuses_sha256=hashlib.sha256(json.dumps(sorted(statuses.items())).encode()).hexdigest(),
                 timings_sha256=hashlib.sha256(json.dumps(sorted(timings.items())).encode()).hexdigest(),
                 task_bindings_sha256=hashlib.sha256(json.dumps(sorted((str(k), v) for k, v in bindings.items())).encode()).hexdigest(),
                 producer_entries_sha256=hashlib.sha256(json.dumps(sorted(
                     [dict(token=e.get("token"), rep=e.get("rep"), job_id=e.get("job_id"), state=e.get("state"),
                           reserved_core_h=e.get("reserved_core_h"), settled_core_h=e.get("settled_core_h")) for e in entries],
                     key=lambda x: str(x["token"]))).encode()).hexdigest(),
                 declaration_sha256=hashlib.sha256(ES.canonical(decl)).hexdigest(),
                 provenance="cooperative: written by the unchanged worker and the S admission; bound, not signed",
                 records_sha256=hashlib.sha256(json.dumps(sorted((f"{r}/{i}", sha(SH.record_path(root, r, i))) for r, i in refs)).encode()).hexdigest())
    return refs, rep, bound


def sandbox_replay(man, part_doc, inv, key, bundle, opp, sandbox, problems):
    """R5 on the actual bundle: a sandbox root holding only the Lengau records Q1 compares with, the same partition
    (k, epoch) under the sandbox manifest, a sandbox controls pin and activation, and an inventory listing Q1 released
    (sealed here, sandbox only). Forced stop after the first published pair, replay, second replay."""
    if part_doc.get("schema") == RP.SCHEMA2:
        problems.append("R5 for a schema-2 epoch is the epoch-2 R5' (`row19_ec2_qualify.py e2`, sandbox_replay_e2), not this panel's")
        return dict(scope=REPLAY_SCOPE, final_state=None, hashes_equal=False)
    shutil.rmtree(sandbox, ignore_errors=True); root = os.path.join(sandbox, "root"); os.makedirs(os.path.join(root, "plans"))
    att = inv["attempts"][key]
    for r, i in [tuple(c) for c in att["sentinels"] + att["duplicates"]]:
        for src, dst in ((SH.record_path(man["storage"]["root"], r, i), SH.record_path(root, r, i)),
                         (SH.timing_path(man["storage"]["root"], r, i), SH.timing_path(root, r, i))):
            os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst)
    sm = copy.deepcopy(man); sm["storage"] = {"root": root, "campaign": os.path.join(sandbox, "camp")}
    mp = os.path.join(sandbox, "manifest.json"); json.dump(sm, open(mp, "w")); msha = sha(mp)
    pred = part_doc["predecessor"]
    sp = RP.declare(sm, msha, part_doc["k"], part_doc["epoch"], pred); pp = os.path.join(sandbox, "partition.json"); json.dump(sp, open(pp, "w"))
    cp = os.path.join(sandbox, "controls.json"); json.dump({"versions": [{"version": 0, "partition": {"sha256": sha(pp)}}]}, open(cp, "w"))
    proof, why = RP.activate(sm, mp, pp, cp, mode="sandbox")
    os.makedirs(os.path.join(root, "ec2"), exist_ok=True); json.dump(proof, open(RP.activation_path(sm, sp["epoch"]), "w"))
    opman = json.load(open(opp)); e = opman["ec2_production"]
    sop = ES.derive_operational(sm, msha, e["epoch"], e["expect_s"], e["contract"]); sopp = os.path.join(sandbox, "op.json"); json.dump(sop, open(sopp, "w"))
    # the bundle's plan is bound to the PRODUCTION partition/opmanifest/activation: re-bind a sandbox copy of the bundle
    sb = os.path.join(sandbox, "bundle"); shutil.copytree(bundle, sb)
    plan = json.load(open(os.path.join(sb, "env", "plan.json")))
    plan.update(partition_sha256=sha(pp), opmanifest_sha256=sha(sopp), activation_sha256=sha(RP.activation_path(sm, sp["epoch"])))
    json.dump(plan, open(os.path.join(sb, "env", "plan.json"), "w"))
    for r in {s["rep"] for s in plan["slots"]}:
        tp = os.path.join(sb, "root", f"task_{r}.json")
        if os.path.exists(tp):
            json.dump(dict(binding=SH.binding_for(sop, sha(sopp), sop["storage"]["root"], r, SH.task(sm, r))), open(tp, "w"), default=str)
    lines = []
    for p in sorted(glob.glob(os.path.join(sb, "**", "*"), recursive=True)):
        rel = os.path.relpath(p, sb)
        if os.path.isfile(p) and rel.split(os.sep)[0] in ("root", "env") and rel not in IG.MUTABLE:
            lines.append(f"{sha(p)}  {rel}\n")
    open(os.path.join(sb, "BUNDLE_SHA256SUMS"), "w").write("".join(lines))
    sa = dict(att, plan_sha256=sha(os.path.join(sb, "env", "plan.json")))
    sinv = ES.seal(dict(ES.inventory_body(inv), attempts=dict(inv["attempts"], **{key: sa}), at=time.time(),
                        release=dict(production_released=True, released_attempts=[key])))
    ip = os.path.join(sandbox, "inventory.json"); json.dump(sinv, open(ip, "w"))
    _, why_inst = ES.install_inventory(root, sinv, dict(root=os.path.abspath(root), manifest_sha256=msha, mode="sandbox"))
    why = list(why) + list(why_inst)
    args = ["--manifest", mp, "--partition", pp, "--opmanifest", sopp, "--authority", ip, "--attempt-key", key, "--bundle", sb]
    old_ctl, real, old_mode = IG.CONTROLS, IG.publish_copy, IG.ACTIVATION_MODE
    IG.CONTROLS = cp; IG.ACTIVATION_MODE = "sandbox"; n = {"k": 0}
    def flaky(src, dst, want):
        n["k"] += 1
        if n["k"] == 3:
            raise ValueError("forced stop after the first published pair")
        return real(src, dst, want)
    def entry():
        rp = ES.paths(root)["register"]
        return json.load(open(rp))["attempts"].get(att["attempt_id"]) if os.path.exists(rp) else None
    try:
        IG.publish_copy = flaky; rc1 = IG.main(args); IG.publish_copy = real
        st1 = (entry() or {}).get("state")
        rc2 = IG.main(args); rc3 = IG.main(args)
        e2 = entry()
        bad = IG.replay_problems(root, e2, sa["plan_sha256"], key) if e2 else ["no register entry"]
    finally:
        IG.publish_copy = real; IG.CONTROLS = old_ctl; IG.ACTIVATION_MODE = old_mode
    rep = dict(scope=REPLAY_SCOPE, forced_stop_rc=rc1, state_after_stop=st1, replay_rc=rc2, second_replay_rc=rc3,
               final_state=(e2 or {}).get("state"), hashes_equal=not bad, activation_problems=why)
    if not (rc1 == 3 and st1 == "ingesting" and rc2 == 0 and rc3 == 0 and e2["state"] == "ingested" and not bad and not why):
        problems.append(f"R5 sandbox replay failed: {rep}")
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser()
    for k in ("--manifest", "--partition", "--authority", "--q1-key", "--q1-bundle", "--q1-opmanifest", "--q2-key", "--q2-bundle",
              "--q2-opmanifest", "--s-manifest", "--sandbox", "--out"):
        ap.add_argument(k, required=True)
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); _MSHA["sha"] = msha = sha(a.manifest)
    part = RP.load(a.partition, man, msha); psha = sha(a.partition)
    actp = RP.activation_path(man, part["epoch"]); actsha = sha(actp) if os.path.exists(actp) else None
    inv = json.load(open(a.authority)); problems = []
    if part.get("schema") == RP.SCHEMA2:
        problems.append(f"partition epoch {part['epoch']} is a schema-2 (explicit coordinate set) epoch: the predeclared Q1/Q2/S panel "
                        "qualifies epoch 1 only; epoch 2 is qualified by `row19_ec2_qualify.py e2` (the QUALIFICATION_E2.md panel, schema-3 certificate)")
    why = ES.inventory_problem(inv)
    if why:
        problems.append(f"inventory: {why}")
    if MODE == "canonical":
        ctl, why = RP.adopted_controls(CONTROLS)
        if why:
            problems.append(f"controls: {why}")
    else:
        ctl = json.load(open(CONTROLS))
    if actsha is None:
        problems.append("the partition has no activation proof")
    elif ctl is not None:
        why = RP.activation_problem(man, msha, part, psha, json.load(open(actp)), controls=ctl, mode=MODE)
        if why:
            problems.append(f"activation: {why}")
    q1, plan1 = load_bundle(man, inv, a.q1_key, a.q1_bundle, a.q1_opmanifest, psha, actsha, problems) if not problems else ({}, None)
    q2, plan2 = load_bundle(man, inv, a.q2_key, a.q2_bundle, a.q2_opmanifest, psha, actsha, problems) if not problems else ({}, None)
    parts, mem, rep, srep, sbound = {}, None, None, None, None
    sref = {}
    if not problems:
        sref, srep, sbound = s_evidence(man, a.s_manifest, problems, ctl)
    if not problems:
        if sorted(c for c, u in q1.items() if u["role"] == "qual_lengau") != sorted(Q1_LENGAU) or \
           sorted(c for c, u in q1.items() if u["role"] == "work") != sorted(Q1_BLOCK) or sorted(q2) != sorted(Q2_REPEAT):
            problems.append("the bundles are not the predeclared panel")
    if not problems:
        def lengau(c):
            return SH.read_record(SH.record_path(man["storage"]["root"], *c), SH.task(man, c[0]), c[1])
        shadow = sref.get
        compare("R1", Q1_LENGAU, q1, lengau, problems, parts, man)
        compare("R2", Q1_BLOCK, q1, shadow, problems, parts, man)
        compare("R3_vs_Q1", Q2_REPEAT, q2, lambda c: q1[c]["rec"], problems, parts, man)
        compare("R3", Q2_REPEAT, q2, shadow, problems, parts, man)
        compare("R4_sentinels", sorted(c for c, u in q1.items() if u["role"] == "sentinel"), q1, lengau, problems, parts, man)
        mem = memory(a.q1_bundle, problems, len(plan1["slots"]))
        rep = sandbox_replay(man, part, inv, a.q1_key, a.q1_bundle, a.q1_opmanifest, a.sandbox, problems)
    short = {k: (parts.get(k) or {}).get("successful_both", 0) for k in COVERAGE if (parts.get(k) or {}).get("successful_both", 0) < COVERAGE[k]}
    outcome = "NO_RELEASE" if problems else ("INCONCLUSIVE" if short else "RELEASE")
    cert = dict(schema=CERT_SCHEMA, outcome=outcome, problems=problems, coverage_required=COVERAGE,
                coverage_short=short, parts=parts, memory=mem, replay=rep, s=srep, released_attempts=[a.q1_key] if outcome == "RELEASE" else [],
                q1=dict(key=a.q1_key, attempt_id=(inv["attempts"].get(a.q1_key) or {}).get("attempt_id"),
                        plan_sha256=(inv["attempts"].get(a.q1_key) or {}).get("plan_sha256"),
                        sequence=(inv["attempts"].get(a.q1_key) or {}).get("sequence")),
                actual_result_review_required=True,
                bound=dict(code={f: sha(os.path.join(T1, f)) for f in CODE if os.path.exists(os.path.join(T1, f))}, manifest_sha256=msha,
                           partition_sha256=psha, activation_sha256=actsha, inventory_sha256=inv.get("sha256"),
                           opmanifests={k: sha(p) for k, p in (("Q1", a.q1_opmanifest), ("Q2", a.q2_opmanifest))},
                           bundles={k: sha(os.path.join(b, "BUNDLE_SHA256SUMS")) if os.path.exists(os.path.join(b, "BUNDLE_SHA256SUMS")) else None
                                    for k, b in (("Q1", a.q1_bundle), ("Q2", a.q2_bundle))},
                           plans={k: sha(os.path.join(b, "env", "plan.json")) if os.path.exists(os.path.join(b, "env", "plan.json")) else None
                                  for k, b in (("Q1", a.q1_bundle), ("Q2", a.q2_bundle))},
                           s=sbound), at=time.time())
    json.dump(cert, open(a.out, "w"), indent=1, sort_keys=True)
    print(json.dumps(dict(outcome=outcome, parts=parts, coverage_short=short, memory=mem, s=srep, problems=problems[:10]), indent=1))
    return 0 if outcome == "RELEASE" else 3


# ---- REVISION 5: the epoch-2 qualification (QUALIFICATION_E2.md s.2-s.3), schema-3 certificate --------------------------------

def code_bound(problems):
    """{promoted path: sha256} of EQ.CODE resolved to the files this run actually uses (candidate copies before promotion), and
    a problem when a loaded module is not the bound file."""
    out = {}
    for rel in EQ.CODE:
        p = EQ.code_path(T1, rel, CANDIDATE)
        if not os.path.isfile(p):
            problems.append(f"code: {rel} is absent ({p})"); continue
        out[rel] = sha(p)
    loaded = {"chpc/row19_ec2_qualify.py": __file__, "chpc/row19_ec2_ingest.py": IG, "chpc/row19_ec2_state.py": ES,
              "chpc/row19_partition.py": RP, "chpc/row19_ec2_e2rules.py": E2R, "chpc/row19_ec2_e2qual.py": EQ,
              "chpc/row19_shard.py": SH, "chpc/row19_screen_verify.py": V}
    for rel, m in loaded.items():
        f = m if isinstance(m, str) else getattr(m, "__file__", None)
        if f is not None and os.path.abspath(f) != os.path.abspath(EQ.code_path(T1, rel, CANDIDATE)):
            problems.append(f"code: the loaded {rel} is {f}, not the bound file {EQ.code_path(T1, rel, CANDIDATE)}")
    return out


def compare_e2(name, coords, units, unproduced, ref_of, problems, out, man, strict=True):
    """Float-bit comparison of the PRODUCED coordinates in `coords`; an unproduced coordinate (a qualifying non-completion,
    already bounded by R4') is reported and never compared, never counted and never given a record."""
    n_ok = failed_both = nonfinite_both = 0; skipped = []
    for c in coords:
        if c in unproduced:
            skipped.append(list(c)); continue
        u = units.get(c)
        if u is None:
            problems.append(f"{name} {c}: no validated record"); continue
        ref = ref_of(c)
        if ref is None:
            problems.append(f"{name} {c}: no reference record"); continue
        if V.payload(ref) != V.payload(u["rec"]):
            problems.append(f"{name} {c}: payload differs (float.hex, failed flag/reason included)"); continue
        bands = SH.task(man, c[0])["bands"]
        if u["rec"]["failed"] or ref["failed"]:
            failed_both += 1
        elif finite_ok(u["rec"], bands) and finite_ok(ref, bands):
            n_ok += 1
        else:
            nonfinite_both += 1
    out[name] = dict(coordinates=len(coords), compared=len(coords) - len(skipped), unproduced=skipped, successful_both=n_ok,
                     failed_both=failed_both, nonfinite_both=nonfinite_both)


def _put_json(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        json.dump(obj, f)


def _sums(b):
    lines = []
    for p in sorted(glob.glob(os.path.join(b, "**", "*"), recursive=True)):
        rel = os.path.relpath(p, b)
        if os.path.isfile(p) and rel.split(os.sep)[0] in ("root", "env") and rel not in IG.MUTABLE:
            lines.append(f"{sha(p)}  {rel}\n")
    open(os.path.join(b, "BUNDLE_SHA256SUMS"), "w").write("".join(lines))


def _sandbox_world(man, part, att, real_root, d, problems, base_designated=None):
    """A sandbox screen root under an ACTIVATED sandbox schema-2 epoch 2 whose predecessor (a sandbox re-declaration of the
    real epoch-1 block) is activated there first: the Lengau records of the attempt's sentinels and duplicates are copied in,
    the bound designated declaration is re-bound to the sandbox manifest, the claims snapshot is taken of the sandbox root,
    and the epoch is declared from them (declare2), so the attempt's work coordinates are owned exactly as in the real epoch."""
    shutil.rmtree(d, ignore_errors=True)
    root, camp = os.path.join(d, "root"), os.path.join(d, "camp")
    os.makedirs(os.path.join(root, "plans")); os.makedirs(camp)
    _put_json(os.path.join(camp, "budget.json"), {"entries": {}})
    for r, i in sorted({tuple(c) for c in att["sentinels"] + att["duplicates"]}):
        for src, dst in ((SH.record_path(real_root, r, i), SH.record_path(root, r, i)),
                         (SH.timing_path(real_root, r, i), SH.timing_path(root, r, i))):
            if os.path.exists(src):
                os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst)
    sm = copy.deepcopy(man); sm["storage"] = {"root": root, "campaign": camp}
    mp = os.path.join(d, "manifest.json"); _put_json(mp, sm); msha = sha(mp)
    RP.DESIGNATED_PATH = base_designated                             # the REAL bound declaration (the caller's setting)
    desig, _ = RP.designated_doc(part)
    dp = os.path.join(d, "designated.json"); _put_json(dp, dict(desig, manifest_sha256=msha))
    RP.DESIGNATED_PATH = dp                                          # this sandbox's re-bound copy; the caller restores it
    pred = part["predecessor"]
    if pred.get("schema") != RP.SCHEMA or int(pred.get("epoch", 0)) != 1:
        problems.append("R5': the sandbox re-declares only an epoch-1 (schema-1) predecessor"); return None
    k = int(pred["coordinates"]) // len(man["datasets"]["reps"])
    e1 = RP.declare(sm, msha, k, 1); e1p = os.path.join(d, "partition_e1.json"); _put_json(e1p, e1)
    cp = os.path.join(d, "controls.json")
    _put_json(cp, {"versions": [{"version": 1, "partition": {"path": "sandbox/e1", "sha256": sha(e1p)}}]})
    proof1, why1 = RP.activate(sm, mp, e1p, cp, mode="sandbox"); _put_json(RP.activation_path(sm, 1), proof1)
    ident = dict(root=os.path.abspath(root), manifest_sha256=msha, mode="sandbox")
    empty = ES.seal(dict(schema=ES.INVENTORY_SCHEMA, generation=1, at=time.time(), attempts={}, owners={}, fence={},
                         release=dict(production_released=False, released_attempts=[]), usd={}))
    _, why_i = ES.install_inventory(root, empty, ident)
    snap = RP.claims_snapshot(sm, msha, {"sandbox": "E2Q R5'"}); sp = os.path.join(d, "claims_snapshot.json"); _put_json(sp, snap)
    e2 = RP.declare2(sm, msha, json.load(open(dp)), sha(dp), snap, sha(sp), e1, sha(e1p), 2)
    pp = os.path.join(d, "partition_e2.json"); _put_json(pp, e2)
    _put_json(cp, {"versions": [{"version": 1, "partition": {"path": "sandbox/e1", "sha256": sha(e1p)}},
                                {"version": 2, "partition": {"path": "sandbox/e2", "sha256": sha(pp)}}]})
    proof2, why2 = RP.activate(sm, mp, pp, cp, mode="sandbox"); _put_json(RP.activation_path(sm, 2), proof2)
    off = [c for c in att["coordinates"] if not RP.blocked(e2, *c)]
    why = list(why1) + list(why_i) + list(why2) + ([f"{len(off)} work coordinate(s) are not owned by the sandbox epoch"] if off else [])
    return dict(d=d, root=root, man=sm, mp=mp, msha=msha, pp=pp, cp=cp, e2=e2, ident=ident, why=why, dp=dp)


def _rebind(w, bundle, att, contract, expect_s, dst):
    """A copy of `bundle` re-bound to the sandbox world (plan bindings, EC2 task bindings, checksums). Returns its plan sha."""
    sop = ES.derive_operational(w["man"], w["msha"], 2, expect_s, contract)
    sopp = os.path.join(w["d"], "op.json"); _put_json(sopp, sop); w["opp"] = sopp
    shutil.rmtree(dst, ignore_errors=True); shutil.copytree(bundle, dst)
    pl = json.load(open(os.path.join(dst, "env", "plan.json")))
    pl.update(partition_sha256=sha(w["pp"]), opmanifest_sha256=sha(sopp), activation_sha256=sha(RP.activation_path(w["man"], 2)))
    _put_json(os.path.join(dst, "env", "plan.json"), pl)
    for r in {s["rep"] for s in pl["slots"]}:
        tp = os.path.join(dst, "root", f"task_{r}.json")
        if os.path.exists(tp):
            with open(tp, "w") as f:
                json.dump(dict(binding=SH.binding_for(sop, sha(sopp), sop["storage"]["root"], r, SH.task(w["man"], r))), f, default=str)
    _sums(dst)
    return sha(os.path.join(dst, "env", "plan.json"))


def _install_attempt(w, key, att, plan_sha, generation):
    """Install a sandbox inventory carrying the attempt deliberately as class PRODUCTION (R5', ruling 12)."""
    sa = dict(att, plan_sha256=plan_sha, state="reconciled", ingestion="pending", disposition_requested=False, **{"class": "production"})
    owners = {f"{c[0]}/{c[1]}": [key, sa["sequence"]] for c in sorted(map(tuple, sa["coordinates"]))}
    inv = ES.seal(dict(schema=ES.INVENTORY_SCHEMA, generation=generation, at=time.time(), attempts={key: sa}, owners=owners,
                       fence={k: sa["sequence"] for k in owners}, release=dict(production_released=False, released_attempts=[]), usd={}))
    ip = os.path.join(w["d"], f"inventory_g{generation}.json"); _put_json(ip, inv)
    _, why = ES.install_inventory(w["root"], inv, w["ident"])
    return sa, ip, list(why)


def _ingest(w, ip, key, b):
    RP.DESIGNATED_PATH = w["dp"]; IG.CONTROLS = w["cp"]                 # each sandbox world reads its own bindings
    return IG.main(["--manifest", w["mp"], "--partition", w["pp"], "--opmanifest", w["opp"], "--authority", ip, "--attempt-key", key, "--bundle", b])


def _entry(w, aid):
    rp = ES.paths(w["root"])["register"]
    reg = json.load(open(rp)) if os.path.exists(rp) else None
    return ((reg or {}).get("attempts") or {}).get(aid), reg


def sandbox_replay_e2(man, part, inv, key, bundle, sandbox, unprod, plan, problems, expect_s=EQ.EXPECT_S):
    """R5' (QUALIFICATION_E2.md s.3 item 5, ruling 12) on the ACTUAL bundle. See the module text, REVISION 5."""
    att = inv["attempts"][key]; contract = att["contract"]; real_root = man["storage"]["root"]
    old = (IG.CONTROLS, IG.publish_copy, IG.ACTIVATION_MODE, RP.DESIGNATED_PATH)
    rep = dict(scope=EQ.REPLAY_SCOPE, presented_class="production", final_state=None, hashes_equal=False)
    by = {int(s["slot"]): s for s in plan["slots"]}
    try:
        shutil.rmtree(sandbox, ignore_errors=True); os.makedirs(sandbox)
        wa = _sandbox_world(man, part, att, real_root, os.path.join(sandbox, "A"), problems, old[3])
        if wa is None:
            return rep
        ba = os.path.join(sandbox, "A", "bundle"); plan_a = _rebind(wa, bundle, att, contract, expect_s, ba)
        sa, ipa, why_a = _install_attempt(wa, key, att, plan_a, 2)
        IG.CONTROLS = wa["cp"]; IG.ACTIVATION_MODE = "sandbox"; real, n = IG.publish_copy, {"k": 0}
        def flaky(src, dst, want):
            n["k"] += 1
            if n["k"] == 3:
                raise ValueError("forced stop after the first published pair")
            return real(src, dst, want)
        IG.publish_copy = flaky; rc1 = _ingest(wa, ipa, key, ba); IG.publish_copy = real
        st1 = (_entry(wa, att["attempt_id"])[0] or {}).get("state")
        rc2 = _ingest(wa, ipa, key, ba); rc3 = _ingest(wa, ipa, key, ba)
        ea, rega = _entry(wa, att["attempt_id"])
        unp_work = {f"{int(by[sl]['rep'])}/{int(by[sl]['indices'][0])}": dict(slot=sl, outcome=oc)
                    for sl, oc in sorted(unprod.items()) if by[sl]["role"] == "work"}
        ev = IG.failure_evidence(ba, sa, json.load(open(os.path.join(ba, "env", "plan.json"))), unprod, unp_work)
        bad = IG.replay_problems(wa["root"], ea, sa["plan_sha256"], key, rega, ev) if ea else ["no register entry"]
        rep.update(forced_stop_rc=rc1, state_after_stop=st1, replay_rc=rc2, second_replay_rc=rc3, final_state=(ea or {}).get("state"),
                   hashes_equal=not bad, activation_problems=wa["why"] + why_a, replay_problems=bad[:5])
        if not (rc1 == 3 and st1 == "ingesting" and rc2 == 0 and rc3 == 0 and (ea or {}).get("state") == "ingested" and not bad
                and not wa["why"] and not why_a):
            problems.append(f"R5' sandbox replay failed: { {k: rep[k] for k in ('forced_stop_rc', 'state_after_stop', 'replay_rc', 'second_replay_rc', 'final_state', 'hashes_equal')} }"
                            f" {(wa['why'] + why_a + bad)[:3]}")
            return rep
        work_un = sorted(sl for sl in unprod if by[sl]["role"] == "work")
        if work_un:                                                  # the actual per-slot case, exercised as it is
            sl = work_un[0]; ck = f"{int(by[sl]['rep'])}/{int(by[sl]['indices'][0])}"
            ps = dict(mode="actual", slot=sl, coordinate=ck, outcome=unprod[sl],
                      listed=(ea.get("unproduced") or {}).get(ck) == dict(slot=sl, outcome=unprod[sl]),
                      fenced=rega["fence"].get(ck, -1) >= sa["sequence"], evidence_journaled=ea.get("failure_evidence") == ev,
                      ack_problem=EQ.ack_problem(ea, sa["coordinates"]), synthetic=[])
        else:                                                        # one CONSISTENT synthetic fatal-signal non-completion
            sl = min(s for s, x in by.items() if x["role"] == "work"); r, i = int(by[sl]["rep"]), int(by[sl]["indices"][0]); ck = f"{r}/{i}"
            wb = _sandbox_world(man, part, att, real_root, os.path.join(sandbox, "B"), problems, old[3])
            if wb is None:
                return rep
            bb = os.path.join(sandbox, "B", "bundle"); plan_b = _rebind(wb, bundle, att, contract, expect_s, bb)
            orig = {rel: sha(os.path.join(bb, rel)) for rel in ("env/outcomes.json", "BUNDLE_SHA256SUMS")}
            gone = {os.path.relpath(p, bb): p for p in (SH.record_path(os.path.join(bb, "root"), r, i), SH.timing_path(os.path.join(bb, "root"), r, i),
                                                         os.path.join(bb, "root", "status", f"job{att['attempt_id']}.slot{sl}.json"))}
            synth = [dict(file=rel, original_sha256=sha(p) if os.path.exists(p) else None, modified_sha256=None, label="SYNTHETIC: removed")
                     for rel, p in sorted(gone.items())]
            for p in gone.values():
                if os.path.exists(p):
                    os.remove(p)
            op = os.path.join(bb, "env", "outcomes.json"); o = json.load(open(op)); o["outcomes"][f"w_slot{sl}"] = 139; _put_json(op, o)
            _sums(bb)
            synth += [dict(file=rel, original_sha256=orig[rel], modified_sha256=sha(os.path.join(bb, rel)),
                           label="SYNTHETIC: outcome set to fatal signal 139" if rel.endswith("outcomes.json") else "SYNTHETIC: checksums regenerated")
                      for rel in sorted(orig)]
            sb_, ipb, why_b = _install_attempt(wb, key, att, plan_b, 2)
            IG.CONTROLS = wb["cp"]; rcb = _ingest(wb, ipb, key, bb)
            eb, regb = _entry(wb, att["attempt_id"])
            un_b = dict(unprod); un_b[sl] = 139                         # any actual non-work non-completions stay as they are
            ev_b = IG.failure_evidence(bb, sb_, json.load(open(os.path.join(bb, "env", "plan.json"))), un_b, {ck: dict(slot=sl, outcome=139)})
            # the modified bundle against the UNMODIFIED journal (sandbox A) must HOLD: re-bind a copy to world A
            IG.CONTROLS = wa["cp"]; bm = os.path.join(sandbox, "A", "bundle_modified"); _rebind(wa, bundle, att, contract, expect_s, bm)
            for p in (SH.record_path(os.path.join(bm, "root"), r, i), SH.timing_path(os.path.join(bm, "root"), r, i),
                      os.path.join(bm, "root", "status", f"job{att['attempt_id']}.slot{sl}.json")):
                if os.path.exists(p):
                    os.remove(p)
            op = os.path.join(bm, "env", "outcomes.json"); o = json.load(open(op)); o["outcomes"][f"w_slot{sl}"] = 139; _put_json(op, o); _sums(bm)
            rc_mod = _ingest(wa, ipa, key, bm)
            ps = dict(mode="synthetic", slot=sl, coordinate=ck, outcome=139, ingest_rc=rcb,
                      listed=(eb or {}).get("unproduced") == {ck: dict(slot=sl, outcome=139)},
                      fenced=bool(regb) and regb["fence"].get(ck, -1) >= sb_["sequence"],
                      evidence_journaled=(eb or {}).get("failure_evidence") == ev_b,
                      ack_problem=EQ.ack_problem(eb, sb_["coordinates"]) if eb else "no register entry",
                      modified_replay_rc=rc_mod, modified_replay_held=rc_mod == 3 and os.path.exists(ES.paths(wa["root"])["hold"]),
                      activation_problems=wb["why"] + why_b, synthetic=synth)
        rep["per_slot"] = ps
        ok = ps["listed"] and ps["fenced"] and ps["evidence_journaled"] and ps["ack_problem"] == "" and \
            (ps["mode"] == "actual" or (ps["ingest_rc"] == 0 and ps["modified_replay_held"] and not ps["activation_problems"]))
        if not ok:
            problems.append(f"R5' per-slot branch failed: { {k: v for k, v in ps.items() if k != 'synthetic'} }")
        return rep
    finally:
        IG.CONTROLS, IG.publish_copy, IG.ACTIVATION_MODE, RP.DESIGNATED_PATH = old


def main_e2(argv=None):
    ap = argparse.ArgumentParser(prog="row19_ec2_qualify.py e2")
    for k in ("--manifest", "--partition", "--authority", "--key", "--bundle", "--opmanifest", "--prod-opmanifest", "--panel",
              "--funding", "--sandbox", "--out"):
        ap.add_argument(k, required=True)
    ap.add_argument("--snapshot", default=None, help="the claims snapshot (default: the panel's recorded path under t1_access)")
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); _MSHA["sha"] = msha = sha(a.manifest)
    problems, parts, mem, rep, conc, unprod_rep = [], {}, None, None, None, []
    part = RP.load(a.partition, man, msha); psha = sha(a.partition)
    if part.get("schema") != RP.SCHEMA2 or int(part["epoch"]) != EQ.EPOCH:
        problems.append(f"the partition is not the schema-2 epoch-{EQ.EPOCH} declaration (schema {part.get('schema')}, epoch {part.get('epoch')})")
    actp = RP.activation_path(man, part["epoch"]); actsha = sha(actp) if os.path.exists(actp) else None
    inv = json.load(open(a.authority))
    why = ES.inventory_problem(inv)
    if why:
        problems.append(f"inventory: {why}")
    if MODE == "canonical":
        ctl, why = RP.adopted_controls(CONTROLS)
        if why:
            problems.append(f"controls: {why}")
    else:
        ctl = json.load(open(CONTROLS))
    if ctl is not None and ((ctl.get("versions") or [{}])[-1].get("partition") or {}).get("sha256") != psha:
        problems.append("the partition is not the one the latest controls pin")
    if actsha is None:
        problems.append("the partition has no activation proof")
    elif ctl is not None and not problems:
        why = RP.activation_problem(man, msha, part, psha, json.load(open(actp)), controls=ctl, mode=MODE)
        if why:
            problems.append(f"activation: {why}")
    panel, snap_sha, panel_sha = None, None, sha(a.panel) if os.path.exists(a.panel) else None
    try:
        panel = json.load(open(a.panel))
        snapp = a.snapshot or os.path.join(T1, (panel.get("claims_snapshot") or {}).get("path") or "-")
        snap = json.load(open(snapp)); snap_sha = sha(snapp)
        why = EQ.panel_problem(panel, part, psha, snap, snap_sha)
    except Exception as e:
        why = f"the panel or its claims snapshot is unreadable ({type(e).__name__}: {e})"
    if why:
        problems.append(f"panel: {why}")
    att = (inv.get("attempts") or {}).get(a.key) or {}
    contract = att.get("contract")
    if not att or att.get("class") != "qualification" or att.get("state") != "reconciled" or att.get("ingestion") != "pending" \
            or contract not in EQ.CONTRACTS or a.key.split("/")[0] != EQ.RUNS[contract]:
        problems.append(f"{a.key}: not a reconciled, pending E2Q qualification attempt of its own run in the inventory")
    elif panel is not None and not problems:
        if att["coordinates"] != panel["work"] or att["duplicates"] != panel["duplicates"]:
            problems.append(f"{a.key}: its work/duplicates are not exactly the declared panel's")
        if len(att.get("sentinels") or []) != EQ.SENTINELS or {tuple(c) for c in att["sentinels"]} & {tuple(c) for c in panel["duplicates"]} \
                or any(RP.blocked(part, *c) for c in att["sentinels"]):
            problems.append(f"{a.key}: not 4 Lengau sentinels outside the duplicates")
    ops = {}
    for lab, path, want_c in (("qualified", a.opmanifest, contract), ("production", a.prod_opmanifest, "production")):
        try:
            opm = json.load(open(path)); e = opm.get("ec2_production") or {}
            why = ES.operational_problem(opm, man, msha)
            if not why and (e.get("epoch") != EQ.EPOCH or e.get("contract") != want_c or e.get("expect_s") != EQ.EXPECT_S
                            or e.get("lifetime_s") != EQ.LIFETIME_S):
                why = f"not the epoch-2 {want_c} manifest at the funded {EQ.LIFETIME_S} s lifetime"
            if not why and open(path, "rb").read() != EQ.opmanifest_bytes(ES, man, msha, want_c):
                why = "not the exact bytes make_prod_manifest.py writes"
        except Exception as ex:
            why = f"unreadable ({type(ex).__name__})"
        if why:
            problems.append(f"{lab} operational manifest: {why}")
        ops[lab] = sha(path) if os.path.exists(path) else None
    try:
        fund = json.load(open(a.funding))
        if fund.get("schema") != "t1-ec2-epoch-funding-1" or fund.get("epoch") != EQ.EPOCH or fund.get("partition_owned_sha256") != part.get("owned_sha256") \
                or fund.get("lifetime_s") != EQ.LIFETIME_S:
            problems.append("funding: not the epoch-2 funding declaration of this partition at the funded lifetime")
    except Exception as e:
        problems.append(f"funding: unreadable ({type(e).__name__})")
    plan, outcomes, unprod, units = None, None, {}, {}
    if not problems:
        p0 = len(problems)
        opsha = ops["qualified"]
        plan, outcomes = IG.check_bundle(a.bundle, att, (psha, opsha, actsha), problems, partial=True)
        if plan is not None:
            off = [(int(s["rep"]), int(s["indices"][0])) for s in plan["slots"] if s["role"] == "work" and not RP.blocked(part, s["rep"], s["indices"][0])]
            if off:
                problems.append(f"{len(off)} work coordinate(s) are not owned by epoch 2, e.g. {off[:3]}")
        if plan is not None and len(problems) == p0:
            unprod = IG.unproduced_slots(plan, outcomes)
            problems += IG.unproduced_problems(a.bundle, att, plan, unprod, man)
            why = E2R.qualification_unproduced_problem(plan["slots"], outcomes)
            if why:
                problems.append(f"R4': {why}")
            by = {int(s["slot"]): s for s in plan["slots"]}
            for sl, oc in sorted(unprod.items()):
                s = by[sl]
                unprod_rep.append(dict(slot=sl, role=s["role"], coordinate=[int(s["rep"]), int(s["indices"][0])], outcome=oc, kind=E2R.kind(oc),
                                       status_present=os.path.lexists(os.path.join(a.bundle, "root", "status", f"job{att['attempt_id']}.slot{sl}.json"))))
        if len(problems) == p0:
            opman = json.load(open(a.opmanifest))
            units = IG.plan_units(a.bundle, man, opman, opsha, att, plan, problems, skip=set(unprod))
    if not problems:
        by = {int(s["slot"]): s for s in plan["slots"]}
        unc = {(int(by[sl]["rep"]), int(by[sl]["indices"][0])) for sl in unprod}
        def lengau(c):
            return SH.read_record(SH.record_path(man["storage"]["root"], *c), SH.task(man, c[0]), c[1])
        dups = [tuple(c) for c in panel["duplicates"]]
        compare_e2("R1", dups, units, unc, lengau, problems, parts, man)
        compare_e2("R4_sentinels", sorted(tuple(c) for c in att["sentinels"]), units, unc, lengau, problems, parts, man)
        work = [tuple(c) for c in panel["work"]]
        wu = {c: units[c] for c in work if c in units}
        parts["R2_validity"] = dict(coordinates=len(work), produced=len(wu), unproduced=sorted([list(c) for c in work if c in unc]),
                                    failed=sum(1 for u in wu.values() if u["rec"]["failed"]),
                                    nonfinite=sum(1 for c, u in wu.items() if not u["rec"]["failed"] and not finite_ok(u["rec"], SH.task(man, c[0])["bands"])),
                                    limitation="validity against the frozen task only: no reference exists for new work coordinates "
                                               "(QUALIFICATION_E2.md s.3 R2'); not a parity claim")
        if len(wu) + len(parts["R2_validity"]["unproduced"]) != len(work):
            problems.append("R2': a work coordinate is neither a validated record nor a qualifying unproduced slot")
        c_ = E2R.rep_concentration(plan["slots"])
        conc = dict(slots=len(plan["slots"]), max=max(c_.values()), max_reps=sorted(r for r, n in c_.items() if n == max(c_.values())),
                    per_rep={str(r): n for r, n in sorted(c_.items())}, qualified_rep_slots=E2R.QUALIFIED_REP_SLOTS)
        if conc["slots"] != EQ.WORKERS or conc["max"] < E2R.QUALIFIED_REP_SLOTS:
            problems.append(f"R4': the plan does not carry the qualified concentration ({conc['slots']} slots, max {conc['max']} on one replicate, need "
                            f"{EQ.WORKERS} and >= {E2R.QUALIFIED_REP_SLOTS})")
        mem = memory(a.bundle, problems, len(plan["slots"]), label=a.key)
        rep = sandbox_replay_e2(man, part, inv, a.key, a.bundle, a.sandbox, unprod, plan, problems)
    code = code_bound(problems)
    short = {k: (parts.get(k) or {}).get("successful_both", 0) for k in EQ.COVERAGE if (parts.get(k) or {}).get("successful_both", 0) < EQ.COVERAGE[k]}
    outcome = "NO_RELEASE" if problems else ("INCONCLUSIVE" if short else "RELEASE")
    bs = os.path.join(a.bundle, "BUNDLE_SHA256SUMS"); pl = os.path.join(a.bundle, "env", "plan.json")
    cert = dict(schema=EQ.CERT_SCHEMA, epoch=EQ.EPOCH, outcome=outcome, problems=problems, coverage_required=EQ.COVERAGE, coverage_short=short,
                parts=parts, memory=mem, concentration=conc, unproduced=unprod_rep, max_unproduced=EQ.QUAL_MAX_UNPRODUCED, replay=rep,
                released_attempts=[a.key] if outcome == "RELEASE" else [],
                attempt=dict(key=a.key, run=a.key.split("/")[0], contract=contract, attempt_id=att.get("attempt_id"),
                             sequence=att.get("sequence"), plan_sha256=att.get("plan_sha256")),
                r3=dict(performed=False, note="QUALIFICATION_E2.md R3' proposes no fresh-host repeat; R1' is the cross-platform parity check at this packing"),
                limitations=["R2' is validity only (no reference for new work)", "R5' demonstrates ingestion publication recovery only, "
                             "not producer/host restart or interrupted-transfer recovery", "an unproduced coordinate is never a failed-fit record"],
                actual_result_review_required=True,
                bound=dict(code=code, manifest_sha256=msha, partition_sha256=psha, owned_sha256=part.get("owned_sha256"), activation_sha256=actsha,
                           inventory_sha256=inv.get("sha256"), panel_sha256=panel_sha, claims_snapshot_sha256=snap_sha,
                           funding_sha256=sha(a.funding) if os.path.exists(a.funding) else None, opmanifests=ops, lifetime_s=EQ.LIFETIME_S,
                           bundle_sha256=sha(bs) if os.path.exists(bs) else None, plan_sha256=sha(pl) if os.path.exists(pl) else None),
                at=time.time())
    json.dump(cert, open(a.out, "w"), indent=1, sort_keys=True)
    print(json.dumps(dict(outcome=outcome, parts=parts, coverage_short=short, memory=mem, concentration=conc, unproduced=unprod_rep,
                          problems=problems[:10]), indent=1, default=str))
    return 0 if outcome == "RELEASE" else 3


def dispatch(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] == ["e2"]:
        return main_e2(argv[1:])
    return main(argv)


if __name__ == "__main__":
    sys.exit(dispatch())
