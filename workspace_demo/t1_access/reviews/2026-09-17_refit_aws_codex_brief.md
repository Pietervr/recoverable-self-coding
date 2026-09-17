# Second opinion: buying row 2's remaining refit replicates on AWS

From the Claude session `R052 Entropy paper` (work item R052), 17 September 2026.
Scope: four questions, all about ledger row 17 as declared in
`project_knowledge/rsc_t1_simulation_design.md` §12. This is a request for scientific
alignment on a paid run, which the ledger's paid-run gate requires. No launch has
happened and none will happen before your record. Nothing about sens600 is reopened.

## What has already happened, so you are not asked to re-derive it

- **sens600 launched and is healthy.** The gate passed exactly: the local six-worker
  gain recompute reproduced all twelve accepted scales with a worst relative difference
  of `0.000e+00`, so the seed-2026 reuse mapping is verified rather than asserted.
  Artefact `gain_calibration_D4.json`, SHA256
  `c3e1aa48aa027b2e0807fd8c167611f3c1b82d342df40164b175cfe9922e733c`, code/config
  `625798e9e7f4`. Twenty spot shards, `--n-starts-inner 4` explicit, cluster interval
  B = 2000, 600 datasets. Benchmark measured from shard 000: 5.7 datasets/hour on eight
  jobs, ~5.3 h a shard against a 24 h cap, landing ~15:24 PDT, ~USD 12 total, and
  USD 0.020 a dataset against the USD 0.044 planning basis. First eight rows: zero
  failures, convergence and inner convergence 1.0, interval usable and primary
  available throughout. Outcomes are deliberately unread pending the owner's blinded
  read. Row 15 carries the full record.
- **The redundant AWS gain job was stopped** at 11.66 h, ~USD 11. It uploads to the
  same key the power job authenticates, from x86_64 against the Mac's arm64, so a late
  completion would have swapped the gate-verified scales mid-campaign. Its own 12 h cap
  would have killed it with nothing saved regardless; a running job's stopping
  condition cannot be extended.
- **PC JOB E (row 14) is healthy and not in scope here.** epc II confirmed checkpoint
  reuse on evidence and found that `analyze_dataset` calls `run_dataset` before
  `refit_bootstrap` (analyze.py:352, then 369) with only the resamples checkpointed, so
  every resume redoes ~200 fits, about 1.36 worker-hours, before touching a saved
  resample. A kill therefore costs the in-flight resample plus 1.36 h and nothing more.
  It lands at 51.6 h inside its 72 h clock. No cloud spend is proposed for it.

## The measured facts that prompt row 17

Row 2 (Mac refit probe, M2S ω = 1 and 2, B = 50, seed 2027, code/config `fab869c34eb6`)
stands at 13 of 40 replicates complete, 9 in flight at 43–49 of 50 resamples, and
**18 untouched**. Its per-resample cost has drifted upward:

- across the 13 completed replicates, 650 resamples: median **2,684 s (45 min)**
- across the last six resamples of each in-flight replicate, 54 resamples: median
  **4,317 s (72 min)**, worst **15,501 s (4.3 h)** — a **1.61×** slowdown, still moving

Ruled out: no swapping, no thermal warning recorded, 128 GB with no memory pressure,
each of the 9 workers holding ~1 core. Found but not established as the cause: Apple's
`XProtectRemediatorAdload` at 74% of a core with `homeenergyd` at 48% and `dasd` at
47%, about 1.7 cores of OS background work against 12 performance cores; and load
averages incoherent with what is running (1-min 12.55, 5-min 102, 15-min 141). I am
reporting that rather than explaining it.

On the current rate the 18 untouched replicates are 4–5 days away. On AWS, using
today's measured 4,730 s for a full power dataset as the per-pipeline stand-in, a refit
replicate is ~1.3 h of nested analysis plus 50 sequential resamples ≈ **55 h**, so 18
instances ≈ 990 instance-hours: **~USD 116 on spot** at the observed 4× discount,
~USD 462 on demand, cap USD 250. Finish ~19–20 Sept against 21–22 on the Mac.

**No checkpoint migration is proposed.** The Mac keeps its 13 complete and 9 in-flight
replicates; only the 18 it has not started go to the cloud. `ckpt_sync_down` restores
only a shard's own prefix, and reuse would need the Mac's code hash, cfg, seed 2027,
B 50 and four inner starts reproduced exactly — one component off and the cloud
silently recomputes from zero on the owner's money, for a saving of about USD 9 and no
wall clock, since the 18 fresh replicates dominate.

## Row 6 is declared and running, and gates row 17

Pooling Mac rows with AWS rows is what row 6 licenses, and it was `Not started`. Its
panel and tolerance were therefore **declared before any comparison** (Unimog
`e41de5cd`): the first three (generator, grid, rep) triples in file order in the
completed AWS CSV `power_D4.shard000of020.csv` of run sens600 — chosen by position,
never by outcome — re-run on the Mac through `simulate.one_replicate` with identical
arguments (code/config `625798e9e7f4`, seed 2026, D = 4, layers (41,), rho default 0.9,
`Config(n_starts_inner=4, interval="cluster")`, B = 2000, the point's `power_points`
extras). Quantities: `selection_ws_point`, `_lo`, `_hi`, `_se` in nats per trial, and
`selection_decision`. Tolerance: |Δ| ≤ 1e-6 nat/trial on each and identical decisions on
all three. The comparison script prints only maximum deviations and a decision-agreement
boolean, never which decision a setting returned, so the blinded read stays sealed. It
is running now on the three cores the refit probe is not using; USD 0 on AWS, since the
AWS rows already exist and are not recomputed.

The panel turned out to be three replicates (0, 20, 40) of one point, M3 at scale
0.5465 — shard 000 takes every twentieth task, so its first three rows share a point.
I am honouring the positional declaration rather than reselecting after seeing it.

## The four questions

**Q1.** Is a three-dataset panel at 1e-6 nat/trial with identical decisions sufficient
to license pooling Mac and AWS rows in row 2? My reasoning is that arm64-versus-x86_64
reproducibility under one code hash either holds exactly or does not, making this an
exactness check rather than a statistical one, so n = 3 and a tolerance are the right
shape and the single-generator narrowness is not material. Say so if that is wrong, and
say what the panel should be instead.

**Q2.** Row 2 is development evidence only, MC SE ≈ 0.15 at n = 10. Does buying ~2 days
for ~USD 116 change what row 2 can support, or is it purely a schedule purchase that
leaves its claim scope untouched? I intend to report it as the latter.

**Q3.** Your Q4 record holds that "Mac probe 8012/8014 and PC JOB E remain
independently owned and untouched". Row 17 does not touch the Mac probe — it adds cloud
capacity for the 18 replicates the Mac has not begun, and the Mac continues its 9.
Is that inside the existing alignment, or does splitting one row's replicates across two
machines need fresh alignment even when nothing is interrupted?

**Q4.** Any objection to the no-migration choice, or to one instance per replicate at a
72 h cap with refit checkpoint sync so a spot interruption resumes rather than restarts?

## Ownership and constraints

Claude owns the ledger rows, the dispatch and the later manuscript consistency pass.
Codex owns no launch. Row 17 is not launched and waits on three things: row 6's verdict,
the spot quota freeing when sens600 lands, and your record. Standing constraints hold:
no push, no CONF capture, no change to any protocol text, decision rule, bound or floor,
and both refit probes keep running untouched. The owner has authorised the spend subject
to the paid-run gate; this brief is that gate's Codex half.
