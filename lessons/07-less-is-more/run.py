"""Chapter 07: less is more. True pages that are merely related, added until an answer changes."""

import json

from lantern import baseline, budget, context, learn, pages
from lantern.budget import Budget
from lantern.config import ROOT, load_config
from lantern.llm import chat
from lantern.ui import Table, chapter, console, evidence, finding, note, save_shot, step

chapter(
    "07",
    "More to go on",
    """
Monday 20 July, 09:40. Mensah's instinct is the careful officer's instinct: give it everything
about Pellmar. Every notice, every minute, every email that names it.

"More to go on," she says.

You expect the answers to get worse, and say so. Every guide you have read says they will.

"Then show me," Varma says.

You run the questions with the two statements that answer them. Then with four more pages
that mention Pellmar and answer nothing. Then eight. Then twelve. Okafor keeps the tally.

"Well?" Mensah asks.

"Not one answer moved," you say. "What moved is how much room is left."
""",
)

MINE = learn.mine()  # --mine: your overlap() and select() from practice/exercise.py
SELECT = MINE.select if MINE else pages.select
OUT = ROOT / ".scratch" / "07"
STEPS = (4, 8, 12)
# The cut-off: a page is admitted if it holds at least this share of the question's telling
# terms. Challenge: move it and read what gets in.
THRESHOLD = 0.5

OUT.mkdir(parents=True, exist_ok=True)
cfg = load_config()
parts = context.sections()
related, unrelated = pages.load("related"), pages.load("unrelated")
questions = baseline.questions()
evidence_ids = [q["id"] for q in questions if q["slice"] == "evidence"]
plan = Budget(window=cfg["generation"]["num_ctx"], reserve=400)


def fits(ps) -> int:
    """Chapter 03's check, with room for the second statement the harness adds."""
    spent = budget.spend(baseline.with_evidence(ps))
    return budget.check(spent, plan)


def run(ps, name: str, only=None, per_question=None) -> list[dict]:
    fits(ps)
    results = baseline.score(ps, chat=chat, only=only, per_question=per_question)
    (OUT / f"{name}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def passed(results) -> int:
    return sum(r["passed"] for r in results)


step("1. Twenty-four true pages")
evidence(related[2].path, related[2].text.strip())
evidence(unrelated[0].path, unrelated[0].text.strip())
rel_tokens = sum(context.count_tokens(p.text) for p in related)
unrel_tokens = sum(context.count_tokens(p.text) for p in unrelated)
note(f"{len(related)} pages about Pellmar, {rel_tokens:,} tokens. {len(unrelated)} pages about "
     f"two suppliers the inquiry closed in April, {unrel_tokens:,} tokens. None answers any of "
     "the signed questions and none says anything false. Several carry a figure, a date or a "
     "reference that looks like one in the statements.")

step("2. Add the related pages, four at a time")
base = baseline.reference(chat=chat)
base_ev = [r for r in base if r["id"] in evidence_ids]
p_first = learn.predict(
    f"The {len(evidence_ids)} questions whose answers are in the statements all pass today. "
    "Related pages are added 4, 8, then 12 at a time. When does the first answer go wrong?",
    ["With 4 pages", "With 8 pages", "With 12 pages", "Never: all still pass"])
ladder = {0: base_ev}
for k in STEPS:
    ladder[k] = run(pages.with_pages(parts, related[:k]), f"related-{k}", only=evidence_ids)
table = Table(title="The evidence slice, with pages about Pellmar added")
for col in ("pages added", "tokens added", "spare in the budget", "passed", "now wrong"):
    table.add_column(col, justify="right" if col != "now wrong" else "left")
for k, rs in ladder.items():
    added = pages.with_pages(parts, related[:k])
    wrong = [r["id"] for r in rs if not r["passed"]]
    table.add_row(str(k), f"{sum(context.count_tokens(p.text) for p in related[:k]):,}",
                  f"{fits(added):,}", f"{passed(rs)} of {len(rs)}", ", ".join(wrong) or "none")
console.print(table)
first = next((k for k in STEPS if passed(ladder[k]) < passed(base_ev)), None)
worst_k = min(STEPS, key=lambda k: passed(ladder[k]))
for r in ladder[worst_k]:
    if not r["passed"]:
        note(f"{r['id']} with {worst_k} pages ({', '.join(r['called']) or 'no tool'}): "
             f"{r['answer'][:150]}")
spare = {k: fits(pages.with_pages(parts, related[:k])) for k in ladder}
note("Every request above passed the budget. Nothing was cut and nothing false was added."
     if first else
     "Every answer held. On these questions and this model, twelve related pages were not "
     f"enough to move one. What they spent is room: {spare[0]:,} tokens to spare became "
     f"{spare[12]:,}.")
learn.reveal(p_first, answer=STEPS.index(first) if first else 3,
             why="Related pages are said to distract. Whether they do, on your model and your "
             "questions, is a measurement. Here the statements were direct and exact, and the "
             "pages did not outweigh them.")

step("3. The same weight of unrelated pages")
p_kind = learn.predict(
    "Twelve pages about telephone bills and stationery, about the same number of tokens. "
    "Against twelve pages about Pellmar, how do they do on the same questions?",
    ["Worse: more is always worse", "The same", "Better: unrelated pages distract less"])
unrel = run(pages.with_pages(parts, unrelated), "unrelated-12", only=evidence_ids)
table = Table(title="Twelve pages of each kind")
for col in ("pages added", "tokens", "passed", "now wrong"):
    table.add_column(col)
table.add_row("12 about Pellmar", f"{rel_tokens:,}", f"{passed(ladder[12])} of {len(base_ev)}",
              ", ".join(r["id"] for r in ladder[12] if not r["passed"]) or "none")
table.add_row("12 about two suppliers", f"{unrel_tokens:,}", f"{passed(unrel)} of {len(base_ev)}",
              ", ".join(r["id"] for r in unrel if not r["passed"]) or "none")
console.print(table)
gap = passed(unrel) - passed(ladder[12])
learn.reveal(p_kind, answer=0 if gap < 0 else 1 if gap == 0 else 2,
             why="Length alone is not what costs. What the added text looks like, against "
             "what was asked, is.")

step("4. A cut-off, and a record of what was left out")
pool = [*related, *unrelated]
left_out_log, admitted = {}, {}


def builder(ps, question):
    kept, left = SELECT(pool, question, THRESHOLD)
    admitted[question], left_out_log[question] = [p.path for p in kept], left
    return pages.with_pages(ps, kept)


p_cut = learn.predict(
    f"All 24 pages are offered. The builder admits a page only if it holds at least "
    f"{THRESHOLD:.0%} of the question's telling terms. Over the 26 questions, how many pages "
    "does it admit in all?", ["None", "1 to 10", "11 to 40", "More than 40"])
everything = run(pages.with_pages(parts, related), "all-related")
cut = run(parts, "cut-off", per_question=builder)
(OUT / "left-out.json").write_text(json.dumps(left_out_log, indent=2), encoding="utf-8")
n_admitted = sum(len(v) for v in admitted.values())
table = Table(title="The 26 signed questions, three ways of treating the pages")
for col in ("context", "pages in the window", "passed", "fixed", "broken"):
    table.add_column(col)
d_all, d_cut = baseline.changed(base, everything), baseline.changed(base, cut)
table.add_row("no pages (the baseline)", "0", f"{passed(base)} of {len(base)}", "", "")
table.add_row("every page about Pellmar", "12 on every question",
              f"{passed(everything)} of {len(base)}", ", ".join(d_all["fixed"]) or "none",
              ", ".join(d_all["broken"]) or "none")
table.add_row(f"cut-off at {THRESHOLD:.0%}", f"{n_admitted} over 26 questions",
              f"{passed(cut)} of {len(base)}", ", ".join(d_cut["fixed"]) or "none",
              ", ".join(d_cut["broken"]) or "none")
console.print(table)
with_page = {q: v for q, v in admitted.items() if v}
for q, v in list(with_page.items())[:3]:
    note(f"Admitted for \"{q[:70]}...\": {', '.join(p.split('/', 1)[1] for p in v)}")
note(f"{n_admitted} pages admitted over 26 questions; {sum(len(v) for v in left_out_log.values())}"
     " left out, each with its score in .scratch/07/left-out.json. A page left out is a "
     "decision somebody may have to defend, so the builder writes it down.")
learn.reveal(p_cut, answer=learn.bucket(n_admitted, [0, 10, 40]),
             why="The cut-off decides by what the question asks. Most questions need none of "
             "these pages, and a builder that admits none of them has done its job.")

learn.record(
    related_pages=len(related),
    unrelated_pages=len(unrelated),
    related_tokens=rel_tokens,
    unrelated_tokens=unrel_tokens,
    evidence_asked=len(base_ev),
    evidence_0=passed(base_ev),
    evidence_4=passed(ladder[4]) if 4 in ladder else -1,
    evidence_8=passed(ladder[8]) if 8 in ladder else -1,
    evidence_12=passed(ladder[12]) if 12 in ladder else -1,
    first_wrong_at=first or 0,
    spare_0=spare[0],
    spare_12=spare[12],
    evidence_unrelated_12=passed(unrel),
    baseline_passed=passed(base),
    all_related_passed=passed(everything),
    all_related_fixed=len(d_all["fixed"]),
    all_related_broken=len(d_all["broken"]),
    threshold=THRESHOLD,
    admitted=n_admitted,
    cut_passed=passed(cut),
    cut_fixed=len(d_cut["fixed"]),
    cut_broken=len(d_cut["broken"]),
    mine=MINE is not None,
)

finding(f"""
Twelve true pages about Pellmar were added to the context, {rel_tokens:,} tokens, none of which
answers a signed question. The eight questions answered by the statements went from
{passed(base_ev)} of 8 to {passed(ladder[4])} with four pages, {passed(ladder[8])} with eight and
{passed(ladder[12])} with twelve. Twelve pages about telephone bills and stationery,
{unrel_tokens:,} tokens, left {passed(unrel)} of 8. Over all 26 questions the baseline passes
{passed(base)}; with every page about Pellmar loaded it passes {passed(everything)}; with a
cut-off that admitted {n_admitted} pages over the 26 questions it passes {passed(cut)}, and
every page left out is on record with its score. The pages cost no answers. They cost
{spare[0] - spare[12]:,} of the {spare[0]:,} tokens the budget had to spare.
""")
save_shot("07-less-is-more")
