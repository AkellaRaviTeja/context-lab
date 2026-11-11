"""Chapter 03 exercise: a budget that refuses, and names the account.

Grade it with `make exercise N=03`. The tests pass in token counts, so no model is needed.
When it passes, `make lesson N=03 ARGS=--mine` checks LANTERN's context with your function.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class OverBudget(Exception):
    """A context that must not be sent."""

    def __init__(self, account: str, spent: int, limit: int):
        self.account, self.spent, self.limit = account, spent, limit
        super().__init__(f"{account}: {spent:,} tokens against a limit of {limit:,} "
                         f"({spent - limit:,} over). Nothing was sent.")


@dataclass(frozen=True)
class Budget:
    window: int  # the model's context window, in tokens
    reserve: int  # kept back for everything the model writes
    limits: dict[str, int] = field(default_factory=dict)  # a limit for some accounts


def check(spent: dict[str, int], budget: Budget) -> int:
    """Refuse a context that is over. Returns the tokens left for input when it fits.

    `spent` maps each account to its tokens, in the order the context is sent.
    - An account over its own limit raises OverBudget(account, spent, limit). When two are
      over, the first in `spent` is named.
    - Otherwise, if the total is more than window minus reserve, raise
      OverBudget("the whole input", total, window - reserve).
    - A context exactly at a limit fits.
    """
    # TODO 1: each account against its own limit, where it has one.
    # TODO 2: the total against window - reserve.
    # TODO 3: return what is left.
    raise NotImplementedError("write check")
