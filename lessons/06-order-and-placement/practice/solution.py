"""Chapter 06 reference solution: where the question sits, and which section sits last."""

from __future__ import annotations

from lantern.context import SYSTEM, Section


def arrange(doc: str, question: str, where: str) -> str:
    """One user turn: the question after the register, before it, or both."""
    body = "Register of accounts:\n" + doc
    if where == "after":
        return f"{body}\n\n{question}"
    if where == "before":
        return f"{question}\n\n{body}"
    if where == "both":
        return f"{question}\n\n{body}\n\n{question}"
    raise ValueError(f"where must be after, before or both, not {where!r}")


def reorder(parts: list[Section], last: str) -> list[Section]:
    """The same sections with the system section named `last` moved to the end of the system
    message. Everything else keeps its order."""
    if not any(s.name == last and s.where == SYSTEM for s in parts):
        raise ValueError(f"no system section named {last!r}")
    system = [s for s in parts if s.where == SYSTEM and s.name != last]
    moved = [s for s in parts if s.name == last]
    rest = [s for s in parts if s.where != SYSTEM]
    return [*system, *moved, *rest]
