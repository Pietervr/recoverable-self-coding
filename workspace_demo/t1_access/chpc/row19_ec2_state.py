"""Row 19 screen: the EC2 state shared by the Lengau ingestion, the status adapter and both admissions (Codex RSC 0483db4
V10-1, V10-2, V10-4, V10-8). Pure Python, no scientific imports, so the Mac and the Lengau login node load the same bytes.

Files under the screen root (written ONLY by the named producer, read by everyone):
  ec2/activation_e<epoch>.json   row19_partition.py activate (Lengau, under the plan lock): the serialized cutover proof
  ec2/authority/inventory.json   the Mac claim authority's inventory of EVERY EC2 attempt of every run (prod_authority.py
                                 inventory), INSTALLED only by row19_ec2_root.py install (monotonic generation; see below)
  ec2/register.json              row19_ec2_ingest.py: the ingestion journal
  ec2/HOLD                       written by an ingestion that saw a sentinel or replay difference; removed only by hand
  STOP                           the common screen STOP (Lengau workers, EC2 admission, EC2 instances via propagation)

`bound(root)` is the digest set a receipt binds and an admission recomputes: a newly journaled attempt (new inventory or
register bytes), a new activation or a HOLD changes it, so an older receipt can no longer admit anything.

REVISION 2 (Codex RSC 3dc0daf R1-2, R1-3):
  install_inventory  the ONLY writer of ec2/authority/inventory.json, run on the Lengau login node UNDER the plan lock
                     (row19_ec2_root.py install): a sealed, fresh inventory is installed only at a generation strictly above
                     the installed one (the same generation only with the same bytes - idempotent); every installation is
                     appended to ec2/authority/installed.jsonl. An attempt the Mac asks to disposition (`disposition_requested`)
                     is FENCED on the root in the same step: the register gains a 'dispositioned' entry with its key, global
                     sequence and coordinates (no ingestion of that attempt can ever start), or the request is refused when the
                     attempt already has an ingesting/ingested entry. The step writes ec2/authority/ack_g<generation>.json
                     (immutable) naming each fenced and each refused key; the Mac releases ownership ONLY against that
                     acknowledgement (prod_authority.py disposition-confirm). Ingestion and both admissions use the INSTALLED
                     view, never a copy supplied beside it.
  current_problems   what every admission rechecks under its lock beyond the receipt: whenever an activation, a register or
                     an installed inventory exists, a valid sealed installed inventory; every registered canonical
                     record/timing/status of every ingested coordinate still the registered bytes, the status still a complete
                     terminal status of exactly that attempt and slot; a dispositioned entry has published nothing."""
import hashlib, json, math, os, time

INVENTORY_SCHEMA = "t1-ec2-authority-inventory-1"
REGISTER_SCHEMA = "row19-ec2-register-2"
ACTIVATION_SCHEMA = "row19-ec2-activation-1"
INVENTORY_MAX_AGE_S = 6 * 3600              # an ingestion or a receipt never trusts an older authority view
ATTEMPT_STATES = ("intent", "launched", "rejected", "ambiguous", "reconciled")
INGESTION_STATES = ("pending", "ingested", "dispositioned")
REGISTER_STATES = ("ingesting", "ingested", "dispositioned")
ACK_SCHEMA = "row19-ec2-authority-ack-1"
CLASSES = ("production", "qualification")
WORKER_DONE, WORKER_RESUME, WORKER_HELD = 0, 75, 4


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def paths(root):
    e = os.path.join(root, "ec2")
    return dict(dir=e, register=os.path.join(e, "register.json"), inventory=os.path.join(e, "authority", "inventory.json"),
                installed=os.path.join(e, "authority", "installed.jsonl"), hold=os.path.join(e, "HOLD"), stop=os.path.join(root, "STOP"))


def ack_path(root, generation):
    return os.path.join(root, "ec2", "authority", f"ack_g{int(generation)}.json")


def activation_path(root, epoch):
    return os.path.join(root, "ec2", f"activation_e{int(epoch)}.json")


def _sha_or_none(p):
    return sha_file(p) if os.path.exists(p) else None


def bound(root):
    """The EC2 digests a whole-role receipt binds and every admission recomputes from the live root."""
    P = paths(root)
    acts = sorted(f for f in os.listdir(P["dir"]) if f.startswith("activation_e") and f.endswith(".json")) if os.path.isdir(P["dir"]) else []
    return dict(register_sha256=_sha_or_none(P["register"]), inventory_sha256=_sha_or_none(P["inventory"]),
                activations={f: sha_file(os.path.join(P["dir"], f)) for f in acts},
                hold=os.path.exists(P["hold"]), stop=os.path.exists(P["stop"]))


def inventory_body(inv):
    return {k: v for k, v in inv.items() if k != "sha256"}


def seal(inv):
    """The inventory with its own sha256 over the canonical body."""
    body = inventory_body(inv)
    return dict(body, sha256=sha_bytes(canonical(body)))


def inventory_problem(inv, now=None, max_age=INVENTORY_MAX_AGE_S):
    """'' for a complete, sealed, fresh authority inventory; otherwise why not. Every attempt of every run is present with a
    known state, ingestion state, class, a GLOBAL sequence and its coordinates; owners and fences are consistent with them."""
    now = time.time() if now is None else now
    if not isinstance(inv, dict) or inv.get("schema") != INVENTORY_SCHEMA:
        return "not an authority inventory"
    if inv.get("sha256") != sha_bytes(canonical(inventory_body(inv))):
        return "the inventory's seal does not match its body"
    t = inv.get("at")
    if not _num(t) or t > now + 60 or now - t > max_age:
        return f"the inventory time {t!r} is not finite, not in the past or older than {max_age} s"
    if not _int(inv.get("generation")) or inv["generation"] < 1:
        return "no integer generation"
    atts = inv.get("attempts")
    if not isinstance(atts, dict):
        return "no attempts map"
    seqs, owners = set(), {}
    for key, a in atts.items():
        if not isinstance(a, dict) or a.get("key") != key:
            return f"attempt {key}: malformed"
        if a.get("state") not in ATTEMPT_STATES or a.get("ingestion") not in INGESTION_STATES or a.get("class") not in CLASSES + ("benchmark",):
            return f"attempt {key}: unknown state/ingestion/class {a.get('state')}/{a.get('ingestion')}/{a.get('class')}"
        if not _int(a.get("sequence")) or a["sequence"] in seqs:
            return f"attempt {key}: sequence missing or not globally unique"
        seqs.add(a["sequence"])
        for fld in ("coordinates", "sentinels", "duplicates"):
            v = a.get(fld, [])
            if not isinstance(v, list) or not all(isinstance(c, list) and len(c) == 2 and all(_int(x) for x in c) for c in v):
                return f"attempt {key}: {fld} malformed"
        if not _num(a.get("charged_usd")) or a["charged_usd"] < 0:
            return f"attempt {key}: charged USD missing or negative"
        if not isinstance(a.get("disposition_requested", False), bool) or (a.get("disposition_requested") and
                                                                             (a.get("state") != "reconciled" or a.get("ingestion") != "pending")):
            return f"attempt {key}: a disposition request on an attempt that is not reconciled and pending"
        if owns(a):
            for c in a.get("coordinates", []):
                k = f"{c[0]}/{c[1]}"
                if k in owners:
                    return f"coordinate {k} owned by {owners[k]} and {key}"
                owners[k] = key
    if inv.get("owners") != {k: [v, atts[v]["sequence"]] for k, v in sorted(owners.items())}:
        return "the owners map is not the attempts' current ownership"
    fence = inv.get("fence")
    if not isinstance(fence, dict) or any(not _int(v) for v in fence.values()):
        return "no fence map"
    for key, a in atts.items():
        for c in a.get("coordinates", []):
            if a.get("state") != "rejected" and fence.get(f"{c[0]}/{c[1]}", -1) < a["sequence"]:
                return f"fence below attempt {key}'s sequence at {c}"
    return ""


def _atomic_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, path)


def installed_inventory(root, now=None, max_age=INVENTORY_MAX_AGE_S):
    """(inventory, '') for the root's installed, valid, sealed inventory (fresh within max_age), else (None, why)."""
    p = paths(root)["inventory"]
    if not os.path.exists(p):
        return None, "no authority inventory is installed on the root"
    try:
        inv = json.load(open(p))
    except Exception as e:
        return None, f"the installed authority inventory is unreadable ({type(e).__name__})"
    why = inventory_problem(inv, now, max_age)
    return (None, f"installed authority inventory: {why}") if why else (inv, "")


def install_inventory(root, inv, now=None):
    """Install `inv` as the root's current view (call ONLY under the plan lock). Returns (ack dict, problems). Monotonic:
    a strictly newer generation, or the same generation with the same bytes (idempotent). Fences every requested
    disposition in the register in the same step and writes the immutable acknowledgement."""
    now = time.time() if now is None else now
    why = inventory_problem(inv, now)
    if why:
        return None, [f"not installed: {why}"]
    P = paths(root)
    cur = None
    if os.path.exists(P["inventory"]):
        try:
            cur = json.load(open(P["inventory"]))
        except Exception:
            return None, ["the installed inventory is unreadable: repair by hand before installing another"]
        if not (_int(cur.get("generation")) and isinstance(cur.get("sha256"), str)):
            return None, ["the installed inventory carries no generation/seal: repair by hand before installing another"]
        if inv["generation"] < cur["generation"]:
            return None, [f"generation {inv['generation']} is older than the installed {cur['generation']} (an out-of-order delivery)"]
        if inv["generation"] == cur["generation"] and inv["sha256"] != cur["sha256"]:
            return None, [f"generation {inv['generation']} is installed with other bytes"]
    reg = json.load(open(P["register"])) if os.path.exists(P["register"]) else {
        "schema": REGISTER_SCHEMA, "authority_generation": 0, "fence": {}, "attempts": {}}
    if reg.get("schema") != REGISTER_SCHEMA:
        return None, ["the register is not schema 2"]
    fenced, refused = {}, {}
    for key, a in sorted(inv["attempts"].items()):
        if not a.get("disposition_requested"):
            continue
        e = reg["attempts"].get(a["attempt_id"])
        if e is not None and e.get("state") != "dispositioned":
            refused[key] = f"the register already holds an {e.get('state')} entry: the output is (being) ingested"; continue
        if e is not None and (e.get("key") != key or e.get("sequence") != a["sequence"]):
            refused[key] = "a dispositioned entry of another key/sequence exists under this attempt id"; continue
        if e is None:
            reg["attempts"][a["attempt_id"]] = dict(attempt_id=a["attempt_id"], key=key, sequence=a["sequence"], state="dispositioned",
                                                    cls=a["class"], plan_sha256=a["plan_sha256"], coordinates={},
                                                    fenced_coordinates=sorted(f"{c[0]}/{c[1]}" for c in a.get("coordinates", [])),
                                                    inventory_generation=inv["generation"], at=now)
            for c in a.get("coordinates", []):
                k = f"{c[0]}/{c[1]}"; reg["fence"][k] = max(reg["fence"].get(k, -1), a["sequence"])
        fenced[key] = dict(attempt_id=a["attempt_id"], sequence=a["sequence"],
                           coordinates_sha256=sha_bytes(canonical(sorted(a.get("coordinates", [])))))
    if fenced:                                    # the register is written only when there is a fence to record
        reg["authority_generation"] = max(reg.get("authority_generation", 0), inv["generation"])
        _atomic_json(P["register"], reg)
    _atomic_json(P["inventory"], inv)
    with open(P["installed"], "a") as fh:
        fh.write(json.dumps(dict(generation=inv["generation"], sha256=inv["sha256"], at=now)) + "\n"); fh.flush(); os.fsync(fh.fileno())
    ack = dict(schema=ACK_SCHEMA, generation=inv["generation"], inventory_sha256=inv["sha256"], dispositioned=fenced,
               refused=refused, register_sha256=_sha_or_none(P["register"]), at=now)
    ap = ack_path(root, inv["generation"])
    if os.path.exists(ap):
        old = json.load(open(ap))
        if {k: v for k, v in old.items() if k not in ("at", "register_sha256")} != {k: v for k, v in ack.items() if k not in ("at", "register_sha256")}:
            return None, [f"{os.path.basename(ap)} exists with another content"]
        return old, []
    _atomic_json(ap, ack)
    return ack, []


def current_problems(root, man, require=None):
    """R1-3: what an admission rechecks under its lock (see the module text). `require` forces the inventory requirement
    (the caller knows a partition is in force); otherwise it applies whenever EC2 evidence is on the root."""
    P = paths(root); out = []
    acts = [f for f in os.listdir(P["dir"]) if f.startswith("activation_e")] if os.path.isdir(P["dir"]) else []
    evidence = bool(acts) or os.path.exists(P["register"]) or os.path.exists(P["inventory"])
    if require or evidence:
        _, why = installed_inventory(root, max_age=float("inf"))
        if why:
            out.append(why)
    if not os.path.exists(P["register"]):
        return out
    try:
        reg = json.load(open(P["register"]))
        assert reg.get("schema") == REGISTER_SCHEMA
    except Exception:
        return out + ["the EC2 register is unreadable or not schema 2"]
    mem_stop = float(man["pbs"].get("mem_stop_gib", 0) or 0) * 2 ** 30
    idents = man["shard"]["identities"]
    for aid, e in sorted((reg.get("attempts") or {}).items()):
        st = e.get("state")
        if st not in REGISTER_STATES:
            out.append(f"EC2 attempt {aid}: unknown register state {st!r}"); continue
        if st == "dispositioned":
            if e.get("coordinates"):
                out.append(f"EC2 attempt {aid}: dispositioned but carries published coordinates")
            continue
        if st != "ingested":
            continue
        for k, ce in sorted((e.get("coordinates") or {}).items()):
            if ce.get("preexisting"):
                continue
            r, i = (int(x) for x in k.split("/"))
            sp = os.path.join(root, "ec2", "status", f"{aid}.slot{ce.get('slot')}.json")
            for what, fp, h in (("record", os.path.join(root, "records", f"rep{r}", f"rec_{i:03d}.json"), ce.get("record_sha256")),
                                ("timing", os.path.join(root, "timing", f"rep{r}", f"t_{i:03d}.json"), ce.get("timing_sha256")),
                                ("status", sp, ce.get("status_sha256"))):
                if not os.path.exists(fp) or sha_file(fp) != h:
                    out.append(f"EC2 unit {k} ({aid}): canonical {what} is missing or not the registered bytes")
            if os.path.exists(sp):
                try:
                    why = status_problem(json.load(open(sp)), aid, ce.get("slot"), r, i, idents.get(str(r)), mem_stop)
                except Exception as ex:
                    why = f"status unreadable ({type(ex).__name__})"
                if why:
                    out.append(f"EC2 unit {k} ({aid}): {why}")
    return out


def owns(a):
    """An attempt owns its coordinates from intent until it is rejected (no instance ever) or its output was ingested or
    dispositioned (fenced). Benchmark and duplicate work never owns."""
    return (a.get("class") in CLASSES and a.get("state") != "rejected" and a.get("ingestion") == "pending")


def status_problem(st, attempt_id, slot, rep, index, ident, mem_stop_bytes):
    """'' for a complete terminal worker status of ONE coordinate that finished it; otherwise why not (V10-4)."""
    if not isinstance(st, dict):
        return "status not an object"
    want = dict(job=attempt_id, slot=slot, rep=rep, ident=ident, indices=[index], left=[], exit=WORKER_DONE)
    for k, v in want.items():
        if st.get(k) != v or (isinstance(v, int) and not _int(st.get(k))):
            return f"status {k} {st.get(k)!r} is not {v!r}"
    if not ((st.get("new") == [index] and st.get("resumed") == []) or (st.get("new") == [] and st.get("resumed") == [index])):
        return f"status new/resumed {st.get('new')}/{st.get('resumed')} do not account for index {index} exactly once"
    for k in ("wall_s", "cpu_s", "started", "ended"):
        if not _num(st.get(k)) or st[k] < 0:
            return f"status {k} not finite and non-negative"
    if not _int(st.get("maxrss")) or not 0 < st["maxrss"] <= mem_stop_bytes:
        return f"status maxrss {st.get('maxrss')!r} not positive or above the memory stop"
    if st.get("reason") != "":
        return f"status reason {st.get('reason')!r} on a completed coordinate"
    return ""


XLA_BASE = "--xla_cpu_multi_thread_eigen=false --xla_cpu_parallel_codegen_split_count=1"


def attestation_problem(d):
    """'' for an EFFECTIVE B_full attestation (aws_ec2/attest.py on the instance): the reviewed row-23 arm-B checks, typed."""
    need = ("profile", "XLA_FLAGS", "threads", "numpy_dispatch_active", "openblas_core", "OPENBLAS_CORETYPE", "problems")
    if not isinstance(d, dict) or any(k not in d for k in need):
        return "attestation fields missing"
    if d["profile"] != "B_full" or d["problems"] != []:
        return f"attestation profile {d['profile']!r} problems {d['problems']!r}"
    th, xf, av, ob = d["threads"], d["XLA_FLAGS"], d["numpy_dispatch_active"], d["openblas_core"]
    if not (isinstance(th, dict) and sorted(th) == ["MKL_NUM_THREADS", "NPROC", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS"]
            and all(v == "1" for v in th.values())):
        return "attestation thread caps are not all 1"
    if not (isinstance(xf, str) and xf.startswith(XLA_BASE) and "--xla_cpu_max_isa=AVX2" in xf.split()):
        return "attestation XLA flags are not the B_full flags"
    if d["OPENBLAS_CORETYPE"] != "Haswell" or not (isinstance(ob, dict) and ob and all(isinstance(v, str) and "haswell" in v.lower() for v in ob.values())):
        return "attestation OpenBLAS core is not Haswell"
    if not (isinstance(av, list) and all(x in ("X86_V2", "X86_V3") for x in av)):
        return f"attestation numpy dispatch {av!r} above X86_V3"
    return ""


# The instance contracts the launcher may build (Codex V10-7): production and the predeclared qualification Q1/Q2.
CONTRACTS = {
    "production": dict(itype="c7a.24xlarge", workers=76, max_price=1.20, volume_gb=60, roles={"work": None, "sentinel": 4}),
    "Q1": dict(itype="c7a.24xlarge", workers=76, max_price=1.20, volume_gb=60, roles={"work": 48, "qual_lengau": 24, "sentinel": 4}),
    "Q2": dict(itype="c7a.12xlarge", workers=24, max_price=0.70, volume_gb=60, roles={"qual_repeat": 24}),
}
OPERATIONAL_FIELDS = ["storage.root", "storage.campaign", "pbs.cores", "shard.expect_layer_s", "shard.expect_note", "ec2_production"]
SETUP_S, UPLOAD_RESERVE_S = 900, 3000


S_ROOT = "/mnt/lustre/users/pvanrooyen/t1_toolchain/qual_S/root"
S_CAMPAIGN = "/mnt/lustre/users/pvanrooyen/t1_toolchain/qual_S/campaign"
S_RESERVED_CORE_H = 2304.0
S_FIELDS = ["storage.root", "storage.campaign", "budget.core_hours_cap", "ec2_qualification_shadow"]


def derive_isolated_S(prod, prod_sha, root=S_ROOT, campaign=S_CAMPAIGN):
    """S's isolated operational manifest: the production screen manifest with ONLY its storage (an isolated root and
    campaign) and its reservation cap (2,304 core-h, both S jobs) changed, plus a marker naming the parent. The science
    (cfg, setting, datasets, shard identities, code pins, pbs shape) is byte-identical, so the unchanged worker computes the
    frozen tasks; nothing it writes is in the screen root."""
    m = json.loads(json.dumps(prod))
    m["storage"] = {"root": root, "campaign": campaign}
    m.setdefault("budget", {})["core_hours_cap"] = S_RESERVED_CORE_H
    m["ec2_qualification_shadow"] = {"derived_from_sha256": prod_sha, "changed": S_FIELDS, "role": "S",
                                     "rule": "isolated Lengau shadow references for the EC2 qualification; never canonical"}
    return m


def isolated_S_problem(sman, prod, prod_sha):
    """'' when `sman` is exactly derive_isolated_S of the production manifest for its own root/campaign."""
    st = sman.get("storage") if isinstance(sman, dict) else None
    if not isinstance(st, dict) or not isinstance(sman.get("ec2_qualification_shadow"), dict):
        return "not the isolated S manifest"
    if st.get("root") == prod["storage"]["root"] or st.get("campaign") == prod["storage"]["campaign"]:
        return "the S manifest is not isolated from the screen root/campaign"
    if canonical(sman) != canonical(derive_isolated_S(prod, prod_sha, st.get("root"), st.get("campaign"))):
        return f"the S manifest is not the exact isolated derivation of {prod_sha[:8]}"
    return ""


def derive_operational(prod, prod_sha, epoch, expect_s, contract):
    """The EC2 operational manifest for one epoch and contract: a deep copy of the production screen manifest with ONLY the
    operational fields changed. The consumer (launcher, ingestion) re-derives it and requires byte-equal canonical JSON."""
    c = CONTRACTS[contract]
    m = json.loads(json.dumps(prod))
    m["storage"] = {"root": "/mnt/prod/root", "campaign": "/mnt/prod/campaign"}
    m["pbs"]["cores"] = int(c["workers"])
    m["shard"]["expect_layer_s"] = int(expect_s)
    m["shard"]["expect_note"] = f"EC2 {contract} epoch {int(epoch)}: first-dispatch expectation from row 23's measured paired walls"
    m["ec2_production"] = {"epoch": int(epoch), "derived_from_sha256": prod_sha, "profile": "B_full", "contract": contract,
                           "instance": dict(c, roles=dict(c["roles"])), "changed": OPERATIONAL_FIELDS,
                           "expect_s": int(expect_s), "lifetime_s": int(expect_s) + SETUP_S + UPLOAD_RESERVE_S}
    return m


def operational_problem(opman, prod, prod_sha):
    """'' when `opman` is exactly derive_operational(...) of the production manifest for its own declared parameters."""
    e = opman.get("ec2_production") if isinstance(opman, dict) else None
    if not isinstance(e, dict) or e.get("contract") not in CONTRACTS or not _int(e.get("epoch")) or not _int(e.get("expect_s")):
        return "not an EC2 operational manifest"
    want = derive_operational(prod, prod_sha, e["epoch"], e["expect_s"], e["contract"])
    if canonical(opman) != canonical(want):
        diff = sorted(k for k in set(want) | set(opman) if want.get(k) != opman.get(k))
        return f"the operational manifest is not the exact derivation of {prod_sha[:8]} (differs on {diff})"
    return ""


def plan_problem(plan, contract, attempt, partition_sha, opman_sha, activation_sha):
    """'' for an immutable attempt plan that is exactly this attempt's (Codex V10-4): bound to the partition, operational
    manifest and activation; slot numbers 0..n-1 unique with n the contract's workers; one index per slot; only the
    contract's roles with their exact counts (production: 4 sentinels, every other slot work); per-role coordinate lists equal
    to the authority's for this attempt; no coordinate twice."""
    c = CONTRACTS[contract]
    if not isinstance(plan, dict):
        return "plan not an object"
    for k, v in (("attempt_id", attempt["attempt_id"]), ("contract", contract), ("partition_sha256", partition_sha),
                 ("opmanifest_sha256", opman_sha), ("activation_sha256", activation_sha), ("sequence", attempt["sequence"])):
        if plan.get(k) != v:
            return f"plan {k} {plan.get(k)!r} is not {v!r}"
    slots = plan.get("slots")
    n_ok = (lambda n: 4 < n <= c["workers"]) if contract == "production" else (lambda n: n == c["workers"])
    if not isinstance(slots, list) or not n_ok(len(slots)):                  # production: the block may run out (<= 76)
        return f"plan has {len(slots) if isinstance(slots, list) else 'no'} slots, not the contract's {c['workers']}"
    if not all(_int(s.get("slot")) for s in slots) or sorted(s["slot"] for s in slots) != list(range(len(slots))):
        return "plan slot numbers are not exactly 0..n-1"
    by_role, seen = {}, set()
    for s in slots:
        if s.get("role") not in c["roles"] or not _int(s.get("rep")) or not (isinstance(s.get("indices"), list) and len(s["indices"]) == 1 and _int(s["indices"][0])):
            return f"slot {s.get('slot')}: role/rep/indices malformed"
        co = (s["rep"], s["indices"][0])
        if co in seen:
            return f"coordinate {co} planned twice"
        seen.add(co); by_role.setdefault(s["role"], []).append(list(co))
    for role, n in c["roles"].items():
        got = sorted(by_role.get(role, []))
        if n is not None and len(got) != n:
            return f"plan has {len(got)} {role} slots, not {n}"
    want = dict(work=attempt.get("coordinates", []), sentinel=attempt.get("sentinels", []),
                qual_lengau=attempt.get("duplicates", []), qual_repeat=attempt.get("duplicates", []))
    for role in c["roles"]:
        if sorted(by_role.get(role, [])) != sorted(want[role]):
            return f"plan {role} coordinates are not the authority's for this attempt"
    return ""
