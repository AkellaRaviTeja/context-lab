"""Chapter 09: tool results. What a result costs after the turn that asked for it."""

import json

from lantern import agent, case, context, learn, results, trail
from lantern.config import ROOT, load_config
from lantern.llm import chat
from lantern.ui import Table, chapter, console, evidence, finding, note, reply, save_shot, step

chapter(
    "09",
    "What stays behind",
    """
Wednesday 22 July, 09:30. One call to the statement tool returns Corvane's whole quarter. The
agent needed nine lines of it.

Okafor follows the trace turn by turn. The quarter is there on turn two, where it was asked
for. It is there again on turn three, and on turn nine.

"It is carrying Corvane everywhere it goes," he says.

By the ninth request most of what LANTERN is reading is statements it has finished with. Case
file 02 chapter 20 counted the cost in tokens. Nobody has yet asked what it costs in room.

"Can it put them down?" Varma asks.
""",
)

MINE = learn.mine()  # --mine: your clear_old() from practice/exercise.py
CLEAR = MINE.clear_old if MINE else results.clear_old
OUT = ROOT / ".scratch" / "09"
RESERVE = 600
MAX_TURNS = 16
# Challenge: which arms run. Remove one to save time, or keep only the one you are changing.
ARMS = ("whole statements, kept", "cleared when used", "summarised when used",
        "trimmed at the tool")
SUMMARISE = ("Summarise this bank statement for a later reader: for every payee the account "
             "paid, give the payee, the number of payments and the total. One line a payee. "
             "Nothing else.")


def trace(tool: str, hook=None):
    """One checked trace. `tool` is "statement" (every line) or "money_out" (a digest)."""
    text, names = trail.listing(True)
    opened: list[str] = []

    def statement(file: str = "", **_):
        if file not in names:
            return {"failed": True, "error": f"No file named {file!r}.", "files": list(names)}
        opened.append(names[file])
        return case.read(f"bank/{names[file]}")

    if tool == "statement":
        schemas = [trail.schema("statement", "Every line of one bank statement, as the bank "
                                "sent it.", file="A file name from the list.")]
        handlers = {"statement": statement}
    else:
        schemas, handlers, opened = trail.tools(names)
    shares = []

    def before(messages):
        messages = hook(messages) if hook else messages
        shares.append(results.old_share(messages, context.count_tokens))
        return messages

    run = agent.run([{"role": "system", "content": trail.RULES + text},
                     {"role": "user", "content": trail.TASK}], chat=chat, schemas=schemas,
                    handlers=handlers, max_turns=MAX_TURNS, max_tokens=RESERVE, limit=limit,
                    until=trail.not_done(opened), before_request=before)
    return {"run": run, "opened": list(dict.fromkeys(opened)), "grade": trail.grade(run.answer),
            "shares": shares}


summaries: list[dict] = []


def write_summary(call: str, content: str) -> str:
    text = chat(content, system=SUMMARISE, seed=7, max_tokens=300).text
    summaries.append({"call": call, "summary": text})
    return text


OUT.mkdir(parents=True, exist_ok=True)
window = load_config()["generation"]["num_ctx"]
limit = window - RESERVE
want = trail.expected()

step("1. One call, one quarter")
corvane = case.read("bank/corvane-trading.csv")
evidence("statement(corvane-trading.csv): the first four of 37 lines",
         "\n".join(corvane.splitlines()[:5]))
needed = [x for x in corvane.splitlines() if "Lowmarsh" in x]
note(f"The result is {context.count_tokens(corvane):,} tokens. The hop the agent is after is "
     f"on {len(needed)} of its 37 lines, {context.count_tokens(chr(10).join(needed)):,} tokens.")

step("2. What the agent carries, request by request")
p_share = learn.predict_number(
    "The agent traces the trail with a tool that returns whole statements, and nothing is "
    "ever removed. By its last request, what share of everything it is sent is tool results "
    "from earlier turns?", unit="%")
arms = {}
arms["whole statements, kept"] = trace("statement")
kept = arms["whole statements, kept"]
table = Table(title="Whole statements, kept: every request")
for col in ("request", "tokens sent", "old tool results", "share", "called"):
    table.add_column(col, justify="left" if col == "called" else "right")
for t, (old, total) in zip(kept["run"].turns, kept["shares"], strict=False):
    table.add_row(str(t.n), f"{t.prompt_tokens:,}", f"{old:,}", f"{old / max(total, 1):.0%}",
                  ", ".join(f"{n}({next(iter(a.values()), '')})" for n, a in t.calls)
                  or "(a report)")
console.print(table)
last_old, last_total = kept["shares"][len(kept["run"].turns) - 1]
share = 100 * last_old / last_total
note(f"Stopped: {kept['run'].stopped}. By the last request it sent, {share:.0f}% of the "
     f"conversation was results from earlier turns. Opened {len(kept['opened'])} statements "
     f"and reported {kept['grade']['found']} of {len(want)} hops, totals right on "
     f"{kept['grade']['totals_right']}.")
learn.reveal(p_share, actual=share, tolerance=0.15,
             why="A tool result is asked for once and paid for on every later request. In a "
             "long run the window fills with things the agent has finished with.")

step("3. Three ways to put a result down")
p_best = learn.predict(
    "Three treatments: clear a used result and leave a note; replace it with a summary the "
    "model writes; or change the tool so it returns only who was paid and how much. Which "
    "finds the most hops with the right totals?",
    ["Cleared when used", "Summarised when used", "Trimmed at the tool",
     "None gets a total right"])
if "cleared when used" in ARMS:
    arms["cleared when used"] = trace("statement", CLEAR)
if "summarised when used" in ARMS:
    arms["summarised when used"] = trace("statement", results.summarise_old(write_summary))
if "trimmed at the tool" in ARMS:
    arms["trimmed at the tool"] = trace("money_out")
table = Table(title="The same trace, four treatments of a used result")
for col in ("treatment", "hops found", "totals right", "not hops", "requests",
            "tokens, all requests", "largest request", "opened", "stopped"):
    table.add_column(col)
for name, a in arms.items():
    g, run = a["grade"], a["run"]
    table.add_row(name, f"{g['found']} of {len(want)}", str(g["totals_right"]), str(g["invented"]),
                  str(len(run.turns)), f"{run.total_prompt_tokens:,}", f"{run.largest_request:,}",
                  str(len(a["opened"])), run.stopped.split(":")[0])
console.print(table)
(OUT / "traces.json").write_text(json.dumps(
    {name: {"answer": a["run"].answer, "opened": a["opened"], "grade": a["grade"],
            "stopped": a["run"].stopped,
            "requests": [(t.n, t.prompt_tokens, t.calls) for t in a["run"].turns]}
     for name, a in arms.items()}, indent=2), encoding="utf-8")
(OUT / "summaries.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
right = {name: a["grade"]["totals_right"] for name, a in arms.items()}
options = ["cleared when used", "summarised when used", "trimmed at the tool"]
best = max((n for n in options if n in right), key=lambda n: right[n], default=None)
learn.reveal(p_best, answer=3 if not best or right[best] == 0 else options.index(best),
             why="Clearing and summarising manage what is already in the window. Trimming at "
             "the tool decides what enters it, and can do the arithmetic before the model "
             "ever sees a figure.")

step("4. Read the summaries")
checked = 0
if summaries:
    first = summaries[0]
    reply(f"LANTERN's summary of {first['call']}", first["summary"][:500])
    for s in summaries:
        file = s["call"].split("(")[1].rstrip(")")
        real = {p["payee"]: p["total"] for p in trail.digest(file)["paid_out_to"]}
        checked += all(t.replace(".00", "") in s["summary"].replace(",", "") for t in real.values())
    note(f"{len(summaries)} summaries were written. Checked against the statements in code, "
         f"{checked} have every payee's total right. A summary of a tool result is a new "
         "document. The model that wrote it will later read it as if it were the statement.")
else:
    note("The summarising arm did not run.")

cleared = arms.get("cleared when used")
summ = arms.get("summarised when used")
trim = arms.get("trimmed at the tool")


def of(arm, key, default=-1):
    return arm["grade"][key] if arm else default


learn.record(
    hops=len(want),
    statement_tokens=context.count_tokens(corvane),
    kept_found=kept["grade"]["found"],
    kept_totals=kept["grade"]["totals_right"],
    kept_stopped=kept["run"].stopped.split(":")[0],
    kept_requests=len(kept["run"].turns),
    kept_tokens=kept["run"].total_prompt_tokens,
    kept_largest=kept["run"].largest_request,
    kept_old_share_pct=round(share),
    cleared_found=of(cleared, "found"),
    cleared_totals=of(cleared, "totals_right"),
    cleared_largest=cleared["run"].largest_request if cleared else -1,
    cleared_stopped=cleared["run"].stopped.split(":")[0] if cleared else "",
    cleared_opened=len(cleared["opened"]) if cleared else -1,
    summarised_found=of(summ, "found"),
    summarised_totals=of(summ, "totals_right"),
    summarised_stopped=summ["run"].stopped.split(":")[0] if summ else "",
    summaries_written=len(summaries),
    summaries_right=checked,
    trimmed_found=of(trim, "found"),
    trimmed_totals=of(trim, "totals_right"),
    trimmed_tokens=trim["run"].total_prompt_tokens if trim else -1,
    trimmed_largest=trim["run"].largest_request if trim else -1,
    mine=MINE is not None,
)

finding(f"""
One call to the statement tool returns {context.count_tokens(corvane):,} tokens of which the
agent needs {len(needed)} lines. With whole statements kept, the trace stopped
({kept['run'].stopped.split(':')[0]}) after {len(kept['run'].turns)} requests, with {share:.0f}%
of its last request made of results from earlier turns, {kept['grade']['found']} of
{len(want)} hops and {kept['grade']['totals_right']} totals right. Cleared when used:
{of(cleared, 'found')} hops, {of(cleared, 'totals_right')} totals right, largest request
{cleared['run'].largest_request if cleared else 0:,} tokens. Summarised when used:
{of(summ, 'found')} hops, {of(summ, 'totals_right')} totals right, and {checked} of
{len(summaries)} summaries had every total right. Trimmed at the tool, so that it returns
payees, counts and totals: {of(trim, 'found')} of {len(want)} hops and
{of(trim, 'totals_right')} totals right.
""")
save_shot("09-tool-results")
