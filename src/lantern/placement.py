"""A register of lookalike lines, for asking where in a context a fact is found.

Chapter 06 uses it. The register is made up, from a fixed seed: 140 companies that do not exist
anywhere in the case, each with an account number. One of them is asked for at a time.
"""

from __future__ import annotations

import random
from dataclasses import replace

from lantern.context import SYSTEM, Section

FIRST = ("Marlow", "Tern", "Alder", "Kelp", "Sorrel", "Dunlin", "Petrel", "Wrack", "Saltmarsh",
         "Cormorant", "Eider", "Gannet", "Linnet", "Plover", "Curlew", "Heron", "Osier", "Sedge",
         "Fulmar", "Shearwater", "Avocet", "Bittern", "Godwit", "Knot", "Sanderling", "Turnstone",
         "Whimbrel", "Redshank", "Lapwing", "Pintail")
SECOND = ("Quay", "Reach", "Point", "Wharf", "Sound", "Haven", "Bank", "Strand", "Ness", "Holm")
KIND = ("Holdings Ltd", "Trading Ltd", "Shipping Ltd", "Nominees Ltd", "Services Ltd", "Marine SA")
MONTHS = ("January", "February", "March", "April", "May")


def register(n: int = 140, seed: int = 6) -> list[tuple[str, str, str]]:
    """`n` made-up accounts as (holder, account number, the line as written)."""
    rng = random.Random(seed)
    names: list[str] = []
    while len(names) < n:
        name = f"{rng.choice(FIRST)} {rng.choice(SECOND)} {rng.choice(KIND)}"
        if name not in names:
            names.append(name)
    out = []
    for name in names:
        number = (f"{rng.choice(('MTB', 'ICB', 'HDB', 'SMB'))}-{rng.randint(10, 99)}-"
                  f"{rng.randint(10000, 99999)}")
        opened = f"{rng.randint(1, 28)} {rng.choice(MONTHS)} 2026"
        out.append((name, number, f"- {name}: account {number}, opened {opened}."))
    return out


def question_for(holder: str) -> str:
    return f"What is the account number of {holder}? Reply with the account number alone."


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
    message, nearest the conversation."""
    if not any(s.name == last and s.where == SYSTEM for s in parts):
        raise ValueError(f"no system section named {last!r}")
    system = [s for s in parts if s.where == SYSTEM and s.name != last]
    moved = [replace(s) for s in parts if s.name == last]
    rest = [s for s in parts if s.where != SYSTEM]
    return [*system, *moved, *rest]
