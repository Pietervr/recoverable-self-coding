"""Row 19 screen: the provider partition (Codex RSC f3dd3d7 contract 1; design aws_ec2/PRODUCTION_DESIGN.md).

A partition declaration fixes, for one EPOCH, which resample-index coordinates of the frozen screen task belong to EC2.
Lengau's planner and admission refuse every coordinate in the block; EC2's allocator draws only from it. The declaration
is immutable: a change of k is a NEW epoch file, its predecessor named, completed coordinates never transferred, and only
uncompleted, terminal/fenced, explicitly named coordinates handed back.

    t1py chpc/row19_partition.py declare --manifest chpc/row19_screen_manifest.json --k 50 --epoch 1 --out chpc/row19_partition_e1.json
    t1py chpc/row19_partition.py cutover --manifest chpc/row19_screen_manifest.json --partition chpc/row19_partition_e1.json

`cutover` is the activation proof: it reads the Lengau screen root and campaign (every record, every plan of every ledger
entry in ANY state - live, settled, closed-no-record, unresolved) and refuses (exit 3) when any coordinate of the block was
ever completed, planned or reserved by Lengau. A block that passes is provably unassigned at that observation.

`activate` (REVISION 2, Codex RSC 0483db4 V10-1) is the SERIALIZED cutover: on the Lengau login node it takes the screen's
plan lock (the same lock every admission and ingestion holds), requires that the LATEST adopted controls version already
pins this partition (so the Lengau guard is live before the scan), runs the cutover scan over every record and every
existing/restored/reserved plan, and writes the immutable proof root/ec2/activation_e<epoch>.json binding the partition,
controls and manifest digests and the digest of the scanned claim sets. EC2 admission requires that proof; while the
latest controls pin a partition with no proof, Lengau refit admission HOLDS too (row19_screen_admit v10). A later epoch
names its predecessor {epoch, sha256, indices}; the coordinates it hands back to Lengau (`transferred` = predecessor block
minus this block) are listed, and activation refuses unless the authority inventory on the root (fresh, sealed) shows no
EC2 attempt still owning any of them: only terminal/fenced, uncompleted coordinates move. Coordinates EC2 completed stay
EC2's records (the register keeps their provenance) whatever the later block.

REVISION 3 (Codex RSC 3dc0daf R1-1). A CANONICAL activation runs only against the canonical controls file
(chpc/row19_screen_controls.json) while it is the ADOPTED bytes (programme_gate.controls_authority_problem: tracked,
unmodified, named by the adoption record with a review literal) and its latest version pins this partition - so the Lengau
guard that admission enforces is live before the scan, under the same plan lock. The proof records its mode, the adopted
controls digest and version, the digest of that version entry and the adoption record's digest. Every consumer
(activation_problem) requires mode `canonical` (a `sandbox` proof - tests and the qualifier's replay - is accepted only by a
consumer explicitly in sandbox mode), that the recorded version entry is byte-identical in the current controls, and that
EVERY version from it to the latest still pins this partition (the guard has been continuously live; a later version that
drops or changes the pin invalidates the proof, and a new epoch needs its own activation; earlier epochs' proofs are kept
as provenance). Provider-aware history: records the EC2 register published (non-preexisting coordinates of its ingesting/
ingested entries) are EC2-completed, not Lengau claims; every such coordinate must lie in the block of the partition its
entry names (looked up through the controls versions' partition pins); completed EC2 coordinates are retained, never
transferred. A plan file that is not a well-formed slot list is refused, never read as "no claims".

REVISION 4 (Codex RSC 299f4b7 R2-2). A canonical consumer authenticates the CURRENT controls before it checks a proof's
lineage: activation_problem in mode canonical reads the controls ONLY through adopted_controls() - the canonical file while
it is git-tracked, unmodified and the adopted review-bound bytes (programme_gate.controls_authority_problem) - and refuses a
supplied controls document that is not exactly those bytes. A later candidate placed at the canonical path without its own
adoption therefore fails on the Mac and in ingestion exactly as it fails Lengau admission. A proof made under an earlier
adopted version stays valid under a later ADOPTED version that still pins the same partition (historical reuse).

REVISION 5 - CANDIDATE, not adopted (EC2 provider epoch 2 for the resized row-19 screen; Codex design
reviews/2026-10-17_row19_resize_codex.md s.3, s.4, s.6 item 5; Codex v16 review reviews/2026-10-17_v16_p80_codex_review.md
s.A item 1). A suffix k cannot express the resized ownership, so epoch 2 is a NEW schema, row19-provider-partition-2, with
EXPLICIT coordinate-set ownership:
  owned        EC2 owns exactly the listed (rep, index) coordinates: the designated coordinates (indices 0..79) of the 47
               EC2-designated replicates (the largest IDs of S, chpc/row19_screen_designated.json) that Lengau had NOT
               claimed - never completed and never planned in any plan of any ledger state - in a hashed claims snapshot
               (row19-lengau-claims-snapshot-1, written by `snapshot` from lengau_claims). Everything Lengau ever planned
               stays Lengau's (s.4: "A lower-index coordinate ever planned by Lengau is not automatically transferable");
               nothing is subtracted from Lengau's scope, so `transferred` is always [] in this schema.
  predecessor  {epoch, schema, sha256, coordinates, coordinates_sha256} of the epoch-1 file. Its block (indices 160..199 of
               all 100 reps) is RETIRED: out of the designated design, neither provider plans it again; Q1/Q2 output on it
               is qualification evidence only, never screen units (s.5).
  cover        the declaration states, and load()/ownership_problem() recompute, that over the 4,800 designated
               coordinates D: D minus done (Lengau-completed + EC2-completed) is the DISJOINT union of Lengau's open scope
               (the 13 Lengau replicates + Lengau's claims on the 47) and the EC2-owned set.
`blocked(part, rep, index)` is the one predicate every consumer uses (Lengau planner/admission guard, status view, launcher,
ingestion); for schema 2 it is membership in `owned`. Activation of a schema-2 epoch additionally requires (under the same
plan lock) that the predecessor's activation is on the root and is the named predecessor, and that the INSTALLED fresh
authority inventory shows no attempt owning any coordinate outside this epoch's set and no live attempt of an earlier epoch
(the e1 Q1 attempt must be dispositioned - fenced - first); the cutover scan still refuses any Lengau claim on an owned
coordinate, so a claim made after the snapshot refuses activation (re-snapshot, re-declare).

REVISION 6 - CANDIDATE, not adopted (Codex review reviews/2026-10-17_e2_p80r_codex_review.md, ruling 1). The `snapshot`
command of the CANONICAL root now takes the common plan lock (<root>/plans/.submit.lock, exclusive, non-blocking: a held
lock refuses with exit 3) for the whole claims scan, as its text always said; the source block records
plan_lock "held". A snapshot of a pulled COPY (--root/--campaign) takes no lock on the live root and records plan_lock
"not taken (copy)"; such a snapshot is candidate input only - the adopted bytes come from the canonical locked one."""
import os, sys, json, glob, time, fcntl, hashlib, argparse

SCHEMA = "row19-provider-partition-1"
SCHEMA2 = "row19-provider-partition-2"
SNAPSHOT_SCHEMA = "row19-lengau-claims-snapshot-1"
DESIGNATED_SCHEMA = "row19-screen-designated-1"
DESIGNATED_REL = "chpc/row19_screen_designated.json"     # where controls v16 promotes the pinned designated declaration
HERE = os.path.dirname(os.path.abspath(__file__))
T1 = HERE
while os.path.basename(T1) != "t1_access":                  # chpc/, aws_ec2/ and chpc/candidate_*/ all resolve to t1_access
    if os.path.dirname(T1) == T1:
        raise RuntimeError(f"{HERE} is not inside a t1_access tree")
    T1 = os.path.dirname(T1)
CHPC = os.path.join(T1, "chpc")
CANONICAL_CONTROLS = os.path.join(CHPC, "row19_screen_controls.json")
ADOPTION = os.path.join(CHPC, "row19_screen_controls_adoption.json")
MODES = ("canonical", "sandbox")
DESIGNATED_PATH = None                                      # tests/sandboxes only: an override of T1/<designated.path>
DESIGN_RULE = ((3, 102), (0, 1, 2), 13, 80)                 # S rule (range, residues mod 5), Lengau replicates, index stop


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def declare(man, man_sha, k, epoch, predecessor=None):
    """`predecessor` is None for epoch 1, else {epoch: epoch - 1, sha256: <its file>, indices: <its block>}."""
    B = int(man["cfg"]["n_boot_refit"]); reps = sorted(int(r) for r in man["datasets"]["reps"])
    if not (isinstance(k, int) and not isinstance(k, bool) and 0 < k < B):
        raise ValueError(f"k must be an integer in 1..{B - 1}")
    if (int(epoch) == 1) != (predecessor is None):
        raise ValueError("epoch 1 has no predecessor; every later epoch names exactly its predecessor")
    indices = list(range(B - k, B)); transferred = []
    if predecessor is not None:
        if (sorted(predecessor) != ["epoch", "indices", "sha256"] or predecessor["epoch"] != int(epoch) - 1
                or not isinstance(predecessor["sha256"], str) or len(predecessor["sha256"]) != 64):
            raise ValueError("predecessor must be {epoch: epoch - 1, sha256, indices}")
        transferred = sorted(set(int(i) for i in predecessor["indices"]) - set(indices))
    idents = man["shard"]["identities"]
    task_digest = hashlib.sha256(json.dumps({str(r): idents[str(r)] for r in reps}, sort_keys=True).encode()).hexdigest()
    return {"schema": SCHEMA, "epoch": int(epoch), "predecessor": predecessor, "provider": "ec2",
            "manifest_sha256": man_sha, "task_identities_sha256": task_digest, "B": B, "reps": reps, "k": k,
            "indices": indices, "transferred_indices": transferred,
            "rule": "EC2 owns (rep, index) for every declared rep and every index in `indices`; Lengau never plans or admits them"}


def load(path, man, man_sha, snapshot_path=None, predecessor_path=None):
    """The partition in `path`, validated against this manifest; raises on any mismatch. Schema 1: recomputed from k.
    Schema 2: structure, manifest, task identities, the bound designated declaration (its bytes at its path) and the owned
    set's digest and range are checked here; with `snapshot_path` AND `predecessor_path` the whole declaration is
    regenerated from those inputs and must be byte-equal in canonical JSON (the `verify2` command)."""
    p = json.load(open(path))
    if p.get("schema") == SCHEMA2:
        why = schema2_problem(p, man, man_sha)
        if why:
            raise ValueError(f"{path}: {why}")
        if snapshot_path is not None or predecessor_path is not None:
            if snapshot_path is None or predecessor_path is None:
                raise ValueError("regeneration needs both the claims snapshot and the predecessor declaration")
            desig, dsha = designated_doc(p)
            pred = load(predecessor_path, man, man_sha)
            want = declare2(man, man_sha, desig, dsha, json.load(open(snapshot_path)), sha_file(snapshot_path), pred,
                            sha_file(predecessor_path), int(p["epoch"]))
            if canonical(want) != canonical(p):
                raise ValueError(f"{path}: not the declaration regenerated from {os.path.basename(snapshot_path)} and its predecessor")
        return p
    if p.get("schema") != SCHEMA:
        raise ValueError(f"{path}: not a {SCHEMA} or {SCHEMA2} declaration")
    want = declare(man, man_sha, int(p["k"]), int(p["epoch"]), p.get("predecessor"))
    diff = [k for k in want if p.get(k) != want[k]] + [k for k in p if k not in want]
    if diff:
        raise ValueError(f"{path}: differs from the manifest-derived declaration on {sorted(set(diff))}")
    return p


_OWNED = {}
def owned_set(part):
    """The EC2-owned coordinates of a partition as a frozenset of (rep, index) (schema 1: reps x indices)."""
    if part.get("schema") == SCHEMA2:
        k = part["owned_sha256"]
        if k not in _OWNED:
            _OWNED[k] = frozenset((int(r), int(i)) for r, ix in part["owned"].items() for i in ix)
        return _OWNED[k]
    return frozenset((int(r), int(i)) for r in part["reps"] for i in part["indices"])


def blocked(part, rep, index):
    if part is None:
        return False
    if part.get("schema") == SCHEMA2:
        return (int(rep), int(index)) in owned_set(part)
    return int(rep) in part["reps"] and int(index) in part["indices"]


def transferred_of(part):
    """What a partition hands back to Lengau: schema 1 indices (all reps), schema 2 always [] (nothing Lengau ever planned
    moves, and no EC2 coordinate is handed back in this schema)."""
    return part["transferred"] if part.get("schema") == SCHEMA2 else part["transferred_indices"]


# ---- schema 2: explicit coordinate-set ownership (REVISION 5) ----------------------------------------------------------------

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def coords_sha(cs):
    return hashlib.sha256(json.dumps(sorted([int(r), int(i)] for r, i in cs)).encode()).hexdigest()


def as_map(cs):
    """{"<rep>": [ascending indices]} with the reps in ascending numeric order (insertion order; sort_keys re-sorts as text)."""
    out = {}
    for r, i in sorted((int(r), int(i)) for r, i in cs):
        out.setdefault(str(r), []).append(i)
    return out


def design_reps(man):
    (lo, hi), res, _, _ = DESIGN_RULE
    return sorted(int(r) for r in man["datasets"]["reps"] if lo <= int(r) <= hi and (int(r) - lo) % 5 in res)


def designated_problem(doc, man, man_sha):
    """'' when `doc` is the adopted designated declaration recomputed from this manifest: S by the ID rule (60 reps, 83
    included), indices exactly 0..79, the smallest 13 to Lengau and the largest 47 to EC2, no ec2_epoch inside it (the
    epoch is THIS file). A subset of row19_screen_admit.designated_shape_problem (v16), recomputed here so this module needs
    no controller import."""
    if not isinstance(doc, dict) or doc.get("schema") != DESIGNATED_SCHEMA:
        return "the designated declaration is not row19-screen-designated-1"
    if doc.get("manifest_sha256") != man_sha:
        return "the designated declaration names another manifest"
    S = design_reps(man); nL, stop = DESIGN_RULE[2], DESIGN_RULE[3]
    if doc.get("reps") != S or len(S) != 60 or 83 not in S:
        return "the designated reps are not S recomputed from the manifest"
    if doc.get("indices") != {"start": 0, "stop": stop} or stop > int(man["cfg"]["n_boot_refit"]):
        return f"the designated indices are not exactly 0..{stop - 1}"
    pv = doc.get("providers") or {}
    if pv.get("lengau_reps") != S[:nL] or pv.get("ec2_reps") != S[nL:] or pv.get("ec2_epoch") is not None:
        return "the designated provider split is not 13 smallest Lengau / 47 largest EC2 with no ec2_epoch"
    return ""


def designated_coords(doc):
    lo, hi = doc["indices"]["start"], doc["indices"]["stop"]
    return {(int(r), i) for r in doc["reps"] for i in range(lo, hi)}


def designated_doc(part):
    """(the designated declaration the epoch binds, its sha256); raises when its bytes are absent or not the bound ones."""
    ref = part["designated"]
    p = DESIGNATED_PATH or os.path.join(T1, ref["path"])
    if not os.path.isfile(p) or sha_file(p) != ref["sha256"]:
        raise ValueError(f"the designated declaration {ref['path']} is absent or not the bound bytes {ref['sha256'][:12]}")
    return json.load(open(p)), ref["sha256"]


def claims_snapshot(man, man_sha, source):
    """The hashed claims snapshot of a screen root/campaign (lengau_claims: every record EC2 did not publish, every plan of
    every ledger entry in any state and every plan file; EC2-published records apart). Raises on any unknown claim."""
    done, planned, problems = lengau_claims(man)
    ec2 = sorted(ec2_completed(man["storage"]["root"], problems))
    if problems:
        raise ValueError(f"the claims are not establishable: {problems[:3]}")
    return {"schema": SNAPSHOT_SCHEMA, "manifest_sha256": man_sha, "source": source,
            "lengau_done": sorted([r, i] for r, i in done), "lengau_planned": sorted([r, i] for r, i in planned),
            "ec2_completed": sorted([r, i] for r, i in ec2), "claims_sha256": claims_digest(done, planned),
            "counts": dict(lengau_done=len(done), lengau_planned=len(planned), ec2_completed=len(ec2))}


def snapshot_problem(snap, man_sha):
    if not isinstance(snap, dict) or snap.get("schema") != SNAPSHOT_SCHEMA:
        return "not a row19-lengau-claims-snapshot-1"
    if snap.get("manifest_sha256") != man_sha:
        return "the snapshot names another manifest"
    try:
        done = {tuple(c) for c in snap["lengau_done"]}; planned = {tuple(c) for c in snap["lengau_planned"]}
        ec2 = {tuple(c) for c in snap["ec2_completed"]}
    except (KeyError, TypeError):
        return "the snapshot's coordinate lists are malformed"
    if claims_digest(done, planned) != snap.get("claims_sha256"):
        return "the snapshot's claims digest does not match its lists"
    if done & ec2:
        return "a coordinate is both Lengau-completed and EC2-completed in the snapshot"
    return ""


def predecessor_ref(pred_doc, pred_sha):
    cs = owned_set(pred_doc)
    return {"epoch": int(pred_doc["epoch"]), "schema": pred_doc["schema"], "sha256": pred_sha, "coordinates": len(cs),
            "coordinates_sha256": coords_sha(cs)}


def classes(desig, snap):
    """The designated cover from a designated declaration and a claims snapshot: (D, lengau_done, ec2_done, lengau_open, owned)."""
    D = designated_coords(desig)
    lengau_reps, ec2_reps = set(desig["providers"]["lengau_reps"]), set(desig["providers"]["ec2_reps"])
    done = {tuple(c) for c in snap["lengau_done"]}; planned = {tuple(c) for c in snap["lengau_planned"]}
    ec2 = {tuple(c) for c in snap["ec2_completed"]}
    claimed = done | planned
    l_done, e_done = D & done, D & ec2
    l_open = {c for c in D if (c[0] in lengau_reps or c in claimed) and c not in done and c not in ec2}
    owned = {c for c in D if c[0] in ec2_reps and c not in claimed and c not in ec2}
    return D, l_done, e_done, l_open, owned


def declare2(man, man_sha, desig, desig_sha, snap, snap_sha, predecessor, predecessor_sha, epoch=2):
    """The schema-2 declaration, deterministically from the manifest, the designated declaration, the claims snapshot and the
    predecessor epoch's declaration document. Raises when an input is invalid."""
    why = designated_problem(desig, man, man_sha) or snapshot_problem(snap, man_sha)
    if why:
        raise ValueError(why)
    epoch = int(epoch)
    if epoch < 2 or not isinstance(predecessor, dict):
        raise ValueError("a schema-2 epoch is epoch 2 or later and names its predecessor")
    pref = predecessor_ref(predecessor, predecessor_sha)
    if pref["epoch"] != epoch - 1 or pref["sha256"] != predecessor_sha or pref["schema"] not in (SCHEMA, SCHEMA2):
        raise ValueError("the predecessor must be epoch - 1, named by its sha256")
    D, l_done, e_done, l_open, owned = classes(desig, snap)
    if not owned:
        raise ValueError("the epoch would own no coordinate")
    pred_cs = set(owned_set(predecessor))
    handback = ((pred_cs - owned) & D) - e_done
    if handback:
        raise ValueError(f"{len(handback)} predecessor coordinate(s) inside the design would be handed back to Lengau; a hand-back "
                         "needs a reviewed Lengau scope change (DESIGN_v16 open point 1), not this schema")
    retired = sorted(pred_cs - owned)
    idents = man["shard"]["identities"]; reps = sorted(int(r) for r in man["datasets"]["reps"])
    task_digest = hashlib.sha256(json.dumps({str(r): idents[str(r)] for r in reps}, sort_keys=True).encode()).hexdigest()
    doc = {"schema": SCHEMA2, "epoch": epoch, "provider": "ec2", "manifest_sha256": man_sha, "task_identities_sha256": task_digest,
           "B": int(man["cfg"]["n_boot_refit"]), "predecessor": pref,
           "designated": {"path": DESIGNATED_REL, "sha256": desig_sha, "reps": len(desig["reps"]),
                          "indices": desig["indices"], "ec2_reps": desig["providers"]["ec2_reps"],
                          "lengau_reps": desig["providers"]["lengau_reps"]},
           "claims_snapshot": {"sha256": snap_sha, "claims_sha256": snap["claims_sha256"], "source": snap["source"],
                               "counts": snap["counts"]},
           "owned": as_map(owned), "owned_count": len(owned), "owned_sha256": coords_sha(owned),
           "transferred": [],
           "retired": dict(count=len(retired), sha256=coords_sha(retired), rule="every predecessor coordinate not owned here is RETIRED: out of the designated "
                           "design, never planned by either provider again; its completed or qualification output stays history/evidence, "
                           "never a screen unit"),
           "cover": {"designated": len(D), "lengau_done": len(l_done), "ec2_done": len(e_done), "lengau_open": len(l_open),
                     "ec2_owned": len(owned)},
           "rule": "EC2 owns exactly the listed (rep, index) coordinates: the designated coordinates of the EC2-designated replicates "
                   "that Lengau had never completed or planned at the claims snapshot; Lengau never plans or admits them; every "
                   "coordinate Lengau ever planned stays Lengau's (nothing transferred)"}
    why = ownership_problem(doc, desig, snap)
    if why:
        raise ValueError(why)
    return doc


def ownership_problem(part, desig, snap):
    """'' when the declaration's ownership is a DISJOINT COVER: D minus every completed coordinate = Lengau's open scope
    (disjoint union) EC2's owned set, recomputed from the designated declaration and the snapshot; the owned set holds no
    Lengau claim and no EC2-completed coordinate and lies on the EC2-designated replicates within 0..79."""
    D, l_done, e_done, l_open, owned = classes(desig, snap)
    got = owned_set(part) if part.get("owned") is not None else frozenset()
    claimed = {tuple(c) for c in snap["lengau_done"]} | {tuple(c) for c in snap["lengau_planned"]}
    if got & claimed:
        return f"{len(got & claimed)} owned coordinate(s) are Lengau claims, e.g. {sorted(got & claimed)[:3]}"
    if got - D:
        return f"{len(got - D)} owned coordinate(s) are outside the designated set"
    if {c for c in got if c[0] not in set(desig['providers']['ec2_reps'])}:
        return "an owned coordinate lies on a Lengau-designated replicate"
    if l_open & got:
        return "Lengau's open scope and the owned set intersect (double ownership)"
    if (l_open | got) != (D - l_done - e_done):
        return "Lengau's open scope and the owned set do not cover the designated coordinates minus done"
    if got != owned:
        return "the owned set is not the unclaimed designated coordinates of the EC2-designated replicates"
    cv = part.get("cover") or {}
    if cv != {"designated": len(D), "lengau_done": len(l_done), "ec2_done": len(e_done), "lengau_open": len(l_open), "ec2_owned": len(got)}:
        return "the declared cover counts are not the recomputed ones"
    return ""


SCHEMA2_KEYS = sorted(["schema", "epoch", "provider", "manifest_sha256", "task_identities_sha256", "B", "predecessor", "designated",
                       "claims_snapshot", "owned", "owned_count", "owned_sha256", "transferred", "retired", "cover", "rule"])


def schema2_problem(p, man, man_sha):
    """Structural validation of a schema-2 declaration against this manifest and its bound designated declaration."""
    if sorted(p) != SCHEMA2_KEYS:
        return f"the declaration's fields are not exactly the schema-2 fields ({sorted(set(p) ^ set(SCHEMA2_KEYS))})"
    idents = man["shard"]["identities"]; reps = sorted(int(r) for r in man["datasets"]["reps"])
    if p["manifest_sha256"] != man_sha or p["provider"] != "ec2" or p["B"] != int(man["cfg"]["n_boot_refit"]):
        return "it names another manifest, provider or B"
    if p["task_identities_sha256"] != hashlib.sha256(json.dumps({str(r): idents[str(r)] for r in reps}, sort_keys=True).encode()).hexdigest():
        return "its task identities are not the manifest's"
    if not (_int(p["epoch"]) and p["epoch"] >= 2):
        return "a schema-2 epoch is 2 or later"
    pr = p["predecessor"]
    if not (isinstance(pr, dict) and sorted(pr) == ["coordinates", "coordinates_sha256", "epoch", "schema", "sha256"]
            and pr["epoch"] == p["epoch"] - 1 and pr["schema"] in (SCHEMA, SCHEMA2) and isinstance(pr["sha256"], str) and len(pr["sha256"]) == 64):
        return "the predecessor reference is not {epoch: epoch - 1, schema, sha256, coordinates, coordinates_sha256}"
    if p["transferred"] != []:
        return "a schema-2 epoch transfers nothing to Lengau"
    try:
        desig, _ = designated_doc(p)
    except (ValueError, OSError) as e:
        return str(e)
    why = designated_problem(desig, man, man_sha)
    if why:
        return why
    if (p["designated"].get("ec2_reps"), p["designated"].get("lengau_reps"), p["designated"].get("indices")) != (
            desig["providers"]["ec2_reps"], desig["providers"]["lengau_reps"], desig["indices"]):
        return "the bound designated split is not the declaration's"
    ow = p["owned"]
    if not (isinstance(ow, dict) and ow and all(isinstance(v, list) and v and v == sorted(set(v)) and all(_int(i) for i in v) for v in ow.values())):
        return "owned is not {rep: ascending unique integer indices}"
    cs = {(int(r), int(i)) for r, ix in ow.items() for i in ix}
    ec2 = set(desig["providers"]["ec2_reps"]); lo, hi = desig["indices"]["start"], desig["indices"]["stop"]
    if any(r not in ec2 or not lo <= i < hi for r, i in cs):
        return "an owned coordinate lies outside the EC2-designated replicates x designated indices"
    if p["owned_count"] != len(cs) or p["owned_sha256"] != coords_sha(cs):
        return "owned_count/owned_sha256 do not match the owned set"
    rt = p["retired"]
    if not (isinstance(rt, dict) and _int(rt.get("count")) and rt["count"] >= 0 and isinstance(rt.get("sha256"), str)):
        return "the retired reference is missing"
    cv = p["cover"]
    if not (isinstance(cv, dict) and cv.get("ec2_owned") == len(cs) and cv.get("designated") == len(designated_coords(desig))
            and cv.get("lengau_done", -1) + cv.get("ec2_done", -1) + cv.get("lengau_open", -1) + cv["ec2_owned"] == cv["designated"]):
        return "the declared cover does not add up to the designated set"
    return ""


def _int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def plan_claims(pp, problems):
    """The (rep, index) claims of one plan file; a plan that is not a well-formed slot list is a problem (R1-1), never empty."""
    try:
        d = json.load(open(pp))
    except Exception as e:
        problems.append(f"plan {os.path.basename(pp)} unreadable ({type(e).__name__}): its claims are unknown"); return set()
    slots = d.get("slots") if isinstance(d, dict) else None
    if not isinstance(slots, list) or not slots:
        problems.append(f"plan {os.path.basename(pp)} has no slot list: its claims are unknown"); return set()
    out = set()
    for s in slots:
        if not (isinstance(s, dict) and _int(s.get("rep")) and isinstance(s.get("indices"), list) and s["indices"]
                and all(_int(i) for i in s["indices"])):
            problems.append(f"plan {os.path.basename(pp)}: malformed slot {s!r:.80}: its claims are unknown"); return set()
        out.update((s["rep"], i) for i in s["indices"])
    return out


def ec2_completed(root, problems):
    """{(rep, index): register entry} for every coordinate the EC2 register published (not Lengau's preexisting ones)."""
    rp = os.path.join(root, "ec2", "register.json")
    if not os.path.exists(rp):
        return {}
    try:
        reg = json.load(open(rp)); atts = reg["attempts"]
    except Exception as e:
        problems.append(f"the EC2 register is unreadable ({type(e).__name__}): EC2 provenance unknown"); return {}
    out = {}
    for aid, e in atts.items():
        if e.get("state") not in ("ingesting", "ingested"):
            continue
        for k, ce in (e.get("coordinates") or {}).items():
            if not ce.get("preexisting"):
                out[tuple(int(x) for x in k.split("/"))] = e
    return out


def lengau_claims(man):
    """Every (rep, index) Lengau has completed (record files EC2 did not publish) or ever planned (plans of ledger entries in
    any state, and plan files without an entry). EC2-published records are reported apart (provider-aware history)."""
    root, camp = man["storage"]["root"], man["storage"]["campaign"]
    done, planned, problems = set(), set(), []
    ec2 = ec2_completed(root, problems)
    for p in glob.glob(os.path.join(root, "records", "rep*", "rec_*.json")):
        try:
            r = int(os.path.basename(os.path.dirname(p))[3:]); i = int(os.path.basename(p)[4:7])
            if (r, i) not in ec2:
                done.add((r, i))
        except ValueError:
            problems.append(f"unparsable record path {p}")
    led = os.path.join(camp, "budget.json")
    entries = list(json.load(open(led))["entries"].values()) if os.path.exists(led) else []
    for e in entries:
        if e.get("kind") != "shard":
            continue
        pp = os.path.join(root, "plans", f"job_{int(e['rep'])}.json")
        if not os.path.exists(pp):
            problems.append(f"ledger entry {e.get('job_id')} (job {e['rep']}, {e.get('state')}) has no plan: its claims are unknown")
            continue
        planned |= plan_claims(pp, problems)
    for pp in glob.glob(os.path.join(root, "plans", "job_*.json")):          # plans with or without a ledger entry
        planned |= plan_claims(pp, problems)
    return done, planned, problems


def historical_partitions(ctl, man, man_sha):
    """{partition sha256: declaration} for every partition any controls version pins (path relative to t1_access); schema 1
    and schema 2 alike (load dispatches)."""
    out = {}
    for v in ctl.get("versions", []):
        ref = v.get("partition")
        if not ref:
            continue
        if not (isinstance(ref, dict) and isinstance(ref.get("path"), str) and ref["path"]):
            continue
        pp = os.path.join(T1, ref["path"])
        if os.path.isfile(pp) and sha_file(pp) == ref.get("sha256"):
            try:
                out[ref["sha256"]] = load(pp, man, man_sha)
            except ValueError:
                pass
    return out


def history_problems(man, man_sha, ctl, extra=None):
    """Every EC2-published coordinate lies in the block of the partition its register entry names (R1-1, later epochs)."""
    problems = []
    hist = historical_partitions(ctl, man, man_sha)
    if extra:
        hist.update(extra)
    for c, e in sorted(ec2_completed(man["storage"]["root"], problems).items()):
        part = hist.get(e.get("partition_sha256"))
        if part is None:
            problems.append(f"EC2 coordinate {c} ({e.get('attempt_id')}): its partition {str(e.get('partition_sha256'))[:12]} is not one any controls version pins")
        elif not blocked(part, *c):
            problems.append(f"EC2 coordinate {c} ({e.get('attempt_id')}): outside the block of its own partition epoch {part['epoch']}")
    return problems


def cutover_problems(man, part):
    done, planned, problems = lengau_claims(man)
    hit_d = sorted(c for c in done if blocked(part, *c)); hit_p = sorted(c for c in planned if blocked(part, *c))
    if hit_d:
        problems.append(f"{len(hit_d)} block coordinate(s) already completed by Lengau, e.g. {hit_d[:3]}")
    if hit_p:
        problems.append(f"{len(hit_p)} block coordinate(s) planned or reserved by Lengau, e.g. {hit_p[:3]}")
    lowest = min((i for _, i in owned_set(part)), default=-1)
    return problems, dict(lengau_done=len(done), lengau_planned=len(planned),
                          lengau_max_index=max([i for _, i in done | planned], default=-1), block_lowest=lowest,
                          **({"owned": len(owned_set(part)), "lengau_claims_on_owned": len(hit_d) + len(hit_p)}
                             if part.get("schema") == SCHEMA2 else {}))


def claims_digest(done, planned):
    return hashlib.sha256(json.dumps(dict(done=sorted(done), planned=sorted(planned))).encode()).hexdigest()


def entry_sha(entry):
    return hashlib.sha256(json.dumps(entry, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def controls_adoption_problem():
    """'' while the canonical controls file is the adopted, review-bound, git-tracked unmodified bytes (programme_gate)."""
    try:
        import programme_gate as PG
        return PG.controls_authority_problem()
    except Exception as e:
        return f"the adoption cannot be checked ({type(e).__name__}: {e})"


def adopted_controls(path=CANONICAL_CONTROLS):
    """(the CURRENT adopted controls document, '') or (None, why) - the only way a canonical consumer reads controls (R2-2)."""
    if os.path.abspath(path) != os.path.abspath(CANONICAL_CONTROLS):
        return None, "canonical consumers read only the canonical controls file"
    why = controls_adoption_problem()
    if why:
        return None, f"the current controls are not the adopted bytes ({why})"
    try:
        return json.load(open(path)), ""
    except Exception as e:
        return None, f"the adopted controls are unreadable ({type(e).__name__})"


def activate(man, man_path, part_path, controls_path=CANONICAL_CONTROLS, now=None, mode="canonical"):
    """The serialized cutover (see the module text). Returns (proof dict, problems); writes nothing itself. `mode` canonical
    requires the adopted canonical controls; `sandbox` (tests, the qualifier's replay) takes any controls file and marks the
    proof so that no canonical consumer accepts it."""
    import row19_ec2_state as ES
    now = time.time() if now is None else now
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    ms = sha_file(man_path); part = load(part_path, man, ms); psha = sha_file(part_path)
    problems = []
    adoption_sha = None
    if mode == "canonical":
        if os.path.abspath(controls_path) != os.path.abspath(CANONICAL_CONTROLS):
            problems.append("a canonical activation reads only the canonical controls file (use mode sandbox for any other)")
        else:
            why = controls_adoption_problem()
            if why:
                problems.append(f"the controls are not the adopted bytes ({why}): the Lengau guard is not proved live")
            adoption_sha = sha_file(ADOPTION) if os.path.exists(ADOPTION) else None
    ctl = json.load(open(controls_path)); latest = ctl["versions"][-1]
    if (latest.get("partition") or {}).get("sha256") != psha:
        problems.append(f"the latest controls version {latest.get('version')} does not pin this partition (the Lengau guard is not live)")
    problems += history_problems(man, ms, ctl, {psha: part})
    if part["predecessor"] is not None:
        prev = activation_path(man, part["predecessor"]["epoch"])
        if not os.path.exists(prev):
            problems.append(f"the predecessor epoch {part['predecessor']['epoch']} was never activated")
        elif json.load(open(prev)).get("partition_sha256") != part["predecessor"]["sha256"]:
            problems.append("the predecessor's activation is not the named predecessor partition")
        if part.get("schema") == SCHEMA2:
            problems += handover_problems(man, part, now)
        elif part["transferred_indices"]:
            invp = ES.paths(man["storage"]["root"])["inventory"]
            inv = json.load(open(invp)) if os.path.exists(invp) else None
            why = ES.inventory_problem(inv, now) if inv is not None else "no authority inventory on the root"
            if why:
                problems.append(f"handback needs a fresh authority inventory: {why}")
            else:
                held = sorted(k for k in inv["owners"] if int(k.split("/")[1]) in part["transferred_indices"])
                if held:
                    problems.append(f"{len(held)} handed-back coordinate(s) still owned by a live EC2 attempt, e.g. {held[:3]}")
    p2, facts = cutover_problems(man, part)
    problems += p2
    done, planned, _ = lengau_claims(man)
    ec2 = sorted(ec2_completed(man["storage"]["root"], []))
    proof = {"schema": ES.ACTIVATION_SCHEMA, "mode": mode, "epoch": part["epoch"], "partition_sha256": psha, "manifest_sha256": ms,
             "controls_sha256": sha_file(controls_path), "controls_version": latest.get("version"),
             "controls_entry_sha256": entry_sha(latest), "adoption_sha256": adoption_sha,
             "predecessor": part["predecessor"], "transferred_indices": transferred_of(part),
             **({"owned_sha256": part["owned_sha256"], "claims_snapshot_sha256": part["claims_snapshot"]["claims_sha256"]}
                if part.get("schema") == SCHEMA2 else {}),
             "claims_sha256": claims_digest(done, planned), "ec2_completed_sha256": claims_digest(set(ec2), set()),
             "facts": dict(facts, ec2_completed=len(ec2)), "at": now}
    return proof, problems


def handover_problems(man, part, now):
    """REVISION 5: what a schema-2 activation needs beyond the cutover scan - the INSTALLED authority inventory on the root,
    sealed and fresh at `now`, showing (1) no attempt owning any coordinate outside this epoch's owned set (the predecessor's
    retired block included: an epoch-1 owner such as the reconciled Q1 attempt must be dispositioned and fenced first) and
    (2) no live (intent/launched/ambiguous) attempt of another epoch's runs; and the claims snapshot it was declared from
    still agreeing on the owned set (a newer Lengau claim on an owned coordinate is refused by the cutover scan itself)."""
    import row19_ec2_state as ES
    out = []
    inv, why = ES.installed_inventory(man["storage"]["root"], now=now)
    if why:
        return [f"a schema-2 activation needs the root's fresh installed authority inventory: {why}"]
    own = owned_set(part)
    outside = sorted(k for k in inv["owners"] if tuple(int(x) for x in k.split("/")) not in own)
    if outside:
        out.append(f"{len(outside)} coordinate(s) outside epoch {part['epoch']} are still owned by an EC2 attempt (e.g. {outside[:3]}, "
                   f"{sorted({inv['owners'][k][0] for k in outside})[:3]}): disposition and fence them first (prod_authority.py disposition, ec2_sync)")
    mine = (f"prod-e{part['epoch']}/", f"qual-E{part['epoch']}")
    live = sorted(k for k, a in inv["attempts"].items() if a.get("state") in ES.LIVE_STATES and not k.startswith(mine))
    if live:
        out.append(f"live attempt(s) of another epoch {live[:3]}: resolve them before the epoch changes")
    return out


def activation_path(man, epoch):
    return os.path.join(man["storage"]["root"], "ec2", f"activation_e{int(epoch)}.json")


def activation_problem(man, man_sha, part, part_sha, proof, controls=None, mode="canonical"):
    """'' when `proof` is THE activation of this partition under this manifest, made in `mode` (consumers: both admissions,
    ingestion, the launcher, the qualifier). With `controls` (the current controls document) the proof's version entry must
    be byte-identical there and every version from it to the latest must still pin this partition (R1-1). In mode canonical
    the controls are the CURRENT ADOPTED ones (adopted_controls, R2-2); a supplied document must be exactly those."""
    if not isinstance(proof, dict) or proof.get("schema") != "row19-ec2-activation-1":
        return "no activation proof"
    if proof.get("mode") != mode:
        return f"the activation proof is a {proof.get('mode')!r} proof, not {mode!r}"
    extra = (("owned_sha256", part["owned_sha256"]),) if part.get("schema") == SCHEMA2 else ()
    for k, v in (("epoch", part["epoch"]), ("partition_sha256", part_sha), ("manifest_sha256", man_sha),
                 ("transferred_indices", transferred_of(part))) + extra:
        if proof.get(k) != v:
            return f"the activation proof's {k} is not this partition's"
    if mode == "canonical" and not (isinstance(proof.get("adoption_sha256"), str) and len(proof["adoption_sha256"]) == 64):
        return "the canonical activation proof names no controls adoption"
    if mode == "canonical":
        cur, why = adopted_controls()
        if why:
            return why
        if controls is not None and controls != cur:
            return "the supplied controls are not the current adopted controls"
        controls = cur
    if controls is None:
        return "no controls document to check the activation proof's lineage against"
    vs = controls.get("versions") or []
    at = [i for i, v in enumerate(vs) if v.get("version") == proof.get("controls_version")]
    if len(at) != 1 or entry_sha(vs[at[0]]) != proof.get("controls_entry_sha256"):
        return f"the activation's controls version {proof.get('controls_version')} is not byte-identical in the current controls"
    if any((v.get("partition") or {}).get("sha256") != part_sha for v in vs[at[0]:]):
        return "a controls version after the activation no longer pins this partition: the proof is historical"
    return ""


def main(argv=None):
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("declare"); d.add_argument("--manifest", required=True); d.add_argument("--k", type=int, required=True)
    d.add_argument("--epoch", type=int, required=True); d.add_argument("--out", required=True)
    d.add_argument("--predecessor", default=None, help="the predecessor epoch's declaration file (every epoch after 1)")
    c = sub.add_parser("cutover"); c.add_argument("--manifest", required=True); c.add_argument("--partition", required=True)
    v = sub.add_parser("activate"); v.add_argument("--manifest", required=True); v.add_argument("--partition", required=True)
    s = sub.add_parser("snapshot", help="REVISION 5: the hashed Lengau claims snapshot (on Lengau, under the plan lock; or of a local copy)")
    s.add_argument("--manifest", required=True); s.add_argument("--out", required=True)
    s.add_argument("--root", default=None, help="read this copy of the screen root instead of the manifest's (a pulled snapshot)")
    s.add_argument("--campaign", default=None, help="read this copy of the campaign instead of the manifest's")
    s.add_argument("--receipt", default=None, help="the whole-role refit receipt this copy belongs to (bound by name and sha256)")
    d2 = sub.add_parser("declare2", help="REVISION 5: a schema-2 (explicit coordinate set) epoch")
    v2 = sub.add_parser("verify2", help="REVISION 5: regenerate a schema-2 declaration from its inputs and compare")
    for q in (d2, v2):
        q.add_argument("--manifest", required=True); q.add_argument("--designated", required=True)
        q.add_argument("--snapshot", required=True); q.add_argument("--predecessor", required=True)
    d2.add_argument("--epoch", type=int, required=True); d2.add_argument("--out", required=True); v2.add_argument("--partition", required=True)
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); ms = sha_file(a.manifest)
    if a.cmd == "snapshot":
        if os.path.exists(a.out):
            sys.exit(f"{a.out} exists: a snapshot is immutable")
        m2 = json.loads(json.dumps(man))
        m2["storage"] = {"root": a.root or man["storage"]["root"], "campaign": a.campaign or man["storage"]["campaign"]}
        copy = bool(a.root or a.campaign)
        src = {"root": os.path.abspath(m2["storage"]["root"]), "campaign": os.path.abspath(m2["storage"]["campaign"]),
               "copy": copy, "plan_lock": "not taken (copy)" if copy else "held",
               "receipt": os.path.basename(a.receipt) if a.receipt else None, "receipt_sha256": sha_file(a.receipt) if a.receipt else None}
        if copy:
            snap = claims_snapshot(m2, ms, src)
        else:                                                     # REVISION 6 (ruling 1): the canonical scan under the plan lock
            with open(os.path.join(man["storage"]["root"], "plans", ".submit.lock"), "a+") as lk:
                try:
                    fcntl.flock(lk.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError:
                    print("HELD: the plan lock is held (an admission, an activation or an ingestion): no snapshot"); return 3
                snap = claims_snapshot(m2, ms, src)
        json.dump(snap, open(a.out, "w"), indent=1, sort_keys=True)
        print(f"snapshot {a.out} sha256 {sha_file(a.out)}: {snap['counts']}"); return 0
    if a.cmd in ("declare2", "verify2"):
        global DESIGNATED_PATH
        DESIGNATED_PATH = os.path.abspath(a.designated)
        pred = load(a.predecessor, man, ms)
        if a.cmd == "verify2":
            load(a.partition, man, ms, snapshot_path=a.snapshot, predecessor_path=a.predecessor)
            print(f"verified {a.partition} sha256 {sha_file(a.partition)}"); return 0
        if os.path.exists(a.out):
            sys.exit(f"{a.out} exists: a declaration is immutable; declare a new epoch instead")
        doc = declare2(man, ms, json.load(open(a.designated)), sha_file(a.designated), json.load(open(a.snapshot)),
                       sha_file(a.snapshot), pred, sha_file(a.predecessor), a.epoch)
        json.dump(doc, open(a.out, "w"), indent=1, sort_keys=True)
        print(f"declared epoch {a.epoch} (schema 2): owned {doc['owned_count']}, cover {doc['cover']}, sha256 {sha_file(a.out)}"); return 0
    if a.cmd == "declare":
        if os.path.exists(a.out):
            sys.exit(f"{a.out} exists: a declaration is immutable; declare a new epoch instead")
        pred = None
        if a.predecessor:
            pp = json.load(open(a.predecessor))
            pred = dict(epoch=pp["epoch"], sha256=sha_file(a.predecessor), indices=pp["indices"])
        json.dump(declare(man, ms, a.k, a.epoch, pred), open(a.out, "w"), indent=1, sort_keys=True)
        print(f"declared epoch {a.epoch}: k {a.k}, sha256 {sha_file(a.out)}"); return 0
    if a.cmd == "activate":
        root = man["storage"]["root"]
        with open(os.path.join(root, "plans", ".submit.lock"), "a+") as lk:
            try:
                fcntl.flock(lk.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                print("HELD: the plan lock is held (an admission or an ingestion)"); return 3
            proof, problems = activate(man, a.manifest, a.partition)        # canonical only: the adopted controls file
            out = activation_path(man, proof["epoch"])
            if os.path.exists(out):
                print(f"HELD: {out} exists - an activation is immutable"); return 3
            if problems:
                print(json.dumps(dict(problems=problems, facts=proof["facts"]))); return 3
            os.makedirs(os.path.dirname(out), exist_ok=True)
            tmp = f"{out}.tmp.{os.getpid()}"
            with open(tmp, "w") as fh:
                json.dump(proof, fh, indent=1, sort_keys=True); fh.flush(); os.fsync(fh.fileno())
            os.link(tmp, out); os.unlink(tmp)
        print(f"activated epoch {proof['epoch']}: {out} sha256 {sha_file(out)}"); return 0
    part = load(a.partition, man, ms)
    problems, facts = cutover_problems(man, part)
    print(json.dumps(dict(partition=os.path.basename(a.partition), partition_sha256=sha_file(a.partition), **facts, problems=problems)))
    return 3 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
