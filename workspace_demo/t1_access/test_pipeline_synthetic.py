"""End-to-end synthetic test of decode_cal.py and validate_pilot.py on fabricated capture runs (no model, no stimuli).

The runs use capture.py's storage format (run_header.json, trials.jsonl, res/answer_logits/variant_logits shards)
with 3 layers and 32 dimensions; the residual carries a k-proportional signal and the target logit rises with k.
Outputs under decoders/, validation/ and captures/ are removed afterwards.

    workspace_demo/t1_access/.venv-decode/bin/python -m pytest workspace_demo/t1_access/test_pipeline_synthetic.py -q
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PY = sys.executable
L, D, SHARD = 3, 32, 1000
LEVELS = [0, 1, 2, 3, 4, 6, 8]


def float32_to_bf16_bits(x: np.ndarray) -> np.ndarray:
    return (x.astype(np.float32).view(np.uint32) >> np.uint32(16)).astype(np.uint16)


def make_run(name: str, split: str, conds, levels, seed: int) -> Path:
    bank = json.loads((HERE / "stimuli" / "concepts.json").read_text())
    answer_ids = sorted(c["token_id"] for c in bank["concepts"])
    variant_ids = sorted({v["ids"][0] for c in bank["concepts"] for v in c["variants"].values()
                          if v["single_token"]} - set(answer_ids))
    concepts = sorted(c["id"] for c in bank["concepts"] if c["role"] == split)
    token_of = {c["id"]: c["token_id"] for c in bank["concepts"]}
    rng = np.random.default_rng(seed)
    direction = np.random.default_rng(0).normal(size=(L, D))  # one signal direction shared by CAL and PILOT
    out = HERE / "captures" / name
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    trials = [(c, cond, car, d, k) for c in concepts for cond in conds for car in range(6) for d in range(4)
              for k in levels]
    n = len(trials)
    res = np.zeros((SHARD, L, D), np.uint16)
    alog = np.zeros((SHARD, len(answer_ids)), np.float32)
    vlog = np.zeros((SHARD, len(variant_ids)), np.float32)
    shards, lines = {}, []
    for i, (c, cond, car, d, k) in enumerate(trials):
        s, j = divmod(i, SHARD)
        if s not in shards:
            shards[s] = (np.zeros((SHARD, L, D), np.uint16), np.zeros((SHARD, len(answer_ids)), np.float32),
                         np.zeros((SHARD, len(variant_ids)), np.float32))
        r, a, v = shards[s]
        r[j] = float32_to_bf16_bits(rng.normal(size=(L, D)) + 2.0 * (k / 8) * direction)
        a[j] = rng.normal(size=len(answer_ids))
        a[j, answer_ids.index(token_of[c])] += 1.2 * k
        v[j] = rng.normal(size=len(variant_ids))
        lines.append(json.dumps({"trial_id": f"{split}|primary|{cond}|{c}|c{car}|d{d}|k{k}", "shard": s, "index": j,
                                 "logsumexp": 20.0, "residuals_sha256": "synthetic"}))
    for s, (r, a, v) in shards.items():
        np.save(out / f"res_{s:05d}.npy", r)
        np.save(out / f"answer_logits_{s:05d}.npy", a)
        np.save(out / f"variant_logits_{s:05d}.npy", v)
    (out / "trials.jsonl").write_text("\n".join(lines) + "\n")
    (out / "run_header.json").write_text(json.dumps({
        "identity": {"answer_ids": answer_ids, "variant_ids": variant_ids, "synthetic": True},
        "provenance": {"server": {"n_layers": L, "d_model": D}}}))
    assert n == len(lines)
    return out


def test_decode_then_validate():
    cal, pilot = "test_synth_cal", "test_synth_pilot"
    try:
        make_run(cal, "CAL", ["active"], [0, 8], seed=1)
        make_run(pilot, "PILOT", ["active", "noreport"], LEVELS, seed=2)
        r = subprocess.run([PY, str(HERE / "decode_cal.py"), "--run", cal, "--n-jobs", "2"],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        summary = json.loads((HERE / "decoders" / cal / "decode_cal.json").read_text())
        assert summary["counts"] == {"0": 384, "8": 384} and len(summary["layers"]) == L
        r = subprocess.run([PY, str(HERE / "validate_pilot.py"), "--decoders", cal, "--run", pilot],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        rep = json.loads((HERE / "validation" / pilot / "report.json").read_text())
        assert rep["n_trials"] == 16 * 2 * 6 * 4 * 7
        assert min(rep["accuracy_k8_vs_k0"]["active"]) > 0.9
        rates = [rep["r3_closed_set_by_level"][str(k)]["closed_correct_rate"] for k in LEVELS]
        assert rates[0] < 0.1 and rates[-1] > 0.99 and rates == sorted(rates)
        scores = np.load(HERE / "validation" / pilot / "scores.npz")
        assert scores["z"].shape == (rep["n_trials"], L)
        assert (HERE / "validation" / pilot / "pilot_validation.png").stat().st_size > 10000
    finally:
        for p in (HERE / "captures" / cal, HERE / "captures" / pilot, HERE / "decoders" / cal,
                  HERE / "validation" / pilot):
            shutil.rmtree(p, ignore_errors=True)
