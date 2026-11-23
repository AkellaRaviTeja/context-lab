"""Chapter 15: isolating context. A reader in a window of its own, and what its report hides."""

import json

from lantern import agent, context, isolation, learn, trail
from lantern.config import ROOT, load_config
from lantern.llm import chat
from lantern.ui import Table, chapter, console, evidence, finding, note, reply, save_shot, step

chapter("15", "Forty-two pages, five lines", """
Thursday 30 July, 10:20. Before anything in LANTERN's memory is trusted with the trail of case
file 02, Varma wants it traced again from the statements and nothing else: every hop from
Corvane. The nine statements run to forty-two pages as the banks printed them.

Reading forty-two pages in the main context would leave room for little else.

"Send someone to read them," Varma says, "and have them report."

That is what a sub-agent is. It reads in a window of its own and hands back five lines. Case
file 02 chapter 18 measured what teams of agents cost. This is a smaller question.

Okafor asks it. "What was on the pages it decided I did not need?"
""")

MINE = learn.mine()  # --mine: your check_report() from practice/exercise.py
CHECK = MINE.check_report if MINE else isolation.check_report
OUT = ROOT / ".scratch" / "15"
RESERVE = 600
MAX_TURNS = 16
FOLLOW_TURNS = 4
OUT.mkdir(parents=True, exist_ok=True)
window = load_config()["generation"]["num_ctx"]
limit = window - RESERVE
want = trail.expected()
PAGES = isolation.pages()
BY_ID = {p.id: p for p in PAGES}


def own_pages():
    """The agent reads the pages itself: one tool, every page into the main context."""
    opened, sent = [], []

    def read_page(page: str = "", **_):
        if page not in BY_ID:
            return {"failed": True, "error": f"No page named {page!r}."}
        opened.append(BY_ID[page].file)
        return BY_ID[page].text

    def before(messages):
        sent.append(list(messages))
        return messages

    run = agent.run([{"role": "system", "content": trail.RULES + trail.KEEP_GOING
                      + isolation.page_listing(PAGES)},
                     {"role": "user", "content": trail.TASK}], chat=chat,
                    schemas=[isolation.page_schema()], handlers={"read_page": read_page},
                    max_turns=MAX_TURNS, max_tokens=RESERVE, limit=limit,
                    until=trail.not_done(opened), before_request=before)
    return {"run": run, "opened": list(dict.fromkeys(opened)), "sent": sent,
            "tools": ([isolation.page_schema()], {"read_page": read_page}),
            "grade": trail.grade(run.answer)}


DELEGATE = trail.schema(
    "delegate", "Send a reader to one statement. It opens every page in a window of its own "
    "and returns at most five lines, each naming the pages it rests on, and the pages it did "
    "not read. " + isolation.TELL,
    file="A statement file from the list.", task="What the reader is to find, in full.")
MAIN = ("You cannot open statements yourself. To learn what a statement shows, call delegate "
        "with the file and a task. ")


def with_readers():
    """The agent sends readers: only their reports enter the main context."""
    opened, reads = [], []

    def delegate(file: str = "", task: str = "", **_):
        if file not in {a["file"] for a in trail.accounts()}:
            return {"failed": True, "error": f"No statement named {file!r}."}
        rec = isolation.read(file, task, chat=chat, limit=limit, reserve=RESERVE, check=CHECK)
        reads.append(rec)
        if not rec["accepted"]:
            return {"failed": True, "error": "The reader's report was refused: "
                    + "; ".join(rec["problems"] or [rec["stopped"]])}
        opened.append(file)
        return rec["report"]

    run = agent.run([{"role": "system", "content": trail.RULES + trail.KEEP_GOING + MAIN
                      + isolation.statement_listing(PAGES)},
                     {"role": "user", "content": trail.TASK}], chat=chat, schemas=[DELEGATE],
                    handlers={"delegate": delegate}, max_turns=MAX_TURNS, max_tokens=RESERVE,
                    limit=limit, until=trail.not_done(opened))
    return {"run": run, "opened": list(dict.fromkeys(opened)), "reads": reads,
            "tools": ([DELEGATE], {"delegate": delegate}), "grade": trail.grade(run.answer)}


def ask(arm, messages, item):
    """A follow-up question in the main context as the trace left it, tools still there."""
    before = len(arm.get("reads", []))
    schemas, handlers = arm["tools"]
    run = agent.run([*messages, {"role": "user", "content": item["q"]}], chat=chat,
                    schemas=schemas, handlers=handlers, max_turns=FOLLOW_TURNS, max_tokens=300,
                    limit=window - 300)
    return {"id": item["id"], "answer": run.answer, "right": isolation.answered(run.answer, item),
            "stopped": run.stopped.split(":")[0], "largest": run.largest_request,
            "calls": len(run.calls), "readers": len(arm.get("reads", [])) - before}


step("1. Forty-two pages")
files = {p.file for p in PAGES}
need = {f.payer for f in want}
holder = {a["holder"]: a["file"] for a in trail.accounts()}
trail_pages = [p for p in PAGES if p.file in {holder[h] for h in need}
               | {holder[want[-1].payee]}]
all_tokens = context.count_tokens("\n\n".join(p.text for p in PAGES))
trail_tokens = context.count_tokens("\n\n".join(p.text for p in trail_pages))
evidence(f"read_page({PAGES[12].id}): the first five lines", "\n".join(
    PAGES[12].text.splitlines()[:5]))
note(f"{len(PAGES)} pages from {len(files)} statements, {all_tokens:,} tokens in all. The "
     f"{len(want)} hops of the trail are on {len(trail_pages)} pages, {trail_tokens:,} tokens. "
     f"The window is {window:,} tokens and a request may carry {limit:,}.")

step("2. One context reads the pages itself")
p_end = learn.predict(
    "The agent reads the pages itself, and every page it reads stays in its context. How "
    "does the trace end?",
    ["It reports all seven hops", "It reports some hops and stops", "It stops over budget"])
a = own_pages()
table = Table(title="One context: every request")
for col in ("request", "tokens sent", "called"):
    table.add_column(col, justify="left" if col == "called" else "right")
for t in a["run"].turns:
    table.add_row(str(t.n), f"{t.prompt_tokens:,}", ", ".join(
        f"{n}({next(iter(x.values()), '')})" for n, x in t.calls) or "(a report)")
console.print(table)
note(f"Stopped: {a['run'].stopped}. {a['grade']['found']} of {len(want)} hops, "
     f"{a['grade']['totals_right']} totals right, largest request "
     f"{a['run'].largest_request:,} tokens.")
a_over = a["run"].stopped.startswith("over budget")
learn.reveal(p_end, answer=2 if a_over else (0 if a["grade"]["found"] == len(want) else 1),
             why="Pages are read once and carried on every later request. The seven hops sit "
             f"on {len(trail_pages)} pages, {trail_tokens:,} tokens, more than "
             f"a request may carry here.")

step("3. Readers in windows of their own")
p_ratio = learn.predict_number(
    "Now the main agent sends readers. Counting every request the readers make as well as the "
    "main agent's, how many tokens are processed in all, as a multiple of the main context's "
    "own requests?", unit="times")
b = with_readers()
reads = b["reads"]
table = Table(title="Every reader the main agent sent")
for col in ("statement", "pages read", "requests", "reader tokens", "lines", "refused",
            "report"):
    table.add_column(col)
for r in reads:
    lines, _ = isolation.parse(r["report"])
    table.add_row(r["file"], f"{len(r['opened'])} of {len(r['pages'])}", str(r["requests"]),
                  f"{r['tokens']:,}", str(len(lines)), str(r["refused"]),
                  "accepted" if r["accepted"] else f"refused ({r['stopped']})")
console.print(table)
reader_tokens = sum(r["tokens"] for r in reads)
main_tokens = b["run"].total_prompt_tokens
ratio = (main_tokens + reader_tokens) / max(main_tokens, 1)
note(f"Stopped: {b['run'].stopped}. The main context made {len(b['run'].turns)} requests, "
     f"{main_tokens:,} tokens in all, the largest {b['run'].largest_request:,}. Its "
     f"{len(reads)} readers made {sum(r['requests'] for r in reads)} requests, "
     f"{reader_tokens:,} tokens.")
learn.reveal(p_ratio, actual=round(ratio, 1), tolerance=0.3,
             why="Isolation moves the reading out of the main window. It does not remove it: "
             "every page a reader opens is processed in the reader's context, and each reader "
             "starts again with its own instructions.")

step("4. What the main context holds")
accepted = [r for r in reads if r["accepted"]]
if accepted:
    first = accepted[0]
    reply(f"The report of the reader sent to {first['file']}", first["report"][:700],
          meta=f"task: {first['task'][:90]}")
table = Table(title="The same trace, two ways")
for col in ("", "requests", "largest request", "main context tokens", "all contexts",
            "hops found", "totals right", "not hops", "stopped"):
    table.add_column(col)
for name, arm, extra in (("one context", a, 0), ("readers", b, reader_tokens)):
    run, g = arm["run"], arm["grade"]
    table.add_row(name, str(len(run.turns)), f"{run.largest_request:,}",
                  f"{run.total_prompt_tokens:,}", f"{run.total_prompt_tokens + extra:,}",
                  f"{g['found']} of {len(want)}", str(g["totals_right"]), str(g["invented"]),
                  run.stopped.split(":")[0])
console.print(table)

step("5. What isolation hid")
p_hid = learn.predict(
    "Each report was checked for its form: sources on every line, and a NOT READ line. "
    "Checked in code against the statements, did any accepted report carry a total or a "
    "count the statement does not show, or leave a payee out?",
    ["No: the reports were right", "Yes, at least one"])
hid = {r["file"].removesuffix(".csv") + f" #{i}": isolation.hidden(r)
       for i, r in enumerate(accepted, 1)}
table = Table(title="Accepted reports, checked against the statements in code")
for col in ("report", "wrong totals", "wrong counts", "payees left out", "pages unread",
            "unread, not said"):
    table.add_column(col)
for k, h in hid.items():
    table.add_row(k, str(len(h["wrong_totals"])), str(len(h["wrong_counts"])),
                  str(len(h["left_out"])), str(len(h["unopened"])), str(len(h["unread_not_said"])))
console.print(table)
wrong_totals = sum(len(h["wrong_totals"]) for h in hid.values())
wrong_counts = sum(len(h["wrong_counts"]) for h in hid.values())
left_out = sum(len(h["left_out"]) for h in hid.values())
unread_not_said = sum(len(h["unread_not_said"]) for h in hid.values())
example = next((x for h in hid.values() for x in h["wrong_totals"]), None)
if example:
    note(f"One of them: {example}. The main context has the report and not the page, so it "
         "has no way to see this.")
any_hidden = (wrong_totals + wrong_counts + left_out) > 0
learn.reveal(p_hid, answer=1 if any_hidden else 0,
             why="The check reads the form of a report, not its truth. A reader's report is "
             "testimony: the main agent can rely on it or send someone to read the page again, "
             "and nothing in between.")

step("6. The questions the reports did not cover")
p_follow = learn.predict(
    "Okafor asks three questions whose answers are on the pages and in no five-line report: "
    "a date, a reference and a single payment. Which context answers more of them right?",
    ["The one that read the pages itself", "The one that sent readers", "The same"])
a_messages = a["sent"][len(a["run"].turns) - 1] if a["run"].turns else a["run"].messages
if a["run"].stopped == "answered":
    a_messages = [*a["run"].messages, {"role": "assistant", "content": a["run"].answer}]
b_messages = [*b["run"].messages, {"role": "assistant", "content": b["run"].answer}]
follow = {"one context": [], "readers": []}
for item in isolation.follow_ups():
    follow["one context"].append(ask(a, a_messages, item))
    follow["readers"].append(ask(b, b_messages, item))
table = Table(title="Follow-up questions, asked in each main context as the trace left it")
for col in ("question", "the answer", "one context", "readers"):
    table.add_column(col)
for i, item in enumerate(isolation.follow_ups()):
    x, y = follow["one context"][i], follow["readers"][i]
    want_text = item["answer"][0] if isinstance(item["answer"], list) else item["answer"]
    table.add_row(item["id"], want_text + (f", {item['also']}" if "also" in item else ""),
                  ("right" if x["right"] else "wrong") + f" ({x['stopped']})",
                  ("right" if y["right"] else "wrong") + f" ({y['stopped']}, "
                  f"{y['readers']} readers sent)")
console.print(table)
a_right = sum(x["right"] for x in follow["one context"])
b_right = sum(y["right"] for y in follow["readers"])
b_resent = sum(y["readers"] for y in follow["readers"])
note(f"One context: {a_right} of 3. Readers: {b_right} of 3, sending {b_resent} more readers "
     "to answer them.")
learn.reveal(p_follow, answer=0 if a_right > b_right else (1 if b_right > a_right else 2),
             why="Detail left behind in a reader's window is gone from the main context. A "
             "follow-up can be answered only by sending a reader again, and only if the main "
             "agent thinks to.")

(OUT / "traces.json").write_text(json.dumps({
    "one_context": {"answer": a["run"].answer, "stopped": a["run"].stopped, "grade": a["grade"],
                    "requests": [(t.n, t.prompt_tokens, t.calls) for t in a["run"].turns]},
    "readers": {"answer": b["run"].answer, "stopped": b["run"].stopped, "grade": b["grade"],
                "requests": [(t.n, t.prompt_tokens, t.calls) for t in b["run"].turns],
                "reads": reads, "hidden": hid},
    "follow_ups": follow}, indent=2, default=str), encoding="utf-8")

learn.record(
    pages=len(PAGES),
    page_tokens=all_tokens,
    trail_page_tokens=trail_tokens,
    hops=len(want),
    one_found=a["grade"]["found"],
    one_totals=a["grade"]["totals_right"],
    one_stopped=a["run"].stopped.split(":")[0],
    one_requests=len(a["run"].turns),
    one_largest=a["run"].largest_request,
    one_tokens=a["run"].total_prompt_tokens,
    readers_found=b["grade"]["found"],
    readers_totals=b["grade"]["totals_right"],
    readers_invented=b["grade"]["invented"],
    readers_stopped=b["run"].stopped.split(":")[0],
    main_requests=len(b["run"].turns),
    main_largest=b["run"].largest_request,
    main_tokens=main_tokens,
    readers_sent=len(reads),
    readers_accepted=len(accepted),
    readers_refused_once=sum(r["refused"] > 0 for r in reads),
    reader_tokens=reader_tokens,
    all_tokens_ratio=round(ratio, 2),
    hidden_wrong_totals=wrong_totals,
    hidden_wrong_counts=wrong_counts,
    hidden_left_out=left_out,
    hidden_unread_not_said=unread_not_said,
    follow_one_right=a_right,
    follow_readers_right=b_right,
    follow_readers_resent=b_resent,
    mine=MINE is not None,
)

finding(f"""
The trail's seven hops are on {len(trail_pages)} of {len(PAGES)} pages, {trail_tokens:,} tokens.
Read in one context, the trace stopped ({a['run'].stopped.split(':')[0]}) after
{len(a['run'].turns)} requests with {a['grade']['found']} of {len(want)} hops and
{a['grade']['totals_right']} totals right; its largest request was
{a['run'].largest_request:,} tokens. With readers, the main context's largest request was
{b['run'].largest_request:,} tokens and it found {b['grade']['found']} of {len(want)} hops,
{b['grade']['totals_right']} totals right, while {len(reads)} readers processed
{reader_tokens:,} tokens it never saw. Checked in code, the accepted reports carried
{wrong_totals} wrong totals and {wrong_counts} wrong counts and left out {left_out} payees,
none of which the main context could see. Asked three follow-up questions, the one context
answered {a_right} and the main context with readers {b_right}.
""")
save_shot("15-isolating-context")
