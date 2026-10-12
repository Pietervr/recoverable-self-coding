# Refit job 13 slot 16: why the worker died (R052, 12 Oct 2026)

**Event.** Refit job 13 (`7531397.sched01`, cnode0892, start 2026-10-11T02:57:55Z) ended HELD 4 at 02:41:32Z on 12 Oct. Slot 16
(rep 83, index 2, the slot's only resample) logged 175 XLA/LLVM lines `execution_engine.cc:54] LLVM compilation error: Cannot
allocate memory` and `releaseMappedMemory failed with error: Cannot allocate memory` at 01:36:18-19Z, 22.6 h into the fit, and
bash reported `Segmentation fault` for that exact worker command (`fixture_refit13/row19_screen_refit_13.err`). No status, record
or timing exists for 83/2 (Lengau `records/rep83/` and `timing/rep83/` hold only indices 0 and 1). The other 23 workers ended 0.

**What the observations argue against (not proven).** Node- or job-wide memory exhaustion is unlikely: no other slot of job 13
(several were still fitting at 01:36Z) and no other refit log ever logged the error; job 13's scheduler memory was 46,155,404 kB
(36.7 % of the 120 GB request); worker resident sets are ~1-3 GB. `ulimit -v` is unlimited on the login node and `vm.overcommit_memory`
is 0 on the login node, cnode0359 and cnode0982 (cnode0892 itself was not read).

**Operator hypothesis: the per-process memory-map limit.** `vm.max_map_count` = 65,530 on the login node and the compute nodes
read (cnode0359, cnode0982). Read-only `/proc/<pid>/maps` samples of running workers on 12 Oct ~04:50Z:

| process | age | mappings | of which anonymous |
|---|---|---|---|
| slice 7525940, `row19_slice` call 7 (same fitting code, sequential) | 8.6 h | 39,653 -> 39,745 in 85 s | 38,869 |
| bank 11 worker (cnode0359) | ~33 h | 24,064 | 23,280 |
| bank 17 worker (cnode0982) | ~9 h | 21,154 | - |

The anonymous mappings are XLA's JIT code/data sections; they grow with the number of compiled executables a process holds.
The slice's rate (~4,000-4,600 mappings/h) reaches 65,530 in ~14-16 h; a refit fit that compiles more distinct shapes can reach
it inside one resample. An mmap refused at the limit returns ENOMEM, which LLVM reports as "Cannot allocate memory", and the
failed code-section release then crashes the process. The same mechanism was already the working diagnosis on 5 Oct, when four
of four long slice processes died after 41-57 h with this LLVM error at 2.6 of 8 GB resident; the slice was changed to a fresh
process per resample (`row19_slice_rep.pbs.template`, PROCESS RECYCLING). A refit shard worker already runs one resample per
process and cannot be split further.

**Unverified.** The crashed process's own map count was not recorded, so the limit is inferred, not observed. Whether 83/2
crashes again on a refill depends on whether its compile sequence (deterministic numerics; shape-dependent compilations) again
exceeds the limit: plausibly yes.

**Consequences for operations (no change made).** (1) The REVISION 14 disposition returns 83/2 to the planner; the next
ordinary refill re-plans it. The exposure is one slot (~23 core-h) per attempt, and a repeat crash is again fail-closed and
dispositioned. (2) The running slice call 7 is at ~39.7k mappings; previous calls lasted 15-17 h each and completed. Nothing is
stopped or changed (RUNBOOK "Never"). (3) A numerics-neutral mitigation for a repeat (for example a higher limit, which Lengau
users cannot set; an EC2 host where it can be set; or releasing compiled executables inside a fit) would be a separate reviewed
change.
