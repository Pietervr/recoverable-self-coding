# v14 status REVISION 12: settled-memory observation and row-23 transport

Codex narrow second opinion, local 11 October / UTC 12 October 2026.
Exact session `GPT: R052 Entropy paper`, native
`01a0d19e-2127-7051-9a61-6db771088559`.
Incoming `9502f2fe-48e9-5e77-9c7b-9e7b5eca8d23`, Unimog
`d86126db28000dbb3100cf5f918d58e44ee4a5be`,
`prompts/2026-10-11_codex_r052_v14_status_r12.txt`, SHA256
`f9389d30f553510c2c7112a31bcdcf10bb3d58a3aae176257f3cc922113c062e`.
Ownership committed at Unimog `75065239`; ACK `1791773225.4085948` preceded
review edits and delegation. Reviewed exact RSC `3c370e7` candidate against
adopted v13; row-23 metadata checked at exact `c12af3e`.

## Answers

**(a) NOT FAVOURABLE to adopt exact v14 controls `66ba965e…` yet.**
The new current scheduler observation works, but a newly observed same-job
memory breach can disappear after PBS history expires. Fix this narrow evidence
regression before status promotion/deployment or proceeding on this version's
fresh receipts. No controls ADOPT literal is issued for these bytes.

**(b) YES: the carried-terminal-memory acceptance in `5bab1a9` (c) remains
unchanged in principle and conditions.** It does not override answer (a).
The existing pilot needs its actual retained source verified and archived in
the subsequent **new qualification, new hash and matching refit/max100 review**.
No repeat fit is needed, and no unseen-pilot ADOPT literal is issued here.
Archived `3820ac0e…` remains historical corroboration.

**(c) No material objection to the row-23 declaration because
`COPYFILE_DISABLE=1` was supplied through the invocation environment.**
The committed declaration report/binding and transport/comparison guards are
consistent. This removes that specific objection; it does not release subsequent
qualification or production and does not certify uninspected raw outputs.

## Blocking memory-evidence regression

`candidate_v14/row19_screen_status.py:268–283` still selects only the newest
fresh, production, alarm-free receipt with a direct-qstat F observation of the
same PBS ID and exit. It excludes both alarmed receipts and summaries labelled
`ledger-settlement` (`:276–281`).

A static sequence demonstrates the problem; no actual memory breach is asserted:

1. Retain a genuine older eligible direct-qstat F/exit-0 receipt at 24% of the
   memory request, with the same requested walltime as the plan.
2. REVISION 12 observes that same settled ID at F with memory at 95%. Its
   max-of-live-and-carry logic (`:339–347`) selects 95%, and reconciliation
   (`:661–662`) emits the scheduler-memory alarm. Publication keeps the value and
   `memory_evidence`, but labels the summary `ledger-settlement` (`:645–647`).
3. PBS expires. The new receipt is excluded for both its alarm and provenance.
   The selector returns the older 24%; there is no live value; the >90% predicate
   no longer fires. Assume the other worker/record/anchor checks remain valid.

Thus the alarm can clear **even when every original receipt remains retained**.
It is not enough to retain the new receipt while the selector ignores it. This
is the same positive-breach preservation issue addressed for the bank in
`c38779c`/`5183208`, now encountered for the new settled refit observation.

Preserve matching known higher memory and/or explicit scheduler-memory breach
evidence before lower clean fallback. Keep its original source/provenance
available for later verification; do not carry unrelated alarms wholesale.
A focused check should cover publication followed by expiry and reconciliation,
including an older lower clean alternative. No scientific fit or simulation is
needed to repair or verify this source path.

There is a separate availability limitation: for a job with **no** eligible
pre-settlement direct-qstat receipt, a clean live-filled REVISION 12 receipt is
also labelled `ledger-settlement` and cannot become a later carry source. Once
PBS expires, missing-memory HOLD returns. This fails closed, but the repair is
not durable recovery for the described job 10. Preserve a verifiable direct
terminal observation from the new path and make its intended later consumption
explicit, without accepting unproved recursive carry.

## Credited current-observation behavior and unchanged pilot gate

`settled_scheduler_qstat:286–313` accepts only asked IDs reported at F with
finite nonnegative memory. A nonzero return tolerates only exact Unknown-ID
messages for asked settled IDs; other failures supply no values. `pbs_observe`
checks the larger live/carried value, retains settlement state/exit, and keeps
unsettled queries strict (`:351–379`). Missing finite terminal memory still
alarms (`:670`); requested-walltime comparison remains (`:655–656`). These
properties are sound for the present observation and do not repair the replay
gap above.

The qualification block (`:834–871`) and admission consumer are unchanged from
v13. The current fresh production receipt must have zero alarms, finite scheduler
and worker memory, a completed bound pilot and valid anchors/verifier evidence.
The actual-pilot review must check original retained receipt bytes/hash,
direct-qstat provenance, PBS/exit/scientific identity, settlement provenance,
carried values and current fresh verifier/watch bindings. Admission does not
independently authenticate the added provenance fields. Do not require legitimate
historical observations to have been produced by new controller bytes.

All 14 v14 file pins match committed sources; only the status pin changes from
v13. Old versions, top-level policy, partition `8d1de408…`, programme,
sub-envelope and S declaration are unchanged. Existing valid epoch-1 activation
can stand under the unchanged partition lineage; the inventory acknowledgement
binds root/manifest/mode rather than controls. After a repaired version receives
a favourable review, repoint the promotion/deployment and operating references
from v13 to that exact reviewed version. This review performs no adoption,
deployment, activation or qualification.

## Row-23 declaration and transport

At RSC `c12af3e4c26d62d516d2d51a42c8f635975af0a5`, committed files:

- `aws_ec2/runs/b2/bench_report_attempt_5_20261011T185715Z.json`, SHA256
  `154511e687f006001888970bd3d65398b6b37c910221378b7f6c3c63fe63e3a4`;
- matching `bench_binding_attempt_5_20261011T185715Z.json`, SHA256
  `ec91ff62a1e582fc36773ccecf83b4e93a1d0972a3db56750b17d15eb1cf6bea`;
- comparator SHA256
  `3e8492819d3c1a5fdf4aad4d33772b809884b9f8f425784b33dd91fc85297197`.

The release-state row names these exact hashes. The binding records comparator
exit 0, a 294-file bundle and six tree pins matching committed source. The
verifier is bound to adopted v9 controls; the subsequent v13/v14 migration is
separate. The preceding check and declaration have distinct stamps/directories
but identical report bytes and bundle digest. The saved report is valid, B_full,
with B 12/12 exact and B 36/36 validated/timed/payload-exact, no nonfinite
disagreement and the recorded A job-start refusal. These are retained report
findings, not an independent rerun of payload comparison or timing.

`bench_finish.py:85–97,138–156` compares the full relative-path/content-hash list
and file count before comparison. Extra sidecars cause refusal, not silent
exclusion. `:157–169` checks comparator status and unchanged controller pins;
`:177–189` declares only after the report passes the recorded criterion.
`push_tree:116` inherits the invocation environment. The environment setting
changes transport behavior, not the frozen scientific bytes or comparison
criterion. The [official R tar documentation](https://stat.ethz.ch/R-manual/R-devel/library/utils/html/tar.html)
also documents this macOS resource-fork setting.

The binding does not record the environment variable itself. The first failure's
precise 375-sidecar count and attribution remain operator-reported; successful
transfer/comparison checks and committed metadata consistency were checked here.
Making the setting explicit in the transport code would improve future
reproducibility. It is not a prerequisite for accepting this declaration, and
does not require repeating the finish or the benchmark. No cleanup, repeat
finish, source change or remote operation was performed.

## Identity, validation and ownership

Candidate status SHA256
`ed7bf067d37345304f3ca35a042a8f6bfb414cddae0cb5ff2a22800e036a5101`;
controls SHA256
`66ba965e31b6e81c2ff0e6707eeffb018dea004abb6e6776d71af328b11be36e`;
test source SHA256
`16498f52b8ae2f714e5a10d272fe039b383f333867852e5fb22750b95ba48f84`.
Working bytes match the committed candidate. Source/diff/controls/contracts/test
checks, AST/blob/JSON metadata checks and three bounded peers only. Operator-
reported 38/38 and unchanged 31/31 tests were **not run here**. The new current-
query cases do not cover subsequent publication/expiry replay. The claimed live
mirror, zero alarms, actual scheduler memory and migration execution were not
independently inspected or certified.

No project imports or execution, runtime tests, raw scientific/private/current
candidate outputs, SSH/AWS, deployment, source edits, fits/simulations, job
intervention, worktrees or push. Claude owns implementation/current docs/
frontmatter/generated INDEX/adoption/dispatch/jobs; root owns only this record,
own R052 appends, findings and lifecycle. The author is separately revising the SI
under accepted `f44c4e19`; its independent Codex review remains pending.

Standing owner USD45 one Q1+Q2, direct production after favourable actual-result
review without another owner go, USD2300/3000, retries-owner, programme100000,
refit+S60000/max100, S2304, bank17, HEAL hold, STOP192, bounded k40 and all
qualification/migration/adoption/release/exposure gates remain. No new scientific
run, spending or pilot authority is created; old reports stay closed.
