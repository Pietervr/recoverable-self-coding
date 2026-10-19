"""migration_v17 (Mac): the exact reviewed v17 package and the Mac-side gates every step uses. Read only; writes nothing.

    python3 chpc/migration_v17/v17_package.py preflight        step 1, the Mac half (the live tree is the adopted v16)
    python3 chpc/migration_v17/v17_package.py check-promoted   steps 4-8: the COMPLETE, committed, verified v17 promotion
    python3 chpc/migration_v17/v17_package.py commit-paths     step 3: the exact explicit paths of the promotion commit
    python3 chpc/migration_v17/v17_package.py payload          step 4: the deploy payload, in copy order (one per line)
    python3 chpc/migration_v17/v17_package.py compare          step 4: every file compared Mac vs controller after the deploy
    python3 chpc/migration_v17/v17_package.py drain            the Mac drain observation alone

THE PACKAGE (Codex re-review reviews/2026-10-19_e2_repair_codex_rereview.md, FAVOURABLE for RSC c26835f + 806c44c): the controls
literal binds the controls bytes only, so the review asks that "the Mac/map/builder/promoter identities as well as the controls"
be verified through the migration. PACKAGE below pins them; every source of the 20-row promotion map is pinned by the builder
(build_v17.MAP, itself pinned here) and checked by promote_v17.py --check. Nothing here edits a reviewed byte.
Run from workspace_demo/t1_access. Exit 0 = OK, 3 = refused (the reasons are printed)."""
import fcntl, hashlib, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, "..", ".."))
CAND = os.path.join(T1, "chpc", "candidate_v17")
REC = "reviews/2026-10-19_e2_repair_codex_rereview.md"
REC_SHA = "48b9cf053cbd4f73e40e3e139f84a7ab50eb6c4252e8727bf90953bc1ed88f2b"
V17_CONTROLS = "9ea4e727c5d308457a2d5901ef6565522845fb31d52c3c1c0f7dd5a51a9d83c0"
LITERAL = "ADOPT row19-screen-controls sha256=%s version=17" % V17_CONTROLS
PACKAGE = {   # the reviewed package identities (DESIGN_v17.md s.1 and s.8; Codex re-review "Scope and exact package")
    "chpc/candidate_v17/row19_screen_controls.json": V17_CONTROLS,
    "chpc/candidate_v17/v17_promotion_map.json": "6bc8bd3947c398c0200c241725ad5dbb70555a3ee0290012a274a4cf6563df74",
    "chpc/candidate_v17/build_v17.py": "f2a80f42962435fc3a6787d26d838c8b67b5e0c9fe231779890a5868cae72abb",
    "chpc/candidate_v17/promote_v17.py": "f0c320c28ef3273b1b62137606372fcab13a9fd4d68765ab826fdae22bb7b5fb",
    "chpc/candidate_v17/row19_screen_admit.py": "c3960464db74a282f20da030008fb759a0fad4e1d4d3c7133c98f3b821d6b9ed",
}
V16 = {"chpc/row19_screen_controls.json": "01976b6a92e7150a82d8397caeb88e5425e0dd051f69bb244bf3f83981e8f220",
       "chpc/row19_screen_controls_adoption.json": "523fe18adad603af23425cdd4cb41039b4a287254e36aa55ba34d933b0081411"}
V16_QUAL = "2c7a7ef1fb903cf0fa75701d2a56d216e98faf14e6638da891afd8bed0bfea44"
QUAL_PATH = "chpc/results/row19_screen/receipts/qualified_refit_job1.json"
BUDGET = "chpc/row19_screen_budget.json"
E1 = "chpc/row19_partition_e1.json"
ADOPT = "chpc/row19_screen_controls_adoption.json"
CTL = "chpc/row19_screen_controls.json"
AUTH_LOCK = "aws_ec2/runs/.authority.lock"
LS_FILE = "chpc/results/archive/row19_screen_v16_before_v17.lengau_SHA256SUMS.txt"   # archive_v16.sh: the Lengau archive's SHA256SUMS
# Mac processes that must not run during the cutover: the refill scripts and slot watcher, every controller, the EC2 authority
# (ec2_sync / prod_authority / launch / permit) and a live EC2 reaper (a live attempt; it is never stopped, the cutover waits)
MAC_PAT = re.compile(r"refill_(r1|b1)\.sh|slot_watch\.sh|row19_screen_(admit|status|verify)\.py|row22_bank_(submit|status)\.py|"
                     r"row19_ec2_|row19_partition\.py|programme_gate\.py|row19_ledger\.py|ec2_sync\.py|prod_authority\.py|"
                     r"prod_launch\.py|qual_permit\.py|bench_reaper\.py")


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
    """build_v17 and promote_v17 from candidate_v17 (their identities are checked first: never import unreviewed bytes)."""
    bad = [p for p, h in PACKAGE.items() if p.endswith(".py") and sha_or_none(p) != h]
    if bad:
        raise SystemExit("REFUSED: the reviewed v17 package code is not the reviewed bytes: %s" % bad)
    sys.path.insert(0, CAND)
    import build_v17 as B, promote_v17 as PV      # noqa: E402
    return B, PV


def package_problems():
    why = []
    for p, h in PACKAGE.items():
        got = sha_or_none(p)
        if got != h:
            why.append("%s is %s, not the reviewed %s" % (p, (got or "absent")[:16], h[:16]))
        elif not committed(p):
            why.append("%s is not git-tracked and unmodified" % p)
    got = sha_or_none(REC)
    if got != REC_SHA:
        why.append("%s is %s, not the reviewed record %s" % (REC, (got or "absent")[:16], REC_SHA[:16]))
    elif not committed(REC):
        why.append("%s is not git-tracked and unmodified" % REC)
    else:
        r = git("show", "HEAD:./" + REC)
        if r.returncode != 0 or LITERAL not in [l.strip() for l in r.stdout.splitlines()]:
            why.append("the committed review record does not carry the exact line in HEAD: %s" % LITERAL)
    return why


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


def run_promote(PV, *args):
    r = subprocess.run([sys.executable, os.path.join(CAND, "promote_v17.py"), *args], cwd=T1, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def preflight():
    why = package_problems() + drain_problems() + auth_lock_problems()
    if why:
        return why                                # never import the package modules unless their bytes are the reviewed ones
    B, PV = modules()
    for rel, h in V16.items():
        if sha_or_none(rel) != h or not committed(rel):
            why.append("%s is not the adopted, committed v16 bytes %s" % (rel, h[:8]))
    st = PV.state()
    other = {k: v for k, v in st.items() if v != "v16"}
    if other:
        why.append("promoted paths are not all at their v16 bytes (or absent when new): %s" % other)
    for r in PV.rows():
        prev = B.PREVIOUS[r["promoted"]]
        if prev is not None and not committed(r["promoted"]):
            why.append("%s is not git-tracked and unmodified" % r["promoted"])
        if prev is None and os.path.lexists(os.path.join(T1, r["promoted"])):
            why.append("%s already exists (a v17 path)" % r["promoted"])
    if sha_or_none(E1) != B.E1[1] or not committed(E1):
        why.append("%s is not the committed e1 8d1de408" % E1)
    if sha_or_none(QUAL_PATH) != V16_QUAL:
        why.append("the Mac %s is not the adopted v16 pilot qualification 2c7a7ef1" % QUAL_PATH)
    if not committed(BUDGET):
        why.append("%s is not git-tracked and unmodified" % BUDGET)
    if os.path.lexists(os.path.join(T1, B.ARCH)):
        why.append("the Mac archive %s already exists (migration started before?)" % B.ARCH)
    if staging_left(B):
        why.append("an interrupted Mac archive build left %s; inspect it by hand" % staging_left(B))
    rc, out = run_promote(PV, "--check")
    if rc != 0:
        why.append("promote_v17.py --check exited %d: %s" % (rc, out[-600:]))
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
    rc, out = run_promote(PV, "--check-promoted", "--review", REC)
    if rc != 0 or "already promoted, verified" not in out:
        why.append("promote_v17.py --check-promoted --review %s exited %d: %s" % (REC, rc, out[-600:]))
    for rel in commit_paths(B, PV):
        if os.path.isdir(os.path.join(T1, rel)):
            files = sorted(os.listdir(os.path.join(T1, rel)))
            bad = [f for f in files if not committed(rel + "/" + f)]
            if bad or git("ls-files", "--", rel).stdout.split() != [rel + "/" + f for f in files]:
                why.append("the Mac archive %s is not committed exactly (uncommitted %s)" % (rel, bad))
        elif not committed(rel):
            why.append("%s is not committed (commit the promotion first; only committed bytes are deployed)" % rel)
    if not committed(REC):
        why.append("%s is not committed" % REC)
    return why


def commit_paths(B=None, PV=None):
    if B is None:
        B, PV = modules()
    return [r["promoted"] for r in PV.rows()] + [CTL, ADOPT, B.ARCH, LS_FILE]


def payload(B=None, PV=None):
    """The 17 files deploy_v17.sh carries, in copy order: the review record, the partition and data, the helpers, the
    admission, then the controls and LAST the adoption record (DESIGN_v17.md s.6 step 4; the promotion's own order)."""
    if B is None:
        B, PV = modules()
    rows = [r for r in PV.rows() if r["group"] in B.DEPLOY_GROUPS]
    first = [r["promoted"] for g in ("part", "data", "pin") for r in rows if r["group"] == g and r["promoted"] != "chpc/row19_screen_admit.py"]
    return [REC] + first + ["chpc/row19_screen_admit.py", CTL, ADOPT]


def compare_list(B=None, PV=None):
    """Every file compared Mac vs controller clone after the deploy: the 17 v17 pins, the controls and adoption, the e2 partition
    and data, the review record and the e1 partition kept for provenance."""
    if B is None:
        B, PV = modules()
    v = json.load(open(os.path.join(T1, CTL)))["versions"][-1]
    return sorted(set(v["files"]) | {CTL, ADOPT, v["partition"]["path"], E1, REC} |
                  {r["promoted"] for r in PV.rows() if r["group"] in ("part", "data")})


def main(argv):
    cmd = argv[0] if len(argv) == 1 else None
    if cmd == "preflight":
        why = preflight()
        if why:
            print("PREFLIGHT REFUSED (Mac):"); [print("  -", w) for w in why]; return 3
        print("mac preflight OK: the live tree is the adopted v16 (controls 01976b6a, adoption 523fe18a), every promoted path at its v16 "
              "bytes or absent, the reviewed package (controls 9ea4e727, map 6bc8bd39, builder f2a80f42, promoter f0c320c2) and record "
              "48b9cf05 committed with the literal in HEAD, promote_v17.py --check OK, Mac qualification 2c7a7ef1, no Mac archive, "
              "Mac drain observed, EC2 authority lock free"); return 0
    if cmd == "check-promoted":
        why = check_promoted()
        if why:
            print("REFUSED (Mac): the v17 promotion is not complete, committed and verified:"); [print("  -", w) for w in why]; return 3
        print("mac v17 promotion OK: complete, committed, archive verifying, package identities exact"); return 0
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
