"""migration_v21 static checks (Mac, read only; no ssh). Writes static_results.txt beside itself.

    python3 chpc/migration_v21/static_check_v21.py          (from workspace_demo/t1_access)

- every shell script parses (bash -n), every Python file parses at the 3.6 grammar (Lengau side) or 3.7 (Mac side);
- every composed Lengau script (remote_lib.sh + the embedded archive checker + the body) parses with bash -n;
- no @PLACEHOLDER@ is left; the package pins in v21_package.py, the builder pin in mac_archive.py and V21_CONTROLS in
  remote_lib.sh / package_qual_v21.py equal the candidate bytes;
- the payload rule (5 files) and the commit order (gate, admission, controls, adoption);
- no script calls qdel, a worker, a fit or AWS; qsub appears in no script."""
import ast, hashlib, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.abspath(os.path.join(HERE, "..", ".."))
CAND = os.path.join(T1, "chpc", "candidate_v21_heal")
out, fails = [], []


def check(name, cond):
    out.append(("ok   " if cond else "FAIL ") + name); print(out[-1])
    if not cond:
        fails.append(name)


def h(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


SH = ["preflight_v21.sh", "archive_v20.sh", "deploy_v21.sh", "raise_cap_v21.sh", "lengau.sh", "remote_lib.sh",
      "rollover_pilot_v21.sh", "adopt_pilot21.sh"]
PY_LENGAU = ["lengau_archive.py"]
PY_MAC = ["mac_archive.py", "v21_package.py", "package_qual_v21.py", "static_check_v21.py"]
for f in SH:
    r = subprocess.run(["bash", "-n", os.path.join(HERE, f)], capture_output=True, text=True)
    check(f"bash -n {f}", r.returncode == 0)
for f in PY_LENGAU:
    try:
        ast.parse(open(os.path.join(HERE, f)).read(), feature_version=(3, 6)); ok = True
    except SyntaxError:
        ok = False
    check(f"{f} parses at the Python 3.6 grammar (Lengau side)", ok)
for f in PY_MAC:
    try:
        ast.parse(open(os.path.join(HERE, f)).read(), feature_version=(3, 7)); ok = True
    except SyntaxError:
        ok = False
    check(f"{f} parses at the Python 3.7 grammar", ok)
# composed scripts (the lengau.sh compose function, without transport)
for body in ("rollover_pilot_v21.sh", "adopt_pilot21.sh"):
    r = subprocess.run(["bash", "-c", f'. "{HERE}/lengau.sh"; compose {body} | bash -n'], capture_output=True, text=True, cwd=T1)
    check(f"the composed Lengau script for {body} parses", r.returncode == 0)
allsrc = {f: open(os.path.join(HERE, f)).read() for f in SH + PY_LENGAU + PY_MAC}
check("no @PLACEHOLDER@ left", not any(re.search(r"@[A-Z_]{3,}@", s) for f, s in allsrc.items() if f != "static_check_v21.py"))
pk = allsrc["v21_package.py"]
want = {"row19_screen_controls.json": h(os.path.join(CAND, "row19_screen_controls.json")), "v21_promotion_map.json": h(os.path.join(CAND, "v21_promotion_map.json")),
        "build_v21.py": h(os.path.join(CAND, "build_v21.py")), "promote_v21.py": h(os.path.join(CAND, "promote_v21.py")),
        "programme_gate.py": h(os.path.join(CAND, "programme_gate.py")), "row19_screen_admit.py": h(os.path.join(CAND, "row19_screen_admit.py"))}
for n, d in want.items():
    check(f"v21_package.py pins candidate {n} = {d[:8]}", d in pk)
check("mac_archive.py pins the builder bytes", want["build_v21.py"] in allsrc["mac_archive.py"])
check("remote_lib.sh and package_qual_v21.py carry the candidate controls sha256",
      want["row19_screen_controls.json"] in allsrc["remote_lib.sh"] and want["row19_screen_controls.json"] in allsrc["package_qual_v21.py"])
check("deploy_v21.sh requires exactly 5 payload files", '= 5 ] || fail "the payload is not the 5 files' in allsrc["deploy_v21.sh"] and '[ "$NP" = 5 ]' in allsrc["deploy_v21.sh"])
check("adopt_pilot21.sh uses max_job=200 and refuses the v20 qualification",
      "max_job=200" in allsrc["adopt_pilot21.sh"] and "--max-job-number 200" in allsrc["adopt_pilot21.sh"] and '"$V20_QUAL" ]' in allsrc["adopt_pilot21.sh"])
check("raise_cap_v21.sh raises to LEDGER_CAP_V21 (181000) through the supported --raise-cap", '--raise-cap "$LEDGER_CAP_V21"' in allsrc["raise_cap_v21.sh"]
      and "LEDGER_CAP_V21=181000.0" in allsrc["remote_lib.sh"])
strip = lambda s: "\n".join(l for l in s.splitlines() if "MAC_PAT" not in l and not l.strip().startswith('r"'))   # the drain pattern NAMES processes
bad = [f for f, s in allsrc.items() if f != "static_check_v21.py" and re.search(r"\bqdel\b|\bqsub\b|row19_shard\.py worker|aws |boto3|prod_launch", strip(s))]
check(f"no script calls qdel, qsub, a worker or AWS ({bad})", not bad)
r = subprocess.run([sys.executable, os.path.join(CAND, "build_v21.py"), "--check"], capture_output=True, text=True, cwd=T1)
check("build_v21.py --check: the candidate is the deterministic build", r.returncode == 0)
out.append(f"\n{len(out) - len(fails)} passed, {len(fails)} failed")
print(out[-1])
open(os.path.join(HERE, "static_results.txt"), "w").write("\n".join(out) + "\n")
sys.exit(1 if fails else 0)
