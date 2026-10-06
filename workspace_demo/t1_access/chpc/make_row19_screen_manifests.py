"""Write the stage-2 screen's two manifests (refit and originals) and their budget-phase files from the slice, shard and bank
manifests (Codex RSC 9202e8b). The 100 fresh datasets are reps 3..102 under the slice's seed base 20261003; the script refuses
unless their resolved seeds are unique and disjoint from the slice manifest's historical exclusions, the three development
datasets' seeds and the bank's 408 seeds. Identities: `--identities FILE` takes the map the PRODUCER RUNTIME computed
(`--emit-identities` run on Lengau through t1py); without it the draft carries no identity map and cannot be admitted.

    python chpc/make_row19_screen_manifests.py --draft OUT.json                 (Mac: the draft, no identities)
    t1py chpc/make_row19_screen_manifests.py --emit-identities DRAFT.json       (Lengau: prints {rep: ident})
    python chpc/make_row19_screen_manifests.py --identities IDS.json            (Mac: the final manifests)
"""
import os, sys, json, hashlib, argparse, time
HERE = os.path.dirname(os.path.abspath(__file__)); T1 = os.path.abspath(os.path.join(HERE, ".."))
for p in (T1, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("NPROC", "1")

TC = "/mnt/lustre/users/pvanrooyen/t1_toolchain"
REPS = list(range(3, 103))
CODE = ["analyze.py", "models.py", "simulate.py", "chpc/row19_slice.py", "chpc/row19_shard.py", "chpc/row19_ledger.py", "chpc/row19_screen_orig.py"]
CONTROLS = ["chpc/row19_screen_admit.py", "chpc/row19_screen_verify.py", "chpc/row19_screen_status.py", "chpc/row19_screen_release.py"]


def fsha(f):
    return hashlib.sha256(open(os.path.join(T1, f), "rb").read()).hexdigest()


def seeds(setting, base, reps):
    import simulate as S
    kw = dict(setting["grid"])
    return {int(r): int(S.dataset_seed(setting["generator"], kw, int(r), int(setting["D"]), int(base))) for r in reps}


def draft():
    sl = json.load(open(os.path.join(HERE, "row19_slice_manifest.json")))
    bank_rel = "chpc/row22_bank_manifest.json"; bank = json.load(open(os.path.join(T1, bank_rel)))
    for f in ("analyze.py", "models.py", "simulate.py"):
        assert fsha(f) == sl["code"]["files"][f] == bank["code"]["files"][f], f"{f}: not the slice's and bank's pin"
    sd = seeds(sl["setting"], sl["datasets"]["seed_base"], REPS)
    bs = seeds(bank["setting"], bank["datasets"]["seed_base"], bank["datasets"]["reps"])
    dev = {int(v) for v in sl["datasets"]["resolved_seeds"].values()}
    hist = {int(x) for x in sl["datasets"]["excluded_resolved_seeds"]}
    assert len(set(sd.values())) == len(sd) == 100, "screen seeds are not 100 distinct"
    assert not set(sd.values()) & hist, "a screen seed is historical"
    assert not set(sd.values()) & dev, "a screen seed is a development dataset's"
    assert not set(sd.values()) & set(bs.values()), "a screen seed is a bank seed"
    excl = sorted(hist | dev | set(bs.values()))
    sha = hashlib.sha256(json.dumps([[r, s] for r, s in sorted(sd.items())]).encode()).hexdigest()
    shard_rel = "chpc/row19_shard_manifest.json"
    common = {
        "row": 19, "stage": "2-screen", "declared": "2026-10-06",
        "setting": sl["setting"],
        "datasets": {"seed_base": int(sl["datasets"]["seed_base"]), "reps": REPS, "n_attempted": 100, "resolved_seeds_sha256": sha,
                     "excluded_resolved_seeds": excl,
                     "exclusion_rule": "every historical M2S omega 1/2 identity (the slice manifest's set), the three disclosed development "
                                       "datasets (reps 0-2, excluded from the screen by row 19) and the 408 bank seeds",
                     "bank_manifest": bank_rel, "bank_manifest_sha256": fsha(bank_rel), "identities": None},
        "cfg": sl["cfg"],
        "code": {"files": {f: fsha(f) for f in CODE}},
        "controls": {f: fsha(f) for f in CONTROLS},
        "environment": sl["environment"],
        "anchors": {"reps": [0, 1, 2], "shard_manifest": shard_rel, "shard_manifest_sha256": fsha(shard_rel),
                    "sequential_root": sl["storage"]["root"], "required_overlap": {"0": [0], "1": [0], "2": [0]},
                    "rule": "external mechanical parity anchors only: validated under their own shard manifest; at the required index and at "
                            "every other index the shard root and the sequential chain both hold, the canonical scientific payload must agree "
                            "to the float bit; all three required; nothing of theirs enters the screen"},
        "funding": {"programme": "CSCI1913", "allocation_core_h": 100000.0, "other_settled_core_h": 6.0,
                    "other_note": "rows 18 (113 min) and 6 (3.6 core-h) settled outside the campaign ledgers",
                    "campaigns": [f"{TC}/row19_campaign", f"{TC}/row19_shard_campaign", f"{TC}/row22_bank_campaign",
                                  f"{TC}/row19_screen_campaign", f"{TC}/row19_screen_orig_campaign"]},
        "release": {"primary": "selection/ws", "rule": "PREREG 10.1: one look; K_max over the whole frozen T, inclusive; exact one-sided 97.5 % "
                                                       "upper bound at the actual usable n; 83 of 100 only at n = 100; non-stop = not ruled out"},
    }
    refit = dict(common, role="refit",
                 purpose="row 19 stage 2: the declared B = 200 resample indices of 100 fresh datasets, packed one index per worker, "
                         "by the unchanged row19_shard.py worker",
                 shard={"toolchain": TC, "clone": f"{TC}/rsc_screen", "per_slot": 1, "expect_layer_s": 90000, "deadline_margin": 1.25,
                        "identities": None,
                        "expect_note": "the first dispatch needs max(90,000 s, 1.25 x 0): 90,000 s is above the development pilot's longest packed "
                                       "resample (88,740 s, rep 2) - a defensible first expectation, not a measurement on fresh datasets"},
                 pbs={"project": "CSCI1913", "queue": "serial", "cores": 24, "walltime_h": 30, "nodetype": "haswell_reg", "mem_gb": 120,
                      "mem_stop_gib": 4.5, "deadline_reserve_s": 1800},
                 storage={"root": f"{TC}/row19_screen", "campaign": f"{TC}/row19_screen_campaign"},
                 budget={"core_hours_cap": None, "admission": "chpc/row19_screen_budget.json",
                         "rule": "null here so no binding names a cap; the live cap and its raise history live in the campaign ledger"})
    orig = dict(common, role="orig",
                purpose="row 19 stage 2: the 100 lossless original fits, one per worker, by row19_screen_orig.py",
                shard={"toolchain": TC, "clone": f"{TC}/rsc_screen", "per_slot": 1, "identities": None},
                originals={"expect_original_s": 90000, "deadline_margin": 1.25},
                pbs={"project": "CSCI1913", "queue": "serial", "cores": 20, "walltime_h": 30, "nodetype": "haswell_reg", "mem_gb": 120,
                     "mem_stop_gib": 4.5, "deadline_reserve_s": 1800, "cores_note": "20 workers a job: 100 originals = 5 full jobs"},
                storage={"root": f"{TC}/row19_screen_orig", "campaign": f"{TC}/row19_screen_orig_campaign"},
                budget={"core_hours_cap": None, "admission": "chpc/row19_screen_orig_budget.json",
                        "rule": "null here; the live cap and its raise history live in the campaign ledger"})
    return refit, orig


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", default=None); ap.add_argument("--emit-identities", default=None); ap.add_argument("--identities", default=None)
    a = ap.parse_args(argv)
    if a.emit_identities:
        sys.path[:0] = [os.getcwd(), os.path.join(os.getcwd(), "chpc")]   # run from the clone's t1_access on Lengau
        import row19_shard as SH
        man = json.load(open(a.emit_identities))
        print(json.dumps({str(r): SH.task(man, r)["ident"] for r in man["datasets"]["reps"]}, sort_keys=True)); return 0
    refit, orig = draft()
    if a.draft:
        json.dump(refit, open(a.draft, "w"), indent=1); print(f"draft written to {a.draft}"); return 0
    ids = json.load(open(a.identities))
    assert sorted(int(k) for k in ids) == REPS and all(isinstance(v, str) and len(v) == 64 for v in ids.values()), "identity map incomplete"
    for m in (refit, orig):
        m["datasets"]["identities"] = ids; m["shard"]["identities"] = ids
    json.dump(refit, open(os.path.join(HERE, "row19_screen_manifest.json"), "w"), indent=1)
    json.dump(orig, open(os.path.join(HERE, "row19_screen_orig_manifest.json"), "w"), indent=1)
    for name, cap, note in (("row19_screen_budget.json", 60000.0, "the initial admission envelope of the screen's refit campaign"),
                            ("row19_screen_orig_budget.json", 3000.0, "5 jobs x 20 cores x 30 h")):
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            json.dump({"phases": [dict(cap_core_h=cap, note=f"{note} (owner 6 Oct 2026: stage 2 as designed; caps are raised, the allocation is the hard stop)",
                                       t=time.time())]}, open(p, "w"), indent=1)
    print("manifests and budget files written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
