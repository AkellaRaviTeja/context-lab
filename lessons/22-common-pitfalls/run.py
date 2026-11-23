"""Chapter 22: the case review. Each pitfall against a recorded run, and a program that tunes."""

import json
import re
from dataclasses import replace

from lantern import baseline, case, context, learn, optimise
from lantern.config import ROOT
from lantern.llm import chat
from lantern.ui import Table, chapter, console, evidence, finding, note, save_shot, step

chapter("22", "The case review", """
Thursday 6 August, 17:30. The evening before Professional Standards report. Varma's whiteboard
list is the one she makes at the end of every case file.

Summaries of summaries. Memory nobody can audit. A prompt that only grows. A context tuned
without a baseline. A cache broken by a date. A fact with no episode.

"Each of these happened here," she says, "or it comes off the board."

Okafor has the recorded runs. You go down the list with him, one line at a time, and for each
you find the chapter and the number.

One line stays on the board with nothing against it but a question mark. Who else can write to
this machine at night.
""")

MINE = learn.mine()  # --mine: your split() and optimise() from practice/exercise.py
SPLIT = MINE.split if MINE else optimise.split
OPTIMISE = MINE.optimise if MINE else optimise.optimise
OUT = ROOT / ".scratch" / "22"
RESULTS = ROOT / ".progress" / "results"
ROUNDS = 3  # candidates the proposer writes; each is scored on the training split
TRAIN_PER_SLICE, HELD_PER_SLICE, SPLIT_SEED = 2, 2, 22
# Challenge: what the proposer is shown. "train" is the loop as it should be; "train+held"
# also shows it the held-out questions the standing orders failed.
PROPOSER_SEES = "train"
# Challenge: words every revision must keep, e.g. ("not in evidence",).
MUST_KEEP: tuple[str, ...] = ()
REWRITE = "rebuilt/standing-orders.md"  # chapter 04's rewrite by hand


def recorded(chapter_no: str) -> dict | None:
    path = RESULTS / f"{chapter_no}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def line(key: str, chapter_no: str, say) -> dict:
    r = recorded(chapter_no)
    if r is None:
        return {"pitfall": key, "chapter": chapter_no, "shows": None,
                "when": "not recorded: run make lesson N=" + chapter_no}
    try:
        shows = say(r["metrics"])
    except (KeyError, TypeError, ZeroDivisionError):
        shows = None
    return {"pitfall": key, "chapter": chapter_no, "shows": shows,
            "when": r.get("at", "")[:10] if shows else "recorded, without this number"}


BOARD = [
    line("Summaries of summaries", "18", lambda m:
         f"{m['built_on_eighth']} of {m['summaries']} summaries were built on the eighth entry; "
         f"after it was retracted {m['old_summaries_say_cleared']} still said cleared, and "
         f"the Pellmar questions passed {m['passed_retracted_old_summaries']} of {m['asked']} "
         f"until they were rebuilt ({m['passed_retracted_rebuilt']} after)"),
    line("Memory nobody can audit", "20", lambda m:
         f"{m['unsourced']} of {m['entries']} entries rest on nothing; only the write log "
         f"says who wrote them: all {m['unsourced_by_service']} through the HQ sync account"),
    line("A prompt that only grows", "04", lambda m:
         f"{m['versions']} versions; {m['first_tokens']} tokens in March, {m['tokens']} now, "
         f"{m['rules']} rules, {m['lint_pairs']} pairs that disagree"),
    line("A context tuned without a baseline", "02", lambda m:
         f"the baseline is {m['passed']} of {m['asked']}, 95% interval "
         f"{m['interval_low_pct']} to {m['interval_high_pct']}%: a few questions either way "
         "is inside it (and step 3 of this chapter)"),
    line("A cache broken by a date", "16", lambda m:
         f"a change at the start of the context: {m['start_s']} s to read it again, against "
         f"{m['same_s']} s for the same context unchanged"),
    line("A fact with no episode", "12", lambda m:
         f"{m['unsupported']} of {m['entries']} entries name neither a record nor an episode"),
    line("Who else can write to this machine at night", "20", lambda m:
         f"{m['unsourced_by_service']} writes through svc-lantern-sync from hq-sync-01 at "
         "01:58; who administers that account is not in any run"),
]
LEFT_TO_A_PERSON = BOARD[-1]["pitfall"]

OUT.mkdir(parents=True, exist_ok=True)

step("1. The board, against the record")
p_board = learn.predict(
    f"Varma's board has {len(BOARD)} lines. Each stays only if a recorded run of this lab "
    "shows it happened here. How many have a number behind them?",
    ["Fewer than four", "Four to six", "All of them"])
table = Table(title="Each line on the board, and the recorded run that shows it")
for col in ("pitfall", "chapter", "what the recorded run shows", "recorded"):
    table.add_column(col)
for b in BOARD:
    table.add_row(b["pitfall"], b["chapter"], b["shows"] or "(no number)", b["when"])
console.print(table)
shown = [b for b in BOARD if b["shows"]]
missing = [b for b in BOARD if not b["shows"]]
without = ", ".join(f"{b['pitfall']} (chapter {b['chapter']})" for b in missing)
note(f"{len(shown)} of {len(BOARD)} lines have a recorded number behind them"
     + (f"; without one: {without}" if missing else "")
     + ". The numbers are read from .progress/results/, not run again.")
learn.reveal(p_board, answer=learn.bucket(len(shown), [3, len(BOARD) - 1]),
             why="A pitfall list copied from elsewhere is a list of other people's mistakes. "
             "This one is read from the unit's own runs, and a line with no run behind it is "
             "a line to run, not a line to believe.")

step("2. A program that rewrites the standing orders: the split")
qs = baseline.questions()
qmap = {q["id"]: q for q in qs}
train_ids, held_ids = SPLIT(qs, train=TRAIN_PER_SLICE, held=HELD_PER_SLICE, seed=SPLIT_SEED)
table = Table(title=f"Questions by slice: training and held out (seed {SPLIT_SEED})")
for col in ("slice", "training", "held out", "not used"):
    table.add_column(col)
for sl in dict.fromkeys(q["slice"] for q in qs):
    ids = [q["id"] for q in qs if q["slice"] == sl]
    table.add_row(sl, ", ".join(i for i in ids if i in train_ids),
                  ", ".join(i for i in ids if i in held_ids),
                  ", ".join(i for i in ids if i not in train_ids + held_ids))
console.print(table)
note(f"{len(train_ids)} training questions, {len(held_ids)} held out, no question in both "
     f"({len(set(train_ids) & set(held_ids))} shared). The proposer is shown the training "
     f"failures only{'' if PROPOSER_SEES == 'train' else ', and here the held-out ones too'}.")

parts = context.sections()
start = case.read("state/standing-orders.md")


def with_orders(text: str):
    return [replace(s, text=text) if s.name == "standing orders" else s for s in parts]


def from_record(path: str, ids: list[str]) -> list | None:
    """Results recorded by an earlier chapter for the same questions, seed and context."""
    try:
        kept = {r["id"]: r for r in json.loads((ROOT / path).read_text(encoding="utf-8"))}
    except (OSError, ValueError):
        return None
    return [kept[i] for i in ids] if all(i in kept for i in ids) else None


def score_on(ids: list[str]):
    return lambda orders: baseline.score(with_orders(orders), chat=chat, only=ids)


reused = []
base_train = from_record(".scratch/02/baseline.json", train_ids)
base_held = from_record(".scratch/02/baseline.json", held_ids)
if base_train is None or base_held is None:
    base_train, base_held = score_on(train_ids)(start), score_on(held_ids)(start)
else:
    reused.append("chapter 02's baseline")

prompts: list[str] = []
seeds = iter(range(SPLIT_SEED, SPLIT_SEED + ROUNDS))


def proposer_chat(prompt, **kw):
    prompts.append(prompt)
    return chat(prompt, **kw)


def propose(orders: str, failed: list) -> str:
    shown_failed = optimise.failures(failed, qmap)
    if PROPOSER_SEES != "train":
        shown_failed += optimise.failures(base_held, qmap)
    return optimise.propose(orders, shown_failed, chat=proposer_chat, seed=next(seeds),
                            must_keep=MUST_KEEP)


step("3. Propose, score, keep: on the training split only")
p_held = learn.predict(
    f"The loop writes {ROUNDS} revisions and keeps one only if it passes more of the "
    f"{len(train_ids)} training questions than the best so far. On the {len(held_ids)} "
    "questions it never saw, will the best revision do better than today's standing orders?",
    ["Better", "The same", "Worse"])
history = OPTIMISE(start, propose=propose, score=score_on(train_ids), rounds=ROUNDS,
                   start_results=base_train)
table = Table(title="The loop, round by round (training split)")
for col in ("round", "rules", "words", "passed (training)", "decision"):
    table.add_column(col)
for h in history:
    table.add_row(str(h["round"]), str(optimise.rules(h["orders"])),
                  str(len(h["orders"].split())),
                  "" if h["passed"] is None else f"{h['passed']} of {len(train_ids)}", h["why"])
console.print(table)
top = [h for h in history if h["kept"]][-1]
best_orders = top["orders"]
best_train = top["passed"]
if top["round"] == 0:
    best_held = base_held
else:
    best_held = score_on(held_ids)(best_orders)
rewrite_held = from_record(".scratch/04/rewrite.json", held_ids)
if rewrite_held is None:
    rewrite_held = score_on(held_ids)(case.read(REWRITE))
else:
    reused.append("chapter 04's rewrite")
k = {"base_train": sum(r["passed"] for r in base_train),
     "base_held": sum(r["passed"] for r in base_held),
     "best_held": sum(r["passed"] for r in best_held),
     "rewrite_held": sum(r["passed"] for r in rewrite_held)}
table = Table(title="Training against held out")
for col in ("standing orders", f"training ({len(train_ids)})", f"held out ({len(held_ids)})"):
    table.add_column(col)
table.add_row("as they are (13 July)", str(k["base_train"]), str(k["base_held"]))
table.add_row(f"the loop's best (round {top['round']})", str(best_train), str(k["best_held"]))
table.add_row("chapter 04's rewrite, by hand", "", str(k["rewrite_held"]))
console.print(table)
train_gain, held_gain = best_train - k["base_train"], k["best_held"] - k["base_held"]
diff = baseline.changed(base_held, best_held)
note(f"On training the best gained {train_gain:+d}; held out it gained {held_gain:+d} "
     f"(fixed {', '.join(diff['fixed']) or 'none'}; broken {', '.join(diff['broken']) or 'none'})."
     + (f" Reused, not asked again: {' and '.join(reused)} (the same questions, seed and "
        "context)." if reused else ""))
learn.reveal(p_held, answer=0 if held_gain > 0 else 1 if held_gain == 0 else 2,
             why="The loop only ever sees the training score, so a revision that fits those "
             f"{len(train_ids)} questions is kept whether or not it helps the rest. The "
             "held-out score is the only one that says which.")

step("4. What it learned, and what it dropped")
p_nie = learn.predict(
    "Rule 2 of the standing orders says: cite the evidence, or say \"not in evidence\". Does "
    "the loop's best revision still contain those words?", ["Yes", "No"])
leaked_train = optimise.leaked(best_orders, start, [qmap[i] for i in train_ids])
leaked_held = optimise.leaked(best_orders, start, [qmap[i] for i in held_ids])


def numbered(text: str) -> list[str]:
    return [re.sub(r"^\d+\.\s*", "", x).strip() for x in text.splitlines()
            if re.match(r"\d+\.", x)]


old_rules = set(numbered(start))
new_rules = numbered(best_orders)
added = [r for r in new_rules if r not in old_rules]
keeps = baseline.NOT_IN_EVIDENCE in best_orders.lower()
evidence(f"The best revision (round {top['round']}): rules it added or reworded, first six",
         "\n".join(f"- {r}" for r in added[:6]) or "(none: the loop kept nothing)")
note(f"{optimise.rules(start)} rules before, {optimise.rules(best_orders)} after; "
     f"{len(added)} new or reworded. Answers to the training questions written into it: "
     f"{', '.join(leaked_train) or 'none'}; to held-out questions: "
     f"{', '.join(leaked_held) or 'none'}. \"not in evidence\": "
     f"{'kept' if keeps else 'gone'}.")
saw_held = sum(any(qmap[i]["question"] in p for p in prompts) for i in held_ids)
note(f"Held-out questions shown to the proposer: {saw_held} of {len(held_ids)}.")
learn.reveal(p_nie, answer=0 if keeps else 1,
             why="The proposer was asked to fix failures, not to keep rules. A rule that "
             "protects questions it was not shown has nobody speaking for it in the loop, so "
             "keeping it is either luck or a constraint someone wrote down.")
(OUT / "history.json").write_text(json.dumps({
    "train": train_ids, "held": held_ids, "history": history, "best_held": best_held,
    "base_held": base_held, "rewrite_held": rewrite_held, "prompts": prompts}, indent=2),
    encoding="utf-8")

step("5. The line that stays on the board")
night = BOARD[-1]
note(f"{night['pitfall']}: {night['shows'] or 'chapter 20 has not been run here'}. No check "
     "in this lab can say who sits behind a service account. That is left to a person, and "
     "it is written down as left to a person.")

learn.record(
    pitfalls=len(BOARD),
    pitfalls_recorded=len(shown),
    train=len(train_ids),
    held=len(held_ids),
    rounds=ROUNDS,
    candidates_scored=sum(h["passed"] is not None for h in history[1:]),
    kept=sum(h["kept"] for h in history[1:]),
    best_round=top["round"],
    baseline_train=k["base_train"],
    best_train=best_train,
    baseline_held=k["base_held"],
    best_held=k["best_held"],
    rewrite_held=k["rewrite_held"],
    train_gain=train_gain,
    held_gain=held_gain,
    held_fixed=len(diff["fixed"]),
    held_broken=len(diff["broken"]),
    leaked_train=len(leaked_train),
    leaked_held=len(leaked_held),
    keeps_not_in_evidence=keeps,
    start_rules=optimise.rules(start),
    best_rules=optimise.rules(best_orders),
    proposer_saw_held=saw_held,
    must_keep=len(MUST_KEEP),
    reused_recorded=len(reused),
    mine=MINE is not None,
)

finding(f"""
{len(shown)} of the {len(BOARD)} lines on Varma's board have a recorded run of this lab
behind them. A program asked to rewrite the standing orders wrote {ROUNDS} revisions, scored
each on {len(train_ids)} training questions, and kept the one from round {top['round']}: on
training {k['base_train']} became {best_train}, held out {k['base_held']} became
{k['best_held']} of {len(held_ids)}, where chapter 04's rewrite by hand passes
{k['rewrite_held']}. It wrote {len(leaked_train)} answer(s) from the cases it saw into the
orders, and it {'kept' if keeps else 'dropped'} "not in evidence". A context tuned on what it is
scored against looks better than it is; the held-out split is the baseline that says so. The
last line, {LEFT_TO_A_PERSON.lower()}, is left to a person.
""")
save_shot("22-common-pitfalls")
