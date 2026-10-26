"""Controls v21 CANDIDATE (NOT adopted): the v20 -> v21 promotion check and (after the operator's adoption record) promotion, on the
chpc/candidate_v20_handback/promote_v20.py base-first pattern. Design: chpc/candidate_v21_heal/DESIGN_v21.md; migration:
chpc/migration_v21/RUNBOOK.md.

    python3 chpc/candidate_v21_heal/promote_v21.py --check                                  (from workspace_demo/t1_access)
    python3 chpc/candidate_v21_heal/promote_v21.py --check-promoted --review reviews/<record>.md
    python3 chpc/candidate_v21_heal/promote_v21.py --dry-run --review reviews/<record>.md
    python3 chpc/candidate_v21_heal/promote_v21.py --review reviews/<record>.md        (the real promotion)

Every command FIRST resolves and authenticates the immutable v20 BASE (build_v21.resolve_base: the live controls and adoption
while both are exactly v20 4e64982b / 1ef162de; otherwise ONLY the completely verified Mac archive
chpc/results/archive/row19_screen_v20_before_v21/) and builds the expected v21 from it, BEFORE any candidate, state, record or
write handling. So:
  --check           (no record, no write) passes before, during and after promotion: the candidate controls and promotion map
                    are build_v21's deterministic bytes from that base; versions 1-20 and every top-level key equal the base;
                    the v21 entry pins exactly the v20 file set, every changed pin equals its map row (this folder's bytes) and
                    every other pin, the partition (e3 ca87fb1d) and qualification_S equal v20's; the refit+S sub-envelope is
                    v20's with only its cap (181,000) and rule changed; the ONE new key is funding_route = build_v21.FUNDING_ROUTE;
                    the map lists exactly the build's rows; every source, the builder and this promoter are git-tracked and
                    unmodified. It then reports each promoted path as v20 / v21 / other.
  --check-promoted  passes exactly for the COMPLETE verified promotion (every path v21, the exact version-21 adoption record,
                    record and archive verifying) and refuses an interrupted one with "not complete".
  the promotion     additionally requires the adoption record (an OPERATOR record under the owner's 20 Oct 2026 rule)
                    git-tracked, unmodified, with the literal
                    `ADOPT row19-screen-controls sha256=<candidate controls sha256> version=21` in HEAD, and the archive verifying
                    (build_v21.archive_problems); every promoted path must hold its v20 (previous) bytes or already its v21 bytes,
                    and the adoption record the v20 record 1ef162de or exactly the version-21 record. It copies, in map order,
                    the programme gate, the admission and LAST the controls (atomic replaces), then writes the version-21
                    adoption record. A finished promotion re-verifies and writes nothing; one interrupted after the controls copy
                    resumes and writes only the adoption record; anything else refuses.
Nothing is bypassed; a missing, partial or corrupt archive refuses wherever the base must come from it."""
import argparse, hashlib, json, os, re, shutil, subprocess, sys

CAND = os.path.dirname(os.path.abspath(__file__))
CHPC = os.path.dirname(CAND)
T1 = os.path.dirname(CHPC)
CREL = "chpc/candidate_v21_heal/"
sys.path.insert(0, CAND)
import build_v21 as B  # noqa: E402  (same folder: the map, the base, the archive and the deterministic build)

CTL = "chpc/row19_screen_controls.json"
ADOPT = "chpc/row19_screen_controls_adoption.json"
V20_CTL, V20_ADOPT = B.ADOPTED_CTL[1], B.ADOPTED_ADOPTION[1]
ARCH = B.ARCH
archive_problems = B.archive_problems
PREVIOUS = {dst: prev for dst, _src, prev in B.MAP + B.DATA + B.MAC}     # v21: MAP only (DATA and MAC are empty)


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
    """Every check of the CANDIDATE (no record). [] when it verifies. The authenticated v20 base is resolved FIRST."""
    base, why = B.resolve_base()
    if why:
        return why
    why = list(B.input_problems(base))
    if why:
        return why
    ctl_b, pm_b = B.build(base)
    for rel, b in ((CREL + "row19_screen_controls.json", ctl_b), (CREL + "v21_promotion_map.json", pm_b)):
        if sha_or_none(rel) != hashlib.sha256(b).hexdigest():
            why.append(f"{rel} is not build_v21.py's deterministic bytes from the {base['source']} v20 base")
    c = json.loads(ctl_b); pm = json.loads(pm_b); base_doc = json.loads(base["controls"])
    if c["versions"][:-1] != base_doc["versions"] or {k: v for k, v in c.items() if k != "versions"} != {k: v for k, v in base_doc.items() if k != "versions"}:
        why.append("candidate versions 1-20 / programme / deployment / history_manifest are not the adopted v20 controls'")
    v21, v20 = c["versions"][-1], c["versions"][-2]
    if v21.get("version") != 21 or v20.get("version") != 20:
        why.append("the candidate's last two entries are not versions 20 and 21")
    if sorted(v21["files"]) != sorted(v20["files"]):
        why.append("the v21 entry pins another file set than v20")
    pins = {r["promoted"]: r["sha256"] for r in rows() if r["group"] == "pin"}
    for f, h in v21["files"].items():
        want = pins.get(f, v20["files"].get(f))
        if h != want:
            why.append(f"v21 pin {f} is not {want[:8] if want else None}")
    for k in ("qualification_S", "partition"):
        if v21.get(k) != v20.get(k):
            why.append(f"v21 {k} differs from v20")
    if v20.get("partition") != B.V20_PARTITION:
        why.append("v20 does not pin the e3 partition ca87fb1d")
    e20, e21 = (v20.get("sub_envelopes") or [{}]), (v21.get("sub_envelopes") or [{}])
    if len(e21) != 1 or len(e20) != 1 or {k: v for k, v in e21[0].items() if k not in ("cap_core_h", "rule")} != {k: v for k, v in e20[0].items() if k not in ("cap_core_h", "rule")} \
            or e21[0].get("cap_core_h") != B.V21_SUBENV_CAP or e20[0].get("cap_core_h") != B.V20_SUBENV_CAP:
        why.append("the v21 sub-envelope is not v20's refit+S with only its cap raised 81,000 -> 181,000")
    if v21.get("funding_route") != B.FUNDING_ROUTE or "funding_route" in v20:
        why.append("the v21 funding_route is not build_v21.FUNDING_ROUTE (or v20 already had one)")
    if sorted(v21) != sorted(list(v20) + ["funding_route"]):
        why.append("the v21 entry carries other keys than v20's + funding_route")
    if [r["promoted"] for r in pm["rows"][:-1]] != [r["promoted"] for r in rows()] or pm["rows"][-1]["sha256"] != hashlib.sha256(ctl_b).hexdigest() \
            or pm["rows"][-1]["promoted"] != CTL:
        why.append("the promotion map does not list the build's rows and the candidate controls")
    if require_git:
        for rel in sorted({r["source"] for r in rows()} | {CREL + "row19_screen_controls.json", CREL + "v21_promotion_map.json",
                                                          CREL + "build_v21.py", CREL + "promote_v21.py", B.NODE_EVIDENCE[0]}):
            if not git_ok(rel):
                why.append(f"{rel} is not git-tracked and unmodified")
    return why


def state():
    """{promoted path: 'v20' | 'v21' | 'other'} (v20 = its previous bytes)."""
    st = {}
    for r in rows() + [dict(promoted=CTL, sha256=sha(CREL + "row19_screen_controls.json"))]:
        h = sha_or_none(r["promoted"])
        prev = V20_CTL if r["promoted"] == CTL else PREVIOUS[r["promoted"]]
        if h is None:
            st[r["promoted"]] = "other"; continue
        st[r["promoted"]] = "v21" if h == r["sha256"] else ("v20" if h == prev else "other")
    return st


def literal():
    return f"ADOPT row19-screen-controls sha256={sha(CREL + 'row19_screen_controls.json')} version=21"


def review_problems(rec):
    if not rec:
        return ["--review reviews/<record>.md is required (the committed operator adoption record with the v21 ADOPT literal)"]
    if not re.match(r"^reviews/[A-Za-z0-9._-]+\.md$", rec) or not os.path.isfile(os.path.join(T1, rec)):
        return [f"{rec} is not an existing reviews/<name>.md record"]
    lit = literal()
    if lit not in [l.strip() for l in open(os.path.join(T1, rec)).read().splitlines()]:
        return [f"{rec} does not carry the literal `{lit}`"]
    r = git("show", f"HEAD:./{rec}")
    if not git_ok(rec) or r.returncode != 0 or lit not in [l.strip() for l in r.stdout.splitlines()]:
        return [f"{rec} is not git-tracked and unmodified with the literal in HEAD"]
    return []


def adoption_v21_bytes(rec):
    """The exact version-21 adoption record (deterministic: commits from git history, no time or host)."""
    ccommit = git("log", "-1", "--format=%h", "--", CREL + "row19_screen_controls.json").stdout.strip()
    rcommit = git("log", "-1", "--format=%h", "--", rec).stdout.strip()
    h = {r["promoted"]: r["sha256"][:8] for r in rows()}
    ad = {"schema": "row19-screen-controls-adoption-1", "controls_path": CTL, "controls_sha256": sha(CREL + "row19_screen_controls.json"),
          "version": 21, "controls_commit": ccommit,
          "review_record": {"path": rec, "sha256": sha(rec), "commit": rcommit, "adopt_line": literal()},
          "by": "R052 Entropy SI (Claude), operator record under the owner's 20 Oct 2026 rule",
          "previous": {"version": 20, "controls_sha256": V20_CTL, "adoption_sha256": V20_ADOPT,
                       "archived": "Lengau archive_screen/v20_before_v21, Mac " + ARCH + "/"},
          "scope": "controls v20 -> v21, the FUNDING ROUTE (owner ruling 26 Oct 2026: CSCI1913 first, then HEAL1922, side by side; "
                   f"chpc/candidate_v21_heal/DESIGN_v21.md): chpc/programme_gate.py ({h['chpc/programme_gate.py']}, REVISION 5: the route "
                   f"and per-programme accounting) and chpc/row19_screen_admit.py ({h['chpc/row19_screen_admit.py']}, REVISION 21: each job "
                   "to the first programme that fits; `programme` on the entry, the plan and #PBS -P), funding_route CSCI1913 100,000 "
                   "then HEAL1922 100,000, refit+S sub-envelope 181,000; every other controller byte, the partition e3, the crash rule, "
                   "the rescue route and the science unchanged. The ledger cap follows by the two-phase --raise-cap 181000; a "
                   "regenerated pilot qualification with a NEW pilot literal precedes any further refit admission"}
    return (json.dumps(ad, indent=1) + "\n").encode()


def adoption_state(rec):
    p = os.path.join(T1, ADOPT)
    if not os.path.isfile(p) or os.path.islink(p):
        return "other"
    b = open(p, "rb").read()
    if hashlib.sha256(b).hexdigest() == V20_ADOPT:
        return "v20"
    return "v21" if rec and b == adoption_v21_bytes(rec) else "other"


def order():
    """The map order (the pins: programme gate, admission), then the controls LAST."""
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
        counts = {k: sum(1 for s in st.values() if s == k) for k in ("v20", "v21", "other")}
        print(f"CANDIDATE OK: controls v21 {sha(CREL + 'row19_screen_controls.json')}, {len(rows())} map rows + the controls, every pin = its "
              f"source bytes, versions 1-20 = adopted v20 (the authenticated {B.resolve_base()[0]['source']} v20 base), funding_route "
              f"CSCI1913 -> HEAL1922, refit+S 81,000 -> 181,000")
        print(f"live tree: {counts} " + ", ".join(f"{k}={s}" for k, s in st.items() if s != "v20"))
        print(f"the adoption literal this candidate needs: {literal()}")
        return 0
    why = review_problems(a.review) + archive_problems()
    if why:
        print("REFUSED:"); [print("  -", w) for w in why]; return 3
    ad = adoption_state(a.review)
    if "other" in st.values():
        print("REFUSED: promoted paths are neither their v20 nor their v21 bytes:", ", ".join(k for k, s in st.items() if s == "other")); return 3
    if ad == "other":
        print("REFUSED: the adoption record is neither the adopted v20 record 1ef162de nor the exact version-21 record"); return 3
    if ad == "v21" and st[CTL] != "v21":
        print("REFUSED: a version-21 adoption is written over non-v21 controls"); return 3
    if all(s == "v21" for s in st.values()) and ad == "v21":
        print(f"already promoted, verified (candidate, record, archive {ARCH}/, the exact version-21 adoption {sha(ADOPT)[:16]}); nothing to do"); return 0
    if a.check_promoted:
        print("REFUSED: --check-promoted: the promotion is not complete:", ", ".join(f"{k}={s}" for k, s in st.items()), f"adoption={ad}"); return 3
    todo = [r for r in order() if st[r["promoted"]] != "v21"]
    if a.dry_run:
        print("DRY RUN - checks pass; would copy, in order:"); [print(f"  - {r['source']} -> {r['promoted']}") for r in todo]
        print("  - then write chpc/row19_screen_controls_adoption.json (version 21), atomically"); return 0
    for r in todo:
        dst = os.path.join(T1, r["promoted"]); os.makedirs(os.path.dirname(dst), exist_ok=True)
        tmp = dst + f".tmp.{os.getpid()}"
        shutil.copyfile(os.path.join(T1, r["source"]), tmp); os.replace(tmp, dst)
        if sha(r["promoted"]) != r["sha256"]:
            print(f"REFUSED: {r['promoted']} does not hold the pinned bytes after the copy"); return 3
    p = os.path.join(T1, ADOPT); tmp = p + f".tmp.{os.getpid()}"
    open(tmp, "wb").write(adoption_v21_bytes(a.review)); os.replace(tmp, p)
    print("promoted:", ", ".join(f"{os.path.basename(r['promoted'])} {r['sha256'][:8]}" for r in todo), "adoption", sha(ADOPT)[:16])
    return 0


if __name__ == "__main__":
    sys.exit(main())
