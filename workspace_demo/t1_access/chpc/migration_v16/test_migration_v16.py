#!/usr/bin/env python3
"""Private-copy tests for the migration_v16 scripts (Codex review 2026-10-17 R1-R4 and the P3 fast path; Codex re-review
2026-10-17: P2 nested containment and P2 deploy-retry proof; Lengau tool compatibility after the live preflight refused on
`git -C`, 17 Oct 2026).

    python3 chpc/migration_v16/test_migration_v16.py [-k <substring>] [--keep]      (from anywhere)

The production scripts carry NO test hook. This harness builds a throwaway world under a fresh private temp directory:
a local git clone of the repository as the "Mac" tree, a fake Lengau toolchain root (two more local clones as the controller
and job clones, a gate, locks, a ledger, job scripts) and a fake-tool bin directory (ps, sha256sum, optionally flock). It then
COPIES the production files into the clone's chpc/migration_v16/ and substitutes exactly two tagged lines in that private copy:
the `# @root` toolchain root in remote_lib.sh (-> the fake root) and the `# @transport` ssh in lengau.sh (-> a local `bash -s`).
It refuses a fake root that is not beneath its own temp directory or that resolves to the production toolchain, and checks the
private copy differs from production on those two lines only. Nothing here runs ssh/scp, touches Lengau or the live tree, or
writes outside the temp directory (removed at the end unless --keep).

LENGAU TOOL EMULATION: the private `# @transport` substitution runs the Lengau half with a private `lengaubin/` first on PATH.
Its `git` emulates Lengau's git 1.8.3.1 for the options this code could reach for - it REJECTS `git -C` exactly as 1.8.3 does
("Unknown option: -C", exit 129), echoes `rev-parse --absolute-git-dir` back as a literal (1.8.3 prints an unknown flag and
exits 0) and rejects later options (`--path-format`, `--porcelain=v2`, `--show-superproject-working-tree`, ...); every call
is logged and every rejection recorded. The fake `flock` emulates util-linux 2.23.2 (no -E/--conflict-exit-code: exit 64;
a -n conflict exits 1). Every Lengau-side Python source is checked statically against Python 3.6 (t_py36)."""
import ast, re
import hashlib, json, os, shlex, shutil, signal, stat, subprocess, sys, tempfile, time

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
REAL_GIT = shutil.which("git") or "/usr/bin/git"
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
        self.lbin = os.path.join(d, "lengaubin")      # Lengau-side tool emulation (git 1.8.3), first on the Lengau half's PATH
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
                src = src.replace(TRANSPORT, 'PATH=%s:"$PATH" bash -s' % shlex.quote(self.lbin))
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
# util-linux 2.23.2 flock(1) as on Lengau: no -E/--conflict-exit-code (added in 2.25) - a usage error, exit 64; a -n conflict exits 1
import fcntl, subprocess, sys
a = sys.argv[1:]; nb = False; mode = fcntl.LOCK_EX
while a and a[0].startswith("-"):
    x = a.pop(0)
    if x in ("-n", "--nb", "--nonblock"): nb = True
    elif x in ("-s", "--shared"): mode = fcntl.LOCK_SH
    elif x in ("-x", "-e", "--exclusive"): mode = fcntl.LOCK_EX
    else:
        sys.stderr.write("flock: invalid option -- '%s'\\n" % x.lstrip("-")); sys.exit(64)
fh = open(a.pop(0), "rb")
try:
    fcntl.flock(fh.fileno(), mode | (fcntl.LOCK_NB if nb else 0))
except BlockingIOError:
    sys.exit(1)
sys.exit(subprocess.call(a))
"""
LENGAU_GIT = """#!/bin/bash
# git 1.8.3.1 as on Lengau (private test shim): every call logged; the options 1.8.3 lacks rejected (or, for rev-parse, echoed)
d=$(cd "$(dirname "$0")" && pwd)
printf '%%s\\n' "$*" >> "$d/git.log"
reject() { printf '%%s\\n' "$*" >> "$d/git.rejected"; echo "$1" >&2; exit 129; }
a=("$@"); i=0
while [ $i -lt ${#a[@]} ]; do                       # global options before the subcommand
  case ${a[$i]} in
    -C) reject "Unknown option: -C" "$*";;
    --no-optional-locks|--literal-pathspecs|--glob-pathspecs|--noglob-pathspecs|--icase-pathspecs|--super-prefix*|--config-env*) reject "Unknown option: ${a[$i]}" "$*";;
    -c) i=$((i + 2));;
    -*) i=$((i + 1));;
    *) break;;
  esac
done
sub=${a[$i]:-}
for x in "${a[@]:$((i + 1))}"; do
  case $sub:$x in
    rev-parse:--absolute-git-dir) printf '%%s\\n' "$x" >> "$d/git.rejected"; echo "$x"; exit 0;;   # 1.8.3 echoes an unknown flag
    rev-parse:--path-format*|rev-parse:--show-superproject-working-tree|rev-parse:--show-object-format*|rev-parse:--end-of-options) reject "unsupported in git 1.8.3: $x" "$*";;
    status:--porcelain=*|status:--ahead-behind|status:--no-ahead-behind|*:--end-of-options) reject "unsupported in git 1.8.3: $x" "$*";;
  esac
done
exec "%s" "$@"
""" % REAL_GIT
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
    write(os.path.join(w.lbin, "git"), LENGAU_GIT, 0o755)
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
    rc, out = w.script("preflight_v16.sh"); refused(rc, out, "not its own physical path")
    rc, out = w.script("archive_v15.sh"); refused(rc, out, "not its own physical path")
    need(tree_digest(w.outside) == before, "something was written outside the fake root")
    need(not os.path.exists(w.MA), "the Mac archive was written after a Lengau refusal")


@test("R4 symlink escape: gate, archive_screen and a gate member pointing outside refuse")
def t_escape_gate_archive():
    w = stage("fresh"); tgt = os.path.join(w.outside, "gate"); os.rename(w.G, tgt); os.symlink(tgt, w.G)
    rc, out = w.script("archive_v15.sh"); refused(rc, out, "not its own physical path")
    w = stage("fresh"); a = os.path.join(w.L, "archive_screen"); tgt = os.path.join(w.outside, "archive_screen")
    os.rmdir(a); os.makedirs(tgt); os.symlink(tgt, a)
    rc, out = w.script("archive_v15.sh"); refused(rc, out, "not its own physical path"); need(os.listdir(tgt) == [], "wrote into the outside archive dir")
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
    rc, out = w.script("lengau.sh", "adopt_pilot16.sh", "--file", "reviews/test_pilot_record.md"); refused(rc, out, "not its own physical path")
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
            if with_flock:
                need("trying the python fcntl probe" not in out, "the 2.23 flock(1) probe did not decide a held lock itself", out)
    w = stage("promoted"); s0 = w.ctl_state()
    with Holder(os.path.join(w.L, "programme_admission.lock")):
        rc, out = w.script("deploy_v16.sh")
    refused(rc, out, "lock held"); need(w.ctl_state() == s0, "deployed under a held lock")
    w = stage("fresh"); w.fake("flock", FAKE_FLOCK); rc, out = w.script("preflight_v16.sh"); need(rc == 0, "flock(1) probe of free locks", out)
    need("trying the python fcntl probe" not in out, "the 2.23 flock(1) probe did not decide free locks itself", out)


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


# ------------------------------------------------------------------------------------------------ re-review P2: deploy retry proof
def proof_dir(w):
    return os.path.join(w.L, "archive_screen", "v16_deploy_proof")


@test("P2 retry: after the missing-simulate.py and changed-analyze.py post-commit fixtures a re-run HOLDS, never DEPLOY OK; science not rewritten")
def t_retry_after_failed_proof():
    for hook, msg in (('echo "# drift" >> "%s/analyze.py"', "science bytes changed"), ('rm -f "%s/simulate.py"', "after-proof is incomplete")):
        w = stage("promoted"); hp = os.path.join(w.L, "rsc_screen_ctl/.git/hooks/post-commit")
        write(hp, "#!/bin/bash\n" + hook % w.J + "\n", 0o755)
        rc, out = w.script("deploy_v16.sh"); refused(rc, out, msg); need("DEPLOY OK" not in out, "deploy reported OK", out)
        pd = proof_dir(w); names = os.listdir(pd)
        need("intent" in names and "science_before.sha256" in names and "DONE" not in names, "the pre-mutation proof is not kept as it should be: %s" % names)
        need([n for n in names if n.startswith("after_failed.")], "the failed after-proof was not kept as evidence: %s" % names)
        jd = tree_digest(os.path.join(w.L, "rsc_screen")); pdd = tree_digest(pd)
        for _ in range(2):
            rc, out = w.script("deploy_v16.sh")
            refused(rc, out, "already holds exactly these v16 bytes", "DEPLOY HELD", "after-proof is unresolved"); need("DEPLOY OK" not in out, "a re-run reported DEPLOY OK", out)
        need(tree_digest(os.path.join(w.L, "rsc_screen")) == jd, "a re-run changed the scientific clone")
        need(tree_digest(pd) == pdd, "a re-run changed the kept proof evidence")
        if "simulate" in hook:
            need(not os.path.exists(os.path.join(w.J, "simulate.py")), "the scientific clone was rewritten (simulate.py recreated)")


@test("P2 retry: a deployed clone without its proof, or whose science changed after DONE, HOLDS; with DONE and equal science it reports OK")
def t_retry_proof_binding():
    w = stage("deployed"); rc, out = w.script("deploy_v16.sh")
    need(rc == 0 and "current manifest equals the preserved pre-mutation manifest" in out and "DEPLOY OK" in out, "re-run with DONE", out)
    w = stage("deployed"); unlock_tree(proof_dir(w)); shutil.rmtree(proof_dir(w))
    rc, out = w.script("deploy_v16.sh"); refused(rc, out, "DEPLOY HELD", "no deploy proof"); need("DEPLOY OK" not in out, "OK without a proof", out)
    w = stage("deployed"); open(os.path.join(w.J, "analyze.py"), "a").write("# later drift\n")
    rc, out = w.script("deploy_v16.sh"); refused(rc, out, "DEPLOY HELD", "differ from the preserved pre-mutation manifest"); need("DEPLOY OK" not in out, "OK", out)
    w = stage("deployed"); os.remove(os.path.join(w.J, "simulate.py"))
    rc, out = w.script("deploy_v16.sh"); refused(rc, out, "DEPLOY HELD", "current science proof is incomplete"); need("DEPLOY OK" not in out, "OK", out)
    w = stage("deployed"); pd = proof_dir(w); os.chmod(pd, 0o755); p = os.path.join(pd, "science_before.sha256"); os.chmod(p, 0o644)
    open(p, "a").write("0" * 64 + "  extra\n"); os.chmod(p, 0o444)
    rc, out = w.script("deploy_v16.sh"); refused(rc, out, "DEPLOY HELD", "not the one its intent record certifies")


@test("P2 retry: an attempt that wrote its pre-mutation proof but changed nothing (copy failed) resumes on the same proof")
def t_retry_reuse_intent():
    w = stage("promoted"); s0 = w.ctl_state()
    w.fake("cp", '#!/bin/bash\nfor a in "$@"; do case $a in *.v16tmp) echo "cp: simulated failure" >&2; exit 1;; esac; done\nexec /bin/cp "$@"\n')
    rc, out = w.script("deploy_v16.sh"); refused(rc, out, "copy of"); need(w.ctl_state() == s0, "the controller clone changed", out)
    need(sorted(os.listdir(proof_dir(w))) == ["intent", "science_before.sha256"], "the pre-mutation proof is not exactly intent + manifest")
    os.remove(os.path.join(w.bin, "cp"))
    rc, out = w.script("deploy_v16.sh"); need(rc == 0 and "reusing the pre-mutation proof" in out and "DEPLOY OK" in out, "resume", out)
    rc, out = w.script("deploy_v16.sh"); need(rc == 0 and "already holds exactly these v16 bytes" in out and "DEPLOY OK" in out, "re-run after resume", out)


# ------------------------------------------------------------------------------------------------ re-review P2: nested containment
def commit_redirect(w, rel, target):
    """In the controller clone, replace directory `rel` by a COMMITTED symlink to `target` (holding the same files): a clean tree."""
    src = os.path.join(w.C, rel)
    if not os.path.exists(target):
        shutil.copytree(src, target, symlinks=True)
    shutil.rmtree(src); os.symlink(target, src)
    sh("git", "-C", w.C, "add", "-A", "--", rel)
    sh("git", "-C", w.C, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "TEST redirect " + rel)
    need(sh("git", "-C", w.C, "status", "--porcelain") == "", "the redirect left the controller clone dirty")


def pilot_record(w):
    write(os.path.join(w.G, "qualified_refit_job1.json"), "{\"regenerated\": true}\n")
    write(os.path.join(w.t1, "reviews/test_pilot_record.md"), "ADOPT row19-screen-pilot role=refit qualification=x max_job=100\n")


@test("P2 nested reviews parent redirected outside the root (committed, clean): adopt and deploy refuse before any copy")
def t_nested_reviews():
    w = stage("rolled"); tgt = os.path.join(w.outside, "ctl_reviews"); commit_redirect(w, "reviews", tgt); pilot_record(w)
    before = tree_digest(w.outside); s0 = w.ctl_state()
    rc, out = w.script("lengau.sh", "adopt_pilot16.sh", "--file", "reviews/test_pilot_record.md"); refused(rc, out, "not its own physical path")
    need(tree_digest(w.outside) == before and not os.path.exists(os.path.join(tgt, "test_pilot_record.md")), "the record was written outside")
    need(w.ctl_state() == s0 and not os.path.lexists(os.path.join(w.G, "review_refit.json")), "the controller clone or the gate changed")
    w = stage("promoted"); tgt = os.path.join(w.outside, "ctl_reviews"); commit_redirect(w, "reviews", tgt)
    before = tree_digest(w.outside); s0 = w.ctl_state()
    rc, out = w.script("deploy_v16.sh"); refused(rc, out, "not its own physical path", "payload 6 destination")
    need(tree_digest(w.outside) == before and w.ctl_state() == s0 and not os.path.lexists(proof_dir(w)), "deploy wrote before refusing")


@test("P2 nested chpc / payload destination and temporary sibling redirected: deploy and archive refuse before any copy")
def t_nested_chpc():
    w = stage("promoted"); tgt = os.path.join(w.outside, "ctl_chpc"); commit_redirect(w, "chpc", tgt)
    before = tree_digest(w.outside); s0 = w.ctl_state()
    rc, out = w.script("deploy_v16.sh"); refused(rc, out, "not its own physical path", "payload 1 destination")
    need(tree_digest(w.outside) == before and w.ctl_state() == s0 and not os.path.lexists(proof_dir(w)), "deploy wrote before refusing")
    w = stage("fresh"); tgt = os.path.join(w.outside, "ctl_chpc"); commit_redirect(w, "chpc", tgt); before = tree_digest(w.outside)
    rc, out = w.script("archive_v15.sh"); refused(rc, out, "not its own physical path")
    need(tree_digest(w.outside) == before and not os.path.lexists(w.A) and not os.path.exists(w.MA), "archive wrote before refusing")
    rc, out = w.script("preflight_v16.sh"); refused(rc, out, "not its own physical path")
    # an ignored, untracked temporary sibling that is a symlink to an outside file: the tree is clean, the copy would follow it
    w = stage("promoted"); victim = os.path.join(w.outside, "victim.py"); write(victim, "outside bytes\n")
    write(os.path.join(w.C, "..", "..", ".git", "info", "exclude"), "*.v16tmp\n")
    os.symlink(victim, os.path.join(w.C, "chpc/row19_screen_status.py.v16tmp"))
    need(sh("git", "-C", w.C, "status", "--porcelain") == "", "the sibling fixture is not clean")
    before = tree_digest(w.outside); s0 = w.ctl_state()
    rc, out = w.script("deploy_v16.sh"); refused(rc, out, "temporary sibling")
    need(tree_digest(w.outside) == before and open(victim).read() == "outside bytes\n" and w.ctl_state() == s0, "the sibling was followed")
    need(not os.path.lexists(proof_dir(w)), "a proof was written before the containment refusal")


@test("P2 a controller alias resolving inside the scientific clone refuses every body; scientific bytes unchanged")
def t_ctl_alias_science():
    def alias_whole(w):
        os.rename(os.path.join(w.L, "rsc_screen_ctl"), os.path.join(w.L, "ctl_moved_aside"))
        os.symlink(os.path.join(w.L, "rsc_screen"), os.path.join(w.L, "rsc_screen_ctl"))
    def alias_chpc(w):
        commit_redirect(w, "chpc", os.path.join(w.J, "chpc"))
    for name, mut, runs in (("fresh", alias_whole, [("preflight_v16.sh",), ("archive_v15.sh",)]),
                            ("promoted", alias_whole, [("deploy_v16.sh",)]),
                            ("promoted", alias_chpc, [("deploy_v16.sh",)]),
                            ("deployed", alias_whole, [("lengau.sh", "rollover_pilot_v16.sh")]),
                            ("rolled", alias_whole, [("lengau.sh", "adopt_pilot16.sh", "--file", "reviews/test_pilot_record.md")])):
        w = stage(name); mut(w)
        if name == "rolled":
            pilot_record(w)
        jd = tree_digest(os.path.join(w.L, "rsc_screen")); jh = sh("git", "-C", w.J, "rev-parse", "HEAD"); gd = tree_digest(w.G)
        for r in runs:
            rc, out = w.script(*r); refused(rc, out, "not its own physical path")
        need(tree_digest(os.path.join(w.L, "rsc_screen")) == jd and sh("git", "-C", w.J, "rev-parse", "HEAD") == jh,
             "the scientific clone changed (%s, %s)" % (name, mut.__name__))
        need(tree_digest(w.G) == gd, "the gate changed (%s, %s)" % (name, mut.__name__))


@test("P2 a gate member changed to a symlink after archive capture: rollover refuses before move/chmod; outside bytes and mode unchanged")
def t_gate_member_symlink():
    for member in ("review_refit.json", "qualified_refit_job1.json"):
        w = stage("deployed"); src = os.path.join(w.G, member); copy = os.path.join(w.outside, member)
        write(copy, open(src, "rb").read(), 0o644); os.remove(src); os.symlink(copy, src)
        before = tree_digest(w.outside); rdir = os.path.join(w.L, "row19_screen", "gate_retired")
        rc, out = w.script("lengau.sh", "rollover_pilot_v16.sh"); refused(rc, out, "not its own physical path")
        need(tree_digest(w.outside) == before and os.stat(copy).st_mode & 0o777 == 0o644, "the outside file changed (bytes or mode)")
        need(os.path.islink(src) and not (os.path.isdir(rdir) and os.listdir(rdir)), "something moved")


# ------------------------------------------------------------------------------------------------ Lengau tool compatibility
LENGAU_BODIES = ["remote_lib.sh", "preflight_v16.sh", "archive_v15.sh", "deploy_v16.sh", "rollover_pilot_v16.sh", "adopt_pilot16.sh"]
PY37_MODULES = {"dataclasses", "contextvars", "importlib.resources", "zoneinfo", "graphlib", "tomllib", "importlib.metadata"}
PY37_ATTRS = {"isascii", "time_ns", "monotonic_ns", "perf_counter_ns", "nullcontext", "fromisoformat", "removeprefix", "removesuffix",
              "isqrt", "prod", "cache", "shlex_join", "unlink_missing_ok", "is_relative_to", "readlink_path"}


def py36_problems(src, name):
    """Python >= 3.7 features in src (the Lengau Python is 3.6.8). Grammar via ast feature_version=(3, 7) (the lowest this
    interpreter accepts: it refuses 3.8+ syntax - walrus, positional-only, match ...), then an AST scan for 3.7+ library use. Every
    f-string is refused outright on the Lengau side: the 3.8 `{x=}` specifier is indistinguishable from `x={x!r}` in the AST."""
    try:
        tree = ast.parse(src, filename=name, feature_version=(3, 7))
    except SyntaxError as e:
        return ["%s: syntax newer than 3.7: %s (line %s)" % (name, e.msg, e.lineno)]
    bad = []
    for n in ast.walk(tree):
        ln = getattr(n, "lineno", "?")
        if isinstance(n, ast.JoinedStr):
            bad.append("%s:%s f-string (refused on the Lengau side)" % (name, ln))
        elif isinstance(n, ast.Call):
            for k in n.keywords:
                if k.arg in ("capture_output", "text"):
                    bad.append("%s:%s subprocess %s= (Python 3.7)" % (name, ln, k.arg))
            if isinstance(n.func, ast.Name) and n.func.id == "breakpoint":
                bad.append("%s:%s breakpoint() (3.7)" % (name, ln))
            if isinstance(n.func, ast.Attribute) and n.func.attr == "run" and isinstance(n.func.value, ast.Name) and n.func.value.id == "asyncio":
                bad.append("%s:%s asyncio.run (3.7)" % (name, ln))
        elif isinstance(n, ast.Attribute) and n.attr in PY37_ATTRS:
            bad.append("%s:%s .%s (3.7+)" % (name, ln, n.attr))
        elif isinstance(n, ast.Import):
            bad += ["%s:%s import %s (3.7+)" % (name, ln, a.name) for a in n.names if a.name in PY37_MODULES]
        elif isinstance(n, ast.ImportFrom):
            if n.module in PY37_MODULES or (n.module == "__future__" and any(a.name == "annotations" for a in n.names)):
                bad.append("%s:%s from %s import (3.7+)" % (name, ln, n.module))
    return bad


def lengau_python_sources():
    srcs = {"lengau_archive.py": open(os.path.join(HERE, "lengau_archive.py")).read()}
    rl = open(os.path.join(HERE, "remote_lib.sh")).read()
    m = re.search(r"^LOCK_PY='(.*?)'$", rl, re.S | re.M); need(m is not None, "remote_lib.sh has no LOCK_PY")
    srcs["remote_lib.sh:LOCK_PY"] = m.group(1)
    for f in LENGAU_BODIES:
        body = open(os.path.join(HERE, f)).read()
        if f != "remote_lib.sh":
            i = body.find("<<'REMOTE'")
            body = body[i:body.index("\nREMOTE\n", i)] if i >= 0 else body     # the Lengau half only (the Mac half is modern)
        for j, m in enumerate(re.finditer(r'"\$T/t1py" -c \'([^\']*)\'', body)):
            srcs["%s:t1py-c#%d" % (f, j + 1)] = m.group(1)
    return srcs


@test("Lengau compat: every Lengau-side Python (lengau_archive.py, LOCK_PY, each t1py -c body) is Python 3.6 code")
def t_py36():
    probe = "import subprocess, dataclasses\nr = subprocess.run(['x'], capture_output=True, text=True)\nprint(f'{r}')\n"
    need(len(py36_problems(probe, "probe")) == 4, "the 3.6 scanner misses known 3.7+ features: %s" % py36_problems(probe, "probe"))
    need(py36_problems("(y := 1)\n", "walrus"), "the 3.6 scanner misses the walrus")
    srcs = lengau_python_sources()
    need(len([k for k in srcs if ":t1py-c#" in k]) == 5, "expected the five t1py -c bodies on the Lengau side: %s" % sorted(srcs))
    bad = [p for name, src in sorted(srcs.items()) for p in py36_problems(src, name)]
    need(not bad, "Lengau-side Python uses features newer than 3.6:\n" + "\n".join(bad))


@test("Lengau compat: the shims reject git -C, echo --absolute-git-dir (as 1.8.3 does) and reject flock -E (2.23)")
def t_lengau_shims():
    w = stage("fresh"); g = os.path.join(w.lbin, "git")
    r = subprocess.run([g, "-C", w.C, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    need(r.returncode == 129 and "Unknown option: -C" in r.stderr, "the git shim accepted -C", r.stdout + r.stderr)
    r = subprocess.run([g, "rev-parse", "--absolute-git-dir"], cwd=w.C, capture_output=True, text=True)
    need(r.returncode == 0 and r.stdout.strip() == "--absolute-git-dir", "the git shim does not echo --absolute-git-dir like 1.8.3", r.stdout + r.stderr)
    r = subprocess.run([g, "status", "--porcelain=v2"], cwd=w.C, capture_output=True, text=True); need(r.returncode == 129, "the git shim accepted --porcelain=v2")
    r = subprocess.run([g, "rev-parse", "--git-dir"], cwd=w.C, capture_output=True, text=True)
    need(r.returncode == 0 and r.stdout.strip() == os.path.join(w.L, "rsc_screen_ctl", ".git"), "the git shim does not pass 1.8.3 calls through", r.stdout + r.stderr)
    w.fake("flock", FAKE_FLOCK); lk = os.path.join(w.L, "programme_admission.lock")
    r = subprocess.run([os.path.join(w.bin, "flock"), "-n", "-s", "-E", "75", lk, "true"], capture_output=True, text=True)
    need(r.returncode == 64 and "invalid option" in r.stderr, "the flock shim accepted -E", r.stdout + r.stderr)
    r = subprocess.run([os.path.join(w.bin, "flock"), "-n", "-s", lk, "true"], capture_output=True, text=True); need(r.returncode == 0, "the flock shim on a free lock")
    with Holder(lk):
        r = subprocess.run([os.path.join(w.bin, "flock"), "-n", "-s", lk, "true"], capture_output=True, text=True)
    need(r.returncode == 1, "the 2.23 flock shim does not exit 1 on a -n conflict (exit %d)" % r.returncode)


@test("Lengau compat: the whole route (preflight, archive, deploy, re-run, rollover, adopt's checks) runs on git 1.8.3 and flock 2.23")
def t_lengau_route():
    w = stage("fresh"); w.fake("flock", FAKE_FLOCK)
    rc, out = w.script("preflight_v16.sh"); need(rc == 0 and "PREFLIGHT OK" in out, "preflight on git 1.8.3", out)
    need("trying the python fcntl probe" not in out, "the flock(1) probe fell back to python", out)
    rc, out = w.script("archive_v15.sh"); need(rc == 0 and "ARCHIVE OK" in out, "archive on git 1.8.3", out)
    rc, out = w.script("promote_v16.py"); need(rc == 0 and "promoted:" in out, "promote", out); w.commit_promotion()
    rc, out = w.script("deploy_v16.sh"); need(rc == 0 and "DEPLOY OK" in out and "IDENTICAL" in out, "deploy on git 1.8.3", out)
    rc, out = w.script("deploy_v16.sh"); need(rc == 0 and "already holds exactly these v16 bytes" in out, "deploy re-run on git 1.8.3", out)
    rc, out = w.script("lengau.sh", "rollover_pilot_v16.sh"); need(rc == 0 and "retired to" in out, "rollover on git 1.8.3", out)
    write(os.path.join(w.t1, "reviews/test_pilot_record.md"), "ADOPT row19-screen-pilot role=refit qualification=x max_job=100\n")
    rc, out = w.script("lengau.sh", "adopt_pilot16.sh", "--file", "reviews/test_pilot_record.md")
    need("gate qualification is still the v15" in out and "Unknown option" not in out, "adopt reached its qualification check on git 1.8.3", out)
    log = open(os.path.join(w.lbin, "git.log")).read()
    for want in ("rev-parse --show-toplevel", "rev-parse --git-dir", "status --porcelain", "rev-parse --verify HEAD", "merge-base --is-ancestor", "commit -q -m"):
        need(want in log, "the Lengau half never ran `git %s` through the 1.8.3 shim" % want, log)
    need(not os.path.exists(os.path.join(w.lbin, "git.rejected")), "a Lengau-side git call used an option git 1.8.3 lacks",
         open(os.path.join(w.lbin, "git.rejected")).read() if os.path.exists(os.path.join(w.lbin, "git.rejected")) else "")


@test("Lengau compat: ctl_git still refuses a gitfile .git and a symlinked .git (the reviewed own-root semantics, on git 1.8.3)")
def t_lengau_ctl_git_semantics():
    for kind in ("gitfile", "symlink"):
        w = stage("fresh"); gd = os.path.join(w.L, "rsc_screen_ctl", ".git"); moved = os.path.join(w.outside, "ctl.git")
        shutil.move(gd, moved)
        if kind == "gitfile":
            write(gd, "gitdir: %s\n" % moved)
        else:
            os.symlink(moved, gd)
        rc, out = w.script("preflight_v16.sh"); refused(rc, out, "git directory is")
        need("Unknown option" not in out and "lengau preflight OK" not in out, "preflight with a %s .git" % kind, out)
    w = stage("fresh"); gd = os.path.join(w.L, "rsc_screen_ctl", ".git"); moved = os.path.join(w.L, "row19_screen", "ctl.git")
    shutil.move(gd, moved); write(gd, "gitdir: %s\n" % moved)                     # an alias elsewhere but still inside $T
    rc, out = w.script("archive_v15.sh"); refused(rc, out, "git directory is"); need(not os.path.exists(w.A), "archived with a gitfile clone")


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
