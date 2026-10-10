"""Synthetic tests of the version-9 pull_tree (no network, no Lengau, no science): a stub `ssh` runs the remote half
locally. python3 candidate_v9/test_pull_tree.py"""
import os, re, shlex, shutil, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__))
ok = True
def check(name, cond, extra=""):
    global ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""))
tmp = tempfile.mkdtemp(); bindir = os.path.join(tmp, "bin"); os.makedirs(bindir)
os.symlink(os.path.join(HERE, "stub_ssh.sh"), os.path.join(bindir, "ssh"))
os.environ["PATH"] = bindir + os.pathsep + os.environ["PATH"]
for f in ("row19_screen_status.py", "row22_bank_status.py"):
    src = open(os.path.join(HERE, f)).read()
    i = src.index("# The remote half of pull_tree"); j = src.index("\n\n\n", src.index("def pull_tree"))
    ns = {}; exec("import os, re, shlex, subprocess, time\nHOST='stub'\n" + src[i:j], ns)
    pull = ns["pull_tree"]; print(f"== {f}")
    big = os.path.join(tmp, "big"); os.makedirs(big + "/records")
    for k in range(60000):
        d = os.path.join(big, "records", f"rep{k % 300}"); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, f"rec_{k // 300:03d}.json"), "w").write("{}")
    os.environ["STUB_SSH_MODE"] = "ok"
    out = tempfile.mkdtemp(dir=tmp); t = time.time(); rc, note = pull(big, out, timeout=300)
    n = sum(len(x) for _, _, x in os.walk(out))
    check("60,000-file tree (listing ~1.9 MB, far above pipe capacity) pulls completely", rc == 0 and n == 60000, f"rc {rc} {note} {n} files {time.time()-t:.1f} s")
    rc, note = pull(os.path.join(tmp, "does_not_exist"), tempfile.mkdtemp(dir=tmp), timeout=60)
    check("missing directory -> PHASE cd FAILED", rc == 255 and "cd FAILED" in note, note)
    bad = os.path.join(tmp, "unreadable"); os.makedirs(bad + "/sub", exist_ok=True); open(bad + "/a.json", "w").write("{}"); os.chmod(bad + "/sub", 0)
    rc, note = pull(bad, tempfile.mkdtemp(dir=tmp), timeout=60); os.chmod(bad + "/sub", 0o755)
    check("enumeration failure -> PHASE find FAILED", rc == 255 and "find FAILED" in note, note)
    os.environ["STUB_SSH_MODE"] = "truncate"
    rc, note = pull(big, tempfile.mkdtemp(dir=tmp), timeout=120)
    check("truncated stream refused", rc == 255, note)
    os.environ["STUB_SSH_MODE"] = "hang"
    t = time.time(); rc, note = pull(big, tempfile.mkdtemp(dir=tmp), timeout=3)
    left = subprocess.run(["pgrep", "-f", "stub_ssh.sh"], capture_output=True, text=True).stdout.split()
    check("deadline: refused within the bound, children reaped", rc == 255 and time.time() - t < 30 and not left, f"{note} {time.time()-t:.1f} s, stray {left}")
    T = ns["_TMP_NAME"]
    check("temporary-name exemption limited to <path>.tmp and <path>.tmp.<pid>",
          all(T.search(x) for x in ("budget.json.tmp", "records/rep3/rec_000.json.tmp.4242")) and
          not any(T.search(x) for x in ("rec_000.json", "a.tmpx", "a.tmp.x1", "tmp/rec.json")))
    shutil.rmtree(big)
print("ALL PASS" if ok else "SOME FAILED"); shutil.rmtree(tmp, ignore_errors=True); sys.exit(0 if ok else 1)
