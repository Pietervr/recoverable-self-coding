"""EC2 provider epoch 2 QUALIFICATION CANDIDATE (NOT adopted): the epoch-2 release branch and the epoch-2 qualification gates
of chpc/candidate_e2q/aws_ec2/prod_authority.py (REVISION 7), prod_launch.py (REVISION 7) and qual_permit.py (REVISION 2).
Pure python on the Mac, no AWS, no Lengau; every ledger and release-state write goes to a temporary authority directory.
The REAL inputs are read only: the candidate epoch-2 partition (87edfb9e), its claims snapshot and funding declaration, the
pinned reconciled Q2 ledger attempt (the A4 basis), the production manifest 43b75f94 and the candidate panel fixture.

  1. a valid schema-3 certificate + its FAVOURABLE epoch-2 review releases exactly the E2Q1 attempt;
  2. the release is refused without EACH prerequisite (review, verdict, literal, outcome, R1'..R5' evidence, code set and
     bytes, manifest, partition pin, exact funding bytes and the authenticated basis, both operational manifests, lifetime,
     panel, the reconciled attempt and its plan, the E2Q2 rule, the qualification-instance counter);
  3. an epoch-1 (schema-2) certificate can never release epoch 2, and an epoch-1 release never admits epoch-2 production;
  4. release_state / release-adopt: production stays shut until a qualification_e2 permission, a schema-3 RELEASE
     certificate, a favourable review and release-adopt all exist; the released epoch and bound production manifest gate
     the production admission;
  5. the USD 300 allowance counters bind (2 qualification instances, base + 4 production attempts, the money);
  6. conformance: the certificate the qualifier actually writes (test_e2q_qualify world) satisfies the release branch's
     evidence checks once its environment bindings are the Mac's.

    python3 chpc/candidate_e2q/test_e2q_release.py            (from workspace_demo/t1_access)"""
import copy, hashlib, importlib.util, json, os, shutil, sys, tempfile, time

Q = os.path.dirname(os.path.abspath(__file__)); CHPC = os.path.dirname(Q); T1 = os.path.dirname(CHPC); E2 = os.path.join(CHPC, "candidate_e2")
AWS = os.path.join(T1, "aws_ec2")
for p in (T1, AWS, CHPC, E2, Q, os.path.join(Q, "aws_ec2")):
    sys.path.insert(0, p)


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m); return m


ES = load_mod("row19_ec2_state", os.path.join(Q, "row19_ec2_state.py"))
RP = load_mod("row19_partition", os.path.join(E2, "row19_partition.py"))
EQ = load_mod("row19_ec2_e2qual", os.path.join(Q, "row19_ec2_e2qual.py"))
PA = load_mod("prod_authority", os.path.join(Q, "aws_ec2", "prod_authority.py"))
PL = load_mod("prod_launch", os.path.join(Q, "aws_ec2", "prod_launch.py"))
QP = load_mod("qual_permit", os.path.join(Q, "aws_ec2", "qual_permit.py"))
import bench_launch as L
fails, n_checks = [], [0]


def check(name, cond, extra=""):
    n_checks[0] += 1
    print(("ok   " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""), flush=True)
    if not cond:
        fails.append(name)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


MAN_PATH = os.path.join(CHPC, "row19_screen_manifest.json"); MAN = json.load(open(MAN_PATH))
PART_PATH = os.path.join(E2, "row19_partition_e2.json"); PSHA = sha(PART_PATH); E2P = RP.load(PART_PATH, MAN, PA.PROD_SHA)
FUND_PATH = os.path.join(E2, "aws_ec2", "e2_funding.json"); FUND = json.load(open(FUND_PATH))
PANEL_PATH = os.path.join(Q, "fixture", "panel_e2q_e2_candidate87ed.json"); PANEL = json.load(open(PANEL_PATH))
SNAP_PATH = os.path.join(T1, PANEL["claims_snapshot"]["path"])
TMP = tempfile.mkdtemp()
for f in ("budget_baseline.json", "ec2_release_state.json"):
    shutil.copy(os.path.join(AWS, f), os.path.join(TMP, f))
os.makedirs(os.path.join(TMP, "runs", "qual-Q2"))
shutil.copy(os.path.join(AWS, "runs", "qual-Q2", "attempts.json"), os.path.join(TMP, "runs", "qual-Q2", "attempts.json"))   # the pinned A4 basis, read-only copy
L.HERE = PA.HERE = TMP
PA.LOCK, PA.STATE = os.path.join(TMP, "runs", ".authority.lock"), os.path.join(TMP, "runs", ".authority_state.json")
PA.INV_DIR, PA.RELEASE_STATE = os.path.join(TMP, "runs", "inventory"), os.path.join(TMP, "ec2_release_state.json")
PA.E2_FUNDING, PA.E2Q_PANEL = FUND_PATH, PANEL_PATH
REAL_PINNED = PA.pinned_partition
PA.pinned_partition = lambda: (E2P, PSHA)                       # as controls v17 will pin it
KEY, AID, SEQ = "qual-E2Q1/1", "ec2-qual-E2Q1-a1", 60
SENT = [[3, 0], [3, 1], [4, 0], [5, 0]]
OPS = dict(qualified=ES.sha_bytes(EQ.opmanifest_bytes(ES, MAN, PA.PROD_SHA, "E2Q1")),
           production=ES.sha_bytes(EQ.opmanifest_bytes(ES, MAN, PA.PROD_SHA, "production")))
check("the candidate E2Q1 operational manifest file IS the bytes the release branch rederives",
      sha(os.path.join(Q, "aws_ec2", "prod", "manifest_e2q1_e2.json")) == OPS["qualified"]
      and sha(os.path.join(E2, "aws_ec2", "prod", "manifest_production_e2.json")) == OPS["production"])


def write_plan(run, n, contract, work, dups, sent, extra=None):
    slots = [dict(slot=k, rep=r, indices=[i], role=role) for k, (role, (r, i)) in
             enumerate([("work", c) for c in work] + [("qual_lengau", c) for c in dups] + [("sentinel", c) for c in sent])]
    plan = dict(job=n, attempt_id=f"ec2-{run}-a{n}", sequence=SEQ + n - 1 if run == "qual-E2Q1" else SEQ + 10 + n, epoch=2, contract=contract,
                partition_sha256=PSHA, opmanifest_sha256=ES.sha_bytes(EQ.opmanifest_bytes(ES, MAN, PA.PROD_SHA, contract)),
                activation_sha256="a" * 64, instance=dict(ES.CONTRACTS[contract]), lifetime_s=79200, slots=slots)
    plan.update(extra or {})
    os.makedirs(L.run_dir(run), exist_ok=True)
    pp = os.path.join(L.run_dir(run), f"plan_attempt{n}.json"); json.dump(plan, open(pp, "w"), indent=1)
    return pp, plan


def e2q_attempt(run, n, contract, state="reconciled", ingestion="pending", compute_s=21 * 3600, plan_extra=None, work=None):
    pp, plan = write_plan(run, n, contract, work or PANEL["work"], PANEL["duplicates"], SENT, plan_extra)
    return dict(attempt=n, sequence=plan["sequence"], attempt_id=plan["attempt_id"], contract=contract, state=state, ingestion=ingestion,
                plan=pp, plan_sha256=sha(pp), coordinates=[list(c) for c in (work or PANEL["work"])], sentinels=SENT, duplicates=PANEL["duplicates"],
                lifetime_s=79200, max_price=1.20, anc_h=PA.ANC_H_PROD, s3_fixed=PA.S3_FIXED_PROD, type="c7a.24xlarge",
                **({"terminal": dict(compute_s=compute_s, ancillary_s=compute_s)} if state == "reconciled" else {}))


def reset_ledgers(e2q1=None, e2q2=None):
    for run in ("qual-E2Q1", "qual-E2Q2", "prod-e2"):          # the ledgers only: plan files the arguments just wrote stay
        p = os.path.join(L.run_dir(run), "attempts.json")
        if os.path.exists(p):
            os.remove(p)
    L.save("qual-E2Q1", {"run": "qual-E2Q1", "attempts": e2q1 if e2q1 is not None else [e2q_attempt("qual-E2Q1", 1, "E2Q1")]})
    if e2q2 is not None:
        L.save("qual-E2Q2", {"run": "qual-E2Q2", "attempts": e2q2})


SYN = [dict(file=f, original_sha256="1" * 64, modified_sha256=None, label="SYNTHETIC: removed") for f in ("root/records/x", "root/timing/x", "root/status/x")] + \
      [dict(file="env/outcomes.json", original_sha256="2" * 64, modified_sha256="3" * 64, label="SYNTHETIC: outcome set to fatal signal 139"),
       dict(file="BUNDLE_SHA256SUMS", original_sha256="4" * 64, modified_sha256="5" * 64, label="SYNTHETIC: checksums regenerated")]


def cert_doc(key=KEY, contract="E2Q1"):
    run, _, n = key.partition("/")
    a = next(x for x in L.load(run)["attempts"] if str(x["attempt"]) == n)
    return dict(schema=EQ.CERT_SCHEMA, epoch=2, outcome="RELEASE", problems=[], coverage_required=dict(EQ.COVERAGE), coverage_short={},
                parts=dict(R1=dict(coordinates=20, compared=20, unproduced=[], successful_both=20, failed_both=0, nonfinite_both=0),
                           R4_sentinels=dict(coordinates=4, compared=4, unproduced=[], successful_both=4, failed_both=0, nonfinite_both=0),
                           R2_validity=dict(coordinates=52, produced=52, unproduced=[], failed=0, nonfinite=0, limitation="validity only")),
                memory=dict(samples=1270, samples_at_full_packing=1200, unmatched_samples=0, workers=76, peak_host_used_gib=151.0),
                concentration=dict(slots=76, max=61, max_reps=[24], per_rep={}, qualified_rep_slots=61), unproduced=[], max_unproduced=3,
                replay=dict(scope=EQ.REPLAY_SCOPE, presented_class="production", forced_stop_rc=3, state_after_stop="ingesting", replay_rc=0,
                            second_replay_rc=0, final_state="ingested", hashes_equal=True,
                            per_slot=dict(mode="synthetic", slot=0, coordinate="24/11", outcome=139, ingest_rc=0, listed=True, fenced=True,
                                          evidence_journaled=True, ack_problem="", modified_replay_rc=3, modified_replay_held=True,
                                          activation_problems=[], synthetic=copy.deepcopy(SYN))),
                released_attempts=[key], attempt=dict(key=key, run=run, contract=contract, attempt_id=a["attempt_id"], sequence=a["sequence"],
                                                      plan_sha256=a["plan_sha256"]),
                bound=dict(code={rel: sha(EQ.code_path(T1, rel, True)) for rel in EQ.CODE}, manifest_sha256=PA.PROD_SHA, partition_sha256=PSHA,
                           owned_sha256=E2P["owned_sha256"], activation_sha256="a" * 64, inventory_sha256="b" * 64, panel_sha256=sha(PANEL_PATH),
                           claims_snapshot_sha256=sha(SNAP_PATH), funding_sha256=sha(FUND_PATH), lifetime_s=79200,
                           opmanifests=dict(OPS, qualified=ES.sha_bytes(EQ.opmanifest_bytes(ES, MAN, PA.PROD_SHA, contract))),
                           bundle_sha256="c" * 64, plan_sha256=a["plan_sha256"]))


def write_cert(doc, name="cert_e2.json"):
    cp = os.path.join(TMP, name); json.dump(doc, open(cp, "w"), indent=1); return cp


def review(cp, verdict="FAVOURABLE", keys=KEY, literal=None, name="review_e2.md"):
    rp = os.path.join(TMP, name)
    lit = literal or EQ.RELEASE_LITERAL.format(sha=sha(cp), keys=keys)
    open(rp, "w").write(f"# actual-result review of the epoch-2 qualification\n{verdict}\n{lit}\n"); return rp


def rel_with(mut, keys_review=KEY):
    doc = cert_doc(); mut(doc); cp = write_cert(doc); return PA.release_problem(cp, review(cp, keys=keys_review))


def refused(res, needle):
    return res[0] == [] and needle in res[1]


# ---- 1. valid --------------------------------------------------------------------------------------------------------------
reset_ledgers()
cp = write_cert(cert_doc())
check("a valid schema-3 certificate with its FAVOURABLE epoch-2 review releases exactly the E2Q1 attempt",
      PA.release_problem(cp, review(cp)) == ([KEY], ""), PA.release_problem(cp, review(cp)))
check("the shared constants: coverage R1 15 of 20, code set without the S files, with the shared rules, the panel and the state module",
      EQ.COVERAGE == {"R1": 15} and "chpc/row19_ec2_shadow.py" not in EQ.CODE and {"chpc/row19_ec2_e2rules.py", "chpc/row19_ec2_e2qual.py",
                                                                                   "chpc/row19_ec2_state.py"} <= set(EQ.CODE) and PA.E2_RELEASE_CODE == EQ.CODE)

# ---- 2. each prerequisite --------------------------------------------------------------------------------------------------
cp = write_cert(cert_doc())
check("refused: a review without FAVOURABLE", refused(PA.release_problem(cp, review(cp, verdict="pending")), "FAVOURABLE"))
rp = review(cp); os.remove(rp)
check("refused: a missing review", refused(PA.release_problem(cp, rp), "unreadable"))
lit1 = f"RELEASE row19-ec2-qualification certificate={sha(cp)} attempts={KEY}"
check("refused: a review carrying the EPOCH-1 literal form (no epoch=2)", refused(PA.release_problem(cp, review(cp, literal=lit1)), "epoch-2 literal"))
check("refused: a review naming another attempt", refused(PA.release_problem(cp, review(cp, keys="qual-E2Q1/2")), "literal"))
check("refused: outcome INCONCLUSIVE", refused(rel_with(lambda d: d.update(outcome="INCONCLUSIVE")), "schema-3 epoch-2 RELEASE"))
check("refused: a certificate carrying a problem", refused(rel_with(lambda d: d.update(problems=["x"])), "schema-3 epoch-2 RELEASE"))
check("refused: R1' 14 finite successful (< 15)", refused(rel_with(lambda d: d["parts"]["R1"].update(successful_both=14)), "R1'"))
check("refused: R2' a work coordinate neither produced nor unproduced", refused(rel_with(lambda d: d["parts"]["R2_validity"].update(produced=51)), "R2'"))
check("refused: R4' 9 samples at the full packing", refused(rel_with(lambda d: d["memory"].update(samples_at_full_packing=9)), "memory"))
check("refused: R4' memory sampled at 75 workers", refused(rel_with(lambda d: d["memory"].update(workers=75)), "memory"))
check("refused: R4' peak host use 185 GiB", refused(rel_with(lambda d: d["memory"].update(peak_host_used_gib=185.0)), "memory"))
check("refused: R4' four non-completions", refused(rel_with(lambda d: d.update(unproduced=[dict(slot=k, outcome=139) for k in range(4)])), "non-completed"))
check("refused: R4' a non-completion of no qualifying kind (exit 1)", refused(rel_with(lambda d: d.update(unproduced=[dict(slot=1, outcome=1)])), "qualifying kind"))
check("refused: R4' concentration 60 (< 61)", refused(rel_with(lambda d: d["concentration"].update(max=60)), "concentration"))
check("refused: R5' replay left 'ingesting'", refused(rel_with(lambda d: d["replay"].update(final_state="ingesting")), "R5'"))
check("refused: R5' another scope", refused(rel_with(lambda d: d["replay"].update(scope="producer restart demonstrated")), "R5'"))
check("refused: R5' not presented as production (the per-slot branch would not have run)", refused(rel_with(lambda d: d["replay"].update(presented_class="qualification")), "R5'"))
check("refused: R5' synthetic case whose modified replay did NOT hold", refused(rel_with(lambda d: d["replay"]["per_slot"].update(modified_replay_held=False)), "per-slot"))
check("refused: R5' a synthetic modification not labelled SYNTHETIC", refused(rel_with(lambda d: d["replay"]["per_slot"]["synthetic"][0].update(label="removed")), "per-slot"))
check("refused: R5' the ack rule did not release", refused(rel_with(lambda d: d["replay"]["per_slot"].update(ack_problem="published + unproduced differ")), "per-slot"))
check("refused: R5' per-slot not fenced", refused(rel_with(lambda d: d["replay"]["per_slot"].update(fenced=False)), "per-slot"))
check("refused: the code set without the shared rules file", refused(rel_with(lambda d: d["bound"]["code"].pop("chpc/row19_ec2_e2rules.py")), "code set"))
check("refused: stale code bytes (the ingestion)", refused(rel_with(lambda d: d["bound"]["code"].update({"chpc/row19_ec2_ingest.py": "0" * 64})), "current bytes"))
check("refused: another manifest", refused(rel_with(lambda d: d["bound"].update(manifest_sha256="0" * 64)), "43b75f94"))
check("refused: another partition digest", refused(rel_with(lambda d: d["bound"].update(partition_sha256="0" * 64)), "partition"))
check("refused: another owned digest", refused(rel_with(lambda d: d["bound"].update(owned_sha256="0" * 64)), "partition"))
PA.pinned_partition = REAL_PINNED
check("refused: the current controls pin epoch 1 (the live controls), not the epoch-2 partition", refused(rel_with(lambda d: None), "partition"))
PA.pinned_partition = lambda: (None, PSHA)
check("refused: the pinned partition bytes are not at the pinned path", refused(rel_with(lambda d: None), "partition"))
PA.pinned_partition = lambda: (E2P, PSHA)
check("refused: other funding bytes than bound", refused(rel_with(lambda d: d["bound"].update(funding_sha256="0" * 64)), "funding"))
f2 = dict(FUND, epoch_cap_usd=3857.04); fp2 = os.path.join(TMP, "e2_funding_doubled.json"); json.dump(f2, open(fp2, "w"))
PA.E2_FUNDING = fp2
check("refused: a coherently re-bound funding file on another basis (A4: rederived from the pinned Q2 ledger attempt)",
      refused(rel_with(lambda d: d["bound"].update(funding_sha256=sha(fp2))), "funding:"))
PA.E2_FUNDING = FUND_PATH
check("refused: the qualified operational manifest digest differs", refused(rel_with(lambda d: d["bound"]["opmanifests"].update(qualified="0" * 64)), "operational manifests"))
check("refused: the production operational manifest digest differs", refused(rel_with(lambda d: d["bound"]["opmanifests"].update(production="0" * 64)), "operational manifests"))
check("refused: another lifetime", refused(rel_with(lambda d: d["bound"].update(lifetime_s=75300)), "operational manifests"))
check("refused: another panel digest", refused(rel_with(lambda d: d["bound"].update(panel_sha256="0" * 64)), "panel"))
check("refused: another claims snapshot digest", refused(rel_with(lambda d: d["bound"].update(claims_snapshot_sha256="0" * 64)), "panel"))
check("refused: released attempts beyond the E2Q attempt", refused(rel_with(lambda d: d.update(released_attempts=[KEY, "prod-e2/1"]), keys_review=f"{KEY},prod-e2/1"), "released attempts"))
check("refused: an attempt of another contract", refused(rel_with(lambda d: d["attempt"].update(contract="Q1")), "E2Q1/E2Q2"))
reset_ledgers([e2q_attempt("qual-E2Q1", 1, "E2Q1", state="launched")])
check("refused: the ledger attempt is not reconciled", refused(rel_with(lambda d: None), "reconciled ledger attempt"))
reset_ledgers()
pp = L.load("qual-E2Q1")["attempts"][0]["plan"]; doc = cert_doc(); open(pp, "a").write(" ")
cp = write_cert(doc); check("refused: the plan file is not the attempt's plan bytes", refused(PA.release_problem(cp, review(cp)), "plan"))
other = PANEL["work"][1:] + [[24, 63]]
reset_ledgers([e2q_attempt("qual-E2Q1", 1, "E2Q1", work=other)])
check("refused: a reconciled attempt whose plan is not the declared panel", refused(rel_with(lambda d: None), "declared panel"), rel_with(lambda d: None))
reset_ledgers([e2q_attempt("qual-E2Q1", 1, "E2Q1", plan_extra=dict(lifetime_s=75300))])
check("refused: a plan at another lifetime", refused(rel_with(lambda d: None), "declared panel"), rel_with(lambda d: None))
reset_ledgers([e2q_attempt("qual-E2Q1", 1, "E2Q1", state="reconciled", ingestion="pending")], [e2q_attempt("qual-E2Q2", 1, "E2Q2")])
d2 = cert_doc("qual-E2Q2/1", "E2Q2"); cp = write_cert(d2)
check("refused: an E2Q2 release while E2Q1 was NOT dispositioned (E2Q2 is the external-cause retry only)",
      refused(PA.release_problem(cp, review(cp, keys="qual-E2Q2/1")), "dispositioned"))
reset_ledgers([e2q_attempt("qual-E2Q1", 1, "E2Q1", ingestion="dispositioned")], [e2q_attempt("qual-E2Q2", 1, "E2Q2")])
d2 = cert_doc("qual-E2Q2/1", "E2Q2"); cp = write_cert(d2)
check("an E2Q2 release after E2Q1 was dispositioned releases exactly E2Q2", PA.release_problem(cp, review(cp, keys="qual-E2Q2/1")) == (["qual-E2Q2/1"], ""),
      PA.release_problem(cp, review(cp, keys="qual-E2Q2/1")))
reset_ledgers([e2q_attempt("qual-E2Q1", 1, "E2Q1", ingestion="dispositioned"), e2q_attempt("qual-E2Q1", 2, "E2Q1", ingestion="dispositioned")],
              [e2q_attempt("qual-E2Q2", 1, "E2Q2")])
d2 = cert_doc("qual-E2Q2/1", "E2Q2"); cp = write_cert(d2)
check("refused: three non-rejected epoch-2 qualification instances exceed the allowance counter (2)",
      refused(PA.release_problem(cp, review(cp, keys="qual-E2Q2/1")), "allowance counter"))
reset_ledgers()

# ---- 3. epoch 1 can never open epoch 2 ----------------------------------------------------------------------------------------
e1code = {f: L.sha256(os.path.join(PA.T1, f)) for f in PA.RELEASE_CODE}
L.save("qual-Q1", {"run": "qual-Q1", "attempts": [dict(attempt=1, sequence=50, attempt_id="ec2-qual-Q1-a1", state="reconciled", ingestion="pending",
                                                       contract="Q1", plan_sha256="q1plan", coordinates=[], lifetime_s=79200, max_price=1.2,
                                                       anc_h=PA.ANC_H_PROD, s3_fixed=PA.S3_FIXED_PROD, terminal=dict(compute_s=60, ancillary_s=60))]})
def e1cert(psha):
    c = dict(schema=PA.CERT_SCHEMA, outcome="RELEASE", problems=[], coverage_short={}, parts={"R1": dict(successful_both=20), "R2": dict(successful_both=40),
             "R3": dict(successful_both=20)}, memory=dict(samples_at_full_packing=30, peak_host_used_gib=170.0), replay=dict(final_state="ingested",
             hashes_equal=True, scope="x"), released_attempts=["qual-Q1/1"], q1=dict(key="qual-Q1/1", attempt_id="ec2-qual-Q1-a1", sequence=50, plan_sha256="q1plan"),
             bound=dict(code=e1code, manifest_sha256=PA.PROD_SHA, partition_sha256=psha, plans={"Q1": "q1plan"}))
    return write_cert(c, "cert_e1.json")
def e1review(cp):
    rp = os.path.join(TMP, "review_e1.md"); open(rp, "w").write(f"FAVOURABLE\nRELEASE row19-ec2-qualification certificate={sha(cp)} attempts=qual-Q1/1\n"); return rp
cp = e1cert(PSHA)
check("an epoch-1 (schema-2) certificate cannot release epoch 2, even bound to the epoch-2 partition digest",
      refused(PA.release_problem(cp, e1review(cp)), "cannot release a schema-2 epoch"))
saved_pin = PA.controls_partition_sha
PA.controls_partition_sha = lambda: PSHA
check("... the guard holds even if the epoch-1 branch's own partition comparison would pass",
      refused(PA.release_problem(cp, e1review(cp)), "cannot release a schema-2 epoch"))
PA.controls_partition_sha = saved_pin
PA.pinned_partition = REAL_PINNED
e1sha = PA.controls_partition_sha(); PA.controls_partition_sha = lambda: e1sha
cp = e1cert(e1sha)
check("control: with epoch 1 pinned the same epoch-1 certificate shape passes the epoch-1 branch (the guard is epoch-specific)",
      PA.release_problem(cp, e1review(cp)) == (["qual-Q1/1"], ""), PA.release_problem(cp, e1review(cp)))
PA.controls_partition_sha = saved_pin
PA.pinned_partition = lambda: (E2P, PSHA)
shutil.rmtree(L.run_dir("qual-Q1"))
check("a schema-3 certificate is never judged by the epoch-1 branch (dispatch on schema)",
      refused(PA.release_problem_e1(write_cert(cert_doc()), review(write_cert(cert_doc()))), "schema-2 RELEASE"))

# ---- 4. release_state / release-adopt / the production gate ------------------------------------------------------------------
reset_ledgers()
r = json.load(open(PA.RELEASE_STATE)); open(os.path.join(TMP, "r23.json"), "w").write("{}")
r["row23"] = dict(declared_success=True, report_path="r23.json", report_sha256=sha(os.path.join(TMP, "r23.json")))
r["qualification"].update(permitted=False)
r.pop("qualification_e2", None)
json.dump(r, open(PA.RELEASE_STATE, "w"))
cp = write_cert(cert_doc()); rp = review(cp)
r = json.load(open(PA.RELEASE_STATE)); r["production"] = dict(released=True, certificate_path="cert_e2.json", certificate_sha256=sha(cp),
                                                             review_path="review_e2.md", review_sha256=sha(rp), released_attempts=[KEY])
json.dump(r, open(PA.RELEASE_STATE, "w"))
rel = PA.release_state()
check("production stays SHUT with a valid adopted epoch-2 certificate but no qualification_e2 permission", not rel["production"]["ok"] and not rel["qualification_e2"]["ok"])
check("the live release state carries no qualification_e2 block: epoch-2 qualification is not permitted today",
      "qualification_e2" not in json.load(open(os.path.join(AWS, "ec2_release_state.json"))))
open(os.path.join(TMP, "e2q_permit.md"), "w").write("reviewed E2Q1 permission\n")
check("qual_permit --e2q2 refuses before the epoch-2 qualification itself is permitted",
      QP.permit("e2q_permit.md", wait_s=1, log=lambda *x: None, epoch2=True, e2q2=True) == 3)
rc = QP.permit("e2q_permit.md", wait_s=1, log=lambda *x: None, epoch2=True)
rel = PA.release_state()
check("qual_permit --epoch2 drains, fences and writes qualification_e2 (record pinned); the epoch-1 block is untouched",
      rc == 0 and rel["qualification_e2"]["ok"] and os.path.exists(L.fence_path()) and rel["qualification"].get("permitted") is False
      and rel["qualification_e2"]["record_sha256"] == sha(os.path.join(TMP, "e2q_permit.md")))
check("... and then the adopted epoch-2 certificate reads RELEASED for epoch 2 with its bound production manifest",
      rel["production"]["ok"] and rel["production"]["epoch"] == 2 and rel["production"]["production_opmanifest_sha256"] == OPS["production"]
      and rel["production"]["derived_released_attempts"] == [KEY], rel["production"]["why"])
r = json.load(open(PA.RELEASE_STATE)); r["production"] = dict(released=False, certificate_path=None, certificate_sha256=None, review_path=None,
                                                             review_sha256=None, released_attempts=[]); json.dump(r, open(PA.RELEASE_STATE, "w"))
try:
    PA.release_adopt("cert_e2.json", "missing_review.md"); ok_ = False
except ValueError:
    ok_ = True
check("release-adopt refuses without the review (production unchanged)", ok_ and not PA.release_state()["production"]["ok"])
check("release-adopt from the valid epoch-2 certificate writes the production block; release_state reads it released for epoch 2",
      PA.release_adopt("cert_e2.json", "review_e2.md") == [KEY] and PA.release_state()["production"]["ok"] and PA.release_state()["production"]["epoch"] == 2)
rel = PA.release_state(); leds = PA.ledgers()
check("production admission gate: epoch 2 with the bound production manifest passes", PL.gate_problem("production", 2, rel, leds, OPS["production"]) == "")
check("production admission gate: epoch 2 with another operational manifest refuses", "bound" in PL.gate_problem("production", 2, rel, leds, "0" * 64))
check("production admission gate: the epoch-2 release never admits epoch-1 production", "epoch 2, not epoch 1" in PL.gate_problem("production", 1, rel, leds, OPS["production"]))
r = json.load(open(PA.RELEASE_STATE)); r["production"]["released_attempts"] = [KEY, "qual-E2Q2/1"]; json.dump(r, open(PA.RELEASE_STATE, "w"))
check("a release state listing other attempts than the certificate releases is NOT released", not PA.release_state()["production"]["ok"])
r["production"]["released_attempts"] = [KEY]; json.dump(r, open(PA.RELEASE_STATE, "w"))
PA.pinned_partition = REAL_PINNED
check("an adopted epoch-2 release reads NOT released while the controls pin another partition (live controls: epoch 1)", not PA.release_state()["production"]["ok"])
PA.pinned_partition = lambda: (E2P, PSHA)
fake1 = dict(production=dict(ok=True, epoch=1, production_opmanifest_sha256=None))
check("an epoch-1 release never admits epoch-2 production", "epoch 1, not epoch 2" in PA.production_release_problem(fake1, 2, OPS["production"]))

# ---- 5. allowance counters and the E2Q admission rule ------------------------------------------------------------------------
rel = PA.release_state()
reset_ledgers([])
check("E2Q1 admission: permitted, no earlier instance -> allowed", PA.e2q_admission_problem("E2Q1", rel, PA.ledgers()) == "")
check("E2Q1 admission refused without the qualification_e2 permission", "does not permit" in PA.e2q_admission_problem("E2Q1", dict(rel, qualification_e2={}), PA.ledgers()))
reset_ledgers([e2q_attempt("qual-E2Q1", 1, "E2Q1", state="rejected")])
check("a capacity-rejected E2Q1 (no instance ever existed) does not consume E2Q1", PA.e2q_admission_problem("E2Q1", rel, PA.ledgers()) == "")
reset_ledgers([e2q_attempt("qual-E2Q1", 1, "E2Q1")])
check("a second non-rejected E2Q1 is refused (no retry by outcome)", "ONE instance" in PA.e2q_admission_problem("E2Q1", rel, PA.ledgers()))
check("E2Q2 refused without its own reviewed record", "own reviewed permission" in PA.e2q_admission_problem("E2Q2", rel, PA.ledgers()))
open(os.path.join(TMP, "e2q2_permit.md"), "w").write("reviewed E2Q2 permission: E2Q1 spot-interrupted before the memory gate\n")
check("qual_permit --epoch2 --e2q2 writes the E2Q2 record once epoch-2 qualification is permitted",
      QP.permit("e2q2_permit.md", wait_s=1, log=lambda *x: None, epoch2=True, e2q2=True) == 0 and PA.release_state()["qualification_e2"]["e2q2_ok"])
rel = PA.release_state()
check("E2Q2 refused while E2Q1 is not dispositioned (it may still hold a usable bundle)", "dispositioned" in PA.e2q_admission_problem("E2Q2", rel, PA.ledgers()))
reset_ledgers([e2q_attempt("qual-E2Q1", 1, "E2Q1", ingestion="dispositioned")])
check("E2Q2 allowed after E2Q1 was reconciled and dispositioned, with its record", PA.e2q_admission_problem("E2Q2", rel, PA.ledgers()) == "")
reset_ledgers([e2q_attempt("qual-E2Q1", 1, "E2Q1", ingestion="dispositioned")], [e2q_attempt("qual-E2Q2", 1, "E2Q2")])
check("a second E2Q2 is refused", "at most one" in PA.e2q_admission_problem("E2Q2", rel, PA.ledgers()))
WORST = PA.worst_usd(PA.QUAL_LIFETIME_S, 1.20)
check("epoch2_problem: two non-rejected qual-E2 instances -> a third refuses (allowance counter 2)",
      "qualification instance" in PA.epoch2_problem(PA.ledgers(), "qual-E2Q3", WORST, FUND))
def prod_att(n, compute_s=3600):
    return dict(attempt=n, sequence=1000 + n, attempt_id=f"ec2-prod-e2-a{n}", contract="production", state="reconciled", ingestion="ingested",
                plan_sha256="p", coordinates=[], lifetime_s=79200, max_price=1.2, anc_h=PA.ANC_H_PROD, s3_fixed=PA.S3_FIXED_PROD,
                terminal=dict(compute_s=compute_s, ancillary_s=compute_s))
reset_ledgers([e2q_attempt("qual-E2Q1", 1, "E2Q1", ingestion="dispositioned", compute_s=60)])
L.save("prod-e2", {"run": "prod-e2", "attempts": [prod_att(n, 60) for n in range(1, 51)]})
check("epoch2_problem: base 46 + 4 extra production attempts used -> the 51st refuses",
      "base 46 + 4 extra" in PA.epoch2_problem(PA.ledgers(), "prod-e2", WORST, FUND))
L.save("prod-e2", {"run": "prod-e2", "attempts": [prod_att(n, 60) for n in range(1, 47)]})
reset_ledgers([e2q_attempt("qual-E2Q1", 1, "E2Q1", ingestion="dispositioned", compute_s=int(3600 * 115))],
              [e2q_attempt("qual-E2Q2", 1, "E2Q2", compute_s=int(3600 * 115))])
L.save("prod-e2", {"run": "prod-e2", "attempts": [prod_att(n, 60) for n in range(1, 47)]})
al = sum(PA.charged(a) for r_ in ("qual-E2Q1", "qual-E2Q2") for a in L.load(r_)["attempts"])
check(f"epoch2_problem: the allowance money binds - two qualification instances charged USD {al:.2f} leave no room for a first extra production batch",
      al + WORST > 300 and "allowance" in PA.epoch2_problem(PA.ledgers(), "prod-e2", WORST, FUND))
check("... while a base production batch (the 46th is base, not allowance) is judged by the epoch cap, not the allowance",
      "allowance" not in PA.epoch2_problem({k: v for k, v in PA.ledgers().items() if k != "prod-e2"} | {"prod-e2": {"attempts": [prod_att(n, 60) for n in range(1, 46)]}},
                                           "prod-e2", WORST, FUND))
shutil.rmtree(L.run_dir("prod-e2"))

# ---- 6. conformance with the qualifier's actual certificate --------------------------------------------------------------------
reset_ledgers()
src = open(os.path.join(Q, "test_e2q_qualify.py")).read().split("# 1 clean")[0]
g = {"__file__": os.path.join(Q, "test_e2q_qualify.py"), "__name__": "conformance"}
exec(compile(src, "test_e2q_qualify(header)", "exec"), g)
PA_mods = {k: sys.modules.get(k) for k in ("row19_ec2_state", "row19_partition", "row19_ec2_e2qual")}
for case, kw in (("conf_clean", {}), ("conf_actual", dict(unprod={20: 139}))):
    _, qcert, qw = g["world"](case, **kw)
    mine = cert_doc()
    qcert.update(attempt=mine["attempt"], released_attempts=mine["released_attempts"], bound=dict(mine["bound"], code=dict(mine["bound"]["code"])))
    qcert["bound"]["code"] = {rel_: sha(EQ.code_path(T1, rel_, True)) for rel_ in EQ.CODE}
    cp = write_cert(qcert, f"cert_{case}.json")
    check(f"conformance ({case}): the qualifier's own parts / memory / concentration / unproduced / replay evidence passes the release branch",
          qcert["outcome"] == "RELEASE" and PA.release_problem(cp, review(cp, name=f"review_{case}.md")) == ([KEY], ""),
          PA.release_problem(cp, review(cp, name=f"review_{case}.md"))[1])
    world_ = "B" if qcert["replay"]["per_slot"]["mode"] == "synthetic" else "A"
    regp = os.path.join(qw["d"], "sb", world_, "root", "ec2", "register.json")
    ent = json.load(open(regp))["attempts"][g["AID"]]
    run_ = "qual-E2Q1-sandbox-ack"
    L.save(run_, {"run": run_, "attempts": [dict(attempt=1, sequence=ent["sequence"], attempt_id=ent["attempt_id"], state="reconciled", ingestion="pending",
                                                  contract="E2Q1", plan_sha256=ent["plan_sha256"], coordinates=[list(c) for c in qw["work"]])]})
    ent_key = dict(ent, key=f"{run_}/1"); reg_ = json.load(open(regp)); reg_["attempts"][g["AID"]] = ent_key
    regp2 = os.path.join(TMP, f"register_{case}.json"); json.dump(reg_, open(regp2, "w"))
    check(f"conformance ({case}): the REAL Mac `ack` accepts the sandbox register entry of the per-slot case (published + unproduced = owned)",
          PA.ack(run_, 1, regp2) is True and L.load(run_)["attempts"][0]["ingestion"] == "ingested")
    shutil.rmtree(L.run_dir(run_))
shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{n_checks[0] - len(fails)}/{n_checks[0]} {'ALL OK' if not fails else f'- {len(fails)} FAILED'}")
sys.exit(1 if fails else 0)
