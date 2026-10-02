# R052: two-channel framework addendum second opinion

**Date:** 2 October 2026 UTC / 1 October 2026 America/Phoenix.

**Reviewer:** GPT: R052 Entropy paper, native session `01a0d19e-2127-7051-9a61-6db771088559`.

**Brief:** Unimog `prompts/2026-10-02_codex_r052_framework_addendum.txt` at `6d421aea77a7df9f321bc07c0cd211a32e0de64e`, SHA-256 `bd272074007264c7f1c389da86dbf26db312e93ee308cbb0e5fc5b50b040aeb3`. Handoff `855f73ec-27e5-5fd5-aaf7-831097ecbca5` accepted after ownership commit `abd79016`.

**Reviewed document:** Unimog `project_knowledge/rsc_t1_two_channel_framework.md`, draft 1 including the later section 10 at `e8ed09ba`; SHA-256 `28571a7ab42badf905cdca6642ad55c26aa4501a0015e247fbe5e86f881d18bb`. Read it in full, the relevant protocol sections and the paper's transfer argument. Mark-ups below belong to the author; no framework, protocol or stimuli file was edited.

**Overall: ON BOARD with a controlled two-channel recognition study; NOT ON BOARD with draft 1's CAPTCHA/ignition argument, inherited calibration language or ambiguous modality-independence prediction.** The four headings can organize the study after their tests and outcome readings are repaired. CAPTCHA success motivates studying recognition under degraded input; it does not measure conscious access. Geirhos is a valuable behavioural reference, with the scope and source corrections below.

This is a separate addendum. The [completed image-channel opinion](2026-10-02_image_channel_design_codex_record.md), RSC `fa24db8`, its seven answers and one delivery remain closed. The dedicated assay brief `08df1dbd-8cbc-5160-a863-e9e7a52cfb37` is a separate handoff; this record does not claim to have accepted or completed it. No image bank was built, photograph transformed, inference/capture/simulation run, human response data loaded, CAPTCHA attempted, account operation performed or push made. Primary papers, source code and release metadata were read only.

## 1. CAPTCHA motivation: retain the question, replace the claimed experiment

**ON BOARD as motivation; NOT ON BOARD as a field test of ignition.** A security challenge is judged by operational acceptance under a changing protocol. A human identification report may involve conscious perception, but CAPTCHA datasets do not identify a perceptual threshold or measure trial-wise neural states. A checkbox/reputation decision may occur without a visual report. Neither the original security objective nor the quoted studies establish that the designers assumed a graded machine representation.

The framework's two headline rates compare different tasks and denominators. Sivakorn and Gottlieb report **463/500 successful sessions (92.6%)**, permitting up to 20 challenge attempts/session, from a CLIP/OWLv2 pipeline. It is not a 92.6% single-image, single-pass Qwen result. Zero-shot concerns no weight fine-tuning: offline labelled challenges were used for model selection and parameter tuning. Their failed-session table also has an inconsistent challenge-count summary; the 463/500 denominator itself agrees. Searles et al.'s **50–84%** range concerns distorted-text case-sensitive agreement used as a correctness proxy; their image-reCAPTCHA estimates are about **81–81.7%**. These are not paired human/model curves over common calibrated strengths. [Robot Visions](https://arxiv.org/html/2609.18518v1), [Searles paper](https://www.usenix.org/system/files/usenixsecurity23-searles.pdf)

Bursztein et al.'s over 318,000 observations are **human annotations**, with repeat judgments over 13 distorted-text and eight audio schemes, not that many verified successful modern object-grid solves. Google introduced challenge-free adaptive scoring in **October 2018**; v2 already uses other signals. Behavioural scoring did not begin as a response to the cited September 2026 result. Cloudflare documents visual-puzzle-free checks and explicitly separates completed challenges from established humanity. [Bursztein primary paper](https://web.stanford.edu/~jurafsky/burszstein_2010_captcha.pdf), [Google announcement](https://developers.google.com/search/blog/2018/10/introducing-recaptcha-v3-new-way-to), [Google versions](https://developers.google.com/recaptcha/docs/versions), [Cloudflare challenges](https://developers.cloudflare.com/cloudflare-challenges/), [Cloudflare outcomes](https://developers.cloudflare.com/turnstile/turnstile-analytics/challenge-outcomes/)

Replace the paragraph with a bounded motivation:

> CAPTCHAs were designed to exploit differences between human and automated recognition. Reports of successful automated solutions to degraded-image challenges show that recognition performance alone cannot identify the internal process producing an answer. We therefore test one fixed multimodal checkpoint under a declared physical image-strength manipulation, asking which registered conditional-density family predicts its content-related readouts and whether interventions establish their use by the answer path.

This replacement makes no claim that CAPTCHA designers proposed a consciousness test, that aggregate success reveals a psychometric crossover, or that any threshold is a workspace ignition. The study tests specified distributional alternatives; a mixture win does not rule out every graded process. Keep the CAPTCHA work as a field motivation, separate from the human experimental anchors and the SI audit.

## 2. Data, dose and image terms

**ON BOARD with Geirhos as a behavioural/degradation reference; NOT ON BOARD with treating its curve as the human curve for new THINGS stimuli or the model's internal readout.** Keep the two collections distinct:

| Collection | Verified human design |
|---|---|
| Geirhos 2018 | 82,880 trials across twelve experiments, usually five/six observers per experiment (three for colour). Images were often 256-square. |
| Geirhos 2021 / model-vs-human | 85,120 trials across 90 observers and 17 datasets: twelve adapted distortion datasets plus sketch, stylized, edge, silhouette and texture–shape cue conflict. New human collection for the twelve sets, shared images across observers,224-square crops. |

Both use **16-way basic-category identification**, brief 200-ms presentation followed by backward noise masking; 2018 specifies a 200-ms 1/f mask. They do not supply EEG or subjective seen/unseen judgments. The later paper limits its conclusions to that brief presentation regime. “Twelve graded degradations” is inaccurate: three are binary, rotation has four orientations, and the remaining series have seven/eight levels. Salt-and-pepper model-training noise has no corresponding human comparison curve. [2018 primary paper](https://proceedings.neurips.cc/paper/2018/file/0937fb5864ed06ffb59ae5f9b5ed67a9-Paper.pdf), [2021 primary paper](https://arxiv.org/html/2106.07411v2)

Useful dose definitions, not interchangeable calibrations:

- **Uniform noise:** grayscale, nominal 30% contrast, pixelwise `U(-w,w)` noise, then clipping to [0,1]; widths `{0,.03,.05,.1,.2,.35,.6,.9}`. This is the closest structural analogue to Sergent's masking, but width is not delivered SNR in dB or equal-RMS signal normalization.
- **Contrast:** `0.5+c*(grayscale-0.5)`, with `{100,50,30,15,10,5,3,1}%`. This is closest to Melcon's manipulated variable. It has no zero/blank catch. Noise-width zero means the signal with no added noise, not no target.

Neither grid supplies the proposed target-free endpoint. Changing normalization, noise spectrum, clipping, geometry or endpoints creates a new physical-dose definition. [Original transform code](https://github.com/rgeirhos/generalisation-humans-DNNs/blob/master/code/image_manipulation.py), [benchmark grids](https://github.com/bethgelab/model-vs-human/blob/master/modelvshuman/datasets/experiments.py)

A model pass has no 200-ms viewing limit or human backward-masking dynamics. Its answer set is not these 16 broad categories; fine concept naming has different priors/chance and may require within-family distinctions. Applying the same transform to THINGS supports a comparable corruption definition; it does **not** transport the published ImageNet identification curve. Freeze the transform and use new CAL/PILOT measurements on the intended concepts. If human/model curves are compared directly, they need shared stimuli, response task, geometry/dose, averaging and uncertainty units, with participant versus concept/photo variation stated. Treat Sergent/Melcon as distinct neural-task anchors, not as evidence that all degraded-image recognition has two states.

**Terms: distinguish code, responses and photographs.** model-vs-human's own toolbox code is MIT; its overview sends the twelve ImageNet-derived image sets to ImageNet access terms, with noncommercial research/education limits and no warranty of image rights. Original 2018 code carries CC BY 4.0. The inspected overview does not explicitly identify a separate licence for trial-response files. Do not label the whole bank “MIT.” [Benchmark licence overview](https://github.com/bethgelab/model-vs-human/blob/master/licenses/LICENSES_OVERVIEW.md), [code licence](https://github.com/bethgelab/model-vs-human/blob/master/licenses/CODE_LICENSE), [2018 licence](https://github.com/rgeirhos/generalisation-humans-DNNs/blob/master/LICENSE.txt), [ImageNet terms](https://image-net.org/download.php)

Original THINGS release terms expressly restrict modification/distribution without the owners' consent. The proposed noise/contrast capture basis remains unresolved until an appropriate grant or documented use basis is established; this is a release-policy gate, not a universal legal conclusion. THINGSplus releases one CC0/public-domain photo per concept, with a possible-misattribution caveat; check per-image provenance and qualify the actual views. Hov's public folder establishes 995 exemplar 1 photos, not a second released view or unrestricted image rights. Their release counts do not prove an accepted E1/E2/role-compatible bank at the required P. Prefer cleared originals and transformed inputs reproducible for exact stimulus figures; label a substituted CC0 illustration explicitly. [THINGS terms](https://osf.io/download/52wrx/), [THINGSplus notice](https://osf.io/download/ahg2k/), [prior source analysis](2026-10-02_image_channel_design_codex_record.md)

### Is there human threshold work on THINGS photographs?

Do not state that none exists. Two relevant primary candidates were found:

| Candidate | What it establishes, and why it is not a direct replacement |
|---|---|
| Rideaux et al. 2022 | Detection of added oriented wavelet filters on THINGS photographic backgrounds, three author-observers, five amplitudes including zero plus alignment/target-number manipulations. Observers locate added filters between images; they do not identify the photographed object. No trial-data release statement was found in the inspected paper. Relevant detection psychophysics, a different target. [Paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC8762697/). |
| Linde-Domingo et al. 2026, THINGS-Mooney | THINGSplus-derived Mooney objects;947 retained participants, subjective identification/naming before/after the clear image, response-limited or five-second viewing. “Threshold” means pixel binarization, not an SNR/contrast visibility staircase. OSF node `mzp23` documents data/code with CC BY 4.0 metadata; author MIT code documents CC0-source images and aggregate image naming measures. A useful related recognition resource, without a graded noise/contrast grid. [Paper](https://www.nature.com/articles/s44271-026-00441-8.pdf), [OSF metadata](https://api.osf.io/v2/nodes/mzp23/), [author release](https://github.com/wobc/things-mooney), [codebook](https://github.com/wobc/things-mooney/blob/main/variable_description.md). |

Six THINGS-specific threshold/masking searches, the initiative catalogue and these candidate methods did **not verify a directly compatible human THINGS object-identification dataset across calibrated SNR/contrast levels**. This is a bounded search result, not evidence of nonexistence. Ordinary nameability, RSVP decoding and pixel binarization thresholds must not be renamed near-threshold object access. No human trial-response files were opened or decoded.

### CAPTCHA banks

**NOT ON BOARD with adopting these as the arm's stimuli or human anchor.** The metadata check yields:

| Release | Qualification consequence |
|---|---|
| `recaptchav2-29k` | 29,568 cropped images and five labels; no controlled human dose curve documented. MIT repository card separately says Google owns images and asserts educational/research fair use, without linked owner permission. That is uploader policy language, not per-image clearance. [Card](https://huggingface.co/datasets/nobodyPerfecZ/recaptchav2-29k/blob/main/README.md). |
| Dataset Ninja Google Recaptcha Image |11,730 images in 12 categories, poor-quality annotations noted. CC0 label is accompanied by a disclaimer of rights over original content and a requirement to check source permissions. No controlled human dose curve documented. [Page](https://datasetninja.com/google-recaptcha-image). |
| CAPTURE | **Human evaluation exists:**25 testers verified initial model annotations and then solved 25 CAPTCHA types; aggregate Human Acc. is reported. No controlled per-image near-threshold grid/curve is documented. Article CC BY 4.0 is not a recorded grant over underlying vendor/site images; no dataset-specific image terms were found in the inspected paper. Its heterogeneous tasks are not all a few object concepts. [Paper §§3.2–3.4/Table 6](https://arxiv.org/html/2512.11323v1). |

Use “no controlled per-image near-threshold dose curves documented,” not “no human data.” No archive was downloaded or usable bank counted. These benchmarks do not replace the required concept/sense/exemplar provenance, image audit or registered population.

## 3. Four predictions: keep the structure, specify the gates

**ON BOARD with statistical / target bridge / causal use / cross-channel conjunction as four headings. NOT ON BOARD with the current compressed tests.** [Protocol §§2, 6, 8, 9, 11](../PREREGISTRATION_T1_model.md) makes several distinctions that draft 1 omits:

| Heading | Required declaration and interpretation |
|---|---|
| (a) Statistical | Per arm, the selected-family held-out R1 score difference averaged over the fixed 23–57 layer grid, with a calibrated interval. Positive excludes zero = specified mixture support; negative excludes zero = specified graded support; includes zero = inconclusive. Do not select a peak/layer on CONF. |
| (b) Target bridge | Not merely an R2 family win: require target-versus-matched-C1 separation (§6.4(i)), R2 mixture support under the same registered comparison, and positive R2 high-versus-low separation at fixed dose using held-out R1-assigned states (§8.5(b)). A missing bridge leaves an R1 coherence result; it is not a capture failure. |
| (c) Causal use | The registered joint-swap interaction with held-out state, its positive 95% interval and 0.5-nat point-estimate SEOI; sham/off-target 90% intervals within±0.25 nat, low-state positive-control sensitivity and declared amplitude/norm policies. Positive-control failure means H3 not testable. If the smooth score account predicts as well or better, do not write “two-state causal mechanism.” H1 with unsupported H3 means use not established by this intervention. |
| (d) Cross-channel | Recommended primary: a bounded **both-arms-mixture/content conjunction**, (a) and(b) passing in both arms, in the same fixed band. Passing(c) in both arms determines the stronger causal tier. Report each component result. This is a shared assay description on this checkpoint/design, not modality independence of a mechanism, equality of parameters or identical peak location. |

Calling (d) “the same description, two-state or graded” makes graded/graded satisfy it while both workspace mixture predictions fail. Replace that ambiguity. For fully qualified arms, let M/G/I denote positive/negative/inconclusive calibrated R1 evidence; preserve bridge and H3 flags separately:

Declare the claim ladder explicitly: passing (a) in both arms establishes statistical replication; adding (b) in both permits content-related replication, the recommended primary (d); adding (c) in both permits the stronger registered causal-use claim. Freeze that hierarchy before CONF. Passing a weaker tier never grants the stronger language.

| Arm verdicts | Reading of the bounded both-arms-mixture prediction |
|---|---|
| M/M, both bridges and causal prerequisites pass | Content-related conjunction and stronger causal tier supported under the registered families, populations, band and instruments. No shared-mechanism/equivalence claim follows. |
| M/M, at least one bridge missing | Statistical agreement only. Content-related conjunction unsupported and H3 gated by the missing bridge. |
| M/M, both bridges pass, H3 unsupported/unavailable | Content-related conjunction supported. Report causal use as unestablished or not testable, respectively; retain successful component interventions. |
| M/G or G/M | The bounded conjunction is contradicted under the qualified instruments. This does not locate a threshold within the system or explain the discrepancy. |
| G/G | Both arm-specific mixture predictions are contradicted under the qualified instruments. Agreement in graded verdicts is not support for the workspace mixture conjunction. |
| Any I with no G | No decisive conjunction. Inconclusive is not graded support. |
| Any G with an I | The G arm contradicts the all-pass prediction; the other arm remains inconclusive. |
| Any required instrument/control/fit unavailable | The content/causal cross-channel test is uncompleted at that gate. Preserve any valid component finding and its limits; do not relabel missing evidence as a biological falsification. |

The last row also handles an unqualified image lens despite successful independent image recognition. A valid G component still contradicts the statistical both-M prediction even if the other component is unavailable; do not erase that evidence. Keep pipeline availability distinct from the scientific absence of a bridge. A mixture density may describe a scalar readout without identifying an all-or-none workspace state. Vision preprocessing/encoder nonlinearities, photograph heterogeneity, the chosen projection and the shared answer bottleneck remain alternatives.

For one all-pass conjunction, calibrated level-α component tests permit an intersection–union bound ≤α even when paired/dependent. That does not validate the components themselves: nominal 95% intervals with a 0.90 inclusion acceptance floor do not alone prove a 5% decision-error guarantee. Specify multiplicity for the claim tiers, separate successful-arm claims, multiple degradations, readouts, bands and optional analyses. A stronger equality claim needs a paired estimand and a numerical equivalence margin; non-significant channel difference or two same-sign intervals is insufficient.

## 4. Table and transfer corrections

| Draft location/statement | Mark-up |
|---|---|
| §3: “both channels therefore read ... the same ... band and lens” | Same weight artifact and downstream architecture permit a proposed probe. Native vision execution is absent from the current capture path; lens transport and useful band location are qualification questions. Preserve snapshot identity and add the changed execution manifest. |
| §3 readouts row | R1/R2 are at the last END marker token; R3 is at the last answer-suffix token; H3 edits three marker positions and measures downstream answer logits. H3 is an intervention test, not a third scalar readout. Include R3 in the table. Expanded image sequence/grid/M-RoPE must determine positions. |
| §3: variability has the EEG design's “own source” | A deterministic checkpoint varied by externally randomized photographs/noise is not repeated intrinsic human neural variability. Declare concept→photograph→mask→dose/carrier/layer hierarchy and source dependencies. |
| §5: THINGS for captures, THINGSplus for publication | Transformation/use terms must be resolved before original THINGS adoption. Prefer individually checked cleared images for initial capture and exact reproducible figures. A substituted CC0 photograph is an illustration, not the captured stimulus. |
| §5: “nothing from the sources is redistributed” | Define a rights-compatible release plan by artifact. Restricted original norms/photos differ from releasable code, manifests and cleared transformed stimuli. A blanket statement does not supply reproducibility or discharge image-use terms. |
| §6: components/procedure transfer “untouched” | The old audit remains a historical result under its generating designs. The five are questions to reassess; they do not certify arbitrary image distributions. Reassess photo effects, dose link, conditional independence, fitting/recovery, estimand/learning variability, interval and band covariance. |
| §8.2: one-layer 16-concept pilot; a fail stops the channel | Use the prior staged fidelity and independent instrument pilot. A failed adapter, probe or grid stops that version and leaves the instrument unqualified; it does not disprove visual representation. One layer cannot qualify a 35-layer band. |
| §10: decoder “trained to be monotone in the dose” | Endpoint logistic classification does not constrain interior-dose responses to be monotone. It learns a separating direction; image-quality discrimination can occur without content identification. |
| §10: all mixture members enforce catch occupancy zero | The retained `M3L` allows free catch occupancy. Dose encoding and endpoint rules must preserve the actual member definitions. A noise-only endpoint is not finite SNR in dB. |
| §10: encoder/band readouts “tell the two apart” | Declare where dose is applied and where the signal is read. Encoder and band observations can diagnose propagation/differences; they do not by themselves locate the causal origin of a threshold. Do not assume the encoder already has a two-state threshold or apply a decoder-layer lens to an undeclared encoder representation. |

Further visible protocol bookkeeping needs reconciliation by its owner before freeze: §3 has three uneven family allocations, while §8 still names eight strata/equal counts; R3 retains 127/128 historical answer-set labels. H3's off-target pair needs two other background families beyond target/foil, as the prior bank opinion records. These are declarations to fix in the prospective specification, not reasons to silently edit old captures or return to a closed audit.

## 5. What the registered report must specify

Draft 1 is a framework, not an executable registered report. Before CONF, a Stage-1 specification must fix:

- Primary claim hierarchy and outcomes above; active condition primary, no-target-report challenge and locality/exact-transfer analyses clearly secondary; all bridge/H3 availability and interpretation rules.
- Population, visible sense/E1/family eligibility, source/photo rights, accepted exemplar counts, audit reader identity and qualification, seeded role/foil/competitor/background allocation, and exclusion/stopping rules independent of CONF performance.
- Exact corruption and colour/noise/RMS/clipping/quantization pipeline, dose coordinate in each predictor, fixed geometry and zero/full definitions, photograph and mask draws, mask reuse/dependence, endpoint deduplication and weights.
- Fixed checkpoint, native multimodal implementation, precision, processor/template/grid/positions, lens, marker/suffix, R1 training/scaling and content/causal controls. All choices and changes learned in development/CAL/PILOT are disclosed and frozen before confirmation.
- Finite predictor family, image heterogeneity/conditional-dependence treatment, starts/recovery/undefined policies, training-only nested selection, paired folds and resampling, layer grid and any image encoder diagnostic. Equal nats do not establish equal effects across distinct predictive tasks.
- Estimand and uncertainty target: conditional on frozen CAL instruments, or including their training/selection variability; generator reference precision and refit coverage validation must match. Declare averaging over concepts/photographs/trials, especially with deduplicated unequal endpoint counts.
- Power and false-call/inclusion qualification for the final concept/photo/mask/carrier design, readout distributions and band dependence; target uncertainty and multiple-testing policy. The existing failed fixed-score interval is not reusable because y is scalar.
- Prospective ledger, task/seeds/shards/identity, runtime/memory/storage and aggregate caps, checkpoint/restart recovery, platform qualification, and exact stop/reconsideration rule. No paid dispatch follows from an accepted design review.
- Release plan for code, manifests, exact stimuli/transforms, raw readouts and logs, compatible with source terms; accepted materials must permit the specified replication. Disclose pilot data and prior exposure rather than treating a later registration as retroactive blindness.

For a **journal Registered Report**, ordinary preregistration is not Stage-1 peer review or acceptance in principle. Select the outlet and obtain its prospective review/acceptance before the registered confirmatory collection; existing development work is disclosed as pilot. These are format requirements, not a recommendation to submit to either example outlet. [Scientific Reports guidance](https://www.nature.com/srep/journal-policies/registered-reports), [AMPPS guidance](https://www.psychologicalscience.org/publications/ampps/registered-report-guidelines)

CONF 64/CAL 16/PILOT 16 per arm remains a working design target, not a power result. A registered-report submission discloses existing development data and all prior source/audit exposure; registering later does not make those observations blind. Current row 19 owner approvals and the prior Codex review's limits remain as recorded; later author amendments have not been re-reviewed here. The 31 October SI stays the narrowed audit.

## 6. Shared concepts and the first pilot

**Share concepts when claiming a within-concept channel comparison.** Use the same role assignment, family/sense, outer folds and joint resamples. A concept cannot be text CONF and image CAL; 64 shared CONF concepts are 64 paired units. Photo IDs and text clauses remain distinct material. Specify cross-arm stimulus seeds and dependencies rather than manufacture independent checkpoints.

Separate banks can support separate arm-specific claims. For a joint interpretation, report the source populations and overlap, ideally a prespecified paired overlap subset. An unpaired modality difference confounds modality with composition. A shared-bank requirement for that paired target need not make every image-only qualification depend on CSLB or twelve clauses.

**First pilot: retain the prior opinion's Stage A/B rather than §8 step 2.** After source/runtime gates, Stage A is ≤200 fidelity/cost forwards on 20 distinct development inputs at fixed 384-square geometry. Native-reference residual/logit tolerances, identical E1 argmax and bitwise sham/self-patch checks are already proposed in `fa24db8`. New execution identity alone does not establish fidelity.

Stage B uses disjoint DEV-CAL 16 + DEV-PILOT 16 (6/5/5 family allocation each), P=2 independently cleared photographs, R=2 mask draws, two neutral carriers and seven strengths, full-dose duplicates removed: 1,664 primary +192 C1 = **1,856 requests**. All 64 layers are captured in the same pass; fixed layer 41 is the main qualification reference, other specified layers diagnostic. Require held-out endpoint R1 performance, recognition on both photos under both carriers, same-family recognition, interior R3 transition, dose/target-control R2 contrasts, zero-input/source integrity and complete bounded execution. Scientific H3/C2 and statistical family outcomes are later work, never go criteria here.

Proposed four-hour single-Mac wall cap per stage, **eight hours aggregate and at most 2,056 forward requests**, plus storage/memory caps bound from Stage A before Stage B; a ledger row precedes any run. Its development layer 41 gate does not replace the protocol's eventual PILOT/band gates. If two cleared views are unavailable, stop this P2 version; one-view native-input qualification is a narrower demonstration. If the frozen pilot fails, diagnose the apparatus/grid/source and validate a revised prospective instrument on fresh held-out material. Do not repeatedly tune on the same PILOT or discard hard concepts until a mixture win appears. No run is approved by this record.

## 7. Wording to strike and the bounded framework to develop

Strike: CAPTCHA as a field “test” of consciousness/ignition; every CAPTCHA being an edge-of-ignition report; a documented graded-machine assumption; crossed human/machine curves from those rates; automatic inherited band/lens or unchanged audit calibration; random masks creating concept exchangeability; matching verdicts locating the threshold or establishing modality independence; the claim that none of the five can fail before their image design is tested.

Retain this structure: **one fixed checkpoint; two declared input channels; separately qualified content instruments; registered per-channel conditional-density/bridge/causal tests; a bounded cross-channel conjunction; explicit inconclusive and unavailable outcomes.** CAPTCHA studies motivate recognition-performance ambiguity. Geirhos supplies a behavioural/degradation reference; Sergent and Melcon supply distinct neural-task anchors. Input-stage and paired-target declarations strengthen the design but do not by themselves establish where any threshold originates. The author revises the framework after the dedicated assay review; nothing is adopted from this opinion alone.
