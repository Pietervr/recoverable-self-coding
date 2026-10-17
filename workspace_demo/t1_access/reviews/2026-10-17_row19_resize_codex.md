# Row 19 resize — Codex design opinion, 17 October 2026

**Recommend 60 fixed attempted datasets × 80 designated refits, omega = 1 only, with replicate-complete planning and one sealed futility analysis.** Preserve each existing B = 200 producer stream and use indices 0–79 through a new reviewed prefix consumer. The concrete CSCI1913 + EC2 split below fits the recorded funding maxima; HEAL1922 is not needed for this screen. Defer omega = 2. This is a useful, limited coverage screen, not a promise of interval validation or a date on which the model study may start.

**Design recommendation only.** No current job, worker, manifest, control, partition, ledger or manuscript was altered. No admission, scientific fit, simulation draw, scheduler command or AWS operation was run. Bounded read-only Lengau record reads and deterministic design arithmetic were used. Adoption, migration, resource/release reviews and any spending remain with Claude and the owner.

## Basis and what blocks first

Brief: Unimog `prompts/2026-10-17_codex_r052_row19_resize.txt`, commit `174ddb2922ef21c5607347c8411637d06b786c1e`, SHA256 `e3ad3fcfe932ecda2258a196fafd4211b7707f5f403d9ae9b4242fd8572c6245`. Ownership was recorded at Unimog `0b110e02b7427ab315ca894a820c4a11ce0676d3`, then handoff `962fd87e-360f-5fbb-bf6d-97163eced62a` accepted by exact session **GPT: R052 Entropy paper**, native `01a0d19e-2127-7051-9a61-6db771088559`.

The present declaration is 100 fresh attempted datasets, reps 3–102, B = 200, omega 1, one look, failure-only. Its primary interval is a 2.5%/97.5% percentile interval on selection/ws. Coverage concerns the complete procedure's expectation, estimated by the independent policy-matched row-22 bank; it is not coverage of the screen's own mean. The bank/target adoption and numerical seal remain prerequisites. The screen cannot establish all-generator or band validation by surviving futility. Sources: `chpc/ROW19_SCREEN_DECLARATIONS.md` §§1,4,6–7; `chpc/row19_screen_release.py`; `PREREGISTRATION_T1_model.md` §10; Unimog `project_knowledge/rsc_t1_simulation_design.md` §§5–6 and rows 19/22; SI `sections/methods.tex:121–125`.

Resolve these in order:

1. **P1 — agree the scientific scope and finite procedure:** B = 80 prefix-of-B = 200, 60 attempted IDs, one omega-1 screen, exact failure/target/error rule below. No positive adoption or protocol freeze follows merely from non-futility.
2. **P1 — fund and qualify the actual EC2 route:** production is unreleased. A cost reconciliation is not R1–R5 qualification. Choose a qualified packing and explicit concurrency; the faster calendar depends on them.
3. **P1 — migrate ownership, planning and release:** a new reviewed epoch/controller/prefix consumer must preserve every historical/live claim. A smaller partition `k` cannot express the proposed ownership. Drain controller commands during migration; leave scientific jobs running.
4. **P1 — bound recurrent crash attempts:** apply the rescue rule prospectively after current attempts settle; do not drop difficult coordinates or continually buy the same failed attempt.
5. **P2 — defer stress and the next-study gate:** decide separately what further settings constitute adequate validation and whether distinct future work belongs under HEAL1922.

## 1. B: 80 is a finite-procedure compromise, not a proven endpoint-precision threshold

The actual code uses `np.percentile(v, 2.5)` / `97.5`, default linear interpolation (`analyze.py:771–776`). It does not use a basic, BCa or studentized interval. In one-based order statistics, the lower endpoint interpolates at rank `1+(B−1)×0.025`; this is the documented [NumPy linear quantile rule](https://numpy.org/doc/stable/reference/generated/numpy.quantile.html).

| B | Lower endpoint | Expected draws in a 2.5% tail | Tail-probability MCSE | Chance of no draw below that quantile |
|---:|---|---:|---:|---:|
| 50 | .775 X₂ + .225 X₃ | 1.25 | .02208 | 28.20% |
| **80** | **.025 X₂ + .975 X₃** | **2.00** | **.01746** | **13.19%** |
| 100 | .525 X₃ + .475 X₄ | 2.50 | .01561 | 7.95% |
| 160 | .025 X₄ + .975 X₅ | 4.00 | .01234 | 1.74% |
| 200 | .025 X₅ + .975 X₆ | 5.00 | .01104 | 0.632% |

The last three columns are continuous-distribution illustrations from Binomial(B,.025), not estimates from the sealed screen. The MCSE is on the probability scale, not nat/trial. Under regularity, statistic-scale endpoint error is approximately `sqrt(p(1−p)/B)/f(q_p)`; its density factor is unknown here. No candidate B guarantees stable endpoints or stable inclusion when the target lies close to an endpoint. Even B = 200 is not a demonstrated numerical limit.

For B = 80, conditional on a dataset and a target at bootstrap CDF position u, the number of draws below the target is Binomial(80,u), ignoring ties. Interpolation implies an inclusion probability between `P(3≤N≤77)` and `P(2≤N≤78)`. At u = .05 those bounds are .7694 and .9140; at u = .10 they are .9893 and .9978. Bootstrap MC can therefore change a particular dataset's classification. These are analytic illustrations, not row-19 results.

B = 100 costs 25% more than B = 80 for only a 10.6% reduction in probability-scale endpoint MCSE; B = 160 doubles cost for a 29.3% reduction. B = 50 is cheaper but has particularly sparse tails. **Choose B = 80 as the procedure being screened, not as an approximation already proved equivalent to B = 200.** Its bootstrap randomization is part of its coverage probability `c₈₀=P{theta_g∈I₈₀(D,U)}`. Across independent datasets/streams, binomial uncertainty in inclusion already includes that randomization; do not add endpoint MCSE to coverage MCSE. A result about c₈₀ establishes no bound on c₂₀₀ or an infinite-B limit.

The numerical identity matters. `stratified_resample` draws the whole B-row block for each family before moving to the next (`analyze.py:312–318`). Re-running with B = 80 and the old seed changes later families' draws. B/config are also hashed into dataset identity (`:494–516`). Therefore **do not change B in the producer manifest, relabel existing records, or use `until=80` as a completed interval**; that hook intentionally remains partial. Keep producer B = 200, folds, draw matrix and per-index fit seeds immutable. Add an explicit analysis contract for the first 80 records, validating them against their original B = 200 task, then computing the 80-record percentile interval without fitting. Future use of this procedure must retain this exact stream convention.

## 2. Sixty attempted IDs, one look, and honest unresolved outcomes

Freeze this simple ID-only set before numerical release:

`S = {r in 3..102 : (r−3) mod 5 ∈ {0,1,2}}`.

It selects 60 IDs spread over the original range and **includes rep 83**. No dataset is selected by success, runtime, interval or score. Operational completion/crash identities were already exposed while costing this redesign; disclose that exposure. Do not call the redesign blind to operational outcomes. The original numerical seal has not been opened by this opinion.

Use all 60 as attempted datasets, retain every original/refit failure and the paired refit/cluster availability partition, and never replace a seed. With 60 usable intervals, MCSE near .90 is .03873, versus .030 at n = 100. This screen can detect gross failure; it cannot reliably resolve coverage close to the floor.

Let T be the frozen, adopted row-22 target set. For usable intervals let `Kmax=max(theta∈T) K(theta)` and `Kmin=min(theta∈T) K(theta)`, evaluating endpoints, T's ends and intervening segments with inclusive ties, as the current maximum-count consumer does. Report `[Kmin/n, Kmax/n]` and exact binomial uncertainty, plus failures. Never substitute the point bank mean for T.

**Recommend a one-sided 98.5% Clopper–Pearson upper bound for futility.** STOP FOR FUTILITY if that bound at `(Kmax,n)` is below .90; otherwise **not ruled out at this look**, never PASS. With all 60 usable, the boundary is **Kmax≤48**. The same count happens to occur under a 97.5% bound, but the revised confidence level and error accounting must be written explicitly. Exact binomial-tail inversion is the [Clopper–Pearson method](https://www.itl.nist.gov/div 898/software/dataplot/refman 2/auxillar/exacbino.htm).

The current T is nominally 99% via a t interval and declared tail/precision/stability gates. Conditional on theta_g being in T, screen false-futility error is at most 1.5%; adding nominal bank noncoverage gives a union bound of 2.5%. This is **conditional on the bank's approximation assumptions**, not a distribution-free guarantee manufactured by passing its checks. Retaining a 2.5% screen error plus 1% target error instead gives up to 3.5%, not 2.5%.

If M of the 60 intervals remain unavailable, retain the complete-case conditional result and add an attempted-set envelope: count all M as covering for an upper/futility assessment and none as covering for the lower assessment. For a conservative stop require **both** the usual usable-n CP upper bound to fail and the all-60 upper bound at `Kmax+M` to fail. The all-60 component reduces to `Kmax+M≤48`. This extra guard prevents a failure conclusion from relying on excluding hard datasets; it is not an assertion that missingness is random or that a nonexistent interval is valid. Unavailability remains an operational result and cannot support unqualified interval adoption.

At a known singleton target, the one-look n = 60 futility probabilities are 85.2% at true coverage .75, 55.1% at .80, 18.1% at .85 and 1.46% at .90. Actual T-based power is no greater, because Kmax is conservative. These are exact deterministic binomial calculations, not simulations. For perspective, n = 80 at the same error allocation has boundary 65 and 65.4% power at .80; n = 100 has boundary 82 and 72.9%. More datasets buy precision but do not fit the concrete maximum-reservation design below.

A positive rule is **not recommended as this screen's adoption gate**. If explicitly added, an n = 60 one-sided 98.5% lower bound at Kmin would clear .90 only at Kmin≥59. Even at true coverage .95 and a known target that occurs only 19.2% of the time. Surviving the proposed futility screen does not establish the replacement, its other generators or the model band; the registered report's freeze condition remains unmet until an adequate validation plan actually passes.

Sequential looks can be valid, but repeated fixed-n 97.5% bounds are not the advertised test. Four looks 40/60/80/100 with a total screen alpha = .015 and equal spending have futility counts 29/46/63/80; the bank error is allocated once. Two looks 40/60 with .0075 per look give 30/47, reducing final power versus the fixed 60 rule. Naively repeating the old fixed-n 97.5% bounds at four looks gives 3.69% false futility at p = .90 even before target error. A genuine time-uniform alternative requires its own implementation, as distinguished in [Howard et al., confidence sequences](https://arxiv.org/abs/1810.08240). **Keep the one-look design here.** If funding stops before the prespecified terminal analysis, complete prefixes remain recoverable evidence, but an unplanned early fixed-n bound is not an adopted decision.

## 3. Progress, programme totals and a funded provider split

### Recorded accounting, not an assumed allocation balance

Bounded record reads at approximately **17 Oct 03:06–03:11 UTC** found the following. These are the programme gate's six known ledgers plus its declared six other hours, not a fresh CHPC portal audit; the adoption gate must refresh them under its lock.

| CSCI1913 campaign | Settled core-h | Live maximum |
|---|---:|---:|
| Slice | 720.71 | 0 |
| Development shard | 4,791.76 | 0 |
| Row 22 bank | 10,882.51 | 0 |
| Screen refit | 21,471.07 | 11,520 |
| Screen originals | 2,168.61 | 0 |
| EC2 qualification S | 1,224.41 | 0 |
| Declared other | 6.00 | 0 |
| **Total** | **41,265.0636** | **11,520** |

Committed total is **52,785.0636**, leaving **47,214.9364 uncommitted** within 100,000. Remaining after settled spend is 58,734.9364, which still has to carry live jobs. The combined refit+S 60,000 envelope has 22,695.4733 spent plus 11,520 live, leaving 25,784.5267 uncommitted. Its recorded cap can be raised; the programme allocation remains the hard stop.

The saved zero-alarm watch at **01:29:30 UTC** has 824 unique completed coordinates, indices 0–8 only, and no complete B = 50-or-larger dataset. All 100 reps have 7–9 records; only indices 0–1 are common to every rep. The ten current live plans contain 240 distinct coordinates, 17 already in that watch, hence 223 not yet known complete. Reconcile the brief's 168 running/in-flight counter with this planned-coordinate convention; **824+223+14,953 = 16,000** reconciles the Lengau allocation without counting a planned coordinate twice. EC2 production has not run.

The 35 settled refit jobs cost 21,471.0667 for 807 new coordinates: **26.606 core-h per new coordinate including failed/idle/retried work**. Ordinary nonzero jobs have median 25.483 core-h/new. Ten 24-core jobs burn at most 5,760 allocated core-h/day; 26.606 implies about 216.5 new coordinates/day, not a guaranteed 230. The all-programme remaining hours fund about 2,207 further refits at that observed all-attempt rate, not 3,300. Current refit admissions reserve **24×48 = 1,152 core-h/job**; unused reservation becomes available only at settlement.

### Concrete allocation for the proposed 4,800 coordinates

For S and indices 0–79, the saved metadata gives:

**493 completed reusable +136 unfinished coordinates already claimed by Lengau +4,171 not yet claimed = 4,800.**

Assign the **largest 47 IDs in S (24 through 100 in this list)** to EC2 for their remaining **unclaimed** prefix coordinates. The smallest 13 remain Lengau's. All existing claims/completions retain Lengau provenance, including 110 live coordinates on EC2-designated replicates. This gives **3,274 new EC2 coordinates and 897 new Lengau coordinates**, in addition to 136 existing in-target claims. It is a whole-*remaining-work* allocation, not retroactive ownership of whole replicates. Preserve the 40 unselected datasets' sunk costs and current live liabilities; do not cancel their workers or credit their work into the new denominator.

Lengau's 897 new coordinates forecast 22,425–23,322 core-h at 25–26, or 23,865.6 at the observed 26.606. At ten jobs that is about 4.1 days of useful service, plus current drain, queue, refill and crash tails. A conservative service envelope is up to 2 days for current 48 h jobs plus four 48 h waves for 38 further jobs, about 10 days **before** queue/migration/rescue delay. It is not a guaranteed calendar date.

Use **38 ordinary full-job reservations = 43,776 core-h**, plus **two full rescue/retry reservations = 2,304**, total future 46,080. Carrying all current live maxima, programme commitment would reach **98,865.0636**, leaving **1,134.9364**. Combined refit+S would reach **80,295.4733**: propose a recorded **81,000** sub-envelope, with the 100,000 programme gate unchanged. This is the maximum-reservation fit, not merely a favorable measured-cost extrapolation. The two rescue jobs are a finite allowance, not a promise of eventual completion. New unrelated programme admissions or changed resource requests require a fresh costed allocation; they cannot consume this headroom unnoticed.

CSCI1913 alone does **not** fund all 4,171 future unclaimed coordinates: at 26.606 they require about 111,000 more core-h. The original plan of 100 datasets with B = 200 also remains unfunded; adding HEAL1922's 100,000 hours does not make its roughly 400,000 remaining Lengau core-hours disappear.

### EC2: money fits only with a qualified, bounded route

Inventory generation 41 at **01:28:59 UTC** has Q1 charged 33.2641 USD across attempts and Q2 charged 11.7008 USD: **44.96495** against the 2,300 envelope, leaving **2,255.03505**. The 3,000 cap has **2,383.35740 remaining**, after baseline 544 and EC2-run charges 72.64260; baseline accrues 5.50 per started UTC day. No new AWS account query was made.

Q2 ran 24 planned repeats in 15.9675 h, with **23 successful and one crashed**, not 24 successful refits. Its 0.48753 USD/planned slot is a cost illustration, not a future success guarantee. At the declared 76-worker geometry, 72 unique work +4 sentinels per instance, 3,274 work coordinates require **46 full batches /3,496 paid slots**, including the partial final batch. The Q2-derived forecasts are **1,704.42 USD** per planned-slot rate or **1,778.52 USD** per successful-slot rate. These extrapolate from another packing; they are not measured production rates.

The declared 22 h lifetime funding formula gives 46×[22.75×(1.20+.014)+.30] = **1,284.251 USD** of per-batch funding maxima for the all-success 76-worker route. The lower bound than the measured-rate forecast reflects different packing, not proof that packing works. **Carry the higher 1,778.52 forecast plus a proposed finite 300 USD qualification/retry allowance**: 2,078.52 new USD fits the remaining 2,255.04 envelope. Bound that allowance to at most two new qualification instances and four extra production batches, all together within 300 USD; a further attempt needs a new decision. At a 41-day calendar, about 225.50 further idle USD gives a projected global total of **2,920.66 USD**, leaving only 79.34; unrelated AWS spend, additional delays or retries cannot be assumed free. The authority must enforce both caps on every attempt. Neither this allowance nor the arithmetic grants purchase permission.

Production is unreleased. A matching R1–R5 certificate/review/release for the new epoch and actual packing is mandatory: exact successful-path parity, full 76-worker memory/occupancy evidence, bound bundles/producer statuses and ingestion replay. A crashed Q2/S coordinate is not an invented scientific failed-fit record. R5 proves ingestion publication recovery, not producer-host restart.

With 46 batches at Q1's 21.2811 h elapsed, the **conditional EC2 service calendars** are 40.79 days at one simultaneous instance, 20.39 at two, 8.87 at five and 4.43 at ten. These use integer batch waves, `ceil(46/fleet_size)×21.2811/24` days. Startup, interruptions, migration, rescue and quota/capacity availability add time. Five qualified concurrent instances would make roughly 9 days of EC2 service comparable to the conservative Lengau envelope; **five-way concurrency is a proposed reviewed capacity choice, not an existing fact or authorization**. No particular finish date is justified before it is qualified and available.

A 24-total-worker route retaining 4 sentinels leaves 20 unique slots/batch: 164 batches, 109 days on one instance. Its all-batch funding maxima total 2,713.73 USD, exceeding the remaining production envelope; its long idle accrual also threatens the 3,000 cap. Do not replace the 76-worker route with that configuration while promising the same funding guarantee or date. If the 76-worker memory/release gate fails, return to the owner with a newly costed packing/design; do not consume the proposed budget as endless qualification retries.

## 4. Order, ownership and recurrent crashes

Change planning to a frozen replicate order, finishing remaining designated indices of a small block before admitting the next. With 24 Lengau slots, prioritize the earliest unfinished replicates within the retained 13; EC2 allocates a batch to enough early replicates to fill its 72 work slots, completes their remainders, then advances. Skip validated DONE and **all still-owned live/planned coordinates**. Do not select the fastest completed 60. The new controller should stop planning indices≥80 and the 40 unselected reps prospectively; existing jobs finish unchanged.

Admit the **first prospective Lengau job under the new order alone**, at the intended 24-worker geometry, using new designated coordinates already included in the 897/38 ordinary allocations. Review actual terminal statuses, records/timings, finite resource/memory evidence and current receipts before scale-up. The mixed-replicate pilot does not establish peak behavior when workers concentrate on one replicate. This is intended new work inside the budget, with all existing jobs continuing, not a rerun of an old pilot; keep qualification-metadata rollover separate. Scale-up stays held until that packing/resource review is favourable.

The present partition declaration always creates a suffix across all 100 reps (`row19_partition.py:59–90`). Its k 40 means 160–199; changing k does not create ownership of selected replicates' low indices. Use a new predecessor-linked epoch and a reviewed explicit coordinate-set/remaining-work schema. Archive every historical plan/claim; retain completed provenance, fence/settle transferred uncompleted ownership, activate under the common lock and install/ACK the new inventory. Never erase old claims to satisfy the activation scan. A lower-index coordinate ever planned by Lengau is not automatically transferable merely because its worker died. Let its declared owner finish/rescue it unless a reviewed transfer explicitly handles that history.

**Crash rule: after two same-envelope fatal allocation/signal crashes, do not issue a third identical attempt.** Already-running attempts, including rep 83/index 2's current retry, finish untouched. For a still-missing coordinate use one prospective, budgeted rescue lane: same dataset/seed/folds/chosen-concept index/start policy/numerical environment, lower packing and larger measured headroom, with parity/resource qualification and retained attempt provenance. A compatible high-memory node or 256 GiB host is an option, not a diagnosed cure; confirm its available shape, numerical identity and charged resources before adoption. Keep the 4.5 GiB policy unless a distinct reviewed amendment changes it.

The successful pilot's 2.32 GiB RSS does not bound LLVM/XLA compile transients. The present 4.5 GiB check occurs at resample boundaries, not inside a fit, so it cannot prevent every ENOMEM/SIGSEGV. The records establish that failure signature, not whether its cause is host pressure, cgroup limits, fragmentation or another allocation path.

If the rescue fails or the finite allowance is exhausted, keep the coordinate missing and its interval unavailable; preserve all charges and report the failure. Do not draw a replacement, take the first 80 successes, silently reduce B for this dataset, or label operational missingness harmless. The repeat crasher remains in the proposed 60 IDs. Coverage conditional on successful computation and attempted-set availability must remain visible separately.

## 5. What can be reused and what omega 2 means

Reuse the 493 validated selected prefix records and existing compatible originals, with strict parent identity/checksum/draw validation; add the 136 current in-target claims only when they actually produce accepted records. Keep every nonselected/out-of-prefix record as history, with no new denominator credit. Maintain all comparison variants from the same fits and their same-dataset pairing. No row-19 interval/coverage aggregation was performed for this opinion.

Retain `refit_min_usable=1.0`: all 80 designated resamples must score for the relevant comparison variant to have a usable interval. A valid record reporting a failed scientific fit is not silently discarded to obtain 80 successes. Original failures and per-variant refit failures/reasons remain separate reported outcomes.

Q1's 48 owned coordinates 198/199 lie outside the prefix, even if subsequently released. Q2/S and all parity duplicates remain qualification evidence, never extra independent refits. Do not substitute these high indices for difficult low ones or rerun/rewrite them under new identities to make a count fit. Existing qualification evidence may support the newly reviewed mechanical route only to its demonstrated scope; it does not itself release a new partition/packing.

**Defer omega 2 entirely from this funded screen.** It requires its own interpretable, policy-matched target and tail-sensitive validation design; a smallB 80 experiment cannot inherit omega 1's precision or declare the known unstable omega 2 reference fixed. Do not pool the two settings. The SI may state that omega 1 screening has been amended for compute and omega 2 stress validation is deferred, with no coverage result reported before release. The registered report may state that the method remains unvalidated outside the studied scope; it cannot start confirmation on the claim that a surviving omega 1 screen validated every retained null or the band.

HEAL1922 offers 100,000 hours to 5 April 2027, subject to its recorded distinct-work requirement, a separate ledger and the same user queue limits. It adds hours, not concurrent Lengau cores. **Do not move the same failed screen coordinates to HEAL merely to evade CSCI1913's cap.** A genuinely distinct future stress question might be proposed to its PI/owner and assessed against programme policy, but this opinion does not establish that permission. No HEAL commitment is needed to execute the costed base screen after its other gates pass.

## 6. Adoption and migration checklist — proposals only

1. **Scientific/owner amendment:** `PREREGISTRATION_T1_model.md` §10/10.1, `chpc/ROW19_SCREEN_DECLARATIONS.md`, Unimog `project_knowledge/rsc_t1_simulation_design.md` row 19 and affected scope/budget summaries. Freeze S/order, B = 80-of-parent 200, failure rule, target set/error allocation, one-look outcome wording, finite budgets, deferredomega 2 and later validation obligations. Record exposure and sunk work.
2. **SI pen-holder update:** replace `sections/methods.tex:125`'s unqualified running 100×B = 200 account with the adopted amendment and its date, retaining that the original plan started, no coverage result is yet reported, and the screen cannot establish validation. Do not rewrite historical development comparisons or their policy labels.
3. **Prefix release package and numerical review:** version `row19_screen_release.py`, analysis contract/adoption/pins and fixtures. Validate exact 80-index parent records/identities, original failures and paired variants, no fitting, Kmax/T and missingness guard, only the fixed terminal look. Require the existing independently reviewed RESOLVED numerical target; preserve bank binding and seed exclusions. No numerical release under an old consumer/adoption literal.
4. **Controller/resource package review:** version `row19_screen_admit.py`, status/resource policy, `row19_screen_controls.json` and adoption; freeze desired coordinates/order, current-claim scan, finite retry/rescue route and admission maxima. Record the 81,000 sub-envelope through the existing two-phase cap protocol, never by direct ledger edit. Regenerated qualification metadata/pilot literal may be needed for new controls; no new pilot fit merely for rollover.
5. **Provider epoch and actual-result review:** update partition/allocator/root/ingestion/qualifier/authority consumers (`row19_partition.py`, `row19_ec2_{state,root,ingest,qualify}.py`, AWS manifest/launch/authority files and design/qualification docs). Review canonical activation, ownership history, ACK/fencing, matching release, chosen packing, per-instance sentinels, explicit fleet ceiling and cumulative money/concurrency reservation. Qualify the rescue host/resource path separately if it changes the numerical/packing contract.
6. **Operational migration:** patterned on `chpc/migration_v13/RUNBOOK.md`: drain controller commands, archive actual adopted state, promote/deploy a new controller clone, activate/ACK, obtain fresh whole-role receipts and exact review-bound qualification, then resume admissions. Do not touch running worker/PBS scripts or their numerical tree. Carry the runbook Never list: no worker/reaper stop or restart, manual qualification permission, mutation of reviewed bytes, or pilot refit.
7. **Fresh budget check immediately before adoption/admission:** recompute all programme ledgers/live claims and the current EC2 inventory/baseline under their authorities. The arithmetic here is a timestamped design, not a reservation or a permission token. If any gate, rescue allowance, qualified packing or fleet availability fails, report the hold and obtain a revised costed design rather than relaxing it in flight.

The owner decisions are therefore concrete: adopt or reject this finite omega 1 screen and its limits; accept the proposed funding split/cap amendment and bounded EC2 route/concurrency after review; and keep omega 2/HEAL and the model-study validation gate as separate decisions. There is no permission here to migrate, launch or spend.

## Accounting provenance

Remote records were read beneath `/mnt/lustre/users/pvanrooyen/t1_toolchain/`: `row19_campaign`, `row19_shard_campaign`, `row22_bank_campaign`, `row19_screen_campaign`, `row19_screen_orig_campaign`, `qual_S/campaign`; plans/watch under `row19_screen/`; controller files under `rsc_screen_ctl/workspace_demo/t1_access/chpc/`. Exact private snapshot copies were retained under `/private/tmp/r052_resize_budget_remote_20261017/`. These reads were not a lock-held admission transaction.

Ledger SHA256s in the table's order: `d403a2d1899a3ef6e69f893e90a61905ded77804d08f22d97c556622b2167f76`; `4838dcef01ac83388ce84db57a35663114035c3fbf3dbef4bc4384291e4d5ab9`; `1988aa1fd2145f8a4a37aa8a35899080efb23e6df7bea1c63a23e943c91fabc9`; `5e7039354051814e6f2f726c36e31af40cc346c98946f5a39ca5bc8e91fd8765`; `fe7d1b81f3f8932fc1613840a8b3cac0ea854dccd93b36b4a8b8fda6c7d147bf`; `f0cfdebfffbbdd29498d662c3c5b7bdb42c4ead641664a50bd77e546dbb2692a`.

Saved watch SHA256 `fab0f5f08e11cbe54a6c461082dd9984b27e5be1c2be44c074035a1a3523c3eb`; controller manifest `43b75f94e2d6d2caab5134130ff0fe8bfd2a2d652df49a6124394dfab7b5dc1c`; controls `828d3b69707cc47340c1773b97450c2c17c95679c4daf93c84021d138a4663a5`; concatenated ten live plans `52cf8be7dc0c7fc311aa9bf809cf068b63e9fbebbefe6b52964693c5bb319ad0`. EC2 accounting came from `aws_ec2/runs/inventory/latest.json`, generation 41,01:28:59 UTC. No mutable future file is assumed to retain these bytes.

Three bounded readers checked statistics, programme accounting and protocol mechanics; their findings were reconciled here. Deterministic binomial/coordinate/cost arithmetic is design analysis, not another scientific run. Manuscript, campaign and protected audit material remain untouched.
