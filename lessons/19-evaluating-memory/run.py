"""Chapter 19: evaluating memory. A suite that recalls, ignores, abstains and catches a plant."""

import json
from datetime import datetime

from suite import CASES, old_memory, rebuilt_store
from suite import run as run_suite

from lantern import learn, memory
from lantern.config import ROOT
from lantern.llm import chat, model_name
from lantern.ui import Table, chapter, console, finding, note, reply, save_shot, step

chapter("19", "The memory suite", """
Wednesday 5 August, 09:30. The store has provenance, a gate and a retraction. Varma wants to
know whether any of it holds tomorrow.

"The answer key was altered in May and we found it by its hash. The memory was altered in June
and we found it when the money had gone." She puts the two dates side by side. "I want the
second kind found like the first."

Okafor writes three headings. Recalls what it was told. Ignores what was retracted. Says so
when it was never told.

"And a fourth," Varma says. "Somebody plants a line. Does anything notice before LANTERN acts
on it?"
""")

MINE = learn.mine()  # --mine: your denies() from practice/exercise.py
DENIES = MINE.denies if MINE else memory.denies
OUT = ROOT / ".scratch" / "19"
GATE_FILE = ROOT / "lessons" / "19-evaluating-memory" / "memory-gate.json"
KINDS = ("recall", "retraction", "not told", "planted")

OUT.mkdir(parents=True, exist_ok=True)


def table_of(runs: dict[str, list[dict]]) -> None:
    t = Table(title="The memory suite: passed, by kind of case")
    t.add_column("kind")
    for name in runs:
        t.add_column(name, justify="right")
    for k in KINDS:
        n = sum(c["kind"] == k for c in CASES)
        t.add_row(k, *(f"{sum(r['passed'] for r in rs if r['kind'] == k)} of {n}"
                       for rs in runs.values()))
    t.add_row("all", *(f"{sum(r['passed'] for r in rs)} of {len(rs)}" for rs in runs.values()))
    console.print(t)


step("1. The suite, and the graders that check it")
note(f"{len(CASES)} cases: " + ", ".join(f"{sum(c['kind'] == k for c in CASES)} {k}"
                                          for k in KINDS) + ". Graders in code: names, whole "
     "figures, the cited entry id, a denial that is not fooled by \"not cleared\", and "
     "abstention in several phrasings. Each has its own tests that try to fool it "
     "(tests/test_memory.py).")
store = rebuilt_store()
planted = store.get("M-17")
note(f"The planted line, written through svc-lantern-sync at 01:58 on 5 August: "
     f"\"{planted.text}\" The gate: {planted.status}, {'; '.join(planted.problems)}.")

step("2. The memory of 13 July")
p_old = learn.predict_number(
    "On the memory as it was on 13 July, every entry loaded and the planted line among them, "
    "how many of the 4 retraction cases does LANTERN pass?", unit="of 4")
old = run_suite(old_memory(), chat=chat, denies=DENIES)
learn.reveal(p_old, actual=sum(r["passed"] for r in old if r["kind"] == "retraction"),
             tolerance=0.0, why="The memory says Pellmar is cleared, Ostrander licensed, "
             "Tidewater routine, the client money ordinary. A suite that never fails on the old "
             "memory has not been shown to detect anything.")

step("3. The store as it is now")
p_plant = learn.predict(
    "On the rebuilt store, the planted Greyfen line was held by the gate. Is it loaded, and "
    "does LANTERN say Greyfen is cleared?", ["Loaded, and it says cleared",
                                             "Not loaded; it does not say cleared",
                                             "Not loaded, and it says cleared anyway"])
new = run_suite(store, chat=chat, denies=DENIES)
p1 = next(r for r in new if r["id"] == "P-1")
learn.reveal(p_plant, answer=0 if "M-17" in p1["loaded"] else 1 if p1["passed"] else 2,
             why="A held entry is never read. The suite checks what the store and the context "
             "builder do together: the gate kept the line out of every session.")

step("4. The same store with its gate taken away")
p_gate = learn.predict(
    "Somebody \"cleans up\" the store so that nothing is held, and the planted line is kept. "
    "Does the memory gate notice?", ["Yes, it fails", "No, it passes"])
open_store = rebuilt_store(policy=lambda e, s: [])
regressed = run_suite(open_store, chat=chat, denies=DENIES)
runs = {"13 July": old, "rebuilt": new, "gate taken away": regressed}
table_of(runs)
t = Table(title="Case by case")
for col in ("case", "kind", *runs):
    t.add_column(col)
for i, c in enumerate(CASES):
    t.add_row(c["id"], c["kind"], *("pass" if rs[i]["passed"] else
                                    "fail: " + ", ".join(k for k, v in rs[i].items()
                                                         if v is False)
                                    for rs in runs.values()))
console.print(t)
caught = [r["id"] for r, n in zip(new, regressed, strict=True) if r["passed"] and not n["passed"]]
learn.reveal(p_gate, answer=0 if caught else 1,
             why=f"The gate compares every case with the verdict recorded for the rebuilt store. "
             f"Cases that passed then and fail now: {', '.join(caught) or 'none'}.")
reply("P-1 with the gate taken away", next(r for r in regressed if r["id"] == "P-1")["answer"])

step("5. A weaker grader on the same answers")
disagree = []
for rs in runs.values():
    for r, c in zip(rs, CASES, strict=True):
        if "denies" in c:
            says_word = c["denies"] in r["answer"].lower()
            if (not says_word) != r["denies"]:
                disagree.append(f"{c['id']}: {r['answer'][:90]}")
note(f"A grader that fails any answer containing the word would disagree with the negation "
     f"grader on {len(disagree)} of {sum('denies' in c for c in CASES) * len(runs)} graded "
     f"answers" + (": " + " | ".join(disagree[:3]) if disagree else "."))

GATE_FILE.write_text(json.dumps({
    "recorded": datetime.now().isoformat(timespec="seconds"), "model": model_name(None),
    "cases": {r["id"]: r["passed"] for r in new}}, indent=2) + "\n", encoding="utf-8")
(OUT / "suite.json").write_text(json.dumps(runs, indent=2), encoding="utf-8")
note("Recorded the rebuilt store's verdicts in lessons/19-evaluating-memory/memory-gate.json. "
     "`make memory-gate` runs the suite again and fails on any case that passed here.")


def passed(rs, kind=None):
    return sum(r["passed"] for r in rs if kind is None or r["kind"] == kind)


learn.record(
    cases=len(CASES),
    old_passed=passed(old),
    old_recall=passed(old, "recall"),
    old_retraction=passed(old, "retraction"),
    old_not_told=passed(old, "not told"),
    old_planted=passed(old, "planted"),
    new_passed=passed(new),
    new_recall=passed(new, "recall"),
    new_retraction=passed(new, "retraction"),
    new_not_told=passed(new, "not told"),
    new_planted=passed(new, "planted"),
    open_passed=passed(regressed),
    open_planted=passed(regressed, "planted"),
    gate_caught=len(caught),
    planted_held=planted.status == "held",
    naive_disagrees=len(disagree),
    mine=MINE is not None,
)

finding(f"""
The suite has {len(CASES)} cases and graders in code that check names, whole figures, the
cited entry, denials and abstention. On the memory of 13 July it passed {passed(old)} of
{len(CASES)}: {passed(old, 'retraction')} of 4 retraction cases and
{passed(old, 'planted')} of 1 planted. On the rebuilt store it passed {passed(new)}:
{passed(new, 'recall')} of 6 recall, {passed(new, 'retraction')} of 4 retraction,
{passed(new, 'not told')} of 3 not told, {passed(new, 'planted')} of 1 planted. With the
gate taken away the planted line was loaded and the suite caught {len(caught)} regressions:
{', '.join(caught) or 'none'}. The memory now has a gate of its own.
""")
save_shot("19-evaluating-memory")
