"""Row 19 screen on EC2: the ONE claim and budget authority for every EC2 attempt of every run (Codex RSC f3dd3d7
contracts 2, 7, 8; repaired for Codex RSC 0483db4 V10-2 and V10-6). Mac only.

    python3 prod_authority.py inventory                       # seal the current inventory (copy it to <root>/ec2/authority/)
    python3 prod_authority.py ack --run prod-e1 --attempt 3 --register <pulled root/ec2/register.json>
    python3 prod_authority.py disposition --run prod-e1 --attempt 3 --reason "<why no output will be ingested>"   # REQUEST only
    python3 prod_authority.py disposition-confirm --run prod-e1 --attempt 3 --ack <pulled root/ec2/authority/ack_g<N>.json>
    python3 prod_authority.py release-adopt --certificate <cert.json> --review <review record .md>   # paths under aws_ec2/
    python3 prod_authority.py budget                          # every envelope, as the next admission would see it

LEDGERS. runs/<run>/attempts.json per run (prod-e<epoch> production, qual-Q1 / qual-Q2 qualification, b2 the row-23
benchmark), states intent / launched / rejected / ambiguous / reconciled as in the reviewed row-23 launcher, plus the
ingestion state pending / ingested / dispositioned. EVERY reservation (admission), settlement acknowledgement, disposition
and inventory is taken under ONE global lock (runs/.authority.lock) in addition to the run lock the reaper shares, and
bumps one global generation; sequences are globally unique and increasing (runs/.authority_state.json).

OWNERSHIP. A production or qualification attempt owns its work coordinates from intent until it is rejected (no instance
ever existed) or its output was ingested (acknowledged from the Lengau register by `ack`, checked against the attempt) or
dispositioned (`disposition`: reconciled with no output to ingest). The fence at a coordinate is the highest sequence of
any non-rejected attempt ever assigned it; ingestion on Lengau accepts a record only from the inventory's CURRENT owner at a
sequence not below its own register fence, so a dispositioned or reassigned late writer can never publish. Duplicates
(qualification repeats, sentinels) never own.

BUDGET (one serialized ledger across all runs and epochs). Every attempt that is not rejected is charged its worst case
until reconciled and its observed hours after, each at its own recorded spot cap and ancillary rate. Envelopes, all checked
before any dispatch: (1) production + qualification across ALL epochs and retries <= USD 2,300; (2) every further AWS
spend - the recorded baseline (Cost Explorer through a stated date, with the post-cutoff part of 12 Sept bounded and an
idle-charge accrual per day after it) + every run under runs/ (row 23 included) - <= USD 3,000 from 12 Sept 2026 21:50 UTC;
(3) each qualification part's cumulative charge (retries included) <= its declared ceiling, and only once the owner has
accepted those ceilings in ec2_release_state.json.

REVISION 3 (Codex RSC 3dc0daf R1-2, R1-4, R1-7).
  disposition  is a REQUEST: the attempt keeps owning (ingestion stays pending) and the next inventory carries
               `disposition_requested`; the Lengau root fences it at installation (row19_ec2_root.py install) and writes
               ack_g<N>.json. `disposition-confirm` releases ownership ONLY against that acknowledgement: it must name this
               key with this attempt id, sequence and coordinate digest, and its inventory digest must be a sealed inventory
               of this authority that carried the request. A refusal in the acknowledgement (output already being ingested)
               keeps the attempt owning.
  release      production is released ONLY by a validated certificate (release_problem): the qualifier's schema-2
               certificate with outcome RELEASE, no problems, the predeclared coverage met on finite successful paths, the
               memory gate at the full packing, the replay; its bound code equal to the current files, its manifest the
               production 43b75f94, its partition the one the current controls pin (a later epoch needs its own reviewed
               release), its Q1 attempt the reconciled ledger attempt (key, id, sequence, plan bytes); and a pinned review
               record carrying `FAVOURABLE` and the literal `RELEASE row19-ec2-qualification certificate=<sha256>
               attempts=<keys>`. The released attempts are DERIVED from the certificate; a release state listing others is
               refused. `release-adopt` writes the production block from a passing validation only.
  exclusion    benchmark launches (bench_launch.py, the reviewed row-23 launcher) are not under this lock; a production or
               qualification admission therefore refuses while any benchmark attempt is unresolved or running, and every
               benchmark charge is counted in the cumulative cap. Each production/qualification attempt records its region
               and zone; an admission refuses while any unresolved attempt was made in another region than the current one,
               and recovery refuses an attempt of another region (the region is attempt identity, not a global).

REVISION 4 (Codex RSC 299f4b7 R2-1).
  generations  EVERY seal is a new generation: write_inventory advances the global generation itself and writes
               runs/inventory/inventory_g<N>.json exactly once (an existing archive is never overwritten); latest.json is
               the newest seal. The root installs each generation once, so a refresh, a launch (intent, then the dispatch
               outcome), a reconciliation and a disposition are all installable views, and an acknowledgement of an older
               generation stays checkable against its immutable archive. Seals read every ledger under the authority lock.
  root ACK     disposition-confirm accepts only an acknowledgement in mode canonical, of the canonical screen root
               (CANONICAL_ROOT, the production manifest's storage root) and the production manifest 43b75f94; an isolated
               S root or a sandbox acknowledgement never releases ownership.

REVISION 5 - CANDIDATE, not adopted (EC2 provider epoch 2; Codex design reviews/2026-10-17_row19_resize_codex.md s.3, s.4,
s.6 item 5; owner 17 Oct 2026: five concurrent instances, ~USD 1,779 forecast + USD 300 bounded allowance).
  allocator    a schema-2 partition (row19_partition REVISION 5) is allocated REPLICATE-COMPLETE: the owned set in ascending
               (rep, index), skipping completed, currently owned and crash-excluded coordinates - an instance takes the
               earliest replicates' remaining coordinates before the next replicate. Schema 1 keeps its order.
  fleet        FLEET_CEILING = 5: no admission while 5 production/qualification attempts of any run are live (intent,
               launched or ambiguous). Every live attempt is charged its worst case (charged()), so concurrent attempts are
               reserved CUMULATIVELY against every envelope - five live instances reserve 5 x USD 27.92 before a sixth
               could even be considered.
  epoch 2      epoch2_problem, for the prod-e2 run and the qual-E2* runs, against the validated funding declaration
               (aws_ec2/e2_funding.json, make_e2_funding.py): base batches = ceil(owned / 72) (46 at the 17 Oct replay); at
               most BASE + 4 non-rejected production attempts; at most 2 non-rejected qualification instances; the
               allowance money - every qual-E2 attempt and every production attempt beyond the base count, each at its
               worst case until reconciled - at most USD 300; the whole epoch at most forecast + allowance; the existing
               USD 2,300 envelope and USD 3,000 cap unchanged. A further attempt needs a new owner decision (s.3).
  crash rule   the EC2 analogue of the design's s.4 rule: `ack` records the attempt's unproduced work slots (ingestion
               REVISION 5) with their exit; a coordinate whose worker died by a fatal signal (REVISION 6: any exit 129..159,
               the class ingestion admits) in TWO acknowledged attempts of the same instance contract is never allocated a third time
               (RESCUE-PENDING on EC2; no EC2 rescue route is built). Deadline-censored slots and dispositioned attempts
               (spot interruption, no output) do not count; they consume the allowance instead.
  ack          accepts a register entry whose published coordinates plus its `unproduced` coordinates are exactly the
               attempt's owned coordinates; all of them are released (the unproduced ones are fenced on the root).
  paths        the module resolves t1_access by name; data (runs/, the baseline, the release state) stay in aws_ec2/.

REVISION 6 - CANDIDATE, not adopted (Codex review reviews/2026-10-17_e2_p80r_codex_review.md A2, A3, A4).
  crash rule   (A2) the fatal-signal class is the ONE set ingestion admits (row19_ec2_e2rules.FATAL_SIGNAL_EXITS, 129..159):
               every acknowledged same-envelope outcome of that class counts, so SIGTRAP 133, SIGFPE 136 or SIGUSR1 138 can
               no longer evade the two-crash cap; `ack` refuses an unproduced outcome of no qualifying class. No
               external-interruption exemption exists (none has evidence of its cause); exit 137 is SIGKILL, never asserted
               as OOM without host evidence.
  packing      (A3) production may not concentrate more workers on one replicate than E2Q1 qualifies:
               E2_QUALIFIED_REP_SLOTS = 61 (row19_ec2_e2rules.QUALIFIED_REP_SLOTS) of 76 across work and sentinels. The
               schema-2 allocator takes at most E2_WORK_PER_REP = 61 - 4 = 57 coordinates of one replicate per batch (still
               ascending (rep, index), so replicates complete in order across consecutive batches); the launcher refuses a
               built plan above 61 on any replicate. Every non-final batch still fills 72 work slots: 46 batches / 3,496
               paid slots at the 17 Oct replay, so the funding derivation is unchanged.
  funding      (A4) the Q2 forecast basis is AUTHENTICATED, not taken from the declaration: funding_problem rederives the
               declaration from the ledger's reconciled Q2 attempt pinned here by key, attempt id, sequence, plan bytes and
               the digest of its charge fields (E2_Q2_BASIS), with the declared 24 planned / 23 successful counts as code
               constants. A coherently regenerated declaration on any other basis, or an edited Q2 ledger, refuses.

REVISION 7 - CANDIDATE, not adopted (EC2 provider epoch 2 QUALIFICATION, chpc/candidate_e2q/DESIGN_e2q.md;
chpc/candidate_e2/QUALIFICATION_E2.md s.3-s.5; DESIGN_e2.md s.5 second bullet).
  release      release_problem dispatches on the certificate schema. Schema 2 (epoch 1) keeps its branch unchanged and in
               addition refuses while the current controls pin a schema-2 partition: an epoch-1 certificate can never open
               epoch 2 (its partition pin differs anyway). Schema 3 (epoch 2, release_problem_e2) requires: outcome RELEASE,
               no problems, no short coverage; R1' >= 15 of the 20 duplicates finite successful; R2' every one of the 52 work
               coordinates a validated record or a qualifying unproduced slot; R4' >= 10 samples with all 76 workers running,
               peak <= 184 GiB, <= 3 non-completions each of a qualifying kind, the plan's 76 slots with >= 61 on one
               replicate; R5' replay ingested and hash-equal with the declared scope, the attempt presented as production,
               and the per-slot branch exercised (listed, fenced, evidence journaled, released by the ack rule; for a
               synthetic case the modified-vs-unmodified-journal replay HELD and every modification labelled); the exact
               epoch-2 code set E2_RELEASE_CODE (row19_ec2_e2qual.CODE, resolved like the qualifier) at its current bytes;
               the production manifest 43b75f94; the partition the current controls pin, schema 2 epoch 2, its owned digest;
               the exact funding bytes (aws_ec2/e2_funding.json) AND funding_problem against the pinned Q2 ledger attempt
               (A4); both operational manifests (the qualified E2Q one and the production one) equal to the maker's bytes at
               the funded 79,200 s lifetime (P3); the declared panel (aws_ec2/prod/panel_e2q_e2.json) regenerated from the
               pinned partition and its bound claims snapshot; the reconciled ledger attempt (key, id, sequence, plan bytes,
               contract) of run qual-E2Q1 or qual-E2Q2 whose plan file is exactly the panel's work and duplicates, 76 slots,
               >= 61 on one replicate, bound to that partition, manifest and lifetime; E2Q2 only after every E2Q1 attempt
               was dispositioned; at most E2_MAX_QUAL_INSTANCES non-rejected qual-E2 instances; and a review carrying
               FAVOURABLE and the epoch-2 literal `RELEASE row19-ec2-qualification epoch=2 certificate=<sha256>
               attempts=<key>`. release_state reports the released epoch and the bound production manifest digest, so an
               epoch-2 production admission can require both.
  qualif. e2   release_state reads an optional `qualification_e2` block of ec2_release_state.json (permitted + a pinned
               reviewed permission record, written by qual_permit.py --epoch2; E2Q2 additionally `e2q2` with its own record).
               Absent = not permitted. e2q_admission_problem: E2Q1 is ONE non-rejected instance (a capacity rejection is no
               instance); E2Q2 needs its own record, every non-rejected E2Q1 attempt dispositioned, and is at most one. The
               USD 300 allowance, the 2 qualification instances and 46 + 4 production attempts stay in epoch2_problem.

REVISION 8 - CANDIDATE, not adopted (Codex review reviews/2026-10-19_e2_adoption_codex_review.md B1, the choice-3 ruling;
replaces the reviewed REVISION 7 bytes eee1bcd4, which stay in git at RSC 92a62f6).
  crash rule   acknowledged fatal (129..159) UNPRODUCED owned work of a released epoch-2 qualification attempt (runs qual-E2Q1 /
               qual-E2Q2, ingested through the canonical per-slot route of ingestion REVISION 8 and acknowledged by `ack`) now
               counts toward the SAME physical two-crash exclusion as production. The crash history (ec2_crash_history) reads
               production runs and the qual-E2* runs, only attempts acknowledged as ingested, only their `ingest_ack`
               unproduced map - which lists owned WORK coordinates only, so duplicates and sentinels never enter it - and the
               counter still counts the fatal-signal class alone (censored / RESUME deadline outcomes never; dispositioned
               attempts carry no ingest_ack). The envelope label is normalised (crash_envelope): E2Q1, E2Q2 and production
               are one label ("production") ONLY when the contract's producer geometry (instance type, workers per instance,
               volume) equals production's AND the attempt's recorded instance type is production's; the lifetime stays in
               the envelope as recorded, so a different lifetime, instance type or geometry stays a different envelope, and
               every other contract (epoch-1 Q1/Q2 included) keeps its own label. B_full: every counted entry comes from an
               `ack` of a register entry, and ingestion publishes only a bundle whose effective attestation is B_full
               (row19_ec2_state.attestation_problem), the profile every one of the three operational manifests declares.
  wording      a certificate binds file CONTENT ({promoted path: sha256}); byte-identical candidate and promoted copies
               resolve to the same map. A location change alone does not invalidate a certificate (DESIGN_e2q choice 8)."""
import argparse, contextlib, fcntl, glob, hashlib, json, math, os, sys, time

SRC = os.path.dirname(os.path.abspath(__file__))
T1 = SRC
while os.path.basename(T1) != "t1_access":
    if os.path.dirname(T1) == T1:
        raise RuntimeError(f"{SRC} is not inside a t1_access tree")
    T1 = os.path.dirname(T1)
HERE = os.path.join(T1, "aws_ec2")                          # the DATA directory (runs/, baseline, release state); = SRC once promoted
CAND = os.path.dirname(SRC) if os.path.basename(os.path.dirname(SRC)).startswith("candidate_") else os.path.join(T1, "chpc")
CANDIDATE_RUN = os.path.abspath(CAND) != os.path.abspath(os.path.join(T1, "chpc"))     # REVISION 7: before promotion
_PATH = [HERE, os.path.join(T1, "chpc")] + ([os.path.join(T1, "chpc", "candidate_e2")] if CANDIDATE_RUN else []) + [CAND]
for _p in _PATH:                                            # CAND last inserted = first searched (the candidate modules)
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)
import bench_launch as L
import row19_ec2_state as ES
import row19_partition as RP
import row19_ec2_e2rules as E2R
import row19_ec2_e2qual as EQ

PROD_ENVELOPE_USD, CUMULATIVE_CAP_USD = 2300.0, 3000.0
PROD_SHA = "43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c"
CERT_SCHEMA = "row19-ec2-qualification-certificate-2"
COVERAGE = {"R1": 18, "R2": 36, "R3": 18}                 # = chpc/row19_ec2_qualify.COVERAGE (predeclared)
MEM_HOST_LIMIT_GIB, MEM_MIN_SAMPLES = 184.0, 10
# The qualification code set a release certificate must bind, exactly (= chpc/row19_ec2_qualify.CODE; Codex 299f4b7)
RELEASE_CODE = sorted(["chpc/row19_ec2_qualify.py", "chpc/row19_ec2_ingest.py", "chpc/row19_ec2_state.py", "chpc/row19_partition.py",
                       "chpc/row19_ec2_root.py", "chpc/row19_ec2_shadow.py", "chpc/row19_shard.py", "chpc/row19_screen_verify.py",
                       "aws_ec2/qual_S_plan.json", "chpc/row19_qual_S_manifest.json", "analyze.py", "models.py"])
# Ancillary per instance-hour for the production/qualification contract (60 GB gp3 at <= USD 0.10/GB-month = 0.0082/h, one
# public IPv4 0.005/h; rounded up) and a fixed per-attempt allowance for transfer and requests (toolchain 0.22 GB and results
# <= 1 GB across eu-north-1 <-> Oregon at 0.02/GB, S3 requests of 10-minute syncs over 22 h, reserve).
ANC_H_PROD, S3_FIXED_PROD = 0.014, 0.30
QUAL_LIFETIME_S = 79200                       # 22 h instance lifetime for Q1 and Q2 (QUALIFICATION_PLAN.md)
QUAL_CEILINGS_USD = {"Q1": 36.0, "Q2": 17.0}  # Q1: attempt 1 (USD 7.13, spot-interrupted) + one owner-approved retry (13 Oct, "1. yes - go"); Q2 one attempt
SENTINELS_PER_ATTEMPT = 4
PROD_CLASSES = ("production", "qualification")
# REVISION 5 (epoch 2). Owner decisions of 17 Oct 2026 (chpc/ROW19_SCREEN_DECLARATIONS.md, final section) as code constants:
# a funding file can carry only derived numbers and is checked against these.
FLEET_CEILING = 5
E2_ALLOWANCE_USD = 300.0
E2_MAX_EXTRA_PRODUCTION = 4
E2_MAX_QUAL_INSTANCES = 2
E2_WORK_PER_BATCH, E2_SENTINELS, E2_WORKERS = 72, 4, 76
E2_FUNDING = os.path.join(HERE, "e2_funding.json")
FUNDING_SCHEMA = "t1-ec2-epoch-funding-1"
FATAL_EXITS = E2R.FATAL_SIGNAL_EXITS                      # REVISION 6 (A2): the ingestion's own set, 128 + signal 1..31
E2_QUALIFIED_REP_SLOTS = E2R.QUALIFIED_REP_SLOTS            # REVISION 6 (A3): E2Q1's declared per-replicate concentration
E2_WORK_PER_REP = E2_QUALIFIED_REP_SLOTS - E2_SENTINELS     # 57: four sentinels on the same replicate stay inside 61
# REVISION 6 (A4): the reviewed forecast basis - the reconciled Q2 attempt, pinned; counts declared (R052 log 16 Oct)
E2_Q2_BASIS = dict(key="qual-Q2/1", attempt_id="ec2-qual-Q2-a1", sequence=7,
                   plan_sha256="5d45f4e157a31ffd027e9b35c48f2d54f54c6293e58ba0e88a53573295cac5e1",
                   charge_fields_sha256="46fd6c92a5d052b79df393c62c8be4161560447496b007780bdc40b3fbdf5092")
E2_Q2_PLANNED, E2_Q2_SUCCESSFUL = 24, 23
FUNDING_NOTE = "Q2 basis: the pinned reconciled ledger attempt qual-Q2/1 and its declared 23/24 slot outcome; owner decisions 17 Oct 2026"
MAX_SAME_ENVELOPE_CRASHES = 2
# REVISION 7: the epoch-2 release (QUALIFICATION_E2.md s.3), every constant from the shared module
E2_CERT_SCHEMA = EQ.CERT_SCHEMA
E2_RELEASE_CODE = list(EQ.CODE)
E2_COVERAGE = dict(EQ.COVERAGE)
E2Q_PANEL = os.path.join(HERE, "prod", "panel_e2q_e2.json")
LOCK =os.path.join(HERE, "runs", ".authority.lock")
STATE = os.path.join(HERE, "runs", ".authority_state.json")
INV_DIR = os.path.join(HERE, "runs", "inventory")
RELEASE_STATE = os.path.join(HERE, "ec2_release_state.json")
CANONICAL_ROOT = json.load(open(os.path.join(T1, "chpc", "row19_screen_manifest.json")))["storage"]["root"]
CANONICAL_MANIFEST_SHA = PROD_SHA


def run_name(epoch):
    return f"prod-e{int(epoch)}"


def qual_run(part):
    return f"qual-{part}"


def run_class(run):
    return "production" if run.startswith("prod-") else "qualification" if run.startswith("qual-") else "benchmark"


@contextlib.contextmanager
def authority_lock(wait_s=0):
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    fh = open(LOCK, "a+"); t0 = time.time()
    while True:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB); break
        except BlockingIOError:
            if time.time() - t0 >= wait_s:
                fh.close(); raise
            time.sleep(1)
    try:
        yield
    finally:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN); fh.close()


def state():
    return json.load(open(STATE)) if os.path.exists(STATE) else {"generation": 1, "next_sequence": 1}


def bump(st, sequences=0):
    """Advance the global generation (and reserve `sequences` sequence numbers); call ONLY under authority_lock."""
    first = st["next_sequence"]
    st = dict(generation=st["generation"] + 1, next_sequence=first + sequences)
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, STATE)
    return st, first


def baseline(now=None):
    """Spend already incurred outside the ledgers: the recorded Cost Explorer figure through `through_utc`, plus the idle
    accrual (VPC endpoints, S3) for every started day after it - a moving bound, never a constant."""
    b = json.load(open(os.path.join(HERE, "budget_baseline.json")))
    assert b.get("schema") == "t1-aws-budget-baseline-2", "budget_baseline.json is not schema 2"
    now = time.time() if now is None else now
    days = max(0.0, (now - b["through_epoch"]) / 86400.0)
    return float(b["spent_usd"]) + float(b["idle_usd_per_day"]) * (int(days) + 1)


def charged(a):
    """One attempt's charge at its own cap and ancillary rate: worst case until reconciled, observed after; rejected 0."""
    if "anc_h" not in a:
        return L.charged(a)                                              # benchmark attempts: the reviewed row-23 rule
    if a.get("state") == "rejected":
        return 0.0
    if a.get("state") == "reconciled":
        t = a["terminal"]
        return (t["compute_s"] / 3600) * a["max_price"] + (t["ancillary_s"] / 3600) * a["anc_h"] + a["s3_fixed"]
    return worst_usd(a["lifetime_s"], a["max_price"])


def worst_usd(lifetime_s, max_price):
    return ((lifetime_s + L.GRACE_S + L.RESERVE_S) / 3600) * (max_price + ANC_H_PROD) + S3_FIXED_PROD


def ledgers():
    out = {}
    for p in sorted(glob.glob(os.path.join(HERE, "runs", "*", "attempts.json"))):
        out[os.path.basename(os.path.dirname(p))] = json.load(open(p))
    return out


def budget(leds, now=None):
    prod = sum(charged(a) for r, l in leds.items() if run_class(r) in PROD_CLASSES for a in l["attempts"])
    allruns = sum(charged(a) for l in leds.values() for a in l["attempts"])
    qual = {q: sum(charged(a) for a in leds.get(qual_run(q), {"attempts": []})["attempts"]) for q in QUAL_CEILINGS_USD}
    return dict(production_usd=prod, all_runs_usd=allruns, baseline_usd=baseline(now), qualification_usd=qual)


def budget_problem(leds, run, new_worst_usd, release=None, now=None):
    b = budget(leds, now)
    if run_class(run) in PROD_CLASSES and b["production_usd"] + new_worst_usd > PROD_ENVELOPE_USD + 1e-9:
        return f"production envelope: {b['production_usd']:.2f} charged across all epochs + {new_worst_usd:.2f} worst > {PROD_ENVELOPE_USD:.0f}"
    if b["baseline_usd"] + b["all_runs_usd"] + new_worst_usd > CUMULATIVE_CAP_USD + 1e-9:
        return (f"cumulative cap: baseline {b['baseline_usd']:.2f} + all runs {b['all_runs_usd']:.2f} + {new_worst_usd:.2f} "
                f"> {CUMULATIVE_CAP_USD:.0f}")
    if run_class(run) == "qualification" and run.split("-", 1)[1] not in QUAL_CEILINGS_USD:
        if not is_e2_qual(run):
            return f"{run} is no declared qualification part"
        return ""                                                  # epoch-2 qualification: bounded by epoch2_problem
    if run_class(run) == "qualification":
        q = run.split("-", 1)[1]
        if not (release or {}).get("qualification", {}).get("owner_accepted_ceilings"):
            return f"the qualification ceilings {QUAL_CEILINGS_USD} are not accepted by the owner (ec2_release_state.json)"
        if b["qualification_usd"][q] + new_worst_usd > QUAL_CEILINGS_USD[q] + 1e-9:
            return f"{q} ceiling: {b['qualification_usd'][q]:.2f} charged + {new_worst_usd:.2f} worst > {QUAL_CEILINGS_USD[q]:.2f}"
    return ""


def owns(a, run):
    return run_class(run) in PROD_CLASSES and a.get("state") != "rejected" and a.get("ingestion", "pending") == "pending"


def owned(leds):
    """{(rep, index): (key, sequence)} across ALL runs and epochs."""
    own = {}
    for run, l in leds.items():
        for a in l["attempts"]:
            if not owns(a, run):
                continue
            for c in a.get("coordinates", []):
                c = tuple(c)
                if c in own:
                    raise RuntimeError(f"coordinate {c} owned by {own[c][0]} and {run}/{a['attempt']}: the ledgers are inconsistent")
                own[c] = (f"{run}/{a['attempt']}", a["sequence"])
    return own


def fence(leds):
    f = {}
    for run, l in leds.items():
        if run_class(run) not in PROD_CLASSES:
            continue
        for a in l["attempts"]:
            if a.get("state") == "rejected":
                continue
            for c in a.get("coordinates", []):
                k = f"{c[0]}/{c[1]}"; f[k] = max(f.get(k, -1), a["sequence"])
    return f


def allocate(part, leds, completed, n, excluded=()):
    """The next n coordinates of the partition, never completed, owned or crash-excluded. Schema 1: the fixed order (index
    199 downward, reps ascending). Schema 2 (REVISION 5): REPLICATE-COMPLETE - ascending (rep, index) over the explicitly
    owned set, so a batch finishes the earliest replicates' remaining coordinates before it starts the next replicate."""
    own = owned(leds); ex = set(map(tuple, excluded))
    if part.get("schema") == RP.SCHEMA2:
        out, per = [], {}                                     # REVISION 6 (A3): at most E2_WORK_PER_REP of one replicate per batch
        for c in sorted(RP.owned_set(part)):
            if len(out) >= n:
                break
            if c in completed or c in own or c in ex or per.get(c[0], 0) >= E2_WORK_PER_REP:
                continue
            out.append(c); per[c[0]] = per.get(c[0], 0) + 1
        return out
    order = [(r, i) for i in sorted(part["indices"], reverse=True) for r in part["reps"]]
    return [c for c in order if c not in completed and c not in own and c not in ex][:n]


# ---- REVISION 5: fleet ceiling, epoch-2 allowance, EC2 crash rule -----------------------------------------------------------

LIVE = ("intent", "launched", "ambiguous")


def is_e2_qual(run):
    return run.startswith("qual-E2")


def live_fleet(leds):
    """Keys of every production/qualification attempt that may hold an instance now (intent, launched, ambiguous)."""
    return sorted(f"{r}/{a['attempt']}" for r, l in leds.items() if run_class(r) in PROD_CLASSES for a in l["attempts"] if a.get("state") in LIVE)


def fleet_problem(leds, ceiling=FLEET_CEILING):
    live = live_fleet(leds)
    if len(live) >= ceiling:
        return f"fleet ceiling: {len(live)} production/qualification instance(s) live ({live[:6]}), ceiling {ceiling}"
    return ""


def q2_basis(leds):
    """REVISION 6 (A4): the authenticated forecast basis - the charge of the PINNED reconciled Q2 ledger attempt (E2_Q2_BASIS:
    key, attempt id, sequence, plan bytes, charge-field digest), rounded to 1e-6. Raises ValueError otherwise."""
    run, _, n = E2_Q2_BASIS["key"].partition("/")
    a = next((x for x in (leds.get(run) or {"attempts": []})["attempts"] if str(x.get("attempt")) == n), None)
    if a is None or a.get("state") != "reconciled":
        raise ValueError(f"the pinned Q2 basis attempt {E2_Q2_BASIS['key']} is not a reconciled ledger attempt")
    if (a.get("attempt_id"), a.get("sequence"), a.get("plan_sha256")) != (E2_Q2_BASIS["attempt_id"], E2_Q2_BASIS["sequence"], E2_Q2_BASIS["plan_sha256"]):
        raise ValueError("the Q2 ledger attempt is not the pinned one (attempt id, sequence, plan bytes)")
    try:
        fields = dict(compute_s=a["terminal"]["compute_s"], ancillary_s=a["terminal"]["ancillary_s"], max_price=a["max_price"],
                      anc_h=a["anc_h"], s3_fixed=a["s3_fixed"])
    except (KeyError, TypeError) as e:
        raise ValueError(f"the Q2 ledger attempt's charge fields are malformed ({type(e).__name__})")
    if ES.sha_bytes(ES.canonical(fields)) != E2_Q2_BASIS["charge_fields_sha256"]:
        raise ValueError("the Q2 ledger attempt's charge fields are not the pinned reviewed values")
    return round(charged(a), 6)


def funding_e2(part, q2_charged_usd, q2_planned=E2_Q2_PLANNED, q2_successful=E2_Q2_SUCCESSFUL, now_note=FUNDING_NOTE):
    """The epoch-2 funding declaration, derived (never chosen): base batches from the owned count at 72 work + 4 sentinels per
    76-worker instance; the design's Q2-derived forecasts (planned-slot and successful-slot rates, the higher one carried);
    the declared per-batch funding maximum at the 22 h lifetime; the allowance and its counters from the owner constants."""
    owned_n = len(RP.owned_set(part)); base = math.ceil(owned_n / E2_WORK_PER_BATCH); slots = base * E2_WORKERS
    per_planned, per_success = q2_charged_usd / q2_planned, q2_charged_usd / q2_successful
    worst = worst_usd(QUAL_LIFETIME_S, ES.CONTRACTS["production"]["max_price"])
    fc = dict(planned_slot_usd=round(slots * per_planned, 2), successful_slot_usd=round(slots * per_success, 2))
    return {"schema": FUNDING_SCHEMA, "epoch": int(part["epoch"]), "partition_owned_sha256": part["owned_sha256"],
            "owned_coordinates": owned_n, "work_per_batch": E2_WORK_PER_BATCH, "sentinels_per_batch": E2_SENTINELS,
            "workers_per_instance": E2_WORKERS, "base_batches": base, "paid_slots": slots,
            "forecast": dict(fc, carried_usd=max(fc.values()), basis=dict(q2_charged_usd=round(q2_charged_usd, 6), q2_planned=q2_planned,
                             q2_successful=q2_successful, q2_attempt=dict(E2_Q2_BASIS),
                             note="Q2 (c7a.12xlarge, 24 workers) rates extrapolated to another packing: a "
                             "cost illustration, not a measured production rate (Codex design s.3)")),
            "qualified_rep_slots": E2_QUALIFIED_REP_SLOTS, "work_per_rep_per_batch": E2_WORK_PER_REP,
            "worst_per_batch_usd": round(worst, 4), "funding_maxima_all_base_usd": round(base * worst, 3),
            "lifetime_s": QUAL_LIFETIME_S, "allowance_usd": E2_ALLOWANCE_USD, "max_extra_production_batches": E2_MAX_EXTRA_PRODUCTION,
            "max_qualification_instances": E2_MAX_QUAL_INSTANCES, "fleet_ceiling": FLEET_CEILING,
            "epoch_cap_usd": round(max(fc.values()) + E2_ALLOWANCE_USD, 2),
            "calendar_days_at_fleet": round(math.ceil(base / FLEET_CEILING) * 21.2811 / 24, 2),
            "rule": "owner 17 Oct 2026: ~USD 1,779 forecast + USD 300 bounded qualification/retry allowance inside the USD 2,300 "
                    "production envelope and the USD 3,000 cap; five concurrent instances subject to qualification of the 76-worker "
                    "packing; the allowance covers at most two new qualification instances and four extra production batches, "
                    "all within USD 300; a further attempt needs a new decision", "note": now_note}


def funding_problem(fund, part, leds=None):
    """'' when the funding declaration is exactly the derivation from this partition, the owner constants and the
    AUTHENTICATED Q2 basis (REVISION 6, A4: the pinned reconciled ledger attempt with the declared 24/23 counts) - never from
    the basis the declaration itself carries."""
    if not isinstance(fund, dict) or fund.get("schema") != FUNDING_SCHEMA:
        return "no epoch-2 funding declaration"
    try:
        want = funding_e2(part, q2_basis(ledgers() if leds is None else leds))
    except ValueError as e:
        return f"the funding basis cannot be authenticated: {e}"
    if ES.canonical(want) != ES.canonical(fund):
        return "the funding declaration is not the derivation from this partition, the owner constants and the pinned Q2 basis"
    return ""


def _nonrejected(leds, pred):
    return [(r, a) for r, l in sorted(leds.items()) if pred(r) for a in l["attempts"] if a.get("state") != "rejected"]


def epoch2_problem(leds, run, new_worst, fund):
    """'' when one more attempt of `run` (prod-e2 or qual-E2*) with worst case `new_worst` stays inside the epoch-2 bounds."""
    prod = _nonrejected(leds, lambda r: r == "prod-e2"); qual = _nonrejected(leds, is_e2_qual)
    base = int(fund["base_batches"])
    is_prod = run == "prod-e2"
    if is_prod and len(prod) + 1 > base + E2_MAX_EXTRA_PRODUCTION:
        return f"epoch 2: {len(prod)} production attempt(s) used; base {base} + {E2_MAX_EXTRA_PRODUCTION} extra is the bound (a further attempt needs a new owner decision)"
    if is_e2_qual(run) and len(qual) + 1 > E2_MAX_QUAL_INSTANCES:
        return f"epoch 2: {len(qual)} qualification instance(s) used; the allowance covers {E2_MAX_QUAL_INSTANCES}"
    if not (is_prod or is_e2_qual(run)):
        return ""
    order = sorted(prod, key=lambda x: x[1]["sequence"])
    extra = [a for _, a in order[base:]]
    allowance = sum(charged(a) for _, a in qual) + sum(charged(a) for a in extra)
    is_allowance = is_e2_qual(run) or len(prod) + 1 > base
    if is_allowance and allowance + new_worst > E2_ALLOWANCE_USD + 1e-9:
        return f"epoch 2 allowance: {allowance:.2f} charged + {new_worst:.2f} worst > {E2_ALLOWANCE_USD:.0f}"
    total = sum(charged(a) for _, a in prod) + sum(charged(a) for _, a in qual)
    if total + new_worst > float(fund["epoch_cap_usd"]) + 1e-9:
        return f"epoch 2 cap: {total:.2f} charged + {new_worst:.2f} worst > forecast + allowance {fund['epoch_cap_usd']:.2f}"
    return ""


CRASH_EQUIVALENT_CONTRACTS = ("production", "E2Q1", "E2Q2")   # REVISION 8 (choice-3 ruling): one physical envelope label


def _producer_geometry(contract):
    c = ES.CONTRACTS.get(contract) or {}
    return (c.get("itype"), c.get("workers"), c.get("volume_gb"))


def crash_envelope(contract, itype, lifetime_s):
    """REVISION 8: the physical envelope [label, instance type, lifetime] of an attempt. E2Q1/E2Q2/production share the label
    "production" only when the contract's producer geometry equals production's and the recorded instance type is
    production's; otherwise the contract name stays the label. The lifetime is never normalised."""
    label = contract
    if contract in CRASH_EQUIVALENT_CONTRACTS and _producer_geometry(contract) == _producer_geometry("production") \
            and itype == ES.CONTRACTS["production"]["itype"]:
        label = "production"
    return [label, itype, lifetime_s]


def crash_counted_run(run):
    """REVISION 8: production runs and the epoch-2 qualification runs (qual-E2Q1 / qual-E2Q2) feed the crash history."""
    return run_class(run) == "production" or is_e2_qual(run)


def ec2_crash_history(leds):
    """{(rep, index): [{attempt, exit, contract, envelope}]} from the ACKNOWLEDGED unproduced owned-work slots of production
    attempts and (REVISION 8) of released, canonically ingested epoch-2 qualification attempts; `envelope` is crash_envelope."""
    out = {}
    for run, l in sorted(leds.items()):
        if not crash_counted_run(run):
            continue
        for a in l["attempts"]:
            if a.get("ingestion") != "ingested":                         # only an acknowledged ingestion (never a disposition)
                continue
            for k, u in sorted(((a.get("ingest_ack") or {}).get("unproduced") or {}).items()):
                out.setdefault(tuple(int(x) for x in k.split("/")), []).append(
                    dict(attempt=f"{run}/{a['attempt']}", exit=(u or {}).get("outcome"), contract=a.get("contract"),
                         envelope=crash_envelope(a.get("contract"), a.get("type"), a.get("lifetime_s"))))
    return out


def ec2_crash_excluded(leds, contract="production", itype=None, lifetime_s=QUAL_LIFETIME_S):
    """Coordinates whose worker died by a fatal signal (REVISION 6: ANY outcome of the class ingestion admits, 129..159) in >= 2
    acknowledged attempts of this physical envelope (REVISION 8: production and released E2Q1/E2Q2 owned work alike when
    crash_envelope makes them one): never allocated again."""
    itype = itype or ES.CONTRACTS[contract]["itype"]; env = crash_envelope(contract, itype, lifetime_s)
    return {c for c, xs in ec2_crash_history(leds).items()
            if sum(1 for x in xs if E2R.counts_toward_crash_rule(x["exit"]) and x["envelope"] == env) >= MAX_SAME_ENVELOPE_CRASHES}


def sentinels(lengau_completed, token, n=SENTINELS_PER_ATTEMPT, exclude=()):
    """n distinct Lengau-completed coordinates chosen by the attempt token, never by outcome."""
    pool = sorted(set(lengau_completed) - set(exclude))
    if len(pool) < n:
        raise ValueError("fewer Lengau-completed coordinates than sentinels")
    picked, k = [], 0
    while len(picked) < n:
        h = int(hashlib.sha256(f"{token}:{k}".encode()).hexdigest(), 16) % len(pool)
        if pool[h] not in picked:
            picked.append(pool[h])
        k += 1
    return picked


def owner_of(leds, coordinate):
    return owned(leds).get(tuple(coordinate))


def controls_partition():
    """(sha256, path) of the partition the latest controls version pins (REVISION 7)."""
    ctl = json.load(open(os.path.join(T1, "chpc", "row19_screen_controls.json")))
    p = ctl["versions"][-1].get("partition") or {}
    return p.get("sha256"), p.get("path")


def controls_partition_sha():
    return controls_partition()[0]


def pinned_partition():
    """(the validated partition document the current controls pin, its sha256), or (None, sha256) when its bytes are not at
    the pinned path or do not load (REVISION 7)."""
    psha, rel = controls_partition()
    p = os.path.join(T1, rel) if rel else None
    if not p or not os.path.isfile(p) or L.sha256(p) != psha:
        return None, psha
    try:
        man_path = os.path.join(T1, "chpc", "row19_screen_manifest.json")
        return RP.load(p, json.load(open(man_path)), PROD_SHA), psha
    except Exception:
        return None, psha


def release_problem(cert_path, review_path, leds=None):
    """(released attempt keys, '') when the certificate and its review release production now; else ([], why). R1-4.
    REVISION 7: a schema-3 certificate is judged by the epoch-2 branch, everything else by the epoch-1 branch."""
    try:
        cert = json.load(open(cert_path))
    except Exception as e:
        return [], f"the certificate is unreadable ({type(e).__name__})"
    if isinstance(cert, dict) and cert.get("schema") == E2_CERT_SCHEMA:
        return release_problem_e2(cert_path, review_path, leds)
    return release_problem_e1(cert_path, review_path, leds)


def release_problem_e1(cert_path, review_path, leds=None):
    """The epoch-1 branch (schema-2 certificate), unchanged but for the REVISION 7 guard: never while a schema-2 epoch is pinned."""
    try:
        cert = json.load(open(cert_path)); csha = L.sha256(cert_path)
    except Exception as e:
        return [], f"the certificate is unreadable ({type(e).__name__})"
    if cert.get("schema") != CERT_SCHEMA or cert.get("outcome") != "RELEASE" or cert.get("problems") != [] or cert.get("coverage_short") != {}:
        return [], "the certificate is not a schema-2 RELEASE without problems and without short coverage"
    pin_doc, _ = pinned_partition()
    if pin_doc is not None and pin_doc.get("schema") == RP.SCHEMA2:
        return [], "an epoch-1 (schema-2) certificate cannot release a schema-2 epoch: epoch 2 needs its own schema-3 certificate"
    parts = cert.get("parts") or {}
    if any((parts.get(k) or {}).get("successful_both", -1) < n for k, n in COVERAGE.items()):
        return [], "the certificate's finite successful coverage is below the predeclared 18 / 36 / 18"
    m = cert.get("memory") or {}
    if not (m.get("samples_at_full_packing", 0) >= MEM_MIN_SAMPLES and 0 < m.get("peak_host_used_gib", 1e9) <= MEM_HOST_LIMIT_GIB):
        return [], "the certificate's memory evidence does not cover the full packing within the limit"
    rp = cert.get("replay") or {}
    if not (rp.get("final_state") == "ingested" and rp.get("hashes_equal") is True and "scope" in rp):
        return [], "the certificate's ingestion replay did not complete or states no scope"
    b = cert.get("bound") or {}
    stale = [f for f, h in (b.get("code") or {}).items() if not os.path.exists(os.path.join(T1, f)) or L.sha256(os.path.join(T1, f)) != h]
    if sorted(b.get("code") or {}) != RELEASE_CODE:
        return [], "the certificate does not bind exactly the qualification code set (prod_authority.RELEASE_CODE)"
    if stale:
        return [], f"the certificate's code is not the current bytes ({stale[:4]}): re-qualify or review a migration"
    if b.get("manifest_sha256") != PROD_SHA:
        return [], "the certificate is not bound to the production manifest 43b75f94"
    if b.get("partition_sha256") != controls_partition_sha():
        return [], "the certificate's partition is not the one the current controls pin: a later epoch needs its own reviewed release"
    q1 = cert.get("q1") or {}; keys = cert.get("released_attempts")
    if not (isinstance(keys, list) and keys == [q1.get("key")]):
        return [], "the certificate's released attempts are not exactly its Q1 attempt"
    leds = ledgers() if leds is None else leds
    run, _, n = str(q1.get("key")).partition("/")
    a = next((x for x in leds.get(run, {"attempts": []})["attempts"] if str(x.get("attempt")) == n), None)
    if a is None or a.get("state") != "reconciled" or (a.get("attempt_id"), a.get("sequence"), a.get("plan_sha256")) != (q1.get("attempt_id"), q1.get("sequence"), q1.get("plan_sha256")):
        return [], "the certificate's Q1 attempt is not the reconciled ledger attempt (id, sequence, plan bytes)"
    if (b.get("plans") or {}).get("Q1") != a.get("plan_sha256"):
        return [], "the certificate's bound Q1 plan is not the attempt's plan"
    try:
        text = open(review_path).read()
    except Exception as e:
        return [], f"the actual-result review is unreadable ({type(e).__name__})"
    lit = f"RELEASE row19-ec2-qualification certificate={csha} attempts={','.join(keys)}"
    if lit not in text.split("\n") or "FAVOURABLE" not in text:
        return [], "the actual-result review carries no FAVOURABLE verdict with the literal release line for this certificate"
    return list(keys), ""


def _file_sha(p):
    return L.sha256(p) if p and os.path.isfile(p) else None


def release_problem_e2(cert_path, review_path, leds=None):
    """REVISION 7: (released attempt keys, '') when a schema-3 epoch-2 certificate and its review release epoch-2 production
    now; else ([], why). The rule is QUALIFICATION_E2.md s.3 (module text, REVISION 7)."""
    try:
        cert = json.load(open(cert_path)); csha = L.sha256(cert_path)
    except Exception as e:
        return [], f"the certificate is unreadable ({type(e).__name__})"
    if cert.get("schema") != E2_CERT_SCHEMA or cert.get("epoch") != EQ.EPOCH or cert.get("outcome") != "RELEASE" \
            or cert.get("problems") != [] or cert.get("coverage_short") != {}:
        return [], "the certificate is not a schema-3 epoch-2 RELEASE without problems and without short coverage"
    parts = cert.get("parts") or {}
    r1 = parts.get("R1") or {}
    if r1.get("coordinates") != EQ.DUP_N or not isinstance(r1.get("successful_both"), int) or r1["successful_both"] < E2_COVERAGE["R1"]:
        return [], f"R1': the finite successful coverage is below the predeclared {E2_COVERAGE['R1']} of {EQ.DUP_N} duplicates"
    r2 = parts.get("R2_validity") or {}
    if r2.get("coordinates") != EQ.WORK_N or not isinstance(r2.get("produced"), int) or not isinstance(r2.get("unproduced"), list) \
            or r2["produced"] + len(r2["unproduced"]) != EQ.WORK_N:
        return [], "R2': not every work coordinate is a validated record or a qualifying unproduced slot"
    if (parts.get("R4_sentinels") or {}).get("coordinates") != EQ.SENTINELS:
        return [], "R4': the sentinel comparison is missing"
    m = cert.get("memory") or {}
    if not (m.get("workers") == EQ.WORKERS and m.get("samples_at_full_packing", 0) >= EQ.MEM_MIN_SAMPLES
            and 0 < m.get("peak_host_used_gib", 1e9) <= EQ.MEM_HOST_LIMIT_GIB):
        return [], "R4': the memory evidence does not cover the full 76-worker packing within the limit"
    un = cert.get("unproduced")
    if not isinstance(un, list) or len(un) > EQ.QUAL_MAX_UNPRODUCED or any(not isinstance(u, dict) or E2R.kind(u.get("outcome")) is None for u in un):
        return [], f"R4': more than {EQ.QUAL_MAX_UNPRODUCED} non-completed slots, or one of no qualifying kind"
    cc = cert.get("concentration") or {}
    if cc.get("slots") != EQ.WORKERS or not isinstance(cc.get("max"), int) or cc["max"] < E2_QUALIFIED_REP_SLOTS:
        return [], f"R4': the certificate does not show the qualified concentration (76 slots, >= {E2_QUALIFIED_REP_SLOTS} on one replicate)"
    rp = cert.get("replay") or {}
    if not (rp.get("final_state") == "ingested" and rp.get("hashes_equal") is True and rp.get("scope") == EQ.REPLAY_SCOPE
            and rp.get("presented_class") == "production"):
        return [], "R5': the ingestion replay did not complete, or states another scope or presentation"
    ps = rp.get("per_slot") or {}
    ok = ps.get("mode") in ("actual", "synthetic") and ps.get("listed") is True and ps.get("fenced") is True \
        and ps.get("evidence_journaled") is True and ps.get("ack_problem") == ""
    if ps.get("mode") == "synthetic":
        syn = ps.get("synthetic")
        ok = ok and ps.get("ingest_rc") == 0 and ps.get("modified_replay_held") is True and ps.get("activation_problems") == [] \
            and isinstance(syn, list) and len(syn) >= 3 and all(isinstance(s, dict) and str(s.get("label", "")).startswith("SYNTHETIC")
                                                                 and "original_sha256" in s and "modified_sha256" in s for s in syn)
    if not ok:
        return [], "R5': the per-slot branch was not exercised completely (listed, fenced, evidence, ack; synthetic: held, labelled)"
    b = cert.get("bound") or {}
    if sorted(b.get("code") or {}) != sorted(E2_RELEASE_CODE):
        return [], "the certificate does not bind exactly the epoch-2 qualification code set (prod_authority.E2_RELEASE_CODE)"
    stale = [f for f, h in sorted((b.get("code") or {}).items()) if _file_sha(EQ.code_path(T1, f, CANDIDATE_RUN)) != h]
    if stale:
        return [], f"the certificate's code is not the current bytes ({stale[:4]}): re-qualify or review a migration"
    if b.get("manifest_sha256") != PROD_SHA:
        return [], "the certificate is not bound to the production manifest 43b75f94"
    part, psha = pinned_partition()
    if part is None or part.get("schema") != RP.SCHEMA2 or int(part.get("epoch", 0)) != EQ.EPOCH or b.get("partition_sha256") != psha \
            or b.get("owned_sha256") != part.get("owned_sha256"):
        return [], "the certificate's partition is not the schema-2 epoch-2 partition the current controls pin (bytes at the pinned path)"
    leds = ledgers() if leds is None else leds
    if b.get("funding_sha256") != _file_sha(E2_FUNDING):
        return [], "the certificate does not bind the exact current funding declaration bytes (aws_ec2/e2_funding.json)"
    try:
        fund = json.load(open(E2_FUNDING))
    except Exception as e:
        return [], f"the funding declaration is unreadable ({type(e).__name__})"
    why = funding_problem(fund, part, leds)
    if why:
        return [], f"funding: {why}"
    at = cert.get("attempt") or {}; contract = at.get("contract")
    if contract not in EQ.CONTRACTS:
        return [], "the certificate's attempt is not an E2Q1/E2Q2 attempt"
    prod = json.load(open(os.path.join(T1, "chpc", "row19_screen_manifest.json")))
    ops = b.get("opmanifests") or {}
    if ops.get("qualified") != ES.sha_bytes(EQ.opmanifest_bytes(ES, prod, PROD_SHA, contract)) \
            or ops.get("production") != ES.sha_bytes(EQ.opmanifest_bytes(ES, prod, PROD_SHA, "production")) \
            or b.get("lifetime_s") != EQ.LIFETIME_S or int(fund.get("lifetime_s", -1)) != EQ.LIFETIME_S:
        return [], "the certificate's operational manifests are not the maker's epoch-2 bytes at the funded lifetime"
    try:
        panel = json.load(open(E2Q_PANEL)); snapp = os.path.join(T1, panel["claims_snapshot"]["path"])
        why = EQ.panel_problem(panel, part, psha, json.load(open(snapp)), L.sha256(snapp))
    except Exception as e:
        panel, snapp, why = None, None, f"unreadable ({type(e).__name__})"
    if why or b.get("panel_sha256") != _file_sha(E2Q_PANEL) or b.get("claims_snapshot_sha256") != _file_sha(snapp):
        return [], f"the declared panel is not the bound one regenerated from the pinned partition ({why or 'digests differ'})"
    key = at.get("key"); keys = cert.get("released_attempts")
    if not (isinstance(keys, list) and keys == [key]) or at.get("run") != EQ.RUNS[contract] or str(key).partition("/")[0] != EQ.RUNS[contract]:
        return [], "the certificate's released attempts are not exactly its own E2Q attempt of its own run"
    run, _, n = str(key).partition("/")
    a = next((x for x in leds.get(run, {"attempts": []})["attempts"] if str(x.get("attempt")) == n), None)
    if a is None or a.get("state") != "reconciled" or a.get("contract") != contract \
            or (a.get("attempt_id"), a.get("sequence"), a.get("plan_sha256")) != (at.get("attempt_id"), at.get("sequence"), at.get("plan_sha256")):
        return [], "the certificate's attempt is not the reconciled ledger attempt (id, sequence, plan bytes, contract)"
    if b.get("plan_sha256") != a["plan_sha256"] or _file_sha(a.get("plan")) != a["plan_sha256"]:
        return [], "the certificate's plan is not the attempt's plan file bytes"
    plan = json.load(open(a["plan"])); slots = plan.get("slots") or []
    by = {}
    for s in slots:
        by.setdefault(s.get("role"), []).append([int(s["rep"]), int(s["indices"][0])])
    conc = E2R.rep_concentration(slots) or {0: 0}
    if plan.get("epoch") != EQ.EPOCH or plan.get("contract") != contract or plan.get("partition_sha256") != psha \
            or plan.get("opmanifest_sha256") != ops.get("qualified") or plan.get("lifetime_s") != EQ.LIFETIME_S \
            or len(slots) != EQ.WORKERS or sorted(by.get("work", [])) != sorted(panel["work"]) \
            or sorted(by.get("qual_lengau", [])) != sorted(panel["duplicates"]) or len(by.get("sentinel", [])) != EQ.SENTINELS \
            or max(conc.values()) < E2_QUALIFIED_REP_SLOTS:
        return [], "the attempt's plan is not the declared panel at the qualified concentration (76 slots, >= 61 on one replicate)"
    if run == EQ.RUNS["E2Q2"]:
        e1s = _nonrejected(leds, lambda r: r == EQ.RUNS["E2Q1"])
        if not e1s or any(x.get("ingestion") != "dispositioned" for _, x in e1s):
            return [], "an E2Q2 release needs every E2Q1 attempt dispositioned (E2Q1 ended without a usable bundle)"
    if len(_nonrejected(leds, is_e2_qual)) > E2_MAX_QUAL_INSTANCES:
        return [], f"more than {E2_MAX_QUAL_INSTANCES} epoch-2 qualification instances exist: the allowance counter is exceeded"
    try:
        text = open(review_path).read()
    except Exception as e:
        return [], f"the actual-result review is unreadable ({type(e).__name__})"
    lit = EQ.RELEASE_LITERAL.format(sha=csha, keys=",".join(keys))
    if lit not in text.split("\n") or "FAVOURABLE" not in text:
        return [], "the actual-result review carries no FAVOURABLE verdict with the epoch-2 literal release line for this certificate"
    return list(keys), ""


def _nonrejected_run(leds, run):
    return [a for _, a in _nonrejected(leds, lambda r: r == run)]


def e2q_admission_problem(contract, rel, leds):
    """REVISION 7: '' when an E2Q1/E2Q2 admission is permitted by the release state and the declared retry rule."""
    q = rel.get("qualification_e2") or {}
    if not q.get("ok"):
        return ("ec2_release_state.json does not permit the epoch-2 qualification (row 23 success, the benchmark fence and a "
                "reviewed qualification_e2 permission record written by qual_permit.py --epoch2)")
    if contract == "E2Q1" and _nonrejected_run(leds, EQ.RUNS["E2Q1"]):
        return "E2Q1 is ONE instance: a further attempt is E2Q2 under its own rule, never a retry by outcome"
    if contract == "E2Q2":
        if not q.get("e2q2_ok"):
            return "E2Q2 needs its own reviewed permission record (qualification_e2.e2q2) naming E2Q1's external-cause end"
        e1s = _nonrejected_run(leds, EQ.RUNS["E2Q1"])
        if not e1s or any(a.get("state") != "reconciled" or a.get("ingestion") != "dispositioned" for a in e1s):
            return "E2Q2 only after E2Q1 ended without a usable bundle: every non-rejected E2Q1 attempt reconciled and dispositioned"
        if _nonrejected_run(leds, EQ.RUNS["E2Q2"]):
            return "E2Q2 is at most one instance"
    return ""


def production_release_problem(rel, epoch, opmanifest_sha):
    """REVISION 7: '' when production of `epoch` is released: the release state's production block is ok, its certificate
    released THIS epoch, and (epoch 2) the operational manifest is the one the certificate bound."""
    pr = rel.get("production") or {}
    if not pr.get("ok"):
        return "ec2_release_state.json does not permit production: no reviewed production release (prod_authority.py release-adopt)"
    if pr.get("epoch") != int(epoch):
        return f"the adopted release is for epoch {pr.get('epoch')}, not epoch {epoch}: each epoch needs its own reviewed release"
    if int(epoch) >= 2 and pr.get("production_opmanifest_sha256") != opmanifest_sha:
        return "the operational manifest is not the production manifest the epoch-2 certificate bound"
    return ""


def release_state(leds=None):
    """The reviewed release state (row 23, qualification, production). Every claim it makes must be backed by a file whose
    sha256 it pins; a missing or differing file reads as NOT released. Production is released only by release_problem.
    REVISION 7: also the epoch-2 qualification permission (`qualification_e2`, absent = not permitted) and the released
    epoch / bound production manifest of the production block."""
    r = json.load(open(RELEASE_STATE))
    assert r.get("schema") == "t1-ec2-release-state-1", "ec2_release_state.json schema"
    def backed(d, pk="path", hk="sha256"):
        p = d.get(pk); return bool(p) and os.path.exists(os.path.join(HERE, p)) and L.sha256(os.path.join(HERE, p)) == d.get(hk)
    r23 = r["row23"]; q = r["qualification"]; pr = r["production"]
    r23["ok"] = bool(r23.get("declared_success")) and backed(r23, "report_path", "report_sha256")
    fence_ok = os.path.exists(os.path.join(HERE, "runs", "BENCH_FENCE.json"))
    q["ok"] = r23["ok"] and bool(q.get("permitted")) and bool(q.get("owner_accepted_ceilings")) and backed(q, "record_path", "record_sha256") \
        and q.get("ceilings_usd") == QUAL_CEILINGS_USD \
        and fence_ok                                                         # D-2: only after the benchmark cutover (qual_permit.py)
    q2 = r.get("qualification_e2") if isinstance(r.get("qualification_e2"), dict) else {}
    q2["ok"] = r23["ok"] and fence_ok and q2.get("permitted") is True and backed(q2, "record_path", "record_sha256")
    e2q2 = q2.get("e2q2") if isinstance(q2.get("e2q2"), dict) else {}
    q2["e2q2_ok"] = q2["ok"] and e2q2.get("permitted") is True and backed(e2q2, "record_path", "record_sha256")
    r["qualification_e2"] = q2
    pr["ok"], pr["derived_released_attempts"], pr["why"], pr["epoch"], pr["production_opmanifest_sha256"] = False, [], "not released", None, None
    if pr.get("released") and backed(pr, "certificate_path", "certificate_sha256") and backed(pr, "review_path", "review_sha256"):
        cp = os.path.join(HERE, pr["certificate_path"])
        try:
            e2 = json.load(open(cp)).get("schema") == E2_CERT_SCHEMA
        except Exception:
            e2 = False
        if not (q2["ok"] if e2 else q["ok"]):                                # each epoch's release needs its own qualification gate
            return r
        keys, why = release_problem(cp, os.path.join(HERE, pr["review_path"]), leds)
        if not why and sorted(pr.get("released_attempts") or []) != sorted(keys):
            why = "the release state lists other attempts than its certificate releases"
        pr["ok"], pr["derived_released_attempts"], pr["why"] = (not why), (keys if not why else []), why
        if not why:
            cert = json.load(open(cp))
            pr["epoch"] = EQ.EPOCH if e2 else 1
            pr["production_opmanifest_sha256"] = ((cert.get("bound") or {}).get("opmanifests") or {}).get("production") if e2 else None
    return r


def release_adopt(cert_rel, review_rel):
    """Write the production block from a PASSING release validation (paths relative to aws_ec2/)."""
    keys, why = release_problem(os.path.join(HERE, cert_rel), os.path.join(HERE, review_rel))
    if why:
        raise ValueError(why)
    r = json.load(open(RELEASE_STATE))
    r["production"] = dict(released=True, certificate_path=cert_rel, certificate_sha256=L.sha256(os.path.join(HERE, cert_rel)),
                           review_path=review_rel, review_sha256=L.sha256(os.path.join(HERE, review_rel)), released_attempts=keys)
    tmp = RELEASE_STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(r, f, indent=1); f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, RELEASE_STATE)
    if not release_state()["production"]["ok"]:
        raise ValueError("the adopted release state does not validate (row 23 / qualification backing)")
    return keys


def exclusion_problem(leds, region):
    """R1-7: no production/qualification admission while a benchmark attempt is unresolved or running (its launcher is not
    under the global lock), nor while an unresolved attempt was made in another region."""
    for run, l in leds.items():
        for a in l["attempts"]:
            live = a.get("state") in ("intent", "launched", "ambiguous")
            if run_class(run) == "benchmark" and live:
                return f"benchmark attempt {run}/{a['attempt']} is {a['state']}: benchmark launches are outside the global lock"
            if run_class(run) in PROD_CLASSES and live and a.get("region", region) != region:
                return f"attempt {run}/{a['attempt']} is {a['state']} in {a.get('region')}, not {region}: resolve it before changing region"
    return ""


def inventory(leds, gen, rel, now=None):
    """The sealed authority inventory of every production/qualification attempt (Lengau's ingestion, status and activation
    read it; row19_ec2_state.inventory_problem is its contract)."""
    now = time.time() if now is None else now
    atts = {}
    for run, l in leds.items():
        cls = run_class(run)
        if cls not in PROD_CLASSES:
            continue
        for a in l["attempts"]:
            key = f"{run}/{a['attempt']}"
            atts[key] = dict(key=key, run=run, attempt=a["attempt"], attempt_id=a["attempt_id"], sequence=a["sequence"],
                             state=a["state"], ingestion=a.get("ingestion", "pending"), **{"class": cls}, contract=a["contract"],
                             disposition_requested=bool(a.get("disposition_request")) and a.get("ingestion", "pending") == "pending",
                             plan_sha256=a["plan_sha256"], coordinates=a.get("coordinates", []), sentinels=a.get("sentinels", []),
                             duplicates=a.get("duplicates", []), charged_usd=round(charged(a), 6))
    own = owned(leds)
    b = budget(leds, now)
    body = dict(schema=ES.INVENTORY_SCHEMA, generation=gen, at=now, attempts=atts,
                owners={f"{c[0]}/{c[1]}": [k, s] for c, (k, s) in sorted(own.items())}, fence=fence(leds),
                release=dict(production_released=rel["production"]["ok"], released_attempts=sorted(rel["production"]["derived_released_attempts"])),
                usd=dict(b, envelope_usd=PROD_ENVELOPE_USD, cap_usd=CUMULATIVE_CAP_USD))
    return ES.seal(body)


def write_inventory(now=None):
    """Under the authority lock: advance the generation, seal, write runs/inventory/inventory_g<gen>.json ONCE (never
    overwritten: R2-1) and latest.json. Returns the archive path."""
    leds = ledgers()
    st, _ = bump(state())
    inv = inventory(leds, st["generation"], release_state(leds), now)
    why = ES.inventory_problem(inv, now)
    if why:
        raise RuntimeError(f"the authority produced an invalid inventory: {why}")
    os.makedirs(INV_DIR, exist_ok=True)
    p = os.path.join(INV_DIR, f"inventory_g{st['generation']}.json")
    body = json.dumps(inv, indent=1, sort_keys=True)
    tmp = f"{p}.tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        f.write(body); f.flush(); os.fsync(f.fileno())
    try:
        os.link(tmp, p)                                   # fails if the archive exists: a generation is sealed once
    except FileExistsError:
        os.unlink(tmp)
        raise RuntimeError(f"{os.path.basename(p)} already exists: a sealed generation is immutable (authority state behind its archives?)")
    os.unlink(tmp)
    lp = os.path.join(INV_DIR, "latest.json"); tmp = lp + ".tmp"
    with open(tmp, "w") as f:
        f.write(body); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, lp)
    return p


def ack(run, n, register_path):
    """Release an attempt's ownership on the Lengau register's evidence (recoverable: idempotent on the same entry)."""
    led = L.load(run); a = next(x for x in led["attempts"] if x["attempt"] == n)
    reg = json.load(open(register_path)); e = (reg.get("attempts") or {}).get(a["attempt_id"])
    if reg.get("schema") != ES.REGISTER_SCHEMA or e is None:
        raise ValueError("the register carries no entry for this attempt")
    if e.get("state") != "ingested" or e.get("key") != f"{run}/{n}" or e.get("sequence") != a["sequence"] or e.get("plan_sha256") != a["plan_sha256"]:
        raise ValueError(f"the register entry is {e.get('state')} / {e.get('key')} / seq {e.get('sequence')}: not this attempt ingested")
    unprod = e.get("unproduced") or {}
    if set(e["coordinates"]) & set(unprod):
        raise ValueError("the register lists a coordinate both published and unproduced")
    if sorted(list(e["coordinates"]) + list(unprod)) != sorted(f"{r}/{i}" for r, i in a["coordinates"]):
        raise ValueError("the register's published + unproduced coordinates are not exactly the attempt's owned coordinates")
    unk = {k: u for k, u in sorted(unprod.items()) if not isinstance(u, dict) or E2R.kind(u.get("outcome")) is None}
    if unk:                                                   # REVISION 6 (A2): the shared classification, also here
        raise ValueError(f"the register lists unproduced outcomes of no qualifying class: {dict(list(unk.items())[:3])}")
    digest = ES.sha_bytes(ES.canonical(e))
    if a.get("ingestion") == "ingested":
        if (a.get("ingest_ack") or {}).get("entry_sha256") != digest:
            raise ValueError("already acknowledged against a different register entry")
        return False
    if a.get("ingestion") != "pending" or a.get("state") != "reconciled":
        raise ValueError(f"attempt is {a.get('state')}/{a.get('ingestion')}: only a reconciled pending attempt is acknowledged")
    a["ingestion"] = "ingested"; a["ingest_ack"] = dict(entry_sha256=digest, register_sha256=L.sha256(register_path), at=time.time(),
                                                        **({"unproduced": unprod} if "unproduced" in e else {}))
    L.save(run, led); return True


def disposition(run, n, reason):
    """REQUEST a disposition (R1-2): ownership stays until the root acknowledges the fence (disposition_confirm)."""
    led = L.load(run); a = next(x for x in led["attempts"] if x["attempt"] == n)
    if a.get("state") != "reconciled" or a.get("ingestion") != "pending":
        raise ValueError(f"attempt is {a.get('state')}/{a.get('ingestion')}: only a reconciled pending attempt is dispositioned")
    if a.get("disposition_request"):
        return False
    a["disposition_request"] = dict(reason=reason, at=time.time())
    L.save(run, led); return True


def disposition_confirm(run, n, ack_path):
    """Release ownership on the root's acknowledgement of the fence (R1-2). Idempotent on the same acknowledgement."""
    led = L.load(run); a = next(x for x in led["attempts"] if x["attempt"] == n); key = f"{run}/{n}"
    ack = json.load(open(ack_path)); asha = L.sha256(ack_path)
    if a.get("ingestion") == "dispositioned":
        if (a.get("disposition_ack") or {}).get("ack_sha256") != asha:
            raise ValueError("already confirmed against another acknowledgement")
        return False
    if a.get("ingestion") != "pending" or not a.get("disposition_request"):
        raise ValueError(f"attempt is {a.get('ingestion')} with no disposition request")
    if ack.get("schema") != ES.ACK_SCHEMA:
        raise ValueError("not a root acknowledgement")
    if (ack.get("mode"), ack.get("root"), ack.get("manifest_sha256")) != ("canonical", os.path.abspath(CANONICAL_ROOT), CANONICAL_MANIFEST_SHA):
        raise ValueError(f"the acknowledgement is not the canonical screen root's ({ack.get('mode')} {ack.get('root')}): "
                         "only the canonical root's fence releases ownership")
    if key in (ack.get("refused") or {}):
        raise ValueError(f"the root REFUSED the disposition: {ack['refused'][key]} - the attempt keeps owning")
    f = (ack.get("dispositioned") or {}).get(key)
    want = dict(attempt_id=a["attempt_id"], sequence=a["sequence"],
                coordinates_sha256=ES.sha_bytes(ES.canonical(sorted(a.get("coordinates", [])))))
    if f != want:
        raise ValueError("the acknowledgement does not fence this attempt (id, sequence, coordinates)")
    invp = os.path.join(INV_DIR, f"inventory_g{int(ack['generation'])}.json")
    inv = json.load(open(invp)) if os.path.exists(invp) else {}
    if inv.get("sha256") != ack.get("inventory_sha256") or not (inv.get("attempts", {}).get(key) or {}).get("disposition_requested"):
        raise ValueError("the acknowledged inventory is not a sealed inventory of this authority carrying the request")
    a["ingestion"] = "dispositioned"; a["disposition_ack"] = dict(ack_sha256=asha, generation=ack["generation"], at=time.time())
    L.save(run, led); return True


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("inventory"); sub.add_parser("budget")
    k = sub.add_parser("ack"); k.add_argument("--run", required=True); k.add_argument("--attempt", type=int, required=True); k.add_argument("--register", required=True)
    d = sub.add_parser("disposition"); d.add_argument("--run", required=True); d.add_argument("--attempt", type=int, required=True); d.add_argument("--reason", required=True)
    c = sub.add_parser("disposition-confirm"); c.add_argument("--run", required=True); c.add_argument("--attempt", type=int, required=True); c.add_argument("--ack", required=True)
    r = sub.add_parser("release-adopt"); r.add_argument("--certificate", required=True); r.add_argument("--review", required=True)
    a = ap.parse_args()
    try:
        with authority_lock(wait_s=60):
            if a.cmd == "budget":
                print(json.dumps(dict(budget(ledgers()), envelope=PROD_ENVELOPE_USD, cap=CUMULATIVE_CAP_USD, ceilings=QUAL_CEILINGS_USD), indent=1)); return 0
            if a.cmd == "release-adopt":
                print("released:", release_adopt(a.certificate, a.review))
            if a.cmd in ("ack", "disposition", "disposition-confirm"):
                with L.run_lock(a.run, wait_s=60):
                    if a.cmd == "ack":
                        changed = ack(a.run, a.attempt, a.register)
                    elif a.cmd == "disposition":
                        changed = disposition(a.run, a.attempt, a.reason)
                    else:
                        changed = disposition_confirm(a.run, a.attempt, a.ack)
            print(write_inventory()); return 0                               # every seal is a new generation (R2-1)
    except BlockingIOError:
        sys.exit("REFUSED: another authority operation holds runs/.authority.lock")


if __name__ == "__main__":
    sys.exit(main())
