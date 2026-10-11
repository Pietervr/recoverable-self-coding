"""Row 19 screen on EC2: evaluate the PREDECLARED qualification (aws_ec2/QUALIFICATION_PLAN.md; Codex RSC 0483db4 V10-7) and
write its certificate. Lengau login node, t1py, controller tree; read-only on the screen root (the replay runs in a sandbox).

    t1py chpc/row19_ec2_qualify.py --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e1.json \
        --authority <inventory.json> --q1-key qual-Q1/1 --q1-bundle <dir> --q1-opmanifest <op Q1> \
        --q2-key qual-Q2/1 --q2-bundle <dir> --q2-opmanifest <op Q2> --shadow-root <S isolated root> --sandbox <scratch> --out cert.json

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
ec2_release_state.json may name it only with a separate actual-result review."""
import os, sys, json, glob, copy, shutil, hashlib, argparse, time

HERE = os.path.dirname(os.path.abspath(__file__)); T1 = os.path.abspath(os.path.join(HERE, ".."))
for p in (T1, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import row19_shard as SH
import row19_screen_verify as V
import row19_partition as RP
import row19_ec2_state as ES
import row19_ec2_ingest as IG

Q1_LENGAU = [(r, i) for r in range(3, 15) for i in (1, 2)]
Q1_BLOCK = [(r, i) for i in (199, 198) for r in range(3, 27)]
Q2_REPEAT = [(r, 199) for r in range(3, 27)]
COVERAGE = {"R1": 18, "R2": 36, "R3": 18}
MEM_HOST_LIMIT_GIB, MEM_MIN_SAMPLES = 184.0, 10
CODE = ["chpc/row19_ec2_qualify.py", "chpc/row19_ec2_ingest.py", "chpc/row19_ec2_state.py", "chpc/row19_partition.py",
        "chpc/row19_shard.py", "chpc/row19_screen_verify.py", "analyze.py", "models.py"]


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


def compare(name, coords, mine, ref_of, problems, out):
    n_ok = failed_both = 0
    for c in coords:
        u = mine.get(c)
        if u is None:
            problems.append(f"{name} {c}: no validated record"); continue
        ref = ref_of(c)
        if ref is None:
            problems.append(f"{name} {c}: no reference record"); continue
        if V.payload(ref) != V.payload(u["rec"]):
            problems.append(f"{name} {c}: payload differs (float.hex, failed flag/reason included)"); continue
        if u["rec"]["failed"] or ref["failed"]:
            failed_both += 1
        else:
            n_ok += 1
    out[name] = dict(coordinates=len(coords), successful_both=n_ok, failed_both=failed_both)


def memory(bundle, problems):
    p = os.path.join(bundle, "env", "memory.txt"); peak = 0.0; n = 0
    try:
        for line in open(p):
            f = line.split()
            if len(f) != 4:
                raise ValueError(f"malformed line {line!r}")
            peak = max(peak, (int(f[1]) - int(f[2])) / 2 ** 20); n += 1
    except Exception as e:
        problems.append(f"Q1 memory timeline unreadable ({e})"); return None
    if n < MEM_MIN_SAMPLES or peak > MEM_HOST_LIMIT_GIB:
        problems.append(f"Q1 memory gate: {n} samples, peak host use {peak:.1f} GiB (need >= {MEM_MIN_SAMPLES}, <= {MEM_HOST_LIMIT_GIB})")
    return dict(samples=n, peak_host_used_gib=peak, limit_gib=MEM_HOST_LIMIT_GIB)


def sandbox_replay(man, part_doc, inv, key, bundle, opp, sandbox, problems):
    """R5 on the actual bundle: a sandbox root holding only the Lengau records Q1 compares with, the same partition
    (k, epoch) under the sandbox manifest, a sandbox controls pin and activation, and an inventory listing Q1 released
    (sealed here, sandbox only). Forced stop after the first published pair, replay, second replay."""
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
    proof, why = RP.activate(sm, mp, pp, cp)
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
    args = ["--manifest", mp, "--partition", pp, "--opmanifest", sopp, "--authority", ip, "--attempt-key", key, "--bundle", sb]
    old_ctl, real = IG.CONTROLS, IG.publish_copy
    IG.CONTROLS = cp; n = {"k": 0}
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
        IG.publish_copy = real; IG.CONTROLS = old_ctl
    rep = dict(forced_stop_rc=rc1, state_after_stop=st1, replay_rc=rc2, second_replay_rc=rc3, final_state=(e2 or {}).get("state"),
               hashes_equal=not bad, activation_problems=why)
    if not (rc1 == 3 and st1 == "ingesting" and rc2 == 0 and rc3 == 0 and e2["state"] == "ingested" and not bad and not why):
        problems.append(f"R5 sandbox replay failed: {rep}")
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser()
    for k in ("--manifest", "--partition", "--authority", "--q1-key", "--q1-bundle", "--q1-opmanifest", "--q2-key", "--q2-bundle",
              "--q2-opmanifest", "--shadow-root", "--sandbox", "--out"):
        ap.add_argument(k, required=True)
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); _MSHA["sha"] = msha = sha(a.manifest)
    part = RP.load(a.partition, man, msha); psha = sha(a.partition)
    actp = RP.activation_path(man, part["epoch"]); actsha = sha(actp) if os.path.exists(actp) else None
    inv = json.load(open(a.authority)); problems = []
    why = ES.inventory_problem(inv)
    if why:
        problems.append(f"inventory: {why}")
    if actsha is None:
        problems.append("the partition has no activation proof")
    q1, plan1 = load_bundle(man, inv, a.q1_key, a.q1_bundle, a.q1_opmanifest, psha, actsha, problems) if not problems else ({}, None)
    q2, plan2 = load_bundle(man, inv, a.q2_key, a.q2_bundle, a.q2_opmanifest, psha, actsha, problems) if not problems else ({}, None)
    parts, mem, rep = {}, None, None
    if not problems:
        if sorted(c for c, u in q1.items() if u["role"] == "qual_lengau") != sorted(Q1_LENGAU) or \
           sorted(c for c, u in q1.items() if u["role"] == "work") != sorted(Q1_BLOCK) or sorted(q2) != sorted(Q2_REPEAT):
            problems.append("the bundles are not the predeclared panel")
    if not problems:
        def lengau(c):
            return SH.read_record(SH.record_path(man["storage"]["root"], *c), SH.task(man, c[0]), c[1])
        def shadow(c):
            return SH.read_record(SH.record_path(a.shadow_root, *c), SH.task(man, c[0]), c[1])
        compare("R1", Q1_LENGAU, q1, lengau, problems, parts)
        compare("R2", Q1_BLOCK, q1, shadow, problems, parts)
        compare("R3_vs_Q1", Q2_REPEAT, q2, lambda c: q1[c]["rec"], problems, parts)
        compare("R3", Q2_REPEAT, q2, shadow, problems, parts)
        compare("R4_sentinels", sorted(c for c, u in q1.items() if u["role"] == "sentinel"), q1, lengau, problems, parts)
        mem = memory(a.q1_bundle, problems)
        rep = sandbox_replay(man, part, inv, a.q1_key, a.q1_bundle, a.q1_opmanifest, a.sandbox, problems)
    short = {k: (parts.get(k) or {}).get("successful_both", 0) for k in COVERAGE if (parts.get(k) or {}).get("successful_both", 0) < COVERAGE[k]}
    outcome = "NO_RELEASE" if problems else ("INCONCLUSIVE" if short else "RELEASE")
    shadow_digest = hashlib.sha256(json.dumps(sorted((f"{r}/{i}", sha(SH.record_path(a.shadow_root, r, i))) for r, i in Q1_BLOCK
                                                      if os.path.exists(SH.record_path(a.shadow_root, r, i)))).encode()).hexdigest()
    cert = dict(schema="row19-ec2-qualification-certificate-1", outcome=outcome, problems=problems, coverage_required=COVERAGE,
                coverage_short=short, parts=parts, memory=mem, replay=rep, released_attempts=[a.q1_key] if outcome == "RELEASE" else [],
                bound=dict(code={f: sha(os.path.join(T1, f)) for f in CODE if os.path.exists(os.path.join(T1, f))}, manifest_sha256=msha,
                           partition_sha256=psha, activation_sha256=actsha, inventory_sha256=inv.get("sha256"),
                           opmanifests={k: sha(p) for k, p in (("Q1", a.q1_opmanifest), ("Q2", a.q2_opmanifest))},
                           bundles={k: sha(os.path.join(b, "BUNDLE_SHA256SUMS")) if os.path.exists(os.path.join(b, "BUNDLE_SHA256SUMS")) else None
                                    for k, b in (("Q1", a.q1_bundle), ("Q2", a.q2_bundle))},
                           plans={k: sha(os.path.join(b, "env", "plan.json")) if os.path.exists(os.path.join(b, "env", "plan.json")) else None
                                  for k, b in (("Q1", a.q1_bundle), ("Q2", a.q2_bundle))},
                           shadow_records_sha256=shadow_digest), at=time.time())
    json.dump(cert, open(a.out, "w"), indent=1, sort_keys=True)
    print(json.dumps(dict(outcome=outcome, parts=parts, coverage_short=short, memory=mem, problems=problems[:10]), indent=1))
    return 0 if outcome == "RELEASE" else 3


if __name__ == "__main__":
    sys.exit(main())
