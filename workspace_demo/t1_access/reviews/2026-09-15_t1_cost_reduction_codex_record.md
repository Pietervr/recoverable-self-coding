# T1 cost-reduction memo — Codex review checkpoint

Status: DRAFT, 15 September 2026. This is a reading checkpoint for the required
context wrap, not a final opinion or permission to launch. No substantive reply
to the cost-review request has been sent. Codex retains the review and receipt
obligations in R052, session `GPT: R052 Entropy paper`.

## Scope and sources already read

Claude Entropy SI requested this separate second opinion through xs at
09:35:58 PDT on 15 September. The complete request and complete memo were read:
[`2026-09-15_t1_cost_reduction_memo.md`](2026-09-15_t1_cost_reduction_memo.md),
RSC `b38f0d2`. The proposed sequence is: numerical development; a fresh
least-favourable-first cluster-interval calibration; a more expensive interval
fallback only if necessary; then the remaining validation stages on local or
academic compute. These are proposals under review, not adopted amendments.

The owner's USD 3,000 additional AWS spending cap remains. The owner rejected
USD 90,000-scale simulation spending. Academic compute access and throughput
must be distinguished from a completed allocation or a measured cost estimate.
Nothing is to be launched by this review.

Fresh logs/status were checked in both repos, followed by xs list/chat. RSC
HEAD was `b38f0d2`; Unimog HEAD was `099b3d23` at the wrap checkpoint. The complete
Unimog `737c9384` addition of design-companion section 11 was read. The broader
current preregistration and companion reads returned truncated tool output;
they must not be described as fully refreshed for this review. The earlier JOB D
review read the preregistration, companion, analyze.py and relevant models and
simulate functions, but that does not settle the new protocol questions.

### Reading progress after the verified continuation (15 September)

The full current preregistration (681 lines) and full companion (128 long lines,
including section 6) have now been read in sequential bounded chunks, as has the
complete memo again. The latest wrap from `01a0a5c8` to `01a0a5fa-f8cb-75d1-ba54-21447d0f239b`
was verified against native/common records, exact name/topic and a single native
user receipt at 16:51:28.553Z. Prompt SHA256 `ac1d4ee1f4a43368442161e7419111ee705189637e615d9239fa0619fa49e676`
matches HEAD and the source checkpoint commit `42333922`. Both repo logs/status
and xs list/chat were refreshed. Claude `ebe16cf8`'s complete post-09:35 text was
read; its latest job note reports the Mac probe's straggler idling ten workers.

Primary paper reading is IN PROGRESS. Downloads/extractions are local temporary
public-source files; no private transcript was copied. Read ranges, inclusive:

- Bates–Hastie–Tibshirani v4, all main text plus appendices through extracted
  line 2250 of `/tmp/r052_bates_cv_clean.txt` (2588 lines total). Continue at
  2251 to EOF. Source https://arxiv.org/pdf/2104.00673.
- Nadeau–Bengio, the actual published 2003 article (43 pages, not the 2001 author
  draft), through line 1270 of `/tmp/r052_nadeau_published_clean.txt` (3086 lines).
  Continue at 1271 in bounded chunks. Source
  https://link.springer.com/content/pdf/10.1023/A:1024068626366.pdf.
- Official CHPC policy sections 2.1/2.3/3.1/3.3 and SU wiki full content read:
  initial 100,000 CPU-hours/six months, free academic programme usage, approval,
  240-core default limit and scratch expiry confirmed in the published policy.
  SU 1,000 free CPU-hours and queue-wide (not personal) week limit of 1,000
  confirmed. CHPC registration URL did not load in the browser tool; no account
  or allocation approval is established. Quickstart overview and PBS allocation
  context read; remaining queue/accounting details may be useful.
- T1 `models.py` constants, densities (160–257), `_run_starts`/`_pick`/`fit`
  (557–635) inspected. No bounds argument in minimize; only M3V has the declared
  0.05 SD floor, while inherited affine scales use absolute value and M3H/M3L
  use exponentials. This conforms to the declared different families; it is
  not by itself a demonstrated Melcon-like implementation defect.

Checks supported so far, still to integrate into a final opinion: the refitting
replacement already fired; v2 is not frozen. Numerical starts and changed model
floors/bounds require different amendment descriptions. Starts sensitivity does
not diagnose coverage. Nadeau–Bengio's correlation approximation depends on
training-set stability (sections 3.1/4), so is a screen, not an automatic repair.
Bates v4 Algorithm 1 takes repetitions R as an input; 200 is their experiment's
choice. Its CI construction targets instance-specific ErrXY (section 4.2),
while T1 targets the unconditional complete-procedure expectation. Dependence
within a concept does not itself rule out a concept-level adaptation; fixed
family strata, joint loss, paired family comparison and target need work.
CHPC CPU-hours are not measured Mac-equivalent hours. No final conclusion,
arithmetic computation, fit, generation, bootstrap, source edit or xs reply yet.

The next sections remain the checking agenda from the first checkpoint; the
completed reading above supersedes their reading-status statements.

## Q1 — Protocol route: unresolved checks

Read the current `../PREREGISTRATION_T1_model.md` end-to-end in manageable
sequential chunks, especially sections 7.4, 7.5, 8–10, 14 and 15. Its previous
single-call read was 681 lines / 16,671 tokens and was truncated. Refresh the
128-line, long-paragraph Unimog `project_knowledge/rsc_t1_simulation_design.md`,
particularly section 6, without truncation. The preregistration wins where the
companion differs.

Resolve the already-fired calibration replacement clause and the fact that the
protocol remains a draft rather than frozen v2. Distinguish changing start
counts or repairing an implementation from changing statistical model bounds,
density floors, prediction rules or the estimand. Section 7.4 is not yet
established as blanket authority to reset the interval decision. Determine the
explicit prospective amendment and fresh evidence needed to reconsider the
cluster interval while preserving the recorded failures.

JOB D measures sensitivity of the nested procedure to starts. A change in Delta
alone does not establish the cause of undercoverage or demonstrate an adequate
final policy. A member-targeted policy would need an exact definition, selection
record and independent validation. The Melcon floor finding does not by itself
establish a T1 defect; inspect T1's own density and bound conventions before
making that inference. Keep development and adoption distinct.

## Q2 — Sequential validation: unresolved checks

The memo proposes null ordering beginning with M2S omega 2, 1 and 0.5, then
other challenging nulls, with looks at R = 100, 200 and 400 and early stopping
for clear failure only. Specify actual prospective stopping boundaries and
final acceptance/indeterminate rules after reading the existing coverage and
false-positive criteria. Fixed-seed prefixes, all failures and tail outcomes,
selection/ensemble targets and denominators must remain explicit.

The complete-procedure reference mean is an estimated target. For omega 2 it
is tail-dominated, so quantify or otherwise account for independent reference
uncertainty under the selected policy before treating interval inclusion as
known Bernoulli outcomes. A nominal coverage Monte Carlo standard error near
0.015 at R = 400 does not establish that reference precision is adequate or
that a near-boundary result is determinate. Do not silently pool development
data into validation or count stopped settings as passed.

If deterministic binomial calculations help define boundaries, use a script
file with no model/analyze imports, data generation or optimizer invocation.
No such arithmetic has yet been performed for this cost review.

## Q3 — Fallback methods: unresolved checks

Read the primary Nadeau–Bengio paper and Bates–Hastie–Tibshirani paper before
answering. Match their estimands and sampling units to the T1 complete
procedure, including inner member selection, concept strata, repeated trials
within concepts and shared training observations. Check whether the memo's
200 nested-CV repetitions are an experimental choice or a requirement, and
whether an i.i.d. limitation applies at the concept level. Nested CV is not
authorized for implementation or fitting by this review.

For corrected repeated splits, define J, the test/train ratio at the relevant
independent unit, the repeated-split statistic and any target change. A variance
correction is not automatically a validated interval for this procedure or its
heavy-tailed score distribution. For reduced-B refitting, separate bootstrap
Monte Carlo error, quantile resolution and replication counts from the
coverage validation itself. Preserve full fitting/recovery semantics and
policy consistency across originals, resamples and reference calculations.

Reading queue:

- https://arxiv.org/abs/2104.00673 (full current paper; memo cites v4, Algorithm 1 and sections 5–7).
- https://link.springer.com/article/10.1023/A:1024068626366 (primary Nadeau–Bengio paper).
- https://cran.r-project.org/web/packages/correctR/vignettes/correctR.html (official implementation context, secondary to the method paper).
- Previously read methods sources, if useful: https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/ and https://numpy.org/doc/stable/reference/random/parallel.html.

## Q4 — Architecture and cost: unresolved checks

Define the provenance and numerical parity evidence needed before pooling Mac
arm64, PC x86 and CHPC x86 results. Include exact code/configuration/policy,
RNG identities, numerical libraries, hardware, balanced machine allocation,
representative paired replay including difficult/failure cases, and tolerances
tied to score/selection/interval decisions. Do not claim identical code hashes
for changed wrappers or demand cross-architecture bitwise identity without
examining the actual requirement. Record architecture-specific failures and
avoid allocating all hard settings to one machine without accounting for it.

Existing JOB D evidence gives policy A 56,647.375 seconds per nested dataset,
cold 5,766.015625 seconds, a 9.824353 multiplier. These are historical loaded
PC worker elapsed-time sums from the declared per-start model, not measured
CPU time, total wall time, or a universal multiplier for every stage. Do not
double-discount concurrency. The actual refitting workload still needs its
own benchmark. The memo's Mac-equivalent hours are not yet converted into
measured CHPC accounting units or a demonstrated queue completion date.

Verify official current allocation, eligibility, charging and scheduling
claims before concluding that every stage fits free compute:

- https://wiki.chpc.ac.za/_media/chpc:chpc_accounts_policy_v2.6.pdf
- https://users.chpc.ac.za/create/register_user/
- https://www0.sun.ac.za/hpc/index.php?title=Main_Page

The memo claims an initial CHPC allocation of 100,000 CPU-hours for six months
and an SU allowance of 1,000 CPU-hours; the owner has opened registration.
Neither claim has been independently verified by Codex for this review yet.

## Q5 — Final disposition still required

After the checks, give a concrete conditional disposition and the conditions
that would prevent endorsement. Do not substitute a request for a large new
experiment for a review answer. Preserve the spending limit and distinguish
a scientific requirement from an implementation or allocation uncertainty.
No claim here is a final answer to Q1–Q5.

## Completion and ownership

Replace this checkpoint with the final Q1–Q5 record after completing the
reading and bounded evidence checks. Commit only the review-owned paths with
the Codex trailer. Append only the R052 log using `wr set 52 --log`; Claude
owns the front matter and all protocol, code, production, manuscript,
execution, monitors and PC dispatch. Commit the work file and generated index.
Send one substantive final reply using `xs say claude:"Entropy SI"`, then
verify the full unchanged record in Claude's native tool_result and log closure.

JOB D is complete: record RSC `016151a`, full native receipt 16:07:02.429Z in
Claude `ebe16cf8`; disposition `b1885a5`; brief v2 running on PC per the new
request. Melcon v7 is complete: record `e42846e`, full native receipt
16:20:09.029Z in the same Claude session; DEVPLAN rev 1 disposition `9cbcc0a`.
Do not reopen or resend either. Their supporting seed/cost checks and review
records remain the detailed evidence, rather than this checkpoint.

Preserve other-owner results, load_verification.csv, models/PIDs, untracked
audit archives and manuscript/counsel artifacts. Refresh substantive jobs
only through Claude's transcript. No fit, generation, bootstrap, BMS, EEG,
cloud launch, production deployment, freeze or push by Codex.
