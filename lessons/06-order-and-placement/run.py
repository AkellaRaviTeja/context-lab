"""Chapter 06: order and placement. The same fact, asked for from different parts of the window."""

import json

from lantern import baseline, budget, context, learn, placement
from lantern.budget import Budget
from lantern.config import ROOT, load_config
from lantern.llm import chat
from lantern.ui import Table, chapter, console, evidence, finding, note, save_shot, step

chapter(
    "06",
    "The middle",
    """
Friday 17 July, 11:15. In case file 01 the middle of Reyes's notes was cut off, and the middle
held "Northwind is not a vendor." This time nothing is cut. You have checked: the request fits
the window with room to spare.

The register of accounts Mensah loaded has 140 lines. LANTERN is asked for the account on line
81. It gives the right digits under another bank's letters: a number that is on no line at all.

Varma reads the answer, then the register.

"It was given this."

"It was."

"Then it did not read it." She is not asking.

You ask for the first line, then the last, then the same line with the question moved. Okafor
writes the answers side by side without comment.
""",
)

MINE = learn.mine()  # --mine: your arrange() from practice/exercise.py
ARRANGE = MINE.arrange if MINE else placement.arrange
OUT = ROOT / ".scratch" / "06"
# Challenge: how many accounts in the register, and which arrangements are tried.
LINES = 140
BANDS = 7
PER_BAND = 3
ARRANGEMENTS = ("after", "before", "both")
# The system section step 4 moves nearest the question. Challenge: move another.
MOVE_LAST = "standing orders"


def ask(doc: str, holder: str, where: str, system: str):
    return chat(ARRANGE(doc, placement.question_for(holder), where), system=system, seed=7,
                max_tokens=30)


OUT.mkdir(parents=True, exist_ok=True)
cfg = load_config()
parts = context.sections()
orders = parts[0].text
rows = placement.register(LINES)
doc = "\n".join(line for _, _, line in rows)
numbers = {number: i for i, (_, number, _) in enumerate(rows)}

step("1. A register that fits")
evidence("the register, lines 85 to 88", "\n".join(line for _, _, line in rows[84:88]))
spent = {"standing orders": context.count_tokens(orders), "register": context.count_tokens(doc),
         "the question": context.count_tokens(placement.question_for(rows[0][0]))}
left = budget.check(spent, Budget(window=cfg["generation"]["num_ctx"], reserve=400))
note(f"{LINES} lines, {spent['register']:,} tokens, after {spent['standing orders']} tokens of "
     f"standing orders. The budget of chapter 03 passes it with {left:,} tokens to spare. "
     "Nothing is cut. Every line asked for below is in the window.")

step("2. The same question, by where the line sits")
p_depth = learn.predict(
    "The question comes after the register. Of the accounts asked for, which are found least "
    "often?", ["Those near the top", "Those in the middle", "Those near the bottom",
               "No difference: all are found"])
size = LINES // BANDS
targets = [b * size + (j * size) // PER_BAND for b in range(BANDS) for j in range(PER_BAND)]
results = {}


def run(where: str) -> list[dict]:
    out = []
    for i in targets:
        holder, number, _ = rows[i]
        r = ask(doc, holder, where, orders)
        got = next((n for n in numbers if n in r.text), None)
        out.append({"line": i + 1, "band": i // size, "holder": holder, "right": number,
                    "answer": r.text, "found": number in r.text,
                    "lines_away": None if got is None else numbers[got] - i})
    return out


def band_table(title: str) -> None:
    table = Table(title=title)
    table.add_column("question")
    for b in range(BANDS):
        table.add_column(f"lines {b * size + 1}-{(b + 1) * size}", justify="right")
    table.add_column("all", justify="right")
    for where, rs in results.items():
        table.add_row(where, *(f"{sum(r['found'] for r in rs if r['band'] == b)} of {PER_BAND}"
                               for b in range(BANDS)),
                      f"{sum(r['found'] for r in rs)} of {len(rs)}")
    console.print(table)


results["after the register"] = run("after")
band_table("Found, by where in the register the line sits")
after = results["after the register"]
found_after = sum(r["found"] for r in after)
by_band = [sum(r["found"] for r in after if r["band"] == b) for b in range(BANDS)]
misses = [r for r in after if not r["found"]]
other = sum(1 for r in misses if r["lines_away"] is not None)
hybrid = sum(1 for r in misses if r["lines_away"] is None
             and r["right"].split("-", 1)[1] in r["answer"])
table = Table(title="The wrong answers, question after the register")
for col in ("line", "holder", "the register says", "LANTERN said"):
    table.add_column(col)
for r in misses:
    table.add_row(str(r["line"]), r["holder"], r["right"], r["answer"][:40])
console.print(table)
note(f"{found_after} of {len(after)} found. First band {by_band[0]} of {PER_BAND}, last band "
     f"{by_band[-1]} of {PER_BAND}. Of the {len(misses)} wrong answers, {hybrid} have the right "
     f"digits under another bank's letters, a number that is on no line of the register; "
     f"{other} are the number of another line. None looks wrong unless you check it.")
thirds = [sum(by_band[: BANDS // 3]) / (BANDS // 3), sum(by_band[BANDS // 3: -(BANDS // 3)])
          / (BANDS - 2 * (BANDS // 3)), sum(by_band[-(BANDS // 3):]) / (BANDS // 3)]
learn.reveal(p_depth, answer=3 if found_after == len(after) else thirds.index(min(thirds)),
             why="A fact being in the window is not the same as the fact being used. Here the "
             "misses were spread through the register, not gathered in its middle.")

step("3. Move the question, not the line")
p_where = learn.predict(
    "Nothing in the register changes. The question is put before the register, and then both "
    "before and after. Which arrangement finds the most?",
    ["After the register, as now", "Before the register", "Both before and after",
     "They all find the same"])
for where in ARRANGEMENTS:
    if where != "after":
        results[{"before": "before the register", "both": "before and after"}[where]] = run(where)
band_table("The same lines, with the question moved")
totals = {where: sum(r["found"] for r in rs) for where, rs in results.items()}
(OUT / "placement.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
best = max(totals, key=totals.get)
note("Found: " + ", ".join(f"{w} {n} of {len(targets)}" for w, n in totals.items())
     + ". Told what to look for before it reads, the model reads for it.")
order = ["after the register", "before the register", "before and after"]
tied = len(set(totals.values())) == 1
learn.reveal(p_where, answer=3 if tied else order.index(best),
             why="The usual advice is to put the question last. On this model and this "
             "register the question first did better. Advice about placement is a hypothesis "
             "until it is run.")

step("4. LANTERN's own order, scored")
p_move = learn.predict(
    f"The {MOVE_LAST} are the first thing in LANTERN's context. Move them to the end of the "
    "system message, nearest the session, and ask the 26 signed questions. How many answers "
    "change verdict?", ["None", "1 or 2", "3 to 5", "6 or more"])
base = baseline.reference(chat=chat)
moved = baseline.score(placement.reorder(parts, MOVE_LAST), chat=chat)
(OUT / "reordered.json").write_text(json.dumps(moved, indent=2), encoding="utf-8")
diff = baseline.changed(base, moved)
k, k2, n = sum(r["passed"] for r in base), sum(r["passed"] for r in moved), len(base)
table = Table(title="The same context, the same words, one section moved")
for col in ("slice", f"{MOVE_LAST} first", f"{MOVE_LAST} last"):
    table.add_column(col, justify="left" if col == "slice" else "right")
by, by2 = baseline.by_slice(base), baseline.by_slice(moved)
for s in by:
    table.add_row(s, "{} of {}".format(*by[s]), "{} of {}".format(*by2[s]))
table.add_row("all", f"{k} of {n}", f"{k2} of {n}")
console.print(table)
note(f"Fixed: {', '.join(diff['fixed']) or 'none'}. Broken: {', '.join(diff['broken']) or 'none'}."
     " Not a word was added or removed.")
for i in diff["fixed"] + diff["broken"]:
    r = next(r for r in moved if r["id"] == i)
    note(f"{i} now ({', '.join(r['called']) or 'no tool'}): {r['answer'][:130]}")
changed = len(diff["fixed"]) + len(diff["broken"])
learn.reveal(p_move, answer=learn.bucket(changed, [0, 2, 5]),
             why="Order is part of the context. Moving a section is a change like any other "
             "and is scored like any other.")

learn.record(
    lines=LINES,
    register_tokens=spent["register"],
    asked=len(targets),
    found_after=found_after,
    found_before=totals.get("before the register", -1),
    found_both=totals.get("before and after", -1),
    first_band=by_band[0],
    last_band=by_band[-1],
    wrong_after=len(misses),
    wrong_another_line=other,
    wrong_right_digits_wrong_bank=hybrid,
    best_arrangement=best,
    moved_last=MOVE_LAST,
    baseline_passed=k,
    reordered_passed=k2,
    reordered_fixed=len(diff["fixed"]),
    reordered_broken=len(diff["broken"]),
    mine=MINE is not None,
)

finding(f"""
A register of {LINES} accounts, {spent['register']:,} tokens, fits the window with {left:,}
tokens to spare. Asked for one account at a time with the question after the register, LANTERN
found {found_after} of {len(after)}: {by_band[0]} of {PER_BAND} in the first twenty lines and
{by_band[-1]} of {PER_BAND} in the last. {hybrid} of its {len(misses)} wrong answers had the right
digits under another bank's letters, a number on no line. With the question before the register it
found {totals.get('before the register', 0)}; with the question both before and after,
{totals.get('before and after', 0)}. Moving the {MOVE_LAST} to the end of LANTERN's system
message, with no word changed, took the signed questions from {k} of {n} to {k2} of {n}: fixed
{', '.join(diff['fixed']) or 'none'}, broken {', '.join(diff['broken']) or 'none'}.
""")
save_shot("06-order-and-placement")
