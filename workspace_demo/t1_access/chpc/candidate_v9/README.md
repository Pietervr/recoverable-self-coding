# Screen controllers version 9 CANDIDATE (not adopted): the snapshot pull as one tar stream

Problem (10 Oct 2026). `fresh_snapshot` pulls the campaign and root with `scp -r` under the 900 s `sh()` timeout. Over
the WireGuard tunnel scp (SFTP mode) costs ~1.1 s per file (measured: 127 files in 141 s); the refit root reached 938
files, so every refit receipt now times out ("pull ... failed (rc 255)") and refit refills cannot pass the gate. The
bank root (733 files) sits just under the limit. Both receipts at 16:5x-17:25Z on 10 Oct failed this way.

Change (revision 2 of the candidate, after Codex RSC 137b261 V9-1..V9-3; the only change in each status file):
`pull_tree(remote, local, timeout=900)` replaces the scp call. The remote half (`_PULL_REMOTE`, run under bash) has
explicit phases - cd, a complete listing into a remote temp file, the sorted listing on stderr closed by
`LISTING-END <n>`, GNU tar on stdout closed by `TAR-RC <rc>` - and any failed phase prints `PHASE <name> FAILED` and
exits non-zero. Locally, ssh's stderr goes to a task-owned temp file (no pipe-capacity deadlock for any listing size),
and one deadline bounds the whole transfer; on any failure both children are terminated, killed if needed, and reaped.
Accepted only when the local extractor exits 0, every marker is present, LISTING-END equals the names received,
TAR-RC is 0 or 1 (GNU tar's 'file changed as we read it', reported in the note) and equals ssh's exit, and every
listed file exists locally except the publishers' temporary names `<path>.tmp` (row19_ledger.write_atomic) and
`<path>.tmp.<pid>` (row19_shard.publish, row19_screen_orig). Everything after the pull is unchanged; a failed pull
keeps the old live snapshot.

Lineage (V9-3): `row19_screen_controls.json` here is the candidate controls file - the adopted v8 file (9f736222...)
with ONE appended version 9 entry whose pins equal v8's except `chpc/row19_screen_status.py` = this candidate's bytes;
every other pin was re-hashed against the files on disk. Its own SHA-256 is what a literal ADOPT line would name. Nothing
is promoted before review; after promotion a fresh generation-9 whole-role observation and qualification from the
retained pilot evidence, then the digest-bound refit adoption, precede further gated refit admissions (no new pilot fits).
The bank status change is the bank lane's own transport repair (its raw-bank scope and job cap unchanged).

Evidence: `test_pull_tree.py` (stub ssh, local): 60,000-file tree pulled completely (listing ~1.9 MB), missing
directory -> PHASE cd FAILED, unreadable subdirectory -> PHASE find FAILED, truncated stream refused, a hung remote
refused at a 3 s deadline with no stray child, temp-name rule exact - ALL PASS for both files. Live read-only pulls
10 Oct ~18:15Z: refit root 1,019 files in 23.4 s, bank root 768 files in 12.4 s, rc 0.

Files: `row19_screen_status.py`, `row22_bank_status.py`, `row19_screen_controls.json` (candidate), their `.diff`
against the adopted bytes, `test_pull_tree.py` + `stub_ssh.sh`.
