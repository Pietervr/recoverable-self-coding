"""Development probe: which surface form does the model rank first after "Answer:"?

The stimulus bank freezes one token id per concept "in the answer context" (§3). Whether that
id is the lower-case (' chair') or capitalised (' Chair') leading-space form is settled here, on
development concepts from none of the eight bank families (household objects and clothing), so
no bank concept is read. For each concept, eight clauses in the packet layout of
stimuli/packet.py, two carriers, instruction A and the answer suffix; the logits of ' x', ' X',
'x' and 'X' are requested and the top five recorded.

    workspace_demo/upstream/jlens-qwen36/.venv/bin/python workspace_demo/t1_access/probe_answer_form.py
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from capture import LOGS, Server, load_tokenizer  # noqa: E402
from stimuli.packet import ANSWER_SUFFIX, INSTRUCTION_A, build_ids, packet_text  # noqa: E402

DEV = {
    "chair": ["has four legs and a flat seat for one person", "usually stands at a desk or a dining table",
              "often has a straight back to lean against", "can be folded, stacked or put on small wheels",
              "is pulled out before someone sits down to eat", "may have armrests on both sides of the seat",
              "is found in classrooms, offices and kitchens", "is made for sitting rather than lying down"],
    "shirt": ["is worn on the upper body with buttons down the front", "comes with short or long sleeves and a collar",
              "is ironed before an office day or a formal dinner", "gets tucked into trousers or left hanging loose",
              "is folded and stacked in a wardrobe drawer", "can be plain white, striped or checked",
              "has a small pocket on the left side of the chest", "is washed after being worn for a day"],
    "lamp": ["gives light from a bulb under a fabric shade", "sits on a bedside table and is switched on at night",
             "plugs into a wall socket with a thin cord", "can be dimmed or angled toward a book",
             "stands in the corner of a living room", "is turned off before going to sleep",
             "has a small switch on its base or cord", "casts a warm circle of light on a desk"],
    "clock": ["has two hands that move around a numbered face", "hangs on a kitchen wall and ticks all day",
              "is wound up or runs on a small battery", "tells people when it is time to leave for work",
              "has a short hand for hours and a long one for minutes", "is set forward or back when the season changes",
              "may chime loudly every hour in a hallway", "shows the time from midnight to noon twice a day"],
    "bed": ["has a mattress, a pillow and warm blankets", "is where people sleep through the night",
            "stands against the wall of a bedroom", "is made neatly in the morning after waking",
            "can be single, double or king size", "has sheets that are changed once a week",
            "is where a sick person stays all day", "often has a headboard at one end"],
    "cup": ["holds hot tea or coffee in the morning", "has a small curved handle on one side",
            "sits on a saucer in an old cafe", "is rinsed and dried after each drink",
            "is made of ceramic and chips when dropped", "holds about a quarter of a litre",
            "is lifted to the lips to take a sip", "hangs on a hook above the kitchen sink"],
    "door": ["opens and closes on metal hinges", "has a handle or knob to turn",
             "is locked with a key at night", "lets people walk from one room to another",
             "can be knocked on by a visitor", "sometimes creaks when it swings slowly",
             "is painted and set into a wooden frame", "is held open with a small wedge"],
    "hat": ["is worn on the head to keep off the sun", "has a brim that shades the eyes",
            "is taken off indoors as a sign of politeness", "can be made of straw, felt or wool",
            "is hung on a hook by the front door", "keeps the ears warm on a cold day",
            "is tipped as a greeting to a neighbour", "sometimes blows away in a strong wind"],
    "mirror": ["shows a reflection of whoever stands in front of it", "hangs above the bathroom sink",
               "is checked before leaving the house", "is made of glass with a silver backing",
               "breaks into sharp pieces when it falls", "makes a small room look larger",
               "is used to fix hair or straighten a tie", "reverses left and right in its image"],
    "candle": ["gives a small flame from a wax stick", "is lit during a power cut",
               "slowly melts and drips as it burns", "is placed on a birthday cake",
               "has a cotton wick in its centre", "is blown out with a short breath",
               "smells of vanilla or lavender when scented", "stands in a holder on a dinner table"],
}
CARRIERS = [("Here are some notes a visitor wrote:", "Those were all the notes."),
            ("A friend described something in a few short lines:", "That is the whole description.")]


def main() -> int:
    server = Server()
    info = server.info()
    tok = load_tokenizer(info)
    rows = []
    for concept, clauses in DEV.items():
        forms = {"sp_lower": " " + concept, "sp_cap": " " + concept.capitalize(),
                 "lower": concept, "cap": concept.capitalize()}
        ids = {}
        for k, f in forms.items():
            enc = tok.encode(f, add_special_tokens=False)
            ids[k] = enc[0] if len(enc) == 1 else None
        req = sorted({v for v in ids.values() if v is not None})
        for carrier in CARRIERS:
            b = build_ids(tok, packet_text(INSTRUCTION_A, carrier[0], clauses, carrier[1]), ANSWER_SUFFIX)
            r = server.capture({"input_ids": b["ids"], "readout_positions": [b["readout_position"]],
                                "capture_layers": [63], "request_token_ids": req, "top_k": 5})
            logit = {x["id"]: x["logit"] for x in r["requested"]}
            by_form = {k: (logit[v] - r["logsumexp"] if v is not None else None) for k, v in ids.items()}
            best = max((k for k in by_form if by_form[k] is not None), key=lambda k: by_form[k])
            row = {"concept": concept, "carrier": carrier[0], "n_tokens": len(b["ids"]), "ids": ids,
                   "logprob": by_form, "best_form": best,
                   "top5": [tok.decode([t]) for t in r["top_ids"]], "extend_s": r["timing_s"]["extend"]}
            rows.append(row)
            print(f"{concept:>7} | best {best:<8} | lp " +
                  " ".join(f"{k}={v:.2f}" if v is not None else f"{k}=n/a" for k, v in by_form.items()) +
                  f" | top5 {row['top5']} | {row['extend_s']:.2f} s")
    counts = {}
    for r in rows:
        counts[r["best_form"]] = counts.get(r["best_form"], 0) + 1
    top1_is_form = sum(r["top5"][0].strip().lower() == r["concept"] for r in rows)
    summary = {"n": len(rows), "best_form_counts": counts, "top1_is_concept_any_case": top1_is_form,
               "median_extend_s": statistics.median(r["extend_s"] for r in rows)}
    print(json.dumps(summary, indent=1))
    LOGS.mkdir(exist_ok=True)
    out = LOGS / f"answer_form_probe_{time.strftime('%Y%m%dT%H%M%S')}.json"
    out.write_text(json.dumps({"summary": summary, "rows": rows, "server": info}, indent=1))
    print(f"written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
