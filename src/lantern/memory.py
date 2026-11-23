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
        def origin(e: Entry) -> str:
            return e.source or (f"episode {e.episode}" if e.episode else "no source")
        return "\n".join(f"- {e.text} [{e.kind}; {origin(e)}; {e.author}, {e.written_at[:10]}]"
                         for e in entries)


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


# ---- chapter 12: kinds ------------------------------------------------------------------------


def by_kind(entries: Iterable[Entry]) -> dict[str, list[Entry]]:
    """Entries split by kind, every kind in KINDS present (empty where none), in the order
    given. An entry of an unknown kind is refused."""
    out: dict[str, list[Entry]] = {k: [] for k in KINDS}
    for e in entries:
        if e.kind not in out:
            raise ValueError(f"{e.id}: unknown kind {e.kind!r}")
        out[e.kind].append(e)
    return out


def unsupported(entries: Iterable[Entry]) -> list[Entry]:
    """Entries with nothing behind them, in the order given. An episode must name its record;
    a fact or a procedure a record, or an episode that is among `entries`; a summary what it
    was built from. A source of only spaces is no source."""
    entries = list(entries)
    episodes = {e.id for e in entries if e.kind == "episode"}
    out = []
    for e in entries:
        source = (e.source or "").strip()
        if e.kind == "summary":
            ok = bool(e.derived_from)
        elif e.kind == "episode":
            ok = bool(source)
        else:
            ok = bool(source) or e.episode in episodes
        if not ok:
            out.append(e)
    return out


# ---- chapter 13: the write gate ---------------------------------------------------------------

JUDGEMENT = re.compile(r"\b(cleared|licensed|routine|ordinary|need no|do not)\b", re.I)
FIGURE = re.compile(r"\b\d[\d,]*\.\d{2}\b|\b[A-Z]{2,}(?:-[A-Z0-9]+)+\b")


def figures(text: str) -> list[str]:
    """Amounts (296,400.00) and references (ICB-77-10458) in a text, commas taken out."""
    return [f.replace(",", "") for f in FIGURE.findall(text)]


def write_gate(read: dict[str, str] | None = None, *,
               machine_accounts: Iterable[str] = ("svc-lantern-sync",),
               inactive: dict[str, str] | None = None,
               models: Iterable[str] = ("lantern",)) -> Policy:
    """Chapter 13's write policy. On top of `default_policy` (a source, no machine account, no
    closed account): an entry the model proposes must cite a document read in this session
    (`read`: name -> text) that shows every amount and reference it states; and an entry that
    passes a judgement on a party (cleared, licensed, routine, ordinary, need no, do not) is
    held for a person whoever wrote it. A word list is crude: it holds, it does not decide."""
    base = default_policy(machine_accounts, inactive)
    docs = read if read is not None else {}  # the session adds to it as it reads
    model_authors = set(models)

    def policy(entry: Entry, store: Store) -> list[str]:
        problems = base(entry, store)
        if entry.author in model_authors:
            cited = [name for name in docs if name.lower() in (entry.source or "").lower()]
            if not cited:
                problems.append("cites no document read in this session")
            else:
                shown = " ".join(docs[n] for n in cited).replace(",", "")
                missing = [f for f in figures(entry.text) if f not in shown]
                if missing:
                    problems.append(f"the source does not show {', '.join(missing)}")
        found = JUDGEMENT.findall(entry.text)
        if found:
            problems.append(f"a judgement ({found[0].lower()}): a person must keep it")
        return problems
    return policy


# ---- chapter 14: reading -------------------------------------------------------------------------

Embed = Callable[[list[str], str], list[list[float]]]  # (texts, "query" | "document") -> vectors


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def retrieve(entries: Iterable[Entry], inquiry: str | None, *, user: str | None = None,
             query: str | None = None, k: int | None = None, by: str = "relevance",
             embed: Embed | None = None) -> list[Entry]:
    """What a session starts with, from a list of entries: kept entries only; then scope
    (`inquiry` None reads every inquiry, and every officer's private notes: the unscoped
    arm); then order: "recency" newest first, "relevance" BM25 against `query` (no match, not
    loaded), "embedding" cosine against `query` with `embed`, "all" as written; then `k`."""
    pool = [e for e in entries if e.status == "kept"]
    if inquiry is not None:
        pool = [e for e in pool if e.inquiry == inquiry and (e.user is None or e.user == user)]
    pool.sort(key=lambda e: (e.written_at, e.id))
    if by == "recency":
        pool = sorted(pool, key=lambda e: e.written_at, reverse=True)
    elif by in ("relevance", "embedding"):
        if not query:
            raise ValueError(f"by={by!r} needs a query")
        if by == "relevance":
            scores = bm25([e.text for e in pool], query)
            keep = [i for i in range(len(pool)) if scores[i] > 0]
        else:
            if embed is None:
                raise ValueError("by='embedding' needs embed")
            q = embed([query], "query")[0]
            scores = [cosine(q, v) for v in embed([e.text for e in pool], "document")] \
                if pool else []
            keep = list(range(len(pool)))
        pool = [pool[i] for i in sorted(keep, key=lambda i: (-scores[i], pool[i].written_at))]
    elif by != "all":
        raise ValueError(f"unknown order {by!r}")
    return pool if k is None else pool[:k]


# ---- chapter 18: correcting --------------------------------------------------------------------

Rebuild = Callable[[Entry, list[Entry]], str]  # (old summary, what it may now rest on) -> text


def vanished(store: Store) -> list[str]:
    """Entries the log says were written that are no longer in the store at all: a row
    deleted by hand. `verify` checks the entries that are there; this checks the ones that
    are not."""
    written = list(dict.fromkeys(e["entry"] for e in store.events() if e["event"] == "write"))
    return [i for i in written if store.get(i) is None]


def retract_and_rebuild(store: Store, ids: Iterable[str], *, by: str, at: str, reason: str,
                        rebuild: Rebuild) -> dict[str, str]:
    """Retract `ids`, then rebuild every live entry built on them, oldest first, so a summary
    built on another summary is rebuilt from the new one. Each rebuilt entry rests on what
    its old one rested on, less what was retracted and with rebuilt entries in place of old
    ones; it supersedes the old entry. Returns {old id: new id}."""
    affected: list[str] = []
    for i in ids:
        for d in store.retract(i, by=by, at=at, reason=reason):
            if d not in affected:
                affected.append(d)
    done: dict[str, str] = {}
    for old in sorted((store.get(i) for i in affected), key=lambda e: (e.written_at, e.id)):
        basis = []
        for d in old.derived_from:
            d = done.get(d, d)
            e = store.get(d)
            if e is not None and e.status == "kept":
                basis.append(e)
        new = Entry(id=f"{old.id}-r", text=rebuild(old, basis), kind=old.kind,
                    inquiry=old.inquiry, author=old.author, written_at=at, via=old.via,
                    user=old.user, derived_from=[e.id for e in basis])
        store.supersede(old.id, new, by=by, reason=f"rebuilt after {reason}")
        done[old.id] = new.id
    return done


# ---- chapter 20: the audit ---------------------------------------------------------------------

MONTH_NUMBERS = {m: i for i, m in enumerate(
    ("January", "February", "March", "April", "May", "June", "July", "August", "September",
     "October", "November", "December"), start=1)}
PERSONNEL_ROW = re.compile(r"^\| \w+ (\d+) (\w+) (\d{4}), (\d\d:\d\d)[^|]*\| ([^|]+?) \|")


def personnel(text: str) -> tuple[str, list[tuple[str, str]]]:
    """A personnel record: the account it covers, and its dated events, oldest first, as
    (ISO time, what happened)."""
    account = re.search(r"^Account: (\S+)", text, re.M)
    events = []
    for line in text.splitlines():
        m = PERSONNEL_ROW.match(line)
        if m:
            d, month, y, hm, what = m.groups()
            events.append((f"{y}-{MONTH_NUMBERS[month]:02d}-{int(d):02d}T{hm}:00", what.strip()))
    return (account.group(1) if account else ""), sorted(events)


def audit(store: Store, write_log: list[dict[str, Any]], record: str) -> list[dict[str, Any]]:
    """Every entry in the write log joined to the store: its source, episode, account, host,
    route, session and tool; whether its text is still the text that was written; whether it
    rests on anything; and, for the account the personnel record covers, every event in that
    record that came before the write."""
    account, events = personnel(record)
    rows = []
    for r in write_log:
        e = store.get(f"M-{r['entry']:02d}")
        rows.append({
            "entry": f"M-{r['entry']:02d}", "written_at": r["written_at"],
            "account": r["account"], "kind": r["kind"], "source": r["source"],
            "episode": r["episode"], "host": r["host"], "route": r["via"],
            "session": r["session"], "tool": r["tool"],
            "text_matches": e is not None and e.text_hash == r["text_sha256"],
            "unsourced": not (r["source"] or r["episode"]),
            "after": [what for at, what in events if at <= r["written_at"]]
            if r["account"] == account else [],
        })
    return rows


# ---- chapter 19: graders for a memory suite ------------------------------------------------------

NEGATION = re.compile(r"\b(not|never|no|nothing|neither|nor|without|cannot|isn't|wasn't|hasn't|"
                      r"didn't|doesn't|aren't|weren't|haven't)\b")
ABSTAIN = ("not in evidence", "not in the case memory", "no record", "was not told",
           "were not told", "does not say", "do not have", "not recorded", "no information",
           "does not record", "not stated")


def _plain(text: str) -> str:
    return re.sub(r"(?<=\d),(?=\d)", "", text.lower().replace("’", "'"))


def whole_figure(answer: str, figure: str) -> bool:
    """`figure` is in the answer as a whole figure: 2,284,893.10 matches 2284893.10, not
    12,284,893.10, 2,284,893.1 or 2,284,893.105."""
    f = re.escape(_plain(figure))
    return re.search(rf"(?<![\d.]){f}(?![\d]|\.\d)", _plain(answer)) is not None


def cites(answer: str, entry_id: str) -> bool:
    """The answer names the entry by its id: M-01, not M-010 or M-1."""
    return re.search(rf"(?<![\w-]){re.escape(entry_id)}(?![\w-]|-r)", answer) is not None


def first_sentence(text: str) -> str:
    return re.split(r"(?<=[.;:!?])\s", text.strip(), maxsplit=1)[0]


def abstains(answer: str, question: str = "") -> bool:
    """The answer says it was not told, in one of several phrasings, in its first sentence,
    and states no figure or date the question did not already give."""
    head = _plain(first_sentence(answer))
    if not any(p in head for p in ABSTAIN):
        return False
    asked = set(re.findall(r"\d+", _plain(question)))
    return all(n in asked for n in re.findall(r"\d+", _plain(answer)))


def denies(answer: str, claim: str) -> bool:
    """The answer does not affirm a retracted claim (`claim` is its key word, "cleared").
    A first word of "no" passes and "yes" fails; otherwise every use of the word must have a
    negation in the six words before it (and after any earlier use), and an answer that
    abstains passes. "Not cleared" is not "cleared"."""
    words = re.findall(r"[a-z']+", _plain(answer))
    if not words:
        return False
    if words[0] == "no":
        return True
    if words[0] == "yes":
        return False
    uses = [i for i, w in enumerate(words) if w.startswith(claim.lower())]
    if not uses:
        return abstains(answer)
    starts = [max(0, i - 6, prev + 1) for prev, i in zip([-1, *uses], uses, strict=False)]
    return all(NEGATION.search(" ".join(words[s:i])) for s, i in zip(starts, uses, strict=True))
