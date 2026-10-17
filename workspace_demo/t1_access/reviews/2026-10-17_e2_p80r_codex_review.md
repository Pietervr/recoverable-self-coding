# Row 19: epoch-2 candidate and repaired first-80 consumer — Codex review

17 October 2026. **A: CHANGE 4. B: CHANGE 2.** Neither package receives an adoption or release literal in this review. The explicit ownership split is sound in the inspected scope; the p80 statistical repairs B2–B4 are correct. The changes below concern failure handling, qualification and authority. The separate Lengau migration review and the owner's conditional switch-over approval retain their existing scope.

## Scope and identity

Read the complete committed brief `Unimog-Projects/prompts/2026-10-17_codex_r052_e2_p80r_review.txt` at `56472f8712a340d62ad3c8845f24dccd4bf51ee3`, SHA256 `d1acaaad11525e563c7fa653e8f6bd4af9f7ec6c23359c00247561571a85ff09`. Ownership was recorded at Unimog `730c5c2f10559ba42ec2ea809055d910be4b7f3e` before accepting handoff `b162afe9-baaf-5a2f-8f00-4613b556aa6d` and before review edits. Exact session: `GPT: R052 Entropy paper`.

A is `chpc/candidate_e2/` at RSC `b510ba0e5952eb121a128527bc1c5f180e6e5aed`; B is `chpc/release_p80/` at `9e7e200baa839504537e399c618b0a53a99bee20`. B consumer SHA256 is `bef5d79e3e93a09ad204f26bc84d5bfadece5adb31885d8483086290b44f58cf`, tests `a8e8cd9271772c1e6f3bc1fbb7ca8fe39a423d2689eeb67668fb613335b3e4a6`, contract `a9b09dcc7369ba059b0de271411d4720b24a8762c5ba55d7f2c885a52eac8495`. Paths below are relative to `workspace_demo/t1_access/`; line numbers refer to these reviewed bytes.

The intended system retains every existing Lengau claim, assigns only designated unclaimed prefix coordinates to a new predecessor-linked EC2 epoch, and preserves the B200 producer identities while screening a fixed B80 prefix. Neither a partial EC2 bundle nor a terminal certificate may manufacture a scientific failed fit. A missing coordinate remains missing; its resource disposition and authority must be established before the one terminal look.

## A. Epoch 2 — changes required

### A1 — P2: censoring can override an explicit HELD/resource failure

`candidate_e2/row19_ec2_ingest.py:220–224,240–253`: `_left_status` permits any status exit when the outcome is the censor string. Thus a present LEFT status with exit 4 and a memory/identity guard can be accepted as routine unproduced output instead of holding the attempt.

A private counter used the literal deadline-censor outcome, no record/timing, and a matching LEFT status with `exit:4`, reason `memory: maxrss above the stop`, maxrss `1000000000000`. The actual candidate ingester returned 0, published the other valid work slots, marked the attempt ingested and fenced/released the censored coordinate. This is a plausible producer ordering: `aws_ec2/prod_userdata.sh:130,148–150,158` snapshots absent wrapper exit files, gives that censor label precedence, then copies statuses later. It need not be an invented operator label.

**Fix:** separate absent status from present status. A present status must satisfy the exact task/coordinate/accounting checks and an allowed orderly deadline/STOP exit/reason. A HELD exit or contradictory resource/identity status holds even under a censor marker. Bind the producer's censor/outcome evidence; test censored+exit4, wrong identity and malformed LEFT accounting. This defect does not create a false scientific record; it hides a known contract failure from the continued-packing decision.

### A2 — P2: ingestion's fatal-signal set and the two-crash counter disagree

Ingestion `:245–247` accepts no-status exits 129–159. `candidate_e2/aws_ec2/prod_authority.py:130–131,375–392` counts only `{132,134,135,137,139}` toward crash exclusion; allocator `:276–285` can therefore issue a third identical attempt after other accepted fatal signals.

The private counter ingested exit133 and performed a real private Mac ACK. Two acknowledged same-envelope exit133 entries produced an empty exclusion set, and allocation selected the coordinate again. The second entry was a copied acknowledged fixture with a new attempt/sequence, a direct counter-rule proof rather than a claim of two live ingestions. SIGTRAP/133 and SIGFPE/136 are fatal signals, not orderly deadline exits.

**Fix:** share one reviewed classification between ingestion and crash exclusion. Every admitted coordinate-specific fatal allocation/signal category must count toward the no-third-identical-attempt rule, or hold until its disposition is established. An external-interruption exemption needs evidence of that cause. Test 133/136/138 through ingestion, ACK and subsequent allocation. Exit137 proves SIGKILL; describe OOM only when host evidence establishes it.

### A3 — P2: E2Q1 does not qualify the allowed production concentration

`candidate_e2/QUALIFICATION_E2.md:44–50,65–71` puts 52 work plus 9 duplicate workers on rep24: **61** workers on that replicate, with the other duplicates elsewhere. Ordinary production already puts 69 work workers on rep24 in batch1. A deterministic replay of the declared owned set also gives **70** work workers on rep69 in batch27 and rep70 in batch28, before any same-replicate sentinels. Skips/retries can alter the boundaries further.

Ten samples with all 76 workers running do not establish peak behavior at an untested concentration. Existing mixed-replicate e1 memory evidence does not supply that implication either.

**Fix:** declare a qualification that covers the actual allowed worst production shape, including sentinel contributions and simultaneous occupancy, or constrain production to the qualified shape and re-cost/review it. A fixed resource panel and a fixed parity panel are possible within the existing bounded allowance if specified before outcomes. R1' parity remains valuable; calling its 61-worker concentration the production packing is insufficient. This is a deficient qualification plan behind an unbuilt fail-closed release gate, not a demonstrated current launch escape.

### A4 — P2, bounded: funding validates against its own unauthenticated basis

`candidate_e2/aws_ec2/prod_authority.py:334–345` rederives the funding declaration using the Q2 basis supplied by that same declaration. `make_e2_funding.py:22–26,39` reads the ledger at construction, but admission does not authenticate that construction input or bind the exact reviewed funding bytes.

A pure private probe doubled the Q2 charge to 23.401608, coherently regenerated the declaration and obtained `funding_problem == ''`, with an epoch cap 3857.04 instead of 2078.52. Single-field tamper tests do not cover this case.

**Fix:** bind the exact reviewed funding declaration/basis in the final release authority and verify it at admission, or rederive from the pinned reconciled Q2 attempt with fixed declared 24/23 counts. The future release branch can supply this binding, but it is not built yet. The global USD 2300/3000 caps, fleet cap and 50-production/2-qualification counters still hold. At the fixed declared per-attempt cost the counters bind earlier than the epoch cap. This is neither unlimited spend nor proof that an extra production dispatch currently passes.

### A follow-up requirements and known holds

**P3, replay provenance:** ingestion `:330–344,431–436,455–468,486–488` journals outcomes/unproduced slots but does not require the replayed bundle's failure evidence to equal it. A completed replay after changing exit133 to the censor string and regenerating bundle checksums returned 0 while the register retained 133. The original journal still governs; no late scientific record or ownership escape was demonstrated. Before R5 acceptance, freeze the bundle/outcome and relevant missing-slot status/censor evidence and compare it on incomplete and completed replay. Revalidate fences without requiring a coordinate legitimately completed by a later attempt to remain absent.

**P3, final lifetime binding:** `make_prod_manifest.py:34–45` enforces the funded 22 h lifetime, while launcher `prod_launch.py:265–270` fixes lifetime only for old Q1/Q2. Final e2 release/admission must bind the exact qualified operational manifest/lifetime; use of the maker alone is insufficient authority. No current positive e2 release path was found.

The documented holds remain genuine: controls v17 and helper pins/print-line repair; fresh post-v16 partition/funding review; e2 contracts, schema-3 certificate, qualifier and release branch; actual-result review/release adoption; actual Q1 attempt 4 disposition/fence; R6 tests and capacity evidence. The current qualifier refuses e2. The crashed e1 Q2 cannot provide the old certificate, and neither retired e1 evidence nor manual permission can substitute for e2 qualification. These are unfinished prerequisites already identified by the builder, not additional discovered launch escapes.

## A. Rulings on choices 1–13

1. **Claims source:** accept `lengau_claims`, preserving records and every historical plan/claim. Final bytes require a fresh Lengau snapshot/receipt after v16 is active, regeneration/`verify2`, and exact declaration/funding review. The `snapshot` command itself (`row19_partition.py:680–690`) does not acquire the plan lock despite the text; the eventual command wrapper must actually acquire it or the command must implement it. Activation rescans under the lock, and v16 closes new claims on those EC2 remainders, so no overlap escape was demonstrated from this omission.
2. **Unchanged designated declaration:** accept. The separately adopted epoch binds its digest and owns the explicit coordinate set. Structural `load` is not a replacement for snapshot-derived `verify2`.
3. **Retire e1 without transfer:** accept. Keep its 4000-coordinate history and Q1/Q2/S evidence. Disposition/fence Q1 attempt 4 before activation; erase no claim or proof. No hand-back to Lengau is authorized.
4. **Stricter activation:** accept. Predecessor activation, current fresh installed inventory, no outside owner, no other-epoch live attempt and an under-lock current-claim scan are appropriate. Q2 owns no work. No ownership bypass was found in these paths.
5. **Ascending replicate-complete allocation:** accept mechanically, conditional on A3. The exact replay covers 3274 coordinates once and retains 486 Lengau claims on the 47 EC2 reps. Qualification must cover what the allocator can actually pack.
6. **Token sentinels:** accept deterministic selection from completed non-owned coordinates, independent of results. They monitor parity; they are not a reference for every work replicate. Report their actual replicate concentration. Every produced sentinel must match; a mismatch holds both providers.
7. **Partial-slot publication and 7/3 bounds:** accept in principle after A1 and the replay repair. Validated produced slots can be retained while missing slots are fenced/released without imputation. The limits are prospective operational choices requiring adoption/qualification, not statistically established safe rates. Nine crashes among about 807 new Lengau coordinates are not an IID 76-slot production cohort; `0.989^76≈43%` and `(23/24)^76≈4%` are independence illustrations, not measured batch-completion forecasts. Deadline censoring is not successful resource qualification. R4's stricter≤3 total non-completions must be implemented explicitly.
8. **Two-crash rule:** change per A2. Same-envelope fatal allocation/signal failures cannot evade the cap merely because a signal number was omitted. Censoring/external interruptions still consume bounded attempts/money. With no EC2 rescue route, excluded coordinates remain unresolved.
9. **Allowance accounting:** accept non-rejected sequence counting, worst-case reservation until reconciliation,≤46+4 production attempts,≤2 qualification instances and a common USD 300 allowance. Repair A4. Capacity rejection is not a purchased instance and does not justify outcome-based qualification retries.
10. **Five-instance ceiling:** accept counting intent/launched/ambiguous production and qualification across epochs. Five declared unresolved instances reserve about USD 139.59 cumulatively; a sixth refuses. Existing benchmark exclusion remains separate authority.
11. **Q2 basis/forecast:** accept the declared 23/24 basis as a transparent planning proxy after authenticating it, not a demonstrated 76-worker cost/throughput model. USD 1778.52 and the 2078.52 cap retain that limitation. `ceil(46/5)×21.2811/24=8.87` service days is conditional on five available instances and qualified packing, before capacity/interruption/qualification/review delays.
12. **E2Q1, no S, optional R3':** change packing per A3. Fixed 15/20 successful exact cross-platform comparisons, validity-only new work and no additional fresh-host repeat are otherwise reasonable in the stated scope; the retired e1 repeat remains descriptive. No producer-host restart claim follows. Candidate ingestion currently allows partial mode only for schema2 production (`:396–407`), so future E2Q1/R5 code must exercise the actual production branch deliberately. Removing a completed slot's files while leaving outcome 0/status-done is not a valid synthetic censored fixture. Label and bind every synthetic modification. Failed/INCONCLUSIVE qualification is not retried by outcome; the one external-cause retry remains bounded.
13. **Five reapers, one ledger:** the static lock order is consistent: global authority lock, then run lock, ledger reload before reconciliation/inventory. No lost-update defect was demonstrated. Current 54 checks use helper dictionaries/source wiring, not five concurrent admissions/reapers. R6 remains required: interleave five stubbed admissions/reconciliations, prove unique sequences, retained sibling changes, immutable monotone inventory generations, cumulative reservations and sixth-admission refusal. Quota arithmetic 512≥480 does not establish spot capacity. No AWS query was made.

## B. Repaired p80 consumer — changes required

### B-R1 — P2: different adoption reads can supply different authority

`release_p80/row19_screen_release_p80.py:323–344` invokes the inherited seal, then rereads the adoption for prefix/review checks. `:785–791` rereads it again for terminal authority, whose controller pins and manifest identity checks (`:420–449`) consume this last object.

Private control-flow evidence changed the adoption after a controlled successful-seal boundary: the actual terminal checker rejected the certificate against the checked object, but accepted it against the reread replacement. The numerical seal and collection were stubbed, with collection forced to hold; no numerical target, record collection or release was produced. This proves a check/use mismatch, not an arbitrary unreviewed-certificate bypass: the exact certificate still needs its independent review.

**Fix:** one immutable adoption byte snapshot, verified tracked/unmodified and equal to its intended committed blob, parsed once and passed through inherited seal, prefix/review checks and terminal authority. Extend the inherited seal with that optional snapshot as it already accepts the one-read target. Fixing only the final read leaves the earlier checks inconsistent.

### B-R2 — P2: newest receipt validity is not checked

`row19_screen_release_p80.py:501–508` checks schema/role/production/zero alarms for the certificate-bound receipts. `:511–516` reads the newest receipt without those checks; `:552,594–595` compares only extracted crashes for the certified coordinate. The inherited numerical seal has no current-receipt check that closes this gap.

A private fixture retained the exactly reviewed old certificate/receipt and added a newer receipt with wrong schema, `production:false`, alarms `['INVALID PROVENANCE']`, and the same crash list. Actual `terminal_authority` accepted it with no problems. The older certificate's review cannot give this newer invalid evidence authority.

**Fix:** validate the newest receipt's schema, role, production, identity/bindings and alarms; refuse malformed, foreign or alarmed current evidence. Freeze its bytes and establish the reviewed state or a validated successor relationship, rather than equality of one parsed sublist alone. This concerns certified prefix coordinates; it does not require unrelated workers to stop. The fixture used synthetic enabled rescue and `check_git=False`; it demonstrates the future terminal-validator gap, not a certificate passing today's disabled-v16 declaration.

## B. Disposition of B1–B4 and the six unresolved choices

**B1:** substantially repaired. The free-form declaration is replaced by immutable certificate/review/controller snapshots, an exact separate review literal, identity/pin checks, controller crash history, settlement equality and outstanding-ownership refusal. Missing originals remain uncertifiable. B-R1/B-R2 must close the remaining authority-consistency gaps. Synthetic favourable review text is not an independent-review bypass.

**B2:** repaired. `Kmin≤K(theta)≤Kmax` for a fixed theta in T; monotonic limits give only `L_CP(Kmin,n)..U_CP(Kmax,n)` and the conservative attempted-set corners. One-sided 98.5% each gives two-sided 97% conditional on the target/binomial assumptions; nominal bank 1% makes the descriptive joint bound up to 4%. The primary directional futility error remains 1.5%+1%=2.5%, with the all-attempt missingness guard. Opposite adaptive corners are no longer represented as exact bounds.

**B3:** repaired. Cluster has a labelled descriptive companion report, pairing/containment counts and no formal decision/error allocation.

**B4:** repaired. Symbolic open segments and closed endpoint counts handle adjacent floats, ties and large finite values without midpoint rounding/overflow.

The unchanged core remains correct: fixed 60 IDs; every index 0–79 validated against the unchanged B200 parent, never first 80 successes; all 80 usability; finite-B80 procedure; one terminal look; refit-only dual futility test; n0 unresolved; never PASS. No B200/infinite-B coverage guarantee is implied.

The six certificate choices are ruled as follows:

1. **No current certificate under rescue-disabled v16:** correct. Disabled is a hold, not exhausted permission. A fully complete prefix needs no certificate or rescue amendment, once the numerical-target/consumer prerequisites hold.
2. **Provisional `route:"rescue"`:** acceptable only as a future interface. Its separate reviewed amendment must define/adopt the marker, qualified resources, attempt/settlement provenance and unsuccessful outcome, or change/re-review this consumer. A marker plus settled/no-record is not already-qualified rescue integration.
3. **Reservation exhaustion:** acceptable as an explicitly adopted finite attempt/reservation quota. Two reserved requests need not have consumed their reserved core-hours to exhaust such a quota; small settlements do not automatically buy more attempts. The future amendment must state whether it means two attempts, cumulative reservations or actual spent hours. At `:649` the code prices the next **ordinary** envelope; that is valid only if it equals the adopted rescue request's full reservation. Otherwise use the rescue envelope. Do not claim charged-hour exhaustion or enable the branch before that contract exists.
4. **Hash-bound receipt evidence:** acceptable with an independent exact certificate review that validates receipt/plan/PBS/settlement provenance. The code does not prove admission previously judged those exact bytes; `crash_history` parses dispositions rather than rederiving them. Private minimal/cross-plan fixtures demonstrate what the reviewer must establish, not an unreviewed-authority escape. B-R2 still applies to newer evidence outside that review. The separate tracked terminal-review record is a reasonable way to review a later exact certificate without changing numerical-target adoption.
5. **Later adoption read:** change per B-R1.
6. **Synthetic B1 fixtures:** useful branch tests, not actual controller/rescue integration. The enabled rescue declaration and envelope resolver are synthetic. Their 131-test claim does not qualify a future rescue producer or its resource/accounting contract.

No favourable p80 literal is supplied for `bef5d79e…`. After repairs/review, eventual target-specific adoption must use the actual independently reviewed RESOLVED target, repaired consumer pins/contract, actual adopted controller/controls/designated bytes and inherited seal dependencies. A missing-coordinate certificate needs its separate exact review and implemented adopted rescue/quota contract. A placeholder target digest is not adoption authority.

## Verification, limitations and handoff

Three bounded readers independently inspected provider/ingestion, authority/qualification and terminal/statistical mechanics. A's authority 54/54 was reproduced on private copies with process/network/scientific-import/write guards. Metadata replay confirmed 46 ordinary batches and the 70-worker concentration. Targeted private real-ingester/ACK probes reproduced A1/A2 and the replay provenance gap. B's source/tests/contract hashes match; nine deterministic checks of AST-extracted pure functions passed: adjacent gaps, ties, large values, sandwich, CP cutoff, missingness veto, one-look guard, n0 and cluster no-decision. CP upper bounds at 47/48/49 of 60 are 0.8871870601/0.8996154975/0.9117490072. Administrative-only probes reproduced B-R1/B-R2.

The saved partition 54/54, ingest 22/22, eight equal live/candidate regression pairs with three pre-existing failures, and B 131/131 are builder results; this pass did not independently rerun those complete suites. In particular the B fixture retains real `simulate.make_dataset` and temporarily writes beneath `reviews/`, so it was not run unmodified under this no-scientific-draw assignment. Pure/guarded counters do not prove actual 76-worker resources, five-way reconciliation, real rescue integration, actual numerical release or cloud capacity.

Private audit artifacts: `/private/tmp/r052_e2_authority_qualification_review_20261017.md`, `/private/tmp/r052_e2_authority_audit_20261017.py`, `/private/tmp/r052_e2_provider_ingest_review_20261017.md`, `/private/tmp/r052_e2_ingest_probe_20261017.py`, `/private/tmp/r052_e2_p80r_release_review_20261017.md`, `/private/tmp/r052_p80r_metadata_checks_20261017.py/.json`, `/private/tmp/r052_e2_p80r_pure_checks_20261017.py/.json`. These are temporary review evidence, not additional scientific outputs.

No package/live/controller/ledger/partition/manuscript edits, numerical release, fits, scientific model draws, AWS/Lengau/scheduler/transport operations, worker/reaper actions, worktrees or push. Foreign migration repairs were preserved and not reviewed as part of this brief. Source Claude/owner retain implementation, declarations, migration and dispatch. Reconsider repaired exact bytes; current e2 production and p80 release gates stay closed.
