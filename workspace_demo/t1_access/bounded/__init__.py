"""t1_access/bounded — the bounded-comparison qualification (R052; DRAFT, not adopted).

Production code for the candidate of reviews/2026-10-27_method_repair_codex_record.md S1 (the point procedure) and S3
(the qualification catalogue). The audited files models.py, analyze.py and simulate.py are imported, never edited:
their bytes define the configuration hash of every published row. The one change to the loaded model family is the
registration of the mixture member M3S into models.MEMBERS at import time of bounded.members (in memory only).

Modules: members (M3S and the per-member start recipe), procedure (the point pipeline), calibrate (the order-statistic
interval, critical value and decision rule), generators (the 30-setting catalogue and its datasets), run_point (CLI:
one setting x replicate -> one JSON row). The design-freeze draft is DESIGN_bounded_v1.md beside them.
"""
import hashlib
import os
import sys

with open(__file__, "rb") as _fh:
    LOADED_SOURCE_DIGEST = hashlib.sha256(_fh.read()).hexdigest()          # bound at this module's own import (B1)

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.dirname(HERE)
if T1 not in sys.path:                      # models / analyze / simulate live one level up
    sys.path.insert(0, T1)
