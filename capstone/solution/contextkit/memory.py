"""A memory store in which every entry has a source, an author, a time and a hash.

Reference solution of the capstone. It imports nothing from lantern.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from collections import Counter
from dataclasses import asdict, dataclass, field

GENESIS = "0" * 64
KINDS = ("episode", "fact", "procedure", "summary")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class Record:
    id: str
    text: str
    kind: str
    inquiry: str
    author: str
    at: str
    source: str | None = None
    episode: str | None = None
    via: str = "lantern-ui"
    user: str | None = None
    derived_from: list[str] = field(default_factory=list)
    status: str = "kept"
    problems: list[str] = field(default_factory=list)


class MemoryStore:
    def __init__(self, path: str = ":memory:", *,
                 machine_accounts: tuple[str, ...] = ("svc-lantern-sync",),
                 closed_accounts: dict[str, str] | None = None):
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, data TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS log (seq INTEGER PRIMARY KEY, body TEXT, "
                        "hash TEXT)")
        self.machines = set(machine_accounts)
        self.closed = dict(closed_accounts or {})

    # the log
    def _append(self, event: str, id: str, at: str, by: str, **detail) -> None:
        row = self.db.execute("SELECT hash FROM log ORDER BY seq DESC LIMIT 1").fetchone()
        prev = row[0] if row else GENESIS
        body = json.dumps({"event": event, "id": id, "at": at, "by": by, "detail": detail,
                           "prev": prev}, sort_keys=True)
        self.db.execute("INSERT INTO log (body, hash) VALUES (?, ?)", (body, sha(body)))

    def log(self) -> list[dict]:
        return [json.loads(b) | {"hash": h}
                for b, h in self.db.execute("SELECT body, hash FROM log ORDER BY seq")]

    def verify(self) -> list[str]:
        problems, prev, hashes = [], GENESIS, {}
        for n, (body, h) in enumerate(self.db.execute("SELECT body, hash FROM log ORDER BY seq"),
                                      1):
            e = json.loads(body)
            if e["prev"] != prev:
                problems.append(f"log {n}: chain broken")
            if sha(body) != h:
                problems.append(f"log {n}: altered")
            prev = h
            if "text_sha256" in e["detail"]:
                hashes[e["id"]] = e["detail"]["text_sha256"]
        for r in self.all():
            if r.status != "forgotten" and hashes.get(r.id) != sha(r.text):
                problems.append(f"{r.id}: text changed after it was written")
        return problems

    # records
    def _save(self, r: Record) -> None:
        self.db.execute("INSERT OR REPLACE INTO records VALUES (?, ?)",
                        (r.id, json.dumps(asdict(r))))
        self.db.commit()

    def get(self, id: str) -> Record | None:
        row = self.db.execute("SELECT data FROM records WHERE id = ?", (id,)).fetchone()
        return Record(**json.loads(row[0])) if row else None

    def all(self) -> list[Record]:
        return sorted((Record(**json.loads(d)) for (d,) in
                       self.db.execute("SELECT data FROM records")), key=lambda r: (r.at, r.id))

    def problems_with(self, r: Record) -> list[str]:
        out = []
        if r.kind not in KINDS:
            out.append(f"unknown kind {r.kind}")
        if r.kind == "summary" and not r.derived_from:
            out.append("a summary must name what it was built from")
        if r.kind in ("fact", "procedure") and not (r.source or r.episode):
            out.append("no source and no episode")
        if r.kind == "episode" and not r.source:
            out.append("an episode must name its record")
        if r.episode and not r.source and self.get(r.episode) is None:
            out.append(f"episode {r.episode} is not in the store")
        if r.via in self.machines:
            out.append(f"written through {r.via}, a machine account")
        if r.author in self.closed and r.at >= self.closed[r.author]:
            out.append(f"{r.author} was closed on {self.closed[r.author][:10]}")
        return out

    def write(self, **fields) -> Record:
        r = Record(**fields)
        if self.get(r.id) is not None:
            raise ValueError(f"{r.id} exists")
        r.problems = self.problems_with(r)
        r.status = "held" if r.problems else "kept"
        self._append("write", r.id, r.at, r.author, text_sha256=sha(r.text), status=r.status,
                     via=r.via, source=r.source)
        self._save(r)
        return r

    def _need(self, id: str, status: str | None = None) -> Record:
        r = self.get(id)
        if r is None:
            raise KeyError(id)
        if status and r.status != status:
            raise ValueError(f"{id} is {r.status}")
        return r

    def release(self, id: str, *, by: str, at: str, reason: str) -> Record:
        r = self._need(id, "held")
        r.status = "kept"
        self._append("release", id, at, by, reason=reason)
        self._save(r)
        return r

    def retract(self, id: str, *, by: str, at: str, reason: str) -> list[str]:
        r = self._need(id)
        r.status = "retracted"
        self._append("retract", id, at, by, reason=reason)
        self._save(r)
        out, todo = [], [id]
        live = [x for x in self.all() if x.status in ("kept", "held")]
        while todo:
            cur = todo.pop()
            for x in live:
                if cur in x.derived_from and x.id not in out:
                    out.append(x.id)
                    todo.append(x.id)
        return out

    def forget(self, id: str, *, by: str, at: str, reason: str) -> Record:
        r = self._need(id)
        r.text, r.status = "", "forgotten"
        self._append("forget", id, at, by, reason=reason)
        self._save(r)
        return r

    # reading
    def load(self, inquiry: str, *, user: str | None = None, query: str | None = None,
             k: int = 8) -> list[Record]:
        pool = [r for r in self.all() if r.status == "kept" and r.inquiry == inquiry
                and (r.user is None or r.user == user)]
        if query:
            scores = bm25([r.text for r in pool], query)
            order = sorted(range(len(pool)), key=lambda i: (-scores[i], pool[i].at))
            pool = [pool[i] for i in order if scores[i] > 0]
        else:
            pool = sorted(pool, key=lambda r: r.at, reverse=True)
        return pool[:k]


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower().replace(",", ""))


def bm25(docs: list[str], query: str, k1: float = 1.2, b: float = 0.75) -> list[float]:
    toks = [words(d) for d in docs]
    if not toks:
        return []
    avg = sum(map(len, toks)) / len(toks) or 1
    df = Counter(w for t in toks for w in set(t))
    out = []
    for t in toks:
        tf, score = Counter(t), 0.0
        for q in set(words(query)):
            if q in tf:
                idf = math.log(1 + (len(toks) - df[q] + 0.5) / (df[q] + 0.5))
                score += idf * tf[q] * (k1 + 1) / (tf[q] + k1 * (1 - b + b * len(t) / avg))
        out.append(score)
    return out
