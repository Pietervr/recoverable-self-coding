#!/usr/bin/env python3
"""Private-copy tests for the migration_v16 scripts (Codex review 2026-10-17 R1-R4 and the P3 fast path).

    python3 chpc/migration_v16/test_migration_v16.py [-k <substring>] [--keep]      (from anywhere)

The production scripts carry NO test hook. This harness builds a throwaway world under a fresh private temp directory:
a local git clone of the repository as the "Mac" tree, a fake Lengau toolchain root (two more local clones as the controller
and job clones, a gate, locks, a ledger, job scripts) and a fake-tool bin directory (ps, sha256sum, optionally flock). It then
COPIES the production files into the clone's chpc/migration_v16/ and substitutes exactly two tagged lines in that private copy:
the `# @root` toolchain root in remote_lib.sh (-> the fake root) and the `# @transport` ssh in lengau.sh (-> a local `bash -s`).
It refuses a fake root that is not beneath its own temp directory or that resolves to the production toolchain, and checks the
private copy differs from production on those two lines only. Nothing here runs ssh/scp, touches Lengau or the live tree, or
writes outside the temp directory (removed at the end unless --keep)."""
import hashlib, json, os, shutil, signal, stat, subprocess, sys, tempfile, time

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
T1_REL = "workspace_demo/t1_access"
REPO = subprocess.run(["git", "-C", HERE, "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip()
LIVE_T1 = os.path.join(REPO, T1_REL)
PROD_ROOT = "/mnt/lustre/users/pvanrooyen/t1_toolchain"
TRANSPORT = "ssh -o ControlPath=none -o ConnectTimeout=30 -o BatchMode=yes lengau bash -s"
ROOT_LINE = "T_ROOT=/mnt/lustre/users/pvanrooyen/t1_toolchain   # @root"
SELF = os.path.basename(__file__)
PROD_FILES = sorted(f for f in os.listdir(HERE) if os.path.isfile(os.path.join(HERE, f)) and f != SELF and not f.startswith("."))
QUAL_V15 = "3c605514fb36d6d9f67a2835adf516fa30298caa10c20411bbcbcff74c94592c"
REAL_SHA256SUM = shutil.which("sha256sum") or "/sbin/sha256sum"
PROMO_PATHS = ["chpc/row19_screen_controls.json", "chpc/row19_screen_controls_adoption.json", "chpc/row19_screen_admit.py",
               "chpc/row19_screen_status.py", "chpc/row19_screen_designated.json", "chpc/results/archive/row19_screen_v15_before_v16"]

BASE = None
TESTS = []


def test(name):
    def deco(fn):
        TESTS.append((name, fn)); return fn
    return deco


class Fail(Exception):
    pass


def sh(*cmd, cwd=None, check=True):
    r = subprocess.run(list(cmd), cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise Fail("command failed: %s\n%s%s" % (" ".join(cmd), r.stdout, r.stderr))
    return r.stdout


def write(p, data, mode=None):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w" if isinstance(data, str) else "wb") as fh:
        fh.write(data)
    if mode is not None:
        os.chmod(p, mode)


def unlock_tree(p):
    for d, dirs, files in os.walk(p):
        os.chmod(d, 0o755)
        for n in files:
            q = os.path.join(d, n)
            if not os.path.islink(q):
                os.chmod(q, 0o644)


def tree_digest(p):
    """A digest of every path, mode, file content and link target under p (the .git directory excluded)."""
    h = hashlib.sha256()
    for d, dirs, files in sorted(os.walk(p)):
        dirs[:] = sorted(x for x in dirs if x != ".git")
        for n in sorted(dirs + files):
            q = os.path.join(d, n); st = os.lstat(q); h.update(("%s %o\n" % (os.path.relpath(q, p), st.st_mode)).encode())
            if stat.S_ISLNK(st.st_mode):
                h.update(os.readlink(q).encode())
            elif stat.S_ISREG(st.st_mode):
                try:
                    h.update(open(q, "rb").read())
                except PermissionError:
                    h.update(b"<unreadable>")
    return h.hexdigest()


class World:
    def __init__(self, d):
        self.d = d; self.mac = os.path.join(d, "mac"); self.t1 = os.path.join(self.mac, T1_REL)
        self.L = os.path.join(d, "lengau"); self.bin = os.path.join(d, "fakebin"); self.outside = os.path.join(d, "outside")
        self.C = os.path.join(self.L, "rsc_screen_ctl", T1_REL); self.J = os.path.join(self.L, "rsc_screen", T1_REL)
        self.G = os.path.join(self.L, "row19_screen", "gate"); self.A = os.path.join(self.L, "archive_screen", "v15_before_v16")
        self.MA = os.path.join(self.t1, "chpc/results/archive/row19_screen_v15_before_v16")

    # -- the private copy: production bytes with exactly the two tagged lines substituted --
    def install(self, root=None):
        root = root or self.L
        base = os.path.realpath(BASE); real = os.path.realpath(root)
        if not real.startswith(base + os.sep):
            raise Fail("refusing a fake root outside the harness temp dir: %s -> %s" % (root, real))
        if real == PROD_ROOT or real.startswith(PROD_ROOT + "/") or os.path.realpath(PROD_ROOT) == real:
            raise Fail("refusing a fake root that is the production toolchain")
        if not os.path.realpath(self.t1).startswith(base + os.sep):
            raise Fail("refusing a Mac tree outside the harness temp dir")
        dst = os.path.join(self.t1, "chpc", "migration_v16")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        os.makedirs(dst)
        for f in PROD_FILES:
            src = open(os.path.join(HERE, f)).read()
            if f == "remote_lib.sh":
                assert src.count(ROOT_LINE) == 1, "remote_lib.sh must carry exactly one production root line"
                src = src.replace(ROOT_LINE, "T_ROOT=%s   # @root (PRIVATE TEST COPY)" % root)
            if f == "lengau.sh":
                assert src.count(TRANSPORT) == 1, "lengau.sh must carry exactly one production transport"
                src = src.replace(TRANSPORT, "bash -s")
            write(os.path.join(dst, f), src, os.stat(os.path.join(HERE, f)).st_mode & 0o777)
        changed = []
        for f in PROD_FILES:
            a = open(os.path.join(HERE, f)).read().splitlines(); b = open(os.path.join(dst, f)).read().splitlines()
            changed += [(f, x) for x, y in zip(a, b) if x != y]
            if len(a) != len(b):
                raise Fail("private copy of %s changed its line count" % f)
        if sorted(c[0] for c in changed) != ["lengau.sh", "remote_lib.sh"] or len(changed) != 2:
            raise Fail("the private copy differs from production on other lines: %s" % changed)

    def run(self, *cmd, timeout=600):
        env = dict(os.environ); env["PATH"] = self.bin + os.pathsep + env["PATH"]
        for k in list(env):
            if k.startswith("V16_"):
                del env[k]
        r = subprocess.run(list(cmd), cwd=self.t1, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout)
        return r.returncode, r.stdout

    def script(self, name, *args):
        if name.endswith(".py"):
            return self.run("python3", "chpc/migration_v16/" + name, *args)
        return self.run("bash", "chpc/migration_v16/" + name, *args)

    def ctl_state(self):
        return (sh("git", "-C", self.C, "rev-parse", "HEAD").strip(), sh("git", "-C", self.C, "status", "--porcelain"))

    def fake(self, name, data):
        write(os.path.join(self.bin, name), data, 0o755)

    def commit_promotion(self):
        sh("git", "-C", self.mac, "add", *[T1_REL + "/" + p for p in PROMO_PATHS])
        sh("git", "-C", self.mac, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "TEST promote v16 (private world)",
           "--", *[T1_REL + "/" + p for p in PROMO_PATHS])


FAKE_PS = """#!/bin/bash
d=$(cd "$(dirname "$0")" && pwd)
case "${1:-}" in -u) k=u;; *) k=x;; esac
rc=0; [ -f "$d/ps_$k.rc" ] && rc=$(cat "$d/ps_$k.rc")
if [ -f "$d/ps_$k.out" ]; then cat "$d/ps_$k.out"; else echo "bash -s"; fi
exit $rc
"""
FAKE_SHA = """#!/bin/bash
d=$(cd "$(dirname "$0")" && pwd)
if [ -f "$d/sha.fail" ]; then pat=$(cat "$d/sha.fail"); for a in "$@"; do case $a in *"$pat"*) echo "sha256sum: simulated failure" >&2; exit 1;; esac; done; fi
if [ -f "$d/sha.partial" ]; then pat=$(cat "$d/sha.partial"); "%s" "$@" | grep -v -- "$pat"; exit 0; fi
exec "%s" "$@"
""" % (REAL_SHA256SUM, REAL_SHA256SUM)
FAKE_T1PY = """#!/bin/bash
d=$(cd "$(dirname "$0")" && pwd)
if [ -f "$d/t1py.nofcntl" ]; then for a in "$@"; do case $a in *fcntl.flock*) echo "simulated: this python has no usable fcntl" >&2; exit 1;; esac; done; fi
exec python3 "$@"
"""
FAKE_FLOCK = """#!/usr/bin/env python3
import fcntl, subprocess, sys
a = sys.argv[1:]; code = 1; nb = False; mode = fcntl.LOCK_EX
while a and a[0].startswith("-"):
    x = a.pop(0)
    if x == "-n": nb = True
    elif x == "-s": mode = fcntl.LOCK_SH
    elif x == "-E": code = int(a.pop(0))
fh = open(a.pop(0), "rb")
try:
    fcntl.flock(fh.fileno(), mode | (fcntl.LOCK_NB if nb else 0))
except BlockingIOError:
    sys.exit(code)
sys.exit(subprocess.call(a))
"""
BROKEN_FLOCK = "#!/bin/bash\necho 'flock: simulated failure' >&2\nexit 64\n"


def build_fresh(d):
    w = World(d); os.makedirs(d)
    sh("git", "clone", "-q", REPO, w.mac)
    q = os.path.join(LIVE_T1, "chpc/results/row19_screen/receipts/qualified_refit_job1.json")
    qd = os.path.join(w.t1, "chpc/results/row19_screen/receipts/qualified_refit_job1.json")
    write(qd, open(q, "rb").read())
    for sub in ("jobs", "row19_screen/gate", "row19_screen/ec2", "row19_screen/plans", "row19_screen_campaign", "archive_screen"):
        os.makedirs(os.path.join(w.L, sub))
    os.makedirs(w.outside); os.makedirs(w.bin)
    write(os.path.join(w.L, "programme_admission.lock"), ""); write(os.path.join(w.L, "row19_screen/plans/.submit.lock"), "")
    write(os.path.join(w.L, "t1py"), FAKE_T1PY, 0o755)
    sh("git", "clone", "-q", REPO, os.path.join(w.L, "rsc_screen_ctl")); sh("git", "clone", "-q", REPO, os.path.join(w.L, "rsc_screen"))
    write(os.path.join(w.G, "qualified_refit_job1.json"), open(q, "rb").read())
    write(os.path.join(w.G, "review_refit.json"), json.dumps({"schema": "private-test", "role": "refit", "qualification_sha256": QUAL_V15, "max_job_number": 100}) + "\n")
    write(os.path.join(w.G, "watch_refit_1.json"), "{}\n"); write(os.path.join(w.G, "pbs/row19_screen_refit_1.o7600001"), "fake PBS out\n")
    write(os.path.join(w.L, "row19_screen/ec2/activation_e1.json"), "{}\n")
    write(os.path.join(w.L, "jobs/row19_screen_refit_1.pbs"), "#PBS private test\n")
    write(os.path.join(w.L, "row19_screen_campaign/budget.json"), json.dumps({"cap_core_h": 60000.0, "cap_history": []}) + "\n")
    w.fake("ps", FAKE_PS); w.fake("sha256sum", FAKE_SHA)
    return w


STAGES = {}


def stage(name):
    """A fresh private world copied from the cached stage `name` (fresh, archived, promoted, deployed, rolled)."""
    order = ["fresh", "archived", "promoted", "deployed", "rolled"]
    if name not in STAGES:
        d = os.path.join(BASE, "stage_" + name)
        if name == "fresh":
            w = build_fresh(d)
        else:
            prev = stage(order[order.index(name) - 1]); sh("cp", "-cR", prev.d, d); w = World(d)
        w.install()
        if name == "archived":
            rc, out = w.script("archive_v15.sh"); need(rc == 0 and "ARCHIVE OK" in out, "stage archive", out)
        elif name == "promoted":
            rc, out = w.script("promote_v16.py"); need(rc == 0 and "promoted:" in out, "stage promote", out); w.commit_promotion()
        elif name == "deployed":
            rc, out = w.script("deploy_v16.sh"); need(rc == 0 and "DEPLOY OK" in out, "stage deploy", out)
        elif name == "rolled":
            rc, out = w.script("lengau.sh", "rollover_pilot_v16.sh"); need(rc == 0 and "retired to" in out, "stage rollover", out)
        STAGES[name] = w
    n = len(os.listdir(BASE)); d = os.path.join(BASE, "t%03d_%s" % (n, name))
    sh("cp", "-cR", STAGES[name].d, d)
    w = World(d); w.install(); return w


def need(cond, what, out=""):
    if not cond:
        raise Fail("%s\n---- output ----\n%s" % (what, out[-3000:]))


def refused(rc, out, *subs):
    need(rc != 0, "expected a refusal (non-zero exit), got 0", out)
    for s in subs:
        need(s in out, "expected the refusal to say %r" % s, out)


class Holder:
    """A private process holding an exclusive flock(2) on a fake lock file."""
    def __init__(self, path):
        self.p = subprocess.Popen([sys.executable, "-c", "import fcntl, sys, time\nfh = open(sys.argv[1], 'rb')\n"
                                   "fcntl.flock(fh.fileno(), fcntl.LOCK_EX)\nprint('held', flush=True)\ntime.sleep(120)", path],
                                  stdout=subprocess.PIPE, text=True)
        need(self.p.stdout.readline().strip() == "held", "the private lock holder did not start")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.p.send_signal(signal.SIGTERM); self.p.wait()


def relock(path, data):
    os.chmod(path, 0o644); write(path, data); os.chmod(path, 0o444)


# ------------------------------------------------------------------------------------------------ static and boundary (R4)
@test("R4 static: production files carry no test hook, one fixed root, one fixed transport, no worker/reaper stop")
def t_static():
    for f in PROD_FILES:
        s = open(os.path.join(HERE, f)).read()
        if f == "RUNBOOK.md":
            continue
        for bad in ("V16_FAKE_LENGAU", "V16_T", "FAKE_LENGAU"):
            need(bad not in s, "%s still mentions %s" % (f, bad))
        for bad in ("qdel", "pkill", "kill ", "killall", "scp "):
            need(bad not in s, "%s contains %r" % (f, bad))
        if f.endswith(".sh"):
            r = subprocess.run(["bash", "-n", os.path.join(HERE, f)], capture_output=True, text=True); need(r.returncode == 0, "bash -n " + f, r.stderr)
    tags = {f: open(os.path.join(HERE, f)).read().count("@transport") for f in PROD_FILES if f != "RUNBOOK.md"}
    need(sum(tags.values()) == 1 and tags["lengau.sh"] == 1, "exactly one @transport line, in lengau.sh: %s" % tags)
    lt = [l for l in open(os.path.join(HERE, "lengau.sh")).read().splitlines() if "@transport" in l][0]
    need(TRANSPORT in lt, "the transport line is not the fixed production ssh", lt)
    need(open(os.path.join(HERE, "remote_lib.sh")).read().count(ROOT_LINE) == 1, "remote_lib.sh lacks the single fixed root line")
    for f in ("rollover_pilot_v16.sh", "adopt_pilot16.sh"):
        s = open(os.path.join(HERE, f)).read()
        need("/mnt/lustre" not in s, "%s names a toolchain root of its own" % f)


@test("R4 production compose: the unsubstituted Lengau script targets only the production root and parses")
def t_compose():
    r = subprocess.run(["bash", "-c", '. "$1"; compose rollover_pilot_v16.sh', "x", os.path.join(HERE, "lengau.sh")], capture_output=True, text=True)
    need(r.returncode == 0, "compose failed", r.stderr)
    need(ROOT_LINE in r.stdout and r.stdout.count("T_ROOT=") == 1, "the composed script does not carry exactly the production root")
    p = subprocess.run(["bash", "-n"], input=r.stdout, capture_output=True, text=True); need(p.returncode == 0, "composed script does not parse", p.stderr)


@test("R4 a body run without the prelude refuses; lengau.sh refuses any other body")
def t_body_alone():
    w = stage("fresh")
    rc, out = w.run("bash", "chpc/migration_v16/rollover_pilot_v16.sh"); refused(rc, out, "run through")
    rc, out = w.run("bash", "chpc/migration_v16/adopt_pilot16.sh"); refused(rc, out, "run through")
    rc, out = w.script("lengau.sh", "preflight_v16.sh"); refused(rc, out, "runs only")


@test("R4 harness guard: a fake root outside the private temp dir or aliasing the production toolchain is refused")
def t_harness_guard():
    w = stage("fresh")
    alias = os.path.join(w.d, "alias_prod"); os.symlink(PROD_ROOT, alias)
    try:
        w.install(alias); raise Fail("install accepted an alias of the production toolchain")
    except Fail as e:
        need("refusing" in str(e), str(e))
    try:
        w.install(tempfile.gettempdir()); raise Fail("install accepted a root outside the harness")
    except Fail as e:
        need("refusing" in str(e), str(e))


@test("R4 valid isolated fake root reached through an alias: every path resolves beneath its physical root")
def t_alias_root_ok():
    w = stage("fresh"); alias = os.path.join(w.d, "alias_root"); os.symlink(w.L, alias); w.install(alias)
    rc, out = w.script("preflight_v16.sh"); need(rc == 0 and "PREFLIGHT OK" in out, "preflight through a private alias", out)


@test("R4 symlink escape: controller clone pointing outside the fake root refuses (preflight, archive)")
def t_escape_ctl():
    w = stage("fresh"); ctl = os.path.join(w.L, "rsc_screen_ctl"); tgt = os.path.join(w.outside, "rsc_screen_ctl")
    os.rename(ctl, tgt); os.symlink(tgt, ctl); before = tree_digest(w.outside)
    rc, out = w.script("preflight_v16.sh"); refused(rc, out, "resolves outside the toolchain root")
    rc, out = w.script("archive_v15.sh"); refused(rc, out, "resolves outside the toolchain root")
    need(tree_digest(w.outside) == before, "something was written outside the fake root")
    need(not os.path.exists(w.MA), "the Mac archive was written after a Lengau refusal")


@test("R4 symlink escape: gate, archive_screen and a gate member pointing outside refuse")
def t_escape_gate_archive():
    w = stage("fresh"); tgt = os.path.join(w.outside, "gate"); os.rename(w.G, tgt); os.symlink(tgt, w.G)
    rc, out = w.script("archive_v15.sh"); refused(rc, out, "resolves outside")
    w = stage("fresh"); a = os.path.join(w.L, "archive_screen"); tgt = os.path.join(w.outside, "archive_screen")
    os.rmdir(a); os.makedirs(tgt); os.symlink(tgt, a)
    rc, out = w.script("archive_v15.sh"); refused(rc, out, "resolves outside"); need(os.listdir(tgt) == [], "wrote into the outside archive dir")
    w = stage("fresh"); write(os.path.join(w.outside, "x.json"), "{}\n"); os.symlink(os.path.join(w.outside, "x.json"), os.path.join(w.G, "x.json"))
    rc, out = w.script("archive_v15.sh"); refused(rc, out, "symlink")
    need(not os.path.exists(w.A) and not [x for x in os.listdir(os.path.join(w.L, "archive_screen")) if "staging" in x], "a refused build left an archive or staging dir")


@test("R4 symlink escape: adopt_pilot16 with the controller clone outside refuses and writes nothing there")
def t_escape_adopt():
    w = stage("rolled"); ctl = os.path.join(w.L, "rsc_screen_ctl"); tgt = os.path.join(w.outside, "rsc_screen_ctl")
    os.rename(ctl, tgt); os.symlink(tgt, ctl)
    write(os.path.join(w.G, "qualified_refit_job1.json"), "{\"regenerated\": true}\n")
    write(os.path.join(w.t1, "reviews/test_pilot_record.md"), "ADOPT row19-screen-pilot role=refit qualification=x max_job=100\n")
    head = sh("git", "-C", tgt, "rev-parse", "HEAD"); before = tree_digest(tgt)
    rc, out = w.script("lengau.sh", "adopt_pilot16.sh", "--file", "reviews/test_pilot_record.md"); refused(rc, out, "resolves outside")
    need(sh("git", "-C", tgt, "rev-parse", "HEAD") == head and tree_digest(tgt) == before, "the outside clone changed")


# ------------------------------------------------------------------------------------------------ positive route
@test("positive: preflight, archive, promote, deploy, re-runs and rollover in a valid isolated fake root")
def t_positive():
    w = stage("fresh")
    rc, out = w.script("preflight_v16.sh"); need(rc == 0 and "PREFLIGHT OK" in out and "archive sources complete" in out, "preflight", out)
    rc, out = w.script("archive_v15.sh"); need(rc == 0 and "ARCHIVE OK" in out and "archive built" in out, "archive", out)
    need(set(os.listdir(w.A)) == {"COMPLETE", "SHA256SUMS", "INVENTORY.gate", "INVENTORY.jobs", "ctl", "gate", "jobs", "ledger"}, "archive layout")
    need(sorted(os.listdir(w.MA)) == sorted(["COMPLETE", "SHA256SUMS", "qualified_refit_job1.json", "row19_screen_admit.py",
         "row19_screen_budget.json", "row19_screen_controls.json", "row19_screen_controls_adoption.json", "row19_screen_status.py"]), "Mac archive layout")
    rc, out = w.script("archive_v15.sh"); need(rc == 0 and "exists and verifies" in out and "names this Lengau archive" in out, "archive re-run", out)
    rc, out = w.script("promote_v16.py", "--check"); refused(rc, out, "not complete")
    rc, out = w.script("promote_v16.py", "--dry-run"); need(rc == 0 and "DRY RUN" in out, "promote dry run", out)
    rc, out = w.script("promote_v16.py"); need(rc == 0 and "promoted:" in out, "promote", out)
    rc, out = w.script("promote_v16.py"); need(rc == 0 and "already promoted, verified" in out, "promote re-run", out)
    w.commit_promotion()
    jbefore = tree_digest(os.path.join(w.L, "rsc_screen")); jhead = sh("git", "-C", w.J, "rev-parse", "HEAD")
    rc, out = w.script("deploy_v16.sh"); need(rc == 0 and "DEPLOY OK" in out and "science bytes UNCHANGED (8 files" in out and "IDENTICAL" in out, "deploy", out)
    need(tree_digest(os.path.join(w.L, "rsc_screen")) == jbefore and sh("git", "-C", w.J, "rev-parse", "HEAD") == jhead, "the job clone changed")
    rc, out = w.script("deploy_v16.sh"); need(rc == 0 and "already holds exactly these v16 bytes" in out and "DEPLOY OK" in out, "deploy re-run", out)
    rc, out = w.script("lengau.sh", "rollover_pilot_v16.sh"); need(rc == 0 and "retired to" in out, "rollover", out)
    rc, out = w.script("lengau.sh", "rollover_pilot_v16.sh"); refused(rc, out, "retired file exists")


# ------------------------------------------------------------------------------------------------ R1 archives
@test("R1 one-file remote archive (qualification + one-line SHA256SUMS) refuses; it is left exactly as it was")
def t_one_file_archive():
    w = stage("fresh"); write(os.path.join(w.A, "gate/qualified_refit_job1.json"), open(os.path.join(w.G, "qualified_refit_job1.json"), "rb").read())
    write(os.path.join(w.A, "SHA256SUMS"), "%s  ./gate/qualified_refit_job1.json\n" % QUAL_V15); before = tree_digest(w.A)
    rc, out = w.script("archive_v15.sh"); refused(rc, out, "does not verify as complete")
    need(tree_digest(w.A) == before and not os.path.exists(w.MA), "the partial archive changed, or the Mac half ran")


@test("R1 one-file remote archive before deploy: deploy refuses before any controller change")
def t_one_file_archive_deploy():
    w = stage("promoted"); unlock_tree(w.A); shutil.rmtree(w.A)
    write(os.path.join(w.A, "gate/qualified_refit_job1.json"), open(os.path.join(w.G, "qualified_refit_job1.json"), "rb").read())
    write(os.path.join(w.A, "SHA256SUMS"), "%s  ./gate/qualified_refit_job1.json\n" % QUAL_V15); s0 = w.ctl_state()
    rc, out = w.script("deploy_v16.sh"); refused(rc, out, "does not verify as complete"); need(w.ctl_state() == s0, "the controller clone changed")


@test("R1 missing campaign ledger refuses the archive; nothing is published")
def t_missing_ledger():
    w = stage("fresh"); os.remove(os.path.join(w.L, "row19_screen_campaign/budget.json"))
    rc, out = w.script("archive_v15.sh"); refused(rc, out, "missing")
    need(not os.path.exists(w.A) and not os.path.exists(w.MA), "an archive was published")


@test("R1 missing budget phases / controller file (committed away in a clean clone) refuses the archive")
def t_missing_ctl_files():
    for f in ("chpc/row19_screen_budget.json", "chpc/row22_bank_submit.py", "chpc/row19_screen_verify.py"):
        w = stage("fresh"); sh("git", "-C", w.C, "rm", "-q", f); sh("git", "-C", w.C, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x")
        rc, out = w.script("archive_v15.sh"); refused(rc, out, "missing")
        need(not os.path.exists(w.A) and not os.path.exists(w.MA), "an archive was published without " + f)
        rc, out = w.script("preflight_v16.sh"); refused(rc, out)


@test("R1 missing gate review / no job scripts refuse the archive")
def t_missing_gate_jobs():
    w = stage("fresh"); os.remove(os.path.join(w.G, "review_refit.json")); rc, out = w.script("archive_v15.sh"); refused(rc, out, "review_refit.json")
    w = stage("fresh"); os.remove(os.path.join(w.L, "jobs/row19_screen_refit_1.pbs")); rc, out = w.script("archive_v15.sh"); refused(rc, out, "no refit job scripts")
    need(not os.path.exists(w.A), "published without job scripts")


@test("R1 failed checksum command / unreadable source refuse the archive; nothing published, no staging left")
def t_failed_checksum():
    w = stage("fresh"); write(os.path.join(w.bin, "sha.fail"), "qualified_refit_job1"); rc, out = w.script("archive_v15.sh"); refused(rc, out, "cannot hash")
    need(not os.path.exists(w.A), "published after a failed checksum command")
    w = stage("fresh"); os.chmod(os.path.join(w.G, "watch_refit_1.json"), 0)
    rc, out = w.script("archive_v15.sh"); refused(rc, out, "unreadable")
    need(not os.path.exists(w.A) and not [x for x in os.listdir(os.path.join(w.L, "archive_screen")) if "staging" in x], "published or left staging")
    os.chmod(os.path.join(w.G, "watch_refit_1.json"), 0o644)


@test("R1 interrupted build (staging left) refuses archive and preflight and is never removed")
def t_interrupted():
    w = stage("fresh"); stg = os.path.join(w.L, "archive_screen/.v15_before_v16.staging.4242"); write(os.path.join(stg, "gate/x"), "partial\n")
    before = tree_digest(stg)
    rc, out = w.script("archive_v15.sh"); refused(rc, out, "interrupted archive build")
    rc, out = w.script("preflight_v16.sh"); refused(rc, out, "interrupted archive build")
    need(tree_digest(stg) == before and not os.path.exists(w.A), "the staging evidence changed or an archive was published")


@test("R1 Lengau archive rewritten self-consistently without its ledger / a controller file refuses (inventory)")
def t_self_consistent_subset():
    sys.path.insert(0, HERE); import lengau_archive as LA
    for drop in ("ledger", "ctl/chpc/row22_bank_submit.py"):
        w = stage("archived"); unlock_tree(w.A); p = os.path.join(w.A, drop)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
        sums = {}
        for d, _, files in os.walk(w.A):
            for n in files:
                rel = os.path.relpath(os.path.join(d, n), w.A)
                if rel not in ("SHA256SUMS", "COMPLETE"):
                    sums[rel] = hashlib.sha256(open(os.path.join(d, n), "rb").read()).hexdigest()
        sb = LA.sums_text(sums).encode(); write(os.path.join(w.A, "SHA256SUMS"), sb)
        c = open(os.path.join(w.A, "COMPLETE")).read().splitlines()
        write(os.path.join(w.A, "COMPLETE"), "\n".join([c[0], "sha256sums " + hashlib.sha256(sb).hexdigest()] + c[2:]) + "\n")
        for d, _, files in os.walk(w.A):
            for n in files:
                os.chmod(os.path.join(d, n), 0o444)
        rc, out = w.script("archive_v15.sh"); refused(rc, out, "does not verify as complete")


@test("R1 Lengau archive corrupted between creation and deploy: byte flip, extra file, missing COMPLETE, writable file")
def t_corrupt_before_deploy():
    def flip(w):
        p = os.path.join(w.A, "gate/review_refit.json"); os.chmod(p, 0o644); open(p, "a").write(" "); os.chmod(p, 0o444)
    def extra(w):
        os.chmod(os.path.join(w.A, "gate"), 0o755); write(os.path.join(w.A, "gate/extra.json"), "{}\n", 0o444)
    def nocomplete(w):
        os.chmod(w.A, 0o755); os.remove(os.path.join(w.A, "COMPLETE"))
    def writable(w):
        os.chmod(os.path.join(w.A, "ledger/row19_screen_campaign_budget.json"), 0o644)
    for mut in (flip, extra, nocomplete, writable):
        w = stage("promoted"); mut(w); s0 = w.ctl_state()
        rc, out = w.script("deploy_v16.sh"); refused(rc, out, "does not verify as complete")
        need(w.ctl_state() == s0, "the controller clone changed after %s" % mut.__name__)


@test("R1 Lengau archive fully regenerated (a gate receipt dropped, INVENTORY+SUMS+COMPLETE rewritten): deploy refuses, it is not the archive the Mac names")
def t_regenerated_archive():
    sys.path.insert(0, HERE); import lengau_archive as LA
    w = stage("promoted"); unlock_tree(w.A); os.remove(os.path.join(w.A, "gate/watch_refit_1.json"))
    inv = {}
    for l in open(os.path.join(w.A, "INVENTORY.gate")).read().splitlines():
        h, p = l.split("  ./"); inv[p] = h
    del inv["gate/watch_refit_1.json"]; write(os.path.join(w.A, "INVENTORY.gate"), LA.sums_text(inv))
    sums = {}
    for d, _, files in os.walk(w.A):
        for n in files:
            rel = os.path.relpath(os.path.join(d, n), w.A)
            if rel not in ("SHA256SUMS", "COMPLETE"):
                sums[rel] = hashlib.sha256(open(os.path.join(d, n), "rb").read()).hexdigest()
    sb = LA.sums_text(sums).encode(); write(os.path.join(w.A, "SHA256SUMS"), sb)
    c = open(os.path.join(w.A, "COMPLETE")).read().splitlines()
    write(os.path.join(w.A, "COMPLETE"), "\n".join([c[0], "sha256sums " + hashlib.sha256(sb).hexdigest()] + c[2:]) + "\n")
    for d, _, files in os.walk(w.A):
        for n in files:
            os.chmod(os.path.join(d, n), 0o444)
    s0 = w.ctl_state(); rc, out = w.script("deploy_v16.sh"); refused(rc, out, "is not the one the Mac archive names")
    need(w.ctl_state() == s0, "the controller clone changed")


@test("R1 substituted Mac sixth file (budget replaced, SHA256SUMS + COMPLETE self-consistent) refuses promote and archive re-run")
def t_mac_substituted():
    w = stage("archived"); os.chmod(w.MA, 0o755)
    for n in os.listdir(w.MA):
        os.chmod(os.path.join(w.MA, n), 0o644)
    os.remove(os.path.join(w.MA, "row19_screen_budget.json")); write(os.path.join(w.MA, "notes.json"), "{}\n")
    sums = {n: hashlib.sha256(open(os.path.join(w.MA, n), "rb").read()).hexdigest() for n in os.listdir(w.MA) if n not in ("SHA256SUMS", "COMPLETE")}
    sb = "".join("%s  %s\n" % (sums[k], k) for k in sorted(sums)).encode(); write(os.path.join(w.MA, "SHA256SUMS"), sb)
    c = open(os.path.join(w.MA, "COMPLETE")).read().splitlines()
    write(os.path.join(w.MA, "COMPLETE"), "\n".join([c[0], "sha256sums " + hashlib.sha256(sb).hexdigest(), "budget " + sums["notes.json"], c[3]]) + "\n")
    rc, out = w.script("promote_v16.py", "--dry-run"); refused(rc, out, "not exactly the six named files")
    rc, out = w.script("archive_v15.sh"); refused(rc, out, "does not verify")


@test("R1 Mac archive missing COMPLETE / a corrupted byte / a leftover staging dir refuses promote")
def t_mac_incomplete():
    w = stage("archived"); os.chmod(w.MA, 0o755); os.remove(os.path.join(w.MA, "COMPLETE"))
    rc, out = w.script("promote_v16.py", "--dry-run"); refused(rc, out, "COMPLETE")
    w = stage("archived"); p = os.path.join(w.MA, "row19_screen_budget.json"); os.chmod(p, 0o644); open(p, "a").write(" ")
    rc, out = w.script("promote_v16.py", "--dry-run"); refused(rc, out, "does not match SHA256SUMS")
    w = stage("archived"); os.makedirs(os.path.join(w.t1, "chpc/results/archive/.row19_screen_v15_before_v16.staging.7"))
    rc, out = w.script("promote_v16.py", "--dry-run"); refused(rc, out, "interrupted Mac archive build")


@test("P3 completed-promotion fast path validates in full: a corrupted Mac archive or a substituted adoption refuses")
def t_fast_path():
    w = stage("promoted"); rc, out = w.script("promote_v16.py"); need(rc == 0 and "already promoted, verified" in out, "fast path", out)
    rc, out = w.script("promote_v16.py", "--check"); need(rc == 0, "--check on a complete promotion", out)
    p = os.path.join(w.MA, "row19_screen_status.py"); os.chmod(p, 0o644); open(p, "a").write("# x\n")
    rc, out = w.script("promote_v16.py"); refused(rc, out, "does not match SHA256SUMS")
    rc, out = w.script("deploy_v16.sh", "--dry-run"); refused(rc, out, "promote_v16.py --check")
    w = stage("promoted"); p = os.path.join(w.t1, "chpc/row19_screen_controls_adoption.json"); a = json.load(open(p)); a["by"] = "someone else"
    write(p, json.dumps(a, indent=1) + "\n"); rc, out = w.script("promote_v16.py"); refused(rc, out, "exact version-16 record")


@test("R1 rollover retires only against the complete archive: a changed active review or a corrupted archive refuses, nothing moves")
def t_rollover_archive():
    w = stage("deployed"); open(os.path.join(w.G, "review_refit.json"), "a").write(" ")
    rc, out = w.script("lengau.sh", "rollover_pilot_v16.sh"); refused(rc, out, "MISMATCH")
    need(os.path.exists(os.path.join(w.G, "review_refit.json")), "the review moved")
    w = stage("deployed"); p = os.path.join(w.A, "ctl/HEAD.txt"); os.chmod(p, 0o644); write(p, "0" * 40 + "\n"); os.chmod(p, 0o444)
    rc, out = w.script("lengau.sh", "rollover_pilot_v16.sh"); refused(rc, out, "does not verify as complete")
    need(os.path.exists(os.path.join(w.G, "review_refit.json")), "the review moved")


# ------------------------------------------------------------------------------------------------ R2 drain observations
@test("R2 process-inventory failure (ps exits 23, no output) refuses: Lengau archive, deploy, rollover; Mac preflight")
def t_ps_fail():
    w = stage("fresh"); write(os.path.join(w.bin, "ps_u.rc"), "23"); write(os.path.join(w.bin, "ps_u.out"), "")
    rc, out = w.script("archive_v15.sh"); refused(rc, out, "process inventory failed (ps exited 23)"); need(not os.path.exists(w.A), "archived")
    w = stage("promoted"); write(os.path.join(w.bin, "ps_u.rc"), "23"); write(os.path.join(w.bin, "ps_u.out"), ""); s0 = w.ctl_state()
    rc, out = w.script("deploy_v16.sh"); refused(rc, out, "process inventory failed"); need(w.ctl_state() == s0, "controller changed")
    w = stage("deployed"); write(os.path.join(w.bin, "ps_u.rc"), "23"); write(os.path.join(w.bin, "ps_u.out"), "")
    rc, out = w.script("lengau.sh", "rollover_pilot_v16.sh"); refused(rc, out, "process inventory failed"); need(os.path.exists(os.path.join(w.G, "review_refit.json")), "retired")
    w = stage("fresh"); write(os.path.join(w.bin, "ps_x.rc"), "1"); rc, out = w.script("preflight_v16.sh"); refused(rc, out, "Mac process inventory failed")


@test("R2 empty process inventory with exit 0 refuses; a matching controller process refuses")
def t_ps_empty_busy():
    w = stage("fresh"); write(os.path.join(w.bin, "ps_u.out"), ""); rc, out = w.script("preflight_v16.sh"); refused(rc, out, "process inventory is empty")
    w = stage("fresh"); write(os.path.join(w.bin, "ps_u.out"), "bash -s\n/x/t1py chpc/row19_screen_status.py --role refit\n")
    rc, out = w.script("archive_v15.sh"); refused(rc, out, "a controller command runs")
    w = stage("fresh"); write(os.path.join(w.bin, "ps_x.out"), "bash refill_r1.sh\n"); rc, out = w.script("preflight_v16.sh"); refused(rc, out, "runs on the Mac")


@test("R2 unavailable lock probe refuses: no flock(1) and no usable python fcntl; broken flock(1) and no python fcntl; missing lock file")
def t_probe_unavailable():
    w = stage("fresh"); write(os.path.join(w.L, "t1py.nofcntl"), ""); rc, out = w.script("preflight_v16.sh"); refused(rc, out, "no reliable lock probe")
    w = stage("fresh"); write(os.path.join(w.L, "t1py.nofcntl"), ""); w.fake("flock", BROKEN_FLOCK)
    rc, out = w.script("archive_v15.sh"); refused(rc, out, "no reliable lock probe"); need(not os.path.exists(w.A), "archived without a lock probe")
    w = stage("fresh"); os.remove(os.path.join(w.L, "row19_screen/plans/.submit.lock")); rc, out = w.script("preflight_v16.sh"); refused(rc, out, "cannot be probed")


@test("R2 an actually held lock refuses (python fcntl probe and flock(1) probe; both lock files)")
def t_lock_held():
    for lock in ("programme_admission.lock", "row19_screen/plans/.submit.lock"):
        for with_flock in (False, True):
            w = stage("fresh")
            if with_flock:
                w.fake("flock", FAKE_FLOCK)
            with Holder(os.path.join(w.L, lock)):
                rc, out = w.script("archive_v15.sh")
            refused(rc, out, "lock held"); need(not os.path.exists(w.A), "archived under a held lock")
    w = stage("promoted"); s0 = w.ctl_state()
    with Holder(os.path.join(w.L, "programme_admission.lock")):
        rc, out = w.script("deploy_v16.sh")
    refused(rc, out, "lock held"); need(w.ctl_state() == s0, "deployed under a held lock")
    w = stage("fresh"); w.fake("flock", FAKE_FLOCK); rc, out = w.script("preflight_v16.sh"); need(rc == 0, "flock(1) probe of free locks", out)


@test("R2 failed git status observation refuses (not read as clean)")
def t_git_status_fail():
    w = stage("fresh"); idx = os.path.join(w.L, "rsc_screen_ctl/.git/index"); write(idx, b"garbage, not an index")
    rc, out = w.script("preflight_v16.sh"); refused(rc, out, "git status failed")
    rc, out = w.script("archive_v15.sh"); refused(rc, out, "git status failed")


# ------------------------------------------------------------------------------------------------ R3 job-clone science proof
@test("R3 missing / unreadable science input refuses deploy before any controller change")
def t_sci_missing():
    w = stage("promoted"); os.remove(os.path.join(w.J, "analyze.py")); s0 = w.ctl_state()
    rc, out = w.script("deploy_v16.sh"); refused(rc, out, "science input missing or unreadable: analyze.py", "nothing was changed"); need(w.ctl_state() == s0, "changed")
    w = stage("promoted"); os.chmod(os.path.join(w.J, "models.py"), 0); s0 = w.ctl_state()
    rc, out = w.script("deploy_v16.sh"); os.chmod(os.path.join(w.J, "models.py"), 0o644)
    refused(rc, out, "missing or unreadable: models.py"); need(w.ctl_state() == s0, "changed")
    w = stage("fresh"); os.remove(os.path.join(w.J, "simulate.py")); rc, out = w.script("preflight_v16.sh"); refused(rc, out, "science")


@test("R3 science digest-command failure and partial digest output refuse deploy before any controller change")
def t_sci_digest():
    w = stage("promoted"); write(os.path.join(w.bin, "sha.fail"), "simulate.py"); s0 = w.ctl_state()
    rc, out = w.script("deploy_v16.sh"); refused(rc, out, "science digest command failed"); need(w.ctl_state() == s0, "changed")
    w = stage("promoted"); write(os.path.join(w.bin, "sha.partial"), "row19_slice.py"); s0 = w.ctl_state()
    rc, out = w.script("deploy_v16.sh"); refused(rc, out, "incomplete or malformed"); need(w.ctl_state() == s0, "changed")


@test("R3 science bytes changed or after-proof incomplete during the deployment refuse completion")
def t_sci_after():
    for hook, msg in (('echo "# drift" >> "%s/analyze.py"', "science bytes changed"), ('rm -f "%s/simulate.py"', "after-proof is incomplete")):
        w = stage("promoted"); hp = os.path.join(w.L, "rsc_screen_ctl/.git/hooks/post-commit")
        write(hp, "#!/bin/bash\n" + hook % w.J + "\n", 0o755)
        rc, out = w.script("deploy_v16.sh"); refused(rc, out, msg); need("DEPLOY OK" not in out, "deploy reported OK")


def main(argv):
    global BASE
    keep = "--keep" in argv; sel = argv[argv.index("-k") + 1] if "-k" in argv else ""
    scratch = os.environ.get("V16_TEST_TMP") or tempfile.gettempdir()
    BASE = os.path.realpath(tempfile.mkdtemp(prefix="v16_migration_test_", dir=scratch))
    print("private test root", BASE)
    ok = 0; bad = []
    t0 = time.time()
    try:
        for name, fn in TESTS:
            if sel and sel not in name:
                continue
            t = time.time()
            try:
                fn(); ok += 1; print("PASS  %-110s %5.1fs" % (name[:110], time.time() - t))
            except (Fail, AssertionError) as e:
                bad.append(name); print("FAIL  %s\n      %s" % (name, str(e).replace("\n", "\n      ")))
    finally:
        if not keep:
            unlock_tree(BASE); shutil.rmtree(BASE, ignore_errors=True)
    print("%d passed, %d failed (%.0f s)%s" % (ok, len(bad), time.time() - t0, "" if not keep else "; kept " + BASE))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
