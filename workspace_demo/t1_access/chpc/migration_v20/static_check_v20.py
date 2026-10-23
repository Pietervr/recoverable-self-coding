"""migration_v20 STATIC checks (Mac, read-only; nothing is sent to Lengau, nothing is written outside a temporary directory).
The end-to-end rehearsal is test_migration_v20.py (the re-pointed migration_v19 harness plus the close; Codex review
2026-10-23 F2); these checks are the quick static layer beside it.

    python3 chpc/migration_v20/static_check_v20.py          (from workspace_demo/t1_access)"""
import ast, glob, hashlib, importlib.util, json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, "..", ".."))
CAND = os.path.join(T1, "chpc", "candidate_v20_handback")
fails = []; npass = [0]


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name, flush=True)
    if cond:
        npass[0] += 1
    else:
        fails.append(name)


def sha(rel):
    return hashlib.sha256(open(os.path.join(T1, rel), "rb").read()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m); return m


SH = sorted(glob.glob(os.path.join(HERE, "*.sh"))); PY = sorted(glob.glob(os.path.join(HERE, "*.py")))
check("bash -n: every shell script parses (%d)" % len(SH), all(subprocess.run(["bash", "-n", p]).returncode == 0 for p in SH))
check("every Python file compiles (%d)" % len(PY), all(compile(open(p).read(), p, "exec") for p in PY))
check("Lengau-side Python (lengau_archive.py) is 3.6-level grammar",
      ast.parse(open(os.path.join(HERE, "lengau_archive.py")).read(), feature_version=(3, 6)) is not None)
rl = open(os.path.join(HERE, "remote_lib.sh")).read()
for var in ("ACT_PY", "ACT3_PY", "LOCK_PY"):
    m = re.search(var + r"='(.*?)'\n", rl, re.S)
    check(f"remote_lib {var} is 3.6-level Python", bool(m) and ast.parse(m.group(1), feature_version=(3, 6)) is not None)
tmp = tempfile.mkdtemp(prefix="mig20_static_")
for body, var in (("preflight_v20.sh", None), ("check_v20.sh", "PHASE=pre"), ("close_e3.sh", None), ("rollover_pilot_v20.sh", None)):
    if body == "preflight_v20.sh":
        continue                               # its Lengau body is a heredoc inside the script (covered by bash -n above)
    args = ["bash", "-c", 'source chpc/migration_v20/lengau.sh && compose "$@"', "x", body] + (["--var", var] if var else [])
    r = subprocess.run(args, cwd=T1, capture_output=True, text=True)
    p = os.path.join(tmp, body + ".composed"); open(p, "w").write(r.stdout)
    ok = r.returncode == 0 and subprocess.run(["bash", "-n", p]).returncode == 0 and "T_ROOT=/mnt/lustre/users/pvanrooyen/t1_toolchain" in r.stdout
    check(f"the composed Lengau script for {body} parses and carries the production root", ok)

# ---- pins agree with the bytes they name -------------------------------------------------------------------------------------
sys.path.insert(0, HERE)
PK = load("v20_package", os.path.join(HERE, "v20_package.py"))
check("v20_package PACKAGE: every pinned identity is the committed candidate bytes",
      all(sha(p) == h for p, h in PK.PACKAGE.items()))
check("v20_package: the @record pin is PENDING (None, None) until the operator record exists", PK.REC is None and PK.REC_SHA is None)
check("v20_package: V19 = the live adopted controls/adoption; V19_QUAL = the Mac pilot qualification; the pilot record",
      all(sha(r) == h for r, h in PK.V19.items()) and sha(PK.QUAL_PATH) == PK.V19_QUAL and sha(PK.PILOT_REC[0]) == PK.PILOT_REC[1])
B, PV = PK.modules()
check("the deploy payload is 7 files: record + partition module, admission, e3, authority + controls + adoption",
      len(PV.rows()) + 3 == 7 and [r["promoted"] for r in PV.rows()] == ["chpc/row19_partition.py", "chpc/row19_screen_admit.py",
                                                                            "chpc/row19_partition_e3.json", "aws_ec2/prod_authority.py"])
MA = load("mac_archive", os.path.join(HERE, "mac_archive.py"))
check("mac_archive: the pinned builder is build_v20's bytes and its archive has N_MEMBERS (9) members",
      sha(MA.BUILDER) == MA.BUILDER_SHA and len(B.ARCHIVE) == MA.N_MEMBERS == 9)
cv = dict(re.findall(r"^([A-Z0-9_]+)=([0-9a-f]{64})$", rl, re.M))
ctl20 = sha("chpc/candidate_v20_handback/row19_screen_controls.json")
check("remote_lib: V20_CONTROLS = the candidate controls; V19_CONTROLS/V19_ADOPTION = live; E2_PART/E3_PART = e2/e3",
      cv["V20_CONTROLS"] == ctl20 and cv["V19_CONTROLS"] == sha("chpc/row19_screen_controls.json")
      and cv["V19_ADOPTION"] == sha("chpc/row19_screen_controls_adoption.json") and cv["E2_PART"] == sha("chpc/row19_partition_e2.json")
      and cv["E3_PART"] == sha("chpc/candidate_v20_handback/row19_partition_e3.json") and cv["V19_QUAL"] == PK.V19_QUAL)
rep = re.search(r'V19_REPLACED="(.*?)"', rl, re.S).group(1).split("\n")
check("remote_lib V19_REPLACED: exactly build_v20.MAP's two pins at their live v19 bytes",
      sorted(l.split()[0] for l in rep) == sorted(m[0] for m in B.MAP) and all(sha(l.split()[0]) == l.split()[1] for l in rep)
      and all(l.split()[1] == prev for l in rep for d, _s, prev in B.MAP if d == l.split()[0]))
check("remote_lib V20_NEW is exactly the e3 data path (absent on the Mac live tree)",
      re.search(r'V20_NEW="(.*?)"', rl).group(1) == "chpc/row19_partition_e3.json" and not os.path.exists(os.path.join(T1, "chpc/row19_partition_e3.json")))
for rs in ("V19_REC", "V19_PILOT_REC"):
    m = re.search(rs + r'="(\S+) ([0-9a-f]{64})"', rl)
    check(f"remote_lib {rs} names a committed record with its bytes", bool(m) and sha(m.group(1)) == m.group(2))
LA = open(os.path.join(HERE, "lengau_archive.py")).read()
la = dict(re.findall(r'^(V19_[A-Z]+) = "([0-9a-f]{64})"$', LA, re.M))
check("lengau_archive: the v19 identities are the live bytes (controls, adoption, admission, status, designated, pilot qualification)",
      la["V19_CONTROLS"] == sha("chpc/row19_screen_controls.json") and la["V19_ADOPTION"] == sha("chpc/row19_screen_controls_adoption.json")
      and la["V19_ADMIT"] == sha("chpc/row19_screen_admit.py") and la["V19_STATUS"] == sha("chpc/row19_screen_status.py")
      and la["V19_DESIGNATED"] == sha("chpc/row19_screen_designated.json") and la["V19_QUAL"] == PK.V19_QUAL
      and 'if v.get("version") != 19' in LA)
for f in ("receipt_check_v20.py", "package_qual_v20.py"):
    check(f"{f}: V20_CONTROLS is the candidate controls and the generation is 20/20",
          ctl20 in open(os.path.join(HERE, f)).read() and 'g.get("version") == 20 and g.get("latest") == 20' in open(os.path.join(HERE, f)).read())
check("no leftover v19-package token (the E2Q3 manifest path, 'nine payload', the v19 map 8256a584) in any script",
      not any(t in open(p).read() for p in SH + PY if not p.endswith(("static_check_v20.py", "test_migration_v20.py")) for t in ("manifest_e2q3_e2.json", "nine payload", "8256a584")))
check("no script stops a worker or reaper, calls AWS, or runs prod_launch/qual_permit/release-adopt",
      not any(re.search(r"\b(qdel|aws |prod_launch\.py --|qual_permit\.py --|release-adopt|kill )", open(p).read()) for p in SH))
RC = load("receipt_check_v20", os.path.join(HERE, "receipt_check_v20.py"))
rdir = os.path.join(T1, "chpc", "results", "row19_screen", "receipts")
newest = json.load(open(sorted(glob.glob(os.path.join(rdir, "watch_refit_*.json")))[-1]))
_, wpre = RC.problems(rdir, newest["time"], "pre")
_, wpost = RC.problems(rdir, newest["time"], "post")
check(f"receipt_check_v20 --phase pre on the newest REAL (v19) receipt refuses ONLY its generation ({wpre})",
      len(wpre) == 1 and "generation is not v20" in wpre[0])
check("receipt_check_v20 --phase post on it also refuses the missing e3 activation and the 3,274 EC2-waiting coordinates",
      any("activation_e3" in w for w in wpost) and any("EC2-designated unclaimed" in w for w in wpost))
import shutil; shutil.rmtree(tmp, ignore_errors=True)
for d in (os.path.join(HERE, "__pycache__"),):
    shutil.rmtree(d, ignore_errors=True)
print(f"\n{npass[0]} passed, {len(fails)} failed")
for f in fails:
    print("FAILED:", f)
sys.exit(1 if fails else 0)
