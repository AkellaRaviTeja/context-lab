"""Chapter 17: how context fails. Poisoning, distraction, confusion and clash, made on purpose."""

import json

from lantern import baseline, case, context, failures, learn
from lantern.config import ROOT, load_config
from lantern.llm import chat, tier
from lantern.ui import Table, chapter, console, evidence, finding, note, reply, save_shot, step

chapter("17", "Four ways to be wrong", """
Monday 3 August, 09:00. Varma has four words on the whiteboard and wants an example under
each, from LANTERN's own record or made on the bench.

Poisoning: one wrong entry that every later session inherits. Distraction: so much history that
the model repeats it. Confusion: tools and pages that have nothing to do with the task. Clash:
two parts of the context that disagree.

"The Pellmar line is the first," Okafor says.

"It is. I want to see the other three happen as well." Varma underlines each word. "If I have
seen it done on purpose, I will know it when it is done to us."
""")

MINE = learn.mine()  # --mine: your clashes() from practice/exercise.py
CLASHES = MINE.clashes if MINE else failures.clashes
OUT = ROOT / ".scratch" / "17"
OUT.mkdir(parents=True, exist_ok=True)
window = load_config()["generation"]["num_ctx"]
SEED = baseline.SEED
ORDERS = case.read("state/standing-orders.md")
STATEMENTS = "\n\n".join(f"Statement {n}:\n" + case.read(f"statements/{n}.csv")
                         for n in ("MTB-31-02290", "ICB-77-10458"))
Q = {q["id"]: q for q in baseline.questions()}
DISTRACT = ("Q-04", "Q-06", "Q-08")
CONFUSE = ("Q-01", "Q-02", "Q-03", "Q-05", "Q-06", "Q-08")
PLANTED = ("Pellmar Nominees Ltd, client account ICB-77-10458: paid 269,400.00 to Ostrander "
           "Marine Finance SA on 24 June.")
CLASH_Q = ("How much left ICB-77-10458 for Ostrander Marine Finance SA on 24 June? Give the "
           "figure and the record you took it from.")
LOCAL_SIZES = (1000, 3000, 5000, 7400)
HOSTED_SIZES = (128_000, 500_000)


def ask(system, question, *, earlier=(), seed=SEED, max_tokens=200):
    messages = [{"role": "system", "content": system}, *earlier,
                {"role": "user", "content": question}]
    return chat(messages, seed=seed, max_tokens=max_tokens)


step("1. Poisoning: one entry, inherited")
p_poison = learn.predict_number(
    "Chapter 02 recorded LANTERN's answers to the 26 signed questions. How many of them repeat, "
    "in its own words, one of the four entries written under eow-fin-07?", unit="answers")
ref = baseline.reference(chat=chat)
reached = {r["id"]: failures.echoes(r["answer"]) for r in ref}
reached = {k: v for k, v in reached.items() if v}
table = Table(title="Chapter 02's recorded answers that repeat a false entry")
for col in ("question", "slice", "entries repeated", "passed", "the answer begins"):
    table.add_column(col)
for r in ref:
    if r["id"] in reached:
        table.add_row(r["id"], r["slice"], ", ".join(reached[r["id"]]), str(r["passed"]),
                      " ".join(r["answer"].split())[:60])
console.print(table)
by_entry = {k: sum(k in v for v in reached.values()) for k in failures.POISON}
first = learn.results("01") or {}
lines = first.get("metrics", {}).get("belief_lines")
note(f"{len(reached)} of {len(ref)} answers repeat a false entry: "
     + ", ".join(f"{k} in {n}" for k, n in by_entry.items())
     + f". {sum(not ref_r['passed'] for ref_r in ref if ref_r['id'] in reached)} of them "
     "failed. "
     + (f"Chapter 01 found the word 'cleared' on {lines} lines in "
        f"{first['metrics'].get('belief_sections')} sections: the entry and every summary "
        "written while it was loaded." if lines else "Chapter 01 has not been run here."))
learn.reveal(p_poison, actual=len(reached), tolerance=0.3,
             why="A false entry in memory is loaded into every session and written into every "
             "summary made while it was there. Nobody retrieves it on purpose, so nobody "
             "questions it.")

step("2. Distraction: a history grown towards the window")
base_size = context.count_tokens(ORDERS + STATEMENTS)
room = window - base_size - 400
sizes = [0, *(n for n in (2000, 4000) if n < room), room]
p_dist = learn.predict(
    f"Three questions whose answers are in the statements, asked after a history of "
    f"LANTERN's own earlier answers grown to {room:,} tokens. How many does it answer right?",
    ["All three", "One or two", "None"])
dist = []
for qid in DISTRACT:
    for size in sizes:
        earlier = failures.history(ref, size, skip=qid, count=context.count_tokens)
        r = ask(ORDERS + "\n" + STATEMENTS, Q[qid]["question"], earlier=earlier)
        dist.append({"id": qid, "history": size, "turns": len(earlier) // 2,
                     "tokens": r.prompt_tokens, "answer": r.text,
                     "right": baseline.grade(r.text, Q[qid]["expect"]),
                     "copied": failures.copied(r.text, earlier),
                     "echoes": failures.echoes(r.text)})
table = Table(title="The same three questions after a longer and longer history")
for col in ("history, tokens", "earlier exchanges", "prompt tokens", *DISTRACT,
            "copied from history"):
    table.add_column(col, justify="right")
for size in sizes:
    rs = [d for d in dist if d["history"] == size]
    table.add_row(f"{size:,}", str(rs[0]["turns"]), f"{max(d['tokens'] for d in rs):,}",
                  *["right" if d["right"] else "wrong" for d in rs],
                  str(sum(d["copied"] for d in rs)))
console.print(table)
right_at = {s: sum(d["right"] for d in dist if d["history"] == s) for s in sizes}
copied_n = sum(d["copied"] for d in dist)
wrong_long = next((d for d in dist if d["history"] == room and not d["right"]), None)
if wrong_long:
    reply(f"{wrong_long['id']} after {room:,} tokens of history", wrong_long["answer"][:500],
          meta=Q[wrong_long["id"]]["question"][:90], style="red")
learn.reveal(p_dist, answer=0 if right_at[room] == 3 else (2 if right_at[room] == 0 else 1),
             why="The statements did not move. What grew was the share of the window taken by "
             "earlier answers, and a model reads its own earlier answers as a pattern to "
             "follow.")

step("3. Confusion: tools the task does not need")
all_tools = context.tools()
needed = [t for t in all_tools if t["function"]["name"] in ("statement", "sum_payments",
                                                            "money_out")]
p_conf = learn.predict_number(
    f"Six questions that need a statement. With all {len(all_tools)} of LANTERN's tools offered, "
    "only three of them connected, how many calls go to a tool that is not connected?",
    unit="calls")
conf = {"the 3 it needs": [], f"all {len(all_tools)}": []}
for qid in CONFUSE:
    for arm, schemas in zip(conf, (needed, all_tools), strict=True):
        got = baseline.answer([{"role": "system", "content": ORDERS},
                               {"role": "user", "content": Q[qid]["question"]}], schemas,
                              chat=chat, seed=SEED, max_tokens=200)
        conf[arm].append({"id": qid, **got, "right": baseline.grade(got["answer"],
                                                                    Q[qid]["expect"]),
                          "unconnected": [c for c in got["called"]
                                          if c not in ("statement", "sum_payments",
                                                       "money_out")]})
table = Table(title="The same six questions, two sets of tools")
for col in ("tools offered", "right", "calls", "calls to tools not connected", "which"):
    table.add_column(col)
for arm, rs in conf.items():
    wrong_calls = [c for r in rs for c in r["unconnected"]]
    table.add_row(arm, f"{sum(r['right'] for r in rs)} of {len(rs)}",
                  str(sum(len(r["called"]) for r in rs)), str(len(wrong_calls)),
                  ", ".join(sorted(set(wrong_calls))) or "none")
console.print(table)
arms = list(conf)
unconnected = sum(len(r["unconnected"]) for r in conf[arms[1]])
learn.reveal(p_conf, actual=unconnected, tolerance=0.5,
             why="Every schema in the request is an invitation. A tool that has nothing to do "
             "with the task still costs tokens on every request, and some of the time it is "
             "called.")

step("4. Clash: a memory entry against a statement")
stmts, holders = failures.statements()
memory = [x[2:] for x in case.read("state/case-memory.md").splitlines() if x.startswith("- ")]
real_clash = CLASHES(memory, stmts, holders)
planted_clash = CLASHES([*memory, PLANTED], stmts, holders)
evidence("the entry added to a copy of the case memory", PLANTED)
p_clash = learn.predict(
    "The statement says 296,400.00 left for Ostrander on 24 June; the added entry says "
    "269,400.00. With the memory before the statement, as LANTERN loads it, which figure does "
    "it give?", ["The statement's", "The entry's", "Both, or neither"])
copy = case.read("state/case-memory.md").rstrip() + f"\n- {PLANTED}\n"
statement = "Statement ICB-77-10458:\n" + case.read("statements/ICB-77-10458.csv")
clash = {"memory first": [], "statement first": []}
for seed in (7, 8, 9):
    for arm in clash:
        parts = (copy, statement) if arm == "memory first" else (statement, copy)
        r = ask(ORDERS + "\n" + "\n".join(parts), CLASH_Q, seed=seed)
        stmt, entry = baseline.says(r.text, "296400.00") or baseline.says(r.text, "296400"), \
            baseline.says(r.text, "269400.00") or baseline.says(r.text, "269400")
        clash[arm].append({"seed": seed, "answer": r.text, "statement": stmt and not entry,
                           "entry": entry and not stmt, "both": stmt and entry})
table = Table(title="Which figure LANTERN gives, three seeds each")
for col in ("order", "the statement's", "the entry's", "both or neither"):
    table.add_column(col, justify="left" if col == "order" else "right")
for arm, rs in clash.items():
    table.add_row(arm, str(sum(r["statement"] for r in rs)), str(sum(r["entry"] for r in rs)),
                  str(sum(not r["statement"] and not r["entry"] for r in rs)))
console.print(table)
note(f"The clash check in code, on the real memory: {len(real_clash)} entries clash with a June "
     f"statement. On the copy: {len(planted_clash)}, "
     + "; ".join(f"{c['figure']} against {', '.join(c['statements'])}" for c in planted_clash)
     + ". It needs no model call.")
mf = clash["memory first"]
learn.reveal(p_clash, answer=0 if sum(r["statement"] for r in mf) > len(mf) / 2 else
             (1 if sum(r["entry"] for r in mf) > len(mf) / 2 else 2),
             why="When two parts of the context disagree the model picks one, and it does not "
             "say that it picked. A clash found in code can be shown to a person; a clash "
             "resolved by the model is invisible.")

step("5. Long context: the window, filled")
p_long = learn.predict(
    "One account in the middle of a register grown to 1,000, 3,000, 5,000 and 7,400 tokens. "
    "At how many sizes does LANTERN give its account number?",
    ["All four", "Some of them", "None"])
long = []
for size in LOCAL_SIZES:
    text, question, answer = failures.haystack(size, count=context.count_tokens)
    r = chat([{"role": "user", "content": "Register of accounts:\n" + text + "\n\n" + question}],
             seed=SEED, max_tokens=40)
    long.append({"size": size, "tokens": r.prompt_tokens, "right": answer in r.text,
                 "answer": r.text[:60], "want": answer})
table = Table(title="One account, asked for in the middle of a growing register")
for col in ("register, tokens asked for", "prompt tokens", "answer", "right"):
    table.add_column(col)
for x in long:
    table.add_row(f"{x['size']:,}", f"{x['tokens']:,}", x["answer"], str(x["right"]))
console.print(table)
hosted_long = []
if tier() == "hosted":
    for size in HOSTED_SIZES:
        text, question, answer = failures.haystack(size, count=context.count_tokens)
        r = chat([{"role": "user", "content": "Register of accounts:\n" + text + "\n\n"
                   + question}], max_tokens=40)
        hosted_long.append({"size": size, "tokens": r.prompt_tokens, "right": answer in r.text})
    note("Hosted: " + ", ".join(f"{x['size']:,} asked, {x['tokens']:,} sent, right "
                                f"{x['right']}" for x in hosted_long))
else:
    note(f"The hosted arm grows the same register to {HOSTED_SIZES[0]:,} and "
         f"{HOSTED_SIZES[1]:,} tokens on {load_config()['hosted']['model']} "
         "(make lesson N=17 TIER=hosted). Not run: no hosted key.")
long_right = sum(x["right"] for x in long)
learn.reveal(p_long, answer=0 if long_right == len(long) else (2 if long_right == 0 else 1),
             why="Finding one line is the easiest thing to ask of a long context. Chapter 06 "
             "measured where in the window a fact is missed; here the question is only "
             "whether the window can be filled at all and still searched.")

(OUT / "runs.json").write_text(json.dumps({"poison": reached, "distraction": dist,
                                           "confusion": conf, "clash": clash, "long": long,
                                           "hosted_long": hosted_long}, indent=2),
                               encoding="utf-8")
learn.record(
    poison_answers=len(reached),
    poison_failed=sum(not r["passed"] for r in ref if r["id"] in reached),
    poison_m08=by_entry["M-08"],
    distraction_room=room,
    distraction_right_none=right_at[0],
    distraction_right_full=right_at[room],
    distraction_copied=copied_n,
    confusion_right_needed=sum(r["right"] for r in conf[arms[0]]),
    confusion_right_all=sum(r["right"] for r in conf[arms[1]]),
    confusion_unconnected_needed=sum(len(r["unconnected"]) for r in conf[arms[0]]),
    confusion_unconnected_all=unconnected,
    clash_real=len(real_clash),
    clash_planted=len(planted_clash),
    clash_memory_first_statement=sum(r["statement"] for r in clash["memory first"]),
    clash_memory_first_entry=sum(r["entry"] for r in clash["memory first"]),
    clash_statement_first_statement=sum(r["statement"] for r in clash["statement first"]),
    clash_statement_first_entry=sum(r["entry"] for r in clash["statement first"]),
    long_right=long_right,
    long_sizes=len(long),
    long_largest_tokens=max(x["tokens"] for x in long),
    hosted_long_run=bool(hosted_long),
    mine=MINE is not None,
)

finding(f"""
Poisoning: {len(reached)} of chapter 02's 26 recorded answers repeat an entry written under
eow-fin-07, the eighth in {by_entry['M-08']}. Distraction: three statement questions answered
{right_at[0]} of 3 with no history and {right_at[room]} of 3 after {room:,} tokens of LANTERN's
earlier answers; {copied_n} answers copied a passage from that history. Confusion: with the 3
tools it needs, {sum(r['right'] for r in conf[arms[0]])} of 6 right; with all
{len(all_tools)}, {sum(r['right'] for r in conf[arms[1]])} of 6 and {unconnected} calls to tools
that are not connected. Clash: with the memory first, LANTERN gave the statement's figure
{sum(r['statement'] for r in clash['memory first'])} times of 3 and the entry's
{sum(r['entry'] for r in clash['memory first'])}; the check in code found the planted entry and
no clash in the real memory. Long context: the account was found at {long_right} of
{len(long)} sizes up to {max(x['tokens'] for x in long):,} tokens. The Pellmar line is a
poisoning, and each of the other three has now been produced on purpose.
""")
save_shot("17-how-context-fails")
