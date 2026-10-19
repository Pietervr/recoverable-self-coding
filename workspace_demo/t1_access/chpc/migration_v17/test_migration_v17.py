#!/usr/bin/env python3
"""Private-copy tests for the migration_v17 scripts (the migration_v16 test pattern; every Codex finding on migration_v16 is a
requirement here too).

    python3 chpc/migration_v17/test_migration_v17.py [-k <substring>] [--keep]      (from anywhere)

The production scripts carry NO test hook. This harness builds throwaway worlds under a fresh private temp directory and never
reads, clones or hashes the whole repository: every world is built from an explicit ALLOWLIST of administrative files copied
from the live tree (controller code, controls, adoption and review records, the reviewed v17 candidate package, the e2_final
data and the v16 pilot qualification), so no protected plant/key/sample file and no scientific source is ever read (the Codex
mig2_e2n incident). The scientific job clone holds eight synthetic placeholder files at the science-inventory paths.
A world is:
  mac/                 a private git repository holding workspace_demo/t1_access/<allowlist> (the "Mac" tree, at the adopted v16)
  lengau/              a fake toolchain root: rsc_screen_ctl (a private git repository holding the v16 controller set, with the
                       three pinned evidence files UNTRACKED with their pinned bytes, read from the Mac history), rsc_screen (the
                       synthetic science), the gate, gate_retired, ec2 (activation_e1.json), plans, locks, the ledger, job files
                       and a fake t1py
  fakebin/             ps, sha256sum (fault injection), ssh and scp (ALWAYS refuse, logged: nothing can leave the Mac)
  lengaubin/           restricted-CLI shims first on the Lengau half's PATH: git rejects `-C` and the options this code must
                       not need (a selected restricted interface, NOT an installed git 1.8.3.1); flock (when installed) rejects
                       -E and exits 1 on a -n conflict (a selected restricted interface: upstream util-linux 2.23.2 does accept
                       -E, so this models a stricter build, not the version - Codex mig_compat P3)
The production files are COPIED into mac/.../chpc/migration_v17/ with exactly two tagged lines substituted: the `# @root`
toolchain root in remote_lib.sh (-> the fake root) and the `# @transport` ssh in lengau.sh (-> a local `bash -s`). The harness
refuses a fake root outside its temp directory or aliasing the production toolchain and checks the private copy differs from
production on those two lines only.
The fake t1py is `python3` for every `-c` snippet; it INTERCEPTS the two positive controller commands the bodies call and that
cannot run outside Lengau - `chpc/row19_partition.py activate` and `chpc/row19_screen_admit.py ... --adopt-review` - and
simulates them (modes: ok / held / problems / crash / wrong-proof; adopter ok / refuse), and refuses ANY other controller
script (no test can reach a production path through the real manifest's storage root). ec2_sync.py, the refit and bank status
commands are private STUBS in the worlds that need them (they would otherwise use ssh); prod_authority.py inventory runs for real
in the private tree. Nothing here runs ssh/scp, touches Lengau, AWS or the live tree, or writes outside the temp directory
(removed at the end unless --keep)."""
import ast, hashlib, json, os, re, shlex, shutil, signal, stat, subprocess, sys, tempfile, time

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
T1_REL = "workspace_demo/t1_access"
LIVE_T1 = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO = os.path.abspath(os.path.join(LIVE_T1, "..", ".."))
PROD_ROOT = "/mnt/lustre/users/pvanrooyen/t1_toolchain"
TRANSPORT = "ssh -o ControlPath=none -o ConnectTimeout=30 -o BatchMode=yes lengau bash -s"
ROOT_LINE = "T_ROOT=/mnt/lustre/users/pvanrooyen/t1_toolchain   # @root"
SELF = os.path.basename(__file__)
PROD_FILES = sorted(f for f in os.listdir(HERE) if os.path.isfile(os.path.join(HERE, f)) and f != SELF and not f.startswith(".")
                    and f != "test_results.txt")
V16_QUAL = "2c7a7ef1fb903cf0fa75701d2a56d216e98faf14e6638da891afd8bed0bfea44"
V16_CONTROLS = "01976b6a92e7150a82d8397caeb88e5425e0dd051f69bb244bf3f83981e8f220"
V17_CONTROLS = "9ea4e727c5d308457a2d5901ef6565522845fb31d52c3c1c0f7dd5a51a9d83c0"
E2_PART = "48cea639e823abbf39238e3dd7c075f63ba9eca8467009348510e2943ed56fa6"
REC = "reviews/2026-10-19_e2_repair_codex_rereview.md"
REAL_SHA256SUM = shutil.which("sha256sum") or "/sbin/sha256sum"
REAL_GIT = shutil.which("git") or "/usr/bin/git"
SCI = ["chpc/row19_screen_manifest.json", "analyze.py", "models.py", "simulate.py", "chpc/row19_shard.py", "chpc/row19_ledger.py",
       "chpc/row19_slice.py", "chpc/row19_screen_orig.py"]
EVIDENCE = {"aws_ec2/ec2_release_state.json": ("f2caf7c", "80ba0ac599f617f8c0ee020d75e7c53dcd30c519d783a76dcb6a2f6b9f1a1d39"),
            "aws_ec2/runs/b2/bench_report_attempt_5_20261011T185715Z.json": ("c12af3e", "154511e687f006001888970bd3d65398b6b37c910221378b7f6c3c63fe63e3a4"),
            "reviews/2026-10-11_d1d2_f3_codex_record.md": ("1609fa7", "636f1e77089578a14ee837bf95fe0f86cc84dbc907f8ced918256b69dbb55c1e")}
# the administrative allowlist (relative to workspace_demo/t1_access); nothing else of the live tree is ever read
CTL_SET = ["chpc/row19_screen_controls.json", "chpc/row19_screen_controls_adoption.json", "chpc/row19_screen_admit.py",
           "chpc/row19_screen_status.py", "chpc/row19_screen_verify.py", "chpc/row19_screen_release.py", "chpc/programme_gate.py",
           "chpc/row19_screen_resources.json", "chpc/row19_ec2_root.py", "chpc/row19_ec2_shadow.py", "chpc/row19_qual_S_manifest.json",
           "chpc/row19_screen_designated.json", "chpc/row19_partition.py", "chpc/row19_ec2_ingest.py", "chpc/row19_ec2_qualify.py",
           "chpc/row19_ec2_state.py", "chpc/row19_ledger.py", "chpc/row19_screen_manifest.json", "chpc/row19_screen_budget.json",
           "chpc/row19_partition_e1.json", "chpc/row22_bank_status.py", "chpc/row22_bank_submit.py", "aws_ec2/qual_S_plan.json",
           "aws_ec2/prod_authority.py", "aws_ec2/prod_launch.py", "aws_ec2/make_prod_manifest.py", "aws_ec2/qual_permit.py",
           "reviews/2026-10-17_v16_p80_codex_review.md"]
CAND_SET = ["chpc/candidate_v17/row19_screen_controls.json", "chpc/candidate_v17/row19_screen_admit.py",
            "chpc/candidate_v17/v17_promotion_map.json", "chpc/candidate_v17/build_v17.py", "chpc/candidate_v17/promote_v17.py",
            "chpc/candidate_e2/row19_partition.py", "chpc/candidate_e2/row19_ec2_ingest.py", "chpc/candidate_e2/row19_ec2_e2rules.py",
            "chpc/candidate_e2/admit_v17_partition_line.diff", "chpc/candidate_e2/aws_ec2/make_e2_funding.py",
            "chpc/candidate_e2q/row19_ec2_qualify.py", "chpc/candidate_e2q/row19_ec2_state.py", "chpc/candidate_e2q/row19_ec2_e2qual.py",
            "chpc/candidate_e2q/aws_ec2/prod_authority.py", "chpc/candidate_e2q/aws_ec2/prod_launch.py",
            "chpc/candidate_e2q/aws_ec2/make_prod_manifest.py", "chpc/candidate_e2q/aws_ec2/qual_permit.py",
            "chpc/e2_final/row19_partition_e2.json", "chpc/e2_final/claims_snapshot_e2.json", "chpc/e2_final/e2_funding.json",
            "chpc/e2_final/manifest_production_e2.json", "chpc/e2_final/manifest_e2q1_e2.json", "chpc/e2_final/manifest_e2q2_e2.json",
            "chpc/e2_final/panel_e2q_e2.json", REC, "aws_ec2/bench_launch.py", "aws_ec2/budget_baseline.json"]
MAC_UNTRACKED = {"chpc/results/row19_screen/receipts/qualified_refit_job1.json": V16_QUAL}

BASE = None
TESTS = []


def test(name):
    def deco(fn):
        TESTS.append((name, fn)); return fn
    return deco


class Fail(Exception):
    pass


def need(cond, what, out=""):
    if not cond:
        raise Fail("%s\n---- output ----\n%s" % (what, out[-3500:]))


def refused(rc, out, *subs):
    need(rc != 0, "expected a refusal (non-zero exit), got 0", out)
    for s in subs:
        need(s in out, "expected the refusal to say %r" % s, out)


def sh(*cmd, cwd=None, check=True):
    r = subprocess.run(list(cmd), cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise Fail("command failed: %s\n%s%s" % (" ".join(cmd), r.stdout, r.stderr))
    return r.stdout


def write(p, data, mode=None):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.lexists(p) and not os.path.isdir(p):
        os.chmod(p, 0o644) if not os.path.islink(p) else None
    with open(p, "w" if isinstance(data, str) else "wb") as fh:
        fh.write(data)
    if mode is not None:
        os.chmod(p, mode)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def unlock_tree(p):
    for d, dirs, files in os.walk(p):
        os.chmod(d, 0o755)
        for n in files:
            q = os.path.join(d, n)
            if not os.path.islink(q):
                os.chmod(q, 0o644)


def tree_digest(p):
    """A digest of every path, mode, file content and link target under p (.git excluded). Used ONLY on private worlds,
    which hold allowlisted administrative copies and synthetic placeholders."""
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


def gitc(repo, *a):
    return sh("git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t", *a)


# ------------------------------------------------------------------------------------------------ fake tools
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
FAKE_NET = """#!/bin/bash
d=$(cd "$(dirname "$0")" && pwd)
printf '%s %s\\n' "$(basename "$0")" "$*" >> "$d/net.log"
echo "$(basename "$0"): REFUSED by the private test world (no network)" >&2
exit 255
"""
FAKE_FLOCK = """#!/usr/bin/env python3
# a restricted flock(1) CLI: -n, -s, -x only (rejects -E / --conflict-exit-code with a usage error, exit 64); a -n conflict exits 1
import fcntl, subprocess, sys
a = sys.argv[1:]; nb = False; mode = fcntl.LOCK_EX
while a and a[0].startswith("-"):
    x = a.pop(0)
    if x in ("-n", "--nb", "--nonblock"): nb = True
    elif x in ("-s", "--shared"): mode = fcntl.LOCK_SH
    elif x in ("-x", "-e", "--exclusive"): mode = fcntl.LOCK_EX
    elif x == "--version": print("flock from util-linux 2.23.2 (private restricted-CLI test shim)"); sys.exit(0)
    else:
        sys.stderr.write("flock: invalid option -- '%s'\\n" % x.lstrip("-")); sys.exit(64)
fh = open(a.pop(0), "rb")
try:
    fcntl.flock(fh.fileno(), mode | (fcntl.LOCK_NB if nb else 0))
except BlockingIOError:
    sys.exit(1)
sys.exit(subprocess.call(a))
"""
BROKEN_FLOCK = "#!/bin/bash\necho 'flock: simulated failure' >&2\nexit 64\n"
LENGAU_GIT = """#!/bin/bash
# a RESTRICTED git CLI (private test shim): every call logged; `-C` and later interfaces rejected (or echoed, for rev-parse)
d=$(cd "$(dirname "$0")" && pwd)
printf '%%s\\n' "$*" >> "$d/git.log"
reject() { printf '%%s\\n' "$*" >> "$d/git.rejected"; echo "$1" >&2; exit 129; }
a=("$@"); i=0
while [ $i -lt ${#a[@]} ]; do
  case ${a[$i]} in
    -C) reject "Unknown option: -C" "$*";;
    --no-optional-locks|--glob-pathspecs|--noglob-pathspecs|--icase-pathspecs|--super-prefix*|--config-env*) reject "Unknown option: ${a[$i]}" "$*";;
    -c) i=$((i + 2));;
    -*) i=$((i + 1));;
    *) break;;
  esac
done
sub=${a[$i]:-}
for x in "${a[@]:$((i + 1))}"; do
  case $sub:$x in
    rev-parse:--absolute-git-dir) printf '%%s\\n' "$x" >> "$d/git.rejected"; echo "$x"; exit 0;;
    rev-parse:--path-format*|rev-parse:--show-superproject-working-tree|rev-parse:--show-object-format*|rev-parse:--end-of-options) reject "unsupported: $x" "$*";;
    status:--porcelain=*|status:--ahead-behind|status:--no-ahead-behind|*:--end-of-options) reject "unsupported: $x" "$*";;
  esac
done
exec "%s" "$@"
""" % REAL_GIT
# the fake $T/t1py: python3 for -c snippets; the two positive controller commands simulated; every other controller script refused
FAKE_T1PY = r"""#!/bin/bash
d=$(cd "$(dirname "$0")" && pwd)
if [ -f "$d/t1py.nofcntl" ]; then for a in "$@"; do case $a in *fcntl.flock*) echo "simulated: this python has no usable fcntl" >&2; exit 1;; esac; done; fi
case "${1:-}" in
  -c) exec python3 "$@";;
  chpc/row19_partition.py)
    [ "${2:-}" = activate ] || { echo "test t1py: unexpected controller command $*" >&2; exit 99; }
    printf '%s\n' "$*" >> "$d/activate.log"
    mode=ok; [ -f "$d/activate.mode" ] && mode=$(cat "$d/activate.mode")
    exec python3 "$d/sim_activate.py" "$d/row19_screen" "$mode";;
  chpc/row19_screen_admit.py)
    case " $* " in *" --adopt-review "*) ;; *) echo "test t1py: unexpected controller command $*" >&2; exit 99;; esac
    printf '%s\n' "$*" >> "$d/adopt.log"
    mode=ok; [ -f "$d/adopt.mode" ] && mode=$(cat "$d/adopt.mode")
    [ "$mode" = ok ] || { echo "REFUSED: simulated adopter refusal (the qualification is not the record's)"; exit 2; }
    rec=""; prev=""; for a in "$@"; do [ "$prev" = --adopt-review ] && rec=$a; prev=$a; done
    g="$d/row19_screen/gate/review_refit.json"
    [ ! -e "$g" ] || { echo "REFUSED: a review exists"; exit 2; }
    printf '{"schema": "private-test-adopted", "record": "%s", "qualification_sha256": "%s", "max_job_number": 100}\n' "$rec" "$(shasum -a 256 "$d/row19_screen/gate/qualified_refit_job1.json" | cut -c1-64)" > "$g"
    echo "adopted: $rec (simulated) for refit, job numbers up to 100"; exit 0;;
  *) echo "test t1py: refusing $*" >&2; exit 99;;
esac
"""
SIM_ACTIVATE = r'''import fcntl, hashlib, json, os, sys, time
sys.path.insert(0, "chpc")
import row19_partition as RP
root, mode = sys.argv[1], sys.argv[2]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
man_p, part_p = "chpc/row19_screen_manifest.json", "chpc/row19_partition_e2.json"
man = json.load(open(man_p)); part = RP.load(part_p, man, sha(man_p))
ctl = json.load(open("chpc/row19_screen_controls.json")); latest = ctl["versions"][-1]
with open(os.path.join(root, "plans", ".submit.lock"), "a+") as lk:
    try:
        fcntl.flock(lk.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("HELD: the plan lock is held (an admission or an ingestion)"); sys.exit(3)
    if mode == "problems":
        print(json.dumps(dict(problems=["simulated: 1 Lengau claim(s) on owned coordinates, e.g. [[3, 61]]"], facts={}))); sys.exit(3)
    out = os.path.join(root, "ec2", "activation_e2.json")
    if os.path.exists(out):
        print("HELD: %s exists - an activation is immutable" % out); sys.exit(3)
    proof = {"schema": "row19-ec2-activation-1", "mode": "canonical", "epoch": part["epoch"], "partition_sha256": sha(part_p),
             "manifest_sha256": sha(man_p), "controls_sha256": sha("chpc/row19_screen_controls.json"), "controls_version": latest["version"],
             "controls_entry_sha256": RP.entry_sha(latest), "adoption_sha256": sha("chpc/row19_screen_controls_adoption.json"),
             "predecessor": part["predecessor"], "transferred_indices": RP.transferred_of(part), "owned_sha256": part["owned_sha256"],
             "claims_snapshot_sha256": part["claims_snapshot"]["claims_sha256"], "claims_sha256": "0" * 64,
             "ec2_completed_sha256": "0" * 64, "facts": {"simulated": True}, "at": time.time()}
    if mode == "wrong":
        proof["owned_sha256"] = "0" * 64
    tmp = "%s.tmp.%d" % (out, os.getpid())
    with open(tmp, "w") as fh:
        json.dump(proof, fh, indent=1, sort_keys=True)
    os.link(tmp, out); os.unlink(tmp)
    if mode == "crash":
        sys.exit(137)
print("activated epoch 2: %s sha256 %s" % (out, sha(out)))
'''
STUB_SYNC = r'''"""PRIVATE TEST STUB of aws_ec2/ec2_sync.py (never production): installs a sealed inventory on the fake root."""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "chpc"))
import row19_ec2_state as ES
ROOT = %r
mode = open(os.path.join(HERE, "stub_sync.mode")).read().strip() if os.path.exists(os.path.join(HERE, "stub_sync.mode")) else "ok"
log = os.path.join(HERE, "stub_sync.log")
open(log, "a").write("cycle %%s\n" %% mode)
if mode == "fail":
    print("stub ec2_sync: the root held the inventory"); sys.exit(3)
gp = os.path.join(HERE, "stub_sync.gen"); g = int(open(gp).read()) + 1 if os.path.exists(gp) else 60
open(gp, "w").write(str(g))
inv = {"schema": ES.INVENTORY_SCHEMA, "generation": g, "at": time.time() - (7 * 3600 if mode == "stale" else 5), "attempts": {}, "owners": {}, "fence": {}}
if mode == "outside":
    c = json.load(open(os.path.join(HERE, "stub_sync.outside")))
    inv["attempts"] = {"qual-Q1/4": {"key": "qual-Q1/4", "state": "reconciled", "ingestion": "pending", "class": "qualification", "sequence": 7,
                                     "coordinates": [c], "charged_usd": 1.0}}
    inv["owners"] = {"%%d/%%d" %% tuple(c): ["qual-Q1/4", 7]}; inv["fence"] = {"%%d/%%d" %% tuple(c): 7}
p = os.path.join(ROOT, "ec2", "authority", "inventory.json"); os.makedirs(os.path.dirname(p), exist_ok=True)
json.dump(ES.seal(inv), open(p, "w"), indent=1, sort_keys=True)
print("stub ec2_sync: installed generation %%d" %% g)
'''
STUB_STATUS = r'''"""PRIVATE TEST STUB of chpc/row19_screen_status.py (never production): publishes a synthetic refit receipt."""
import hashlib, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "results", "row19_screen", "receipts"); os.makedirs(R, exist_ok=True)
mode = open(os.path.join(HERE, "stub_status.mode")).read().strip() if os.path.exists(os.path.join(HERE, "stub_status.mode")) else "ok"
if mode == "fail":
    print("ALARMS: - simulated"); sys.exit(1)
now = time.time(); stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(now))
gen = {"version": 16 if mode == "gen16" else 17, "latest": 16 if mode == "gen16" else 17, "controls_problem": "",
       "controls_sha256": "9ea4e727c5d308457a2d5901ef6565522845fb31d52c3c1c0f7dd5a51a9d83c0", "verify_sha256": "0" * 64}
vp = os.path.join(R, "verify_refit_%s.json" % stamp); json.dump({"generation": gen}, open(vp, "w"))
acts = {"activation_e1.json": "1" * 64} if mode == "noe2" else {"activation_e1.json": "1" * 64, "activation_e2.json": "2" * 64}
rc = {"schema": "row19-screen-watch-test", "role": "refit", "time": now, "fresh": True, "production": True,
      "alarms": ["simulated alarm"] if mode == "alarm" else [], "designated": {"declaration_sha256": "a96eb598"},
      "bound": {"verify_file": os.path.basename(vp), "verify_file_sha256": hashlib.sha256(open(vp, "rb").read()).hexdigest()},
      "ec2": {"bound": {"activations": acts, "hold": False, "stop": False}, "problems": []}}
json.dump(rc, open(os.path.join(R, "watch_refit_%s.json" % stamp), "w"), indent=1)
print("stub status: receipt watch_refit_%s.json" % stamp); sys.exit(0)
'''
STUB_BANK = '"""PRIVATE TEST STUB of chpc/row22_bank_status.py."""\nimport sys\nprint("stub bank receipt")\nsys.exit(0)\n'


class World:
    def __init__(self, d):
        self.d = d; self.mac = os.path.join(d, "mac"); self.t1 = os.path.join(self.mac, T1_REL)
        self.L = os.path.join(d, "lengau"); self.bin = os.path.join(d, "fakebin"); self.outside = os.path.join(d, "outside")
        self.lbin = os.path.join(d, "lengaubin")
        self.CR = os.path.join(self.L, "rsc_screen_ctl"); self.C = os.path.join(self.CR, T1_REL)
        self.J = os.path.join(self.L, "rsc_screen", T1_REL)
        self.GS = os.path.join(self.L, "row19_screen"); self.G = os.path.join(self.GS, "gate"); self.R = os.path.join(self.GS, "gate_retired")
        self.A = os.path.join(self.L, "archive_screen", "v16_before_v17"); self.PROOF = os.path.join(self.L, "archive_screen", "v17_deploy_proof")
        self.ACT2 = os.path.join(self.GS, "ec2", "activation_e2.json")
        self.MA = os.path.join(self.t1, "chpc/results/archive/row19_screen_v16_before_v17")
        self.LSF = os.path.join(self.t1, "chpc/results/archive/row19_screen_v16_before_v17.lengau_SHA256SUMS.txt")

    def install(self, root=None):
        root = root or self.L
        base = os.path.realpath(BASE); real = os.path.realpath(root)
        if not real.startswith(base + os.sep):
            raise Fail("refusing a fake root outside the harness temp dir: %s -> %s" % (root, real))
        if real == PROD_ROOT or real.startswith(PROD_ROOT + "/") or os.path.realpath(PROD_ROOT) == real:
            raise Fail("refusing a fake root that is the production toolchain")
        if not os.path.realpath(self.t1).startswith(base + os.sep):
            raise Fail("refusing a Mac tree outside the harness temp dir")
        dst = os.path.join(self.t1, "chpc", "migration_v17")
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
            if k.startswith("V17_") or k.startswith("V16_") or k.startswith("GIT_"):
                del env[k]
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        r = subprocess.run(list(cmd), cwd=self.t1, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout)
        return r.returncode, r.stdout

    def script(self, name, *args):
        if name.endswith(".py"):
            return self.run("python3", "chpc/migration_v17/" + name, *args)
        return self.run("bash", "chpc/migration_v17/" + name, *args)

    def promote(self, *args):
        return self.run("python3", "chpc/candidate_v17/promote_v17.py", *args)

    def ctl_state(self):
        return (sh("git", "-C", self.CR, "rev-parse", "HEAD").strip(), sh("git", "-C", self.CR, "status", "--porcelain", "--untracked-files=all"))

    def fake(self, name, data):
        write(os.path.join(self.bin, name), data, 0o755)

    def commit_promotion(self):
        rc, out = self.script("v17_package.py", "commit-paths"); need(rc == 0, "commit-paths", out)
        paths = [T1_REL + "/" + p for p in out.split()]
        sh("git", "-C", self.mac, "add", "--", *paths)
        gitc(self.mac, "commit", "-q", "-m", "TEST promote v17 (private world)", "--", *paths)

    def net_log(self):
        p = os.path.join(self.bin, "net.log")
        return open(p).read() if os.path.exists(p) else ""


def copy_live(rel, dst_root):
    src = os.path.join(LIVE_T1, rel)
    if os.path.islink(src) or not os.path.isfile(src):
        raise Fail("allowlisted live file missing or not regular: %s" % rel)
    write(os.path.join(dst_root, rel), open(src, "rb").read())


def git_init(repo):
    os.makedirs(repo, exist_ok=True)
    sh("git", "init", "-q", repo)
    sh("git", "-C", repo, "config", "commit.gpgsign", "false")


def build_fresh(d):
    w = World(d); os.makedirs(d)
    # the Mac tree: the allowlist, committed (the adopted v16 state plus the reviewed candidate package)
    git_init(w.mac)
    for rel in CTL_SET + CAND_SET:
        copy_live(rel, w.t1)
    gitc(w.mac, "add", "-A"); gitc(w.mac, "commit", "-q", "-m", "TEST the Mac tree at the adopted v16 (allowlisted copies)")
    for rel, want in MAC_UNTRACKED.items():
        copy_live(rel, w.t1); need(sha(os.path.join(w.t1, rel)) == want, "the live Mac %s is not %s" % (rel, want[:8]))
    write(os.path.join(w.t1, "aws_ec2/runs/.authority.lock"), "")
    write(os.path.join(w.mac, ".git", "info", "exclude"), "aws_ec2/runs/\n%s/aws_ec2/runs/\n%s/chpc/results/row19_screen/\n" % (T1_REL, T1_REL))
    # the fake Lengau root
    for sub in ("jobs", "row19_screen/gate/pbs", "row19_screen/gate_retired", "row19_screen/ec2", "row19_screen/plans",
                "row19_screen_campaign", "archive_screen"):
        os.makedirs(os.path.join(w.L, sub), exist_ok=True)
    os.makedirs(w.outside); os.makedirs(w.bin)
    write(os.path.join(w.L, "programme_admission.lock"), ""); write(os.path.join(w.GS, "plans/.submit.lock"), "")
    write(os.path.join(w.L, "t1py"), FAKE_T1PY, 0o755); write(os.path.join(w.L, "sim_activate.py"), SIM_ACTIVATE)
    git_init(w.CR)
    for rel in CTL_SET:
        copy_live(rel, w.C)
    gitc(w.CR, "add", "-A"); gitc(w.CR, "commit", "-q", "-m", "TEST the controller clone at v16")
    for p, (c, want) in EVIDENCE.items():
        b = subprocess.run(["git", "-C", REPO, "show", "%s:%s/%s" % (c, T1_REL, p)], capture_output=True, check=True).stdout
        need(hashlib.sha256(b).hexdigest() == want, "the Mac history does not hold the pinned bytes of " + p)
        write(os.path.join(w.C, p), b)
    need(ctl_untracked(w) == sorted(T1_REL + "/" + p for p in EVIDENCE) and ctl_dirty(w) == [], "the Lengau evidence fixture is wrong")
    git_init(os.path.join(w.L, "rsc_screen"))
    for i, f in enumerate(SCI):
        write(os.path.join(w.J, f), "# synthetic science placeholder %d (%s), private test world\n" % (i, f))
    gitc(os.path.join(w.L, "rsc_screen"), "add", "-A"); gitc(os.path.join(w.L, "rsc_screen"), "commit", "-q", "-m", "TEST synthetic science")
    write(os.path.join(w.G, "qualified_refit_job1.json"), open(os.path.join(w.t1, "chpc/results/row19_screen/receipts/qualified_refit_job1.json"), "rb").read())
    write(os.path.join(w.G, "review_refit.json"), json.dumps({"schema": "private-test", "role": "refit", "qualification_sha256": V16_QUAL, "max_job_number": 100}) + "\n")
    write(os.path.join(w.G, "watch_refit_1.json"), "{}\n"); write(os.path.join(w.G, "pbs/row19_screen_refit_1.o7600001"), "fake PBS out\n")
    write(os.path.join(w.G, "scaleup_refit_v16.json"), json.dumps({"schema": "private-test-scaleup", "first_job": 46}) + "\n")
    write(os.path.join(w.R, "review_refit.v15_qual3c605514_max100.json"), "{}\n", 0o444)
    write(os.path.join(w.GS, "ec2/activation_e1.json"), json.dumps({"schema": "row19-ec2-activation-1", "epoch": 1,
          "partition_sha256": "8d1de408b6ef9dc66d4736b6138536de6591f0d29ebdd6fd00a6e43307225608"}) + "\n")
    write(os.path.join(w.L, "jobs/row19_screen_refit_1.pbs"), "#PBS private test\n"); write(os.path.join(w.L, "jobs/row19_screen_refit_47.pbs"), "#PBS private test 47\n")
    write(os.path.join(w.L, "row19_screen_campaign/budget.json"), json.dumps({"cap_core_h": 81000.0, "cap_history": [], "entries": {}}) + "\n")
    w.fake("ps", FAKE_PS); w.fake("sha256sum", FAKE_SHA); w.fake("ssh", FAKE_NET); w.fake("scp", FAKE_NET)
    write(os.path.join(w.lbin, "git"), LENGAU_GIT, 0o755)
    return w


def ctl_status(w):
    return [l for l in sh("git", "-C", w.CR, "status", "--porcelain", "--untracked-files=all").split("\n") if l]


def ctl_untracked(w):
    return sorted(l[3:] for l in ctl_status(w) if l.startswith("?? "))


def ctl_dirty(w):
    ev = {"?? %s/%s" % (T1_REL, p) for p in EVIDENCE}
    return [l for l in ctl_status(w) if l not in ev]


def stub_sync(w):
    write(os.path.join(w.t1, "aws_ec2/ec2_sync.py"), STUB_SYNC % w.GS)
    write(os.path.join(w.t1, "aws_ec2/ec2_release_state.json"), json.dumps({"schema": "t1-ec2-release-state-1", "row23": {},
          "qualification": {}, "production": {}}) + "\n")


def stub_receipts(w):
    write(os.path.join(w.t1, "chpc/row19_screen_status.py"), STUB_STATUS)
    write(os.path.join(w.t1, "chpc/row22_bank_status.py"), STUB_BANK)
    write(os.path.join(w.t1, "chpc/row22_bank_manifest.json"), "{}\n")


ORDER = ["fresh", "archived", "promoted", "deployed", "precycled", "activated", "postcycled", "rolled", "qualified"]
STAGES = {}


def fake_qualification(w):
    """A synthetic regenerated qualification (as the ONE --qualify 1 call writes it): Mac copy + gate copy + receipts."""
    R = os.path.join(w.t1, "chpc/results/row19_screen/receipts"); stamp = "20261020T101010Z"
    vp = os.path.join(R, "verify_refit_%s.json" % stamp)
    write(vp, json.dumps({"generation": {"version": 17, "latest": 17, "controls_problem": "", "controls_sha256": V17_CONTROLS}}))
    write(os.path.join(R, "watch_refit_%s.json" % stamp), json.dumps({"role": "refit", "time": 1.0, "alarms": []}))
    write(os.path.join(R, "watch_refit_20261017T204309Z.json"), json.dumps({"role": "refit", "old": True}))
    q = {"schema": "private-test-qualification", "role": "refit", "qualified_job": 1, "production": True, "verify_file": os.path.basename(vp),
         "bound": {"verify_file_sha256": sha(vp)}, "receipt": {"alarms": [], "fresh": True, "production": True,
                                                               "note": "earlier evidence watch_refit_20261017T204309Z.json"}}
    qp = os.path.join(R, "qualified_refit_job1.json"); write(qp, json.dumps(q, indent=1) + "\n")
    write(os.path.join(w.G, "qualified_refit_job1.json"), open(qp, "rb").read())
    return sha(qp)


def stage(name):
    """A fresh private world copied from the cached stage `name`."""
    if name not in STAGES:
        d = os.path.join(BASE, "stage_" + name)
        if name == "fresh":
            w = build_fresh(d)
        else:
            prev = stage(ORDER[ORDER.index(name) - 1]); sh("cp", "-cR", prev.d, d); w = World(d)
        w.install()
        if name == "archived":
            rc, out = w.script("archive_v16.sh"); need(rc == 0 and "ARCHIVE OK" in out, "stage archive", out)
        elif name == "promoted":
            rc, out = w.promote("--review", REC); need(rc == 0 and "promoted:" in out, "stage promote", out); w.commit_promotion()
        elif name == "deployed":
            rc, out = w.script("deploy_v17.sh"); need(rc == 0 and "DEPLOY OK" in out, "stage deploy", out)
        elif name == "precycled":
            stub_sync(w); rc, out = w.script("ec2_cycle_v17.sh", "pre-activation"); need(rc == 0 and "PRE-ACTIVATION CYCLE OK" in out, "stage pre-cycle", out)
        elif name == "activated":
            rc, out = w.script("lengau.sh", "activate_e2.sh"); need(rc == 0 and "ACTIVATED epoch 2" in out, "stage activate", out)
        elif name == "postcycled":
            stub_receipts(w); rc, out = w.script("ec2_cycle_v17.sh", "post-activation"); need(rc == 0 and "RECEIPTS OK" in out, "stage post-cycle", out)
        elif name == "rolled":
            rc, out = w.script("lengau.sh", "rollover_pilot_v17.sh"); need(rc == 0 and "retired to" in out, "stage rollover", out)
        elif name == "qualified":
            fake_qualification(w)
        STAGES[name] = w
    n = len(os.listdir(BASE)); d = os.path.join(BASE, "t%03d_%s" % (n, name))
    sh("cp", "-cR", STAGES[name].d, d)
    w = World(d); w.install(); return w


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


def commit_redirect(w, rel, target):
    """In the controller clone, replace directory `rel` by a COMMITTED symlink to `target` (holding the same files): a clean tree."""
    src = os.path.join(w.C, rel)
    if not os.path.exists(target):
        shutil.copytree(src, target, symlinks=True)
    shutil.rmtree(src); os.symlink(target, src)
    sh("git", "-C", w.CR, "add", "-A", "--", T1_REL + "/" + rel)
    gitc(w.CR, "commit", "-q", "-m", "TEST redirect " + rel)
    need(ctl_dirty(w) == [], "the redirect left the controller clone dirty", "\n".join(ctl_dirty(w)))


def pilot_record(w, qsha, name="reviews/test_pilot_v17_record.md"):
    p = os.path.join(w.t1, name)
    write(p, "# test pilot record\n\nADOPT row19-screen-pilot role=refit qualification=%s max_job=100\n" % qsha)
    sh("git", "-C", w.mac, "add", "--", T1_REL + "/" + name); gitc(w.mac, "commit", "-q", "-m", "TEST pilot record", "--", T1_REL + "/" + name)
    return name


# ================================================================================================ static and boundary
@test("static: no test hook, one fixed root, one fixed transport, no worker/reaper stop, no AWS call, every shell file parses")
def t_static():
    for f in PROD_FILES:
        s = open(os.path.join(HERE, f)).read()
        if f == "RUNBOOK.md":
            continue
        for bad in ("FAKE_LENGAU", "V17_FAKE", "V17_T=", "TEST_ROOT"):
            need(bad not in s, "%s mentions %s" % (f, bad))
        for bad in ("qdel", "pkill", "kill ", "killall", "scp ", "aws ", "boto3", "--force", "git add -A", "git add ."):
            need(bad not in s, "%s contains %r" % (f, bad))
        if f.endswith(".sh"):
            r = subprocess.run(["bash", "-n", os.path.join(HERE, f)], capture_output=True, text=True); need(r.returncode == 0, "bash -n " + f, r.stderr)
        if f.endswith(".py"):
            compile(s, f, "exec")
    tags = {f: open(os.path.join(HERE, f)).read().count("@transport") for f in PROD_FILES if f != "RUNBOOK.md"}
    need(sum(tags.values()) == 1 and tags["lengau.sh"] == 1, "exactly one @transport line, in lengau.sh: %s" % tags)
    lt = [l for l in open(os.path.join(HERE, "lengau.sh")).read().splitlines() if "@transport" in l][0]
    need(TRANSPORT in lt, "the transport line is not the fixed production ssh", lt)
    need(open(os.path.join(HERE, "remote_lib.sh")).read().count(ROOT_LINE) == 1, "remote_lib.sh lacks the single fixed root line")
    for f in ("check_v17.sh", "activate_e2.sh", "rollover_pilot_v17.sh", "adopt_pilot17.sh"):
        need("/mnt/lustre" not in open(os.path.join(HERE, f)).read(), "%s names a toolchain root of its own" % f)


@test("static: the composed production Lengau script (each direct body) carries exactly the production root and parses")
def t_compose():
    for body in ("activate_e2.sh", "rollover_pilot_v17.sh", "adopt_pilot17.sh", "check_v17.sh"):
        r = subprocess.run(["bash", "-c", '. "$1"; compose "$2"', "x", os.path.join(HERE, "lengau.sh"), body], capture_output=True, text=True)
        need(r.returncode == 0, "compose %s failed" % body, r.stderr)
        need(ROOT_LINE in r.stdout and r.stdout.count("T_ROOT=") == 1, "the composed %s does not carry exactly the production root" % body)
        p = subprocess.run(["bash", "-n"], input=r.stdout, capture_output=True, text=True); need(p.returncode == 0, "composed %s does not parse" % body, p.stderr)


@test("static: the package identities equal the reviewed ones (controls literal, map, builder, promoter, record) and the archive inventory is build_v17.ARCHIVE")
def t_identities():
    sys.path.insert(0, HERE)
    try:
        import v17_package as VP
    finally:
        sys.path.pop(0)
    for p, h in VP.PACKAGE.items():
        need(sha(os.path.join(LIVE_T1, p)) == h, "the live %s is not the pinned %s" % (p, h[:8]))
    need(sha(os.path.join(LIVE_T1, VP.REC)) == VP.REC_SHA, "the live review record is not 48b9cf05")
    need(VP.LITERAL in open(os.path.join(LIVE_T1, VP.REC)).read().splitlines(), "the review record lacks the literal")
    need(VP.LITERAL == "ADOPT row19-screen-controls sha256=9ea4e727c5d308457a2d5901ef6565522845fb31d52c3c1c0f7dd5a51a9d83c0 version=17", "literal")
    rl = open(os.path.join(HERE, "remote_lib.sh")).read()
    for k, v in (("V17_CONTROLS", V17_CONTROLS), ("V16_CONTROLS", V16_CONTROLS), ("V16_QUAL", V16_QUAL), ("E2_PART", E2_PART)):
        need("%s=%s" % (k, v) in rl, "remote_lib.sh %s is not %s" % (k, v[:8]))
    sys.path.insert(0, os.path.join(LIVE_T1, "chpc", "candidate_v17"))
    try:
        import build_v17 as B
    finally:
        sys.path.pop(0)
    m = re.search(r'^V16_REPLACED="(.*?)"$', rl, re.S | re.M)
    rep = dict(l.split(" ") for l in m.group(1).split("\n"))
    want = {d: B.PREVIOUS[d] for d, s, h, g in B.MAP if g == "pin" and B.PREVIOUS[d]}
    need(rep == want, "V16_REPLACED is not the five replaced pins of build_v17: %s" % rep)
    new = re.search(r'^V17_NEW="(.*?)"$', rl, re.M).group(1).split()
    need(sorted(new) == sorted(d for d, s, h, g in B.MAP if g in B.DEPLOY_GROUPS and B.PREVIOUS[d] is None), "V17_NEW is not the nine new deployed paths")
    need(len(B.ARCHIVE) == 13, "the builder's archive inventory is not 13 members")


@test("static: CTL_EVIDENCE (remote_lib.sh) and UNTRACKED_CTL (lengau_archive.py) are the same three pinned files")
def t_evidence_static():
    rl = open(os.path.join(HERE, "remote_lib.sh")).read()
    m = re.search(r'^CTL_EVIDENCE="(.*?)"$', rl, re.S | re.M); need(m is not None, "remote_lib.sh has no CTL_EVIDENCE")
    sh_list = dict(l.split(" ") for l in m.group(1).split("\n"))
    sys.path.insert(0, HERE)
    try:
        import lengau_archive as LA
    finally:
        sys.path.pop(0)
    want = {p: h for p, (_, h) in EVIDENCE.items()}
    need(sh_list == want and LA.UNTRACKED_CTL == want, "the allowlists differ")


LENGAU_BODIES = ["remote_lib.sh", "preflight_v17.sh", "archive_v16.sh", "deploy_v17.sh", "check_v17.sh", "activate_e2.sh",
                 "rollover_pilot_v17.sh", "adopt_pilot17.sh"]
PY37_MODULES = {"dataclasses", "contextvars", "importlib.resources", "zoneinfo", "graphlib", "tomllib", "importlib.metadata"}
PY37_ATTRS = {"isascii", "time_ns", "monotonic_ns", "perf_counter_ns", "nullcontext", "fromisoformat", "removeprefix", "removesuffix",
              "isqrt", "prod", "cache", "shlex_join", "is_relative_to"}


def py36_problems(src, name):
    """A conservative syntax/API scan for code newer than Python 3.6 (3.7 grammar plus a finite API blacklist; every f-string
    refused on the Lengau side). Not a 3.6 runtime certification (Codex mig_compat P3)."""
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
    for k in ("LOCK_PY", "ACT_PY", "INV_PY"):
        m = re.search(r"^%s='(.*?)'$" % k, rl, re.S | re.M); need(m is not None, "remote_lib.sh has no " + k)
        srcs["remote_lib.sh:" + k] = m.group(1)
    for f in LENGAU_BODIES:
        body = open(os.path.join(HERE, f)).read()
        i = body.find("<<'REMOTE'")
        if i >= 0:
            body = body[i:body.index("\nREMOTE\n", i)]
        for j, m in enumerate(re.finditer(r'"\$T/t1py" -c \'([^\']*)\'', body)):
            srcs["%s:t1py-c#%d" % (f, j + 1)] = m.group(1)
    return srcs


@test("Lengau compat: every Lengau-side Python (lengau_archive.py, LOCK_PY, ACT_PY, INV_PY, each t1py -c body) is 3.6-level code")
def t_py36():
    probe = "import subprocess, dataclasses\nr = subprocess.run(['x'], capture_output=True, text=True)\nprint(f'{r}')\n"
    need(len(py36_problems(probe, "probe")) == 4, "the scanner misses known 3.7+ features")
    srcs = lengau_python_sources()
    need(len([k for k in srcs if ":t1py-c#" in k]) >= 9, "expected the t1py -c bodies on the Lengau side: %s" % sorted(srcs))
    bad = [p for name, src in sorted(srcs.items()) for p in py36_problems(src, name)]
    need(not bad, "Lengau-side Python uses features newer than 3.6:\n" + "\n".join(bad))


@test("restricted-CLI shims: git rejects -C and echoes --absolute-git-dir; flock rejects -E and exits 1 on a -n conflict")
def t_shims():
    w = stage("fresh"); g = os.path.join(w.lbin, "git")
    r = subprocess.run([g, "-C", w.C, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    need(r.returncode == 129 and "Unknown option: -C" in r.stderr, "the git shim accepted -C")
    r = subprocess.run([g, "rev-parse", "--absolute-git-dir"], cwd=w.C, capture_output=True, text=True)
    need(r.returncode == 0 and r.stdout.strip() == "--absolute-git-dir", "the git shim does not echo --absolute-git-dir")
    w.fake("flock", FAKE_FLOCK); lk = os.path.join(w.L, "programme_admission.lock")
    r = subprocess.run([os.path.join(w.bin, "flock"), "-n", "-s", "-E", "75", lk, "true"], capture_output=True, text=True)
    need(r.returncode == 64, "the flock shim accepted -E")
    with Holder(lk):
        r = subprocess.run([os.path.join(w.bin, "flock"), "-n", "-s", lk, "true"], capture_output=True, text=True)
    need(r.returncode == 1, "the flock shim does not exit 1 on a -n conflict")


@test("boundary: a body run without the prelude refuses; lengau.sh refuses any other body; the harness refuses an alias of production")
def t_boundary():
    w = stage("fresh")
    for b in ("activate_e2.sh", "rollover_pilot_v17.sh", "adopt_pilot17.sh", "check_v17.sh"):
        rc, out = w.run("bash", "chpc/migration_v17/" + b); refused(rc, out)
        need("ABORT" not in out or "run through" in out or "sourced through" in out, "a body ran without the prelude", out)
    rc, out = w.script("lengau.sh", "preflight_v17.sh"); refused(rc, out, "runs only")
    rc, out = w.script("lengau.sh", "check_v17.sh"); refused(rc, out, "runs only")
    alias = os.path.join(w.d, "alias_prod"); os.symlink(PROD_ROOT, alias)
    try:
        w.install(alias); raise Fail("install accepted an alias of the production toolchain")
    except Fail as e:
        need("refusing" in str(e), str(e))
    w.install()


@test("boundary: a valid isolated fake root reached through an alias passes preflight (every path resolves beneath its physical root)")
def t_alias_root_ok():
    w = stage("fresh"); alias = os.path.join(w.d, "alias_root"); os.symlink(w.L, alias); w.install(alias)
    rc, out = w.script("preflight_v17.sh"); need(rc == 0 and "PREFLIGHT OK" in out, "preflight through a private alias", out)


# ================================================================================================ the positive route
@test("positive route: preflight, archive (+re-run), promote_v17 (+re-run), commit, deploy (+re-run), pre-cycle, activate (+re-run), post-cycle, rollover (+re-run), package, adopt")
def t_positive():
    w = stage("fresh")
    rc, out = w.script("preflight_v17.sh", "--local-only"); need(rc == 0 and "Lengau checks were NOT run" in out, "local-only", out)
    rc, out = w.script("preflight_v17.sh")
    need(rc == 0 and "PREFLIGHT OK" in out and "archive sources complete" in out and "lengau tools:" in out and "mac preflight OK" in out, "preflight", out)
    need("gate: scaleup_refit_v16.json present" in out, "preflight did not report the scale-up adoption", out)
    rc, out = w.script("archive_v16.sh", "--dry-run"); need(rc == 0 and "DRY RUN" in out and not os.path.exists(w.A), "archive dry run", out)
    rc, out = w.script("archive_v16.sh"); need(rc == 0 and "ARCHIVE OK" in out and "archive built" in out, "archive", out)
    need(set(os.listdir(w.A)) == {"COMPLETE", "SHA256SUMS", "INVENTORY.gate", "INVENTORY.jobs", "ctl", "gate", "jobs", "ledger", "ec2"}, "archive layout")
    need(os.path.isfile(os.path.join(w.A, "gate/scaleup_refit_v16.json")) and os.path.isfile(os.path.join(w.A, "ec2/activation_e1.json")), "gate/ec2 members")
    need(len(os.listdir(w.MA)) == 15 and os.path.isfile(w.LSF) and sha(w.LSF) == sha(os.path.join(w.A, "SHA256SUMS")), "Mac archive layout / Lengau sums copy")
    rc, out = w.script("archive_v16.sh"); need(rc == 0 and "exists and verifies" in out and "names this Lengau archive" in out, "archive re-run", out)
    rc, out = w.script("preflight_v17.sh"); refused(rc, out, "already exists")
    rc, out = w.promote("--check-promoted", "--review", REC); refused(rc, out, "not complete")
    rc, out = w.promote("--dry-run", "--review", REC); need(rc == 0 and "DRY RUN" in out, "promote dry run", out)
    rc, out = w.promote("--review", REC); need(rc == 0 and "promoted:" in out, "promote", out)
    rc, out = w.promote("--review", REC); need(rc == 0 and "already promoted, verified" in out, "promote re-run", out)
    rc, out = w.script("deploy_v17.sh", "--dry-run"); refused(rc, out, "not committed")
    w.commit_promotion()
    rc, out = w.script("deploy_v17.sh", "--dry-run"); need(rc == 0 and "DRY RUN" in out, "deploy dry run", out)
    jd = tree_digest(os.path.join(w.L, "rsc_screen")); jh = sh("git", "-C", os.path.join(w.L, "rsc_screen"), "rev-parse", "HEAD")
    h0 = sh("git", "-C", w.CR, "rev-parse", "HEAD").strip()
    rc, out = w.script("deploy_v17.sh")
    need(rc == 0 and "DEPLOY OK" in out and "science bytes UNCHANGED (8 files" in out and "IDENTICAL" in out and "activation HOLD" in out
         and "deploy proof written before any controller change" in out and "compile and the JSON payloads parse" in out, "deploy", out)
    need(tree_digest(os.path.join(w.L, "rsc_screen")) == jd and sh("git", "-C", os.path.join(w.L, "rsc_screen"), "rev-parse", "HEAD") == jh, "the job clone changed")
    cp = sh("git", "-C", w.CR, "diff", "--name-only", h0, "HEAD").split()
    need(len(cp) == 17 and all(not p.endswith(tuple(EVIDENCE)) for p in cp) and ctl_untracked(w) == sorted(T1_REL + "/" + p for p in EVIDENCE),
         "the deploy commit is not exactly the 17 payload paths, or the evidence became tracked: %s" % cp)
    need(sha(os.path.join(w.C, "chpc/row19_screen_controls.json")) == V17_CONTROLS and os.path.isfile(os.path.join(w.C, "aws_ec2/prod/panel_e2q_e2.json"))
         and os.path.isfile(os.path.join(w.C, "chpc/claims_snapshot_e2.json")), "the v17 bytes and data are not in the controller clone")
    need(not os.path.exists(os.path.join(w.C, "aws_ec2/prod_authority.py.v17tmp")) and sha(os.path.join(w.C, "aws_ec2/prod_authority.py")) ==
         "b8ca02b86bd42ebcdea15c823d0503f81c9a91978dfd3e0e4673028bdd8f5585", "the Mac-only aws_ec2 code was deployed")
    rc, out = w.script("deploy_v17.sh"); need(rc == 0 and "already holds exactly these v17 bytes" in out and "DEPLOY OK" in out, "deploy re-run", out)
    rc, out = w.script("lengau.sh", "activate_e2.sh"); refused(rc, out, "INVENTORY NOT USABLE")
    need(not os.path.exists(os.path.join(w.L, "activate.log")), "the activation was attempted without an installed inventory")
    stub_sync(w)
    rc, out = w.script("ec2_cycle_v17.sh", "post-activation"); refused(rc, out, "not on the root")
    rc, out = w.script("ec2_cycle_v17.sh", "pre-activation")
    need(rc == 0 and "PRE-ACTIVATION CYCLE OK" in out and "installed inventory: generation" in out, "pre-activation cycle", out)
    rc, out = w.script("lengau.sh", "rollover_pilot_v17.sh"); refused(rc, out, "activation")
    rc, out = w.script("lengau.sh", "activate_e2.sh"); need(rc == 0 and "ACTIVATED epoch 2" in out and "activation_problem ''" in out, "activate", out)
    rc, out = w.script("lengau.sh", "activate_e2.sh"); need(rc == 0 and "ALREADY ACTIVATED (verified)" in out, "activate re-run", out)
    need(open(os.path.join(w.L, "activate.log")).read().count("activate") == 1, "the activation command ran more than once")
    rc, out = w.script("ec2_cycle_v17.sh", "pre-activation"); refused(rc, out, "already exists")
    stub_receipts(w)
    rc, out = w.script("ec2_cycle_v17.sh", "post-activation"); need(rc == 0 and "RECEIPT OK" in out and "RECEIPTS OK" in out, "post cycle", out)
    rc, out = w.script("lengau.sh", "rollover_pilot_v17.sh"); need(rc == 0 and "retired to" in out, "rollover", out)
    need(not os.path.exists(os.path.join(w.G, "review_refit.json")) and os.path.isfile(os.path.join(w.G, "scaleup_refit_v16.json")), "rollover moved the wrong file")
    rc, out = w.script("lengau.sh", "rollover_pilot_v17.sh"); need(rc == 0 and "already retired (verified)" in out, "rollover re-run", out)
    rc, out = w.script("package_qual_v17.py"); refused(rc, out, "still the v16 2c7a7ef1")
    qsha = fake_qualification(w)
    rc, out = w.script("package_qual_v17.py"); need(rc == 0 and "packaged" in out and qsha in out, "package", out)
    pd = os.path.join(w.t1, "chpc", "qualification_v17_" + qsha[:8])
    need(sorted(os.listdir(pd)) == sorted(["SHA256SUMS", "qualified_refit_job1.json", "verify_refit_20261020T101010Z.json", "watch_refit_20261020T101010Z.json",
         "watch_refit_20261017T204309Z.json", "mac_archive_v16_before_v17.SHA256SUMS", "lengau_archive_v16_before_v17.SHA256SUMS.txt"]), "package layout %s" % os.listdir(pd))
    rc, out = w.script("package_qual_v17.py"); need(rc == 0 and "exists and verifies" in out, "package re-run", out)
    rec = pilot_record(w, qsha)
    rc, out = w.script("lengau.sh", "adopt_pilot17.sh", "--file", rec); need(rc == 0 and "adopt_pilot17 complete" in out, "adopt", out)
    need(json.load(open(os.path.join(w.G, "review_refit.json")))["qualification_sha256"] == qsha, "the simulated adopter wrote another review")
    rc, out = w.script("lengau.sh", "adopt_pilot17.sh", "--file", rec); refused(rc, out, "an active review exists")
    need(w.net_log() == "", "something tried ssh/scp: " + w.net_log())


@test("Lengau compat: the whole route runs on the restricted git and flock CLIs (no rejected call, no python fallback for a decidable lock)")
def t_lengau_route():
    w = stage("fresh"); w.fake("flock", FAKE_FLOCK)
    rc, out = w.script("preflight_v17.sh"); need(rc == 0 and "PREFLIGHT OK" in out and "trying the python fcntl probe" not in out, "preflight", out)
    rc, out = w.script("archive_v16.sh"); need(rc == 0 and "ARCHIVE OK" in out, "archive", out)
    rc, out = w.promote("--review", REC); need(rc == 0, "promote", out); w.commit_promotion()
    rc, out = w.script("deploy_v17.sh"); need(rc == 0 and "DEPLOY OK" in out, "deploy", out)
    rc, out = w.script("deploy_v17.sh"); need(rc == 0 and "DEPLOY OK" in out, "deploy re-run", out)
    stub_sync(w); rc, out = w.script("ec2_cycle_v17.sh", "pre-activation"); need(rc == 0, "pre-cycle", out)
    rc, out = w.script("lengau.sh", "activate_e2.sh"); need(rc == 0 and "ACTIVATED" in out, "activate", out)
    stub_receipts(w); rc, out = w.script("ec2_cycle_v17.sh", "post-activation"); need(rc == 0, "post-cycle", out)
    rc, out = w.script("lengau.sh", "rollover_pilot_v17.sh"); need(rc == 0, "rollover", out)
    qsha = fake_qualification(w); rec = pilot_record(w, qsha)
    rc, out = w.script("lengau.sh", "adopt_pilot17.sh", "--file", rec); need(rc == 0, "adopt", out)
    log = open(os.path.join(w.lbin, "git.log")).read()
    for want in ("rev-parse --show-toplevel", "rev-parse --git-dir", "status --porcelain --untracked-files=all", "rev-parse --verify HEAD",
                 "merge-base --is-ancestor", "diff-tree --no-commit-id --name-only -r", "ls-files"):
        need(want in log, "the Lengau half never ran `git %s` through the restricted shim" % want, log[-2000:])
    need(not os.path.exists(os.path.join(w.lbin, "git.rejected")), "a Lengau-side git call used a rejected interface",
         open(os.path.join(w.lbin, "git.rejected")).read() if os.path.exists(os.path.join(w.lbin, "git.rejected")) else "")
    need("trying the python fcntl probe" not in out, "a decidable lock fell back to python", out)


# ================================================================================================ step 1: preflight
@test("preflight refuses (Mac): a changed package byte (promoter, builder, map), an uncommitted record, a held authority lock, a busy Mac")
def t_preflight_mac():
    for rel in ("chpc/candidate_v17/promote_v17.py", "chpc/candidate_v17/build_v17.py", "chpc/candidate_v17/v17_promotion_map.json"):
        w = stage("fresh"); open(os.path.join(w.t1, rel), "a").write("\n")
        rc, out = w.script("preflight_v17.sh"); refused(rc, out, rel, "not the reviewed")
    w = stage("fresh"); p = os.path.join(w.t1, REC); open(p, "a").write("x\n")
    rc, out = w.script("preflight_v17.sh"); refused(rc, out, "not the reviewed record")
    w = stage("fresh")
    with Holder(os.path.join(w.t1, "aws_ec2/runs/.authority.lock")):
        rc, out = w.script("preflight_v17.sh")
    refused(rc, out, "authority lock")
    for line in ("python3 aws_ec2/ec2_sync.py cycle", "caffeinate -i python3 aws_ec2/bench_reaper.py --run qual-E2Q1", "bash refill_r1.sh"):
        w = stage("fresh"); write(os.path.join(w.bin, "ps_x.out"), "bash -s\n%s\n" % line)
        rc, out = w.script("preflight_v17.sh"); refused(rc, out, "runs on the Mac")
    w = stage("fresh"); write(os.path.join(w.bin, "ps_x.rc"), "1"); rc, out = w.script("preflight_v17.sh"); refused(rc, out, "Mac process inventory failed")


@test("preflight refuses (Mac): live tree not v16 (a promoted path changed / a v17 path present), Mac qualification not 2c7a7ef1, uncommitted budget")
def t_preflight_mac_state():
    w = stage("fresh"); write(os.path.join(w.t1, "chpc/row19_ec2_e2rules.py"), "# early\n")
    rc, out = w.script("preflight_v17.sh"); refused(rc, out, "row19_ec2_e2rules.py")
    w = stage("fresh"); open(os.path.join(w.t1, "aws_ec2/qual_permit.py"), "a").write("# x\n")
    rc, out = w.script("preflight_v17.sh"); refused(rc, out, "qual_permit.py")
    w = stage("fresh"); write(os.path.join(w.t1, "chpc/results/row19_screen/receipts/qualified_refit_job1.json"), "{}\n")
    rc, out = w.script("preflight_v17.sh"); refused(rc, out, "2c7a7ef1")
    w = stage("fresh"); open(os.path.join(w.t1, "chpc/row19_screen_budget.json"), "a").write(" ")
    rc, out = w.script("preflight_v17.sh"); refused(rc, out, "row19_screen_budget.json")


@test("preflight refuses (Lengau): an e2 path already in the controller, activation_e2 present, review not bound to 2c7a7ef1, ledger cap not 81,000, leftovers")
def t_preflight_lengau():
    w = stage("fresh"); write(os.path.join(w.C, "chpc/claims_snapshot_e2.json"), "{}\n")
    sh("git", "-C", w.CR, "add", "--", T1_REL + "/chpc/claims_snapshot_e2.json"); gitc(w.CR, "commit", "-q", "-m", "x")
    rc, out = w.script("preflight_v17.sh"); refused(rc, out, "claims_snapshot_e2.json")
    w = stage("fresh"); write(w.ACT2, "{}\n"); rc, out = w.script("preflight_v17.sh"); refused(rc, out, "activation_e2.json")
    w = stage("fresh"); write(os.path.join(w.G, "review_refit.json"), "{}\n"); rc, out = w.script("preflight_v17.sh"); refused(rc, out, "not bound to qualification 2c7a7ef1")
    w = stage("fresh"); write(os.path.join(w.L, "row19_screen_campaign/budget.json"), json.dumps({"cap_core_h": 60000.0}))
    rc, out = w.script("preflight_v17.sh"); refused(rc, out, "81,000")
    w = stage("fresh"); os.makedirs(os.path.join(w.L, "archive_screen/v17_deploy_proof")); rc, out = w.script("preflight_v17.sh"); refused(rc, out, "v17 deploy proof")
    w = stage("fresh"); os.makedirs(os.path.join(w.L, "archive_screen/.v16_before_v17.staging.9")); rc, out = w.script("preflight_v17.sh"); refused(rc, out, "interrupted archive build")
    w = stage("fresh"); write(os.path.join(w.R, "review_refit.v16_qual2c7a7ef1_max100.json"), "{}\n"); rc, out = w.script("preflight_v17.sh"); refused(rc, out, "retirement target")
    w = stage("fresh"); os.remove(os.path.join(w.GS, "ec2/activation_e1.json")); rc, out = w.script("preflight_v17.sh"); refused(rc, out, "epoch-1 activation proof")


# ================================================================================================ step 2: archives
@test("archive: one-file remote archive refuses and is left as it was; missing ledger / e1 proof / controller file / review / jobs refuse")
def t_archive_incomplete():
    w = stage("fresh"); write(os.path.join(w.A, "gate/qualified_refit_job1.json"), open(os.path.join(w.G, "qualified_refit_job1.json"), "rb").read())
    write(os.path.join(w.A, "SHA256SUMS"), "%s  ./gate/qualified_refit_job1.json\n" % V16_QUAL); before = tree_digest(w.A)
    rc, out = w.script("archive_v16.sh"); refused(rc, out, "does not verify as complete")
    need(tree_digest(w.A) == before and not os.path.exists(w.MA), "the partial archive changed, or the Mac half ran")
    w = stage("fresh"); os.remove(os.path.join(w.L, "row19_screen_campaign/budget.json")); rc, out = w.script("archive_v16.sh"); refused(rc, out, "missing")
    need(not os.path.exists(w.A) and not os.path.exists(w.MA), "published without the ledger")
    for f in ("chpc/row22_bank_submit.py", "chpc/row19_screen_verify.py", "chpc/row19_partition_e1.json"):
        w = stage("fresh"); sh("git", "-C", w.CR, "rm", "-q", "--", T1_REL + "/" + f); gitc(w.CR, "commit", "-q", "-m", "x")
        rc, out = w.script("archive_v16.sh"); refused(rc, out)
        need(not os.path.exists(w.A) and not os.path.exists(w.MA), "an archive was published without " + f)
    w = stage("fresh"); os.remove(os.path.join(w.G, "review_refit.json")); rc, out = w.script("archive_v16.sh"); refused(rc, out, "review_refit.json")
    w = stage("fresh"); [os.remove(os.path.join(w.L, "jobs", f)) for f in os.listdir(os.path.join(w.L, "jobs"))]
    rc, out = w.script("archive_v16.sh"); refused(rc, out, "no refit job scripts")


@test("archive: failed checksum / unreadable source refuse; an interrupted build (staging left, Lengau or Mac) refuses and is never removed")
def t_archive_interrupted():
    w = stage("fresh"); write(os.path.join(w.bin, "sha.fail"), "qualified_refit_job1"); rc, out = w.script("archive_v16.sh"); refused(rc, out, "cannot hash")
    need(not os.path.exists(w.A), "published after a failed checksum command")
    w = stage("fresh"); os.chmod(os.path.join(w.G, "watch_refit_1.json"), 0)
    rc, out = w.script("archive_v16.sh"); os.chmod(os.path.join(w.G, "watch_refit_1.json"), 0o644); refused(rc, out, "unreadable")
    need(not os.path.exists(w.A) and not [x for x in os.listdir(os.path.join(w.L, "archive_screen")) if "staging" in x], "published or left staging")
    w = stage("fresh"); stg = os.path.join(w.L, "archive_screen/.v16_before_v17.staging.4242"); write(os.path.join(stg, "gate/x"), "partial\n"); before = tree_digest(stg)
    rc, out = w.script("archive_v16.sh"); refused(rc, out, "interrupted archive build")
    need(tree_digest(stg) == before and not os.path.exists(w.A), "the staging evidence changed")
    w = stage("fresh"); os.makedirs(os.path.join(w.t1, "chpc/results/archive/.row19_screen_v16_before_v17.staging.7"))
    rc, out = w.script("archive_v16.sh"); refused(rc, out, "interrupted Mac archive build"); need(not os.path.exists(w.A), "the Lengau half ran")


@test("archive retry: the Lengau half published but the Mac half failed (budget mismatch) -> nothing on the Mac; repaired, the re-run builds the Mac half")
def t_archive_retry_mac_half():
    w = stage("fresh"); p = os.path.join(w.C, "chpc/row19_screen_budget.json"); orig = open(p, "rb").read()
    write(p, orig.replace(b"81000", b"81000 ") if b"81000" in orig else orig + b" "); gitc(w.CR, "commit", "-q", "-am", "TEST another budget")
    rc, out = w.script("archive_v16.sh"); refused(rc, out, "budget phases")
    need(os.path.isdir(w.A) and not os.path.exists(w.MA) and not os.path.exists(w.LSF), "the Lengau archive was not kept, or the Mac half was written")
    # the Lengau archive certifies the controller's budget; the recovery is to make the Mac and controller budgets agree in a
    # NEW archive - here (private) the archive is set aside and the controller budget restored, then the whole step re-runs
    unlock_tree(w.A); shutil.rmtree(w.A); write(p, orig); gitc(w.CR, "commit", "-q", "-am", "TEST budget restored")
    rc, out = w.script("archive_v16.sh"); need(rc == 0 and "ARCHIVE OK" in out, "archive after recovery", out)
    w = stage("fresh"); rc, out = w.script("archive_v16.sh"); need(rc == 0, "archive", out)
    unlock_tree(w.MA); shutil.rmtree(w.MA); os.remove(w.LSF)        # an interruption after the Lengau half: no Mac half yet
    rc, out = w.script("archive_v16.sh"); need(rc == 0 and "exists and verifies" in out and "Mac archive" in out and os.path.isdir(w.MA) and os.path.isfile(w.LSF), "Mac half resumed", out)


@test("archive: a self-consistently rewritten Lengau archive (ledger or e1 proof dropped) and a substituted Mac member refuse")
def t_archive_subset():
    sys.path.insert(0, HERE)
    try:
        import lengau_archive as LA
    finally:
        sys.path.pop(0)
    for drop in ("ledger", "ec2", "ctl/chpc/row22_bank_submit.py"):
        w = stage("archived"); unlock_tree(w.A); p = os.path.join(w.A, drop)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
        sums = {}
        for d, _, files in os.walk(w.A):
            for n in files:
                rel = os.path.relpath(os.path.join(d, n), w.A)
                if rel not in ("SHA256SUMS", "COMPLETE"):
                    sums[rel] = sha(os.path.join(d, n))
        sb = LA.sums_text(sums).encode(); write(os.path.join(w.A, "SHA256SUMS"), sb)
        c = open(os.path.join(w.A, "COMPLETE")).read().splitlines()
        write(os.path.join(w.A, "COMPLETE"), "\n".join([c[0], "sha256sums " + hashlib.sha256(sb).hexdigest()] + c[2:]) + "\n")
        for d, _, files in os.walk(w.A):
            for n in files:
                os.chmod(os.path.join(d, n), 0o444)
        rc, out = w.script("archive_v16.sh"); refused(rc, out, "does not verify as complete")
    w = stage("archived"); os.chmod(w.MA, 0o755)
    for n in os.listdir(w.MA):
        os.chmod(os.path.join(w.MA, n), 0o644)
    write(os.path.join(w.MA, "row19_ec2_state.py"), "# substituted\n")
    sums = {n: sha(os.path.join(w.MA, n)) for n in os.listdir(w.MA) if n not in ("SHA256SUMS", "COMPLETE")}
    sb = "".join("%s  %s\n" % (sums[k], k) for k in sorted(sums)).encode(); write(os.path.join(w.MA, "SHA256SUMS"), sb)
    comp = json.load(open(os.path.join(w.MA, "COMPLETE"))); comp["sha256sums"] = hashlib.sha256(sb).hexdigest()
    write(os.path.join(w.MA, "COMPLETE"), json.dumps(comp, indent=1, sort_keys=True) + "\n")
    for n in os.listdir(w.MA):
        os.chmod(os.path.join(w.MA, n), 0o444)
    rc, out = w.script("archive_v16.sh"); refused(rc, out, "does not verify")
    rc, out = w.promote("--dry-run", "--review", REC); refused(rc, out)


@test("Mac archive: writable member, foreign COMPLETE, extra file refuse the strict verify; the builder's archive_problems accepts the real one")
def t_mac_archive_strict():
    w = stage("archived"); rc, out = w.script("mac_archive.py", "verify"); need(rc == 0 and "archive_problems: []" in out, "verify", out)
    p = os.path.join(w.MA, "row19_screen_budget.json"); os.chmod(p, 0o644)
    rc, out = w.script("mac_archive.py", "verify"); refused(rc, out, "writable")
    w = stage("archived"); os.chmod(w.MA, 0o755); p = os.path.join(w.MA, "COMPLETE"); os.chmod(p, 0o644)
    write(p, "schema row19-screen-mac-archive-v15-before-v16-1\n", 0o444); rc, out = w.script("mac_archive.py", "verify"); refused(rc, out, "COMPLETE")
    w = stage("archived"); os.chmod(w.MA, 0o755); write(os.path.join(w.MA, "notes.txt"), "x\n", 0o444)
    rc, out = w.script("mac_archive.py", "verify"); refused(rc, out, "not exactly the 13 members")


# ================================================================================================ step 3: promotion (promote_v17.py)
@test("promote interruption: a promotion stopped after the controls copy (adoption still v16) - deploy refuses; promote_v17 resumes; deploy proceeds")
def t_promote_interrupted():
    w = stage("archived")
    sys.path.insert(0, os.path.join(w.t1, "chpc", "candidate_v17"))
    try:
        import importlib
        for m in ("build_v17", "promote_v17"):
            sys.modules.pop(m, None)
        PV = importlib.import_module("promote_v17")
        order = PV.order()
    finally:
        sys.path.pop(0)
        for m in ("build_v17", "promote_v17"):
            sys.modules.pop(m, None)
    for r in order:                                   # exactly what the real promoter copies, controls last, then STOP (no adoption)
        write(os.path.join(w.t1, r["promoted"]), open(os.path.join(w.t1, r["source"]), "rb").read())
    rc, out = w.promote("--check-promoted", "--review", REC); refused(rc, out, "not complete", "adoption=v16")
    rc, out = w.script("deploy_v17.sh", "--dry-run"); refused(rc, out, "not complete")
    rc, out = w.promote("--review", REC); need(rc == 0 and "promoted:" in out and "adoption" in out, "promote resume", out)
    w.commit_promotion()
    rc, out = w.script("deploy_v17.sh"); need(rc == 0 and "DEPLOY OK" in out, "deploy after the resumed promotion", out)


# ================================================================================================ step 4: deploy
@test("deploy refuses before any controller change: one-file / corrupted / regenerated Lengau archive, uncommitted promotion, changed e2 data on the Mac")
def t_deploy_archive():
    def onefile(w):
        unlock_tree(w.A); shutil.rmtree(w.A)
        write(os.path.join(w.A, "gate/qualified_refit_job1.json"), open(os.path.join(w.G, "qualified_refit_job1.json"), "rb").read())
        write(os.path.join(w.A, "SHA256SUMS"), "%s  ./gate/qualified_refit_job1.json\n" % V16_QUAL)
    def flip(w):
        p = os.path.join(w.A, "gate/review_refit.json"); os.chmod(p, 0o644); open(p, "a").write(" "); os.chmod(p, 0o444)
    def nocomplete(w):
        os.chmod(w.A, 0o755); os.remove(os.path.join(w.A, "COMPLETE"))
    for mut in (onefile, flip, nocomplete):
        w = stage("promoted"); mut(w); s0 = w.ctl_state()
        rc, out = w.script("deploy_v17.sh"); refused(rc, out, "does not verify as complete")
        need(w.ctl_state() == s0 and not os.path.lexists(w.PROOF), "the controller clone changed after %s" % mut.__name__)
    w = stage("promoted"); open(os.path.join(w.t1, "chpc/claims_snapshot_e2.json"), "a").write(" "); s0 = w.ctl_state()
    rc, out = w.script("deploy_v17.sh"); refused(rc, out); need(w.ctl_state() == s0, "deployed changed data")
    w = stage("archived"); rc, out = w.promote("--review", REC); need(rc == 0, "promote", out); s0 = w.ctl_state()
    rc, out = w.script("deploy_v17.sh"); refused(rc, out, "not committed"); need(w.ctl_state() == s0, "deployed an uncommitted promotion")


@test("deploy: drain observations (ps failed/empty/busy, a held lock, no probe) refuse before any controller change")
def t_deploy_drain():
    cases = [("ps_u.rc", "23", "process inventory failed"), ("ps_u.out", "", "process inventory is empty"),
             ("ps_u.out", "bash -s\n/x/t1py chpc/programme_gate.py settle --manifest m -- t1py chpc/row19_ledger.py settle\n", "a controller command runs")]
    for f, data, msg in cases:
        w = stage("promoted"); write(os.path.join(w.bin, f), data); s0 = w.ctl_state()
        rc, out = w.script("deploy_v17.sh"); refused(rc, out, msg); need(w.ctl_state() == s0 and not os.path.lexists(w.PROOF), "changed: " + msg)
    for with_flock in (False, True):
        w = stage("promoted"); s0 = w.ctl_state()
        if with_flock:
            w.fake("flock", FAKE_FLOCK)
        with Holder(os.path.join(w.GS, "plans/.submit.lock")):
            rc, out = w.script("deploy_v17.sh")
        refused(rc, out, "lock held"); need(w.ctl_state() == s0, "deployed under a held lock")
    w = stage("promoted"); write(os.path.join(w.L, "t1py.nofcntl"), ""); w.fake("flock", BROKEN_FLOCK)
    rc, out = w.script("deploy_v17.sh"); refused(rc, out, "no reliable lock probe")


@test("deploy: missing/unreadable/digest-failed/partial science refuses before any change; a changed or incomplete after-proof refuses completion")
def t_deploy_science():
    w = stage("promoted"); os.remove(os.path.join(w.J, "analyze.py")); s0 = w.ctl_state()
    rc, out = w.script("deploy_v17.sh"); refused(rc, out, "science input missing or unreadable: analyze.py"); need(w.ctl_state() == s0, "changed")
    w = stage("promoted"); write(os.path.join(w.bin, "sha.fail"), "simulate.py"); s0 = w.ctl_state()
    rc, out = w.script("deploy_v17.sh"); refused(rc, out, "science digest command failed"); need(w.ctl_state() == s0, "changed")
    w = stage("promoted"); write(os.path.join(w.bin, "sha.partial"), "row19_slice.py"); s0 = w.ctl_state()
    rc, out = w.script("deploy_v17.sh"); refused(rc, out, "incomplete or malformed"); need(w.ctl_state() == s0, "changed")
    for hook, msg in (('echo "# drift" >> "%s/analyze.py"', "science bytes changed"), ('rm -f "%s/simulate.py"', "after-proof is incomplete")):
        w = stage("promoted"); write(os.path.join(w.CR, ".git/hooks/post-commit"), "#!/bin/bash\n" + hook % w.J + "\n", 0o755)
        rc, out = w.script("deploy_v17.sh"); refused(rc, out, msg); need("DEPLOY OK" not in out, "deploy reported OK", out)
        names = os.listdir(w.PROOF)
        need("intent" in names and "DONE" not in names and [n for n in names if n.startswith("after_failed.")], "proof evidence %s" % names)
        jd = tree_digest(os.path.join(w.L, "rsc_screen")); pdd = tree_digest(w.PROOF)
        for _ in range(2):
            rc, out = w.script("deploy_v17.sh")
            refused(rc, out, "already holds exactly these v17 bytes", "DEPLOY HELD", "after-proof is unresolved"); need("DEPLOY OK" not in out, "a re-run reported OK", out)
        need(tree_digest(os.path.join(w.L, "rsc_screen")) == jd and tree_digest(w.PROOF) == pdd, "a re-run changed the science or the proof")


@test("deploy retry: a copy failure resumes on the pre-mutation proof; a mid-payload failure / a refused commit leave a dirty clone every re-run refuses")
def t_deploy_retry():
    w = stage("promoted"); s0 = w.ctl_state()
    w.fake("cp", '#!/bin/bash\nfor a in "$@"; do case $a in *.v17tmp) echo "cp: simulated failure" >&2; exit 1;; esac; done\nexec /bin/cp "$@"\n')
    rc, out = w.script("deploy_v17.sh"); refused(rc, out, "copy of"); need(w.ctl_state() == s0, "the controller clone changed", out)
    need(sorted(os.listdir(w.PROOF)) == ["intent", "science_before.sha256"], "the pre-mutation proof is not exactly intent + manifest")
    os.remove(os.path.join(w.bin, "cp"))
    rc, out = w.script("deploy_v17.sh"); need(rc == 0 and "reusing the pre-mutation proof" in out and "DEPLOY OK" in out, "resume", out)
    w = stage("promoted")
    w.fake("cp", '#!/bin/bash\nfor a in "$@"; do case $a in *row19_ec2_qualify.py.v17tmp) echo "cp: simulated failure" >&2; exit 1;; esac; done\nexec /bin/cp "$@"\n')
    rc, out = w.script("deploy_v17.sh"); refused(rc, out, "copy of chpc/row19_ec2_qualify.py failed")
    need(ctl_dirty(w) != [], "a mid-payload failure did not leave the clone dirty")
    os.remove(os.path.join(w.bin, "cp"))
    rc, out = w.script("deploy_v17.sh"); refused(rc, out, "uncommitted changes or untracked files"); need("DEPLOY OK" not in out, "OK on a dirty clone", out)
    w = stage("promoted"); write(os.path.join(w.CR, ".git/hooks/pre-commit"), "#!/bin/bash\nexit 1\n", 0o755); h0 = w.ctl_state()[0]
    rc, out = w.script("deploy_v17.sh"); refused(rc, out, "git commit failed"); need(w.ctl_state()[0] == h0 and ctl_dirty(w) != [], "commit failure state")
    os.remove(os.path.join(w.CR, ".git/hooks/pre-commit"))
    rc, out = w.script("deploy_v17.sh"); refused(rc, out, "uncommitted changes")


@test("deploy retry: a deployed clone without its proof, with science changed after DONE, or a tampered preserved manifest HOLDS; DONE + equal science is OK")
def t_deploy_proof_binding():
    w = stage("deployed"); rc, out = w.script("deploy_v17.sh"); need(rc == 0 and "current manifest equals the preserved" in out and "DEPLOY OK" in out, "re-run", out)
    w = stage("deployed"); unlock_tree(w.PROOF); shutil.rmtree(w.PROOF)
    rc, out = w.script("deploy_v17.sh"); refused(rc, out, "DEPLOY HELD", "no deploy proof")
    w = stage("deployed"); open(os.path.join(w.J, "analyze.py"), "a").write("# later drift\n")
    rc, out = w.script("deploy_v17.sh"); refused(rc, out, "DEPLOY HELD", "differ from the preserved pre-mutation manifest")
    w = stage("deployed"); os.chmod(w.PROOF, 0o755); p = os.path.join(w.PROOF, "science_before.sha256"); os.chmod(p, 0o644)
    open(p, "a").write("0" * 64 + "  extra\n"); os.chmod(p, 0o444)
    rc, out = w.script("deploy_v17.sh"); refused(rc, out, "DEPLOY HELD", "not the one its intent record certifies")
    w = stage("deployed"); os.chmod(w.PROOF, 0o755); p = os.path.join(w.PROOF, "DONE"); os.chmod(p, 0o644)
    write(p, open(p).read().replace("science_after ", "science_after 0"), 0o444)
    rc, out = w.script("deploy_v17.sh"); refused(rc, out, "DEPLOY HELD", "does not bind this payload")
    d = open(os.path.join(stage("deployed").PROOF, "DONE")).read()
    m = dict(l.split(" ", 1) for l in d.strip().split("\n"))
    need(m["science_after"] == m["science_before"] and len(m["science_after"]) == 64, "DONE does not carry the proven-equal science digest: %s" % m)


@test("deploy: payload that does not compile/parse under t1py, or a v17 path already in the controller, refuses before any change")
def t_deploy_payload_checks():
    w = stage("promoted")
    t1 = open(os.path.join(w.L, "t1py")).read().replace('  -c) exec python3 "$@";;',
                                                         '  -c) case "${2:-}" in *"compile(open(sys.argv[1]"*) echo "SyntaxError (simulated)" >&2; exit 1;; esac; exec python3 "$@";;')
    write(os.path.join(w.L, "t1py"), t1, 0o755); s0 = w.ctl_state()
    rc, out = w.script("deploy_v17.sh"); refused(rc, out, "does not compile under"); need(w.ctl_state() == s0 and not os.path.lexists(w.PROOF), "changed")
    w = stage("promoted"); write(os.path.join(w.C, "chpc/row19_ec2_e2rules.py"), "# early\n")
    sh("git", "-C", w.CR, "add", "--", T1_REL + "/chpc/row19_ec2_e2rules.py"); gitc(w.CR, "commit", "-q", "-m", "x"); s0 = w.ctl_state()
    rc, out = w.script("deploy_v17.sh"); refused(rc, out); need(w.ctl_state() == s0 and not os.path.lexists(w.PROOF), "changed")


# ================================================================================================ containment
@test("containment: controller clone, gate, archive dir, ec2 dir or a gate member pointing outside refuse; nothing written outside")
def t_escape():
    w = stage("fresh"); tgt = os.path.join(w.outside, "rsc_screen_ctl"); os.rename(w.CR, tgt); os.symlink(tgt, w.CR); before = tree_digest(w.outside)
    rc, out = w.script("preflight_v17.sh"); refused(rc, out, "not its own physical path")
    rc, out = w.script("archive_v16.sh"); refused(rc, out, "not its own physical path")
    need(tree_digest(w.outside) == before and not os.path.exists(w.MA), "wrote outside or built the Mac half")
    w = stage("fresh"); a = os.path.join(w.L, "archive_screen"); tgt = os.path.join(w.outside, "archive_screen"); os.rmdir(a); os.makedirs(tgt); os.symlink(tgt, a)
    rc, out = w.script("archive_v16.sh"); refused(rc, out, "not its own physical path"); need(os.listdir(tgt) == [], "wrote into the outside archive dir")
    w = stage("fresh"); write(os.path.join(w.outside, "x.json"), "{}\n"); os.symlink(os.path.join(w.outside, "x.json"), os.path.join(w.G, "x.json"))
    rc, out = w.script("archive_v16.sh"); refused(rc, out, "symlink")
    w = stage("precycled"); e = os.path.join(w.GS, "ec2"); tgt = os.path.join(w.outside, "ec2"); shutil.copytree(e, tgt); shutil.rmtree(e); os.symlink(tgt, e)
    before = tree_digest(w.outside)
    rc, out = w.script("lengau.sh", "activate_e2.sh"); refused(rc, out, "not its own physical path")
    need(tree_digest(w.outside) == before and not os.path.exists(os.path.join(w.L, "activate.log")), "the activation ran or wrote outside")


@test("containment: a committed nested chpc / reviews / aws_ec2 redirect refuses deploy and adopt before any copy")
def t_nested():
    for rel, msg in (("chpc", "payload 2"), ("reviews", "payload 1"), ("aws_ec2", "payload")):
        w = stage("promoted"); tgt = os.path.join(w.outside, "ctl_" + rel); commit_redirect(w, rel, tgt)
        before = tree_digest(w.outside); s0 = w.ctl_state()
        rc, out = w.script("deploy_v17.sh"); refused(rc, out, "not its own physical path", msg)
        need(tree_digest(w.outside) == before and w.ctl_state() == s0 and not os.path.lexists(w.PROOF), "deploy wrote before refusing (%s)" % rel)
    w = stage("qualified"); qsha = sha(os.path.join(w.G, "qualified_refit_job1.json")); rec = pilot_record(w, qsha)
    tgt = os.path.join(w.outside, "ctl_reviews"); commit_redirect(w, "reviews", tgt); before = tree_digest(w.outside)
    rc, out = w.script("lengau.sh", "adopt_pilot17.sh", "--file", rec); refused(rc, out, "not its own physical path")
    need(tree_digest(w.outside) == before and not os.path.lexists(os.path.join(w.G, "review_refit.json")), "adopt wrote before refusing")
    w = stage("promoted"); victim = os.path.join(w.outside, "victim.py"); write(victim, "outside bytes\n")
    write(os.path.join(w.CR, ".git", "info", "exclude"), "*.v17tmp\n")
    os.symlink(victim, os.path.join(w.C, "chpc/row19_ec2_state.py.v17tmp")); s0 = w.ctl_state()
    rc, out = w.script("deploy_v17.sh"); refused(rc, out, "temporary sibling")
    need(open(victim).read() == "outside bytes\n" and w.ctl_state() == s0 and not os.path.lexists(w.PROOF), "the sibling was followed")


@test("containment: a controller alias resolving inside the scientific clone refuses every body; scientific bytes unchanged")
def t_ctl_alias_science():
    def alias_whole(w):
        os.rename(w.CR, os.path.join(w.L, "ctl_moved_aside")); os.symlink(os.path.join(w.L, "rsc_screen"), w.CR)
    for name, runs in (("fresh", [("preflight_v17.sh",), ("archive_v16.sh",)]), ("promoted", [("deploy_v17.sh",)]),
                       ("precycled", [("lengau.sh", "activate_e2.sh")]), ("postcycled", [("lengau.sh", "rollover_pilot_v17.sh")])):
        w = stage(name); alias_whole(w)
        jd = tree_digest(os.path.join(w.L, "rsc_screen")); gd = tree_digest(w.G)
        for r in runs:
            rc, out = w.script(*r); refused(rc, out, "not its own physical path")
        need(tree_digest(os.path.join(w.L, "rsc_screen")) == jd and tree_digest(w.G) == gd, "the science clone or gate changed (%s)" % name)


@test("controller git: a gitfile or symlinked .git refuses (own-root semantics on the restricted git)")
def t_ctl_git():
    for kind in ("gitfile", "symlink"):
        w = stage("fresh"); gd = os.path.join(w.CR, ".git"); moved = os.path.join(w.outside, "ctl.git"); shutil.move(gd, moved)
        write(gd, "gitdir: %s\n" % moved) if kind == "gitfile" else os.symlink(moved, gd)
        rc, out = w.script("preflight_v17.sh"); refused(rc, out, "git directory is"); need("Unknown option" not in out, "used -C", out)
    w = stage("fresh"); write(os.path.join(w.CR, ".git/index"), b"garbage, not an index")
    rc, out = w.script("preflight_v17.sh"); refused(rc, out, "git status failed")


# ================================================================================================ evidence allowlist
@test("evidence: the exact three pass and are archived with their hashes; a fourth file, a changed hash, a symlink, a newline-named entry refuse")
def t_evidence():
    w = stage("archived")
    for p, (_, h) in EVIDENCE.items():
        need(sha(os.path.join(w.A, "ctl/untracked", p)) == h, "evidence %s not archived with its hash" % p)
    muts = []
    muts.append(("fourth", lambda w: write(os.path.join(w.C, "aws_ec2/runs/b2/extra.json"), "{}\n")))
    muts.append(("hash", lambda w: open(os.path.join(w.C, "aws_ec2/ec2_release_state.json"), "a").write(" ")))
    def symlinked(w):
        p = os.path.join(w.C, "reviews/2026-10-11_d1d2_f3_codex_record.md"); q = os.path.join(w.outside, "rec.md")
        shutil.move(p, q); os.symlink(q, p)
    muts.append(("symlink", symlinked))
    muts.append(("newline-dir", lambda w: os.makedirs(os.path.join(w.C, "aws_ec2/runs/b2/bench_report_attempt_5_20261011T185715Z.json\n"))))
    muts.append(("stray-dir", lambda w: os.makedirs(os.path.join(w.C, "aws_ec2/runs/stray"))))
    for name, mut in muts:
        w = stage("fresh"); mut(w)
        rc, out = w.script("preflight_v17.sh"); refused(rc, out); need("lengau preflight OK" not in out, "preflight passed with %s" % name, out)
        rc, out = w.script("archive_v16.sh"); refused(rc, out); need(not os.path.exists(w.A), "archived with %s" % name)
    w = stage("fresh"); os.remove(os.path.join(w.C, "aws_ec2/ec2_release_state.json"))
    rc, out = w.script("archive_v16.sh"); refused(rc, out, "missing")


# ================================================================================================ steps 5-7: EC2 cycles and activation
@test("pre-activation cycle: a failed sync, a stale inventory or an owner outside the e2 set refuses; a re-run seals a new generation")
def t_precycle():
    w = stage("deployed"); stub_sync(w); write(os.path.join(w.t1, "aws_ec2/stub_sync.mode"), "fail")
    rc, out = w.script("ec2_cycle_v17.sh", "pre-activation"); refused(rc, out, "ec2_sync.py cycle exited 3")
    write(os.path.join(w.t1, "aws_ec2/stub_sync.mode"), "stale")
    rc, out = w.script("ec2_cycle_v17.sh", "pre-activation"); refused(rc, out, "older than")
    sys.path.insert(0, os.path.join(w.C, "chpc"))
    try:
        for m in ("row19_partition", "row19_ec2_state"):
            sys.modules.pop(m, None)
        import row19_partition as RP
        man_p = os.path.join(w.C, "chpc/row19_screen_manifest.json"); man = json.load(open(man_p))
        part = RP.load(os.path.join(w.C, "chpc/row19_partition_e2.json"), man, sha(man_p)); own = RP.owned_set(part)
    finally:
        sys.path.pop(0)
        for m in ("row19_partition", "row19_ec2_state"):
            sys.modules.pop(m, None)
    outside = next([r, i] for r in range(0, 200) for i in range(0, 80) if (r, i) not in own)
    write(os.path.join(w.t1, "aws_ec2/stub_sync.outside"), json.dumps(outside)); write(os.path.join(w.t1, "aws_ec2/stub_sync.mode"), "outside")
    rc, out = w.script("ec2_cycle_v17.sh", "pre-activation"); refused(rc, out, "1 outside the e2 owned set")
    rc, out = w.script("lengau.sh", "activate_e2.sh"); refused(rc, out, "does not admit the activation")
    need(not os.path.exists(os.path.join(w.L, "activate.log")), "the activation ran with an outside owner")
    write(os.path.join(w.t1, "aws_ec2/stub_sync.mode"), "ok")
    rc, out = w.script("ec2_cycle_v17.sh", "pre-activation"); need(rc == 0 and "PRE-ACTIVATION CYCLE OK" in out, "recovered", out)
    gens = open(os.path.join(w.t1, "aws_ec2/stub_sync.log")).read().count("cycle")
    need(gens == 4, "every cycle is a new sealing (4 cycles), got %d" % gens)
    need(os.path.isdir(os.path.join(w.t1, "aws_ec2/runs/inventory")), "the real prod_authority.py inventory did not seal locally")


@test("activation: a held plan lock, refused problems, a crash after the link, a wrong proof, drain failures - each handled; nothing erased")
def t_activation():
    w = stage("precycled"); write(os.path.join(w.L, "activate.mode"), "problems")
    rc, out = w.script("lengau.sh", "activate_e2.sh"); refused(rc, out, "Lengau claim(s) on owned coordinates", "no activation was written")
    need(not os.path.exists(w.ACT2), "a proof was written on refusal")
    os.remove(os.path.join(w.L, "activate.mode"))
    with Holder(os.path.join(w.GS, "plans/.submit.lock")):
        rc, out = w.script("lengau.sh", "activate_e2.sh")
    refused(rc, out, "lock held"); need(not os.path.exists(w.ACT2), "activated under a held lock")
    rc, out = w.script("lengau.sh", "activate_e2.sh"); need(rc == 0 and "ACTIVATED" in out, "activation after the lock was released", out)
    w = stage("precycled"); write(os.path.join(w.L, "activate.mode"), "crash")
    rc, out = w.script("lengau.sh", "activate_e2.sh"); refused(rc, out, "now exists", "re-run activate_e2.sh")
    os.remove(os.path.join(w.L, "activate.mode"))
    rc, out = w.script("lengau.sh", "activate_e2.sh"); need(rc == 0 and "ALREADY ACTIVATED (verified)" in out, "verify after the crash", out)
    need(open(os.path.join(w.L, "activate.log")).read().count("activate") == 1, "the activation command was repeated")
    w = stage("precycled"); write(os.path.join(w.L, "activate.mode"), "wrong")
    rc, out = w.script("lengau.sh", "activate_e2.sh"); refused(rc, out, "not the canonical epoch-2 activation")
    p0 = sha(w.ACT2); rc, out = w.script("lengau.sh", "activate_e2.sh"); refused(rc, out, "not the canonical epoch-2 activation")
    need(sha(w.ACT2) == p0, "the wrong proof was edited or replaced")
    w = stage("precycled"); write(os.path.join(w.bin, "ps_u.out"), "bash -s\n/x/t1py chpc/row19_ec2_root.py install --manifest m\n")
    rc, out = w.script("lengau.sh", "activate_e2.sh"); refused(rc, out, "a controller command runs"); need(not os.path.exists(w.ACT2), "activated")
    w = stage("deployed"); stub_sync(w)
    rc, out = w.script("ec2_cycle_v17.sh", "pre-activation"); need(rc == 0, "pre", out)
    p = os.path.join(w.t1, "aws_ec2/stub_sync.gen")
    inv = os.path.join(w.GS, "ec2/authority/inventory.json"); d = json.load(open(inv))
    sys.path.insert(0, os.path.join(w.C, "chpc"))
    try:
        sys.modules.pop("row19_ec2_state", None); import row19_ec2_state as ES
        d["at"] = time.time() - 6 * 3600 - 30; json.dump(ES.seal({k: v for k, v in d.items() if k != "sha256"}), open(inv, "w"))
    finally:
        sys.path.pop(0); sys.modules.pop("row19_ec2_state", None)
    rc, out = w.script("lengau.sh", "activate_e2.sh"); refused(rc, out, "older than"); need(not os.path.exists(os.path.join(w.L, "activate.log")), "attempted on a stale inventory")


@test("activation before deploy (v16 controller) or with an undeployed proof refuses; rollover/adopt before activation refuse")
def t_activation_order():
    w = stage("archived"); rc, out = w.script("lengau.sh", "activate_e2.sh"); refused(rc, out, "v17"); need(not os.path.exists(w.ACT2), "activated under v16")
    w = stage("deployed"); unlock_tree(w.PROOF); os.remove(os.path.join(w.PROOF, "DONE"))
    rc, out = w.script("lengau.sh", "activate_e2.sh"); refused(rc, out, "DONE")
    w = stage("precycled"); rc, out = w.script("lengau.sh", "rollover_pilot_v17.sh"); refused(rc, out, "activation")
    need(os.path.exists(os.path.join(w.G, "review_refit.json")), "the review moved before activation")
    w = stage("precycled"); shutil.move(os.path.join(w.G, "review_refit.json"), os.path.join(w.R, "review_refit.v16_qual2c7a7ef1_max100.json"))
    write(os.path.join(w.G, "qualified_refit_job1.json"), "{\"regenerated\": true}\n"); rec = pilot_record(w, sha(os.path.join(w.G, "qualified_refit_job1.json")))
    h0 = w.ctl_state()[0]
    rc, out = w.script("lengau.sh", "adopt_pilot17.sh", "--file", rec); refused(rc, out, "epoch-2 activation proof")
    need(w.ctl_state()[0] == h0 and not os.path.lexists(os.path.join(w.G, "review_refit.json")) and not os.path.exists(os.path.join(w.L, "adopt.log")), "adopt ran before the activation")


@test("post-activation receipts: an alarm, a v16 generation, a receipt without activation_e2, a failed status or bank receipt refuse")
def t_postcycle():
    for mode, msg in (("alarm", "alarms"), ("gen16", "not v17"), ("noe2", "not exactly e1 and e2"), ("fail", "not fresh, production and alarm-free")):
        w = stage("activated"); stub_receipts(w); write(os.path.join(w.t1, "chpc/stub_status.mode"), mode)
        rc, out = w.script("ec2_cycle_v17.sh", "post-activation"); refused(rc, out, msg); need("RECEIPTS OK" not in out, "OK with " + mode, out)
    w = stage("activated"); stub_receipts(w); write(os.path.join(w.t1, "chpc/row22_bank_status.py"), "import sys\nsys.exit(2)\n")
    rc, out = w.script("ec2_cycle_v17.sh", "post-activation"); refused(rc, out, "bank receipt exited 2")
    w = stage("activated"); stub_receipts(w)
    rc, out = w.script("receipt_check_v17.py", "--since", str(time.time() + 3600)); refused(rc, out, "no refit watch receipt published")
    w = stage("activated"); stub_receipts(w); write(os.path.join(w.t1, "chpc/stub_status.mode"), "alarm")      # retry after a refusal
    rc, out = w.script("ec2_cycle_v17.sh", "post-activation"); refused(rc, out, "alarms")
    os.remove(os.path.join(w.t1, "chpc/stub_status.mode"))
    rc, out = w.script("ec2_cycle_v17.sh", "post-activation"); need(rc == 0 and "RECEIPTS OK" in out, "post cycle retry", out)
    need(open(os.path.join(w.t1, "aws_ec2/stub_sync.log")).read().count("cycle") >= 3, "each post cycle sealed a new generation")


# ================================================================================================ step 8: pilot rollover, package, adoption
@test("rollover: a changed active review or a corrupted archive refuses (nothing moves); a gate member symlink refuses before move/chmod; an interrupted chmod completes on re-run")
def t_rollover():
    w = stage("postcycled"); open(os.path.join(w.G, "review_refit.json"), "a").write(" ")
    rc, out = w.script("lengau.sh", "rollover_pilot_v17.sh"); refused(rc, out, "MISMATCH"); need(os.path.exists(os.path.join(w.G, "review_refit.json")), "moved")
    w = stage("postcycled"); p = os.path.join(w.A, "ctl/HEAD.txt"); os.chmod(p, 0o644); write(p, "0" * 40 + "\n"); os.chmod(p, 0o444)
    rc, out = w.script("lengau.sh", "rollover_pilot_v17.sh"); refused(rc, out, "does not verify as complete"); need(os.path.exists(os.path.join(w.G, "review_refit.json")), "moved")
    for member in ("review_refit.json", "qualified_refit_job1.json"):
        w = stage("postcycled"); src = os.path.join(w.G, member); copy = os.path.join(w.outside, member)
        write(copy, open(src, "rb").read(), 0o644); os.remove(src); os.symlink(copy, src); before = tree_digest(w.outside)
        rc, out = w.script("lengau.sh", "rollover_pilot_v17.sh"); refused(rc, out, "not its own physical path")
        need(tree_digest(w.outside) == before and os.stat(copy).st_mode & 0o777 == 0o644 and os.path.islink(src), "something moved or changed")
    w = stage("postcycled"); ra = sha(os.path.join(w.G, "review_refit.json"))
    out_p = os.path.join(w.R, "review_refit.v16_qual2c7a7ef1_max100.json"); shutil.move(os.path.join(w.G, "review_refit.json"), out_p)   # moved, chmod lost
    rc, out = w.script("lengau.sh", "rollover_pilot_v17.sh"); need(rc == 0 and "completed the interrupted retirement" in out and not os.access(out_p, os.W_OK) and sha(out_p) == ra, "chmod completion", out)
    w = stage("rolled"); write(os.path.join(w.G, "review_refit.json"), "{}\n")
    rc, out = w.script("lengau.sh", "rollover_pilot_v17.sh"); refused(rc, out, "both the retired v16 review")


@test("package: a qualification not regenerated / of another generation / naming a missing receipt refuses; an existing different package refuses")
def t_package():
    w = stage("rolled"); rc, out = w.script("package_qual_v17.py"); refused(rc, out, "still the v16 2c7a7ef1")
    w = stage("qualified"); R = os.path.join(w.t1, "chpc/results/row19_screen/receipts")
    vp = [f for f in os.listdir(R) if f.startswith("verify_refit_2026102")][0]
    write(os.path.join(R, vp), json.dumps({"generation": {"version": 16, "latest": 16, "controls_problem": "", "controls_sha256": V16_CONTROLS}}))
    rc, out = w.script("package_qual_v17.py"); refused(rc, out, "not v17")
    w = stage("qualified"); os.remove(os.path.join(w.t1, "chpc/results/row19_screen/receipts/watch_refit_20261017T204309Z.json"))
    rc, out = w.script("package_qual_v17.py"); refused(rc, out, "watch_refit_20261017T204309Z.json")
    w = stage("qualified"); qsha = sha(os.path.join(w.t1, "chpc/results/row19_screen/receipts/qualified_refit_job1.json"))
    stg = os.path.join(w.t1, "chpc/qualification_v17_%s.staging.77" % qsha[:8]); os.makedirs(stg)
    rc, out = w.script("package_qual_v17.py"); refused(rc, out, "interrupted build"); need(os.path.isdir(stg), "the staging evidence was removed")
    w = stage("qualified"); rc, out = w.script("package_qual_v17.py"); need(rc == 0, "package", out)
    qsha = sha(os.path.join(w.t1, "chpc/results/row19_screen/receipts/qualified_refit_job1.json")); pd = os.path.join(w.t1, "chpc/qualification_v17_" + qsha[:8])
    os.chmod(pd, 0o755); p = os.path.join(pd, "watch_refit_20261017T204309Z.json"); os.chmod(p, 0o644); open(p, "a").write(" ")
    rc, out = w.script("package_qual_v17.py"); refused(rc, out, "does not verify")


@test("adopt: an active review, the gate still at 2c7a7ef1, a record without THIS qualification's literal, an evidence path, an adopter refusal - each refuses; the gate is never overwritten")
def t_adopt():
    w = stage("postcycled"); rec = pilot_record(w, "f" * 64)
    rc, out = w.script("lengau.sh", "adopt_pilot17.sh", "--file", rec); refused(rc, out, "an active review exists")
    w = stage("rolled"); rec = pilot_record(w, "f" * 64)
    rc, out = w.script("lengau.sh", "adopt_pilot17.sh", "--file", rec); refused(rc, out, "still the v16 2c7a7ef1")
    w = stage("qualified"); rec = pilot_record(w, V16_QUAL); h0 = w.ctl_state()[0]
    rc, out = w.script("lengau.sh", "adopt_pilot17.sh", "--file", rec); refused(rc, out, "does not carry the literal for the gate qualification")
    need(w.ctl_state()[0] == h0, "the wrong record was committed in the controller clone")
    w = stage("qualified"); qsha = sha(os.path.join(w.G, "qualified_refit_job1.json"))
    p = os.path.join(w.t1, "reviews/2026-10-11_d1d2_f3_codex_record.md"); write(p, "ADOPT row19-screen-pilot role=refit qualification=%s max_job=100\n" % qsha)
    rc, out = w.script("lengau.sh", "adopt_pilot17.sh", "--file", "reviews/2026-10-11_d1d2_f3_codex_record.md"); refused(rc, out, "pinned untracked evidence")
    w = stage("qualified"); qsha = sha(os.path.join(w.G, "qualified_refit_job1.json")); rec = pilot_record(w, qsha); write(os.path.join(w.L, "adopt.mode"), "refuse")
    rc, out = w.script("lengau.sh", "adopt_pilot17.sh", "--file", rec); refused(rc, out, "the supported adopter refused")
    need(not os.path.lexists(os.path.join(w.G, "review_refit.json")), "a gate review was written on refusal")
    os.remove(os.path.join(w.L, "adopt.mode"))
    rc, out = w.script("lengau.sh", "adopt_pilot17.sh", "--file", rec); need(rc == 0 and "adopt_pilot17 complete" in out, "adopt retry after the refusal (record already committed)", out)


def main(argv):
    global BASE
    keep = "--keep" in argv; sel = argv[argv.index("-k") + 1] if "-k" in argv else None
    BASE = tempfile.mkdtemp(prefix="mig_v17_test_")
    print("private test worlds under", BASE)
    ok = fail = 0; t0 = time.time()
    for name, fn in TESTS:
        if sel and sel not in name and sel != fn.__name__:
            continue
        t = time.time()
        try:
            fn(); ok += 1; print("PASS (%4.1fs) %s" % (time.time() - t, name))
        except Exception as e:
            fail += 1; print("FAIL (%4.1fs) %s\n    %s" % (time.time() - t, name, str(e).replace("\n", "\n    ")))
    print("\n%d passed, %d failed (%d tests, %.0f s)" % (ok, fail, ok + fail, time.time() - t0))
    if not keep:
        for d, dirs, files in os.walk(BASE):
            for x in dirs:
                try:
                    os.chmod(os.path.join(d, x), 0o755)
                except OSError:
                    pass
        shutil.rmtree(BASE, ignore_errors=True)
    else:
        print("kept:", BASE)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
