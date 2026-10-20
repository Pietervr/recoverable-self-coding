"""migration_v18: the Lengau v17_before_v18 recovery archive - its mandatory inventory, its staged construction and its
completion certificate (the migration_v17 lengau_archive.py, re-pointed at the adopted v17 state). lengau.sh embeds this file
in every Lengau script and remote_lib.sh runs it through $T/t1py:

    inventory <T>          every required source exists, is a regular file and carries its v17 identity (read only)
    build <T> <ctl_head>   stage, verify, then publish $T/archive_screen/v17_before_v18 atomically (refuses any existing one)
    verify <T> [--get k]   the complete certificate: exact inventory, every digest, COMPLETE; prints k (ctl_head, review,
                           qualification, budget, node_evidence, sha256sums, files) when asked

The archive (all files read-only):
    ctl/HEAD.txt                       the controller clone's HEAD (40 hex)
    ctl/<repo path>                    every file the adopted v17 entry pins, its partition reference (e2 48cea639), the e1
                                       declaration kept as provenance, the v17 controls review record and the v17 pilot record,
                                       and REQUIRED_CTL below, from rsc_screen_ctl
    ctl/untracked/<path>               the three pinned UNTRACKED evidence files of rsc_screen_ctl (UNTRACKED_CTL below, the
                                       same allowlist as remote_lib.sh CTL_EVIDENCE), each with exactly its pinned sha256
    gate/...                           the WHOLE gate (regular files only), listed by INVENTORY.gate as captured from the source:
                                       the adopted v17 pilot qualification 8fdbf48e and its active review among them
    jobs/row19_screen_refit_*          the refit job files, listed by INVENTORY.jobs, which MUST include the retained captured
                                       node document row19_screen_refit_54.nodefail.json at exactly 730ea262
    ledger/row19_screen_campaign_budget.json   the campaign ledger (a point-in-time reference copy, see below)
    ec2/activation_e1.json, ec2/activation_e2.json   both activation proofs (provenance; they stay on the root, unchanged;
                                       epoch 2 stays active through v18)
    INVENTORY.gate, INVENTORY.jobs     `sha256  ./path` lines captured from the sources before copying
    SHA256SUMS                         `sha256  ./path` for every file except SHA256SUMS and COMPLETE, sorted
    COMPLETE                           written last: schema, the SHA256SUMS digest, ctl_head, qualification, review, budget,
                                       node_evidence
A missing, extra, substituted, malformed or unfinished entry fails verify; a staging directory left by an interrupted build
is reported and never overwritten or removed.

The ledger: refit jobs keep running through the migration (jobs 47-56 except the node-failed 54 were live when this was
written) and each job's job-end writes its runner end into the ledger by an atomic replace. The ledger member is therefore
read ONCE (a complete version, never a torn one) and archived as those bytes; unlike every other member it is not re-read from
the source after the copy, so a job ending during the build cannot refuse the archive. It is a reference copy, never a budget
authority. A job ending during the build may also add its PBS .out/.err to $T/jobs; INVENTORY.jobs is the set captured at
the start, so such a file is simply not in this archive (it is not a v17 identity).
Python 3.6-level code (the Lengau-side rule); run by $T/t1py."""
import glob, hashlib, json, os, re, stat, sys

V17_CONTROLS = "9ea4e727c5d308457a2d5901ef6565522845fb31d52c3c1c0f7dd5a51a9d83c0"
V17_ADOPTION = "61ca680e932fcb6d32a972c3198b5bd9c029da3955e15dd7acb2e07db125699b"
V17_ADMIT = "c3960464db74a282f20da030008fb759a0fad4e1d4d3c7133c98f3b821d6b9ed"
V17_STATUS = "a9f9180b73438221788d745567603fd267befca8fbc60528e3e7de47421ff64a"
V17_DESIGNATED = "a96eb59833ff794d3f9ce0ca09ada03d045a29cb9f8a676dad86f8aba85d5584"
V17_QUAL = "8fdbf48e998e39a8c0b12900d75e3dfaf4ab64396ade08a17a5cab549c0b5faa"
E1_PATH, E1_SHA = "chpc/row19_partition_e1.json", "8d1de408b6ef9dc66d4736b6138536de6591f0d29ebdd6fd00a6e43307225608"
E2_PATH, E2_SHA = "chpc/row19_partition_e2.json", "48cea639e823abbf39238e3dd7c075f63ba9eca8467009348510e2943ed56fa6"
V17_REC = ("reviews/2026-10-19_e2_repair_codex_rereview.md", "48b9cf053cbd4f73e40e3e139f84a7ab50eb6c4252e8727bf90953bc1ed88f2b")
V17_PILOT_REC = ("reviews/2026-10-20_pilot_v17_codex_review.md", "75bb50101afa7eebc07e47915afbed32dec92ebf1e68235fe742bf9e5ff0035d")
NODE_EV_NAME, NODE_EV_SHA = "row19_screen_refit_54.nodefail.json", "730ea262c65c9e70d9bc39d572d65bd4ea70ac77c52fb3a4e4a1ed9238164b1f"
SCHEMA = "row19-screen-archive-v17-before-v18-1"
CTL_REL = "rsc_screen_ctl/workspace_demo/t1_access"
REQUIRED_CTL = {"chpc/row19_screen_controls.json": V17_CONTROLS, "chpc/row19_screen_controls_adoption.json": V17_ADOPTION,
                "chpc/row19_screen_admit.py": V17_ADMIT, "chpc/row19_screen_status.py": V17_STATUS,
                "chpc/row19_screen_designated.json": V17_DESIGNATED, E1_PATH: E1_SHA, E2_PATH: E2_SHA,
                V17_REC[0]: V17_REC[1], V17_PILOT_REC[0]: V17_PILOT_REC[1],
                "chpc/row19_screen_budget.json": None, "chpc/row19_screen_manifest.json": None,
                "chpc/row22_bank_status.py": None, "chpc/row22_bank_submit.py": None}
# the controller clone's pinned untracked evidence (v16 live preflight 17 Oct 2026, carried unchanged through v17; row-23 bench
# comparator / EC2 qualification permit copies written 12 Oct 18:39, historical evidence, not authority for this migration):
# mandatory archive members
UNTRACKED_CTL = {"aws_ec2/ec2_release_state.json": "80ba0ac599f617f8c0ee020d75e7c53dcd30c519d783a76dcb6a2f6b9f1a1d39",
                 "aws_ec2/runs/b2/bench_report_attempt_5_20261011T185715Z.json":
                     "154511e687f006001888970bd3d65398b6b37c910221378b7f6c3c63fe63e3a4",
                 "reviews/2026-10-11_d1d2_f3_codex_record.md": "636f1e77089578a14ee837bf95fe0f86cc84dbc907f8ced918256b69dbb55c1e"}
UNTRACKED_PREFIX = "untracked/"
TOP = {"COMPLETE", "SHA256SUMS", "INVENTORY.gate", "INVENTORY.jobs", "ctl", "gate", "jobs", "ledger", "ec2"}
LEDGER = "ledger/row19_screen_campaign_budget.json"
ACT1 = "ec2/activation_e1.json"
ACT2 = "ec2/activation_e2.json"
STAGING = ".v17_before_v18.staging"
LINE = re.compile(r"^([0-9a-f]{64})  \./([A-Za-z0-9._+=@,:~-]+(?:/[A-Za-z0-9._+=@,:~-]+)*)$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


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
            "act1": os.path.join(T, "row19_screen", "ec2", "activation_e1.json"),
            "act2": os.path.join(T, "row19_screen", "ec2", "activation_e2.json"),
            "parent": os.path.join(T, "archive_screen"), "A": os.path.join(T, "archive_screen", "v17_before_v18")}


def ctl_inventory(controls_bytes):
    """{repo path: required sha or None} for the controller files: REQUIRED_CTL plus every v17 pin and its partition."""
    if sha_bytes(controls_bytes) != V17_CONTROLS:
        raise Refuse("the controller controls are not the adopted v17 bytes 9ea4e727")
    v = json.loads(controls_bytes.decode())["versions"][-1]
    if v.get("version") != 17 or not isinstance(v.get("files"), dict) or not v["files"]:
        raise Refuse("the adopted controls' latest entry is not version 17 with pinned files")
    if v.get("partition") != {"path": E2_PATH, "sha256": E2_SHA}:
        raise Refuse("the adopted v17 entry does not pin the partition e2 48cea639")
    inv = dict(REQUIRED_CTL)
    for f, hsh in v["files"].items():
        if not isinstance(hsh, str) or not HEX64.match(hsh) or f.startswith("/") or ".." in f.split("/") \
                or f.startswith(UNTRACKED_PREFIX) or f in UNTRACKED_CTL:
            raise Refuse("malformed v17 pin %r" % f)
        if inv.get(f) not in (None, hsh):
            raise Refuse("v17 pin for %s disagrees with the adopted identity" % f)
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
        mem.append(("gate/" + f, os.path.join(P["G"], f), V17_QUAL if f == "qualified_refit_job1.json" else None))
    canon(P["C"], "the controller clone"); canon(P["jobs"], "the job-script directory")
    jobs = sorted(glob.glob(os.path.join(P["jobs"], "row19_screen_refit_*")))
    if not jobs:
        raise Refuse("no refit job scripts %s/row19_screen_refit_*" % P["jobs"])
    if os.path.join(P["jobs"], NODE_EV_NAME) not in jobs:
        raise Refuse("the captured node document %s/%s is missing (it must be retained)" % (P["jobs"], NODE_EV_NAME))
    for j in jobs:
        mem.append(("jobs/" + os.path.basename(j), j, NODE_EV_SHA if os.path.basename(j) == NODE_EV_NAME else None))
    mem.append((LEDGER, P["ledger"], None))
    mem.append((ACT1, P["act1"], None))
    mem.append((ACT2, P["act2"], None))
    for a, _, _ in mem:
        if not LINE.match("0" * 64 + "  ./" + a):
            raise Refuse("an archive member name is not portable: %r" % a)
    return mem


def inventory(T):
    mem = sources(T); n = 0
    for a, src, want in mem:
        b = read_regular(src)
        if want and sha_bytes(b) != want:
            raise Refuse("%s is not its v17 identity %s" % (src, want[:8]))
        n += 1
    print("archive sources complete: %d files (ctl %d incl. %d pinned untracked evidence, gate %d, jobs %d incl. the node document, ledger 1, ec2 2)" % (
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


def complete_text(sums_sha, head, qual, review, budget, node_ev):
    return "schema %s\nsha256sums %s\nctl_head %s\nqualification %s\nreview %s\nbudget %s\nnode_evidence %s\n" % (
        SCHEMA, sums_sha, head, qual, review, budget, node_ev)


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
    m = re.match(r"^schema (\S+)\nsha256sums ([0-9a-f]{64})\nctl_head ([0-9a-f]{40})\nqualification ([0-9a-f]{64})\n"
                 r"review ([0-9a-f]{64})\nbudget ([0-9a-f]{64})\nnode_evidence ([0-9a-f]{64})\n$", comp)
    if not m or m.group(1) != SCHEMA:
        raise Refuse("COMPLETE is missing or malformed")
    ident = {"sha256sums": m.group(2), "ctl_head": m.group(3), "qualification": m.group(4), "review": m.group(5), "budget": m.group(6),
             "node_evidence": m.group(7)}
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
            raise Refuse("ctl/%s is not its v17 identity %s" % (f, want[:8]))
    for f, want in UNTRACKED_CTL.items():
        if sums["ctl/" + UNTRACKED_PREFIX + f] != want:
            raise Refuse("ctl/%s%s is not its pinned untracked evidence identity %s" % (UNTRACKED_PREFIX, f, want[:8]))
    if sums["ctl/chpc/row19_screen_budget.json"] != ident["budget"]:
        raise Refuse("COMPLETE does not certify the archived budget phases")
    # the variable gate and job contents, against the inventories captured from the sources
    for part in ("gate", "jobs"):
        cap = parse_sums(read_regular(os.path.join(A, "INVENTORY." + part)).decode("utf-8", "replace"), "INVENTORY." + part)
        have = {f: sums[f] for f in listed if f.startswith(part + "/")}
        if cap != have:
            raise Refuse("%s/ is not exactly the captured INVENTORY.%s" % (part, part))
        if part == "jobs" and (not have or not all(os.path.basename(f).startswith("row19_screen_refit_") for f in have)):
            raise Refuse("jobs/ holds no refit job script, or another file")
    if sums.get("gate/qualified_refit_job1.json") != V17_QUAL or ident["qualification"] != V17_QUAL:
        raise Refuse("the archived gate qualification is not the adopted v17 8fdbf48e")
    if sums.get("jobs/" + NODE_EV_NAME) != NODE_EV_SHA or ident["node_evidence"] != NODE_EV_SHA:
        raise Refuse("the archived jobs/ do not retain the captured node document %s at 730ea262" % NODE_EV_NAME)
    if "gate/review_refit.json" not in sums or sums["gate/review_refit.json"] != ident["review"]:
        raise Refuse("the archived active review is missing or not the certified one")
    if {f for f in listed if f.startswith("ledger/")} != {LEDGER}:
        raise Refuse("ledger/ is not exactly %s" % LEDGER)
    if {f for f in listed if f.startswith("ec2/")} != {ACT1, ACT2}:
        raise Refuse("ec2/ is not exactly %s and %s" % (ACT1, ACT2))
    for f in (LEDGER, ACT1, ACT2):
        try:
            json.loads(read_regular(os.path.join(A, f)).decode())
        except ValueError:
            raise Refuse("the archived %s is not JSON" % f)
    extra = listed - {f for f in listed if f.split("/")[0] in ("ctl", "gate", "jobs", "ledger", "ec2")} - {"INVENTORY.gate", "INVENTORY.jobs"}
    if extra:
        raise Refuse("unexpected archive members %s" % sorted(extra)[:3])
    ident["files"] = str(len(listed))
    return ident


def leftovers(parent):
    return sorted(glob.glob(os.path.join(parent, STAGING + "*")))


def read_ledger_once(src):
    """One complete version of the ledger (atomically replaced by running jobs): read until it parses, at most 3 times."""
    last = None
    for _ in range(3):
        b = read_regular(src)
        try:
            json.loads(b.decode())
            return b
        except ValueError as e:
            last = e
    raise Refuse("the campaign ledger %s does not read as JSON (%s)" % (src, last))


def build(T, head):
    P = paths(T); A = P["A"]
    if not HEX40.match(head):
        raise Refuse("the controller HEAD %r is not a 40-hex commit" % head)
    canon(P["parent"], "the archive parent"); canon(A, "the archive")
    if os.path.lexists(A):
        raise Refuse("%s already exists; not overwriting (verify it instead)" % A)
    if os.path.lexists(P["parent"]) and (os.path.islink(P["parent"]) or not os.path.isdir(P["parent"])):
        raise Refuse("the archive parent %s is not a real directory" % P["parent"])
    if not os.path.isdir(P["parent"]):
        os.makedirs(P["parent"])
    left = leftovers(P["parent"])
    if left:
        raise Refuse("an interrupted archive build left %s; partial evidence is kept, inspect and recover it by hand" % left)
    mem = sources(T)
    pre = {}; snap = {}
    for a, src, want in mem:                      # every source reads and carries its identity BEFORE anything is staged
        if a == LEDGER:
            snap[a] = read_ledger_once(src); pre[a] = sha_bytes(snap[a])
            continue
        pre[a] = sha_bytes(read_regular(src))
        if want and pre[a] != want:
            raise Refuse("%s is not its v17 identity %s" % (src, want[:8]))
    stg = canon(os.path.join(P["parent"], "%s.%d" % (STAGING, os.getpid())), "the staging directory")
    os.mkdir(stg)
    sums = {}; inv = {"gate": {}, "jobs": {}}
    for a, src, want in mem:
        b = snap[a] if a in snap else read_regular(src)
        d = sha_bytes(b)
        if d != pre[a]:
            raise Refuse("%s changed while archiving (staging %s kept)" % (src, stg))
        dst = canon(os.path.join(stg, a), "the staged copy"); canon(os.path.dirname(dst), "the staged parent")
        if not os.path.isdir(os.path.dirname(dst)):
            os.makedirs(os.path.dirname(dst))
        with open(dst, "xb") as fh:
            fh.write(b); fh.flush(); os.fsync(fh.fileno())
        if sha_bytes(read_regular(dst)) != d or (a not in snap and sha_bytes(read_regular(src)) != d):
            raise Refuse("copy of %s did not verify, or the source changed while archiving (staging %s kept)" % (src, stg))
        st = os.lstat(src)
        os.utime(dst, ns=(st.st_atime_ns, st.st_mtime_ns))
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
    with open(os.path.join(stg, "COMPLETE"), "xb") as fh:
        fh.write(complete_text(sha_bytes(sb), head, V17_QUAL, sums["gate/review_refit.json"],
                               sums["ctl/chpc/row19_screen_budget.json"], sums["jobs/" + NODE_EV_NAME]).encode())
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
        if len(argv) == 2 and argv[0] == "inventory":
            inventory(argv[1]); return 0
        if len(argv) == 3 and argv[0] == "build":
            ident = build(argv[1], argv[2])
            print("archive built %s: %s files, SHA256SUMS %s, ctl_head %s, review %s, budget %s" % (
                paths(argv[1])["A"], ident["files"], ident["sha256sums"][:16], ident["ctl_head"][:12], ident["review"][:16],
                ident["budget"][:16]))
            print("sha256sums=%s" % ident["sha256sums"]); print("budget=%s" % ident["budget"]); return 0
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
            print("archive verifies %s: %s files, SHA256SUMS %s, ctl_head %s, review %s, budget %s" % (
                P["A"], ident["files"], ident["sha256sums"][:16], ident["ctl_head"][:12], ident["review"][:16], ident["budget"][:16]))
            print("sha256sums=%s" % ident["sha256sums"]); print("budget=%s" % ident["budget"]); return 0
        print("usage: inventory <T> | build <T> <ctl_head> | verify <T> [--get key]"); return 2
    except Refuse as e:
        print("ABORT: archive: %s" % e); return 1
    except (OSError, ValueError, KeyError, TypeError) as e:
        print("ABORT: archive: %s: %s" % (type(e).__name__, e)); return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
