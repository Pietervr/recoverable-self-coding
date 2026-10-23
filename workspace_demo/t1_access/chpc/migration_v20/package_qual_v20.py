"""migration_v20 step 8.3 (Mac): package the REGENERATED v20 pilot qualification for the operator pilot record, on the
chpc/migration_v19/package_qual_v19.py pattern. Writes ONLY chpc/qualification_v20_<qsha8>/ (staged, verified, then renamed into
place; every file read-only). Commit it with explicit paths and write the operator pilot record carrying
    ADOPT row19-screen-pilot role=refit qualification=<qsha> max_job=100

    python3 chpc/migration_v20/package_qual_v20.py [--dry-run]           (from workspace_demo/t1_access)

Refuses unless the Mac qualified_refit_job1.json (written by the ONE metadata-only `--qualify 1` call) is NOT any earlier
pilot qualification (v19 e123d6e5, v18 530df9a2, v17 8fdbf48e, v16 2c7a7ef1, v15 3c605514), is a refit qualification of job 1 from production evidence with
an alarm-free receipt, and its verifier document (in the receipts folder) reports generation 20 with the v20 controls
4e64982b. The package holds exactly:
  qualified_refit_job1.json                            the regenerated qualification
  verify_refit_<stamp>.json                            the verifier document it names (bytes = its bound digest)
  watch_refit_<stamp>.json (each)                      the receipt the --qualify call published, and every watch receipt the
                                                       qualification names
  mac_archive_v19_before_v20.SHA256SUMS                the Mac archive's SHA256SUMS
  lengau_archive_v19_before_v20.SHA256SUMS.txt         the Lengau archive's SHA256SUMS (kept on the Mac by archive_v19.sh)
  SHA256SUMS                                           `sha256  name` of the files above, sorted
A re-run on an existing package that verifies with exactly these bytes reports it and writes nothing; anything else refuses."""
import argparse, hashlib, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, "..", ".."))
REC = os.path.join(T1, "chpc", "results", "row19_screen", "receipts")
QUAL = os.path.join(REC, "qualified_refit_job1.json")
OLD_QUALS = {"e123d6e5d136dfda31ac5f61dd18a2cce31ecc8dea9f1ad27be73d427cc50b02": "v19 e123d6e5",
             "530df9a208eb1578282ef564708447fd3b32c5fa1366f388f51059ebcfd70839": "v18 530df9a2",
             "8fdbf48e998e39a8c0b12900d75e3dfaf4ab64396ade08a17a5cab549c0b5faa": "v17 8fdbf48e",
             "2c7a7ef1fb903cf0fa75701d2a56d216e98faf14e6638da891afd8bed0bfea44": "v16 2c7a7ef1"}
OLD_PREFIX = {"3c605514": "v15 3c605514"}
V20_CONTROLS = "4e64982befebb3106019f99aa58bb012487f944c7ca59edb906c688e493adf6c"
MAC_SUMS = os.path.join(T1, "chpc", "results", "archive", "row19_screen_v19_before_v20", "SHA256SUMS")
LENGAU_SUMS = os.path.join(T1, "chpc", "results", "archive", "row19_screen_v19_before_v20.lengau_SHA256SUMS.txt")
WATCH = re.compile(r"watch_refit_\d{8}T\d{6}Z\.json")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def plan():
    """(qsha, {package name: source path}, problems)."""
    why = []
    if not os.path.isfile(QUAL):
        return None, {}, ["no Mac %s (run the ONE --qualify 1 call first)" % os.path.relpath(QUAL, T1)]
    qsha = sha(QUAL)
    old = OLD_QUALS.get(qsha) or OLD_PREFIX.get(qsha[:8])
    if old:
        return qsha, {}, ["the Mac qualification is still the %s (not regenerated under v20)" % old]
    q = json.load(open(QUAL))
    rcpt = q.get("receipt") or {}
    if q.get("role") != "refit" or q.get("qualified_job") != 1 or q.get("production") is not True:
        why.append("the qualification is not a production refit qualification of job 1")
    if rcpt.get("alarms") != [] or rcpt.get("fresh") is not True or rcpt.get("production") is not True:
        why.append("the qualification's receipt is not fresh, production and alarm-free")
    vf = q.get("verify_file")
    files = {"qualified_refit_job1.json": QUAL}
    if not isinstance(vf, str) or "/" in vf or not os.path.isfile(os.path.join(REC, vf)):
        why.append("the qualification names no retained verifier document")
    else:
        vp = os.path.join(REC, vf); files[vf] = vp
        if (q.get("bound") or {}).get("verify_file_sha256") not in (None, sha(vp)):
            why.append("the verifier document %s is not the bytes the qualification binds" % vf)
        g = (json.load(open(vp)) or {}).get("generation") or {}
        if not (g.get("version") == 20 and g.get("latest") == 20 and g.get("controls_problem") == "" and g.get("controls_sha256") == V20_CONTROLS):
            why.append("the verifier generation is not v20 (version %r, controls %s)" % (g.get("version"), str(g.get("controls_sha256"))[:12]))
        own = "watch_refit_" + vf[len("verify_refit_"):] if vf.startswith("verify_refit_") else None
        if own:
            if not os.path.isfile(os.path.join(REC, own)):
                why.append("the receipt the --qualify call published (%s) is missing" % own)
            else:
                files[own] = os.path.join(REC, own)
    for n in sorted(set(WATCH.findall(open(QUAL).read()))):
        if not os.path.isfile(os.path.join(REC, n)):
            why.append("the qualification names %s, which is not in %s" % (n, os.path.relpath(REC, T1)))
        else:
            files[n] = os.path.join(REC, n)
    for name, p in (("mac_archive_v19_before_v20.SHA256SUMS", MAC_SUMS), ("lengau_archive_v19_before_v20.SHA256SUMS.txt", LENGAU_SUMS)):
        if not os.path.isfile(p):
            why.append("%s is missing (archive_v19.sh)" % os.path.relpath(p, T1))
        else:
            files[name] = p
    return qsha, files, why


def sums_text(d):
    return "".join("%s  %s\n" % (d[k], k) for k in sorted(d))


def verify(dst, files):
    names = sorted(os.listdir(dst))
    if names != sorted(list(files) + ["SHA256SUMS"]):
        return "%s holds %s, not exactly the package" % (os.path.relpath(dst, T1), names)
    want = {n: sha(p) for n, p in files.items()}
    if open(os.path.join(dst, "SHA256SUMS")).read() != sums_text(want):
        return "SHA256SUMS is not the package's"
    for n, h in want.items():
        if sha(os.path.join(dst, n)) != h:
            return "%s is not its source bytes" % n
    return ""


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args(argv)
    qsha, files, why = plan()
    if why:
        print("PACKAGE REFUSED:"); [print("  -", w) for w in why]; return 3
    dst = os.path.join(T1, "chpc", "qualification_v20_%s" % qsha[:8])
    if os.path.lexists(dst):
        w = verify(dst, files)
        if w:
            print("PACKAGE REFUSED: %s exists and does not verify (%s); not overwriting" % (os.path.relpath(dst, T1), w)); return 3
        print("package exists and verifies: %s (%d files + SHA256SUMS); qualification %s" % (os.path.relpath(dst, T1), len(files), qsha)); return 0
    stg = dst + ".staging.%d" % os.getpid()
    if [n for n in os.listdir(os.path.dirname(dst)) if n.startswith(os.path.basename(dst) + ".staging")]:
        print("PACKAGE REFUSED: an interrupted build left a staging directory beside %s; inspect it by hand" % os.path.relpath(dst, T1)); return 3
    if a.dry_run:
        print("DRY RUN - would write %s:" % os.path.relpath(dst, T1)); [print("  -", n) for n in sorted(files)]; return 0
    os.mkdir(stg)
    for n, p in files.items():
        shutil.copyfile(p, os.path.join(stg, n))
    with open(os.path.join(stg, "SHA256SUMS"), "w") as fh:
        fh.write(sums_text({n: sha(p) for n, p in files.items()}))
    w = verify(stg, files)
    if w:
        print("PACKAGE REFUSED: the staged package does not verify (%s); staging kept" % w); return 3
    for n in os.listdir(stg):
        os.chmod(os.path.join(stg, n), 0o444)
    os.rename(stg, dst)
    print("packaged %s: %d files + SHA256SUMS; qualification %s" % (os.path.relpath(dst, T1), len(files), qsha))
    print("operator pilot record literal: ADOPT row19-screen-pilot role=refit qualification=%s max_job=100" % qsha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
