"""Chapter 11: notes and scratchpads. The agent's own record, outside the window, with sources."""

import json

from lantern import agent, compaction, context, learn, trail
from lantern.config import ROOT, load_config
from lantern.llm import chat
from lantern.notes import RULE, Notebook
from lantern.ui import Table, chapter, console, evidence, finding, note, reply, save_shot, step

chapter(
    "11",
    "Its own notes",
    """
Friday 24 July, 09:00. A detective who loses her notebook starts the interview again. LANTERN,
after a compaction, has only what the summary kept.

"Give it a notebook," Mensah says.

Case file 02 gave it a memory file, and the file kept its mistakes along with its findings. This
is narrower: working notes for one task, in a form code can read, kept outside the window and
opened when needed.

Varma asks the only question she ever asks about a new record. "Who can write in it?"

"The agent. Only for this run. And every line says which statement it came from."

"Then I can check it," she says.
""",
)

MINE = learn.mine()  # --mine: your problem_with() from practice/exercise.py
OUT = ROOT / ".scratch" / "11"
RESERVE = 600
THRESHOLD = 1500
MAX_TURNS = 30
# The first session is stopped after this many requests, as if the workstation had restarted.
# Challenge: stop it earlier or later and see what the second session has to do again.
RESTART_AFTER = 8


def book_at(name: str) -> Notebook:
    path = OUT / f"{name}.json"
    path.unlink(missing_ok=True)
    book = Notebook.open(path)
    if MINE:
        book.problem_with = lambda *a: MINE.problem_with(*a, digest=trail.digest,
                                                         holder_of=trail.holder_of)
    return book


def session(book: Notebook | None, *, turns: int, compact: bool, opened: list[str],
            carry: str = ""):
    """One session of the trace. `book` adds the notes tools; `carry` is what is read back in
    at the start; `compact` compacts to a paragraph, as chapter 10's lossy arm did."""
    text, names = trail.listing(True)
    schemas, handlers, opened_now = trail.tools(names)
    rules = trail.RULES
    if book:
        note_schemas, note_handlers = book.tools()
        schemas, handlers, rules = schemas + note_schemas, {**handlers, **note_handlers}, \
            rules + RULE
    log = compaction.Log()
    paragraph = compaction.free_text(chat, THRESHOLD, context.count_tokens, log)

    def before(messages):
        was = len(messages)
        messages = paragraph(messages) if compact else messages
        if book and len(messages) < was:  # just compacted: put the notebook back in front
            messages = [*messages, {"role": "user", "content": book.text()}]
        return messages

    def until(report: str):
        return trail.not_done([*opened, *opened_now])(report)

    task = trail.TASK + ("\n\n" + carry if carry else "")
    run = agent.run([{"role": "system", "content": rules + text},
                     {"role": "user", "content": task}], chat=chat, schemas=schemas,
                    handlers=handlers, max_turns=turns, max_tokens=RESERVE,
                    limit=window - RESERVE, until=until, before_request=before)
    return run, list(dict.fromkeys(opened_now)), log


def row(table, name, runs, opened, book):
    g = trail.grade(runs[-1].answer)
    table.add_row(name, f"{g['found']} of {len(want)}", str(g["totals_right"]),
                  str(sum(len(r.turns) for r in runs)),
                  f"{sum(r.total_prompt_tokens for r in runs):,}", str(len(set(opened))),
                  f"{len(book.flows)} kept, {len(book.refused)} refused" if book else "",
                  runs[-1].stopped.split(":")[0])
    return g


OUT.mkdir(parents=True, exist_ok=True)
window = load_config()["generation"]["num_ctx"]
want = trail.expected()

step("1. A notebook that checks what is written in it")
demo = book_at("demo")
good = demo.note_flow("Corvane Trading Ltd", "Lowmarsh Shipping Services Ltd", 9, "2262000.00",
                      "corvane-trading.csv")
no_source = demo.note_flow("Corvane Trading Ltd", "Lowmarsh Shipping Services Ltd", 9,
                           "2262000.00", "")
wrong = demo.note_flow("Corvane Trading Ltd", "Arden Logistics Ltd", 14, "1625000.00",
                       "corvane-trading.csv")
evidence("note_flow, three attempts", "\n".join(json.dumps(x) for x in (good, no_source, wrong)))
note("The third is the mistake LANTERN's own summary made in chapter 09: Arden as a payee of "
     "Corvane's. The notebook compares a note with its source's digest before keeping it.")

step("2. A compaction in the middle, without notes and with")
p_notes = learn.predict(
    "The trace is compacted to a paragraph whenever it passes 1,500 tokens, which lost the "
    "trail in chapter 10. This time LANTERN has a notebook, read back after every compaction. "
    "How many of the 7 hops does its report hold?",
    ["All 7", "5 or 6", "2 to 4", "0 or 1"])
table = Table(title="The same lossy compaction, with and without a notebook")
for col in ("arm", "hops found", "totals right", "requests", "tokens, all requests",
            "statements opened", "notes", "stopped"):
    table.add_column(col)
plain, opened_p, log_p = session(None, turns=MAX_TURNS, compact=True, opened=[])
g_plain = row(table, "a paragraph, no notes", [plain], opened_p, None)
book = book_at("compacted")
noted, opened_n, log_n = session(book, turns=MAX_TURNS, compact=True, opened=[])
g_noted = row(table, "a paragraph, and a notebook", [noted], opened_n, book)
console.print(table)
evidence(".scratch/11/compacted.json, as read back to LANTERN", book.text())
if book.refused:
    reply("notes the notebook refused", "\n".join(book.refused[:4]), style="red")
note(f"{log_n.compactions} compactions with the notebook, {log_p.compactions} without. The "
     f"notebook holds {len(book.flows)} flows, each checked against its statement, and "
     f"refused {len(book.refused)}.")
learn.reveal(p_notes, answer=0 if g_noted["found"] == 7 else 1 if g_noted["found"] >= 5
             else 2 if g_noted["found"] >= 2 else 3,
             why="What the paragraph drops is still in the notebook, outside the window, in a "
             "form that code checked when it was written.")

step("3. A restart")
p_restart = learn.predict(
    f"The workstation restarts after {RESTART_AFTER} requests. A new session begins with "
    "nothing but the task, or with the task and the notebook. How many statements does each "
    "second session open that the first had already opened?",
    ["Both reopen everything", "Without notes it reopens them; with notes it opens none again",
     "Neither reopens anything"])
table = Table(title=f"Stopped after {RESTART_AFTER} requests, then started again")
for col in ("arm", "hops found", "totals right", "requests", "tokens, all requests",
            "statements opened", "notes", "stopped"):
    table.add_column(col)
first_a, opened_a1, _ = session(None, turns=RESTART_AFTER, compact=False, opened=[])
second_a, opened_a2, _ = session(None, turns=MAX_TURNS, compact=False, opened=[])
g_a = row(table, "no notes", [first_a, second_a], [*opened_a1, *opened_a2], None)
book2 = book_at("restarted")
first_b, opened_b1, _ = session(book2, turns=RESTART_AFTER, compact=False, opened=[])
kept_at_restart = len(book2.flows)
book2 = Notebook.open(OUT / "restarted.json")  # a new process: only the file is left
second_b, opened_b2, _ = session(book2, turns=MAX_TURNS, compact=False,
                                 opened=book2.sources(), carry=book2.text())
g_b = row(table, "with the notebook", [first_b, second_b], [*opened_b1, *opened_b2], book2)
console.print(table)
again_a = len(set(opened_a1) & set(opened_a2))
again_b = len(set(opened_b1) & set(opened_b2))
note(f"Without notes the second session reopened {again_a} of the {len(set(opened_a1))} "
     f"statements the first had read. With the notebook, which held {kept_at_restart} flows "
     f"at the restart, it reopened {again_b}.")
learn.reveal(p_restart, answer=0 if again_a and again_b >= again_a else 1 if again_a > again_b
             else 2,
             why="Notes are context the agent wrote for itself and can read again. They are "
             "for one task: what should outlive the task is a memory, and that is decided "
             "differently.")

(OUT / "traces.json").write_text(json.dumps({
    "paragraph": plain.answer, "paragraph and notebook": noted.answer,
    "restart": second_a.answer, "restart with notebook": second_b.answer}, indent=2),
    encoding="utf-8")
learn.record(
    hops=len(want),
    demo_kept=good["kept"],
    demo_refused=2 - int(no_source["kept"]) - int(wrong["kept"]),
    plain_found=g_plain["found"],
    plain_totals=g_plain["totals_right"],
    noted_found=g_noted["found"],
    noted_totals=g_noted["totals_right"],
    notes_kept=len(book.flows),
    notes_refused=len(book.refused),
    noted_compactions=log_n.compactions,
    noted_tokens=noted.total_prompt_tokens,
    restart_found=g_a["found"],
    restart_reopened=again_a,
    restart_tokens=first_a.total_prompt_tokens + second_a.total_prompt_tokens,
    restart_notes_found=g_b["found"],
    restart_notes_totals=g_b["totals_right"],
    restart_notes_reopened=again_b,
    restart_notes_kept=kept_at_restart,
    restart_notes_tokens=first_b.total_prompt_tokens + second_b.total_prompt_tokens,
    restart_after=RESTART_AFTER,
    mine=MINE is not None,
)

finding(f"""
LANTERN now keeps working notes outside the window, and a note is kept only if it names its
statement and agrees with it. Compacted to a paragraph as in chapter 10, the trace reported
{g_plain['found']} of {len(want)} hops without notes and {g_noted['found']} with a notebook read
back after each compaction, totals right on {g_noted['totals_right']}; the notebook kept
{len(book.flows)} flows and refused {len(book.refused)}. Stopped after {RESTART_AFTER} requests
and started again, a session with no notes reopened {again_a} statements and reported
{g_a['found']} hops; a session given the notebook reopened {again_b} and reported
{g_b['found']}, totals right on {g_b['totals_right']}.
""")
save_shot("11-notes-and-scratchpads")
