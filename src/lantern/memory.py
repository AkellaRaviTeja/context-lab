"""LANTERN's memory, rebuilt: every entry has a kind, a source, an author, a time and a hash.

Chapters 12 to 23 build it a piece at a time; the capstone asks for it again from a blank folder.

- **Kinds** (chapter 12): an *episode* is what happened, a *fact* what is true, a *procedure*
  how the team works. A fact should rest on an episode or a record.
- **Writing** (chapter 13): `Store.write` runs a policy; an entry that fails it is *held* for a
  person, not kept, and `release` is a person's decision with their name on it.
- **Reading** (chapter 14): `Store.load` reads by inquiry and user scope first, then by
  recency or relevance (BM25 over the text, here; embeddings in the chapter), up to `k`.
- **Correcting** (chapter 18): `retract` keeps the entry and marks it, and names every entry
  derived from it (a summary built on it) so it can be rebuilt; `supersede` replaces an entry
  with a corrected one; `forget` erases the text and keeps only the record that it existed.
- **Proof** (chapters 13 and 20): every change is an event in an append-only log, each
  event hashed with the one before it. `verify` recomputes the chain. An event holds the hash
  of an entry's text, not the text, so a forgotten entry leaves the chain intact.

SQLite, one file, under `.scratch/` in the lessons. Nothing here calls a model.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

KINDS = ("episode", "fact", "procedure", "summary")
GENESIS = "0" * 64


@dataclass
class Entry:
    id: str
    text: str
    kind: str
    inquiry: str
    author: str
    written_at: str
    source: str | None = None
    episode: str | None = None
    via: str = "lantern-ui"
    user: str | None = None  # None: the whole inquiry may read it; else only this officer
    derived_from: list[str] = field(default_factory=list)
    status: str = "kept"  # kept | held | retracted | superseded | forgotten
    problems: list[str] = field(default_factory=list)
    note: str = ""

    @property
    def text_hash(self) -> str:
        return sha(self.text)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


Policy = Callable[[Entry, "Store"], list[str]]


def needs_source(entry: Entry, store: Store) -> list[str]:
    """Chapter 13's first rule: a fact or a procedure names the record or the episode it
    rests on. A summary names what it was derived from."""
    if entry.kind == "summary":
        return [] if entry.derived_from else ["a summary must name what it was built from"]
    if entry.kind == "episode":
        return [] if entry.source else ["an episode must name its record"]
    if not entry.source and not entry.episode:
        return ["no source and no episode"]
    if entry.episode and store.get(entry.episode) is None and not entry.source:
        return [f"episode {entry.episode} is not in the store"]
    return []


def default_policy(machine_accounts: Iterable[str] = ("svc-lantern-sync",),
                   inactive: dict[str, str] | None = None) -> Policy:
    """Sources required; nothing written through a machine account is kept without a person;
    nothing written under an account after the date it was closed (`inactive`: account ->
    ISO time) is kept at all without a person."""
    machines = set(machine_accounts)
    closed = dict(inactive or {})

    def policy(entry: Entry, store: Store) -> list[str]:
        problems = needs_source(entry, store)
        if entry.via in machines:
            problems.append(f"written through {entry.via}, a machine account")
        if entry.author in closed and entry.written_at >= closed[entry.author]:
            problems.append(f"{entry.author} was closed on {closed[entry.author][:10]}")
        if entry.kind not in KINDS:
            problems.append(f"unknown kind {entry.kind!r}")
        return problems
    return policy


class Store:
    """The memory store: entries, and an append-only, hash-chained log of every change."""

    def __init__(self, path: Path | str = ":memory:", policy: Policy | None = None):
        self.path = str(path)
        self.db = sqlite3.connect(self.path)
        self.db.execute("CREATE TABLE IF NOT EXISTS entries (id TEXT PRIMARY KEY, data TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, "
                        "event TEXT, entry TEXT, at TEXT, by TEXT, detail TEXT, prev TEXT, "
                        "hash TEXT)")
        self.policy = policy or default_policy()

    # ---- the log ------------------------------------------------------------------------------

    def _last_hash(self) -> str:
        row = self.db.execute("SELECT hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        return row[0] if row else GENESIS

    def _event(self, event: str, entry: str, at: str, by: str, detail: dict[str, Any]) -> str:
        prev = self._last_hash()
        body = json.dumps({"event": event, "entry": entry, "at": at, "by": by,
                           "detail": detail, "prev": prev}, sort_keys=True)
        h = sha(body)
        self.db.execute("INSERT INTO events (event, entry, at, by, detail, prev, hash) VALUES "
                        "(?, ?, ?, ?, ?, ?, ?)",
                        (event, entry, at, by, json.dumps(detail, sort_keys=True), prev, h))
        return h

    def events(self) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT seq, event, entry, at, by, detail, prev, hash FROM events "
                               "ORDER BY seq").fetchall()
        return [{"seq": r[0], "event": r[1], "entry": r[2], "at": r[3], "by": r[4],
                 "detail": json.loads(r[5]), "prev": r[6], "hash": r[7]} for r in rows]

    def verify(self) -> list[str]:
        """Problems with the log and the entries: a broken link, an altered event, or an
        entry whose text no longer matches the hash written when it was stored."""
        problems, prev = [], GENESIS
        written: dict[str, str] = {}
        for e in self.events():
            body = json.dumps({"event": e["event"], "entry": e["entry"], "at": e["at"],
                               "by": e["by"], "detail": e["detail"], "prev": e["prev"]},
                              sort_keys=True)
            if e["prev"] != prev:
                problems.append(f"event {e['seq']}: does not follow event {e['seq'] - 1}")
            if sha(body) != e["hash"]:
                problems.append(f"event {e['seq']}: altered after it was written")
            prev = e["hash"]
            if "text_sha256" in e["detail"]:
                written[e["entry"]] = e["detail"]["text_sha256"]
        for entry in self.all():
            if entry.status == "forgotten":
                continue
            if written.get(entry.id) != entry.text_hash:
                problems.append(f"{entry.id}: text differs from the text that was written")
        return problems

    # ---- entries ------------------------------------------------------------------------------

    def _save(self, entry: Entry) -> None:
        self.db.execute("INSERT OR REPLACE INTO entries (id, data) VALUES (?, ?)",
                        (entry.id, json.dumps(asdict(entry))))
        self.db.commit()

    def get(self, id: str) -> Entry | None:
        row = self.db.execute("SELECT data FROM entries WHERE id = ?", (id,)).fetchone()
        return Entry(**json.loads(row[0])) if row else None

    def all(self) -> list[Entry]:
        rows = self.db.execute("SELECT data FROM entries").fetchall()
        return sorted((Entry(**json.loads(r[0])) for r in rows),
                      key=lambda e: (e.written_at, e.id))

    def write(self, entry: Entry) -> Entry:
        """Store an entry. The policy's problems decide: none, it is kept; any, it is held
        for a person, with the problems on it. Either way the write is in the log."""
        if self.get(entry.id) is not None:
            raise ValueError(f"{entry.id} is already in the store; supersede it instead")
        entry.problems = self.policy(entry, self)
        entry.status = "held" if entry.problems else "kept"
        self._event("write", entry.id, entry.written_at, entry.author,
                    {"text_sha256": entry.text_hash, "kind": entry.kind, "via": entry.via,
                     "source": entry.source, "episode": entry.episode,
                     "status": entry.status, "problems": entry.problems})
        self._save(entry)
        return entry

    def release(self, id: str, *, by: str, at: str, reason: str) -> Entry:
        """A person keeps a held entry, by name and with a reason."""
        entry = self._must(id, "held")
        entry.status, entry.note = "kept", f"released by {by}: {reason}"
        self._event("release", id, at, by, {"reason": reason})
        self._save(entry)
        return entry

    def retract(self, id: str, *, by: str, at: str, reason: str) -> list[str]:
        """Mark an entry retracted (it stays, so the record of what LANTERN was told stays)
        and return every entry built on it, directly or not, to be rebuilt or retracted."""
        entry = self._must(id)
        entry.status, entry.note = "retracted", f"retracted by {by} on {at[:10]}: {reason}"
        self._event("retract", id, at, by, {"reason": reason})
        self._save(entry)
        return self.built_on(id)

    def supersede(self, id: str, new: Entry, *, by: str, reason: str) -> Entry:
        """Replace an entry with a corrected one; the old one stays, marked."""
        old = self._must(id)
        new.derived_from = list(dict.fromkeys([*new.derived_from]))
        written = self.write(new)
        old.status, old.note = "superseded", f"superseded by {new.id}: {reason}"
        self._event("supersede", id, new.written_at, by, {"by_entry": new.id,
                                                         "reason": reason})
        self._save(old)
        return written

    def forget(self, id: str, *, by: str, at: str, reason: str) -> Entry:
        """Erase an entry's text. Its id, its dates, who wrote it and the hash of what it said
        stay in the log; what it said does not. For a person cleared of suspicion."""
        entry = self._must(id)
        entry.text, entry.status = "", "forgotten"
        entry.note = f"forgotten at the request of {by} on {at[:10]}: {reason}"
        self._event("forget", id, at, by, {"reason": reason})
        self._save(entry)
        return entry

    def built_on(self, id: str) -> list[str]:
        """Every live entry derived from `id`, directly or through other entries."""
        out: list[str] = []
        frontier = [id]
        live = [e for e in self.all() if e.status in ("kept", "held")]
        while frontier:
            cur = frontier.pop()
            for e in live:
                if cur in e.derived_from and e.id not in out:
                    out.append(e.id)
                    frontier.append(e.id)
        return out

    def _must(self, id: str, status: str | None = None) -> Entry:
        entry = self.get(id)
        if entry is None:
            raise KeyError(id)
        if status and entry.status != status:
            raise ValueError(f"{id} is {entry.status}, not {status}")
        return entry

    # ---- reading ------------------------------------------------------------------------------

    def visible(self, inquiry: str, user: str | None = None) -> list[Entry]:
        """Kept entries this inquiry may read, and this officer's own private ones."""
        return [e for e in self.all() if e.status == "kept" and e.inquiry == inquiry
                and (e.user is None or e.user == user)]

    def load(self, inquiry: str, *, user: str | None = None, query: str | None = None,
             k: int | None = None, by: str = "relevance") -> list[Entry]:
        """What a session on `inquiry` starts with: scope first, then order, then `k`.
        by="relevance" ranks by BM25 against `query`; by="recency" newest first;
        by="all" in the order written."""
        pool = self.visible(inquiry, user)
        if by == "recency":
            pool = sorted(pool, key=lambda e: e.written_at, reverse=True)
        elif by == "relevance":
            if not query:
                raise ValueError("by='relevance' needs a query")
            scores = bm25([e.text for e in pool], query)
            order = sorted(range(len(pool)), key=lambda i: (-scores[i], pool[i].written_at))
            pool = [pool[i] for i in order if scores[i] > 0]
        return pool if k is None else pool[:k]

    def render(self, entries: list[Entry]) -> str:
        """Entries as the context shows them: the text, then where it came from."""
        return "\n".join(
            f"- {e.text} [{e.kind}; {e.source or ('episode ' + e.episode if e.episode else 'no source')}; "
            f"{e.author}, {e.written_at[:10]}]" for e in entries)


WORD = re.compile(r"[a-z0-9]+")


def words(text: str) -> list[str]:
    return WORD.findall(text.lower().replace(",", ""))


def bm25(docs: list[str], query: str, k1: float = 1.2, b: float = 0.75) -> list[float]:
    """Okapi BM25 of each document against the query. Plain, so the chapter can show it."""
    toks = [words(d) for d in docs]
    if not toks:
        return []
    avg = sum(map(len, toks)) / len(toks) or 1
    df = Counter(w for t in toks for w in set(t))
    n = len(toks)
    out = []
    for t in toks:
        tf = Counter(t)
        score = 0.0
        for q in set(words(query)):
            if q not in tf:
                continue
            idf = math.log(1 + (n - df[q] + 0.5) / (df[q] + 0.5))
            score += idf * tf[q] * (k1 + 1) / (tf[q] + k1 * (1 - b + b * len(t) / avg))
        out.append(score)
    return out


def from_case(policy: Policy | None = None, path: Path | str = ":memory:") -> Store:
    """LANTERN's case memory of 13 July replayed into a store, entry by entry, through the
    policy, with each entry's kind, source, episode and route from the write log. The
    episodes are written first. Other inquiries' memories go in too, so scope matters."""
    from lantern import case

    store = Store(path, policy or (lambda e, s: []))
    inquiry = "EOW/2026/0412"
    for line in case.read("state/episodes.jsonl").splitlines():
        ep = json.loads(line)
        store.write(Entry(id=ep["id"], text=ep["what"], kind="episode", inquiry=inquiry,
                          author=ep["who"], written_at=ep["at"], source="case log"))
    texts = [line[2:] for line in case.read("state/case-memory.md").splitlines()
             if line.startswith("- ")]
    for line, text in zip(case.read("state/memory-write-log.jsonl").splitlines(), texts,
                          strict=True):
        r = json.loads(line)
        store.write(Entry(id=f"M-{r['entry']:02d}", text=text, kind=r["kind"], inquiry=inquiry,
                          author=r["account"], written_at=r["written_at"], source=r["source"],
                          episode=r["episode"], via=r["via"]))
    for line in case.read("state/other-inquiries.jsonl").splitlines():
        o = json.loads(line)
        store.write(Entry(id=o["id"], text=o["text"], kind=o["kind"], inquiry=o["inquiry"],
                          author=o["author"], written_at=o["written_at"], user=o["user"],
                          source="officer's note"))
    return store
