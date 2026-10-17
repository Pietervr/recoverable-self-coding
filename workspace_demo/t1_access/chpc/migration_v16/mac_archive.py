"""migration_v16: the Mac v15_before_v16 archive chpc/results/archive/row19_screen_v15_before_v16/ - its exact inventory,
staged construction and completion certificate. Used by archive_v15.sh (build, verify) and promote_v16.py / deploy_v16.sh
(verify, through problem()).

    python3 chpc/migration_v16/mac_archive.py build <lengau SHA256SUMS sha256>     (from workspace_demo/t1_access)
    python3 chpc/migration_v16/mac_archive.py verify [--get lengau_sha256sums]

The archive holds EXACTLY the six named files below, SHA256SUMS (`sha256  name`, sorted, those six) and COMPLETE (written last:
schema, the SHA256SUMS digest, the budget-phase digest and the digest of the Lengau archive's SHA256SUMS it was made with).
Five carry fixed v15 identities; row19_screen_budget.json must be git-tracked and unmodified when archived. A missing, extra,
substituted or malformed entry, or a staging directory left by an interrupted build, refuses; nothing is ever overwritten."""
import glob, hashlib, os, re, stat, subprocess, sys

T1 = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ARCH = "chpc/results/archive/row19_screen_v15_before_v16"
QUAL = "chpc/results/row19_screen/receipts/qualified_refit_job1.json"
SOURCES = {   # archive name: (source path, fixed v15 sha256 or None)
    "row19_screen_controls.json": ("chpc/row19_screen_controls.json", "828d3b69707cc47340c1773b97450c2c17c95679c4daf93c84021d138a4663a5"),
    "row19_screen_controls_adoption.json": ("chpc/row19_screen_controls_adoption.json", "970c29f5fc7832f9ef23d20ecf6ae40e9a8808d99ee0aad5a6e9fe109e4f8f2d"),
    "row19_screen_admit.py": ("chpc/row19_screen_admit.py", "ac06e803fdb1b3fdb11652017d8d1808f4ace880b8b2bb22463c3694e646d2ac"),
    "row19_screen_status.py": ("chpc/row19_screen_status.py", "0effcba3977b1d7e76347a4082020633bceaf9ddeec0b05d4255aa9d7b93671b"),
    "row19_screen_budget.json": ("chpc/row19_screen_budget.json", None),
    "qualified_refit_job1.json": (QUAL, "3c605514fb36d6d9f67a2835adf516fa30298caa10c20411bbcbcff74c94592c"),
}
SCHEMA = "row19-screen-mac-archive-v15-before-v16-1"
LINE = re.compile(r"^([0-9a-f]{64})  ([A-Za-z0-9._-]+)$")


class Refuse(Exception):
    pass


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read_regular(p):
    try:
        st = os.lstat(p)
    except OSError as e:
        raise Refuse("missing: %s (%s)" % (os.path.relpath(p, T1), e))
    if not stat.S_ISREG(st.st_mode):
        raise Refuse("not a regular file (symlink or special): %s" % os.path.relpath(p, T1))
    with open(p, "rb") as fh:
        return fh.read()


def committed(rel):
    run = lambda *a: subprocess.run(["git", "-C", T1, *a], capture_output=True).returncode
    return run("ls-files", "--error-unmatch", "--", rel) == 0 and run("diff", "--quiet", "HEAD", "--", rel) == 0


def leftovers():
    return sorted(glob.glob(os.path.join(T1, os.path.dirname(ARCH), "." + os.path.basename(ARCH) + ".staging*")))


def sums_text(d):
    return "".join("%s  %s\n" % (d[k], k) for k in sorted(d))


def verify_dir(A):
    """The identities of a complete Mac archive at A, or Refuse."""
    if not os.path.isdir(A) or os.path.islink(A):
        raise Refuse("%s does not exist as a real directory (run archive_v15.sh first)" % os.path.relpath(A, T1))
    names = set(os.listdir(A))
    want = set(SOURCES) | {"SHA256SUMS", "COMPLETE"}
    if names != want:
        raise Refuse("%s holds %s, not exactly the six named files + SHA256SUMS + COMPLETE (missing %s, extra %s)" % (
            ARCH, len(names), sorted(want - names), sorted(names - want)))
    sb = read_regular(os.path.join(A, "SHA256SUMS")); txt = sb.decode("utf-8", "replace")
    if not txt.endswith("\n"):
        raise Refuse("SHA256SUMS does not end with a newline")
    got = {}
    for ln in txt[:-1].split("\n"):
        m = LINE.match(ln)
        if not m or m.group(2) in got:
            raise Refuse("SHA256SUMS has a malformed or duplicate line %r" % ln[:80])
        got[m.group(2)] = m.group(1)
    if sorted(got) != sorted(SOURCES) or txt != sums_text(got):
        raise Refuse("SHA256SUMS does not list exactly the six named files, sorted")
    for name, (_, pin) in SOURCES.items():
        if sha(read_regular(os.path.join(A, name))) != got[name]:
            raise Refuse("%s/%s does not match SHA256SUMS" % (ARCH, name))
        if pin and got[name] != pin:
            raise Refuse("%s/%s is not the adopted v15 bytes %s" % (ARCH, name, pin[:8]))
    comp = read_regular(os.path.join(A, "COMPLETE")).decode("utf-8", "replace")
    m = re.match(r"^schema (\S+)\nsha256sums ([0-9a-f]{64})\nbudget ([0-9a-f]{64})\nlengau_sha256sums ([0-9a-f]{64})\n$", comp)
    if not m or m.group(1) != SCHEMA:
        raise Refuse("%s/COMPLETE is missing or malformed (an interrupted or foreign archive)" % ARCH)
    if m.group(2) != sha(sb) or m.group(3) != got["row19_screen_budget.json"]:
        raise Refuse("%s/COMPLETE does not certify this SHA256SUMS and budget" % ARCH)
    return {"sha256sums": m.group(2), "budget": m.group(3), "lengau_sha256sums": m.group(4)}


def problem():
    """'' when the Mac archive is complete and certified (and no interrupted build is left); else the reason."""
    try:
        if leftovers():
            raise Refuse("an interrupted Mac archive build left %s; inspect it by hand" % [os.path.relpath(x, T1) for x in leftovers()])
        verify_dir(os.path.join(T1, ARCH)); return ""
    except Refuse as e:
        return str(e)


def build(lengau_sums):
    if not re.match(r"^[0-9a-f]{64}$", lengau_sums):
        raise Refuse("the Lengau archive SHA256SUMS digest %r is not 64 hex" % lengau_sums)
    A = os.path.join(T1, ARCH)
    if os.path.lexists(A):
        raise Refuse("%s already exists; not overwriting" % ARCH)
    if leftovers():
        raise Refuse("an interrupted Mac archive build left %s; inspect it by hand" % [os.path.relpath(x, T1) for x in leftovers()])
    if not committed(SOURCES["row19_screen_budget.json"][0]):
        raise Refuse("chpc/row19_screen_budget.json is not git-tracked and unmodified")
    data = {}
    for name, (src, pin) in SOURCES.items():
        b = read_regular(os.path.join(T1, src))
        if pin and sha(b) != pin:
            raise Refuse("%s is not the adopted v15 bytes %s" % (src, pin[:8]))
        data[name] = b
    os.makedirs(os.path.dirname(A), exist_ok=True)
    stg = os.path.join(os.path.dirname(A), ".%s.staging.%d" % (os.path.basename(A), os.getpid()))
    os.mkdir(stg)
    sums = {}
    for name, b in data.items():
        with open(os.path.join(stg, name), "xb") as fh:
            fh.write(b); fh.flush(); os.fsync(fh.fileno())
        if sha(read_regular(os.path.join(stg, name))) != sha(b) or sha(read_regular(os.path.join(T1, SOURCES[name][0]))) != sha(b):
            raise Refuse("copy of %s did not verify or the source changed (staging %s kept)" % (name, stg))
        sums[name] = sha(b)
    sb = sums_text(sums).encode()
    with open(os.path.join(stg, "SHA256SUMS"), "xb") as fh:
        fh.write(sb)
    with open(os.path.join(stg, "COMPLETE"), "xb") as fh:
        fh.write(("schema %s\nsha256sums %s\nbudget %s\nlengau_sha256sums %s\n" % (
            SCHEMA, sha(sb), sums["row19_screen_budget.json"], lengau_sums)).encode())
    for n in os.listdir(stg):
        os.chmod(os.path.join(stg, n), 0o444)
    verify_dir(stg)
    if os.path.lexists(A):
        raise Refuse("%s appeared during the build; staging %s kept" % (ARCH, stg))
    os.rename(stg, A)
    return verify_dir(A)


def main(argv):
    try:
        if len(argv) == 2 and argv[0] == "build":
            ident = build(argv[1])
        elif argv in (["verify"], ["verify", "--get", "lengau_sha256sums"]):
            why = problem()
            if why:
                raise Refuse(why)
            ident = verify_dir(os.path.join(T1, ARCH))
            if len(argv) == 3:
                print(ident["lengau_sha256sums"]); return 0
        else:
            print("usage: mac_archive.py build <lengau SHA256SUMS sha256> | verify [--get lengau_sha256sums]"); return 2
    except Refuse as e:
        print("REFUSED: Mac archive: %s" % e); return 3
    print("Mac archive %s verifies: 6 files, SHA256SUMS %s, budget %s, Lengau SHA256SUMS %s" % (
        ARCH, ident["sha256sums"][:16], ident["budget"][:16], ident["lengau_sha256sums"][:16]))
    for name in sorted(SOURCES):
        print("  %s" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
