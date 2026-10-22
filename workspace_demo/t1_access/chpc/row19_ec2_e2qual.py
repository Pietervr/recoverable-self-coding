"""Row 19 screen on EC2, provider epoch 2 - CANDIDATE, not adopted: the declared FIXED qualification panel (E2Q1, and the
conditional identical E2Q2) and the constants of the epoch-2 release rule R1'-R5', shared by the Mac (manifest builder,
launcher, release branch of prod_authority) and Lengau (qualifier), so they cannot disagree. chpc/candidate_e2/
QUALIFICATION_E2.md s.2-s.3 is the declaration this module implements; chpc/candidate_e2q/DESIGN_e2q.md maps it.

Pure: no scientific import, no network, no file reads (code_path only tests for a file's existence).

PANEL (QUALIFICATION_E2.md s.2, declared before any epoch-2 result, never chosen by outcome)
  work        the first 52 owned coordinates of the bound epoch-2 partition in the PRODUCTION allocation order: ascending
              (rep, index) over the explicitly owned set, at most 57 of one replicate (prod_authority.allocate with no ledger
              history; row19_ec2_e2rules.QUALIFIED_REP_SLOTS - 4). On the 17 Oct candidate partition: rep 24, indices 11..62.
              E2Q1 OWNS them; after a RELEASE they are ingested as production.
  duplicates  the 20 lowest Lengau-completed DESIGNATED coordinates of the EC2-designated replicates, ascending (rep, index),
              read from the claims snapshot the partition is bound to (its sha256 is in the partition). On 17 Oct: rep 24
              (0-8), 25 (0-5, 7, 8), 28 (0-2). They never own; they give R1' float-bit parity at the same packing.
  sentinels   4, the token rule (prod_authority.sentinels over Lengau-completed non-owned coordinates), never among the
              duplicates; chosen at admission from the attempt token, so they are NOT in the panel file.
  shape       76 workers; the panel's work + duplicates must put >= QUALIFIED_REP_SLOTS (61) on ONE replicate, the
              concentration production is held to (A3). A partition on which that fails is refused here: the panel must be
              re-declared before any outcome (or the production cap lowered and re-costed) - QUALIFICATION_E2.md s.2.
The panel file binds the partition (sha256, owned digest) and the claims snapshot (path, sha256, claims digest). It is
DERIVED: panel_problem regenerates it from those inputs and requires byte-equal canonical JSON, so it carries no authority
of its own. It must be regenerated whenever the partition is (DESIGN_e2q.md s.6).

REVISION 2 - controls v19 CANDIDATE (owner decision 21 Oct 2026, R052: "On-demand E2Q3"; chpc/candidate_v19_oploss/DESIGN_v19.md
s.7). The contract set grows by E2Q3 (row19_ec2_state REVISION 5: the identical geometry on-demand), run qual-E2Q3; the release
rule R1'-R5', the code set, the coverage and every panel coordinate are unchanged. The panel DECLARATION keeps naming the two
contracts it was declared for (PANEL_CONTRACTS / PANEL_RUNS, frozen), so the committed panel aws_ec2/prod/panel_e2q_e2.json
(f04a5e43) regenerates byte-equal and stays the one declared panel E2Q3 runs: its `contracts`/`runs` fields are provenance of
the 17 Oct declaration, never a gate (no consumer reads them; the gates read CONTRACTS / RUNS below)."""
import hashlib, json, os

import row19_ec2_e2rules as E2R

PANEL_SCHEMA = "row19-ec2-e2q-panel-1"
PARTITION_SCHEMA2 = "row19-provider-partition-2"               # = row19_partition.SCHEMA2 (not imported: this module stays pure)
SNAPSHOT_SCHEMA = "row19-lengau-claims-snapshot-1"             # = row19_partition.SNAPSHOT_SCHEMA
CONTRACTS = ("E2Q1", "E2Q2", "E2Q3")                            # row19_ec2_state.CONTRACTS (REVISION 4; E2Q3 REVISION 5)
RUNS = {"E2Q1": "qual-E2Q1", "E2Q2": "qual-E2Q2", "E2Q3": "qual-E2Q3"}   # prod_authority.qual_run(contract); is_e2_qual counts all
PANEL_CONTRACTS = ("E2Q1", "E2Q2")                              # REVISION 2: the 17 Oct panel declaration's own text (frozen)
PANEL_RUNS = {"E2Q1": "qual-E2Q1", "E2Q2": "qual-E2Q2"}
EPOCH = 2
WORK_N, DUP_N, SENTINELS, WORKERS = 52, 20, 4, 76
WORK_PER_REP = E2R.QUALIFIED_REP_SLOTS - SENTINELS              # 57: the production allocator's per-replicate cap
EXPECT_S, LIFETIME_S = 75300, 79200                             # the funded 22 h lifetime (make_prod_manifest REVISION 2)
# The release rule (QUALIFICATION_E2.md s.3), declared now
CERT_SCHEMA = "row19-ec2-qualification-certificate-3"
COVERAGE = {"R1": 15}                                           # >= 15 of the 20 duplicates finite successful on both sides
MEM_HOST_LIMIT_GIB, MEM_MIN_SAMPLES = 184.0, 10                 # R4': the e1 R4 method at the 76-worker packing
QUAL_MAX_UNPRODUCED = E2R.QUAL_MAX_UNPRODUCED                   # R4': at most 3 non-completed slots of ALL roles
REPLAY_SCOPE = ("ingestion-publication interruption on a relocated, re-bound sandbox copy of the E2Q attempt's actual bundle "
                "(presented as class production so the per-slot branch runs), replay and second replay, plus the per-slot "
                "branch; NOT producer process/host restart, NOT interrupted-transfer recovery, NOT the canonical Mac ACK")
RELEASE_LITERAL = "RELEASE row19-ec2-qualification epoch=2 certificate={sha} attempts={keys}"
# The epoch-2 qualification code set a schema-3 certificate binds EXACTLY (paths as promoted; = prod_authority.E2_RELEASE_CODE).
# No S shadow exists in epoch 2, so the S files of the epoch-1 set are not in it; the shared rules, the panel module and the
# state module carrying the E2Q contracts are.
CODE = sorted(["chpc/row19_ec2_qualify.py", "chpc/row19_ec2_ingest.py", "chpc/row19_ec2_state.py", "chpc/row19_partition.py",
               "chpc/row19_ec2_root.py", "chpc/row19_ec2_e2rules.py", "chpc/row19_ec2_e2qual.py", "chpc/row19_shard.py",
               "chpc/row19_screen_verify.py", "analyze.py", "models.py"])


CANDIDATE_DIRS = ("chpc/candidate_e2q", "chpc/candidate_e2")   # pre-promotion only: newest candidate first, then the reviewed e2


def code_path(t1, rel, candidate):
    """The file a run uses for the promoted path `rel`: before promotion (`candidate` True: the caller itself runs from a
    chpc/candidate_* folder) the candidate copy when one exists, else the live file; after promotion always t1/rel. A
    certificate binds the CONTENT of these files as {promoted path: sha256}, and the release branch resolves the same way.
    Byte-identical candidate and promoted copies therefore give the same map: the binding is content, not location or
    installation provenance, and a location change alone does not invalidate a certificate (Codex review
    reviews/2026-10-19_e2_adoption_codex_review.md, choice 8; docstring-only correction, the code is unchanged). The actual
    certificate is generated after deployment and activation from the deployed files."""
    if candidate and rel.startswith("chpc/"):
        for d in CANDIDATE_DIRS:
            p = os.path.join(t1, d, rel[len("chpc/"):])
            if os.path.isfile(p):
                return p
    return os.path.join(t1, rel)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def owned_coords(part):
    return sorted((int(r), int(i)) for r, ix in part["owned"].items() for i in ix)


def work_order(part, n=WORK_N, per_rep=WORK_PER_REP):
    """The first n owned coordinates in the production allocation order (ascending, at most per_rep of one replicate) - the
    order prod_authority.allocate gives a schema-2 partition with no ledger history."""
    out, per = [], {}
    for c in owned_coords(part):
        if len(out) >= n:
            break
        if per.get(c[0], 0) >= per_rep:
            continue
        out.append(c); per[c[0]] = per.get(c[0], 0) + 1
    return out


def duplicate_order(part, snap, n=DUP_N):
    """The n lowest Lengau-completed designated coordinates of the EC2-designated replicates, ascending (rep, index)."""
    d = part["designated"]; lo, hi = int(d["indices"]["start"]), int(d["indices"]["stop"]); ec2 = {int(r) for r in d["ec2_reps"]}
    done = sorted({(int(r), int(i)) for r, i in snap["lengau_done"] if int(r) in ec2 and lo <= int(i) < hi})
    return done[:n]


def derive_panel(part, part_sha, snap, snap_sha, snap_path):
    """The panel declaration for this partition and its bound claims snapshot (`snap_path` as recorded: relative to
    t1_access, or absolute for a sandbox). Raises ValueError when the inputs are not the bound ones or the panel cannot
    carry the declared shape."""
    if not isinstance(part, dict) or part.get("schema") != PARTITION_SCHEMA2 or int(part.get("epoch", -1)) != EPOCH:
        raise ValueError("the E2Q panel is declared on the epoch-2 schema-2 partition only")
    if not isinstance(snap, dict) or snap.get("schema") != SNAPSHOT_SCHEMA:
        raise ValueError("not a row19-lengau-claims-snapshot-1")
    cs = part.get("claims_snapshot") or {}
    if snap_sha != cs.get("sha256") or snap.get("claims_sha256") != cs.get("claims_sha256"):
        raise ValueError("the claims snapshot is not the one the partition is bound to (sha256 / claims digest)")
    work = work_order(part)
    if len(work) != WORK_N:
        raise ValueError(f"the partition owns only {len(work)} coordinates for the {WORK_N} E2Q work slots")
    dups = duplicate_order(part, snap)
    if len(dups) != DUP_N:
        raise ValueError(f"only {len(dups)} Lengau-completed designated coordinates on the EC2 replicates for {DUP_N} duplicates")
    owned = set(owned_coords(part))
    if set(dups) & owned:
        raise ValueError("a duplicate is an owned coordinate (the snapshot and the partition disagree)")
    conc = E2R.rep_concentration([dict(rep=r) for r, _ in work + dups])
    top = max(conc.values())
    if top < E2R.QUALIFIED_REP_SLOTS:
        raise ValueError(f"the panel puts at most {top} workers on one replicate, below the qualified {E2R.QUALIFIED_REP_SLOTS}: "
                         "re-declare the panel before any outcome, or lower and re-cost the production cap (QUALIFICATION_E2.md s.2)")
    return {"schema": PANEL_SCHEMA, "epoch": EPOCH, "contracts": list(PANEL_CONTRACTS), "runs": dict(PANEL_RUNS),
            "partition_sha256": part_sha, "owned_sha256": part["owned_sha256"], "owned_count": int(part["owned_count"]),
            "claims_snapshot": {"path": snap_path, "sha256": snap_sha, "claims_sha256": snap["claims_sha256"]},
            "workers": WORKERS, "roles": {"work": WORK_N, "qual_lengau": DUP_N, "sentinel": SENTINELS},
            "work": [list(c) for c in work], "duplicates": [list(c) for c in dups],
            "concentration": {"per_rep": {str(r): n for r, n in sorted(conc.items())}, "max": top,
                              "max_reps": sorted(r for r, n in conc.items() if n == top),
                              "qualified_rep_slots": E2R.QUALIFIED_REP_SLOTS, "note": "work + duplicates; the token sentinels can only raise it"},
            "sentinels": {"n": SENTINELS, "rule": "prod_authority.sentinels(Lengau-completed non-owned coordinates, attempt token, "
                          "exclude=duplicates): fixed by the token at admission, never by outcome"},
            "lifetime_s": LIFETIME_S, "expect_s": EXPECT_S,
            "rule": "QUALIFICATION_E2.md s.2: work = the first 52 owned coordinates in the production allocation order (ascending, "
                    "<= 57 per replicate); duplicates = the 20 lowest Lengau-completed designated coordinates of the EC2 replicates "
                    "(ascending); E2Q2 is the identical request under its own contract and run, only after an external-cause end of E2Q1"}


def panel_bytes(panel):
    return (json.dumps(panel, indent=1, sort_keys=True) + "\n").encode()


def panel_problem(panel, part, part_sha, snap, snap_sha):
    """'' when `panel` is exactly the derivation from this partition and its bound claims snapshot."""
    if not isinstance(panel, dict) or panel.get("schema") != PANEL_SCHEMA:
        return "not a row19-ec2-e2q-panel-1 declaration"
    try:
        want = derive_panel(part, part_sha, snap, snap_sha, (panel.get("claims_snapshot") or {}).get("path"))
    except ValueError as e:
        return f"the panel cannot be derived: {e}"
    if canonical(want) != canonical(panel):
        diff = sorted(k for k in set(want) | set(panel) if want.get(k) != panel.get(k))
        return f"the panel is not the derivation from this partition and snapshot (differs on {diff})"
    return ""


def opmanifest_bytes(es, prod, prod_sha, contract):
    """The exact bytes make_prod_manifest.py writes for an epoch-2 operational manifest of `contract` at the funded lifetime
    (row19_ec2_state.derive_operational, json indent 1, sorted keys, no trailing newline)."""
    return json.dumps(es.derive_operational(prod, prod_sha, EPOCH, EXPECT_S, contract), indent=1, sort_keys=True).encode()


def ack_problem(entry, owned):
    """The Mac `ack` rule (prod_authority.ack, REVISION 6) applied to a register entry: '' when it is ingested, its published
    plus unproduced coordinates are exactly `owned` ([rep, index] list) and disjoint, and every unproduced outcome is of a
    qualifying class. The qualifier's sandbox uses it; the Mac applies the real `ack`."""
    if not isinstance(entry, dict) or entry.get("state") != "ingested":
        return "the register entry is not ingested"
    pub, unp = set(entry.get("coordinates") or {}), entry.get("unproduced") or {}
    if pub & set(unp):
        return "a coordinate is both published and unproduced"
    if sorted(list(pub) + list(unp)) != sorted(f"{int(r)}/{int(i)}" for r, i in owned):
        return "published + unproduced coordinates are not exactly the attempt's owned coordinates"
    bad = {k: u for k, u in unp.items() if not isinstance(u, dict) or E2R.kind(u.get("outcome")) is None}
    return f"unproduced outcomes of no qualifying class: {bad}" if bad else ""
