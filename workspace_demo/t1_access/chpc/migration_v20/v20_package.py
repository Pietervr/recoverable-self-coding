"""migration_v20 (Mac): the exact v20 package and the Mac-side gates every step uses (the migration_v19 v19_package.py,
re-pointed). Read only; writes nothing.

    python3 chpc/migration_v20/v20_package.py preflight        step 1, the Mac half (the live tree is the adopted v19)
    python3 chpc/migration_v20/v20_package.py check-promoted   steps 4-6: the COMPLETE, committed, verified v20 promotion
    python3 chpc/migration_v20/v20_package.py commit-paths     step 3: the exact explicit paths of the promotion commit
    python3 chpc/migration_v20/v20_package.py payload          step 4: the deploy payload, in copy order (one per line)
    python3 chpc/migration_v20/v20_package.py compare          step 4: every file compared Mac vs controller after the deploy
    python3 chpc/migration_v20/v20_package.py drain            the Mac drain observation alone

THE PACKAGE (the migration_v19 identity rule, kept: "verify exact new package/map/builder/review identities"): the controls
literal binds the controls bytes only, so PACKAGE below pins the candidate controls, promotion map, builder, promoter, the two
promoted controller sources (the partition module REVISION 7, the admission REVISION 20), the e3 closing declaration (a NEW data
path), the Mac authority prod_authority.py REVISION 10 (a replaced Mac tool) and the retained node evidence (an archive member);
every map source is also checked by promote_v20.py --check. THE RECORD: v20 carries the owner's decision of 23 Oct 2026 (R052,
route A: the EC2 close); its adoption record is an OPERATOR record (the owner's 20 Oct 2026 rule; the parent session runs one
Codex review of the candidate before the migration) - any committed reviews/<name>.md carrying the exact line
    ADOPT row19-screen-controls sha256=4e64982befebb3106019f99aa58bb012487f944c7ca59edb906c688e493adf6c version=20
(the migration_v19 rule: the literal in HEAD and the pinned bytes; who wrote it is not checked). It does NOT exist yet, so the
single line tagged @record below is PENDING (None, None) and every gate refuses until it names that committed record and its
SHA-256 - a one-line change the operator makes after committing the record (RUNBOOK step 0).
Run from workspace_demo/t1_access. Exit 0 = OK, 3 = refused (the reasons are printed)."""
import fcntl, hashlib, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, "..", ".."))
CAND = os.path.join(T1, "chpc", "candidate_v20_handback")
REC, REC_SHA = None, None   # @record: the committed operator record with the v20 ADOPT literal, and its sha256
V20_CONTROLS = "4e64982befebb3106019f99aa58bb012487f944c7ca59edb906c688e493adf6c"
LITERAL = "ADOPT row19-screen-controls sha256=%s version=20" % V20_CONTROLS
PACKAGE = {   # the package identities (chpc/candidate_v20_handback/DESIGN_v20.md; the candidate commit)
    "chpc/candidate_v20_handback/row19_screen_controls.json": V20_CONTROLS,
    "chpc/candidate_v20_handback/v20_promotion_map.json": "b33359536d11527bda567e3401d5b13d93ee255fb4c39277591dce92b866b140",
    "chpc/candidate_v20_handback/build_v20.py": "6e82bb13d1e7015866eeccecc7171b0107c42e734c1b434a97f35d4133f40999",
    "chpc/candidate_v20_handback/promote_v20.py": "4dfd05575cbcea5622db6d5b81d6fe90c10c891d7a23bd57dd6e3aec6e4a9136",
    "chpc/candidate_v20_handback/row19_partition.py": "a762933779529a20d6f458dd7118105c855ea122353b1eaa168a8b033c6dc17e",
    "chpc/candidate_v20_handback/row19_screen_admit.py": "7c49bf86c6809941bc982393fb4ae095f7186e0c47665c426c27350a841b08af",
    # the closing declaration (a NEW data path, pinned by the version entry's `partition`) and the replaced Mac authority
    "chpc/candidate_v20_handback/row19_partition_e3.json": "ca87fb1da163df10e720e5778542d2bcc5c78f30fc08b6a1cc61d671773f0e6a",
    "chpc/candidate_v20_handback/aws_ec2/prod_authority.py": "20de63d2fcf6685d96b23cc3543ff72864774ca17cf4983ceabf4a52d73d71e7",
    "chpc/candidate_v18_nodefail/evidence_row19_screen_refit_54.nodefail.json": "730ea262c65c9e70d9bc39d572d65bd4ea70ac77c52fb3a4e4a1ed9238164b1f",
}
V19 = {"chpc/row19_screen_controls.json": "111c3107636f2a621cdf24e4e4c86cdba1f735204237fd1ff1bfbc3a5a0315a5",
       "chpc/row19_screen_controls_adoption.json": "2b9f3c783e1f7ce53cbdafa4a84e66315874512d7afcde6b03783c343ba2939c"}
V19_QUAL = "e123d6e5d136dfda31ac5f61dd18a2cce31ecc8dea9f1ad27be73d427cc50b02"
QUAL_PATH = "chpc/results/row19_screen/receipts/qualified_refit_job1.json"
PILOT_REC = ("reviews/2026-10-22_pilot_v19_operator_record.md", "26aa4f8dc52be9d7f67fc493bd6002ae4d3b29ca73b77ce9c30082336ff4bde6")
E2 = ("chpc/row19_partition_e2.json", "48cea639e823abbf39238e3dd7c075f63ba9eca8467009348510e2943ed56fa6")
BUDGET = "chpc/row19_screen_budget.json"
ADOPT = "chpc/row19_screen_controls_adoption.json"
CTL = "chpc/row19_screen_controls.json"
AUTH_LOCK = "aws_ec2/runs/.authority.lock"
LS_FILE = "chpc/results/archive/row19_screen_v19_before_v20.lengau_SHA256SUMS.txt"   # archive_v19.sh: the Lengau archive's SHA256SUMS
# Mac processes that must not run during the cutover: the refill scripts and slot watcher, every controller, the EC2 authority
# (ec2_sync / prod_authority / launch / permit) and a live EC2 reaper (a live attempt; it is never stopped, the cutover waits)
MAC_PAT = re.compile(r"refill_(r1|b1)\.sh|slot_watch\.sh|row19_screen_(admit|status|verify)\.py|row22_bank_(submit|status)\.py|"
                     r"row19_ec2_|row19_partition\.py|programme_gate\.py|row19_ledger\.py|ec2_sync\.py|prod_authority\.py|"
                     r"prod_launch\.py|qual_permit\.py|bench_reaper\.py|promote_v20\.py")


def sha(rel):
    with open(os.path.join(T1, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha_or_none(rel):
    p = os.path.join(T1, rel)
    return sha(rel) if os.path.isfile(p) and not os.path.islink(p) else None


def git(*a):
    return subprocess.run(["git", *a], cwd=T1, capture_output=True, text=True)


def committed(rel):
    return git("ls-files", "--error-unmatch", "--", rel).returncode == 0 and git("diff", "--quiet", "HEAD", "--", rel).returncode == 0


def modules():
    """build_v20 and promote_v20 from candidate_v20_handback (their identities are checked first: never import other bytes)."""
    bad = [p for p, h in PACKAGE.items() if p.endswith(".py") and sha_or_none(p) != h]
    if bad:
        raise SystemExit("REFUSED: the v20 package code is not the pinned bytes: %s" % bad)
    sys.path.insert(0, CAND)
    import build_v20 as B, promote_v20 as PV      # noqa: E402
    return B, PV


def record_problems():
    if REC is None or REC_SHA is None:
        return ["the v20 controls adoption record is not pinned (the v20_package.py record pin is PENDING): no committed operator "
                "record with the ADOPT literal for the exact package 4e64982b is pinned; nothing may be promoted or deployed"]
    why = []
    got = sha_or_none(REC)
    if got != REC_SHA:
        why.append("%s is %s, not the pinned record %s" % (REC, (got or "absent")[:16], REC_SHA[:16]))
    elif not committed(REC):
        why.append("%s is not git-tracked and unmodified" % REC)
    else:
        r = git("show", "HEAD:./" + REC)
        if r.returncode != 0 or LITERAL not in [l.strip() for l in r.stdout.splitlines()]:
            why.append("the committed review record does not carry the exact line in HEAD: %s" % LITERAL)
    return why


def package_problems():
    why = []
    for p, h in PACKAGE.items():
        got = sha_or_none(p)
        if got != h:
            why.append("%s is %s, not the pinned %s" % (p, (got or "absent")[:16], h[:16]))
        elif not committed(p):
            why.append("%s is not git-tracked and unmodified" % p)
    return why + record_problems()


def drain_problems():
    r = subprocess.run(["ps", "-x", "-o", "args="], capture_output=True, text=True)
    if r.returncode != 0:
        return ["the Mac process inventory failed (ps exited %d); the drain is not observed" % r.returncode]
    if not r.stdout.strip():
        return ["the Mac process inventory is empty; the drain is not observed"]
    hits = [l for l in r.stdout.splitlines() if MAC_PAT.search(l)]
    return ["a refill, slot-watch, controller, EC2-authority or EC2-reaper process runs on the Mac: %s" % h for h in hits]


def auth_lock_problems():
    """A checked non-blocking SHARED probe of the Mac EC2 authority lock (ec2_sync / prod_authority hold it exclusively)."""
    p = os.path.join(T1, AUTH_LOCK)
    if not os.path.isfile(p) or os.path.islink(p):
        return ["the Mac EC2 authority lock %s is missing; it cannot be probed" % AUTH_LOCK]
    try:
        with open(p, "rb") as fh:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError:
                return ["the Mac EC2 authority lock %s is held (an authority operation is running)" % AUTH_LOCK]
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    except OSError as e:
        return ["the Mac EC2 authority lock cannot be probed (%s)" % e]
    return []


def staging_left(B):
    d = os.path.join(T1, os.path.dirname(B.ARCH))
    pre = "." + os.path.basename(B.ARCH) + ".staging"
    return sorted(n for n in os.listdir(d) if n.startswith(pre)) if os.path.isdir(d) else []


def run_promote(*args):
    r = subprocess.run([sys.executable, os.path.join(CAND, "promote_v20.py"), *args], cwd=T1, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def preflight():
    why = package_problems() + drain_problems() + auth_lock_problems()
    if why:
        return why                                # never import the package modules unless their bytes are the pinned ones
    B, PV = modules()
    for rel, h in V19.items():
        if sha_or_none(rel) != h or not committed(rel):
            why.append("%s is not the adopted, committed v19 bytes %s" % (rel, h[:8]))
    st = PV.state()
    other = {k: v for k, v in st.items() if v != "v19"}
    if other:
        why.append("promoted paths are not all at their v19 bytes: %s" % other)
    for r in PV.rows():
        prev = PV.PREVIOUS[r["promoted"]]
        if prev is not None and not committed(r["promoted"]):
            why.append("%s is not git-tracked and unmodified" % r["promoted"])
        if prev is None and os.path.lexists(os.path.join(T1, r["promoted"])):
            why.append("%s already exists (a v20 path)" % r["promoted"])
    if sha_or_none(E2[0]) != E2[1] or not committed(E2[0]):
        why.append("%s is not the committed e2 48cea639" % E2[0])
    if sha_or_none(QUAL_PATH) != V19_QUAL:
        why.append("the Mac %s is not the adopted v19 pilot qualification e123d6e5" % QUAL_PATH)
    if sha_or_none(PILOT_REC[0]) != PILOT_REC[1] or not committed(PILOT_REC[0]):
        why.append("%s is not the committed v19 pilot record 26aa4f8d" % PILOT_REC[0])
    if not committed(BUDGET):
        why.append("%s is not git-tracked and unmodified" % BUDGET)
    if os.path.lexists(os.path.join(T1, B.ARCH)) or os.path.lexists(os.path.join(T1, LS_FILE)):
        why.append("the Mac archive %s (or its Lengau SHA256SUMS copy) already exists (migration started before?)" % B.ARCH)
    if staging_left(B):
        why.append("an interrupted Mac archive build left %s; inspect it by hand" % staging_left(B))
    rc, out = run_promote("--check")
    if rc != 0:
        why.append("promote_v20.py --check exited %d: %s" % (rc, out[-600:]))
    # REVISION (v20): the EC2 close must be ready - the Mac half of its preconditions (step 0b) holds NOW (read-only check with the
    # candidate authority; the promoted one is the same bytes)
    r = subprocess.run([sys.executable, os.path.join(CAND, "aws_ec2", "prod_authority.py"), "close-check"], cwd=T1, capture_output=True, text=True)
    if r.returncode != 0 or '"close_preconditions": "MET"' not in r.stdout:
        why.append("the EC2 close preconditions are NOT MET on the Mac (RUNBOOK step 0b: disposition qual-E2Q3/1 and qual-Q2/1, "
                   "ec2_sync, disposition-confirm, a fresh inventory): %s" % (r.stdout + r.stderr).strip()[-600:])
    return why


def check_promoted():
    why = package_problems() + drain_problems()
    if why:
        return why
    B, PV = modules()
    import mac_archive as MA                      # this folder (sys.path[0] is the script's folder)
    why += MA.problems()
    if why:
        return why
    comp = MA.verify_dir(MA.builder(), os.path.join(T1, B.ARCH))
    if sha_or_none(LS_FILE) != comp["lengau_sha256sums"]:
        why.append("%s is not the Lengau SHA256SUMS the Mac archive names (%s)" % (LS_FILE, comp["lengau_sha256sums"][:16]))
    rc, out = run_promote("--check-promoted", "--review", REC)
    if rc != 0 or "already promoted, verified" not in out:
        why.append("promote_v20.py --check-promoted --review %s exited %d: %s" % (REC, rc, out[-600:]))
    for rel in commit_paths(B, PV):
        if os.path.isdir(os.path.join(T1, rel)):
            files = sorted(os.listdir(os.path.join(T1, rel)))
            bad = [f for f in files if not committed(rel + "/" + f)]
            if bad or git("ls-files", "--", rel).stdout.split() != [rel + "/" + f for f in files]:
                why.append("the Mac archive %s is not committed exactly (uncommitted %s)" % (rel, bad))
        elif not committed(rel):
            why.append("%s is not committed (commit the promotion first; only committed bytes are deployed)" % rel)
    return why


def commit_paths(B=None, PV=None):
    if B is None:
        B, PV = modules()
    return [r["promoted"] for r in PV.rows()] + [CTL, ADOPT, B.ARCH, LS_FILE]


def payload(B=None, PV=None):
    """The 7 files deploy_v20.sh carries, in copy order: the controls adoption (operator) record, the map rows in map order (the
    partition module, the admission, the NEW e3 closing declaration, the Mac authority prod_authority.py), then the controls and
    LAST the adoption record (the promotion's own order)."""
    if B is None:
        B, PV = modules()
    return [REC] + [r["promoted"] for r in PV.rows()] + [CTL, ADOPT]


def compare_list(B=None, PV=None):
    """Every file compared Mac vs controller clone after the deploy: the 19 v20 pins, every promoted map row (incl. the e3 data
    row and the Mac authority), the controls and adoption, the e3 partition the latest entry pins, e2 (its bound predecessor) and
    the operator adoption record."""
    if B is None:
        B, PV = modules()
    v = json.load(open(os.path.join(T1, CTL)))["versions"][-1]
    return sorted(set(v["files"]) | {r["promoted"] for r in PV.rows()} | {CTL, ADOPT, v["partition"]["path"], E2[0], REC})


def main(argv):
    cmd = argv[0] if len(argv) == 1 else None
    if cmd == "preflight":
        why = preflight()
        if why:
            print("PREFLIGHT REFUSED (Mac):"); [print("  -", w) for w in why]; return 3
        print("mac preflight OK: the live tree is the adopted v19 (controls 111c3107, adoption 2b9f3c78), every promoted path at its v19 "
              "bytes, the pinned package (controls 4e64982b, map b3335953, builder, promoter, sources, e3 ca87fb1d, authority 20de63d2, node evidence 730ea262) "
              "and the operator adoption record committed with the literal in HEAD, promote_v20.py --check OK, Mac qualification e123d6e5, "
              "no Mac archive, Mac drain observed, EC2 authority lock free, the EC2 close preconditions MET (close-check)"); return 0
    if cmd == "check-promoted":
        why = check_promoted()
        if why:
            print("REFUSED (Mac): the v20 promotion is not complete, committed and verified:"); [print("  -", w) for w in why]; return 3
        print("mac v20 promotion OK: complete, committed, archive verifying, package identities exact"); return 0
    if cmd == "drain":
        why = drain_problems() + auth_lock_problems()
        if why:
            print("REFUSED (Mac):"); [print("  -", w) for w in why]; return 3
        print("mac drain observed"); return 0
    if cmd in ("commit-paths", "payload", "compare"):
        why = package_problems()
        if why:
            print("REFUSED (Mac):"); [print("  -", w) for w in why]; return 3
        lst = {"commit-paths": commit_paths, "payload": payload, "compare": compare_list}[cmd]()
        print("\n".join(lst)); return 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
