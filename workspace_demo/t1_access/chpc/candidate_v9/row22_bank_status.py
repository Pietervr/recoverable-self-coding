"""Ledger row 22: the bank's live view, watch receipt and pilot qualification (Mac). Codex RSC 97fc278 conditions 3-4: fresh
coherent snapshots and successful scheduler observations; every planned rep and slot reconciled with disjoint new / resumed /
left lists, exact status, record and timing provenance, finite non-negative measurements, scheduler state, exit and
accounting; any HELD or missing worker, invalid or foreign record, missing or invalid timing, memory breach, failed admission
or absent accounting is an ALARM that holds progression.

EVIDENCE, every call:
  1. the producer-runtime verdict: `t1py chpc/row22_bank_verify.py` run in the bank clone on the login node; its stdout (one
     JSON document) is kept and its SHA-256 bound into the receipt. Records are validated THERE, against the production task
     identities; the Mac never recomputes an identity.
  2. a fresh pull of the bank root and campaign into a new staging directory, rotated in only when EVERY pull succeeded.
  3. one `qstat -xf` of every bank job id in the ledger: the call must RETURN 0 (a non-zero return is a failed observation
     whatever its stdout - the defect Codex found in the shard parser) and every id must be either listed or reported unknown.
RECONCILIATION per bank job (plan file, ledger entry, scheduler, statuses, verify verdict):
  - a terminal job (scheduler F/E/X/gone) must have a status for EVERY planned slot; a status's reps equal its plan slot's;
    new, resumed and left are disjoint and their union is the slot's reps; exit 0 iff left is empty, 75 with left non-empty,
    anything else (4 HELD, missing) is an alarm;
  - every new or resumed rep has a VALID record (verify) and a valid timing file; a new rep's timing names this job and slot;
  - worker maxrss below the per-worker stop; scheduler memory below 90 % of the request; a terminal job's scheduler exit 0
    or 75 and its runner end recorded in the ledger;
  - a running job: records published so far must be valid with timings; nothing else is required yet.
  - a record or timing for a rep no plan assigns is an alarm (foreign evidence).
RECEIPT (--publish-receipt): schema row22-bank-watch-1, fresh/production flags, alarms, bound = manifest SHA-256, root, campaign,
code pins, wrapper, bank binding SHA-256, the verify document's SHA-256, and every bank job (PBS id, token, plan SHA-256).
QUALIFICATION (--qualify 1): only on fresh production evidence with zero alarms, job 1 terminal with scheduler exit 0, every
planned slot exit 0, every planned rep a valid record with timing, runner end in the ledger; written locally and copied to
<root>/gate/qualified_bank_job1.json. It is EVIDENCE for the reviewer; the submitter also needs the adopted review.

    python chpc/row22_bank_status.py --manifest chpc/row22_bank_manifest.json [--publish-receipt] [--qualify 1]
Exit 1 on any alarm or when the evidence is not fresh."""
import os, sys, json, glob, math, time, shutil, hashlib, argparse, subprocess, shlex, re

HERE = os.path.dirname(os.path.abspath(__file__))
HOST, LOGIN = "chpc-scp", "lengau"
LIVE_DIR = os.path.join(HERE, "results", "row22_bank", "live")
RECEIPTS = os.path.join(HERE, "results", "row22_bank", "receipts")
WATCH_SCHEMA = "row22-bank-watch-1"
QUAL_SCHEMA = "row22-bank-qualification-1"
TERMINAL = ("F", "E", "X", "gone")


def sh(cmd, timeout=600):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return 255, "", str(e)

def pull_tree(remote, local, timeout=900):
    """REVISION 9: copy a remote directory tree in ONE ssh stream (GNU tar on the transfer node -> tar here) instead of
    scp -r's per-file round trips (~1.1 s per file over the tunnel on 10 Oct: 938 files overran the 900 s pull timeout;
    the stream takes ~15-25 s). Same source, destination and timeout. Integrity: the remote lists every regular file
    BEFORE archiving (to stderr), the local extractor must exit 0 (a truncated or corrupt stream fails), the remote tar
    must exit 0 or 1 (GNU tar's 'file changed as we read it', the live-tree race scp also had), and EVERY file of the
    pre-archive listing must exist locally (temporary *.tmp.* files excepted: publishers remove them). A file published
    while the archive streams may or may not be included, exactly as with scp. Returns (0, '') or (255, reason)."""
    q = shlex.quote(remote)
    cmd = f"cd {q} && find . -type f | LC_ALL=C sort >&2 && tar -cf - ."
    src = dst = None
    try:
        src = subprocess.Popen(["ssh", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", HOST, cmd],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        dst = subprocess.Popen(["tar", "-xf", "-", "-C", local], stdin=src.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        src.stdout.close()
        _, derr = dst.communicate(timeout=timeout)
        _, serr = src.communicate(timeout=60)
    except Exception as e:
        for p in (src, dst):
            if p is not None:
                try:
                    p.kill()
                except Exception:
                    pass
        return 255, f"tar stream: {type(e).__name__}: {e}"
    serr = serr.decode(errors="replace"); derr = derr.decode(errors="replace")
    if dst.returncode != 0:
        return 255, f"local tar rc {dst.returncode}: {derr.strip()[:160]}"
    if src.returncode not in (0, 1):
        return 255, f"remote rc {src.returncode}: {serr.strip()[-160:]}"
    listed = [l[2:] for l in serr.splitlines() if l.startswith("./")]
    if not listed and os.listdir(local):
        return 255, "the remote pre-archive listing is empty"
    missing = [p for p in listed if ".tmp." not in p and not os.path.isfile(os.path.join(local, p))]
    if missing:
        return 255, f"{len(missing)} listed file(s) not extracted, e.g. {missing[:3]}"
    return 0, ""



def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha_bytes(open(p, "rb").read())


def finite_nonneg(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x >= 0


def verify_remote(man, manifest_rel):
    clone = man["bank"]["clone"]; tc = man["bank"]["toolchain"]
    rc, out, err = sh(["ssh", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", LOGIN,
                       f"cd {clone}/workspace_demo/t1_access && {tc}/t1py chpc/row22_bank_verify.py --manifest {manifest_rel}"], timeout=1800)
    if rc != 0:
        return None, None, f"producer-runtime verify failed (rc {rc}): {err.strip()[-200:]}"
    line = [l for l in out.splitlines() if l.startswith("{")]
    if len(line) != 1:
        return None, None, "producer-runtime verify printed no single JSON document"
    try:
        doc = json.loads(line[0])
    except Exception as e:
        return None, None, f"producer-runtime verify output is not JSON ({e})"
    if doc.get("schema") != "row22-bank-verify-1":
        return None, None, "producer-runtime verify has another schema"
    return doc, sha_bytes(line[0].encode()), ""


def fresh_snapshot(man):
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    stage = os.path.join(os.path.dirname(LIVE_DIR), f"stage_{stamp}")
    problems = []
    for name, remote in (("campaign", man["storage"]["campaign"]), ("root", man["storage"]["root"])):
        local = os.path.join(stage, name); os.makedirs(local, exist_ok=True)
        rc, err = pull_tree(remote, local, timeout=900)
        if rc != 0:
            problems.append(f"pull of {remote} failed (rc {rc}): {err.strip()[:160]}")
    if problems:
        shutil.rmtree(stage, ignore_errors=True); return False, problems
    shutil.rmtree(LIVE_DIR, ignore_errors=True); os.makedirs(os.path.dirname(LIVE_DIR), exist_ok=True); shutil.move(stage, LIVE_DIR)
    return True, []


def pbs_observe(job_ids, pbs_file=None):
    """({job_id: {state, exit, mem_kb, walltime}}, problem). A non-zero return of qstat is a FAILED observation."""
    if pbs_file:
        return json.load(open(pbs_file)), ""
    if not job_ids:
        return {}, ""
    rc, out, err = sh(["ssh", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", LOGIN, "qstat -xf " + " ".join(job_ids)], timeout=300)
    if rc != 0:
        return None, f"qstat failed (rc {rc}): {(err or out).strip()[:160]}"
    obs, cur = {}, None
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("Job Id:"):
            cur = s.split(":", 1)[1].strip(); obs[cur] = {"state": None}
        elif cur and " = " in s:
            k, v = s.split(" = ", 1)
            if k == "job_state":
                obs[cur]["state"] = v
            elif k == "Exit_status":
                obs[cur]["exit"] = int(v)
            elif k == "resources_used.mem":
                obs[cur]["mem_kb"] = int(v[:-2]) if v.endswith("kb") else None
            elif k == "resources_used.walltime":
                obs[cur]["walltime"] = v
    missing = [j for j in job_ids if j not in obs or not obs[j].get("state")]
    if missing:
        return None, f"qstat returned 0 but did not describe {missing}"
    return obs, ""


def reconcile(man, verify, obs, ledger):
    """(alarms, notes, per-job summaries, the bound job map)."""
    alarms, notes, summary, jobs = [], [], {}, {}
    root = LIVE_DIR + "/root"
    mem_stop = float(man["pbs"].get("mem_stop_gib", 0) or 0) * 2 ** 30
    mem_req_kb = float(man["pbs"]["mem_gb"]) * 1024 ** 2
    vreps = verify.get("reps", {})
    planned = {}
    for e in sorted((e for e in ledger["entries"].values() if e.get("kind") == "bank"), key=lambda e: int(e["rep"])):
        n = int(e["rep"]); pp = os.path.join(root, "plans", f"job_{n}.json")
        jobs[str(n)] = dict(job_id=e.get("job_id"), token=e.get("token"), plan_sha256=sha_file(pp) if os.path.exists(pp) else None)
        if not os.path.exists(pp):
            alarms.append(f"bank job {n}: no plan file"); continue
        plan = json.load(open(pp)); j = e.get("job_id")
        o = (obs or {}).get(j, {}) if j else {}
        state = o.get("state"); terminal = state in TERMINAL
        s_sum = dict(job_id=j, state=state, exit=o.get("exit"), slots=len(plan["slots"]), ended=0, exits={}, new=0, resumed=0, left=0)
        if not j:
            alarms.append(f"bank job {n}: reserved but not bound to a PBS id")
        if j and o.get("mem_kb") is not None and o["mem_kb"] > 0.9 * mem_req_kb:
            alarms.append(f"bank job {n}: scheduler memory {o['mem_kb']/1024**2:.1f} GiB above 90 % of the request")
        if terminal and o.get("exit") not in (0, 75):
            alarms.append(f"bank job {n} ({j}): scheduler state {state}, exit {o.get('exit')}")
        if terminal and e.get("runner_exit") is None:
            alarms.append(f"bank job {n} ({j}): terminal in the scheduler but no runner end in the ledger")
        for sl in plan["slots"]:
            reps = [int(r) for r in sl["reps"]]
            for r in reps:
                planned[r] = (n, int(sl["slot"]))
            stp = os.path.join(root, "status", f"job{j}.slot{sl['slot']}.json")
            st = None
            if os.path.exists(stp):
                try:
                    st = json.load(open(stp))
                except Exception:
                    alarms.append(f"bank job {n} slot {sl['slot']}: status unreadable")
            if st is None:
                if terminal:
                    alarms.append(f"bank job {n} slot {sl['slot']}: no worker status after the job ended (killed, segfault or import failure: read its log)")
                continue
            s_sum["ended"] += 1; s_sum["exits"][str(st.get("exit"))] = s_sum["exits"].get(str(st.get("exit")), 0) + 1
            new, res, left = st.get("new", []), st.get("resumed", []), st.get("left", [])
            if st.get("reps") != reps:
                alarms.append(f"bank job {n} slot {sl['slot']}: status reps {st.get('reps')} are not the plan's {reps}")
            if set(new) & set(res) or set(new) & set(left) or set(res) & set(left) or sorted(new + res + left) != sorted(reps):
                alarms.append(f"bank job {n} slot {sl['slot']}: new/resumed/left are not a partition of {reps}")
            ex = st.get("exit")
            if ex == 0 and left:
                alarms.append(f"bank job {n} slot {sl['slot']}: exit 0 with reps left {left}")
            elif ex == 75 and not left:
                alarms.append(f"bank job {n} slot {sl['slot']}: exit 75 with nothing left")
            elif ex not in (0, 75):
                alarms.append(f"bank job {n} slot {sl['slot']}: worker exit {ex} ({str(st.get('reason'))[:120]})")
            if mem_stop and finite_nonneg(st.get("maxrss")) and st["maxrss"] > mem_stop:
                alarms.append(f"bank job {n} slot {sl['slot']}: worker maxrss {st['maxrss']/2**30:.2f} GiB above the stop")
            for k in ("wall_s", "cpu_s", "maxrss"):
                if not finite_nonneg(st.get(k)):
                    alarms.append(f"bank job {n} slot {sl['slot']}: status {k} is not finite and non-negative")
            s_sum["new"] += len(new); s_sum["resumed"] += len(res); s_sum["left"] += len(left)
            for r in new + res:
                v = vreps.get(str(r))
                if not v or not v.get("record") or not v["record"].get("ok"):
                    alarms.append(f"bank rep {r}: no valid record in the producer runtime ({(v or {}).get('record')})"); continue
                if not v.get("timing") or not v["timing"].get("ok"):
                    alarms.append(f"bank rep {r}: no valid timing ({(v or {}).get('timing')})"); continue
                if r in new and (v["timing"].get("job") != j or v["timing"].get("slot") != int(sl["slot"])):
                    alarms.append(f"bank rep {r}: timing names job {v['timing'].get('job')} slot {v['timing'].get('slot')}, not {j} slot {sl['slot']}")
        summary[str(n)] = s_sum
    for r, v in vreps.items():
        if int(r) not in planned:
            alarms.append(f"bank rep {r}: a record or timing that no plan assigns (foreign evidence)")
        elif v.get("record") and not v["record"].get("ok"):
            alarms.append(f"bank rep {r}: invalid record ({v['record'].get('reason')})")
        elif v.get("record") and v["record"].get("ok") and not (v.get("timing") or {}).get("ok"):
            alarms.append(f"bank rep {r}: record without a valid timing")
    return alarms, notes, summary, jobs


def ledger_line(path, label):
    if not os.path.exists(path):
        return f"{label}: ledger not in this snapshot"
    led = json.load(open(path))
    settled = sum(float(e.get("settled_core_h", 0) or 0) for e in led["entries"].values() if e.get("state") == "settled")
    live = sum(float(e["reserved_core_h"]) for e in led["entries"].values() if e.get("state") != "settled")
    return f"{label}: cap {led.get('cap_core_h')} settled {settled:.1f} live {live:.1f}"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=os.path.join(HERE, "row22_bank_manifest.json"))
    ap.add_argument("--no-pull", action="store_true", help="tests: read the local cache (never fresh evidence)")
    ap.add_argument("--verify-file", default=None, help="tests: a verify document instead of the producer runtime")
    ap.add_argument("--pbs-file", default=None, help="tests: {job_id: {state, exit, mem_kb}} instead of the scheduler")
    ap.add_argument("--publish-receipt", action="store_true")
    ap.add_argument("--qualify", type=int, default=None)
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); now = time.time()
    manifest_rel = "chpc/" + os.path.basename(a.manifest)
    alarms = []
    fresh = False
    if not a.no_pull:
        fresh, probs = fresh_snapshot(man); alarms += probs
    if a.verify_file:
        verify = json.load(open(a.verify_file)); vsha = sha_file(a.verify_file); vprob = ""
    else:
        verify, vsha, vprob = verify_remote(man, manifest_rel)
    if vprob:
        alarms.append(vprob); verify = verify or {"reps": {}}
    led_p = os.path.join(LIVE_DIR, "campaign", "budget.json")
    ledger = json.load(open(led_p)) if os.path.exists(led_p) else {"entries": {}}
    if not os.path.exists(led_p):
        alarms.append("the bank ledger is not in the snapshot")
    ids = [e["job_id"] for e in ledger["entries"].values() if e.get("kind") == "bank" and e.get("job_id")]
    obs, oprob = pbs_observe(ids, a.pbs_file)
    if oprob:
        alarms.append(oprob)
    if verify.get("seed_problem"):
        alarms.append(f"seed gate: {verify['seed_problem']}")
    if verify.get("environment_bad") or verify.get("code_bad"):
        alarms.append(f"producer runtime: environment {verify.get('environment_bad')} code {verify.get('code_bad')}")
    if verify.get("binding_equal") is False:
        alarms.append("the bank binding is not what the producer runtime recomputes")
    if verify.get("manifest_sha256") and verify["manifest_sha256"] != sha_file(a.manifest):
        alarms.append("the producer runtime's manifest is not this manifest")
    al, notes, summary, jobs = reconcile(man, verify, obs, ledger)
    alarms += al
    production = fresh and not a.no_pull and not a.verify_file and not a.pbs_file
    print(f"ROW 22 BANK, live view at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))}  evidence: "
          f"{'FRESH snapshot' if fresh else 'NOT FRESH'}{'' if production else ' (not production)'}")
    print("  " + ledger_line(led_p, "bank ledger"))
    nrec = sum(1 for v in verify.get("reps", {}).values() if (v.get("record") or {}).get("ok"))
    print(f"  valid records {nrec}/{len(man['datasets']['reps'])} (producer runtime); verify {str(vsha)[:12]}")
    for n, s in summary.items():
        print(f"  bank job {n} {s['job_id']} PBS {s['state']} exit {s['exit']}: workers ended {s['ended']}/{s['slots']} exits {s['exits']}, "
              f"new {s['new']} resumed {s['resumed']} left {s['left']}")
    print("\n  ALARMS:" if alarms else ("\n  no alarms (fresh evidence)" if fresh else "\n  no alarms, but NOT fresh evidence"))
    for x in alarms:
        print("   -", x)
    bp = os.path.join(LIVE_DIR, "root", "bank_binding.json")
    bound = dict(manifest_sha256=sha_file(a.manifest), root=man["storage"]["root"], campaign=man["storage"]["campaign"],
                 code=dict(man["code"]["files"]), wrapper_sha256=man.get("environment", {}).get("wrapper_sha256"),
                 bank_binding_sha256=sha_file(bp) if os.path.exists(bp) else None, verify_sha256=vsha, jobs=jobs)
    receipt = dict(schema=WATCH_SCHEMA, time=now, fresh=fresh, production=production, alarms=alarms, bound=bound, jobs=summary)
    os.makedirs(RECEIPTS, exist_ok=True)
    if a.verify_file is None and verify.get("reps") is not None:
        open(os.path.join(RECEIPTS, f"verify_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime(now))}.json"), "w").write(json.dumps(verify, sort_keys=True))
    rc_out = 1 if (alarms or not fresh) else 0
    if a.publish_receipt or a.qualify is not None:
        rp = os.path.join(RECEIPTS, f"bank_watch_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime(now))}.json")
        json.dump(receipt, open(rp, "w"), indent=1, allow_nan=False)
        if production:
            rc, _, err = sh(["scp", "-q", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", rp, f"{HOST}:{man['storage']['root']}/gate/{os.path.basename(rp)}"])
            print(f"  receipt {os.path.basename(rp)} " + ("copied to the root's gate" if rc == 0 else f"NOT copied (rc {rc}: {err.strip()[:80]})"))
    if a.qualify is not None:
        n = str(int(a.qualify)); why = []
        if not production:
            why.append("the evidence is not fresh production evidence")
        if alarms:
            why.append(f"{len(alarms)} alarm(s)")
        s = summary.get(n)
        if not s:
            why.append(f"no bank job {n} in the ledger")
        else:
            if s["state"] not in TERMINAL or s["exit"] != 0:
                why.append(f"job {n} is not terminal with scheduler exit 0 (state {s['state']}, exit {s['exit']})")
            if s["ended"] != s["slots"] or s["exits"] != {"0": s["slots"]}:
                why.append(f"job {n}: not every planned worker ended with exit 0 ({s['exits']}, {s['ended']}/{s['slots']})")
            if s["left"]:
                why.append(f"job {n}: {s['left']} planned rep(s) left")
        jn = jobs.get(n)
        if not jn or None in jn.values():
            why.append(f"job {n} has no PBS id, token or plan hash to bind")
        if why:
            print(f"\n  NOT QUALIFIED (bank job {n}):"); [print("   -", w) for w in why]
            return 1
        qp = os.path.join(RECEIPTS, f"qualified_bank_job{n}.json")
        json.dump(dict(schema=QUAL_SCHEMA, qualified_job=int(n), by="R052", time=now, production=production, bound=bound, receipt=receipt),
                  open(qp, "w"), indent=1, allow_nan=False)
        rc, _, err = sh(["scp", "-q", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", qp, f"{HOST}:{man['storage']['root']}/gate/qualified_bank_job{n}.json"])
        print(f"\n  QUALIFIED: bank job {n} ({sha_file(qp)[:16]}) " + ("copied to the root's gate" if rc == 0 else f"NOT copied (rc {rc})")
              + " - evidence for the reviewer; the submitter also needs the adopted review")
        return 0 if rc == 0 else 1
    return rc_out


if __name__ == "__main__":
    sys.exit(main())
