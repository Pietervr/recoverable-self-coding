"""Controls v17 CANDIDATE (NOT adopted): the promotion state machine of chpc/candidate_v17/promote_v17.py REVISION 2 and
build_v17.py REVISION 2, for Codex's review reviews/2026-10-19_e2_adoption_codex_review.md C1. Everything runs in PRIVATE test
trees (a temporary git repository holding a copy of the files the promoter reads); the live tree is never written and is checked
untouched at the end. No AWS, no Lengau.

  1. before promotion: --check passes from the LIVE v16 base; the real promotion refuses without the archive; --dry-run passes
     with the archive and a committed review record carrying the v17 literal;
  2. interrupted promotion: the REAL promote code runs until the adoption write, which is made to fail (a simulated crash after
     the controls-last copy). In that state --check and build_v17.py --check pass from the ARCHIVED v16 base, --check-promoted
     refuses as "not complete", and a retry resumes and writes only the version-17 adoption record;
  3. complete promotion: --check-promoted passes ("already promoted, verified"), --check passes, and a complete retry writes
     nothing (every file's bytes and mtime unchanged);
  4. the archive: missing, partial (a member removed), corrupt (a member changed with SHA256SUMS and COMPLETE regenerated; a
     SHA256SUMS line changed; COMPLETE of another schema; an extra file) - each refuses --check, --check-promoted, the retry and
     build_v17.py --check while the base must come from the archive;
  5. the review's case (b): exact v17 controls with a CHANGED adoption record refuses --check-promoted and the retry on the
     adoption, never on the base;
  6. the live tree is untouched (controls v16, adoption v16, no archive).

    python3 chpc/candidate_v17/test_v17_promote.py            (from workspace_demo/t1_access)"""
import hashlib, importlib.util, json, os, shutil, subprocess, sys, tempfile

V17 = os.path.dirname(os.path.abspath(__file__)); CHPC = os.path.dirname(V17); T1 = os.path.dirname(CHPC)
fails, n = [], [0]


def check(name, cond, extra=""):
    n[0] += 1
    print(("ok   " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""), flush=True)
    if not cond:
        fails.append(name)


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def sha(p):
    return sha_b(open(p, "rb").read())


# the live tree's map and inventory, read by parsing the real build_v17 module text in a throwaway namespace (not imported by name,
# so the private promoter's own `import build_v17` stays its private copy)
spec = importlib.util.spec_from_file_location("build_v17_live_ref", os.path.join(V17, "build_v17.py"))
BL = importlib.util.module_from_spec(spec); spec.loader.exec_module(BL)
LIVE_BEFORE = {rel: (sha(os.path.join(T1, rel)) if os.path.isfile(os.path.join(T1, rel)) else None)
               for rel in [BL.ADOPTED_CTL[0], BL.ADOPTED_ADOPTION[0]] + [d for d, _s, _h, _g in BL.MAP]}
check("live tree before: controls v16 01976b6a, adoption 523fe18a, no v17 archive",
      LIVE_BEFORE[BL.ADOPTED_CTL[0]] == BL.ADOPTED_CTL[1] and LIVE_BEFORE[BL.ADOPTED_ADOPTION[0]] == BL.ADOPTED_ADOPTION[1]
      and not os.path.exists(os.path.join(T1, BL.ARCH)))

# ---- the private tree -------------------------------------------------------------------------------------------------------
REPO = tempfile.mkdtemp(prefix="v17_promote_")
P = os.path.join(REPO, "workspace_demo", "t1_access")
COPY = set(["chpc/candidate_v17/build_v17.py", "chpc/candidate_v17/promote_v17.py", "chpc/candidate_v17/row19_screen_controls.json",
            "chpc/candidate_v17/v17_promotion_map.json", BL.ADMIT_DIFF[0], BL.E1[0], BL.ADOPTED_CTL[0], BL.ADOPTED_ADOPTION[0],
            "chpc/row19_screen_manifest.json", "chpc/row19_screen_designated.json", "chpc/row19_ec2_state.py", "chpc/row19_screen_budget.json"]
           + [s for _d, s, _h, _g in BL.MAP] + [p for p, h in BL.PREVIOUS.items() if h is not None])
for rel in sorted(COPY):
    os.makedirs(os.path.dirname(os.path.join(P, rel)), exist_ok=True); shutil.copyfile(os.path.join(T1, rel), os.path.join(P, rel))
QUAL_SRC = os.path.join(T1, BL.QUAL[0])
HAVE_QUAL = os.path.isfile(QUAL_SRC) and sha(QUAL_SRC) == BL.QUAL[1]
if HAVE_QUAL:                                       # bytes copied, never parsed: the archive member must be the v16 qualification
    os.makedirs(os.path.dirname(os.path.join(P, BL.QUAL[0])), exist_ok=True); shutil.copyfile(QUAL_SRC, os.path.join(P, BL.QUAL[0]))
check("the v16 pilot qualification 2c7a7ef1 is available to build a complete private archive (else section 2-5 cannot run)", HAVE_QUAL)


def git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True)


git("init", "-q"); git("config", "user.email", "test@example.invalid"); git("config", "user.name", "v17 promote test")
git("config", "commit.gpgsign", "false")
LIT = None


def run(*args, script="promote_v17.py"):
    p = subprocess.run([sys.executable, os.path.join(P, "chpc", "candidate_v17", script), *args], cwd=P, capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout + p.stderr


def snapshot():
    out = {}
    for d, _ds, fs in os.walk(P):
        if "__pycache__" in d:
            continue
        for f in fs:
            p_ = os.path.join(d, f); st = os.stat(p_)
            out[os.path.relpath(p_, P)] = (sha(p_), st.st_mtime_ns)
    return out


rc, out = run("--check")
check("private tree, before git: --check refuses (candidate sources must be git-tracked and unmodified)", rc == 3 and "git-tracked" in out, out[-300:])
git("add", "-A"); r = git("commit", "-q", "-m", "private v17 promotion test tree")
check("private git tree committed", r.returncode == 0, r.stderr)
rc, out = run("--check")
check("1. before promotion: --check passes from the LIVE v16 base (no archive needed)", rc == 0 and "authenticated live v16 base" in out, out[-400:])
LIT = [l for l in out.splitlines() if l.startswith("the adoption literal")][0].split(": ", 1)[1]
REC = "reviews/2026-10-19_v17_private_test_review.md"
os.makedirs(os.path.join(P, "reviews"))
open(os.path.join(P, REC), "w").write(f"# private test record\n\nFAVOURABLE (test fixture only)\n\n{LIT}\n")
git("add", os.path.join(P, REC)); git("commit", "-q", "-m", "private review record")
rc, out = run("--review", REC)
check("1. the real promotion refuses without the v16 archive", rc == 3 and "does not exist" in out, out[-300:])


def make_archive():
    d = os.path.join(P, BL.ARCH); os.makedirs(d)
    for name, (src, _fixed) in BL.ARCHIVE.items():
        shutil.copyfile(os.path.join(P, src), os.path.join(d, name))
    sums = "".join(f"{sha(os.path.join(d, nm))}  {nm}\n" for nm in sorted(BL.ARCHIVE))
    open(os.path.join(d, "SHA256SUMS"), "w").write(sums)
    json.dump(dict(schema=BL.ARCH_SCHEMA, sha256sums=sha_b(sums.encode()), lengau_sha256sums="0" * 64), open(os.path.join(d, "COMPLETE"), "w"))
    return d


if HAVE_QUAL:
    ARCHD = make_archive()
    check("the private archive verifies: 13 members (5 chpc, 4 Mac, controls, adoption, qualification, budget) + SHA256SUMS + COMPLETE",
          len(BL.ARCHIVE) == 13 and run("--dry-run", "--review", REC)[0] == 0)
    rc, out = run("--dry-run", "--review", REC)
    check("1. --dry-run passes with the archive and the committed review; it would copy 19 rows + the controls, then write the adoption",
          rc == 0 and out.count("  - chpc/") + out.count("  - aws_ec2/") >= 20 and "adoption" in out, out[-300:])

    # ---- 2. interrupted promotion: the REAL promote code until the adoption write fails ------------------------------------------
    sys.path.insert(0, os.path.join(P, "chpc", "candidate_v17"))
    sp = importlib.util.spec_from_file_location("promote_v17_private", os.path.join(P, "chpc", "candidate_v17", "promote_v17.py"))
    PVp = importlib.util.module_from_spec(sp); sp.loader.exec_module(PVp)
    check("the in-process promoter is the PRIVATE copy (its T1 is the private tree)", os.path.abspath(PVp.T1) == os.path.abspath(P)
          and os.path.abspath(PVp.B.T1) == os.path.abspath(P))
    real_replace = os.replace
    ADOPT_P = os.path.join(P, PVp.ADOPT)
    def crash_on_adoption(src, dst):
        if os.path.abspath(dst) == os.path.abspath(ADOPT_P):
            raise OSError("simulated crash after the controls-last copy, before the adoption write")
        return real_replace(src, dst)
    os.replace = crash_on_adoption
    try:
        PVp.main(["--review", REC]); crashed = False
    except OSError:
        crashed = True
    finally:
        os.replace = real_replace
    for f in os.listdir(os.path.dirname(ADOPT_P)):                       # the crashed write's temp file (as a real crash leaves it)
        if f.startswith(os.path.basename(ADOPT_P) + ".tmp."):
            os.remove(os.path.join(os.path.dirname(ADOPT_P), f))
    st = PVp.state()
    check("2. the simulated crash hit after every copy including the controls: every promoted path v17, the adoption still v16",
          crashed and set(st.values()) == {"v17"} and sha(ADOPT_P) == BL.ADOPTED_ADOPTION[1], st)
    before = snapshot()
    rc, out = run("--check")
    check("2. interrupted: --check passes from the ARCHIVED v16 base (reviewed bytes refused here)", rc == 0 and "authenticated archive v16 base" in out, out[-400:])
    rc_b, out_b = run("--check", script="build_v17.py")
    check("2. interrupted: build_v17.py --check rebuilds the identical candidate from the archived base", rc_b == 0 and "archive v16 base" in out_b, out_b[-300:])
    rc, out = run("--check-promoted", "--review", REC)
    check("2. interrupted: --check-promoted refuses for the right reason (promotion not complete: adoption v16), not the base",
          rc == 3 and "not complete" in out and "adoption=v16" in out and "no authenticated" not in out, out[-400:])
    check("2. the checks wrote nothing", snapshot() == before)
    rc, out = run("--review", REC)
    after = snapshot()
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    check("2. the retry resumes: it copies nothing and writes ONLY the version-17 adoption record",
          rc == 0 and changed == [PVp.ADOPT] and PVp.adoption_state(REC) == "v17", (rc, changed, out[-300:]))

    # ---- 3. complete ------------------------------------------------------------------------------------------------------------
    before = snapshot()
    rc, out = run("--check-promoted", "--review", REC)
    check("3. complete: --check-promoted passes ('already promoted, verified')", rc == 0 and "already promoted, verified" in out, out[-400:])
    rc, out = run("--check")
    check("3. complete: --check passes from the archived base", rc == 0 and "archive v16 base" in out, out[-300:])
    rc, out = run("--review", REC)
    check("3. complete retry: rc 0, 'nothing to do', and no file's bytes or mtime changed", rc == 0 and "nothing to do" in out and snapshot() == before,
          out[-300:])
    rc, out = run("--dry-run", "--review", REC)
    check("3. complete: --dry-run also reports already promoted", rc == 0 and "already promoted" in out, out[-200:])

    # ---- 4. the archive: missing, partial, corrupt -------------------------------------------------------------------------------
    BACK = os.path.join(REPO, "archive_backup"); shutil.copytree(ARCHD, BACK)
    def restore():
        shutil.rmtree(ARCHD, ignore_errors=True); shutil.copytree(BACK, ARCHD)
    def all_refuse(tag):
        res = {"check": run("--check"), "check_promoted": run("--check-promoted", "--review", REC), "retry": run("--review", REC),
               "build_check": run("--check", script="build_v17.py")}
        ok = all(r_[0] == 3 and "no authenticated v16 base" in r_[1] for r_ in res.values())
        check(f"4. {tag}: --check, --check-promoted, the retry and build_v17.py --check all refuse (no authenticated v16 base)", ok,
              {k: (v[0], v[1][-160:]) for k, v in res.items() if v[0] != 3 or "no authenticated" not in v[1]})
    shutil.rmtree(ARCHD); before = snapshot(); all_refuse("missing archive")
    check("4. ... and refusing wrote nothing", snapshot() == before); restore()
    os.remove(os.path.join(ARCHD, "prod_launch.py")); all_refuse("partial archive (a member removed)"); restore()
    pa = os.path.join(ARCHD, "prod_authority.py"); open(pa, "a").write("# tampered\n")
    sums = "".join(f"{sha(os.path.join(ARCHD, nm))}  {nm}\n" for nm in sorted(BL.ARCHIVE)); open(os.path.join(ARCHD, "SHA256SUMS"), "w").write(sums)
    json.dump(dict(schema=BL.ARCH_SCHEMA, sha256sums=sha_b(sums.encode()), lengau_sha256sums="0" * 64), open(os.path.join(ARCHD, "COMPLETE"), "w"))
    all_refuse("corrupt archive (a member changed, SHA256SUMS and COMPLETE regenerated around it)"); restore()
    s_ = open(os.path.join(ARCHD, "SHA256SUMS")).read(); open(os.path.join(ARCHD, "SHA256SUMS"), "w").write(s_.replace(s_[:8], "00000000", 1))
    all_refuse("corrupt archive (a SHA256SUMS digest changed)"); restore()
    c_ = json.load(open(os.path.join(ARCHD, "COMPLETE"))); c_["schema"] = "other"; json.dump(c_, open(os.path.join(ARCHD, "COMPLETE"), "w"))
    all_refuse("corrupt archive (COMPLETE of another schema)"); restore()
    open(os.path.join(ARCHD, "extra.json"), "w").write("{}"); all_refuse("archive with an extra file"); restore()
    check("4. the restored archive verifies again (complete state passes)", run("--check-promoted", "--review", REC)[0] == 0)

    # ---- 5. the review's case (b): v17 controls with a changed adoption ---------------------------------------------------------
    good_ad = open(ADOPT_P, "rb").read()
    ad = json.loads(good_ad); ad["by"] = "someone else"; open(ADOPT_P, "w").write(json.dumps(ad, indent=1) + "\n")
    rc, out = run("--check-promoted", "--review", REC)
    rc2, out2 = run("--review", REC)
    rc3, out3 = run("--check")
    check("5. exact v17 controls with a CHANGED adoption: --check-promoted and the retry refuse on the adoption record; --check (no state claim) passes",
          rc == 3 and rc2 == 3 and "adoption record is neither" in out and "adoption record is neither" in out2 and rc3 == 0, (out[-200:], out2[-200:]))
    open(ADOPT_P, "wb").write(good_ad)
    check("5. restored: --check-promoted passes again", run("--check-promoted", "--review", REC)[0] == 0)
    sys.path.remove(os.path.join(P, "chpc", "candidate_v17"))

# ---- 6. the live tree is untouched -----------------------------------------------------------------------------------------------
LIVE_AFTER = {rel: (sha(os.path.join(T1, rel)) if os.path.isfile(os.path.join(T1, rel)) else None) for rel in LIVE_BEFORE}
check("6. the live tree is untouched: controls, adoption and every promoted path hold the same bytes; no archive was created there",
      LIVE_AFTER == LIVE_BEFORE and not os.path.exists(os.path.join(T1, BL.ARCH)))
shutil.rmtree(REPO, ignore_errors=True)
print(f"\n{n[0] - len(fails)} passed, {len(fails)} failed" + (": " + "; ".join(fails) if fails else ""))
sys.exit(1 if fails else 0)
