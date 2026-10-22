"""Row 19 screen: ingest ONE reconciled EC2 attempt into the Lengau screen root (Codex RSC f3dd3d7 contract 4; repaired for
Codex RSC 0483db4 V10-2, V10-4, V10-5, V10-8).

    t1py chpc/row19_ec2_ingest.py --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e1.json \
        --opmanifest <EC2 operational manifest> --authority <inventory.json from the Mac authority> --attempt-key prod-e1/3 \
        --bundle <staged dir>

Runs on the Lengau login node under t1py from the controller tree. Nothing is published unless EVERY check passes.
BEFORE THE LOCK (static evidence; repeated where it matters under the lock):
  authority  the Mac claim authority's sealed inventory (chpc/row19_ec2_state.inventory_problem: complete, sealed, fresh
             <= 6 h, globally unique sequences, owners and fences consistent); the attempt is in it, 'reconciled', class
             production - or a qualification attempt the inventory lists as RELEASED (Q1's block coordinates after the
             reviewed release certificate); never a generation older than one this register has already consumed.
  inputs     the partition is the one the LATEST adopted controls pin and has its activation proof; the operational
             manifest is the exact derivation (row19_ec2_state.operational_problem) of this production manifest.
  bundle     BUNDLE_SHA256SUMS lists every frozen file under root/ and env/ and each one matches (the mutable transport
             diagnostics are excluded by name); the plan is the attempt's bytes and passes plan_problem (bound to partition,
             operational manifest, activation, sequence; exact slots, roles, counts and per-role coordinates); outcomes name
             exactly w_slot<k> for every slot with typed int 0; nothing unresolved; transfer verified; the attestation is an
             effective B_full one; no FAILED marker.
  units      every slot: record valid against the frozen task (row19_shard.read_record), EC2 binding, timing naming this
             attempt and slot with positive finite wall/fit, a COMPLETE terminal worker status of exactly this coordinate
             (row19_ec2_state.status_problem: exit 0, index done once, nothing left, finite times, maxrss under the stop).
             Procedure-level failed fits are valid records and are published and reported as failed, never dropped.
UNDER THE PLAN LOCK (plans/.submit.lock, shared with every admission and the activation):
  STOP/HOLD  the root STOP or ec2/HOLD refuses publication (evidence stays in the bundle; release is a reviewed step).
  ownership  every work coordinate's CURRENT owner in the inventory is this attempt (key and global sequence) and the
             register's fence at it is not above this sequence: a dispositioned or reassigned (late) writer is refused.
  compare    sentinels and duplicates against the live root (float.hex payload): any difference writes ec2/HOLD and HOLDS;
             a work coordinate already present counts once if identical (provenance kept), HOLDS if contrary - never replaced.
PUBLICATION (crash-safe). The register gains this attempt as 'ingesting' with every coordinate's record, timing and status
sha256 BEFORE the first file is written; each coordinate is published timing first, record second, status third, each by
verified temp bytes + fsync + hard link (never replacing); the fence is raised; the entry becomes 'ingested' last. A rerun
finds the 'ingesting' entry and completes it (a present file must be the registered bytes). A rerun of an 'ingested'
attempt re-validates every registered canonical record/timing/status hash, the plan and the attempt key; any difference
writes ec2/HOLD. The canonical Lengau task_<rep>.json bindings are never written; EC2 bindings are kept in the register.

REVISION 3 (Codex RSC 3dc0daf R1-1, R1-2). Under the lock the supplied --authority must be byte-for-byte the root's
INSTALLED current inventory (row19_ec2_root.py install is its only writer, monotonic in generation), so a fresh but
superseded inventory can never license a late writer; an attempt with a disposition request, or with a 'dispositioned'
register entry (fenced at installation), is refused. The activation proof must be a CANONICAL one whose controls lineage
still pins the partition (row19_partition.activation_problem with the current controls); only the qualifier's sandbox
replay sets ACTIVATION_MODE = "sandbox". Ingestion no longer writes the inventory.

REVISION 4 (Codex RSC 299f4b7 R2-1, R2-2). In mode canonical the controls are read only through
row19_partition.adopted_controls (the current adopted, tracked, unmodified bytes); a later unadopted candidate at the
canonical path HOLDS here exactly as at Lengau admission. A completed attempt can be replayed AFTER the Mac acknowledged it:
an inventory showing the attempt 'ingested' (not dispositioned, no request) is accepted for the replay branch only - the
register entry must be 'ingested' and every registered canonical file is re-validated; such an inventory can never start or
complete a publication.

REVISION 5 - CANDIDATE, not adopted (EC2 provider epoch 2; Codex design reviews/2026-10-17_row19_resize_codex.md s.3-s.6).
  schema 2   the partition may be a row19-provider-partition-2 declaration (explicit coordinate set; row19_partition
             REVISION 5): every WORK slot of the plan must be an owned coordinate of THIS epoch (blocked), checked statically
             and again under the lock; a work coordinate outside the epoch HOLDS the whole attempt.
  per-slot   (schema 2 production attempts only) a worker that ended without its coordinate is an UNPRODUCED slot, not a
             reason to discard the batch. Exactly three kinds qualify, each with NO record and NO timing of its coordinate in
             the bundle: (a) a fatal signal (exit 129..159) and no status - the crashed-worker signature (the worker writes
             its status on every orderly exit); (b) the worker's own RESUME exit 75 (deadline or STOP) with its status
             showing the coordinate left and nothing new or resumed; (c) the censored marker (still running at the upload
             deadline) with no status or such a status. Anything else - exit 4 (the worker's HELD guard: admission,
             identity, memory), any other exit, a record or timing beside a nonzero outcome, an inconsistent status - is
             ambiguous or a contract failure and HOLDS the whole attempt. Every other slot must pass the full unit contract
             exactly as before and is published. A crashed worker is never turned into
             a scientific failed-fit record (s.3: "A crashed Q2/S coordinate is not an invented scientific failed-fit
             record"). Bounds: at most MAX_UNPRODUCED_WORK unproduced work slots (more is a packing/resource failure and
             HOLDS for review), at least MIN_SENTINELS_COMPARED sentinels produced and every produced sentinel equal (any
             mismatch writes ec2/HOLD as before). The register entry lists `unproduced` {rep/index: slot, outcome} and the
             fence is raised at those coordinates too, so this attempt can never publish them later; the Mac `ack` releases
             them for re-allocation and counts fatal-signal exits towards the EC2 crash rule (prod_authority REVISION 5).
  epoch 1    unchanged: a schema-1 partition keeps the all-or-nothing contract (every outcome int 0).
  paths      the module resolves t1_access by name, so it runs from chpc/ (promoted) and from chpc/candidate_e2/.

REVISION 6 - CANDIDATE, not adopted (Codex review reviews/2026-10-17_e2_p80r_codex_review.md A1, A2 and the replay follow-up).
  classes    the non-completion classes come from ONE shared module, row19_ec2_e2rules (also read by the Mac authority's ack
             and crash rule), so ingestion and the two-crash counter can never disagree (A2): a fatal signal is any exit
             129..159 and only WITHOUT a status; every such slot counts toward the crash rule on the Mac.
  status     a PRESENT status of an unproduced slot is never overridden by the censor marker (A1). Under RESUME 75 and under
             the censored marker alike it must pass row19_ec2_e2rules.left_status_problem: this attempt/slot/rep/identity,
             exactly this index left, exit 75 with an orderly deadline/STOP reason, finite times, maxrss within the stop. A
             HELD exit 4, a memory/identity reason, a wrong identity or malformed LEFT accounting HOLDS the attempt.
  censor     the censored marker is bound to the producer's frozen evidence: env/censored.txt (written by prod_userdata.sh
             before cleanup) must be listed in BUNDLE_SHA256SUMS and name exactly the slots whose outcome is the marker.
  replay     a schema-2 production entry journals its frozen failure evidence (the BUNDLE_SHA256SUMS bytes, the outcomes,
             env/censored.txt and every unproduced slot's status bytes or their absence) and the computed `unproduced` map;
             the completion of an 'ingesting' entry and every replay of an 'ingested' one recompute it from the supplied
             bundle and HOLD (ec2/HOLD) on any difference. The replay re-validates the fence at every unproduced coordinate
             (>= this sequence) and never requires that coordinate to stay absent: a later attempt may legitimately complete it.

REVISION 7 - CANDIDATE, not adopted (Codex re-review reviews/2026-10-17_e2_p80_codex_rereview.md A, P2). Status presence is
a filesystem fact kept apart from the parsed value: a PRESENT status file of an unproduced slot must parse to a JSON object
before its outcome is classified (a present null, list or scalar HOLDS, as does unreadable JSON); the fatal-signal and
censored "no status" kinds require the file to be actually absent; a present status under RESUME or censoring must pass
row19_ec2_e2rules.left_status_problem as before.

REVISION 8 - CANDIDATE, not adopted (Codex review reviews/2026-10-19_e2_adoption_codex_review.md B1; replaces the reviewed
REVISION 6/7 bytes 6ac144c6, which stay in git at RSC 92a62f6). The per-slot branch also serves a RELEASED epoch-2
qualification attempt, narrowly: only a schema-2 partition, only class qualification, only an attempt the installed inventory
lists as released (the same `released` the class gate above reads), and only contract E2Q1 or E2Q2. Such an attempt keeps
its real class (the register entry records cls "qualification") and passes every check production passes - inventory,
release, activation, operational manifest, plan, typed outcomes, the censor list, the three qualifying kinds and the
present-status rules, units, ownership and fence under the lock, comparisons, the journaled failure evidence, completion and
replay - and in addition R4' (row19_ec2_e2rules.qualification_unproduced_problem): at most 3 non-completed slots of ALL roles
across the attempt, the qualification-wide bound; production's 7-work-slot bound is not a replacement for it. Every other
qualification attempt (unreleased, schema 1, or another contract such as epoch-1 Q1) keeps the all-or-nothing contract."""
import os, sys, json, glob, math, time, fcntl, hashlib, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = HERE
while os.path.basename(T1) != "t1_access":
    if os.path.dirname(T1) == T1:
        raise RuntimeError(f"{HERE} is not inside a t1_access tree")
    T1 = os.path.dirname(T1)
CHPC = os.path.join(T1, "chpc")
for p in (T1, CHPC, HERE):                                  # HERE last inserted = first searched (the candidate's partition)
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)
import row19_shard as SH
import row19_screen_verify as V
import row19_partition as RP
import row19_ec2_state as ES
import row19_ec2_e2rules as E2R

HOLD, DONE = 3, 0
MUTABLE = ("env/upload_verify.json", "env/userdata.log", "env/spot_notice.json", "env/stop_seen.txt", "env/memory_live.txt")
CONTROLS = os.path.join(CHPC, "row19_screen_controls.json")
MAX_UNPRODUCED_WORK = 7                                     # of up to 72 work slots (~10 %); more HOLDS for a resource review
MIN_SENTINELS_COMPARED = 3                                  # of the 4 per attempt
CENSORED = E2R.CENSORED
ACTIVATION_MODE = "canonical"                       # the qualifier's sandbox replay alone sets "sandbox"
E2Q_CONTRACTS = ("E2Q1", "E2Q2")                    # REVISION 8 (B1): the released epoch-2 qualification contracts with a per-slot route


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def _fsync_dir(d):
    fd = os.open(d, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, path); _fsync_dir(os.path.dirname(path))


def publish_copy(src, dst, want_sha):
    """dst := the bytes of src, which must hash to want_sha BEFORE anything is written; temp + fsync, the temp's bytes
    re-verified, then a hard link (never replacing). A present dst must already be exactly want_sha. Returns True if written."""
    if os.path.exists(dst):
        if sha_file(dst) != want_sha:
            raise ValueError(f"{dst} exists with other bytes than the registered {want_sha[:12]}")
        return False
    data = open(src, "rb").read()
    if hashlib.sha256(data).hexdigest() != want_sha:
        raise ValueError(f"{src}: the staged bytes are not the registered {want_sha[:12]}")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = f"{dst}.tmp.{os.getpid()}"
    with open(tmp, "wb") as fo:
        fo.write(data); fo.flush(); os.fsync(fo.fileno())
    try:
        if sha_file(tmp) != want_sha:
            raise ValueError(f"{tmp}: the written temp bytes are not {want_sha[:12]}")
        os.link(tmp, dst)
    finally:
        os.unlink(tmp)
    _fsync_dir(os.path.dirname(dst))
    if sha_file(dst) != want_sha:
        raise ValueError(f"{dst}: published bytes do not hash to {want_sha[:12]}")
    return True


def hold(root, why):
    """Write ec2/HOLD (never overwritten: the first reason stays) - every admission refuses while it exists."""
    p = ES.paths(root)["hold"]
    if not os.path.exists(p):
        atomic_json(p, dict(reason=why, at=time.time()))


def check_bundle(bundle, att, plan_args, problems, partial=False):
    """Frozen inventory, plan, outcomes, attestation, transfer. Returns (plan, outcomes) or (None, None). With `partial`
    (REVISION 5, schema-2 production) a slot may end with a nonzero integer or the censored marker; such slots are returned
    as outcomes and judged by unproduced_problems."""
    sums = os.path.join(bundle, "BUNDLE_SHA256SUMS")
    if not os.path.exists(sums):
        problems.append("no BUNDLE_SHA256SUMS"); return None, None
    listed = {}
    for line in open(sums):
        h, f = line.rstrip("\n").split("  ", 1)
        listed[os.path.normpath(f)] = h
    present = {os.path.normpath(os.path.relpath(p, bundle)) for sub in ("root", "env")
               for p in glob.glob(os.path.join(bundle, sub, "**", "*"), recursive=True) if os.path.isfile(p)}
    for m in MUTABLE:
        present.discard(os.path.normpath(m)); listed.pop(os.path.normpath(m), None)
    for f in sorted(present - set(listed)):
        problems.append(f"unlisted file {f}")
    for f, h in sorted(listed.items()):
        p = os.path.join(bundle, f)
        if not os.path.isfile(p):
            problems.append(f"listed file missing {f}")
        elif sha_file(p) != h:
            problems.append(f"checksum differs {f}")
    env = os.path.join(bundle, "env")
    try:
        pp = os.path.join(env, "plan.json")
        if sha_file(pp) != att["plan_sha256"]:
            problems.append("the bundle's plan is not the attempt's bytes"); return None, None
        plan = json.load(open(pp))
        why = ES.plan_problem(plan, att["contract"], att, *plan_args)
        if why:
            problems.append(f"plan: {why}"); return None, None
        uv = json.load(open(os.path.join(env, "upload_verify.json")))
        if uv.get("transfer_verified") is not True:
            problems.append(f"transfer not verified: {uv}")
        why = ES.attestation_problem(json.load(open(os.path.join(env, "attest_B.json"))))
        if why:
            problems.append(why)
        for f in ("FAILED", "OUTCOMES_FAILED", "BUNDLE_FAILED"):
            if os.path.exists(os.path.join(env, f)):
                problems.append(f"instance reported {f}")
        oc = json.load(open(os.path.join(env, "outcomes.json")))
        names = {f"w_slot{s['slot']}" for s in plan["slots"]}
        out = oc.get("outcomes")
        if not isinstance(out, dict) or set(out) != names or oc.get("declared") != len(names):
            problems.append(f"outcomes do not name exactly the {len(names)} planned workers")
        else:
            if partial:
                bad = {k: v for k, v in out.items() if not (type(v) is int or v == CENSORED)}
            else:
                bad = {k: v for k, v in out.items() if not (type(v) is int and v == 0)}
            if bad:
                problems.append(f"{len(bad)} worker(s) not ended with {'an integer or the censored marker' if partial else 'int 0'}: "
                                f"{dict(list(bad.items())[:4])}")
            if partial:                                                    # REVISION 6 (A1): the censor label is producer evidence
                cn = os.path.normpath("env/censored.txt")
                if cn not in listed or not os.path.isfile(os.path.join(bundle, cn)):
                    problems.append("env/censored.txt (the producer's censor evidence) is not a frozen listed bundle file")
                else:
                    named = open(os.path.join(bundle, cn)).read().split()
                    marked = sorted(k for k, v in out.items() if v == CENSORED)
                    if len(named) != len(set(named)) or sorted(named) != marked:
                        problems.append(f"the censored outcomes {marked[:4]} are not exactly env/censored.txt {sorted(named)[:4]}")
        if oc.get("unresolved_after_kill") != []:
            problems.append(f"cleanup left unresolved process groups {oc.get('unresolved_after_kill')}")
        return plan, out
    except Exception as e:
        problems.append(f"bundle metadata unreadable ({type(e).__name__}: {e})"); return None, None


def unproduced_slots(plan, outcomes):
    """{slot: outcome} of the slots whose worker did not end with int 0 (REVISION 5)."""
    return {int(s["slot"]): outcomes.get(f"w_slot{s['slot']}") for s in plan["slots"]
            if not (type(outcomes.get(f"w_slot{s['slot']}")) is int and outcomes.get(f"w_slot{s['slot']}") == 0)}


def unproduced_problems(bundle, att, plan, unprod, man):
    """Each unproduced slot must be one of the three qualifying kinds (module text, REVISION 5/6; classes from
    row19_ec2_e2rules) and must have left no record or timing of its coordinate; otherwise the attempt holds. A present
    status must be the worker's own orderly LEFT status (A1), whatever the outcome label. Bounds on how many work slots may
    be unproduced and how many sentinels must remain to compare."""
    out = []
    root = os.path.join(bundle, "root")
    by = {int(s["slot"]): s for s in plan["slots"]}
    mem_stop = float(man["pbs"].get("mem_stop_gib", 0) or 0) * 2 ** 30
    for sl, oc in sorted(unprod.items()):
        s = by[sl]; r, i = int(s["rep"]), int(s["indices"][0])
        left = [f for f in (SH.record_path(root, r, i), SH.timing_path(root, r, i)) if os.path.exists(f)]
        if left:
            out.append(f"unproduced slot {sl} ({r}, {i}, outcome {oc!r}) left output {[os.path.relpath(f, root) for f in left]}: ambiguous")
            continue
        sp = os.path.join(root, "status", f"job{att['attempt_id']}.slot{sl}.json")
        has_status = os.path.lexists(sp)                                   # REVISION 7: presence is a filesystem fact, not a JSON value
        st = None
        if has_status:
            try:
                st = json.load(open(sp))
            except Exception:
                out.append(f"unproduced slot {sl} ({r}, {i}): its status is unreadable"); continue
            if not isinstance(st, dict):                                   # a present null/list/scalar is unknown evidence, never absence
                out.append(f"unproduced slot {sl} ({r}, {i}, outcome {oc!r}): its present status is not a JSON object "
                           f"({type(st).__name__}): held for review"); continue
        k = E2R.kind(oc)
        if k == "fatal_signal" and not has_status:
            continue                                                       # (a) crashed worker, status file actually absent
        if k in ("resume", "censored") and has_status:                     # (b)/(c) with a status: never overridden by the label
            try:
                ident = SH.task(man, r)["ident"]
            except Exception as e:
                out.append(f"unproduced slot {sl} ({r}, {i}): the task identity is unavailable ({type(e).__name__})"); continue
            why = E2R.left_status_problem(st, att["attempt_id"], sl, r, i, ident, mem_stop)
            if not why:
                continue
            out.append(f"unproduced slot {sl} ({r}, {i}, outcome {oc!r}): its present status is not an orderly LEFT status ({why}): held for review")
            continue
        if k == "censored" and not has_status:
            continue                                                       # (c) still running at the upload deadline, status file absent
        out.append(f"unproduced slot {sl} ({r}, {i}): outcome {oc!r} with {'a status' if has_status else 'no status'} is not a "
                   "qualifying non-completion (fatal signal without status, RESUME 75 with an orderly left status, censored): held for review")
    n_work = sum(1 for sl in unprod if by[sl]["role"] == "work")
    if n_work > MAX_UNPRODUCED_WORK:
        out.append(f"{n_work} unproduced work slots (> {MAX_UNPRODUCED_WORK}): a packing/resource failure, held for review")
    n_sent = sum(1 for s in plan["slots"] if s["role"] == "sentinel" and int(s["slot"]) not in unprod)
    if n_sent < MIN_SENTINELS_COMPARED:
        out.append(f"only {n_sent} sentinel(s) produced (< {MIN_SENTINELS_COMPARED}): too little parity evidence to publish")
    return out


def failure_evidence(bundle, att, plan, unprod, unprod_work):
    """REVISION 6 (replay follow-up): the frozen failure evidence a schema-2 production entry journals and every completion
    or replay must find again in the supplied bundle."""
    def fsha(rel):
        p = os.path.join(bundle, rel)
        return sha_file(p) if os.path.isfile(p) else None
    oc = json.load(open(os.path.join(bundle, "env", "outcomes.json")))
    return dict(bundle_sums_sha256=fsha("BUNDLE_SHA256SUMS"), outcomes_sha256=ES.sha_bytes(ES.canonical(oc.get("outcomes"))),
                censored_sha256=fsha(os.path.join("env", "censored.txt")),
                unproduced_status={str(sl): fsha(os.path.join("root", "status", f"job{att['attempt_id']}.slot{sl}.json")) for sl in sorted(unprod)},
                unproduced=unprod_work)


def plan_units(bundle, man, opman, opsha, att, plan, problems, skip=()):
    """Validated (rep, index) -> unit for every plan slot (records, binding, timing, complete terminal status); slots in
    `skip` (REVISION 5: the unproduced slots) are not units."""
    root = os.path.join(bundle, "root"); units = {}; tasks = {}
    mem_stop = float(man["pbs"].get("mem_stop_gib", 0) or 0) * 2 ** 30
    for s in plan["slots"]:
        r, i, slot, role = int(s["rep"]), int(s["indices"][0]), int(s["slot"]), s["role"]
        if slot in skip:
            continue
        c = (r, i)
        t = tasks.setdefault(r, SH.task(man, r))
        rp, tp = SH.record_path(root, r, i), SH.timing_path(root, r, i)
        try:
            rec = SH.read_record(rp, t, i)
        except ValueError as e:
            problems.append(f"slot {slot} {c}: {e}"); continue
        if rec is None:
            problems.append(f"slot {slot} {c}: no record (censored or failed worker)"); continue
        b = None
        try:
            b = json.load(open(os.path.join(root, f"task_{r}.json")))["binding"]
            want = json.loads(json.dumps(SH.binding_for(opman, opsha, opman["storage"]["root"], r, t), default=str))
            if b != want:
                problems.append(f"slot {slot} {c}: EC2 binding differs from the operational manifest's")
        except Exception as e:
            problems.append(f"slot {slot} {c}: EC2 binding unreadable ({e})")
        try:
            td = json.load(open(tp))
            why = V.timing_ok(td, rep=r, index=i, ident=t["ident"], job=att["attempt_id"], slot=slot)
            if why or not (math.isfinite(td["wall_s"]) and td["wall_s"] > 0 and math.isfinite(td["fit_seconds"]) and td["fit_seconds"] > 0):
                problems.append(f"slot {slot} {c}: timing {why or 'wall/fit not positive and finite'}")
        except Exception as e:
            problems.append(f"slot {slot} {c}: timing unreadable ({e})"); continue
        stp = os.path.join(root, "status", f"job{att['attempt_id']}.slot{slot}.json")
        try:
            why = ES.status_problem(json.load(open(stp)), att["attempt_id"], slot, r, i, t["ident"], mem_stop)
        except Exception as e:
            why = f"status missing or unreadable ({type(e).__name__})"
        if why:
            problems.append(f"slot {slot} {c}: {why}"); continue
        units[c] = dict(rec=rec, rec_path=rp, timing_path=tp, status_path=stp, slot=slot, role=role,
                        rec_sha=sha_file(rp), timing_sha=sha_file(tp), status_sha=sha_file(stp), binding=b)
    return units


def _compare(man, root, units, problems):
    """Sentinels/duplicates must equal the live root; work coordinates already present must be identical. Returns
    (preexisting work coordinates, compared coordinate keys). Called UNDER the plan lock."""
    pre, compared = set(), []
    for c, u in sorted(units.items()):
        lp = SH.record_path(root, *c)
        if u["role"] in ("sentinel", "qual_lengau"):
            try:
                l = SH.read_record(lp, SH.task(man, c[0]), c[1])
            except ValueError as e:
                problems.append(f"{u['role']} {c}: Lengau record invalid ({e})"); continue
            if l is None or V.payload(l) != V.payload(u["rec"]):
                problems.append(f"{u['role'].upper()} MISMATCH at {c}: the EC2 payload is not Lengau's (float.hex)")
            compared.append(f"{c[0]}/{c[1]}")
        elif u["role"] == "work" and os.path.exists(lp):
            l = SH.read_record(lp, SH.task(man, c[0]), c[1])
            if V.payload(l) != V.payload(u["rec"]):
                problems.append(f"contrary duplicate at {c}: a different payload is already in the root")
            pre.add(c)
    return pre, compared


def evidence_problem(e, evidence):
    """REVISION 6: '' when the entry's journaled failure evidence is the supplied bundle's (schema-2 production entries)."""
    if "unproduced" not in e:
        return ""
    if e.get("failure_evidence") is None:
        return "the entry journals no failure evidence"
    if evidence is None or ES.canonical(e["failure_evidence"]) != ES.canonical(evidence):
        diff = sorted(k for k in set(e["failure_evidence"]) | set(evidence or {}) if (e["failure_evidence"] or {}).get(k) != (evidence or {}).get(k))
        return f"the bundle's failure evidence differs from the journal ({diff})"
    return ""


def replay_problems(root, e, plan_sha, key, reg=None, evidence=None):
    """An 'ingested' entry re-validated against the root: every registered canonical file is the registered bytes; for a
    schema-2 production entry (REVISION 6) also the frozen failure evidence and the fence at every unproduced coordinate."""
    out = []
    if e.get("plan_sha256") != plan_sha or e.get("key") != key:
        out.append("the ingested entry's plan or attempt key is not this attempt's")
    why = evidence_problem(e, evidence)
    if why:
        out.append(why)
    for k in sorted(e.get("unproduced") or {}):                                # the fence, never the coordinate's absence
        if reg is not None and reg["fence"].get(k, -1) < e["sequence"]:
            out.append(f"{k}: the fence at an unproduced coordinate is below this attempt's sequence")
    for k, ce in sorted(e["coordinates"].items()):
        r, i = (int(x) for x in k.split("/"))
        if ce["preexisting"]:                                                  # Lengau's own record: the verifier owns it
            continue
        files = [(SH.record_path(root, r, i), ce["record_sha256"]), (SH.timing_path(root, r, i), ce["timing_sha256"]),
                 (os.path.join(root, "ec2", "status", f"{e['attempt_id']}.slot{ce['slot']}.json"), ce["status_sha256"])]
        for fp, h in files:
            if not os.path.exists(fp) or sha_file(fp) != h:
                out.append(f"{k}: {os.path.relpath(fp, root)} is not the registered bytes")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    for k in ("--manifest", "--partition", "--opmanifest", "--authority", "--attempt-key", "--bundle"):
        ap.add_argument(k, required=True)
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); msha = sha_file(a.manifest); part = RP.load(a.partition, man, msha); psha = sha_file(a.partition)
    opman = json.load(open(a.opmanifest)); opsha = sha_file(a.opmanifest)
    root = man["storage"]["root"]; P = ES.paths(root); problems = []
    # --- authority, inputs (static) ---
    try:
        inv = json.load(open(a.authority))
    except Exception as e:
        print(f"HELD: the authority inventory is unreadable ({e})"); return HOLD
    why = ES.inventory_problem(inv)
    if why:
        print(f"HELD: authority inventory: {why}"); return HOLD
    att = inv["attempts"].get(a.attempt_key)
    if att is None:
        print(f"HELD: attempt {a.attempt_key} is not in the authority inventory"); return HOLD
    if att.get("state") != "reconciled":
        print(f"HELD: attempt {a.attempt_key} is {att.get('state')}, not reconciled"); return HOLD
    replay_only = att.get("ingestion") == "ingested" and not att.get("disposition_requested")   # R2-1: post-ACK replay
    if not replay_only and (att.get("disposition_requested") or att.get("ingestion") != "pending"):
        print(f"HELD: attempt {a.attempt_key} is {att.get('ingestion')}{' with a disposition request' if att.get('disposition_requested') else ''}: nothing of it is ingested")
        return HOLD
    released = a.attempt_key in ((inv.get("release") or {}).get("released_attempts") or [])
    if not (att["class"] == "production" or (att["class"] == "qualification" and released)):
        print(f"HELD: attempt {a.attempt_key} is {att['class']} and not released: qualification output never enters the root before release")
        return HOLD
    if ACTIVATION_MODE == "canonical":
        ctl, why = RP.adopted_controls(CONTROLS)
        if why:
            print(f"HELD: {why}"); return HOLD
    else:
        ctl = json.load(open(CONTROLS))
    pin = (ctl["versions"][-1].get("partition") or {}).get("sha256")
    if pin != psha:
        print("HELD: the partition is not the one the latest adopted controls pin"); return HOLD
    actp = RP.activation_path(man, part["epoch"])
    try:
        why = RP.activation_problem(man, msha, part, psha, json.load(open(actp)), controls=ctl, mode=ACTIVATION_MODE)
    except Exception as e:
        why = f"no readable activation proof ({type(e).__name__})"
    if why:
        print(f"HELD: {why}"); return HOLD
    why = ES.operational_problem(opman, man, msha)
    if why or opman["ec2_production"]["epoch"] != part["epoch"] or opman["ec2_production"]["contract"] != att["contract"]:
        print(f"HELD: {why or 'the operational manifest is not this epoch/contract'}"); return HOLD
    # --- bundle, units (static) ---
    schema2 = part.get("schema") == RP.SCHEMA2
    # REVISION 8 (B1): a RELEASED schema-2 E2Q1/E2Q2 qualification attempt joins production's per-slot route, keeping its class
    e2q_released = schema2 and att["class"] == "qualification" and released and att.get("contract") in E2Q_CONTRACTS
    partial = schema2 and (att["class"] == "production" or e2q_released)
    plan, outcomes = check_bundle(a.bundle, att, (psha, opsha, sha_file(actp)), problems, partial=partial)
    unprod = {}
    if plan is not None and schema2:
        off = [(int(s["rep"]), int(s["indices"][0])) for s in plan["slots"] if s["role"] == "work" and not RP.blocked(part, s["rep"], s["indices"][0])]
        if off:
            problems.append(f"{len(off)} work coordinate(s) are not owned by epoch {part['epoch']}, e.g. {off[:3]}")
    if plan is not None and partial and not problems:
        unprod = unproduced_slots(plan, outcomes)
        problems += unproduced_problems(a.bundle, att, plan, unprod, man)
        if e2q_released:                                                   # REVISION 8 (B1): R4' stays the qualification-wide bound
            why = E2R.qualification_unproduced_problem(plan["slots"], outcomes)
            if why:
                problems.append(f"R4' (released qualification attempt): {why}")
    units =plan_units(a.bundle, man, opman, opsha, att, plan, problems, skip=set(unprod)) if not problems else {}
    if problems:
        print(f"HELD: {len(problems)} problem(s); nothing published"); [print("   -", p) for p in problems[:20]]; return HOLD
    os.makedirs(os.path.join(root, "ec2", "status"), exist_ok=True)
    with open(os.path.join(root, "plans", ".submit.lock"), "a+") as lk:
        try:
            fcntl.flock(lk.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("HELD: the plan lock is held (an admission, an activation or another ingestion)"); return HOLD
        if os.path.exists(P["stop"]) or os.path.exists(P["hold"]):
            print(f"HELD: {'STOP' if os.path.exists(P['stop']) else 'ec2/HOLD'} in force - no canonical publication"); return HOLD
        cur, why = ES.installed_inventory(root)
        if why or cur.get("sha256") != inv["sha256"]:
            print(f"HELD: {why or 'the supplied authority is not the root installed current inventory (generation ' + str(cur.get('generation')) + ')'}")
            return HOLD
        reg = json.load(open(P["register"])) if os.path.exists(P["register"]) else {
            "schema": ES.REGISTER_SCHEMA, "authority_generation": 0, "fence": {}, "attempts": {}}
        if reg.get("schema") != ES.REGISTER_SCHEMA:
            print("HELD: the register is not schema 2"); return HOLD
        if inv["generation"] < reg["authority_generation"]:
            print(f"HELD: authority generation {inv['generation']} is older than the {reg['authority_generation']} already consumed"); return HOLD
        e = reg["attempts"].get(att["attempt_id"])
        if e is not None and e["state"] == "dispositioned":
            print(f"HELD: {att['attempt_id']} was dispositioned and fenced on this root (generation {e.get('inventory_generation')})"); return HOLD
        by_slot = {int(s["slot"]): s for s in plan["slots"]}
        unprod_work = {f"{int(by_slot[sl]['rep'])}/{int(by_slot[sl]['indices'][0])}": dict(slot=sl, outcome=oc)
                       for sl, oc in sorted(unprod.items()) if by_slot[sl]["role"] == "work"}
        evidence = failure_evidence(a.bundle, att, plan, unprod, unprod_work) if partial else None
        if e is not None and e["state"] == "ingested":
            bad = replay_problems(root, e, att["plan_sha256"], a.attempt_key, reg, evidence)
            if bad:
                hold(root, f"replay of {att['attempt_id']}: {bad[0]}")
                print(f"HELD: replay of an ingested attempt differs: {bad[:5]}"); return HOLD
            print(f"already ingested and re-validated: {att['attempt_id']}"); return DONE
        if replay_only:
            print(f"HELD: the inventory shows {a.attempt_key} acknowledged as ingested but the register holds "
                  f"{'no entry' if e is None else repr(e['state'])}: a replay never publishes"); return HOLD
        work = {c: u for c, u in units.items() if u["role"] == "work"}
        for c in list(work) + [tuple(int(x) for x in k.split("/")) for k in unprod_work]:   # ownership and fence, under the lock
            k = f"{c[0]}/{c[1]}"
            if inv["owners"].get(k) != [a.attempt_key, att["sequence"]]:
                problems.append(f"{k}: the authority's current owner is {inv['owners'].get(k)}, not {a.attempt_key}")
            if reg["fence"].get(k, -1) > att["sequence"]:
                problems.append(f"{k}: fenced at sequence {reg['fence'][k]} above this attempt's {att['sequence']} (late writer)")
        pre, compared = _compare(man, root, units, problems)
        if problems:
            if any("MISMATCH" in p or "contrary" in p for p in problems):
                hold(root, f"{att['attempt_id']}: {next(p for p in problems if 'MISMATCH' in p or 'contrary' in p)}")
            print(f"HELD: {len(problems)} problem(s) under the lock; nothing published"); [print("   -", p) for p in problems[:20]]; return HOLD
        if e is None:
            e = dict(attempt_id=att["attempt_id"], key=a.attempt_key, sequence=att["sequence"], cls=att["class"], contract=att["contract"],
                     epoch=part["epoch"], plan_sha256=att["plan_sha256"], opmanifest_sha256=opsha, partition_sha256=psha,
                     inventory_sha256=inv["sha256"], inventory_generation=inv["generation"], state="ingesting", started=time.time(),
                     coordinates={f"{r}/{i}": dict(slot=u["slot"], record_sha256=u["rec_sha"], timing_sha256=u["timing_sha"],
                                                   status_sha256=u["status_sha"], preexisting=(r, i) in pre, failed=bool(u["rec"]["failed"]),
                                                   ec2_binding=u["binding"])
                                  for (r, i), u in work.items()},
                     compared_equal=compared, outcomes=outcomes, charged_usd=att.get("charged_usd"),
                     **({"unproduced": unprod_work, "failure_evidence": evidence} if partial else {}))
            reg["attempts"][att["attempt_id"]] = e
            reg["authority_generation"] = max(reg["authority_generation"], inv["generation"]); atomic_json(P["register"], reg)
        elif e.get("key") != a.attempt_key or e.get("plan_sha256") != att["plan_sha256"]:
            print("HELD: an 'ingesting' entry of another attempt key or plan exists under this id"); return HOLD
        elif evidence_problem(e, evidence) or ("unproduced" in e and ES.canonical(e["unproduced"]) != ES.canonical(unprod_work)):
            why = evidence_problem(e, evidence) or "the bundle's unproduced slots differ from the journal"
            hold(root, f"completion of {att['attempt_id']}: {why}")
            print(f"HELD: completion of an 'ingesting' attempt: {why}"); return HOLD
        published = 0
        try:
            for key, ce in e["coordinates"].items():
                r, i = (int(x) for x in key.split("/")); u = work.get((r, i))
                if u is None or u["rec_sha"] != ce["record_sha256"] or u["timing_sha"] != ce["timing_sha256"] or u["status_sha"] != ce["status_sha256"]:
                    raise ValueError(f"{key}: the staged unit is not the one journaled")
                if ce["preexisting"]:
                    if V.payload(json.load(open(SH.record_path(root, r, i)))) != V.payload(u["rec"]):
                        raise ValueError(f"{key}: the preexisting record changed since it was journaled")
                    continue
                published += publish_copy(u["timing_path"], SH.timing_path(root, r, i), ce["timing_sha256"])
                published += publish_copy(u["rec_path"], SH.record_path(root, r, i), ce["record_sha256"])
                publish_copy(u["status_path"], os.path.join(root, "ec2", "status", f"{att['attempt_id']}.slot{u['slot']}.json"), ce["status_sha256"])
                reg["fence"][key] = max(reg["fence"].get(key, -1), att["sequence"])
        except ValueError as ex:
            atomic_json(P["register"], reg)
            print(f"HELD during publication (entry stays 'ingesting' for a checked replay): {ex}"); return HOLD
        for key in (e.get("unproduced") or {}):                          # REVISION 5: never publishable by this attempt later
            reg["fence"][key] = max(reg["fence"].get(key, -1), att["sequence"])
        e.update(state="ingested", finished=time.time()); atomic_json(P["register"], reg)
    print(f"ingested {att['attempt_id']}: {len(e['coordinates'])} coordinates ({published} files published, "
          f"{sum(1 for c in e['coordinates'].values() if c['failed'])} failed fits kept), {len(e['compared_equal'])} comparisons equal"
          + (f", {len(e.get('unproduced') or {})} unproduced work slot(s) released for re-allocation" if e.get("unproduced") is not None else ""))
    return DONE


if __name__ == "__main__":
    sys.exit(main())
