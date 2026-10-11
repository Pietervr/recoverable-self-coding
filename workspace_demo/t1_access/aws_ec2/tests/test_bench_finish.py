"""Tests of bench_finish: the row-23 success criterion recorded before the completed parity/refit results, and the fresh
staging / exit-status / report-binding rules of Codex 3f67eaf F-2. A fake transport stands in for S3 and Lengau: remote paths
map under a temporary directory, the comparator's exit status and report are scripted. No AWS, no ssh.
    python3 tests/test_bench_finish.py"""
import copy, json, os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE); sys.path.insert(0, PKG)
import bench_finish as BF
ok = True
def check(n, c, x=""):
    global ok; ok &= bool(c); print(("PASS " if c else "FAIL ") + n + (f"  [{x}]" if x and not c else ""))

# 1 criterion
good = dict(valid=True, problems=[], profile_B="B_full",
            stage1=dict(B=dict(exact_quantities="12/12", decisions_identical=True, failed_flags_identical=True)),
            stage2=dict(A=dict(refused_at_job_start=True, reason="HELD: ..."),
                        B=dict(validated_records=36, valid_timing_pairs=36, payload_exact=36, nonfinite_disagreements=0)))
check("the recorded success shape passes", BF.criterion(good) == [])
def bad(path, v):
    r = copy.deepcopy(good); d = r
    for k in path[:-1]:
        d = d[k]
    d[path[-1]] = v; return BF.criterion(r)
check("an invalid report fails", bad(["valid"], False))
check("B_nomask fails", bad(["profile_B"], "B_nomask"))
check("row 6 11/12 fails", bad(["stage1", "B", "exact_quantities"], "11/12"))
check("a decision difference at row 6 fails", bad(["stage1", "B", "decisions_identical"], False))
check("35 exact payloads fail", bad(["stage2", "B", "payload_exact"], 35))
check("35 timing pairs fail", bad(["stage2", "B", "valid_timing_pairs"], 35))
check("a non-finite disagreement fails", bad(["stage2", "B", "nonfinite_disagreements"], 1))
check("a missing arm-B stage 2 fails", bad(["stage2", "B"], {}))
check("arm A neither refused nor validated fails", bad(["stage2", "A"], dict(validated_records=12)))
check("arm A fully validated passes", bad(["stage2", "A"], dict(validated_records=36)) == [])

# 2 transport: fresh staging, exit status, binding, declaration
TMP = tempfile.mkdtemp(); S3 = os.path.join(TMP, "s3"); RFS = os.path.join(TMP, "lengau")
os.makedirs(os.path.join(TMP, "runs")); shutil.copy(os.path.join(PKG, "bench_compare.py"), TMP)
REL0 = dict(schema="t1-ec2-release-state-1", row23=dict(declared_success=False, report_path=None, report_sha256=None))
BF.HERE = TMP; BF.REL = os.path.join(TMP, "ec2_release_state.json")
def reset_rel():
    json.dump(REL0, open(BF.REL, "w"))
def s3_put(name, files):
    d = os.path.join(S3, "b2", name); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    for rel, body in files.items():
        os.makedirs(os.path.dirname(os.path.join(d, rel)) or d, exist_ok=True); open(os.path.join(d, rel), "w").write(body)
def R(p):
    return os.path.join(RFS, p.lstrip("/"))


class Fake:
    def __init__(self, rc=0, report=good, tamper=False):
        self.rc, self.report, self.tamper = rc, report, tamper
    def fetch(self, run, name, dest):
        os.makedirs(dest); shutil.copytree(os.path.join(S3, run, name), dest, dirs_exist_ok=True)
    def push_tree(self, local_parent, name, remote_dir):
        os.makedirs(R(remote_dir))                                     # raises if not new, like `mkdir` remotely
        shutil.copytree(os.path.join(local_parent, name), os.path.join(R(remote_dir), name))
        if self.tamper:
            open(os.path.join(R(remote_dir), name, "extra.txt"), "w").write("x")
    def put(self, src, dst):
        os.makedirs(os.path.dirname(R(dst)), exist_ok=True); shutil.copy(src, R(dst))
    def get(self, src, dst):
        if not os.path.exists(R(src)):
            raise subprocess.CalledProcessError(1, "scp")
        shutil.copy(R(src), dst)
    def ssh(self, cmd, stdin=None, timeout=0):
        remote = R(cmd.split("cd ", 1)[1].split(" &&")[0])
        if "sha256sum bench_compare.py" in cmd:
            name = [x for x in os.listdir(remote) if x.startswith("attempt_")][0]
            d, n = BF.bundle_digest(os.path.join(remote, name))
            pins = "".join(f"{'0' * 64}  {p}\n" for p in BF.TREE_PINS)
            out = f"{BF.L.sha256(os.path.join(remote, 'bench_compare.py'))}  bench_compare.py\n{d} {n}\n{pins}"
            return subprocess.CompletedProcess(cmd, 0, out, "")
        if self.report is not None:
            json.dump(self.report, open(os.path.join(remote, "report.json"), "w"))
        return subprocess.CompletedProcess(cmd, self.rc, "", "")

logs = []
s3_put("attempt_5", {"env/a.json": "1", "env/b.json": "2", "root_B/records/rep3/rec_000.json": "r"})
reset_rel()
rc = BF.finish(Fake(), "b2", 5, declare=True, stamp="S1", log=logs.append)
rel = json.load(open(BF.REL))
check("success: exit 0, declared with report + binding sha256", rc == 0 and rel["row23"]["declared_success"] is True
      and rel["row23"]["report_path"].endswith("bench_report_attempt_5_S1.json") and rel["row23"]["binding_sha256"], logs)
bind = json.load(open(os.path.join(TMP, "runs", "b2", "bench_binding_attempt_5_S1.json")))
check("the binding names run, attempt, comparator sha, tree pins, bundle digest and the report sha", bind["run"] == "b2"
      and bind["attempt"] == 5 and bind["comparator_sha256"] == BF.L.sha256(os.path.join(TMP, "bench_compare.py"))
      and sorted(bind["tree_pins"]) == sorted(BF.TREE_PINS) and bind["bundle_files"] == 3
      and bind["report_sha256"] == BF.L.sha256(os.path.join(TMP, rel["row23"]["report_path"])))

# F-2 (a): an old passing report exists in the remote parent; the fresh comparator fails -> nothing declared
reset_rel(); logs.clear()
os.makedirs(R("/home/pvanrooyen/lustre/aws_bench/b2a5"), exist_ok=True)
json.dump(good, open(R("/home/pvanrooyen/lustre/aws_bench/b2a5/report_attempt_5.json"), "w"))
rc = BF.finish(Fake(rc=1, report=None), "b2", 5, declare=True, stamp="S2", log=logs.append)
check("old passing report + fresh comparator failure: exit 2, NOT declared", rc == 2 and json.load(open(BF.REL)) == REL0, logs)
rc = BF.finish(Fake(rc=1, report=good), "b2", 5, declare=True, stamp="S3", log=logs.append)
check("a comparator crash that left a passing-looking report is still refused (exit status rules)", rc == 2 and json.load(open(BF.REL)) == REL0)
rc = BF.finish(Fake(rc=3, report=good), "b2", 5, declare=True, stamp="S4", log=logs.append)
check("comparator exit 3 (invalid panel) is never success", rc == 3 and json.load(open(BF.REL)) == REL0)

# F-2 (b): a source file removed from S3 after an earlier fetch; the old cache must not carry it into the new bundle
s3_put("attempt_5", {"env/a.json": "1", "root_B/records/rep3/rec_000.json": "r"})
reset_rel(); logs.clear()
rc = BF.finish(Fake(), "b2", 5, declare=False, stamp="S5", log=logs.append)
b5 = json.load(open(os.path.join(TMP, "runs", "b2", "bench_binding_attempt_5_S5.json")))
st = os.path.join(TMP, "runs", "b2", "fetched", "attempt_5.S5", "attempt_5")
check("removed source + old cache: the fresh stage has only the current files", rc == 0 and b5["bundle_files"] == 2
      and not os.path.exists(os.path.join(st, "env", "b.json")) and os.path.exists(os.path.join(TMP, "runs", "b2", "fetched", "attempt_5.S1", "attempt_5", "env", "b.json")))
check("without --declare nothing is declared", json.load(open(BF.REL)) == REL0)
rc = BF.finish(Fake(), "b2", 5, declare=True, stamp="S5", log=logs.append)
check("a reused stamp (staging directory not new) refuses", rc == 2 and json.load(open(BF.REL)) == REL0)
rc = BF.finish(Fake(tamper=True), "b2", 5, declare=True, stamp="S6", log=logs.append)
check("a Lengau copy that differs from the staged bundle refuses", rc == 2 and json.load(open(BF.REL)) == REL0)

shutil.rmtree(TMP)
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
