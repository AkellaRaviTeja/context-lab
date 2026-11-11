"""Chapter 08: just in time. Everything loaded before the question, or a list and two tools."""

import json

from lantern import agent, budget, case, context, learn, trail
from lantern.budget import Budget, OverBudget
from lantern.config import ROOT, load_config
from lantern.llm import chat
from lantern.ui import Table, chapter, console, evidence, finding, note, reply, save_shot, step

chapter(
    "08",
    "A list, not the files",
    """
Tuesday 21 July, 10:00. Every morning since April the nightly service has loaded the same nine
statements into the context before the first question, whether the question concerned them or
not.

"It reads all nine to tell me the time," Okafor says.

"It does not read all nine," you say. "They do not fit. It reads what is left of them."

You replace the statements with a list: account, bank, a line on what each holds. And two
tools, one to search and one to open.

Varma is cautious. "Then it reads only what it chooses to."

"Yes."

"And if it chooses not to open the one that matters?"

You measure both ways.
""",
)

MINE = learn.mine()  # --mine: your listing() from practice/exercise.py
OUT = ROOT / ".scratch" / "08"
RESERVE = 600
# Challenge: the sentence added to the rules in the last arm. Write a better one.
KEEP_GOING = trail.KEEP_GOING
MAX_TURNS = 14


def listing(described: bool):
    if MINE:
        return MINE.listing(trail.accounts(), {a["file"]: len(trail.statement(a["file"]))
                                               for a in trail.accounts()}, described)
    return trail.listing(described)


def trace(system: str, names: dict[str, str] | None, checked: bool = False):
    """One trace of the trail. With `names`, the agent has the two tools over those files.
    With `checked`, code refuses a report while a payee's statement is unopened."""
    schemas, handlers, opened = trail.tools(names) if names else (None, {}, [])
    run = agent.run([{"role": "system", "content": system},
                     {"role": "user", "content": trail.TASK}], chat=chat, schemas=schemas,
                    handlers=handlers, max_turns=MAX_TURNS, max_tokens=RESERVE, limit=limit,
                    until=trail.not_done(opened) if checked else None)
    return run, opened, trail.grade(run.answer)


OUT.mkdir(parents=True, exist_ok=True)
cfg = load_config()
window = cfg["generation"]["num_ctx"]
limit = window - RESERVE
want = trail.expected()
accounts = trail.accounts()

step("1. What the nightly service loads")
sizes = {a["file"]: context.count_tokens(case.read(f"bank/{a['file']}")) for a in accounts}
table = Table(title="The nine statements, as loaded every morning")
for col in ("statement", "lines", "tokens"):
    table.add_column(col, justify="left" if col == "statement" else "right")
for a in accounts:
    table.add_row(a["holder"], str(len(trail.statement(a["file"]))), f"{sizes[a['file']]:,}")
table.add_row("all nine", str(sum(len(trail.statement(a["file"])) for a in accounts)),
              f"{sum(sizes.values()):,}")
console.print(table)
p_fit = learn.predict(
    f"The window is {window:,} tokens. How many of the nine statements fit in it, loaded in "
    "the order of the trail, with nothing else?", ["All nine", "5 to 8", "2 to 4", "One or none"])
running, fit = 0, 0
for a in accounts:
    running += sizes[a["file"]]
    fit += running <= limit
refused = None
try:
    budget.check({"statements": sum(sizes.values())}, Budget(window=window, reserve=RESERVE))
except OverBudget as e:
    refused = e
    reply("budget.check, nine statements up front", str(e), style="red")
note(f"All nine come to {sum(sizes.values()):,} tokens, {sum(sizes.values()) / window:.1f} "
     f"times the window. In trail order {fit} fit. For three months the server has cut this "
     "to about half a window each morning and answered from what was left.")
learn.reveal(p_fit, answer=0 if fit == 9 else 1 if fit >= 5 else 2 if fit >= 2 else 3,
             why="Loading everything up front was never what happened. What happened was a "
             "silent cut. The choice is between a smaller thing loaded and a thing fetched.")

step("2. The trail, from the statements themselves")
table = Table(title=f"Every hop from {trail.START}, computed from the statements")
for col in ("payer", "payee", "payments", "total"):
    table.add_column(col, justify="right" if col in ("payments", "total") else "left")
for f in want:
    table.add_row(f.payer, f.payee, str(f.payments), f"{f.total:,.2f}")
console.print(table)
note(f"{len(want)} hops. No model wrote this table: lantern.trail.expected() follows the "
     "debits. It is what each trace below is graded against.")

step("3. Up front: a digest of every statement")
digests = "\n".join(json.dumps(trail.digest(a["file"])) for a in accounts)
evidence("one digest", json.dumps(trail.digest("lowmarsh-shipping.csv")))
p_up = learn.predict_number(
    "Each statement is reduced to who it paid, how often and how much, and all nine digests "
    f"are loaded before the question. No tools. How many of the {len(want)} hops are reported?",
    unit="hops")
arms = {}
arms["digests up front"] = trace(
    trail.RULES + "Money out of every statement on file, by payee:\n" + digests, None)
run_up, _, g_up = arms["digests up front"]
note(f"{g_up['found']} of {len(want)} hops, totals right on {g_up['totals_right']}, lines "
     f"that are not hops {g_up['invented']}, in one request of {run_up.largest_request:,} "
     f"tokens. Missing: {', '.join(g_up['missing']) or 'none'}.")
learn.reveal(p_up, actual=g_up["found"], tolerance=0.01,
             why="A digest is small enough to load whole, and everything needed is in front "
             "of the model at once. Somebody had to decide in advance what a digest holds.")

step("4. Just in time: a list and two tools")
p_jit = learn.predict(
    "Now only a list of the nine files is loaded, with the holder, account and bank of each, "
    "and two tools: money_out(file) and search_files(text). How many hops are reported?",
    ["All 7", "5 or 6", "2 to 4", "0 or 1"])
text, names = listing(True)
arms["a described list"] = trace(trail.RULES + text, names)
text_bare, names_bare = listing(False)
arms["a bare list"] = trace(trail.RULES + text_bare, names_bare)
arms["a described list, and a rule"] = trace(trail.RULES + KEEP_GOING + text, names)
arms["a described list, and a check"] = trace(trail.RULES + text, names, checked=True)
table = Table(title="The same task, five ways of giving LANTERN the statements")
for col in ("given", "hops found", "totals right", "not hops", "requests", "tokens, all requests",
            "statements opened", "stopped"):
    table.add_column(col)
for name, (run, opened, g) in arms.items():
    table.add_row(name, f"{g['found']} of {len(want)}", str(g["totals_right"]),
                  str(g["invented"]), str(len(run.turns)), f"{run.total_prompt_tokens:,}",
                  str(len(set(opened))) if name != "digests up front" else "all 9, as digests",
                  run.stopped.split(":")[0])
console.print(table)
run_l, opened_l, g_l = arms["a described list"]
reply("a described list: the whole report", run_l.answer[:500])
note(f"With the list, LANTERN opened {', '.join(dict.fromkeys(opened_l)) or 'nothing'} and "
     "stopped. Nothing failed and nothing was cut. It chose not to open the next one.")
learn.reveal(p_jit, answer=0 if g_l["found"] == 7 else 1 if g_l["found"] >= 5 else
             2 if g_l["found"] >= 2 else 3,
             why="A reference costs a few tokens. An agent that does not follow it costs the "
             "answer, and the report it writes looks complete.")

step("5. What it opened is part of the record")
run_r, opened_r, g_r = arms["a described list, and a rule"]
run_c, opened_c, g_c = arms["a described list, and a check"]
note(f"A sentence in the rules telling LANTERN not to finish early: {g_r['found']} of "
     f"{len(want)}. The same condition checked in code, with the report sent back "
     f"{run_c.sent_back} times: {g_c['found']} of {len(want)}.")
run_r, opened_r, g_r = run_c, opened_c, g_c
table = Table(title="A described list, and a check: request by request")
for col in ("request", "tokens", "called"):
    table.add_column(col)
for t in run_r.turns:
    table.add_row(str(t.n), f"{t.prompt_tokens:,}",
                  ", ".join(f"{n}({next(iter(a.values()), '')})" for n, a in t.calls)
                  or "(a report)")
console.print(table)
never = [a["holder"] for a in accounts if a["file"] not in opened_r]
note(f"Opened: {len(set(opened_r))} of 9. Never opened: {', '.join(never) or 'none'}. A "
     "finding now comes with the list of statements read to reach it, and the list of those "
     "that were not.")
(OUT / "traces.json").write_text(json.dumps(
    {name: {"answer": run.answer, "opened": opened, "grade": g, "stopped": run.stopped,
            "requests": [(t.n, t.prompt_tokens, t.calls) for t in run.turns]}
     for name, (run, opened, g) in arms.items()}, indent=2), encoding="utf-8")

g_b = arms["a bare list"][2]
learn.record(
    statements=len(accounts),
    all_tokens=sum(sizes.values()),
    window=window,
    fit_up_front=fit,
    refused=refused is not None,
    hops=len(want),
    digest_found=g_up["found"],
    digest_totals=g_up["totals_right"],
    digest_invented=g_up["invented"],
    digest_tokens=run_up.total_prompt_tokens,
    list_found=g_l["found"],
    list_opened=len(set(opened_l)),
    list_requests=len(run_l.turns),
    list_tokens=run_l.total_prompt_tokens,
    bare_found=g_b["found"],
    bare_opened=len(set(arms["a bare list"][1])),
    rule_found=arms["a described list, and a rule"][2]["found"],
    check_found=g_c["found"],
    check_totals=g_c["totals_right"],
    check_invented=g_c["invented"],
    check_opened=len(set(opened_c)),
    check_requests=len(run_c.turns),
    check_tokens=run_c.total_prompt_tokens,
    check_largest=run_c.largest_request,
    check_sent_back=run_c.sent_back,
    check_stopped=run_c.stopped.split(":")[0],
    mine=MINE is not None,
)

finding(f"""
The nine statements the nightly service loads come to {sum(sizes.values()):,} tokens against a
window of {window:,}; {fit} fit, and the request is now refused where it used to be cut. With a
digest of every statement loaded up front LANTERN reported {g_up['found']} of {len(want)} hops
in one request of {run_up.largest_request:,} tokens. With a list of the files and two tools it
opened {len(set(opened_l))} statement and reported {g_l['found']}; with file names that say
nothing, {g_b['found']}; told in a sentence not to finish early,
{arms["a described list, and a rule"][2]['found']}. With the same condition checked in code and
the report sent back {run_c.sent_back} times, it opened {len(set(opened_c))} statements and
reported {g_c['found']} of {len(want)}, totals right on {g_c['totals_right']}, in
{len(run_c.turns)} requests and {run_c.total_prompt_tokens:,} tokens. Each trace records which
statements were opened and which never were.
""")
save_shot("08-just-in-time")
