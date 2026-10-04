"""Fresh-process harness for the image-audit CLI fixtures (tests/test_ai_audit_cli.py): runs the PUBLIC entry point
`ai_audit_exec.main(argv)` of the copy of the package this file sits in (a temporary repository), in its own process.

Only the PROVIDER is substituted, and only here: the reader binary at the owned-CLI path of the temporary copy is a
fake (tests/fake_codex.py behind a wrapper reporting the pinned version); the sandbox-exec wrapper is dropped, because a
Python fake cannot run under the codex-only allowlist; the exec-invocation receipt, which parses the real CLI's debug
log, is replaced by a stub saying so. Everything else - construction order, configure, the chain, the set check, the
go guard, the journal, the clock, the receipts per attempt - is the production code of the copy.

    <venv>/python tests/audit_cli_harness.py run 1        (TMPDIR points the attempts root and fake plan into the test)
"""

from __future__ import annotations

import sys
from pathlib import Path

PHOTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PHOTO))
import ai_reader_runtime as R  # noqa: E402

R.boxed = lambda adir, argv, sandbox=True, prof="profile.sb": list(argv)          # no sandbox-exec around the fake
R.invocation_receipt = lambda *a, **k: {"equivalent": True, "user_input_exact": True,
                                        "note": "fixture stub: the fake binary writes no debug log"}

import ai_audit_exec  # noqa: E402

if __name__ == "__main__":
    sys.exit(ai_audit_exec.main(sys.argv[1:]))
