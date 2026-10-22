"""EC2 epoch 2 - collect, verify and stage ONE reconciled E2Q1/E2Q2 bundle, then run the reviewed qualification command
(the Codex-reviewed chpc/candidate_e2s bytes of 0a72081, promoted to aws_ec2/ on 20 Oct 2026 with ONE administrative
change: the controls pin moved from v17 9ea4e727 to v18 452b82df - owner rule 20 Oct 2026, no Codex review for an
administrative change; the v18 controls keep every qualification code pin of v17). Mac only.

REVISION 2 (owner decision 21 Oct 2026, R052 "On-demand E2Q3"; chpc/candidate_v19_oploss/DESIGN_v19.md s.7; operational change,
no Codex review of this tooling). The run qual-E2Q3 (contract E2Q3, the on-demand third attempt) is staged by the same
procedure: RUNS and OPMANIFEST gain E2Q3, DATA_PINS gains its operational manifest aws_ec2/prod/manifest_e2q3_e2.json (promoted
and deployed with controls v19), and the controls pin moves to the v19 candidate controls (ADOPTED_CONTROLS_SHA), whose
qualification code pins include the v19 EC2 state / E2Q module / ingestion. Until v19 is promoted and deployed this tool
REFUSES every run (the Mac controls are not the pinned bytes) - intended: E2Q3 launches after v19. Every check is unchanged.

    python3 e2q_stage.py stage   --run qual-E2Q1 --attempt 1        # collect + verify + stage on Lengau + re-verify there
    python3 e2q_stage.py qualify --run qual-E2Q1 --attempt 1 --stamp <stamp of a verified staging>
    python3 e2q_stage.py run     --run qual-E2Q1 --attempt 1        # both, in one invocation

It closes the "concrete bundle collection / verification / staging procedure" Codex requires before one paid E2Q1
(reviews/2026-10-19_e2_adoption_codex_review.md "Before one paid E2Q1"; 2026-10-19_e2_repair_codex_rereview.md "Staging,
wording and remaining sequence"). It is DESIGN_e2q.md s.7 step 6, made explicit. The epoch-1 Q1/Q2 bundles were never staged
for qualification or ingestion (qual-Q1/4 was dispositioned, qual-Q2/1 waits on a release that never came), so the one
REAL precedent is row 23's aws_ec2/bench_finish.py (S3 sync into a fresh local directory, a fresh remote directory, the
bundle digest recomputed on Lengau, the controller-tree pins checked before and after the remote tool runs, the exit status
propagated, a binding file); this tool follows it and adds what an E2Q bundle needs.

PHASES (each refuses on the first failed check; nothing is ever written inside a bundle, here or on Lengau):
  identity  the attempt is THE ledger attempt runs/<run>/attempts.json #n: contract E2Q1/E2Q2 of its own run, reconciled,
            ingestion pending, no disposition request, attempt id ec2-<run>-a<n>, results prefix exactly
            s3://<bucket>/results/t1_access/aws_bench/<run>/attempt_<n>/, plan file runs/<run>/plan_attempt<n>.json with its
            plan_sha256, work = the declared panel's work, duplicates = its duplicates, 4 sentinels outside them; the CURRENT
            sealed inventory (runs/inventory/latest.json, generation = the authority state's) carries it identically. The Mac
            data files (partition, deployed snapshot, panel, three operational manifests, funding), the adopted controls and
            the production manifest are their pinned bytes (DATA_PINS, ADOPTED_CONTROLS_SHA, PROD_SHA).
  collect   list the prefix (s3api list-objects-v2), then `aws s3 sync` it into a NEW local directory
            runs/<run>/e2q_stage/<stamp>/bundle; the local file set and sizes must be exactly the listing (no partial sync,
            nothing extra).
  verify    e2q_stage_verify.verify on the local copy (member contract: sealed / required / allowed / bound - see that file).
            The staging receipt (receipt.json, beside the bundle) binds the identity, the S3 listing, every member's sha256,
            the tree digest, the inventory generation and seal, the expected Lengau tree pins and both tool digests.
  stage     through the sanctioned transfer node (TRANSFER_HOST chpc-scp): one tar stream into a NEW directory
            <REMOTE_T>/ec2_stage/<run>/attempt_<n>/<stamp>/ (the fixed contained staging root: outside the controller
            clone, the scientific clone, the screen root and its campaign), then the verifier and the expectation beside the
            bundle - never inside it.
  reverify  on the login node (LOGIN_HOST lengau, where the controller commands run; status/ingestion precedent): the shipped
            verifier's sha256 must be the Mac's, it runs under t1py with --stage-root and must report the Mac's tree digest,
            file count and members; the controller tree's qualification inputs (the code set row19_ec2_e2qual.CODE at the
            adopted controls / manifest pins, controls, manifest, partition, deployed snapshot, panel, operational manifests,
            funding) are their pinned bytes; the INSTALLED inventory is the Mac's current generation and seal, carries the
            attempt reconciled and pending, and is fresh with QUALIFY_MARGIN_S to spare (a stale inventory would otherwise end
            in a NO_RELEASE certificate for an administrative reason).
  qualify   one claim per attempt: the remote shell creates <attempt dir>/EVALUATION_CLAIM with noclobber and refuses if it
            exists, then runs exactly the reviewed command (DESIGN_e2q.md s.7 step 6, qualifier REVISION 6 docstring) with the
            explicit `--snapshot chpc/claims_snapshot_e2.json`, a NEW --sandbox and a NEW --out inside the staging directory.
            Afterwards the bundle is re-verified (tree digest unchanged: never mutated), the tree pins are re-read (unchanged),
            the certificate must be fresh and bind this bundle (BUNDLE_SHA256SUMS), plan, attempt, panel, snapshot, partition,
            funding and operational manifests, its outcome must agree with the exit status (0 RELEASE, 3 NO_RELEASE or
            INCONCLUSIVE). The certificate is copied to the Mac stage directory with binding.json. Nothing is committed,
            adopted or released here: the actual-result review and release-adopt stay the reviewed later steps.
EXIT 0 staged and verified / RELEASE; 3 a completed evaluation that is not RELEASE; 4 REFUSED (identity, partial, extra,
tampered, replayed, pins, claim); 2 a transport or qualifier failure (no certificate is used). A claimed attempt is never
evaluated again by this tool (no retry by outcome; a failed evaluation needs a reviewed decision - DESIGN_e2s.md choice 6).
Every Lengau path is a constant of this file; tests substitute REMOTE_T and the Transport, never the checks."""
import argparse, contextlib, fcntl, hashlib, json, os, shlex, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import e2q_stage_verify as V


def _t1(start):
    t = start
    while os.path.basename(t) != "t1_access":
        if os.path.dirname(t) == t:
            raise RuntimeError(f"{start} is not inside a t1_access tree")
        t = os.path.dirname(t)
    return t


T1 = _t1(HERE)                                   # the Mac tree (tests point it at a synthetic tree)
BUCKET = "xtenure-cself-pvr-usw2"
RESULTS_PREFIX = "results/t1_access/aws_bench"   # = prod_userdata.sh OUT and prod_launch's ledger `results`
AWS_PROFILE, S3_REGION = "xtenure-read", "us-west-2"
REMOTE_T = "/mnt/lustre/users/pvanrooyen/t1_toolchain"
TRANSFER_HOST, LOGIN_HOST = "chpc-scp", "lengau"  # ~/.ssh/config: scp.chpc.ac.za (login1, transfer) / lengau (login2)
RUNS = {"E2Q1": "qual-E2Q1", "E2Q2": "qual-E2Q2", "E2Q3": "qual-E2Q3"}                   # REVISION 2: E2Q3
PROD_SHA = "43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c"
ADOPTED_CONTROLS_SHA = "111c3107636f2a621cdf24e4e4c86cdba1f735204237fd1ff1bfbc3a5a0315a5"   # v19 (chpc/candidate_v19_oploss/v19_promotion_map.json controls row)
SNAPSHOT_REL = "chpc/claims_snapshot_e2.json"   # the DEPLOYED snapshot the reviewed command passes explicitly
DATA_PINS = {                                    # chpc/candidate_v17/v17_promotion_map.json rows (e2_final, Codex A favourable); v18 changes none
    "chpc/row19_partition_e2.json": "48cea639e823abbf39238e3dd7c075f63ba9eca8467009348510e2943ed56fa6",
    SNAPSHOT_REL: "31cc268ff3247858fc73ac17a3a387b43e17a829d9cdea505958890a97eecb6f",
    "aws_ec2/prod/panel_e2q_e2.json": "f04a5e43634e13bfceaf173e303ebf780f4280de044b6bd97ee9e2c3f711c7a2",
    "aws_ec2/prod/manifest_e2q1_e2.json": "3ea8cafd736871de715062ca398f36ff98f93f27d1d82bd977c3b72b0f1cfb8b",
    "aws_ec2/prod/manifest_e2q2_e2.json": "4af4a64d83c749394c7159814359da716b2a9f9a694cd23fe46157aecd7b0cec",
    "aws_ec2/prod/manifest_e2q3_e2.json": "6d59c1f8568945f6121f9f16779aabe30f6334178bb0ba8c9d192a024805e17f",   # REVISION 2: the v19 map's data row
    "aws_ec2/prod/manifest_production_e2.json": "e126050536a8459cb1432cf78321e82147c67f5406441fff131a1f543f9f82f9",
    "aws_ec2/e2_funding.json": "d6f414e8107f25e5de43d6b33764106c6c92dd64440ff33fddf4873416ce4815",
}
OPMANIFEST = {"E2Q1": "aws_ec2/prod/manifest_e2q1_e2.json", "E2Q2": "aws_ec2/prod/manifest_e2q2_e2.json",
              "E2Q3": "aws_ec2/prod/manifest_e2q3_e2.json"}
PROD_OPMANIFEST, PANEL, FUNDING, PARTITION = ("aws_ec2/prod/manifest_production_e2.json", "aws_ec2/prod/panel_e2q_e2.json",
                                              "aws_ec2/e2_funding.json", "chpc/row19_partition_e2.json")
CODE = sorted(["chpc/row19_ec2_qualify.py", "chpc/row19_ec2_ingest.py", "chpc/row19_ec2_state.py", "chpc/row19_partition.py",
               "chpc/row19_ec2_root.py", "chpc/row19_ec2_e2rules.py", "chpc/row19_ec2_e2qual.py", "chpc/row19_shard.py",
               "chpc/row19_screen_verify.py", "analyze.py", "models.py"])          # = row19_ec2_e2qual.CODE (a test checks)
MANIFEST_CODE = ("analyze.py", "models.py", "chpc/row19_shard.py")                # pinned by the manifest, not by controls
INVENTORY_MAX_AGE_S, QUALIFY_MARGIN_S = 6 * 3600, 3600                           # = row19_ec2_state.INVENTORY_MAX_AGE_S
CERT_SCHEMA = "row19-ec2-qualification-certificate-3"
OUTCOME_RC = {"RELEASE": 0, "NO_RELEASE": 3, "INCONCLUSIVE": 3}
OK, NOT_RELEASE, TRANSPORT, REFUSED = 0, 3, 2, 4
RECEIPT_SCHEMA, BINDING_SCHEMA = "row19-e2q-staging-receipt-1", "row19-e2q-qualification-binding-1"


class Refused(Exception):
    """A check failed: nothing further is done (exit 4)."""


class TransportError(Exception):
    """A transfer or remote step failed (exit 2)."""


def sha(p):
    return V.sha_file(p)


def jdump(obj, p, exclusive=False):
    data = json.dumps(obj, indent=1, sort_keys=True) + "\n"
    if exclusive:
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, "w") as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        return
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, p)


def layout(T=None):
    T = T or REMOTE_T
    return dict(T=T, t1py=f"{T}/t1py", ctl=f"{T}/rsc_screen_ctl/workspace_demo/t1_access", root=f"{T}/row19_screen",
                campaign=f"{T}/row19_screen_campaign", science=f"{T}/rsc_screen", stage_root=f"{T}/ec2_stage")


def containment_problem(L):
    """The staging root may neither be, contain nor lie inside the controller clone, scientific clone, root or campaign."""
    s = L["stage_root"].rstrip("/")
    for k in ("ctl", "science", "root", "campaign"):
        o = L[k].rstrip("/")
        if s == o or s.startswith(o + "/") or o.startswith(s + "/"):
            return f"the staging root {s} overlaps the {k} path {o}"
    return ""


def remote_dirs(L, run, n, stamp):
    a = f"{L['stage_root']}/{run}/attempt_{n}"
    return a, f"{a}/{stamp}"


class Transport:
    """The real transport: aws (S3, read profile), ssh/scp with ControlPath=none (bench_finish / ec2_sync precedent)."""
    SSH_OPTS = ["-o", "ControlPath=none", "-o", "ConnectTimeout=30", "-o", "BatchMode=yes"]

    def s3_list(self, url):
        bucket, _, prefix = url[len("s3://"):].partition("/")
        p = subprocess.run(["aws", "--profile", AWS_PROFILE, "--region", S3_REGION, "s3api", "list-objects-v2", "--bucket", bucket,
                            "--prefix", prefix, "--output", "json"], capture_output=True, text=True, timeout=600)
        if p.returncode:
            raise TransportError(f"s3api list-objects-v2 failed: {p.stderr.strip()[:300]}")
        doc = json.loads(p.stdout or "{}")
        if doc.get("IsTruncated") or doc.get("NextContinuationToken"):
            raise TransportError("the S3 listing is truncated")
        return {o["Key"][len(prefix):]: int(o["Size"]) for o in doc.get("Contents") or []}

    def s3_sync(self, url, dest):
        os.makedirs(dest)                                  # must be new: no destination-only file can survive
        p = subprocess.run(["aws", "--profile", AWS_PROFILE, "--region", S3_REGION, "s3", "sync", "--only-show-errors", url, dest + "/"],
                           capture_output=True, text=True, timeout=3600)
        if p.returncode:
            raise TransportError(f"s3 sync failed: {p.stderr.strip()[:300]}")

    def run(self, host, cmd, timeout=7200):
        p = subprocess.run(["ssh", *self.SSH_OPTS, host, cmd], capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr

    def push_tree(self, host, local_parent, name, remote_dir):
        parent = os.path.dirname(remote_dir)
        rc, _, err = self.run(host, f"mkdir -p -- {shlex.quote(parent)} && mkdir -- {shlex.quote(remote_dir)}", timeout=120)
        if rc:
            raise TransportError(f"the remote staging directory is not new: {err.strip()[:200]}")
        tar = subprocess.Popen(["tar", "-C", local_parent, "-cf", "-", name], stdout=subprocess.PIPE)
        p = subprocess.run(["ssh", *self.SSH_OPTS, host, f"tar -xf - -C {shlex.quote(remote_dir)}"], stdin=tar.stdout,
                           capture_output=True, timeout=7200)
        tar.stdout.close()
        if tar.wait() != 0 or p.returncode != 0:
            raise TransportError("the bundle transfer failed")

    def put(self, host, src, dst):
        p = subprocess.run(["scp", *self.SSH_OPTS, "-q", src, f"{host}:{dst}"], capture_output=True, text=True, timeout=300)
        if p.returncode:
            raise TransportError(f"scp to {host} failed: {p.stderr.strip()[:200]}")

    def get(self, host, src, dst):
        p = subprocess.run(["scp", *self.SSH_OPTS, "-q", f"{host}:{src}", dst + ".part"], capture_output=True, text=True, timeout=300)
        if p.returncode:
            raise TransportError(f"scp from {host} failed: {p.stderr.strip()[:200]}")
        os.replace(dst + ".part", dst)


# ---- identity ---------------------------------------------------------------------------------------------------------------

def aws_dir():
    return os.path.join(T1, "aws_ec2")


def tree_pins():
    """{t1_access-relative path: sha256} the Lengau controller tree must hold for the qualification: the code set at the
    adopted controls' latest version pins (chpc helpers) and the production manifest's code pins (analyze, models,
    row19_shard), plus the data files, the controls and the manifest. The Mac copies must already be these bytes."""
    bad = [f"{rel} ({sha(os.path.join(T1, rel))[:12] if os.path.exists(os.path.join(T1, rel)) else 'missing'})"
           for rel, h in sorted(DATA_PINS.items()) if not os.path.exists(os.path.join(T1, rel)) or sha(os.path.join(T1, rel)) != h]
    cp, mp = os.path.join(T1, "chpc", "row19_screen_controls.json"), os.path.join(T1, "chpc", "row19_screen_manifest.json")
    if not os.path.exists(cp) or sha(cp) != ADOPTED_CONTROLS_SHA:
        bad.append("chpc/row19_screen_controls.json (not the adopted v19 bytes: promote and deploy controls v19 first)")
    if not os.path.exists(mp) or sha(mp) != PROD_SHA:
        bad.append("chpc/row19_screen_manifest.json (not 43b75f94)")
    if bad:
        raise Refused(f"the Mac's pinned inputs are not their reviewed bytes: {bad}")
    files = json.load(open(cp))["versions"][-1].get("files") or {}
    mcode = json.load(open(mp))["code"]["files"]
    pins = dict(DATA_PINS, **{"chpc/row19_screen_controls.json": ADOPTED_CONTROLS_SHA, "chpc/row19_screen_manifest.json": PROD_SHA})
    for rel in CODE:
        h = mcode.get(rel) if rel in MANIFEST_CODE else files.get(rel)
        if not h:
            raise Refused(f"no adopted pin for the qualification code file {rel}")
        pins[rel] = h
    return pins


def identity(run, n):
    """(expect, context) for the ledger attempt run/n; raises Refused."""
    contract = {v: k for k, v in RUNS.items()}.get(run)
    if contract is None:
        raise Refused(f"{run} is not an epoch-2 qualification run ({sorted(RUNS.values())})")
    key, aid = f"{run}/{n}", f"ec2-{run}-a{n}"
    lp = os.path.join(aws_dir(), "runs", run, "attempts.json")
    try:
        led = json.load(open(lp))
    except Exception as e:
        raise Refused(f"the {run} ledger is unreadable ({type(e).__name__})")
    att = [a for a in led.get("attempts") or [] if a.get("attempt") == n]
    if len(att) != 1:
        raise Refused(f"{key} is not exactly one ledger attempt")
    a = att[0]
    want = dict(contract=contract, state="reconciled", ingestion="pending", attempt_id=aid,
                results=f"s3://{BUCKET}/{RESULTS_PREFIX}/{run}/attempt_{n}/")
    bad = {k: a.get(k) for k, v in want.items() if a.get(k) != v}
    if bad or a.get("disposition_request"):
        raise Refused(f"{key} is not a reconciled, pending, undispositioned {contract} attempt of its own prefix: {bad or 'disposition requested'}")
    planp = os.path.join(aws_dir(), "runs", run, f"plan_attempt{n}.json")
    if os.path.realpath(a.get("plan") or "") != os.path.realpath(planp) or not os.path.isfile(planp) or sha(planp) != a.get("plan_sha256"):
        raise Refused(f"{key}: the plan file is not runs/{run}/plan_attempt{n}.json with the attempt's plan_sha256")
    pins = tree_pins()
    panel = json.load(open(os.path.join(T1, PANEL)))
    sent = [list(c) for c in a.get("sentinels") or []]
    if [list(c) for c in a.get("coordinates") or []] != panel["work"] or [list(c) for c in a.get("duplicates") or []] != panel["duplicates"] \
            or len(sent) != 4 or {tuple(c) for c in sent} & {tuple(c) for c in panel["duplicates"]}:
        raise Refused(f"{key}: its work/duplicates are not the declared panel's, or not 4 sentinels outside the duplicates")
    st = json.load(open(os.path.join(aws_dir(), "runs", ".authority_state.json")))
    inv = json.load(open(os.path.join(aws_dir(), "runs", "inventory", "latest.json")))
    if inv.get("generation") != st.get("generation"):
        raise Refused("the sealed inventory is not the authority's current generation: run ec2_sync.py cycle first")
    e = (inv.get("attempts") or {}).get(key) or {}
    iw = dict(attempt_id=aid, sequence=a["sequence"], plan_sha256=a["plan_sha256"], state="reconciled", ingestion="pending",
              contract=contract, coordinates=panel["work"], duplicates=panel["duplicates"], sentinels=sent, disposition_requested=False,
              **{"class": "qualification"})
    bad = sorted(k for k, v in iw.items() if (e.get(k) if not isinstance(v, list) else [list(c) for c in e.get(k) or []]) != v)
    if bad:
        raise Refused(f"the current sealed inventory does not carry {key} as the ledger does ({bad})")
    expect = dict(key=key, attempt_id=aid, sequence=a["sequence"], contract=contract, plan_sha256=a["plan_sha256"],
                  partition_sha256=DATA_PINS[PARTITION], opmanifest_sha256=DATA_PINS[OPMANIFEST[contract]],
                  work=panel["work"], duplicates=panel["duplicates"], sentinels=sent)
    ctx = dict(run=run, attempt=n, prefix=want["results"], instance=a.get("instance"), pins=pins,
               inventory=dict(generation=inv["generation"], sha256=inv.get("sha256"), at=inv.get("at")))
    return expect, ctx


# ---- phases -----------------------------------------------------------------------------------------------------------------

def stage_dir(run, stamp):
    return os.path.join(aws_dir(), "runs", run, "e2q_stage", stamp)


@contextlib.contextmanager
def stage_lock(run):
    d = os.path.join(aws_dir(), "runs", run, "e2q_stage"); os.makedirs(d, exist_ok=True)
    fh = open(os.path.join(d, ".lock"), "a+")
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fh.close(); raise Refused(f"another e2q_stage invocation holds runs/{run}/e2q_stage/.lock")
    try:
        yield
    finally:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN); fh.close()


def collect(tr, expect, ctx, stamp, log):
    sd = stage_dir(ctx["run"], stamp)
    if os.path.exists(sd):
        raise Refused(f"the local staging directory {sd} exists: every invocation is fresh")
    os.makedirs(sd)
    listing = tr.s3_list(ctx["prefix"])
    if not listing:
        raise Refused(f"PARTIAL: nothing under {ctx['prefix']}")
    bad = sorted(k for k in listing if not k or k.startswith("/") or k.endswith("/") or ".." in k.split("/"))
    if bad:
        raise Refused(f"EXTRA: S3 keys outside a plain relative layout {bad[:3]}")
    bundle = os.path.join(sd, "bundle")
    tr.s3_sync(ctx["prefix"], bundle)
    local = {}
    for d, _, fs in os.walk(bundle):
        for f in fs:
            p = os.path.join(d, f); local[os.path.relpath(p, bundle).replace(os.sep, "/")] = os.lstat(p).st_size
    if set(local) != set(listing):
        raise Refused(f"the local copy is not the S3 listing: missing {sorted(set(listing) - set(local))[:3]}, "
                      f"extra {sorted(set(local) - set(listing))[:3]} (PARTIAL or EXTRA)")
    diff = sorted(k for k in listing if listing[k] != local[k])
    if diff:
        raise Refused(f"PARTIAL: sizes differ from the S3 listing for {diff[:3]}")
    doc = V.verify(bundle, expect)
    if not doc["ok"]:
        raise Refused(f"the collected bundle fails verification: {doc['problems'][:6]}")
    receipt = dict(schema=RECEIPT_SCHEMA, stamp=stamp, at=time.time(), expect=expect, context=ctx,
                   s3=dict(prefix=ctx["prefix"], objects=len(listing), listing_sha256=V.tree_digest([[k, str(v)] for k, v in listing.items()])),
                   bundle=dict(path=os.path.relpath(bundle, T1), files=doc["files"], tree_sha256=doc["tree_sha256"], sums_sha256=doc["sums_sha256"],
                               plan_sha256=doc["plan_sha256"], sealed=doc["sealed"], members=doc["members"]),
                   tools={"e2q_stage.py": sha(os.path.abspath(__file__)), "e2q_stage_verify.py": sha(V.__file__)})
    jdump(receipt, os.path.join(sd, "receipt.json"), exclusive=True)
    jdump(dict(expect=expect), os.path.join(sd, "expect.json"), exclusive=True)
    log(f"collected and verified {doc['files']} files ({doc['sealed']} sealed), tree {doc['tree_sha256'][:12]}")
    return sd, receipt


def _pin_cmd(L, pins):
    return f"cd -- {shlex.quote(L['ctl'])} && sha256sum -- " + " ".join(shlex.quote(p) for p in sorted(pins))


def _parse_sums(out):
    got = {}
    for ln in out.splitlines():
        parts = ln.split()
        if len(parts) == 2 and len(parts[0]) == 64:
            got[parts[1]] = parts[0]
    return got


def remote_pins(tr, L, pins):
    rc, out, err = tr.run(LOGIN_HOST, _pin_cmd(L, pins), timeout=600)
    got = _parse_sums(out)
    if rc or sorted(got) != sorted(pins):
        raise TransportError(f"the controller-tree pins could not be read (rc {rc}): {err.strip()[:200]}")
    return got


def remote_verify(tr, L, rdir, receipt):
    """Run the shipped verifier on Lengau; returns its document. Raises Refused on any disagreement with the Mac."""
    cmd = (f"cd -- {shlex.quote(rdir)} && sha256sum -- e2q_stage_verify.py expect.json && {shlex.quote(L['t1py'])} e2q_stage_verify.py "
           f"--bundle {shlex.quote(rdir + '/bundle')} --expect expect.json --stage-root {shlex.quote(L['stage_root'])}")
    rc, out, err = tr.run(LOGIN_HOST, cmd, timeout=3600)
    sums = _parse_sums(out)
    docs = [ln for ln in out.splitlines() if ln.startswith("{")]
    if len(docs) != 1 or "e2q_stage_verify.py" not in sums:
        raise TransportError(f"the remote verifier did not run (rc {rc}): {err.strip()[:200]}")
    if sums["e2q_stage_verify.py"] != receipt["tools"]["e2q_stage_verify.py"]:
        raise Refused("the verifier on Lengau is not the Mac's bytes")
    if sums.get("expect.json") != sha(os.path.join(stage_dir(receipt["context"]["run"], receipt["stamp"]), "expect.json")):
        raise Refused("the expectation on Lengau is not the Mac's bytes")
    doc = json.loads(docs[0])
    b = receipt["bundle"]
    if rc != 0 or not doc.get("ok"):
        raise Refused(f"the Lengau copy fails verification: {doc.get('problems', [])[:6]}")
    if (doc.get("tree_sha256"), doc.get("files"), doc.get("members")) != (b["tree_sha256"], b["files"], b["members"]):
        raise Refused("the Lengau copy is not the staged bundle (tree digest, count or members differ)")
    return doc


def inventory_preflight(tr, L, ctx, sd, now=None):
    """The root's INSTALLED inventory must be the Mac's current generation/seal, carry the attempt reconciled and pending,
    and stay fresh for QUALIFY_MARGIN_S more."""
    now = time.time() if now is None else now
    p = os.path.join(sd, f"installed_inventory_{int(now)}.json")
    tr.get(TRANSFER_HOST, f"{L['root']}/ec2/authority/inventory.json", p)
    inv = json.load(open(p))
    e = (inv.get("attempts") or {}).get(f"{ctx['run']}/{ctx['attempt']}") or {}
    at = inv.get("at")
    if inv.get("generation") != ctx["inventory"]["generation"] or inv.get("sha256") != ctx["inventory"]["sha256"]:
        raise Refused(f"the installed inventory (g{inv.get('generation')}) is not the Mac's current generation "
                      f"g{ctx['inventory']['generation']}: run ec2_sync.py cycle and stage again")
    if (e.get("state"), e.get("ingestion")) != ("reconciled", "pending") or e.get("disposition_requested"):
        raise Refused("the installed inventory does not carry the attempt reconciled and pending")
    if not isinstance(at, (int, float)) or now - at > INVENTORY_MAX_AGE_S - QUALIFY_MARGIN_S or at > now + 60:
        raise Refused(f"the installed inventory is {now - (at or 0):.0f} s old: within {QUALIFY_MARGIN_S} s of the "
                      f"{INVENTORY_MAX_AGE_S} s limit the qualifier enforces; install a fresh generation first")
    return dict(generation=inv["generation"], sha256=inv["sha256"], at=at, copy=os.path.basename(p))


def push(tr, L, sd, receipt, log):
    run, n, stamp = receipt["context"]["run"], receipt["context"]["attempt"], receipt["stamp"]
    why = containment_problem(L)
    if why:
        raise Refused(why)
    _, rdir = remote_dirs(L, run, n, stamp)
    tr.push_tree(TRANSFER_HOST, sd, "bundle", rdir)
    tr.put(TRANSFER_HOST, V.__file__, f"{rdir}/e2q_stage_verify.py")
    tr.put(TRANSFER_HOST, os.path.join(sd, "expect.json"), f"{rdir}/expect.json")
    log(f"staged on Lengau at {rdir} through {TRANSFER_HOST}")
    return rdir


def local_unchanged(sd, receipt):
    doc = V.verify(os.path.join(sd, "bundle"), receipt["expect"])
    if not doc["ok"] or doc["tree_sha256"] != receipt["bundle"]["tree_sha256"]:
        raise Refused("the local staged bundle changed since its receipt (or fails verification): stage afresh")


def claimed_problem(tr, L, run, n):
    """Refuse when the attempt's evaluation claim exists on Lengau; an unanswered probe is a transport failure, never absence."""
    claim = remote_dirs(L, run, n, "-")[0] + "/EVALUATION_CLAIM"
    rc, out, err = tr.run(LOGIN_HOST, f"if [ -e {shlex.quote(claim)} ]; then echo CLAIMED; cat -- {shlex.quote(claim)}; else echo UNCLAIMED; fi",
                          timeout=120)
    first = (out.splitlines() or [""])[0].strip()
    if rc != 0 or first not in ("CLAIMED", "UNCLAIMED"):
        raise TransportError(f"the evaluation claim could not be probed (rc {rc}): {err.strip()[:160]}")
    if first == "CLAIMED":
        raise Refused(f"{run}/{n} was already claimed for evaluation (stamp {' '.join(out.split()[1:])}): no re-evaluation")


def stage(tr, run, n, log=print, stamp=None, now=None):
    """collect + verify + stage + reverify. Returns (stage dir, remote dir, receipt)."""
    L = layout()
    stamp = stamp or time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    with stage_lock(run):
        expect, ctx = identity(run, n)
        claimed_problem(tr, L, run, n)
        sd, receipt = collect(tr, expect, ctx, stamp, log)
        rdir = push(tr, L, sd, receipt, log)
        doc = remote_verify(tr, L, rdir, receipt)
        got = remote_pins(tr, L, ctx["pins"])
        bad = sorted(f for f in ctx["pins"] if got.get(f) != ctx["pins"][f])
        if bad:
            raise Refused(f"the Lengau controller tree is not the reviewed qualification inputs on {bad}")
        local_unchanged(sd, receipt)
        jdump(dict(schema=RECEIPT_SCHEMA + "-remote", stamp=stamp, remote_dir=rdir, transfer_host=TRANSFER_HOST, login_host=LOGIN_HOST,
                   tree_sha256=doc["tree_sha256"], files=doc["files"], tree_pins=got, at=time.time()),
              os.path.join(sd, "remote.json"), exclusive=True)
        log(f"verified on Lengau: tree {doc['tree_sha256'][:12]}, {doc['files']} files; controller tree pins OK")
        return sd, rdir, receipt


def qualify_cmd(L, key, contract, rdir):
    """The reviewed qualification command (DESIGN_e2q.md s.7 step 6) with the explicit deployed snapshot."""
    return [L["t1py"], "chpc/row19_ec2_qualify.py", "e2", "--manifest", "chpc/row19_screen_manifest.json",
            "--partition", PARTITION, "--authority", f"{L['root']}/ec2/authority/inventory.json", "--key", key,
            "--bundle", f"{rdir}/bundle", "--opmanifest", OPMANIFEST[contract], "--prod-opmanifest", PROD_OPMANIFEST,
            "--panel", PANEL, "--snapshot", SNAPSHOT_REL, "--funding", FUNDING, "--sandbox", f"{rdir}/sandbox",
            "--out", f"{rdir}/cert_{key.replace('/', '_')}.json"]


def cert_problems(cert, receipt, pins):
    e, b = receipt["expect"], receipt["bundle"]
    bd = cert.get("bound") or {}; at = cert.get("attempt") or {}; ops = bd.get("opmanifests") or {}
    out = []
    if cert.get("schema") != CERT_SCHEMA or cert.get("outcome") not in OUTCOME_RC:
        out.append("not a schema-3 certificate with a known outcome")
    for k, got, want in (("attempt.key", at.get("key"), e["key"]), ("attempt.attempt_id", at.get("attempt_id"), e["attempt_id"]),
                         ("attempt.sequence", at.get("sequence"), e["sequence"]), ("attempt.plan_sha256", at.get("plan_sha256"), e["plan_sha256"]),
                         ("bound.bundle_sha256", bd.get("bundle_sha256"), b["sums_sha256"]), ("bound.plan_sha256", bd.get("plan_sha256"), b["plan_sha256"]),
                         ("bound.claims_snapshot_sha256", bd.get("claims_snapshot_sha256"), pins[SNAPSHOT_REL]),
                         ("bound.panel_sha256", bd.get("panel_sha256"), pins[PANEL]), ("bound.partition_sha256", bd.get("partition_sha256"), pins[PARTITION]),
                         ("bound.funding_sha256", bd.get("funding_sha256"), pins[FUNDING]),
                         ("bound.opmanifests.qualified", ops.get("qualified"), pins[OPMANIFEST[e["contract"]]]),
                         ("bound.opmanifests.production", ops.get("production"), pins[PROD_OPMANIFEST]),
                         ("bound.manifest_sha256", bd.get("manifest_sha256"), PROD_SHA)):
        if got != want:
            out.append(f"{k} {str(got)[:16]} is not {str(want)[:16]}")
    return out


def qualify(tr, run, n, stamp, log=print, now=None):
    """Run the reviewed qualification command once for a staged, verified stamp. Returns the exit code."""
    L = layout()
    with stage_lock(run):
        expect, ctx = identity(run, n)
        sd = stage_dir(run, stamp)
        try:
            receipt = json.load(open(os.path.join(sd, "receipt.json"))); remote = json.load(open(os.path.join(sd, "remote.json")))
        except Exception as e:
            raise Refused(f"stamp {stamp} has no complete staging receipt ({type(e).__name__}): stage first")
        if receipt.get("expect") != expect or receipt["context"]["pins"] != ctx["pins"] or receipt.get("stamp") != stamp:
            raise Refused("the attempt or the pins changed since this staging: stage afresh")
        claimed_problem(tr, L, run, n)
        if os.path.exists(os.path.join(sd, "binding.json")):
            raise Refused(f"stamp {stamp} already carries a qualification binding")
        local_unchanged(sd, receipt)
        adir, rdir = remote_dirs(L, run, n, stamp)
        if remote.get("remote_dir") != rdir:
            raise Refused("the staging record names another remote directory")
        remote_verify(tr, L, rdir, receipt)
        before = remote_pins(tr, L, ctx["pins"])
        if before != ctx["pins"]:
            raise Refused("the Lengau controller tree is not the reviewed qualification inputs")
        inv = inventory_preflight(tr, L, ctx, sd, now)
        argv = qualify_cmd(L, expect["key"], expect["contract"], rdir)
        out_p, sb = argv[argv.index("--out") + 1], argv[argv.index("--sandbox") + 1]
        q = shlex.quote
        shell = (f"set -u; cd -- {q(L['ctl'])} || exit 90; "
                 f"if [ -e {q(out_p)} ] || [ -e {q(sb)} ]; then echo 'STALE-OUTPUT' >&2; exit 92; fi; "
                 f"( set -C; printf '%s\\n' {q(stamp)} > {q(adir + '/EVALUATION_CLAIM')} ) 2>/dev/null || {{ echo 'CLAIM-EXISTS' >&2; exit 91; }}; "
                 f"{' '.join(q(x) for x in argv)} > {q(rdir + '/qualify.out')} 2>&1; rc=$?; "
                 f"printf '%s\\n' \"$rc\" > {q(rdir + '/qualify.rc')}; exit $rc")
        t0 = time.time()
        log(f"qualifying {expect['key']} on {LOGIN_HOST} (claim {adir}/EVALUATION_CLAIM)")
        rc, _, err = tr.run(LOGIN_HOST, shell, timeout=6 * 3600)
        if rc in (90, 91, 92):
            raise Refused({90: "the controller clone is not reachable", 91: "the attempt was already claimed for evaluation",
                           92: "a stale certificate or sandbox exists at the fresh paths"}[rc] + f" ({err.strip()[:120]})")
        after_doc = remote_verify(tr, L, rdir, receipt)          # never mutated (raises Refused otherwise)
        after = remote_pins(tr, L, ctx["pins"])
        if after != before:
            raise Refused("the controller tree changed while the qualifier ran: no certificate is used")
        if rc not in (0, 3):
            log(f"QUALIFIER FAILED (exit {rc}): no certificate is used; the attempt stays claimed (DESIGN_e2s.md choice 6)")
            return TRANSPORT
        cp = os.path.join(sd, os.path.basename(out_p))
        if os.path.exists(cp):
            raise Refused(f"a local certificate {cp} already exists")
        tr.get(TRANSFER_HOST, out_p, cp)
        try:
            cert = json.load(open(cp))
        except Exception as e:
            raise Refused(f"the certificate is unreadable ({type(e).__name__})")
        why = cert_problems(cert, receipt, ctx["pins"])
        if not why and (OUTCOME_RC[cert["outcome"]] != rc or not isinstance(cert.get("at"), (int, float)) or cert["at"] < t0 - 5):
            why = [f"the certificate (outcome {cert.get('outcome')}, at {cert.get('at')}) is not this run's exit {rc}"]
        if why:
            raise Refused(f"the certificate does not bind this staging: {why[:5]}")
        bind = dict(schema=BINDING_SCHEMA, key=expect["key"], stamp=stamp, qualifier_exit=rc, outcome=cert["outcome"],
                    certificate=os.path.basename(cp), certificate_sha256=sha(cp), receipt_sha256=sha(os.path.join(sd, "receipt.json")),
                    remote_dir=rdir, tree_sha256=after_doc["tree_sha256"], tree_pins=after, installed_inventory=inv,
                    command=argv, login_host=LOGIN_HOST, transfer_host=TRANSFER_HOST, at=time.time())
        jdump(bind, os.path.join(sd, "binding.json"), exclusive=True)
        log(f"{cert['outcome']}: certificate {os.path.relpath(cp, T1)} sha256 {bind['certificate_sha256'][:12]}; "
            "next: commit it, then the actual-result review (never release-adopt before it)")
        return OK if rc == 0 else NOT_RELEASE


def main(argv=None):
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("stage", "qualify", "run"):
        p = sub.add_parser(c); p.add_argument("--run", required=True, choices=sorted(RUNS.values())); p.add_argument("--attempt", type=int, required=True)
        if c == "qualify":
            p.add_argument("--stamp", required=True)
    a = ap.parse_args(argv)
    tr = Transport()
    try:
        if a.cmd == "qualify":
            return qualify(tr, a.run, a.attempt, a.stamp)
        sd, rdir, receipt = stage(tr, a.run, a.attempt)
        return qualify(tr, a.run, a.attempt, receipt["stamp"]) if a.cmd == "run" else OK
    except Refused as e:
        print(f"REFUSED: {e}"); return REFUSED
    except (TransportError, subprocess.TimeoutExpired, OSError, ValueError) as e:
        print(f"TRANSPORT OR REMOTE STEP FAILED: {type(e).__name__}: {e}"); return TRANSPORT


if __name__ == "__main__":
    sys.exit(main())
