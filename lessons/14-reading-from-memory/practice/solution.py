"""Chapter 14 reference solution: the scoped retriever."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from lantern.memory import Entry, bm25, cosine

Embed = Callable[[list[str], str], list[list[float]]]


def retrieve(entries: Iterable[Entry], inquiry: str | None, *, user: str | None = None,
             query: str | None = None, k: int | None = None, by: str = "relevance",
             embed: Embed | None = None) -> list[Entry]:
    """What a session starts with: kept entries, then scope, then order, then k."""
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
