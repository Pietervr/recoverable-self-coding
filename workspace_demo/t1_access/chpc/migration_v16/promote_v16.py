"""Migration v15 -> v16, step 3 (Mac): promote the exact reviewed v16 controller bytes (controls, admission, status and the NEW
designated-coordinates declaration) into chpc/ and write the version-16 adoption record. Lineage (Codex record
reviews/2026-10-17_v16_p80_codex_review.md section A, RSC f6896e1, literal ADOPT for controls 01976b6a version 16): v16 = adopted
v15 828d3b69 with chpc/row19_screen_admit.py and chpc/row19_screen_status.py changed and chpc/row19_screen_designated.json added
(REVISION 16: S x 0..79, replicate-complete order, crash rule, first-job-alone scale-up gate, disabled rescue). No v9 replay: the
epoch-1 activation, bench finish and pilot fit are NOT repeated.

    python3 chpc/migration_v16/promote_v16.py [--dry-run | --check]          (from workspace_demo/t1_access)

Refuses unless: candidate_v16 controls = 01976b6a with latest entry version 16 pinning partition e1 8d1de408; versions 1-15 are
byte-identical to the adopted controls; the record is a315d7d2, git-tracked, unmodified and holds the literal ADOPT line in HEAD;
the candidate files are git-tracked and unmodified; every file the v16 entry pins equals its pin (admission, status and
declaration from candidate_v16/); every other pin equals v15's and the file set is v15's plus the declaration; the Mac archive
chpc/results/archive/row19_screen_v15_before_v16/ written by archive_v15.sh holds EXACTLY its six named files (the v15 controls,
adoption, admission, status, the budget phases row19_screen_budget.json and the pilot qualification 3c605514) plus SHA256SUMS
and its COMPLETE certificate, every digest verifying (mac_archive.py), and candidate versions 1-15 equal the ARCHIVED v15
controls. These checks run on EVERY invocation, before any state is reported.
Then (not with --dry-run): copy the declaration, admission, status and LAST the controls into chpc/, and write
chpc/row19_screen_controls_adoption.json for version 16 (atomically). Idempotent: every promoted file must be either its v15 or
its v16 bytes and the adoption record either the v15 record or the EXACT version-16 record this script writes; a fully
promoted tree reports "already promoted" only after the full authority and archive validation, and an interrupted promotion
resumes; anything else refuses. --check is that full validation as a no-write gate: exit 0 only for a complete, verified
promotion (deploy_v16.sh requires it). Commit the result with explicit paths; deploy with deploy_v16.sh."""
import argparse, hashlib, json, os, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mac_archive  # noqa: E402  (the same folder: the Mac archive's exact inventory and certificate)

T1 = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CAND = "chpc/candidate_v16/"
V16 = "01976b6a92e7150a82d8397caeb88e5425e0dd051f69bb244bf3f83981e8f220"
CTL = "chpc/row19_screen_controls.json"
ADOPT = "chpc/row19_screen_controls_adoption.json"
DESIG = "chpc/row19_screen_designated.json"
CHANGED = ("chpc/row19_screen_status.py", "chpc/row19_screen_admit.py", DESIG)
PART = ("chpc/row19_partition_e1.json", "8d1de408b6ef9dc66d4736b6138536de6591f0d29ebdd6fd00a6e43307225608")
REC = ("reviews/2026-10-17_v16_p80_codex_review.md", "a315d7d2f7b91baec3b668e4dcec4c2530ab44d8c07aef597b77e28fdd3d447c", "f6896e1")
LINE = f"ADOPT row19-screen-controls sha256={V16} version=16"
V15 = {CTL: "828d3b69707cc47340c1773b97450c2c17c95679c4daf93c84021d138a4663a5",
       ADOPT: "970c29f5fc7832f9ef23d20ecf6ae40e9a8808d99ee0aad5a6e9fe109e4f8f2d",
       "chpc/row19_screen_status.py": "0effcba3977b1d7e76347a4082020633bceaf9ddeec0b05d4255aa9d7b93671b",
       "chpc/row19_screen_admit.py": "ac06e803fdb1b3fdb11652017d8d1808f4ace880b8b2bb22463c3694e646d2ac"}
QUAL = ("chpc/results/row19_screen/receipts/qualified_refit_job1.json", "3c605514fb36d6d9f67a2835adf516fa30298caa10c20411bbcbcff74c94592c")
ARCH = mac_archive.ARCH + "/"
ORDER = (DESIG, "chpc/row19_screen_admit.py", "chpc/row19_screen_status.py", CTL)      # the controls last: never v16 controls over v15 code


def sha(rel):
    return hashlib.sha256(open(os.path.join(T1, rel), "rb").read()).hexdigest()


def git_ok(rel):
    """True when rel is git-tracked and its working bytes equal HEAD."""
    run = lambda *a: subprocess.run(["git", "-C", T1, *a], capture_output=True).returncode
    return run("ls-files", "--error-unmatch", "--", rel) == 0 and run("diff", "--quiet", "HEAD", "--", rel) == 0


def in_head(rel, line):
    r = subprocess.run(["git", "-C", T1, "show", f"HEAD:./{rel}"], capture_output=True, text=True)
    return r.returncode == 0 and line in [l.strip() for l in r.stdout.splitlines()]


def problems():
    why = []
    if sha(CAND + "row19_screen_controls.json") != V16:
        why.append("candidate controls are not 01976b6a")
    c = json.load(open(os.path.join(T1, CAND, "row19_screen_controls.json"))); v = c["versions"][-1]
    live = sha(CTL)
    if c["versions"][:-1] != json.load(open(os.path.join(T1, ARCH, "row19_screen_controls.json")))["versions"]:
        why.append("candidate versions 1-15 are not the archived adopted v15 controls' versions")
    if live not in (V15[CTL], V16):
        why.append(f"{CTL} is neither adopted v15 nor v16 ({live[:8]})")
    if v.get("version") != 16 or (v.get("partition") or {}).get("sha256") != PART[1] or (v.get("partition") or {}).get("path") != PART[0]:
        why.append("the latest candidate entry is not version 16 pinning partition e1")
    if sha(PART[0]) != PART[1]:
        why.append("the partition file is not 8d1de408")
    if not os.path.exists(os.path.join(T1, REC[0])) or sha(REC[0]) != REC[1] \
            or LINE not in [l.strip() for l in open(os.path.join(T1, REC[0])).read().splitlines()]:
        why.append("the review record is not a315d7d2 with the literal ADOPT line")
    elif not git_ok(REC[0]) or not in_head(REC[0], LINE):
        why.append("the review record is not git-tracked and unmodified with the literal in HEAD")
    for f in ("row19_screen_controls.json",) + tuple(os.path.basename(x) for x in CHANGED):
        if not git_ok(CAND + f):
            why.append(f"{CAND}{f} is not git-tracked and unmodified")
    prev = c["versions"][-2]
    for f, h in sorted(v["files"].items()):
        src = CAND + os.path.basename(f) if f in CHANGED else f
        if not os.path.exists(os.path.join(T1, src)) or sha(src) != h:
            why.append(f"{src} is not the v16 pin for {f}")
        if f not in CHANGED and prev["files"].get(f) != h:
            why.append(f"{f} differs from v15 (this cutover changes only status, admission and the new declaration)")
    if sorted(v["files"]) != sorted(set(prev["files"]) | {DESIG}) or DESIG in prev["files"]:
        why.append("the v16 entry pins another file set than v15 plus the designated declaration")
    if prev.get("version") != 15 or prev["files"].get("chpc/row19_screen_admit.py") != V15["chpc/row19_screen_admit.py"] \
            or prev["files"].get("chpc/row19_screen_status.py") != V15["chpc/row19_screen_status.py"]:
        why.append("the candidate's version-15 entry does not pin the adopted v15 admission and status")
    return why, v


def archive_problem():
    return mac_archive.problem()


def state():
    """Per promoted path: 'v15', 'v16' or 'other'."""
    st = {}
    for rel in ORDER:
        p = os.path.join(T1, rel)
        h = sha(rel) if os.path.exists(p) else None
        new = sha(CAND + os.path.basename(rel))
        st[rel] = "v16" if h == new else ("v15" if (h == V15.get(rel) or (rel == DESIG and h is None)) else "other")
    return st


def adoption_v16_bytes():
    """The exact version-16 adoption record this script writes (deterministic: no time or host field)."""
    ad = {"schema": "row19-screen-controls-adoption-1", "controls_path": CTL, "controls_sha256": V16,
          "version": 16, "controls_commit": "3686a11",
          "review_record": {"path": REC[0], "sha256": REC[1], "commit": REC[2], "adopt_line": LINE},
          "by": "R052 Entropy SI (Claude)",
          "previous": {"version": 15, "controls_sha256": V15[CTL], "adoption_sha256": V15[ADOPT],
                       "archived": "Lengau archive_screen/v15_before_v16, Mac " + ARCH},
          "scope": "admission + status v15 -> v16 and the new designated-coordinates declaration (Codex f6896e1 section A; REVISION 16: "
                   "the resized screen S x 0..79 of 60 reps, replicate-complete order, Lengau scope = the 13 retained reps plus "
                   "Lengau's existing claims, the two-crash same-envelope rule with RESCUE-PENDING reporting, the disabled rescue "
                   "route, the first-new-order-job-alone scale-up gate, and the 81,000 core-h refit+S sub-envelope in the controls): "
                   "every other controller byte, the epoch-1 partition 8d1de408 and the activation unchanged; grants no job, no EC2 "
                   "permission and no cap raise (the ledger's 60,000 binds until the two-phase --raise-cap 81000); fresh whole-role v16 "
                   "receipts, an adopted review of the REGENERATED refit pilot qualification (new hash, max job 100, no new fit), ONE "
                   "first new-order job and an adopted scale-up review precede any further gated refit admission"}
    return (json.dumps(ad, indent=1) + "\n").encode()


def adoption_state():
    """'v15', 'v16' (exactly the record adoption_v16_bytes) or 'other'."""
    p = os.path.join(T1, ADOPT)
    if not os.path.isfile(p):
        return "other"
    b = open(p, "rb").read()
    return "v15" if hashlib.sha256(b).hexdigest() == V15[ADOPT] else ("v16" if b == adoption_v16_bytes() else "other")


def main():
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true"); g.add_argument("--check", action="store_true"); a = ap.parse_args()
    why = archive_problem()                   # the archive first: the version comparison below reads the archived v15 controls
    if why:
        print(f"REFUSED: {why}"); return 3
    why, v = problems()
    if why:
        print("REFUSED:"); [print("  -", w) for w in why]; return 3
    st = state(); ad = adoption_state()
    if "other" in st.values():
        print("REFUSED: promoted paths are neither their v15 nor their v16 bytes:", ", ".join(k for k, s in st.items() if s == "other")); return 3
    if ad == "other":
        print("REFUSED: the adoption record is neither the adopted v15 record 970c29f5 nor the exact version-16 record"); return 3
    if ad == "v16" and st[CTL] != "v16":
        print("REFUSED: a version-16 adoption is written over non-v16 controls"); return 3
    asum = hashlib.sha256(open(os.path.join(T1, ARCH, "SHA256SUMS"), "rb").read()).hexdigest()[:16]
    if all(s == "v16" for s in st.values()) and ad == "v16":
        print(f"already promoted, verified (authority, candidate pins, archive {ARCH} SHA256SUMS {asum} + COMPLETE, the exact "
              f"version-16 adoption {sha(ADOPT)[:16]}); nothing to do"); return 0
    if a.check:
        print("REFUSED: --check: the promotion is not complete:", ", ".join(f"{k}={s}" for k, s in st.items()), f"adoption={ad}"); return 3
    resume = any(s == "v16" for s in st.values())
    todo = [rel for rel in ORDER if st[rel] != "v16"]
    plan = [f"{'resume: ' if resume else ''}copy {', '.join(CAND + os.path.basename(r) for r in todo)} -> chpc/ (controls last)",
            "write chpc/row19_screen_controls_adoption.json (version 16, review f6896e1), atomically"]
    if a.dry_run:
        print(f"DRY RUN - checks pass (Mac archive {ARCH} verifies, SHA256SUMS {asum}); would:"); [print("  -", p) for p in plan]
        print("  pinned files:", len(v["files"])); return 0
    for rel in todo:
        dst = os.path.join(T1, rel); tmp = dst + f".tmp.{os.getpid()}"
        shutil.copyfile(os.path.join(T1, CAND, os.path.basename(rel)), tmp); os.replace(tmp, dst)
    p = os.path.join(T1, ADOPT); tmp = p + f".tmp.{os.getpid()}"
    with open(tmp, "wb") as fh:
        fh.write(adoption_v16_bytes())
    os.replace(tmp, p)
    print("promoted: controls", sha(CTL)[:16], "admit", sha("chpc/row19_screen_admit.py")[:16], "status", sha("chpc/row19_screen_status.py")[:16],
          "designated", sha(DESIG)[:16], "adoption", sha(ADOPT)[:16], "archive SHA256SUMS", asum)
    return 0


if __name__ == "__main__":
    sys.exit(main())
