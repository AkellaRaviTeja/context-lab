"""Chapter 12 exercise: split the memory by kind, and find what rests on nothing.

Grade it with `make exercise N=12`. The tests use LANTERN's own case memory, replayed from the
write log, so no model is needed. When it passes, `make lesson N=12 ARGS=--mine` sorts the
memory with yours.
"""

from __future__ import annotations

from collections.abc import Iterable

from lantern.memory import KINDS, Entry


def by_kind(entries: Iterable[Entry]) -> dict[str, list[Entry]]:
    """Entries split by kind.

    - Every kind in KINDS ("episode", "fact", "procedure", "summary") is a key, in that order,
      with an empty list where there is none of that kind.
    - Within a kind, entries keep the order they were given in.
    - An entry whose kind is not in KINDS raises ValueError naming the entry.
    """
    # TODO 1: start a dict with an empty list for every kind in KINDS.
    # TODO 2: append each entry to its kind's list; raise ValueError for an unknown kind.
    raise NotImplementedError("write by_kind")


def unsupported(entries: Iterable[Entry]) -> list[Entry]:
    """Every entry with nothing behind it, in the order given.

    - An episode is a record of something that happened: it must name its record (`source`).
    - A fact or a procedure must name a record (`source`), or an episode (`episode`) that is
      one of the episodes in `entries`. An episode id that is not there supports nothing.
    - A summary must name what it was built from (`derived_from`).
    - A source of only spaces is no source.
    """
    # TODO 1: collect the ids of the entries whose kind is "episode".
    # TODO 2: decide, kind by kind, whether each entry has something behind it.
    # TODO 3: return the ones that do not, in the order given.
    raise NotImplementedError("write unsupported")
