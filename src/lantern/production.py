"""Context in production: a version on every answer, a change log, a budget alarm, a nightly audit.

Chapter 23 builds these over the pieces of chapters 01 to 20:

- **The context version** (`context_version`): a hash over everything LANTERN is given before
  a question that is not the question itself or the session: the standing orders, the loaded
  memory, the standing notes, the tool schemas, and the layout (which sections, in which
  order, sent where). Recorded with every answer, it says which context produced it.
- **The change log** (`ChangeLog`): who changed the context, what, why, and the version before
  and after; one JSON line a change, each hashed with the one before, like the memory's log.
- **The budget alarm** (`alarm`): a warning before the window is full, naming the largest
  account, and how many more turns of the same size a session has before it.
- **The nightly audit** (`nightly`): chapter 20's audit, the chain check, every write since
  the last run with what the gate did with it, and whether the chain still contains the last
  hash the previous night recorded (kept outside the store, so a rewritten log shows).

Nothing here calls a model.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lantern import memory
from lantern.budget import Budget
from lantern.context import HISTORY, QUESTION, Section
from lantern.memory import GENESIS, Entry, Store

INQUIRY = "EOW/2026/0412"
SESSION_PARTS = (HISTORY, QUESTION)


def _content(s: Section) -> str:
    if s.payload is not None and s.where not in SESSION_PARTS:
        return json.dumps(s.payload, sort_keys=True)  # tool schemas: key order is not a change
    return s.text


def context_version(parts: list[Section]) -> str:
    """"ctx-" and twelve hex digits of a SHA-256 over the context's configuration: every
    section's name, where it is sent and its content, except the session so far and the
    question, plus the order of all the sections. The same context gives the same version;
    one changed word, a changed tool schema, a changed memory or a moved section gives
    another; a new question does not."""
    body = {"layout": [[s.name, s.where] for s in parts],
            "sections": [[s.name, s.where, _content(s)] for s in parts
                         if s.where not in SESSION_PARTS]}
    digest = hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()
    return "ctx-" + digest[:12]


def fingerprints(parts: list[Section]) -> list[tuple[str, str, str]]:
    """(section, where, eight hex digits of its content) for the sections the version covers:
    which part changed between two versions."""
    return [(s.name, s.where, hashlib.sha256(_content(s).encode("utf-8")).hexdigest()[:8])
            for s in parts if s.where not in SESSION_PARTS]


# ---- the change log ------------------------------------------------------------------------------


class ChangeLog:
    """Every change to LANTERN's context: one JSON line, hashed with the line before."""

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(x) for x in self.path.read_text(encoding="utf-8").splitlines() if x]

    def add(self, *, at: str, by: str, what: str, reason: str, before: str, after: str
            ) -> dict[str, Any]:
        prev = (self.entries() or [{"hash": GENESIS}])[-1]["hash"]
        row = {"at": at, "by": by, "what": what, "reason": reason, "before": before,
               "after": after, "prev": prev}
        row["hash"] = memory.sha(json.dumps(row, sort_keys=True))
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, sort_keys=True) + "\n")
        return row

    def verify(self) -> list[str]:
        problems, prev = [], GENESIS
        for n, row in enumerate(self.entries(), start=1):
            body = {k: v for k, v in row.items() if k != "hash"}
            if row["prev"] != prev:
                problems.append(f"change {n}: does not follow change {n - 1}")
            if memory.sha(json.dumps(body, sort_keys=True)) != row["hash"]:
                problems.append(f"change {n}: altered after it was written")
            prev = row["hash"]
        return problems


# ---- the budget alarm ----------------------------------------------------------------------------


@dataclass(frozen=True)
class Alarm:
    level: str  # "ok", "warn" (at or past warn_at of the input budget) or "over"
    total: int
    limit: int
    share: float
    largest: str
    message: str


def alarm(spent: dict[str, int], budget: Budget, *, warn_at: float = 0.8) -> Alarm:
    """The window, checked before it is full. "over" when the whole or any account is past
    its limit, "warn" from `warn_at` of the input budget, else "ok"; the message names the
    largest account."""
    total = sum(spent.values())
    limit = budget.for_input
    largest = max(spent, key=spent.get) if spent else ""
    over = [a for a, t in spent.items() if a in budget.limits and t > budget.limits[a]]
    share = total / limit if limit else 1.0
    level = "over" if over or total > limit else "warn" if share >= warn_at else "ok"
    what = f"{over[0]} is over its limit" if over else f"{share:.0%} of the input budget"
    return Alarm(level, total, limit, share, largest,
                 f"{level}: {total:,} of {limit:,} tokens ({what}); largest account "
                 f"{largest} ({spent.get(largest, 0):,})")


def turns_until(total: int, per_turn: int, budget: Budget, *, warn_at: float = 0.8) -> int:
    """How many more turns of `per_turn` tokens a session can take before the alarm warns."""
    if per_turn <= 0:
        raise ValueError("a turn adds tokens")
    room = int(budget.for_input * warn_at) - total
    return max(0, -(-room // per_turn))


# ---- the production store and the nightly audit --------------------------------------------------


def build_store(path: Path | str, *, at: str, by: str, reason: str,
                retract: tuple[str, ...] = ("M-08", "M-12", "M-14", "M-16"),
                notes: str = "", inactive: dict[str, str] | None = None) -> Store:
    """The memory as it stands on 7 August: the case replayed, the unsourced entries
    retracted (chapter 18), the standing notes as procedures with their author and date, and
    chapter 13's gate on every write from now on."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).unlink(missing_ok=True)
    store = memory.from_case(path=path)
    for i in retract:
        store.retract(i, by=by, at=at, reason=reason)
    for n, line in enumerate((x[2:] for x in notes.splitlines() if x.startswith("- ")), 1):
        text, _, sig = line.rpartition(" (")
        author, _, day = sig.rstrip(")").partition(", ")
        store.write(Entry(id=f"N-{n:02d}", text=text, kind="procedure", inquiry=INQUIRY,
                          author=author, written_at=f"{day}T09:00:00",
                          source=f"standing note of {day}"))
    store.policy = memory.default_policy(inactive=inactive)
    return store


def nightly(store: Store, write_log: list[dict[str, Any]], record: str, *, since: str,
            last_hash: str | None = None) -> dict[str, Any]:
    """Last night's audit. Problems: a broken or altered chain, an entry gone from the store,
    a kept entry that rests on nothing, a chain that no longer holds the hash recorded at the
    last run. Waiting for a person: every write since `since` that the gate held."""
    events = store.events()
    rows = memory.audit(store, write_log, record)
    problems = store.verify() + [f"{i}: in the log, gone from the store"
                                 for i in memory.vanished(store)]
    kept_bare = [e.id for e in store.all() if e.status == "kept" and e.kind != "episode"
                 and memory.needs_source(e, store)]
    problems += [f"{i}: kept with no source" for i in kept_bare]
    continues = last_hash is None or any(e["hash"] == last_hash for e in events)
    if not continues:
        problems.append("the chain no longer holds the hash recorded at the last run")
    new = [{"entry": e["entry"], "at": e["at"], "by": e["by"], "via": e["detail"].get("via"),
            "status": e["detail"].get("status"), "problems": e["detail"].get("problems", [])}
           for e in events if e["event"] == "write" and e["at"] > since]
    return {"since": since, "entries": len(store.all()), "audited": len(rows),
            "unsourced_in_log": sum(r["unsourced"] for r in rows),
            "text_matches": sum(r["text_matches"] for r in rows),
            "new_writes": new, "held": [w for w in new if w["status"] == "held"],
            "chain_continues": continues, "problems": problems, "ok": not problems,
            "last_hash": events[-1]["hash"] if events else GENESIS}


def write_report(report: dict[str, Any], folder: Path | str, day: str) -> Path:
    """The night's report as JSON, and the last hash in a file of its own for the next run."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / f"audit-{day}.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (folder / "last-hash").write_text(report["last_hash"] + "\n", encoding="utf-8")
    return out


__all__ = ["Alarm", "ChangeLog", "alarm", "build_store", "context_version", "fingerprints",
           "nightly", "turns_until", "write_report"]
