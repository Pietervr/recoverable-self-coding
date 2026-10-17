"""migration_v16: the Lengau v15_before_v16 recovery archive - its mandatory inventory, its staged construction and its
completion certificate. lengau.sh embeds this file in every Lengau script and remote_lib.sh runs it through $T/t1py:

    inventory <T>          every required source exists, is a regular file and carries its v15 identity (read only)
    build <T> <ctl_head>   stage, verify, then publish $T/archive_screen/v15_before_v16 atomically (refuses any existing one)
    verify <T> [--get k]   the complete certificate: exact inventory, every digest, COMPLETE; prints k (ctl_head, review,
                           qualification, sha256sums) when asked

The archive (all files read-only):
    ctl/HEAD.txt                       the controller clone's HEAD (40 hex)
    ctl/<repo path>                    every file the adopted v15 entry pins, plus REQUIRED_CTL below, from rsc_screen_ctl
    ctl/untracked/<path>               the three pinned UNTRACKED evidence files of rsc_screen_ctl (UNTRACKED_CTL below, the
                                       same allowlist as remote_lib.sh CTL_EVIDENCE), each with exactly its pinned sha256
    gate/...                           the WHOLE gate (regular files only), listed by INVENTORY.gate as captured from the source
    jobs/row19_screen_refit_*          the refit job scripts, listed by INVENTORY.jobs (at least one)
    ledger/row19_screen_campaign_budget.json   the campaign ledger (a reference copy)
    INVENTORY.gate, INVENTORY.jobs     `sha256  ./path` lines captured from the sources before copying
    SHA256SUMS                         `sha256  ./path` for every file except SHA256SUMS and COMPLETE, sorted
    COMPLETE                           written last: schema, the SHA256SUMS digest, ctl_head, qualification, review
A missing, extra, substituted, malformed or unfinished entry fails verify; a staging directory left by an interrupted build
is reported and never overwritten or removed."""
import glob, hashlib, json, os, re, stat, sys

V15_CONTROLS = "828d3b69707cc47340c1773b97450c2c17c95679c4daf93c84021d138a4663a5"
V15_ADOPTION = "970c29f5fc7832f9ef23d20ecf6ae40e9a8808d99ee0aad5a6e9fe109e4f8f2d"
V15_ADMIT = "ac06e803fdb1b3fdb11652017d8d1808f4ace880b8b2bb22463c3694e646d2ac"
V15_STATUS = "0effcba3977b1d7e76347a4082020633bceaf9ddeec0b05d4255aa9d7b93671b"
V15_QUAL = "3c605514fb36d6d9f67a2835adf516fa30298caa10c20411bbcbcff74c94592c"
SCHEMA = "row19-screen-archive-v15-before-v16-1"
CTL_REL = "rsc_screen_ctl/workspace_demo/t1_access"
REQUIRED_CTL = {"chpc/row19_screen_controls.json": V15_CONTROLS, "chpc/row19_screen_controls_adoption.json": V15_ADOPTION,
                "chpc/row19_screen_admit.py": V15_ADMIT, "chpc/row19_screen_status.py": V15_STATUS,
                "chpc/row19_screen_budget.json": None, "chpc/row19_screen_manifest.json": None,
                "chpc/row22_bank_status.py": None, "chpc/row22_bank_submit.py": None}
# the controller clone's pinned untracked evidence (live preflight 17 Oct 2026; row-23 bench comparator / EC2 qualification permit
# copies written 12 Oct 18:39, not controller authority): mandatory archive members, each with exactly its pinned digest
UNTRACKED_CTL = {"aws_ec2/ec2_release_state.json": "80ba0ac599f617f8c0ee020d75e7c53dcd30c519d783a76dcb6a2f6b9f1a1d39",
                 "aws_ec2/runs/b2/bench_report_attempt_5_20261011T185715Z.json":
                     "154511e687f006001888970bd3d65398b6b37c910221378b7f6c3c63fe63e3a4",
                 "reviews/2026-10-11_d1d2_f3_codex_record.md": "636f1e77089578a14ee837bf95fe0f86cc84dbc907f8ced918256b69dbb55c1e"}
UNTRACKED_PREFIX = "untracked/"
TOP = {"COMPLETE", "SHA256SUMS", "INVENTORY.gate", "INVENTORY.jobs", "ctl", "gate", "jobs", "ledger"}
LEDGER = "ledger/row19_screen_campaign_budget.json"
LINE = re.compile(r"^([0-9a-f]{64})  \./([A-Za-z0-9._+=@,:~-]+(?:/[A-Za-z0-9._+=@,:~-]+)*)$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")


class Refuse(Exception):
    pass


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


ROOT = None     # the physical toolchain root, set by main(); every source and destination must be canonical beneath it


def canon(p, what):
    """Containment (Codex re-review 2026-10-17, P2): p is its OWN physical path - absolute, lexically clean, no symlink or alias
    in any existing component - strictly beneath the toolchain root, and never in the scientific job clone. Checked for every
    source immediately before it is read and for every destination immediately before it is written."""
    if ROOT is None:
        raise Refuse("internal: the toolchain root is not set")
    if not os.path.isabs(p) or os.path.normpath(p) != p or os.path.realpath(p) != p:
        raise Refuse("%s %s is not its own physical path (a symlink, alias or unclean name in it); refusing" % (what, p))
    if not p.startswith(ROOT + os.sep):
        raise Refuse("%s %s is not beneath the toolchain root %s; refusing" % (what, p, ROOT))
    job = os.path.join(ROOT, "rsc_screen")
    if p == job or p.startswith(job + os.sep):
        raise Refuse("%s %s is inside the scientific job clone; refusing" % (what, p))
    return p


def read_regular(p, what="source"):
    """The bytes of a contained, regular, non-symlink file; anything else refuses."""
    canon(p, what)
    try:
        st = os.lstat(p)
    except OSError as e:
        raise Refuse("missing: %s (%s)" % (p, e))
    if not stat.S_ISREG(st.st_mode):
        raise Refuse("not a regular file (symlink or special): %s" % p)
    try:
        fd = os.open(p, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError as e:
        raise Refuse("unreadable: %s (%s)" % (p, e))
    with os.fdopen(fd, "rb") as fh:
        if not stat.S_ISREG(os.fstat(fh.fileno()).st_mode):
            raise Refuse("not a regular file (special): %s" % p)
        return fh.read()


def paths(T):
    return {"C": os.path.join(T, CTL_REL), "G": os.path.join(T, "row19_screen", "gate"), "jobs": os.path.join(T, "jobs"),
            "ledger": os.path.join(T, "row19_screen_campaign", "budget.json"),
            "parent": os.path.join(T, "archive_screen"), "A": os.path.join(T, "archive_screen", "v15_before_v16")}


def ctl_inventory(controls_bytes):
    """{repo path: required sha or None} for the controller files: REQUIRED_CTL plus every v15 pin."""
    if sha_bytes(controls_bytes) != V15_CONTROLS:
        raise Refuse("the controller controls are not the adopted v15 bytes 828d3b69")
    v = json.loads(controls_bytes.decode())["versions"][-1]
    if v.get("version") != 15 or not isinstance(v.get("files"), dict) or not v["files"]:
        raise Refuse("the adopted controls' latest entry is not version 15 with pinned files")
    inv = dict(REQUIRED_CTL)
    for f, hsh in v["files"].items():
        if not isinstance(hsh, str) or not re.match(r"^[0-9a-f]{64}$", hsh) or f.startswith("/") or ".." in f.split("/") \
                or f.startswith(UNTRACKED_PREFIX) or f in UNTRACKED_CTL:
            raise Refuse("malformed v15 pin %r" % f)
        if inv.get(f) not in (None, hsh):
            raise Refuse("v15 pin for %s disagrees with the adopted identity" % f)
        inv[f] = hsh
    return inv


def walk_files(root, label):
    """Sorted relative paths of every regular file below root; a symlink or special file refuses."""
    out = []
    canon(root, label)
    if not os.path.isdir(root) or os.path.islink(root):
        raise Refuse("%s %s is not a real directory" % (label, root))
    for d, dirs, files in os.walk(root, followlinks=False):
        for n in dirs + files:
            p = os.path.join(d, n); m = os.lstat(p).st_mode
            if stat.S_ISDIR(m):
                continue
            if not stat.S_ISREG(m):
                raise Refuse("%s holds a symlink or special file: %s" % (label, p))
            out.append(os.path.relpath(p, root))
    return sorted(out)


def sources(T):
    """Every archive member as (archive path, source path, required sha or None); refuses an incomplete source set."""
    P = paths(T); mem = []
    controls = read_regular(os.path.join(P["C"], "chpc/row19_screen_controls.json"))
    for f, want in sorted(ctl_inventory(controls).items()):
        mem.append(("ctl/" + f, os.path.join(P["C"], f), want))
    for f, want in sorted(UNTRACKED_CTL.items()):
        mem.append(("ctl/" + UNTRACKED_PREFIX + f, os.path.join(P["C"], f), want))
    gate = walk_files(P["G"], "the gate")
    for need in ("qualified_refit_job1.json", "review_refit.json"):
        if need not in gate:
            raise Refuse("the gate has no %s" % need)
    for f in gate:
        mem.append(("gate/" + f, os.path.join(P["G"], f), V15_QUAL if f == "qualified_refit_job1.json" else None))
    canon(P["C"], "the controller clone"); canon(P["jobs"], "the job-script directory")
    jobs = sorted(glob.glob(os.path.join(P["jobs"], "row19_screen_refit_*")))
    if not jobs:
        raise Refuse("no refit job scripts %s/row19_screen_refit_*" % P["jobs"])
    for j in jobs:
        mem.append(("jobs/" + os.path.basename(j), j, None))
    mem.append((LEDGER, P["ledger"], None))
    for a, _, _ in mem:
        if not LINE.match("0" * 64 + "  ./" + a):
            raise Refuse("an archive member name is not portable: %r" % a)
    return mem


def inventory(T):
    mem = sources(T); n = 0
    for a, src, want in mem:
        b = read_regular(src)
        if want and sha_bytes(b) != want:
            raise Refuse("%s is not its v15 identity %s" % (src, want[:8]))
        n += 1
    print("archive sources complete: %d files (ctl %d incl. %d pinned untracked evidence, gate %d, jobs %d, ledger 1)" % (
        n, sum(a.startswith("ctl/") for a, _, _ in mem), len(UNTRACKED_CTL), sum(a.startswith("gate/") for a, _, _ in mem),
        sum(a.startswith("jobs/") for a, _, _ in mem)))


def parse_sums(text, what):
    out = {}; prev = None
    lines = text.split("\n")
    if not text.endswith("\n") or lines[-1] != "":
        raise Refuse("%s does not end with a newline" % what)
    for ln in lines[:-1]:
        m = LINE.match(ln)
        if not m:
            raise Refuse("%s has a malformed line %r" % (what, ln[:80]))
        if m.group(2) in out or (prev is not None and m.group(2) <= prev):
            raise Refuse("%s is not strictly sorted and unique at %s" % (what, m.group(2)))
        out[m.group(2)] = m.group(1); prev = m.group(2)
    return out


def sums_text(d):
    return "".join("%s  ./%s\n" % (d[k], k) for k in sorted(d))


def complete_text(sums_sha, head, qual, review):
    return "schema %s\nsha256sums %s\nctl_head %s\nqualification %s\nreview %s\n" % (SCHEMA, sums_sha, head, qual, review)


def verify(A):
    """The complete certificate of archive directory A; returns its identities or raises Refuse."""
    canon(A, "the archive")
    if not os.path.isdir(A) or os.path.islink(A):
        raise Refuse("%s is not a real directory" % A)
    top = set(os.listdir(A))
    if top != TOP:
        raise Refuse("archive top level is %s, not exactly %s" % (sorted(top), sorted(TOP)))
    files = walk_files(A, "the archive")
    for f in files:
        if os.lstat(os.path.join(A, f)).st_mode & 0o222:
            raise Refuse("archive file is writable (unfinished or altered): %s" % f)
    sums_b = read_regular(os.path.join(A, "SHA256SUMS"))
    sums = parse_sums(sums_b.decode("utf-8", "replace"), "SHA256SUMS")
    listed = set(files) - {"SHA256SUMS", "COMPLETE"}
    if set(sums) != listed:
        raise Refuse("SHA256SUMS does not list exactly the archived files (missing %s, extra %s)" % (
            sorted(listed - set(sums))[:3], sorted(set(sums) - listed)[:3]))
    for f in sorted(listed):
        if sha_bytes(read_regular(os.path.join(A, f))) != sums[f]:
            raise Refuse("%s does not match SHA256SUMS" % f)
    comp = read_regular(os.path.join(A, "COMPLETE")).decode("utf-8", "replace")
    m = re.match(r"^schema (\S+)\nsha256sums ([0-9a-f]{64})\nctl_head ([0-9a-f]{40})\nqualification ([0-9a-f]{64})\nreview ([0-9a-f]{64})\n$", comp)
    if not m or m.group(1) != SCHEMA:
        raise Refuse("COMPLETE is missing or malformed")
    ident = {"sha256sums": m.group(2), "ctl_head": m.group(3), "qualification": m.group(4), "review": m.group(5)}
    if ident["sha256sums"] != sha_bytes(sums_b):
        raise Refuse("COMPLETE does not certify this SHA256SUMS")
    head = read_regular(os.path.join(A, "ctl/HEAD.txt")).decode("utf-8", "replace")
    if head != ident["ctl_head"] + "\n":
        raise Refuse("ctl/HEAD.txt is not the certified controller HEAD")
    # the controller inventory, exactly
    inv = ctl_inventory(read_regular(os.path.join(A, "ctl/chpc/row19_screen_controls.json")))
    want_ctl = {"ctl/" + f for f in inv} | {"ctl/HEAD.txt"} | {"ctl/" + UNTRACKED_PREFIX + f for f in UNTRACKED_CTL}
    have_ctl = {f for f in listed if f.startswith("ctl/")}
    if have_ctl != want_ctl:
        raise Refuse("the controller files are not exactly the required set (missing %s, extra %s)" % (
            sorted(want_ctl - have_ctl)[:3], sorted(have_ctl - want_ctl)[:3]))
    for f, want in inv.items():
        if want and sums["ctl/" + f] != want:
            raise Refuse("ctl/%s is not its v15 identity %s" % (f, want[:8]))
    for f, want in UNTRACKED_CTL.items():
        if sums["ctl/" + UNTRACKED_PREFIX + f] != want:
            raise Refuse("ctl/%s%s is not its pinned untracked evidence identity %s" % (UNTRACKED_PREFIX, f, want[:8]))
    # the variable gate and job contents, against the inventories captured from the sources
    for part in ("gate", "jobs"):
        cap = parse_sums(read_regular(os.path.join(A, "INVENTORY." + part)).decode("utf-8", "replace"), "INVENTORY." + part)
        have = {f: sums[f] for f in listed if f.startswith(part + "/")}
        if cap != have:
            raise Refuse("%s/ is not exactly the captured INVENTORY.%s" % (part, part))
        if part == "jobs" and (not have or not all(os.path.basename(f).startswith("row19_screen_refit_") for f in have)):
            raise Refuse("jobs/ holds no refit job script, or another file")
    if sums.get("gate/qualified_refit_job1.json") != V15_QUAL or ident["qualification"] != V15_QUAL:
        raise Refuse("the archived gate qualification is not the adopted v15 3c605514")
    if "gate/review_refit.json" not in sums or sums["gate/review_refit.json"] != ident["review"]:
        raise Refuse("the archived active review is missing or not the certified one")
    if {f for f in listed if f.startswith("ledger/")} != {LEDGER}:
        raise Refuse("ledger/ is not exactly %s" % LEDGER)
    try:
        json.loads(read_regular(os.path.join(A, LEDGER)).decode())
    except ValueError:
        raise Refuse("the archived ledger is not JSON")
    extra = listed - {f for f in listed if f.split("/")[0] in ("ctl", "gate", "jobs", "ledger")} - {"INVENTORY.gate", "INVENTORY.jobs"}
    if extra:
        raise Refuse("unexpected archive members %s" % sorted(extra)[:3])
    ident["files"] = str(len(listed))
    return ident


def leftovers(parent):
    return sorted(glob.glob(os.path.join(parent, ".v15_before_v16.staging*")))


def build(T, head):
    P = paths(T); A = P["A"]
    if not HEX40.match(head):
        raise Refuse("the controller HEAD %r is not a 40-hex commit" % head)
    canon(P["parent"], "the archive parent"); canon(A, "the archive")
    if os.path.lexists(A):
        raise Refuse("%s already exists; not overwriting (verify it instead)" % A)
    if os.path.lexists(P["parent"]) and (os.path.islink(P["parent"]) or not os.path.isdir(P["parent"])):
        raise Refuse("the archive parent %s is not a real directory" % P["parent"])
    os.makedirs(P["parent"], exist_ok=True)
    left = leftovers(P["parent"])
    if left:
        raise Refuse("an interrupted archive build left %s; partial evidence is kept, inspect and recover it by hand" % left)
    mem = sources(T)
    pre = {}
    for a, src, want in mem:                      # every source reads and carries its identity BEFORE anything is staged
        pre[a] = sha_bytes(read_regular(src))
        if want and pre[a] != want:
            raise Refuse("%s is not its v15 identity %s" % (src, want[:8]))
    stg = canon(os.path.join(P["parent"], ".v15_before_v16.staging.%d" % os.getpid()), "the staging directory")
    os.mkdir(stg)
    sums = {}; inv = {"gate": {}, "jobs": {}}
    for a, src, want in mem:
        b = read_regular(src); d = sha_bytes(b)
        if d != pre[a]:
            raise Refuse("%s changed while archiving (staging %s kept)" % (src, stg))
        dst = canon(os.path.join(stg, a), "the staged copy"); canon(os.path.dirname(dst), "the staged parent")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "xb") as fh:
            fh.write(b); fh.flush(); os.fsync(fh.fileno())
        if sha_bytes(read_regular(dst)) != d or sha_bytes(read_regular(src)) != d:
            raise Refuse("copy of %s did not verify, or the source changed while archiving (staging %s kept)" % (src, stg))
        os.utime(dst, ns=(os.lstat(src).st_atime_ns, os.lstat(src).st_mtime_ns))
        sums[a] = d
        if a.split("/")[0] in inv:
            inv[a.split("/")[0]][a] = d
    extra = {"ctl/HEAD.txt": (head + "\n").encode(), "INVENTORY.gate": sums_text(inv["gate"]).encode(),
             "INVENTORY.jobs": sums_text(inv["jobs"]).encode()}
    for a, b in extra.items():
        with open(os.path.join(stg, a), "xb") as fh:
            fh.write(b)
        sums[a] = sha_bytes(b)
    sb = sums_text(sums).encode()
    with open(os.path.join(stg, "SHA256SUMS"), "xb") as fh:
        fh.write(sb)
    review = sums["gate/review_refit.json"]
    with open(os.path.join(stg, "COMPLETE"), "xb") as fh:
        fh.write(complete_text(sha_bytes(sb), head, V15_QUAL, review).encode())
    for d, _, files in os.walk(stg):
        for n in files:
            os.chmod(os.path.join(d, n), 0o444)
    verify(stg)                                   # the whole certificate, before anything is published
    canon(A, "the archive"); canon(stg, "the staging directory")
    if os.path.lexists(A):
        raise Refuse("%s appeared during the build; staging %s kept" % (A, stg))
    os.rename(stg, A)                             # atomic publish on the same file system
    for d, dirs, _ in os.walk(A, topdown=False):
        os.chmod(d, 0o555)
    return verify(A)


def main(argv):
    global ROOT
    try:
        if len(argv) >= 2:
            if not os.path.isabs(argv[1]) or os.path.realpath(argv[1]) != argv[1]:
                raise Refuse("the toolchain root %s is not its own physical path" % argv[1])
            ROOT = argv[1]
        if len(argv) >= 2 and argv[0] == "inventory":
            inventory(argv[1]); return 0
        if len(argv) == 3 and argv[0] == "build":
            ident = build(argv[1], argv[2])
            print("archive built %s: %s files, SHA256SUMS %s, ctl_head %s, review %s" % (
                paths(argv[1])["A"], ident["files"], ident["sha256sums"][:16], ident["ctl_head"][:12], ident["review"][:16]))
            print("sha256sums=%s" % ident["sha256sums"]); return 0
        if len(argv) in (2, 4) and argv[0] == "verify":
            P = paths(argv[1])
            left = leftovers(P["parent"]) if os.path.isdir(P["parent"]) else []
            if left:
                raise Refuse("an interrupted archive build left %s; partial evidence is kept, inspect and recover it by hand" % left)
            ident = verify(P["A"])
            if len(argv) == 4:
                if argv[2] != "--get" or argv[3] not in ident:
                    raise Refuse("verify --get takes one of %s" % sorted(ident))
                print(ident[argv[3]]); return 0
            print("archive verifies %s: %s files, SHA256SUMS %s, ctl_head %s, review %s" % (
                P["A"], ident["files"], ident["sha256sums"][:16], ident["ctl_head"][:12], ident["review"][:16]))
            print("sha256sums=%s" % ident["sha256sums"]); return 0
        print("usage: inventory <T> | build <T> <ctl_head> | verify <T> [--get key]"); return 2
    except Refuse as e:
        print("ABORT: archive: %s" % e); return 1
    except (OSError, ValueError, KeyError, TypeError) as e:
        print("ABORT: archive: %s: %s" % (type(e).__name__, e)); return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
