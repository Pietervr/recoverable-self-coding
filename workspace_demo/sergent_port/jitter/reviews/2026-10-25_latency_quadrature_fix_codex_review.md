# Latency quadrature and fit stability — Codex science review, 25 October 2026

Scope: R052, before S3. Read against HEAD `eae6433` and working code hash `86eccfb3e15e` (concurrent edits).
Paths below are relative to `workspace_demo/sergent_port/jitter/`. Only this review was written.
No fits, AWS work, commits or launches were performed. The longest diagnostic took 36.2 seconds after imports.

1. **Q1 — The records show an optimisation/acceptance failure, not an isolated 4.3e-3 integration error.**
   In the AWS 31-node reference, m15/S4 fold 3 has these training likelihoods:
   G3+ = -10944.007517; B3+ = -10955.539364; B2 = -10944.752139.
   G selects POSITIVE; B selects REDUCED. B3+ is 11.531847 nat below its G subfamily.
   The B warm chain actually reaches -10944.007506, with projected gradient 9.49e-8,
   but its retained endpoint is NOT_CONVERGED: 12 iterations, two retries, `early=True`.
   Its note says `collapseG3+|chain UNAVAILABLE`; the much worse main chain is selected instead.
   This is direct evidence that losing a good warm endpoint changes the boundary selection.
   The five held-out B-minus-G fold sums are [0.338005, -0.000248, -0.000491, 3.090556, 0.027423] nat.
   Fold 3 alone contributes +0.003811 nat/trial of the participant's +0.004260 (811 scored trials).
   Source: `results/s2_aws/decision/W2/set_0.json:1`, participant 15, fold 3, B3+ starts/notes and G3/B3 candidates.

   This also identifies a code path: `fit.py:825` sends each warm chain through `fit_model` first;
   `fit.py:437` rejects every non-CONVERGED endpoint, so this chain never enters the generalised EM loop.
   The D4 ascent handling inside that loop (`fit.py:756`) cannot rescue it.
   The current acceptance rule correctly refuses the EARLY exception for a retained endpoint with 12 iterations,
   even when the initial attempt was EARLY (`fit.py:306`). Do not restore the earlier blanket relaxation.
   A deterministic restart/polish from that retained endpoint, under its own Sigma, is the cheap repair to test.
   It must earn the existing convergence criteria. A small gradient alone is insufficient.

2. **Q1 — There are two different 31-node baselines. Do not conflate them.**
   Mac m15: G3 = -16.296420131, B3 = -16.296277941, contrast +0.000142189.
   AWS m15: G3 = -16.297749953, B3 = -16.293489479, contrast +0.004260473.
   Both families move between these runs. The contrast difference is +0.004118284 without changing node counts.
   Code hashes are `a45a07d92b82` and `6d447ad94463`; data IDs also differ (for all 20 members).
   Thus this is not a controlled same-data, same-code hardware experiment.
   The Mac fold-3 B3 is POSITIVE, with training likelihood -10944.138316; its held-out fold gain is only +0.083138 nat.
   Source: `results/s2/decision/W2/set_0.json:1`; `results/s2_aws/decision/W2/set_0.json:1`.

   The two-pass scale comparison uses the Mac baseline and an AWS blanket-33 reference.
   Its four failures are m12 +1.75e-4, m14 +6.24e-4, m15 -3.70e-3, **m18 -5.05e-4**.
   The brief's count of three failures omits m18. There are sixteen within tolerance.
   For m14 and m18 the two-pass contrast equals the Mac 17-node contrast exactly: neither participant was refitted.
   Lowering the scale threshold can change an EM path; a resulting improvement would not by itself identify scale error.
   Source: `results/s2/checks/twopass_g_W2_set0.json:17`, `:152`, `:2008`; `s2.py:431`.

3. **Q1 — Archived Mac spreads do not support a small-spread-only explanation or trigger.**
   Below are parent s_tau in ms / s_g, folds 0 through 4. All these Mac selected fits are POSITIVE.
   Vectors were read from `results/s2/archive/W2/set_0.npz`, keys `m{m}_f{fold}_{G3,B3}_theta`.
   The archive convention is in `s2.py:131`; parameter conversion is in `models.py:386`.
   Fit identities and selections: `results/s2/decision/W2/set_0.json:1`.

   - m15/S4: G [(150/.452), (15.212/.653), (8.405/.638), (97.413/.356), (13.268/.734)];
     B [(150/.452), (15.216/.653), (8.405/.638), (97.335/.356), (13.272/.735)].
   - m0/S18: G [(16.980/.448), (13.656/.442), (10.241/.485), (16.598/.401), (13.986/.478)];
     B [(16.859/.426), (13.673/.432), (10.019/.484), (16.599/.401), (14.007/.453)].
   - m12/S19: G [(53.340/.691), (52.782/.694), (47.214/.691), (53.366/.701), (54.592/.700)];
     B [(53.508/.677), (52.779/.694), (47.438/.679), (53.563/.696), (54.762/.694)].
   - m14/S18: G [(6.882/.508), (14.165/.501), (12.234/.499), (14.030/.535), (13.515/.529)];
     B [(6.880/.475), (14.364/.486), (12.276/.499), (14.052/.535), (13.485/.487)].
   - m18/S15: G [(32.647/.461), (31.980/.483), (31.397/.452), (35.712/.451), (39.690/.455)];
     B [(32.729/.466), (31.634/.435), (30.921/.401), (35.491/.443), (39.453/.423)].
   - m19/S13: G [(60.032/.603), (73.021/.609), (63.356/.555), (150/.577), (103.250/.571)];
     B [(60.171/.600), (73.380/.606), (62.985/.548), (150/.573), (103.165/.568)].

   These are not the missing AWS 61-node estimates. In particular, m15's conspicuous AWS fold-3 failure
   is not established to be at small spread. The Mac counterpart is near 97 ms.

4. **Q1 — New measurement: fixed-parameter integration changes are small on ALL TWENTY Mac participants.**
   I regenerated W2 set 0 from the stored generators and verified every data ID against the Mac record.
   I held each selected theta, Sigma and training-catch baseline fixed, including REDUCED selections.
   I evaluated the spline at 31/61/121 latency nodes and the adaptive scale integral at 17/33 nodes.
   This used NumPy, the archived float32 theta/Sigma promoted to float64, and the existing formula
   `models.py:436`; the likelihood construction is `models.py:478`, `:552`.
   Rebuilt 31/17 family scores agree with the archived scores within 9.79e-8 nat/trial.
   No optimisation, new selection or covariance update was performed.
   Inputs: `results/s2/decision/W2/set_0.json:1`, its archive NPZ, and `s2.py:82`.

   Max absolute participant-contrast changes, nat/trial:
   31/17 -> 61/17: 1.25740e-5 (m14); 61/17 -> 121/17: 6.72767e-6 (m8).
   31/17 -> 31/33: 2.61296e-5 (m4); 31/17 -> 61/33: 2.56238e-5 (m4).
   61/33 -> 121/33: 6.72962e-6 (m8). Every value is below 8.83225e-5.
   For m15, 31 -> 61 changes G by -8.41426e-5 and B by -8.48323e-5;
   their contrast changes by -6.89644e-7. The next contrast change is -3.57287e-7.
   For m12, individual family changes are about -4.7e-4 but cancel to -4.61e-6.

   This is evidence for an inexpensive route through fit stability. It is NOT the design's required refit check.
   It neither measures the AWS 61 optimum nor excludes another optimum under refinement.
   `node_check` discards its fit rows and parameters: only contrasts survive (`s2.py:391`, `:401`).
   Therefore the available 61-node JSON cannot answer whether G, B, or both changed, or whether its selection flipped.
   Retrieve any surviving endpoints, or rerun while archiving them. Do not invent their spreads or likelihoods.

5. **Q1 — How to separate the four proposed mechanisms.**
   (a) The comb is real: weights are softmax(-tau^2/(2s^2)), `models.py:501`.
   At s=2 ms the 31-node zero weight is 0.99999255 (`results/s2/checks/small_spread.json:16`).
   Compare fixed-theta training/held-out likelihoods, gradients and realised SD across grids, then refit.
   Also check broad spreads: equal endpoint weights in `models.py:228` are not trapezoidal half-weights;
   endpoint discretisation can matter even when many nodes carry weight. Small spread is not the only possible error.

   (b) A different interpolated template model is not what this implementation does.
   Every node uses the same cubic spline, same knots, coefficients, support and window averaging
   (`models.py:190`). Arbitrary shifts already exist (`models.py:172`). There is no interpolation of a 31-node table.
   The numerical mixture changes; the intended continuous latent model does not.
   The 10 Hz filter and 53 window means limit inference about timing, not the necessary accuracy of a latent integral
   (`data.py:33`, `:49`, `:114`). A 30 ms readout step does not license a 10 ms integration step.

   (c) A discarded near-optimal warm endpoint is shown in finding 1. Multiple near-equal optima and free-Sigma
   degeneracy remain plausible additional mechanisms, not an established complete explanation.
   (d) Asymmetric boundary selection is shown at 31 nodes. A 31-to-61 selection flip is not archived.
   Use a matrix of fixed-point cross-evaluations and bidirectional warm refits under the SAME data and code.
   Save training likelihood, convergence history, theta, Sigma, selection and each family's held-out fold sums.
   Select endpoints on training likelihood only. This separates integration, path, and boundary effects.

6. **Q2(a) — Adaptive latency quadrature: worthwhile later, unvalidated tonight.**
   Possible DESIGN rule: “Integrate the truncated normal using 31 Gauss–Legendre nodes in its probability coordinate:
   tau_j = s Phi^-1(Phi(-150/s)+u_j[Phi(150/s)-Phi(-150/s)]), with weights on u in (0,1).
   Keep the exact reduced model; refine to 61 if the declared accuracy check fails.”
   This is one precise way to scale nodes with spread while retaining the entire declared support.
   Ordinary untruncated GH nodes, clipping them, or silently dropping nodes outside support are not equivalent rules.
   Mechanism: the small-spread comb and endpoint weighting, not lost optimisation chains.
   Cost: approximately x1 in node count, plus moving-basis/derivative work; runtime multiplier unmeasured.
   Check: same-data W2-set-0 full refits versus 61 and an independent finer reference; rerun small-spread/rank checks,
   gradients and EM moments. Differentiate through moving nodes and preserve normalization at tau=0.
   Risk: a prior-adapted rule can miss narrow or multiple posterior peaks. Thirty-one nodes is not an accuracy theorem.

7. **Q2(b) — Spread-triggered two-pass latency: cheap warm chains, insufficient trigger.**
   Possible DESIGN rule: “Fit at 31; if any positive candidate in a training fold has s_tau <20 ms,
   warm-refit both families' candidates at 61, reapply cross-family rescues and reduced/positive selection.”
   Twenty ms is a proposed development threshold, not a measured guarantee.
   Do not use |Delta3| to decide refits: it uses held-out outcomes and changes the CV procedure.
   Mechanism: poor resolution at small spread. It misses broad-spread failures and failed warm chains.
   Cost: x(1+q*k), q = fraction of triggered paired folds, k = fine warm-refit cost / original fold cost.
   Neither q nor k is measured for latency; this need not approach x2, but no numeric speedup is licensed.
   Check: all 20 full-procedure contrasts against a repaired 61 reference, plus the 121 recheck where 61 is adopted.
   Risk: one warm chain can remain in the wrong basin. The failed scale experiment is a warning about that shortcut.

8. **Q2(c) — Fixed-point error estimate: use as a diagnostic and training-only escalation trigger.**
   Possible DESIGN rule: “At every candidate endpoint evaluate 31 and 61 on training trials, at fixed theta/Sigma;
   refine and refit when a predeclared familywise training-error or gradient threshold fails.”
   Pick and validate that threshold on development data; no training-error bound here implies the contrast tolerance.
   Include boundary candidates, nesting failures and failed stationary warm chains in the escalation checks.
   Mechanism: integration error at the found optimum. It cannot detect a better unseen basin or all flat-direction drift.
   Cost: x(1+e+q*k), e = a few evaluations / the complete fitting workload; likely small, but measure compilation too.
   Check: the frozen trigger must reproduce all 20 repaired 61-node refit contrasts within tolerance; do not inspect only
   triggered cases. Finding 4 alone does not pass it. A held-out score error may guide numerical integration at fixed
   parameters; using that score to choose whether to REFIT makes the fitted predictor depend on test outcomes.
   Risk: cancellation between family errors, parameter movement, and hidden optima defeat a score-only sentinel.

9. **Q2(d) — Fit at 31, score at 61: valid as a new estimator, not the declared MML repair.**
   Possible DESIGN rule: “Train with the 31-node objective and report 61-node predictive densities.”
   This is honest held-out prediction if completely specified from training data and calibrated as such.
   It is not fitting the 61-node objective; its boundary selection, Sigma and stationary points can be wrong for it.
   It cannot repair finding 1. Do not describe it as a harmless scoring precision upgrade.
   Cost: x(1+e_score), one extra scoring evaluation per fit, not x2 fitting; runtime unmeasured.
   Check: full development comparison and fresh S4 calibration/validation of that exact estimator, including selection
   and recovery/profile consistency. Risk: accurate evaluation of a poorly fitted density. I do not recommend it here.

10. **Q2(e) — Blanket 61: a fallback, not a cure for the demonstrated failure.**
    DESIGN rule: “Use 61 fixed equally spaced latency nodes; require full 61-versus-121 refit agreement before S3.”
    Mechanism: finer integration; it still needs the chain repair. Cost: x61/31 = x1.968 on positive-latency evaluations;
    the whole-pipeline multiplier and memory contention must be measured. Blanket scale 33 adds x33/17 = x1.941
    on scale evaluations; their product is x3.82, not a measured host-throughput guarantee.
    Check: same-code full paired refits, all 20 participants, unchanged tolerance, with no missing cases passing silently.
    Risks: more nodes do not guarantee the same basin or resolution at the 2 ms floor.

    If this fallback is necessary, the reduced first-submission manifest is W1–W4/O1–O5 at R=100, T1 at R=50,
    E1 at R=100 if certified; T2 development-only and T3 S4b deferred. Retain both targets' S4a search/certification,
    epsilon, both c0 batches, R1–R5, and the inherited mechanism comparison. Recovery R=15; nine profile grid points
    {0,5,10,20,40,60,80,120,150}, with the same hull rule and two endpoint bisections: at most 11 fits.
    This grid must be explicitly frozen and validated; do not merely change a cost spreadsheet.
    Sources: `DESIGN_jitter.md:598`, `:605`, `:461`.

    On the OLD per-category prices, removing T2/T3 saves about 161/3307 core-hours; reducing recovery saves 118;
    reducing profile replicates and 15->11 evaluations saves about 414. Total factor about 0.790, not a fourfold saving.
    Blanket 61 with a hypothetically validated x1.015 scale refinement gives a planning factor about x1.58 overall:
    roughly 950–1110 host-hours, 48–56 h on twenty hosts, before barriers/retries and revised recovery accounting.
    Blanket 61 AND blanket 33 still gives roughly x3.0 after these reductions: 1800–2110 host-hours.
    These extrapolations do not certify the budget. Use the measured fleet rate, actual four-region prices and spend;
    the USD 3000 total cap and the separate USD 1300 S4 ledger limit both need reconciliation before launch.
    Sources: `S2_REPORT.md:255`, `:277`, `:299`; `recost_rev7.py:66`.

11. **Q2(f) — Preferred next experiment: repair the fit, then try to retain the existing 31-node rule.**
    DESIGN addition: “A stationary but unaccepted warm endpoint gets a bounded restart from that endpoint under
    its own Sigma, with unchanged acceptance tolerances. Reapply the G/B rescue and nesting checks after refinement.
    A failed required rescue is reported as a numerical failure, not hidden by choosing a worse candidate.”
    Make this a deterministic rule for every relevant fit, not a special treatment of m15 or S4.
    A new failure-to-UNAVAILABLE condition is an explicit pre-S3 amendment, not something current code already does.
    Do not automatically discard an identifiable participant because its spread is small or its contrast inconvenient.
    UNRESOLVED is a set interval outcome; it is not a substitute status for a failed participant fit.
    Cost: x(1+r), r = measured extra rescue work / original workload, with no blanket node multiplication.
    Check: same-data, same-code 31/17, 61/17 and 31/33 full refits with bidirectional endpoint transports;
    compare the final retained 31 procedure to the repaired finer procedures for all 20 participants.
    If refinement changes the selected basin, transport it back and polish at 31 before diagnosing quadrature.
    Then validate the reproducible fitting algorithm, not a hand-picked union of favourable held-out scores.

    This is the strongest low-cost lead because finding 4 measures small fixed-point error on all twenty,
    and finding 1 identifies a concrete preventable loss. It is not yet a passed alternative.
    The scale two-pass result logs 193/400 refits and x1.01528 archived fit-seconds, but FAILS its accuracy check
    (`results/s2/checks/twopass_g_W2_set0.json:130`, `:1994`). That ratio is neither an accepted S4 cost nor a fleet
    benchmark. Its second pass also follows the cross-family loop without rerunning those rescues (`fit.py:700`).
    Repair and validate this interaction at the FINAL combined latency/scale rule; separate marginal passes do not
    bound the combined contrast error. A threshold-0.4 result was not present when this review was read.

12. **Q3 — Preserve historical readings; withdraw numerical closure and causal overstatements.**
    W2 sets 0–9 remain the recorded 0 POSITIVE / 8 NEGATIVE / 2 UNRESOLVED under that procedure.
    AWS set 0 is NEGATIVE under 31, g33 and tau61; its means are -0.001262, -0.001306 and -0.001452.
    This stability of sign does not satisfy the every-participant tolerance.
    Reread the development contrasts after the frozen repair, including T1/O1, before treating them as its evidence.
    Source: `S2_REPORT.md:132`; `results/s2_aws/checks/nodes_tau61_W2_set0.json:35` and `:79`;
    `results/s2_aws/checks/nodes_g33_W2_set0.json:57`.

    S4's weak-response recovery collapse remains an observed result of the earlier procedure, not proof that finer
    quadrature restores recovery. Rerun the S4 configuration under the final fitter and rule. Keep free Sigma and
    measure R1–R5; do not drop S4 from the fixed roster. The oracle comparison also changes baseline, as the earlier
    review noted (`S2_REPORT.md:177`; `reviews/2026-10-24_s3_freeze_rev7_codex_review.md:110`).
    S19's residual gains remain unexplained until the numerical rerun; neither “flexibility established” nor
    “quadrature artefact established” is warranted (`S2_REPORT.md:159`).
    Generic full ranks remain valid on their tested cases. Smooth small-spread profiles show behaviour of that grid;
    “the floor loses nothing” and “10 ms resolves the first rise” must be qualified as grid-conditional observations,
    not evidence of continuous-integral accuracy (`S2_REPORT.md:220`, `:228`; `results/s2/checks/ranks.json:1`).

    The inherited human/per-window results and 989/12000 synthetic calls stand; this code does not recompute them.
    Keep the paper's matched jitter comparison pending. Add that numerical convergence of that comparison is pending;
    make no attenuation, survival or latency-identification claim yet (`DESIGN_jitter.md:42`, `:619`).
    There is a local anti-conservative example at m15, not a general sign theorem for coarse quadrature.
    Other node changes have both signs, and both families, templates and Sigma are fitted separately.
    Gate (b) must use the exact frozen numerical procedure on fresh seeds. Even a conservative average bias would
    not license it. UNAVAILABLE sets count as false calls; available-case participants require the declared minimum
    16, and V2 still applies (`DESIGN_jitter.md:296`, `:395`, `:528`). Do not waive a failed check by removing m15.

13. **Q4 — The 121 obligation depends on the adopted rule, not on the cost pressure.**
    If repaired 31 passes the full 31-versus-61 comparison and 31 is retained, §4's conditional adoption of 61 has not
    occurred. A full 121 refit is then not required by that sentence. Finding 4 supplies an extra fixed-point probe.
    If 61 is adopted anywhere as the operational fallback, retain a 61-versus-121 full-procedure check on W2 set 0,
    including untriggered participants. Do not compare only m15 or substitute a fixed-point score check for refitting.
    Warm-starting 121 from 61, with the declared rescues and acceptance rules, is the cheapest candidate check;
    an independent start/path audit is still needed to keep both grids from sharing a missed basin.
    Archive both grids' endpoints. The old contrast-only 61 file is useful evidence, not a resumable fit cache.
    Source: `DESIGN_jitter.md:148`; `s2.py:401`; `fit.py:803`.

    Schedule twenty participant-dataset tasks as one queue on the Mac's twelve performance cores, no nested parallelism.
    At the observed Mac 31-node task average of 626 s, the optimistic linear work bound for warm-independent full
    121 fits is 20*4*626/12 = 4173 s, about 70 min; two waves and contention make 80–100+ min a planning estimate.
    A 61-plus-121 full rerun is about 104 min by work division, before these overheads.
    Across twenty otherwise idle AWS hosts, one participant per host avoids the 48-worker bandwidth load; using the
    measured single-task 1513 s as an example gives about 101 min for 121. Participant mix prevents a guarantee.
    The Mac may be cheaper and faster than AWS for this small queue. These are schedules for the owner job,
    not commands executed in this review (`results/s2/checks/twopass_g_W2_set0.json:2003`; `S2_REPORT.md:282`).

14. **Q5 — Verdict and exact proposed text.**

LATENCY RULE: Retain 31 equally spaced nodes on ±150 ms, with the exact reduced candidate, only if the repaired paired fitter passes the full same-data, same-code 31-versus-61 W2-set-0 refit check for every participant; otherwise adopt 61 and pass the full 61-versus-121 recheck before S3.

    Tonight: first repair/polish the lost warm endpoints, starting with m15 fold 3 as a reproducible failure case.
    Then run the paired comparisons in finding 11 and the FINAL combined two-pass-scale procedure against its repaired
    fine reference. PASS means all 20 participants accounted for, max absolute contrast difference <T, with
    T=min(8.8322454e-5, one tenth of the repaired reference interval half-width) nat/trial; no unresolved numerical/
    nesting failure; and recorded selections/endpoints. Do not silently shrink the
    finite comparison roster as `s2.py:395` currently permits. Record any unavailable case as a failed numerical check.
    No change to tolerance, no participant deletion and no selection of a start using its held-out score.

    Expected node-count multiplier if this passes: x1 latency. With a validated scale two-pass rule, the planning
    multiplier is its measured cost times (1+r), the extra rescue fraction. The existing failed run suggests a cheap
    warm-pass workload near x1.015, but there is NO measured passing combined S4 multiplier yet.
    At r=0 the illustrative range is 609–711 host-hours; at r=0.10 it is 670–782, before fleet overhead changes.
    Measure r and host throughput; do not label either illustrative range a forecast. If these checks fail, use
    finding 10's 61-node fallback and reduced manifest, with a new cost and the 121 evidence, or hold the study.

    Proposed DESIGN §4 sentences:
    “Node comparisons use the same data and final paired fitting algorithm and archive each candidate's parameters,
    covariance, likelihood, status and boundary selection. Integration at fixed parameters is reported separately
    from changes after refitting. Failed stationary warm chains are polished under unchanged acceptance criteria;
    numerical failures cannot pass by omission. The latency rule is the LATENCY RULE stated above.”

    Proposed S2_REPORT §8 sentences:
    “The original 31-versus-61 latency and 17-versus-33 scale refit checks failed. The two-pass scale check also failed.
    The AWS m15 reference loses a near-optimal B warm chain and selects the reduced candidate on fold 3.
    A separate fixed-parameter diagnostic on all twenty archived Mac fits found maximum contrast changes of
    1.26e-5 for latency and 2.61e-5 for scale, below 8.83e-5; this does not replace the full-procedure node checks.
    Numerical closure and S3 remain pending the repaired same-data comparisons and the final combined rule.”

FREEZE: HOLD. The available full-refit checks fail; no passing combined rule or S4 cost has been demonstrated.
