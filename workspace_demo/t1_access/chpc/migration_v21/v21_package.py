"""migration_v21 (Mac): the exact v21 package and the Mac-side gates every step uses (the migration_v20 v20_package.py,
re-pointed). Read only; writes nothing.

    python3 chpc/migration_v21/v21_package.py preflight        step 1, the Mac half (the live tree is the adopted v20)
    python3 chpc/migration_v21/v21_package.py check-promoted   steps 4-8: the COMPLETE, committed, verified v21 promotion
    python3 chpc/migration_v21/v21_package.py commit-paths     step 3: the exact explicit paths of the promotion commit
    python3 chpc/migration_v21/v21_package.py payload          step 4: the deploy payload, in copy order (one per line)
    python3 chpc/migration_v21/v21_package.py compare          step 4: every file compared Mac vs controller after the deploy
    python3 chpc/migration_v21/v21_package.py drain            the Mac drain observation alone

THE PACKAGE (the migration_v19/v20 identity rule, kept): the controls literal binds the controls bytes only, so PACKAGE pins the
candidate controls, promotion map, builder, promoter, the two promoted controller sources (the programme gate REVISION 5, the
admission REVISION 21) and the retained node evidence (an archive member). THE RECORD: v21 carries the owner's ruling of 26 Oct
2026 (R052: CSCI1913 first, then HEAL1922, side by side); no science byte moves, so its adoption record is an OPERATOR record (the
owner's 20 Oct 2026 rule) - a committed reviews/<name>.md carrying the exact line
    ADOPT row19-screen-controls sha256=<V21_CONTROLS> version=21
The single line tagged @record names that committed record and its SHA-256; until it does every gate refuses.
Run from workspace_demo/t1_access. Exit 0 = OK, 3 = refused (the reasons are printed)."""
import fcntl, hashlib, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, "..", ".."))
CAND = os.path.join(T1, "chpc", "candidate_v21_heal")
REC, REC_SHA = None, None   # @record: the committed operator record with the v21 ADOPT literal, and its sha256
V21_CONTROLS = "72a5d2606c387433715befcc097e723c18bf4ba124ca5558878d550ea10ee8fb"
LITERAL = "ADOPT row19-screen-controls sha256=%s version=21" % V21_CONTROLS
PACKAGE = {   # the package identities (chpc/candidate_v21_heal/DESIGN_v21.md; the candidate commit)
    "chpc/candidate_v21_heal/row19_screen_controls.json": V21_CONTROLS,
    "chpc/candidate_v21_heal/v21_promotion_map.json": "41a7bc5e18ae2904d15d8f747da2647488ec2ad90cffd3956aec0c01c94a546a",
    "chpc/candidate_v21_heal/build_v21.py": "10fd311a0a8f9d83cf0d32b4b5634c2cff284611558258055a072c5589f88d15",
    "chpc/candidate_v21_heal/promote_v21.py": "9d43120654d3b28f7997fc69f790d7f72df5c6f5f1fd945f58f06e549facfe5d",
    "chpc/candidate_v21_heal/programme_gate.py": "041bc123530c92625bd2433e514a345bf6c18459b52a6d9c39d4c64eaa8453b0",
    "chpc/candidate_v21_heal/row19_screen_admit.py": "1caf69331d27e1c880e62f6d4fe5a29b0e9455548542111fb5ce6b2ffbc45cf6",
    "chpc/candidate_v18_nodefail/evidence_row19_screen_refit_54.nodefail.json": "730ea262c65c9e70d9bc39d572d65bd4ea70ac77c52fb3a4e4a1ed9238164b1f",
}
V20 = {"chpc/row19_screen_controls.json": "4e64982befebb3106019f99aa58bb012487f944c7ca59edb906c688e493adf6c",
       "chpc/row19_screen_controls_adoption.json": "1ef162deb000bdc8a423d2c74d606c5db481a92fa2484d8cef75944687232894"}
V20_QUAL = "2e99d6159623b787568d538493f44f2ef5fc97ec0b340ae9e3c48672cca00959"
QUAL_PATH = "chpc/results/row19_screen/receipts/qualified_refit_job1.json"
PILOT_REC = ("reviews/2026-10-26_pilot_v20_max200_operator_record.md", "34c2b22b62fd018fc92114a669e1807bc7ba39c63a85dcdc1223fcbbdef99a51")
E3 = ("chpc/row19_partition_e3.json", "ca87fb1da163df10e720e5778542d2bcc5c78f30fc08b6a1cc61d671773f0e6a")
BUDGET = "chpc/row19_screen_budget.json"
ADOPT = "chpc/row19_screen_controls_adoption.json"
CTL = "chpc/row19_screen_controls.json"
LS_FILE = "chpc/results/archive/row19_screen_v20_before_v21.lengau_SHA256SUMS.txt"   # archive_v20.sh: the Lengau archive's SHA256SUMS
# Mac processes that must not run during the cutover: the refill and settle scripts, the slot watcher and every controller (the
# EC2 route is closed since v20; its authority is not a running process any more)
MAC_PAT = re.compile(r"refill(_r1|_b1)?\.sh|settle_many\.sh|slot_watch\.sh|row19_screen_(admit|status|verify)\.py|row22_bank_(submit|status)\.py|"
                     r"row19_ec2_|row19_partition\.py|programme_gate\.py|row19_ledger\.py|ec2_sync\.py|prod_launch\.py|promote_v21\.py")


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
    """build_v21 and promote_v21 from candidate_v21_heal (their identities are checked first: never import other bytes)."""
    bad = [p for p, h in PACKAGE.items() if p.endswith(".py") and sha_or_none(p) != h]
    if bad:
        raise SystemExit("REFUSED: the v21 package code is not the pinned bytes: %s" % bad)
    sys.path.insert(0, CAND)
    import build_v21 as B, promote_v21 as PV      # noqa: E402
    return B, PV


def record_problems():
    if REC is None or REC_SHA is None:
        return ["the v21 controls adoption record is not pinned (the v21_package.py record pin is PENDING): no committed operator "
                "record with the ADOPT literal for the exact package is pinned; nothing may be promoted or deployed"]
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
    return ["a refill, settle, slot-watch or controller process runs on the Mac: %s" % h for h in hits]


def staging_left(B):
    d = os.path.join(T1, os.path.dirname(B.ARCH))
    pre = "." + os.path.basename(B.ARCH) + ".staging"
    return sorted(n for n in os.listdir(d) if n.startswith(pre)) if os.path.isdir(d) else []


def run_promote(*args):
    r = subprocess.run([sys.executable, os.path.join(CAND, "promote_v21.py"), *args], cwd=T1, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def preflight():
    why = package_problems() + drain_problems()
    if why:
        return why                                # never import the package modules unless their bytes are the pinned ones
    B, PV = modules()
    for rel, h in V20.items():
        if sha_or_none(rel) != h or not committed(rel):
            why.append("%s is not the adopted, committed v20 bytes %s" % (rel, h[:8]))
    st = PV.state()
    other = {k: v for k, v in st.items() if v != "v20"}
    if other:
        why.append("promoted paths are not all at their v20 bytes: %s" % other)
    for r in PV.rows():
        if not committed(r["promoted"]):
            why.append("%s is not git-tracked and unmodified" % r["promoted"])
    if sha_or_none(E3[0]) != E3[1] or not committed(E3[0]):
        why.append("%s is not the committed e3 ca87fb1d" % E3[0])
    if sha_or_none(QUAL_PATH) != V20_QUAL:
        why.append("the Mac %s is not the adopted v20 pilot qualification 2e99d615" % QUAL_PATH)
    if sha_or_none(PILOT_REC[0]) != PILOT_REC[1] or not committed(PILOT_REC[0]):
        why.append("%s is not the committed v20 pilot record 34c2b22b (max 200)" % PILOT_REC[0])
    if not committed(BUDGET):
        why.append("%s is not git-tracked and unmodified" % BUDGET)
    if os.path.lexists(os.path.join(T1, B.ARCH)) or os.path.lexists(os.path.join(T1, LS_FILE)):
        why.append("the Mac archive %s (or its Lengau SHA256SUMS copy) already exists (migration started before?)" % B.ARCH)
    if staging_left(B):
        why.append("an interrupted Mac archive build left %s; inspect it by hand" % staging_left(B))
    rc, out = run_promote("--check")
    if rc != 0:
        why.append("promote_v21.py --check exited %d: %s" % (rc, out[-600:]))
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
        why.append("promote_v21.py --check-promoted --review %s exited %d: %s" % (REC, rc, out[-600:]))
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
    """The 5 files deploy_v21.sh carries, in copy order: the controls adoption (operator) record, the map rows in map order (the
    programme gate, the admission), then the controls and LAST the adoption record (the promotion's own order)."""
    if B is None:
        B, PV = modules()
    return [REC] + [r["promoted"] for r in PV.rows()] + [CTL, ADOPT]


def compare_list(B=None, PV=None):
    """Every file compared Mac vs controller clone after the deploy: the v21 pins, the promoted rows, the controls and adoption,
    the e3 partition the latest entry pins and the operator adoption record."""
    if B is None:
        B, PV = modules()
    v = json.load(open(os.path.join(T1, CTL)))["versions"][-1]
    return sorted(set(v["files"]) | {r["promoted"] for r in PV.rows()} | {CTL, ADOPT, v["partition"]["path"], REC})


def main(argv):
    cmd = argv[0] if len(argv) == 1 else None
    if cmd == "preflight":
        why = preflight()
        if why:
            print("PREFLIGHT REFUSED (Mac):"); [print("  -", w) for w in why]; return 3
        print("mac preflight OK: the live tree is the adopted v20 (controls 4e64982b, adoption 1ef162de), every promoted path at its v20 "
              "bytes, the pinned package (controls, map, builder, promoter, programme gate, admission, node evidence 730ea262) and the "
              "operator adoption record committed with the literal in HEAD, promote_v21.py --check OK, Mac qualification 2e99d615, e3 "
              "committed, no Mac archive, Mac drain observed"); return 0
    if cmd == "check-promoted":
        why = check_promoted()
        if why:
            print("REFUSED (Mac): the v21 promotion is not complete, committed and verified:"); [print("  -", w) for w in why]; return 3
        print("mac v21 promotion OK: complete, committed, archive verifying, package identities exact"); return 0
    if cmd == "drain":
        why = drain_problems()
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
