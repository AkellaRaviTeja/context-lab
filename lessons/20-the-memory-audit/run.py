"""Chapter 20: the memory audit. Every entry joined to its source, its account and its route."""

import json
import re
from collections import Counter

from lantern import case, learn, memory
from lantern.config import ROOT
from lantern.llm import chat
from lantern.ui import Table, chapter, console, finding, note, reply, save_shot, step

chapter("20", "Every entry", """
Thursday 6 August, 08:30. Professional Standards report tomorrow. DS Iyer has been at home
since May, his badge in a drawer at headquarters.

The audit runs over every write the memory store has ever taken. Most trace to a statement, a
ruling, a signed file.

A set do not. Okafor lays them out by date, and then lays Iyer's suspension beside them.

"These were written under his account."

"After he surrendered his badge," Varma says. "Every one of them."

She does not say what that means. She asks for the session records behind each write: the
machine it came from, and the account that opened the connection.
""")

MINE = learn.mine()  # --mine: your audit() from practice/exercise.py
AUDIT = MINE.audit if MINE else memory.audit
OUT = ROOT / ".scratch" / "20"
# Challenge: the audit's inputs. Drop the session records ("" in place of the log fields) to see
# how far the store alone gets.
WRITE_LOG = case.jsonl("state/memory-write-log.jsonl")
ASK = """Below is the audit of LANTERN's case memory for inquiry EOW/2026/0412: one row an
entry, joined to the write log and to the personnel record of the account eow-fin-07.

Who wrote the eighth entry (M-08), from where, and by what route? Name the fields you rely on.
Say what the audit shows and what it cannot show. Five sentences at most."""

OUT.mkdir(parents=True, exist_ok=True)
store = memory.from_case()
record = case.read("personnel/iyer.md")
account, events = memory.personnel(record)
rows = AUDIT(store, WRITE_LOG, record)

step("1. Every entry, joined")
table = Table(title="The case memory, entry by entry, from the store and the write log")
for col in ("entry", "written", "account", "host", "route", "tool", "source or episode",
            "text"):
    table.add_column(col)
for r in rows:
    table.add_row(r["entry"], r["written_at"].replace("T", " ")[:16], r["account"], r["host"],
                  r["route"], r["tool"], (r["source"] or r["episode"] or "NONE")[:30],
                  "as written" if r["text_matches"] else "CHANGED")
console.print(table)
lone = [r for r in rows if r["unsourced"]]
note(f"{len(rows)} entries. {sum(r['text_matches'] for r in rows)} still read exactly as "
     f"written (the hash in the log against the store). {len(lone)} name neither a source nor "
     f"an episode: {', '.join(r['entry'] for r in lone)}.")

step("2. The entries with no source, against the personnel record")
p_after = learn.predict(
    f"The personnel record for {account} has five dated events in May: the interview, the "
    "suspension, the badge, the revocation of the EOW login and the request to disable the "
    "HQ account. How many of the unsourced entries were written after the badge was "
    "surrendered?", ["None", "Some of them", "All of them"])
table = Table(title=f"{account}: the personnel record and the writes, in time order")
for col in ("when", "what", "source"):
    table.add_column(col)
timeline = [(at, what, "personnel record") for at, what in events]
timeline += [(r["written_at"], f"{r['entry']} written ({r['route']} from {r['host']}, "
              f"session {r['session']})", "write log") for r in lone]
for at, what, src in sorted(timeline):
    table.add_row(at.replace("T", " ")[:16], what[:70], src)
console.print(table)
badge = next(at for at, what in events if "badge" in what.lower())
revoked = next(at for at, what in events if "revoked" in what.lower())
after_badge = [r for r in lone if r["written_at"] > badge]
after_revoked = [r for r in lone if r["written_at"] > revoked]
note(f"Badge surrendered {badge.replace('T', ' ')[:16]}; EOW login revoked "
     f"{revoked.replace('T', ' ')[:16]}. Written under {account} after the badge: "
     f"{len(after_badge)} of {len(lone)}; after the revocation: {len(after_revoked)} of "
     f"{len(lone)}. Ticket DGS-44817, to disable the HQ account, was "
     f"{'still open on 13 July' if 'still open' in record else 'closed'}.")
learn.reveal(p_after, answer=0 if not after_badge else 2 if len(after_badge) == len(lone)
             else 1,
             why="An account wrote after its holder had handed in his badge and lost his EOW "
             "login. A login name on an entry says which account was used, not who used it.")

step("3. The route")
p_route = learn.predict(
    "Officers' entries came from lantern-ws-01 through LANTERN's screen or its remember tool. "
    "Which route did the unsourced entries come by?",
    ["The same workstation", "A VPN session under eow-fin-07", "An HQ service account"])
routes = Counter((r["route"], r["host"], r["tool"], r["unsourced"]) for r in rows)
table = Table(title="Routes into the memory")
for col in ("route", "host", "tool", "entries", "with a source"):
    table.add_column(col)
for (route, host, tool, unsourced), n in sorted(routes.items()):
    table.add_row(route, host, tool, str(n), "no" if unsourced else "yes")
console.print(table)
lone_routes = {(r["route"], r["host"]) for r in lone}
sessions = [r["session"] for r in lone]
note(f"Every unsourced entry: {', '.join(f'{a} on {b}' for a, b in sorted(lone_routes))}, "
     f"sessions {', '.join(sessions)}, each at "
     f"{', '.join(sorted({r['written_at'][11:16] for r in lone}))}. No entry with a source "
     "came that way.")
by_service = lone_routes == {("svc-lantern-sync", "hq-sync-01")}
learn.reveal(p_route, answer=2 if by_service else 1 if any("vpn" in r for r, _ in lone_routes)
             else 0,
             why="svc-lantern-sync is HQ Digital Services' nightly sync account, the account "
             "Owen Strand's sync runs under. It opened the connection; eow-fin-07 is only the "
             "name it wrote under. Whoever administers the sync administers these logs too.")

step("4. LANTERN asked, with the audit in front of it")
audit_text = "\n".join(json.dumps({k: v for k, v in r.items() if k != "after"}) for r in rows)
audit_text += "\nPersonnel record of eow-fin-07:\n" + "\n".join(f"{a}: {w}" for a, w in events)
r = chat(f"{ASK}\n\n{audit_text}", seed=7, max_tokens=400)
reply("LANTERN: who wrote the eighth entry?", r.text)
said = r.text.lower()
cites = {"svc-lantern-sync": "svc-lantern-sync" in said, "hq-sync-01": "hq-sync-01" in said,
         "the session": "sync-2026-06-02-0158" in said, "eow-fin-07": "eow-fin-07" in said}
blames = bool(re.search(r"\biyer\b[^.]{0,40}\b(wrote|added|created|entered|made)\b", said))
note("Named in the answer: " + ", ".join(f"{k} {'yes' if v else 'no'}" for k, v in cites.items())
     + f". Says Iyer wrote it: {'yes' if blames else 'no'}.")
(OUT / "audit.json").write_text(json.dumps({"rows": rows, "answer": r.text}, indent=2),
                                encoding="utf-8")

learn.record(
    entries=len(rows),
    text_matches=sum(r["text_matches"] for r in rows),
    unsourced=len(lone),
    unsourced_after_badge=len(after_badge),
    unsourced_after_revoked=len(after_revoked),
    unsourced_by_service=sum(r["route"] == "svc-lantern-sync" for r in lone),
    sourced_by_service=sum(r["route"] == "svc-lantern-sync" for r in rows if not r["unsourced"]),
    routes=len({(r["route"], r["host"]) for r in rows}),
    personnel_events=len(events),
    answer_names_service=cites["svc-lantern-sync"],
    answer_names_host=cites["hq-sync-01"],
    answer_names_session=cites["the session"],
    answer_blames_iyer=blames,
    mine=MINE is not None,
)

finding(f"""
Every one of the {len(rows)} entries is joined to its source, episode, account, host, route
and session, and {sum(r['text_matches'] for r in rows)} still read exactly as written.
{len(lone)} rest on nothing, and all {len(after_badge)} of those written after
{badge.replace('T', ' ')[:16]} were written under {account} after DS Iyer had surrendered his
badge and lost his EOW login. None came from the EOW: each came through
{', '.join(f'{a} on {b}' for a, b in sorted(lone_routes))}, at 01:58, by memory.append. With
the audit in front of it LANTERN named the service account
{'and' if cites['hq-sync-01'] else 'but not'} the host, and
{'did' if blames else 'did not'} say that Iyer wrote the entry. The audit shows which account
and which machine. It cannot show whose hand.
""")
save_shot("20-the-memory-audit")
