"""Controls v20 CANDIDATE (NOT adopted): the v19 -> v20 promotion check and (after the operator's adoption record) promotion, on the
chpc/candidate_v19_oploss/promote_v19.py base-first pattern. Design: chpc/candidate_v20_handback/DESIGN_v20.md; migration:
chpc/migration_v20/RUNBOOK.md. The real promotion has NOT been run.

    python3 chpc/candidate_v20_handback/promote_v20.py --check                              (from workspace_demo/t1_access)
    python3 chpc/candidate_v20_handback/promote_v20.py --check-promoted --review reviews/<record>.md
    python3 chpc/candidate_v20_handback/promote_v20.py --dry-run --review reviews/<record>.md
    python3 chpc/candidate_v20_handback/promote_v20.py --review reviews/<record>.md        (the real promotion)

Every command FIRST resolves and authenticates the immutable v19 BASE (build_v20.resolve_base: the live controls and adoption
while both are exactly v19 111c3107 / 2b9f3c78; otherwise ONLY the completely verified Mac archive
chpc/results/archive/row19_screen_v19_before_v20/) and builds the expected v20 from it, BEFORE any candidate, state, record or
write handling. So:
  --check           (no record, no write) passes before, during and after promotion: the candidate controls and promotion map
                    are build_v20's deterministic bytes from that base; versions 1-19 and every top-level key equal the base;
                    the v20 entry pins exactly the v19 file set, every changed pin equals its map row (this folder's bytes) and
                    every other pin, sub_envelopes and qualification_S equal v19's; the partition is exactly the e3 closing
                    declaration of this folder (v19: e2 48cea639); the map lists exactly the build's rows; every source, the
                    builder and this promoter are git-tracked and unmodified. It then reports each promoted path as
                    v19 / v20 / other.
  --check-promoted  passes exactly for the COMPLETE verified promotion (every path v20, the exact version-20 adoption record,
                    record and archive verifying) and refuses an interrupted one with "not complete".
  the promotion     additionally requires the adoption record (an OPERATOR record under the owner's 20 Oct 2026 rule, or any
                    reviews/<name>.md) git-tracked, unmodified, with the literal
                    `ADOPT row19-screen-controls sha256=<candidate controls sha256> version=20` in HEAD, and the archive verifying
                    (build_v20.archive_problems); every promoted path must hold its v19 (previous) bytes or already its v20 bytes
                    (a DATA row - a new path - must be absent or already its v20 bytes), and the adoption record the v19 record
                    2b9f3c78 or exactly the version-20 record. It copies, in map order, the partition module, the admission, the
                    e3 closing declaration, the Mac authority and LAST the controls (atomic replaces), then writes the
                    version-20 adoption record. A finished promotion re-verifies and writes nothing; one interrupted after the
                    controls copy resumes and writes only the adoption record; anything else refuses.
Nothing is bypassed; a missing, partial or corrupt archive refuses wherever the base must come from it."""
import argparse, hashlib, json, os, re, shutil, subprocess, sys

CAND = os.path.dirname(os.path.abspath(__file__))
CHPC = os.path.dirname(CAND)
T1 = os.path.dirname(CHPC)
CREL = "chpc/candidate_v20_handback/"
sys.path.insert(0, CAND)
import build_v20 as B  # noqa: E402  (same folder: the map, the base, the archive and the deterministic build)

CTL = "chpc/row19_screen_controls.json"
ADOPT = "chpc/row19_screen_controls_adoption.json"
V19_CTL, V19_ADOPT = B.ADOPTED_CTL[1], B.ADOPTED_ADOPTION[1]
ARCH = B.ARCH
archive_problems = B.archive_problems
PREVIOUS = {dst: prev for dst, _src, prev in B.MAP + B.DATA + B.MAC}     # DATA: None (a new path)


def sha(rel):
    return hashlib.sha256(open(os.path.join(T1, rel), "rb").read()).hexdigest()


def sha_or_none(rel):
    p = os.path.join(T1, rel)
    return sha(rel) if os.path.isfile(p) and not os.path.islink(p) else None


def git(*a):
    return subprocess.run(["git", "-C", T1, *a], capture_output=True, text=True)


def git_ok(rel):
    return git("ls-files", "--error-unmatch", "--", rel).returncode == 0 and git("diff", "--quiet", "HEAD", "--", rel).returncode == 0


def rows():
    return ([dict(promoted=dst, source=src, sha256=sha(src), group="pin") for dst, src, _prev in B.MAP]
            + [dict(promoted=dst, source=src, sha256=sha(src), group="data") for dst, src, _prev in B.DATA]
            + [dict(promoted=dst, source=src, sha256=sha(src), group="mac") for dst, src, _prev in B.MAC])


def candidate_problems(require_git=True):
    """Every check of the CANDIDATE (no record). [] when it verifies. The authenticated v19 base is resolved FIRST."""
    base, why = B.resolve_base()
    if why:
        return why
    why = list(B.input_problems(base))
    if why:
        return why
    ctl_b, pm_b = B.build(base)
    for rel, b in ((CREL + "row19_screen_controls.json", ctl_b), (CREL + "v20_promotion_map.json", pm_b)):
        if sha_or_none(rel) != hashlib.sha256(b).hexdigest():
            why.append(f"{rel} is not build_v20.py's deterministic bytes from the {base['source']} v19 base")
    c = json.loads(ctl_b); pm = json.loads(pm_b); base_doc = json.loads(base["controls"])
    if c["versions"][:-1] != base_doc["versions"] or {k: v for k, v in c.items() if k != "versions"} != {k: v for k, v in base_doc.items() if k != "versions"}:
        why.append("candidate versions 1-19 / programme / deployment / history_manifest are not the adopted v19 controls'")
    v20, v19 = c["versions"][-1], c["versions"][-2]
    if v20.get("version") != 20 or v19.get("version") != 19:
        why.append("the candidate's last two entries are not versions 19 and 20")
    if sorted(v20["files"]) != sorted(v19["files"]):
        why.append("the v20 entry pins another file set than v19")
    pins = {r["promoted"]: r["sha256"] for r in rows() if r["group"] == "pin"}
    for f, h in v20["files"].items():
        want = pins.get(f, v19["files"].get(f))
        if h != want:
            why.append(f"v20 pin {f} is not {want[:8] if want else None}")
    for k in ("sub_envelopes", "qualification_S"):
        if v20.get(k) != v19.get(k):
            why.append(f"v20 {k} differs from v19")
    if v20.get("partition") != {"path": B.PARTITION_REL, "sha256": sha(B.DATA[0][1])}:
        why.append("v20 does not pin exactly this folder's e3 closing declaration at chpc/row19_partition_e3.json")
    if sorted(v20) != sorted(v19):
        why.append("the v20 entry carries other keys than v19's")
    if v19.get("partition") != B.V19_PARTITION:
        why.append("v19 does not pin the e2 partition 48cea639")
    if [r["promoted"] for r in pm["rows"][:-1]] != [r["promoted"] for r in rows()] or pm["rows"][-1]["sha256"] != hashlib.sha256(ctl_b).hexdigest() \
            or pm["rows"][-1]["promoted"] != CTL:
        why.append("the promotion map does not list the build's rows and the candidate controls")
    if require_git:
        for rel in sorted({r["source"] for r in rows()} | {CREL + "row19_screen_controls.json", CREL + "v20_promotion_map.json",
                                                          CREL + "build_v20.py", CREL + "promote_v20.py", B.NODE_EVIDENCE[0]}):
            if not git_ok(rel):
                why.append(f"{rel} is not git-tracked and unmodified")
    return why


def state():
    """{promoted path: 'v19' | 'v20' | 'other'} (v19 = its previous bytes)."""
    st = {}
    for r in rows() + [dict(promoted=CTL, sha256=sha(CREL + "row19_screen_controls.json"))]:
        h = sha_or_none(r["promoted"])
        prev = V19_CTL if r["promoted"] == CTL else PREVIOUS[r["promoted"]]
        if h is None:                         # a NEW data path (previous None) is absent in the v19 state; a pin never is
            st[r["promoted"]] = "v19" if prev is None and not os.path.lexists(os.path.join(T1, r["promoted"])) else "other"; continue
        st[r["promoted"]] = "v20" if h == r["sha256"] else ("v19" if prev is not None and h == prev else "other")
    return st


def literal():
    return f"ADOPT row19-screen-controls sha256={sha(CREL + 'row19_screen_controls.json')} version=20"


def review_problems(rec):
    if not rec:
        return ["--review reviews/<record>.md is required (the committed operator adoption record with the v20 ADOPT literal)"]
    if not re.match(r"^reviews/[A-Za-z0-9._-]+\.md$", rec) or not os.path.isfile(os.path.join(T1, rec)):
        return [f"{rec} is not an existing reviews/<name>.md record"]
    lit = literal()
    if lit not in [l.strip() for l in open(os.path.join(T1, rec)).read().splitlines()]:
        return [f"{rec} does not carry the literal `{lit}`"]
    r = git("show", f"HEAD:./{rec}")
    if not git_ok(rec) or r.returncode != 0 or lit not in [l.strip() for l in r.stdout.splitlines()]:
        return [f"{rec} is not git-tracked and unmodified with the literal in HEAD"]
    return []


def adoption_v20_bytes(rec):
    """The exact version-20 adoption record (deterministic: commits from git history, no time or host)."""
    ccommit = git("log", "-1", "--format=%h", "--", CREL + "row19_screen_controls.json").stdout.strip()
    rcommit = git("log", "-1", "--format=%h", "--", rec).stdout.strip()
    h = {r["promoted"]: r["sha256"][:8] for r in rows()}
    ad = {"schema": "row19-screen-controls-adoption-1", "controls_path": CTL, "controls_sha256": sha(CREL + "row19_screen_controls.json"),
          "version": 20, "controls_commit": ccommit,
          "review_record": {"path": rec, "sha256": sha(rec), "commit": rcommit, "adopt_line": literal()},
          "by": "R052 Entropy SI (Claude), operator record under the owner's 20 Oct 2026 rule",
          "previous": {"version": 19, "controls_sha256": V19_CTL, "adoption_sha256": V19_ADOPT,
                       "archived": "Lengau archive_screen/v19_before_v20, Mac " + ARCH + "/"},
          "scope": "controls v19 -> v20, the EC2 CLOSE (route A, owner decision 23 Oct 2026; chpc/candidate_v20_handback/DESIGN_v20.md): "
                   f"chpc/row19_partition.py ({h['chpc/row19_partition.py']}, REVISION 7: the closing schema 3) and "
                   f"chpc/row19_screen_admit.py ({h['chpc/row19_screen_admit.py']}, REVISION 20: Lengau's scope gains the hand-back), "
                   f"the closing epoch e3 chpc/row19_partition_e3.json ({h['chpc/row19_partition_e3.json']}) pinned in place of e2 "
                   f"48cea639, and the Mac authority aws_ec2/prod_authority.py ({h['aws_ec2/prod_authority.py']}, REVISION 10: the "
                   "terminal close); every other controller byte, the crash rule, the rescue route, sub_envelopes, the ledger cap and "
                   "the funding unchanged. Lengau refit admission holds until the e3 activation; fresh v20 receipts and a regenerated "
                   "pilot qualification with a NEW pilot literal precede any further refit admission"}
    return (json.dumps(ad, indent=1) + "\n").encode()


def adoption_state(rec):
    p = os.path.join(T1, ADOPT)
    if not os.path.isfile(p) or os.path.islink(p):
        return "other"
    b = open(p, "rb").read()
    if hashlib.sha256(b).hexdigest() == V19_ADOPT:
        return "v19"
    return "v20" if rec and b == adoption_v20_bytes(rec) else "other"


def order():
    """The map order (the pins: partition module, admission; the e3 declaration; the Mac authority), then the controls LAST."""
    return rows() + [dict(promoted=CTL, source=CREL + "row19_screen_controls.json", sha256=sha(CREL + "row19_screen_controls.json"), group="ctl")]


def main(argv=None):
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true"); g.add_argument("--check-promoted", action="store_true"); g.add_argument("--dry-run", action="store_true")
    ap.add_argument("--review", default=None); a = ap.parse_args(argv)
    why = candidate_problems()
    if why:
        print("REFUSED: the candidate does not verify:"); [print("  -", w) for w in why]; return 3
    st = state()
    if a.check:
        counts = {k: sum(1 for s in st.values() if s == k) for k in ("v19", "v20", "other")}
        print(f"CANDIDATE OK: controls v20 {sha(CREL + 'row19_screen_controls.json')}, {len(rows())} map rows + the controls, every pin = its "
              f"source bytes, versions 1-19 = adopted v19 (the authenticated {B.resolve_base()[0]['source']} v19 base), partition e2 48cea639 -> "
              f"e3 {sha(B.DATA[0][1])[:8]}")
        print(f"live tree: {counts} " + ", ".join(f"{k}={s}" for k, s in st.items() if s != "v19"))
        print(f"the adoption literal this candidate needs: {literal()}")
        return 0
    why = review_problems(a.review) + archive_problems()
    if why:
        print("REFUSED:"); [print("  -", w) for w in why]; return 3
    ad = adoption_state(a.review)
    if "other" in st.values():
        print("REFUSED: promoted paths are neither their v19 nor their v20 bytes:", ", ".join(k for k, s in st.items() if s == "other")); return 3
    if ad == "other":
        print("REFUSED: the adoption record is neither the adopted v19 record 2b9f3c78 nor the exact version-20 record"); return 3
    if ad == "v20" and st[CTL] != "v20":
        print("REFUSED: a version-20 adoption is written over non-v20 controls"); return 3
    if all(s == "v20" for s in st.values()) and ad == "v20":
        print(f"already promoted, verified (candidate, record, archive {ARCH}/, the exact version-20 adoption {sha(ADOPT)[:16]}); nothing to do"); return 0
    if a.check_promoted:
        print("REFUSED: --check-promoted: the promotion is not complete:", ", ".join(f"{k}={s}" for k, s in st.items()), f"adoption={ad}"); return 3
    todo = [r for r in order() if st[r["promoted"]] != "v20"]
    if a.dry_run:
        print("DRY RUN - checks pass; would copy, in order:"); [print(f"  - {r['source']} -> {r['promoted']}") for r in todo]
        print("  - then write chpc/row19_screen_controls_adoption.json (version 20), atomically"); return 0
    for r in todo:
        dst = os.path.join(T1, r["promoted"]); os.makedirs(os.path.dirname(dst), exist_ok=True)
        tmp = dst + f".tmp.{os.getpid()}"
        shutil.copyfile(os.path.join(T1, r["source"]), tmp); os.replace(tmp, dst)
        if sha(r["promoted"]) != r["sha256"]:
            print(f"REFUSED: {r['promoted']} does not hold the pinned bytes after the copy"); return 3
    p = os.path.join(T1, ADOPT); tmp = p + f".tmp.{os.getpid()}"
    open(tmp, "wb").write(adoption_v20_bytes(a.review)); os.replace(tmp, p)
    print("promoted:", ", ".join(f"{os.path.basename(r['promoted'])} {r['sha256'][:8]}" for r in todo), "adoption", sha(ADOPT)[:16])
    return 0


if __name__ == "__main__":
    sys.exit(main())
