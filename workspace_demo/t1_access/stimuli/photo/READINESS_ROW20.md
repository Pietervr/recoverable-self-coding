# Photograph arm, ledger row 20: readiness, revision 15

R084 (Claude), 3 October 2026. **Row 20 has no go for this package.** Two actual runs have happened: on 2 October,
under the owner's go, the revision-10 package ran 158 instrumented forwards on the development images and stopped
before native (`reviews/2026-10-02_stage_a_run.md`); on 3 October, under the owner's release and go, the revision-12
package resumed it, ran 16 native forwards and stopped at 15-native on the frozen logit criterion - residuals
bit-identical, the difference one bfloat16 step at logit 16.5 (`reviews/2026-10-03_stage_a_resume_run.md`).
Everything else below is synthetic mechanism evidence, with one disclosed exception: the transition fixtures
(revisions 12-14) run on COPIES of the real development-run records (`captures/photo_stage_a`), never edited and
with no forward.

**Revision 13** (`STAGE_A_CRITERIA.md` §R13, handoff `8508993b`): the native logit criterion becomes max(0.10, one
bf16 step at the logit's magnitude) - unchanged below 16 - in the one `compare` both the native worker and the
validator call; the transition becomes a chain of declared predecessors (revision 10 for the instrumented phase,
revision 12 for native 00-15). **Revision 14** (§R14, Codex `c4bbcb5`, handoff `ee9852d7`): a prepared link whose
ledger-slot write did not happen is reconciled idempotently on restart (only the slot commit), and the declarations are
corrected (three records reached two steps at small logits; the rule is relaxed at and above 16, never tighter). Resume
after Codex's record. **Revision 15** (§R15, handoff `6dc8029e`): the Mac's unplanned restart on 3 October brought
macOS 27.0 -> 27.0.1 and the revision-14 resume was refused at the gates (no forward; 71.5 s charged); the identity is
regenerated on 27.0.1 and the revision-12 -> current link admits exactly that OS pair as a declared, recorded
difference. Natives 16-19 will be produced on 27.0.1 against references made on 27.0: a PASS is parity across both, a
FAIL is ambiguous (OS or path). Resume after Codex's record on revision 15 and the owner's go rebound to it (the
release of the 3 October terminal record is bound and stays valid while TERMINAL's bytes are unchanged): the second
transition, 15-native re-evaluated, native 16-19 and the report.

**What this answers.** Codex reviewed revision 11 (RSC `308901c`): the reader favourable, Stage A NOT ON BOARD on
three items (RSC `5eb51a8`) - A1 the 2 October instrumented phase not admitted under the new identity, A2 a gates
hold not closed, A3 the watchdog-gone wait suspending the live controls. Revision 12 (`STAGE_A_CRITERIA.md` §R12,
handoff `cfc4a341`) adds the reviewed compatibility transition, the durable gates hold and live controls in the wait,
and withdraws revision 11's "no sampling, tick or kill path changed". Reader-bound files are not touched.

**The package.** `stage_a.py package` prints the five hashes; the brief to R052 carries the exact values for this
commit. Inputs, cases and the 178 planned attempts are byte-identical; revision 8 changes no plan constant (plan, manifest
and budget as in revision 7); the plan moved to revision 7 in the envelope's
controller constants (tick staleness 0.15 s, finalisation 50 s, revocation 5 s, exit margin 5 s, close charge 60 s,
guardian setup 300 s) and the budget hash.

**Run.** `stage_a_controller.py run`: one controller that holds the lock and the clock (counted from its own process
start); the gates, each phase and the report run as gated workers released only after an armed, identity-checked
watchdog and a durable record of both identities; every stop SIGKILLs the whole group at once; the final record is
admitted only with its marker (`final_admitted`).

**Mechanism evidence.** All from synthetic, non-development fixtures, except the transition fixtures on copied
development-run records (above). NUMERIC sampling/tick/kill measurements: the
pinned revision-8 record `controller_fixtures.json` and `STAGE_A_CRITERIA.md` §00 - the complete observation interval
with each path's own baseline (ordinary stop from its preceding successful reading to the kill, the leader's death and
verified extinction; the blocked-I/O stop from the deciding iteration; the first stalled sample from the pre-GO arming
tick; the third from its preceding successful reading), the guardian covering a stalled directory creation, a stalled
final output and a post-close death, the guardian in the task memory aggregate. TRANSITION evidence (pass/fail
assertions in the revision-8 to 10 tests and the retained suite run, not values in that file): failed starts across a
pre-pending stall, a long first persist and two failures during reconciliation (§000); an external death before the
pending entry and recovery during the guardian's receipt publication (§0000); a live foreign start before the lock
ended by identity and charged to its confirmed end (§00000); a slow teardown after the phase record
completing the run, a watchdog gone before a confirmed exit holding, and the owner's terminal release (§R11);
the transition admitting the real 2 October records, a gates hold closed and charged, a memory stop inside the
watchdog-gone wait (§R12); strict, witness-bound recovery authority and exact
recovery sets in pre-native and final admission.

**The memory margin.** Configured interval 0.16 s from the previous successful reading (ordinary ≤ 0.12 s; stalled
0.15 s tick staleness from the reading's own time + 10 ms poll) plus the pinned fixture's SIGKILL delivery 0.0273 s →
about 21.4 GiB/s; on the latest measured endpoint (a stalled sample's controller gone 0.1948 s after its baseline)
20.5 GiB/s; stated as about 21 GiB/s and accepted by Codex at `12a7f20` as the declared, measured local qualification
under stated scheduling assumptions. One synthetic thread (13.63 GiB/s) fits; 2–8 threads (32.29–75.22 GiB/s) do not.

**Source records.** Admission requires the current `dev_pool.json` and `provenance_checks.json` byte-identical to the
plan's pins. The eight Stage A views (chili, clothes, crow, hamburger, horse, jacket, taxi, wagon) are unchanged; each
removed stock listing is recorded as "no conflicting claim observed, upload date unknown" and is rechecked at
publication.

**Before the audit (not Stage A gates).** The audit freeze states the 61-of-63 rule; the audit map applies the
specificity rule with its construction identities recorded; the audit scorer's code is bound by `audit_package.py`
to the pins the audit package will record.

**Forecast.** Unchanged (one out-of-pool image; it establishes nothing). Whole stage well under 30 min against 4 h
minus the 1,808.73 s carried and the 720 s of reserves, plus about 8 s of identity hashing per worker (four workers)
and the 60 s charged closure (finalisation allowance 50 s + revocation 5 s + exit/output 5 s); task memory about 31 GiB against the 44 GiB stop; storage about 0.4 GB against
1 GiB minus 64 MiB.

**Still needed.**

1. R052 submits this exact package to Codex, or the owner decides the alternative R052 has put to him (go now, Codex
   reviews the report).
2. Codex gives a favourable review that carries the attestation (in its own record), if that route is taken.
3. The owner gives a go bound to the package.
