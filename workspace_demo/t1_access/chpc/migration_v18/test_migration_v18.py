#!/usr/bin/env python3
"""Private-copy tests for the migration_v18 scripts (the migration_v17 test pattern; every Codex finding on migration_v16/v17 is
a requirement here too).

    python3 chpc/migration_v18/test_migration_v18.py [-k <substring>] [--keep]      (from anywhere)

FROZEN FIXTURES (the v17 suite can no longer run end to end: it seeds its worlds from the LIVE tree, which the v17 promotion
moved past its v16 starting state). This harness never seeds a world from live, movable state. The adopted-v17 starting state is
read from git objects at ONE pinned commit (FIXTURE_COMMIT, RSC 6d82a73, where the Mac tree was exactly the adopted v17) through
`git show <commit>:<path>`, and every file is checked against FROZEN (its pinned sha256) or, for the 17 v17 pins, against the
frozen v17 controls entry. Only the immutable v18 candidate package (chpc/candidate_v18_nodefail/*, pinned by
v18_package.PACKAGE) is read from the working tree, and the three pinned controller-clone evidence files come from their own
pinned commits (as in v17). It never reads, clones or hashes the whole repository, and no protected plant/key/sample file or
scientific source: the scientific job clone holds eight synthetic placeholders.
A world is:
  mac/        a private git repository holding workspace_demo/t1_access/<frozen allowlist + candidate package + a synthetic
              controls review record carrying the v18 literal>, at the adopted v17
  lengau/     a fake toolchain root: rsc_screen_ctl (a private git repository holding the frozen v17 controller set, with the
              three pinned evidence files UNTRACKED), rsc_screen (synthetic science), the gate (8fdbf48e + an active review bound
              to it), gate_retired (the retired v16 review), ec2 (activation_e1.json and a CANONICAL activation_e2.json generated
              under the frozen v17 controls by the real row19_partition code), the v16_before_v17 archive and v17 deploy proof
              left by the v17 migration, plans, locks, the ledger, refit job files including the captured node document
              row19_screen_refit_54.nodefail.json (730ea262), and a fake t1py
  fakebin/    ps, sha256sum (fault injection), ssh and scp (ALWAYS refuse, logged: nothing can leave the Mac)
  lengaubin/  restricted-CLI shims first on the Lengau half's PATH (git rejects -C; flock rejects -E) as in migration_v17
The production files are COPIED into mac/.../chpc/migration_v18/ with exactly three tagged lines substituted: the `# @root`
toolchain root in remote_lib.sh (-> the fake root), the `# @transport` ssh in lengau.sh (-> a local `bash -s`) and the
`# @record` controls-record pin in v18_package.py (in production the REAL committed Codex record PROD_REC/PROD_REC_SHA ->
install(record=True): the world's SYNTHETIC record REC and its own private digest; install(record=False): an explicit private
PENDING (None, None), so the PENDING refusals still test PENDING and not a wrong/absent record).
The fake t1py is `python3` for every `-c` snippet and INTERCEPTS only `chpc/row19_screen_admit.py ... --adopt-review` (simulated:
ok / refuse); ANY other controller script is refused. The refit and bank status commands are private STUBS. Nothing here runs
ssh/scp, touches Lengau, AWS or the live tree, or writes outside the temp directory (removed at the end unless --keep)."""
import ast, hashlib, json, os, re, shlex, shutil, signal, stat, subprocess, sys, tempfile, time

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
T1_REL = "workspace_demo/t1_access"
LIVE_T1 = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO = os.path.abspath(os.path.join(LIVE_T1, "..", ".."))
PROD_ROOT = "/mnt/lustre/users/pvanrooyen/t1_toolchain"
TRANSPORT = "ssh -o ControlPath=none -o ConnectTimeout=30 -o BatchMode=yes lengau bash -s"
ROOT_LINE = "T_ROOT=/mnt/lustre/users/pvanrooyen/t1_toolchain   # @root"
PROD_REC = "reviews/2026-10-20_v18r2_mig18_codex_review.md"    # the REAL production record (committed at RSC 785f103)
PROD_REC_SHA = "11ebc12467a50a125f4b583c4d673274e2ff3ea1a2ac0d3e6c03f3725c8cc2c8"
RECORD_LINE = ('REC, REC_SHA = "%s", "%s"   # @record: the committed Codex record with the v18 ADOPT literal, and its sha256'
               % (PROD_REC, PROD_REC_SHA))                       # the ONE expected (filled) production assignment
PENDING_LINE = "REC, REC_SHA = None, None   # @record (PRIVATE TEST COPY: PENDING)"
SELF = os.path.basename(__file__)
PROD_FILES = sorted(f for f in os.listdir(HERE) if os.path.isfile(os.path.join(HERE, f)) and f != SELF and not f.startswith(".")
                    and f != "test_results.txt" and not f.endswith(".diff"))
V16_QUAL = "2c7a7ef1fb903cf0fa75701d2a56d216e98faf14e6638da891afd8bed0bfea44"
V17_QUAL = "8fdbf48e998e39a8c0b12900d75e3dfaf4ab64396ade08a17a5cab549c0b5faa"
V17_CONTROLS = "9ea4e727c5d308457a2d5901ef6565522845fb31d52c3c1c0f7dd5a51a9d83c0"
V18_CONTROLS = "452b82df0d7184cbe7c1390d5d43787501990d380c4ca275d1db70adc131ba2b"
NODE_EV_SHA = "730ea262c65c9e70d9bc39d572d65bd4ea70ac77c52fb3a4e4a1ed9238164b1f"
REC = "reviews/test_v18_controls_record.md"            # the world's SYNTHETIC controls record (never PROD_REC)
REC_TEXT = "# PRIVATE TEST RECORD (never production)\n\nADOPT row19-screen-controls sha256=%s version=18\n" % V18_CONTROLS
REAL_SHA256SUM = shutil.which("sha256sum") or "/sbin/sha256sum"
REAL_PY = shutil.which("python3") or sys.executable
REAL_GIT = shutil.which("git") or "/usr/bin/git"
SCI = ["chpc/row19_screen_manifest.json", "analyze.py", "models.py", "simulate.py", "chpc/row19_shard.py", "chpc/row19_ledger.py",
       "chpc/row19_slice.py", "chpc/row19_screen_orig.py"]
EVIDENCE = {"aws_ec2/ec2_release_state.json": ("f2caf7c", "80ba0ac599f617f8c0ee020d75e7c53dcd30c519d783a76dcb6a2f6b9f1a1d39"),
            "aws_ec2/runs/b2/bench_report_attempt_5_20261011T185715Z.json": ("c12af3e", "154511e687f006001888970bd3d65398b6b37c910221378b7f6c3c63fe63e3a4"),
            "reviews/2026-10-11_d1d2_f3_codex_record.md": ("1609fa7", "636f1e77089578a14ee837bf95fe0f86cc84dbc907f8ced918256b69dbb55c1e")}
# ---- the frozen fixture: ONE pinned commit, every member pinned ------------------------------------------------------------
FIXTURE_COMMIT = "6d82a737516cd3cfeb71b2087b9e886e62ed8b8c"     # RSC 6d82a73: the Mac tree at the adopted v17 (20 Oct 2026)
FROZEN = {
    "chpc/row19_screen_controls.json": V17_CONTROLS,
    "chpc/row19_screen_controls_adoption.json": "61ca680e932fcb6d32a972c3198b5bd9c029da3955e15dd7acb2e07db125699b",
    "chpc/row19_screen_budget.json": "45738358cd716558f9acf65ddac9a3faf4e16bf856db45ba66360b4d0d6129d3",
    "chpc/row19_screen_manifest.json": "43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c",
    "chpc/row19_partition_e2.json": "48cea639e823abbf39238e3dd7c075f63ba9eca8467009348510e2943ed56fa6",
    "chpc/row19_partition_e1.json": "8d1de408b6ef9dc66d4736b6138536de6591f0d29ebdd6fd00a6e43307225608",
    "chpc/claims_snapshot_e2.json": "31cc268ff3247858fc73ac17a3a387b43e17a829d9cdea505958890a97eecb6f",
    "aws_ec2/e2_funding.json": "d6f414e8107f25e5de43d6b33764106c6c92dd64440ff33fddf4873416ce4815",
    "aws_ec2/prod/manifest_production_e2.json": "e126050536a8459cb1432cf78321e82147c67f5406441fff131a1f543f9f82f9",
    "aws_ec2/prod/manifest_e2q1_e2.json": "3ea8cafd736871de715062ca398f36ff98f93f27d1d82bd977c3b72b0f1cfb8b",
    "aws_ec2/prod/manifest_e2q2_e2.json": "4af4a64d83c749394c7159814359da716b2a9f9a694cd23fe46157aecd7b0cec",
    "aws_ec2/prod/panel_e2q_e2.json": "f04a5e43634e13bfceaf173e303ebf780f4280de044b6bd97ee9e2c3f711c7a2",
    "chpc/row19_ledger.py": "9a7797029a153769ebff78a9256f5c7874f5ad2204b38dff3ac4701a4b23d494",
    "chpc/row22_bank_status.py": "1ac4b5036ca9550cdd68c711144b9673dcba626765dc58187c56b9857bb4903a",
    "chpc/row22_bank_submit.py": "9665c3292cd01263be315020aac43bcc893c50574d5e69e4211cdbe931d3b8fe",
    "reviews/2026-10-19_e2_repair_codex_rereview.md": "48b9cf053cbd4f73e40e3e139f84a7ab50eb6c4252e8727bf90953bc1ed88f2b",
    "reviews/2026-10-20_pilot_v17_codex_review.md": "75bb50101afa7eebc07e47915afbed32dec92ebf1e68235fe742bf9e5ff0035d",
    "reviews/2026-10-17_v16_p80_codex_review.md": "a315d7d2f7b91baec3b668e4dcec4c2530ab44d8c07aef597b77e28fdd3d447c",
}
FROZEN_QUAL = ("chpc/qualification_v17_8fdbf48e/qualified_refit_job1.json", V17_QUAL)   # -> the Mac receipts copy and the gate copy
CAND_SET = ["chpc/candidate_v18_nodefail/" + f for f in ("row19_screen_controls.json", "v18_promotion_map.json", "build_v18.py",
            "promote_v18.py", "row19_screen_admit.py", "row19_screen_status.py", "row19_screen_nodefail.py",
            "row19_nodefail_capture.py", "evidence_row19_screen_refit_54.nodefail.json")]
QUAL_MAC = "chpc/results/row19_screen/receipts/qualified_refit_job1.json"

BASE = None
TESTS = []
_FROZEN_CACHE = {}


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
    """A digest of every path, mode, file content and link target under p (.git excluded). Used ONLY on private worlds."""
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


def frozen(rel):
    """The bytes of `rel` at FIXTURE_COMMIT (never the live tree)."""
    if rel not in _FROZEN_CACHE:
        r = subprocess.run(["git", "-C", REPO, "show", "%s:%s/%s" % (FIXTURE_COMMIT, T1_REL, rel)], capture_output=True)
        if r.returncode != 0:
            raise Fail("the frozen fixture commit %s has no %s" % (FIXTURE_COMMIT[:8], rel))
        _FROZEN_CACHE[rel] = r.stdout
    return _FROZEN_CACHE[rel]


def frozen_set():
    """{rel: bytes} of the whole frozen controller allowlist: FROZEN + the 17 pins of the frozen v17 entry, each verified."""
    out = {}
    for rel, want in FROZEN.items():
        b = frozen(rel)
        need(hashlib.sha256(b).hexdigest() == want, "frozen fixture %s is not %s" % (rel, want[:8]))
        out[rel] = b
    v17 = json.loads(out["chpc/row19_screen_controls.json"])["versions"][-1]
    need(v17["version"] == 17 and len(v17["files"]) == 17, "the frozen controls' latest entry is not v17 with 17 pins")
    for rel, want in v17["files"].items():
        b = frozen(rel)
        need(hashlib.sha256(b).hexdigest() == want, "frozen v17 pin %s is not %s" % (rel, want[:8]))
        out[rel] = b
    return out


def package_pins():
    sys.path.insert(0, HERE)
    try:
        sys.modules.pop("v18_package", None)
        import v18_package as VP
        return VP
    finally:
        sys.path.pop(0); sys.modules.pop("v18_package", None)


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
# the fake $T/t1py: python3 for -c snippets; the supported pilot adopter simulated; every other controller script refused
FAKE_T1PY = r"""#!/bin/bash
d=$(cd "$(dirname "$0")" && pwd)
if [ -f "$d/t1py.nofcntl" ]; then for a in "$@"; do case $a in *fcntl.flock*) echo "simulated: this python has no usable fcntl" >&2; exit 1;; esac; done; fi
case "${1:-}" in
  -c) exec python3 "$@";;
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
# the canonical epoch-2 activation, generated ONCE per fresh world by the REAL frozen row19_partition code under the frozen,
# committed v17 controls in the private controller clone (it is what the v17 migration left on the root)
GEN_ACT2 = r'''import hashlib, json, os, sys, time
sys.path.insert(0, "chpc")
import row19_partition as RP
out = sys.argv[1]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
man_p, part_p = "chpc/row19_screen_manifest.json", "chpc/row19_partition_e2.json"
man = json.load(open(man_p)); part = RP.load(part_p, man, sha(man_p))
ctl = json.load(open("chpc/row19_screen_controls.json")); latest = ctl["versions"][-1]
proof = {"schema": "row19-ec2-activation-1", "mode": "canonical", "epoch": part["epoch"], "partition_sha256": sha(part_p),
         "manifest_sha256": sha(man_p), "controls_sha256": sha("chpc/row19_screen_controls.json"), "controls_version": latest["version"],
         "controls_entry_sha256": RP.entry_sha(latest), "adoption_sha256": sha("chpc/row19_screen_controls_adoption.json"),
         "predecessor": part["predecessor"], "transferred_indices": RP.transferred_of(part), "owned_sha256": part["owned_sha256"],
         "claims_snapshot_sha256": part["claims_snapshot"]["claims_sha256"], "claims_sha256": "0" * 64,
         "ec2_completed_sha256": "0" * 64, "facts": {"private_test_world": True}, "at": 1792400000.0}
why = RP.activation_problem(man, sha(man_p), part, sha(part_p), proof, mode="canonical")
if why:
    print("GEN_ACT2: %s" % why); sys.exit(3)
json.dump(proof, open(out, "w"), indent=1, sort_keys=True)
print("canonical activation_e2 under controls version %s" % latest["version"])
'''
STUB_STATUS = r'''"""PRIVATE TEST STUB standing in for chpc/row19_screen_status.py (never production): a synthetic refit receipt."""
import hashlib, json, os, sys, time
HERE = os.path.join(os.getcwd(), "chpc")
R = os.path.join(HERE, "results", "row19_screen", "receipts"); os.makedirs(R, exist_ok=True)
mode = open(os.path.join(HERE, "stub_status.mode")).read().strip() if os.path.exists(os.path.join(HERE, "stub_status.mode")) else "ok"
if mode == "fail":
    print("ALARMS: - simulated"); sys.exit(1)
now = time.time(); stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(now))
v = 17 if mode == "gen17" else 18
gen = {"version": v, "latest": v, "controls_problem": "", "controls_sha256": "452b82df0d7184cbe7c1390d5d43787501990d380c4ca275d1db70adc131ba2b",
       "verify_sha256": "0" * 64}
vp = os.path.join(R, "verify_refit_%s.json" % stamp); json.dump({"generation": gen}, open(vp, "w"))
acts = {"activation_e1.json": "1" * 64} if mode == "noe2" else {"activation_e1.json": "1" * 64, "activation_e2.json": "2" * 64}
ev = ("row19_screen_refit_54.nodefail.json", "730ea262c65c9e70d9bc39d572d65bd4ea70ac77c52fb3a4e4a1ed9238164b1f")
nd = {"kind": "node-failure", "counts_as_crash": False, "evidence_file": ev[0], "evidence_sha256": ev[1] if mode != "otherev" else "3" * 64}
jobs = {"53": {"exit": 0}, "54": {"exit": 265, "node_disposition": nd}}
if mode == "nonode":
    jobs["54"] = {"exit": 265, "node_disposition_held": "the node evidence was not retrieved"}
if mode == "othernode":
    jobs["55"] = {"exit": 265, "node_disposition": dict(nd)}
rc = {"schema": "row19-screen-watch-test", "role": "refit", "time": now, "fresh": True, "production": True,
      "alarms": ["simulated alarm"] if mode == "alarm" else [], "designated": {"declaration_sha256": "a96eb598"}, "jobs": jobs,
      "bound": {"verify_file": os.path.basename(vp), "verify_file_sha256": hashlib.sha256(open(vp, "rb").read()).hexdigest(),
                "node_evidence": {"54": {"file": ev[0], "sha256": ev[1]}}},
      "ec2": {"bound": {"activations": acts, "hold": False, "stop": False}, "problems": []}}
json.dump(rc, open(os.path.join(R, "watch_refit_%s.json" % stamp), "w"), indent=1)
print("stub status: receipt watch_refit_%s.json" % stamp); sys.exit(0)
'''
STUB_BANK = ('"""PRIVATE TEST STUB standing in for chpc/row22_bank_status.py."""\nimport os, sys\n'
             'm = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stub_bank.mode")\n'
             'rc = int(open(m).read()) if os.path.exists(m) else 0\nprint("stub bank receipt", rc)\nsys.exit(rc)\n')
# the Mac-side python3 wrapper: ONLY the two receipt commands are redirected to the stubs; everything else is the real python3
PY_WRAPPER = """#!/bin/bash
d=$(cd "$(dirname "$0")" && pwd)
case "${1:-}" in
  chpc/row19_screen_status.py) shift; exec "%s" "$d/stub_status.py" "$@";;
  chpc/row22_bank_status.py) shift; exec "%s" "$d/stub_bank.py" "$@";;
esac
exec "%s" "$@"
""" % (REAL_PY, REAL_PY, REAL_PY)


class World:
    def __init__(self, d):
        self.d = d; self.mac = os.path.join(d, "mac"); self.t1 = os.path.join(self.mac, T1_REL)
        self.L = os.path.join(d, "lengau"); self.bin = os.path.join(d, "fakebin"); self.outside = os.path.join(d, "outside")
        self.lbin = os.path.join(d, "lengaubin")
        self.CR = os.path.join(self.L, "rsc_screen_ctl"); self.C = os.path.join(self.CR, T1_REL)
        self.J = os.path.join(self.L, "rsc_screen", T1_REL)
        self.GS = os.path.join(self.L, "row19_screen"); self.G = os.path.join(self.GS, "gate"); self.R = os.path.join(self.GS, "gate_retired")
        self.A = os.path.join(self.L, "archive_screen", "v17_before_v18"); self.PROOF = os.path.join(self.L, "archive_screen", "v18_deploy_proof")
        self.ACT2 = os.path.join(self.GS, "ec2", "activation_e2.json")
        self.NODE_EV = os.path.join(self.L, "jobs", "row19_screen_refit_54.nodefail.json")
        self.MA = os.path.join(self.t1, "chpc/results/archive/row19_screen_v17_before_v18")
        self.LSF = os.path.join(self.t1, "chpc/results/archive/row19_screen_v17_before_v18.lengau_SHA256SUMS.txt")
        self.RETIRED = os.path.join(self.R, "review_refit.v17_qual8fdbf48e_max100.json")

    def install(self, root=None, record=True):
        root = root or self.L
        base = os.path.realpath(BASE); real = os.path.realpath(root)
        if not real.startswith(base + os.sep):
            raise Fail("refusing a fake root outside the harness temp dir: %s -> %s" % (root, real))
        if real == PROD_ROOT or real.startswith(PROD_ROOT + "/") or os.path.realpath(PROD_ROOT) == real:
            raise Fail("refusing a fake root that is the production toolchain")
        if not os.path.realpath(self.t1).startswith(base + os.sep):
            raise Fail("refusing a Mac tree outside the harness temp dir")
        dst = os.path.join(self.t1, "chpc", "migration_v18")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        os.makedirs(dst)
        rec_line = 'REC, REC_SHA = %r, %r   # @record (PRIVATE TEST COPY: the synthetic record)' % (
            REC, hashlib.sha256(REC_TEXT.encode()).hexdigest())
        for f in PROD_FILES:
            src = open(os.path.join(HERE, f)).read()
            if f == "remote_lib.sh":
                assert src.count(ROOT_LINE) == 1, "remote_lib.sh must carry exactly one production root line"
                src = src.replace(ROOT_LINE, "T_ROOT=%s   # @root (PRIVATE TEST COPY)" % root)
            if f == "lengau.sh":
                assert src.count(TRANSPORT) == 1, "lengau.sh must carry exactly one production transport"
                src = src.replace(TRANSPORT, 'PATH=%s:"$PATH" bash -s' % shlex.quote(self.lbin))
            if f == "v18_package.py":
                assert src.count(RECORD_LINE) == 1, "v18_package.py must carry exactly one filled production record line"
                src = src.replace(RECORD_LINE, rec_line if record else PENDING_LINE)
            write(os.path.join(dst, f), src, os.stat(os.path.join(HERE, f)).st_mode & 0o777)
        changed = []
        for f in PROD_FILES:
            a = open(os.path.join(HERE, f)).read().splitlines(); b = open(os.path.join(dst, f)).read().splitlines()
            changed += [(f, x) for x, y in zip(a, b) if x != y]
            if len(a) != len(b):
                raise Fail("private copy of %s changed its line count" % f)
        want = sorted([("lengau.sh", [l for l in open(os.path.join(HERE, "lengau.sh")).read().splitlines() if TRANSPORT in l][0]),
                       ("remote_lib.sh", ROOT_LINE), ("v18_package.py", RECORD_LINE)])
        if sorted(changed) != want:      # root, transport AND record substituted on both paths; nothing else
            raise Fail("the private copy differs from production on other lines: %s" % changed)
        if open(os.path.join(dst, "v18_package.py")).read().splitlines().count(rec_line if record else PENDING_LINE) != 1:
            raise Fail("the private v18_package.py does not carry exactly one %s record line" % ("synthetic" if record else "PENDING"))

    def run(self, *cmd, timeout=600):
        env = dict(os.environ); env["PATH"] = self.bin + os.pathsep + env["PATH"]
        for k in list(env):
            if k.startswith("V17_") or k.startswith("V18_") or k.startswith("V16_") or k.startswith("GIT_"):
                del env[k]
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        r = subprocess.run(list(cmd), cwd=self.t1, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout)
        return r.returncode, r.stdout

    def script(self, name, *args):
        if name.endswith(".py"):
            return self.run("python3", "chpc/migration_v18/" + name, *args)
        return self.run("bash", "chpc/migration_v18/" + name, *args)

    def promote(self, *args):
        return self.run("python3", "chpc/candidate_v18_nodefail/promote_v18.py", *args)

    def ctl_state(self):
        return (sh("git", "-C", self.CR, "rev-parse", "HEAD").strip(), sh("git", "-C", self.CR, "status", "--porcelain", "--untracked-files=all"))

    def fake(self, name, data):
        write(os.path.join(self.bin, name), data, 0o755)

    def commit_promotion(self):
        rc, out = self.script("v18_package.py", "commit-paths"); need(rc == 0, "commit-paths", out)
        paths = [T1_REL + "/" + p for p in out.split()]
        sh("git", "-C", self.mac, "add", "--", *paths)
        gitc(self.mac, "commit", "-q", "-m", "TEST promote v18 (private world)", "--", *paths)

    def net_log(self):
        p = os.path.join(self.bin, "net.log")
        return open(p).read() if os.path.exists(p) else ""

    def running_state(self):
        """What a running refit job and its settlement depend on: the science clone, the job files, the ledger and the plans."""
        return (tree_digest(os.path.join(self.L, "rsc_screen")), tree_digest(os.path.join(self.L, "jobs")),
                sha(os.path.join(self.L, "row19_screen_campaign/budget.json")), tree_digest(os.path.join(self.GS, "plans")))


def git_init(repo):
    os.makedirs(repo, exist_ok=True)
    sh("git", "init", "-q", repo)
    sh("git", "-C", repo, "config", "commit.gpgsign", "false")


def build_fresh(d):
    w = World(d); os.makedirs(d)
    fz = frozen_set()
    # the Mac tree: the frozen adopted v17 allowlist, the v18 candidate package (pinned) and the synthetic controls record
    git_init(w.mac)
    for rel, b in fz.items():
        write(os.path.join(w.t1, rel), b)
    for rel in CAND_SET:
        src = os.path.join(LIVE_T1, rel)
        need(os.path.isfile(src) and not os.path.islink(src), "candidate file missing: " + rel)
        write(os.path.join(w.t1, rel), open(src, "rb").read())
    write(os.path.join(w.t1, REC), REC_TEXT)
    gitc(w.mac, "add", "-A"); gitc(w.mac, "commit", "-q", "-m", "TEST the Mac tree at the adopted v17 (frozen fixture) + the v18 package")
    qb = frozen(FROZEN_QUAL[0]); need(hashlib.sha256(qb).hexdigest() == V17_QUAL, "the frozen pilot qualification is not 8fdbf48e")
    write(os.path.join(w.t1, QUAL_MAC), qb)
    write(os.path.join(w.t1, "aws_ec2/runs/.authority.lock"), "")
    write(os.path.join(w.mac, ".git", "info", "exclude"), "aws_ec2/runs/\n%s/aws_ec2/runs/\n%s/chpc/results/row19_screen/\n" % (T1_REL, T1_REL))
    # the fake Lengau root, as the v17 migration left it
    for sub in ("jobs", "row19_screen/gate/pbs", "row19_screen/gate_retired", "row19_screen/ec2", "row19_screen/plans",
                "row19_screen_campaign", "archive_screen"):
        os.makedirs(os.path.join(w.L, sub), exist_ok=True)
    os.makedirs(w.outside); os.makedirs(w.bin)
    write(os.path.join(w.L, "programme_admission.lock"), ""); write(os.path.join(w.GS, "plans/.submit.lock"), "")
    write(os.path.join(w.GS, "plans/job_53.json"), json.dumps({"job": 53, "token": "t53"}) + "\n")
    write(os.path.join(w.L, "t1py"), FAKE_T1PY, 0o755)
    git_init(w.CR)
    for rel, b in fz.items():
        write(os.path.join(w.C, rel), b)
    gitc(w.CR, "add", "-A"); gitc(w.CR, "commit", "-q", "-m", "TEST the controller clone at the adopted v17 (frozen fixture)")
    for p, (c, want) in EVIDENCE.items():
        b = subprocess.run(["git", "-C", REPO, "show", "%s:%s/%s" % (c, T1_REL, p)], capture_output=True, check=True).stdout
        need(hashlib.sha256(b).hexdigest() == want, "the repository history does not hold the pinned bytes of " + p)
        write(os.path.join(w.C, p), b)
    need(ctl_untracked(w) == sorted(T1_REL + "/" + p for p in EVIDENCE) and ctl_dirty(w) == [], "the Lengau evidence fixture is wrong")
    git_init(os.path.join(w.L, "rsc_screen"))
    for i, f in enumerate(SCI):
        write(os.path.join(w.J, f), "# synthetic science placeholder %d (%s), private test world\n" % (i, f))
    gitc(os.path.join(w.L, "rsc_screen"), "add", "-A"); gitc(os.path.join(w.L, "rsc_screen"), "commit", "-q", "-m", "TEST synthetic science")
    write(os.path.join(w.G, "qualified_refit_job1.json"), qb)
    write(os.path.join(w.G, "review_refit.json"), json.dumps({"schema": "private-test", "role": "refit", "qualification_sha256": V17_QUAL, "max_job_number": 100}) + "\n")
    write(os.path.join(w.G, "watch_refit_1.json"), "{}\n"); write(os.path.join(w.G, "pbs/row19_screen_refit_1.o7600001"), "fake PBS out\n")
    write(os.path.join(w.G, "scaleup_refit_v16.json"), json.dumps({"schema": "private-test-scaleup", "first_job": 46}) + "\n")
    write(os.path.join(w.R, "review_refit.v16_qual2c7a7ef1_max100.json"), "{}\n", 0o444)
    write(os.path.join(w.R, "review_refit.v15_qual3c605514_max100.json"), "{}\n", 0o444)
    write(os.path.join(w.GS, "ec2/activation_e1.json"), json.dumps({"schema": "row19-ec2-activation-1", "epoch": 1,
          "partition_sha256": "8d1de408b6ef9dc66d4736b6138536de6591f0d29ebdd6fd00a6e43307225608"}) + "\n")
    r = subprocess.run([sys.executable, "-B", "-c", GEN_ACT2, w.ACT2], cwd=w.C, capture_output=True, text=True)
    need(r.returncode == 0 and os.path.isfile(w.ACT2), "the canonical activation_e2 fixture could not be generated", r.stdout + r.stderr)
    write(os.path.join(w.L, "jobs/row19_screen_refit_1.pbs"), "#PBS private test\n"); write(os.path.join(w.L, "jobs/row19_screen_refit_47.pbs"), "#PBS private test 47\n")
    write(os.path.join(w.L, "jobs/row19_screen_refit_54.pbs"), "#PBS private test 54\n"); write(os.path.join(w.L, "jobs/row19_screen_refit_53.out"), "exit 0\n")
    write(w.NODE_EV, open(os.path.join(LIVE_T1, "chpc/candidate_v18_nodefail/evidence_row19_screen_refit_54.nodefail.json"), "rb").read(), 0o644)
    need(sha(w.NODE_EV) == NODE_EV_SHA, "the node evidence fixture is not 730ea262")
    write(os.path.join(w.L, "row19_screen_campaign/budget.json"), json.dumps({"cap_core_h": 81000.0, "cap_history": [], "entries": {}}) + "\n")
    write(os.path.join(w.L, "archive_screen/v16_before_v17/COMPLETE"), "schema row19-screen-archive-v16-before-v17-1 (private test placeholder)\n", 0o444)
    write(os.path.join(w.L, "archive_screen/v17_deploy_proof/DONE"), "schema row19-screen-v17-deploy-proof-1\n", 0o444)
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


def stub_receipts(w):
    """The two receipt commands run as private stubs through a python3 wrapper on the Mac PATH; the promoted v18 status view
    and the bank controller stay in place (the promotion checks see their real bytes)."""
    write(os.path.join(w.bin, "stub_status.py"), STUB_STATUS); write(os.path.join(w.bin, "stub_bank.py"), STUB_BANK)
    w.fake("python3", PY_WRAPPER)


def unstub_receipts(w):
    for f in ("python3", "stub_status.py", "stub_bank.py", "stub_bank.mode"):
        if os.path.exists(os.path.join(w.bin, f)):
            os.remove(os.path.join(w.bin, f))


ORDER = ["fresh", "archived", "promoted", "deployed", "receipted", "rolled", "qualified"]
STAGES = {}


def fake_qualification(w):
    """A synthetic regenerated qualification (as the ONE --qualify 1 call writes it): Mac copy + gate copy + receipts."""
    R = os.path.join(w.t1, "chpc/results/row19_screen/receipts"); stamp = "20261021T101010Z"
    vp = os.path.join(R, "verify_refit_%s.json" % stamp)
    write(vp, json.dumps({"generation": {"version": 18, "latest": 18, "controls_problem": "", "controls_sha256": V18_CONTROLS}}))
    write(os.path.join(R, "watch_refit_%s.json" % stamp), json.dumps({"role": "refit", "time": 1.0, "alarms": []}))
    write(os.path.join(R, "watch_refit_20261020T033232Z.json"), json.dumps({"role": "refit", "old": True}))
    q = {"schema": "private-test-qualification", "role": "refit", "qualified_job": 1, "production": True, "verify_file": os.path.basename(vp),
         "bound": {"verify_file_sha256": sha(vp)}, "receipt": {"alarms": [], "fresh": True, "production": True,
                                                               "note": "earlier evidence watch_refit_20261020T033232Z.json"}}
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
            rc, out = w.script("archive_v17.sh"); need(rc == 0 and "ARCHIVE OK" in out, "stage archive", out)
        elif name == "promoted":
            rc, out = w.promote("--review", REC); need(rc == 0 and "promoted:" in out, "stage promote", out); w.commit_promotion()
        elif name == "deployed":
            rc, out = w.script("deploy_v18.sh"); need(rc == 0 and "DEPLOY OK" in out, "stage deploy", out)
        elif name == "receipted":
            stub_receipts(w); rc, out = w.script("receipts_v18.sh"); need(rc == 0 and "V18 RECEIPTS OK" in out, "stage receipts", out)
            unstub_receipts(w)
        elif name == "rolled":
            rc, out = w.script("lengau.sh", "rollover_pilot_v18.sh"); need(rc == 0 and "retired to" in out, "stage rollover", out)
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


def pilot_record(w, qsha, name="reviews/test_pilot_v18_record.md", filler=0, literal=True):
    p = os.path.join(w.t1, name)
    body = "# test pilot record\n\n```text\n%s\n```\n" % ("ADOPT row19-screen-pilot role=refit qualification=%s max_job=100" % qsha if literal else "no literal")
    body += "".join("filler line %d of the review body to exceed four kilobytes of sed output buffering\n" % i for i in range(filler))
    write(p, body)
    sh("git", "-C", w.mac, "add", "--", T1_REL + "/" + name); gitc(w.mac, "commit", "-q", "-m", "TEST pilot record", "--", T1_REL + "/" + name)
    return name


# ================================================================================================ static and boundary
@test("static: no test hook, one fixed root, one fixed transport, one filled real record line, no worker/reaper stop, no AWS/EC2/activation call, no `| grep -q`, every file parses")
def t_static():
    for f in PROD_FILES:
        s = open(os.path.join(HERE, f)).read()
        if f == "RUNBOOK.md":
            continue
        for bad in ("FAKE_LENGAU", "V18_FAKE", "V18_T=", "TEST_ROOT", "PRIVATE TEST"):
            need(bad not in s, "%s mentions %s" % (f, bad))
        for bad in ("qdel", "pkill", "kill ", "killall", "scp ", "aws ", "boto3", "--force", "git add -A", "git add .",
                    "ec2_sync.py", "prod_authority.py", "row19_partition.py activate", "partition.py activate"):
            need(bad not in s, "%s contains %r" % (f, bad))
        if f.endswith(".sh"):
            r = subprocess.run(["bash", "-n", os.path.join(HERE, f)], capture_output=True, text=True); need(r.returncode == 0, "bash -n " + f, r.stderr)
            need(not re.search(r"\|\s*grep\s+(-[A-Za-z]*q|--quiet)", s), "%s pipes into grep -q (SIGPIPE under pipefail: the 9df2a1f bug)" % f)
        if f.endswith(".py"):
            compile(s, f, "exec")
    tags = {f: open(os.path.join(HERE, f)).read().count("@transport") for f in PROD_FILES if f != "RUNBOOK.md"}
    need(sum(tags.values()) == 1 and tags["lengau.sh"] == 1, "exactly one @transport line, in lengau.sh: %s" % tags)
    lt = [l for l in open(os.path.join(HERE, "lengau.sh")).read().splitlines() if "@transport" in l][0]
    need(TRANSPORT in lt, "the transport line is not the fixed production ssh", lt)
    need(open(os.path.join(HERE, "remote_lib.sh")).read().count(ROOT_LINE) == 1, "remote_lib.sh lacks the single fixed root line")
    rec = {f: open(os.path.join(HERE, f)).read().count("# @record") for f in PROD_FILES if f != "RUNBOOK.md"}
    need(sum(rec.values()) == 1 and rec["v18_package.py"] == 1, "exactly one @record line, in v18_package.py: %s" % rec)
    need(open(os.path.join(HERE, "v18_package.py")).read().splitlines().count(RECORD_LINE) == 1,
         "the production @record line is not the one filled real record (%s, %s)" % (PROD_REC, PROD_REC_SHA[:16]))
    for f in ("check_v18.sh", "rollover_pilot_v18.sh", "adopt_pilot18.sh"):
        need("/mnt/lustre" not in open(os.path.join(HERE, f)).read(), "%s names a toolchain root of its own" % f)
    need("PENDINGBUILDER" not in open(os.path.join(HERE, "v18_package.py")).read() + open(os.path.join(HERE, "mac_archive.py")).read()
         and "PENDINGPROMOTER" not in open(os.path.join(HERE, "v18_package.py")).read(), "a package pin is still a placeholder")


@test("static: the composed production Lengau script (each direct body) carries exactly the production root and parses")
def t_compose():
    for body in ("rollover_pilot_v18.sh", "adopt_pilot18.sh", "check_v18.sh"):
        r = subprocess.run(["bash", "-c", '. "$1"; compose "$2"', "x", os.path.join(HERE, "lengau.sh"), body], capture_output=True, text=True)
        need(r.returncode == 0, "compose %s failed" % body, r.stderr)
        need(ROOT_LINE in r.stdout and r.stdout.count("T_ROOT=") == 1, "the composed %s does not carry exactly the production root" % body)
        p = subprocess.run(["bash", "-n"], input=r.stdout, capture_output=True, text=True); need(p.returncode == 0, "composed %s does not parse" % body, p.stderr)


@test("static: the package identities (controls, map, builder, promoter, sources, node evidence) equal the candidate folder; every script constant agrees with build_v18")
def t_identities():
    VP = package_pins()
    for p, h in VP.PACKAGE.items():
        need(sha(os.path.join(LIVE_T1, p)) == h, "the candidate %s is not the pinned %s" % (p, h[:8]))
    need(VP.LITERAL == "ADOPT row19-screen-controls sha256=%s version=18" % V18_CONTROLS and VP.V18_CONTROLS == V18_CONTROLS, "literal")
    need(VP.REC == PROD_REC and VP.REC_SHA == PROD_REC_SHA, "the production record pin is not the real record: %s %s" % (VP.REC, VP.REC_SHA))
    need(PROD_REC != REC and PROD_REC_SHA != hashlib.sha256(REC_TEXT.encode()).hexdigest(), "the synthetic record is not distinct from production")
    need(sha(os.path.join(LIVE_T1, PROD_REC)) == PROD_REC_SHA, "the real record %s is not %s" % (PROD_REC, PROD_REC_SHA[:16]))
    need(VP.LITERAL in [l.strip() for l in open(os.path.join(LIVE_T1, PROD_REC)).read().splitlines()], "the real record lacks the literal line")
    rl = open(os.path.join(HERE, "remote_lib.sh")).read()
    for k, v in (("V17_CONTROLS", V17_CONTROLS), ("V18_CONTROLS", V18_CONTROLS), ("V17_QUAL", V17_QUAL), ("V16_QUAL", V16_QUAL),
                 ("NODE_EV_SHA", NODE_EV_SHA), ("V17_ADOPTION", FROZEN["chpc/row19_screen_controls_adoption.json"]),
                 ("E2_PART", FROZEN["chpc/row19_partition_e2.json"])):
        need("%s=%s" % (k, v) in rl, "remote_lib.sh %s is not %s" % (k, v[:8]))
    sys.path.insert(0, os.path.join(LIVE_T1, "chpc", "candidate_v18_nodefail"))
    try:
        sys.modules.pop("build_v18", None); import build_v18 as B
    finally:
        sys.path.pop(0)
    m = re.search(r'^V17_REPLACED="(.*?)"$', rl, re.S | re.M)
    rep = dict(l.split(" ") for l in m.group(1).split("\n"))
    need(rep == {d: p for d, s, p in B.MAP if p}, "V17_REPLACED is not the two replaced pins of build_v18: %s" % rep)
    new = re.search(r'^V18_NEW="(.*?)"$', rl, re.M).group(1).split()
    need(sorted(new) == sorted(d for d, s, p in B.MAP if p is None), "V18_NEW is not the two new paths")
    need(len(B.ARCHIVE) == 8 and B.ARCHIVE["row19_screen_refit_54.nodefail.json"][1] == NODE_EV_SHA
         and B.ARCHIVE["qualified_refit_job1.json"][1] == V17_QUAL, "the builder's archive inventory is not the 8 members")
    ma = open(os.path.join(HERE, "mac_archive.py")).read()
    need('BUILDER_SHA = "%s"' % VP.PACKAGE["chpc/candidate_v18_nodefail/build_v18.py"] in ma, "mac_archive.py pins another builder")
    for f in ("package_qual_v18.py", "receipt_check_v18.py"):
        need(V18_CONTROLS in open(os.path.join(HERE, f)).read(), "%s does not name the v18 controls" % f)
    sys.modules.pop("build_v18", None)


@test("static: the frozen fixture - one pinned commit, every member at its pinned hash, the 17 v17 pins verified; nothing read from the live controller state")
def t_frozen():
    fz = frozen_set()
    need(len(fz) == len(FROZEN) + 17, "the frozen allowlist is not FROZEN + 17 v17 pins (%d)" % len(fz))
    need(hashlib.sha256(frozen(FROZEN_QUAL[0])).hexdigest() == V17_QUAL, "the frozen qualification is not 8fdbf48e")
    need(not set(FROZEN) & set(CAND_SET) and all(not r.startswith("chpc/candidate_") for r in fz), "the frozen set overlaps the candidate package")
    need(all(r.startswith("chpc/candidate_v18_nodefail/") for r in CAND_SET), "a non-candidate file would be read from the working tree")


@test("static: CTL_EVIDENCE (remote_lib.sh) and UNTRACKED_CTL (lengau_archive.py) are the same three pinned files")
def t_evidence_static():
    rl = open(os.path.join(HERE, "remote_lib.sh")).read()
    m = re.search(r'^CTL_EVIDENCE="(.*?)"$', rl, re.S | re.M); need(m is not None, "remote_lib.sh has no CTL_EVIDENCE")
    sh_list = dict(l.split(" ") for l in m.group(1).split("\n"))
    sys.path.insert(0, HERE)
    try:
        sys.modules.pop("lengau_archive", None); import lengau_archive as LA
    finally:
        sys.path.pop(0); sys.modules.pop("lengau_archive", None)
    want = {p: h for p, (_, h) in EVIDENCE.items()}
    need(sh_list == want and LA.UNTRACKED_CTL == want, "the allowlists differ")


LENGAU_BODIES = ["remote_lib.sh", "preflight_v18.sh", "archive_v17.sh", "deploy_v18.sh", "check_v18.sh", "rollover_pilot_v18.sh", "adopt_pilot18.sh"]
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
    for k in ("LOCK_PY", "ACT_PY"):
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


@test("Lengau compat: every Lengau-side Python (lengau_archive.py, LOCK_PY, ACT_PY, each t1py -c body) is 3.6-level code")
def t_py36():
    probe = "import subprocess, dataclasses\nr = subprocess.run(['x'], capture_output=True, text=True)\nprint(f'{r}')\n"
    need(len(py36_problems(probe, "probe")) == 4, "the scanner misses known 3.7+ features")
    srcs = lengau_python_sources()
    need(len([k for k in srcs if ":t1py-c#" in k]) >= 7, "expected the t1py -c bodies on the Lengau side: %s" % sorted(srcs))
    bad = [p for name, src in sorted(srcs.items()) for p in py36_problems(src, name)]
    need(not bad, "Lengau-side Python uses features newer than 3.6:\n" + "\n".join(bad))


@test("boundary: a body run without the prelude refuses; lengau.sh refuses any other body; the harness refuses an alias of production")
def t_boundary():
    w = stage("fresh")
    for b in ("rollover_pilot_v18.sh", "adopt_pilot18.sh", "check_v18.sh"):
        rc, out = w.run("bash", "chpc/migration_v18/" + b); refused(rc, out)
        need("ABORT" not in out or "run through" in out or "sourced through" in out, "a body ran without the prelude", out)
    for b in ("preflight_v18.sh", "check_v18.sh", "deploy_v18.sh"):
        rc, out = w.script("lengau.sh", b); refused(rc, out, "runs only")
    alias = os.path.join(w.d, "alias_prod"); os.symlink(PROD_ROOT, alias)
    try:
        w.install(alias); raise Fail("install accepted an alias of the production toolchain")
    except Fail as e:
        need("refusing" in str(e), str(e))
    w.install()


@test("record pin: v18_package.py with its record pin explicitly PENDING (install(record=False)) refuses preflight, check-promoted, payload and every step; a record of other bytes or without the literal refuses")
def t_record_pending():
    w = stage("fresh"); w.install(record=False)
    for args in (("v18_package.py", "preflight"), ("v18_package.py", "payload"), ("preflight_v18.sh",), ("archive_v17.sh",)):
        rc, out = w.script(*args); refused(rc, out, "PENDING")
    need(not os.path.exists(w.A) and not os.path.exists(w.MA), "an archive was built without the record pin")
    w = stage("fresh"); p = os.path.join(w.t1, REC); write(p, REC_TEXT + "edited\n"); gitc(w.mac, "commit", "-q", "-am", "TEST another record")
    rc, out = w.script("preflight_v18.sh"); refused(rc, out, "not the pinned record")
    w = stage("promoted"); w.install(record=False); s0 = w.ctl_state()
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "PENDING"); need(w.ctl_state() == s0 and not os.path.lexists(w.PROOF), "deployed without the record pin")


@test("boundary: a valid isolated fake root reached through an alias passes preflight (every path resolves beneath its physical root)")
def t_alias_root_ok():
    w = stage("fresh"); alias = os.path.join(w.d, "alias_root"); os.symlink(w.L, alias); w.install(alias)
    rc, out = w.script("preflight_v18.sh"); need(rc == 0 and "PREFLIGHT OK" in out, "preflight through a private alias", out)


# ================================================================================================ the positive route
@test("positive route: preflight, archive (+re-run), promote_v18 (+re-run), commit, deploy (+re-run), receipts, rollover (+re-run), package, adopt; running jobs and epoch 2 untouched")
def t_positive():
    w = stage("fresh")
    act0 = sha(w.ACT2); ev0 = sha(w.NODE_EV); run0 = w.running_state()
    rc, out = w.script("preflight_v18.sh", "--local-only"); need(rc == 0 and "Lengau checks were NOT run" in out, "local-only", out)
    rc, out = w.script("preflight_v18.sh")
    need(rc == 0 and "PREFLIGHT OK" in out and "archive sources complete" in out and "lengau tools:" in out and "mac preflight OK" in out
         and "epoch 2 active" in out and "activation_problem ''" in out, "preflight", out)
    need("gate: scaleup_refit_v16.json present" in out, "preflight did not report the scale-up adoption", out)
    rc, out = w.script("archive_v17.sh", "--dry-run"); need(rc == 0 and "DRY RUN" in out and not os.path.exists(w.A), "archive dry run", out)
    rc, out = w.script("archive_v17.sh"); need(rc == 0 and "ARCHIVE OK" in out and "archive built" in out, "archive", out)
    need(set(os.listdir(w.A)) == {"COMPLETE", "SHA256SUMS", "INVENTORY.gate", "INVENTORY.jobs", "ctl", "gate", "jobs", "ledger", "ec2"}, "archive layout")
    need(sha(os.path.join(w.A, "jobs/row19_screen_refit_54.nodefail.json")) == NODE_EV_SHA, "the archive does not retain the node document")
    need(sorted(os.listdir(os.path.join(w.A, "ec2"))) == ["activation_e1.json", "activation_e2.json"], "the archive does not hold both activations")
    need(os.path.isfile(os.path.join(w.A, "ctl/reviews/2026-10-20_pilot_v17_codex_review.md")) and
         os.path.isfile(os.path.join(w.A, "gate/scaleup_refit_v16.json")), "the archive lacks the pilot record or the scale-up adoption")
    need("node_evidence %s" % NODE_EV_SHA in open(os.path.join(w.A, "COMPLETE")).read(), "COMPLETE does not certify the node document")
    need(len(os.listdir(w.MA)) == 10 and os.path.isfile(w.LSF) and sha(w.LSF) == sha(os.path.join(w.A, "SHA256SUMS")), "Mac archive layout / Lengau sums copy")
    need(sha(os.path.join(w.MA, "row19_screen_refit_54.nodefail.json")) == NODE_EV_SHA, "the Mac archive does not retain the node document")
    rc, out = w.script("archive_v17.sh"); need(rc == 0 and "exists and verifies" in out and "names this Lengau archive" in out, "archive re-run", out)
    rc, out = w.script("preflight_v18.sh"); refused(rc, out, "already exists")
    rc, out = w.promote("--check-promoted", "--review", REC); refused(rc, out, "not complete")
    rc, out = w.promote("--dry-run", "--review", REC); need(rc == 0 and "DRY RUN" in out, "promote dry run", out)
    rc, out = w.promote("--review", REC); need(rc == 0 and "promoted:" in out, "promote", out)
    rc, out = w.promote("--review", REC); need(rc == 0 and "already promoted, verified" in out, "promote re-run", out)
    rc, out = w.promote("--check"); need(rc == 0 and "authenticated archive v17 base" in out, "promote --check after the promotion (archive base)", out)
    rc, out = w.run("python3", "chpc/candidate_v18_nodefail/build_v18.py", "--check"); need(rc == 0 and "archive v17 base" in out, "build --check after", out)
    ad = json.load(open(os.path.join(w.t1, "chpc/row19_screen_controls_adoption.json")))
    need(ad["version"] == 18 and ad["controls_sha256"] == V18_CONTROLS and ad["previous"]["adoption_sha256"] == FROZEN["chpc/row19_screen_controls_adoption.json"]
         and ad["review_record"]["path"] == REC, "the version-18 adoption record: %s" % ad)
    rc, out = w.script("deploy_v18.sh", "--dry-run"); refused(rc, out, "not committed")
    w.commit_promotion()
    rc, out = w.script("deploy_v18.sh", "--dry-run"); need(rc == 0 and "DRY RUN" in out, "deploy dry run", out)
    jh = sh("git", "-C", os.path.join(w.L, "rsc_screen"), "rev-parse", "HEAD"); gd = tree_digest(w.G)
    h0 = sh("git", "-C", w.CR, "rev-parse", "HEAD").strip()
    rc, out = w.script("deploy_v18.sh")
    need(rc == 0 and "DEPLOY OK" in out and "science bytes UNCHANGED (8 files" in out and "IDENTICAL" in out and "epoch 2 STILL ACTIVE" in out
         and "deploy proof written before any controller change" in out and "compile and the JSON payloads parse" in out
         and "accepted under the current version 18; activation_problem ''" in out, "deploy", out)
    need(w.running_state() == run0 and sh("git", "-C", os.path.join(w.L, "rsc_screen"), "rev-parse", "HEAD") == jh,
         "the science clone, job files, ledger or plans changed (running jobs must survive untouched)")
    need(tree_digest(w.G) == gd and sha(w.ACT2) == act0 and sha(w.NODE_EV) == ev0, "the gate, the activation or the node document changed in the deploy")
    cp = sh("git", "-C", w.CR, "diff", "--name-only", h0, "HEAD").split()
    need(sorted(cp) == sorted(T1_REL + "/" + p for p in (REC, "chpc/row19_screen_nodefail.py", "chpc/row19_nodefail_capture.py",
         "chpc/row19_screen_status.py", "chpc/row19_screen_admit.py", "chpc/row19_screen_controls.json", "chpc/row19_screen_controls_adoption.json"))
         and ctl_untracked(w) == sorted(T1_REL + "/" + p for p in EVIDENCE), "the deploy commit is not exactly the 7 payload paths: %s" % cp)
    need(sha(os.path.join(w.C, "chpc/row19_screen_controls.json")) == V18_CONTROLS, "the v18 controls are not in the controller clone")
    rc, out = w.script("deploy_v18.sh"); need(rc == 0 and "already holds exactly these v18 bytes" in out and "DEPLOY OK" in out, "deploy re-run", out)
    stub_receipts(w)
    rc, out = w.script("receipts_v18.sh"); need(rc == 0 and "RECEIPT OK" in out and "V18 RECEIPTS OK" in out and "lengau check OK" in out, "receipts", out)
    unstub_receipts(w)
    rc, out = w.script("lengau.sh", "rollover_pilot_v18.sh"); need(rc == 0 and "retired to" in out, "rollover", out)
    need(not os.path.exists(os.path.join(w.G, "review_refit.json")) and os.path.isfile(os.path.join(w.G, "scaleup_refit_v16.json"))
         and os.path.isfile(os.path.join(w.R, "review_refit.v16_qual2c7a7ef1_max100.json")), "rollover moved the wrong file")
    rc, out = w.script("lengau.sh", "rollover_pilot_v18.sh"); need(rc == 0 and "already retired (verified)" in out, "rollover re-run", out)
    rc, out = w.script("package_qual_v18.py"); refused(rc, out, "still the v17 8fdbf48e")
    qsha = fake_qualification(w)
    rc, out = w.script("package_qual_v18.py"); need(rc == 0 and "packaged" in out and qsha in out, "package", out)
    pd = os.path.join(w.t1, "chpc", "qualification_v18_" + qsha[:8])
    need(sorted(os.listdir(pd)) == sorted(["SHA256SUMS", "qualified_refit_job1.json", "verify_refit_20261021T101010Z.json", "watch_refit_20261021T101010Z.json",
         "watch_refit_20261020T033232Z.json", "mac_archive_v17_before_v18.SHA256SUMS", "lengau_archive_v17_before_v18.SHA256SUMS.txt"]), "package layout %s" % os.listdir(pd))
    rc, out = w.script("package_qual_v18.py"); need(rc == 0 and "exists and verifies" in out, "package re-run", out)
    rec = pilot_record(w, qsha)
    rc, out = w.script("lengau.sh", "adopt_pilot18.sh", "--file", rec); need(rc == 0 and "adopt_pilot18 complete" in out, "adopt", out)
    need(json.load(open(os.path.join(w.G, "review_refit.json")))["qualification_sha256"] == qsha, "the simulated adopter wrote another review")
    rc, out = w.script("lengau.sh", "adopt_pilot18.sh", "--file", rec); refused(rc, out, "an active review exists")
    need(sha(w.ACT2) == act0 and sha(w.NODE_EV) == ev0 and w.running_state() == run0, "epoch 2, the node document or a running job's state changed")
    need(w.net_log() == "", "something tried ssh/scp: " + w.net_log())


@test("Lengau compat: the whole route runs on the restricted git and flock CLIs (no rejected call, no python fallback for a decidable lock)")
def t_lengau_route():
    w = stage("fresh"); w.fake("flock", FAKE_FLOCK)
    rc, out = w.script("preflight_v18.sh"); need(rc == 0 and "PREFLIGHT OK" in out and "trying the python fcntl probe" not in out, "preflight", out)
    rc, out = w.script("archive_v17.sh"); need(rc == 0 and "ARCHIVE OK" in out, "archive", out)
    rc, out = w.promote("--review", REC); need(rc == 0, "promote", out); w.commit_promotion()
    rc, out = w.script("deploy_v18.sh"); need(rc == 0 and "DEPLOY OK" in out, "deploy", out)
    rc, out = w.script("deploy_v18.sh"); need(rc == 0 and "DEPLOY OK" in out, "deploy re-run", out)
    stub_receipts(w); rc, out = w.script("receipts_v18.sh"); need(rc == 0, "receipts", out); unstub_receipts(w)
    rc, out = w.script("lengau.sh", "rollover_pilot_v18.sh"); need(rc == 0, "rollover", out)
    qsha = fake_qualification(w); rec = pilot_record(w, qsha)
    rc, out = w.script("lengau.sh", "adopt_pilot18.sh", "--file", rec); need(rc == 0, "adopt", out)
    log = open(os.path.join(w.lbin, "git.log")).read()
    for want in ("rev-parse --show-toplevel", "rev-parse --git-dir", "status --porcelain --untracked-files=all", "rev-parse --verify HEAD",
                 "merge-base --is-ancestor", "diff-tree --no-commit-id --name-only -r", "ls-files"):
        need(want in log, "the Lengau half never ran `git %s` through the restricted shim" % want, log[-2000:])
    need(not os.path.exists(os.path.join(w.lbin, "git.rejected")), "a Lengau-side git call used a rejected interface",
         open(os.path.join(w.lbin, "git.rejected")).read() if os.path.exists(os.path.join(w.lbin, "git.rejected")) else "")
    need("trying the python fcntl probe" not in out, "a decidable lock fell back to python", out)


# ================================================================================================ step 1: preflight
@test("preflight refuses (Mac): a changed package byte (controls, map, builder, promoter, a source, the node evidence), a held authority lock, a busy Mac")
def t_preflight_mac():
    for rel in ("row19_screen_controls.json", "v18_promotion_map.json", "build_v18.py", "promote_v18.py", "row19_screen_nodefail.py",
                "row19_nodefail_capture.py", "evidence_row19_screen_refit_54.nodefail.json"):
        w = stage("fresh"); open(os.path.join(w.t1, "chpc/candidate_v18_nodefail", rel), "a").write("\n")
        rc, out = w.script("preflight_v18.sh"); refused(rc, out, rel, "not the pinned")
    w = stage("fresh")
    with Holder(os.path.join(w.t1, "aws_ec2/runs/.authority.lock")):
        rc, out = w.script("preflight_v18.sh")
    refused(rc, out, "authority lock")
    for line in ("python3 aws_ec2/ec2_sync.py cycle", "caffeinate -i python3 aws_ec2/bench_reaper.py --run qual-E2Q1", "bash refill_r1.sh"):
        w = stage("fresh"); write(os.path.join(w.bin, "ps_x.out"), "bash -s\n%s\n" % line)
        rc, out = w.script("preflight_v18.sh"); refused(rc, out, "runs on the Mac")
    w = stage("fresh"); write(os.path.join(w.bin, "ps_x.rc"), "1"); rc, out = w.script("preflight_v18.sh"); refused(rc, out, "Mac process inventory failed")


@test("preflight refuses (Mac): live tree not v17 (status edited / a v18 path present), Mac qualification not 8fdbf48e, pilot record changed, uncommitted budget")
def t_preflight_mac_state():
    w = stage("fresh"); write(os.path.join(w.t1, "chpc/row19_screen_nodefail.py"), "# early\n")
    rc, out = w.script("preflight_v18.sh"); refused(rc, out, "row19_screen_nodefail.py")
    w = stage("fresh"); open(os.path.join(w.t1, "chpc/row19_screen_status.py"), "a").write("# x\n")
    rc, out = w.script("preflight_v18.sh"); refused(rc, out, "row19_screen_status.py")
    w = stage("fresh"); write(os.path.join(w.t1, QUAL_MAC), "{}\n")
    rc, out = w.script("preflight_v18.sh"); refused(rc, out, "8fdbf48e")
    w = stage("fresh"); open(os.path.join(w.t1, "reviews/2026-10-20_pilot_v17_codex_review.md"), "a").write(" ")
    rc, out = w.script("preflight_v18.sh"); refused(rc, out, "pilot record")
    w = stage("fresh"); open(os.path.join(w.t1, "chpc/row19_screen_budget.json"), "a").write(" ")
    rc, out = w.script("preflight_v18.sh"); refused(rc, out, "row19_screen_budget.json")


@test("preflight refuses (Lengau): a v18 path in the controller, no/invalid epoch-2 activation, node document missing/changed, review not bound to 8fdbf48e, ledger cap, leftovers, controller not v17")
def t_preflight_lengau():
    w = stage("fresh"); write(os.path.join(w.C, "chpc/row19_nodefail_capture.py"), "# early\n")
    sh("git", "-C", w.CR, "add", "--", T1_REL + "/chpc/row19_nodefail_capture.py"); gitc(w.CR, "commit", "-q", "-m", "x")
    rc, out = w.script("preflight_v18.sh"); refused(rc, out, "row19_nodefail_capture.py")
    w = stage("fresh"); os.remove(w.ACT2); rc, out = w.script("preflight_v18.sh"); refused(rc, out, "epoch-2 activation proof")
    w = stage("fresh"); d = json.load(open(w.ACT2)); d["owned_sha256"] = "0" * 64; json.dump(d, open(w.ACT2, "w"))
    rc, out = w.script("preflight_v18.sh"); refused(rc, out, "not the canonical epoch-2 activation")
    w = stage("fresh"); os.remove(w.NODE_EV); rc, out = w.script("preflight_v18.sh"); refused(rc, out, "node document")
    w = stage("fresh"); open(w.NODE_EV, "a").write(" "); rc, out = w.script("preflight_v18.sh"); refused(rc, out, "730ea262")
    w = stage("fresh"); write(os.path.join(w.G, "review_refit.json"), "{}\n"); rc, out = w.script("preflight_v18.sh"); refused(rc, out, "not bound to qualification 8fdbf48e")
    w = stage("fresh"); write(os.path.join(w.L, "row19_screen_campaign/budget.json"), json.dumps({"cap_core_h": 60000.0}))
    rc, out = w.script("preflight_v18.sh"); refused(rc, out, "81,000")
    w = stage("fresh"); os.makedirs(os.path.join(w.L, "archive_screen/v18_deploy_proof")); rc, out = w.script("preflight_v18.sh"); refused(rc, out, "v18 deploy proof")
    w = stage("fresh"); os.makedirs(os.path.join(w.L, "archive_screen/.v17_before_v18.staging.9")); rc, out = w.script("preflight_v18.sh"); refused(rc, out, "interrupted archive build")
    w = stage("fresh"); write(w.RETIRED, "{}\n"); rc, out = w.script("preflight_v18.sh"); refused(rc, out, "retirement target")
    w = stage("fresh"); p = os.path.join(w.C, "chpc/row19_screen_controls_adoption.json"); open(p, "a").write(" "); gitc(w.CR, "commit", "-q", "-am", "x")
    rc, out = w.script("preflight_v18.sh"); refused(rc, out, "61ca680e")


# ================================================================================================ step 2: archives
@test("archive: one-file remote archive refuses and is left as it was; missing ledger / activation_e2 / node document / pilot record / review / jobs refuse")
def t_archive_incomplete():
    w = stage("fresh"); write(os.path.join(w.A, "gate/qualified_refit_job1.json"), open(os.path.join(w.G, "qualified_refit_job1.json"), "rb").read())
    write(os.path.join(w.A, "SHA256SUMS"), "%s  ./gate/qualified_refit_job1.json\n" % V17_QUAL); before = tree_digest(w.A)
    rc, out = w.script("archive_v17.sh"); refused(rc, out, "does not verify as complete")
    need(tree_digest(w.A) == before and not os.path.exists(w.MA), "the partial archive changed, or the Mac half ran")
    w = stage("fresh"); os.remove(os.path.join(w.L, "row19_screen_campaign/budget.json")); rc, out = w.script("archive_v17.sh"); refused(rc, out, "missing")
    need(not os.path.exists(w.A) and not os.path.exists(w.MA), "published without the ledger")
    w = stage("fresh"); os.remove(w.ACT2); rc, out = w.script("archive_v17.sh"); refused(rc, out, "activation")
    need(not os.path.exists(w.A), "published without activation_e2")
    w = stage("fresh"); os.remove(w.NODE_EV); rc, out = w.script("archive_v17.sh"); refused(rc, out, "node document")
    need(not os.path.exists(w.A), "published without the node document")
    for f in ("chpc/row22_bank_submit.py", "reviews/2026-10-20_pilot_v17_codex_review.md", "chpc/row19_partition_e1.json"):
        w = stage("fresh"); sh("git", "-C", w.CR, "rm", "-q", "--", T1_REL + "/" + f); gitc(w.CR, "commit", "-q", "-m", "x")
        rc, out = w.script("archive_v17.sh"); refused(rc, out)
        need(not os.path.exists(w.A) and not os.path.exists(w.MA), "an archive was published without " + f)
    w = stage("fresh"); os.remove(os.path.join(w.G, "review_refit.json")); rc, out = w.script("archive_v17.sh"); refused(rc, out, "review_refit.json")
    w = stage("fresh"); [os.remove(os.path.join(w.L, "jobs", f)) for f in os.listdir(os.path.join(w.L, "jobs"))]
    rc, out = w.script("archive_v17.sh"); refused(rc, out)
    need(not os.path.exists(w.A), "published without job files")


@test("archive: failed checksum / unreadable source refuse; an interrupted build (staging left, Lengau or Mac) refuses and is never removed")
def t_archive_interrupted():
    w = stage("fresh"); write(os.path.join(w.bin, "sha.fail"), "qualified_refit_job1"); rc, out = w.script("archive_v17.sh"); refused(rc, out, "cannot hash")
    need(not os.path.exists(w.A), "published after a failed checksum command")
    w = stage("fresh"); os.chmod(os.path.join(w.G, "watch_refit_1.json"), 0)
    rc, out = w.script("archive_v17.sh"); os.chmod(os.path.join(w.G, "watch_refit_1.json"), 0o644); refused(rc, out, "unreadable")
    need(not os.path.exists(w.A) and not [x for x in os.listdir(os.path.join(w.L, "archive_screen")) if "staging" in x], "published or left staging")
    w = stage("fresh"); stg = os.path.join(w.L, "archive_screen/.v17_before_v18.staging.4242"); write(os.path.join(stg, "gate/x"), "partial\n"); before = tree_digest(stg)
    rc, out = w.script("archive_v17.sh"); refused(rc, out, "interrupted archive build")
    need(tree_digest(stg) == before and not os.path.exists(w.A), "the staging evidence changed")
    w = stage("fresh"); os.makedirs(os.path.join(w.t1, "chpc/results/archive/.row19_screen_v17_before_v18.staging.7"))
    rc, out = w.script("archive_v17.sh"); refused(rc, out, "interrupted Mac archive build"); need(not os.path.exists(w.A), "the Lengau half ran")


@test("archive retry: the Lengau half published but the Mac half failed (budget mismatch) -> nothing on the Mac; repaired, the re-run builds the Mac half")
def t_archive_retry_mac_half():
    w = stage("fresh"); p = os.path.join(w.C, "chpc/row19_screen_budget.json"); orig = open(p, "rb").read()
    write(p, orig.replace(b"81000", b"81000 ") if b"81000" in orig else orig + b" "); gitc(w.CR, "commit", "-q", "-am", "TEST another budget")
    rc, out = w.script("archive_v17.sh"); refused(rc, out, "budget phases")
    need(os.path.isdir(w.A) and not os.path.exists(w.MA) and not os.path.exists(w.LSF), "the Lengau archive was not kept, or the Mac half was written")
    unlock_tree(w.A); shutil.rmtree(w.A); write(p, orig); gitc(w.CR, "commit", "-q", "-am", "TEST budget restored")
    rc, out = w.script("archive_v17.sh"); need(rc == 0 and "ARCHIVE OK" in out, "archive after recovery", out)
    w = stage("fresh"); rc, out = w.script("archive_v17.sh"); need(rc == 0, "archive", out)
    unlock_tree(w.MA); shutil.rmtree(w.MA); os.remove(w.LSF)        # an interruption after the Lengau half: no Mac half yet
    rc, out = w.script("archive_v17.sh"); need(rc == 0 and "exists and verifies" in out and "Mac archive" in out and os.path.isdir(w.MA) and os.path.isfile(w.LSF), "Mac half resumed", out)


@test("archive: a self-consistently rewritten Lengau archive (node document, activation_e2 or pilot record dropped) and a substituted Mac member refuse")
def t_archive_subset():
    sys.path.insert(0, HERE)
    try:
        sys.modules.pop("lengau_archive", None); import lengau_archive as LA
    finally:
        sys.path.pop(0); sys.modules.pop("lengau_archive", None)
    for drop in ("jobs/row19_screen_refit_54.nodefail.json", "ec2/activation_e2.json", "ctl/reviews/2026-10-20_pilot_v17_codex_review.md"):
        w = stage("archived"); unlock_tree(w.A); p = os.path.join(w.A, drop); os.remove(p)
        if drop.startswith("jobs/"):
            inv = LA.parse_sums(open(os.path.join(w.A, "INVENTORY.jobs")).read(), "x"); inv.pop(drop)
            write(os.path.join(w.A, "INVENTORY.jobs"), LA.sums_text(inv))
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
        rc, out = w.script("archive_v17.sh"); refused(rc, out, "does not verify as complete")
    w = stage("archived"); os.chmod(w.MA, 0o755)
    for n in os.listdir(w.MA):
        os.chmod(os.path.join(w.MA, n), 0o644)
    write(os.path.join(w.MA, "row19_screen_refit_54.nodefail.json"), "{}\n")
    sums = {n: sha(os.path.join(w.MA, n)) for n in os.listdir(w.MA) if n not in ("SHA256SUMS", "COMPLETE")}
    sb = "".join("%s  %s\n" % (sums[k], k) for k in sorted(sums)).encode(); write(os.path.join(w.MA, "SHA256SUMS"), sb)
    comp = json.load(open(os.path.join(w.MA, "COMPLETE"))); comp["sha256sums"] = hashlib.sha256(sb).hexdigest()
    write(os.path.join(w.MA, "COMPLETE"), json.dumps(comp, indent=1, sort_keys=True) + "\n")
    for n in os.listdir(w.MA):
        os.chmod(os.path.join(w.MA, n), 0o444)
    rc, out = w.script("archive_v17.sh"); refused(rc, out, "does not verify")
    rc, out = w.promote("--dry-run", "--review", REC); refused(rc, out)


@test("Mac archive: writable member, foreign COMPLETE, extra file refuse the strict verify; the builder's archive_problems accepts the real one")
def t_mac_archive_strict():
    w = stage("archived"); rc, out = w.script("mac_archive.py", "verify"); need(rc == 0 and "archive_problems: []" in out, "verify", out)
    p = os.path.join(w.MA, "row19_screen_budget.json"); os.chmod(p, 0o644)
    rc, out = w.script("mac_archive.py", "verify"); refused(rc, out, "writable")
    w = stage("archived"); os.chmod(w.MA, 0o755); p = os.path.join(w.MA, "COMPLETE"); os.chmod(p, 0o644)
    write(p, "schema row19-screen-mac-archive-v16-before-v17-1\n", 0o444); rc, out = w.script("mac_archive.py", "verify"); refused(rc, out, "COMPLETE")
    w = stage("archived"); os.chmod(w.MA, 0o755); write(os.path.join(w.MA, "notes.txt"), "x\n", 0o444)
    rc, out = w.script("mac_archive.py", "verify"); refused(rc, out, "not exactly the 8 members")


# ================================================================================================ step 3: promotion (promote_v18.py)
@test("promote interruption: stopped after the controls copy (adoption still v17) - check-promoted and deploy refuse; promote_v18 resumes from the ARCHIVE base; deploy proceeds")
def t_promote_interrupted():
    w = stage("archived")
    sys.path.insert(0, os.path.join(w.t1, "chpc", "candidate_v18_nodefail"))
    try:
        import importlib
        for m in ("build_v18", "promote_v18"):
            sys.modules.pop(m, None)
        PV = importlib.import_module("promote_v18")
        order = PV.order()
    finally:
        sys.path.pop(0)
        for m in ("build_v18", "promote_v18"):
            sys.modules.pop(m, None)
    need([r["promoted"] for r in order] == ["chpc/row19_screen_nodefail.py", "chpc/row19_nodefail_capture.py", "chpc/row19_screen_status.py",
                                            "chpc/row19_screen_admit.py", "chpc/row19_screen_controls.json"], "the promotion order is not new files, status, admission, controls LAST")
    for r in order:                                   # exactly what the real promoter copies, controls last, then STOP (no adoption)
        write(os.path.join(w.t1, r["promoted"]), open(os.path.join(w.t1, r["source"]), "rb").read())
    rc, out = w.promote("--check"); need(rc == 0 and "archive v17 base" in out, "--check during an interrupted promotion (archive base)", out)
    rc, out = w.promote("--check-promoted", "--review", REC); refused(rc, out, "not complete", "adoption=v17")
    rc, out = w.script("deploy_v18.sh", "--dry-run"); refused(rc, out, "not complete")
    rc, out = w.promote("--review", REC); need(rc == 0 and "promoted:" in out and "adoption" in out, "promote resume", out)
    w.commit_promotion()
    rc, out = w.script("deploy_v18.sh"); need(rc == 0 and "DEPLOY OK" in out, "deploy after the resumed promotion", out)


@test("promote base: after the promotion a missing or corrupted Mac archive refuses every promote_v18/build_v18 command (no live v18 base is ever accepted)")
def t_promote_base():
    w = stage("promoted"); unlock_tree(w.MA); shutil.rmtree(w.MA)
    for args in (("--check",), ("--check-promoted", "--review", REC)):
        rc, out = w.promote(*args); refused(rc, out, "no authenticated v17 base")
    rc, out = w.run("python3", "chpc/candidate_v18_nodefail/build_v18.py", "--check"); refused(rc, out, "no authenticated v17 base")
    w = stage("promoted"); os.chmod(w.MA, 0o755); p = os.path.join(w.MA, "row19_screen_controls.json"); os.chmod(p, 0o644); open(p, "a").write(" ")
    rc, out = w.promote("--check"); refused(rc, out, "does not verify")
    w = stage("archived"); p = os.path.join(w.t1, "chpc/row19_screen_admit.py"); open(p, "a").write("# x\n")
    rc, out = w.promote("--review", REC); refused(rc, out, "neither their v17 nor their v18 bytes")


# ================================================================================================ step 4: deploy
@test("deploy refuses before any controller change: one-file / corrupted Lengau archive, uncommitted promotion, a broken epoch-2 activation, a changed node document")
def t_deploy_archive():
    def onefile(w):
        unlock_tree(w.A); shutil.rmtree(w.A)
        write(os.path.join(w.A, "gate/qualified_refit_job1.json"), open(os.path.join(w.G, "qualified_refit_job1.json"), "rb").read())
        write(os.path.join(w.A, "SHA256SUMS"), "%s  ./gate/qualified_refit_job1.json\n" % V17_QUAL)
    def flip(w):
        p = os.path.join(w.A, "gate/review_refit.json"); os.chmod(p, 0o644); open(p, "a").write(" "); os.chmod(p, 0o444)
    def nocomplete(w):
        os.chmod(w.A, 0o755); os.remove(os.path.join(w.A, "COMPLETE"))
    for mut in (onefile, flip, nocomplete):
        w = stage("promoted"); mut(w); s0 = w.ctl_state()
        rc, out = w.script("deploy_v18.sh"); refused(rc, out, "does not verify as complete")
        need(w.ctl_state() == s0 and not os.path.lexists(w.PROOF), "the controller clone changed after %s" % mut.__name__)
    w = stage("archived"); rc, out = w.promote("--review", REC); need(rc == 0, "promote", out); s0 = w.ctl_state()
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "not committed"); need(w.ctl_state() == s0, "deployed an uncommitted promotion")
    w = stage("promoted"); d = json.load(open(w.ACT2)); d["controls_version"] = 16; json.dump(d, open(w.ACT2, "w")); s0 = w.ctl_state()
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "not the canonical epoch-2 activation"); need(w.ctl_state() == s0 and not os.path.lexists(w.PROOF), "deployed")
    w = stage("promoted"); open(w.NODE_EV, "a").write(" "); s0 = w.ctl_state()
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "730ea262"); need(w.ctl_state() == s0 and not os.path.lexists(w.PROOF), "deployed")


@test("deploy: drain observations (ps failed/empty, a settlement in flight, a capture running, a held lock, no probe) refuse before any controller change")
def t_deploy_drain():
    cases = [("ps_u.rc", "23", "process inventory failed"), ("ps_u.out", "", "process inventory is empty"),
             ("ps_u.out", "bash -s\n/x/t1py chpc/programme_gate.py settle --manifest m -- t1py chpc/row19_ledger.py settle\n", "a controller command runs"),
             ("ps_u.out", "bash -s\n/x/t1py chpc/row19_nodefail_capture.py --manifest m --role refit --job 55\n", "a controller command runs")]
    for f, data, msg in cases:
        w = stage("promoted"); write(os.path.join(w.bin, f), data); s0 = w.ctl_state()
        rc, out = w.script("deploy_v18.sh"); refused(rc, out, msg); need(w.ctl_state() == s0 and not os.path.lexists(w.PROOF), "changed: " + msg)
    for with_flock in (False, True):
        w = stage("promoted"); s0 = w.ctl_state()
        if with_flock:
            w.fake("flock", FAKE_FLOCK)
        with Holder(os.path.join(w.GS, "plans/.submit.lock")):
            rc, out = w.script("deploy_v18.sh")
        refused(rc, out, "lock held"); need(w.ctl_state() == s0, "deployed under a held lock")
    w = stage("promoted"); write(os.path.join(w.L, "t1py.nofcntl"), ""); w.fake("flock", BROKEN_FLOCK)
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "no reliable lock probe")


@test("deploy: missing/digest-failed/partial science refuses before any change; a changed or incomplete after-proof refuses completion and every re-run HOLDS")
def t_deploy_science():
    w = stage("promoted"); os.remove(os.path.join(w.J, "analyze.py")); s0 = w.ctl_state()
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "science input missing or unreadable: analyze.py"); need(w.ctl_state() == s0, "changed")
    w = stage("promoted"); write(os.path.join(w.bin, "sha.fail"), "simulate.py"); s0 = w.ctl_state()
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "science digest command failed"); need(w.ctl_state() == s0, "changed")
    w = stage("promoted"); write(os.path.join(w.bin, "sha.partial"), "row19_slice.py"); s0 = w.ctl_state()
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "incomplete or malformed"); need(w.ctl_state() == s0, "changed")
    for hook, msg in (('echo "# drift" >> "%s/analyze.py"', "science bytes changed"), ('rm -f "%s/simulate.py"', "after-proof is incomplete")):
        w = stage("promoted"); write(os.path.join(w.CR, ".git/hooks/post-commit"), "#!/bin/bash\n" + hook % w.J + "\n", 0o755)
        rc, out = w.script("deploy_v18.sh"); refused(rc, out, msg); need("DEPLOY OK" not in out, "deploy reported OK", out)
        names = os.listdir(w.PROOF)
        need("intent" in names and "DONE" not in names and [n for n in names if n.startswith("after_failed.")], "proof evidence %s" % names)
        jd = tree_digest(os.path.join(w.L, "rsc_screen")); pdd = tree_digest(w.PROOF)
        for _ in range(2):
            rc, out = w.script("deploy_v18.sh")
            refused(rc, out, "already holds exactly these v18 bytes", "DEPLOY HELD", "after-proof is unresolved"); need("DEPLOY OK" not in out, "a re-run reported OK", out)
        need(tree_digest(os.path.join(w.L, "rsc_screen")) == jd and tree_digest(w.PROOF) == pdd, "a re-run changed the science or the proof")


@test("deploy retry: a copy failure resumes on the pre-mutation proof; a mid-payload failure / a refused commit leave a dirty clone every re-run refuses")
def t_deploy_retry():
    w = stage("promoted"); s0 = w.ctl_state()
    w.fake("cp", '#!/bin/bash\nfor a in "$@"; do case $a in *.v18tmp) echo "cp: simulated failure" >&2; exit 1;; esac; done\nexec /bin/cp "$@"\n')
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "copy of"); need(w.ctl_state() == s0, "the controller clone changed", out)
    need(sorted(os.listdir(w.PROOF)) == ["intent", "science_before.sha256"], "the pre-mutation proof is not exactly intent + manifest")
    os.remove(os.path.join(w.bin, "cp"))
    rc, out = w.script("deploy_v18.sh"); need(rc == 0 and "reusing the pre-mutation proof" in out and "DEPLOY OK" in out, "resume", out)
    w = stage("promoted")
    w.fake("cp", '#!/bin/bash\nfor a in "$@"; do case $a in *row19_screen_status.py.v18tmp) echo "cp: simulated failure" >&2; exit 1;; esac; done\nexec /bin/cp "$@"\n')
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "copy of chpc/row19_screen_status.py failed")
    need(ctl_dirty(w) != [], "a mid-payload failure did not leave the clone dirty")
    os.remove(os.path.join(w.bin, "cp"))
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "uncommitted changes or untracked files"); need("DEPLOY OK" not in out, "OK on a dirty clone", out)
    w = stage("promoted"); write(os.path.join(w.CR, ".git/hooks/pre-commit"), "#!/bin/bash\nexit 1\n", 0o755); h0 = w.ctl_state()[0]
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "git commit failed"); need(w.ctl_state()[0] == h0 and ctl_dirty(w) != [], "commit failure state")
    os.remove(os.path.join(w.CR, ".git/hooks/pre-commit"))
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "uncommitted changes")


@test("deploy retry: a deployed clone without its proof, with science changed after DONE, or a tampered preserved manifest HOLDS; DONE + equal science is OK")
def t_deploy_proof_binding():
    w = stage("deployed"); rc, out = w.script("deploy_v18.sh"); need(rc == 0 and "current manifest equals the preserved" in out and "DEPLOY OK" in out, "re-run", out)
    w = stage("deployed"); unlock_tree(w.PROOF); shutil.rmtree(w.PROOF)
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "DEPLOY HELD", "no deploy proof")
    w = stage("deployed"); open(os.path.join(w.J, "analyze.py"), "a").write("# later drift\n")
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "DEPLOY HELD", "differ from the preserved pre-mutation manifest")
    w = stage("deployed"); os.chmod(w.PROOF, 0o755); p = os.path.join(w.PROOF, "science_before.sha256"); os.chmod(p, 0o644)
    open(p, "a").write("0" * 64 + "  extra\n"); os.chmod(p, 0o444)
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "DEPLOY HELD", "not the one its intent record certifies")
    w = stage("deployed"); os.chmod(w.PROOF, 0o755); p = os.path.join(w.PROOF, "DONE"); os.chmod(p, 0o644)
    write(p, open(p).read().replace("science_after ", "science_after 0"), 0o444)
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "DEPLOY HELD", "does not bind this payload")
    d = open(os.path.join(stage("deployed").PROOF, "DONE")).read()
    m = dict(l.split(" ", 1) for l in d.strip().split("\n"))
    need(m["science_after"] == m["science_before"] and len(m["science_after"]) == 64 and m["schema"] == "row19-screen-v18-deploy-proof-1", "DONE: %s" % m)


@test("deploy: payload that does not compile/parse under t1py, or a v18 path already in the controller, refuses before any change")
def t_deploy_payload_checks():
    w = stage("promoted")
    t1 = open(os.path.join(w.L, "t1py")).read().replace('  -c) exec python3 "$@";;',
                                                         '  -c) case "${2:-}" in *"compile(open(sys.argv[1]"*) echo "SyntaxError (simulated)" >&2; exit 1;; esac; exec python3 "$@";;')
    write(os.path.join(w.L, "t1py"), t1, 0o755); s0 = w.ctl_state()
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "does not compile under"); need(w.ctl_state() == s0 and not os.path.lexists(w.PROOF), "changed")
    w = stage("promoted"); write(os.path.join(w.C, "chpc/row19_screen_nodefail.py"), "# early\n")
    sh("git", "-C", w.CR, "add", "--", T1_REL + "/chpc/row19_screen_nodefail.py"); gitc(w.CR, "commit", "-q", "-m", "x"); s0 = w.ctl_state()
    rc, out = w.script("deploy_v18.sh"); refused(rc, out); need(w.ctl_state() == s0 and not os.path.lexists(w.PROOF), "changed")


# ================================================================================================ containment
@test("containment: controller clone, archive dir, gate member, ec2 dir or the node document pointing outside refuse; nothing written outside")
def t_escape():
    w = stage("fresh"); tgt = os.path.join(w.outside, "rsc_screen_ctl"); os.rename(w.CR, tgt); os.symlink(tgt, w.CR); before = tree_digest(w.outside)
    rc, out = w.script("preflight_v18.sh"); refused(rc, out, "not its own physical path")
    rc, out = w.script("archive_v17.sh"); refused(rc, out, "not its own physical path")
    need(tree_digest(w.outside) == before and not os.path.exists(w.MA), "wrote outside or built the Mac half")
    w = stage("fresh"); a = os.path.join(w.L, "archive_screen"); tgt = os.path.join(w.outside, "archive_screen"); shutil.move(a, tgt); os.symlink(tgt, a)
    before = tree_digest(tgt)
    rc, out = w.script("archive_v17.sh"); refused(rc, out, "not its own physical path"); need(tree_digest(tgt) == before, "wrote into the outside archive dir")
    w = stage("fresh"); write(os.path.join(w.outside, "x.json"), "{}\n"); os.symlink(os.path.join(w.outside, "x.json"), os.path.join(w.G, "x.json"))
    rc, out = w.script("archive_v17.sh"); refused(rc, out, "symlink")
    w = stage("fresh"); q = os.path.join(w.outside, "nodefail.json"); shutil.move(w.NODE_EV, q); os.symlink(q, w.NODE_EV)
    rc, out = w.script("preflight_v18.sh"); refused(rc, out, "not its own physical path")
    w = stage("deployed"); e = os.path.join(w.GS, "ec2"); tgt = os.path.join(w.outside, "ec2"); shutil.copytree(e, tgt); shutil.rmtree(e); os.symlink(tgt, e)
    before = tree_digest(w.outside)
    rc, out = w.script("lengau.sh", "rollover_pilot_v18.sh"); refused(rc, out, "not its own physical path")
    need(tree_digest(w.outside) == before and os.path.exists(os.path.join(w.G, "review_refit.json")), "the rollover ran or wrote outside")


@test("containment: a committed nested chpc / reviews redirect refuses deploy and adopt before any copy; a temporary-sibling symlink is never followed")
def t_nested():
    for rel, msg in (("chpc", "payload 2"), ("reviews", "payload 1")):
        w = stage("promoted"); tgt = os.path.join(w.outside, "ctl_" + rel); commit_redirect(w, rel, tgt)
        before = tree_digest(w.outside); s0 = w.ctl_state()
        rc, out = w.script("deploy_v18.sh"); refused(rc, out, "not its own physical path")
        need(tree_digest(w.outside) == before and w.ctl_state() == s0 and not os.path.lexists(w.PROOF), "deploy wrote before refusing (%s)" % rel)
    w = stage("qualified"); qsha = sha(os.path.join(w.G, "qualified_refit_job1.json")); rec = pilot_record(w, qsha)
    tgt = os.path.join(w.outside, "ctl_reviews"); commit_redirect(w, "reviews", tgt); before = tree_digest(w.outside)
    rc, out = w.script("lengau.sh", "adopt_pilot18.sh", "--file", rec); refused(rc, out, "not its own physical path")
    need(tree_digest(w.outside) == before and not os.path.lexists(os.path.join(w.G, "review_refit.json")), "adopt wrote before refusing")
    w = stage("promoted"); victim = os.path.join(w.outside, "victim.py"); write(victim, "outside bytes\n")
    write(os.path.join(w.CR, ".git", "info", "exclude"), "*.v18tmp\n")
    os.symlink(victim, os.path.join(w.C, "chpc/row19_screen_admit.py.v18tmp")); s0 = w.ctl_state()
    rc, out = w.script("deploy_v18.sh"); refused(rc, out, "temporary sibling")
    need(open(victim).read() == "outside bytes\n" and w.ctl_state() == s0 and not os.path.lexists(w.PROOF), "the sibling was followed")


@test("containment: a controller alias resolving inside the scientific clone refuses every body; scientific bytes unchanged")
def t_ctl_alias_science():
    def alias_whole(w):
        os.rename(w.CR, os.path.join(w.L, "ctl_moved_aside")); os.symlink(os.path.join(w.L, "rsc_screen"), w.CR)
    for name, runs in (("fresh", [("preflight_v18.sh",), ("archive_v17.sh",)]), ("promoted", [("deploy_v18.sh",)]),
                       ("receipted", [("lengau.sh", "rollover_pilot_v18.sh")])):
        w = stage(name); alias_whole(w)
        jd = tree_digest(os.path.join(w.L, "rsc_screen")); gd = tree_digest(w.G)
        for r in runs:
            rc, out = w.script(*r); refused(rc, out, "not its own physical path")
        need(tree_digest(os.path.join(w.L, "rsc_screen")) == jd and tree_digest(w.G) == gd, "the science clone or gate changed (%s)" % name)


@test("controller git: a gitfile or symlinked .git refuses (own-root semantics on the restricted git); a corrupt index refuses")
def t_ctl_git():
    for kind in ("gitfile", "symlink"):
        w = stage("fresh"); gd = os.path.join(w.CR, ".git"); moved = os.path.join(w.outside, "ctl.git"); shutil.move(gd, moved)
        write(gd, "gitdir: %s\n" % moved) if kind == "gitfile" else os.symlink(moved, gd)
        rc, out = w.script("preflight_v18.sh"); refused(rc, out, "git directory is"); need("Unknown option" not in out, "used -C", out)
    w = stage("fresh"); write(os.path.join(w.CR, ".git/index"), b"garbage, not an index")
    rc, out = w.script("preflight_v18.sh"); refused(rc, out, "git status failed")


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
        rc, out = w.script("preflight_v18.sh"); refused(rc, out); need("lengau preflight OK" not in out, "preflight passed with %s" % name, out)
        rc, out = w.script("archive_v17.sh"); refused(rc, out); need(not os.path.exists(w.A), "archived with %s" % name)


# ================================================================================================ step 5: receipts
@test("receipts: an alarm, a v17 generation, no activation_e2, no or another job-54 node disposition, a second node disposition, a failed status or bank receipt refuse; a retry passes")
def t_receipts():
    for mode, msg in (("alarm", "alarms"), ("gen17", "not v18"), ("noe2", "not exactly e1 and e2"), ("nonode", "refit job 54 is not a node-failure"),
                      ("otherev", "refit job 54 is not a node-failure"), ("othernode", "other jobs carry node dispositions"),
                      ("fail", "not fresh, production and alarm-free")):
        w = stage("deployed"); stub_receipts(w); write(os.path.join(w.t1, "chpc/stub_status.mode"), mode)
        rc, out = w.script("receipts_v18.sh"); refused(rc, out, msg); need("V18 RECEIPTS OK" not in out, "OK with " + mode, out)
    w = stage("deployed"); stub_receipts(w); write(os.path.join(w.bin, "stub_bank.mode"), "2")
    rc, out = w.script("receipts_v18.sh"); refused(rc, out, "bank receipt exited 2")
    w = stage("deployed"); stub_receipts(w)
    rc, out = w.script("receipt_check_v18.py", "--since", str(time.time() + 3600)); refused(rc, out, "no refit watch receipt published")
    w = stage("deployed"); stub_receipts(w); write(os.path.join(w.t1, "chpc/stub_status.mode"), "alarm")
    rc, out = w.script("receipts_v18.sh"); refused(rc, out, "alarms")
    os.remove(os.path.join(w.t1, "chpc/stub_status.mode"))
    rc, out = w.script("receipts_v18.sh"); need(rc == 0 and "V18 RECEIPTS OK" in out, "receipts retry", out)


@test("receipts: the Lengau check refuses before the deploy (controller still v17), without DONE, with epoch 2 broken or the node document changed - no receipt published")
def t_receipts_lengau():
    R = lambda w: os.path.join(w.t1, "chpc/results/row19_screen/receipts")
    w = stage("promoted"); stub_receipts(w)
    rc, out = w.script("receipts_v18.sh"); refused(rc, out, "deployed controls (v18)")
    need(not os.path.isdir(R(w)) or not [f for f in os.listdir(R(w)) if f.startswith("watch_refit_")], "a receipt was published")
    w = stage("deployed"); stub_receipts(w); unlock_tree(w.PROOF); os.remove(os.path.join(w.PROOF, "DONE"))
    rc, out = w.script("receipts_v18.sh"); refused(rc, out, "DONE")
    w = stage("deployed"); stub_receipts(w); os.remove(w.ACT2)
    rc, out = w.script("receipts_v18.sh"); refused(rc, out, "epoch-2 activation proof")
    w = stage("deployed"); stub_receipts(w); open(w.NODE_EV, "a").write(" ")
    rc, out = w.script("receipts_v18.sh"); refused(rc, out, "730ea262")


# ================================================================================================ step 6: pilot rollover, package, adoption
@test("rollover: before the deploy refuses; a changed active review or a corrupted archive refuses (nothing moves); a gate member symlink refuses; an interrupted chmod completes on re-run")
def t_rollover():
    w = stage("promoted"); rc, out = w.script("lengau.sh", "rollover_pilot_v18.sh"); refused(rc, out, "deployed controls (v18)")
    need(os.path.exists(os.path.join(w.G, "review_refit.json")), "moved before the deploy")
    w = stage("receipted"); open(os.path.join(w.G, "review_refit.json"), "a").write(" ")
    rc, out = w.script("lengau.sh", "rollover_pilot_v18.sh"); refused(rc, out, "MISMATCH"); need(os.path.exists(os.path.join(w.G, "review_refit.json")), "moved")
    w = stage("receipted"); p = os.path.join(w.A, "ctl/HEAD.txt"); os.chmod(p, 0o644); write(p, "0" * 40 + "\n"); os.chmod(p, 0o444)
    rc, out = w.script("lengau.sh", "rollover_pilot_v18.sh"); refused(rc, out, "does not verify as complete"); need(os.path.exists(os.path.join(w.G, "review_refit.json")), "moved")
    for member in ("review_refit.json", "qualified_refit_job1.json"):
        w = stage("receipted"); src = os.path.join(w.G, member); copy = os.path.join(w.outside, member)
        write(copy, open(src, "rb").read(), 0o644); os.remove(src); os.symlink(copy, src); before = tree_digest(w.outside)
        rc, out = w.script("lengau.sh", "rollover_pilot_v18.sh"); refused(rc, out, "not its own physical path")
        need(tree_digest(w.outside) == before and os.stat(copy).st_mode & 0o777 == 0o644 and os.path.islink(src), "something moved or changed")
    w = stage("receipted"); ra = sha(os.path.join(w.G, "review_refit.json"))
    shutil.move(os.path.join(w.G, "review_refit.json"), w.RETIRED)   # moved, chmod lost
    rc, out = w.script("lengau.sh", "rollover_pilot_v18.sh"); need(rc == 0 and "completed the interrupted retirement" in out and not os.access(w.RETIRED, os.W_OK) and sha(w.RETIRED) == ra, "chmod completion", out)
    w = stage("rolled"); write(os.path.join(w.G, "review_refit.json"), "{}\n")
    rc, out = w.script("lengau.sh", "rollover_pilot_v18.sh"); refused(rc, out, "both the retired v17 review")


@test("package: a qualification not regenerated (8fdbf48e / 2c7a7ef1) / of generation 17 / naming a missing receipt refuses; staging left and a tampered package refuse")
def t_package():
    w = stage("rolled"); rc, out = w.script("package_qual_v18.py"); refused(rc, out, "still the v17 8fdbf48e")
    w = stage("rolled"); write(os.path.join(w.t1, QUAL_MAC), frozen("chpc/results/archive/row19_screen_v16_before_v17/qualified_refit_job1.json"))
    rc, out = w.script("package_qual_v18.py"); refused(rc, out, "still the v16 2c7a7ef1")
    w = stage("qualified"); R = os.path.join(w.t1, "chpc/results/row19_screen/receipts")
    vp = [f for f in os.listdir(R) if f.startswith("verify_refit_20261021")][0]
    write(os.path.join(R, vp), json.dumps({"generation": {"version": 17, "latest": 17, "controls_problem": "", "controls_sha256": V17_CONTROLS}}))
    rc, out = w.script("package_qual_v18.py"); refused(rc, out, "not v18")
    w = stage("qualified"); os.remove(os.path.join(w.t1, "chpc/results/row19_screen/receipts/watch_refit_20261020T033232Z.json"))
    rc, out = w.script("package_qual_v18.py"); refused(rc, out, "watch_refit_20261020T033232Z.json")
    w = stage("qualified"); qsha = sha(os.path.join(w.t1, QUAL_MAC))
    stg = os.path.join(w.t1, "chpc/qualification_v18_%s.staging.77" % qsha[:8]); os.makedirs(stg)
    rc, out = w.script("package_qual_v18.py"); refused(rc, out, "interrupted build"); need(os.path.isdir(stg), "the staging evidence was removed")
    w = stage("qualified"); rc, out = w.script("package_qual_v18.py"); need(rc == 0, "package", out)
    qsha = sha(os.path.join(w.t1, QUAL_MAC)); pd = os.path.join(w.t1, "chpc/qualification_v18_" + qsha[:8])
    os.chmod(pd, 0o755); p = os.path.join(pd, "watch_refit_20261020T033232Z.json"); os.chmod(p, 0o644); open(p, "a").write(" ")
    rc, out = w.script("package_qual_v18.py"); refused(rc, out, "does not verify")


@test("adopt: an active review, the gate still at 8fdbf48e, a record without THIS qualification's literal, an evidence path, an adopter refusal - each refuses; a LARGE record (> 4 KB) is accepted (the pipefail fix) and a large record without the literal refuses")
def t_adopt():
    w = stage("receipted"); rec = pilot_record(w, "f" * 64)
    rc, out = w.script("lengau.sh", "adopt_pilot18.sh", "--file", rec); refused(rc, out, "an active review exists")
    w = stage("rolled"); rec = pilot_record(w, "f" * 64)
    rc, out = w.script("lengau.sh", "adopt_pilot18.sh", "--file", rec); refused(rc, out, "still the v17 8fdbf48e")
    w = stage("qualified"); rec = pilot_record(w, V17_QUAL); h0 = w.ctl_state()[0]
    rc, out = w.script("lengau.sh", "adopt_pilot18.sh", "--file", rec); refused(rc, out, "does not carry the literal for the gate qualification")
    need(w.ctl_state()[0] == h0, "the wrong record was committed in the controller clone")
    w = stage("qualified"); qsha = sha(os.path.join(w.G, "qualified_refit_job1.json"))
    p = os.path.join(w.t1, "reviews/2026-10-11_d1d2_f3_codex_record.md"); write(p, "ADOPT row19-screen-pilot role=refit qualification=%s max_job=100\n" % qsha)
    rc, out = w.script("lengau.sh", "adopt_pilot18.sh", "--file", "reviews/2026-10-11_d1d2_f3_codex_record.md"); refused(rc, out, "pinned untracked evidence")
    w = stage("qualified"); qsha = sha(os.path.join(w.G, "qualified_refit_job1.json")); rec = pilot_record(w, qsha); write(os.path.join(w.L, "adopt.mode"), "refuse")
    rc, out = w.script("lengau.sh", "adopt_pilot18.sh", "--file", rec); refused(rc, out, "the supported adopter refused")
    need(not os.path.lexists(os.path.join(w.G, "review_refit.json")), "a gate review was written on refusal")
    os.remove(os.path.join(w.L, "adopt.mode"))
    rc, out = w.script("lengau.sh", "adopt_pilot18.sh", "--file", rec); need(rc == 0 and "adopt_pilot18 complete" in out, "adopt retry after the refusal (record already committed)", out)
    w = stage("qualified"); qsha = sha(os.path.join(w.G, "qualified_refit_job1.json")); rec = pilot_record(w, qsha, name="reviews/test_pilot_v18_large.md", filler=400)
    need(os.path.getsize(os.path.join(w.t1, rec)) > 16384, "the large record is not large")
    for _ in range(3):
        if os.path.lexists(os.path.join(w.G, "review_refit.json")):
            os.remove(os.path.join(w.G, "review_refit.json"))
        rc, out = w.script("lengau.sh", "adopt_pilot18.sh", "--file", rec); need(rc == 0 and "adopt_pilot18 complete" in out, "a large record with the literal at the top (pipefail fix)", out)
    w = stage("qualified"); rec = pilot_record(w, "x", name="reviews/test_pilot_v18_large_nolit.md", filler=400, literal=False)
    rc, out = w.script("lengau.sh", "adopt_pilot18.sh", "--file", rec); refused(rc, out, "does not carry the literal")


def main(argv):
    global BASE
    keep = "--keep" in argv; sel = argv[argv.index("-k") + 1] if "-k" in argv else None
    BASE = tempfile.mkdtemp(prefix="mig_v18_test_")
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
