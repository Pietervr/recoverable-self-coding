"""Controls v17 CANDIDATE (NOT adopted): tests of chpc/candidate_v17 on the Mac, pure python, no AWS, no Lengau, no live write.
Design chpc/candidate_v17/DESIGN_v17.md.

  1. the candidate: build_v17.py is deterministic; versions 1-16 byte-identical to the adopted v16 controls; v17 changes exactly
     the partition pin and the seven controller pins; every pin = its candidate source bytes; the admission = the adopted v16
     admission + exactly the hunk of candidate_e2/admit_v17_partition_line.diff; promote_v17.py's candidate check passes;
  2. admission on the schema-2 partition: v16's print line raises KeyError ('indices'); v17 prints the explicit-set line and
     goes on; the schema-1 line is unchanged;
  3. refit admission HOLDS between v17 adoption and the epoch-2 activation (activation_problem_v10), and opens only on an
     activation of THIS partition made under a controls version that still pins it;
  4. the epoch-1 release path cannot open epoch 2 under the REAL v17 controls bytes (prod_authority REVISION 7 guard).

    python3 chpc/candidate_v17/test_v17.py            (from workspace_demo/t1_access)"""
import contextlib, copy, difflib, hashlib, importlib.util, io, json, os, shutil, sys, tempfile

V17 = os.path.dirname(os.path.abspath(__file__)); CHPC = os.path.dirname(V17); T1 = os.path.dirname(CHPC)
E2, E2Q, V16, FIN = (os.path.join(CHPC, d) for d in ("candidate_e2", "candidate_e2q", "candidate_v16", "e2_final"))
for p in (T1, os.path.join(T1, "aws_ec2"), CHPC, V17):
    sys.path.insert(0, p)
fails, n = [], [0]


def check(name, cond, extra=""):
    n[0] += 1
    print(("ok   " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""), flush=True)
    if not cond:
        fails.append(name)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m); return m


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# the v17 module set, by name, before anything imports it (= what controls v17 pins)
ES = load("row19_ec2_state", os.path.join(E2Q, "row19_ec2_state.py"))
RP = load("row19_partition", os.path.join(E2, "row19_partition.py"))
load("row19_ec2_e2rules", os.path.join(E2, "row19_ec2_e2rules.py"))
load("row19_ec2_e2qual", os.path.join(E2Q, "row19_ec2_e2qual.py"))
import build_v17 as B
import promote_v17 as PV
SA16 = load("sa16_admit", os.path.join(CHPC, "row19_screen_admit.py"))            # the ADOPTED v16 admission (1b02f336)
SA17 = load("sa17_admit", os.path.join(V17, "row19_screen_admit.py"))
MAN_PATH = os.path.join(CHPC, "row19_screen_manifest.json"); MAN = json.load(open(MAN_PATH)); MAN_SHA = sha(MAN_PATH)
RP.DESIGNATED_PATH = os.path.join(CHPC, "row19_screen_designated.json")
E2_PATH = os.path.join(FIN, "row19_partition_e2.json"); PSHA = sha(E2_PATH); E2DOC = RP.load(E2_PATH, MAN, MAN_SHA)
E1_PATH = os.path.join(CHPC, "row19_partition_e1.json"); E1SHA = sha(E1_PATH); E1DOC = RP.load(E1_PATH, MAN, MAN_SHA)
CTL16 = json.load(open(os.path.join(CHPC, "row19_screen_controls.json")))
CTL17 = json.load(open(os.path.join(V17, "row19_screen_controls.json")))

# ---- 1. the candidate -------------------------------------------------------------------------------------------------------
check("adopted inputs are the expected bytes (controls 01976b6a, adoption 523fe18a, diff 0fc23704, e1 8d1de408)", B.input_problems() == [], B.input_problems())
cb, pb = B.build()
check("build_v17.py is deterministic: the committed candidate controls and promotion map are its bytes",
      cb == open(os.path.join(V17, "row19_screen_controls.json"), "rb").read() and pb == open(os.path.join(V17, "v17_promotion_map.json"), "rb").read())
adopted_b = open(os.path.join(CHPC, "row19_screen_controls.json"), "rb").read()
cand_b = open(os.path.join(V17, "row19_screen_controls.json"), "rb").read()
ops = [o for o in difflib.SequenceMatcher(None, adopted_b, cand_b, autojunk=False).get_opcodes() if o[0] != "equal"]
check("the candidate controls are the adopted bytes plus ONE insertion (versions 1-16 textually untouched)", len(ops) == 1 and ops[0][0] == "insert", ops[:3])
check("versions 1-16, programme, deployment, history_manifest equal the adopted v16 controls",
      CTL17["versions"][:-1] == CTL16["versions"] and {k: v for k, v in CTL17.items() if k != "versions"} == {k: v for k, v in CTL16.items() if k != "versions"})
v17, v16 = CTL17["versions"][-1], CTL16["versions"][-1]
changed = sorted(f for f in v17["files"] if v17["files"][f] != v16["files"].get(f))
check("v17 changes exactly seven pins (the admission, four replaced helpers, two new helpers), nothing else",
      changed == sorted(["chpc/row19_screen_admit.py", "chpc/row19_partition.py", "chpc/row19_ec2_ingest.py", "chpc/row19_ec2_qualify.py",
                         "chpc/row19_ec2_state.py", "chpc/row19_ec2_e2rules.py", "chpc/row19_ec2_e2qual.py"]), changed)
check("v17 file set = v16's + row19_ec2_e2rules.py + row19_ec2_e2qual.py", sorted(v17["files"]) == sorted(set(v16["files"]) | set(PV.NEW_PINS)))
check("v17 partition = chpc/row19_partition_e2.json 48cea639; v16 = e1 8d1de408; sub_envelopes, qualification_S, keys unchanged",
      v17["partition"] == {"path": "chpc/row19_partition_e2.json", "sha256": PSHA} and PSHA.startswith("48cea639")
      and v16["partition"] == {"path": "chpc/row19_partition_e1.json", "sha256": E1SHA}
      and v17["sub_envelopes"] == v16["sub_envelopes"] and v17["qualification_S"] == v16["qualification_S"] and sorted(v17) == sorted(v16))
check("e1 stays pinned by versions 13-16 unchanged (provenance) and is the e2 file's named predecessor",
      all((v.get("partition") or {}).get("sha256") == E1SHA for v in CTL17["versions"] if 13 <= v["version"] <= 16)
      and E2DOC["predecessor"]["sha256"] == E1SHA and E2DOC["predecessor"]["epoch"] == 1)
src = {r["promoted"]: r for r in json.loads(pb)["rows"]}
check("every v17 pin of a changed path is its promotion-map source's bytes",
      all(sha(os.path.join(T1, src[f]["source"])) == v17["files"][f] for f in changed))
check("the qualifier pinned is candidate_e2q's (the superset of candidate_e2's REVISION 4)",
      src["chpc/row19_ec2_qualify.py"]["source"] == "chpc/candidate_e2q/row19_ec2_qualify.py")
q_e2 = open(os.path.join(E2, "row19_ec2_qualify.py")).read().splitlines(); q_e2q = open(os.path.join(E2Q, "row19_ec2_qualify.py")).read().splitlines()
removed = [l for l in difflib.ndiff(q_e2, q_e2q) if l.startswith("- ")]
check("superset: every candidate_e2 qualifier line is in candidate_e2q's except 10 text/label/path lines (each replaced, none dropped)",
      len(removed) == 10 and "def main_e2" not in "\n".join(q_e2) and any("def main_e2" in l for l in q_e2q), len(removed))
check("the state module pinned is candidate_e2q's (E2Q contracts); its only change to the live bda200dc is the docstring + 2 contracts",
      [l for l in difflib.ndiff(open(os.path.join(CHPC, "row19_ec2_state.py")).read().splitlines(),
                                open(os.path.join(E2Q, "row19_ec2_state.py")).read().splitlines()) if l.startswith("- ")]
      == ['-                      before the threshold no longer carries a stale view through its 2,700 s validity)."""'])
a16 = open(os.path.join(CHPC, "row19_screen_admit.py")).read().splitlines(); a17 = open(os.path.join(V17, "row19_screen_admit.py")).read().splitlines()
dl = [l for l in difflib.unified_diff(a16, a17, lineterm="", n=0) if l[:1] in "+-" and not l.startswith(("+++", "---"))]
want = [l for l in open(os.path.join(T1, B.ADMIT_DIFF[0])).read().splitlines() if l[:1] in "+-" and not l.startswith(("+++", "---"))]
check("the v17 admission = the adopted v16 admission + exactly the admit_v17_partition_line.diff hunk (1 line out, 4 in)",
      dl == want and len([l for l in dl if l[0] == "-"]) == 1 and len([l for l in dl if l[0] == "+"]) == 4, dl)
import ast
gram = []
for f in changed:
    s_ = open(os.path.join(T1, src[f]["source"])).read()
    try:
        tr = ast.parse(s_, feature_version=(3, 7))
        if any(isinstance(x, ast.NamedExpr) for x in ast.walk(tr)):
            gram.append(f"{f}: walrus")
    except SyntaxError as e:
        gram.append(f"{f}: {e.msg} line {e.lineno}")
check("every changed v17 controller parses with the Python 3.7 grammar (the oldest this interpreter checks), as the live v16 "
      "controllers do (they run under the Lengau t1py)", gram == [], gram)
check("promote_v17 candidate check (pins, versions, partition load + verify2 regeneration) passes", PV.candidate_problems(require_git=False) == [],
      PV.candidate_problems(require_git=False))
check("the promotion order ends admission -> controls (controls LAST)", [r["promoted"] for r in PV.order()][-2:] == ["chpc/row19_screen_admit.py", PV.CTL])
check("the archive inventory names every replaced file's v16 bytes, the v16 qualification and the budget phases (13 members)",
      len(PV.ARCHIVE) == 13 and PV.ARCHIVE["row19_screen_admit.py"][1].startswith("1b02f336") and PV.ARCHIVE["prod_authority.py"][1].startswith("b8ca02b8"))
check("the live tree is untouched: every promoted path still holds its v16 bytes (or is absent)", set(PV.state().values()) == {"v16"}, PV.state())

# tamper: the candidate check refuses an edited controls copy (in memory: the build is compared byte for byte)
real_build = B.build
B.build = lambda: (cb.replace(b'"version": 17', b'"version": 18'), pb)
check("tamper: a candidate controls file that is not the deterministic build refuses", any("deterministic" in w for w in PV.candidate_problems(require_git=False)))
bad = json.loads(cb); bad["versions"][-1]["files"]["chpc/row19_screen_verify.py"] = "0" * 64
B.build = lambda: (json.dumps(bad, indent=1).encode(), pb)
check("tamper: an unchanged pin edited in v17 refuses", any("row19_screen_verify.py" in w for w in PV.candidate_problems(require_git=False)))
bad = json.loads(cb); bad["versions"][-1]["partition"] = v16["partition"]
B.build = lambda: (json.dumps(bad, indent=1).encode(), pb)
check("tamper: v17 still pinning e1 refuses", any("partition reference" in w for w in PV.candidate_problems(require_git=False)))
bad = json.loads(cb); bad["versions"][3]["reviewed"] += " "
B.build = lambda: (json.dumps(bad, indent=1).encode(), pb)
check("tamper: an edited historical version (v4) refuses", any("versions 1-16" in w for w in PV.candidate_problems(require_git=False)))
B.build = real_build
check("the review gate refuses without a record, and with a record lacking the v17 literal",
      PV.review_problems(None) != [] and PV.review_problems("reviews/2026-10-17_v16_p80_codex_review.md") != [])
check("the archive gate refuses while the v16 archive does not exist", any("does not exist" in w for w in PV.archive_problems()))


# ---- 2. admission on the schema-2 partition ----------------------------------------------------------------------------------
import types
if "row19_shard" not in sys.modules:                  # evidence() imports the worker (jax) even with validate=False; its validation is
    try:                                              # not under test (the empty fixture root has no records): the v16 test's stub
        import row19_shard  # noqa: F401
    except ImportError:
        sys.modules["row19_shard"] = types.ModuleType("row19_shard")


def fixture():
    d = tempfile.mkdtemp(); root = os.path.join(d, "root"); camp = os.path.join(d, "campaign")
    for sub in ("plans", "records", "status", "gate", "timing"):
        os.makedirs(os.path.join(root, sub))
    os.makedirs(camp)
    json.dump({"cap_core_h": 81000.0, "entries": {}}, open(os.path.join(camp, "budget.json"), "w"))
    man = dict(MAN, storage=dict(root=root, campaign=camp), shard=dict(MAN["shard"], toolchain=os.path.join(d, "tc"), clone=os.path.join(d, "clone")))
    mp = os.path.join(d, "manifest.json"); json.dump(man, open(mp, "w"))
    return d, root, man, mp


def run(SA, part, act, mp, ctl=None):
    SA.PG.programme_lock = lambda f: contextlib.nullcontext(); SA.PG.programme_funding = lambda man: {}
    real_ev = SA.evidence
    SA.evidence = lambda man, role, validate=True: real_ev(man, role, validate=False)
    SA.partition = lambda man, mpath: part
    if act is not None:
        SA.activation_problem_v10 = act
    if ctl is not None:
        SA.controls = lambda: ctl
    out = io.StringIO(); exc = None
    try:
        with contextlib.redirect_stdout(out):
            rc = SA.main(["--manifest", mp, "--role", "refit", "--jobs", "1", "--dry-run"])
    except Exception as e:
        rc, exc = None, e
    finally:
        SA.evidence = real_ev
    return rc, out.getvalue(), exc


STOP = lambda *a: "STOP-HERE (test: the activation check is reached)"
d, root, man, mp = fixture()
rc, out, exc = run(SA16, E2DOC, STOP, mp)
check("v16 admission on the schema-2 partition raises KeyError('indices') at the print line (the defect the diff fixes)",
      isinstance(exc, KeyError) and exc.args == ("indices",), repr(exc))
rc, out, exc = run(SA17, E2DOC, STOP, mp)
check("v17 admission on the schema-2 partition does NOT raise; it prints the explicit-set line and reaches the activation check",
      exc is None and rc == 2 and "provider partition epoch 2: ec2 owns 3274 explicit coordinates (schema 2, owned ee31504e4a04)" in out
      and "HELD: STOP-HERE" in out, (repr(exc), out[-400:]))
rc16, out16, _ = run(SA16, E1DOC, STOP, mp); rc17, out17, _ = run(SA17, E1DOC, STOP, mp)
line = lambda o: [l for l in o.splitlines() if l.startswith("provider partition")]
check("schema 1 (e1): v17 prints exactly v16's line (indices 160..199, k 40) and both reach the activation check",
      line(out16) == line(out17) and len(line(out17)) == 1 and "indices 160..199" in line(out17)[0] and rc16 == rc17 == 2, (line(out16), line(out17)))
SA17.activation_problem_v10 = load("sa17_fresh", os.path.join(V17, "row19_screen_admit.py")).activation_problem_v10   # unstubbed copy
SA17 = load("sa17_admit", os.path.join(V17, "row19_screen_admit.py"))
rc, out, exc = run(SA17, E2DOC, None, mp, ctl=CTL17)
check("v17 CLI with the REAL activation check, v17 controls, no epoch-2 activation -> HELD 'partition epoch 2 is pinned but not activated'",
      exc is None and rc == 2 and "HELD: partition epoch 2 is pinned but not activated" in out, (repr(exc), out[-300:]))


# ---- 3. the activation hold between v17 adoption and the epoch-2 activation ------------------------------------------------
def act(SA, part, mp_):
    return SA.activation_problem_v10(json.load(open(mp_)), mp_, part)


SA17 = load("sa17_admit", os.path.join(V17, "row19_screen_admit.py")); SA17.controls = lambda: CTL17
check("v17 pinning e2, no proof on the root -> HOLD (not activated)", "pinned but not activated" in act(SA17, E2DOC, mp))
os.makedirs(os.path.join(root, "ec2"))
E1PROOF = os.path.join(CHPC, "results", "row19_screen", "live", "refit", "root", "ec2", "activation_e1.json")
have_e1 = os.path.isfile(E1PROOF)
if have_e1:
    shutil.copyfile(E1PROOF, os.path.join(root, "ec2", "activation_e1.json"))
check("only the e1 activation on the root (the real Mac copy) -> still HOLD: an e1 proof never activates e2", "pinned but not activated" in act(SA17, E2DOC, mp)
      if have_e1 else False, "no local copy of activation_e1.json")
if have_e1:
    shutil.copyfile(E1PROOF, os.path.join(root, "ec2", "activation_e2.json"))
    check("the e1 proof placed at activation_e2.json -> HOLD (its epoch/partition are not e2's)", "is not this partition's" in act(SA17, E2DOC, mp))
ent17 = RP.entry_sha(CTL17["versions"][-1])
base = {"schema": "row19-ec2-activation-1", "epoch": 2, "partition_sha256": PSHA, "manifest_sha256": sha(mp), "transferred_indices": RP.transferred_of(E2DOC),
        "owned_sha256": E2DOC["owned_sha256"], "controls_version": 17, "controls_entry_sha256": ent17}


def put(proof):
    json.dump(proof, open(os.path.join(root, "ec2", "activation_e2.json"), "w"))


put(dict(base, mode="canonical", adoption_sha256="1" * 64))
check("a canonical e2 proof while the canonical controls are still the adopted v16 -> HOLD (v17 is not the adopted controls)",
      "not the current adopted controls" in act(SA17, E2DOC, mp) or "not the adopted" in act(SA17, E2DOC, mp), act(SA17, E2DOC, mp))
SA17.ACTIVATION_MODE = "sandbox"
put(dict(base, mode="sandbox"))
check("positive control (sandbox): an activation of THIS e2 partition under v17 -> admission proceeds ('')", act(SA17, E2DOC, mp) == "", act(SA17, E2DOC, mp))
put(dict(base, mode="sandbox", owned_sha256="0" * 64))
check("a proof binding another owned set -> HOLD", "owned_sha256" in act(SA17, E2DOC, mp))
put(dict(base, mode="sandbox", controls_version=16, controls_entry_sha256=RP.entry_sha(CTL16["versions"][-1])))
check("a proof claiming v16 as its controls version (v16 pins e1, not e2) -> HOLD (historical lineage)", "historical" in act(SA17, E2DOC, mp), act(SA17, E2DOC, mp))
put(dict(base, mode="sandbox"))
c18 = copy.deepcopy(CTL17); v18 = copy.deepcopy(c18["versions"][-1]); v18["version"] = 18; v18["partition"] = CTL16["versions"][-1]["partition"]; c18["versions"].append(v18)
h18 = RP.activation_problem(json.load(open(mp)), sha(mp), E2DOC, PSHA, dict(base, mode="sandbox"), controls=c18, mode="sandbox")
check("a later version that drops the e2 pin makes the e2 proof historical (RP.activation_problem)", "historical" in h18, h18)
e1p = dict(base, mode="sandbox", epoch=1, partition_sha256=E1SHA, transferred_indices=RP.transferred_of(E1DOC), controls_version=13,
           controls_entry_sha256=RP.entry_sha([v for v in CTL17["versions"] if v["version"] == 13][0]))
e1p.pop("owned_sha256")
check("the e1 activation's lineage under v17: v17 no longer pins e1, so an e1 proof is historical (provenance only)",
      "historical" in RP.activation_problem(json.load(open(mp)), sha(mp), E1DOC, E1SHA, e1p, controls=CTL17, mode="sandbox"))
check("... while under v16 the same e1 proof shape is current (the hand-over is exactly the v17 pin change)",
      RP.activation_problem(json.load(open(mp)), sha(mp), E1DOC, E1SHA, e1p, controls=CTL16, mode="sandbox") == "")
cp = os.path.join(d, "ctl17.json"); shutil.copyfile(os.path.join(V17, "row19_screen_controls.json"), cp)
saved = {k: getattr(RP, k) for k in ("load", "history_problems", "handover_problems", "cutover_problems", "lengau_claims", "ec2_completed")}
RP.load = lambda *a, **k: E2DOC                       # the fixture manifest's storage differs from 43b75f94; the scans are not under test
RP.history_problems = lambda *a, **k: []; RP.handover_problems = lambda *a, **k: []
RP.cutover_problems = lambda *a, **k: ([], {}); RP.lengau_claims = lambda *a, **k: (set(), set(), []); RP.ec2_completed = lambda *a, **k: {}
try:
    _proof, probs = RP.activate(json.load(open(mp)), mp, E2_PATH, controls_path=cp, mode="canonical")
except Exception as e:
    probs = [f"raised {type(e).__name__}: {e}"]
finally:
    for k, v in saved.items():
        setattr(RP, k, v)
check("a canonical activation from the CANDIDATE controls file is refused (reads only the adopted canonical controls)",
      any("reads only the canonical controls file" in p for p in probs), probs[:3])
SA17.ACTIVATION_MODE = "canonical"

# ---- 4. the epoch-1 release path cannot open epoch 2 (real v17 controls bytes) ------------------------------------------------
W = tempfile.mkdtemp(); os.makedirs(os.path.join(W, "chpc"))
for s_, d_ in ((os.path.join(V17, "row19_screen_controls.json"), "row19_screen_controls.json"), (E2_PATH, "row19_partition_e2.json"),
               (MAN_PATH, "row19_screen_manifest.json"), (E1_PATH, "row19_partition_e1.json")):
    shutil.copyfile(s_, os.path.join(W, "chpc", d_))
PA = load("prod_authority", os.path.join(E2Q, "aws_ec2", "prod_authority.py"))
PA.T1 = W
pin_doc, pin_sha = PA.pinned_partition()
check("prod_authority under the real v17 controls bytes reads the pinned partition = e2 schema 2 (48cea639)",
      pin_doc is not None and pin_doc.get("schema") == RP.SCHEMA2 and pin_sha == PSHA)


def e1cert(psha):
    c = dict(schema=PA.CERT_SCHEMA, outcome="RELEASE", problems=[], coverage_short={},
             parts={"R1": dict(successful_both=20), "R2": dict(successful_both=40), "R3": dict(successful_both=20)},
             memory=dict(samples_at_full_packing=30, peak_host_used_gib=170.0), replay=dict(final_state="ingested", hashes_equal=True, scope="x"),
             released_attempts=["qual-Q1/1"], q1=dict(key="qual-Q1/1", attempt_id="ec2-qual-Q1-a1", sequence=50, plan_sha256="q1plan"),
             bound=dict(code={}, manifest_sha256=PA.PROD_SHA, partition_sha256=psha, plans={"Q1": "q1plan"}))
    p = os.path.join(W, f"cert_e1_{psha[:8]}.json"); json.dump(c, open(p, "w")); return p


rv = os.path.join(W, "review.md"); open(rv, "w").write("FAVOURABLE\n")
for psha_, lab in ((E1SHA, "e1"), (PSHA, "e2")):
    keys, why = PA.release_problem(e1cert(psha_), rv)
    check(f"an epoch-1 certificate bound to the {lab} partition cannot release under v17 (the schema-2 guard fires first)",
          keys == [] and "cannot release a schema-2 epoch" in why, why)
v16w = copy.deepcopy(CTL17); v16w["versions"].pop()
json.dump(v16w, open(os.path.join(W, "chpc", "row19_screen_controls.json"), "w"), indent=1)
keys, why = PA.release_problem(e1cert(E1SHA), rv)
check("control: with the v16 bytes (e1 pinned) the same certificate is NOT stopped by that guard (it is epoch-specific)",
      "cannot release a schema-2 epoch" not in why, why)
shutil.copyfile(os.path.join(V17, "row19_screen_controls.json"), os.path.join(W, "chpc", "row19_screen_controls.json"))
check("an epoch-1 production release never admits epoch-2 production",
      "epoch 1, not epoch 2" in PA.production_release_problem(dict(production=dict(ok=True, epoch=1, production_opmanifest_sha256=None)), 2, "0" * 64))
check("the epoch-2 release literal carries epoch=2, so an epoch-1-form review line never matches it",
      "epoch=2" in open(os.path.join(E2Q, "aws_ec2", "prod_authority.py")).read())

shutil.rmtree(d, ignore_errors=True); shutil.rmtree(W, ignore_errors=True)
print(f"\n{n[0] - len(fails)} passed, {len(fails)} failed" + ("" if not fails else ": " + "; ".join(fails)))
sys.exit(1 if fails else 0)
