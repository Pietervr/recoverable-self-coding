"""Row 19 screen: ingest ONE reconciled EC2 production attempt into the Lengau screen root (Codex RSC f3dd3d7 contract 4).

    t1py chpc/row19_ec2_ingest.py --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e1.json \
        --opmanifest <EC2 operational manifest> --attempt <attempt.json exported by the Mac authority> --bundle <staged dir>

Runs on the Lengau login node under t1py from the controller tree, holding the screen's plan lock (plans/.submit.lock), so
it never interleaves with an admission. Nothing is published unless EVERY check passes:
  bundle   BUNDLE_SHA256SUMS lists every file under root/ and env/ and each one matches; no unlisted file; the plan's sha256 is
           the attempt's; outcomes.json covers the declared processes; upload_verify.json transfer_verified; the attestation
           is B_full with no problem; the attempt id, epoch and partition sha agree everywhere.
  records  every work coordinate: in the partition block AND in the attempt's owned coordinates; row19_shard.read_record
           against the frozen task (identity, seed, B, index, draw, payload, own checksum); its EC2 binding equal to
           binding_for(operational manifest, its sha, the instance root, rep, task); its timing names this attempt id and
           the plan's slot, with positive finite wall and fit seconds; failed fits are kept as failed records (never dropped).
  sentinels each sentinel's record payload (row19_screen_verify.payload, float.hex) equals Lengau's record at that
           coordinate; ANY difference HOLDS the whole attempt (exit 3) and nothing is published.
  overlap  a work coordinate already present in the root counts once if its payload is identical (provenance kept in the
           register), and HOLDS the attempt if it differs - never replaced.
PUBLICATION (crash-safe). The register root/ec2/register.json gains this attempt as 'ingesting' with every coordinate's
staged record and timing sha256 BEFORE the first file is written; each pair is then published timing first, record second,
by temp + fsync + hard link (never replacing); the statuses are copied to root/ec2/status/<attempt>.slot<k>.json; the
entry becomes 'ingested' last. A rerun after a crash finds the 'ingesting' entry and completes it: a file already present
must hash to the registered value (a swapped or foreign file HOLDS), a missing one is published. The canonical Lengau
task_<rep>.json bindings are never written or changed; EC2 bindings are kept in the register."""
import os, sys, json, glob, math, time, fcntl, hashlib, argparse

HERE = os.path.dirname(os.path.abspath(__file__)); T1 = os.path.abspath(os.path.join(HERE, ".."))
for p in (T1, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import row19_shard as SH
import row19_screen_verify as V
import row19_partition as RP

HOLD, DONE = 3, 0


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def atomic_json(path, obj):
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, path)
    d = os.open(os.path.dirname(path), os.O_RDONLY)
    try:
        os.fsync(d)
    finally:
        os.close(d)


def publish_copy(src, dst, want_sha):
    """dst := bytes of src by temp + fsync + link (never replacing). Present dst must already hash to want_sha."""
    if os.path.exists(dst):
        if sha_file(dst) != want_sha:
            raise ValueError(f"{dst} exists with other bytes than the registered {want_sha[:12]}")
        return False
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = f"{dst}.tmp.{os.getpid()}"
    with open(src, "rb") as fi, open(tmp, "wb") as fo:
        fo.write(fi.read()); fo.flush(); os.fsync(fo.fileno())
    try:
        os.link(tmp, dst)
    finally:
        os.unlink(tmp)
    d = os.open(os.path.dirname(dst), os.O_RDONLY)
    try:
        os.fsync(d)
    finally:
        os.close(d)
    if sha_file(dst) != want_sha:
        raise ValueError(f"{dst}: published bytes do not hash to {want_sha[:12]}")
    return True


def check_bundle(bundle, att, problems):
    sums = os.path.join(bundle, "BUNDLE_SHA256SUMS")
    if not os.path.exists(sums):
        problems.append("no BUNDLE_SHA256SUMS"); return {}
    listed = {}
    for line in open(sums):
        h, f = line.rstrip("\n").split("  ", 1)
        listed[os.path.normpath(f)] = h
    present = {os.path.normpath(os.path.relpath(p, bundle)) for sub in ("root", "env")
               for p in glob.glob(os.path.join(bundle, sub, "**", "*"), recursive=True) if os.path.isfile(p)}
    for mutable in ("env/upload_verify.json", "env/userdata.log", "env/spot_notice.json", "env/stop_seen.txt"):   # diagnostics
        present.discard(os.path.normpath(mutable))                                                            # written after hashing
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
        if sha_file(os.path.join(env, "plan.json")) != att["plan_sha256"]:
            problems.append("the bundle's plan is not the attempt's")
        uv = json.load(open(os.path.join(env, "upload_verify.json")))
        if uv.get("transfer_verified") is not True:
            problems.append(f"transfer not verified: {uv}")
        at = json.load(open(os.path.join(env, "attest_B.json")))
        if at.get("profile") != "B_full" or at.get("problems"):
            problems.append(f"attestation {at.get('profile')} {at.get('problems')}")
        for f in ("FAILED", "OUTCOMES_FAILED", "BUNDLE_FAILED"):
            if os.path.exists(os.path.join(env, f)):
                problems.append(f"instance reported {f}")
        oc = json.load(open(os.path.join(env, "outcomes.json")))
        if oc.get("unresolved_after_kill") != []:
            problems.append(f"cleanup left unresolved process groups {oc.get('unresolved_after_kill')}")
        return oc["outcomes"]
    except Exception as e:
        problems.append(f"bundle metadata unreadable ({type(e).__name__}: {e})"); return {}


def plan_units(bundle, man, part, opman, opsha, att, problems):
    """Validated (rep, index) -> dict(rec, rec_path, timing_path, status_path, slot, role) for every plan slot."""
    plan = json.load(open(os.path.join(bundle, "env", "plan.json")))
    if plan.get("attempt_id") != att["attempt_id"] or plan.get("epoch") != part["epoch"]:
        problems.append("plan attempt id or epoch differs from the attempt/partition"); return {}
    owned = {tuple(c) for c in att["coordinates"]}; sent = {tuple(c) for c in att["sentinels"]}
    root = os.path.join(bundle, "root"); units = {}; tasks = {}
    for s in plan["slots"]:
        r, i, slot = int(s["rep"]), int(s["indices"][0]), int(s["slot"])
        c = (r, i); role = s.get("role")
        if role == "work" and (c not in owned or not RP.blocked(part, r, i)):
            problems.append(f"work slot {slot} {c}: not an owned block coordinate"); continue
        if role == "sentinel" and (c not in sent or RP.blocked(part, r, i)):
            problems.append(f"sentinel slot {slot} {c}: not the attempt's sentinel outside the block"); continue
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
        units[c] = dict(rec=rec, rec_path=rp, timing_path=tp, status_path=stp if os.path.exists(stp) else None, slot=slot, role=role,
                        rec_sha=sha_file(rp), timing_sha=sha_file(tp), binding=b)
    return units


def main(argv=None):
    ap = argparse.ArgumentParser()
    for k in ("--manifest", "--partition", "--opmanifest", "--attempt", "--bundle"):
        ap.add_argument(k, required=True)
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); msha = sha_file(a.manifest); part = RP.load(a.partition, man, msha)
    opman = json.load(open(a.opmanifest)); opsha = sha_file(a.opmanifest); att = json.load(open(a.attempt))
    root = man["storage"]["root"]; problems = []
    if att.get("state") != "reconciled":
        print(f"HELD: attempt {att.get('attempt_id')} is {att.get('state')}, not reconciled"); return HOLD
    if (opman.get("ec2_production") or {}).get("epoch") != part["epoch"]:
        print("HELD: the operational manifest is not this partition epoch's"); return HOLD
    outcomes = check_bundle(a.bundle, att, problems)
    units = plan_units(a.bundle, man, part, opman, opsha, att, problems) if not problems else {}
    # sentinels and overlaps against the live root
    for c, u in units.items():
        lp = SH.record_path(root, *c)
        if u["role"] == "sentinel":
            try:
                l = SH.read_record(lp, SH.task(man, c[0]), c[1])
            except ValueError as e:
                problems.append(f"sentinel {c}: Lengau record invalid ({e})"); continue
            if l is None or V.payload(l) != V.payload(u["rec"]):
                problems.append(f"SENTINEL MISMATCH at {c}: the EC2 payload is not Lengau's (float.hex)")
        elif os.path.exists(lp):
            l = SH.read_record(lp, SH.task(man, c[0]), c[1])
            if V.payload(l) != V.payload(u["rec"]):
                problems.append(f"contrary duplicate at {c}: a different payload is already in the root")
    if problems:
        print(f"HELD: {len(problems)} problem(s); nothing published"); [print("   -", p) for p in problems[:20]]; return HOLD
    os.makedirs(os.path.join(root, "ec2", "status"), exist_ok=True)
    regp = os.path.join(root, "ec2", "register.json")
    with open(os.path.join(root, "plans", ".submit.lock"), "a+") as lk:
        try:
            fcntl.flock(lk.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("HELD: the plan lock is held (an admission or another ingestion)"); return HOLD
        reg = json.load(open(regp)) if os.path.exists(regp) else {"schema": "row19-ec2-register-1", "attempts": {}}
        e = reg["attempts"].get(att["attempt_id"])
        work = {c: u for c, u in units.items() if u["role"] == "work"}
        if e is None:
            e = dict(attempt_id=att["attempt_id"], sequence=att["sequence"], epoch=part["epoch"], plan_sha256=att["plan_sha256"],
                     opmanifest_sha256=opsha, partition_sha256=sha_file(a.partition), state="ingesting", started=time.time(),
                     coordinates={f"{r}/{i}": dict(slot=u["slot"], record_sha256=u["rec_sha"], timing_sha256=u["timing_sha"],
                                                   preexisting=os.path.exists(SH.record_path(root, r, i)), failed=bool(u["rec"]["failed"]),
                                                   ec2_binding=u["binding"])
                                  for (r, i), u in work.items()},
                     sentinels_equal=sorted(f"{r}/{i}" for (r, i), u in units.items() if u["role"] == "sentinel"),
                     outcomes=outcomes, settlement=att.get("terminal"), charged_usd=att.get("charged_usd"))
            reg["attempts"][att["attempt_id"]] = e; atomic_json(regp, reg)
        elif e["state"] == "ingested":
            print(f"already ingested: {att['attempt_id']}"); return DONE
        published = 0
        try:
            for key, ce in e["coordinates"].items():
                r, i = (int(x) for x in key.split("/")); u = work[(r, i)]
                if ce["preexisting"]:
                    continue                                                   # identical payload already counted
                published += publish_copy(u["timing_path"], SH.timing_path(root, r, i), ce["timing_sha256"])
                published += publish_copy(u["rec_path"], SH.record_path(root, r, i), ce["record_sha256"])
                if u["status_path"]:
                    publish_copy(u["status_path"], os.path.join(root, "ec2", "status", f"{att['attempt_id']}.slot{u['slot']}.json"), sha_file(u["status_path"]))
        except ValueError as ex:
            print(f"HELD during publication (entry stays 'ingesting' for a checked replay): {ex}"); return HOLD
        e.update(state="ingested", finished=time.time()); atomic_json(regp, reg)
    print(f"ingested {att['attempt_id']}: {len(e['coordinates'])} coordinates ({published} files published), "
          f"{len(e['sentinels_equal'])} sentinels equal")
    return DONE


if __name__ == "__main__":
    sys.exit(main())
