"""Chapter 14 exercise: the scoped retriever, what a session loads from memory.

Grade it with `make exercise N=14`. The tests use plain entries and a fake embedding function,
so no model is needed. When it passes, `make lesson N=14 ARGS=--mine` loads every session in
the chapter with yours, on the case store and at ten thousand entries.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from lantern.memory import Entry, bm25, cosine

Embed = Callable[[list[str], str], list[list[float]]]  # (texts, "query" | "document") -> vectors


def retrieve(entries: Iterable[Entry], inquiry: str | None, *, user: str | None = None,
             query: str | None = None, k: int | None = None, by: str = "relevance",
             embed: Embed | None = None) -> list[Entry]:
    """What a session starts with, in this order of steps:

    1. Only entries whose status is "kept" (a held or retracted entry is never loaded).
    2. Scope: when `inquiry` is not None, only that inquiry's entries, and of those only the
       shared ones (`user` None) and this officer's own (`user` equal to `user`). With
       `inquiry` None nothing is scoped: that is the arm that shows what leaks.
    3. Order, starting from written order (written_at, then id):
       - "all": as written;
       - "recency": newest written_at first;
       - "relevance": `bm25(texts, query)`, highest first; an entry scoring 0 is not loaded;
       - "embedding": `cosine(embed([query], "query")[0], v)` for each entry's vector from
         `embed(texts, "document")`, highest first;
       ties keep the older entry first. "relevance" and "embedding" without a query, or
       "embedding" without `embed`, raise ValueError; so does an unknown order.
    4. The first `k` (all of them when k is None).
    """
    # TODO 1: keep only kept entries.
    # TODO 2: apply the scope when an inquiry is given.
    # TODO 3: order them as `by` says, raising ValueError where the docstring says.
    # TODO 4: cut to k.
    raise NotImplementedError("write retrieve")
