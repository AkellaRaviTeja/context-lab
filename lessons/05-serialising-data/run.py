"""Chapter 05: serialising data. The same thirty-one payments in six shapes, counted and read."""

import json
import random
from collections import Counter

from lantern import baseline, case, context, formats, learn
from lantern.config import ROOT
from lantern.llm import chat
from lantern.ui import Table, chapter, console, evidence, finding, note, save_shot, step

chapter(
    "05",
    "Thirty-one payments, five ways",
    """
Thursday 16 July, 09:00. Halcyon paid Northwind thirty-one times. Those thirty-one rows have
been in front of LANTERN since April, always in the same shape: the JSON the bank tool returns.

Okafor has never liked it. "Every row says 'amount' again. Thirty-one times. I would not pay a
clerk to write that."

You show him the same rows as a table, then as comma-separated lines.

"Smaller," he says. "Does it still read the right cell?"

That is the question. A format that saves a third of the window and misreads one amount in
thirty-one has saved nothing the court can use.
""",
)

MINE = learn.mine()  # --mine: your to_toon() and to_markdown() from practice/exercise.py
OUT = ROOT / ".scratch" / "05"
SEEDS = (7, 8, 9)
SYSTEM = "Answer from the payments only. Reply with the value alone, nothing else."
FORMATS = dict(formats.FORMATS)
if MINE:
    FORMATS["TOON"] = lambda rows: MINE.to_toon(rows, "payments")
    FORMATS["Markdown table"] = MINE.to_markdown
else:
    FORMATS["TOON"] = lambda rows: formats.to_toon(rows, "payments")
# Challenge: the shape step 4 gives every tool result. None lets the run choose: the fewest
# tokens among the shapes that read best in step 3.
STATEMENT_AS: str | None = None


def questions_for(rows) -> list[tuple[str, str, str]]:
    """Ten questions with one right answer each, of five kinds. (kind, question, answer)."""
    rng = random.Random(6)
    pick = rng.sample(rows, 7)
    qs = [("a cell, by reference", f"What is the amount of the payment with reference "
           f"{r['reference']}?", r["amount"]) for r in pick[:4]]
    qs += [("a cell, by two others", f"What is the reference of the payment dated {r['date']} "
            f"for {r['amount']}?", r["reference"]) for r in pick[4:]]
    qs.append(("a count of all rows", "How many payments are listed? Reply with a number.",
               str(len(rows))))
    rare = Counter(r["payer_account"] for r in rows).most_common()[-1]
    qs.append(("a count of some rows", f"How many payments came from payer_account {rare[0]}? "
               "Reply with a number.", str(rare[1])))
    biggest = max(rows, key=lambda r: float(r["amount"]))
    qs.append(("the largest", "What is the reference of the largest payment?",
               biggest["reference"]))
    return qs


def read(doc: str, question: str, seed: int):
    return chat("Payments from Halcyon to Northwind:\n\n" + doc + "\n\n" + question,
                system=SYSTEM, seed=seed, max_tokens=40)


OUT.mkdir(parents=True, exist_ok=True)
rows = case.rows("ledger/halcyon-to-northwind.csv")
docs = {name: f(rows) for name, f in FORMATS.items()}

step("1. The same rows, six shapes")
evidence("case/ledger/halcyon-to-northwind.csv",
         f"{len(rows)} payments, {len(rows[0])} fields each: {', '.join(rows[0])}.")
for name in ("JSON, indented", "CSV", "TOON"):
    evidence(f"{name}: the first two payments", "\n".join(docs[name].splitlines()[:{
        "JSON, indented": 14, "CSV": 3, "TOON": 3}[name]]))

step("2. What each costs")
p_ratio = learn.predict_number(
    "Indented JSON, as the bank tool returns it, against the smallest of the other shapes. How "
    "many times as many tokens is the JSON?", unit="times")
tokens = {name: context.count_tokens(doc) for name, doc in docs.items()}
table = Table(title=f"{len(rows)} payments, counted with the model's tokenizer")
for col in ("shape", "characters", "tokens", "tokens a row", "against indented JSON"):
    table.add_column(col, justify="left" if col == "shape" else "right")
for name, n in tokens.items():
    table.add_row(name, f"{len(docs[name]):,}", f"{n:,}", f"{n / len(rows):.0f}",
                  f"{n / tokens['JSON, indented']:.0%}")
console.print(table)
smallest = min(tokens, key=tokens.get)
ratio = tokens["JSON, indented"] / tokens[smallest]
note(f"The smallest is {smallest}, {tokens[smallest]:,} tokens. Indented JSON is "
     f"{tokens['JSON, indented']:,}, {ratio:.2f} times as many, and every one of the extra "
     "tokens is a key, a quote, a brace or white space written again for each row.")
learn.reveal(p_ratio, actual=ratio, tolerance=0.15,
             why="The values are identical in every shape. What a shape costs is how often it "
             "repeats the keys and what it puts between the cells.")

step("3. Does it still read the right cell?")
qs = questions_for(rows)
p_read = learn.predict(
    f"Each shape is asked the same {len(qs)} questions on {len(SEEDS)} seeds. Which is read "
    "right most often?",
    ["Indented JSON: the keys are beside every value", "A table shape: Markdown, CSV or TOON",
     "They all read the same"])
results, wrong = {}, {}
for name, doc in docs.items():
    answers = [(kind, q, a, seed, read(doc, q, seed).text) for kind, q, a in qs for seed in SEEDS]
    results[name] = [(kind, a in got.replace(",", "")) for kind, _, a, _, got in answers]
    wrong[name] = [{"kind": k, "question": q, "right": a, "seed": s, "got": got}
                   for k, q, a, s, got in answers if a not in got.replace(",", "")]
(OUT / "wrong.json").write_text(json.dumps(wrong, indent=2), encoding="utf-8")
kinds = list(dict.fromkeys(k for k, _, _ in qs))
table = Table(title=f"Right answers of {len(qs) * len(SEEDS)}, by kind of question")
table.add_column("shape")
for k in kinds:
    table.add_column(k, justify="right")
table.add_column("all", justify="right")
table.add_column("tokens", justify="right")
right = {}
for name, rs in results.items():
    right[name] = sum(ok for _, ok in rs)
    table.add_row(name, *(f"{sum(ok for kk, ok in rs if kk == k)} of "
                          f"{sum(kk == k for kk, _ in rs)}" for k in kinds),
                  f"{right[name]}", f"{tokens[name]:,}")
console.print(table)
asked = len(qs) * len(SEEDS)
best = max(right.values())
counted_all = [n for n, rs in results.items()
               if all(ok for k, ok in rs if k == "a count of all rows")]
note(f"Best: {best} of {asked}. Worst: {min(right.values())} of {asked}. The row count was "
     f"right on every seed only for: {', '.join(counted_all) or 'none of them'}. Every wrong "
     "answer is in .scratch/05/wrong.json.")
tables = ("Markdown table", "CSV", "TOON")
best_table, best_json = max(right[n] for n in tables), right["JSON, indented"]
learn.reveal(p_read, answer=0 if best_json > best_table else 1 if best_table > best_json else 2,
             why="Keys beside every value did not make the cell easier to find here. Counting "
             "rows is hard in every shape that does not state the count.")

step("4. One shape, scored on the signed questions")
chosen = STATEMENT_AS or min((n for n in right if right[n] == best), key=tokens.get)
p_score = learn.predict(
    f"Every statement a tool returns is now drawn as {chosen} and the 26 signed questions are "
    "asked again. How many answers change verdict against the baseline of 17?",
    ["None", "1 or 2", "3 to 5", "6 or more"])
parts = context.sections()


def render(result):
    return formats.render_result(result, FORMATS[chosen])


base = baseline.reference(chat=chat)
after = baseline.score(parts, chat=chat, render=render)
(OUT / "reshaped.json").write_text(json.dumps(after, indent=2), encoding="utf-8")
diff = baseline.changed(base, after)
k, k2, n = sum(r["passed"] for r in base), sum(r["passed"] for r in after), len(base)
big, big2 = max(r["prompt_tokens"] for r in base), max(r["prompt_tokens"] for r in after)
table = Table(title="Both Pellmar statements in the session, in two shapes")
for col in ("statements as", "largest request", "passed", "evidence slice"):
    table.add_column(col, justify="left" if col == "statements as" else "right")
table.add_row("JSON, as the tool returns it", f"{big:,}", f"{k} of {n}",
              "{} of {}".format(*baseline.by_slice(base)["evidence"]))
table.add_row(chosen, f"{big2:,}", f"{k2} of {n}",
              "{} of {}".format(*baseline.by_slice(after)["evidence"]))
console.print(table)
note(f"Fixed: {', '.join(diff['fixed']) or 'none'}. Broken: {', '.join(diff['broken']) or 'none'}."
     f" The largest request fell by {big - big2:,} tokens.")
for i in diff["broken"] + diff["fixed"]:
    r = next(r for r in after if r["id"] == i)
    note(f"{i} now ({', '.join(r['called']) or 'no tool'}): {r['answer'][:130]}")
moved = len(diff["fixed"]) + len(diff["broken"])
learn.reveal(p_score, answer=learn.bucket(moved, [0, 2, 5]),
             why="A shape that reads well on one table is still a change to the context. It is "
             "kept only if the signed questions say so.")

learn.record(
    payments=len(rows),
    tokens_json=tokens["JSON, indented"],
    tokens_compact=tokens["JSON, compact"],
    tokens_yaml=tokens["YAML"],
    tokens_markdown=tokens["Markdown table"],
    tokens_csv=tokens["CSV"],
    tokens_toon=tokens["TOON"],
    smallest=smallest,
    json_over_smallest=round(ratio, 2),
    asked=asked,
    right_json=right["JSON, indented"],
    right_compact=right["JSON, compact"],
    right_yaml=right["YAML"],
    right_markdown=right["Markdown table"],
    right_csv=right["CSV"],
    right_toon=right["TOON"],
    counted_all=len(counted_all),
    chosen=chosen,
    baseline_passed=k,
    reshaped_passed=k2,
    reshaped_fixed=len(diff["fixed"]),
    reshaped_broken=len(diff["broken"]),
    reshaped_evidence=baseline.by_slice(after)["evidence"][0],
    tokens_saved_largest=big - big2,
    mine=MINE is not None,
)

finding(f"""
The {len(rows)} payments are {tokens['JSON, indented']:,} tokens as the indented JSON the bank
tool returns and {tokens[smallest]:,} as {smallest}: {ratio:.2f} times as many for the same
values. Asked {len(qs)} questions on {len(SEEDS)} seeds, the shapes were read right between
{min(right.values())} and {best} times of {asked}; indented JSON {right['JSON, indented']}, CSV
{right['CSV']}, TOON {right['TOON']}, the Markdown table {right['Markdown table']}. With every
statement in the session drawn as {chosen}, the signed questions went from {k} of {n} to {k2} of
{n}: fixed {', '.join(diff['fixed']) or 'none'}, broken {', '.join(diff['broken']) or 'none'},
and the largest request {big - big2:,} tokens smaller.
""")
save_shot("05-serialising-data")
