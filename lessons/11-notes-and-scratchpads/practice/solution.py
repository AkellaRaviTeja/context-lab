"""Chapter 11 reference solution: the check that decides whether a note is kept."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def number(value: Any) -> float | None:
    """A figure as a number, or None. A model may write 9, "9", 9.0 or "2,262,000.00"; None, a
    list or "n/a" is no figure."""
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
    """Why a flow cannot be kept, or None when it can."""
    if not source:
        return "a note needs its source: the file the flow was read from"
    owner = holder_of(source)
    if owner is None:
        return f"no statement named {source!r} is on file"
    if owner != payer:
        return f"{source} is the statement of {owner}, not of {payer}"
    paid = {p["payee"]: p for p in digest(source)["paid_out_to"]}
    if payee not in paid:
        return f"{source} shows no payment to {payee}"
    n, t = number(payments), number(total)
    if n is None or t is None or n != int(n):
        return "payments must be a whole number and total a figure"
    if abs(t - float(paid[payee]["total"])) > 0.005:
        return f"{source} gives {paid[payee]['total']} to {payee}, the note says {total}"
    if int(n) != paid[payee]["payments"]:
        return (f"{source} shows {paid[payee]['payments']} payments to {payee}, the note says "
                f"{payments}")
    return None
