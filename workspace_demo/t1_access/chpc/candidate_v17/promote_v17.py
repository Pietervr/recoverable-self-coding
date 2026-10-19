"""Controls v17 CANDIDATE (NOT adopted): the v16 -> v17 promotion check and (after review) promotion, on the
chpc/migration_v16/promote_v16.py pattern. Design: chpc/candidate_v17/DESIGN_v17.md. The real promotion has NOT been run.

    python3 chpc/candidate_v17/promote_v17.py --check                                (from workspace_demo/t1_access)
    python3 chpc/candidate_v17/promote_v17.py --check-promoted --review reviews/<record>.md
    python3 chpc/candidate_v17/promote_v17.py --dry-run --review reviews/<record>.md
    python3 chpc/candidate_v17/promote_v17.py --review reviews/<record>.md         (the real promotion; needs the review + archive)

--check (no review needed, no write): verifies the CANDIDATE - the controls and promotion map are build_v17.py's deterministic
bytes; every row's source holds exactly its pinned sha256; versions 1-16 of the candidate are byte-identical to the adopted
v16 controls (or, once promoted, to the archived v16 controls); the v17 entry pins exactly the v16 file set plus
row19_ec2_e2rules.py and row19_ec2_e2qual.py, every changed pin equals the promotion-map row and every unchanged pin equals
v16's; the partition reference is the e2 final file 48cea639; sub_envelopes, qualification_S, programme, deployment and
history_manifest are v16's; the e2 partition loads under the candidate row19_partition (schema 2, epoch 2, predecessor = e1
8d1de408, owned 3,274, the bound snapshot 31cc268f and designated a96eb598); and every candidate source is git-tracked and
unmodified. It then reports each promoted path as v16 / v17 / other. Exit 0 when the candidate verifies.

--check-promoted: the deploy gate (promote_v16.py --check): exit 0 only for a COMPLETE verified promotion - every path at its
v17 bytes, the exact version-17 adoption record, the review and the archive verifying.

The real promotion refuses unless, in addition to --check: the review record is git-tracked, unmodified, holds the literal
`ADOPT row19-screen-controls sha256=<candidate controls sha256> version=17` in HEAD; the Mac archive
chpc/results/archive/row19_screen_v16_before_v17/ holds EXACTLY the ARCHIVE inventory below plus SHA256SUMS and COMPLETE, every
digest verifying (written by the migration_v17 archive step - NOT built in this package); every promoted path holds its v16
(previous) bytes or already its v17 bytes, and the adoption record is the v16 record or exactly the version-17 record. It then
copies data and partition, Mac code, helpers, admission and LAST the controls, then writes the version-17 adoption record
(atomic replaces). A finished promotion re-runs every check and reports "already promoted"; an interrupted one resumes;
anything else refuses."""
import argparse, hashlib, importlib.util, json, os, re, shutil, subprocess, sys

CAND = os.path.dirname(os.path.abspath(__file__))
CHPC = os.path.dirname(CAND)
T1 = os.path.dirname(CHPC)
CREL = "chpc/candidate_v17/"
sys.path.insert(0, CAND)
import build_v17 as B  # noqa: E402  (same folder: the map, the expected bytes and the deterministic build)

CTL = "chpc/row19_screen_controls.json"
ADOPT = "chpc/row19_screen_controls_adoption.json"
V16_CTL, V16_ADOPT = B.ADOPTED_CTL[1], B.ADOPTED_ADOPTION[1]
NEW_PINS = ("chpc/row19_ec2_e2rules.py", "chpc/row19_ec2_e2qual.py")
ARCH = "chpc/results/archive/row19_screen_v16_before_v17"
QUAL = ("chpc/results/row19_screen/receipts/qualified_refit_job1.json", "2c7a7ef1fb903cf0fa75701d2a56d216e98faf14e6638da891afd8bed0bfea44")
ARCHIVE = dict({os.path.basename(p): (p, h) for p, h in B.PREVIOUS.items() if h is not None},
               **{"row19_screen_controls.json": (CTL, V16_CTL), "row19_screen_controls_adoption.json": (ADOPT, V16_ADOPT),
                  "qualified_refit_job1.json": QUAL, "row19_screen_budget.json": ("chpc/row19_screen_budget.json", None)})
ARCH_SCHEMA = "row19-screen-mac-archive-v16-before-v17-1"
ORDER_GROUPS = ("part", "data", "mac", "pin")          # then the admission (a pin, moved last among pins), then the controls


def sha(rel):
    return hashlib.sha256(open(os.path.join(T1, rel), "rb").read()).hexdigest()


def sha_or_none(rel):
    p = os.path.join(T1, rel)
    return sha(rel) if os.path.isfile(p) else None


def git(*a):
    return subprocess.run(["git", "-C", T1, *a], capture_output=True, text=True)


def git_ok(rel):
    return git("ls-files", "--error-unmatch", "--", rel).returncode == 0 and git("diff", "--quiet", "HEAD", "--", rel).returncode == 0


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def rows():
    return [dict(promoted=d, source=s, sha256=h, group=g) for d, s, h, g in B.MAP]


def candidate_problems(require_git=True):
    """Every check of the CANDIDATE (no live state, no review). [] when it verifies."""
    why = list(B.input_problems())
    if why:
        return why
    ctl_b, pm_b = B.build()
    for rel, b in ((CREL + "row19_screen_controls.json", ctl_b), (CREL + "v17_promotion_map.json", pm_b)):
        if sha_or_none(rel) != hashlib.sha256(b).hexdigest():
            why.append(f"{rel} is not build_v17.py's deterministic bytes")
    c = json.loads(ctl_b)
    pm = json.loads(pm_b)
    base_doc = json.load(open(os.path.join(T1, CTL))) if sha(CTL) == V16_CTL else None
    if base_doc is None and os.path.isfile(os.path.join(T1, ARCH, "row19_screen_controls.json")):
        base_doc = json.load(open(os.path.join(T1, ARCH, "row19_screen_controls.json")))      # promoted: compare with the archived v16
    if base_doc is None:
        why.append("neither the live controls nor the archive holds the adopted v16 controls to compare versions 1-16 with")
    elif c["versions"][:-1] != base_doc["versions"] or {k: v for k, v in c.items() if k != "versions"} != {k: v for k, v in base_doc.items() if k != "versions"}:
        why.append("candidate versions 1-16 / programme / deployment / history_manifest are not the adopted v16 controls'")
    v17, v16 = c["versions"][-1], c["versions"][-2]
    if v17.get("version") != 17 or v16.get("version") != 16:
        why.append("the candidate's last two entries are not versions 16 and 17")
    if sorted(v17["files"]) != sorted(set(v16["files"]) | set(NEW_PINS)) or any(p in v16["files"] for p in NEW_PINS):
        why.append("the v17 entry pins another file set than v16 plus row19_ec2_e2rules.py and row19_ec2_e2qual.py")
    pins = {r["promoted"]: r["sha256"] for r in rows() if r["group"] == "pin"}
    for f, h in v17["files"].items():
        want = pins.get(f, v16["files"].get(f))
        if h != want:
            why.append(f"v17 pin {f} is not {want[:8] if want else None}")
        if f not in pins and h != v16["files"].get(f):
            why.append(f"{f} differs from v16 (v17 changes only the admission and the epoch-2 helpers)")
    part = [r for r in rows() if r["group"] == "part"][0]
    if v17.get("partition") != {"path": part["promoted"], "sha256": part["sha256"]}:
        why.append("the v17 partition reference is not chpc/row19_partition_e2.json 48cea639")
    for k in ("sub_envelopes", "qualification_S"):
        if v17.get(k) != v16.get(k):
            why.append(f"v17 {k} differs from v16")
    if sorted(v17) != sorted(v16):
        why.append("the v17 entry carries other keys than v16's")
    if v16.get("partition") != {"path": B.E1[0], "sha256": B.E1[1]}:
        why.append("v16 does not pin e1 8d1de408 (the provenance predecessor)")
    if [r["promoted"] for r in pm["rows"][:-1]] != [r["promoted"] for r in rows()] or pm["rows"][-1]["sha256"] != hashlib.sha256(ctl_b).hexdigest():
        why.append("the promotion map does not list the build's rows and the candidate controls")
    why += partition_problems()
    if require_git:
        for rel in sorted({r["source"] for r in rows()} | {CREL + "row19_screen_controls.json", CREL + "v17_promotion_map.json",
                                                          CREL + "build_v17.py", CREL + "promote_v17.py", B.ADMIT_DIFF[0]}):
            if not git_ok(rel):
                why.append(f"{rel} is not git-tracked and unmodified")
    return why


def partition_problems():
    """The e2 final declaration loads under the candidate partition module and binds what the design says."""
    why = []
    try:
        RP = load_mod("row19_partition_v17check", os.path.join(CHPC, "candidate_e2", "row19_partition.py"))
        man_path = os.path.join(CHPC, "row19_screen_manifest.json")
        RP.DESIGNATED_PATH = os.path.join(CHPC, "row19_screen_designated.json")
        src = [r for r in rows() if r["group"] == "part"][0]["source"]
        p = RP.load(os.path.join(T1, src), json.load(open(man_path)), sha("chpc/row19_screen_manifest.json"))
        snap = [r for r in rows() if r["promoted"] == "chpc/claims_snapshot_e2.json"][0]
        if not (p["schema"] == RP.SCHEMA2 and p["epoch"] == 2 and p["predecessor"]["sha256"] == B.E1[1] and p["predecessor"]["epoch"] == 1
                and p["owned_count"] == 3274 and p["claims_snapshot"]["sha256"] == snap["sha256"]
                and p["designated"]["sha256"] == "a96eb59833ff794d3f9ce0ca09ada03d045a29cb9f8a676dad86f8aba85d5584" and p["transferred"] == []):
            why.append("the e2 declaration does not bind schema 2 / epoch 2 / predecessor e1 / 3,274 owned / snapshot 31cc268f / designated a96eb598")
        RP.load(os.path.join(T1, src), json.load(open(man_path)), sha("chpc/row19_screen_manifest.json"),
                snapshot_path=os.path.join(T1, snap["source"]), predecessor_path=os.path.join(T1, B.E1[0]))   # verify2: byte-equal regeneration
    except Exception as e:
        why.append(f"the e2 declaration does not load/regenerate under the candidate row19_partition ({type(e).__name__}: {e})")
    return why


def state():
    """{promoted path: 'v16' | 'v17' | 'other'} (v16 = its previous bytes, or absent for a new path)."""
    st = {}
    for r in rows() + [dict(promoted=CTL, sha256=sha(CREL + "row19_screen_controls.json"))]:
        h = sha_or_none(r["promoted"])
        prev = V16_CTL if r["promoted"] == CTL else B.PREVIOUS[r["promoted"]]
        st[r["promoted"]] = "v17" if h == r["sha256"] else ("v16" if h == prev else "other")
    return st


def archive_problems():
    d = os.path.join(T1, ARCH)
    if not os.path.isdir(d):
        return [f"the Mac archive {ARCH}/ does not exist (migration_v17 archive step)"]
    why = []
    names = sorted(os.listdir(d))
    if names != sorted(list(ARCHIVE) + ["SHA256SUMS", "COMPLETE"]):
        return [f"the archive holds {names}, not exactly its inventory + SHA256SUMS + COMPLETE"]
    sums = {}
    for line in open(os.path.join(d, "SHA256SUMS")).read().splitlines():
        m = re.match(r"^([0-9a-f]{64})  ([A-Za-z0-9._-]+)$", line)
        if not m:
            return ["the archive's SHA256SUMS has a malformed line"]
        sums[m.group(2)] = m.group(1)
    if sorted(sums) != sorted(ARCHIVE):
        why.append("the archive's SHA256SUMS does not list exactly its inventory")
    for n, (src, fixed) in ARCHIVE.items():
        h = hashlib.sha256(open(os.path.join(d, n), "rb").read()).hexdigest()
        if sums.get(n) != h or (fixed is not None and h != fixed):
            why.append(f"archive member {n} does not verify ({h[:8]})")
    try:
        comp = json.load(open(os.path.join(d, "COMPLETE")))
        if comp.get("schema") != ARCH_SCHEMA or comp.get("sha256sums") != hashlib.sha256(open(os.path.join(d, "SHA256SUMS"), "rb").read()).hexdigest():
            why.append("the archive's COMPLETE certificate does not name its SHA256SUMS")
    except Exception as e:
        why.append(f"the archive's COMPLETE is unreadable ({type(e).__name__})")
    return why


def literal():
    return f"ADOPT row19-screen-controls sha256={sha(CREL + 'row19_screen_controls.json')} version=17"


def review_problems(rec):
    if not rec:
        return ["--review reviews/<record>.md is required (the committed Codex record with the v17 ADOPT literal)"]
    if not re.match(r"^reviews/[A-Za-z0-9._-]+\.md$", rec) or not os.path.isfile(os.path.join(T1, rec)):
        return [f"{rec} is not an existing reviews/<name>.md record"]
    lit = literal()
    if lit not in [l.strip() for l in open(os.path.join(T1, rec)).read().splitlines()]:
        return [f"{rec} does not carry the literal `{lit}`"]
    r = git("show", f"HEAD:./{rec}")
    if not git_ok(rec) or r.returncode != 0 or lit not in [l.strip() for l in r.stdout.splitlines()]:
        return [f"{rec} is not git-tracked and unmodified with the literal in HEAD"]
    return []


def adoption_v17_bytes(rec):
    """The exact version-17 adoption record (deterministic: commits from git history, no time or host)."""
    ccommit = git("log", "-1", "--format=%h", "--", CREL + "row19_screen_controls.json").stdout.strip()
    rcommit = git("log", "-1", "--format=%h", "--", rec).stdout.strip()
    ad = {"schema": "row19-screen-controls-adoption-1", "controls_path": CTL, "controls_sha256": sha(CREL + "row19_screen_controls.json"),
          "version": 17, "controls_commit": ccommit,
          "review_record": {"path": rec, "sha256": sha(rec), "commit": rcommit, "adopt_line": literal()},
          "by": "R052 Entropy SI (Claude)",
          "previous": {"version": 16, "controls_sha256": V16_CTL, "adoption_sha256": V16_ADOPT,
                       "archived": "Lengau archive_screen/v16_before_v17, Mac " + ARCH + "/"},
          "scope": "controls v16 -> v17, the EC2 provider epoch-2 adoption (chpc/candidate_v17/DESIGN_v17.md): the partition pin e1 8d1de408 -> "
                   "the final epoch-2 declaration 48cea639 (e1 kept as pinned provenance in versions 13-16 and as the e2 predecessor); the "
                   "epoch-2 helpers (row19_partition eabf50c3, row19_ec2_ingest 6ac144c6, row19_ec2_e2rules a9ea1f61, row19_ec2_state 7bdedafc, "
                   "row19_ec2_qualify 73f912b8, row19_ec2_e2qual b3f29816) and the admission's schema-2 print line (c3960464); every other "
                   "controller byte unchanged. Lengau refit admission HOLDS until the canonical epoch-2 activation; fresh v17 receipts and a "
                   "regenerated pilot qualification with a NEW pilot literal precede any further refit admission; grants no EC2 qualification "
                   "or production (schema-3 RELEASE + FAVOURABLE actual-result review + release-adopt)"}
    return (json.dumps(ad, indent=1) + "\n").encode()


def adoption_state(rec):
    p = os.path.join(T1, ADOPT)
    if not os.path.isfile(p):
        return "other"
    b = open(p, "rb").read()
    if hashlib.sha256(b).hexdigest() == V16_ADOPT:
        return "v16"
    return "v17" if rec and b == adoption_v17_bytes(rec) else "other"


def order():
    rs = rows()
    first = [r for g in ORDER_GROUPS for r in rs if r["group"] == g and r["promoted"] != "chpc/row19_screen_admit.py"]
    return first + [r for r in rs if r["promoted"] == "chpc/row19_screen_admit.py"] + \
        [dict(promoted=CTL, source=CREL + "row19_screen_controls.json", sha256=sha(CREL + "row19_screen_controls.json"), group="ctl")]


def main(argv=None):
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true"); g.add_argument("--check-promoted", action="store_true"); g.add_argument("--dry-run", action="store_true")
    ap.add_argument("--review", default=None); a = ap.parse_args(argv)
    why = candidate_problems()
    if why:
        print("REFUSED: the candidate does not verify:"); [print("  -", w) for w in why]; return 3
    st = state()
    if a.check:
        counts = {k: sum(1 for s in st.values() if s == k) for k in ("v16", "v17", "other")}
        print(f"CANDIDATE OK: controls v17 {sha(CREL + 'row19_screen_controls.json')}, {len(rows())} map rows + the controls, every pin = its "
              f"source bytes, versions 1-16 = adopted v16, e2 partition 48cea639 loads and regenerates (verify2)")
        print(f"live tree: {counts} " + ", ".join(f"{k}={s}" for k, s in st.items() if s != "v16"))
        print(f"the adoption literal this candidate needs: {literal()}")
        return 0
    why = review_problems(a.review) + archive_problems()
    if why:
        print("REFUSED:"); [print("  -", w) for w in why]; return 3
    ad = adoption_state(a.review)
    if "other" in st.values():
        print("REFUSED: promoted paths are neither their v16 nor their v17 bytes:", ", ".join(k for k, s in st.items() if s == "other")); return 3
    if ad == "other":
        print("REFUSED: the adoption record is neither the adopted v16 record 523fe18a nor the exact version-17 record"); return 3
    if ad == "v17" and st[CTL] != "v17":
        print("REFUSED: a version-17 adoption is written over non-v17 controls"); return 3
    if all(s == "v17" for s in st.values()) and ad == "v17":
        print(f"already promoted, verified (candidate, review, archive {ARCH}/, the exact version-17 adoption {sha(ADOPT)[:16]}); nothing to do"); return 0
    if a.check_promoted:
        print("REFUSED: --check-promoted: the promotion is not complete:", ", ".join(f"{k}={s}" for k, s in st.items()), f"adoption={ad}"); return 3
    todo = [r for r in order() if st[r["promoted"]] != "v17"]
    if a.dry_run:
        print("DRY RUN - checks pass; would copy, in order:"); [print(f"  - {r['source']} -> {r['promoted']}") for r in todo]
        print("  - then write chpc/row19_screen_controls_adoption.json (version 17), atomically"); return 0
    for r in todo:
        dst = os.path.join(T1, r["promoted"]); os.makedirs(os.path.dirname(dst), exist_ok=True)
        tmp = dst + f".tmp.{os.getpid()}"
        shutil.copyfile(os.path.join(T1, r["source"]), tmp); os.replace(tmp, dst)
        if sha(r["promoted"]) != r["sha256"]:
            print(f"REFUSED: {r['promoted']} does not hold the pinned bytes after the copy"); return 3
    p = os.path.join(T1, ADOPT); tmp = p + f".tmp.{os.getpid()}"
    open(tmp, "wb").write(adoption_v17_bytes(a.review)); os.replace(tmp, p)
    print("promoted:", ", ".join(f"{os.path.basename(r['promoted'])} {r['sha256'][:8]}" for r in todo), "adoption", sha(ADOPT)[:16])
    return 0


if __name__ == "__main__":
    sys.exit(main())
