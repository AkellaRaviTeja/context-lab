"""Chapter 04 exercise: read the numbered rules, and lint them for clashes.

Grade it with `make exercise N=04`. The tests pass in text, so no model is needed. When it
passes, `make lesson N=04 ARGS=--mine` lints LANTERN's standing orders with your function.
"""

from __future__ import annotations

import re

ALWAYS = ("always", "every")  # a rule containing one of these demands something
NEVER = ("never", "do not", "no ")  # a rule containing one of these forbids something


def rules(text: str) -> dict[int, str]:
    """The numbered rules of a standing-orders file: {1: "You are LANTERN...", ...}.

    A rule is a line that starts with a number, a full stop and a space. Headings, blank lines
    and unnumbered text are not rules.
    """
    # TODO 1: one regular expression with re.M, or a loop over the lines.
    raise NotImplementedError("write rules")


def clashes(numbered: dict[int, str], terms: list[str]) -> list[tuple[str, int, int]]:
    """Pairs of rules that share a term, where one says always and the other says never.

    Returns (term, demanding rule, forbidding rule) for every such pair, terms in the order
    given. Compare in lower case. A rule is never paired with itself.
    """
    # TODO 2: for each term, the rules that mention it.
    # TODO 3: split those into the ones with an ALWAYS word and the ones with a NEVER word.
    # TODO 4: every (term, a, b) with a from the first group, b from the second, a != b.
    raise NotImplementedError("write clashes")
