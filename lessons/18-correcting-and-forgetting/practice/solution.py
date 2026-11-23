"""Chapter 18 reference solution: retract, then rebuild everything built on what was retracted."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from lantern.memory import Entry, Store

Rebuild = Callable[[Entry, list[Entry]], str]


def retract_and_rebuild(store: Store, ids: Iterable[str], *, by: str, at: str, reason: str,
                        rebuild: Rebuild) -> dict[str, str]:
    """Retract `ids`; rebuild, oldest first, every live entry built on them."""
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
