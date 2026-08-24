# workspace_demo — RSC × global-workspace open-weight demo

Tests three predictions of the RSC collapse paper
([arXiv:2606.24861](https://arxiv.org/abs/2606.24861)) through the Jacobian-lens
instrument of Gurnee et al.
([arXiv:2607.15495](https://arxiv.org/abs/2607.15495)) on an open-weight model,
locally:

- **E1** — workspace occupancy saturation; SR (uncertified:certified
  commitments) rises before accuracy falls.
- **E2** — hysteresis under feedback closure: load ramp-up → collapse →
  ramp-down at α=1 (model output re-enters context) vs α=0
  (context-length-matched control), plus the reset arm
  (clear context, keep weights: *reset restores only what is archived*).
- **E3** — the workspace signature of collapse: determinant absence at
  commitment time; ignition sharpness β̂
  ([arXiv:2608.05160](https://arxiv.org/abs/2608.05160)) on both branches.

Design doc (operationalization table, controls, falsification stance,
execution plan P0–P4): `rsc_gwt_demo_design.md` in the Unimog-Projects
`project_knowledge/` (private); it will be mirrored here when the demo is
published.

## Rig

- **Model:** Qwen3.6-27B, 4-bit MLX (Apple Silicon; auto-downloads ~15 GB).
- **Lens:** Neuronpedia n=1000 pre-fitted J-lens for Qwen3.6-27B
  (`huggingface.co/neuronpedia/jacobian-lens`; conversion recipe in
  `upstream/jlens-qwen36/docs/lenses.md`).
- **Runtime + interventions:** [`WeZZard/jlens-qwen36`](https://github.com/WeZZard/jlens-qwen36)
  (Apache-2.0) — J-lens serve/visualize on MLX with a read/write workspace
  intervention engine (used to causally validate the certification classifier).
- **Reference implementation + task materials:**
  [`anthropics/jacobian-lens`](https://github.com/anthropics/jacobian-lens)
  (Apache-2.0) — its `data/experiments/` (capacity, dual-task, ignition,
  probe-swap, selectivity) and `data/evaluations/` (multihop, association,
  order-ops) seed the task battery.

`upstream/` holds shallow clones of the two repos above and is **gitignored**
(their code is not vendored; clone them via `setup_upstream.sh`).

## Status

P0 (rig bring-up) in progress — see the design doc's §7 execution plan.
