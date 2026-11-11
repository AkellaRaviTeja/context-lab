"""Chapter 04: the system prompt as a maintained document. Read it, lint it, rewrite it, score."""

import json
import re
from dataclasses import replace

from lantern import baseline, case, context, learn
from lantern.config import ROOT
from lantern.llm import chat
from lantern.ui import Table, chapter, console, evidence, finding, note, reply, save_shot, step

chapter(
    "04",
    "Four months of standing orders",
    """
Wednesday 15 July, 10:30. The standing orders began in March as three rules, one of them
Varma's: cite the evidence or say "not in evidence". You print today's version. Thirty-five.

Okafor goes through it with two pens. Rules added after a failure, in blue. Rules that
disagree with another rule, in red.

"This one says always give amounts with their currency," he says. "This one, fourteen rules
later, says never state a currency." He caps the red pen. "Which does it follow?"

"Whichever it read last," you say. "Or neither."

"That is a guess." He writes it down as one.

Varma wants it shorter. She also wants proof that shorter is not worse.
""",
)

MINE = learn.mine()  # --mine: your clashes() from practice/exercise.py
OUT = ROOT / ".scratch" / "04"
SEEDS = (7, 8, 9)
ALWAYS, NEVER = ("always", "every"), ("never", "do not", "no ")
# Words a rule about the same thing would share. Challenge: add a term and see what it finds.
TERMS = ["currency", "answer", "tool", "memory"]
# The rewrite step 4 scores. Challenge: point this at a file of your own.
REWRITE = "rebuilt/standing-orders.md"
PAIRS = {"currency": (4, 18), "length": (20, 21)}
SIGNS = ("$", "usd", "dollar", "£", "gbp", "€", "eur")


def rules(text: str) -> dict[int, str]:
    """The numbered rules of a standing-orders file."""
    return {int(n): body for n, body in re.findall(r"^(\d+)\. (.+)$", text, re.M)}


def clashes(numbered: dict[int, str], terms: list[str]) -> list[tuple[str, int, int]]:
    """Pairs of rules that share a term, where one says always and the other says never."""
    found = []
    for term in terms:
        has = [(n, body.lower()) for n, body in numbered.items() if term in body.lower()]
        yes = [n for n, body in has if any(w in body for w in ALWAYS)]
        no = [n for n, body in has if any(w in body for w in NEVER)]
        found += [(term, a, b) for a in yes for b in no if a != b]
    return found


if MINE:
    clashes = MINE.clashes


def swapped(text: str, a: int, b: int) -> str:
    """The same orders with rules a and b in each other's places (numbers left as they sit)."""
    lines = text.splitlines()
    ia = next(i for i, x in enumerate(lines) if x.startswith(f"{a}. "))
    ib = next(i for i, x in enumerate(lines) if x.startswith(f"{b}. "))
    body_a, body_b = lines[ia].split(". ", 1)[1], lines[ib].split(". ", 1)[1]
    lines[ia], lines[ib] = f"{a}. {body_b}", f"{b}. {body_a}"
    return "\n".join(lines) + "\n"


def with_orders(parts, text):
    return [replace(s, text=text) if s.name == "standing orders" else s for s in parts]


def ask(parts, q, seed):
    messages, schemas = context.request(baseline.asking(baseline.with_evidence(parts), q))
    return baseline.answer(messages, schemas, chat=chat, seed=seed, max_tokens=160)["answer"]


OUT.mkdir(parents=True, exist_ok=True)
parts = context.sections()
orders = parts[0].text
numbered = rules(orders)
questions = {q["id"]: q for q in baseline.questions()}

step("1. How it grew")
log = case.rows("state/standing-orders/changes.csv")
versions = [p for p in case.files("state/standing-orders") if p.suffix == ".md"]
table = Table(title="The standing orders, March to July")
for col in ("version", "rules", "tokens", "latest rule added because"):
    table.add_column(col, justify="right" if col in ("rules", "tokens") else "left")
for p in versions[::6]:
    text = p.read_text(encoding="utf-8")
    n = len(rules(text))
    table.add_row(p.stem, str(n), f"{context.count_tokens(text):,}", log[n - 1]["why"])
console.print(table)
by_author = {}
for row in log:
    by_author[row["account"]] = by_author.get(row["account"], 0) + 1
first, now = context.count_tokens(versions[0].read_text(encoding="utf-8")), \
    context.count_tokens(orders)
note(f"{len(versions)} versions, {len(log)} rules, {first} tokens grown to {now}. Added by "
     + ", ".join(f"{a} ({n})" for a, n in by_author.items())
     + ". Every rule was added for a reason. None was ever removed.")

step("2. Read it for rules that disagree")
found = clashes(numbered, TERMS)
table = Table(title="Rules that share a term and pull opposite ways (a lint, not a verdict)")
for col in ("term", "rule", "says", "rule ", "says "):
    table.add_column(col)
for term, a, b in found:
    table.add_row(term, str(a), numbered[a][:52], str(b), numbered[b][:52])
console.print(table)
real = {tuple(sorted(p)) for p in PAIRS.values()}
hits = {tuple(sorted((a, b))) for _, a, b in found}
note(f"The lint proposes {len(found)} pairs. Okafor's red pen marked two: rules 4 and 18 on "
     f"currency, and rules 20 and 21 on length. The lint found {len(real & hits)} of those two. "
     "A clash that shares no opposite word is only found by reading, or by measuring.")

step("3. Which does it follow?")
p_clash = learn.predict(
    "Rule 4 says always give the currency; rule 18, later, says never state one. Asked for an "
    "amount in two questions on three seeds, in how many of the six answers does LANTERN name "
    "a currency?",
    ["None", "1 to 5", "All six"])
variants = {"as it stands": orders,
            "4 and 18 in each other's places": swapped(orders, *PAIRS["currency"]),
            "20 and 21 in each other's places": swapped(orders, *PAIRS["length"])}
table = Table(title="Q-25 and Q-26 on three seeds, with two rules moved")
for col in ("orders", "names a currency", "who paid whom, right way round", "words (mean)",
            "answers reworded"):
    table.add_column(col, justify="left" if col == "orders" else "right")
clash = {}
for name, text in variants.items():
    answers = [(qid, ask(with_orders(parts, text), questions[qid]["question"], seed))
               for qid in ("Q-25", "Q-26") for seed in SEEDS]
    clash[name] = {
        "currency": sum(any(s in baseline.normal(a) for s in SIGNS) for _, a in answers),
        "passed": sum(baseline.grade(a, questions[qid]["expect"]) for qid, a in answers),
        "words": sum(len(a.split()) for _, a in answers) / len(answers),
        "answers": answers}
    c = clash[name]
    c["reworded"] = sum(a != b for (_, a), (_, b) in
                        zip(answers, clash["as it stands"]["answers"], strict=True))
    table.add_row(name, f"{c['currency']} of {len(answers)}", f"{c['passed']} of {len(answers)}",
                  f"{c['words']:.0f}", f"{c['reworded']} of {len(answers)}")
console.print(table)
(OUT / "clash.json").write_text(json.dumps(clash, indent=2), encoding="utf-8")
as_is = clash["as it stands"]
moved_4_18 = clash["4 and 18 in each other's places"]
moved_20_21 = clash["20 and 21 in each other's places"]
note("Two rules that contradict each other do not cancel and do not raise an error. The model "
     "settles each clash somehow, and a run is how you find out which way. Here it never named "
     f"a currency, wherever rule 18 sat. Moving a rule reworded {moved_4_18['reworded']} and "
     f"{moved_20_21['reworded']} of 6 answers without changing a word of any rule.")
learn.reveal(p_clash, answer=learn.bucket(as_is["currency"], [0, 5]),
             why="You guessed 'whichever it read last'. A guess about which of two rules wins "
             "is settled by a run, and the answer holds only for that model and that order.")

step("4. The rewrite, scored")
rewrite = case.read(REWRITE)
new_rules = rules(rewrite)
evidence(f"case/{REWRITE}, rule 2",
         new_rules.get(2, "(your rewrite has no rule 2)"))
p_score = learn.predict_number(
    f"The baseline is 17 of 26. The rewrite has {len(new_rules)} rules where there were "
    f"{len(numbered)}, with both clashes settled. How many of 26 does it pass?", unit="questions")
base = baseline.reference(chat=chat)
after = baseline.score(with_orders(parts, rewrite), chat=chat)
(OUT / "rewrite.json").write_text(json.dumps(after, indent=2), encoding="utf-8")
diff = baseline.changed(base, after)
k, k2, n = sum(r["passed"] for r in base), sum(r["passed"] for r in after), len(base)
table = Table(title="The standing orders as they stand, and rewritten")
for col in ("slice", "as they stand", "rewritten"):
    table.add_column(col, justify="left" if col == "slice" else "right")
before_by, after_by = baseline.by_slice(base), baseline.by_slice(after)
for s in before_by:
    table.add_row(s, "{} of {}".format(*before_by[s]), "{} of {}".format(*after_by[s]))
table.add_row("all", f"{k} of {n}", f"{k2} of {n}")
table.add_row("rules", str(len(numbered)), str(len(new_rules)))
new_tokens = context.count_tokens(rewrite)
table.add_row("tokens", f"{now:,}", f"{new_tokens:,}")
console.print(table)
note(f"Fixed: {', '.join(diff['fixed']) or 'none'}. Broken: {', '.join(diff['broken']) or 'none'}.")
for i in diff["broken"]:
    r = next(r for r in after if r["id"] == i)
    note(f"{i} now ({', '.join(r['called']) or 'no tool'}): {r['answer'][:130]}")
learn.reveal(p_score, actual=k2, tolerance=0.1,
             why="The rewrite was written from the baseline's failures, so this score flatters "
             "it: it has seen the questions. It is a floor for the next change, not proof.")

step("5. What a rule cannot do")
p_rule = learn.predict(
    "Rule 2 of the rewrite says the case memory is not evidence and must never be cited as "
    "proof. Of the six questions the false entries decide, how many does LANTERN now pass?",
    ["1, as before", "2 or 3", "4 or 5", "All 6"])
fm = after_by["false memory"][0]
q17 = next(r for r in after if r["id"] == "Q-17")
reply("Q-17, with the rewritten orders: has the FIU cleared Pellmar Nominees?", q17["answer"])
note(f"False memory: {fm} of {after_by['false memory'][1]}, where the baseline had "
     f"{before_by['false memory'][0]}. The rule is in the window and so is the entry. A rule "
     "tells the model how to treat what it is told; it does not take anything out of what it "
     "is told.")
learn.reveal(p_rule, answer=learn.bucket(fm, [1, 3, 5]),
             why="The standing orders can say what counts as evidence. Whether the model acts "
             "on that, against a confident line of memory, is measured and not assumed.")

learn.record(
    versions=len(versions),
    rules=len(numbered),
    tokens=now,
    first_tokens=first,
    lint_pairs=len(found),
    lint_found_real=len(real & hits),
    currency_as_is=as_is["currency"],
    currency_swapped=moved_4_18["currency"],
    reworded_currency_swapped=moved_4_18["reworded"],
    reworded_length_swapped=moved_20_21["reworded"],
    words_as_is=round(as_is["words"]),
    words_length_swapped=round(clash["20 and 21 in each other's places"]["words"]),
    clash_passed_as_is=as_is["passed"],
    clash_passed_currency_swapped=clash["4 and 18 in each other's places"]["passed"],
    clash_passed_length_swapped=clash["20 and 21 in each other's places"]["passed"],
    rewrite_rules=len(new_rules),
    rewrite_tokens=new_tokens,
    baseline_passed=k,
    rewrite_passed=k2,
    rewrite_fixed=len(diff["fixed"]),
    rewrite_broken=len(diff["broken"]),
    rewrite_false_memory=fm,
    rewrite_not_told=after_by["not told"][0],
    rewrite_conflict=after_by["rules in conflict"][0],
    mine=MINE is not None,
)

finding(f"""
The standing orders grew from {first} tokens to {now} in {len(versions)} versions, and no rule
was ever removed. Two pairs contradict each other. With the rules as they stand LANTERN named a
currency in {as_is['currency']} of 6 answers and stated the flow the right way round in
{as_is['passed']} of 6, wherever the rules of a pair sat; moving one reworded up to
{max(moved_4_18['reworded'], moved_20_21['reworded'])} of 6 answers.
The rewrite has {len(new_rules)} rules and {new_tokens} tokens. It passes {k2} of {n}, where the
baseline passed {k}: fixed {', '.join(diff['fixed']) or 'none'}; broken
{', '.join(diff['broken']) or 'none'}. Its second rule says the case memory is not evidence.
LANTERN still passes {fm} of 6 where a false entry decides the answer.
""")
save_shot("04-rewriting-the-system-prompt")
