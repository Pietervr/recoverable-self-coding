"""Ledger row 19 stage 2: the screen's live view, watch receipt and pilot qualification, per role (Mac). Codex RSC 9202e8b item 5.

EVIDENCE every call: (1) the producer-runtime verdict, `t1py chpc/row19_screen_verify.py --role R` in the screen clone, its stdout
SHA-256 bound; (2) a fresh pull of the role's root and campaign (rotated in only when every pull succeeded); (3) one `qstat -xf`
that must RETURN 0 and describe every job of the role.
RAW ONLY (item 4): nothing here reads a statistic, builds an interval, endpoint, decision or coverage. Records are reported as
valid/invalid with their checksums; the scientific payload never enters this view.
RECONCILIATION per job of the role: a terminal job (F/E/X/gone) has a status for every planned slot; the status's assignment
equals the plan slot's (refit: rep and indices; orig: reps); new / resumed / left partition it; exit 0 iff nothing is left,
75 only with work left, anything else an alarm; every new or resumed unit has a valid record and a valid timing, and a new
unit's timing names this job and slot; worker memory under the stop; scheduler memory under 90 % of the request; a terminal
job's scheduler exit 0 or 75 and its runner end in the ledger; records no plan assigns are foreign (an alarm). Refit task
bindings: every binding must equal what the producer runtime recomputes and name the declared identity. ANCHORS: every
required overlap present, compared and equal on all three anchors; any invalid anchor record or difference is an alarm.
RECEIPT (--publish-receipt): schema row19-screen-watch-1, role, fresh, production, alarms, bound = manifest SHA-256, root,
campaign, code pins, wrapper, every job of the role (PBS id, token, plan SHA-256), every task binding's SHA-256, the anchor
verdict's SHA-256 and the verify document's SHA-256; copied to <root>/gate/watch_<role>_<stamp>.json.
QUALIFICATION (--qualify 1): fresh production evidence, zero alarms, job 1 terminal with scheduler exit 0 or 75, every planned
slot ended 0 with every planned unit a valid record with timing, the three anchors equal; refit: job 1's reps all bound.

    python chpc/row19_screen_status.py --manifest chpc/row19_screen_manifest.json --role refit [--publish-receipt] [--qualify 1]
Exit 1 on any alarm or when the evidence is not fresh.

REVISION 2 (Codex RSC a1ce224): qualification needs scheduler state F exactly (not E, X or gone), scheduler exit and the
ledger's runner exit both 0 or 75, finite scheduler memory and finite worker memory for every slot; a refit worker's status
must name its task's declared identity; a status file for a job or slot no plan assigns is an alarm; every rep of a STARTED
job (scheduler R or terminal) must have a task binding, checked against the plans rather than the files present; the full
verifier document is saved beside every receipt and copied to the gate; the anchor verdict itself is embedded in the receipt
and the qualification (not only its digest); the job summary carries timings, peaks and failures.

REVISION 3 (Codex RSC ee99ee1, R2 and R3): EVERY job, not only job 1: a terminal job must be scheduler state F with scheduler
and runner exits 0/75 and finite observed scheduler memory; a runner exit outside 0/75 is an alarm whatever the state; every
ended worker needs finite memory and wall time. The status directory is checked against the WHOLE planned job/slot universe
(a status of an unplanned job is an alarm). The producer verifier runs from the CONTROLLER clone named in the lineage
(chpc/row19_screen_controls.json `deployment`), and its document must report the latest controller generation with a clean
lineage check; the producer's binding digests must equal the local snapshot's (one coherent observation); the full verifier
document is saved, copied to the gate and only a SUCCESSFUL copy lets the evidence count as production; the receipt and the
qualification name the verifier file and its SHA-256, and the qualification binds job 1's own tasks only."""
import os, sys, json, glob, math, time, shutil, hashlib, argparse, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
HOST, LOGIN = "chpc-scp", "lengau"
BASE = os.path.join(HERE, "results", "row19_screen")
LIVE_DIR = os.path.join(BASE, "live")
RECEIPTS = os.path.join(BASE, "receipts")
WATCH_SCHEMA = "row19-screen-watch-1"
QUAL_SCHEMA = "row19-screen-qualification-1"
TERMINAL = ("F", "E", "X", "gone")
KIND = {"refit": "shard", "orig": "orig"}


def sh(cmd, timeout=900):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return 255, "", str(e)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha_bytes(open(p, "rb").read())


def finite_nonneg(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x >= 0


def controls():
    return json.load(open(os.path.join(HERE, "row19_screen_controls.json")))


def verify_remote(man, role, manifest_rel):
    clone, tc = controls()["deployment"]["controller_clone"], man["shard"]["toolchain"]
    rc, out, err = sh(["ssh", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", LOGIN,
                       f"cd {clone}/workspace_demo/t1_access && {tc}/t1py chpc/row19_screen_verify.py --manifest {manifest_rel} --role {role}"], timeout=3600)
    if rc != 0:
        return None, None, f"producer-runtime verify failed (rc {rc}): {err.strip()[-200:]}"
    lines = [l for l in out.splitlines() if l.startswith("{")]
    if len(lines) != 1:
        return None, None, "producer-runtime verify printed no single JSON document"
    doc = json.loads(lines[0])
    if doc.get("schema") != "row19-screen-verify-1" or doc.get("role") != role:
        return None, None, "producer-runtime verify has another schema or role"
    g = doc.get("generation") or {}
    latest = controls()["versions"][-1]["version"]
    if g.get("version") != latest or g.get("controls_problem"):
        return None, None, f"the producer verifier is generation {g.get('version')} ({g.get('controls_problem')}), not the latest {latest}"
    return doc, sha_bytes(lines[0].encode()), ""


def fresh_snapshot(man, role):
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    live = os.path.join(LIVE_DIR, role); stage = os.path.join(BASE, f"stage_{role}_{stamp}")
    problems = []
    for name, remote in (("campaign", man["storage"]["campaign"]), ("root", man["storage"]["root"])):
        local = os.path.join(stage, name); os.makedirs(local, exist_ok=True)
        rc, out, err = sh(["scp", "-q", "-r", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", f"{HOST}:{remote}/.", local])
        if rc != 0:
            problems.append(f"pull of {remote} failed (rc {rc}): {err.strip()[:160]}")
    if problems:
        shutil.rmtree(stage, ignore_errors=True); return False, problems
    shutil.rmtree(live, ignore_errors=True); os.makedirs(LIVE_DIR, exist_ok=True); shutil.move(stage, live)
    return True, []


def pbs_observe(job_ids, pbs_file=None):
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
    missing = [j for j in job_ids if j not in obs or not obs[j].get("state")]
    if missing:
        return None, f"qstat returned 0 but did not describe {missing}"
    return obs, ""


def anchor_alarms(verify):
    an = verify.get("anchors") or {}
    if an.get("problem"):
        return [f"anchors: {an['problem']}"]
    al = []
    reps = an.get("reps") or {}
    if sorted(reps) != ["0", "1", "2"]:
        al.append(f"anchors: the verdict covers {sorted(reps)}, not all three development anchors")
    for r, e in reps.items():
        if e.get("problem"):
            al.append(f"anchor {r}: {e['problem']}")
        if e.get("missing"):
            al.append(f"anchor {r}: required overlap {e['missing']} not present in both the shard root and the sequential chain")
        if e.get("invalid"):
            al.append(f"anchor {r}: {len(e['invalid'])} invalid record(s), e.g. {e['invalid'][0]}")
        if e.get("differ"):
            al.append(f"anchor {r}: payload DIFFERS at {e['differ']}")
        if e.get("conflict"):
            al.append(f"anchor {r}: conflicting duplicate sequential records at {e['conflict']}")
        if 0 not in (e.get("equal") or []):
            al.append(f"anchor {r}: index 0 is not observed equal")
        if not e.get("equal"):
            al.append(f"anchor {r}: no overlap observed equal")
    return al


def reconcile(man, role, verify, obs, ledger, live):
    alarms, summary, jobs = [], {}, {}
    root = os.path.join(live, "root")
    mem_stop = float(man["pbs"].get("mem_stop_gib", 0) or 0) * 2 ** 30
    mem_req_kb = float(man["pbs"]["mem_gb"]) * 1024 ** 2
    units = verify.get("units", {}); assigned = set(); expected_status = set()
    for e in sorted((e for e in ledger["entries"].values() if e.get("kind") == KIND[role]), key=lambda e: int(e["rep"])):
        n = int(e["rep"]); pp = os.path.join(root, "plans", f"job_{n}.json")
        jobs[str(n)] = dict(job_id=e.get("job_id"), token=e.get("token"), plan_sha256=sha_file(pp) if os.path.exists(pp) else None)
        if not os.path.exists(pp):
            alarms.append(f"{role} job {n}: no plan file"); continue
        plan = json.load(open(pp)); j = e.get("job_id")
        o = (obs or {}).get(j, {}) if j else {}
        state = o.get("state"); terminal = state in TERMINAL
        s_sum = dict(job_id=j, state=state, exit=o.get("exit"), runner_exit=e.get("runner_exit"), mem_kb=o.get("mem_kb"),
                     slots=len(plan["slots"]), ended=0, exits={}, new=0, resumed=0, left=0, max_worker_maxrss=None, max_wall_s=None,
                     failed_units=[])
        started = state == "R" or terminal
        expected_status.update(f"job{j}.slot{sl['slot']}.json" for sl in plan["slots"])
        if not j:
            alarms.append(f"{role} job {n}: reserved but not bound to a PBS id")
        if o.get("mem_kb") is not None and o["mem_kb"] > 0.9 * mem_req_kb:
            alarms.append(f"{role} job {n}: scheduler memory above 90 % of the request")
        if terminal and (state != "F" or o.get("exit") not in (0, 75)):
            alarms.append(f"{role} job {n} ({j}): terminal as state {state}, scheduler exit {o.get('exit')} (F with 0/75 required)")
        if terminal and e.get("runner_exit") is None:
            alarms.append(f"{role} job {n} ({j}): terminal but no runner end in the ledger")
        if e.get("runner_exit") not in (None, 0, 75):
            alarms.append(f"{role} job {n} ({j}): runner exit {e.get('runner_exit')}")
        if terminal and not finite_nonneg(o.get("mem_kb")):
            alarms.append(f"{role} job {n} ({j}): no finite observed scheduler memory")
        for sl in plan["slots"]:
            want = ([f"{int(sl['rep'])}/{int(i)}" for i in sl["indices"]] if role == "refit" else [str(int(r)) for r in sl["reps"]])
            assigned.update(want)
            stp = os.path.join(root, "status", f"job{j}.slot{sl['slot']}.json")
            st = json.load(open(stp)) if os.path.exists(stp) else None
            if st is None:
                if terminal:
                    alarms.append(f"{role} job {n} slot {sl['slot']}: no worker status after the job ended (read its log)")
                continue
            s_sum["ended"] += 1; s_sum["exits"][str(st.get("exit"))] = s_sum["exits"].get(str(st.get("exit")), 0) + 1
            if st.get("job") != j or st.get("slot") != int(sl["slot"]):
                alarms.append(f"{role} job {n} slot {sl['slot']}: the status names job {st.get('job')} slot {st.get('slot')}")
            if finite_nonneg(st.get("maxrss")):
                s_sum["max_worker_maxrss"] = max(s_sum["max_worker_maxrss"] or 0, st["maxrss"])
            else:
                alarms.append(f"{role} job {n} slot {sl['slot']}: worker memory is not finite")
            if finite_nonneg(st.get("wall_s")):
                s_sum["max_wall_s"] = max(s_sum["max_wall_s"] or 0, st["wall_s"])
            else:
                alarms.append(f"{role} job {n} slot {sl['slot']}: worker wall time is not finite")
            if role == "refit":
                if st.get("rep") != int(sl["rep"]) or st.get("indices") != [int(i) for i in sl["indices"]]:
                    alarms.append(f"{role} job {n} slot {sl['slot']}: status assignment is not the plan's")
                if st.get("ident") != man["datasets"]["identities"].get(str(int(sl["rep"]))):
                    alarms.append(f"{role} job {n} slot {sl['slot']}: the status names another identity than the declared one")
                key = lambda i: f"{int(sl['rep'])}/{int(i)}"
            else:
                if st.get("reps") != [int(r) for r in sl["reps"]]:
                    alarms.append(f"{role} job {n} slot {sl['slot']}: status assignment is not the plan's")
                key = lambda r: str(int(r))
            new, res, left = [key(x) for x in st.get("new", [])], [key(x) for x in st.get("resumed", [])], [key(x) for x in st.get("left", [])]
            if set(new) & set(res) or set(new) & set(left) or set(res) & set(left) or sorted(new + res + left) != sorted(want):
                alarms.append(f"{role} job {n} slot {sl['slot']}: new/resumed/left are not a partition of its assignment")
            ex = st.get("exit")
            if ex == 0 and left:
                alarms.append(f"{role} job {n} slot {sl['slot']}: exit 0 with work left")
            elif ex == 75 and not left:
                alarms.append(f"{role} job {n} slot {sl['slot']}: exit 75 with nothing left")
            elif ex not in (0, 75):
                alarms.append(f"{role} job {n} slot {sl['slot']}: worker exit {ex} ({str(st.get('reason'))[:120]})")
            if mem_stop and finite_nonneg(st.get("maxrss")) and st["maxrss"] > mem_stop:
                alarms.append(f"{role} job {n} slot {sl['slot']}: worker memory above the stop")
            s_sum["new"] += len(new); s_sum["resumed"] += len(res); s_sum["left"] += len(left)
            s_sum["failed_units"] += [u for u in new + res if ((units.get(u) or {}).get("record") or {}).get("failed")]
            for u in new + res:
                v = units.get(u) or {}
                if not (v.get("record") or {}).get("ok"):
                    alarms.append(f"{role} unit {u}: no valid record in the producer runtime"); continue
                if not (v.get("timing") or {}).get("ok"):
                    alarms.append(f"{role} unit {u}: no valid timing"); continue
                if u in new and (v["timing"].get("job") != j or v["timing"].get("slot") != int(sl["slot"])):
                    alarms.append(f"{role} unit {u}: timing names another job or slot")
        if role == "refit" and started:
            bound_reps = set((verify.get("bindings") or {}).keys())
            missing = sorted({int(sl["rep"]) for sl in plan["slots"]} - {int(k) for k in bound_reps if k.isdigit()})
            if missing:
                alarms.append(f"{role} job {n}: started, but reps {missing[:5]} have no task binding")
        summary[str(n)] = s_sum
    for sp in glob.glob(os.path.join(root, "status", "*")):
        if os.path.basename(sp) not in expected_status:
            alarms.append(f"{role}: status {os.path.basename(sp)!r} that no planned job and slot assigns")
    for u, v in units.items():
        if u not in assigned:
            alarms.append(f"{role} unit {u}: evidence no plan assigns (foreign)")
        elif not (v.get("record") or {}).get("ok") and v.get("record") is not None:
            alarms.append(f"{role} unit {u}: invalid record ({(v.get('record') or {}).get('reason')})")
    for r, b in (verify.get("bindings") or {}).items():
        if not b.get("ok") or not b.get("declared_ident_equal"):
            alarms.append(f"task binding of rep {r}: {b.get('reason') or 'not the declared identity'}")
    return alarms, summary, jobs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True); ap.add_argument("--role", required=True, choices=("refit", "orig"))
    ap.add_argument("--no-pull", action="store_true"); ap.add_argument("--verify-file", default=None); ap.add_argument("--pbs-file", default=None)
    ap.add_argument("--publish-receipt", action="store_true"); ap.add_argument("--qualify", type=int, default=None)
    a = ap.parse_args(argv)
    man = json.load(open(a.manifest)); role = a.role; now = time.time()
    if man.get("role") != role:
        print(f"{a.manifest} is not the {role} manifest"); return 2
    live = os.path.join(LIVE_DIR, role); alarms = []; fresh = False
    if not a.no_pull:
        fresh, probs = fresh_snapshot(man, role); alarms += probs
    if a.verify_file:
        verify = json.load(open(a.verify_file)); vsha = sha_file(a.verify_file); vprob = ""
    else:
        verify, vsha, vprob = verify_remote(man, role, "chpc/" + os.path.basename(a.manifest))
    if vprob:
        alarms.append(vprob); verify = verify or {}
    if verify.get("environment_bad") or verify.get("code_bad"):
        alarms.append(f"producer runtime: environment {verify.get('environment_bad')} code {verify.get('code_bad')}")
    if verify.get("manifest_sha256") and verify["manifest_sha256"] != sha_file(a.manifest):
        alarms.append("the producer runtime's manifest is not this manifest")
    alarms += anchor_alarms(verify)
    led_p = os.path.join(live, "campaign", "budget.json")
    ledger = json.load(open(led_p)) if os.path.exists(led_p) else {"entries": {}}
    ids = [e["job_id"] for e in ledger["entries"].values() if e.get("kind") == KIND[role] and e.get("job_id")]
    obs, oprob = pbs_observe(ids, a.pbs_file)
    if oprob:
        alarms.append(oprob)
    al, summary, jobs = reconcile(man, role, verify, obs, ledger, live)
    alarms += al
    production = fresh and not (a.no_pull or a.verify_file or a.pbs_file)
    nvalid = sum(1 for v in (verify.get("units") or {}).values() if (v.get("record") or {}).get("ok"))
    print(f"ROW 19 SCREEN ({role}), live view at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))}  evidence: "
          f"{'FRESH snapshot' if fresh else 'NOT FRESH'}{'' if production else ' (not production)'}; valid units {nvalid}; verify {str(vsha)[:12]}")
    for n, s in summary.items():
        print(f"  {role} job {n} {s['job_id']} PBS {s['state']} exit {s['exit']}: workers ended {s['ended']}/{s['slots']} exits {s['exits']}, "
              f"new {s['new']} resumed {s['resumed']} left {s['left']}")
    for r, e in sorted(((verify.get("anchors") or {}).get("reps") or {}).items()):
        print(f"  anchor {r}: required {e.get('required')} compared {len(e.get('compared', []))} equal {len(e.get('equal', []))}")
    print("\n  ALARMS:" if alarms else ("\n  no alarms (fresh evidence)" if fresh else "\n  no alarms, but NOT fresh evidence"))
    for x in alarms:
        print("   -", x)
    bindings = {os.path.basename(p)[5:-5]: sha_file(p) for p in sorted(glob.glob(os.path.join(live, "root", "task_*.json")))}
    produced = {k: (v or {}).get("sha256") for k, v in (verify.get("bindings") or {}).items()}
    if role == "refit" and produced != bindings:
        alarms.append("the producer's task-binding digests are not the local snapshot's (not one coherent observation; recollect)")
    bound = dict(manifest_sha256=sha_file(a.manifest), root=man["storage"]["root"], campaign=man["storage"]["campaign"],
                 code=dict(man["code"]["files"]), wrapper_sha256=man.get("environment", {}).get("wrapper_sha256"), jobs=jobs,
                 bindings=bindings, anchors_sha256=sha_bytes(json.dumps(verify.get("anchors"), sort_keys=True).encode()), verify_sha256=vsha)
    receipt = dict(schema=WATCH_SCHEMA, role=role, time=now, fresh=fresh, production=production, alarms=alarms, bound=bound, jobs=summary,
                   anchors=verify.get("anchors"), plan_slots={k: v["slots"] for k, v in summary.items()})
    os.makedirs(RECEIPTS, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(now))
    vp = os.path.join(RECEIPTS, f"verify_{role}_{stamp}.json")
    json.dump(verify, open(vp, "w"), sort_keys=True)
    vsha_saved = sha_file(vp)
    if production:
        rc, _, err = sh(["scp", "-q", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", vp, f"{HOST}:{man['storage']['root']}/gate/{os.path.basename(vp)}"])
        if rc != 0:
            alarms.append(f"the full verifier document could not be retained in the gate (rc {rc}); this is not production evidence")
            production = False; receipt.update(production=False, alarms=alarms)
    bound["verify_file"] = os.path.basename(vp); bound["verify_file_sha256"] = vsha_saved
    if a.publish_receipt or a.qualify is not None:
        rp = os.path.join(RECEIPTS, f"watch_{role}_{stamp}.json")
        json.dump(receipt, open(rp, "w"), indent=1, allow_nan=False)
        if production:
            rc, _, err = sh(["scp", "-q", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", rp, f"{HOST}:{man['storage']['root']}/gate/{os.path.basename(rp)}"])
            print(f"  receipt {os.path.basename(rp)} " + ("copied to the gate" if rc == 0 else f"NOT copied (rc {rc})"))
    if a.qualify is not None:
        n = str(int(a.qualify)); why = []
        if not production:
            why.append("the evidence is not fresh production evidence")
        if alarms:
            why.append(f"{len(alarms)} alarm(s)")
        s = summary.get(n)
        if not s:
            why.append(f"no {role} job {n} in the ledger")
        else:
            if s["state"] != "F" or s["exit"] not in (0, 75) or s.get("runner_exit") not in (0, 75):
                why.append(f"job {n} is not state F with scheduler and runner exits 0 or 75")
            if not (finite_nonneg(s.get("mem_kb")) and finite_nonneg(s.get("max_worker_maxrss"))):
                why.append(f"job {n}: observed scheduler and worker memory are not finite")
            if s["ended"] != s["slots"] or s["exits"] != {"0": s["slots"]} or s["left"]:
                why.append(f"job {n}: not every planned worker completed its assignment ({s['exits']}, left {s['left']})")
        jn = jobs.get(n)
        if not jn or None in jn.values():
            why.append(f"job {n} has no PBS id, token or plan hash to bind")
        if role == "refit" and s:
            plan = json.load(open(os.path.join(live, "root", "plans", f"job_{n}.json")))
            unbound = [sl["rep"] for sl in plan["slots"] if str(sl["rep"]) not in bindings]
            if unbound:
                why.append(f"job {n}'s reps {unbound[:5]} have no task binding")
        if why:
            print(f"\n  NOT QUALIFIED ({role} job {n}):"); [print("   -", w) for w in why]; return 1
        qp = os.path.join(RECEIPTS, f"qualified_{role}_job{n}.json")
        p1 = json.load(open(os.path.join(live, "root", "plans", f"job_{n}.json")))
        reps1 = {str(sl["rep"]) for sl in p1["slots"]} if role == "refit" else set()
        qbound = dict(bound, jobs={n: jobs[n]}, bindings={k: v for k, v in bindings.items() if k in reps1})
        json.dump(dict(schema=QUAL_SCHEMA, role=role, qualified_job=int(n), by="R052", time=now, production=True, bound=qbound, receipt=receipt,
                       anchors=verify.get("anchors"), verify_file=os.path.basename(vp)),
                  open(qp, "w"), indent=1, allow_nan=False)
        rc, _, err = sh(["scp", "-q", "-o", "ConnectTimeout=20", "-o", "BatchMode=yes", qp, f"{HOST}:{man['storage']['root']}/gate/qualified_{role}_job{n}.json"])
        print(f"\n  QUALIFIED: {role} job {n} ({sha_file(qp)[:16]}) " + ("copied to the gate" if rc == 0 else f"NOT copied (rc {rc})"))
        return 0 if rc == 0 else 1
    return 1 if (alarms or not fresh) else 0


if __name__ == "__main__":
    sys.exit(main())
