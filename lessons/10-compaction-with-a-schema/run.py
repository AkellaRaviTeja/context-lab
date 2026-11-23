"""Chapter 10: compaction with a schema. A form that must keep who paid whom, checked in code."""

import json

from lantern import agent, compaction, context, learn, trail
from lantern.config import ROOT, load_config
from lantern.llm import chat
from lantern.ui import Table, chapter, console, evidence, finding, note, reply, save_shot, step

chapter(
    "10",
    "Who paid whom",
    """
Thursday 23 July, 10:10. Varma has not forgotten April. Three days of tracing, a compacted
history, and a summary that kept the amounts and lost which account paid which.

"It summarised the trail into a list of numbers," she says. "Tell me that cannot happen again."

You cannot tell her that about a paragraph the model writes freely. You can about a form.

Okafor drafts it on the whiteboard as he would a schedule: payer, payee, total, count, the
statement it came from. Open questions. Accounts read.

"If a line has no payer," he says, "it is not a line."
""",
)

MINE = learn.mine()  # --mine: your check() from practice/exercise.py
if MINE:
    compaction.check = MINE.check
OUT = ROOT / ".scratch" / "10"
RESERVE = 600
MAX_TURNS = 18
# The conversation is compacted when it passes this many tokens. Challenge: lower it and count
# the compactions; summaries of summaries are where a free-text compaction loses most.
THRESHOLD = 1500


def trace(make_hook=None, report_checked: bool = False):
    """One checked trace. With `report_checked`, the report must also hold every flow in the
    ledger of tool results, or it is sent back."""
    text, names = trail.listing(True)
    schemas, handlers, opened = trail.tools(names)
    log = compaction.Log()
    ledger: dict = {}
    hook = make_hook(log, ledger) if make_hook else None
    followed = trail.not_done(opened)
    covers = compaction.report_covers(ledger, skip=("Northwind Freight Ltd",))

    def until(report: str):
        return followed(report) or (covers(report) if report_checked else None)

    run = agent.run([{"role": "system", "content": trail.RULES + text},
                     {"role": "user", "content": trail.TASK}], chat=chat, schemas=schemas,
                    handlers=handlers, max_turns=MAX_TURNS, max_tokens=RESERVE,
                    limit=window - RESERVE, until=until, before_request=hook)
    return {"run": run, "opened": list(dict.fromkeys(opened)), "grade": trail.grade(run.answer),
            "log": log}


OUT.mkdir(parents=True, exist_ok=True)
window = load_config()["generation"]["num_ctx"]
want = trail.expected()
count = context.count_tokens

step("1. The form")
evidence("lantern.compaction.SCHEMA, as the model is asked to fill it in",
         '{"flows": [{"payer", "payee", "payments", "total", "source"}], '
         '"accounts_read": [file], "open_questions": [text]}')
note("Every flow needs all five fields. The check compares each one with the tool result it "
     "came from, kept in a ledger outside the window, and names what is missing or wrong.")
PROBED = compaction.probe(compaction.check)
note(f"Before any model fills it in, the check is tried on {PROBED['probes']} broken forms "
     f"whose fault is known, and on one right form. It refused {PROBED['caught']} of the "
     f"{PROBED['probes']}" + (f" (missed: {', '.join(PROBED['missed'])})" if PROBED["missed"]
                             else "") + (" and kept the right one." if PROBED["kept_good"]
                                         else " and refused the right one too."))

step("2. A paragraph, as in April")
p_para = learn.predict(
    f"The trace is compacted whenever the conversation passes {THRESHOLD:,} tokens, by asking "
    "the model for one paragraph. Of the flows the tools had returned by the last compaction, "
    "how many are still whole in the paragraph: payer, payee and total?",
    ["All of them", "More than half", "Half or fewer", "None"])
arms = {}
arms["no compaction"] = trace()
arms["a paragraph"] = trace(
    lambda log, ledger: compaction.free_text(chat, THRESHOLD, count, log, ledger))
para = arms["a paragraph"]
table = Table(title="A paragraph: what each compaction kept")
for col in ("compaction", "flows the tools had returned", "still whole in the paragraph"):
    table.add_column(col, justify="right")
for i, (kept, seen) in enumerate(para["log"].kept, 1):
    table.add_row(str(i), str(seen), str(kept))
console.print(table)
if para["log"].states:
    reply("the last paragraph LANTERN wrote for itself", para["log"].states[-1][:600])
last_kept, last_seen = para["log"].kept[-1] if para["log"].kept else (0, 0)
note(f"{para['log'].compactions} compactions. After the last, {last_kept} of {last_seen} flows "
     f"were whole. The trace then reported {para['grade']['found']} of {len(want)} hops, totals "
     f"right on {para['grade']['totals_right']}.")
learn.reveal(p_para, answer=0 if last_kept == last_seen else 1 if last_kept > last_seen / 2
             else 2 if last_kept else 3,
             why="A paragraph has no place a payer must go. The model that writes it decides "
             "what matters, and it is the same model that will have nothing else to read.")

step("3. A form, checked in code")
p_form = learn.predict(
    "Now the model fills in the form, and code refuses a form with a missing field or a figure "
    "that differs from the tool's. How many times is a form refused over the run?",
    ["Never", "Once or twice", "3 to 5 times", "More than 5"])
arms["a form, checked"] = trace(
    lambda log, ledger: compaction.with_schema(chat, THRESHOLD, count, log, ledger=ledger))
form = arms["a form, checked"]
for problems in form["log"].problems[:3]:
    reply("a form refused", "; ".join(problems)[:400], style="red")
note(f"{form['log'].compactions} compactions, {form['log'].refused} forms refused. Every form "
     f"that was kept had every flow whole: {form['log'].kept}.")
learn.reveal(p_form, answer=learn.bucket(form["log"].refused, [0, 2, 5]),
             why="The check does not make the model careful. It makes carelessness visible, "
             "and gives the next attempt the list of what was wrong.")

step("4. The form filled in by code")
arms["a form, filled in by code"] = trace(
    lambda log, ledger: compaction.from_source(THRESHOLD, count, log, ledger))
code = arms["a form, filled in by code"]
reply("the report after a form that kept every flow", code["run"].answer[:400])
note(f"The form was whole: {code['log'].kept}. The report holds {code['grade']['found']} of "
     f"{len(want)} hops. LANTERN reported what it had read since the compaction and treated "
     "the form as background. Keeping a fact and using it are separate things.")

step("5. The report, checked against the ledger")
p_cov = learn.predict(
    "Last arm. The form is filled in by code, and the final report is also checked in code: "
    "it is sent back while it leaves out any flow in the ledger. How many hops now?",
    ["All 7", "5 or 6", "1 to 4", "None"])
arms["a form by code, report checked"] = trace(
    lambda log, ledger: compaction.from_source(THRESHOLD, count, log, ledger),
    report_checked=True)
both = arms["a form by code, report checked"]
learn.reveal(p_cov, answer=0 if both["grade"]["found"] == 7 else 1 if both["grade"]["found"] >= 5
             else 2 if both["grade"]["found"] else 3,
             why="The compaction keeps the facts. A second check makes the report carry them. "
             "Neither check is the model being careful.")
table = Table(title="The same checked trace, five ways")
for col in ("compaction", "hops found", "totals right", "not hops", "compactions", "refused",
            "requests", "tokens, all requests", "largest request", "stopped"):
    table.add_column(col)
for name, a in arms.items():
    g, run, log = a["grade"], a["run"], a["log"]
    table.add_row(name, f"{g['found']} of {len(want)}", str(g["totals_right"]),
                  str(g["invented"]), str(log.compactions), str(log.refused),
                  str(len(run.turns)), f"{run.total_prompt_tokens:,}",
                  f"{run.largest_request:,}", run.stopped.split(":")[0])
console.print(table)
(OUT / "traces.json").write_text(json.dumps(
    {name: {"answer": a["run"].answer, "grade": a["grade"], "stopped": a["run"].stopped,
            "states": a["log"].states, "problems": a["log"].problems, "kept": a["log"].kept}
     for name, a in arms.items()}, indent=2), encoding="utf-8")
note("The last two rows have no model in the compaction at all: the form is built from the "
     "ledger of tool results. It cannot drop a payer, and it cannot record an open question, "
     "because nothing in a tool result is a question.")


def m(arm, key):
    return arms[arm]["grade"][key]


learn.record(
    hops=len(want),
    threshold=THRESHOLD,
    plain_found=m("no compaction", "found"),
    plain_tokens=arms["no compaction"]["run"].total_prompt_tokens,
    plain_largest=arms["no compaction"]["run"].largest_request,
    paragraph_found=m("a paragraph", "found"),
    paragraph_totals=m("a paragraph", "totals_right"),
    paragraph_compactions=para["log"].compactions,
    paragraph_kept_last=last_kept,
    paragraph_seen_last=last_seen,
    paragraph_stopped=para["run"].stopped.split(":")[0],
    form_found=m("a form, checked", "found"),
    form_totals=m("a form, checked", "totals_right"),
    form_compactions=form["log"].compactions,
    form_refused=form["log"].refused,
    form_largest=form["run"].largest_request,
    form_stopped=form["run"].stopped.split(":")[0],
    code_found=m("a form, filled in by code", "found"),
    code_totals=m("a form, filled in by code", "totals_right"),
    code_compactions=code["log"].compactions,
    code_tokens=code["run"].total_prompt_tokens,
    code_largest=code["run"].largest_request,
    code_kept_last=code["log"].kept[-1][0] if code["log"].kept else 0,
    both_found=both["grade"]["found"],
    both_totals=both["grade"]["totals_right"],
    both_invented=both["grade"]["invented"],
    both_sent_back=both["run"].sent_back,
    both_tokens=both["run"].total_prompt_tokens,
    both_largest=both["run"].largest_request,
    both_stopped=both["run"].stopped.split(":")[0],
    check_probes=PROBED["probes"],
    check_caught=PROBED["caught"],
    check_kept_good=PROBED["kept_good"],
    mine=MINE is not None,
)

finding(f"""
Compacted to a paragraph whenever it passed {THRESHOLD:,} tokens, the trace was compacted
{para['log'].compactions} times; after the last, {last_kept} of the {last_seen} flows the tools
had returned were still whole, and the report held {m('a paragraph', 'found')} of {len(want)}
hops with {m('a paragraph', 'totals_right')} totals right. With a form checked in code,
{form['log'].refused} forms were refused and the report held {m('a form, checked', 'found')}
hops with {m('a form, checked', 'totals_right')} totals right. With the form filled in by code
from the tool results, the form held every flow and the report
{m('a form, filled in by code', 'found')} hops. With the report also checked against the ledger
and sent back {both['run'].sent_back} times:
{both['grade']['found']} of {len(want)} hops, totals right on {both['grade']['totals_right']}, in
{both['run'].total_prompt_tokens:,} tokens with no request over {both['run'].largest_request:,},
where the uncompacted trace took {arms['no compaction']['run'].total_prompt_tokens:,} and reached
{arms['no compaction']['run'].largest_request:,}.
""")
save_shot("10-compaction-with-a-schema")
