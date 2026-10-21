"""migration_v19 (Mac): the exact v19 package and the Mac-side gates every step uses (the migration_v18 v18_package.py,
re-pointed). Read only; writes nothing.

    python3 chpc/migration_v19/v19_package.py preflight        step 1, the Mac half (the live tree is the adopted v18)
    python3 chpc/migration_v19/v19_package.py check-promoted   steps 4-6: the COMPLETE, committed, verified v19 promotion
    python3 chpc/migration_v19/v19_package.py commit-paths     step 3: the exact explicit paths of the promotion commit
    python3 chpc/migration_v19/v19_package.py payload          step 4: the deploy payload, in copy order (one per line)
    python3 chpc/migration_v19/v19_package.py compare          step 4: every file compared Mac vs controller after the deploy
    python3 chpc/migration_v19/v19_package.py drain            the Mac drain observation alone

THE PACKAGE (the migration_v18 identity rule, kept: "verify exact new package/map/builder/review identities"): the controls
literal binds the controls bytes only, so PACKAGE below pins the candidate controls, promotion map, builder, promoter, the two
promoted sources and the retained node evidence (an archive member); every map source is also checked by promote_v19.py
--check. THE RECORD: v19 is an owner-approved operational change (R052 lean T1 plan item 2, 20 Oct 2026; no Codex review), so
its adoption record is an OPERATOR record - any committed reviews/<name>.md carrying the exact line
    ADOPT row19-screen-controls sha256=4d868856905f914858ca224ec0dcb902792646f437fa4a9ddaa75d1b6d729a7d version=19
(the migration_v18 rule: the literal in HEAD and the pinned bytes; who wrote it is not checked). It does NOT exist yet, so the
single line tagged @record below is PENDING (None, None) and every gate refuses until it names that committed record and its
SHA-256 - a one-line change the operator makes after committing the record (RUNBOOK step 0).
Run from workspace_demo/t1_access. Exit 0 = OK, 3 = refused (the reasons are printed)."""
import fcntl, hashlib, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, "..", ".."))
CAND = os.path.join(T1, "chpc", "candidate_v19_oploss")
REC, REC_SHA = None, None   # @record: the committed operator record with the v19 ADOPT literal, and its sha256 (PENDING)
V19_CONTROLS = "4d868856905f914858ca224ec0dcb902792646f437fa4a9ddaa75d1b6d729a7d"
LITERAL = "ADOPT row19-screen-controls sha256=%s version=19" % V19_CONTROLS
PACKAGE = {   # the package identities (chpc/candidate_v19_oploss/DESIGN_v19.md; the candidate commit)
    "chpc/candidate_v19_oploss/row19_screen_controls.json": V19_CONTROLS,
    "chpc/candidate_v19_oploss/v19_promotion_map.json": "b3a1778c5bec64dac32ec62684cc23b85f45a13bf1789c0b370494a0ebef78b5",
    "chpc/candidate_v19_oploss/build_v19.py": "c04a17eb119e618673da03f4d9e4cdebb264fdc8fd41c04e60774cb391324759",
    "chpc/candidate_v19_oploss/promote_v19.py": "b32e161755f692c412ebae6c80321e3f8f08f7dfdbff5dea239439df334d98b5",
    "chpc/candidate_v19_oploss/row19_screen_status.py": "258d43293b15f1ae9457cd323f2a4a7b71af79e83695dff51601037991a7cb45",
    "chpc/candidate_v19_oploss/row19_screen_admit.py": "27e066c72ed43919a92083fcf3f035cbee232c2137c2e97832f0e41b1113f9df",
    "chpc/candidate_v18_nodefail/evidence_row19_screen_refit_54.nodefail.json": "730ea262c65c9e70d9bc39d572d65bd4ea70ac77c52fb3a4e4a1ed9238164b1f",
}
V18 = {"chpc/row19_screen_controls.json": "452b82df0d7184cbe7c1390d5d43787501990d380c4ca275d1db70adc131ba2b",
       "chpc/row19_screen_controls_adoption.json": "3e1fe9a1ddd10a6ed160f5f1f9fc3f4f4de707efa3e90259104e7e5670ae1616"}
V18_QUAL = "530df9a208eb1578282ef564708447fd3b32c5fa1366f388f51059ebcfd70839"
QUAL_PATH = "chpc/results/row19_screen/receipts/qualified_refit_job1.json"
PILOT_REC = ("reviews/2026-10-20_pilot_v18_operator_record.md", "67f2b4383a1b25d7e6921f0c8252514a6fe797e37419af3ddfbb8116753fae87")
E2 = ("chpc/row19_partition_e2.json", "48cea639e823abbf39238e3dd7c075f63ba9eca8467009348510e2943ed56fa6")
BUDGET = "chpc/row19_screen_budget.json"
ADOPT = "chpc/row19_screen_controls_adoption.json"
CTL = "chpc/row19_screen_controls.json"
AUTH_LOCK = "aws_ec2/runs/.authority.lock"
LS_FILE = "chpc/results/archive/row19_screen_v18_before_v19.lengau_SHA256SUMS.txt"   # archive_v18.sh: the Lengau archive's SHA256SUMS
# Mac processes that must not run during the cutover: the refill scripts and slot watcher, every controller, the EC2 authority
# (ec2_sync / prod_authority / launch / permit) and a live EC2 reaper (a live attempt; it is never stopped, the cutover waits)
MAC_PAT = re.compile(r"refill_(r1|b1)\.sh|slot_watch\.sh|row19_screen_(admit|status|verify)\.py|row22_bank_(submit|status)\.py|"
                     r"row19_ec2_|row19_partition\.py|programme_gate\.py|row19_ledger\.py|ec2_sync\.py|prod_authority\.py|"
                     r"prod_launch\.py|qual_permit\.py|bench_reaper\.py|promote_v19\.py")


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
    """build_v19 and promote_v19 from candidate_v19_oploss (their identities are checked first: never import other bytes)."""
    bad = [p for p, h in PACKAGE.items() if p.endswith(".py") and sha_or_none(p) != h]
    if bad:
        raise SystemExit("REFUSED: the v19 package code is not the pinned bytes: %s" % bad)
    sys.path.insert(0, CAND)
    import build_v19 as B, promote_v19 as PV      # noqa: E402
    return B, PV


def record_problems():
    if REC is None or REC_SHA is None:
        return ["the v19 controls adoption record is not pinned (the v19_package.py record pin is PENDING): no committed operator "
                "record with the ADOPT literal for the exact package 4d868856 is pinned; nothing may be promoted or deployed"]
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
    r = subprocess.run([sys.executable, os.path.join(CAND, "promote_v19.py"), *args], cwd=T1, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def preflight():
    why = package_problems() + drain_problems() + auth_lock_problems()
    if why:
        return why                                # never import the package modules unless their bytes are the pinned ones
    B, PV = modules()
    for rel, h in V18.items():
        if sha_or_none(rel) != h or not committed(rel):
            why.append("%s is not the adopted, committed v18 bytes %s" % (rel, h[:8]))
    st = PV.state()
    other = {k: v for k, v in st.items() if v != "v18"}
    if other:
        why.append("promoted paths are not all at their v18 bytes: %s" % other)
    for r in PV.rows():
        prev = PV.PREVIOUS[r["promoted"]]
        if prev is not None and not committed(r["promoted"]):
            why.append("%s is not git-tracked and unmodified" % r["promoted"])
        if prev is None and os.path.lexists(os.path.join(T1, r["promoted"])):
            why.append("%s already exists (a v19 path)" % r["promoted"])
    if sha_or_none(E2[0]) != E2[1] or not committed(E2[0]):
        why.append("%s is not the committed e2 48cea639" % E2[0])
    if sha_or_none(QUAL_PATH) != V18_QUAL:
        why.append("the Mac %s is not the adopted v18 pilot qualification 530df9a2" % QUAL_PATH)
    if sha_or_none(PILOT_REC[0]) != PILOT_REC[1] or not committed(PILOT_REC[0]):
        why.append("%s is not the committed v18 pilot record 67f2b438" % PILOT_REC[0])
    if not committed(BUDGET):
        why.append("%s is not git-tracked and unmodified" % BUDGET)
    if os.path.lexists(os.path.join(T1, B.ARCH)) or os.path.lexists(os.path.join(T1, LS_FILE)):
        why.append("the Mac archive %s (or its Lengau SHA256SUMS copy) already exists (migration started before?)" % B.ARCH)
    if staging_left(B):
        why.append("an interrupted Mac archive build left %s; inspect it by hand" % staging_left(B))
    rc, out = run_promote("--check")
    if rc != 0:
        why.append("promote_v19.py --check exited %d: %s" % (rc, out[-600:]))
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
        why.append("promote_v19.py --check-promoted --review %s exited %d: %s" % (REC, rc, out[-600:]))
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
    """The 5 files deploy_v19.sh carries, in copy order: the controls adoption (operator) record, the map rows in map order (the
    status view, the admission), then the controls and LAST the adoption record (the promotion's own order)."""
    if B is None:
        B, PV = modules()
    return [REC] + [r["promoted"] for r in PV.rows()] + [CTL, ADOPT]


def compare_list(B=None, PV=None):
    """Every file compared Mac vs controller clone after the deploy: the 19 v19 pins, the controls and adoption, the e2
    partition and the operator adoption record."""
    if B is None:
        B, PV = modules()
    v = json.load(open(os.path.join(T1, CTL)))["versions"][-1]
    return sorted(set(v["files"]) | {CTL, ADOPT, v["partition"]["path"], REC})


def main(argv):
    cmd = argv[0] if len(argv) == 1 else None
    if cmd == "preflight":
        why = preflight()
        if why:
            print("PREFLIGHT REFUSED (Mac):"); [print("  -", w) for w in why]; return 3
        print("mac preflight OK: the live tree is the adopted v18 (controls 452b82df, adoption 3e1fe9a1), every promoted path at its v18 "
              "bytes, the pinned package (controls 4d868856, map b3a1778c, builder, promoter, sources, node evidence 730ea262) "
              "and the operator adoption record committed with the literal in HEAD, promote_v19.py --check OK, Mac qualification 530df9a2, "
              "no Mac archive, Mac drain observed, EC2 authority lock free"); return 0
    if cmd == "check-promoted":
        why = check_promoted()
        if why:
            print("REFUSED (Mac): the v19 promotion is not complete, committed and verified:"); [print("  -", w) for w in why]; return 3
        print("mac v19 promotion OK: complete, committed, archive verifying, package identities exact"); return 0
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
