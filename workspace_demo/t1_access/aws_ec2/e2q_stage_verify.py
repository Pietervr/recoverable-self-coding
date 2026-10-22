"""EC2 epoch 2 - E2Q bundle STAGING verifier (CANDIDATE for Codex review; not adopted, never run against the world).

    python3 e2q_stage_verify.py --bundle <dir> --expect <expect.json> [--stage-root <dir>]      (Mac: python3; Lengau: t1py)

ONE pure, stdlib-only check of a collected E2Q1/E2Q2 bundle, run unchanged on the Mac after the S3 collection and on Lengau
after the transfer (chpc/candidate_e2s/e2q_stage.py ships this exact file beside the staged bundle and checks its sha256
before and after it runs). It READS the bundle and writes nothing anywhere; it prints one JSON document (schema
row19-e2q-stage-verify-1) and exits 0 when the bundle is complete and is exactly the bound attempt, 3 otherwise.

The member contract is the producer's (aws_ec2/prod_userdata.sh) and the ingestion's (chpc/row19_ec2_ingest.py check_bundle,
REVISION 8), applied to EVERY regular file of the tree, not only root/ and env/:
  sealed     every line of BUNDLE_SHA256SUMS is `<64 lowercase hex>  <path>`, the path relative, normalised, under root/ or
             env/, unique, no escaped name, in C order (the producer writes `find root env | LC_ALL=C sort | xargs sha256sum`);
             each listed file exists and has that sha256 (a missing or short member is PARTIAL);
  required   env/plan.json, env/outcomes.json, env/attest_B.json, env/censored.txt and env/declared.txt are sealed;
             env/upload_verify.json is present with transfer_verified true; no env/FAILED, OUTCOMES_FAILED, BUNDLE_FAILED;
  allowed    the only unsealed members are BUNDLE_SHA256SUMS itself, the ingestion's mutable diagnostics (MUTABLE below,
             = row19_ec2_ingest.MUTABLE) and the producer's unsealed per-worker files logs/w_slot<k>.log and
             exits/w_slot<k>.code of PLANNED slots k. Any other file - unlisted under root/ or env/, at the top level, of an
             unplanned slot, a symbolic link or a special file - is an EXTRA member and refuses;
  bound      env/plan.json is the attempt's bytes (plan_sha256) and names the attempt (attempt id, sequence, contract, epoch 2,
             the partition and the contract's operational manifest, the funded lifetime) with exactly 76 slots 0..75 whose
             work / qual_lengau / sentinel coordinates are, in order, the declared panel's work, its duplicates and the
             attempt's sentinels; env/outcomes.json names exactly w_slot0..w_slot75 and declares 76; every worker status is
             root/status/job<attempt id>.slot<k>.json of a planned slot.
The scientific contract (records against the frozen task, statuses, outcome classes, comparisons, memory, replay) is NOT
judged here: that is the qualifier's and the ingestion's, unchanged. This check only proves that the bytes the qualifier will
read are, member for member, the producer's sealed bundle of the bound attempt and nothing else.

The tree digest is bench_finish.bundle_digest's: sha256 of json.dumps(sorted([relative path, file sha256])) over every
regular file - the identity the Mac and Lengau compare. With --stage-root the bundle must lie strictly inside that
directory with no symbolic link between it and the bundle (the fixed contained staging path; the root itself may sit
behind a site symlink such as a Lustre mount alias).

REVISION 2 (owner decision 21 Oct 2026, R052 "On-demand E2Q3"; operational change, no Codex review of this tooling): the
expectation's contract may also be E2Q3 (the on-demand third attempt, same 52 / 20 / 4 roles). Nothing else changes; these
bytes differ from the reviewed chpc/candidate_e2s copy (f742f017) only by this paragraph and E2Q_CONTRACTS."""
import argparse, hashlib, json, os, re, stat, sys

SCHEMA = "row19-e2q-stage-verify-1"
MUTABLE = ("env/upload_verify.json", "env/userdata.log", "env/spot_notice.json", "env/stop_seen.txt", "env/memory_live.txt")
REQUIRED_SEALED = ("env/plan.json", "env/outcomes.json", "env/attest_B.json", "env/censored.txt", "env/declared.txt")
FAIL_MARKERS = ("env/FAILED", "env/OUTCOMES_FAILED", "env/BUNDLE_FAILED")
SUMS = "BUNDLE_SHA256SUMS"
EPOCH, WORKERS, LIFETIME_S = 2, 76, 79200
E2Q_CONTRACTS = ("E2Q1", "E2Q2", "E2Q3")                     # REVISION 2: E2Q3
_LINE = re.compile(r"^([0-9a-f]{64})  (\S(?:.*\S)?)$")
_PER_SLOT = re.compile(r"^(logs/w_slot(\d+)\.log|exits/w_slot(\d+)\.code)$")
EXPECT_KEYS = ("key", "attempt_id", "sequence", "contract", "plan_sha256", "partition_sha256", "opmanifest_sha256", "work",
               "duplicates", "sentinels")


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def tree_digest(items):
    """bench_finish.bundle_digest's formula over [[relative path, sha256], ...]."""
    return hashlib.sha256(json.dumps(sorted([list(x) for x in items])).encode()).hexdigest()


def walk(bundle, problems):
    """{relative path: sha256} of every regular file; a symbolic link, special file or unreadable entry is a problem."""
    out = {}
    for d, dirs, files in os.walk(bundle, followlinks=False):
        for name in sorted(dirs):
            p = os.path.join(d, name)
            if os.path.islink(p):
                problems.append(f"symbolic link {os.path.relpath(p, bundle)} (EXTRA: never followed)")
        for name in sorted(files):
            p = os.path.join(d, name); rel = os.path.relpath(p, bundle).replace(os.sep, "/")
            try:
                st = os.lstat(p)
            except OSError as e:
                problems.append(f"member {rel} unreadable ({type(e).__name__})"); continue
            if stat.S_ISLNK(st.st_mode):
                problems.append(f"symbolic link {rel} (EXTRA: never followed)"); continue
            if not stat.S_ISREG(st.st_mode):
                problems.append(f"special file {rel} (EXTRA)"); continue
            try:
                out[rel] = sha_file(p)
            except OSError as e:
                problems.append(f"member {rel} unreadable ({type(e).__name__})")
    return out


def parse_sums(text, problems):
    """{path: sha256} of a well-formed BUNDLE_SHA256SUMS, or None."""
    listed, order = {}, []
    if not text.endswith("\n") and text:
        problems.append(f"{SUMS} does not end with a newline (truncated?)")
    for k, line in enumerate(text.split("\n")[:-1] if text.endswith("\n") else text.split("\n"), 1):
        m = _LINE.match(line)
        if not m:
            problems.append(f"{SUMS} line {k} is not '<sha256>  <path>' (an escaped or malformed name)"); return None
        h, f = m.group(1), m.group(2)
        if f.startswith("/") or "\\" in f or os.path.normpath(f).replace(os.sep, "/") != f or f.split("/")[0] not in ("root", "env") \
                or ".." in f.split("/") or f.count("/") < 1:
            problems.append(f"{SUMS} line {k} names {f!r}: not a normalised path under root/ or env/"); return None
        if f in listed:
            problems.append(f"{SUMS} lists {f} twice"); return None
        listed[f] = h; order.append(f)
    if order != sorted(order, key=lambda s: s.encode()):
        problems.append(f"{SUMS} is not in the producer's C order")
    if not listed:
        problems.append(f"{SUMS} lists nothing")
    return listed


def expect_problem(e):
    if not isinstance(e, dict) or any(k not in e for k in EXPECT_KEYS):
        return f"the expectation lacks {[k for k in EXPECT_KEYS if not isinstance(e, dict) or k not in e]}"
    if e["contract"] not in E2Q_CONTRACTS or len(e["work"]) != 52 or len(e["duplicates"]) != 20 or len(e["sentinels"]) != 4:
        return "the expectation is not an E2Q attempt (52 work, 20 duplicates, 4 sentinels)"
    return ""


def verify(bundle, expect, stage_root=None):
    """The verification document (see the module text). Reads only."""
    problems = []
    doc = dict(schema=SCHEMA, bundle=os.path.abspath(bundle), key=(expect or {}).get("key"), ok=False, problems=problems)
    why = expect_problem(expect)
    if why:
        problems.append(why); return doc
    if stage_root is not None:
        sr, bd = os.path.abspath(stage_root), os.path.abspath(bundle)
        below = os.path.relpath(bd, sr).split(os.sep) if bd.startswith(sr + os.sep) else None
        links = [] if below is None else [os.sep.join(below[:k + 1]) for k in range(len(below)) if os.path.islink(os.path.join(sr, *below[:k + 1]))]
        if below is None or ".." in below or links or not os.path.realpath(bd).startswith(os.path.realpath(sr) + os.sep):
            problems.append(f"the bundle {bundle} is not strictly inside the staging root {stage_root} without symbolic links ({links})")
            return doc
    if not os.path.isdir(bundle) or os.path.islink(bundle):
        problems.append("no bundle directory"); return doc
    members = walk(bundle, problems)
    doc.update(files=len(members), tree_sha256=tree_digest(members.items()), members=members)
    if SUMS not in members:
        problems.append(f"no {SUMS} (PARTIAL: the producer's sealed list is missing)"); return doc
    try:
        text = open(os.path.join(bundle, SUMS), encoding="utf-8").read()
    except (OSError, UnicodeDecodeError) as e:
        problems.append(f"{SUMS} unreadable ({type(e).__name__})"); return doc
    listed = parse_sums(text, problems)
    doc["sums_sha256"] = members[SUMS]
    if listed is None:
        return doc
    for f, h in sorted(listed.items()):
        if f not in members:
            problems.append(f"PARTIAL: sealed member {f} is missing")
        elif members[f] != h:
            problems.append(f"sealed member {f} differs from its sealed sha256")
    for f in MUTABLE:
        if f in listed:
            problems.append(f"{f} is a mutable diagnostic but is sealed (not the producer's list)")
    for f in REQUIRED_SEALED:
        if f not in listed:
            problems.append(f"{f} is not a sealed member")
    for f in FAIL_MARKERS:
        if f in members:
            problems.append(f"the instance reported {f.split('/')[-1]}")
    plan_slots = set()
    try:
        plan = json.load(open(os.path.join(bundle, "env", "plan.json")))
        doc["plan_sha256"] = members.get("env/plan.json")
        if members.get("env/plan.json") != expect["plan_sha256"]:
            problems.append("env/plan.json is not the attempt's plan bytes (plan_sha256): another attempt's bundle?")
        for k, want in (("attempt_id", expect["attempt_id"]), ("sequence", expect["sequence"]), ("contract", expect["contract"]),
                        ("epoch", EPOCH), ("partition_sha256", expect["partition_sha256"]),
                        ("opmanifest_sha256", expect["opmanifest_sha256"]), ("lifetime_s", LIFETIME_S)):
            if plan.get(k) != want:
                problems.append(f"the plan's {k} is {plan.get(k)!r}, not the bound {want!r}")
        slots = plan.get("slots") or []
        nums = [s.get("slot") for s in slots]
        if len(slots) != WORKERS or sorted(nums) != list(range(WORKERS)):
            problems.append(f"the plan does not carry exactly the {WORKERS} slots 0..{WORKERS - 1}")
        plan_slots = {int(n) for n in nums if isinstance(n, int) and not isinstance(n, bool)}
        by = {}
        for s in sorted(slots, key=lambda s: s.get("slot") if isinstance(s.get("slot"), int) else -1):
            by.setdefault(s.get("role"), []).append([s.get("rep"), (s.get("indices") or [None])[0]])
        for role, want in (("work", expect["work"]), ("qual_lengau", expect["duplicates"]), ("sentinel", expect["sentinels"])):
            if by.get(role, []) != [list(c) for c in want]:
                problems.append(f"the plan's {role} coordinates are not the bound {'panel work' if role == 'work' else 'panel duplicates' if role == 'qual_lengau' else 'sentinels'}")
        if sorted(by) != ["qual_lengau", "sentinel", "work"]:
            problems.append(f"the plan has roles {sorted(map(str, by))}, not exactly work / qual_lengau / sentinel")
    except Exception as e:
        problems.append(f"env/plan.json unreadable ({type(e).__name__})")
    names = {f"w_slot{k}" for k in plan_slots}
    try:
        oc = json.load(open(os.path.join(bundle, "env", "outcomes.json")))
        if not isinstance(oc.get("outcomes"), dict) or set(oc["outcomes"]) != names or oc.get("declared") != len(names):
            problems.append(f"env/outcomes.json does not name exactly the {len(names)} planned workers")
    except Exception as e:
        problems.append(f"env/outcomes.json unreadable ({type(e).__name__})")
    try:
        uv = json.load(open(os.path.join(bundle, "env", "upload_verify.json")))
        if uv.get("transfer_verified") is not True:
            problems.append(f"PARTIAL: the producer's transfer is not verified ({uv})")
    except Exception as e:
        problems.append(f"PARTIAL: env/upload_verify.json missing or unreadable ({type(e).__name__})")
    status_re = re.compile(r"^root/status/job" + re.escape(str(expect["attempt_id"])) + r"\.slot(\d+)\.json$")
    for f in sorted(members):
        if f.startswith("root/status/"):
            m = status_re.match(f)
            if not m or int(m.group(1)) not in plan_slots:
                problems.append(f"status {f} is not a planned worker status of {expect['attempt_id']}")
        if f in listed or f == SUMS or f in MUTABLE:
            continue
        m = _PER_SLOT.match(f)
        if m and int(m.group(2) or m.group(3)) in plan_slots:
            continue
        problems.append(f"EXTRA member {f} (neither sealed, nor a mutable diagnostic, nor a planned worker's log/exit file)")
    doc["sealed"] = len(listed)
    doc["ok"] = not problems
    return doc


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True); ap.add_argument("--expect", required=True); ap.add_argument("--stage-root")
    a = ap.parse_args(argv)
    try:
        expect = json.load(open(a.expect))
    except Exception as e:
        expect = {"_unreadable": str(e)}
    doc = verify(a.bundle, expect.get("expect", expect), a.stage_root)
    print(json.dumps(doc, sort_keys=True))
    return 0 if doc["ok"] else 3


if __name__ == "__main__":
    sys.exit(main())
