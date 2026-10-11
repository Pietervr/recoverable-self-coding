"""Tests of ec2_sync.py: a full cycle against a local stand-in for the Lengau root (the transport copies files and runs
chpc/row19_ec2_root.py install in-process on a sandbox manifest). No AWS, no ssh; a temporary authority directory.
    python3 tests/test_ec2_sync.py"""
import contextlib, io, json, os, shutil, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE); sys.path[:0] = [PKG, os.path.join(PKG, "..", "chpc")]
import prod_authority as PA, bench_launch as L, row19_ec2_state as ES, row19_ec2_root as RR, ec2_sync as SY
TMP = tempfile.mkdtemp()
for f in ("budget_baseline.json", "ec2_release_state.json"):
    shutil.copy(os.path.join(PKG, f), os.path.join(TMP, f))
L.HERE = PA.HERE = TMP
PA.LOCK, PA.STATE = os.path.join(TMP, "runs", ".authority.lock"), os.path.join(TMP, "runs", ".authority_state.json")
PA.INV_DIR, PA.RELEASE_STATE = os.path.join(TMP, "runs", "inventory"), os.path.join(TMP, "ec2_release_state.json")
ROOT = os.path.join(TMP, "lroot"); MAN = os.path.join(TMP, "manifest.json")
json.dump({"storage": {"root": ROOT}}, open(MAN, "w"))
ok = True
def check(n, c, x=""):
    global ok; ok &= bool(c); print(("PASS " if c else "FAIL ") + n + (f"  [{x}]" if x and not c else ""))
def att(n, seq, coords, state="reconciled", **kw):
    return dict(dict(attempt=n, sequence=seq, attempt_id=f"a{n}", state=state, ingestion="pending", contract="production", plan_sha256="p",
                     coordinates=[list(c) for c in coords], lifetime_s=79200, max_price=1.20, anc_h=PA.ANC_H_PROD, s3_fixed=PA.S3_FIXED_PROD,
                     terminal=dict(compute_s=60, ancillary_s=60)), **kw)


class Local:
    def __init__(self, fail_install=False):
        self.fail_install, self.installs = fail_install, 0
    def put(self, src, dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy(src, dst)
    def get(self, src, dst):
        if not os.path.exists(src):
            return False
        os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy(src, dst); return True
    def install(self, rinv):
        self.installs += 1
        if self.fail_install:
            return 3, "HELD: simulated"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = RR.main(["install", "--manifest", MAN, "--inventory", rinv])
        return rc, buf.getvalue().strip()

logs = []
log = logs.append
with PA.authority_lock():
    PA.bump(PA.state(), sequences=3)
L.save("prod-e1", {"run": "prod-e1", "attempts": [att(1, 1, [(3, 199)]), att(2, 2, [(4, 199)], disposition_request=dict(reason="no output", at=1.0))]})

# 1 a held installation stops the cycle before anything is released
tr = Local(fail_install=True)
check("a held installation fails the cycle (exit 3), nothing released", SY.cycle(tr, ROOT, log) == 3
      and all(a["ingestion"] == "pending" for a in L.load("prod-e1")["attempts"]))

# 2 full cycle: install, the root fences the disposition, the Mac confirms it; the ingested attempt is acknowledged
reg = dict(schema=ES.REGISTER_SCHEMA, authority_generation=0, fence={}, attempts={
    "a1": dict(attempt_id="a1", state="ingested", key="prod-e1/1", sequence=1, plan_sha256="p", coordinates={"3/199": {}})})
os.makedirs(os.path.dirname(ES.paths(ROOT)["register"]), exist_ok=True); json.dump(reg, open(ES.paths(ROOT)["register"], "w"))
tr = Local(); logs.clear()
rc = SY.cycle(tr, ROOT, log)
A = {a["attempt"]: a for a in L.load("prod-e1")["attempts"]}
check("cycle exits 0", rc == 0, logs)
check("the requested disposition is confirmed on the root's acknowledgement", A[2]["ingestion"] == "dispositioned" and A[2]["disposition_ack"]["generation"] >= 1)
check("the ingested attempt is acknowledged against the pulled register", A[1]["ingestion"] == "ingested")
check("neither attempt owns any more", PA.owned(PA.ledgers()) == {})
check("after releases the next generation is sealed and installed in the same cycle", tr.installs == 2
      and json.load(open(ES.paths(ROOT)["inventory"]))["generation"] == PA.state()["generation"])
check("the acknowledgements are kept on the Mac", len(os.listdir(os.path.join(PA.INV_DIR, "acks"))) == 2)

# 3 idempotent: a second cycle changes nothing and installs one generation
gen = PA.state()["generation"]; tr = Local()
check("a repeated cycle is a no-op apart from one installation", SY.cycle(tr, ROOT, log) == 0 and tr.installs == 1
      and all(a["ingestion"] in ("ingested", "dispositioned") for a in L.load("prod-e1")["attempts"]))

# 4 a root refusal keeps ownership and is reported
L.save("prod-e2", {"run": "prod-e2", "attempts": [att(1, 9, [(5, 199)], attempt_id="b1", disposition_request=dict(reason="x", at=1.0))]})
reg = json.load(open(ES.paths(ROOT)["register"]))
reg["attempts"]["b1"] = dict(attempt_id="b1", key="prod-e2/1", sequence=9, state="ingesting", coordinates={})
json.dump(reg, open(ES.paths(ROOT)["register"], "w"))
with PA.authority_lock():
    PA.bump(PA.state(), sequences=9)
logs.clear(); rc = SY.cycle(Local(), ROOT, log)
check("a root refusal (output being ingested) keeps the attempt owning and is reported",
      rc == 0 and PA.owner_of(PA.ledgers(), (5, 199)) == ("prod-e2/1", 9) and any("REFUSED" in x for x in logs), logs)

# 5 an acknowledgement that does not match the sealed inventory stops the cycle
class Forging(Local):
    def get(self, src, dst):
        r = super().get(src, dst)
        if r and os.path.basename(dst).startswith("ack_g"):
            d = json.load(open(dst)); d["inventory_sha256"] = "0" * 64; json.dump(d, open(dst, "w"))
        return r
check("a pulled acknowledgement of another inventory stops the cycle", SY.cycle(Forging(), ROOT, log) == 3)

shutil.rmtree(TMP)
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
