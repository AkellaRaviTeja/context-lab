"""Chapter 16: layout for the cache. What a change costs depends on where it is."""

import json
import os
import statistics
import subprocess
import time
from dataclasses import replace

from lantern import baseline, context, layout, learn
from lantern.config import ROOT, load_config
from lantern.context import SYSTEM, Section
from lantern.llm import chat
from lantern.ui import Table, chapter, console, evidence, finding, note, save_shot, step

chapter("16", "The same beginning", """
Friday 31 July, 08:45. Varma's first question each morning takes the best part of a minute to
begin answering. The second, straight after, starts almost at once.

"Why is it slow only when I arrive?"

Case file 02 chapter 20 found one cause: a timestamp in the system prompt, new every request,
so that nothing after it could be reused.

The cause this morning is the nightly sync. At 01:58 it rewrites the case memory, the second
thing LANTERN reads.

"So every morning it reads everything again from the top," Okafor says.

"From the first thing that changed," you say.
""")

MINE = learn.mine()  # --mine: your layout() from practice/exercise.py
LAYOUT = MINE.layout if MINE else layout.layout
OUT = ROOT / ".scratch" / "16"
OUT.mkdir(parents=True, exist_ok=True)
REPEATS = 3  # every timing is taken this many times; the machine is shared
SESSION = 10  # questions in the priced session of step 5
cfg = load_config()
prices = cfg["hosted"]["prices"]


def others() -> int:
    """Other lessons running on this machine now, from any lab: they share the model server."""
    try:
        out = subprocess.run(["pgrep", "-f", r"lessons/[0-9][0-9]-.*/run\.py"],
                             capture_output=True, text=True, timeout=5).stdout.split()
    except (OSError, subprocess.SubprocessError):
        return -1
    return len([p for p in out if int(p) not in (os.getpid(), os.getppid())])


def send(parts, ordered=None):
    """One request that reads the prompt and writes one token: the time is the reading."""
    messages, schemas = layout.request(ordered if ordered is not None else parts)
    r = chat(messages, tools=schemas, seed=7, max_tokens=1)
    return {"seconds": round(r.prompt_seconds, 2), "tokens": r.prompt_tokens}


def stamped(parts, stamp):
    return [Section("session stamp", SYSTEM, f"Session opened {stamp}.\n"), *parts]


def changed_line(parts, name, old, new):
    out = []
    for s in parts:
        if s.name == name:
            if old not in s.text:
                raise ValueError(f"{old!r} is not in {name}")
            s = replace(s, text=s.text.replace(old, new, 1))
        out.append(s)
    return out


def before(parts, name):
    """Tokens of text before the start of a section, counted on the text."""
    i = [s.name for s in parts].index(name)
    return context.count_tokens(context.flat(parts[:i])) if i else 0


busy_start = others()
questions = baseline.questions()
base = context.sections()
names = [s.name for s in base]
sizes = {s.name: context.count_tokens(s.text) for s in base}
total = sum(sizes.values())
MIDDLE = "summary week-2026-06-29"
middle_at = before(base, MIDDLE)
other_q = questions[5]["question"]

step("1. The same request, and a change at the start, the middle and the end")
evidence("what is sent, in order (tokens as qwen3 counts the text)",
         "\n".join(f"{n:<26}{sizes[n]:>6,}" for n in names) + f"\n{'all':<26}{total:>6,}")
p_count = learn.predict(
    "The same request is sent twice. What does Ollama report as the second request's prompt "
    "token count?", ["The same count as the first", "Only the tokens it had to read again",
                     "Zero"])
p_mid = learn.predict(
    f"A line {middle_at:,} tokens into a {total:,}-token context is changed. How long does "
    "reading the prompt take, against reading it the first time?",
    ["About the same", "Roughly the share after the change", "Almost nothing"])
rows: dict[str, list[dict]] = {k: [] for k in ("first time", "the same again", "end changed",
                                                "middle changed", "start changed")}
for rep in range(REPEATS):
    stamp = f"Friday 31 July 2026 08:45:{rep:02d}.{time.time_ns() % 10**6:06d}"
    first = stamped(base, stamp)
    rows["first time"].append(send(first))
    rows["the same again"].append(send(first))
    rows["end changed"].append(send(baseline.asking(first, other_q)))
    send(first)
    rows["middle changed"].append(send(changed_line(first, MIDDLE, "\n", " (rewritten)\n")))
    send(first)
    rows["start changed"].append(send(stamped(base, stamp + " again")))
where = {"first time": "nothing read before", "the same again": "none",
         "end changed": f"the question, after {total - sizes['the question']:,}",
         "middle changed": f"after {middle_at:,}", "start changed": "the first line"}
table = Table(title=f"Reading the prompt, qwen3:8b on local Ollama, {REPEATS} times each")
for col in ("request", "change", "prompt tokens", *[f"seconds, run {i + 1}"
                                                    for i in range(REPEATS)], "median"):
    table.add_column(col, justify="left" if col in ("request", "change") else "right")
med = {}
for k, rs in rows.items():
    med[k] = statistics.median(r["seconds"] for r in rs)
    table.add_row(k, where[k], f"{rs[0]['tokens']:,}", *[f"{r['seconds']:.2f}" for r in rs],
                  f"{med[k]:.2f}")
console.print(table)
# the same prompt twice: the second request reuses everything, so compare those two counts
same_count = all(a["tokens"] == b["tokens"]
                 for a, b in zip(rows["first time"], rows["the same again"], strict=True))
note(f"The first time, {med['first time']:.2f} s. The same again, {med['the same again']:.2f} s. "
     f"Prompt tokens reported for the same prompt twice were equal: {same_count}.")
learn.reveal(p_count, answer=0 if same_count else 1,
             why="Ollama reports the whole prompt in prompt_eval_count whatever it reused. The "
             "saving shows only in the time, prompt_eval_duration.")
ratio_mid = med["middle changed"] / max(med["first time"], 1e-9)
learn.reveal(p_mid, answer=0 if ratio_mid > 0.85 else (2 if ratio_mid < 0.15 else 1),
             why=f"The server reuses the prompt up to the first token that differs and reads "
             f"the rest again. {1 - middle_at / total:.0%} of this prompt is after the change; "
             f"reading took {ratio_mid:.0%} of the first time.")

step("2. The morning after the sync")
SYNC_OLD = "# LANTERN case memory: inquiry EOW/2026/0412\n"
changes = {s.name: layout.how_often(s.name) for s in base}
p_save = learn.predict_number(
    "Put what changes least first: standing orders and tool schemas, then the weekly "
    "summaries and notes, then the case memory, then the session and the question. What share "
    "of the morning's first-question reading time does that save?", unit="%")
morning = {"today's order": [], "stable first": []}
yesterday = baseline.asking(base, questions[0]["question"])
for rep in range(REPEATS):
    # a new rewrite each morning, so no run finds the last run's rewritten memory still held
    sync_new = SYNC_OLD + f"Rewritten by the nightly sync, 31 July 2026 01:58 (run {rep + 1}, " \
        f"{time.time_ns() % 10**6:06d}).\n"
    overnight = changed_line(base, "case memory", SYNC_OLD, sync_new)
    for name in morning:
        def order(parts, name=name):
            return parts if name == "today's order" else LAYOUT(parts, changes)[0]
        send(yesterday, order(yesterday))
        q1 = baseline.asking(overnight, questions[1]["question"])
        q2 = baseline.asking(overnight, questions[2]["question"])
        morning[name].append({"first": send(q1, order(q1)), "second": send(q2, order(q2))})
ordered, ends = LAYOUT(base, changes)
reread = {"today's order": total - before(base, "case memory"),
          "stable first": total - before(ordered, "case memory")}
table = Table(title="The morning after the sync: reading the prompt, seconds")
for col in ("layout", "tokens from the change on", *[f"first question, run {i + 1}"
                                                     for i in range(REPEATS)],
            "first, median", "second, median"):
    table.add_column(col, justify="left" if col == "layout" else "right")
mm = {}
for name, rs in morning.items():
    mm[name] = (statistics.median(r["first"]["seconds"] for r in rs),
                statistics.median(r["second"]["seconds"] for r in rs))
    table.add_row(name, f"{reread[name]:,}", *[f"{r['first']['seconds']:.2f}" for r in rs],
                  f"{mm[name][0]:.2f}", f"{mm[name][1]:.2f}")
console.print(table)
saved = 100 * (1 - mm["stable first"][0] / max(mm["today's order"][0], 1e-9))
note("Stable first: " + ", ".join(f"{s.name} ({layout.how_often(s.name)})" for s in ordered)
     + f". The cache breaks at indexes {ends}.")
learn.reveal(p_save, actual=round(saved), tolerance=0.3,
             why="Today the memory is second, so the sync's change makes the server read the "
             "notes, the summaries and all 19 tool schemas again. Stable first, the change is "
             "near the end and only what follows it is read again.")

step("3. Does the order change the answers?")
p_score = learn.predict(
    "The case memory now travels as a user turn after the tools, not inside the system "
    "message. Asked the 26 signed questions, does LANTERN score differently from chapter 02's "
    "baseline of 17?", ["The same score, the same answers", "The same score, different answers",
                        "A different score"])
ref = baseline.reference(chat=chat)
parts = baseline.with_evidence(base)
results, seconds, outs = [], 0.0, []


def counted(*args, **kwargs):
    r = chat(*args, **kwargs)
    outs.append(r.output_tokens)
    return r


for q in questions:
    asked = baseline.asking(parts, q["question"])
    messages, schemas = layout.request(LAYOUT(asked, changes)[0])
    t0 = time.perf_counter()
    got = baseline.answer(messages, schemas, chat=counted, seed=baseline.SEED,
                          max_tokens=160)
    seconds += time.perf_counter() - t0
    results.append({"id": q["id"], "slice": q["slice"], "question": q["question"], **got,
                    "passed": baseline.grade(got["answer"], q["expect"])})
(OUT / "stable-first.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
diff = baseline.changed(ref, results)
passed, was = sum(r["passed"] for r in results), sum(r["passed"] for r in ref)
same_answers = sum(a["answer"] == b["answer"] for a, b in zip(ref, results, strict=True))
note(f"Stable first: {passed} of 26, against {was} of 26. Fixed: {diff['fixed'] or 'none'}. "
     f"Broken: {diff['broken'] or 'none'}. {same_answers} of 26 answers word for word the "
     f"same. The 26 questions took {seconds:.0f} s.")
learn.reveal(p_score, answer=2 if passed != was else (0 if same_answers == 26 else 1),
             why="Moving a section changes what the model reads next to what. Chapter 06 "
             "measured that place matters; a layout for the cache has to be scored like any "
             "other change to the context.")

step("4. On a hosted model: breakpoints and a price calculation")
kw = layout.hosted_request(ordered, ends, model=cfg["hosted"]["model"], max_tokens=160)
stable = sum(sizes[s.name] for s in ordered[:ends[-2] + 1])
tail = total - stable
out_tokens = round(sum(outs) / len(questions))
table = Table(title=f"A session of {SESSION} questions on {cfg['hosted']['model']}: a price "
              "calculation from these token counts, not a bill")
for col in ("questions arrive", "no cache", "cache, 5 minutes", "cache, 1 hour"):
    table.add_column(col, justify="left" if col == "questions arrive" else "right")
costs = {}
for label, writes_5m in (("within 5 minutes of each other", 1),
                         ("20 minutes apart", SESSION)):
    row = [layout.session_cost(stable=stable, tail=tail, output=out_tokens, questions=SESSION,
                               writes=0, prices=prices, cached=False),
           layout.session_cost(stable=stable, tail=tail, output=out_tokens, questions=SESSION,
                               writes=writes_5m, prices=prices, ttl="5m"),
           layout.session_cost(stable=stable, tail=tail, output=out_tokens, questions=SESSION,
                               writes=1, prices=prices, ttl="1h")]
    costs[label] = row
    table.add_row(label, *[f"${c:.4f}" for c in row])
console.print(table)
note(f"The request carries {layout.breakpoints_in(kw)} cache breakpoints, one at the end of "
     f"each group but the question. Cached prefix: everything up to the case memory, "
     f"{stable:,} tokens; after it, {tail:,}; {out_tokens} tokens out a question, as step 3 "
     "measured. Prices per "
     f"million tokens from config.yaml, checked {cfg['hosted']['prices_checked']}. Not run on "
     "the hosted model: no key.")
busy_end = others()

learn.record(
    context_tokens=total,
    middle_at=middle_at,
    repeats=REPEATS,
    first_s=med["first time"],
    same_s=med["the same again"],
    end_s=med["end changed"],
    middle_s=med["middle changed"],
    start_s=med["start changed"],
    same_count_reported=same_count,
    today_first_s=mm["today's order"][0],
    today_second_s=mm["today's order"][1],
    stable_first_s=mm["stable first"][0],
    stable_second_s=mm["stable first"][1],
    today_reread_tokens=reread["today's order"],
    stable_reread_tokens=reread["stable first"],
    morning_saved_pct=round(saved),
    breakpoints=layout.breakpoints_in(kw),
    stable_passed=passed,
    baseline_passed=was,
    fixed=len(diff["fixed"]),
    broken=len(diff["broken"]),
    same_answers=same_answers,
    cached_prefix_tokens=stable,
    session_no_cache_usd=round(costs["within 5 minutes of each other"][0], 6),
    session_5m_close_usd=round(costs["within 5 minutes of each other"][1], 6),
    session_5m_apart_usd=round(costs["20 minutes apart"][1], 6),
    session_1h_apart_usd=round(costs["20 minutes apart"][2], 6),
    other_runs_start=busy_start,
    other_runs_end=busy_end,
    mine=MINE is not None,
)

finding(f"""
On qwen3:8b on local Ollama, reading this {total:,}-token context took {med['first time']:.2f} s
the first time and {med['the same again']:.2f} s the same again (medians of {REPEATS}). A change
at the end cost {med['end changed']:.2f} s, in the middle {med['middle changed']:.2f} s, at the
start {med['start changed']:.2f} s: the server reads again from the first thing that changed,
and reports the same token count either way. On the morning after the sync, today's order made
the first question read {reread["today's order"]:,} tokens again
({mm["today's order"][0]:.2f} s); with what changes least first it was
{reread['stable first']:,} ({mm['stable first'][0]:.2f} s), {saved:.0f}% less time. The new
order scored {passed} of 26 against {was}, with {len(diff['fixed'])} fixed and
{len(diff['broken'])} broken. On the hosted model the same layout carries
{layout.breakpoints_in(kw)} cache breakpoints; its price is calculated here, not measured.
""")
save_shot("16-layout-for-the-cache")
