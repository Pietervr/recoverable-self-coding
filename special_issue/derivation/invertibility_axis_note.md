# Where we stand: defending the two-dimensional regime map (D1)

**Status:** scratch assessment, not yet folded into the paper.
**Question:** can we *defend* the "(CR, SR) two-dimensional regime map" and the
two-condition admissibility law against the referee, rather than demoting them?
**Answer:** **Yes — but the second axis must be corrected.** The defense is
viable and turns the referee's two strongest structural objections into a
strengthened result with a new figure. It costs a rework of the signature
diagram and ~half a page.

---

## 1. The referee's concern (restated, and it is correct)

In the pure single-server certification queue at steady state,
`SR = (1−P_c)/P_c` with `P_c = 1 − e^{−θ⋆Δt}` and `θ⋆ = μ(1−CR)`, so

> **SR is an exact deterministic function of CR.**

Therefore the `(CR, SR)` plane collapses to a *curve*: SR is not an independent
second axis, and — since the paper diagnoses condition (ii) *via SR* — condition
(ii) appears to do no work independent of condition (i). Both objections are
correct **as written**.

## 2. The defense: invertibility has its own order parameter

The paper already names it and then never uses it. Local invertibility (Eq. for
`I(δE;Z) ≥ ι`) is "enforced by a gate with timescale ratio **ζ = τ_cert/τ_upd**."
That ζ — certification *latency* relative to how fast the environmental cause
*drifts* — is **independent of CR = utilization**:

- **CR (capacity axis):** throughput vs load. Governs whether the backlog is
  stable and whether commitments clear the deadline. Observable: SR.
- **ζ (invertibility axis):** latency vs environmental coherence time. Governs
  whether a *certified* macrostate `Z` still grounds the *current* cause `δE`.
  Observable: `I(δE;Z)`.

A low-utilization system (CR = 0.3) in a fast-changing world (ζ ≫ 1) is **stable
but un-invertible**: the queue clears fine, but by the time each commitment is
certified the cause it grounded has moved, so `Z` no longer informs `δE`.
Condition (i) holds; condition (ii) fails. The two are independent.

Crucially, this exposes the labeling error: **a commitment can be *certified*
(cleared the deadline, SR-good) yet *un-invertible* (its `Z` is stale).** SR
captures only the deadline split; the invertibility loss *among the certified*
is invisible to SR. So the genuine second axis is `I(δE;Z)` (driven by ζ), and
SR is the *one-dimensional observable of the capacity axis*.

## 3. Minimal model (simulated: `invertibility_axis_sim.py`)

M/M/1 certification queue (CR = λ/μ) coupled to a telegraph environment `δE(t)`
of flip rate `κ = 1/τ_upd`. For each commitment (arrival `t_a`, sojourn `T`,
commit `t_c`): the cause drifts, `corr(δE(t_c), δE(t_a)) = e^{−2κT}`; certified
iff `T < Δt`; a certified commitment grounds `Z = δE(t_a)`, an uncertified one
commits on prior. Define `ζ = 2κΔt`.

## 4. Result — the decoupling is clean

**At fixed CR = 0.70, sweeping the environment speed ζ:**

| ζ = 2κΔt | SR | I(δE;Z) [bit] | recoverable |
|---:|---:|---:|---:|
| 0.02 | **0.417** | 0.388 | 0.703 |
| 0.10 | **0.417** | 0.360 | 0.692 |
| 0.50 | **0.417** | 0.258 | 0.644 |
| 1.00 | **0.417** | 0.181 | 0.599 |
| 2.00 | **0.417** | 0.098 | 0.536 |
| 5.00 | **0.417** | 0.028 | 0.451 |

**SR is flat to three decimals (0.417) — the capacity axis is independent of ζ —
while `I(δE;Z)` collapses 0.39 → 0.03 bit.** Condition (i) holds throughout
(CR = 0.7 < 1, SR unchanged); condition (ii) fails as ζ rises. The
`(CR, ζ)` phase diagram (figure panel b) shows the recoverable region bounded by
**two independent boundaries**: `CR < 1` (sharp, the capacity transition) and
`ζ < ζ_c` (a smooth crossover, the invertibility decay).

→ `invertibility_axis.pdf`

## 5. Verdict

**The two-dimensional map and the two-condition admissibility law are
defensible.** The referee is right that SR is CR-slaved; the fix is not to demote
to 1D but to put the *correct* quantity on the second axis:

- **Capacity axis** = CR, observed via SR (the well-measured, field-estimable
  half).
- **Invertibility axis** = `I(δE;Z)`, driven by ζ (a genuinely independent
  failure mode, demonstrated above).

This **answers referee concern #2** (condition (ii) now provably does independent
work — here is the regime where it fails while (i) holds) and **reframes #1**
correctly (the second axis is invertibility, not SR).

### Bonus: it also helps the venue question (#5)
The capacity/invertibility decoupling driven by *two independent order
parameters* (utilization and a latency-vs-drift ratio) is a **genuinely new
result**, not relabeled queueing — which is exactly the "what is new for
*Entropy*?" gap. Defending D1 partially answers D2.

## 6. What it costs the paper (be honest)

1. **Rework the signature figure.** The "(CR, SR) regime map" becomes a
   "(CR, ζ) — capacity × invertibility" map. SR is demoted from "second axis" to
   "the capacity axis's observable." This touches the abstract, the Regime-Map
   section, and Fig. (regime).
2. **Add the drift model + this figure** (~half a page). The current queue model
   has no environment process; we must introduce `δE` with a coherence time.
3. **Honest remaining limitation:** the invertibility axis `I(δE;Z)` is still
   *not* field-estimable from counts (the cause `δE` is latent) — so condition
   (ii) is now *independent* but its field measurement stays open. This is the
   already-flagged open problem; the defense makes (ii) non-vacuous without
   making it field-cheap.
4. **The ζ-boundary is a crossover, not a sharp transition** like CR = 1. We
   should say "smooth invertibility decay," not "second phase boundary."

## 7. Recommendation

**Adopt Defend.** It converts the referee's two structural objections into a
strengthened, more honest framing plus a new result that also shores up the
venue case. Net: a more defensible paper. The cost (rework the central figure,
+½ page) is worth it.

**Open for decision before folding in:**
- Are we willing to rework the signature `(CR, SR)` diagram into `(CR, ζ)`? (It
  changes the paper's most recognizable picture.)
- Keep SR prominent (it is the field-measurable half) but explicitly *as the
  capacity observable*, with the invertibility axis carried by `I(δE;Z)`/ζ and
  its field-estimation flagged open.
- This likely pushes the SI back over 20pp; revisit the length target.
