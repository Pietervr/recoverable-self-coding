"""Step 2/3: the naming test that decides decisiveness (§3.1).

Each rendered clause is presented ALONE to a reader model and the model attempts to name the
concept; the clause counts decisive when the concept is named. This replaces the withdrawn K
threshold, which rested on a sharing count - a record of how many cues happened to ELICIT a word
in a production study, not of how many things the word is true of.

READER MODEL: ollama llama3.1:8b (Meta Llama 3.1 8B Instruct, Q4_K_M), served locally on
127.0.0.1:11434. It is distinct from the model under test (Qwen3.6-27B, Alibaba) and from the
model that renders the clauses (Claude, Anthropic), which is what §3.1 requires. The exact digest
is recorded in the output.

A clause counts NAMED when the concept word or any of its accepted surface forms appears in the
reader's answer, matched on word boundaries and case-insensitively.

    .venv-build/bin/python stimuli/norms_bank/naming_test.py <clauses.json>
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLLAMA = "http://127.0.0.1:11434/api/chat"
MODEL = "llama3.1:8b"
PROMPT = ("Here is a single clue about one everyday thing.\n\n"
          "Clue: {clause}\n\n"
          "What is being described? Answer with the single most likely word, and nothing else.")


def reader_identity() -> dict:
    out = subprocess.run(["ollama", "list"], capture_output=True, text=True).stdout
    digest = next((ln.split()[1] for ln in out.splitlines() if ln.startswith(MODEL)), "")
    return {"runner": "ollama", "model": MODEL, "digest": digest,
            "developer": "Meta", "quantization": "Q4_K_M"}


def ask(clause: str) -> str:
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT.format(clause=clause)}],
        "stream": False,
        "options": {"temperature": 0, "seed": 20260924, "num_predict": 12},
    }).encode()
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["message"]["content"].strip()


def named(answer: str, forms: list[str]) -> bool:
    return any(re.search(r"(?<![A-Za-z])" + re.escape(f) + r"(?![A-Za-z])", answer, re.IGNORECASE)
               for f in forms)


def main(argv: list[str]) -> int:
    data = json.loads(Path(argv[0]).read_text())
    ident = reader_identity()
    print(f"reader: {ident['model']} ({ident['developer']}, digest {ident['digest']}), "
          f"temperature 0\n")
    results = {}
    for cid, entry in data["clues"].items():
        forms = entry["surface_forms"]
        rows = []
        for i, clause in enumerate(entry["clauses"]):
            answer = ask(clause)
            hit = named(answer, forms)
            rows.append({"i": i, "clause": clause, "answer": answer, "named": hit,
                         "feature": entry["features"][i], "sharing": entry["sharing"][i]})
        n = sum(r["named"] for r in rows)
        verdict = "ACCEPT" if n <= 2 else "RE-SELECT or PASS OVER"
        results[cid] = {"named": n, "verdict": verdict, "rows": rows}
        print(f"=== {cid}: {n} of {len(rows)} clauses named -> {verdict}")
        for r in rows:
            flag = "NAMED" if r["named"] else "     "
            print(f"  {flag} [{r['feature']}/{r['sharing']}] {r['clause']}")
            print(f"        reader said: {r['answer']!r}")
        print()
    out = {"reader": ident, "prompt_template": PROMPT, "results": results}
    dest = Path(argv[1]) if len(argv) > 1 else HERE / "naming_test_results.json"
    dest.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"-> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
