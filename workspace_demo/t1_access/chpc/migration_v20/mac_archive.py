"""migration_v20: the Mac v19_before_v20 archive chpc/results/archive/row19_screen_v19_before_v20/ - its exact inventory, staged
construction and completion certificate (the migration_v19 mac_archive.py, re-pointed). Used by archive_v19.sh (build, verify)
and v20_package.py check-promoted (deploy and every later step). promote_v20.py reads the SAME archive through the builder's
own check (build_v20.archive_problems).

    python3 chpc/migration_v20/mac_archive.py build <lengau SHA256SUMS sha256> <lengau budget sha256>   (from workspace_demo/t1_access)
    python3 chpc/migration_v20/mac_archive.py verify [--get lengau_sha256sums]

The inventory is build_v20.ARCHIVE itself (9 members: the v19 bytes of the two replaced controllers - the partition module
eabf50c3 and the admission 27e066c7 - and of the replaced Mac authority prod_authority.py ba726a19, the v19 controls 111c3107
and adoption record 2b9f3c78, the adopted v19 pilot qualification e123d6e5 and its operator pilot record 26aa4f8d, the
committed budget phases and the RETAINED captured node document of refit job 54, 730ea262), plus SHA256SUMS (`sha256  name`,
sorted, those 9) and COMPLETE, a JSON certificate written last:
    {"budget": <the budget member's sha256>, "lengau_sha256sums": <the Lengau archive's SHA256SUMS digest>,
     "schema": "row19-screen-mac-archive-v19-before-v20-1", "sha256sums": <the digest of SHA256SUMS>}
(build_v20.archive_problems reads COMPLETE as JSON and requires schema and sha256sums). Every member carries its fixed v19
digest (the budget: its committed bytes, which must equal the budget the Lengau archive certifies). Every file is read-only. A
missing, extra, substituted, writable or malformed entry, a staging directory left by an interrupted build, or an archive the
builder's archive_problems does not accept refuses; nothing is ever overwritten or removed."""
import glob, hashlib, json, os, re, stat, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, "..", ".."))
BUILDER = "chpc/candidate_v20_handback/build_v20.py"
BUILDER_SHA = "6e82bb13d1e7015866eeccecc7171b0107c42e734c1b434a97f35d4133f40999"
N_MEMBERS = 9
LINE = re.compile(r"^([0-9a-f]{64})  ([A-Za-z0-9._-]+)$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class Refuse(Exception):
    pass


def builder():
    """build_v20 (the pinned bytes only): its ARCHIVE, ARCH, ARCH_SCHEMA and archive_problems are the inventory."""
    p = os.path.join(T1, BUILDER)
    if not os.path.isfile(p) or hashlib.sha256(open(p, "rb").read()).hexdigest() != BUILDER_SHA:
        raise Refuse("%s is not the pinned builder %s" % (BUILDER, BUILDER_SHA[:8]))
    sys.path.insert(0, os.path.dirname(p))
    try:
        import build_v20 as B
    finally:
        sys.path.pop(0)
    if len(B.ARCHIVE) != N_MEMBERS:
        raise Refuse("the builder's archive inventory is not the %d members" % N_MEMBERS)
    return B


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
    run = lambda *a: subprocess.run(["git", *a], cwd=T1, capture_output=True).returncode
    return run("ls-files", "--error-unmatch", "--", rel) == 0 and run("diff", "--quiet", "HEAD", "--", rel) == 0


def leftovers(B):
    return sorted(glob.glob(os.path.join(T1, os.path.dirname(B.ARCH), "." + os.path.basename(B.ARCH) + ".staging*")))


def sums_text(d):
    return "".join("%s  %s\n" % (d[k], k) for k in sorted(d))


def complete_bytes(B, sums_sha, budget, lengau_sums):
    return (json.dumps({"schema": B.ARCH_SCHEMA, "sha256sums": sums_sha, "budget": budget, "lengau_sha256sums": lengau_sums},
                       indent=1, sort_keys=True) + "\n").encode()


def verify_dir(B, A, final=True):
    """The identities of a complete Mac archive at A, or Refuse. final: A is the published path (also the builder's view)."""
    if not os.path.isdir(A) or os.path.islink(A):
        raise Refuse("%s does not exist as a real directory (run archive_v19.sh first)" % os.path.relpath(A, T1))
    names = set(os.listdir(A))
    want = set(B.ARCHIVE) | {"SHA256SUMS", "COMPLETE"}
    if names != want:
        raise Refuse("%s holds %d entries, not exactly the %d members + SHA256SUMS + COMPLETE (missing %s, extra %s)" % (
            B.ARCH, len(names), N_MEMBERS, sorted(want - names), sorted(names - want)))
    for n in sorted(names):
        if os.lstat(os.path.join(A, n)).st_mode & 0o222:
            raise Refuse("%s/%s is writable (unfinished or altered)" % (B.ARCH, n))
    sb = read_regular(os.path.join(A, "SHA256SUMS")); txt = sb.decode("utf-8", "replace")
    if not txt.endswith("\n"):
        raise Refuse("SHA256SUMS does not end with a newline")
    got = {}
    for ln in txt[:-1].split("\n"):
        m = LINE.match(ln)
        if not m or m.group(2) in got:
            raise Refuse("SHA256SUMS has a malformed or duplicate line %r" % ln[:80])
        got[m.group(2)] = m.group(1)
    if sorted(got) != sorted(B.ARCHIVE) or txt != sums_text(got):
        raise Refuse("SHA256SUMS does not list exactly the %d members, sorted" % N_MEMBERS)
    for name, (_src, pin) in B.ARCHIVE.items():
        if sha(read_regular(os.path.join(A, name))) != got[name]:
            raise Refuse("%s/%s does not match SHA256SUMS" % (B.ARCH, name))
        if pin and got[name] != pin:
            raise Refuse("%s/%s is not the adopted v19 bytes %s" % (B.ARCH, name, pin[:8]))
    cb = read_regular(os.path.join(A, "COMPLETE"))
    try:
        comp = json.loads(cb.decode())
    except ValueError:
        raise Refuse("%s/COMPLETE is not JSON (an interrupted or foreign archive)" % B.ARCH)
    if not isinstance(comp, dict) or sorted(comp) != ["budget", "lengau_sha256sums", "schema", "sha256sums"] \
            or comp["schema"] != B.ARCH_SCHEMA or not all(HEX64.match(str(comp[k])) for k in ("budget", "lengau_sha256sums", "sha256sums")):
        raise Refuse("%s/COMPLETE is missing or malformed" % B.ARCH)
    if comp["sha256sums"] != sha(sb) or comp["budget"] != got["row19_screen_budget.json"]:
        raise Refuse("%s/COMPLETE does not certify this SHA256SUMS and budget" % B.ARCH)
    if cb != complete_bytes(B, comp["sha256sums"], comp["budget"], comp["lengau_sha256sums"]):
        raise Refuse("%s/COMPLETE is not in its canonical form" % B.ARCH)
    if final:
        why = B.archive_problems()                  # the reviewed promoter's own view of the same archive
        if why:
            raise Refuse("build_v20.archive_problems refuses the archive: %s" % why[:3])
    return comp


def problems():
    """[] when the Mac archive is complete and certified (and no interrupted build is left); else the reasons."""
    try:
        B = builder()
        if leftovers(B):
            raise Refuse("an interrupted Mac archive build left %s; inspect it by hand" % [os.path.relpath(x, T1) for x in leftovers(B)])
        verify_dir(B, os.path.join(T1, B.ARCH)); return []
    except Refuse as e:
        return [str(e)]


def build(lengau_sums, lengau_budget):
    B = builder()
    for x, what in ((lengau_sums, "SHA256SUMS digest"), (lengau_budget, "budget digest")):
        if not HEX64.match(x):
            raise Refuse("the Lengau archive %s %r is not 64 hex" % (what, x))
    A = os.path.join(T1, B.ARCH)
    if os.path.lexists(A):
        raise Refuse("%s already exists; not overwriting" % B.ARCH)
    if leftovers(B):
        raise Refuse("an interrupted Mac archive build left %s; inspect it by hand" % [os.path.relpath(x, T1) for x in leftovers(B)])
    if not committed(B.ARCHIVE["row19_screen_budget.json"][0]):
        raise Refuse("chpc/row19_screen_budget.json is not git-tracked and unmodified")
    data = {}
    for name, (src, pin) in B.ARCHIVE.items():
        b = read_regular(os.path.join(T1, src))
        if pin and sha(b) != pin:
            raise Refuse("%s is not the adopted v19 bytes %s" % (src, pin[:8]))
        data[name] = b
    if sha(data["row19_screen_budget.json"]) != lengau_budget:
        raise Refuse("the Mac committed budget phases (%s) are not the controller clone's archived budget (%s)" % (
            sha(data["row19_screen_budget.json"])[:16], lengau_budget[:16]))
    if not os.path.isdir(os.path.dirname(A)):
        os.makedirs(os.path.dirname(A))
    stg = os.path.join(os.path.dirname(A), ".%s.staging.%d" % (os.path.basename(A), os.getpid()))
    os.mkdir(stg)
    sums = {}
    for name, b in data.items():
        with open(os.path.join(stg, name), "xb") as fh:
            fh.write(b); fh.flush(); os.fsync(fh.fileno())
        if sha(read_regular(os.path.join(stg, name))) != sha(b) or sha(read_regular(os.path.join(T1, B.ARCHIVE[name][0]))) != sha(b):
            raise Refuse("copy of %s did not verify or the source changed (staging %s kept)" % (name, stg))
        sums[name] = sha(b)
    sb = sums_text(sums).encode()
    with open(os.path.join(stg, "SHA256SUMS"), "xb") as fh:
        fh.write(sb)
    with open(os.path.join(stg, "COMPLETE"), "xb") as fh:
        fh.write(complete_bytes(B, sha(sb), sums["row19_screen_budget.json"], lengau_sums))
    for n in os.listdir(stg):
        os.chmod(os.path.join(stg, n), 0o444)
    verify_dir(B, stg, final=False)
    if os.path.lexists(A):
        raise Refuse("%s appeared during the build; staging %s kept" % (B.ARCH, stg))
    os.rename(stg, A)
    return verify_dir(B, A)


def main(argv):
    try:
        if len(argv) == 3 and argv[0] == "build":
            comp = build(argv[1], argv[2])
        elif argv in (["verify"], ["verify", "--get", "lengau_sha256sums"]):
            why = problems()
            if why:
                raise Refuse(why[0])
            B = builder(); comp = verify_dir(B, os.path.join(T1, B.ARCH))
            if len(argv) == 3:
                print(comp["lengau_sha256sums"]); return 0
        else:
            print("usage: mac_archive.py build <lengau SHA256SUMS sha256> <lengau budget sha256> | verify [--get lengau_sha256sums]"); return 2
    except Refuse as e:
        print("REFUSED: Mac archive: %s" % e); return 3
    B = builder()
    print("Mac archive %s verifies: %d members, SHA256SUMS %s, budget %s, Lengau SHA256SUMS %s; build_v20.archive_problems: []" % (
        B.ARCH, N_MEMBERS, comp["sha256sums"][:16], comp["budget"][:16], comp["lengau_sha256sums"][:16]))
    for name in sorted(B.ARCHIVE):
        print("  %s" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
