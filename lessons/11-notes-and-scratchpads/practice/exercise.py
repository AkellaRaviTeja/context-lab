"""Chapter 11 exercise: the check that decides whether a note is kept.

Grade it with `make exercise N=11`. The tests pass in a statement's digest and its holder as
plain functions, so no model is needed. When it passes, `make lesson N=11 ARGS=--mine` runs
every note LANTERN writes through yours.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def number(value: Any) -> float | None:
    """A figure as a number, or None. A model may write 9, "9", 9.0 or "2,262,000.00"; None, a
    list or "n/a" is no figure. (Written for you: chapter 10's exercise.)"""
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").strip())
        except ValueError:
            return None
    return None


def problem_with(payer: str, payee: str, payments: Any, total: Any, source: str, *,
                 digest: Callable[[str], dict[str, Any]],
                 holder_of: Callable[[str], str | None]) -> str | None:
    """Why a flow cannot be kept, or None when it can.

    LANTERN calls note_flow(payer, payee, payments, total, source); the notebook keeps the
    note only when this returns None. `holder_of(file)` is the account holder of a statement,
    or None when no statement by that name is on file. `digest(file)` is what the statement
    tool returns: {"statement", "holder", "paid_out_to": [{"payee", "payments", "total"}]},
    with total a string such as "2262000.00".

    The first check that fails is the reason, in this order:

    - "a note needs its source: the file the flow was read from"    source is empty
    - "no statement named 'x.csv' is on file"                       (the name with !r)
    - "x.csv is the statement of H, not of P"                       the payer is not its holder
    - "x.csv shows no payment to B"                                 the digest has no such payee
    - "payments must be a whole number and total a figure"          9.5, None, "n/a", a list
    - "x.csv gives T to B, the note says t"                         totals differ by more than
                                                                    half a penny, as numbers
    - "x.csv shows N payments to B, the note says n"                counts differ
    """
    # TODO 1: no source, then a source with no holder, then a holder who is not the payer.
    # TODO 2: index the digest's paid_out_to by payee; a payee it does not hold is refused.
    # TODO 3: read payments and total with number(); refuse what is not a figure, and a count
    #         that is not whole.
    # TODO 4: compare the total, then the count, with the digest's. Return None when all agree.
    raise NotImplementedError("write problem_with")
