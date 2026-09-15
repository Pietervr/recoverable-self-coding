# T1 cost-reduction memo — finishing the model-side validation without cloud money

15 September 2026, Claude Entropy SI (R052), for Codex's second opinion. Proposal only: nothing here launches a job,
changes the pre-registration or adopts a procedure.

## 0. The rule

The owner, 15 Sept ~16:10Z: *"there is no way to ever spend $90k or more on these simulations - we need to find another
way."*

The standing AWS cap stays: USD 3,000 of further spend from 12 Sept, costed, with the owner's go and Codex on board. About
USD 70–130 of it is used. That is an estimate from billed hours: the omega-2 bank on spot, plus the M2B refit control that
is still finishing. No plan may depend on the refitting-bootstrap validation at the reviewed counts, or on an expensive
start recipe, without a cheaper design.

## 1. Where the cost comes from

The recorded projections are the 12 Sept on-demand estimates (R052 log, 12 Sept 21:50 UTC). They predate the later code
changes and have not been re-benchmarked. Core-hours are converted at the measured AWS rate of USD 0.48 per Mac-core-hour
equivalent.

| Stage | Recorded USD (on-demand) | Core-hour equivalent |
|---|---|---|
| Power, recovery and five-layer pilot, D = 4, cluster interval | ≈ 3,000 | ≈ 6,250 |
| D = 8 repeat (only if D = 4 lacks power) | ≈ 4,000 | ≈ 8,330 |
| Band validation | ≈ 2,500 | ≈ 5,210 |
| Refitting bootstrap as primary on CONF | ≈ 4,500 | ≈ 9,380 |
| Refitting-bootstrap validation, R = 400 × B = 200, **per null** | ≈ 9,800 | ≈ 20,400 (6 nulls ≈ 122,500; 12 ≈ 245,000) |

On top of that, any stage run under JOB D's policy A costs 9.82 times the cold fits (Codex, RSC 016151a).

**The two multipliers are the problem: the refitting bootstrap and the start policy.** The cluster-interval stages
themselves are modest.

## 2. Measured unit rates and free capacity

**Unit rates**
- **d4v12b calibration row:** USD 0.16 per row, about 0.33 core-hours on AWS.
- **Refit probe on the Mac:** 545 refit resamples in about 31 h × 11 workers, so about 0.6 worker-hours per refit
  (M2S ω = 1 and 2, layer 41, under load).
- **Nested dataset on the PC, cold starts:** 5,766 worker-seconds (1.6 worker-hours) at loaded seven-worker rates.
- **The same under policy A:** 56,647 worker-seconds.

**Free capacity**
- **Mac (M4 Max):** 12 performance cores, about 8,600 core-hours a month. The probe holds 11 workers until about
  20 Sept.
- **PC:** 4 physical cores. Seven workers deliver about four processes' throughput, so about 2,900 core-hours a month.
  JOB D holds it for about 45–54 h.
- **Stellenbosch HPC1 (Rhasatsha):** 1,000 free CPU-hours per campus login, then a registration fee for unlimited CPU;
  the fee is not published on the wiki. 2,344 cores; the week queue allows up to 1,000 cores.
- **CHPC** (Accounts Policy v2.6, §2.1 and §2.3):
  - free for academic PIs and programme members (funded by the DSI);
  - a new Research Programme gets an **initial 100,000 CPU-hours** for a six-month evaluation, then six-monthly
    allocations up to 6,000,000 CPU-hours at CHPC's discretion;
  - the owner opened the PI registration page on 15 Sept.
- **Per-core speed** on HPC1 and CHPC relative to the Mac is unmeasured.

**What that means.** Every cluster-interval stage, D = 8 included (about 19,800 core-hours), fits inside CHPC's initial
allocation. So does refitting-bootstrap validation on the **two** worst nulls (about 41,000). All twelve nulls at
R = 400 × B = 200 (about 245,000) would need a regular allocation. Compute is no longer the binding constraint once CHPC
approves; wall time, portability and scientific design are.

## 3. Proposed sequence

**S0 — running now; no new spend.**
- JOB D on the PC: does policy A move the nested Delta, member choices or cluster decisions at M2S ω = 1 and 2, M2B and
  M3H?
- The refit probe on the Mac (old policy, B = 50, 40 datasets): does refitting change coverage at the worst nulls?
- The M2B refit control in Stockholm, already paid, due about 06:30Z on 16 Sept.

**S1 — stabilize before buying a costlier interval.** The coverage failures sit where fits are unstable and losses are
heavy-tailed.
- At M2S ω = 2, coverage is 0.216 and the dispersion ratio 4.20. The ω = 2 bank's mean is set by one dataset at −2,650.
- The fit audit found catastrophic M3V misses at M2S ω = 2.

Two cheap actions:
- **(a)** Read JOB D and the probe together. If added starts move Delta materially, the instability is in fitting. Adopt a
  **member-targeted** start policy priced by JOB D's measured cost (for example M3H and M3V only), not policy A wholesale.
- **(b)** Audit T1's member bounds and floors on the Mac. Melcón's graded family was found today to allow an effective SD
  ten times below the floor of its competitors (DEVPLAN_v7 rev 1 §2.4 Q4). An analogous asymmetry in T1 would be a
  procedure defect that no interval fixes.

Any change is a numerical amendment to the snapshot, with the d4v12b rows kept as the historical procedure.

**S2 — revalidate the cluster interval under the (possibly revised) procedure, least favourable first.**
- **Order:** M2S ω = 2 and 1, then M2S ω = 0.5, M2H τ = 0.5 and 2, M2K α = 1, then all twelve nulls.
- **Stopping:** checks at R = 100, 200 and 400 with predeclared boundaries. Stop a null early only on a clear failure.
  Codex's R = 400 final precision stands (Monte Carlo SE 1.5 points at 0.90), with a declared rule for estimates too
  close to call.
- **Cost:** a cold-policy row is about 0.33–1.6 worker-hours depending on the machine, so 4,800 rows is about
  1,600–7,700 core-hours. That is days on the Mac or CHPC, not money. Under a member-targeted policy it would be
  measured first.

**S3 — only if S2 still undercovers: a cheaper corrected interval, screened on the two worst nulls first.**
- **(i)** The refitting bootstrap at reduced B with sequential validation, on free compute.
- **(ii)** A repeated-split variance with the Nadeau & Bengio correction. It multiplies the resampling variance by
  1/J + n_test/n_train over J repeated splits, so it costs about J nested layers per dataset. It was derived for resampled
  train/test splits; whether it holds under nested selection, concept strata and heavy tails is unknown and would be
  screened.

**Excluded as a cost saver: nested cross-validation** (Bates, Hastie & Tibshirani, arXiv 2104.00673).
- Algorithm 1 fits K² models per repetition. The experiments use 200 repetitions, "about 1000 times more model fits" than
  standard CV (§5 and §7).
- It assumes i.i.d. data and names dependent data as future work.
- Around T1's nested pipeline it costs about R·K nested layers per dataset (1,000 at K = 5, R = 200), more than
  B = 200 refits.
- This corrects my 15 Sept statement to the owner that it adds "a small number of extra passes".

**Also excluded:** warm-starting bootstrap refits from the original solution. It changes the resampled procedure and
suppresses the start-to-start variability the interval must capture. Only speed-ups with exact numerical parity (for
example batched starts in JAX) are candidates, benchmarked on the Mac.

**S4 — the remaining stages on free compute.** Power, recovery and the five-layer pilot run at D = 4; D = 8 only if
power fails; the band validation after the pilot. The Mac, the PC and CHPC do the work. AWS is used only for a
time-critical piece within the cap, costed and with the owner's go.

**Engineering, owned by Claude:**
- job scripts for the CHPC and HPC1 batch schedulers
- a pinned Python environment (jax 0.11.1 and the rest)
- checkpoint and resume, which already exist
- results synced off the Lustre scratch, which deletes files after 90 days

## 4. Questions for Codex

1. **Protocol.** The pre-registration's permitted calibration revisions are the bootstrap type, the family predictor and
   the band summary. Is "stabilize the fitter (S1), then revalidate the cluster interval (S2)" legitimate as a
   numerical-correctness amendment (§7.4) followed by a fresh calibration? Or does the recorded coverage failure bind the
   study to the refitting replacement whatever S1 finds?
2. **Sequential validation.** What stopping boundaries and final counts would you accept for S2, given the heavy tail at
   ω = 2, where one dataset sets the target?
3. **Fallbacks.** Are S3 (i) and (ii) defensible to screen? Is there a cheaper corrected interval you would prefer? Do you
   agree nested CV is excluded on cost and on its i.i.d. assumption?
4. **Machines.** Rows from the Mac (arm64), the PC and CHPC (x86) would enter one validation. What parity check, if any,
   must precede pooling: exact numerical parity per architecture, or a declared tolerance on the per-dataset outcome?
5. **Your line.** What in this sequence would make you not on board?

## Sources

- Owner rule and cost projections: R052 log (12 Sept 21:50 UTC; 15 Sept ~16:10Z); `rsc_t1_simulation_design.md` §5, §6, §11.
- JOB D record and dispositions: RSC 016151a, b1885a5.
- Melcón SD-floor asymmetry: `melcon_port/DEVPLAN_v7.md` rev 1 (RSC 9cbcc0a).
- S. Bates, T. Hastie, R. Tibshirani, *Cross-validation: what does it estimate and how well does it do it?*, arXiv
  2104.00673 v4 (2022), Algorithm 1 and §5–§7: https://arxiv.org/abs/2104.00673
- C. Nadeau, Y. Bengio, *Inference for the Generalization Error*, Machine Learning 52, 239–281 (2003):
  https://link.springer.com/article/10.1023/A:1024068626366; the correction as implemented in correctR:
  https://cran.r-project.org/web/packages/correctR/vignettes/correctR.html
- CHPC Accounts Policy v2.6 (4 March 2022): https://wiki.chpc.ac.za/_media/chpc:chpc_accounts_policy_v2.6.pdf;
  registration: https://users.chpc.ac.za/create/register_user/
- Stellenbosch HPC1/HPC2 wiki: https://www0.sun.ac.za/hpc/index.php?title=Main_Page
