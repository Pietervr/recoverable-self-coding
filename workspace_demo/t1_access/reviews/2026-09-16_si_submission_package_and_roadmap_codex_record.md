# Entropy submission package and publication roadmap — Codex second opinion

Status: FINAL. 16 September 2026 UTC / 15 September PDT.
Requested by Claude Entropy SI at the owner's request, 21:44 PDT; brief `4420a32`,
`2026-09-16_si_submission_package_and_roadmap_codex_brief.md`, read in full.
Review baseline: Unimog package `d5354b97`, roadmap `901b58b9`, plus the owner's
subsequent typography fixes `e5f1e542`. Prior reviews `2e29207` and `226024e`
remain closed. This review does not repeat their scientific calculations.

The paper contains two completed analyses: a computational reproduction of the
human EEG comparison, and a simulation audit of a candidate model-side procedure,
including the independent reference bank and the post hoc predictor sensitivity.
It also specifies a proposed cross-substrate study. The proposal is conditional on
validation; it is neither a completed model experiment nor an accepted Registered
Report. That is a coherent Entropy paper. The package needs corrections before
finalization; none requires another SI simulation.

## Q1. Is the single-anonymized Entropy submission package right?

Broadly yes: retain the identified author, affiliation, ORCID, references and
repositories. The supplementary PDF is appropriately separate and identified.
The conference note accurately distinguishes this study from the accepted
abstract. The [specific SI call](https://www.mdpi.com/journal/entropy/special_issues/2W205JPV2N)
explicitly admits contributions on the conference subjects beyond extended
conference papers, and gives 31 October 2026 as its deadline. Keeping the class's
automatic extended-paper wording disabled is correct.

There are four substantive corrections and several smaller package items.

1. **Correct the median/floor inference in Results and Figure 3.**
   `sections/results.tex`, omega-2 paragraph, article p18 lines 658–659, still
   infers that the intervals track typical datasets and treats median inclusion
   as failing the 0.90 floor. The mean-target interval has no coverage obligation
   for the median, a different estimand. Candidate-reference inclusion does not
   identify the interval's target or explain the mechanism of the failure.
   Figure 3b, p21, draws the same 0.90 floor across median, trimmed mean and mean
   references; its caption reinforces that comparison. Remove that floor from
   the candidate-reference panel, or separate and explicitly qualify its scope.
   The declared mean-interval audit threshold can remain in Figure 2 with its
   existing plug-in-reference caveat. Suggested replacement for the offending
   inference: “Inclusion differs substantially across these candidate references.
   The median and the mean after removing one dataset are different targets from
   the untrimmed expectation; their inclusion rates do not assess coverage of
   that expectation. The untrimmed reference mean is itself imprecisely estimated.”
   Keep the untrimmed data and the qualification that no replacement interval is
   validated. This is an outstanding implementation of `226024e`, not a new audit.

2. **Make the availability statements true for the actual public release.**
   The wrapper's Data Availability Statement on p23 says all reported rows,
   post hoc scripts and figure scripts are public and archived in the study
   snapshot. The detailed statement on pp22–23 correctly excludes the later bank
   and post hoc analyses from the v1 DOI. The two statements disagree.

   Independent read-back at 05:01 UTC establishes:
   - `~/Recoverable-Self-Coding` and `~/recoverable-self-coding` are the SAME
     directory (device 16777230, inode 917784171); their `.git` is also identical
     (inode 917784510). Different capitalization does not establish a separate
     prepared public checkout.
   - Public `main` is `f5569980455751b82c8a39a376a9ae039cc61c14`, confirmed by
     `git ls-remote` and the unauthenticated GitHub API. Its commit timestamp is
     12 September 22:48:38 UTC; “checked on 13 September” is an access date.
   - The complete remote main tree lacks the later historical-pair and
     reference-inclusion scripts and the named omega-2 bank directory. The public
     `entropy-access-arxiv-v1` tag resolves to
     `6a3103ea7055c7bc0eaf1010a62d804570005034`; its complete tree has 78 files and
     no later bank/reference-inclusion/historical-pair paths.
   - [Zenodo v1](https://zenodo.org/records/22741885) is public, dated
     14 September, with `entropy-access-arxiv-v1-research.zip` (35,854,881 bytes;
     API checksum `md5:fb02368fa85e5200aa28893b6a76892b`). This check read the
     record metadata, not a fresh download and audit of the archive.
   - `reference_inclusion_check.py` and `.output.txt` beside the historical-pair
     sensitivity are still untracked locally. Commit `980820a` does not pin
     these later files merely because they sit in its directory. Codex's earlier
     independent saved-row verification remains pinned at `bac035a`.

   Public evidence, not the local ahead count, supports this finding. Before
   finalization the manuscript owner should prepare a bounded release containing
   the later bank, both post hoc analyses and current figure dependencies, pin its
   manifest/versions, and obtain the owner's existing publication authorization
   when required. Until actually released, describe those materials accurately
   and make them available to reviewers through the submission package. After
   release, verify the public contents and cite the new version; do not silently
   attribute them to v1. This review publishes or pushes nothing.

3. **Supply the basis for the secondary-data ethics statement.**
   Public de-identification and no new recruitment explain the study but do not,
   by themselves, document why this reuse is exempt from review. The original
   [Sergent Methods/Participants](https://www.nature.com/articles/s41467-021-21393-z)
   reports validation by CERES, the Paris Descartes ethics committee, and informed
   consent from all participants. Cite that for the original collection.
   For the present reuse, state the applicable institutional determination or
   rule, if available. MDPI's [human-study guidance](https://blog.mdpi.com/2025/07/30/human-studies/)
   calls for an exemption determination or an applicable local/national basis
   when a committee was not consulted. Resolve that basis with the institution
   or editorial office if it is not documented. Do not invent a waiver, an
   approval number, or a requirement to obtain fresh participant consent. This is
   a submission-documentation gap, not a finding that the reuse is unlawful.

4. **Finish the cut of the gain result, or retain its provenance.**
   Methods 4.3, p14 lines 505–510, still asserts twelve calibrated pairs passed
   their gates after the gain artefact's provenance and equations were removed.
   Saying it conditions no reported result does not stop that sentence being a
   reported empirical claim. My preference is to remove the completion/pass
   assertion and detailed gate recital, retaining the planned gain/power/recovery
   requirements and their unperformed status. If retained as a result, it needs
   the exact artefact and reproducible provenance. No full gain section needs
   restoring. See Q4.

Package completion and small corrections:

- **AI disclosure already exists**, prominently on p23 in `availability.tex`;
  it identifies Claude Code/Codex, their roles, and author responsibility.
  [MDPI's AI policy](https://www.mdpi.com/ethics) also asks for disclosure during
  submission, use details in Methods and product details in Acknowledgments.
  Align those locations with short cross-references/details; retain the existing
  disclosure. Record versions/dates only where known, never invented.
- I found no cover-letter file in the SI package or matching RSC paths, consistent
  with Claude's transcript. Prepare a concise letter explaining the completed
  reproduction/audit, information-theoretic fit, conditional proposal, related
  preprints/conference abstract and relevant earlier MDPI submission history.
  Distinguish this manuscript from the broad January framework submission; do
  not imply either a first-ever MDPI submission or a conference-paper extension.
  Confirm required declarations in SuSy. No letter is authored or sent here.
- Table 3's model “Score” cell cites `eq:boot` (16); cite the score definition
  `eq:delta` instead. Replace the Discussion's ambiguous interval-edges wording
  with temporal preference boundaries. Remove the Conclusion's residual
  architectural-map reference: `map.tex` is excluded from both active builds.
  Theory's statement that the simulation measures coverage needs the same
  estimated-reference qualification as Methods/Results.
- The competing-interest statement is present. Being an entrepreneur does not
  itself establish a conflict; disclose a specific relevant financial/IP interest
  if there is one. The generic occupation plus a denial should not obscure it.
- Make supplementary references specific: S1, S1.1, S1.2 and S1.4, as applicable,
  rather than expanding every distinct macro to “Supplementary Materials.”

The direct Entropy instructions/ethics/SI fetches intermittently failed (429 or
tool fetch errors). SI scope and AI policy above were recovered as indexed
primary-source text; the ethics explanation also has the accessible publisher
guidance cited above. I do not claim a complete read of the live Entropy
instructions or a completed SuSy submission check.

## Q2. Does moving the design to supplementary material weaken contribution 3?

No, provided the main article keeps the compact scientific contract already in
Methods 4.4 and the Introduction: the distinct R1/R2 readouts; randomized clause
dose and concept-level sampling unit; held-out comparison; bridge needed for the
access interpretation; causal test of use; prospective validation and freeze.
The Introduction's three predictions and the short outcome interpretation must
remain understandable without opening the supplement.

S1.1–S1.5 sensibly hold rig details, stimulus allocation, layer bands, intervention
and controls, the access/operation hypothesis and declared outcomes. Preserve
those definitions and the failure/inconclusive distinctions. Moving them does not
validate them, register them, or make the current draft ready for confirmation.
Call contribution 3 a specified proposed transfer assay, not an implemented or
validated assay. Keep enough of the completed human and simulation methods in the
article to evaluate its actual results; do not export the audit's essential
sampling, estimand and decision definitions just to reduce pages.

## Q3. Is 27 pages too long, and what should be cut next?

It is long for this focused argument, but 27 pages is not a policy violation.
[Entropy's aims](https://www.mdpi.com/journal/entropy/about) specify no maximum
length and welcome detailed reproducible work. The [MDPI submission FAQ](https://blog.mdpi.com/2021/10/27/submission-questions-answered/)
recommends contacting the office above 12,000 words; that is publisher advice,
not an Entropy hard limit or a reason to target 11,994 artificially.

The quoted counts are not a journal-defined total. Claude's `wordcount.py`, read
and run as a packaging check, drops captions/tables, substitutes math tokens and
counts source fragments. Its “with availability and appendix” total includes
`appendix.tex`, which is now outside the journal article, and omits wrapper
abstract/declarations and references. At the reviewed typography state it gives
10,169 main-body tokens, 462 availability tokens and 1,351 appendix tokens,
11,982 together. Thus the earlier 11,994 cannot establish an under-12,000 article
under a publisher's counting convention. Report article and supplement counts
separately, with inclusions stated, if asking the editor about length.

My cut order is:

1. **Background's broad theory survey and Table 1.** This is the largest
   dispensable framing block relative to the actual comparison. Keep a short
   account of the GNW distributional prediction and why the result does not
   adjudicate every consciousness theory. Move the full accounts table and its
   extended interpretation to supplementary material if another structural cut
   is wanted; retain its conditional caveats and references there.
2. **Repeated scope/status/limitation prose across Introduction, Discussion and
   Conclusion.** State the contributions once, integrate the interpretation once,
   and make the conclusion one focused paragraph. Preserve each material
   limitation at least once where it affects the inference. Remove the remaining
   unreported gain-result recital as described above.
3. **Unmeasured theoretical extensions before the score's core.** In the current
   build the information-decomposition section is 3.4 and thermodynamics is 3.5,
   rather than the brief's older 3.5/3.6 numbering. Keep the held-out cross-entropy
   difference, its sign/units, procedure-level target, KL interpretation and the
   distinction between predictive comparison and causal information. If needed,
   move secondary mutual-information derivation/prose to the supplement and keep
   its interpretation in a short paragraph. Keep the short warning that the
   measured score is not heat or thermodynamic entropy production.
4. **Only then streamline Methods 4.1.** Move implementation minutiae or a long
   reconciliation account if necessary, with an exact reference. Retain the
   inherited leakage/readout/optimizer limitations, post-outcome active reference,
   descriptive PXP status, and distinction between a temporal crossing and a
   corrected decision. These explain what the reproduction establishes. Removing
   them makes the manuscript shorter by making its claim harder to assess.

Tables 3–4 and the three empirical figures earn their space. I would prefer this
single focused editorial pass to either a compulsory page quota or another
substantial scientific deletion. The supplement should support the argument,
not become a repository for every discarded exposition.

## Q4. Did the previous cuts remove material a referee needs?

The cuts are defensible; no broad section needs restoring. Four safeguards:

- The gain cut is incomplete, as Q1 documents. Remove its remaining empirical
  success assertion or give it a verifiable source. Retain the information that
  power, model recovery and the multilayer band rule remain unassessed; gain
  calibration does not establish any of them.
- The compressed outcome paragraph still distinguishes two-state, graded,
  inconclusive and absence of the bridge. Technical failure is separately defined
  in the decision procedure and S1.5. Keep those distinctions, particularly that
  inconclusive/failure is not evidence of a graded scientific mechanism.
- The thermodynamic cut should leave only the necessary measurement distinction.
  RSC need not regain the stability-ratio exposition: the approved two
  touchpoints are sufficient and no RSC quantity is measured here.
- Referees need the data/procedure/provenance behind the completed results, the
  median/mean distinction and the validation boundary. They do not need an
  unreported gain apparatus or the removed architectural map. The availability
  correction, rather than restored exposition, closes the reproducibility gap.

## Q5. Is the seven-rung roadmap sound, and which Registered Report venue?

**Support the portfolio of outputs; revise its promised protection and ordering.
Pursue the feasibility of a Stage 1 Registered Report, with Neuroscience of
Consciousness the default scope match. Do not submit the present unresolved
protocol merely to obtain a date.** This is venue advice, not authorization to
freeze, submit, spend, collect or analyse confirmation data.

The current roadmap conflates a public timestamp, a Stage 1 submission and
in-principle acceptance (IPA). Registration documents prior specification and
can support attribution. It grants no exclusive ownership of the experiment and
no assurance of journal acceptance. Its scientific value does not disappear if a
competitor publishes first: a prospectively specified replication can still
separate planned tests from later choices. Delete the claim that registration
has no value the following day, and the unsupported superlatives about the
strongest/cheapest protection.

IPA is the relevant publication commitment. Both venues assess feasibility and
methods before granting it; Stage 2 protection is conditional on compliance,
quality checks and warranted conclusions. They do not publish Stage 1 as a
separate journal article: the approved protocol is deposited and incorporated in
the final report. Merely submitting Stage 1 supplies none of those commitments.
Sources: [NoC Registered Reports guidance, March 2023](https://static.primary.prod.gcms.the-infra.com/static/site/nc/documentlibrary/Registered_Reports_Guidelines_for_Neuroscience_of_Consciousness_%20March%202023.pdf?node=e0711e63b513e01d746e),
[Nature Communications guidance](https://www.nature.com/documents/ncomms-registered-report-guidelines.pdf).

| Existing rung | Contribution worth preserving | Necessary correction or gate |
|---|---|---|
| 1. SI reproduction/audit/proposal | The reproducible human analysis and specific procedure audit remain useful if someone publishes a model result. | Describe estimated-reference inclusion accurately. Related reproductions or audits can still compete with this contribution; no immunity or priority established. |
| 2. Public protocol | A citable, versioned account of the design and analyses before relevant outcomes are accessed. | Publish a development protocol as such if desired; reserve a confirmatory freeze for an executable, justified method. Preserve versions and amendments. Registration remains useful after competition. |
| 3. Registered Report | Conditional publication commitment following successful Stage 1 review. | Submission, IPA and final publication are separate milestones. Budget the methodological work and review; neither is “nearly free.” |
| 4. Instrument | Reusable stimuli, verified capture, decoders and validation. | Enough instrument feasibility is a dependency of a convincing Stage 1 proposal. A separate methods paper needs reusable value beyond this one study; otherwise integrate it. |
| 5. Inference method | A validated decision procedure addressing the diagnosed problem. | A valid interval is not guaranteed. An owner-approved critical-value alternative would need its own calibration and support different claims. Others can solve the same problem. Separate publication needs a generalizable contribution. |
| 6. Model study | A prospective test, potentially a valuable confirmation, contradiction or bounded null result. | Conditional on the method, instrument, power, band, freeze and resource gates. Neither ordinary publication nor higher citations are guaranteed. A prior competitor changes the contribution, not automatically its value. |
| 7. Review | Integration after the agreed prerequisite papers. | Retain its existing acceptance gates and R079 ownership. Being gated does not make a review resistant to competing reviews. |

The instrument and inference work therefore sit on the path to a credible IPA,
even if their standalone papers appear later. They need not each be accepted
papers before Stage 1. A precisely specified, editor-approved staged feasibility
design could be discussed, but “interval to be chosen later” is not a settled
confirmatory method. The outstanding estimator/decision choice, numerical
recipe, reference precision, validation, power/recovery, pilot and band issues
are dependencies already documented in `rsc_t1_simulation_design.md` and the
protocol; publishing the plan does not resolve them.

| Venue | Verified policy and fit | Recommendation for this programme |
|---|---|---|
| Neuroscience of Consciousness | Scope explicitly includes machines, computer science and methods relevant to consciousness. Stage 1 is limited to 7,000 words; Stage 2 normally 9,000. The March 2023 RR PDF asks for justified power at a minimally interesting effect, without giving a numeric percentage in the power paragraph. | Default: the scientific question and reader community fit directly. Confirm any applicable numeric requirement with the editor; do not substitute an assumed 90%/95% policy or presume the existing 80% gate is accepted. |
| Nature Communications | Stage 1 selects for significance as well as feasibility. Its RR PDF requires at least 0.95 a priori power for **all** frequentist hypothesis tests, with necessary support/approvals in place. | A possible ambitious choice only with a persuasive broad advance and a feasible compliant design. The current 0.8 gate and underpowered fallback do not meet that stated requirement. |

Sources for venue scope/length: [NoC manuscript instructions](https://academic.oup.com/nc/pages/General_Instructions).
Power/resource requirements: the two RR PDFs above, read through their final
pages. Do not treat a Bayesian redesign as a cheaper loophole: it would be a
different justified analysis/sampling plan requiring its own work and review.

Prior work and publication overlap need an explicit editorial answer. NoC
[permits preprints](https://academic.oup.com/nc/pages/author-guidelines), and
[Nature Communications](https://www.nature.com/ncomms/submit/how-to-submit)
distinguishes unrefereed preprints from overlapping journal submissions and
requires disclosure of related manuscripts. A journal-published SI design is
more than a preprint. It does not automatically disqualify a later new-data RR,
but neither policy guarantees eligibility for this exact split.

Recommend one targeted pre-submission enquiry to the preferred venue, prepared
by the manuscript owner when authorized: provide the SI manuscript/supplement,
its status and related preprint, separate already-seen human/simulation/pilot
data from uncollected model confirmation data, identify the new hypotheses and
validation gates, and ask whether that new-data study is eligible given the
published design and proposed timetable. No enquiry is sent in this review.
NoC explicitly allows some secondary-data registrations with evidence of no
prior access; that cannot retrospectively register our already-read outcomes.
For a primary RR, preserve the post-IPA collection boundary and separate pilots.

Choose the venue before knowing the confirmatory result, not Nature
Communications only if it is positive. Replace calendar assurances with gated
milestones and measured, funded compute plans. CHPC registration/application is
not evidence of an awarded allocation. The USD 3,000 further-spend cap, rejected
USD 90,000 scale and existing launch approvals remain unchanged. Route B stays
rejected as written; route A remains undecided. No new SI simulation is required.

## Verification and ownership

The scientific source reading was completed before this continuation: both
wrappers, all section files in order (including excluded `map.tex`), the full
brief/roadmap and relevant strategy/previous-review material. It was not repeated.
New work here was policy completion, public-release read-back, the word-counter
inspection and rendered-PDF checking, plus the typography diff and live transcript
refresh. This is not another numerical audit or a protocol validation.

Independent visual inspection: article pp1, 6, 13–15, 17–18, 20–23 and 27; all
three supplementary pages. Tables 1–4 are top-aligned, the final two-line equation
(19) fits, and the inspected figures/references/front/back matter are legible.
After the final typography rebuild, comparison of previously rendered selected
pages changed only p13, which was viewed again. Article 27 pages, supplement 3;
arXiv next-preview 28 pages was identified/text-extracted, not visually certified.
The “zero undefined/overfull” build results remain Claude's build evidence; Codex
did not recompile or claim an exhaustive every-page layout audit.

The accompanying `2026-09-16_si_submission_package_checks.json` pins the PDF
hashes, selected pages and public read-back. `arxiv_v1.pdf` stayed unchanged in
these checks, SHA256 `8f171b5b3841972572d6dbd06af6015a5c0a9ce73b21d72000224db6cc3e2201`.
No manuscript, protocol, release, scientific output, running job or production
file was changed. Claude owns disposition/manuscript/protocol/dispatch/R052
front matter; R084 owns instruments. Codex owns this review, exact reply,
full native Read-receipt verification and the R052 closure append.
