# Screen controllers version 9 CANDIDATE (not adopted): the snapshot pull as one tar stream

Problem (10 Oct 2026). `fresh_snapshot` pulls the campaign and root with `scp -r` under the 900 s `sh()` timeout. Over
the WireGuard tunnel scp (SFTP mode) costs ~1.1 s per file (measured: 127 files in 141 s); the refit root reached 938
files, so every refit receipt now times out ("pull ... failed (rc 255)") and refit refills cannot pass the gate. The
bank root (733 files) sits just under the limit. Both receipts at 16:5x-17:25Z on 10 Oct failed this way.

Change (the only change in each file): `pull_tree(remote, local, timeout=900)` replaces the scp call - one ssh command
on the transfer node lists every regular file (sorted, to stderr), then streams `tar -cf - .`; the Mac extracts with
`tar -xf - -C local`. Accepted only when the local extractor exits 0, the remote exits 0 or 1 (GNU tar's
'file changed as we read it', the live-tree race scp had too), and every pre-archive file exists locally (temporary
`*.tmp.*` excepted). Same source paths, destination, timeout and failure reporting (rc 255 + reason); everything after
the pull (stage/live rotation, job-output fetch, verifier, receipts) is unchanged.

Evidence (read-only, 10 Oct ~17:45Z): refit root 950 files in 6.9 s, bank root 736 files in 5.1 s, both rc 0. A first
version that compared counts after the archive correctly REFUSED a pull during which a refit job-7 worker published
rec_001/t_001/status (950 vs 947); the pre-listing check above is race-tolerant without dropping any file that existed
when the pull began.

Files: `row19_screen_status.py` (controls version 9 when adopted), `row22_bank_status.py` (bank lane, not under the
screen controls), and their `.diff` against the adopted bytes.
