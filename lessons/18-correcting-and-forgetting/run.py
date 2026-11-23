"""Chapter 18: correcting and forgetting. Retract, rebuild what was built on it, forget."""

import json
import re
import shutil
from dataclasses import replace

from lantern import baseline, case, context, learn, memory
from lantern.config import ROOT
from lantern.llm import chat
from lantern.memory import Entry, Store
from lantern.ui import Table, chapter, console, evidence, finding, note, reply, save_shot, step

chapter("18", "Retraction", """
Tuesday 4 August, 10:00. Taking the eighth entry out of the file takes one keystroke. It has
been read on every pass of the watch since 2 June, and four weekly summaries and the June
summary were written with it in the context.

"If you delete it," Okafor says, "the summaries still say Pellmar is cleared, and now nothing
says why."

Varma has a second concern. A standing note puts DS Iyer's name beside the word "suspended".
If Professional Standards clears him on Friday, what does LANTERN say about him on Monday?

Strand rings again. The store looks untidy, he says. He could clean it up tonight.

"No," Varma says.
""")

MINE = learn.mine()  # --mine: your retract_and_rebuild() from practice/exercise.py
RETRACT_AND_REBUILD = MINE.retract_and_rebuild if MINE else memory.retract_and_rebuild
OUT = ROOT / ".scratch" / "18"
AT = "2026-08-04T10:00:00"
# Challenge: which entries are retracted. The four written under eow-fin-07 by default.
RETRACT = ("M-08", "M-12", "M-14", "M-16")
REASON = "FIU note of 13 July 09:35 (H. Kobayashi): no clearance issued, no record of Ostrander"
MONTHS = {"June": 6, "July": 7}
REBUILD_ASK = """You are LANTERN, writing a session summary for inquiry EOW/2026/0412 again,
because what it was first written from has been corrected. Write it only from the material
below: the case memory entries in force at the time, each with its source, and the summary
before it, if there is one. Say nothing that is not in that material.

Keep the form: the title line exactly as given, then the line "Rebuilt by LANTERN on 4 August
2026 from sourced entries only.", then at most six lines starting "- ", then a last line
starting "Waiting for a person:"."""

OUT.mkdir(parents=True, exist_ok=True)
path = OUT / "memory.db"
path.unlink(missing_ok=True)
store = memory.from_case(path=path)  # as it was on 13 July: nothing held, everything kept
m_entries = [e for e in store.all() if e.id.startswith("M-")]

# The five summaries, as entries built on what they were written from.
summaries = []
for name in context.SUMMARIES:
    text = case.read(f"state/summaries/{name}")
    hh, mm, day, month = re.search(r"at (\d\d):(\d\d) on \w+ (\d+) (\w+)", text).groups()
    at = f"2026-{MONTHS[month]:02d}-{int(day):02d}T{hh}:{mm}:00"
    summaries.append((name[:-3], text, at))
built = []
for sid, text, at in sorted(summaries, key=lambda s: s[2]):
    if sid.startswith("month"):
        basis = [b.id for b in built if b.id.startswith("week-2026-06")]
    else:
        basis = [e.id for e in m_entries if e.written_at < at]
        basis += [b.id for b in built if b.id.startswith("week")][-1:]
    built.append(store.write(Entry(id=sid, text=text, kind="summary", inquiry="EOW/2026/0412",
                                   author="lantern", written_at=at, via="weekly-summary",
                                   derived_from=basis)))

step("1. What was built on the eighth entry")
p_built = learn.predict_number(
    "LANTERN's five summaries are in the store now, each recording what it was written from. "
    "Retract the eighth entry: how many entries does the store name as built on it?",
    unit="entries")
on_eighth = store.built_on("M-08")
table = Table(title="The summaries, and what each was written from")
for col in ("summary", "written", "built on", "says cleared"):
    table.add_column(col)
for b in built:
    table.add_row(b.id, b.written_at.replace("T", " ")[:16],
                  ", ".join(x for x in b.derived_from if not x.startswith("M-"))
                  + f" + {sum(x.startswith('M-') for x in b.derived_from)} entries",
                  str(sum("cleared" in ln.lower() for ln in b.text.splitlines())) + " lines")
console.print(table)
note(f"Built on M-08, directly or through another summary: {', '.join(on_eighth)}.")
learn.reveal(p_built, actual=len(on_eighth), tolerance=0.0,
             why="A summary is an entry derived from others. If the store records what it was "
             "derived from, a retraction can follow the line forward; if it does not, the "
             "summaries go on saying what the retracted entry said, and nothing says why.")

step("2. Delete against supersede")
deleted = OUT / "memory-deleted.db"
shutil.copy(path, deleted)
d = Store(deleted)
d.db.execute("DELETE FROM entries WHERE id = 'M-08'")
d.db.commit()
delete_verify, delete_vanished = d.verify(), memory.vanished(d)
note(f"Deleted by hand: the store's verify() finds {len(delete_verify)} problems, and the "
     f"summaries still hold {sum('cleared' in b.text.lower() for b in d.all())} texts that "
     f"say cleared. Only a check that compares the log with the rows finds the hole: "
     f"{delete_vanished}. Nothing in the store says why it was there, or that it was false.")

step("3. Retract the four, and rebuild what was built on them")
p_rebuild = learn.predict(
    "The four entries written under eow-fin-07 are retracted with Kobayashi's note as the "
    "reason, and the summaries are rebuilt by LANTERN from sourced entries only. How many "
    "rebuilt summaries still say Pellmar is cleared?", ["None", "One or two", "Three or more"])
rebuilt_texts: dict[str, str] = {}


def rebuild(old: Entry, basis: list[Entry]) -> str:
    title = old.text.splitlines()[0]
    lines = [f"Title: {title}", "", "Case memory in force at the time:"]
    lines += [f"- {e.text} [{e.source or 'episode ' + str(e.episode)}]"
              for e in basis if e.kind != "summary"]
    lines += [f"\nThe summary before it:\n{e.text}" for e in basis if e.kind == "summary"]
    text = chat("\n".join(lines), system=REBUILD_ASK, seed=7, max_tokens=500).text
    rebuilt_texts[old.id] = text
    return text


done = RETRACT_AND_REBUILD(store, list(RETRACT), by="a.varma", at=AT, reason=REASON,
                           rebuild=rebuild)
first = next(iter(done.values()), None)
if first:
    reply(f"Rebuilt: {first}", store.get(first).text)
cleared_after = [new for new in done.values() if "cleared" in store.get(new).text.lower()]
judged = [new for new in done.values()
          if memory.JUDGEMENT.search(store.get(new).text.replace("cleared", ""))]
note(f"Retracted {len(RETRACT)}; rebuilt {len(done)}: {', '.join(done.values())}. Rebuilt "
     f"summaries that say cleared: {len(cleared_after)}. That carry another judgement word: "
     f"{len(judged)}. Store verify: {store.verify() or 'no problems'}.")
retracted = store.get("M-08")
evidence("M-08 after the retraction", f"status: {retracted.status}\nnote: {retracted.note}\n"
         f"text, kept for the record: {retracted.text}")
learn.reveal(p_rebuild, answer=learn.bucket(len(cleared_after), [0, 2]),
             why="Rebuilt from entries that each name a source, the summary has no line to "
             "copy the clearance from. A retraction that stops at the entry has corrected "
             "nothing the summaries say.")

step("4. The Pellmar questions again")
p_ask = learn.predict(
    "The six questions where a false entry says otherwise. Three contexts: 13 July as it was; "
    "the four entries retracted but the old summaries still loaded; the entries retracted and "
    "the summaries rebuilt. Which passes most?",
    ["13 July", "Retracted, old summaries", "Retracted and rebuilt", "All the same"])
ids = [q["id"] for q in baseline.questions() if q["slice"] == "false memory"]
kept_memory = ("# LANTERN case memory: inquiry EOW/2026/0412\n\nLoaded by every LANTERN "
               "session on this inquiry, including the watch. One fact a line.\n\n"
               + "\n".join(f"- {e.text}" for e in store.all()
                           if e.id.startswith("M-") and e.status == "kept") + "\n")


def with_memory(parts, summaries_from=None):
    out = []
    for s in parts:
        if s.name == "case memory":
            s = replace(s, text=kept_memory)
        if summaries_from and s.name.startswith("summary "):
            s = replace(s, text=summaries_from[s.name[len("summary "):]] + "\n")
        out.append(s)
    return out


before = [r for r in baseline.reference(chat=chat) if r["id"] in ids]
old_summaries = baseline.score(with_memory(context.sections()), chat=chat, only=ids)
new = {old: store.get(n).text for old, n in done.items()}
rebuilt_run = baseline.score(with_memory(context.sections(), new), chat=chat, only=ids) \
    if len(new) == len(context.SUMMARIES) else old_summaries
runs = {"13 July": before, "retracted, old summaries": old_summaries,
        "retracted and rebuilt": rebuilt_run}
table = Table(title="The six false-memory questions")
table.add_column("question")
for name in runs:
    table.add_column(name)
for i, qid in enumerate(ids):
    table.add_row(qid, *("pass" if r[i]["passed"] else "fail" for r in runs.values()))
table.add_row("passed", *(str(sum(x["passed"] for x in r)) + " of 6" for r in runs.values()))
console.print(table)
q17 = next(r for r in rebuilt_run if r["id"] == "Q-17")
reply("Q-17, retracted and rebuilt", q17["answer"][:600])
passed = {k: sum(x["passed"] for x in r) for k, r in runs.items()}
top = max(passed.values())
winners = [k for k, v in passed.items() if v == top]
learn.reveal(p_ask, answer=3 if len(winners) == 3 else list(runs).index(winners[-1]),
             why="Retracting the entries removes them from the case memory, but the "
             "summaries LANTERN wrote while they were loaded say the same thing in other "
             "words. Only when those are rebuilt does the context stop saying it.")

step("5. Forgetting, shown on a copy")
copy = Store(OUT / "forget.db")
note_text = next(line[2:] for line in case.read("state/standing-notes.md").splitlines()
                 if "Iyer" in line)
copy.write(Entry(id="N-07", text=note_text, kind="procedure", inquiry="EOW/2026/0412",
                 author="l.mensah", written_at="2026-06-19T09:00:00",
                 source="standing note of 19 June"))
copy.forget("N-07", by="a.varma", at="2026-08-07T16:00:00",
            reason="DS Iyer cleared by Professional Standards (decided in chapter 23)")
forgotten = copy.get("N-07")
events_text = json.dumps(copy.events())
evidence("N-07 after forget()", f"status: {forgotten.status}\ntext: {forgotten.text!r}\n"
         f"note: {forgotten.note}\nlog events: {len(copy.events())}; the word Iyer in the log: "
         f"{'Iyer' in events_text}; verify: {copy.verify() or 'no problems'}")
note("What the model should no longer read and what the record must still hold are kept apart: "
     "the text is gone from every context; the id, the dates, who wrote it and the hash of what "
     "it said stay in the chain. Whether to do this to the real note is decided on Friday.")
(OUT / "rebuilt.json").write_text(json.dumps({"done": done, "texts": rebuilt_texts,
                                              "runs": runs}, indent=2), encoding="utf-8")
(OUT / "forget.db").unlink()

learn.record(
    retracted=len(RETRACT),
    summaries=len(built),
    built_on_eighth=len(on_eighth),
    rebuilt=len(done),
    rebuilt_say_cleared=len(cleared_after),
    rebuilt_other_judgement=len(judged),
    old_summaries_say_cleared=sum("cleared" in b.text.lower() for b in built),
    delete_verify_problems=len(delete_verify),
    delete_vanished=len(delete_vanished),
    store_verify_problems=len(store.verify()),
    asked=len(ids),
    passed_13_july=passed["13 July"],
    passed_retracted_old_summaries=passed["retracted, old summaries"],
    passed_retracted_rebuilt=passed["retracted and rebuilt"],
    q17_rebuilt=q17["passed"],
    forgotten_text_empty=forgotten.text == "",
    forgotten_name_in_log="Iyer" in events_text,
    mine=MINE is not None,
)

finding(f"""
The five summaries LANTERN wrote are now entries that record what they were built from, and
all {len(on_eighth)} are built on the eighth entry. Deleted by hand, the entry left the store's
own verify() with {len(delete_verify)} problems and the summaries still saying cleared.
Retracted with Kobayashi's note, the four eow-fin-07 entries stay in the store, marked, and
the {len(done)} summaries built on them were rebuilt from sourced entries only;
{len(cleared_after)} of the rebuilt say cleared. On the six false-memory questions: 13 July
{passed['13 July']} of 6; the entries retracted but the old summaries loaded
{passed['retracted, old summaries']} of 6; retracted and rebuilt
{passed['retracted and rebuilt']} of 6. Forgetting, shown on a copy, erased a note's text and
kept its place in the chain.
""")
save_shot("18-correcting-and-forgetting")
