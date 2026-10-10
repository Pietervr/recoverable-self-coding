"""Sandbox test of chpc/row19_ec2_ingest.py on REAL records (Lengau login node, t1py, no fits, nothing in a production root).

    t1py test_row19_ec2_ingest.py <lengau screen root> <scratch dir>

Copies reps 3..6 of the Lengau root into a sandbox root, declares a test partition k=199 (block = indices 1..199) against a
sandbox manifest, moves the index-1 records out into a synthetic EC2 bundle (relabelled to the attempt: timing job/slot,
EC2 bindings under the operational manifest, plan, outcomes, attestation, checksums) and uses index-0 records as
sentinels. Cases: success; replay of an ingested attempt; crash after the first pair then replay; a swapped published
timing on replay; a sentinel mismatch; a contrary duplicate; an unlisted file; a coordinate outside the attempt."""
import os, sys, json, glob, shutil, hashlib, copy, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, "chpc")]
import row19_shard as SH, row19_partition as RP, analyze as A
import row19_ec2_ingest as IG

src_root, scratch = sys.argv[1], sys.argv[2]
REPS = [3, 4, 5, 6]; ok = True
def check(name, cond, extra=""):
    global ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""), flush=True)
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()

prod = json.load(open(os.path.join(HERE, "chpc", "row19_screen_manifest.json")))

def build(case):
    d = os.path.join(scratch, case); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    root = os.path.join(d, "root"); os.makedirs(os.path.join(root, "plans"))
    for r in REPS:
        for sub, f in (("records", "rec_000.json"), ("records", "rec_001.json"), ("timing", "t_000.json"), ("timing", "t_001.json")):
            os.makedirs(os.path.join(root, sub, f"rep{r}"), exist_ok=True)
            shutil.copy2(os.path.join(src_root, sub, f"rep{r}", f), os.path.join(root, sub, f"rep{r}", f))
    man = copy.deepcopy(prod); man["storage"] = {"root": root, "campaign": os.path.join(d, "camp")}
    mp = os.path.join(d, "manifest.json"); json.dump(man, open(mp, "w")); msha = sha(mp)
    part = RP.declare(man, msha, 199, 1); pp = os.path.join(d, "partition.json"); json.dump(part, open(pp, "w"))
    op = copy.deepcopy(prod); op["storage"] = {"root": "/mnt/prod/root", "campaign": "/mnt/prod/campaign"}; op["pbs"]["cores"] = 76
    op["ec2_production"] = {"epoch": 1}; opp = os.path.join(d, "op.json"); json.dump(op, open(opp, "w")); opsha = sha(opp)
    aid = "ec2-e1-a1"; b = os.path.join(d, "bundle"); broot = os.path.join(b, "root"); env = os.path.join(b, "env")
    os.makedirs(env); slots = []
    for k, r in enumerate(REPS):                                   # work: index 1 moved from the sandbox root into the bundle
        for sub, f in (("records", "rec_001.json"), ("timing", "t_001.json")):
            os.makedirs(os.path.join(broot, sub, f"rep{r}"), exist_ok=True)
            shutil.move(os.path.join(root, sub, f"rep{r}", f), os.path.join(broot, sub, f"rep{r}", f))
        slots.append(dict(slot=k, rep=r, indices=[1], role="work"))
    for k, r in enumerate(REPS[:2]):                               # sentinels: index 0 copies (Lengau keeps its own)
        for sub, f in (("records", "rec_000.json"), ("timing", "t_000.json")):
            os.makedirs(os.path.join(broot, sub, f"rep{r}"), exist_ok=True)
            shutil.copy2(os.path.join(root, sub, f"rep{r}", f), os.path.join(broot, sub, f"rep{r}", f))
        slots.append(dict(slot=len(REPS) + k, rep=r, indices=[0], role="sentinel"))
    for s in slots:                                                # relabel timings to the attempt and slot
        tp = SH.timing_path(broot, s["rep"], s["indices"][0]); t = json.load(open(tp)); t.update(job=aid, slot=s["slot"]); json.dump(t, open(tp, "w"))
    for r in REPS:
        json.dump(dict(binding=SH.binding_for(op, opsha, "/mnt/prod/root", r, SH.task(prod, r))), open(os.path.join(broot, f"task_{r}.json"), "w"), default=str)
    plan = dict(job=1, attempt_id=aid, epoch=1, slots=slots); json.dump(plan, open(os.path.join(env, "plan.json"), "w"))
    json.dump(dict(transfer_verified=True), open(os.path.join(env, "upload_verify.json"), "w"))
    json.dump(dict(profile="B_full", problems=[]), open(os.path.join(env, "attest_B.json"), "w"))
    json.dump(dict(outcomes={f"w_slot{s['slot']}": 0 for s in slots}, unresolved_after_kill=[]), open(os.path.join(env, "outcomes.json"), "w"))
    att = dict(attempt_id=aid, sequence=1, state="reconciled", plan_sha256=sha(os.path.join(env, "plan.json")),
               coordinates=[[r, 1] for r in REPS], sentinels=[[r, 0] for r in REPS[:2]], charged_usd=1.0)
    ap = os.path.join(d, "attempt.json"); json.dump(att, open(ap, "w"))
    return d, root, mp, pp, opp, ap, b

def sums(b):
    lines = []
    for p in sorted(glob.glob(os.path.join(b, "**", "*"), recursive=True)):
        rel = os.path.relpath(p, b)
        if os.path.isfile(p) and rel.split(os.sep)[0] in ("root", "env") and rel != os.path.join("env", "upload_verify.json"):
            lines.append(f"{sha(p)}  {rel}\n")
    open(os.path.join(b, "BUNDLE_SHA256SUMS"), "w").write("".join(lines))

def ingest(mp, pp, opp, ap, b):
    return IG.main(["--manifest", mp, "--partition", pp, "--opmanifest", opp, "--attempt", ap, "--bundle", b])

# 1 success + replay
d, root, mp, pp, opp, ap, b = build("ok"); sums(b)
rc = ingest(mp, pp, opp, ap, b)
reg = json.load(open(os.path.join(root, "ec2", "register.json")))["attempts"]["ec2-e1-a1"]
pub = all(os.path.exists(SH.record_path(root, r, 1)) and sha(SH.record_path(root, r, 1)) == reg["coordinates"][f"{r}/1"]["record_sha256"] for r in REPS)
check("success: 4 pairs published, register ingested, 2 sentinels equal", rc == 0 and reg["state"] == "ingested" and pub and len(reg["sentinels_equal"]) == 2)
check("canonical task bindings untouched (none written)", not glob.glob(os.path.join(root, "task_*.json")))
check("replay of an ingested attempt is a no-op", ingest(mp, pp, opp, ap, b) == 0)

# 2 crash after the first pair, then replay
d, root, mp, pp, opp, ap, b = build("crash"); sums(b)
real = IG.publish_copy; calls = {"n": 0}
def flaky(src, dst, want):
    calls["n"] += 1
    if calls["n"] == 3:
        raise ValueError("simulated crash")
    return real(src, dst, want)
IG.publish_copy = flaky; rc1 = ingest(mp, pp, opp, ap, b); IG.publish_copy = real
st1 = json.load(open(os.path.join(root, "ec2", "register.json")))["attempts"]["ec2-e1-a1"]["state"]
rc2 = ingest(mp, pp, opp, ap, b)
st2 = json.load(open(os.path.join(root, "ec2", "register.json")))["attempts"]["ec2-e1-a1"]["state"]
check("crash leaves 'ingesting'; replay completes to 'ingested'", rc1 == 3 and st1 == "ingesting" and rc2 == 0 and st2 == "ingested")

# 3 swapped timing on replay
d, root, mp, pp, opp, ap, b = build("swap"); sums(b)
IG.publish_copy = flaky; calls["n"] = 0; ingest(mp, pp, opp, ap, b); IG.publish_copy = real
tp = SH.timing_path(root, REPS[0], 1); t = json.load(open(tp)); t["wall_s"] += 1; json.dump(t, open(tp, "w"))
check("a swapped published timing HOLDS the replay", ingest(mp, pp, opp, ap, b) == 3)

# 4 sentinel mismatch (valid checksum, different statistic)
d, root, mp, pp, opp, ap, b = build("sentinel")
rp = SH.record_path(os.path.join(b, "root"), REPS[0], 0); rec = json.load(open(rp))
p0 = A.PREDICTORS[0]; band = sorted(rec["stats"][p0])[0]; rec["stats"][p0][band] = float(rec["stats"][p0][band]) + 1e-9
rec = {k: v for k, v in rec.items() if k != "sha"}; rec["sha"] = A._record_sha(rec); json.dump(rec, open(rp, "w")); sums(b)
check("sentinel mismatch HOLDS, nothing published", ingest(mp, pp, opp, ap, b) == 3 and not os.path.exists(os.path.join(root, "ec2", "register.json")))

# 5 contrary duplicate
d, root, mp, pp, opp, ap, b = build("dup")
rp = SH.record_path(os.path.join(b, "root"), REPS[1], 1); rec = json.load(open(rp)); shutil.copy2(rp, SH.record_path(root, REPS[1], 1))
p0 = A.PREDICTORS[0]; band = sorted(rec["stats"][p0])[0]; rec["stats"][p0][band] = float(rec["stats"][p0][band]) + 1e-9
rec = {k: v for k, v in rec.items() if k != "sha"}; rec["sha"] = A._record_sha(rec); json.dump(rec, open(rp, "w")); sums(b)
check("contrary duplicate HOLDS", ingest(mp, pp, opp, ap, b) == 3)

# 6 unlisted file / 7 coordinate outside the attempt
d, root, mp, pp, opp, ap, b = build("unlisted"); sums(b); open(os.path.join(b, "root", "stray.json"), "w").write("{}")
check("unlisted bundle file HOLDS", ingest(mp, pp, opp, ap, b) == 3)
d, root, mp, pp, opp, ap, b = build("foreign"); sums(b)
a = json.load(open(ap)); a["coordinates"] = a["coordinates"][1:]; json.dump(a, open(ap, "w"))
check("work coordinate not owned by the attempt HOLDS", ingest(mp, pp, opp, ap, b) == 3)
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
