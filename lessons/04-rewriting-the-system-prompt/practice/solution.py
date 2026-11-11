"""Chapter 04 reference solution: read the numbered rules, and lint them for clashes."""

from __future__ import annotations

import re

ALWAYS = ("always", "every")
NEVER = ("never", "do not", "no ")


def rules(text: str) -> dict[int, str]:
    """The numbered rules of a standing-orders file: {1: "You are LANTERN...", ...}."""
    return {int(n): body for n, body in re.findall(r"^(\d+)\. (.+)$", text, re.M)}


def clashes(numbered: dict[int, str], terms: list[str]) -> list[tuple[str, int, int]]:
    """Pairs of rules that share a term, where one says always and the other says never."""
    found = []
    for term in terms:
        has = [(n, body.lower()) for n, body in numbered.items() if term.lower() in body.lower()]
        yes = [n for n, body in has if any(w in body for w in ALWAYS)]
        no = [n for n, body in has if any(w in body for w in NEVER)]
        found += [(term, a, b) for a in yes for b in no if a != b]
    return found
