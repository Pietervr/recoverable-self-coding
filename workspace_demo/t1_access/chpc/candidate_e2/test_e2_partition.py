"""EC2 provider epoch 2 CANDIDATE (NOT adopted): tests of the schema-2 partition (chpc/candidate_e2/row19_partition.py
REVISION 5) on the Mac, pure python, no fits, no Lengau, no AWS. Design reviews/2026-10-17_row19_resize_codex.md s.3, s.4,
s.6 item 5; Codex v16 review reviews/2026-10-17_v16_p80_codex_review.md s.A item 1.

  1. the generated declaration (row19_partition_e2.json) regenerates byte-for-byte from its hashed inputs (manifest, the
     v16 designated declaration, the claims snapshot of the 17 Oct 17:00Z receipt, the e1 file);
  2. ownership is a DISJOINT COVER of the 4,800 designated coordinates minus done, recomputed;
  3. no double ownership with Lengau: no snapshot claim (done or ever planned, any state) is owned; the v16 planner's scope
     and order never reach an owned coordinate; Lengau's claims on the 47 EC2 replicates stay Lengau's;
  4. the predecessor link: epoch 2 names e1 by sha256, retires its whole block (4,000), transfers nothing; a wrong epoch,
     a hand-back to Lengau or an edited declaration refuses;
  5. activation in a sandbox root: the predecessor's activation is required, the installed fresh inventory must show no
     owner outside the epoch (the e1 Q1 attempt fenced first), no live attempt of another epoch, and a Lengau claim made after
     the snapshot on an owned coordinate refuses; the proof's lineage check covers the owned digest.

    python3 chpc/candidate_e2/test_e2_partition.py            (from workspace_demo/t1_access)"""
import copy, hashlib, importlib.util, json, os, shutil, sys, tempfile, time

CAND = os.path.dirname(os.path.abspath(__file__)); CHPC = os.path.dirname(CAND); T1 = os.path.dirname(CHPC)
for p in (T1, CHPC, CAND):
    sys.path.insert(0, p)


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m); return m


RP = load_mod("row19_partition", os.path.join(CAND, "row19_partition.py"))
import row19_ec2_state as ES
fails, n_checks = [], [0]


def check(name, cond, extra=""):
    n_checks[0] += 1
    print(("ok   " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        fails.append(name)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def refuses(fn):
    try:
        fn(); return False
    except ValueError:
        return True


MAN_PATH = os.path.join(CHPC, "row19_screen_manifest.json"); MAN = json.load(open(MAN_PATH)); MAN_SHA = sha(MAN_PATH)
DESIG_PATH = os.path.join(CHPC, "candidate_v16", "row19_screen_designated.json"); DESIG = json.load(open(DESIG_PATH))
E1_PATH = os.path.join(CHPC, "row19_partition_e1.json"); E1 = RP.load(E1_PATH, MAN, MAN_SHA)
E2_PATH = os.path.join(CAND, "row19_partition_e2.json"); SNAP_PATH = os.path.join(CAND, "claims_snapshot_e2.json")
RP.DESIGNATED_PATH = DESIG_PATH                                 # before the v16 promotion the declaration lives in candidate_v16/
S = [r for r in range(3, 103) if (r - 3) % 5 in (0, 1, 2)]; L13, E47 = S[:13], S[13:]

# ---- 1. the generated declaration -------------------------------------------------------------------------------------------
E2 = RP.load(E2_PATH, MAN, MAN_SHA)
check("the e2 declaration loads (schema 2, epoch 2, provider ec2, manifest 43b75f94)",
      E2["schema"] == RP.SCHEMA2 and E2["epoch"] == 2 and E2["provider"] == "ec2" and E2["manifest_sha256"] == MAN_SHA)
check("it regenerates byte-for-byte from the snapshot and the predecessor (verify2)",
      RP.load(E2_PATH, MAN, MAN_SHA, snapshot_path=SNAP_PATH, predecessor_path=E1_PATH) is not None)
SNAP = json.load(open(SNAP_PATH))
again = RP.declare2(MAN, MAN_SHA, DESIG, sha(DESIG_PATH), SNAP, sha(SNAP_PATH), E1, sha(E1_PATH), 2)
check("generation is deterministic (two runs, identical canonical bytes)", RP.canonical(again) == RP.canonical(E2))
check("it binds the designated declaration (a96eb598), the snapshot and its claims digest",
      E2["designated"]["sha256"] == sha(DESIG_PATH) == "a96eb59833ff794d3f9ce0ca09ada03d045a29cb9f8a676dad86f8aba85d5584"
      and E2["claims_snapshot"]["sha256"] == sha(SNAP_PATH) and E2["claims_snapshot"]["claims_sha256"] == SNAP["claims_sha256"])
check("the snapshot is the 17 Oct 17:00Z receipt's copy (bound by name and sha256)",
      SNAP["source"]["receipt"] == "watch_refit_20261017T170047Z.json" and SNAP["source"]["copy"] is True
      and SNAP["source"]["receipt_sha256"] == sha(os.path.join(CHPC, "results", "row19_screen", "receipts", "watch_refit_20261017T170047Z.json")))

# ---- 2. disjoint cover ------------------------------------------------------------------------------------------------------
D, l_done, e_done, l_open, owned = RP.classes(DESIG, SNAP)
own = set(RP.owned_set(E2))
print("   cover:", E2["cover"])
check("D = S x 0..79 = 4,800", len(D) == 4800 and D == {(r, i) for r in S for i in range(80)})
check("cover on the 17 Oct snapshot: 499 done + 1,027 Lengau open + 3,274 EC2 owned = 4,800 (design s.3: 3,274 new EC2)",
      E2["cover"] == {"designated": 4800, "lengau_done": 499, "ec2_done": 0, "lengau_open": 1027, "ec2_owned": 3274})
check("Lengau open and EC2 owned are disjoint", not (l_open & own))
check("Lengau open + EC2 owned = D minus done, exactly", (l_open | own) == D - l_done - e_done)
check("ownership_problem recomputes the cover from the inputs", RP.ownership_problem(E2, DESIG, SNAP) == "")
check("every owned coordinate is on one of the 47 EC2-designated replicates, index 0..79", all(r in E47 and 0 <= i < 80 for r, i in own))
check("the 13 Lengau replicates own nothing on EC2", not any(r in L13 for r, _ in own))

# ---- 3. no double ownership with Lengau -------------------------------------------------------------------------------------
claimed = {tuple(c) for c in SNAP["lengau_done"]} | {tuple(c) for c in SNAP["lengau_planned"]}
on47 = {c for c in claimed if c[0] in E47 and c in D}
check("no snapshot claim (done or ever planned, any ledger state) is EC2-owned", not (claimed & own))
check("Lengau's claims on the 47 EC2 replicates stay Lengau's (design s.3/s.4) and are not owned",
      on47 and not (on47 & own) and on47 - l_done <= l_open, len(on47))
print(f"   Lengau claims on the 47 EC2 replicates inside the design: {len(on47)} ({len(on47 - l_done)} not yet done)")
for c in ((24, 0), (83, 2), (43, 4)):
    check(f"claimed coordinate {c} (completed or crash-rescue-pending) is Lengau's, never EC2's", c in claimed and not RP.blocked(E2, *c))
check("an unclaimed coordinate of an EC2 replicate is owned (24/79)", RP.blocked(E2, 24, 79) and (24, 79) not in claimed)
check("index 80+ and epoch-1's 160..199 are not owned by epoch 2", not RP.blocked(E2, 24, 80) and not RP.blocked(E2, 24, 199))
# the v16 Lengau planner with this partition: scope and replicate-complete order never touch an owned coordinate
SA = load_mod("row19_screen_admit", os.path.join(CHPC, "candidate_v16", "row19_screen_admit.py"))
doc = dict(DESIG, _sha256=sha(DESIG_PATH))
scope = SA.lengau_scope(doc, {tuple(c) for c in SNAP["lengau_planned"]})
check("v16 lengau_scope and the e2 owned set are disjoint", not (scope & own))
check("v16 lengau_scope (minus done) + e2 owned = D minus done (nothing falls between the providers)",
      ((scope - l_done) | own) == D - l_done - e_done)
order = SA.designated_order(doc, l_done, set(), {tuple(c) for c in SNAP["lengau_planned"]}, {}, E2)
check("the v16 replicate-complete order with the e2 partition plans no owned coordinate", not ({(r, ix[0]) for r, ix in order} & own) and order)
jobs = [{"job": 46, "slots": [{"slot": 0, "rep": 24, "indices": [79]}]}]
check("the v16 admission check refuses a supplied plan holding an owned coordinate",
      SA.designated_problem(jobs, doc, l_done, set(), {tuple(c) for c in SNAP["lengau_planned"]}, {}, E2) != ""
      and SA.partition_problem(jobs, E2) != "")

# ---- 4. the predecessor link ------------------------------------------------------------------------------------------------
pr = E2["predecessor"]
e1_block = {(r, i) for r in range(3, 103) for i in range(160, 200)}
check("predecessor = epoch 1, schema 1, its file sha256 8d1de408, 4,000 coordinates",
      pr == {"epoch": 1, "schema": RP.SCHEMA, "sha256": sha(E1_PATH), "coordinates": 4000, "coordinates_sha256": RP.coords_sha(e1_block)}
      and sha(E1_PATH).startswith("8d1de408"))
check("the whole e1 block is RETIRED (out of design), nothing transferred to Lengau",
      E2["retired"]["count"] == 4000 and E2["retired"]["sha256"] == RP.coords_sha(e1_block) and E2["transferred"] == [] and not (own & e1_block))
check("Q1's 48 coordinates (198/199 of reps 3..26) are retired, never epoch-2 units", not any(RP.blocked(E2, r, i) for r in range(3, 27) for i in (198, 199)))
check("a predecessor of the wrong epoch refuses", refuses(lambda: RP.declare2(MAN, MAN_SHA, DESIG, sha(DESIG_PATH), SNAP, sha(SNAP_PATH), E1, sha(E1_PATH), 3)))
check("a predecessor named by another sha256 refuses at load of the regenerated file",
      refuses(lambda: RP.load(E2_PATH, MAN, MAN_SHA, snapshot_path=SNAP_PATH, predecessor_path=MAN_PATH)))
# an epoch 3 whose snapshot shows Lengau claiming an e2-owned coordinate would hand it back: refused in this schema
d = tempfile.mkdtemp(); e2f = os.path.join(d, "e2.json"); json.dump(E2, open(e2f, "w"))
snap3 = copy.deepcopy(SNAP); snap3["lengau_planned"] = sorted(snap3["lengau_planned"] + [[24, 79]])
snap3["claims_sha256"] = RP.claims_digest({tuple(c) for c in snap3["lengau_done"]}, {tuple(c) for c in snap3["lengau_planned"]})
check("a hand-back of an owned coordinate to Lengau refuses (needs a reviewed Lengau scope change)",
      refuses(lambda: RP.declare2(MAN, MAN_SHA, DESIG, sha(DESIG_PATH), snap3, "0" * 64, E2, sha(e2f), 3)))
e3 = RP.declare2(MAN, MAN_SHA, DESIG, sha(DESIG_PATH), SNAP, "1" * 64, E2, sha(e2f), 3)
check("an epoch 3 on an unchanged snapshot carries the same owned set and names e2 (schema 2 predecessor)",
      e3["owned_sha256"] == E2["owned_sha256"] and e3["predecessor"]["schema"] == RP.SCHEMA2 and e3["retired"]["count"] == 0)

# tampering: every edit of the stored declaration refuses at load
def tampered(fn):
    t = copy.deepcopy(E2); fn(t); p = os.path.join(d, "t.json"); json.dump(t, open(p, "w"))
    return refuses(lambda: RP.load(p, MAN, MAN_SHA))
check("tamper: an extra owned coordinate (a Lengau rep) refuses", tampered(lambda t: t["owned"].setdefault("3", []).append(79)))
check("tamper: a dropped owned coordinate refuses (digest)", tampered(lambda t: t["owned"]["24"].pop()))
check("tamper: owned_count refuses", tampered(lambda t: t.update(owned_count=3273)))
check("tamper: a non-empty transfer refuses", tampered(lambda t: t.update(transferred=[[24, 0]])))
check("tamper: another manifest refuses", tampered(lambda t: t.update(manifest_sha256="0" * 64)))
check("tamper: another designated digest refuses", tampered(lambda t: t["designated"].update(sha256="0" * 64)))
check("tamper: a predecessor reference of the wrong shape refuses", tampered(lambda t: t["predecessor"].pop("coordinates_sha256")))
check("tamper: cover counts that do not add up refuse", tampered(lambda t: t["cover"].update(lengau_open=1026)))
check("tamper: an extra field refuses", tampered(lambda t: t.update(k=40)))
t = copy.deepcopy(E2); t["owned"]["24"] = t["owned"]["24"][:-1]; t["owned_count"] -= 1; t["owned_sha256"] = RP.coords_sha(
    {(int(r), i) for r, ix in t["owned"].items() for i in ix}); t["cover"] = dict(t["cover"], ec2_owned=3273, lengau_open=1028)
pt = os.path.join(d, "t2.json"); json.dump(t, open(pt, "w"))
check("a self-consistent edit (one coordinate moved to Lengau with digests redone) passes structure but fails regeneration",
      RP.load(pt, MAN, MAN_SHA) is not None and refuses(lambda: RP.load(pt, MAN, MAN_SHA, snapshot_path=SNAP_PATH, predecessor_path=E1_PATH)))
desig_bad = os.path.join(d, "desig.json"); dd = copy.deepcopy(DESIG); dd["rule"] += " "; json.dump(dd, open(desig_bad, "w"))
RP.DESIGNATED_PATH = desig_bad
check("a changed designated declaration on disk refuses the epoch (bound bytes)", refuses(lambda: RP.load(E2_PATH, MAN, MAN_SHA)))
RP.DESIGNATED_PATH = DESIG_PATH

# ---- 5. activation in a sandbox root ----------------------------------------------------------------------------------------
sb = tempfile.mkdtemp(); root = os.path.join(sb, "root"); camp = os.path.join(sb, "camp")
for sub in ("plans", "ec2"):
    os.makedirs(os.path.join(root, sub))
os.makedirs(camp)
claims_sb = {(3, 0), (3, 1), (24, 0), (24, 1), (25, 0)}                     # Lengau: rep 3 (its own) and claims on EC2 reps 24/25
for r, i in sorted(claims_sb - {(25, 0)}):
    os.makedirs(os.path.join(root, "records", f"rep{r}"), exist_ok=True); open(os.path.join(root, "records", f"rep{r}", f"rec_{i:03d}.json"), "w").write("{}")
json.dump({"job": 1, "slots": [{"slot": k, "rep": r, "indices": [i]} for k, (r, i) in enumerate(sorted(claims_sb))]}, open(os.path.join(root, "plans", "job_1.json"), "w"))
json.dump({"entries": {"t1": {"kind": "shard", "rep": 1, "state": "live", "job_id": "1.s"}}}, open(os.path.join(camp, "budget.json"), "w"))
sm = copy.deepcopy(MAN); sm["storage"] = {"root": root, "campaign": camp}; smp = os.path.join(sb, "manifest.json"); json.dump(sm, open(smp, "w")); smsha = sha(smp)
sdes = os.path.join(sb, "designated.json"); json.dump(dict(DESIG, manifest_sha256=smsha), open(sdes, "w")); RP.DESIGNATED_PATH = sdes
se1 = RP.declare(sm, smsha, 40, 1); se1p = os.path.join(sb, "e1.json"); json.dump(se1, open(se1p, "w"))
ctl = os.path.join(sb, "controls.json")
json.dump({"versions": [{"version": 13, "partition": {"path": "x", "sha256": sha(se1p)}}]}, open(ctl, "w"))
proof1, pr1 = RP.activate(sm, smp, se1p, ctl, mode="sandbox")
check("sandbox: epoch 1 activates on the clean sandbox root", pr1 == [], pr1)
snap_sb = RP.claims_snapshot(sm, smsha, {"root": root, "note": "sandbox"}); sp = os.path.join(sb, "snap.json"); json.dump(snap_sb, open(sp, "w"))
se2 = RP.declare2(sm, smsha, json.load(open(sdes)), sha(sdes), snap_sb, sha(sp), se1, sha(se1p), 2)
se2p = os.path.join(sb, "e2.json"); json.dump(se2, open(se2p, "w"))
check("sandbox e2 owns every unclaimed designated coordinate of the 47 and none of Lengau's claims",
      se2["owned_count"] == 47 * 80 - 3 and not RP.blocked(se2, 24, 0) and not RP.blocked(se2, 25, 0) and RP.blocked(se2, 25, 1))
json.dump({"versions": [{"version": 13, "partition": {"path": "x", "sha256": sha(se1p)}},
                        {"version": 17, "partition": {"path": "y", "sha256": sha(se2p)}}]}, open(ctl, "w"))
_, pr2 = RP.activate(sm, smp, se2p, ctl, mode="sandbox")
check("sandbox: epoch 2 refuses before epoch 1 was activated (predecessor proof required)", any("never activated" in x for x in pr2), pr2)
json.dump(proof1, open(RP.activation_path(sm, 1), "w"))
_, pr2 = RP.activate(sm, smp, se2p, ctl, mode="sandbox")
check("sandbox: epoch 2 refuses without an installed authority inventory", any("installed authority inventory" in x for x in pr2), pr2)


def inventory(atts, gen):
    own = {}
    for k, a in atts.items():
        if ES.owns(a):
            for c in a["coordinates"]:
                own[f"{c[0]}/{c[1]}"] = [k, a["sequence"]]
    fence = {}
    for k, a in atts.items():
        if a["state"] != "rejected":
            for c in a["coordinates"]:
                fence[f"{c[0]}/{c[1]}"] = max(fence.get(f"{c[0]}/{c[1]}", -1), a["sequence"])
    return ES.seal(dict(schema=ES.INVENTORY_SCHEMA, generation=gen, at=time.time(), attempts=atts, owners=dict(sorted(own.items())),
                        fence=fence, release={}, usd={}))


def att(key, seq, state, ingestion, coords, cls="qualification"):
    run, n = key.split("/")
    return dict(key=key, run=run, attempt=int(n), attempt_id=f"ec2-{run}-a{n}", sequence=seq, state=state, ingestion=ingestion,
                contract="Q1", plan_sha256="p" * 64, coordinates=[list(c) for c in coords], sentinels=[], duplicates=[], charged_usd=26.14,
                disposition_requested=False, **{"class": cls})


Q1BLOCK = [(r, i) for i in (199, 198) for r in range(3, 27)]
ident = dict(root=os.path.abspath(root), manifest_sha256=smsha, mode="sandbox")
_, why = ES.install_inventory(root, inventory({"qual-Q1/4": att("qual-Q1/4", 5, "reconciled", "pending", Q1BLOCK)}, 2), ident)
_, pr2 = RP.activate(sm, smp, se2p, ctl, mode="sandbox")
check("sandbox: epoch 2 refuses while the e1 Q1 attempt still OWNS its retired block (disposition + fence first)",
      why == [] and any("outside epoch 2" in x and "qual-Q1/4" in x for x in pr2), pr2)
_, why = ES.install_inventory(root, inventory({"qual-Q1/4": att("qual-Q1/4", 5, "reconciled", "dispositioned", Q1BLOCK),
                                              "prod-e1/1": att("prod-e1/1", 6, "launched", "pending", [], "production")}, 3), ident)
_, pr2 = RP.activate(sm, smp, se2p, ctl, mode="sandbox")
check("sandbox: epoch 2 refuses while an attempt of another epoch is live", any("live attempt" in x for x in pr2), pr2)
_, why = ES.install_inventory(root, inventory({"qual-Q1/4": att("qual-Q1/4", 5, "reconciled", "dispositioned", Q1BLOCK),
                                              "qual-Q2/1": att("qual-Q2/1", 7, "reconciled", "pending", [])}, 4), ident)
proof2, pr2 = RP.activate(sm, smp, se2p, ctl, mode="sandbox")
check("sandbox: epoch 2 activates once Q1 is fenced (Q2 owns nothing and does not block)", why == [] and pr2 == [], pr2)
C = json.load(open(ctl))
check("the e2 proof names the owned digest, transfers nothing and passes activation_problem",
      proof2["owned_sha256"] == se2["owned_sha256"] and proof2["transferred_indices"] == []
      and RP.activation_problem(sm, smsha, se2, sha(se2p), proof2, C, "sandbox") == "")
check("activation_problem refuses an e2 proof whose owned digest differs",
      RP.activation_problem(sm, smsha, se2, sha(se2p), dict(proof2, owned_sha256="0" * 64), C, "sandbox") != "")
check("the e1 proof is historical once a later version pins e2 (lineage)",
      "historical" in RP.activation_problem(sm, smsha, se1, sha(se1p), proof1, C, "sandbox"))
json.dump({"job": 2, "slots": [{"slot": 0, "rep": 25, "indices": [1]}]}, open(os.path.join(root, "plans", "job_2.json"), "w"))
_, pr3 = RP.activate(sm, smp, se2p, ctl, mode="sandbox")
check("a Lengau claim made after the snapshot on an owned coordinate refuses activation (re-snapshot, re-declare)",
      any("planned or reserved by Lengau" in x for x in pr3), pr3)
cp_, facts = RP.cutover_problems(sm, se2)
check("the cutover facts of a schema-2 epoch report the owned count and the Lengau hits", facts["owned"] == se2["owned_count"] and facts["lengau_claims_on_owned"] == 1)
RP.DESIGNATED_PATH = DESIG_PATH
hist = RP.historical_partitions({"versions": [{"partition": {"path": os.path.relpath(E1_PATH, T1), "sha256": sha(E1_PATH)}},
                                              {"partition": {"path": os.path.relpath(E2_PATH, T1), "sha256": sha(E2_PATH)}}]}, MAN, MAN_SHA)
check("historical_partitions loads schema 1 and schema 2 pins alike", set(hist) == {sha(E1_PATH), sha(E2_PATH)})
shutil.rmtree(sb); shutil.rmtree(d)
print(f"\n{n_checks[0] - len(fails)}/{n_checks[0]} {'ALL OK' if not fails else f'- {len(fails)} FAILED'}")
sys.exit(1 if fails else 0)
