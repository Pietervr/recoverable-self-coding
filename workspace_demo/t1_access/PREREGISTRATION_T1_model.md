# T1, model side — pre-registration (DRAFT v1.2, 2026-09-11, after review rounds 1 and 2 and the first code pass)

**Freeze rule.** This document becomes v2 — the frozen pre-registration — by a commit whose hash is
recorded here, made only when every file in the §15 manifest exists and the §7.5/§10 validation
outputs are committed beside them. Until then it is a draft. After v2, changes are dated, committed
amendments (§15); nothing marked *[frozen]* is changed silently.

**Study.** Access at threshold in brain and language model (Entropy special issue, deadline 31 Oct 2026).
**Question.** Does the statistical description that separates graded from discontinuous *access* in
human EEG — the competing-model comparison of Sergent et al. 2021 (Nat Commun 12:1149), reproduced and
reconciled in `../sergent_port/` (commit e341319) — generalize to a language model's workspace
representations under a declared, randomized evidence dose?
**Not claimed.** Consciousness, experience, a first-order law shared by brain and model, entropy
production, ten model "subjects", a rejection of every graded account (only of the graded predictors
named in §7).
**Human reference.** A late active-session preference for the specified two-state mixture over the
specified heteroscedastic unimodal comparator, modest per-trial gain (~0.003 nat), boundary
sensitivity; the no-report case open. An assay to transfer, not a standard to meet.
**Inference statement.** One fixed checkpoint maps randomized clue packets deterministically to
residual activations. The study compares the conditional distribution of a pre-answer readout across a
declared stimulus population, then tests whether the readout's content affects the answer. Every
inference is conditional on this checkpoint and this stimulus population; the statistical clusters
are **concepts** (stratified by family), not model subjects. The primary readout R1 is a *coherence*
decoder; "access" is claimed only through the target bridge of §8.5.

---

## 1. Correspondence map

| Human (Sergent 2021) | Model (here) | Status of the correspondence |
|---|---|---|
| Vowel in noise; SNR (6–7 levels) | Coherence dose $k/8$: $k$ of eight descriptive clauses describe the target, the rest are a fixed family-balanced background (§3) | a randomized channel setting, not a semantic SNR; distinct-source count falls with $k$ (8, 8, 7, 6, 5, 3, 1) and is part of the manipulation |
| Time after stimulus (30 ms windows) | Layer depth at a fixed readout position | a computational-stage correspondence, not elapsed time; no requirement that late layers return to graded |
| Trial | One packet realization (concept × carrier × draw × level) | variability is declared and randomized in the stimulus |
| Subject ($n=20$), random effect | Concept ($n=64$ in confirmation), stratified by 8 families; carriers fixed (6); draws and levels are repeated observations within concept | the cluster for all uncertainty; ten pre-assigned bundles are a descriptive display only |
| EEG → CV linear decoder → per-trial distance | Residual stream → **frozen** linear decoder (calibration set) → per-trial decision-function score (R1) | a coherence readout; frozen scale for every confirmatory trial |
| Report: vowel identity + audibility | Next-token argmax (correct/incorrect) + the target token's log-probability and margin (R3) | no self-rating |
| Passive session | No-target-report condition: instruction before the packet, equal-length instructions, same marker (§12) | secondary; a challenge condition, not a passive state |
| M0 / M2B / M3, spm_BMS | The three inherited comparators; a frozen graded family and a frozen mixture family; primary evidence = out-of-sample joint log-score advantage with concept-cluster CIs (§8) | SPM curves kept, not given Bayesian calibration |

## 2. Hypotheses and outcomes

- **H1 (mixture support, coherence readout).** In the workspace band the mixture family predicts
  held-out concepts better than the graded family on R1: band-mean $\bar\Delta_{\text{ws}} > 0$ with a
  concept-cluster CI excluding 0 (§8.3).
- **H1-T (target bridge).** The same comparison on the target–foil projection R2 (§8.5) also gives
  mixture support, and the R1-assigned state predicts R2 at fixed $k$. "Discontinuous access" is
  written only if H1 and H1-T both hold; H1 alone is reported as a coherence-readout result.
- **H1′ (exact transfer).** The historical M3 beats the historical M2B on the two-model contrast in the
  band. Reported separately; H1 does not require it.
- **H2 (locality).** $\bar\Delta_{\text{ws}} - \bar\Delta_{\text{early}}$ has a CI excluding 0.
  "No contrast" is an explicit outcome.
- **H3 (causal use).** The state assigned by the held-out mixture fit moderates the effect of a
  target-direction intervention on the target–foil logit contrast (§11).
- **H0 (graded support).** $\bar\Delta_{\text{ws}} < 0$ with CI excluding 0.

Outcomes (§9): mixture support / graded support / inconclusive / technical assay failure. Family
heterogeneity, low high-state occupancy, or a mixture confined to some families are **scientific
results** under whichever outcome the primary statistic gives. A missing target bridge (§8.5) is not a
technical failure: it limits the interpretation to the coherence readout.

## 3. Stimulus population *[frozen at v2: `stimuli/concepts.json`, `stimuli/clues.json`, `stimuli/background.json`, `stimuli/manifest.csv`]*

**Concepts and roles.** 128 single-token concepts, 16 per family, 8 families (animals, countries,
tools, foods, vehicles, instruments, body parts, materials); token id frozen per concept in the answer
context (case and leading-space variants enumerated at build time). Seeded assignment per family:
4 → **BACKGROUND** (never a target, foil or competitor), 2 → CAL, 2 → PILOT, 8 → CONF. Roles are
disjoint by construction: a CAL/PILOT/CONF concept's clues appear only in packets of its own split,
and only as target, foil or competitor clues; background clauses come only from BACKGROUND concepts.
So a held-out CONF concept's clues are absent from every training packet of the primary set. No
concept is selected or dropped on model performance; difficulty is a recorded covariate.
**Clue bank.** 12 descriptive clauses per concept (all 128), 8–14 tokens each, written and audited by
two readers against a checklist (true of the concept; not containing the concept's name, an
inflection, or an accepted token variant; not naming the family). Clue identities are kept in every
record; single-clue difficulty is measured on CAL (§5) as a covariate.
**Pairs.** Within each split, concepts are paired across families by seed (CAL 8 pairs, PILOT 8,
CONF 32): each member is the **foil** of the other. A **competitor** (C2) is a third pre-assigned
concept of the same split from a third family.
**Background list.** Per (concept, carrier, draw): eight background clauses, exactly one from a
BACKGROUND concept of each family (the target's own family included), drawn by seed; identical for
the target packet and its paired foil packet.
**Packet and nesting.** Eight slots. A draw fixes a slot permutation $\sigma$, a permutation of the
12 target clues, the same for the foil's clues, and the background list, with background clause $d_j$
attached to slot $\sigma(j)$. Level $k$ replaces slots $\sigma(1..k)$ with target clues $t_1..t_k$;
slots $\sigma(k{+}1..8)$ keep their own background clause. Levels are therefore nested by slot, and
$k=0$ and $k=8$ are matched endpoints. $k=0$ means "no deliberately inserted target clues", not "no
semantic evidence for the target"; incidental similarity remains possible and is not corrected.
Levels $k \in \{0,1,2,3,4,6,8\}$ — dense where the transition is expected, sparse above; the pilot may
move one interior level (§5), recorded.
**Controls at fixed $k \in \{2,3,4\}$, draw 1 of each (concept, carrier), separate from the primary
density fitting:**
- *Foil packets* (C1): slots $\sigma(1..k)$ carry the foil's clues $f_1..f_k$, same background — the
  target-specificity comparison (§6.4, §8.5).
- *Competition packets* (C2): $k$ target clues in $\sigma(1..k)$ and $8-k$ clues of the competitor in
  the other slots (no background) — the one-competitor evidence baseline, explicitly a different
  structure from the primary channel.
**Carriers.** Six fixed frames (opening + closing sentences), fixed effects.
**Prompt scan.** Every assembled prompt (instruction, carrier, all slots, marker, suffix) is scanned
case-insensitively for the target's and the foil's surface forms and accepted variants; a hit
regenerates the draw with the next seed (recorded); after ten failures the concept is excluded at
build time, before any capture, on this string rule (recorded).
**Size.** Primary set per condition: CONF 64 × 6 × 7 × $D$ ($D=4$: 10,752); CAL and PILOT 16 × 6 × 7 × 4
= 2,688 each. Controls per condition: C1 64 × 6 × 3 = 1,152; C2 1,152. Overlength prompts (> 160
packet tokens or beyond the capture limit) are rejected at build time, never truncated.

## 4. Execution contract *[frozen]*

- Model: `mlx-community/Qwen3.6-27B-4bit`, the weights used in E1–E4 and E5–E9 (sha256 in the run
  log; E10 was Llama). 64 decoder layers (0–63), $d=5120$. Lens: Neuronpedia $n=1000$ Jacobian lens,
  fitted layers 0–62 (sha256); layer 63 has no Jacobian and reads out through the plain logit lens
  ($J_{63}=I$). Analysis layer set: 0–62; layer 63 descriptive only. Workspace band: layers 23–57
  (the E1 prior; the lens metadata's own band, 26–59, is a different definition and is not adopted);
  early band 3–15; late band 58–62.
- **One execution path, one pass per trial.** A read-only server addition `POST /api/capture` takes
  explicit `input_ids` (built by our code from raw text with the model tokenizer, no chat template),
  runs one `StreamSession.extend` over all ids with `capture_layers` = 0–63, and returns: the post-layer
  residual `acts[l]` (pre-norm, the tensor the lens transports) at the requested positions for every
  layer; the final position's logits reduced to `logsumexp`, the logits of a requested token-id list,
  and the top-1000 (id, logit) pairs; and, when an edit list is supplied, applies it inside that same
  pass with `StreamSession.set_edits` — at the named layers and global positions, before those layers'
  residuals are captured, so downstream layers consume the edited stream — logging $\|\Delta h\|$ per
  layer and position. Edit modes: `steer` (h + λv), `ablate` (`ablate_rows`, λ = removal fraction),
  `swap_delta` (Δ = patch_swap(h, α=1) − h, then h + λΔ — the linear-dose form; the raw `swap` alpha is
  not a dose and is not used), `patch` (replace the rows at the positions with supplied fp16 vectors).
  The legacy `/api/intervene` is not used.
- Suffix rule: the answer suffix is tokenized separately and its ids concatenated; the build asserts
  that tokenizing the joined text reproduces the prefix ids exactly, else the item is rejected.
- Empty-edit parity: a capture with an empty edit list must equal the plain capture bit for bit on 20
  prompts before any run; an edit with λ=0 must equal the plain capture likewise.
- Batch size 1; identical kernels and precision; no cache reuse between prompts (a new
  `StreamSession` per trial); model, lens, runtime and OS versions, and every token id, in the run log.
- Readout position: the last token of the terminal marker (§12).

## 5. Calibration (CAL) and pilot (PILOT)

**CAL (16 concepts).** Builds the instrument, frozen before CONF is read. Per layer: the R1 decoder
(§6.1) trained on CAL $k=8$ vs $k=0$ packets. $C$ is chosen by 5-fold concept-disjoint CV on CAL with
feature standardization fitted inside each training fold; selection metric = mean held-out log-loss;
ties → the smaller $C$. The decoder and standardization are then refitted on all CAL and frozen,
together with the affine z-scaling of the decision function (mean/SD of the CAL training scores).
Also on CAL: single-clue difficulty (target log-prob with one clue + 7 background); the family
recovery simulations (§7.5); the CAL layer scores for H3 (§11).
**PILOT (16 other concepts).** Validates the frozen instrument: held-out-concept accuracy at $k=8$ vs
$k=0$ per layer and per family on PILOT is the number reported (CAL's CV score is a selection score,
not a validation). Places the dose: the argmax-correct rate must cross 0.5 between $k=1$ and $k=4$; if
not, one interior level is moved (e.g. $\{0,1,2,3,4,6,8\} \to \{0,1,2,3,4,5,8\}$) and recorded. Supplies
the variance inputs for §10. Pilot model-comparison numbers are reported as pilot; they decide nothing
about the outcome.

## 6. Readouts *[frozen]*

### 6.1 R1 (primary assay; a coherence readout)
Per layer: `sklearn.linear_model.LogisticRegression(penalty="l2", C=C_l, solver="lbfgs", tol=1e-6,
max_iter=5000)` on standardized `acts[l]` at the readout position; $C_l \in \{10^{-3},\dots,10^{1}\}$
(9 values, log-spaced) from §5; response = `decision_function`, z-scaled with the CAL constants.
Trained on the active condition; frozen; applied to every trial at every level. "Distance" means
this quantity and nothing else.
### 6.2 R2 (target readout)
With $v^{(l)}_t = J_l^{\top} W_U[t]$ (the code's `j_lens_vectors_lite`; $J_{63}=I$), the linear
target–foil projection $r_2 = (v^{(l)}_t - v^{(l)}_f)\cdot h_l = (W_U[t]-W_U[f])\cdot J_l h_l$, and the
raw target projection $v^{(l)}_t\cdot h_l$. The normalized lens logit $(W_U\,\mathrm{norm}(J_l h_l))[t]$
is recorded as a secondary readout and never substituted for $r_2$. Endpoint projection
$\pi = (h - \bar h_{k=0})\cdot u / \|u\|^2$ with $u = \bar h_{k=8} - \bar h_{k=0}$ per (concept, carrier,
draw) from the matched endpoints; if $\|u\| < 0.05\,\overline{\|h\|}$ the trial is excluded from
$\pi$ only.
### 6.3 R3 (behaviour; active condition only)
From the final position of the active pass: the target token's log-probability
$\ell_t - \mathrm{logsumexp}$ (always recorded), its margin over the best other token, correct =
(argmax == target id); the foil's log-probability on every item. No sampling, so no malformed
outputs. Undefined in the no-target-report condition (no answer is elicited).
### 6.4 Content diagnostics (reported before H1 is read; §8.5 governs the interpretation)
On CONF at $k \in \{2,3,4\}$, paired target vs C1 foil packets (same background, same slots):
(i) R2 separates target from foil: the paired difference has a concept-cluster CI excluding 0 —
this is the **target-bridge precondition**; (ii) R1 target-vs-foil: a paired equivalence test
(TOST, margin 0.2 in z units, 90 % CI) per layer, plus the distribution of per-concept absolute
differences — a diagnostic of what R1 encodes, not a gate; non-significance is not equivalence;
(iii) R1 on target packets exceeds its $k=0$ value (coherence tracked).

## 7. Models *[frozen finite family after §7.5]*

Response $y$ = R1 score (or R2 projection in §8.5); regressor = level $k$; fits per layer.
### 7.1 Inherited comparators (ported line by line, `../sergent_port/fit_models.py`)
M0: $y \sim N(\mu, \sigma^2)$. M2B: $\mu(k) = L\,\mathrm{lg}(k) - L\,\mathrm{lg}(k_{\max}) + \mu_{\max}$
with $\mathrm{lg}(k) = 1/(1+e^{-\kappa(k-x_0)})$, $\sigma(k) = |a\,\mu(k) + b|$ (affine, as inherited).
M3: $A(k) = 1/(1+e^{-\kappa(k-x_0)})$ with $A=0$ at the catch level; $\mu_{\text{high}}(k) =
L_h\,\mathrm{lg}_h(k) + \text{step}$, forced to $\mu_{\text{low}}$ at the catch; $y \sim (1-A)N(\mu_{\text{low}},
\sigma^2) + A\,N(\mu_{\text{high}}, \sigma^2)$; shared $\sigma$. (In this form "step > 0" does not order
the components; M3 is kept exactly as inherited and is the historical comparator only.)
### 7.2 Graded family G
- **M2B** as above.
- **M2H**: M2B with a concept random effect on the threshold, $x_0 + u_c$, $u_c \sim N(0, \tau^2)$,
  $\tau = e^{t}$.
- **M2S**: M2B with a concept random scale multiplying the signal-dependent base scale,
  $\sigma_c(k) = |a\,\mu(k)+b|\,e^{v_c}$, $v_c \sim N(0, \omega^2)$, $\omega = e^{w}$.
- **M2K**: single-state skew-normal $y \sim \mathrm{SN}(\xi(k), \omega(k), \alpha(k))$ with
  **location** $\xi(k)$ the M2B logistic form, **scale** $\omega(k) = |a\,\xi(k) + b|$, **shape**
  $\alpha(k) = \alpha_0 + \alpha_1\,\xi(k)$ (Azzalini; the mean is $\xi + \omega\delta\sqrt{2/\pi}$,
  $\delta = \alpha/\sqrt{1+\alpha^2}$ — location and scale are not mean and SD).
### 7.3 Mixture family X (ordered parameterisation)
For every new member: $\mu_{\text{low}}$ free; $\mu_{\text{high}}(k) = \mu_{\text{low}} + e^{\delta_0} +
e^{\delta_1}\,\mathrm{lg}_h(k)$ — strictly above $\mu_{\text{low}}$ at every level; $A(k) =
1/(1+e^{-\kappa_A(k-x_0)})$.
- **M3** as inherited (historical comparator; unordered).
- **M3H**: ordered M3 with $A(0)=0$ and $u_c \sim N(0,\tau^2)$ on the shared $x_0$ of $A$ and
  $\mathrm{lg}_h$; shared $\sigma = e^{s}$.
- **M3V**: ordered M3 with $A(0)=0$ and component scales $\sigma_{\text{low}} = e^{s_0}$,
  $\sigma_{\text{high}} = e^{s_1}$, each floored at $0.05\,\mathrm{SD}_{\text{train}}(y)$ where the SD is
  that of the outer training fold (CAL for CAL fits) — never a CONF-wide SD; implemented as
  $\sigma = \text{floor} + e^{s}$ (v1.2), the smooth form of the floor.
- **M3L**: ordered M3 with a free catch-level occupancy $A(0) = \pi_0 = \mathrm{lg}(\theta_0)$ and the
  catch-level high emission $\mu_{\text{high}}(0) = \mu_{\text{low}} + e^{\delta_0}$ (not forced to
  $\mu_{\text{low}}$), so the catch mixture is identifiable whenever $e^{\delta_0}$ is not negligible;
  spontaneous occupancy is read from $\pi_0$ with its CI.
### 7.4 Fitting (v1.2: `models.py`)
Multi-start: 8 starts from the declared generator in `models.starts_from_moments` — data moments of
the training fold only (the inherited members keep the inherited moment initialisation; the ordered
mixtures start at the catch-level mean, the log offsets from the level means, unit slopes and the
midpoint-crossing level); start 0 unjittered, starts 1–7 jittered by a seeded $N(0, 0.25^2)$ per
coordinate in the optimiser's own parameter units (the raw vectors of §7.1–7.3). Each start is
L-BFGS-B (`ftol=1e-10, gtol=1e-6, maxiter=2000`) on the **analytic gradient** (JAX, x64); Nelder–Mead
is not used — the §14 start count is not computable with derivative-free fits (v1.2). A run is
*converged* if L-BFGS-B reports success. The kept solution is the converged run with the highest
training log-likelihood; if no run converged, the highest-likelihood run is kept and flagged. All
likelihoods in log space (`logsumexp` for mixtures). Random-effect integrals per concept by a
**two-scale trapezoid rule** in log space (v1.2, revised after the Codex review of v1.2): the mode
$\hat u_c$ of the concept's log-posterior in $u$ is found by a nine-point grid over $\pm 4\tau$ and
four safeguarded Newton steps (unrolled in the differentiated graph, so the gradient is exact); the
Laplace SD $\hat s_c$ is taken there and **capped** at $\tau$ by the curvature safeguard; the peak is
integrated by a $P$-point trapezoid rule on $[\hat u_c \pm 6\hat s_c]$ and the rest of the prior's
range, $[-6\tau, \hat u_c - 6\hat s_c]$ and $[\hat u_c + 6\hat s_c, 6\tau]$, by two further trapezoid
rules with $P/3$ points each (32 at $P = 96$) and exact endpoints, so that a flat tail or a second mode (M2H's
anchored mean returns to $\mu_{\max}$ at both extremes of the shifted threshold) is carried by the
outer rules. Why not Gauss–Hermite: prior-centred nodes do not converge at the CONF cluster size
(`verify.py` V3 — with 168 trials per concept 80 nodes still miss by 0.06–0.3 nat, so the v1.1 ladder
never terminates), and mode-centred nodes fail for the concepts whose shifted threshold leaves the
level range (a flat likelihood in $u$, a truncated-Gaussian posterior; 1–5 nat off at $\tau = 2$ with
the counts tried). The independent check is `audit_quadrature.py`: every hierarchical member at
every grid value against dense quadrature (80,001 points over $\pm 10\tau$) at the generating
parameters, at the **fitted** parameters on the held-out and training concepts, and under cross-fits
to the other family's data. At $P = 96$ (2026-09-11): max error $3.1 \times 10^{-4}$ nat over every
generating and fitted case, and $3.6 \times 10^{-3}$ nat in one cross-fit — M3H fitted to M2S data
at $\omega = 2$, where the fitted slope is so large that the likelihood in the threshold shift is a
staircase and the trapezoid error falls only linearly with $P$ ($5.4 \times 10^{-3}$ at 64,
$1.7 \times 10^{-3}$ at 128). These are observed errors of the likelihood at the audited parameters,
not a bound on the whole refitting and selection procedure; the case error over $n_c$,
$2 \times 10^{-5}$ nat per trial, is the size of the per-trial score perturbation at those
parameters, a hundred times below the smallest declared effect. Pass rule: < 1e-3 nat in the
generating and fitted cases, < 5e-3 in the cross-fits. $P$ is set on CAL/PILOT by raising it
(64 → 96 → 128) until every concept's joint log-likelihood changes by < 1e-3 at full cluster size
($n_c = 6 \times 7 \times D$), then frozen.
### 7.5 Recovery of the family distinction (before v2; `simulate.py` outputs committed)
Generators: every member of G and X at CAL/PILOT-fitted parameters and across a frozen grid —
heterogeneity $\tau, \omega \in \{0, 0.5, 1, 2\}$ (in level units / log-scale units), component
separation $e^{\delta_0}/\sigma \in \{0.5, 1, 2, 4\}$, catch occupancy $\pi_0 \in \{0, 0.05, 0.2\}$,
skew $\alpha \in \{0, 1, 3\}$ — 48 generator points (`simulate.recovery_points`), 200 replicates each
at CONF cluster sizes; the first pass (v1.2, `run_sims.sh`) runs 20 replicates per point on one
synthetic layer, the remaining parameters of every generator at the declared base of `simulate.py`
(graded: $\mu(0) = -1$, $\mu(8) = +1$, $x_0 = 3$, $\kappa = 1.5$, $\sigma = |0.15\mu + 0.75|$; mixtures:
$\mu_{\text{low}} = -1$, $\sigma = 0.6$, $A(k) = \mathrm{lg}(1.5(k-3))$, $\mu_{\text{high}}(k) = \mu_{\text{low}} +
\text{sep}\cdot\sigma + \mathrm{lg}_h(k)$). The full family decision of §8 is run on each. Reported: the
family confusion matrix per generator and grid point. **No member is
dropped for being individually unrecoverable**: nested members are expected to coincide at some
parameters. A member is consolidated only under an explicit rule — its held-out joint score never
differs from a sibling's by more than 1e-4 nat/trial anywhere on the grid (redundant), or it fails
numerically after the §7.4 recovery (repair first). A graded generator classified as mixture is a
discrimination failure that §10's calibration must absorb, not a reason to remove the generator.
The family is frozen after this step.

## 8. Primary analysis *[frozen]*

### 8.1 Joint concept scoring (the one scoring definition)
Five concept-disjoint outer folds on CONF, stratified by family (8 per family; the same folds for every
model and layer; `folds.json`); decoders and scaling are frozen from CAL, so nothing in the outer
split touches decoder training. For member $m$, concept $c$ with trials $i = 1..n_c$ and effect $u$:
$$q_{m,c} = \int \prod_i p_m(y_{ci} \mid k_{ci}, u)\,p_m(u)\,du,$$
the integral absent for non-hierarchical members. The primary family predictor is
**training-only selection**: for each outer fold and layer, the member of each family with the best
inner 4-fold concept-disjoint (stratified) joint log score on the training concepts is selected,
refitted on all training concepts, and scores the held-out concepts: $q_{F,c} = q_{m^\ast_F,c}$.
$$\Delta_c = \frac{\log q_{X,c} - \log q_{G,c}}{n_c}.$$
Sensitivity predictors, reported alongside: the equal-weight ensemble of joint likelihoods,
$q_{F,c} = \frac{1}{|F|}\sum_{m \in F} q_{m,c}$ (a mixture over members of the concept-level
likelihood, not a per-trial average); and the historical pair M3 vs M2B (H1′). The estimand is the
out-of-sample joint log-score advantage per trial of the training-selected mixture member over the
training-selected graded member; a positive result rejects those graded predictors, not the graded
class.
### 8.2 Uncertainty
Primary CI: concept-cluster bootstrap of the fixed out-of-fold concept scores $\Delta_c$ — resample
whole concepts with replacement within each of the eight family strata, 2,000 replicates, carrying
every layer, level and carrier of a concept together (`analyze.band_bootstrap`). Foil pairs cross
families, so they cannot be kept together under family strata (v1.2): the primary R1 statistic
resamples concepts; the paired statistics of §6.4 and §8.5(b) resample foil pairs as the unit,
unstratified. This is a
conditional approximation (it does not re-run the density fits); its coverage is validated in §10 by
simulations that regenerate the data and refit the pipeline. If simulated coverage of the nominal
95 % interval is below 0.90 under any retained generator, the pipeline-refitting bootstrap (200
replicates, all copies of a concept in one fold) replaces it as primary — decided and recorded before
CONF is read. Per-family (8) summaries with the same CIs.
### 8.3 Layer summary and criterion
Band mean $\bar\Delta_{\text{ws}}$ over the frozen layer grid within 23–57 (primary; the grid is every
layer, or a fixed stride of 2 if the §14 benchmark requires it, frozen at v2), $\bar\Delta_{\text{early}}$
over 3–15, $\bar\Delta_{\text{late}}$ over 58–62; the band maximum is reported with its location but is
not the criterion. **Mixture support:** the 95 % CI of $\bar\Delta_{\text{ws}}$ excludes 0 and is
positive. **Graded support:** excludes 0 and is negative. **Inconclusive:** includes 0. No layer
selection on CONF.
### 8.4 Secondary, reported alongside
The historical SPM curves (spm_BMS on the averaged held-out ML scores, all members and the three
inherited ones), an inherited assay without Bayesian calibration; H1′; within-family member scores;
per-family directions (count of families whose $\bar\Delta_{\text{ws}}$ has the pooled sign; no
threshold); fitted high-state occupancy by level, separation $(\mu_{\text{high}} - \mu_{\text{low}})/\sigma$,
M3L's $\pi_0$; R2 and $\pi$ profiles by level with CIs; the descriptive ten-bundle display.
### 8.5 Target bridge (H1-T; an analysis of the same captures)
(a) The §7–§8.3 comparison run on $y = r_2$ (the target–foil projection, z-scaled with CAL
constants) instead of R1, same folds, same predictors, same criterion; (b) at fixed $k \in \{2,3,4\}$,
the R2 mean in R1-assigned high-state trials minus low-state trials (state = posterior of the
training-selected mixture member at the reference layer of §11, > 0.9 / < 0.1), with a concept-cluster
CI. H1-T holds if (a) gives mixture support in the band and (b)'s CI excludes 0 in the positive
direction. Precondition: §6.4(i). If (a) or (b) fails, or §6.4(i) fails, the result is written as a
coherence-readout result and "discontinuous access" is not used.

## 9. Outcomes and technical failure *[frozen]*

- **Mixture support / graded support / inconclusive** by §8.3 on R1 (primary: active condition,
  active-trained decoder — one H1). The no-target-report condition (§12) is a secondary analysis with
  its own pre-declared predictor order (transfer decoder primary, separately trained decoder as
  sensitivity); it does not offer a second chance at H1.
- **Technical assay failure** (reported as such, no scientific reading): PILOT held-out decoder
  accuracy at $k=8$ vs $k=0$ below 0.75 in more than a third of band layers; capture-parity failure;
  suffix-tokenization failure; a retained member that cannot be scored after the §7.4 recovery
  (16 further starts, then a doubled jitter) — in which case the **primary comparison is unavailable**
  and any reduced-family result is a secondary amended analysis, never the H1 result. **Amended
  policy for the inner selection** (v1.2, weaker than the rule above and declared as such): a member
  whose inner fit or inner held-out score is not finite after the recovery scores $-\infty$ and
  cannot be selected, and is recorded; if every member of a family is unscorable in a fold, the
  primary comparison is unavailable. Inner convergence and the count of non-finite inner scores are
  reported beside the refit convergence, and the simulations of §10 run under this policy.
- **Coherence-only reading** (a scientific outcome, not a failure): §6.4(i) or §8.5 fails; H1 is
  reported on R1, H3 is not run.
- **Underpowered** (§10) is declared before CONF and reported with the result.

## 10. Calibration and power *[rule frozen; the grid and counts frozen at v2; `simulate.py` outputs committed]*

Simulated: the **full** §8 procedure — outer folds, inner selection, refit, joint scoring, the §8.2
bootstrap, the band mean and the §8.3 rule, the §7.4 convergence handling and the §9 failure rule —
on synthetic CONF-sized data at the frozen layer grid, with concept effects and the measured residual
correlation across layers (from PILOT) generated as declared in `simulate.py`. Nulls: **every retained
graded member** (M2B, M2H, M2S, M2K) at CAL/PILOT-fitted and grid parameters; alternatives: every
retained mixture member at per-trial gains 0.003 (the human scale), 0.01 and 0.03 nat — the gain
being the expected out-of-sample joint log-score advantage per trial of the generator over the best
graded member fitted at large sample (256 concepts), reached by scaling both high-state offsets
(`simulate.calibrate_gain`; the truth term is scored under the generating density). **Acceptance
gate** (v1.2 after the Codex re-check; `simulate.gain_gate`, enforced when the gain file is written
and again when it is loaded): the twelve (member, gain) pairs present exactly once; scale, gain,
check and check-SE finite; every graded reference fit converged in the calibration draw (8 × 32
concepts) and in the independent check draw (a fresh seed, 8 × 64 concepts); the check's SE — the
test-concept variation conditional on the check's own fitted graded reference — at most 20 % of the
target; and the check within 25 % of the target. A pair that fails is recalibrated with more
reference simulation or the gain claim for that pair is changed explicitly; the power stage does not
run on a file that fails. "0.003 nat" is a numerical reference scale, the oracle-to-large-sample-graded
separation, not the finite-design selected-X-versus-selected-G $\bar\Delta$ nor the human historical
pair's gain. For run `d4v12b`, whose job code recorded the check without enforcing it, the gate is
applied to the recorded entries with the check recomputed at 8 × 64 concepts
(`simulate.revalidate_gain_entries`) before any power result is read; a pair whose scale the gate
would change has its power replicates and five-layer rows rerun under a new namespace. Counts: 1,000 datasets per generator and setting (Monte-Carlo SE ≈ 0.7 pp at a 5 %
rate). The §14 benchmark (v1.2) puts one dataset through the full procedure at 900 s per layer on one
Mac core, so the full counts on one synthetic layer (12 nulls and 12 alternatives at 1,000, the 36
mixture recovery points at 200, the five-layer pilot) are ≈ 9,000 Mac-core-hours per $D$ — not this
machine's work (owner, 11 Sept: it is too slow and not always on). The simulations run as sharded, resumable SageMaker
training jobs in the cloud (`t1_job.py`, `launch_t1.py`; results under
`s3://xtenure-cself-pvr/results/t1_access/<run>/`, one immutable code snapshot and one result
namespace per numerical configuration, every row and the gain file carrying the code/config hash,
resumes refused across hashes; per-concept scores and the selected members per layer and fold are
saved with every replicate for offline re-scoring), $D = 4$ first and $D = 8$ only if the §10 power
rule asks for it. The recovery grid's twelve graded points at replicates 0–199 are the calibration
stage's first 200 replicates (same seeds, same configuration) and are reused, not refitted. The run
launched on 11 Sept 23:00 UTC (160 shards on 50 jobs: 20 managed-spot and 22 on-demand
`ml.c8i.2xlarge`, 8 on-demand `ml.c8i.48xlarge` with fifteen shards each) was stopped after one hour
on the Codex review of v1.2 and its rows discarded. **The corrected run, `d4v12b`, launched on 12
Sept 00:38 UTC** from commit `52267ec` with the same fleet layout, code snapshot
`code/t1_access/d4v12b/`, results under `results/t1_access/d4v12b/`; at the §14 cost of the
corrected method (900 s per layer on a Mac core; 83 min per replicate on a loaded small-instance
vCPU) it is expected to take 45–50 h. Runtime: Python 3.12, jax 0.11.1, numpy 2.4.6, scipy 1.18.0,
pandas 3.0.5, joblib 1.5.3 on x86-64 Linux (logged by every job and written into every row from the
next snapshot on; the launcher pins them so a resume is the same runtime). Codex's re-check of the
fixes (17:45 PDT) accepted findings 1–5, 10 and 12 and held finding 7 open until the gain gate above
existed; two integration slips in the gate commit were fixed at `eae1cb8` with mocked tests, the
revalidated-artefact path at `fa83301`; **Codex's final verdict (17:56 PDT): on board** — continue
`d4v12b` as the per-layer calibration and recovery run, power results held until the revalidated
gain artefact passes, band validation a separate post-PILOT stage. The owner funded the run on that
verdict (12 Sept), with spot checks throughout: the landed rows are read at every stage boundary
(`spotcheck.py`), not only at the end. **Calibration stage of `d4v12b`, read 12 Sept 18:30 UTC at 11,923 of
12,000 rows (every null at $n \ge 958$):** the false-positive rate is 0 of 11,923 under all twelve graded
nulls (one-sided 95 % upper limit ≈ 0.3 % per setting), convergence 1.000, no failures; the interval coverage
of $\theta_g$ is below 0.90 for six settings — M2H $\tau = 0.5$ (0.819), $\tau = 2$ (0.894), M2K
$\alpha = 1$ (0.884), M2S $\omega = 0.5$ (0.848), $\omega = 1$ (0.780), $\omega = 2$ (0.216) — so the
**§8.2 replacement by the refitting bootstrap is invoked** (coverage below 0.90 under any retained
generator). Every miss is an interval lying above its target; at $\omega = 2$ the root-mean-square bootstrap
SE (22.0) matches the replicate SD (23.2), so the failure is tail sampling and interval shape under a
heavy-tailed held-out loss (one concept in one replicate at $-26{,}627$ nat): extreme tail losses and the
percentile interval's shape must be investigated alongside fitting and selection variability — RMS-SE agreement
alone does not separate these mechanisms (Codex, 12 Sept, review 3), and the categorical exclusion of fitting
variance is withdrawn.
Disposition (Codex review, 12 Sept): the refitting bootstrap is corrected first (original-concept grouping at
both fold levels; failed replicates propagated), benchmarked, and the chosen interval validated on new seeds
with declared counts — the choice is recorded as method development on these rows, never as their
validation; M2S $\omega = 2$ stays as the declared stress condition; the rows keep their code/config hash
and an explicit cross-snapshot reuse manifest carries them forward. **The refitting bootstrap was corrected the same
day** (`analyze.refit_bootstrap`, `grouped_stratified_folds`, `Dataset.group`; `test_refit_bootstrap.py`): the
copies of an original concept share a fold at both levels; the grouped fold maker reduces to the plain one when
every group is distinct, so the plain analysis and every d4v12b null fit are reproduced bit for bit; the
analysis's own outer folds are passed in, each copy staying in its original concept's outer fold (the declared
fixed-fold specification); a resample whose procedure fails, or whose band scores are not all finite, yields no
statistic (no `nanmean`), and **the interval is usable only when every replicate is scored** — a lower fraction is an
explicit amendment with a missing-tail analysis, never a default (Codex re-check). The interval method is a declared
`Config` choice carried through the runner (`interval = "cluster" | "refit"`, `n_boot_refit`, both in the code/config
hash and in every row): with `"refit"` the point estimates stay the fixed scores' band means, the cluster interval is
kept beside, the three predictors and the paired ws − early statistic come from the same refits, and an unusable
refit interval is an **assay failure**, never an inconclusive reading (`decide` on a non-finite interval returns
"unavailable"); the per-replicate statistics are returned for persistence and rescoring (`test_interval_path.py`).
Three flags are kept apart in every row (Codex, third review): `failed` (the original fits and points are
invalid), `primary_available` (valid points and a usable primary interval) and each predictor's own interval
availability; every valid point estimates the unconditional target $\theta_g$ whether or not its interval could
be built, coverage is computed among that predictor's finite usable intervals, and the missing intervals are
counted and reported as a performance result of their own (Morris, White & Crowther 2019, §5.1). Every band,
the paired ws − early statistic, the companion cluster interval, the bootstrap's seed, policy, folds, failure
reasons and per-replicate statistics are written with the row; completed resamples are checkpointed as they
finish and a restart resumes them. The launcher carries the declared interval method and replicate count into
the job's environment and hash (`launch_t1.py --interval --n-boot-refit`).
Cost (`bench_refit.py`, one Mac core, one layer, D = 4, M2S $\omega = 0.5$, inner selection at 4 starts): 15.3 min
per replicate, so 200 replicates ≈ 51 Mac-core-hours per dataset per layer; the cloud cost is **not** established by
this — the corrected procedure is benchmarked at the intended cloud concurrency before any projection (loaded cloud
fits ran several times slower than the Mac in `d4v12b`), and the R2/H1-T and declared additional analyses need their
own accounting. **Validation plan (candidate amendment, Codex re-check):** the interval choice is screened cheaply
first, then validated on new seeds at declared counts with Monte-Carlo intervals — R = 400 datasets × B = 200
replicates per setting (Monte-Carlo SE ≈ 1.5 pp at coverage 0.90, 1.1 pp at 0.95; R = 1,000 if the original precision
is kept) with a pre-declared disposition for estimates too close to 0.90 to resolve; every retained null setting and
the declared mixture alternatives, not only the six settings that failed; selection and ensemble scored from the
same bootstrap fits; $\theta_g$ estimated by ordinary-pipeline repetitions without bootstrapping each reference
dataset (eligible old fits may contribute), its uncertainty mattering most at $\omega = 2$; bookkeeping after Morris,
White & Crowther (2019, §§5.2–5.3). The power stage did not run: the
job-side gain calibration failed the gate at M3L, 0.01 nat (`bisection limit: 0.00806 vs target 0.01`), and no
power, recovery or five-layer rows exist. **Cause, established 12 Sept** (`repro_gain_m3l.py`, `diag_gain_jump.py`;
outputs in `sim_results/d4v12b/monitor/`): the failure reproduces exactly on one Mac core; at the fixed
calibration seed the gain is a deterministic but discontinuous function of the scale — 0.00806 just below
0.684661 and 0.01097 just above — with the selected reference **M2K on both sides**, so not a switch of $G^*$.
The best-found M2K solution at 256 concepts (training log-likelihood −44,543.6) is reached by one start of the
eight-start batch; the other seven end in a basin 155 nat worse whose held-out score is 0.003 nat per trial worse;
at the scale of bisection step 21 that one start lands and at the scale of step 22, $1.6 \times 10^{-6}$ further in
scale ($2.4 \times 10^{-6}$ relative), it slides into the shallow basin, both runs reporting convergence — optimiser
basin loss within M2K (Codex, 12 Sept: accepted; the $G^*$-switch candidate withdrawn). A 5 % search tolerance
cannot be met across a 30 % jump. How often a batch of eight misses the best-found solution is **not established**
by these runs (one batch found it once in eight, a second batch with another seed never; the corrected run's
evaluation at scale 3 found a better M2K solution in one start of 57). **Amendment (calibration side only;
`models.py` and the pipeline untouched; `simulate.expected_gain`, `calibrate_gain`, `gain_gate`, after the Codex
re-check of the same day):** the graded reference fits use 32 jittered cold starts; the distinct basins found
earlier on the bisection path travel as warm starts (up to six per member, deduplicated); a member whose
best-found solution is reached by fewer than two DISTINCT cold starts gets 24 more jittered starts from a further
seed — never the unjittered moment start the cold batch already holds, and mirrored in the skew coordinates on
every second start so both orientations are tried; every start's source, likelihood and convergence are recorded.
The bisection also stops when the bracket has collapsed to 0.1 % in scale; both ends are then re-evaluated with the
full warm set (the evaluated function depends on the search history, so a stale end must not be read as a
discontinuity); if an end is within tolerance the scale is resolved there, else the scale is frozen at the
bracket's centre, the gain re-measured there at twice the concepts and a fresh calibration seed as the declared
fallback (not a further chance to pick a seed), and the jump recorded. The gate additionally requires the selected
reference's best-found solution reproduced by at least two distinct cold or extra starts in the calibration draw
and in the check draw (a warm-start discovery never counts as a cold one) and the calibration-side gain within
25 % of the target; the check is warm-started on its training draw only, its test draw is never fitted. **After Codex's
third review (same day):** the evaluation that is gated and archived is always the FINAL one, made at the chosen
scale on the calibration draw (its seed and concept count recorded) — never an endpoint evaluated for another
purpose; if the second re-evaluated endpoint finds a basin the first had not seen, the first is refreshed before
the pair is read. That final evaluation, and the check on its own training draw, carry a declared **training-only
challenge**: an independently seeded batch on the same training data — four starts at the moment start with the
skew coordinates set to every sign combination of ±2 (deliberately separated basins) and jittered starts at twice
the jitter — run before any test score is read; if it improves the best likelihood by more than 0.5 nat the
reference IS the improved solution, the gain is scored against it and the improvement is recorded, and the
reproduction count then refers to it (an independently seeded challenge discovery counts; a warm start's never).
Every start's source, batch and seed ids, initial vector and final vector are archived; reproduction counts
DISTINCT initial vectors. Reproduction by two starts is not proof of global optimality: it says the best-found
solution was reached independently twice, and the rarity of a miss under this scheme is not yet demonstrated. The
twelve-pair artefact is computed **once** (`TASK=gain`, or locally), validated (`spotcheck --revalidate`, the
legacy route: one declared check, never a search over check seeds, every check field rewritten together) and read
by every power job through the same rule as the monitor's — the revalidated artefact when it exists, else the
job-written one, both under the run's hash; a power job whose namespace lacks it fails closed (`t1_job.gain_file`).
Reaching the one failed pair does not approve the other eleven. **Diagnostic result (12 Sept, one Mac core, the
first-fix code `a508601`: 32 cold starts, the previous winner as warm start, reproduction ≥ 2, no challenge):**
M3L at 0.01 nat RESOLVED in ten search evaluations (119 min) — with the deep M2K reference found, the gain is
continuous and monotone in the scale (0.00537 at 0.627, 0.00770 at 0.678, 0.00916 at 0.705, 0.00997 at 0.719,
0.01084 at 0.733) and the scale is 0.7188, not the 0.685 the shallow reference had collapsed onto; check 0.01003 ±
0.00052 (64 per family, fresh seed), gate passed. The deep M2K solution was reached by 2–4 of the 32 cold starts at
every scale above 0.63 (6 of 32 in the check), so the reproduction rule was met but not by much; the same pair is
being recomputed under the final code with the training-only challenge and start provenance, and the twelve-pair
artefact is computed only under that code. This is a diagnostic, not the artefact. **Open, before v2 (Codex, finding 6):** the same fragility may sit in the pipeline's own refits (§7.4,
eight starts, at the inner and outer training sizes of ≈ 38 and 51 concepts); FPR 0 under the M2K nulls does not
show every graded fit was accurate. A numerical-sensitivity audit on declared representative draws, mixture-shaped
data included, with stronger training-only reference searches, decides whether §7.4 is amended for the new
snapshot (never a warm start from another CONF fold that holds the current held-out concepts; CAL-derived starts
and within-training-fold searches are allowed). d4v12b's immutability is a provenance constraint, not a reason
to keep a demonstrated weakness in the eventual CONF pipeline. The historical M3-versus-M2B contrast, saved with every
row, returns mixture support in 651 of 1,000 M2H $\tau = 2$ and 337 of 1,000 M2S $\omega = 2$ replicates —
a simulation demonstration of the inherited pair's vulnerability to omitted heterogeneity.

**What the single-layer simulations establish, and what they do not** (v1.2 after the Codex
review): with one synthetic layer per dataset they calibrate the **per-layer procedure** (inner
selection, refit, joint scoring, the concept-cluster interval) and establish the family recovery;
they do not by themselves certify the **35-layer band rule** of §8.3, whose validation needs the
frozen band grid, the cross-layer heterogeneity and residual correlation measured on PILOT, every
retained null family, and Monte-Carlo precision adequate to the thresholds. That band validation is
its own pre-specified stage, run after PILOT with the measured correlation structure, with counts
declared at v2; its grid is never chosen from the outcome of a pilot. The five-layer stage of the
present run (every graded member at one grid value — M2B; M2H $\tau = 0.5$; M2S $\omega = 0.5$; M2K
$\alpha = 1$ — and every mixture member at the 0.01 nat gain, on layers 25, 33, 41, 49, 57, 200
replicates) is a computational pilot of the layer averaging, not that validation. Until PILOT is
read, the cross-layer residual correlation is a declared AR(1) stand-in with coefficient $\rho = 0.9$
**per physical layer** (so $0.9^{8}$ between sampled layers eight apart), the mixture state is
shared across a trial's layers and the concept effect is shared across layers.

**Coverage estimand** (v1.2): the interval's coverage is assessed for
$\theta_g(D, L) = E[\bar\Delta_{\text{ws}}]$, the expectation of the complete procedure's band-mean
held-out score difference under generator $g$ at the design sizes, over the stimulus draws, the folds
and the optimiser's randomness — an unconditional algorithm-performance target, estimated by the
replicate mean with its own Monte-Carlo SE reported; coverage is reported among usable intervals and
failures separately. It is not the oracle gain of `expected_gain`, not the conditional risk of the
particular fitted predictors, and not the risk after training on all 64 concepts. Two separate
failures:
- **Calibration**: the false-positive rate (mixture support under a graded null) must be ≤ 0.064
  (0.05 + 2 SE) for every null at the chosen $D$, and CI coverage ≥ 0.90. Failure at $D=8$ requires
  revision **before CONF** — permitted changes, frozen here: the bootstrap type (§8.2), the family
  predictor (selection vs equal-weight), the band summary (mean vs trimmed mean) — recorded as a v2
  amendment; the underpowered fallback does not apply to a calibration failure.
- **Power**: draws per (concept, carrier) $D \in \{4, 8\}$ — the smallest $D$ with power ≥ 0.8 at
  0.01 nat under every mixture alternative; ceiling $D=8$ (21,504 trials per condition). If $D=8$
  gives power < 0.8 at 0.01 nat, the study is declared underpowered below that scale and proceeds at
  $D=8$ with that statement in the paper.

## 11. H3 — causal use *[frozen]*

**Layer selection (independent of CONF).** The §8 pipeline is run on CAL with 4 concept-disjoint
stratified folds (4 concepts each); the three band layers with the largest CAL $\bar\Delta$ are the
intervention layers; the largest is the **reference layer**. Not cross-fitting — a CAL choice.
**State.** Per CONF trial: the posterior high-state probability of the training-selected mixture
member (§8.1) at the reference layer, fitted on the other folds; high if > 0.9, low if < 0.1;
$k \in \{2,3,4\}$ only; up to 200 high and 200 low trials matched on level, carrier and family (all
eligible trials if fewer; number reported).
**Single-pass interventions** (`/api/capture`, edits at the marker positions, joint at the three
layers in one pass; separate single-layer effects reported as secondary): baseline (empty edit list);
(i) **swap_delta** target → foil, λ=1 — the primary operation; (ii) **ablate** the target direction
(`ablate_token_ids=[target]`, λ=1); (iii) **rescue**: steer with $v_t$ at a per-layer amplitude
$\lambda_l$ frozen on CAL so that $\|\lambda_l v_t\|$ equals the median $\|\Delta h_l\|$ of the swap
operation on CAL high-state trials — applied to **both** low- and high-state trials (saturation is the
prediction on high); (iv) **sham**: λ=0 (must equal baseline bit for bit); (v) **off-target**: swap_delta
between a pre-assigned unrelated pair $(u_1 \to u_2)$ of BACKGROUND single-token concepts from
families other than the target's and foil's, scaled per layer to $\|\Delta h_l\|$ of the trial's own
target swap (per-layer norm matching); if $\|\Delta'\| < 10^{-3}\|h\|$ the control is undefined and
reported; (vi) **positive control**: `patch` the marker-position residuals from the trial's matched
$k=8$ packet (same draw) at the three layers.
**Outcomes.** Primary: the reduction of the target–foil logit contrast at the final position,
effect $= (\ell_t - \ell_f)_{\text{before}} - (\ell_t - \ell_f)_{\text{after}}$ (positive = reduction) for
swap and ablate; for rescue the increase (sign reversed). Secondary: argmax flips (denominator =
trials correct at baseline for swap/ablate; all trials for rescue).
**Decision rule.** The primary contrast is the intervention × state interaction for the joint
swap: $\bar E_{\text{high}} - \bar E_{\text{low}}$ with its concept-cluster 95 % CI. H3 supported if the
CI excludes 0 and the point estimate ≥ 0.5 nat (SEOI); "strong" if the CI lower bound ≥ 0.5 nat.
Controls: sham and off-target effects must satisfy |effect| < 0.25 nat with the 90 % CI inside
(equivalence); the positive control must increase the contrast on low-state trials with a CI
excluding 0 — if it does not, the apparatus is insensitive and H3 is reported as **not testable**.
Ablate and rescue interactions are secondary, with CIs, no correction. The effect is also regressed
on $\|\Delta h\|$, baseline margin, level, carrier and family (dose regression), and the binary-state
account is compared with a smooth account (effect linear in the z-scored R1 score) by held-out log
score; "two-state causal mechanism" is not written if the smooth account predicts as well or better.
**Reading.** H1 supported and H3 unsupported is "causal use not established by this intervention".
Secondary downstream task: 100 pre-assigned yes/no property items (`stimuli/properties.json`;
"Does it fly?"), scored by the log-odds of the correct answer token after the packet and question;
the same intervention × state contrast, reported with CI.

## 12. Conditions *[frozen]*

**Active (report).** ids = `<instruction A> <carrier open> <8 slots> <carrier close> <terminal
marker>` + `Answer:`; instruction A = "Read the description below; afterwards, name in one word what
is described." One pass: residuals at the marker's last token (unaffected by the suffix under the
causal mask), logits at the final position.
**No-target-report (challenge).** Instruction B, wording adjusted at build time until it tokenizes to
**exactly the same number of tokens** as instruction A (asserted in the manifest, so every packet and
marker position is the same global index in both conditions); same packet, same marker, no suffix;
residuals at the marker's last token. Called "no-target-report", never "passive". Secondary (§9).

## 13. Exploratory (not confirmatory; deferred unless time allows)
Token-axis history dependence (dose ramped within one context) with the controls listed in the
10 Sept consensus; no bistability claim from lag alone.

## 14. Budget and timeline
Captures (single pass each, $D=4$): primary 2 × 10,752 + controls 2 × 2,304 + CAL/PILOT 2 × 5,376 =
36,864, at 3–5 s → 31–51 h. Storage per capture: 64 × 5120 fp16 residuals at one position (0.66 MB)
+ logsumexp, requested-token logits and top-1000 (≈ 10 kB) → ≈ 25 GB, gitignored. H3: 400 trials ×
(baseline + 6 joint + 3 × 3 single-layer) = 6,400 captures ≈ 7 h. Fitting: 8 members × 63 layers ×
5 outer folds × (4 inner + 1 refit) × 8 starts = 100,800 starts per condition, plus CAL/PILOT, the
§7.5 recovery and §10 calibration runs; benchmarked on CAL before v2 — if the band cannot be fitted
within 24 h per condition on this machine, the frozen layer grid becomes stride 2 within each band
and inner selection uses 4 starts (recorded in v2). **Benchmark, synthetic CONF size, one core
(v1.2, `bench.py`, 2026-09-11, the process pinned to one XLA thread with `NPROC=1`, the §7.4
two-scale trapezoid quadrature at $P = 96$ with the eight-fraction backtracking search):** the
nine refits at 8 starts take 74.7 s at $D = 4$ (M3H 55.2 s, M2H 11.4 s, M2S 6.7 s, the rest under
1 s; ≈ 1.7× at $D = 8$), every start converging; one layer of the full §8 procedure (5 outer folds ×
8 members × (4 inner fits + refit)) takes 900 s with 4 inner-selection starts (the earlier
single-window rule gave 860 s with 8 and 556 s with 4; selections and $\Delta$ identical to five
figures across all three), so the 63-layer band is ≈ 16 h per condition on one core, ≈ 1.5 h on
the machine's 11 usable workers, well inside the 24 h — every layer stays. **Inner selection uses 4 starts** (v1.2, the
clause above invoked for the simulation budget rather than the CONF fit: the §10 simulations
re-run the whole procedure tens of thousands of times, and 4 starts cut a third of the cost); the
refits keep 8, and CONF is fitted with the same setting so that the simulated procedure is the
procedure. The machine (Apple M4 Max, 12
performance + 4 efficiency cores, 128 GB) takes 11 single-threaded workers before they slow each
other; one x86 cloud core (`ml.c7i`, SageMaker) is 0.36 of a Mac core on this code, and a fully
loaded hyperthread a tenth. Server patch + stimulus bank: week of 15 Sept;
CAL, PILOT, recovery and calibration: week of 22 Sept; **v2 freeze by 29 Sept** (with the manifest
files); CONF captures and fits 30 Sept–6 Oct; H3 and write-up in October.

## 15. Freeze manifest for v2 and amendment log
Frozen at v2 (all committed, hashes in the v2 commit): `stimuli/` (concepts, clues, background,
pairs, competitors, properties, draws, manifest with token counts and scan results); the level set;
`capture.py` (ids, suffix assertion, parity tests, run log); `decode_cal.py` outputs (per-layer
decoders, $C_l$, standardization, scaling); `models.py` (the members, parameterisations, start
generator, optimizer settings, GH node count); `folds.json`; `analyze.py` (joint scoring, selection,
bootstrap, band summaries, outcome table, target bridge); `simulate.py` with its §7.5 and §10 outputs
and the resulting $D$, bootstrap type and layer grid; `h3.py` (CAL layer scores, matching, edit
lists, amplitudes, outcomes); this document.

| date | change | reason |
|---|---|---|
| 2026-09-11 | v0 drafted | for second-opinion review |
| 2026-09-11 | v1: inference unit = concepts; frozen CAL decoder; distractor channel; nine-model family; held-out family log score; outcomes split; power by simulation; H3 via one capture path; no-target-report condition | review round 1 (Codex) |
| 2026-09-11 | v1.2 (second entry, after the Codex review of v1.2 — verdict "not on board", `reviews/2026-09-11_v1.2_codex_brief.md`): the first cloud run stopped after 1 h and discarded; §7.4 quadrature rebuilt as the two-scale trapezoid rule with the independent audit at generating, fitted and cross-fitted parameters (`audit_quadrature.py`), the Laplace SD stated as capped; §9 inner-selection failure policy; §10 gain truth term under the generating density, twelve-calibration gate with independent check and D passed, "0.003" named a reference scale, coverage estimand stated, the single-layer run's scope stated and the band validation made its own post-PILOT stage, five-layer pilot with every graded member, correlation per physical layer, recovery reuse of the calibration rows; versioned code snapshots and result namespaces with the code/config hash in every row; per-concept scores saved | Codex review of v1.2 (session Entropy) |
| 2026-09-11 | v1.2: `models.py`, `analyze.py`, `simulate.py`, `verify.py`, `bench.py` written and verified (inherited likelihoods equal the numpy originals to 1e-9, gradients to 1e-8, self-refits recover every generator); §7.4: L-BFGS-B on analytic gradients replaces Nelder–Mead, the start generator and its jitter defined, the random-effect integral becomes a per-concept trapezoid rule on an adaptive window (prior-centred Gauss–Hermite does not converge at $n_c = 168$, mode-centred Gauss–Hermite fails on the truncated posteriors at $\tau = 2$) with the point ladder 48 → 96 → 192; §7.3 M3V floor as $\text{floor} + e^{s}$; §8.2 foil pairs resampled as units only in the paired statistics; §7.5 and §10 generator base declared, the gain definition made operational; §14 benchmark recorded — every layer kept, inner selection at 4 starts, refits at 8; the simulations moved to sharded SageMaker spot jobs (§10) | first code pass (session Entropy) |
| 2026-09-11 | v1.1: BACKGROUND concept bank with family-balanced backgrounds identical across target/foil pairs, slot-nested levels, role disjointness, prompt scan; H1 = coherence readout with a pre-declared target bridge (§8.5); one joint concept-scoring definition with training-only within-family selection (equal-weight and M3-vs-M2B as sensitivity); ordered mixture parameterisation, identifiable M3L catch, inherited affine sigma kept, skew-normal parameters named; SciPy option names and solver rule; recovery of the family distinction replaces member-recoverability; post-CONF member loss = primary unavailable; bootstrap defined and validated by refit simulation; calibration vs power failures separated with permitted changes; single-pass active capture with edits inside the answer pass; swap_delta linear dose, per-layer norm matching, rescue amplitude, patch mode; H3 decision rule, polarity, positive-control criterion, smooth-vs-binary check; layer count 64 / lens 0–62 / band 23–57 kept; equal-length instructions; budget recomputed | review round 2 (Codex) |
| 2026-09-12 | v1.2 (third entry, after the d4v12b calibration-stage read and the Codex re-check of the fixes): §10 records FPR 0 under all twelve nulls, coverage below 0.90 for six settings and the §8.2 refitting-bootstrap replacement invoked; the refitting bootstrap corrected (copies of a concept in one fold at both levels, the analysis's outer folds, failed or partially scored resamples never averaged, every replicate required, the interval method a declared Config choice carried through the runner with an unusable interval = assay failure) and benchmarked on the Mac; the gain-gate failure at M3L 0.01 nat diagnosed as optimiser basin loss within the M2K reference (the best-found solution reached by one start of the batch; the gain discontinuous in the scale at a fixed seed) and the calibration amended on its own side — 32 cold reference starts, distinct basins carried as warm starts, an extra batch without the repeated moment start and skew-mirrored, reproduction of the best-found reference by distinct cold starts required in both draws, the collapsed bracket re-evaluated before the jump is read, the declared fallback re-measurement, the calibration-side gain gated, every start archived; the gain artefact computed once and power jobs failing closed without it; the validation plan (R = 400 × B = 200 with Monte-Carlo intervals, every setting) and the pre-v2 pipeline numerical audit recorded; `models.py` and the pipeline unchanged; the corrected code reproduces the d4v12b null fits bit for bit (cross-snapshot reuse manifest to follow, with separate source and analysis hashes) | run d4v12b's calibration read and gain-gate failure; Codex review of the read and of the fixes (session Entropy SI) |
