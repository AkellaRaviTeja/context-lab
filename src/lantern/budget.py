"""The token budget: the window as a fixed sum, spent by account, and refused when it is over.

Chapter 03 builds it. `spend()` groups the sections of a context into the accounts Okafor reads
it by, `check()` refuses a context that would not fit before it is sent, and names the account
that broke it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from lantern import context
from lantern.context import HISTORY, Section

ACCOUNTS = ("standing orders", "case memory", "standing notes", "summaries", "tool schemas",
            "session: evidence", "session: talk", "the question")


class OverBudget(Exception):
    """A context that must not be sent: it names the account and by how much it is over."""

    def __init__(self, account: str, spent: int, limit: int):
        self.account, self.spent, self.limit = account, spent, limit
        super().__init__(f"{account}: {spent:,} tokens against a limit of {limit:,} "
                         f"({spent - limit:,} over). Nothing was sent.")


@dataclass(frozen=True)
class Budget:
    """A window, the part of it kept back for the answer, and a limit for any account."""

    window: int
    reserve: int
    limits: dict[str, int] = field(default_factory=dict)

    @property
    def for_input(self) -> int:
        return self.window - self.reserve


def account_of(section: Section) -> str:
    return "summaries" if section.name.startswith("summary") else section.name


def spend(parts: list[Section], count: Callable[[str], int] = context.count_tokens
          ) -> dict[str, int]:
    """Tokens by account, in the order of ACCOUNTS. The session is split: what tools returned
    is evidence, the rest is talk."""
    out = dict.fromkeys(ACCOUNTS, 0)
    for s in parts:
        if s.where == HISTORY:
            for m in s.payload:
                key = "session: evidence" if m["role"] == "tool" else "session: talk"
                out[key] += count(context._turn(m))
        else:
            out[account_of(s)] = out.get(account_of(s), 0) + count(s.text)
    return {k: v for k, v in out.items() if v}


def check(spent: dict[str, int], budget: Budget) -> int:
    """Refuse a context that is over. Returns the tokens left for input when it fits.

    An account over its own limit is named first, in the order given; then the whole.
    """
    for account, tokens in spent.items():
        limit = budget.limits.get(account)
        if limit is not None and tokens > limit:
            raise OverBudget(account, tokens, limit)
    total = sum(spent.values())
    if total > budget.for_input:
        raise OverBudget("the whole input", total, budget.for_input)
    return budget.for_input - total
