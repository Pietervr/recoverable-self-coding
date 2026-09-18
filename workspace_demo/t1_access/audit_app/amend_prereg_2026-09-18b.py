"""Second draft amendment of 18 Sept 2026 to PREREGISTRATION_T1_model.md §3 and §15: the human readers are
anonymous and open. The owner forwarded the four part links and asked recipients to forward them on
("no personal names needed"), so a link is a part, not a person. Exact replacements, each matched once.
"""
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "PREREGISTRATION_T1_model.md"
t = P.read_text()

EDITS = [
    (" is read twice and independently: once by one of four human readers and once by an AI reader.",
     " is read independently by one or more anonymous human readers and by an AI reader."),
    ("Human readers work through a click-through page (audit.raconteur-road.com, one private link per reader) that"
     " asks the `CHECKLIST.md` questions in plain words and saves each answer as it is given; they work alone and"
     " see no model output and no other reader's marks. A clause or item passes only when both of its readers pass"
     " it; every other case is decided by the author, with both readers' marks and comments recorded beside the"
     " resolution. The frozen bank records each reader's name and part, the AI reader's model and version, and the"
     " dates.",
     "Human readers work through a click-through page (audit.raconteur-road.com, one link per part) that asks the"
     " `CHECKLIST.md` questions in plain words and saves each answer as it is given. The links were forwarded by"
     " the recipients, so each visitor's browser holds a private, anonymous session and answers are stored per"
     " session; readers see no model output and no other reader's answers, and the page shows each visitor the"
     " least-read cards of the part first. A clause or item passes only when it has at least one human read and"
     " the AI reader and every human reader pass it; every other case is decided by the author, with all readers'"
     " answers and comments recorded beside the resolution. The frozen bank records, per item, the number of human"
     " reads with their anonymous session ids and times, the AI reader's model and version, and the dates; no"
     " reader's name is recorded."),
]
for old, new in EDITS:
    assert t.count(old) == 1, old[:60]
    t = t.replace(old, new)

ROW = ("| 2026-09-18 | Draft amendment, second entry: the human readers are anonymous and open; answers stored per"
       " browser session; an item passes only with at least one human read and no reader's objection; no names"
       " recorded | the owner forwarded the part links for onward sharing (\"no personal names needed\"), so one"
       " link is not one person; the first page version kept one set of answers per link, and the 13 answers saved"
       " under it (part A) were kept under a legacy session |")
t = t.rstrip("\n") + "\n" + ROW + "\n"
P.write_text(t)
print("§3 paragraph revised; §15 row appended")
