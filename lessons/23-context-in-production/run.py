"""Chapter 23: context in production. A version on every answer, a change log, a budget alarm,
the audit every night, one session traced, and what a session costs."""

import json
import subprocess
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from lantern import (
    baseline,
    budget,
    case,
    context,
    layout,
    learn,
    llm,
    memory,
    production,
    tracing,
)
from lantern.config import ROOT, load_config
from lantern.llm import chat
from lantern.memory import Entry
from lantern.ui import Table, chapter, console, finding, note, reply, save_shot, step

chapter("23", "Friday 7 August", """
Friday 7 August, 09:00. Professional Standards report at noon.

The context LANTERN is given now has a version, as the index did in case file 04 and the answer
key in case file 03. A change to the standing orders, the memory or the layout makes a new
version, with a name against it. The audit runs every night and its result is on Varma's desk
before she is.

At 12:10 she takes the call standing up. She listens, says "Thank you", and puts the phone down.

"He is cleared."

Within the hour Strand rings to offer, again, to clean up the memory store now that the inquiry
is closing. Varma declines for the second time.

Then she reads this morning's audit. One write overnight, held at the gate. And a delivery note
from headquarters: something is in the loading bay for Monday.
""")

MINE = learn.mine()  # --mine: your context_version() from practice/exercise.py
VERSION = MINE.context_version if MINE else production.context_version
OUT = ROOT / ".scratch" / "23"
NIGHTLY = Path(__file__).with_name("nightly.py")
INQ = production.INQUIRY
REASON = "FIU note of 13 July 09:35 (H. Kobayashi): no clearance issued, no record of Ostrander"
# Challenge: what came in overnight. Add an entry of your own and read the morning's audit.
NIGHT_WRITES = [
    Entry(id="M-17", text="Pellmar Nominees: the HQ review is closed. No further action.",
          kind="fact", inquiry=INQ, author="eow-fin-07", written_at="2026-08-07T01:58:00",
          via="svc-lantern-sync"),
]
# Challenge: a change to the standing orders at 08:45, as (old words, new words).
ORDERS_EDIT: tuple[str, str] | None = None
WARN_AT = 0.8  # Challenge: when the alarm warns, as a share of the input budget
RESERVE = 400  # kept back for the answer, as in chapter 03
SESSION = ("Q-17", "Q-12", "Q-21")
IYER = ("Monday's hand-over goes out at 09:00. May DS Iyer be copied on it? Answer yes or no "
        "first, then give the reason in one sentence.")

OUT.mkdir(parents=True, exist_ok=True)
for old in [*(OUT / "nightly").glob("*"), *(OUT / "nightly-cron").glob("*"),
            *(OUT / n for n in ("changes.jsonl", "answers.jsonl", "trace.jsonl", "alarms.jsonl"))]:
    old.unlink(missing_ok=True)
record = case.read("personnel/iyer.md")
account, events = memory.personnel(record)
suspended = next(at for at, what in events if "suspend" in what.lower())
write_log = case.jsonl("state/memory-write-log.jsonl")
store = production.build_store(OUT / "memory.db", at="2026-08-04T10:00:00", by="a.varma",
                               reason=REASON, notes=case.read("state/standing-notes.md"),
                               inactive={account: suspended})
changes = production.ChangeLog(OUT / "changes.jsonl")
questions = {q["id"]: q for q in baseline.questions()}


def parts_now(orders: str | None = None) -> list[context.Section]:
    """The context of 7 August: the store's kept memory and notes, rendered with their source;
    the summaries left out until chapter 18's rebuilt ones are signed off."""
    kept = store.visible(INQ)
    mem = [e for e in kept if e.id.startswith("M-")]
    notes = [e for e in kept if e.id.startswith("N-")]
    out = []
    for s in context.sections():
        if s.name.startswith("summary"):
            continue
        if s.name == "case memory":
            s = replace(s, text=f"# Case memory: inquiry {INQ}\n{store.render(mem)}\n")
        elif s.name == "standing notes":
            s = replace(s, text=f"# Standing notes: inquiry {INQ}\n{store.render(notes)}\n")
        elif s.name == "standing orders" and orders:
            s = replace(s, text=orders)
        out.append(s)
    return out


step("1. 06:00: last night's audit")
p_night = learn.predict(
    "Overnight, one write came in under eow-fin-07 through svc-lantern-sync, citing nothing. "
    "What does the morning's audit report?",
    ["It was kept", "It is held, waiting for a person", "Nothing: the audit reads only the "
     "case's write log"])
thursday = production.nightly(store, write_log, record, since="2026-08-05T18:00:00")
production.write_report(thursday, OUT / "nightly", "2026-08-06")
version_before = VERSION(parts_now())
for e in NIGHT_WRITES:
    store.write(replace(e, status="kept", problems=[]))
friday = production.nightly(store, write_log, record, since="2026-08-06T18:00:00",
                            last_hash=thursday["last_hash"])
production.write_report(friday, OUT / "nightly", "2026-08-07")
table = Table(title="Friday 7 August, 06:00: written since Thursday 18:00")
for col in ("entry", "written", "account", "route", "gate", "why"):
    table.add_column(col)
for w in friday["new_writes"]:
    table.add_row(w["entry"], w["at"].replace("T", " ")[:16], w["by"], w["via"], w["status"],
                  "; ".join(w["problems"])[:70])
console.print(table)
# the scheduler's folder starts from Thursday's report, as a real one would; without the
# last hash there is nothing to check the chain against and a missing hash counts as whole
(OUT / "nightly-cron").mkdir(parents=True, exist_ok=True)
(OUT / "nightly-cron" / "last-hash").write_text(thursday["last_hash"] + "\n", encoding="utf-8")
cron = subprocess.run([sys.executable, str(NIGHTLY), "--store", str(OUT / "memory.db"),
                       "--out", str(OUT / "nightly-cron"), "--since", "2026-08-06T18:00:00",
                       "--day", "2026-08-07"], capture_output=True, text=True, cwd=ROOT,
                      timeout=120)
note(f"{friday['entries']} entries; {friday['text_matches']} of {friday['audited']} logged case "
     f"entries still read as written; {len(friday['new_writes'])} written since Thursday "
     f"18:00, {len(friday['held'])} held for a person; the chain "
     f"{'still holds' if friday['chain_continues'] else 'NO LONGER HOLDS'} Thursday's last hash "
     f"({thursday['last_hash'][:12]}, kept outside the store); {len(friday['problems'])} "
     f"problems. The same job as a scheduler runs it (nightly.py) exited {cron.returncode}.")
mine_held = [w for w in friday["held"] if w["entry"] in {e.id for e in NIGHT_WRITES}]
seen = {w["entry"] for w in friday["new_writes"]}
learn.reveal(p_night, answer=2 if not seen else 1 if mine_held else 0,
             why="The gate held it: no source, a machine account, an account closed in May. "
             "The audit found it because it reads the store's own log, not only the case's. A "
             "nightly audit finds what was written last night; it does not stop the writing.")

step("2. The context version")
p_version = learn.predict(
    "The store has one more entry this morning, held at the gate. Is the context version "
    "LANTERN answers under today the one it answered under last night?",
    ["No: the store changed", "Yes: what LANTERN is given did not change"])
orders = case.read("state/standing-orders.md")
v_morning = VERSION(parts_now())
if ORDERS_EDIT:
    old_words, new_words = ORDERS_EDIT
    edited = orders.replace(old_words, new_words)
    if edited == orders:
        raise SystemExit(f"ORDERS_EDIT: {old_words!r} is not in the standing orders")
    orders = edited
    v_edit = VERSION(parts_now(orders))
    changes.add(at="2026-08-07T08:45:00", by="a.varma",
                what=f"standing orders: {old_words!r} to {new_words!r}", reason="ORDERS_EDIT",
                before=v_morning, after=v_edit)
v1 = VERSION(parts_now(orders))
table = Table(title=f"Context version {v1}: what it covers")
for col in ("section", "sent as", "content hash"):
    table.add_column(col)
for name, where, h in production.fingerprints(parts_now(orders)):
    table.add_row(name, where, h)
table.add_row("(layout)", "", " > ".join(s.name for s in parts_now(orders))[:60])
console.print(table)
same_overnight = version_before == v_morning
note(f"Last night {version_before}; this morning {v_morning}"
     + (f"; after the 08:45 edit {v1}" if ORDERS_EDIT else "") + ". The session so far and the "
     "question are not in the version: they are recorded beside it.")
learn.reveal(p_version, answer=1 if same_overnight else 0,
             why="The version covers what LANTERN is given, and a held entry is not given. "
             "The store's log changed; the context did not. An answer without its version "
             "cannot be reproduced, so the version is part of the finding.")

step("3. 09:00: one session, traced, every answer with its version")
tracing.enable(OUT / "trace.jsonl")
before = llm.USAGE.summary()
answers = []


def ask(parts, qid: str, text: str, version: str, at: str):
    with tracing.span("answer", **{"lantern.context_version": version, "lantern.question": qid}):
        messages, schemas = context.request(baseline.asking(baseline.with_evidence(parts), text))
        got = baseline.answer(messages, schemas, chat=chat, seed=7, max_tokens=160)
    row = {"at": at, "question": qid, "version": version, "answer": got["answer"],
           "passed": baseline.grade(got["answer"], questions[qid]["expect"])
           if qid in questions else None}
    answers.append(row)
    with (OUT / "answers.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return row


with tracing.span("session lantern", **{"gen_ai.operation.name": "invoke_agent",
                                        "lantern.context_version": v1}):
    parts = parts_now(orders)
    for n, qid in enumerate(SESSION):
        ask(parts, qid, questions[qid]["question"], v1, f"2026-08-07T09:{n * 5:02d}:00")
    iyer_before = ask(parts, "iyer", IYER, v1, "2026-08-07T09:20:00")
table = Table(title="answers.jsonl: every answer with the context it was given")
for col in ("at", "question", "version", "passed", "answer"):
    table.add_column(col)
for a in answers:
    table.add_row(a["at"][11:16], a["question"], a["version"],
                  "" if a["passed"] is None else "yes" if a["passed"] else "no",
                  a["answer"].replace("\n", " ")[:60])
console.print(table)

step("4. 12:10: DS Iyer is cleared")
p_iyer = learn.predict(
    "Varma forgets the standing note that names Iyer as suspended: its text is erased, the "
    "record that it existed stays. Asked the same question, does LANTERN still say he is "
    "suspended?", ["Yes", "No"])
note_id = next(e.id for e in store.visible(INQ) if "Iyer" in e.text)
store.forget(note_id, by="a.varma", at="2026-08-07T12:10:00",
             reason="DS Iyer cleared by Professional Standards, Friday 7 August 2026")
v2 = VERSION(parts_now(orders))
changes.add(at="2026-08-07T12:10:00", by="a.varma",
            what=f"memory: {note_id} forgotten (the standing note on DS Iyer)",
            reason="cleared by Professional Standards at noon", before=v1, after=v2)
with tracing.span("session lantern", **{"gen_ai.operation.name": "invoke_agent",
                                        "lantern.context_version": v2}):
    iyer_after = ask(parts_now(orders), "iyer", IYER, v2, "2026-08-07T12:15:00")
tracing_file = OUT / "trace.jsonl"
reply(f"Before, under {v1}", iyer_before["answer"])
reply(f"After, under {v2}", iyer_after["answer"])
said_before = "suspend" in iyer_before["answer"].lower()
said_after = "suspend" in iyer_after["answer"].lower()
log_rows = changes.entries()
table = Table(title="changes.jsonl: the change log")
for col in ("at", "by", "what", "before", "after"):
    table.add_column(col)
for c in log_rows:
    table.add_row(c["at"][11:16], c["by"], c["what"][:52], c["before"], c["after"])
console.print(table)
chain = changes.verify()
note(f"\"suspended\" in the answer: {'yes' if said_before else 'no'} before, "
     f"{'yes' if said_after else 'no'} after. {note_id}: {store.get(note_id).status}, text "
     f"{store.get(note_id).text!r}; the store's chain: "
     f"{'; '.join(store.verify()) or 'no problems'}; the change log's: "
     f"{'; '.join(chain) or 'no problems'}.")
learn.reveal(p_iyer, answer=0 if said_after else 1,
             why="What LANTERN says about a person is what its context says. The version "
             "changed with the note, and the log says who changed it, when and why.")

step("5. The budget alarm")
spans = [json.loads(x) for x in tracing_file.read_text(encoding="utf-8").splitlines() if x]
cfg = load_config()
plan = budget.Budget(window=cfg["generation"]["num_ctx"], reserve=RESERVE)
# the request as sent: the reserve statement with_evidence adds, and the question
spent = budget.spend(baseline.asking(baseline.with_evidence(parts_now(orders)), IYER))
level = production.alarm(spent, plan, warn_at=WARN_AT)
turn_tokens = [context.count_tokens(f"user: {questions[a['question']]['question']}\n"
                                    f"assistant: {a['answer']}\n")
               for a in answers if a["question"] in questions]
per_turn = round(sum(turn_tokens) / len(turn_tokens)) if turn_tokens else 1
p_turns = learn.predict_number(
    f"A session on this context adds about {per_turn} tokens a question and answer. How many "
    f"more before the alarm warns at {WARN_AT:.0%} of the input budget?", unit="turns")
more = production.turns_until(level.total, per_turn, plan, warn_at=WARN_AT)
table = Table(title=f"Tokens by account, against {plan.for_input:,} for input "
              f"({plan.window:,} window, {plan.reserve} kept for the answer)")
for col in ("account", "tokens"):
    table.add_column(col)
for k, v in spent.items():
    table.add_row(k, f"{v:,}")
console.print(table)
with (OUT / "alarms.jsonl").open("a", encoding="utf-8") as f:
    f.write(json.dumps({"at": "2026-08-07T12:15:00", "version": v2, "level": level.level,
                        "message": level.message, "turns_left": more}) + "\n")
note(f"Alarm: {level.message}. At about {per_turn} tokens a turn it warns after {more} more "
     "turns. It is written to alarms.jsonl beside the answers; an alarm nobody reads is not a "
     "control.")
learn.reveal(p_turns, actual=more, tolerance=0.3,
             why="The fixed part of the context is most of the window before the first "
             "question. The alarm is there so a long session is stopped with a reason, not cut "
             "by the server without one (chapter 03).")

step("6. What a session costs, and the trace")
after = llm.USAGE.summary()
calls = after["calls"] - before["calls"]
prompt = after["prompt_tokens"] - before["prompt_tokens"]
output = after["output_tokens"] - before["output_tokens"]
seconds = round(after["latency_s"] - before["latency_s"], 1)
prices = cfg["hosted"]["prices"]
stable = sum(v for k, v in spent.items() if k in ("standing orders", "case memory",
                                                  "standing notes", "tool schemas"))
uncached = (prompt * prices["input"] + output * prices["output"]) / 1e6
# a cache write for the first request, for every change of version, and after every gap
# longer than the cache lives; the session's requests are the answers, in order
ttl_s = {"5m": 300, "1h": 3600}[cfg["hosted"]["features"]["ttl"]]
stamps = [(datetime.fromisoformat(a["at"]), a["version"]) for a in answers]
writes = 1 + sum(v != pv or (t - pt).total_seconds() > ttl_s
                 for (pt, pv), (t, v) in zip(stamps, stamps[1:], strict=False))
cached = layout.session_cost(stable=stable, tail=max(0, round(prompt / max(calls, 1)) - stable),
                             output=round(output / max(calls, 1)), questions=calls, writes=writes,
                             prices=prices, ttl=cfg["hosted"]["features"]["ttl"]) if calls else 0.0
local_cost = (after["cost_usd"] or 0.0) - (before["cost_usd"] or 0.0)
table = Table(title="One session: measured on qwen3:8b, and priced for "
              f"{cfg['hosted']['model']} as a calculation, not a bill")
for col in ("", "requests", "prompt tokens", "output tokens", "seconds", "US dollars"):
    table.add_column(col)
table.add_row(f"local, {cfg['models']['default']} (measured)", str(calls),
              f"{prompt:,}", f"{output:,}", str(seconds), f"{local_cost:.4f}")
table.add_row("hosted price, no cache (calculated)", str(calls), f"{prompt:,}", f"{output:,}",
              "", f"{uncached:.4f}")
table.add_row(f"hosted price, {stable:,}-token prefix cached, {writes} cache writes "
              "(calculated)", str(calls),
              f"{prompt:,}", f"{output:,}", "", f"{cached:.4f}")
console.print(table)
chat_spans = [s for s in spans if s["name"].startswith("chat ")]
span_in = sum(s["attributes"].get("gen_ai.usage.input_tokens", 0) for s in chat_spans)
versions_on_spans = sorted({s["attributes"]["lantern.context_version"] for s in spans
                            if "lantern.context_version" in s["attributes"]})
note(f"Trace: {len(spans)} spans in .scratch/23/trace.jsonl ({len(chat_spans)} model calls, "
     f"{sum(s['name'] == 'answer' for s in spans)} answers, "
     f"{sum(s['name'] == 'session lantern' for s in spans)} sessions), OpenTelemetry GenAI "
     f"attributes; input tokens on the chat spans: {span_in:,}, against {prompt:,} in "
     f"llm.USAGE. Versions on the spans: {', '.join(versions_on_spans)}. Prices from "
     f"config.yaml, checked {cfg['hosted']['prices_checked']}.")

learn.record(
    versions=len({version_before, v_morning, v1, v2}),
    version_morning=v_morning,
    version_after=v2,
    held_write_changes_version=not same_overnight,
    orders_edited=ORDERS_EDIT is not None,
    changelog_entries=len(log_rows),
    changelog_problems=len(chain),
    answers_recorded=len(answers),
    answers_with_version=sum(bool(a["version"]) for a in answers),
    session_passed=sum(bool(a["passed"]) for a in answers if a["passed"] is not None),
    session_asked=sum(a["passed"] is not None for a in answers),
    iyer_suspended_before=said_before,
    iyer_suspended_after=said_after,
    forgotten_text_empty=store.get(note_id).text == "",
    night_writes=len(NIGHT_WRITES),
    nightly_new_writes=len(friday["new_writes"]),
    nightly_held=len(friday["held"]),
    nightly_problems=len(friday["problems"]),
    nightly_chain_continues=friday["chain_continues"],
    nightly_exit=cron.returncode,
    cache_writes=writes,
    alarm_level=level.level,
    alarm_warns=level.level != "ok",
    alarm_share_pct=round(level.share * 100),
    warn_at_pct=round(WARN_AT * 100),
    turns_until_alarm=more,
    tokens_per_turn=per_turn,
    spans=len(spans),
    chat_spans=len(chat_spans),
    span_input_tokens=span_in,
    session_requests=calls,
    session_prompt_tokens=prompt,
    session_output_tokens=output,
    session_seconds=seconds,
    local_cost_usd=round(local_cost, 6),
    hosted_uncached_usd=round(uncached, 6),
    hosted_cached_usd=round(cached, 6),
    mine=MINE is not None,
)

said_now = ("still says suspended" if said_after else "no longer says suspended"
            if said_before else "did not say suspended before or after")
finding(f"""
Every answer this morning is recorded with its context version: {len(answers)} answers under
{', '.join(dict.fromkeys(a['version'] for a in answers))}. Overnight
{len(friday['new_writes'])} write came in through svc-lantern-sync; the gate held
{len(friday['held'])}, the nightly audit reported it at 06:00, and the version did
{'not ' if same_overnight else ''}change, because a held entry is not given to LANTERN. At 12:10
DS Iyer was cleared; the note naming him was forgotten under a change log entry by a.varma,
and LANTERN's answer about him {said_now}.
The context uses {level.share:.0%} of its input budget, and the alarm warns after {more} more
turns. One session took {calls} requests and {prompt:,} prompt tokens on qwen3:8b; priced for
the hosted model, a calculation and not a bill, it is ${uncached:.4f} uncached and
${cached:.4f} with the prefix cached. The account that wrote the false memories is a machine
account that belongs to headquarters, and the delivery note says that same sync brings a new
LANTERN workstation and model bundle on Monday.
""")
save_shot("23-context-in-production")
