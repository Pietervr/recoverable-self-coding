"""R6' - the five-instance fleet: INTERLEAVED admissions and reconciliations on one prod-e2 run ledger through the REAL
administrative locks, ledgers, sealed inventory generations and budget/fleet/epoch reservations
(chpc/candidate_e2/QUALIFICATION_E2.md s.3 item 6; reviews/2026-10-19_e2_adoption_codex_review.md "Before five-way
production"). CANDIDATE test, synthetic only: no AWS, no ssh, no Lengau, no network.

A temporary PROMOTED tree is built from the exact reviewed bytes (every promoted file is checked against its v17 promotion
map row; unchanged live files are copied as they are): aws_ec2/{prod_authority,prod_launch,bench_launch,bench_reaper}.py,
the epoch-2 helpers in chpc/, the v17 controls with a FIXTURE adoption record bound to the committed re-review (which
carries the ADOPT line) in a private git repository, the final partition, snapshot, funding, panel and manifests, and a
copy of the pinned qual-Q2 ledger (the A4 funding basis). The epoch-2 release is adopted IN THAT TREE by the real
prod_authority.release_adopt from a synthetic schema-3 certificate and review (fixtures, labelled). Then:
  - admissions are separate processes running the real prod_launch.main() (r6_admit.py; the only substitution is the
    toolchain tarball pin), so the global authority lock and the run lock are real flock()s between processes;
  - each admitted instance gets the REAL bench_reaper.py, started detached by the real launcher (caffeinate), polling a fake
    EC2 (fake_aws.py on PATH; AWS credential files, profile and proxies pointed at nothing, a guard checks the resolved
    binary);
  - Lengau is a local directory: the real row19_ec2_state.install_inventory installs each sealed generation and a
    synthetic whole-role receipt binds it (the ec2_sync + watch steps).
Checked: unique global sequences; sibling changes retained across interleaved admission/reconciliation; immutable, strictly
increasing inventory generations (and the installer's refusal of an older one); cumulative worst-case reservations
(including a refusal and an admission at the USD 3,000 cap boundary); the sixth-admission refusal at five live instances;
stale-receipt refusals; admission interruption (killed in RunInstances) and recovery re-issuing the same token without a
second instance; reaper interruption and manual restart; replays that change nothing.

    python3 chpc/candidate_r6/test_r6_fleet.py            (from workspace_demo/t1_access; ~5.5 min, reapers poll at 60 s)"""
import glob, hashlib, json, os, shutil, signal, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__)); CHPC = os.path.dirname(HERE); RSC_T1 = os.path.dirname(CHPC)
fails, n = [], [0]
T0 = time.time()


def check(name, cond, extra=""):
    n[0] += 1
    print(f"{'ok  ' if cond else 'FAIL'} [{time.time() - T0:5.0f}s] {name}" + (f"  [{str(extra)[:400]}]" if extra and not cond else ""), flush=True)
    if not cond:
        fails.append(name)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def wjson(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True)
    return p


TMP = os.path.realpath(tempfile.mkdtemp(prefix="r6_"))
import atexit
atexit.register(lambda: subprocess.run(["pkill", "-9", "-f", TMP], capture_output=True))      # never leave a reaper behind
FT1 = os.path.join(TMP, "rsc", "workspace_demo", "t1_access"); FAWS = os.path.join(FT1, "aws_ec2")
MAP = {r["promoted"]: r for r in json.load(open(os.path.join(CHPC, "candidate_v17", "v17_promotion_map.json")))["rows"]}
V17 = json.load(open(os.path.join(CHPC, "candidate_v17", "row19_screen_controls.json")))["versions"][-1]["files"]
LIVE = ["aws_ec2/bench_launch.py", "aws_ec2/bench_reaper.py", "aws_ec2/attest.py", "aws_ec2/prod_userdata.sh", "chpc/programme_gate.py",
        "chpc/row19_ec2_root.py", "chpc/row19_shard.py", "chpc/row19_screen_verify.py", "chpc/row19_screen_designated.json",
        "chpc/row19_screen_manifest.json", "chpc/row19_partition_e1.json", "analyze.py", "models.py"]
REVIEW = "reviews/2026-10-19_e2_repair_codex_rereview.md"
copied = {}
for rel, row in MAP.items():
    if rel.startswith("chpc/row19_screen_admit") or rel.endswith("make_e2_funding.py") or rel.endswith("qual_permit.py") or rel.endswith("make_prod_manifest.py"):
        continue                                                         # not used by admission/reconciliation
    src = os.path.join(RSC_T1, row["source"]); dst = os.path.join(FT1, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst); copied[rel] = (sha(dst) == row["sha256"])
for rel in LIVE + [REVIEW]:
    dst = os.path.join(FT1, rel); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copyfile(os.path.join(RSC_T1, rel), dst)
os.makedirs(os.path.join(FT1, "chpc", "e2_final"))
shutil.copyfile(os.path.join(CHPC, "e2_final", "claims_snapshot_e2.json"), os.path.join(FT1, "chpc", "e2_final", "claims_snapshot_e2.json"))
os.makedirs(os.path.join(FAWS, "runs", "qual-Q2"))
shutil.copyfile(os.path.join(RSC_T1, "aws_ec2", "runs", "qual-Q2", "attempts.json"), os.path.join(FAWS, "runs", "qual-Q2", "attempts.json"))
check("tree: every promoted file is its v17 promotion-map bytes", copied and all(copied.values()), copied)
check("tree: unchanged pins are the v17 controls' pins (programme_gate, row19_ec2_root, verifier, designated)",
      all(sha(os.path.join(FT1, r)) == V17[r] for r in ("chpc/programme_gate.py", "chpc/row19_ec2_root.py", "chpc/row19_screen_verify.py",
                                                         "chpc/row19_screen_designated.json")))
CTL_SHA = sha(os.path.join(FT1, "chpc", "row19_screen_controls.json"))
wjson(os.path.join(FT1, "chpc", "row19_screen_controls_adoption.json"),
      {"schema": "row19-screen-controls-adoption-1", "controls_path": "chpc/row19_screen_controls.json", "controls_sha256": CTL_SHA, "version": 17,
       "review_record": {"path": REVIEW, "sha256": sha(os.path.join(FT1, REVIEW)),
                         "adopt_line": f"ADOPT row19-screen-controls sha256={CTL_SHA} version=17"},
       "by": "R6' TEST FIXTURE", "scope": "synthetic adoption inside a temporary test tree; adopts nothing anywhere else"})
G = ["git", "-c", "user.name=r6-fixture", "-c", "user.email=r6@invalid", "-c", "commit.gpgsign=false"]
subprocess.run(["git", "init", "-q", FT1], check=True)
subprocess.run(G + ["-C", FT1, "add", "chpc/row19_screen_controls.json", "chpc/row19_screen_controls_adoption.json", REVIEW], check=True)
subprocess.run(G + ["-C", FT1, "commit", "-q", "-m", "R6' fixture tree"], check=True)

# ---- the fake EC2 / S3 / SSM environment (subprocesses only ever see this) --------------------------------------------------
FAKE = os.path.join(TMP, "fake"); BIN = os.path.join(FAKE, "bin"); os.makedirs(BIN)
STATE = os.path.join(FAKE, "state.json"); json.dump({}, open(STATE, "w"))
open(os.path.join(BIN, "aws"), "w").write(f"#!/bin/bash\nexec {sys.executable} {os.path.join(HERE, 'fake_aws.py')} \"$@\"\n")
os.chmod(os.path.join(BIN, "aws"), 0o755)
TGZ = os.path.join(FAKE, "t1_toolchain_lengau.tgz"); open(TGZ, "w").write("synthetic toolchain tarball (R6')\n")
ENV = {k: v for k, v in os.environ.items() if not k.startswith("AWS_")}
ENV.update(PATH=BIN + os.pathsep + os.environ["PATH"], R6_FAKE_STATE=STATE, R6_TARBALL_SHA=sha(TGZ), AWS_CONFIG_FILE="/nonexistent/r6",
           AWS_SHARED_CREDENTIALS_FILE="/nonexistent/r6", AWS_EC2_METADATA_DISABLED="true", HTTPS_PROXY="http://127.0.0.1:9",
           HTTP_PROXY="http://127.0.0.1:9", NO_PROXY="")
which = subprocess.run(["bash", "-c", "command -v aws"], env=ENV, capture_output=True, text=True).stdout.strip()
check("guard: `aws` resolves to the fake for every subprocess; credentials, profile and proxies point at nothing", which == os.path.join(BIN, "aws"), which)
if which != os.path.join(BIN, "aws"):
    sys.exit("REFUSING to continue: a real aws binary could be reached")


def fake(fn):
    import fcntl
    with open(STATE + ".lock", "a+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        s = json.load(open(STATE)); r = fn(s)
        json.dump(s, open(STATE + ".tmp", "w"), indent=1); os.replace(STATE + ".tmp", STATE)
        return r


def aws_calls(kind=None):
    p = os.path.join(FAKE, "aws_calls.jsonl")
    calls = [json.loads(l) for l in open(p)] if os.path.exists(p) else []
    return [c for c in calls if kind is None or kind in c["args"]]


def runi_count():
    """RunInstances calls actually answered or hung (the fake logs each call once more with its result)."""
    return len([c for c in aws_calls("run-instances") if "result" in c])


# ---- in-process view of the fake tree's own authority modules (for setup and for reading state) -----------------------------
sys.path.insert(0, FAWS)
import prod_authority as PA                                               # the fake tree's file: its T1/HERE are the fake tree
import bench_launch as L
import row19_ec2_state as ES, row19_partition as RP, row19_ec2_e2qual as EQ
check("tree: the in-process modules are the fake tree's (paths resolve inside it, promoted layout, not a candidate run)",
      PA.HERE == FAWS and L.HERE == FAWS and PA.T1 == FT1 and not PA.CANDIDATE_RUN and os.path.dirname(ES.__file__) == os.path.join(FT1, "chpc"))
MAN = json.load(open(os.path.join(FT1, "chpc", "row19_screen_manifest.json")))
PART_P = os.path.join(FT1, "chpc", "row19_partition_e2.json"); PSHA = sha(PART_P); PART = RP.load(PART_P, MAN, PA.PROD_SHA)
PANEL = json.load(open(os.path.join(FAWS, "prod", "panel_e2q_e2.json")))
MANP = os.path.join(FAWS, "prod", "manifest_production_e2.json")
ctl_doc, why = RP.adopted_controls()
check("tree: the real adoption gate accepts the fixture adoption of the exact v17 controls (git-tracked, review line)", not why and ctl_doc["versions"][-1]["version"] == 17, why)

# the qualified E2Q1 attempt and the epoch-2 release (fixtures), adopted by the REAL release_adopt
os.makedirs(os.path.join(FAWS, "fixture")); os.makedirs(os.path.join(FAWS, "runs", "qual-E2Q1"))
SENT_Q = [[3, 0], [3, 1], [4, 0], [5, 0]]
slots = [dict(slot=k, rep=r, indices=[i], role=role) for k, (role, (r, i)) in
         enumerate([("work", c) for c in PANEL["work"]] + [("qual_lengau", c) for c in PANEL["duplicates"]] + [("sentinel", c) for c in SENT_Q])]
plan_q = dict(job=1, attempt_id="ec2-qual-E2Q1-a1", sequence=60, epoch=2, contract="E2Q1", partition_sha256=PSHA,
              opmanifest_sha256=MAP["aws_ec2/prod/manifest_e2q1_e2.json"]["sha256"], activation_sha256="a" * 64,
              instance=dict(ES.CONTRACTS["E2Q1"]), lifetime_s=79200, slots=slots)
pq = wjson(os.path.join(FAWS, "runs", "qual-E2Q1", "plan_attempt1.json"), plan_q)
L.save("qual-E2Q1", {"run": "qual-E2Q1", "attempts": [dict(
    attempt=1, sequence=60, attempt_id="ec2-qual-E2Q1-a1", contract="E2Q1", state="reconciled", ingestion="pending", plan=pq, plan_sha256=sha(pq),
    coordinates=PANEL["work"], sentinels=SENT_Q, duplicates=PANEL["duplicates"], lifetime_s=79200, max_price=1.20, anc_h=PA.ANC_H_PROD,
    s3_fixed=PA.S3_FIXED_PROD, type="c7a.24xlarge", region=L.REGION, terminal=dict(compute_s=21 * 3600, ancillary_s=21 * 3600))]})
json.dump({"generation": 1, "next_sequence": 61}, open(PA.STATE, "w"))
open(os.path.join(FAWS, "fixture", "row23_report.json"), "w").write('{"R6 FIXTURE": "row 23 report stand-in"}\n')
open(os.path.join(FAWS, "fixture", "e2q1_permission.md"), "w").write("R6' FIXTURE: qualification_e2 permission record stand-in\n")
open(os.path.join(FAWS, "runs", "BENCH_FENCE.json"), "w").write("{}")
wjson(PA.RELEASE_STATE, {"schema": "t1-ec2-release-state-1", "note": "R6' FIXTURE release state of a temporary tree",
                         "row23": dict(declared_success=True, report_path="fixture/row23_report.json", report_sha256=sha(os.path.join(FAWS, "fixture", "row23_report.json"))),
                         "qualification": dict(permitted=False, ceilings_usd=PA.QUAL_CEILINGS_USD, owner_accepted_ceilings=False, record_path=None, record_sha256=None),
                         "qualification_e2": dict(permitted=True, record_path="fixture/e2q1_permission.md", record_sha256=sha(os.path.join(FAWS, "fixture", "e2q1_permission.md"))),
                         "production": dict(released=False, certificate_path=None, certificate_sha256=None, review_path=None, review_sha256=None, released_attempts=[])})
wjson(os.path.join(FAWS, "budget_baseline.json"), dict(schema="t1-aws-budget-baseline-2", spent_usd=500.0, through_utc="R6 fixture",
                                                       through_epoch=time.time(), idle_usd_per_day=0.0, note="R6' FIXTURE"))
SYN = [dict(file=f, original_sha256="1" * 64, modified_sha256=None, label="SYNTHETIC: removed") for f in ("root/records/x", "root/timing/x", "root/status/x")]
cert = dict(schema=EQ.CERT_SCHEMA, epoch=2, outcome="RELEASE", problems=[], coverage_required=dict(EQ.COVERAGE), coverage_short={},
            parts=dict(R1=dict(coordinates=20, successful_both=20), R4_sentinels=dict(coordinates=4), R2_validity=dict(coordinates=52, produced=52, unproduced=[])),
            memory=dict(workers=76, samples_at_full_packing=1200, peak_host_used_gib=151.0), unproduced=[], concentration=dict(slots=76, max=63),
            replay=dict(scope=EQ.REPLAY_SCOPE, presented_class="production", final_state="ingested", hashes_equal=True,
                        per_slot=dict(mode="synthetic", listed=True, fenced=True, evidence_journaled=True, ack_problem="", ingest_rc=0,
                                      modified_replay_held=True, activation_problems=[], synthetic=SYN)),
            released_attempts=["qual-E2Q1/1"], attempt=dict(key="qual-E2Q1/1", run="qual-E2Q1", contract="E2Q1", attempt_id="ec2-qual-E2Q1-a1",
                                                            sequence=60, plan_sha256=sha(pq)),
            bound=dict(code={rel: sha(os.path.join(FT1, rel)) for rel in EQ.CODE}, manifest_sha256=PA.PROD_SHA, partition_sha256=PSHA,
                       owned_sha256=PART["owned_sha256"], funding_sha256=sha(PA.E2_FUNDING), lifetime_s=79200,
                       opmanifests=dict(qualified=MAP["aws_ec2/prod/manifest_e2q1_e2.json"]["sha256"], production=sha(MANP)),
                       panel_sha256=sha(PA.E2Q_PANEL), claims_snapshot_sha256=sha(os.path.join(FT1, PANEL["claims_snapshot"]["path"])), plan_sha256=sha(pq)),
            note="R6' FIXTURE: a synthetic certificate in a temporary tree, never an actual qualification result")
cp = wjson(os.path.join(FAWS, "fixture", "cert_e2q1.json"), cert)
open(os.path.join(FAWS, "fixture", "review_e2q1.md"), "w").write(
    "R6' FIXTURE review (synthetic): FAVOURABLE\n" + EQ.RELEASE_LITERAL.format(sha=sha(cp), keys="qual-E2Q1/1") + "\n")
with PA.authority_lock():
    keys = PA.release_adopt("fixture/cert_e2q1.json", "fixture/review_e2q1.md")
rel = PA.release_state()
check("setup: the REAL release_adopt releases epoch-2 production in the fake tree (bound production manifest)",
      keys == ["qual-E2Q1/1"] and rel["production"]["ok"] and rel["production"]["epoch"] == 2
      and rel["production"]["production_opmanifest_sha256"] == sha(MANP), rel["production"].get("why"))

# ---- the Lengau stand-in: installed inventory, activation, receipts --------------------------------------------------------
SNAP = os.path.join(TMP, "lengau_snapshot"); ROOT = os.path.join(SNAP, "live", "refit", "root"); RECS = os.path.join(SNAP, "receipts")
os.makedirs(os.path.join(ROOT, "ec2")); os.makedirs(RECS)
IDENT = dict(root=os.path.abspath(ROOT), manifest_sha256=PA.PROD_SHA, mode="canonical")
v17 = ctl_doc["versions"][-1]
wjson(os.path.join(ROOT, "ec2", "activation_e2.json"),
      dict(schema=ES.ACTIVATION_SCHEMA, mode="canonical", epoch=2, partition_sha256=PSHA, manifest_sha256=PA.PROD_SHA, controls_sha256=CTL_SHA,
           controls_version=17, controls_entry_sha256=RP.entry_sha(v17), adoption_sha256=sha(os.path.join(FT1, "chpc", "row19_screen_controls_adoption.json")),
           predecessor=PART["predecessor"], transferred_indices=RP.transferred_of(PART), owned_sha256=PART["owned_sha256"], note="R6' FIXTURE"))
snapdoc = json.load(open(os.path.join(FT1, "chpc", "claims_snapshot_e2.json")))
json.dump({"units": {f"{r}/{i}": {"record": {"ok": True}} for r, i in snapdoc["lengau_done"]}}, open(os.path.join(RECS, "verify_refit_r6.json"), "w"))
RCPT = [0]


def lengau_sync(**kw):
    """ec2_sync's install step (the REAL installer) + a fresh whole-role receipt binding the installed state."""
    inv = json.load(open(os.path.join(PA.INV_DIR, "latest.json")))
    ack, why = ES.install_inventory(ROOT, inv, IDENT)
    assert not why, why
    RCPT[0] += 1
    w = dict(schema="row19-screen-watch-1", role="refit", time=time.time(), fresh=True, production=True, alarms=[],
             bound=dict(verify_file="verify_refit_r6.json", verify_file_sha256=sha(os.path.join(RECS, "verify_refit_r6.json"))),
             ec2=dict(bound=ES.bound(ROOT)))
    w.update(kw)
    json.dump(w, open(os.path.join(RECS, f"watch_refit_{RCPT[0]:06d}.json"), "w"))
    return inv["generation"]


with PA.authority_lock():
    PA.write_inventory()
lengau_sync()

R6_ADMIT = os.path.join(HERE, "r6_admit.py")
BASE_ARGS = ["--contract", "production", "--epoch", "2", "--partition", PART_P, "--manifest", MANP, "--snapshot", SNAP, "--tarball", TGZ]


def admit(*extra, wait=True):
    p = subprocess.Popen([sys.executable, R6_ADMIT, FT1, *BASE_ARGS, *extra], env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, start_new_session=True)
    if not wait:
        return p
    out, _ = p.communicate(timeout=600)
    return p.returncode, out


def led():
    return L.load("prod-e2")["attempts"]


def att(k):
    return next((a for a in led() if a["attempt"] == k), None)


def gen():
    return PA.state()["generation"]


ARCH = {}


def archives():
    """{generation: sha256} of every sealed archive; asserts earlier archives never change."""
    cur = {int(os.path.basename(p)[len("inventory_g"):-5]): sha(p) for p in glob.glob(os.path.join(PA.INV_DIR, "inventory_g*.json"))}
    changed = [g for g, h in ARCH.items() if cur.get(g) != h]
    ARCH.update(cur)
    return cur, changed


def iid_of(k):
    tok = att(k)["client_token"]
    return fake(lambda s: next((i for i, v in s.get("instances", {}).items() if v["token"] == tok), None))


def terminate(*ks):
    ids = [iid_of(k) for k in ks]
    fake(lambda s: [s["instances"][i].update(state="terminated", reason="Client.InstanceInitiatedShutdown: R6 fake") for i in ids])
    return ids


def wait_for(pred, timeout=150, step=1.0):
    t = time.time()
    while time.time() - t < timeout:
        if pred():
            return True
        time.sleep(step)
    return pred()


def reaper_pids(k=None):
    pat = os.path.join(FAWS, "bench_reaper.py") + " --run prod-e2" + (f" --attempt {k}$" if k else "")
    r = subprocess.run(["pgrep", "-f", pat], capture_output=True, text=True)
    return [int(x) for x in r.stdout.split()]


def reconciled(k):
    """The reaper records the ledger and THEN seals a generation, both under the locks; it is done when it has exited."""
    return att(k)["state"] == "reconciled" and not reaper_pids(k)


def reaper_log(k):
    p = os.path.join(FAWS, "runs", "prod-e2", f"reaper_attempt{k}.log")
    return open(p).read() if os.path.exists(p) else ""


WORST = PA.worst_usd(79200, 1.20)
SEQ = []


def admitted(name, k, rc_out):
    rc, out = rc_out
    a = att(k)
    ok = rc == 0 and a is not None and a["state"] == "launched" and a.get("instance") == iid_of(k)
    if ok:
        SEQ.append(a["sequence"])
    check(name, ok and wait_for(lambda: bool(reaper_pids(k)), 30), out[-600:])


def refused(name, rc_out, want, k_next=None):
    rc, out = rc_out
    REFUSALS.append(name)
    g0 = GEN_BEFORE[0]
    check(name, rc != 0 and want in out and (k_next is None or att(k_next) is None) and gen() == g0
          and runi_count() == RUNI[0], out[-400:])


GEN_BEFORE, RUNI, REFUSALS = [0], [0], []


def snap_counts():
    GEN_BEFORE[0] = gen(); RUNI[0] = runi_count()


# ============================================================================================================================
# 1. admissions 1-3, with a stale-receipt refusal between
g0 = gen()
admitted("A1: the first production admission (real locks, ledger, sequence, sealed generations, dispatch, reaper)", 1, admit())
a1 = att(1)
check("A1: global sequence 61 (after qual-Q2 7 and qual-E2Q1 60), 72 work + 4 sentinels, worst-case reserved", a1["sequence"] == 61
      and sum(1 for s in json.load(open(a1["plan"]))["slots"] if s["role"] == "work") == 72 and abs(PA.charged(a1) - WORST) < 1e-9)
check("A1: intent and dispatch outcome are two new sealed generations (and the sequence reservation bump)", gen() == g0 + 3, (g0, gen()))
snap_counts()
refused("stale receipt: a second admission on the receipt taken before A1 is refused (does not bind the current inventory)",
        admit(), "does not bind the current authority inventory", 2)
lengau_sync(time=time.time() - 2800)
snap_counts()
refused("stale receipt: an installed-and-bound receipt older than 2,700 s is refused", admit(), "older than 2700", 2)
lengau_sync()
admitted("A2: admitted on a fresh receipt binding the current generation", 2, admit())
lengau_sync()
admitted("A3: admitted", 3, admit())

# 2. INTERLEAVING: admission A4 holds the global and run locks (paused in its S3 uploads) while reaper 1 observes its
#    instance's end and must wait for the authority lock to record the reconciliation
lengau_sync()
open(os.path.join(FAKE, "hold_s3cp"), "w").write("hold")
p4 = admit(wait=False)
check("interleave: A4 is inside its locks (paused in an S3 upload)", wait_for(lambda: os.path.exists(os.path.join(FAKE, "s3cp_waiting")), 60))
snap_counts()
refused("interleave: a concurrent admission while A4 holds the locks is refused at once (another authority operation holds the lock)",
        admit(), "holds the lock")
terminate(1)
check("interleave: reaper 1 observes its instance terminated", wait_for(lambda: "observed terminated" in reaper_log(1), 90), reaper_log(1)[-300:])
time.sleep(4)
check("interleave: ... and cannot record it while A4 holds the global authority lock (attempt 1 still 'launched', reaper alive)",
      att(1)["state"] == "launched" and reaper_pids(1) and att(4) is None)
os.remove(os.path.join(FAKE, "hold_s3cp")); os.remove(os.path.join(FAKE, "s3cp_waiting"))
out4, _ = p4.communicate(timeout=300)
admitted("interleave: A4 completes once released", 4, (p4.returncode, out4))
check("interleave: reaper 1 then records attempt 1 'reconciled'", wait_for(lambda: reconciled(1), 60), reaper_log(1)[-300:])
latest = json.load(open(os.path.join(PA.INV_DIR, "latest.json")))
check("retained siblings: the ledger and the newest generation carry BOTH changes (A4 launched, attempt 1 reconciled)",
      att(4)["state"] == "launched" and att(1)["state"] == "reconciled" and att(1).get("terminal") and
      latest["attempts"]["prod-e2/4"]["state"] == "launched" and latest["attempts"]["prod-e2/1"]["state"] == "reconciled")
cur, changed = archives()
check("generations: no sealed archive ever changed", not changed, changed)

# 3. a reconciliation that lands AFTER the receipt makes that receipt stale for the next admission
lengau_sync()
terminate(2)
check("reaper 2 reconciles attempt 2 (sealing a new generation after the receipt)", wait_for(lambda: reconciled(2), 120))
snap_counts()
refused("stale receipt: a reconciliation sealed after the receipt refuses the next admission", admit(), "does not bind the current authority inventory", 5)
lengau_sync(); admitted("A5: admitted on a receipt taken after the reconciliation", 5, admit())
lengau_sync(); admitted("A6: admitted", 6, admit())
lengau_sync(); admitted("A7: admitted - five instances live (3, 4, 5, 6, 7)", 7, admit())
live = PA.live_fleet(PA.ledgers())
check("fleet: exactly five live production/qualification instances", live == [f"prod-e2/{k}" for k in (3, 4, 5, 6, 7)], live)

# 4. the sixth-admission refusal
lengau_sync(); snap_counts()
refused("SIXTH ADMISSION REFUSED at five live instances (fleet ceiling): nothing journaled, no RunInstances, no generation", admit(), "fleet ceiling", 8)

# 5. cumulative reservations: every unreconciled attempt is held at its worst case; the USD 3,000 cap binds exactly
leds = PA.ledgers(); b = PA.budget(leds)
exp_prod = sum(PA.charged(a) for r, l in leds.items() if PA.run_class(r) in PA.PROD_CLASSES for a in l["attempts"])
live_worst = sum(WORST for a in leds["prod-e2"]["attempts"] if a["state"] in PA.LIVE)
check("reservations: five live attempts are each reserved at worst case USD 27.9185 in the production total",
      abs(live_worst - 5 * WORST) < 1e-9 and abs(b["production_usd"] - exp_prod) < 1e-9 and abs(WORST - 27.9185) < 1e-3, (b, WORST))
latest = json.load(open(os.path.join(PA.INV_DIR, "latest.json")))
check("reservations: the sealed inventory states the same production total", abs(latest["usd"]["production_usd"] - b["production_usd"]) < 1e-6)
terminate(3)
check("reaper 3 reconciles attempt 3 (four live)", wait_for(lambda: reconciled(3), 120))
b = PA.budget(PA.ledgers())
base = json.load(open(os.path.join(FAWS, "budget_baseline.json")))
base.update(spent_usd=round(3000.0 - b["all_runs_usd"] - WORST + 0.5, 6), through_epoch=time.time()); wjson(os.path.join(FAWS, "budget_baseline.json"), base)
lengau_sync(); snap_counts()
refused("reservations: with the four live worst cases + reconciled charges + baseline, one more worst case would pass USD 3,000 -> refused",
        admit(), "cumulative cap", 8)
base.update(spent_usd=round(3000.0 - b["all_runs_usd"] - WORST - 0.5, 6)); wjson(os.path.join(FAWS, "budget_baseline.json"), base)
lengau_sync(); admitted("A8: admitted at USD 0.50 under the cap (the same reservations, one more worst case fits)", 8, admit())
base.update(spent_usd=500.0); wjson(os.path.join(FAWS, "budget_baseline.json"), base)

# 6. an admission INTERRUPTED inside RunInstances (killed), then recovered with the SAME request
terminate(4)
check("reaper 4 reconciles attempt 4 (four live)", wait_for(lambda: reconciled(4), 120))
fake(lambda s: s.update(run_modes=["hang"]))
lengau_sync()
p9 = admit(wait=False)
hung = wait_for(lambda: os.path.exists(os.path.join(FAKE, "run_instances_hanging")) or p9.poll() is not None, 90)
check("interrupt: A9 journaled its intent and is inside RunInstances (instance created, answer never returned)",
      hung and p9.poll() is None and att(9) is not None and att(9)["state"] == "intent", p9.communicate()[0][-800:] if p9.poll() is not None else "")
try:
    os.killpg(p9.pid, signal.SIGKILL)
except (PermissionError, ProcessLookupError):
    pass
p9.wait(timeout=30)
n_inst = fake(lambda s: len(s["instances"]))
check("interrupt: the killed admission left attempt 9 'intent', funded at worst case, locks released",
      att(9)["state"] == "intent" and abs(PA.charged(att(9)) - WORST) < 1e-9)
snap_counts()
refused("interrupt: a fresh admission refuses while attempt 9 is unresolved (recover it)", admit(), "unresolved")
snap_counts()
refused("interrupt: recovery on a receipt that does not bind the intent's generation re-issues nothing", admit("--recover"),
        "no re-issue")
lengau_sync()
rc, out = admit("--recover")
inst9 = [i for i, v in fake(lambda s: s["instances"]).items() if v["token"] == att(9)["client_token"]]
check("recovery: the SAME token is re-issued, the instance the lost call created is adopted, no second instance",
      rc == 0 and att(9)["state"] == "launched" and len(inst9) == 1 and att(9)["instance"] == inst9[0]
      and fake(lambda s: len(s["instances"])) == n_inst and wait_for(lambda: bool(reaper_pids(9)), 30), out[-500:])
rc, out = admit("--recover")
check("replay: a second recovery finds nothing to recover and changes nothing", rc != 0 and "nothing to recover" in out, out[-200:])

# 7. a reaper INTERRUPTED (killed) and restarted by hand; a replay of the reaper changes nothing
for pid in reaper_pids(5):
    os.kill(pid, signal.SIGKILL)
check("reaper interrupt: reaper 5 killed", wait_for(lambda: not reaper_pids(5), 20))
terminate(5); time.sleep(3)
check("reaper interrupt: with no reaper, attempt 5 stays 'launched' and reserved at worst case", att(5)["state"] == "launched" and abs(PA.charged(att(5)) - WORST) < 1e-9)
g5 = gen()
r = subprocess.run([sys.executable, os.path.join(FAWS, "bench_reaper.py"), "--run", "prod-e2", "--attempt", "5", "--poll-s", "1"], env=ENV,
                   capture_output=True, text=True, timeout=300)
check("reaper restart: the hand-started reaper reconciles attempt 5 and seals a new generation", r.returncode == 0 and att(5)["state"] == "reconciled" and gen() > g5,
      r.stdout[-300:] + r.stderr[-300:])
g5 = gen(); before5 = json.dumps(att(5), sort_keys=True)
r = subprocess.run([sys.executable, os.path.join(FAWS, "bench_reaper.py"), "--run", "prod-e2", "--attempt", "5", "--poll-s", "1"], env=ENV,
                   capture_output=True, text=True, timeout=120)
check("reaper replay: a second reaper for a reconciled attempt refuses and changes nothing", r.returncode != 0 and "not launched" in (r.stdout + r.stderr)
      and json.dumps(att(5), sort_keys=True) == before5 and gen() == g5, r.stderr[-200:])

# 8. drain: every remaining instance ends; five-way concurrent reconciliations
lengau_sync(); admitted("A10: admitted (five live again: 6, 7, 8, 9, 10)", 10, admit())
check("fleet: five live before the drain", PA.live_fleet(PA.ledgers()) == [f"prod-e2/{k}" for k in (10, 6, 7, 8, 9)] or
      sorted(PA.live_fleet(PA.ledgers())) == sorted(f"prod-e2/{k}" for k in (6, 7, 8, 9, 10)), PA.live_fleet(PA.ledgers()))
gd = gen()
terminate(6, 7, 8, 9, 10)
check("drain: FIVE reapers reconcile concurrently on the one prod-e2 ledger", wait_for(lambda: all(reconciled(k) for k in (6, 7, 8, 9, 10)), 180),
      [(a["attempt"], a["state"]) for a in led()])
check("drain: every reaper process has exited", wait_for(lambda: not reaper_pids(), 60), reaper_pids())
final = led()
check("drain: the five concurrent reconciliations sealed five distinct new generations", gen() >= gd + 5, (gd, gen()))

# 9. the invariants over the whole run
alls = [(r, a) for r, l in PA.ledgers().items() for a in l["attempts"]]
seqs = [a["sequence"] for _, a in alls]
check("sequences: globally unique across every run and epoch", len(seqs) == len(set(seqs)), sorted(seqs))
prod = sorted(final, key=lambda a: a["attempt"])
check("sequences: prod-e2 sequences strictly increase in admission order; the authority's next sequence is past them all",
      [a["sequence"] for a in prod] == sorted(a["sequence"] for a in prod) and len({a["sequence"] for a in prod}) == len(prod)
      and PA.state()["next_sequence"] == max(seqs) + 1, ([a["sequence"] for a in prod], PA.state()))
check("admissions/reconciliations: 10 admitted, 10 reconciled, each with a terminal record and its own fake instance",
      len(prod) == 10 and all(a["state"] == "reconciled" and a.get("terminal") and a.get("instance") == iid_of(a["attempt"]) for a in prod))
works = [tuple(map(tuple, a["coordinates"])) for a in prod] + [tuple(map(tuple, PANEL["work"]))]
flat = [c for w in works for c in w]
check("ownership: no coordinate was allocated twice (ten production batches and the E2Q1 panel are pairwise disjoint)", len(flat) == len(set(flat)))
check("ownership: every allocated coordinate is an epoch-2 owned coordinate", all(RP.blocked(PART, *c) for c in flat))
cur, changed = archives()
gens = sorted(cur)
check("generations: every sealed archive is unchanged since first seen, strictly increasing, its own generation, latest = newest",
      not changed and all(json.load(open(os.path.join(PA.INV_DIR, f"inventory_g{g}.json")))["generation"] == g for g in gens)
      and json.load(open(os.path.join(PA.INV_DIR, "latest.json")))["generation"] == gens[-1] == gen(), (changed, gens[-5:], gen()))
lengau_sync()
inst = [(json.loads(l)["generation"], json.loads(l)["sha256"]) for l in open(ES.paths(ROOT)["installed"])]
check("generations: the Lengau installs never went back, and a repeated generation was the same sealed bytes (idempotent)",
      [g for g, _ in inst] == sorted(g for g, _ in inst) and all(h == dict(inst)[g] for g, h in inst) and inst[-1][0] == gens[-1], inst)
old = json.load(open(os.path.join(PA.INV_DIR, f"inventory_g{gens[-3]}.json")))
_, why = ES.install_inventory(ROOT, old, IDENT)
check("generations: the real installer refuses an older generation (out-of-order delivery)", why and "older" in why[0], why)
b = PA.budget(PA.ledgers())
check("reservations: once every attempt is reconciled, the production total is the observed charges only",
      abs(b["production_usd"] - sum(PA.charged(a) for r, a in alls if PA.run_class(r) in PA.PROD_CLASSES)) < 1e-9
      and all(abs(PA.charged(a) - WORST) > 1 for a in prod))
runi = [c for c in aws_calls("run-instances") if "result" in c]
check("dispatch: 11 RunInstances calls in all (10 admissions + the one recovery re-issue), never under a refusal", len(runi) == 11, len(runi))
check("guard: every aws call went to the fake (and only modelled calls were made)",
      all([x for i, x in enumerate(c["args"]) if x not in ("--profile", "--region") and c["args"][i - 1] not in ("--profile", "--region")][0]
          in ("s3api", "ssm", "s3", "ec2") for c in aws_calls()) and not [l for l in open(os.path.join(FAKE, "aws_calls.jsonl")) if '"unmodelled' in l])
for pid in reaper_pids():
    os.kill(pid, signal.SIGKILL)
left = subprocess.run(["pgrep", "-f", FT1], capture_output=True, text=True).stdout.split()
check("cleanup: no process of the fake tree remains", not left, left)
print(f"\nR6' counts: {len(SEQ)} fresh admissions + 1 recovered (A9); {len(REFUSALS)} refused admissions/recoveries; prod-e2 attempts {len(prod)}; reconciled "
      f"{sum(1 for a in prod if a['state'] == 'reconciled')}; sealed generations {len(gens)}; RunInstances {len(runi)}")
print(f"{n[0] - len(fails)} passed, {len(fails)} failed")
if not fails:
    shutil.rmtree(TMP, ignore_errors=True)
else:
    print(f"(fixture tree kept for inspection: {TMP})")
sys.exit(1 if fails else 0)
