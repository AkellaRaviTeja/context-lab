"""Chapter 12 reference solution: split the memory by kind, and find what rests on nothing."""

from __future__ import annotations

from collections.abc import Iterable

from lantern.memory import KINDS, Entry


def by_kind(entries: Iterable[Entry]) -> dict[str, list[Entry]]:
    """Entries split by kind: every kind in KINDS a key, in order, empty where none."""
    out: dict[str, list[Entry]] = {k: [] for k in KINDS}
    for e in entries:
        if e.kind not in out:
            raise ValueError(f"{e.id}: unknown kind {e.kind!r}")
        out[e.kind].append(e)
    return out


def unsupported(entries: Iterable[Entry]) -> list[Entry]:
    """Every entry with nothing behind it, in the order given."""
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
