"""Row 19 screen on EC2: admit and dispatch ONE instance of a production epoch or of a predeclared qualification part
(Codex RSC f3dd3d7; repaired for Codex RSC 0483db4 V10-1, V10-2, V10-6, V10-7, V10-8). Mac only.

    python3 prod_launch.py --contract Q1 --epoch 1 --partition ../chpc/row19_partition_e1.json --manifest prod/manifest_q1_e1.json \
        --snapshot ../chpc/results/row19_screen --tarball ~/aws_t1_bench/t1_toolchain_lengau.tgz [--dry-run]
    python3 prod_launch.py --contract production --epoch 1 ...      # only after the reviewed production release
    python3 prod_launch.py --contract production --epoch 1 --recover # re-issue an unresolved attempt's SAME request (STOP-checked)

Admission, under the GLOBAL authority lock and the run lock (shared with the reaper), refuses unless ALL hold:
  STOP     no STOP anywhere: the run's and the global local STOP (runs/STOP), the run's and the global S3 STOP (bounded
           30 s calls; an API failure is not proof of absence and refuses), the Lengau screen root STOP and ec2/HOLD in the
           pulled snapshot. Recovery checks the same before re-issuing.
  release  ec2_release_state.json: Q1/Q2 need row 23's declared success (pinned report) AND qualification permitted with
           the owner's acceptance of the per-part USD ceilings; production needs the reviewed release certificate (outcome
           RELEASE). Q2 also needs a reconciled Q1 attempt.
  inputs   the partition is the one the LATEST adopted controls (chpc/row19_screen_controls.json) pin, and the pulled root
           carries its serialized activation proof; the operational manifest is the exact derivation of 43b75f94 for this
           epoch and contract (row19_ec2_state.operational_problem).
  receipt  the newest whole-role refit receipt is a FRESH PRODUCTION one (explicit true flags, schema, role), alarm-free,
           finite, not in the future, <= 2,700 s old; it binds the snapshot's EC2 state (ec2.bound = row19_ec2_state.bound of
           the snapshot root) AND the authority inventory this Mac last sealed, at the CURRENT generation - so a newly
           journaled attempt refuses until the inventory is copied to Lengau and a new receipt taken. Completion comes from the
           receipt's own bound verifier document (record ok), not from file names.
  budget   prod_authority.budget_problem: global production envelope across all epochs/qualification/retries, the cumulative
           USD 3,000 cap over baseline + every run, the per-part qualification ceiling.
Then: global sequence reserved, the immutable plan (bound to partition, operational manifest, activation, sequence and the
contract) and request written, the attempt journaled 'intent' BEFORE RunInstances, the generation bumped and a new
inventory sealed; dispatch through the reviewed issue/resolve and the reaper.

Plans by contract (row19_ec2_state.CONTRACTS; QUALIFICATION_PLAN.md): production = up to 72 block coordinates in the fixed
order + 4 sentinels; Q1 = 48 block coordinates (index 199 and 198 of reps 3..26, owned) + 24 Lengau-completed
coordinates (index 1 and 2 of reps 3..14, duplicates) + 4 sentinels = 76; Q2 = the 24 coordinates index 199 of reps 3..26
recomputed on a c7a.12xlarge at cap 0.70 (duplicates; Q1 owns them).

REVISION 3 (Codex RSC 3dc0daf R1-1, R1-3, R1-5, R1-7). STOP absence is accepted ONLY when S3 answers that the object does
not exist (HeadObject 404 / NoSuchKey / NotFound); every other outcome - credentials, configuration, connection, timeout,
throttling, any unparsed failure - refuses admission and recovery. The activation proof must be canonical with its controls
lineage intact (row19_partition.activation_problem with the current controls). The snapshot root's registered EC2 artifacts
and installed inventory are rechecked now (row19_ec2_state.current_problems), not trusted from the receipt's metadata. An
admission refuses while a benchmark attempt is unresolved/running or an unresolved attempt was made in another region
(prod_authority.exclusion_problem); every attempt and request records its region and zone, and recovery refuses an attempt
of another region.

REVISION 4 (Codex RSC 299f4b7 R2-1, R2-2, R2-3). Controls are read only through row19_partition.adopted_controls (the
current adopted, tracked, unmodified bytes): a later unadopted candidate refuses here as on Lengau. STOP (every source) and
the receipt's freshness are checked AGAIN after the uploads, immediately before the attempt is journaled and RunInstances is
issued, and before every issue and re-issue of the saved request (dispatch_guard, passed to bench_launch.finish): a STOP
written during staging, or a receipt that aged past 2,700 s, dispatches nothing - a never-issued attempt is withdrawn
('rejected', no instance can exist), an issued one stays ambiguous and funded. After the dispatch outcome (launched /
rejected / ambiguous) the inventory is sealed again, so every lifecycle state is an installable generation.

REVISION 5 - CANDIDATE, not adopted (EC2 provider epoch 2; Codex design reviews/2026-10-17_row19_resize_codex.md s.3, s.4,
s.6 item 5). For a schema-2 partition (explicit coordinate set) the production plan is 72 work coordinates REPLICATE-COMPLETE
from the owned set (prod_authority.allocate: ascending rep then index; completed, owned and EC2 crash-excluded coordinates
skipped) + 4 Lengau-completed sentinels on the 76-worker c7a.24xlarge contract. Admission additionally refuses (under the
same global authority lock, after the existing envelopes) when the FLEET CEILING of five live production/qualification
instances is reached (prod_authority.fleet_problem) and, for epoch 2, when the validated funding declaration's bounds would be
exceeded (prod_authority.epoch2_problem: base batches + 4 extra, 2 qualification instances, USD 300 allowance, forecast +
allowance). Production stays shut until a reviewed epoch-2 release (QUALIFICATION_E2.md; not built).

REVISION 6 - CANDIDATE, not adopted (Codex review reviews/2026-10-17_e2_p80r_codex_review.md A3, A4, lifetime follow-up).
  packing   a schema-2 production plan never carries more than prod_authority.E2_QUALIFIED_REP_SLOTS (61, E2Q1's declared
            concentration) workers of any role on one replicate (row19_ec2_e2rules.concentration_problem on the built
            slots, sentinels included); the allocator already caps work at 57 per replicate per batch.
  funding   the epoch gate validates the funding declaration against the AUTHENTICATED Q2 basis of the same ledgers it
            admits under (prod_authority.funding_problem(fund, part, leds)).
  lifetime  an epoch-2 admission's lifetime must be the funded lifetime_s of the declaration (79,200 s); the operational
            manifest maker alone is not the authority. Binding the exact QUALIFIED operational manifest belongs to the
            epoch-2 release branch (not built).

REVISION 7 - CANDIDATE, not adopted (EC2 provider epoch 2 QUALIFICATION, chpc/candidate_e2q/DESIGN_e2q.md;
chpc/candidate_e2/QUALIFICATION_E2.md s.2, s.5).
  E2Q       contracts E2Q1 and E2Q2 (row19_ec2_state REVISION 4) admit as runs qual-E2Q1 / qual-E2Q2 of an epoch-2 schema-2
            partition: the plan is the DECLARED panel (--panel, default aws_ec2/prod/panel_e2q_e2.json, regenerated from the
            partition and its bound claims snapshot by row19_ec2_e2qual.panel_problem) - its 52 work coordinates, each still
            free (owned by epoch 2, not completed, not owned by another attempt, not crash-excluded), its 20 duplicates, each
            Lengau-completed in the receipt, and 4 token sentinels outside the duplicates; the built plan must carry >= 61
            workers on one replicate. The gate is prod_authority.e2q_admission_problem (qualification_e2 permission; E2Q1 one
            instance; E2Q2 its own record, only after every E2Q1 attempt was dispositioned, at most one); the money is
            epoch2_problem's (2 qualification instances inside the USD 300 allowance) at the funded 79,200 s lifetime.
  release   production of an epoch needs the adopted release OF THAT EPOCH (prod_authority.production_release_problem): an
            epoch-1 release never admits epoch-2 production, and an epoch-2 production admission must use the production
            operational manifest the schema-3 certificate bound."""
import argparse, glob, json, math, os, sys, time, uuid

SRC = os.path.dirname(os.path.abspath(__file__))
if SRC in sys.path:
    sys.path.remove(SRC)
sys.path.insert(0, SRC)
import prod_authority as PA                                  # resolves t1_access, puts aws_ec2/, chpc/ and the candidate on the path
import bench_launch as L
HERE = PA.HERE                                               # aws_ec2/ (attest.py, prod_userdata.sh, runs/); = SRC once promoted
T1 = PA.T1
import row19_partition as RP
import row19_ec2_state as ES
import row19_ec2_e2rules as E2R
import row19_ec2_e2qual as EQ
QUAL_CONTRACTS = ("Q1", "Q2") + EQ.CONTRACTS                 # REVISION 7: every qualification contract (22 h lifetime, qual-* run)


def run_of(contract, epoch):
    return PA.qual_run(contract) if contract in QUAL_CONTRACTS else PA.run_name(epoch)


def panel_for(part, psha, panel_path):
    """REVISION 7: the declared E2Q panel at `panel_path`, validated against the partition and its bound claims snapshot."""
    panel = json.load(open(panel_path))
    snapp = os.path.join(T1, (panel.get("claims_snapshot") or {}).get("path") or "-")
    why = EQ.panel_problem(panel, part, psha, json.load(open(snapp)), L.sha256(snapp))
    if why:
        raise ValueError(f"the E2Q panel: {why}")
    return panel

PROD_SHA = "43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c"
RECEIPT_MAX_AGE_S = 2700
WATCH_SCHEMA = "row19-screen-watch-1"
Q1_BLOCK = [(r, i) for i in (199, 198) for r in range(3, 27)]
Q1_LENGAU = [(r, i) for r in range(3, 15) for i in (1, 2)]
Q2_REPEAT = [(r, 199) for r in range(3, 27)]


def s3_stop_key(run=None):
    return f"s3://{L.BUCKET}/code/t1_access/aws_bench/{run + '/' if run else ''}STOP"


ABSENT_CODES = ("404", "NoSuchKey", "NotFound")
MODE = "canonical"                                                        # tests alone set "sandbox"


def s3_stop_present(key):
    """True when the STOP object exists, False ONLY when S3 proves it absent (HeadObject 404/NoSuchKey/NotFound); raises
    L.AwsError for every other outcome (R1-5: no unproved absence)."""
    bucket, _, k = key[len("s3://"):].partition("/")
    try:
        L.aws("s3api", "head-object", "--bucket", bucket, "--key", k, timeout=30)
        return True
    except L.AwsError as e:
        if e.code in ABSENT_CODES:
            return False
        raise


def stop_problem(run, snapshot):
    """Every STOP source; anything but a proved absence on S3 refuses (fail closed)."""
    found = [p for p in (os.path.join(L.run_dir(run), "STOP"), os.path.join(PA.HERE, "runs", "STOP"),
                         os.path.join(snapshot, "live", "refit", "root", "STOP"),
                         os.path.join(snapshot, "live", "refit", "root", "ec2", "HOLD")) if os.path.exists(p)]
    for key in (s3_stop_key(run), s3_stop_key()):
        try:
            if s3_stop_present(key):
                found.append(key)
        except L.AwsError as e:
            return f"the S3 STOP check did not prove absence ({e.code or 'no service code'}: {str(e)[:160]})"
        except Exception as e:
            return f"the S3 STOP check failed ({type(e).__name__}: {e})"
    return f"STOP/HOLD in force ({found})" if found else ""


def snapshot_state(snapshot, part, now=None):
    """(Lengau-verified completed coordinates, receipt name, receipt) from the newest whole-role refit receipt, strictly."""
    now = time.time() if now is None else now
    recs = sorted(glob.glob(os.path.join(snapshot, "receipts", "watch_refit_*.json")))
    if not recs:
        raise ValueError("no refit receipt in the snapshot")
    w = json.load(open(recs[-1])); t = w.get("time")
    if w.get("schema") != WATCH_SCHEMA or w.get("role") != "refit" or w.get("fresh") is not True or w.get("production") is not True:
        raise ValueError(f"{os.path.basename(recs[-1])} is not a fresh production refit receipt")
    if w.get("alarms") != []:
        raise ValueError(f"{os.path.basename(recs[-1])} carries alarms or no alarm list")
    if not (isinstance(t, (int, float)) and not isinstance(t, bool) and math.isfinite(t)) or t > now + 60 or now - t > RECEIPT_MAX_AGE_S:
        raise ValueError(f"{os.path.basename(recs[-1])}: time {t!r} not finite, in the future or older than {RECEIPT_MAX_AGE_S} s")
    b = w.get("bound") or {}
    vp = os.path.join(snapshot, "receipts", b.get("verify_file") or "-")
    if not os.path.exists(vp) or L.sha256(vp) != b.get("verify_file_sha256"):
        raise ValueError("the receipt's bound verifier document is missing or not its bytes")
    units = json.load(open(vp)).get("units") or {}
    done = {tuple(int(x) for x in k.split("/")) for k, v in units.items() if (v.get("record") or {}).get("ok")}
    root = os.path.join(snapshot, "live", "refit", "root")
    if (w.get("ec2") or {}).get("bound") != ES.bound(root):
        raise ValueError("the receipt's EC2 binding is not the snapshot root's")
    cur = ES.current_problems(root, json.load(open(os.path.join(T1, "chpc", "row19_screen_manifest.json"))), require=True)
    if cur:                                                                  # R1-3: the artifacts as they are now
        raise ValueError(f"the snapshot's registered EC2 artifacts or installed inventory fail now: {cur[:3]}")
    return done, os.path.basename(recs[-1]), w


def inventory_bound_problem(w):
    """The receipt must bind the inventory this authority last sealed, at the current generation."""
    lp = os.path.join(PA.INV_DIR, "latest.json")
    if not os.path.exists(lp):
        return "no sealed inventory yet (python3 prod_authority.py inventory, then install it on Lengau: chpc/row19_ec2_root.py install)"
    inv = json.load(open(lp))
    if inv.get("generation") != PA.state()["generation"]:
        return "the sealed inventory is not the current generation; seal and copy it"
    if (w.get("ec2") or {}).get("bound", {}).get("inventory_sha256") != L.sha256(lp):
        return "the receipt does not bind the current authority inventory: install it on Lengau (chpc/row19_ec2_root.py install) and take a fresh receipt"
    return ""


def controls_doc():
    """The CURRENT adopted controls (R2-2); raises ValueError when the canonical file is not the adopted bytes."""
    ctl, why = RP.adopted_controls()
    if why:
        raise ValueError(why)
    return ctl


def controls_pin():
    return (controls_doc()["versions"][-1].get("partition") or {}).get("sha256")


def build(contract, part, leds, done, token, panel=None):
    """(work, duplicates, sentinels) for the contract; raises when the predeclared panel cannot be built as declared."""
    lengau = {c for c in done if not RP.blocked(part, *c)}
    if contract in EQ.CONTRACTS:                                         # REVISION 7: the declared epoch-2 panel
        if part.get("schema") != RP.SCHEMA2 or int(part["epoch"]) != EQ.EPOCH or panel is None:
            raise ValueError("the E2Q contracts run only on the epoch-2 schema-2 partition with its declared panel")
        work = [tuple(c) for c in panel["work"]]; dups = [tuple(c) for c in panel["duplicates"]]
        own = PA.owned(leds); ex = PA.ec2_crash_excluded(leds)
        bad = [c for c in work if not RP.blocked(part, *c) or c in done or c in own or c in ex]
        if bad:
            raise ValueError(f"E2Q's work coordinates are not all free epoch-2 coordinates, e.g. {bad[:3]}")
        miss = [c for c in dups if c not in lengau]
        if miss:
            raise ValueError(f"E2Q's Lengau duplicates are not all Lengau-completed in the receipt, e.g. {miss[:3]}")
        sent = PA.sentinels(lengau, token, exclude=dups)
        conc = E2R.rep_concentration([dict(rep=r) for r, _ in work + dups + sent])
        if len(work) + len(dups) + len(sent) != EQ.WORKERS or max(conc.values()) < E2R.QUALIFIED_REP_SLOTS:
            raise ValueError(f"the E2Q plan does not carry the declared shape (76 workers, >= {E2R.QUALIFIED_REP_SLOTS} on one replicate)")
        return work, dups, sent
    if contract == "production":
        excluded = PA.ec2_crash_excluded(leds) if part.get("schema") == RP.SCHEMA2 else set()
        work = PA.allocate(part, leds, done, ES.CONTRACTS["production"]["workers"] - PA.SENTINELS_PER_ATTEMPT, excluded)
        if not work:
            raise ValueError("the partition block has no free coordinate left")
        sent = PA.sentinels(lengau, token)
        if part.get("schema") == RP.SCHEMA2:                                # REVISION 6 (A3): only the qualified shape
            why = E2R.concentration_problem([dict(rep=r) for r, _ in work + sent], PA.E2_QUALIFIED_REP_SLOTS)
            if why:
                raise ValueError(f"the production plan is outside the qualified packing: {why}")
        return work, [], sent
    if contract == "Q1":
        own = PA.owned(leds)
        bad = [c for c in Q1_BLOCK if not RP.blocked(part, *c) or c in done or c in own]
        if bad:
            raise ValueError(f"Q1's block coordinates are not all free block coordinates, e.g. {bad[:3]}")
        miss = [c for c in Q1_LENGAU if c not in lengau]
        if miss:
            raise ValueError(f"Q1's Lengau duplicates are not all Lengau-completed, e.g. {miss[:3]}")
        return list(Q1_BLOCK), list(Q1_LENGAU), PA.sentinels(lengau, token, exclude=Q1_LENGAU)
    q1 = [a for a in leds.get(PA.qual_run("Q1"), {"attempts": []})["attempts"] if a.get("state") == "reconciled"]
    if not q1:
        raise ValueError("Q2 compares with Q1: no reconciled Q1 attempt")
    return [], list(Q2_REPEAT), []


def epoch_problem(part, leds, run, worst, lifetime_s=None):
    """REVISION 5: a schema-2 epoch admits only inside its validated funding declaration's bounds. REVISION 6: validated
    against the authenticated Q2 basis of these ledgers (A4), at the funded lifetime only."""
    if part.get("schema") != RP.SCHEMA2:
        return ""
    if int(part["epoch"]) != 2:
        return f"epoch {part['epoch']}: only epoch 2's funding bounds are declared"
    try:
        fund = json.load(open(PA.E2_FUNDING))
    except Exception as e:
        return f"no readable epoch-2 funding declaration ({type(e).__name__})"
    why = PA.funding_problem(fund, part, leds)
    if why:
        return why
    if lifetime_s is None or int(lifetime_s) != int(fund["lifetime_s"]):
        return f"epoch 2 admits only at the funded lifetime {fund['lifetime_s']} s, not {lifetime_s!r}"
    return PA.epoch2_problem(leds, run, worst, fund)


def receipt_age_problem(w, now=None):
    now = time.time() if now is None else now
    t = w.get("time")
    if not (isinstance(t, (int, float)) and not isinstance(t, bool) and math.isfinite(t)) or t > now + 60 or now - t > RECEIPT_MAX_AGE_S:
        return f"the receipt's time {t!r} is no longer within {RECEIPT_MAX_AGE_S} s"
    return ""


def dispatch_guard(run, snapshot, w):
    """R2-3: called immediately before EVERY RunInstances issue/re-issue; '' lets the call go out."""
    def guard():
        return stop_problem(run, snapshot) or receipt_age_problem(w)
    return guard


def gate_problem(contract, epoch, rel, leds, opmanifest_sha):
    """REVISION 7: the release-state gate of one admission: Q1/Q2 the epoch-1 qualification permission; E2Q1/E2Q2 the
    epoch-2 permission and retry rule (prod_authority.e2q_admission_problem); production the adopted release OF THIS EPOCH
    with, for epoch 2, the operational manifest its certificate bound (prod_authority.production_release_problem)."""
    if contract in ("Q1", "Q2"):
        return "" if rel["qualification"]["ok"] else (f"ec2_release_state.json does not permit {contract} (row 23 success / "
                                                      "qualification permission and owner-accepted ceilings)")
    if contract in EQ.CONTRACTS:
        return "" if int(epoch) == EQ.EPOCH and not PA.e2q_admission_problem(contract, rel, leds) else \
            (PA.e2q_admission_problem(contract, rel, leds) or f"{contract} qualifies epoch {EQ.EPOCH} only")
    return PA.production_release_problem(rel, epoch, opmanifest_sha)


def admit(a, now=None):
    run = run_of(a.contract, a.epoch)
    try:
        controls_doc()
    except ValueError as e:
        sys.exit(f"REFUSED: {e}")
    leds = PA.ledgers(); led = L.load(run)
    if any(x.get("state") in ("intent", "ambiguous") for x in led["attempts"]):
        sys.exit(f"REFUSED: an attempt of {run} is unresolved - python3 prod_launch.py --contract {a.contract} --epoch {a.epoch} --recover")
    why = stop_problem(run, a.snapshot)
    if why:
        sys.exit(f"REFUSED: {why} - no new EC2 dispatch")
    why = PA.exclusion_problem(leds, L.REGION)
    if why:
        sys.exit(f"REFUSED: {why}")
    rel = PA.release_state(leds)
    why = gate_problem(a.contract, a.epoch, rel, leds, L.sha256(a.manifest) if a.manifest and os.path.exists(a.manifest) else None)
    if why:
        sys.exit(f"REFUSED: {why}")
    man_prod = json.load(open(os.path.join(T1, "chpc", "row19_screen_manifest.json")))
    part = RP.load(a.partition, man_prod, PROD_SHA); psha = RP.sha_file(a.partition)
    if part["epoch"] != a.epoch or controls_pin() != psha:
        sys.exit("REFUSED: the partition is not this epoch's or not the one the latest adopted controls pin")
    actp = os.path.join(a.snapshot, "live", "refit", "root", "ec2", f"activation_e{a.epoch}.json")
    try:
        why = RP.activation_problem(man_prod, PROD_SHA, part, psha, json.load(open(actp)), controls=controls_doc(), mode=MODE)
    except Exception as e:
        why = f"no activation proof in the snapshot ({type(e).__name__})"
    if why:
        sys.exit(f"REFUSED: {why}")
    opm = json.load(open(a.manifest))
    why = ES.operational_problem(opm, man_prod, PROD_SHA)
    if why or opm["ec2_production"]["epoch"] != a.epoch or opm["ec2_production"]["contract"] != a.contract:
        sys.exit(f"REFUSED: {why or 'the operational manifest is not this epoch and contract'}")
    try:
        done, receipt, w = snapshot_state(a.snapshot, part, now)
    except ValueError as e:
        sys.exit(f"REFUSED: {e}")
    why = inventory_bound_problem(w)
    if why:
        sys.exit(f"REFUSED: {why}")
    c = ES.CONTRACTS[a.contract]
    life = PA.QUAL_LIFETIME_S if a.contract in QUAL_CONTRACTS else int(opm["ec2_production"]["lifetime_s"])
    if a.contract in QUAL_CONTRACTS and int(opm["ec2_production"]["lifetime_s"]) != life:
        sys.exit(f"REFUSED: the qualification lifetime is declared {life} s; the manifest says {opm['ec2_production']['lifetime_s']}")
    worst = PA.worst_usd(life, c["max_price"])
    why = PA.budget_problem(leds, run, worst, rel, now) or PA.fleet_problem(leds) or epoch_problem(part, leds, run, worst, life)
    if why:
        sys.exit(f"REFUSED: {why}")
    st = PA.state(); n = max([x["attempt"] for x in led["attempts"]], default=0) + 1
    token = f"t1-{run}-{n}-{uuid.uuid4().hex[:12]}"
    try:
        panel = panel_for(part, psha, a.panel or PA.E2Q_PANEL) if a.contract in EQ.CONTRACTS else None
        work, dup, sent = build(a.contract, part, leds, done, token, panel)
    except (ValueError, OSError, KeyError) as e:
        sys.exit(f"REFUSED: {e}")
    st, seq = PA.bump(st, sequences=1)
    attempt_id = f"ec2-{run}-a{n}"
    roles = ([("work", x) for x in work] + [("qual_lengau" if a.contract in ("Q1",) + EQ.CONTRACTS else "qual_repeat", x) for x in dup]
             + [("sentinel", x) for x in sent])
    plan = {"job": n, "attempt_id": attempt_id, "sequence": seq, "epoch": a.epoch, "contract": a.contract, "partition_sha256": psha,
            "opmanifest_sha256": L.sha256(a.manifest), "activation_sha256": L.sha256(actp), "instance": dict(c, roles=dict(c["roles"])),
            "lifetime_s": life, "slots": [dict(slot=k, rep=r, indices=[i], role=role) for k, (role, (r, i)) in enumerate(roles)]}
    att_view = dict(attempt_id=attempt_id, sequence=seq, coordinates=[list(x) for x in work], sentinels=[list(x) for x in sent],
                    duplicates=[list(x) for x in dup])
    why = ES.plan_problem(plan, a.contract, att_view, psha, plan["opmanifest_sha256"], plan["activation_sha256"])
    if why:
        sys.exit(f"REFUSED: the built plan fails its own contract ({why})")
    d = L.run_dir(run); planp = os.path.join(d, f"plan_attempt{n}.json")
    json.dump(plan, open(planp, "w"), indent=1)
    files = {"t1_toolchain_lengau.tgz": os.path.expanduser(a.tarball), "manifest_prod.json": a.manifest, "plan.json": planp,
             "attest.py": os.path.join(HERE, "attest.py")}
    sums = {k: L.sha256(p) for k, p in files.items()}
    if sums["t1_toolchain_lengau.tgz"] != L.PINS["t1_toolchain_lengau.tgz"]:
        sys.exit("REFUSED: the toolchain tarball is not the pinned bytes")
    ud = (open(os.path.join(HERE, "prod_userdata.sh")).read().replace("__RUN__", run).replace("__ATTEMPT__", str(n))
          .replace("__LIFETIME_S__", str(life)).replace("__ATTEMPT_ID__", attempt_id)
          .replace("__SUMS__", "\n".join(f"{v}  {k}" for k, v in sums.items())))
    if any(t in ud for t in ("__RUN__", "__ATTEMPT__", "__LIFETIME_S__", "__ATTEMPT_ID__", "__SUMS__")):
        sys.exit("REFUSED: unfilled user-data placeholder")
    udp = os.path.join(d, f"userdata_attempt{n}.sh"); open(udp, "w").write(ud)
    print(f"{attempt_id} ({a.contract}, seq {seq}): {len(work)} owned, {len(dup)} duplicates, {len(sent)} sentinels on {c['itype']} "
          f"cap {c['max_price']:.2f}, lifetime {life} s, worst USD {worst:.2f}; receipt {receipt}")
    ami = json.loads(L.aws("ssm", "get-parameters", "--names", L.AMI_PARAM, "--output", "json").stdout)["Parameters"][0]["Value"]
    tags = [{"ResourceType": rt, "Tags": [{"Key": "project", "Value": "t1"}, {"Key": "row", "Value": "19-ec2"}, {"Key": "run", "Value": run},
                                            {"Key": "attempt", "Value": str(n)}, {"Key": "Name", "Value": attempt_id}]} for rt in ("instance", "volume")]
    args = ["ec2", "run-instances", "--image-id", ami, "--instance-type", c["itype"], "--count", "1", "--client-token", token,
            "--placement", f"AvailabilityZone={L.AZ}", "--iam-instance-profile", f"Name={L.ROLE}",
            "--instance-market-options", json.dumps({"MarketType": "spot", "SpotOptions": {
                "MaxPrice": f"{c['max_price']:.2f}", "SpotInstanceType": "one-time", "InstanceInterruptionBehavior": "terminate"}}),
            "--instance-initiated-shutdown-behavior", "terminate",
            "--block-device-mappings", json.dumps([{"DeviceName": "/dev/xvda", "Ebs": {"VolumeSize": c["volume_gb"], "VolumeType": "gp3", "DeleteOnTermination": True}}]),
            "--metadata-options", "HttpTokens=required", "--tag-specifications", json.dumps(tags), "--user-data", f"file://{udp}", "--output", "json"]
    if a.dry_run:
        try:
            L.aws(*args, "--dry-run")
        except L.AwsError as e:
            print("DRY RUN:", "EC2 authorization OK" if e.code == "DryRunOperation" else str(e)); return 0 if e.code == "DryRunOperation" else 1
        return 1
    for k, p in files.items():
        L.aws("s3", "cp", p, f"s3://{L.BUCKET}/code/t1_access/aws_bench/{run}/attempt_{n}/{k}", "--only-show-errors", timeout=1800)
    guard = dispatch_guard(run, a.snapshot, w)
    why = guard()                                                            # R2-3: after staging, before journaling/issue
    if why:
        sys.exit(f"REFUSED after staging: {why} - nothing journaled, no RunInstances")
    reqp = os.path.join(d, f"request_attempt{n}.json")
    json.dump(dict(client_token=token, args=args, userdata_sha256=L.sha256(udp), sha256=sums, region=L.REGION, az=L.AZ), open(reqp, "w"), indent=1)
    att = dict(attempt=n, sequence=seq, attempt_id=attempt_id, contract=a.contract, state="intent", client_token=token, request=reqp,
               region=L.REGION, az=L.AZ,
               lifetime_s=life, max_price=c["max_price"], anc_h=PA.ANC_H_PROD, s3_fixed=PA.S3_FIXED_PROD, type=c["itype"], ami=ami,
               plan=planp, plan_sha256=L.sha256(planp), coordinates=att_view["coordinates"], sentinels=att_view["sentinels"],
               duplicates=att_view["duplicates"], ingestion="pending",
               results=f"s3://{L.BUCKET}/results/t1_access/aws_bench/{run}/attempt_{n}/", intent_at=time.time(), receipt=receipt)
    led["attempts"].append(att); L.save(run, led)
    PA.write_inventory()                                                     # the intent: a new generation to install
    rc = L.finish(run, led, att, fresh=True, guard=guard)
    PA.write_inventory()                                                     # the dispatch outcome: another generation (R2-1)
    return rc


def recover(a):
    run = run_of(a.contract, a.epoch)
    led = L.load(run)
    att = next((x for x in reversed(led["attempts"]) if x.get("state") in ("intent", "ambiguous")), None)
    if att is None:
        sys.exit("nothing to recover")
    if att.get("region", L.REGION) != L.REGION:                               # R1-7: the region is attempt identity
        sys.exit(f"REFUSED: the attempt was made in {att.get('region')}; this launcher is set to {L.REGION} - recover it there")
    why = stop_problem(run, a.snapshot)
    if why:                                                                  # V10-8: never re-issue a launch under STOP
        sys.exit(f"REFUSED: {why} - the unresolved attempt stays charged at its worst case; resolve it by "
                 f"describe-instances on token {att['client_token']} (the reaper) once STOP is lifted or by hand")
    # D-1 (Codex cf07869): a re-issue needs a correctly bound CURRENT receipt, exactly as fresh admission does after staging -
    # fresh production refit receipt within RECEIPT_MAX_AGE_S binding the current sealed inventory, and that inventory must
    # carry THIS attempt (key, id, sequence, plan, unresolved state): an unrelated fresh receipt cannot authorize an old request.
    # Any failure: REFUSED, zero RunInstances, the attempt keeps its token/region/plan and stays funded at its worst case.
    w, why = recovery_receipt(a, run, att)
    if why:
        sys.exit(f"REFUSED: {why} - no re-issue; the unresolved attempt stays funded at its worst case (token {att['client_token']})")
    base = dispatch_guard(run, a.snapshot, w)
    def guard():                                                         # before EVERY re-issue: STOP + receipt age + binding
        return base() or inventory_bound_problem(w) or attempt_in_inventory_problem(run, att)
    rc = L.finish(run, led, att, fresh=False, guard=guard)
    PA.write_inventory()
    return rc


def attempt_in_inventory_problem(run, att):
    lp = os.path.join(PA.INV_DIR, "latest.json")
    try:
        e = (json.load(open(lp)).get("attempts") or {}).get(f"{run}/{att['attempt']}") or {}
    except Exception as ex:
        return f"the sealed inventory is unreadable ({type(ex).__name__})"
    if (e.get("attempt_id"), e.get("sequence"), e.get("plan_sha256")) != (att["attempt_id"], att["sequence"], att["plan_sha256"]) \
            or e.get("state") not in ("intent", "ambiguous"):
        return "the current sealed inventory does not carry this unresolved attempt (id, sequence, plan, state)"
    return ""


def recovery_receipt(a, run, att):
    """(receipt, '') for a re-issue, or (None, why)."""
    if not a.partition:
        return None, "--partition is required to recover (the receipt is validated against it)"
    try:
        man_prod = json.load(open(os.path.join(T1, "chpc", "row19_screen_manifest.json")))
        part = RP.load(a.partition, man_prod, PROD_SHA)
        if controls_pin() != RP.sha_file(a.partition):
            return None, "the partition is not the one the latest adopted controls pin"
        _, _, w = snapshot_state(a.snapshot, part)
    except (ValueError, OSError, KeyError) as e:
        return None, f"no correctly bound current receipt ({e})"
    why = receipt_age_problem(w) or inventory_bound_problem(w) or attempt_in_inventory_problem(run, att)
    return (None, why) if why else (w, "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", choices=sorted(ES.CONTRACTS), required=True); ap.add_argument("--epoch", type=int, required=True)
    ap.add_argument("--partition"); ap.add_argument("--manifest"); ap.add_argument("--panel", default=None)
    ap.add_argument("--snapshot", default=os.path.join(T1, "chpc", "results", "row19_screen")); ap.add_argument("--tarball")
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--recover", action="store_true")
    a = ap.parse_args()
    run = run_of(a.contract, a.epoch)
    try:
        with PA.authority_lock(), L.run_lock(run):
            if a.recover:
                return recover(a)
            if not (a.partition and a.manifest and a.tarball):
                sys.exit("--partition, --manifest and --tarball are required to admit an instance")
            return admit(a)
    except BlockingIOError:
        sys.exit(f"REFUSED: another authority operation, launcher or reaper holds the lock")


if __name__ == "__main__":
    sys.exit(main())
