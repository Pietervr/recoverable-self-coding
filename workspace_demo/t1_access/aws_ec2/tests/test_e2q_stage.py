"""Tests of the E2Q bundle collection / verification / staging procedure (aws_ec2/e2q_stage.py and
e2q_stage_verify.py). CANDIDATE, synthetic only: no AWS, no ssh/scp, no Lengau, no network.

A synthetic Mac tree (ledger, plan, authority state, sealed inventory, panel, pinned data files, controls, manifest), a
local directory standing in for the S3 prefix, and a local directory standing in for Lengau's /mnt/lustre/.../t1_toolchain
(controller clone with the pinned qualification inputs, an installed inventory, a stand-in qualifier, a t1py that execs
python3). The FakeTransport runs every "remote" shell command the tool builds through `bash -c` unchanged, with the
tool's REMOTE_T pointed at that directory; uploads/downloads are copies; the S3 listing/sync read the local prefix. PATH
for those shells holds aws/ssh/scp guards that fail and log if anything ever tries the real tools. Synthetic bundle
members carry no scientific payload (records are labelled SYNTHETIC placeholders).

    python3 aws_ec2/tests/test_e2q_stage.py         (from workspace_demo/t1_access)"""
import ast, copy, hashlib, json, os, re, shutil, stat, subprocess, sys, tempfile, time, types

TESTS = os.path.dirname(os.path.abspath(__file__)); HERE = os.path.dirname(TESTS); T1REAL = os.path.dirname(HERE); CHPC = os.path.join(T1REAL, "chpc")
sys.path.insert(0, HERE)
import e2q_stage as S, e2q_stage_verify as V

fails, n = [], [0]


def check(name, cond, extra=""):
    n[0] += 1
    print(("ok   " if cond else "FAIL ") + name + (f"  [{str(extra)[:300]}]" if extra and not cond else ""), flush=True)
    if not cond:
        fails.append(name)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def wjson(p, obj, nl=False):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True); f.write("\n" if nl else "")
    return p


def wtext(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(s); return p


def tree_state(root):
    """{rel: (sha256, mtime_ns, mode)} - to prove a tree was never touched."""
    out = {}
    for d, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(d, f); st = os.lstat(p)
            out[os.path.relpath(p, root)] = (sha(p), st.st_mtime_ns, st.st_mode)
    return out


TMP = os.path.realpath(tempfile.mkdtemp(prefix="e2s_"))
GUARD = os.path.join(TMP, "guard_bin"); os.makedirs(GUARD)
GUARD_LOG = os.path.join(TMP, "guard.log")
for tool in ("aws", "ssh", "scp"):                          # any real-tool call inside a test shell fails loudly
    p = wtext(os.path.join(GUARD, tool), f"#!/bin/bash\necho \"{tool} $*\" >> {GUARD_LOG}\nexit 99\n"); os.chmod(p, 0o755)

# ---- the synthetic Mac tree ----------------------------------------------------------------------------------------------------
MAC = os.path.join(TMP, "mac", "workspace_demo", "t1_access"); AWS = os.path.join(MAC, "aws_ec2")
REM = os.path.join(TMP, "lustre", "t1_toolchain")
S3 = os.path.join(TMP, "s3")
S.T1, S.REMOTE_T = MAC, REM
L = S.layout()
WORK = [[24, i] for i in range(11, 63)]
DUPS = [[24, i] for i in range(0, 11)] + [[25, i] for i in range(0, 9)]
SENT = [[3, 0], [4, 1], [5, 2], [6, 3]]
DATA = {}
for rel in S.DATA_PINS:
    if rel == S.PANEL:
        continue
    DATA[rel] = wjson(os.path.join(MAC, rel), {"synthetic": rel})
wjson(os.path.join(MAC, S.PANEL), {"schema": "row19-ec2-e2q-panel-1", "work": WORK, "duplicates": DUPS, "synthetic": True})
S.DATA_PINS = {rel: sha(os.path.join(MAC, rel)) for rel in S.DATA_PINS}
QUAL_STANDIN = r'''"""STAND-IN qualifier for test_e2q_stage.py only (NOT the reviewed qualifier): same command line, writes a schema-3
shaped certificate binding the files it was given. Mode from <ctl>/chpc/.standin_mode."""
import argparse, hashlib, json, os, sys, time
def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()
a = sys.argv[1:]
assert a[0] == "e2", a
ap = argparse.ArgumentParser()
for k in ("--manifest", "--partition", "--authority", "--key", "--bundle", "--opmanifest", "--prod-opmanifest", "--panel", "--funding", "--sandbox", "--out"):
    ap.add_argument(k, required=True)
ap.add_argument("--snapshot", required=True)
x = ap.parse_args(a[1:])
here = os.path.dirname(os.path.abspath(__file__))
mode = open(os.path.join(here, ".standin_mode")).read().strip()
json.dump(sys.argv, open(os.path.join(here, ".standin_argv.json"), "w"))
os.makedirs(x.sandbox)
if mode == "crash":
    sys.exit(1)
if mode == "mutate":
    open(os.path.join(x.bundle, "env", "plan.json"), "a").write(" ")
inv = json.load(open(x.authority)); e = inv["attempts"][x.key]
outcome = {"release": "RELEASE", "no_release": "NO_RELEASE", "mutate": "RELEASE", "wrong_bind": "RELEASE", "lie": "RELEASE"}[mode]
cert = dict(schema="row19-ec2-qualification-certificate-3", epoch=2, outcome=outcome, problems=[] if outcome == "RELEASE" else ["synthetic"],
            attempt=dict(key=x.key, attempt_id=e["attempt_id"], sequence=e["sequence"], plan_sha256=e["plan_sha256"]),
            bound=dict(bundle_sha256=sha(os.path.join(x.bundle, "BUNDLE_SHA256SUMS")) if mode != "wrong_bind" else "0" * 64,
                       plan_sha256=sha(os.path.join(x.bundle, "env", "plan.json")), claims_snapshot_sha256=sha(x.snapshot),
                       panel_sha256=sha(x.panel), partition_sha256=sha(x.partition), funding_sha256=sha(x.funding),
                       manifest_sha256=sha(x.manifest), opmanifests=dict(qualified=sha(x.opmanifest), production=sha(x.prod_opmanifest))),
            at=time.time(), synthetic="STAND-IN")
json.dump(cert, open(x.out, "w"))
sys.exit(3 if mode == "lie" else (0 if outcome == "RELEASE" else 3))
'''
CODE_BYTES = {rel: f"# synthetic stand-in bytes of {rel}\n" for rel in S.CODE}
CODE_BYTES["chpc/row19_ec2_qualify.py"] = QUAL_STANDIN
CODE_SHA = {rel: hashlib.sha256(b.encode()).hexdigest() for rel, b in CODE_BYTES.items()}
ctl = {"versions": [{"version": 17, "files": {r: h for r, h in CODE_SHA.items() if r not in S.MANIFEST_CODE},
                     "partition": {"path": S.PARTITION, "sha256": S.DATA_PINS[S.PARTITION]}}]}
wjson(os.path.join(MAC, "chpc", "row19_screen_controls.json"), ctl)
wjson(os.path.join(MAC, "chpc", "row19_screen_manifest.json"), {"code": {"files": {r: CODE_SHA[r] for r in S.MANIFEST_CODE}}, "synthetic": True})
S.ADOPTED_CONTROLS_SHA = sha(os.path.join(MAC, "chpc", "row19_screen_controls.json"))
S.PROD_SHA = sha(os.path.join(MAC, "chpc", "row19_screen_manifest.json"))


def plan_doc(run, n, contract, seq, work=WORK, sent=SENT):
    slots = [dict(slot=k, rep=r, indices=[i], role=role) for k, (role, (r, i)) in
             enumerate([("work", c) for c in work] + [("qual_lengau", c) for c in DUPS] + [("sentinel", c) for c in sent])]
    return dict(job=n, attempt_id=f"ec2-{run}-a{n}", sequence=seq, epoch=2, contract=contract, partition_sha256=S.DATA_PINS[S.PARTITION],
                opmanifest_sha256=S.DATA_PINS[S.OPMANIFEST[contract]], activation_sha256="a" * 64, instance={}, lifetime_s=79200, slots=slots)


def ledger_attempt(run, n, contract, seq, **kw):
    d = os.path.join(AWS, "runs", run); os.makedirs(d, exist_ok=True)
    pp = wjson(os.path.join(d, f"plan_attempt{n}.json"), plan_doc(run, n, contract, seq))
    a = dict(attempt=n, sequence=seq, attempt_id=f"ec2-{run}-a{n}", contract=contract, state="reconciled", ingestion="pending",
             plan=pp, plan_sha256=sha(pp), coordinates=WORK, duplicates=DUPS, sentinels=SENT, instance="i-synthetic",
             results=f"s3://{S.BUCKET}/{S.RESULTS_PREFIX}/{run}/attempt_{n}/", lifetime_s=79200)
    a.update(kw)
    return a


GEN = [10]


def seal_inventory(ledgers, at=None):
    """A sealed-inventory stand-in with the fields the tool reads; generation advanced, state file kept equal."""
    GEN[0] += 1
    atts = {}
    for run, atts_ in ledgers.items():
        for a in atts_:
            atts[f"{run}/{a['attempt']}"] = dict(attempt_id=a["attempt_id"], sequence=a["sequence"], plan_sha256=a["plan_sha256"], state=a["state"],
                                                 ingestion=a["ingestion"], contract=a["contract"], coordinates=a["coordinates"],
                                                 duplicates=a["duplicates"], sentinels=a["sentinels"], disposition_requested=bool(a.get("disposition_request")),
                                                 **{"class": "qualification"})
    inv = dict(schema="t1-ec2-authority-inventory-synthetic", generation=GEN[0], at=time.time() if at is None else at, attempts=atts)
    inv["sha256"] = hashlib.sha256(json.dumps(inv, sort_keys=True).encode()).hexdigest()
    wjson(os.path.join(AWS, "runs", "inventory", "latest.json"), inv)
    wjson(os.path.join(AWS, "runs", ".authority_state.json"), {"generation": GEN[0], "next_sequence": 99})
    return inv


def install(inv=None):
    inv = inv or json.load(open(os.path.join(AWS, "runs", "inventory", "latest.json")))
    wjson(os.path.join(L["root"], "ec2", "authority", "inventory.json"), inv)


LEDGERS = {}


def set_ledgers(**runs):
    LEDGERS.clear(); LEDGERS.update(runs)
    for run, atts in runs.items():
        wjson(os.path.join(AWS, "runs", run, "attempts.json"), {"run": run, "attempts": atts})
    inv = seal_inventory(runs); install(inv); return inv


# ---- the synthetic producer bundle on the fake S3 prefix --------------------------------------------------------------------

def make_bundle(dest, plan_path, aid, outcomes=None):
    plan = json.load(open(plan_path)); slots = plan["slots"]
    shutil.copy(plan_path, wtext(os.path.join(dest, "env", "plan.json"), ""))
    oc = outcomes or {f"w_slot{s['slot']}": 0 for s in slots}
    wjson(os.path.join(dest, "env", "outcomes.json"), dict(at=1.0, declared=len(slots), outcomes=oc, unresolved_after_kill=[]))
    wjson(os.path.join(dest, "env", "attest_B.json"), {"profile": "B_full", "synthetic": True})
    wtext(os.path.join(dest, "env", "censored.txt"), "")
    wtext(os.path.join(dest, "env", "declared.txt"), "".join(f"w_slot{s['slot']}\n" for s in slots))
    for f in ("SHA256SUMS", "manifest_prod.json", "attest.py", "profile_B.txt", "job_start.log", "window.json", "lscpu.txt", "free.txt",
              "uname.txt", "npy_mask_check.txt", "slots.txt", "unresolved.txt"):
        wtext(os.path.join(dest, "env", f), f"synthetic {f}\n")
    wtext(os.path.join(dest, "env", "occupancy.txt"), "".join(f"{1000 + 60 * k} 0 1.0 1.0 1.0\n" for k in range(12)))
    wtext(os.path.join(dest, "env", "memory.txt"), "".join(f"{1000 + 60 * k} 201326592 50331648 1000\n" for k in range(12)))
    for s in slots:
        r, i, k = s["rep"], s["indices"][0], s["slot"]
        wtext(os.path.join(dest, "root", "records", f"rep{r}", f"idx{i}.json"), '{"SYNTHETIC": "placeholder, no scientific payload"}\n')
        wtext(os.path.join(dest, "root", "timing", f"rep{r}", f"t_{i}.json"), '{"SYNTHETIC": 1}\n')
        wjson(os.path.join(dest, "root", "status", f"job{aid}.slot{k}.json"), {"SYNTHETIC": True, "slot": k})
        wtext(os.path.join(dest, "logs", f"w_slot{k}.log"), "synthetic log\n")
        wtext(os.path.join(dest, "exits", f"w_slot{k}.code"), "0\n")
    for r in sorted({s["rep"] for s in slots}):
        wjson(os.path.join(dest, "root", f"task_{r}.json"), {"SYNTHETIC": r})
    seal_sums(dest)
    wjson(os.path.join(dest, "env", "upload_verify.json"), {"transfer_verified": True, "tries": 1})
    wtext(os.path.join(dest, "env", "userdata.log"), "synthetic userdata log\n")


def seal_sums(dest):
    rels = []
    for sub in ("root", "env"):
        for d, _, fs in os.walk(os.path.join(dest, sub)):
            for f in fs:
                rel = os.path.relpath(os.path.join(d, f), dest)
                if rel not in V.MUTABLE and not f.startswith("BUNDLE_SHA256SUMS"):
                    rels.append(rel)
    rels.sort(key=lambda s: s.encode())
    wtext(os.path.join(dest, "BUNDLE_SHA256SUMS"), "".join(f"{sha(os.path.join(dest, r))}  {r}\n" for r in rels))


def prefix_dir(run, n):
    return os.path.join(S3, S.BUCKET, S.RESULTS_PREFIX, run, f"attempt_{n}")


# ---- the synthetic Lengau side -----------------------------------------------------------------------------------------------
os.makedirs(REM)
p = wtext(os.path.join(REM, "t1py"), "#!/bin/bash\nexec python3 \"$@\"\n"); os.chmod(p, 0o755)
CTLD = L["ctl"]
for rel in list(S.DATA_PINS) + ["chpc/row19_screen_controls.json", "chpc/row19_screen_manifest.json"]:
    os.makedirs(os.path.dirname(os.path.join(CTLD, rel)), exist_ok=True); shutil.copy(os.path.join(MAC, rel), os.path.join(CTLD, rel))
for rel, b in CODE_BYTES.items():
    wtext(os.path.join(CTLD, rel), b)
MODE = os.path.join(CTLD, "chpc", ".standin_mode")


def mode(m):
    open(MODE, "w").write(m)


class Fake(S.Transport):
    """Local stand-ins for S3 and the two Lengau hosts; every remote shell string runs unchanged through bash."""
    def __init__(self):
        self.calls, self.hooks = [], {}

    def hook(self, name, *a):
        f = self.hooks.get(name)
        if f:
            f(*a)

    def s3_list(self, url):
        self.calls.append(("s3_list", url))
        d = os.path.join(S3, url[len("s3://"):])
        out = {}
        for dd, _, fs in os.walk(d):
            for f in fs:
                p = os.path.join(dd, f); out[os.path.relpath(p, d)] = os.path.getsize(p)
        return out

    def s3_sync(self, url, dest):
        self.calls.append(("s3_sync", url))
        os.makedirs(dest)
        src = os.path.join(S3, url[len("s3://"):])
        for dd, _, fs in os.walk(src):
            for f in fs:
                p = os.path.join(dd, f); q = os.path.join(dest, os.path.relpath(p, src)); os.makedirs(os.path.dirname(q), exist_ok=True)
                shutil.copyfile(p, q)
        self.hook("after_sync", dest)

    def run(self, host, cmd, timeout=7200):
        self.calls.append(("run", host, cmd))
        self.hook("before_run", host, cmd)
        env = dict(os.environ, PATH=GUARD + os.pathsep + os.environ["PATH"])
        p = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=timeout, env=env)
        return p.returncode, p.stdout, p.stderr

    def push_tree(self, host, local_parent, name, remote_dir):
        self.calls.append(("push_tree", host, remote_dir))
        rc, _, err = self.run(host, f"mkdir -p -- {S.shlex.quote(os.path.dirname(remote_dir))} && mkdir -- {S.shlex.quote(remote_dir)}")
        if rc:
            raise S.TransportError(f"the remote staging directory is not new: {err.strip()[:200]}")
        tar = subprocess.Popen(["tar", "-C", local_parent, "-cf", "-", name], stdout=subprocess.PIPE)
        p = subprocess.run(["bash", "-c", f"tar -xf - -C {S.shlex.quote(remote_dir)}"], stdin=tar.stdout, capture_output=True)
        tar.stdout.close()
        if tar.wait() != 0 or p.returncode != 0:
            raise S.TransportError("the bundle transfer failed")
        self.hook("after_push", remote_dir)

    def put(self, host, src, dst):
        self.calls.append(("put", host, dst)); shutil.copyfile(src, dst); self.hook("after_put", dst)

    def get(self, host, src, dst):
        self.calls.append(("get", host, src))
        if not os.path.exists(src):
            raise S.TransportError(f"scp from {host} failed: no {src}")
        shutil.copyfile(src, dst + ".part"); os.replace(dst + ".part", dst)


LOG = []
def log(m):
    LOG.append(m)


STAMP = [0]
def stamp():
    STAMP[0] += 1; return f"20261020T0000{STAMP[0]:02d}Z"


def do_stage(tr, run="qual-E2Q1", n=1, st=None):
    try:
        sd, rdir, rec = S.stage(tr, run, n, log=log, stamp=st or stamp())
        return "OK", (sd, rdir, rec)
    except S.Refused as e:
        return "REFUSED", str(e)
    except S.TransportError as e:
        return "TRANSPORT", str(e)


def do_qualify(tr, st, run="qual-E2Q1", n=1, now=None):
    try:
        return "RC", S.qualify(tr, run, n, st, log=log, now=now)
    except S.Refused as e:
        return "REFUSED", str(e)
    except S.TransportError as e:
        return "TRANSPORT", str(e)


def claim_path(run="qual-E2Q1", n=1):
    return os.path.join(L["stage_root"], run, f"attempt_{n}", "EVALUATION_CLAIM")


# ============================================================================================================================
# 0. the real constants are the reviewed ones (read-only hashes of the committed files; nothing imported from the live tree)
REAL_FINAL = os.path.join(CHPC, "e2_final")
real_map = {"chpc/row19_partition_e2.json": "row19_partition_e2.json", "chpc/claims_snapshot_e2.json": "claims_snapshot_e2.json",
            "aws_ec2/prod/panel_e2q_e2.json": "panel_e2q_e2.json", "aws_ec2/prod/manifest_e2q1_e2.json": "manifest_e2q1_e2.json",
            "aws_ec2/prod/manifest_e2q2_e2.json": "manifest_e2q2_e2.json", "aws_ec2/prod/manifest_production_e2.json": "manifest_production_e2.json",
            "aws_ec2/e2_funding.json": "e2_funding.json"}
import importlib.util
_spec = importlib.util.spec_from_file_location("e2q_stage_committed", os.path.join(HERE, "e2q_stage.py"))
REAL = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(REAL)      # a second copy with its committed constants
E2Q3_MAN = "aws_ec2/prod/manifest_e2q3_e2.json"           # REVISION 2: promoted with controls v19 (its data row), not from e2_final
check("real: every DATA_PIN but the E2Q3 manifest is the sha256 of the reviewed chpc/e2_final file it promotes from",
      all(REAL.DATA_PINS[k] == sha(os.path.join(REAL_FINAL, f)) for k, f in real_map.items())
      and sorted(REAL.DATA_PINS) == sorted(list(real_map) + [E2Q3_MAN]))
pm = json.load(open(os.path.join(CHPC, "candidate_v17", "v17_promotion_map.json")))
check("real: DATA_PINS agree with the v17 promotion map rows (E2Q3's manifest: not a v17 path)",
      all(any(r["promoted"] == k and r["sha256"] == h for r in pm["rows"]) for k, h in REAL.DATA_PINS.items() if k != E2Q3_MAN)
      and not any(r["promoted"] == E2Q3_MAN for r in pm["rows"]))
pm18 = json.load(open(os.path.join(CHPC, "candidate_v18_nodefail", "v18_promotion_map.json")))
check("real: the v18 promotion map promotes none of the DATA_PINS paths (the v17 data pins stand)",
      not any(r["promoted"] in REAL.DATA_PINS for r in pm18["rows"]))
pm19 = json.load(open(os.path.join(CHPC, "candidate_v19_oploss", "v19_promotion_map.json")))
check("real: the E2Q3 manifest pin is the v19 map's NEW data row (previous none) and that row's source bytes; v19 promotes no other DATA_PINS path",
      [(r["sha256"], r["previous_sha256"], r["group"]) for r in pm19["rows"] if r["promoted"] == E2Q3_MAN] == [(REAL.DATA_PINS[E2Q3_MAN], None, "data")]
      and sha(os.path.join(CHPC, "candidate_v19_oploss", "manifest_e2q3_e2.json")) == REAL.DATA_PINS[E2Q3_MAN]
      and not any(r["promoted"] in REAL.DATA_PINS for r in pm19["rows"] if r["promoted"] != E2Q3_MAN))
check("real: ADOPTED_CONTROLS_SHA is the v19 candidate controls, the v19 map's controls row, on the v18 base 452b82df",
      REAL.ADOPTED_CONTROLS_SHA == sha(os.path.join(CHPC, "candidate_v19_oploss", "row19_screen_controls.json"))
      and any(r["promoted"] == "chpc/row19_screen_controls.json" and r["sha256"] == REAL.ADOPTED_CONTROLS_SHA
              and r["previous_sha256"] == "452b82df0d7184cbe7c1390d5d43787501990d380c4ca275d1db70adc131ba2b"
              == sha(os.path.join(CHPC, "candidate_v18_nodefail", "row19_screen_controls.json")) for r in pm19["rows"]))
check("real: RUNS / OPMANIFEST carry E2Q1, E2Q2 and E2Q3, each its own run and manifest; the verifier accepts exactly those contracts",
      REAL.RUNS == {c: f"qual-{c}" for c in ("E2Q1", "E2Q2", "E2Q3")} and REAL.OPMANIFEST == {c: f"aws_ec2/prod/manifest_{c.lower()}_e2.json" for c in REAL.RUNS}
      and V.E2Q_CONTRACTS == ("E2Q1", "E2Q2", "E2Q3"))
check("real: PROD_SHA is the production manifest's bytes", REAL.PROD_SHA == sha(os.path.join(CHPC, "row19_screen_manifest.json")))
eq_src = open(os.path.join(CHPC, "candidate_e2q", "row19_ec2_e2qual.py")).read()
eq_code = ast.literal_eval(re.search(r"CODE = sorted\((\[.*?\])\)", eq_src, re.S).group(1))
check("real: CODE is row19_ec2_e2qual.CODE (the certificate's code set)", REAL.CODE == sorted(eq_code))
v17 = json.load(open(os.path.join(CHPC, "candidate_v17", "row19_screen_controls.json")))["versions"][-1]["files"]
v18c = json.load(open(os.path.join(CHPC, "candidate_v18_nodefail", "row19_screen_controls.json")))
v18 = v18c["versions"][-1]["files"]
v19c = json.load(open(os.path.join(CHPC, "candidate_v19_oploss", "row19_screen_controls.json")))
v19 = v19c["versions"][-1]["files"]
mcode = json.load(open(os.path.join(CHPC, "row19_screen_manifest.json")))["code"]["files"]
check("real: the v18 controls' latest version is version 18",
      v18c["versions"][-1].get("version") == 18)
v19_moved = sorted(r for r in REAL.CODE if r not in REAL.MANIFEST_CODE and v19.get(r) != v18.get(r))
check("real: v19 (the controls e2q_stage now pins) moves exactly three qualification code pins - the EC2 state, the E2Q module and the "
      "ingestion (E2Q3) - each to the candidate bytes; the qualifier and every other code pin stay v18's",
      v19c["versions"][-1].get("version") == 19
      and v19_moved == ["chpc/row19_ec2_e2qual.py", "chpc/row19_ec2_ingest.py", "chpc/row19_ec2_state.py"]
      and all(v19[r] == sha(os.path.join(CHPC, "candidate_v19_oploss", os.path.basename(r))) for r in v19_moved)
      and v19["chpc/row19_ec2_qualify.py"] == v18["chpc/row19_ec2_qualify.py"], v19_moved)
check("real: every code-set file has a pin in v18's latest version or the manifest's code pins",
      all((mcode.get(r) if r in REAL.MANIFEST_CODE else v18.get(r)) for r in REAL.CODE))
check("real: v18 keeps every qualification code pin of v17 unchanged (the v17 -> v18 move is administrative for E2Q)",
      all(v18.get(r) == v17.get(r) for r in REAL.CODE if r not in REAL.MANIFEST_CODE))
check("real: the v18 pin of the qualifier is the re-reviewed REVISION 6 bytes (1d8eee78) of chpc/candidate_e2q",
      v18["chpc/row19_ec2_qualify.py"] == sha(os.path.join(CHPC, "candidate_e2q", "row19_ec2_qualify.py")) == "1d8eee78fc9427cd9e4cebe09deac37cf4284f0b8a86714dcc9d80cde63cbb29")
ig_src = open(os.path.join(CHPC, "candidate_e2", "row19_ec2_ingest.py")).read()
check("real: the verifier's MUTABLE set is the ingestion's (REVISION 8)", tuple(V.MUTABLE) == ast.literal_eval(re.search(r"^MUTABLE = (\(.*?\))", ig_src, re.M).group(1)))
qsrc = open(os.path.join(CHPC, "candidate_e2q", "row19_ec2_qualify.py")).read()
m = re.search(r"def main_e2\(argv=None\):(.*?)a = ap\.parse_args", qsrc, re.S).group(1)
req = set(re.findall(r'"(--[a-z-]+)"', m))
cmd = S.qualify_cmd(S.layout("/T"), "qual-E2Q1/1", "E2Q1", "/T/ec2_stage/qual-E2Q1/attempt_1/X")
flags = [x for x in cmd if x.startswith("--")]
check("real: the command passes every flag the reviewed qualifier's `e2` parser defines (required ones and --snapshot), once each",
      set(flags) == req and len(flags) == len(set(flags)), (sorted(req), flags))
doc = open(os.path.join(CHPC, "candidate_e2q", "DESIGN_e2q.md")).read()
step6 = re.search(r"t1py chpc/row19_ec2_qualify\.py e2 (.*?)--out <cert_e2q1\.json>", doc, re.S).group(1)
docflags = dict(re.findall(r"(--[a-z-]+) (\S+)", step6.replace("\\\n", " ")))
cmdmap = {cmd[i]: cmd[i + 1] for i in range(len(cmd) - 1) if cmd[i].startswith("--")}
same = all(cmdmap.get(k) == v for k, v in docflags.items() if not v.startswith("<"))
check("real: the command equals DESIGN_e2q.md s.7 step 6 on every fixed argument, incl. --snapshot chpc/claims_snapshot_e2.json",
      same and cmdmap["--snapshot"] == "chpc/claims_snapshot_e2.json" and cmd[:3] == ["/T/t1py", "chpc/row19_ec2_qualify.py", "e2"], (docflags, cmdmap))
RL = REAL.layout()
check("real: the staging root is fixed and contained (not inside/over the controller clone, scientific clone, root or campaign)",
      RL["stage_root"] == "/mnt/lustre/users/pvanrooyen/t1_toolchain/ec2_stage" and REAL.containment_problem(RL) == ""
      and S.containment_problem(dict(RL, stage_root=RL["ctl"] + "/x")) != "" and S.containment_problem(dict(RL, stage_root=RL["T"])) != "")
check("real: transfer through chpc-scp, controller commands through lengau", (REAL.TRANSFER_HOST, REAL.LOGIN_HOST) == ("chpc-scp", "lengau"))

# the REAL transport's argv, with subprocess replaced by a recorder (nothing is executed)
rec = []
class _P:
    returncode, stdout, stderr = 0, json.dumps({"Contents": [{"Key": "results/t1_access/aws_bench/qual-E2Q1/attempt_1/a", "Size": 3}]}), ""
real_run = S.subprocess.run
S.subprocess = types.SimpleNamespace(run=lambda argv, **kw: rec.append(argv) or _P(), Popen=None, TimeoutExpired=subprocess.TimeoutExpired, PIPE=subprocess.PIPE)
tr0 = S.Transport()
lst = tr0.s3_list(f"s3://{S.BUCKET}/{S.RESULTS_PREFIX}/qual-E2Q1/attempt_1/")
tr0.run("chpc-scp", "true"); tr0.put("chpc-scp", "/a", "/b")
S.subprocess = subprocess
check("real transport: the S3 listing uses the read profile in us-west-2 on the exact prefix, and strips it",
      rec[0][:5] == ["aws", "--profile", "xtenure-read", "--region", "us-west-2"] and "list-objects-v2" in rec[0]
      and rec[0][rec[0].index("--prefix") + 1] == "results/t1_access/aws_bench/qual-E2Q1/attempt_1/" and lst == {"a": 3}, rec[:1])
check("real transport: ssh with ControlPath=none, BatchMode and the named host", rec[1][:7] == ["ssh", "-o", "ControlPath=none", "-o", "ConnectTimeout=30", "-o", "BatchMode=yes"] and rec[1][7] == "chpc-scp")
check("real transport: scp with the same options to host:path", rec[2][:8] == ["scp", "-o", "ControlPath=none", "-o", "ConnectTimeout=30", "-o", "BatchMode=yes", "-q"]
      and rec[2][-1] == "chpc-scp:/b", rec[2:3])

# ============================================================================================================================
# 1. the clean path
A1 = ledger_attempt("qual-E2Q1", 1, "E2Q1", 60)
set_ledgers(**{"qual-E2Q1": [A1]})
make_bundle(prefix_dir("qual-E2Q1", 1), A1["plan"], A1["attempt_id"])
S3_BEFORE = tree_state(S3)
tr = Fake(); mode("release")
r = do_stage(tr)
check("stage: a clean synthetic bundle is collected, verified, staged and re-verified on Lengau", r[0] == "OK", r)
sd, rdir, rec1 = r[1] if r[0] == "OK" else (None, None, None)
check("stage: the remote directory is <REMOTE_T>/ec2_stage/qual-E2Q1/attempt_1/<stamp> with the bundle and the shipped tools BESIDE it",
      rdir == f"{REM}/ec2_stage/qual-E2Q1/attempt_1/{rec1['stamp']}" and os.path.isdir(rdir + "/bundle")
      and os.path.exists(rdir + "/e2q_stage_verify.py") and not os.path.exists(rdir + "/bundle/e2q_stage_verify.py"))
check("stage: the Lengau copy's tree digest equals the Mac's and the producer's sealed list is carried unchanged",
      V.verify(rdir + "/bundle", rec1["expect"])["tree_sha256"] == rec1["bundle"]["tree_sha256"] == V.verify(prefix_dir("qual-E2Q1", 1), rec1["expect"])["tree_sha256"])
hosts = {(c[0], c[1]) for c in tr.calls if c[0] in ("push_tree", "put", "get")}
runs_ = [c for c in tr.calls if c[0] == "run"]
check("stage: every byte goes to Lengau through chpc-scp; every remote command runs on lengau except the push's mkdir",
      hosts == {("push_tree", "chpc-scp"), ("put", "chpc-scp")} and all(c[1] == "lengau" or c[2].startswith("mkdir -p") for c in runs_), (hosts, [c[1] for c in runs_]))
check("stage: the receipt binds identity, S3 listing, every member, inventory generation, pins and both tool digests",
      rec1["context"]["inventory"]["generation"] == GEN[0] and rec1["s3"]["objects"] == rec1["bundle"]["files"] == len(rec1["bundle"]["members"])
      and set(rec1["tools"]) == {"e2q_stage.py", "e2q_stage_verify.py"} and rec1["context"]["pins"]["chpc/row19_ec2_qualify.py"] == CODE_SHA["chpc/row19_ec2_qualify.py"])
check("stage: no evaluation claim exists after staging alone", not os.path.exists(claim_path()))
mtime_before = tree_state(rdir + "/bundle")
r = do_qualify(tr, rec1["stamp"])
check("qualify: RELEASE from the stand-in qualifier -> exit 0", r == ("RC", 0), (r, LOG[-3:]))
argv = json.load(open(os.path.join(CTLD, "chpc", ".standin_argv.json")))
check("qualify: the qualifier ran with exactly the reviewed command, incl. --snapshot chpc/claims_snapshot_e2.json",
      argv[1:] == S.qualify_cmd(L, "qual-E2Q1/1", "E2Q1", rdir)[2:] and argv[argv.index("--snapshot") + 1] == "chpc/claims_snapshot_e2.json", argv)
bind = json.load(open(os.path.join(sd, "binding.json")))
check("qualify: binding.json binds certificate, receipt, tree digest, pins, installed inventory and the exact command",
      bind["outcome"] == "RELEASE" and bind["certificate_sha256"] == sha(os.path.join(sd, bind["certificate"]))
      and bind["receipt_sha256"] == sha(os.path.join(sd, "receipt.json")) and bind["tree_sha256"] == rec1["bundle"]["tree_sha256"]
      and bind["installed_inventory"]["generation"] == GEN[0] and bind["command"][:3] == [L["t1py"], "chpc/row19_ec2_qualify.py", "e2"])
check("qualify: the claim names this stamp", open(claim_path()).read().strip() == rec1["stamp"])
check("never mutated: the S3 source, the Mac copy and the Lengau copy are byte-, mode- and mtime-identical after the run",
      tree_state(S3) == S3_BEFORE and tree_state(rdir + "/bundle") == mtime_before
      and V.verify(sd + "/bundle", rec1["expect"])["tree_sha256"] == rec1["bundle"]["tree_sha256"])
check("guard: no real aws/ssh/scp was ever invoked", not os.path.exists(GUARD_LOG))
r = do_qualify(tr, rec1["stamp"])
check("replay: qualifying the same stamp again is refused", r[0] == "REFUSED" and ("binding" in r[1] or "claimed" in r[1]), r)
r = do_stage(tr)
check("replay: staging the claimed attempt again is refused before anything is collected", r[0] == "REFUSED" and "already claimed" in r[1]
      and tr.calls[-1][0] == "run", r)

# ============================================================================================================================
# 2. a second world per case: attempts 2.. of qual-E2Q1 ledgers are not realistic (E2Q1 is ONE instance), so each case uses
#    a fresh synthetic attempt number of its own run; only the staging procedure is under test here.
CASE = [1]


def fresh(contract="E2Q1", **kw):
    CASE[0] += 1
    run = S.RUNS[contract]; nn = CASE[0]
    a = ledger_attempt(run, nn, contract, 100 + nn, **kw)
    set_ledgers(**{run: [a]})
    pd = prefix_dir(run, nn); shutil.rmtree(pd, ignore_errors=True)
    make_bundle(pd, a["plan"], a["attempt_id"])
    return run, nn, a, pd


def staged_refusal(name, mutate_s3=None, want="", contract="E2Q1", tr_hooks=None, kind="REFUSED", **kw):
    run, nn, a, pd = fresh(contract, **kw)
    if mutate_s3:
        mutate_s3(pd, a)
    t = Fake(); t.hooks.update(tr_hooks or {})
    before = tree_state(S3)
    r = do_stage(t, run, nn)
    check(name, r[0] == kind and want in r[1] and tree_state(S3) == before and not os.path.exists(claim_path(run, nn)), r)
    return r


def edit(rel, fn):
    def f(pd, a):
        p = os.path.join(pd, rel); fn(p)
    return f


# tamper at the source
staged_refusal("tamper: a sealed record changed at S3 -> refused (sealed sha256 differs)",
               edit("root/records/rep24/idx11.json", lambda p: open(p, "a").write(" ")), "differs from its sealed sha256")
staged_refusal("tamper: the plan replaced at S3 by another sequence's plan -> refused (not the attempt's plan bytes)",
               lambda pd, a: (wjson(os.path.join(pd, "env", "plan.json"), plan_doc("qual-E2Q1", 1, "E2Q1", 7)), seal_sums(pd)), "not the attempt's plan bytes")
# partial
staged_refusal("partial: a sealed member missing at S3 -> refused", lambda pd, a: os.remove(os.path.join(pd, "root", "status", f"job{a['attempt_id']}.slot5.json")),
               "PARTIAL: sealed member")
staged_refusal("partial: no BUNDLE_SHA256SUMS -> refused", lambda pd, a: os.remove(os.path.join(pd, "BUNDLE_SHA256SUMS")), "no BUNDLE_SHA256SUMS")
staged_refusal("partial: a truncated BUNDLE_SHA256SUMS (last line cut) -> refused",
               edit("BUNDLE_SHA256SUMS", lambda p: open(p, "w").write(open(p).read()[:-40])), "BUNDLE_SHA256SUMS")
staged_refusal("partial: the producer's transfer not verified -> refused",
               lambda pd, a: wjson(os.path.join(pd, "env", "upload_verify.json"), {"transfer_verified": False}), "transfer is not verified")
staged_refusal("partial: env/upload_verify.json absent -> refused", lambda pd, a: os.remove(os.path.join(pd, "env", "upload_verify.json")),
               "upload_verify.json missing")
staged_refusal("partial: the instance's BUNDLE_FAILED marker -> refused", lambda pd, a: wtext(os.path.join(pd, "env", "BUNDLE_FAILED"), "x"), "BUNDLE_FAILED")
staged_refusal("partial: the S3 sync drops an object -> refused (local copy is not the listing)",
               tr_hooks={"after_sync": lambda dest: os.remove(os.path.join(dest, "logs", "w_slot3.log"))}, want="not the S3 listing")
staged_refusal("partial: a short object after sync -> refused (size differs from the listing)",
               tr_hooks={"after_sync": lambda dest: open(os.path.join(dest, "env", "userdata.log"), "w").write("x")}, want="sizes differ")
# extra
staged_refusal("extra: an unlisted file under root/ -> refused", lambda pd, a: wtext(os.path.join(pd, "root", "records", "rep24", "idx99.json"), "{}"), "EXTRA member root/records")
staged_refusal("extra: a top-level stray file -> refused", lambda pd, a: wtext(os.path.join(pd, "notes.txt"), "x"), "EXTRA member notes.txt")
staged_refusal("extra: a log of an unplanned slot -> refused", lambda pd, a: wtext(os.path.join(pd, "logs", "w_slot99.log"), "x"), "EXTRA member logs/w_slot99.log")
staged_refusal("extra: a status of another attempt id -> refused",
               lambda pd, a: (wjson(os.path.join(pd, "root", "status", "jobec2-qual-E2Q1-a1.slot1.json"), {}), seal_sums(pd)), "not a planned worker status")
staged_refusal("extra: a mutable diagnostic sealed by an altered list -> refused",
               lambda pd, a: open(os.path.join(pd, "BUNDLE_SHA256SUMS"), "a").write(f"{sha(os.path.join(pd, 'env', 'userdata.log'))}  env/userdata.log\n"),
               "mutable diagnostic but is sealed")
staged_refusal("extra: the S3 sync adds an object not in the listing -> refused",
               tr_hooks={"after_sync": lambda dest: wtext(os.path.join(dest, "env", "stop_seen.txt"), "x")}, want="not the S3 listing")
# replay / identity
staged_refusal("replay: the E2Q2 bundle presented under an E2Q1 attempt -> refused (contract/opmanifest/plan)",
               lambda pd, a: (wjson(os.path.join(pd, "env", "plan.json"), plan_doc("qual-E2Q2", 1, "E2Q2", 101)), seal_sums(pd)), "not the attempt's plan bytes")
for name, kw, want in (("not reconciled", dict(state="launched"), "not a reconciled"), ("already ingested", dict(ingestion="ingested"), "not a reconciled"),
                       ("disposition requested", dict(disposition_request={"reason": "x"}), "disposition"),
                       ("another results prefix", dict(results="s3://other/x/"), "own prefix"),
                       ("another plan hash", dict(plan_sha256="0" * 64), "plan file"),
                       ("work not the panel's", dict(coordinates=WORK[:-1] + [[30, 1]]), "declared panel")):
    staged_refusal(f"identity: a ledger attempt {name} -> refused", want=want, **kw)
run, nn, a, pd = fresh()
inv = json.load(open(os.path.join(AWS, "runs", "inventory", "latest.json"))); inv["attempts"][f"{run}/{nn}"]["sequence"] = 1
wjson(os.path.join(AWS, "runs", "inventory", "latest.json"), inv)
t = Fake(); r = do_stage(t, run, nn)
check("identity: the sealed inventory carries the attempt differently -> refused before any S3 call", r[0] == "REFUSED" and "sealed inventory" in r[1]
      and not any(c[0].startswith("s3") for c in t.calls), r)
run, nn, a, pd = fresh()
wjson(os.path.join(AWS, "runs", ".authority_state.json"), {"generation": GEN[0] + 1})
r = do_stage(Fake(), run, nn)
check("identity: the sealed inventory is not the authority's current generation -> refused", r[0] == "REFUSED" and "current generation" in r[1], r)
run, nn, a, pd = fresh()
open(os.path.join(MAC, S.FUNDING), "a").write(" ")
r = do_stage(Fake(), run, nn)
check("identity: a Mac pinned input (funding) not its reviewed bytes -> refused", r[0] == "REFUSED" and "aws_ec2/e2_funding.json" in r[1], r)
shutil.copy(os.path.join(CTLD, S.FUNDING), os.path.join(MAC, S.FUNDING))
r = do_stage(Fake(), "qual-Q1", 4)
check("identity: an epoch-1 run is refused (only qual-E2Q1 / qual-E2Q2)", r[0] == "REFUSED" and "epoch-2 qualification run" in r[1], r)

# tamper / partial / extra on the way to Lengau and on Lengau
staged_refusal("transfer tamper: a byte flipped in transit -> refused by the Lengau re-verification",
               tr_hooks={"after_push": lambda rd: open(os.path.join(rd, "bundle", "root", "task_24.json"), "a").write(" ")}, want="Lengau copy fails")
staged_refusal("transfer partial: a member lost in transit -> refused on Lengau",
               tr_hooks={"after_push": lambda rd: os.remove(os.path.join(rd, "bundle", "exits", "w_slot0.code"))}, want="Lengau copy")
staged_refusal("transfer extra: a file appears in the Lengau copy -> refused",
               tr_hooks={"after_push": lambda rd: wtext(os.path.join(rd, "bundle", "env", "extra.json"), "{}")}, want="Lengau copy fails")
staged_refusal("tool tamper: the shipped verifier altered on Lengau -> refused (not the Mac's bytes)",
               tr_hooks={"after_put": lambda dst: dst.endswith("e2q_stage_verify.py") and open(dst, "a").write("\n# x\n")}, want="not the Mac's bytes")
staged_refusal("tool tamper: the shipped expectation altered on Lengau -> refused",
               tr_hooks={"after_put": lambda dst: dst.endswith("expect.json") and wjson(dst, {"expect": dict(json.load(open(dst))["expect"], sequence=1)})},
               want="expectation on Lengau")
staged_refusal("containment: a symbolic link inside the staging root on the way to the bundle -> refused",
               tr_hooks={"after_push": lambda rd: (os.rename(rd + "/bundle", rd + "/real_bundle"), os.symlink(rd + "/real_bundle", rd + "/bundle"))},
               want="Lengau copy fails")
qp = os.path.join(CTLD, "chpc", "row19_ec2_qualify.py"); keep = open(qp).read(); open(qp, "a").write("\n# drift\n")
staged_refusal("pins: the Lengau qualifier is not the adopted bytes -> refused", want="controller tree is not the reviewed")
open(qp, "w").write(keep)
sp = os.path.join(CTLD, S.SNAPSHOT_REL); keep_s = open(sp).read(); os.remove(sp)
staged_refusal("pins: the deployed snapshot chpc/claims_snapshot_e2.json missing on Lengau -> transport failure, nothing claimed",
               want="pins could not be read", kind="TRANSPORT")
open(sp, "w").write(keep_s)
run, nn, a, pd = fresh()
st_ = stamp(); _, rd_ = S.remote_dirs(L, run, nn, st_); os.makedirs(rd_)
r = do_stage(Fake(), run, nn, st=st_)
check("replay: an existing remote staging directory (same stamp) -> transport refusal, nothing extracted into it",
      r[0] == "TRANSPORT" and "not new" in r[1] and os.listdir(rd_) == [], r)
r = do_stage(Fake(), run, nn, st=st_)
check("replay: an existing local staging directory (same stamp) -> refused", r[0] == "REFUSED" and "every invocation is fresh" in r[1], r)
with S.stage_lock(run):
    r = do_stage(Fake(), run, nn)
check("concurrency: a second invocation while one holds runs/<run>/e2q_stage/.lock -> refused", r[0] == "REFUSED" and ".lock" in r[1], r)

# verifier unit cases not reachable through S3 (S3 holds no symlinks or special files)
run, nn, a, pd = fresh()
loc = os.path.join(TMP, "unit_bundle"); shutil.copytree(pd, loc)
e = dict(key=f"{run}/{nn}", attempt_id=a["attempt_id"], sequence=a["sequence"], contract="E2Q1", plan_sha256=a["plan_sha256"],
         partition_sha256=S.DATA_PINS[S.PARTITION], opmanifest_sha256=S.DATA_PINS[S.OPMANIFEST["E2Q1"]], work=WORK, duplicates=DUPS, sentinels=SENT)
check("verifier: the clean copy passes", V.verify(loc, e)["ok"])
os.symlink(os.path.join(loc, "env", "lscpu.txt"), os.path.join(loc, "logs", "w_slot2.lnk"))
d = V.verify(loc, e); os.remove(os.path.join(loc, "logs", "w_slot2.lnk"))
check("verifier: a symbolic link member is refused, never followed", not d["ok"] and any("symbolic link" in p for p in d["problems"]), d["problems"][:3])
os.mkfifo(os.path.join(loc, "logs", "fifo")); d = V.verify(loc, e); os.remove(os.path.join(loc, "logs", "fifo"))
check("verifier: a special file is refused", not d["ok"] and any("special file" in p for p in d["problems"]), d["problems"][:3])
for name, ex in (("another sequence", dict(e, sequence=1)), ("another partition", dict(e, partition_sha256="0" * 64)),
                 ("the E2Q2 contract", dict(e, contract="E2Q2")), ("other sentinels", dict(e, sentinels=[[7, 0]] + SENT[1:])),
                 ("a short panel", dict(e, work=WORK[:51]))):
    d = V.verify(loc, ex)
    check(f"verifier: an expectation with {name} is refused", not d["ok"], d["problems"][:2])
lines = open(os.path.join(loc, "BUNDLE_SHA256SUMS")).read().splitlines(True)
open(os.path.join(loc, "BUNDLE_SHA256SUMS"), "w").write("".join([lines[1], lines[0]] + lines[2:]))
d = V.verify(loc, e); open(os.path.join(loc, "BUNDLE_SHA256SUMS"), "w").write("".join(lines))
check("verifier: a re-ordered sealed list (not the producer's C order) is refused", not d["ok"] and any("C order" in p for p in d["problems"]))
open(os.path.join(loc, "BUNDLE_SHA256SUMS"), "w").write("".join(lines) + lines[0])
d = V.verify(loc, e); open(os.path.join(loc, "BUNDLE_SHA256SUMS"), "w").write("".join(lines))
check("verifier: a member listed twice is refused", not d["ok"] and any("twice" in p for p in d["problems"]))
open(os.path.join(loc, "BUNDLE_SHA256SUMS"), "w").write("".join(lines) + f"{'0' * 64}  ../escape\n")
d = V.verify(loc, e); open(os.path.join(loc, "BUNDLE_SHA256SUMS"), "w").write("".join(lines))
check("verifier: a sealed path escaping the bundle is refused", not d["ok"] and any("normalised path" in p for p in d["problems"]))
before = tree_state(loc); V.verify(loc, e)
check("verifier: reading never changes a byte, mode or mtime", tree_state(loc) == before)
d = V.verify(loc, e, stage_root=os.path.join(TMP, "elsewhere"))
check("verifier: a bundle outside the staging root is refused", not d["ok"] and "not strictly inside" in d["problems"][0])

# E2Q2 is staged by the same procedure
run, nn, a, pd = fresh("E2Q2")
r = do_stage(Fake(), run, nn)
check("E2Q2: a clean qual-E2Q2 bundle stages with its own contract and operational manifest pin", r[0] == "OK" and r[1][2]["expect"]["contract"] == "E2Q2"
      and r[1][2]["expect"]["opmanifest_sha256"] == S.DATA_PINS["aws_ec2/prod/manifest_e2q2_e2.json"], r)

# E2Q3 (REVISION 2, owner 21 Oct 2026: the on-demand third attempt) is staged by the same procedure
run, nn, a, pd = fresh("E2Q3")
r = do_stage(Fake(), run, nn)
check("E2Q3: a clean qual-E2Q3 bundle stages with its own contract and operational manifest pin", r[0] == "OK" and r[1][2]["expect"]["contract"] == "E2Q3"
      and r[1][2]["expect"]["opmanifest_sha256"] == S.DATA_PINS["aws_ec2/prod/manifest_e2q3_e2.json"] and run == "qual-E2Q3", r)
run, nn, a, pd = fresh("E2Q3")
wjson(os.path.join(pd, "env", "plan.json"), plan_doc(run, nn, "E2Q2", a["sequence"])); seal_sums(pd)
r = do_stage(Fake(), run, nn)
check("E2Q3: an E2Q2-contract plan presented under the qual-E2Q3 attempt -> refused (contract / plan bytes)", r[0] == "REFUSED", r)

# ============================================================================================================================
# 3. qualification-time cases (each on a fresh staged attempt)

def staged(contract="E2Q1"):
    run, nn, a, pd = fresh(contract)
    t = Fake(); r = do_stage(t, run, nn)
    assert r[0] == "OK", r
    return run, nn, r[1], t


run, nn, (sd2, rd2, rc2), t = staged(); mode("no_release")
r = do_qualify(t, rc2["stamp"], run, nn)
b2 = json.load(open(os.path.join(sd2, "binding.json"))) if os.path.exists(os.path.join(sd2, "binding.json")) else {}
check("qualify: a NO_RELEASE certificate is a completed evaluation -> exit 3, bound, claimed", r == ("RC", 3) and b2.get("outcome") == "NO_RELEASE"
      and os.path.exists(claim_path(run, nn)), r)
r = do_stage(Fake(), run, nn)
check("no retry by outcome: after NO_RELEASE the attempt cannot be staged again", r[0] == "REFUSED" and "already claimed" in r[1], r)

run, nn, (sd3, rd3, rc3), t = staged(); mode("release")
inv = json.load(open(os.path.join(L["root"], "ec2", "authority", "inventory.json")))
install(dict(inv, generation=inv["generation"] - 1))
r = do_qualify(t, rc3["stamp"], run, nn)
check("preflight: an installed inventory of an older generation -> refused, NOTHING claimed", r[0] == "REFUSED" and "ec2_sync" in r[1]
      and not os.path.exists(claim_path(run, nn)), r)
install(inv)
r = do_qualify(t, rc3["stamp"], run, nn, now=inv["at"] + S.INVENTORY_MAX_AGE_S - S.QUALIFY_MARGIN_S + 10)
check("preflight: an installed inventory within the margin of the qualifier's 6 h limit -> refused, nothing claimed (no NO_RELEASE for a stale view)",
      r[0] == "REFUSED" and "old" in r[1] and not os.path.exists(claim_path(run, nn)), r)
open(os.path.join(rd3, "bundle", "env", "censored.txt"), "a").write("w_slot1\n")
r = do_qualify(t, rc3["stamp"], run, nn)
check("tamper on Lengau after staging -> refused before the claim", r[0] == "REFUSED" and "Lengau copy" in r[1] and not os.path.exists(claim_path(run, nn)), r)

run, nn, (sd4, rd4, rc4), t = staged()
open(os.path.join(sd4, "bundle", "env", "declared.txt"), "a").write("x\n")
r = do_qualify(t, rc4["stamp"], run, nn)
check("tamper of the Mac staged copy after its receipt -> refused, nothing claimed", r[0] == "REFUSED" and "changed since its receipt" in r[1]
      and not os.path.exists(claim_path(run, nn)), r)

run, nn, (sd5, rd5, rc5), t = staged(); mode("mutate")
r = do_qualify(t, rc5["stamp"], run, nn)
check("never mutated: a qualifier that writes into the bundle -> refused after the run, no binding, the claim stays",
      r[0] == "REFUSED" and "Lengau copy" in r[1] and not os.path.exists(os.path.join(sd5, "binding.json")) and os.path.exists(claim_path(run, nn)), r)

run, nn, (sd6, rd6, rc6), t = staged(); mode("crash")
r = do_qualify(t, rc6["stamp"], run, nn)
check("qualifier failure (exit 1, no certificate) -> exit 2, no certificate used, claim kept", r == ("RC", 2) and not os.path.exists(os.path.join(sd6, "binding.json"))
      and open(os.path.join(rd6, "qualify.rc")).read().strip() == "1" and os.path.exists(claim_path(run, nn)), r)
r = do_qualify(t, rc6["stamp"], run, nn)
check("... and a retry of the failed evaluation is refused (claimed; DESIGN choice 6)", r[0] == "REFUSED" and "claimed" in r[1], r)

run, nn, (sd7, rd7, rc7), t = staged(); mode("release")
wtext(os.path.join(rd7, f"cert_{run}_{nn}.json"), '{"outcome": "RELEASE"}')
r = do_qualify(t, rc7["stamp"], run, nn)
check("stale output: a certificate already at --out -> refused by the remote shell before the claim", r[0] == "REFUSED" and "stale" in r[1]
      and not os.path.exists(claim_path(run, nn)), r)

run, nn, (sd8, rd8, rc8), t = staged(); mode("wrong_bind")
r = do_qualify(t, rc8["stamp"], run, nn)
check("a certificate that binds another bundle -> refused, no binding", r[0] == "REFUSED" and "bound.bundle_sha256" in r[1]
      and not os.path.exists(os.path.join(sd8, "binding.json")), r)

run, nn, (sd9, rd9, rc9), t = staged(); mode("lie")
r = do_qualify(t, rc9["stamp"], run, nn)
check("a certificate whose outcome disagrees with the exit status -> refused", r[0] == "REFUSED" and "exit 3" in r[1], r)

run, nn, (sd10, rd10, rc10), t = staged(); mode("release")
qp = os.path.join(CTLD, "chpc", "row19_ec2_qualify.py"); keep = open(qp).read()
t.hooks["before_run"] = lambda host, cmd: ("EVALUATION_CLAIM" in cmd and "noclobber" not in cmd and "set -C" in cmd) and open(
    os.path.join(CTLD, "analyze.py"), "a").write("# drift during the run\n")
r = do_qualify(t, rc10["stamp"], run, nn)
wtext(os.path.join(CTLD, "analyze.py"), CODE_BYTES["analyze.py"])
check("pins: the controller tree changing while the qualifier runs -> refused, no certificate used", r[0] == "REFUSED" and "changed while" in r[1]
      and not os.path.exists(os.path.join(sd10, "binding.json")), r)

run, nn, (sd11, rd11, rc11), t = staged(); mode("release")
a_dir = S.remote_dirs(L, run, nn, "-")[0]; wtext(os.path.join(a_dir, "EVALUATION_CLAIM"), "someone-else\n")
r = do_qualify(t, rc11["stamp"], run, nn)
check("claim race: a claim written between staging and qualification -> refused, the qualifier never runs", r[0] == "REFUSED" and "claimed" in r[1]
      and not os.path.exists(os.path.join(rd11, "qualify.rc")), r)

run, nn, (sd12, rd12, rc12), t = staged("E2Q2"); mode("release")
r = do_qualify(t, rc12["stamp"], run, nn)
argv = json.load(open(os.path.join(CTLD, "chpc", ".standin_argv.json")))
check("E2Q2: qualified with key qual-E2Q2/<n> and the E2Q2 operational manifest", r == ("RC", 0) and argv[argv.index("--key") + 1] == f"{run}/{nn}"
      and argv[argv.index("--opmanifest") + 1] == "aws_ec2/prod/manifest_e2q2_e2.json", (r, argv[-6:]))

run, nn, (sd13, rd13, rc13), t = staged("E2Q3"); mode("release")
r = do_qualify(t, rc13["stamp"], run, nn)
argv = json.load(open(os.path.join(CTLD, "chpc", ".standin_argv.json")))
check("E2Q3: qualified with key qual-E2Q3/<n> and the E2Q3 operational manifest", r == ("RC", 0) and argv[argv.index("--key") + 1] == f"{run}/{nn}"
      and argv[argv.index("--opmanifest") + 1] == "aws_ec2/prod/manifest_e2q3_e2.json", (r, argv[-6:]))

check("guard: no real aws/ssh/scp was ever invoked in any case", not os.path.exists(GUARD_LOG), open(GUARD_LOG).read() if os.path.exists(GUARD_LOG) else "")
print(f"\n{n[0] - len(fails)} passed, {len(fails)} failed")
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if fails else 0)
