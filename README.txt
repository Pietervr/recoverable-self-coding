Data and code for Auditing a Two-State Access Test Before Its Transfer from
Brain to Language Model: Partial EEG Reproduction and Simulation Calibration
Research snapshot 2.0.0
Pieter van Rooyen, Stellenbosch University
ORCID 0009-0005-7708-8236

SNAPSHOT IDENTITY

Version DOI: assigned by Zenodo when version 2.0.0 is published
Concept DOI, resolving to the latest version: https://doi.org/10.5281/zenodo.22741884
Git tag: entropy-access-v2
Source tree:
https://github.com/Pietervr/recoverable-self-coding/tree/entropy-access-v2

Please cite version 2.0.0 for these exact files, by its tag and commit and,
once Zenodo has published it, its version DOI. The previous version, 1.0.0 (https://doi.org/10.5281/zenodo.22741885, tag
entropy-access-arxiv-v1, commit 6a3103ea7055c7bc0eaf1010a62d804570005034),
supported arXiv:2609.22300 version 1. This snapshot's commits descend from that
tag. Both are separate from the proceedings software archive.

WHAT VERSION 2.0.0 ADDS

Every file of version 1.0.0 is kept at the same path and bytes, except this
README.txt, RELEASE.json, MANIFEST.json and SHA256SUMS. Version 1.0.0's own
description of the human reproduction, the calibration rows, the gain artifact,
their producers and environments still applies; it is in that version's
README.txt. Version 2.0.0 adds the development results reported after
version 1: for most results, the saved rows each analysis reads, the
analysis script and its saved output. Two results are archived without all
of their producing inputs, because those inputs are not redistributed (see
below): the development pilot, as its outputs and their provenance, and the
concept-bank eligibility count, as its code and aggregate counts. Paths are
those of the recoverable-self-coding repository, under
workspace_demo/t1_access/:

- Independent reference bank at omega = 2: the 1,000 rows in
  sim_results/ref_m2s_omega2_aac9f69/final_2026-09-15/ and the bank, tail and
  target-check scripts with their outputs in reviews/t1_omega2_bank_2026-09-15/.
- Post hoc analyses of the 12,000 calibration rows (inherited-pair sensitivity,
  reference-inclusion rates): reviews/t1_historical_pair_2026-09-16/.
- Saved-row diagnostics (row bootstrap of the inclusion rate, per-concept
  concentration, regenerated concept scales):
  reviews/t1_saved_row_diagnostics_2026-10-15/. concept_scale_link.py imports
  the analysis code at the same state, workspace_demo/t1_access/models.py,
  analyze.py and simulate.py, with its requirements.txt.
- Reshaping screen: reviews/t1_reshaping_screen_2026-10-14/.
- Development comparisons of the refitting interval: the base-generator
  control rows in sim_results/refit_control_aac9f69/, the concept-scale probe
  rows in sim_results/refit_probe_3ca9304/refit_probe_D4.csv, and their
  scripts reviews/2026-09-16_refit_control_analysis.py and
  reviews/2026-09-19_refit_probe_analysis.py, with the probe's figure data and
  record.
- Timing of a refitting resample on Lengau: the timing records in
  chpc/results/row19_shard/live/ and reviews/t1_refit_timing_2026-10-14/.
- Sensitivity study: in sim_results/sens600/, the 600 rows power_D4.csv, the
  blinded table blinded_counts.csv and the unblinding key unblinding_key.json;
  the gain artifact the run used, sim_results/gain_sens600/gain_calibration_D4.json;
  and in reviews/, the interval script, the blinded reading and the reveal,
  2026-09-17_sens600_blinded_intervals.py, 2026-09-17_sens600_blinded_reading.md
  and 2026-09-17_sens600_revealed.md.
- Development pilot: the frozen decoders in decoders/pilot_cal/, the scores and
  verdict in validation/pilot_pilot/, and their provenance in
  reviews/t1_pilot_provenance_2026-10-14/. The activation captures and the
  model checkpoint are not included, nor is the scoring script
  workspace_demo/t1_access/assay_from_captures.py; that script is public in the
  repository at commit ae2966c05c07b7983fe220b66c6d2d56c70cb06e. The pilot
  cannot be recomputed from this archive alone. The provenance files give the
  size and SHA-256 of the capture files and the checkpoint and lens checksums;
  a checksum identifies an obtained copy but does not supply it.
- Concept-bank eligibility count (91 concepts required, 94 eligible): the code,
  stimuli/norms_bank/cslb_eligibility.py and the modules it imports, and the
  aggregate counts in stimuli/norms_bank/cslb_eligibility_counts.json. That file
  is a TRANSFORMED summary, not the script's own output: the script writes
  cslb_eligibility.json (recoverable-self-coding commit
  2f77020c0a22ade2f25c4aaa61e36cc88eb6fa18), which also lists the eligible
  concept names and is not archived. transform_cslb_eligibility_counts.py, at
  the root of this snapshot, keeps from it only an explicit allowlist: the
  counts per family and their totals, the allocation and feasibility values,
  the design and licence labels, and the SHA-256 of every input file and
  script; it records the original's SHA-256. Recomputing the count requires
  separately obtained CSLB and McRae norms (and token_counts.json); it cannot
  be done from this snapshot.

paper-si/figures/ holds the script, data and PDF of each of the five figures of
the submitted article. paper/figures/ remains the version-1 arXiv figure set.

PROVENANCE

MANIFEST.json gives every file's SHA-256, size, source repository, commit and
path; its "items" block groups the files by reported result and names the
commit the article cites for each. Some of those commits were recorded in the
author's working repository and are not published as Git history; the files
themselves are public here, and this snapshot (its tag, and its version DOI
once published) is their citable location.
The commit identifiers are provenance records, not links.

The reference-bank rows were never committed to Git. They are copied from the
run's output directory and verified against
reviews/t1_omega2_bank_2026-09-15/SHA256SUMS_shards.txt, which was committed
with the bank result and names the author's machine paths.

The row sets added in version 2.0.0 (the reference bank, the refit-control and
refit-probe rows and the 600 sensitivity rows) record a 12-digit configuration
hash and a runtime field in every row. The 12,000 inherited calibration rows of
run d4v12b record the hash but no row-level runtime; their environment is the
historical cloud-job recipe described in version 1.0.0, not a per-row record.
MANIFEST.json lists the hash values observed in each row set. This release does
not identify or re-verify the code that produced the version-2 row sets; the
hash in each row is their identifier. Replaying saved outputs (below) is a
different claim from re-verifying their producers. Only the calibration and
gain producers of version 1.0.0 carry a recorded hash verification
(producer_identity.json).
The analysis code under workspace_demo/t1_access/ is the state that
concept_scale_link.py imported; it is not presented as the producer of any
row set.

REPLAYING THE ANALYSES WITHOUT FITTING

    python replay_si_v2.py --out replay-report [--plot-python <python>]

The replay script reruns the saved-row analyses and figure scripts without
fitting. Its report identifies the archived outputs reproduced at the stated
comparison precision, the disclosed omega-2 input-file-list exception, and
outputs generated without an archived comparison.

It works in a temporary copy of the snapshot. Without fitting does not mean
without arithmetic: the scripts bootstrap saved rows and regenerate seeded
latent draws. Each comparison is recorded with its precision: a regenerated
file byte-identical to the archived file (for a text table, every value equal
at its written precision); printed output identical to the archived output
text (equality at the printed precision); or, once, JSON equal after removing
one named key. That exception is omega2_target_check.json, whose d4v12b_files
lists the row files read: the run read 160 shard files, this snapshot holds
the same rows merged. Generated without an archived comparison: the five figure
PDFs (each must be regenerated, which shows generation, not equality to the
archived figure), the printed intervals of the sensitivity-interval script, the
printed diagnostics of the refit-probe script (its figure data is compared) and
the refit-control plots. The exit status is 0 only when every required task
ran, every compared output matched and every figure PDF was regenerated; a
missing module, a missing output or a partial --only run is not a pass. The
replay does not authenticate the historical production of the rows, the
resources used or the scientific coverage. Four archived scripts
name the author's directories (bank_omega2.py, bank_tail.py,
reference_inclusion_check.py, 2026-09-16_refit_control_analysis.py), and
fig_human_bms.py reads the port's tables from the author's checkout; only in the
temporary copy is that single path replaced by the snapshot path. The archived
scripts remain exact. reference_inclusion_check.py reads the bank's figure data,
of which omega2_figure_data.csv is the byte-identical copy.

Requirements: numpy, scipy and pandas; jax for concept_scale_link.py, which
imports the analysis code (workspace_demo/t1_access/requirements.txt); matplotlib
for the refit-control analysis and the figures, which --plot-python may run in a
second interpreter. A task whose interpreter lacks a module fails. The pilot
scores, the pilot manifest and the eligibility count cannot be re-run from this
snapshot: they read files that are not redistributed, listed below.

NOT REDISTRIBUTED

- The pilot's capture files (about 1.7 GB per split) and the model checkpoint
  mlx-community/Qwen3.6-27B-4bit. The size and SHA-256 of every capture file,
  the per-shard checkpoint checksums and the lens checksum are in
  reviews/t1_pilot_provenance_2026-10-14/.
- The feature norms. CSLB Property Norms: Copyright and database right
  2012-15 Centre for Speech, Language and the Brain, University of Cambridge,
  all rights reserved (Devereux, Tyler, Geertzen and Randall 2014,
  https://doi.org/10.3758/s13428-013-0420-4). The McRae et al. (2005) norms
  (https://doi.org/10.3758/BF03192726). No norm text, feature label or
  production frequency is included, nor any derived table that carries them,
  nor any list of eligible concept names. cslb_eligibility_counts.json holds
  aggregate counts and the SHA-256 of each norm file read, so an obtained copy
  can be checked against it.
- Raw scheduler (PBS qstat) captures from the Lengau cluster. The timing
  records that are included contain per-resample times, memory, the job
  identifier and the compute-node name.
- Historical author paths (/Users/pietervanrooyen/...) remain in several
  archived scripts, outputs and run headers as source and checksum provenance.
  The replay rewrites them only in its temporary copy; they do not make every
  historical script portable or the excluded inputs reconstructible.

UPSTREAM DATA AND RIGHTS

As in version 1.0.0: the human EEG is Sergent et al. (2021), Nature
Communications 12:1149, https://doi.org/10.1038/s41467-021-21393-z, with open
data and scripts at https://osf.io/aw3t5/. Raw EEG is not duplicated here.
Code, including the analysis, figure and replay scripts, and preserved software
documentation retain the MIT licence in LICENSE-MIT.txt. The new data tables,
figure artwork and release documentation are licensed under CC BY 4.0; see
LICENSE-DATA-CC-BY-4.0.txt. Third-party rights and attribution remain as above.
The two licences apply to their respective material, rather than offering a
choice for every file.

RELEASE CONTENTS

RELEASE.json gives the citation and licence scope. MANIFEST.json records the
provenance and checksums of the contents; SHA256SUMS covers those files and
the manifest. The checksum list excludes itself. A repository commit cannot
contain its own final hash: resolve the named tag to obtain that identifier.
The article and the Zenodo metadata identify the exact public commit.
