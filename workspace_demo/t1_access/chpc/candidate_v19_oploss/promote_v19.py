"""Controls v19 CANDIDATE (NOT adopted): the v18 -> v19 promotion check and (after the operator's adoption record) promotion, on the
chpc/candidate_v18_nodefail/promote_v18.py base-first pattern. Design: chpc/candidate_v19_oploss/DESIGN_v19.md; migration:
chpc/migration_v19/RUNBOOK.md. The real promotion has NOT been run.

    python3 chpc/candidate_v19_oploss/promote_v19.py --check                                (from workspace_demo/t1_access)
    python3 chpc/candidate_v19_oploss/promote_v19.py --check-promoted --review reviews/<record>.md
    python3 chpc/candidate_v19_oploss/promote_v19.py --dry-run --review reviews/<record>.md
    python3 chpc/candidate_v19_oploss/promote_v19.py --review reviews/<record>.md          (the real promotion)

Every command FIRST resolves and authenticates the immutable v18 BASE (build_v19.resolve_base: the live controls and adoption
while both are exactly v18 452b82df / 3e1fe9a1; otherwise ONLY the completely verified Mac archive
chpc/results/archive/row19_screen_v18_before_v19/) and builds the expected v19 from it, BEFORE any candidate, state, record or
write handling. So:
  --check           (no record, no write) passes before, during and after promotion: the candidate controls and promotion map
                    are build_v19's deterministic bytes from that base; versions 1-18 and every top-level key equal the base;
                    the v19 entry pins exactly the v18 file set, every changed pin equals its map row (this folder's bytes) and
                    every other pin, the partition (e2 48cea639), sub_envelopes and qualification_S equal v18's; the map lists
                    exactly the build's rows; every source, the builder and this promoter are git-tracked and unmodified. It then
                    reports each promoted path as v18 / v19 / other.
  --check-promoted  passes exactly for the COMPLETE verified promotion (every path v19, the exact version-19 adoption record,
                    record and archive verifying) and refuses an interrupted one with "not complete".
  the promotion     additionally requires the adoption record (an OPERATOR record under the owner's 20 Oct 2026 rule, or any
                    reviews/<name>.md) git-tracked, unmodified, with the literal
                    `ADOPT row19-screen-controls sha256=<candidate controls sha256> version=19` in HEAD, and the archive verifying
                    (build_v19.archive_problems); every promoted path must hold its v18 (previous) bytes or already its v19 bytes,
                    and the adoption record the v18 record 3e1fe9a1 or exactly the version-19 record. It copies, in map order, the
                    status view, the admission and LAST the controls (atomic replaces), then writes the version-19 adoption
                    record. A finished promotion re-verifies and writes nothing; one interrupted after the controls copy resumes
                    and writes only the adoption record; anything else refuses.
Nothing is bypassed; a missing, partial or corrupt archive refuses wherever the base must come from it."""
import argparse, hashlib, json, os, re, shutil, subprocess, sys

CAND = os.path.dirname(os.path.abspath(__file__))
CHPC = os.path.dirname(CAND)
T1 = os.path.dirname(CHPC)
CREL = "chpc/candidate_v19_oploss/"
sys.path.insert(0, CAND)
import build_v19 as B  # noqa: E402  (same folder: the map, the base, the archive and the deterministic build)

CTL = "chpc/row19_screen_controls.json"
ADOPT = "chpc/row19_screen_controls_adoption.json"
V18_CTL, V18_ADOPT = B.ADOPTED_CTL[1], B.ADOPTED_ADOPTION[1]
ARCH = B.ARCH
archive_problems = B.archive_problems
PREVIOUS = {dst: prev for dst, _src, prev in B.MAP}


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
    return [dict(promoted=dst, source=src, sha256=sha(src), group="pin") for dst, src, _prev in B.MAP]


def candidate_problems(require_git=True):
    """Every check of the CANDIDATE (no record). [] when it verifies. The authenticated v18 base is resolved FIRST."""
    base, why = B.resolve_base()
    if why:
        return why
    why = list(B.input_problems(base))
    if why:
        return why
    ctl_b, pm_b = B.build(base)
    for rel, b in ((CREL + "row19_screen_controls.json", ctl_b), (CREL + "v19_promotion_map.json", pm_b)):
        if sha_or_none(rel) != hashlib.sha256(b).hexdigest():
            why.append(f"{rel} is not build_v19.py's deterministic bytes from the {base['source']} v18 base")
    c = json.loads(ctl_b); pm = json.loads(pm_b); base_doc = json.loads(base["controls"])
    if c["versions"][:-1] != base_doc["versions"] or {k: v for k, v in c.items() if k != "versions"} != {k: v for k, v in base_doc.items() if k != "versions"}:
        why.append("candidate versions 1-18 / programme / deployment / history_manifest are not the adopted v18 controls'")
    v19, v18 = c["versions"][-1], c["versions"][-2]
    if v19.get("version") != 19 or v18.get("version") != 18:
        why.append("the candidate's last two entries are not versions 18 and 19")
    if sorted(v19["files"]) != sorted(v18["files"]):
        why.append("the v19 entry pins another file set than v18")
    pins = {r["promoted"]: r["sha256"] for r in rows()}
    for f, h in v19["files"].items():
        want = pins.get(f, v18["files"].get(f))
        if h != want:
            why.append(f"v19 pin {f} is not {want[:8] if want else None}")
    for k in ("partition", "sub_envelopes", "qualification_S"):
        if v19.get(k) != v18.get(k):
            why.append(f"v19 {k} differs from v18")
    if sorted(v19) != sorted(v18):
        why.append("the v19 entry carries other keys than v18's")
    if v18.get("partition") != {"path": "chpc/row19_partition_e2.json", "sha256": "48cea639e823abbf39238e3dd7c075f63ba9eca8467009348510e2943ed56fa6"}:
        why.append("v18 does not pin the e2 partition 48cea639")
    if [r["promoted"] for r in pm["rows"][:-1]] != [r["promoted"] for r in rows()] or pm["rows"][-1]["sha256"] != hashlib.sha256(ctl_b).hexdigest() \
            or pm["rows"][-1]["promoted"] != CTL:
        why.append("the promotion map does not list the build's rows and the candidate controls")
    if require_git:
        for rel in sorted({r["source"] for r in rows()} | {CREL + "row19_screen_controls.json", CREL + "v19_promotion_map.json",
                                                          CREL + "build_v19.py", CREL + "promote_v19.py", B.NODE_EVIDENCE[0]}):
            if not git_ok(rel):
                why.append(f"{rel} is not git-tracked and unmodified")
    return why


def state():
    """{promoted path: 'v18' | 'v19' | 'other'} (v18 = its previous bytes)."""
    st = {}
    for r in rows() + [dict(promoted=CTL, sha256=sha(CREL + "row19_screen_controls.json"))]:
        h = sha_or_none(r["promoted"])
        if h is None:
            st[r["promoted"]] = "other"; continue
        prev = V18_CTL if r["promoted"] == CTL else PREVIOUS[r["promoted"]]
        st[r["promoted"]] = "v19" if h == r["sha256"] else ("v18" if h == prev else "other")
    return st


def literal():
    return f"ADOPT row19-screen-controls sha256={sha(CREL + 'row19_screen_controls.json')} version=19"


def review_problems(rec):
    if not rec:
        return ["--review reviews/<record>.md is required (the committed operator adoption record with the v19 ADOPT literal)"]
    if not re.match(r"^reviews/[A-Za-z0-9._-]+\.md$", rec) or not os.path.isfile(os.path.join(T1, rec)):
        return [f"{rec} is not an existing reviews/<name>.md record"]
    lit = literal()
    if lit not in [l.strip() for l in open(os.path.join(T1, rec)).read().splitlines()]:
        return [f"{rec} does not carry the literal `{lit}`"]
    r = git("show", f"HEAD:./{rec}")
    if not git_ok(rec) or r.returncode != 0 or lit not in [l.strip() for l in r.stdout.splitlines()]:
        return [f"{rec} is not git-tracked and unmodified with the literal in HEAD"]
    return []


def adoption_v19_bytes(rec):
    """The exact version-19 adoption record (deterministic: commits from git history, no time or host)."""
    ccommit = git("log", "-1", "--format=%h", "--", CREL + "row19_screen_controls.json").stdout.strip()
    rcommit = git("log", "-1", "--format=%h", "--", rec).stdout.strip()
    h = {r["promoted"]: r["sha256"][:8] for r in rows()}
    ad = {"schema": "row19-screen-controls-adoption-1", "controls_path": CTL, "controls_sha256": sha(CREL + "row19_screen_controls.json"),
          "version": 19, "controls_commit": ccommit,
          "review_record": {"path": rec, "sha256": sha(rec), "commit": rcommit, "adopt_line": literal()},
          "by": "R052 Entropy SI (Claude), operator record under the owner's 20 Oct 2026 rule",
          "previous": {"version": 18, "controls_sha256": V18_CTL, "adoption_sha256": V18_ADOPT,
                       "archived": "Lengau archive_screen/v18_before_v19, Mac " + ARCH + "/"},
          "scope": "controls v18 -> v19, the OPERATIONAL-LOSS disposition (chpc/candidate_v19_oploss/DESIGN_v19.md): "
                   f"chpc/row19_screen_status.py ({h['chpc/row19_screen_status.py']}) and chpc/row19_screen_admit.py "
                   f"({h['chpc/row19_screen_admit.py']}) = v18 + REVISION 19; every other controller byte, the v18 node-failure rule, "
                   "the e2 partition 48cea639 (epoch 2 stays active) and the funding unchanged. An operational-loss job never "
                   "qualifies and never counts toward the crash rule. Fresh v19 receipts and a regenerated pilot qualification with a "
                   "NEW pilot literal precede any further refit admission"}
    return (json.dumps(ad, indent=1) + "\n").encode()


def adoption_state(rec):
    p = os.path.join(T1, ADOPT)
    if not os.path.isfile(p) or os.path.islink(p):
        return "other"
    b = open(p, "rb").read()
    if hashlib.sha256(b).hexdigest() == V18_ADOPT:
        return "v18"
    return "v19" if rec and b == adoption_v19_bytes(rec) else "other"


def order():
    """The map order (the status view, the admission), then the controls LAST."""
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
        counts = {k: sum(1 for s in st.values() if s == k) for k in ("v18", "v19", "other")}
        print(f"CANDIDATE OK: controls v19 {sha(CREL + 'row19_screen_controls.json')}, {len(rows())} map rows + the controls, every pin = its "
              f"source bytes, versions 1-18 = adopted v18 (the authenticated {B.resolve_base()[0]['source']} v18 base), partition e2 48cea639 unchanged")
        print(f"live tree: {counts} " + ", ".join(f"{k}={s}" for k, s in st.items() if s != "v18"))
        print(f"the adoption literal this candidate needs: {literal()}")
        return 0
    why = review_problems(a.review) + archive_problems()
    if why:
        print("REFUSED:"); [print("  -", w) for w in why]; return 3
    ad = adoption_state(a.review)
    if "other" in st.values():
        print("REFUSED: promoted paths are neither their v18 nor their v19 bytes:", ", ".join(k for k, s in st.items() if s == "other")); return 3
    if ad == "other":
        print("REFUSED: the adoption record is neither the adopted v18 record 3e1fe9a1 nor the exact version-19 record"); return 3
    if ad == "v19" and st[CTL] != "v19":
        print("REFUSED: a version-19 adoption is written over non-v19 controls"); return 3
    if all(s == "v19" for s in st.values()) and ad == "v19":
        print(f"already promoted, verified (candidate, record, archive {ARCH}/, the exact version-19 adoption {sha(ADOPT)[:16]}); nothing to do"); return 0
    if a.check_promoted:
        print("REFUSED: --check-promoted: the promotion is not complete:", ", ".join(f"{k}={s}" for k, s in st.items()), f"adoption={ad}"); return 3
    todo = [r for r in order() if st[r["promoted"]] != "v19"]
    if a.dry_run:
        print("DRY RUN - checks pass; would copy, in order:"); [print(f"  - {r['source']} -> {r['promoted']}") for r in todo]
        print("  - then write chpc/row19_screen_controls_adoption.json (version 19), atomically"); return 0
    for r in todo:
        dst = os.path.join(T1, r["promoted"]); os.makedirs(os.path.dirname(dst), exist_ok=True)
        tmp = dst + f".tmp.{os.getpid()}"
        shutil.copyfile(os.path.join(T1, r["source"]), tmp); os.replace(tmp, dst)
        if sha(r["promoted"]) != r["sha256"]:
            print(f"REFUSED: {r['promoted']} does not hold the pinned bytes after the copy"); return 3
    p = os.path.join(T1, ADOPT); tmp = p + f".tmp.{os.getpid()}"
    open(tmp, "wb").write(adoption_v19_bytes(a.review)); os.replace(tmp, p)
    print("promoted:", ", ".join(f"{os.path.basename(r['promoted'])} {r['sha256'][:8]}" for r in todo), "adoption", sha(ADOPT)[:16])
    return 0


if __name__ == "__main__":
    sys.exit(main())
