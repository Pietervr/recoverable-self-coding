# Power-stage second opinion — Codex working record

Status: IN PROGRESS, 16 September 2026. No final verdict or substantive reply sent.
Request: `2026-09-16_power_stage_codex_brief.md`, RSC `26f34d8`, six questions.
This checkpoint preserves completed checks at measured 85.4% context usage.
No fitting, response simulation, job interruption, launch, protocol edit or push.

## Verified implementation and provenance

Read `simulate.py` (all 1,025 lines), `analyze.py` (all 668 lines),
`probe_refit.py` (all 73 lines), the entire request, and preregistration
sections 7–9 plus section 10 through line 460. Remaining reading is listed below.

Source snapshot: RSC HEAD `26f34d8`; SHA256:

- `simulate.py`: `0832d490f6b2f10749f53f6f5ea69c2079acb240fbf0dce7f1dba7b2f89ab3fb`
- `analyze.py`: `c49c8f744c1dae0cca59fdebe0c6f7134027d6555bb11eb69dcb1ed8c455d219`
- `probe_refit.py`: `84db00f684cf7382bbc19a1d245b026f5e1055c85c7dada190f400b46654281c`

The brief's Q6 chronology is incorrect. `gain_gate` was introduced/enforced in
RSC `4677e41` (11 September 2026, 17:49 PDT). The named local artifact was
committed in `3ca9304` (13 September 2026, 08:04 PDT), produced under `9b277df`,
code/config hash `d77c3ecc161e`. The legacy ungated cloud file is a different
artifact. Preregistration §10 explicitly assigns the recomputed-check route to
the earlier d4v12b job output.

Named local file: `sim_results/gain_local_9b277df/gain_calibration_D4.json`;
3,477,642 bytes; SHA256
`38a67e1c8caa76c4bdefbc0e22a59b62678ef3d8e902e53b0b88ee6d3e0a8697`.
Metadata: D=4, seed 2026, calibration 32 concepts per family, independent check
64 per family at seed 3026; check relative-SE gate .20 and relative agreement .25.
The actual pure reader/gate functions extracted from current `simulate.py`
accept all twelve pairs with no problems. All entries carry calibration and
check convergence/reproduction flags; none has a failure note. No numerical
revalidation was executed. The companion script records exactly what ran:
AST-extracted functions with a scalar finite-check substitute, without importing
the numerical pipeline. This establishes the stored-entry gate result, not a
new independent reproduction of the numerical calibration.

`power_points(file)` returns twelve alternatives. `power_points(file,
targets=[.01])` returns exactly M3, M3H(tau=.5), M3V, M3L(pi0=.05), with scales
0.7048470316951376, 0.5359075609613234, 0.6267476817856267,
0.7187787541376713. `accepted_gain_artefact` accepts this raw D4 file under its
own stored hash. Run compatibility with a future numerical configuration still
requires an explicit provenance/reuse decision; no future dispatch is approved.

Implementation facts relevant to Q2–Q4:

- `expected_gain` measures the generating-density versus a best-found graded
  reference fitted at 256 concepts; the independent check uses 512. It is not
  the finite-design selected-X minus selected-G procedure's expectation. The
  preregistration says this explicitly. A nominal positive gain need not yield
  positive finite-design mean scores or high detection probability.
- `decide` is positive lower endpoint -> mixture, negative upper endpoint ->
  graded, otherwise inconclusive; unavailable intervals are separate failures.
  A simulation can measure this rule's actual operating characteristics without
  certifying the interval's nominal coverage. This distinction needs a complete
  final discussion, including the null boundary and finite generator scope.
- The local CLI defaults to five layers (25,33,41,49,57), eight inner starts,
  all twelve gain points and chunks of 32. d4v12b used one layer 41 and four
  inner starts. There is no target-only CLI argument: target selection exists
  in the Python API. The proposed 200-dataset run is not the default CLI task.
- The local CLI calls `power_points` without the stronger top-level
  `accepted_gain_artefact` D/hash checks. It also creates no refit checkpoint
  directory, unlike `probe_refit.py`. Any future runner must make these
  configuration/provenance choices concrete before a benchmark/launch.
- `fit_seconds` is the sum of elapsed fitter times, not a hardware-independent
  core-cost benchmark. The preregistration contrasts a historical 900 s Mac
  layer with roughly 83 min on a loaded cloud vCPU. The brief's 6,188-second
  cloud average cannot establish a 31-hour Mac schedule, especially on new
  mixture generators. Actual first-replicate benchmarking remains required.
- All three predictors are saved from the same fits: primary selection,
  ensemble and inherited pair. Their mixture-generator operating characteristics
  can be compared without another density-fitting run.
- With refit intervals, the companion cluster interval is retained on the same
  datasets. Refitting is substantial additional work: B full sequential
  pipelines per dataset with this runner, not a second cheap interval formula.
- The probe checkpoints completed resamples, while `run_points` writes complete
  datasets only after a worker chunk returns. Restart reruns the original
  dataset fit before loading bootstrap checkpoints; unfinished work may be
  lost. The claim that a kill/restart resumes without any loss is too strong.
  Suspension is a distinct operation. No pause/stop was performed.

## Provisional reasoning to finish, not a delivered verdict

Q1: empirical false calls on the twelve declared graded settings remain useful;
they do not establish sensitivity or a calibrated assay/predictor in general.
The new narrower claim may be publishable as an audit without another run;
assess the actual current manuscript before recommending that more work is
necessary. A finite generative label and the expected-score null differ.

Q2: a matched historical-cluster power study can characterize the historical
rule. Neither apparent power nor poor reference inclusion alone proves a
valid/invalid binary operating characteristic at the zero boundary. Do not
infer that the observed .216 is simply interval narrowness, or that it certifies
known-target coverage. A replacement interval would be another procedure with
its own null and alternative validation. No obligation to run both merely to
answer the historical question; paired refit development is a separate scope.

Q3/Q5: R=50 per generator gives MCSE about .057 at p=.8, not precise certification
of p>=.8. Report each alternative and all four outcome counts; an equal-weight
pool is a declared average, never an every-alternative guarantee. Compute exact
binomial intervals and precision implications before final wording. A single
gain target supports only that point; a power curve needs multiple targets and
monotonicity is not automatic for different fitted generators. The R=50 proposal
is not the preregistration's 1,000-per-setting full stage.

Q4: do not endorse pausing the probe on the unchecked 31-hour estimate. Decide
the paper's claim first, then artifact/configuration checks, a benchmark and a
bounded costed scope. Preserve current jobs and all owner/ledger gates. Scope
and whether any new SI run is needed remain under consideration.

## Remaining work

1. Finish preregistration §10 (461–581) and pertinent budget/freeze sections.
2. Read the simulation-design document through its current ledger. A previous
   combined output of lines 1–105 was truncated after part of §6; §§1–5 were
   read, §6 onward needs complete reading. Strategy top 1–100 was also partly
   lost in that combined output and needs a complete read.
3. Read current manuscript claim/methods/results/discussion/transfer sections;
   Claude is actively editing them. Pin the reviewed baseline/hashes and avoid
   taking any manuscript ownership. Latest known committed change at start was
   Unimog `3fe024a3`; discussion/transfer were dirty, owned by Claude.
4. Verify the saved timing summary/provenance and gain history against the named
   artifacts as needed, without repeating the closed 12,000-row science audit.
   Inspect numerical source changes if needed to state cross-snapshot scope.
5. Consult primary methodological sources (not yet browsed for this request),
   calculate exact Monte-Carlo uncertainty and complete final Q1–Q6 advice.
6. Commit the final record/evidence; one substantive reply to current Claude
   Entropy SI; verify complete unchanged native Read receipt and log closure.

Wrap refresh at approximately 12:53 PDT: Unimog HEAD is now `42de4d12`, with
no tracked manuscript edits outstanding. Claude's native `9c0d76b5` transcript
reports a freeze through §2.5 and a separate AI-side pilot ledger row 16;
power row 15 still awaits this review. Those are not Codex launch approvals or
an expansion of the six-question request. Read the current owner/Claude exchange
before finalizing advice. The Mac probe remains live as PID 8012, PPID 1,
PGID 8010, with caffeinate 8014, independently of Codex PID 83876. No process
has been paused or changed. Compaction occurred while saving this checkpoint;
the shared lifecycle now requires the automatic wrap at this safe boundary.

Ownership unchanged: Codex review/evidence/reply/receipt and R052 log append;
Claude manuscript/protocol/dispatch/front matter; R084 instruments. No AWS,
launch, spend, pause, protocol amendment, freeze, submission or publication
authorized by this review. Prior c4abb4f and 226024e deliveries remain closed.
