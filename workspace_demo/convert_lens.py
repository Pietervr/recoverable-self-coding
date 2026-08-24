"""Convert the Neuronpedia n=1000 J-lens (.pt, torch) to the jlens-qwen36 NPZ
schema, per upstream/jlens-qwen36/docs/lenses.md. Output lands at the path the
port's CLAUDE.md mandates: data/lens/qwen36_27b_neuronpedia_n1000.npz.

Run (torch needed only here):
    uv run --directory upstream/jlens-qwen36 --with torch python ../../convert_lens.py
"""

import json
import pathlib

import numpy as np
import torch

PORT = pathlib.Path(
    "/Users/pietervanrooyen/Recoverable-Self-Coding/workspace_demo/upstream/jlens-qwen36"
)
PT = (
    PORT
    / "data/lens/hf/qwen3.6-27b/jlens/Salesforce-wikitext/Qwen3.6-27B_jacobian_lens_n1000.pt"
)
NPZ = PORT / "data/lens/qwen36_27b_neuronpedia_n1000.npz"
META = PORT / "data/lens/qwen36_27b_neuronpedia_n1000.json"

d = torch.load(PT, map_location="cpu", weights_only=False)
out = {f"J_{l}": J.to(torch.float16).numpy() for l, J in d["J"].items()}
out.update(n_prompts=d["n_prompts"], d_model=d["d_model"])
np.savez(NPZ, **out)
json.dump(
    {
        "n_prompts": int(d["n_prompts"]),
        "d_model": int(d["d_model"]),
        "source_layers": sorted(int(k) for k in d["J"]),
    },
    open(META, "w"),
    indent=1,
)
print("wrote", NPZ, NPZ.stat().st_size, "bytes")
print("layers:", len(d["J"]), "n_prompts:", d["n_prompts"], "d_model:", d["d_model"])
