"""AI image-reader qualification, revision 12: the IMAGES and the reader-side SET (framework §8.2 reader rule, R052
2 Oct 2026; Codex RSC cf3e49e and 7048bb8, not favourable to revisions 1 and 2; R052 handoffs 7f25830e and 742146ad).
Nothing here calls a model.

    .venv-build/bin/python stimuli/photo/ai_reader_key.py      # the key (needs WordNet) - first
    .venv-image/bin/python stimuli/photo/ai_reader_qual.py      # the images + ai_reader_qual_set.json

WHAT IS QUALIFIED. The free-naming judgement of the image audit, and only that: an AI reader from a different
developer than the model under test (Codex) names 300 THINGSplus photographs outside the development pool, each as
the colour original and as our grayscale clean canvas (dose pipeline, a = 1: fitting, padding, luma, contrast
normalisation, clipping and quantisation - not just colour removal). The THINGSplus per-image recognition norm
(Experiment 3 of Mukherjee et al. 2026: a best label chosen from a searchable menu of the 1,854 labels, 8-22
ratings per image here) is a DIFFICULTY REFERENCE and an item diagnostic - not a free-naming measure, not
individual human verdicts, and never read as human equivalence. Admission is decided on grayscale only
(`ai_reader_score.py`); colour is the external human-reference diagnostic.

THE TASK (revision 12, the owner's decision of 3 October 2026; repair 1 before it): the frozen PROMPT below, alone
with one image, in a fresh stateless image-only request - the most common name for the object in one or two words, or
'unclear'. The same prompt is the image audit's question 1. Revision 11's prompt ("one short noun or noun phrase")
invited the noun phrases its whole-answer key then refused; the answers are now scored by the shared matching rule
(ai_reader_key.names_concept). No label, menu, caption, path, concept, sense, prior answer or the
item's other view. This task is separate from the target model's single-token naming convention.

THIS FILE writes, to captures/ai_reader_qual/ (git-ignored), one file per REQUEST named by its opaque request id -
<request>.jpg for the colour original (the release file's bytes, unchanged) and <request>.png for the grayscale
canvas - and ai_reader_qual_set.json, the reader-side record, which carries NO label: per request its opaque item,
view, file, bytes and sha256; the frozen delivery order (a seeded permutation of all 600 requests, colour and gray
of one item never adjacent by construction of the check below); the prompt and its hash; the reader identity;
stratum and easy counts; the frame's exclusion counts; and the per-image SOURCE BASIS. The labels, aliases, human
norms and senses are in the key (`ai_reader_qual_key.json`), which only the orchestrator reads.

SOURCE BASIS (R052's ruling, §8.2; accepted by Codex as a project scope rule, RSC 7048bb8): qualification is a
RESTRICTED PRIVATE USE resting on the release's collective CC0/public-domain statement and its misattribution caveat;
the per-image provenance of these 300 is UNVERIFIED and the known conflicts are excluded. The images are never
captured as stimuli, published or redistributed; each is transmitted to the external reader for a naming answer -
600 planned transmissions (colour and grayscale), up to 660 attempts with repeats on permitted failures - and is
reported by opaque id with aggregate scores. The capture gate's per-image check is not required for these
transmissions and qualification clears no image for formal reuse. Each image records the collective THINGSplus basis
- the release zip, notice and LICENSE hashes and OSF ids, the download date and the misattribution caveat.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ai_reader_frame as F  # noqa: E402
import dose  # noqa: E402

OUT = HERE.parents[1] / "captures" / "ai_reader_qual"
SET = HERE / "ai_reader_qual_set.json"
KEY = HERE / "ai_reader_qual_key.json"
ORDER_SEED = 20261008
PROMPT = ("Look at this picture. What is the main object in it? Answer with the most common name for the object, "
          "in one or two words, or with the single word 'unclear' if you cannot tell. Reply with the name only.")
READER = {"product": "OpenAI Codex CLI (codex exec)", "cli_version": "codex-cli 0.159.3", "model": "gpt-6.1-sol",
          "reasoning_effort": "medium", "delivery": "one image attached with -i to a fresh ephemeral exec session, the "
          "prompt after '--', under a sandbox-exec ALLOWLIST (deny by default: only the codex binary may run; reads "
          "only of the attempt directory with the image, the auth file, the codex binary and the system runtime), "
          "pinned minimal environment, private CODEX_HOME holding only the auth link, user config, rules and optional "
          "instructions off, read-only, web search and tool features disabled (unified_exec cannot be, and no program "
          "but codex may run); the prompt-input and exec-invocation receipts and the JSONL event stream checked "
          "(ai_reader_runtime.py, ai_reader_exec.py)"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    d = F.draw()
    key = json.loads(KEY.read_text())
    if sorted(key["items"]) != sorted(x["item"] for x in d["chosen"]):
        raise SystemExit("the key and this draw disagree: rebuild the key first (ai_reader_key.py)")
    release = json.loads((HERE / "manifest_dev.json").read_text())["release"]
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.iterdir():                          # revision 1's q###_*.jpg/png and any stale files
        if old.is_file() and old.suffix in (".jpg", ".png"):
            old.unlink()
    requests = []
    for x in d["chosen"]:
        src = F.THINGS / "cc0" / "object_images_CC0" / f"{x['concept']}.jpg"
        raw = src.read_bytes()
        canvas, _ = dose.load_canvas(src)
        S = dose.signal(dose.luma(canvas))
        rgb8, _ = dose.quantise(dose.mix(S, S * 0.0, 1.0))
        png = dose.to_png(rgb8)
        for view, data, ext in (("colour", raw, ".jpg"), ("gray", png, ".png")):
            rq = x["requests"][view]
            (OUT / f"{rq}{ext}").write_bytes(data)
            requests.append({"request": rq, "item": x["item"], "view": view, "file": f"{rq}{ext}",
                             "bytes": len(data), "sha256": sha(data),
                             "source_basis": "THINGSplus collective release (see 'release')" if view == "colour" else
                             "derived from the THINGSplus release file by the dose pipeline (a = 1)"})
    rng = random.Random(ORDER_SEED)
    order = [r["request"] for r in sorted(requests, key=lambda r: r["request"])]
    while True:                                        # a seeded permutation with no item's two views adjacent
        rng.shuffle(order)
        item_of = {r["request"]: r["item"] for r in requests}
        if all(item_of[a] != item_of[b] for a, b in zip(order, order[1:])):
            break
    strata = {s: sum(1 for x in d["chosen"] if x["stratum"] == s) for s in (0, 1, 2)}
    out = {"revision": 12, "note": "Reader-side record of the AI-reader qualification: no labels. The key is "
           "ai_reader_qual_key.json (orchestrator only).", "seed": F.SEED, "order_seed": ORDER_SEED,
           "n_items": len(d["chosen"]), "n_requests": len(requests), "easy_items": sum(x["easy"] for x in d["chosen"]),
           "strata": strata, "cuts": d["cuts"], "frame_size": d["n_frame"],
           "frame_exclusion_counts": d["exclusion_counts"], "prompt": PROMPT, "prompt_sha256": sha(PROMPT.encode()),
           "reader": READER, "release": release, "requests": requests, "delivery_order": order,
           "key_sha256": sha(KEY.read_bytes()),
           "code_sha256": {n: sha((HERE / n).read_bytes()) for n in ("ai_reader_frame.py", "ai_reader_key.py",
                                                                     "ai_reader_qual.py", "dose.py")}}
    SET.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"{len(requests)} requests for {len(d['chosen'])} items; easy {out['easy_items']}; strata {strata}; "
          f"prompt {out['prompt_sha256'][:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
