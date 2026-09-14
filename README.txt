Data and code for Testing Two-State Access in Brain and Language Model:
Human EEG Reproduction, Simulation Audit, and a Proposed Model Assay
Research snapshot 1.0.0 for arXiv version 1
Pieter van Rooyen, Stellenbosch University
ORCID 0009-0005-7708-8236

SNAPSHOT IDENTITY

Version DOI: https://doi.org/10.5281/zenodo.22741885
Git tag: entropy-access-arxiv-v1
Source tree:
https://github.com/Pietervr/recoverable-self-coding/tree/entropy-access-arxiv-v1

Please cite version 1.0.0 and its version DOI for these exact files. The Zenodo
landing page supplies the link to all versions as the study develops. This is
a separate study snapshot from the proceedings archive.

This snapshot contains the completed human EEG reproduction and the one-layer
simulation audit reported in the article. It does not contain a confirmatory
language-model study or results from the second EEG dataset.

CONTENTS AND PROVENANCE

MANIFEST.json identifies every included file with a full SHA-256 and its source.
SHA256SUMS also covers the manifest. The human reproduction code and aggregate,
fit, score and diagnostic tables are preserved at RSC commit
e341319f5c6e0ce27fdeeb83ca6124009b7e0996, under workspace_demo/sergent_port/.
Its README and RESULTS_sergent describe the inherited validation limitations,
deviations, optimizer sensitivity and upstream data provenance.
They are preserved historical documentation. The article qualifies three
overstatements against the archived tables: active 645 ms pxp is 0.934929,
passive graded pxp reaches 0.526263 at 585 ms, and the passive max6 sensitivity
changes the winning model at 615 ms. The tabular outputs are unchanged.

The 12,000 calibration rows are the exact d4v12b/calibration_D4.csv, SHA-256
7762f152aaeb00fb8f0b36e453c4c57fc04f0f1910bb265ed8a0d9d19211babb.
Their producer code is preserved in producers/calibration_52267ec/ at commit
52267ec1f9cd84fe02016770b083312a59a19194. The analysis/settings hash is
b29215469af9. This historical producer has the historical failure handling;
later finite-decision guards must not be attributed retrospectively to it.

The accepted twelve-pair gain artifact is
gain_local_9b277df/gain_calibration_D4.json, SHA-256
38a67e1c8caa76c4bdefbc0e22a59b62678ef3d8e902e53b0b88ee6d3e0a8697.
Its producer is preserved in producers/gain_9b277df/ at commit
9b277df59af7807d34f6e99cb718ab1b1734aec1. Its analysis/settings hash is
d77c3ecc161e. The local run used D=4, layer 41, seed 2026, four inner starts
and the concept-cluster interval. Each pair used 32 calibration and 64 check
concepts per family; none used the discontinuity fallback. The check SE is
conditional on its fitted reference; it is not a global-optimality guarantee.

producer_identity.json records that both historical settings hashes reproduce
from these exact code files. That verification imports modules and computes
configuration hashes only; it runs no fits or simulations.

REPRODUCING FIGURES WITHOUT FITTING

paper/figures/ contains the exact article figure scripts, their tabular inputs
and the two PDF figures. With numpy and matplotlib installed, run:

    python replay_figures.py --out regenerated-figures

The adapter changes only the human script's machine-specific input directory
in memory and writes to a temporary copy. The original scripts remain exact.
It verifies the regenerated human figure CSV against the archived bytes.
The calibration summary is an existing aggregate input, not a new simulation.

ENVIRONMENTS

environments/ records direct dependency versions from the gain artifact, the
human run's contemporaneous README and the historical cloud pinning recipe.
These are not complete historical transitive locks. The calibration rows carry
no runtime field; the cloud recipe alone does not prove their runtime. The
current proceedings requirements-lock.txt describes a different experiment and
is intentionally not substituted for these records.
Each historical producer also includes its exact checked-in requirements.txt.
Those local package pins match the gain runtime's named packages; they are not
evidence of the cloud workers' installed versions. The figure replay executed
in a separate plotting environment, recorded in the release verification.

UPSTREAM DATA AND RIGHTS

Raw EEG, source workbooks and per-trial metadata are not duplicated here.
Sergent et al. (2021), Nature Communications 12:1149:
https://doi.org/10.1038/s41467-021-21393-z
Open EEG and authors' scripts: https://osf.io/aw3t5/ (CC0 as recorded by the port).
The published comparison values derive from the article's Source Data under
CC BY 4.0; attribution and the exact workbook link are in the port README.
Code, including the figure and replay scripts, and preserved software
documentation retain the MIT licence in LICENSE-MIT.txt. The new data tables,
figure artwork and release documentation are licensed under CC BY 4.0; see
LICENSE-DATA-CC-BY-4.0.txt. Third-party rights and attribution remain as above;
CC0 source material retains its public-domain status. The two licences apply
to their respective material, rather than offering a choice for every file.

RELEASE CONTENTS

RELEASE.json gives the citation and licence scope. MANIFEST.json records the
provenance and checksums of the contents; SHA256SUMS covers those files and
the manifest. The checksum list excludes itself. A repository commit cannot
contain its own final hash: resolve the named tag to obtain that identifier.
The manuscript and the Zenodo metadata identify the exact public commit.
