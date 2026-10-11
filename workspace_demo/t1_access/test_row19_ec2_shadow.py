"""Tests of chpc/row19_ec2_shadow.py (the S admission shim, Codex RSC 3dc0daf shortest route): declaration checks against
the candidate version-11 controls, the release gate, the fixed plan, the PBS script's S names, and a dry-run admission with
the programme gate and the screen admission stubbed. No qsub, no Lengau.    .venv/bin/python test_row19_ec2_shadow.py"""
import os, sys, json, copy, shutil, tempfile, hashlib, importlib.util, contextlib, types
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, "chpc")]
import row19_ec2_state as ES, row19_ec2_shadow as SHD
ok = True
def check(n, c, x=""):
    global ok; ok &= bool(c); print(("PASS " if c else "FAIL ") + n + (f"  [{x}]" if x and not c else ""))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
spec = importlib.util.spec_from_file_location("sa11", os.path.join(HERE, "chpc", "candidate_v10r2", "row19_screen_admit.py"))
SA = importlib.util.module_from_spec(spec); spec.loader.exec_module(SA); SHD.SA = SA
prod_p = os.path.join(HERE, "chpc", "row19_screen_manifest.json"); prod = json.load(open(prod_p))
CTL = json.load(open(os.path.join(HERE, "chpc", "candidate_v10r2", "row19_screen_controls.json")))
sman_p = os.path.join(HERE, "chpc", "row19_qual_S_manifest.json")

check("the committed isolated S manifest is the exact derivation of 43b75f94", ES.isolated_S_problem(json.load(open(sman_p)), prod, SHD.PROD_SHA) == "")
check("the candidate v11 controls declare S exactly as the shim runs it", SHD.decl_problem(CTL, sman_p, prod) == "", SHD.decl_problem(CTL, sman_p, prod))
c2 = copy.deepcopy(CTL); c2["versions"][-1]["sub_envelopes"] = []
check("no combined 60,000 sub-envelope -> refused", "sub-envelope" in SHD.decl_problem(c2, sman_p, prod))
c3 = copy.deepcopy(CTL); c3["programme"]["campaigns"] = c3["programme"]["campaigns"][:-1]
check("the S campaign missing from the programme block -> refused", "programme block" in SHD.decl_problem(c3, sman_p, prod))
c4 = copy.deepcopy(CTL); c4["versions"][-1]["qualification_S"]["manifest_sha256"] = "0" * 64
check("an isolated manifest that is not the declared bytes -> refused", "declared bytes" in SHD.decl_problem(c4, sman_p, prod))
bad = json.load(open(sman_p)); bad["cfg"]["n_boot_refit"] = 100; bp = os.path.join(tempfile.mkdtemp(), "bad.json"); json.dump(bad, open(bp, "w"))
check("an isolated manifest that changes science -> refused", "derivation" in SHD.decl_problem(CTL, bp, prod))
same = json.load(open(sman_p)); same["storage"] = dict(prod["storage"]); sp_ = os.path.join(tempfile.mkdtemp(), "same.json"); json.dump(same, open(sp_, "w"))
check("an 'isolated' manifest pointing at the screen root -> refused", "not isolated" in ES.isolated_S_problem(same, prod, SHD.PROD_SHA))
j1, j2 = SHD.s_job(1), SHD.s_job(2)
check("fixed plan: job 1 = index 199, job 2 = index 198, reps 3..26, 24 slots each, labels S1/S2",
      [s["indices"] for s in j1["slots"]] == [[199]] * 24 and [s["indices"] for s in j2["slots"]] == [[198]] * 24
      and [s["rep"] for s in j1["slots"]] == list(range(3, 27)) and (j1["label"], j2["label"]) == ("S1", "S2"))
script = SHD.pbs_script(json.load(open(sman_p)), j1, "TOK", "/t", "/c", "chpc/row19_qual_S_manifest.json")
check("the PBS script uses S job and file names, the unchanged worker, the isolated manifest and 48 h",
      "#PBS -N t1_qualS_1" in script and "row19_qualS_1.out" in script and "row19_screen_refit_1" not in script
      and "chpc/row19_shard.py worker --manifest chpc/row19_qual_S_manifest.json" in script and "walltime=48:00:00" in script)
rd = tempfile.mkdtemp(); rs = os.path.join(rd, "rel.json"); json.dump(json.load(open(os.path.join(HERE, "aws_ec2", "ec2_release_state.json"))), open(rs, "w"))
check("the release gate refuses while row 23 is not declared successful", "row 23" in SHD.release_problem(rs))
r = json.load(open(rs)); open(os.path.join(rd, "r23.json"), "w").write("{}"); open(os.path.join(rd, "q.md"), "w").write("q")
r["row23"].update(declared_success=True, report_path="r23.json", report_sha256=sha(os.path.join(rd, "r23.json")))
json.dump(r, open(rs, "w")); check("... and while the qualification is not permitted", "qualification" in SHD.release_problem(rs))
r["qualification"].update(permitted=True, record_path="q.md", record_sha256=sha(os.path.join(rd, "q.md"))); json.dump(r, open(rs, "w"))
check("... and passes once both are backed", SHD.release_problem(rs) == "")

# a dry-run admission with the programme gate stubbed and the S root/campaign/clone in a sandbox
d = tempfile.mkdtemp(); sroot, scamp, clone = os.path.join(d, "root"), os.path.join(d, "camp"), os.path.join(d, "clone")
prod2 = copy.deepcopy(prod); prod2["shard"] = dict(prod["shard"], toolchain=d, clone=clone)
sm = ES.derive_isolated_S(prod2, SHD.PROD_SHA, sroot, scamp); smp = os.path.join(HERE, "chpc", "_test_qual_S_manifest.json"); json.dump(sm, open(smp, "w"))
os.makedirs(os.path.join(clone, "workspace_demo", "t1_access", "chpc")); shutil.copy(smp, os.path.join(clone, "workspace_demo", "t1_access", "chpc", os.path.basename(smp)))
ctl = copy.deepcopy(CTL); q = ctl["versions"][-1]["qualification_S"]; q.update(root=sroot, campaign=scamp, manifest_sha256=sha(smp))
ctl["programme"]["campaigns"][-1] = {"path": scamp, "may_be_absent": True, "root": sroot}
ctl["versions"][-1]["sub_envelopes"][0]["campaigns"] = [os.path.join(d, "refit_camp"), scamp]
SA.controls = lambda: ctl; SA.controls_problem = lambda: ""
SHD.release_problem = lambda path=None: ""
PG = types.ModuleType("programme_gate"); PG.programme_funding = lambda m: {"lock": os.path.join(d, "lock")}
PG.programme_lock = contextlib.contextmanager(lambda f: (yield)); PG.funding_problem = lambda f, p: ""; sys.modules["programme_gate"] = PG
_orig_sha = SHD.sha; SHD.sha = lambda p: SHD.PROD_SHA if os.path.abspath(p) == os.path.abspath(prod_p) else _orig_sha(p)
mp2 = os.path.join(d, "prod.json"); json.dump(prod2, open(mp2, "w")); SHD.sha = lambda p, _o=_orig_sha: SHD.PROD_SHA if os.path.abspath(p) == os.path.abspath(mp2) else _o(p)
import argparse
a = argparse.Namespace(manifest=mp2, s_manifest=smp, job=1, dry_run=True)
why = SHD.admit(a); check("a dry-run S admission passes every gate and plans 24 slots without writing", why == "" and not os.path.exists(os.path.join(sroot, "plans")), why)
open(os.path.join(sroot if os.path.isdir(sroot) else d, "x"), "w").close(); os.makedirs(sroot, exist_ok=True); open(os.path.join(sroot, "STOP"), "w").write("x")
check("a STOP in the S root refuses", "STOP" in SHD.admit(a)); os.remove(os.path.join(sroot, "STOP"))
os.makedirs(os.path.join(d, "refit_camp")); json.dump(dict(cap_core_h=60000.0, entries={"t": dict(state="settled", settled_core_h=59500.0, reserved_core_h=1152.0)}),
                                                      open(os.path.join(d, "refit_camp", "budget.json"), "w"))
check("the combined refit+S sub-envelope refuses S when the refit has used the shared 60,000", "sub-envelope" in SHD.admit(a))
os.remove(smp)
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
