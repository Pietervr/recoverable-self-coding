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
s.5). Paths resolve t1_access by name (runs from chpc/ and chpc/candidate_e2/)."""
import os, sys, json, glob, copy, shutil, hashlib, argparse, time

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = HERE
while os.path.basename(T1) != "t1_access":
    if os.path.dirname(T1) == T1:
        raise RuntimeError(f"{HERE} is not inside a t1_access tree")
    T1 = os.path.dirname(T1)
CHPC = os.path.join(T1, "chpc")
for p in (T1, CHPC, HERE):
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)
import row19_shard as SH
import row19_screen_verify as V
import row19_partition as RP
import row19_ec2_state as ES
import row19_ec2_ingest as IG

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


def _timeline(p, width):
    rows, prev = [], -1
    for line in open(p):
        f = line.split()
        if len(f) != width:
            raise ValueError(f"malformed line {line!r}")
        t = int(f[0])
        if t < prev:
            raise ValueError(f"time goes backwards at {line!r}")
        prev = t; rows.append(f)
    return rows


def memory(bundle, problems, workers):
    """R4 memory (R1-6): chronological samples joined to the occupancy line of the same producer iteration (<= 60 s apart);
    >= MEM_MIN_SAMPLES taken at the full planned packing (`workers` running); peak host use <= the limit over ALL samples."""
    try:
        mem = _timeline(os.path.join(bundle, "env", "memory.txt"), 4)
        occ = _timeline(os.path.join(bundle, "env", "occupancy.txt"), 5)
    except Exception as e:
        problems.append(f"Q1 memory/occupancy timeline unreadable ({e})"); return None
    import bisect
    ot = [int(o[0]) for o in occ]
    peak = peak_full = worker_rss_peak = 0.0; full = unmatched = 0
    for f in mem:
        t, used = int(f[0]), (int(f[1]) - int(f[2])) / 2 ** 20
        peak = max(peak, used); worker_rss_peak = max(worker_rss_peak, int(f[3]) / 2 ** 20)
        k = bisect.bisect_right(ot, t) - 1
        if k < 0 or t - ot[k] > 60:
            unmatched += 1; continue
        if int(occ[k][1]) == workers:
            full += 1; peak_full = max(peak_full, used)
    if full < MEM_MIN_SAMPLES or peak > MEM_HOST_LIMIT_GIB:
        problems.append(f"Q1 memory gate: {full} samples at the full {workers}-worker packing (need >= {MEM_MIN_SAMPLES}), "
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
        problems.append("R5 for a schema-2 epoch belongs to the epoch-2 qualification package (QUALIFICATION_E2.md, not built)")
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
                        "qualifies epoch 1 only; epoch 2 needs the QUALIFICATION_E2.md panel and its own certificate (not built)")
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


if __name__ == "__main__":
    sys.exit(main())
