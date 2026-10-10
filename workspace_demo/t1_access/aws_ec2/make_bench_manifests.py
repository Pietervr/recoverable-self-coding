"""Ledger row 23 (revision 2): derive the BENCHMARK-ONLY operational manifests and plans from the production screen
manifest, without editing it. Only operational fields change; every scientific field (setting, datasets, seeds,
identities, cfg incl. B = 200, code pins, environment pins, anchors) is copied byte-for-value.

    python3 make_bench_manifests.py            # writes bench/manifest_{A,B}.json, bench/plan.json, bench/SHA256SUMS

Changes, per arm X in {A, B}:
  storage.root      /mnt/bench/root_X        (an empty local root on the instance; never a Lengau root)
  storage.campaign  /mnt/bench/campaign_X    (unused: job-start runs with --no-reservation)
  pbs.cores         36                       (row19_shard.job-start refuses more slots than cores; 36 workers per arm)
  shard.expect_layer_s  68400                (19 h: the worker admits a first index only with at least this much time
                                              left before its deadline; Lengau's longest packed resample is 88,740 s and
                                              EC2 is expected faster - if it is not, the fit is censored and reported)
  bench             the derivation record (production manifest sha256, arm, what changed and why)
The production manifest's guards are not weakened: the worker, job-start and their checks run unchanged against these
files, and nothing here can be read by the Lengau controllers (different paths, never deployed to Lengau roots)."""
import hashlib, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
PROD = os.path.join(HERE, "..", "chpc", "row19_screen_manifest.json")
PROD_SHA = "43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c"
OUT = os.path.join(HERE, "bench")
REPS = list(range(3, 39))
EXPECT_S = 68400


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    assert sha(PROD) == PROD_SHA, "the production screen manifest is not the pinned 43b75f94"
    prod = json.load(open(PROD))
    assert all(r in [int(x) for x in prod["datasets"]["reps"]] for r in REPS)
    assert all(str(r) in prod["shard"]["identities"] for r in REPS)
    os.makedirs(OUT, exist_ok=True)
    for arm in ("A", "B"):
        m = json.loads(json.dumps(prod))
        m["storage"] = {"root": f"/mnt/bench/root_{arm}", "campaign": f"/mnt/bench/campaign_{arm}"}
        m["pbs"]["cores"] = len(REPS)
        m["shard"]["expect_layer_s"] = EXPECT_S
        m["shard"]["expect_note"] = ("row 23 benchmark only: 68,400 s (19 h) inside the instance's costed window; "
                                     "a longer fit is censored at the upload deadline and reported, never extended")
        m["bench"] = {"row": 23, "arm": arm, "derived_from": "chpc/row19_screen_manifest.json", "derived_from_sha256": PROD_SHA,
                      "changed": ["storage.root", "storage.campaign", "pbs.cores", "shard.expect_layer_s", "shard.expect_note", "bench"],
                      "rule": "qualification duplicates only; enters no screen root, ledger, denominator or pooling"}
        json.dump(m, open(os.path.join(OUT, f"manifest_{arm}.json"), "w"), indent=1, sort_keys=True)
    json.dump({"job": 0, "slots": [{"slot": i, "rep": r, "indices": [0]} for i, r in enumerate(REPS)]},
              open(os.path.join(OUT, "plan.json"), "w"), indent=1)
    names = ["manifest_A.json", "manifest_B.json", "plan.json"]
    with open(os.path.join(OUT, "SHA256SUMS"), "w") as f:
        for n in names:
            f.write(f"{sha(os.path.join(OUT, n))}  {n}\n")
    print(open(os.path.join(OUT, "SHA256SUMS")).read(), end="")


if __name__ == "__main__":
    main()
