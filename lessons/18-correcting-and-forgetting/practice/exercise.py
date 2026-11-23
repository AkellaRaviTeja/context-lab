"""Chapter 18 exercise: retract an entry, and rebuild everything that was built on it.

Grade it with `make exercise N=18`. The tests use a `lantern.memory.Store` and a rebuild function
that does not call a model. When it passes, `make lesson N=18 ARGS=--mine` retracts the four
eow-fin-07 entries with yours and LANTERN rebuilds the five summaries.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from lantern.memory import Entry, Store

Rebuild = Callable[[Entry, list[Entry]], str]  # (old entry, what it may now rest on) -> new text


def retract_and_rebuild(store: Store, ids: Iterable[str], *, by: str, at: str, reason: str,
                        rebuild: Rebuild) -> dict[str, str]:
    """Retract each id in `ids`, then rebuild every live entry built on any of them.

    1. `store.retract(id, by=, at=, reason=)` marks an entry retracted and returns the ids of
       every live entry built on it, directly or not. Collect them all, without repeats.
    2. Rebuild them oldest first (by written_at, then id), so a summary built on another
       summary is rebuilt after it, from the new one.
    3. What a rebuilt entry rests on (its basis): its old `derived_from`, in order, with any id
       already rebuilt replaced by its new id, keeping only entries whose status is "kept".
       A retracted entry is never part of a basis.
    4. The new entry: id f"{old.id}-r", text `rebuild(old, basis)`, written_at `at`,
       derived_from the basis ids, everything else (kind, inquiry, author, via, user) as the
       old one. Put it in with `store.supersede(old.id, new, by=by, reason=...)`.
    5. Return {old id: new id} for every entry rebuilt.
    """
    # TODO 1: retract every id and collect the affected ids, once each.
    # TODO 2: walk the affected entries oldest first.
    # TODO 3: work out each one's basis from what is kept, using rebuilt ids where there are some.
    # TODO 4: build the new entry, supersede the old one, and remember old id -> new id.
    raise NotImplementedError("write retract_and_rebuild")
