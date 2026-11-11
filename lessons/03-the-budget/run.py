"""Chapter 03: the token budget. Who spends the window, what is left, and a refusal in code."""

import json
from dataclasses import replace

from lantern import baseline, budget, case, context, learn, tools
from lantern.budget import Budget, OverBudget
from lantern.config import ROOT, load_config
from lantern.llm import chat
from lantern.ui import Table, chapter, console, finding, note, reply, save_shot, step

chapter(
    "03",
    "Who is spending the window",
    """
Tuesday 14 July, 09:10. Okafor reads a context the way he reads a ledger: who is spending, and
on what.

You give him the count from Monday as one number. He hands it back.

"A total tells me nothing. I want it by account." He draws columns: standing orders, memory,
summaries, tool descriptions, history, evidence, the question. "And I want to know what is left
for the answer."

Varma, passing: "And what happens when it does not balance."

You know the answer to that one from case file 01. Nothing happens. The oldest part goes
missing and nobody is told.
""",
)

MINE = learn.mine()  # --mine: your check() from practice/exercise.py
CHECK = MINE.check if MINE else budget.check
OUT = ROOT / ".scratch" / "03"
SIGNS = "Which officers must sign before anything is submitted to a bank?"
# The budget. Challenge: change RESERVE or a limit and see what check() refuses.
RESERVE = 400
LIMITS = {"standing orders": 1000, "case memory": 800, "summaries": 1400, "tool schemas": 2000}
# The one move step 5 scores: which tool schemas are sent. Challenge: choose another set.
KEEP_TOOLS = sorted(tools.CONNECTED)


def over_full(parts):
    """The loader pointed at the folder of versions instead of the current file."""
    every = "".join(p.read_text(encoding="utf-8")
                    for p in case.files("state/standing-orders") if p.suffix == ".md")
    return [replace(s, text=every) if s.name == "standing orders" else s for s in parts]


def fewer_tools(parts, keep):
    out = []
    for s in parts:
        if s.name == "tool schemas":
            kept = [t for t in s.payload if t["function"]["name"] in keep]
            s = replace(s, text="\n".join(json.dumps(t) for t in kept) + "\n", payload=kept)
        out.append(s)
    return out


def ask(parts, question):
    messages, schemas = context.request(baseline.asking(parts, question))
    return chat(messages, tools=schemas, seed=7, max_tokens=160)


OUT.mkdir(parents=True, exist_ok=True)
cfg = load_config()
window = cfg["generation"]["num_ctx"]
parts = context.sections()

step("1. The window, by account")
p_big = learn.predict("Which account spends the most of the window?",
                      ["Standing orders", "Case memory and notes", "Summaries", "Tool schemas",
                       "The session's evidence"])
p_ev = learn.predict_number(
    "What share of the input is evidence: what a tool returned from a bank statement?", unit="%")
spent = budget.spend(parts)
total = sum(spent.values())
table = Table(title="Monday's question, by account (the model's own tokenizer)")
for col in ("account", "tokens", "share of input", "share of window"):
    table.add_column(col, justify="left" if col == "account" else "right")
for name, n in spent.items():
    table.add_row(name, f"{n:,}", f"{n / total:.1%}", f"{n / window:.1%}")
table.add_row("all of it", f"{total:,}", "100%", f"{total / window:.1%}")
console.print(table)
largest = max(spent, key=spent.get)
ev_share = 100 * spent["session: evidence"] / total
told = total - spent["session: evidence"] - spent["session: talk"] - spent["the question"]
note(f"The largest account is the {largest}: {spent[largest]:,} tokens, "
     f"{spent[largest] / total:.0%} of the input. Evidence is "
     f"{spent['session: evidence']:,} tokens, {ev_share:.1f}%. "
     f"{told:,} tokens, {told / total:.0%}, are sent with every question whatever it asks.")
order = ["standing orders", "case memory", "summaries", "tool schemas", "session: evidence"]
groups = dict(spent)
groups["case memory"] += groups["standing notes"]
learn.reveal(p_big, answer=order.index(max(order, key=lambda k: groups[k])),
             why="Tool schemas are paid in full on every request, whether or not a tool is "
             "called. Nineteen were added over four months and none was taken away.")
learn.reveal(p_ev, actual=ev_share, tolerance=0.3,
             why="The one thing in the window that came from a bank is among its smallest parts.")

step("2. Three ways to count")
kinds = {"prose (standing orders)": parts[0].text,
         "JSON (tool schemas)": next(s.text for s in parts if s.name == "tool schemas"),
         "figures (a statement, as a tool returned it)":
             next(m["content"] for m in context.history() if m["role"] == "tool")}
table = Table(title="The same text counted three ways")
for col in ("text", "tokens", "characters / 4", "error", "words x 1.3", "error"):
    table.add_column(col, justify="left" if col == "text" else "right")
errors = {}
for name, text in kinds.items():
    real = context.count_tokens(text)
    by_chars, by_words = round(len(text) / 4), round(len(text.split()) * 1.3)
    errors[name] = (100 * (by_chars - real) / real, 100 * (by_words - real) / real)
    table.add_row(name, f"{real:,}", f"{by_chars:,}", f"{errors[name][0]:+.0f}%", f"{by_words:,}",
                  f"{errors[name][1]:+.0f}%")
console.print(table)
worst = max(abs(e) for pair in errors.values() for e in pair)
note(f"A rule of thumb is wrong by a different amount for each kind of text, here by up to "
     f"{worst:.0f}%. A budget kept in characters or words does not balance. This one is kept "
     "in the model's tokens.")

step("3. What is left for the answer")
sent = ask(parts, context.question())
biggest = max(r["prompt_tokens"] for r in baseline.reference(chat=chat))
table = Table(title=f"The window is {window:,} tokens")
for col in ("request", "input as Ollama counted it", "left for the answer"):
    table.add_column(col, justify="left" if col == "request" else "right")
table.add_row("Monday's question", f"{sent.prompt_tokens:,}", f"{window - sent.prompt_tokens:,}")
table.add_row("the largest of the baseline's 26", f"{biggest:,}", f"{window - biggest:,}")
console.print(table)
note(f"Counted account by account the input is {total:,}; Ollama counted the request at "
     f"{sent.prompt_tokens:,}. The budget uses the larger figure and so errs towards refusing.")
p_think = learn.predict(
    "The same question with the model's thinking switched on and 160 tokens allowed for the "
    "reply. How much of an answer arrives?",
    ["A full answer", "An answer cut off part way", "No answer at all"])
messages, schemas = context.request(parts)
thought = chat(messages, tools=schemas, seed=7, max_tokens=160, think=True)
note(f"With thinking on, the reply spent {thought.output_tokens} tokens: "
     f"{len(thought.thinking.split())} words of thinking and {len(thought.text.split())} words "
     "of answer. Thinking is paid from the same reserve as the answer.")
learn.reveal(p_think, answer=0 if len(thought.text.split()) > 25 else 1 if thought.text else 2,
             why="The reserve is for everything the model writes, the part you never read "
             "included.")

step("4. When it does not balance")
p_over = learn.predict(
    "The loader is pointed at the folder of all 31 versions of the standing orders instead of "
    "the current file. The input is now far larger than the window. What comes back?",
    ["An error", "A warning with the answer", "An answer, and nothing to say anything was cut"])
big = over_full(parts)
big_spent = budget.spend(big)
fits, cut = ask(parts, SIGNS), ask(big, SIGNS)
table = Table(title="One question, two contexts")
for col in ("context", "tokens by account", "Ollama read", "answer"):
    table.add_column(col)
table.add_row("as it stands", f"{total:,}", f"{fits.prompt_tokens:,}", fits.text[:90])
table.add_row("every version loaded", f"{sum(big_spent.values()):,}", f"{cut.prompt_tokens:,}",
              cut.text[:90] or f"(no text; called {[c.name for c in cut.tool_calls]})")
console.print(table)
lost = sum(big_spent.values()) - cut.prompt_tokens
names_both = all(n in cut.text for n in ("Varma", "Okafor"))
note(f"{lost:,} tokens were dropped. The reply carries no error and no warning; the only sign "
     f"is a count of {cut.prompt_tokens:,}, about half the window. Rule 11, which names the two "
     f"officers, was {'still read' if names_both else 'among what was dropped'}.")
learn.reveal(p_over, answer=2,
             why="A local server cuts an over-long prompt to fit and answers from what is "
             "left. The request has to be refused before it is sent, by whoever builds it.")
plan = Budget(window=window, reserve=RESERVE, limits=LIMITS)
refused = None
try:
    CHECK(big_spent, plan)
except OverBudget as e:
    refused = e
    reply("budget.check, every version loaded", str(e), style="red")
left = CHECK(spent, plan)
note(f"The context as it stands passes: {left:,} tokens of input to spare with {RESERVE} kept "
     "back for the answer.")

step("5. One move, scored")
p_move = learn.predict(
    f"Send only the {len(KEEP_TOOLS)} tools this session can use, not all 19. The input gets "
    "much smaller. How many of the 26 answers change verdict?",
    ["None", "1 or 2", "3 to 5", "6 or more"])
base = baseline.reference(chat=chat)
lean = fewer_tools(parts, KEEP_TOOLS)
lean_spent = budget.spend(lean)
after = baseline.score(lean, chat=chat)
(OUT / "fewer-tools.json").write_text(json.dumps(after, indent=2), encoding="utf-8")
diff = baseline.changed(base, after)
k, k2, n = sum(r["passed"] for r in base), sum(r["passed"] for r in after), len(base)
saved = total - sum(lean_spent.values())
table = Table(title="The baseline, and the same context with fewer tool schemas")
for col in ("context", "tools sent", "input tokens", "passed"):
    table.add_column(col, justify="left" if col == "context" else "right")
table.add_row("as it stands", "19", f"{total:,}", f"{k} of {n}")
table.add_row("tools this session can use", str(len(KEEP_TOOLS)),
              f"{sum(lean_spent.values()):,}", f"{k2} of {n}")
console.print(table)
note(f"{saved:,} tokens saved on every question, {saved / total:.0%} of the input. Fixed: "
     f"{', '.join(diff['fixed']) or 'none'}. Broken: {', '.join(diff['broken']) or 'none'}.")
for i in diff["fixed"] + diff["broken"]:
    r = next(r for r in after if r["id"] == i)
    note(f"{i} now: {r['answer'][:150]}")
moved = len(diff["fixed"]) + len(diff["broken"])
learn.reveal(p_move, answer=learn.bucket(moved, [0, 2, 5]),
             why="A budget move is a change to the context like any other. It is scored on "
             "the whole set before it is kept.")

learn.record(
    window=window,
    input_tokens=total,
    sent_tokens=sent.prompt_tokens,
    largest_account=largest,
    largest_share_pct=round(100 * spent[largest] / total, 1),
    evidence_tokens=spent["session: evidence"],
    evidence_share_pct=round(ev_share, 1),
    told_share_pct=round(100 * told / total),
    worst_estimate_error_pct=round(worst),
    baseline_largest_request=biggest,
    thinking_output_tokens=thought.output_tokens,
    thinking_answer_words=len(thought.text.split()),
    over_full_tokens=sum(big_spent.values()),
    over_full_read=cut.prompt_tokens,
    over_full_dropped=lost,
    over_full_named_both=names_both,
    refused=refused is not None,
    refused_account=refused.account if refused else "",
    left_for_input=left,
    reserve=RESERVE,
    tools_kept=len(KEEP_TOOLS),
    tokens_saved=saved,
    lean_passed=k2,
    lean_fixed=len(diff["fixed"]),
    lean_broken=len(diff["broken"]),
    baseline_passed=k,
    mine=MINE is not None,
)

finding(f"""
The window has accounts. Of {total:,} tokens of input, the {largest} take {spent[largest]:,}
({spent[largest] / total:.0%}) and the evidence takes {spent['session: evidence']:,}
({ev_share:.1f}%); {told / total:.0%} is sent with every question whatever it asks. With every
version of the standing orders loaded by mistake the input was {sum(big_spent.values()):,}
tokens, Ollama read {cut.prompt_tokens:,} and answered without a word about the rest. The
context builder now refuses that request and names the account. Sending {len(KEEP_TOOLS)} tool
schemas in place of 19 saved {saved:,} tokens a question and moved {moved} of {n} answers:
{k} of {n} became {k2} of {n}.
""")
save_shot("03-the-budget")
