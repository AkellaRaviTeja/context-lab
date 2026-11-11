"""Chapter 03 reference solution: a budget that refuses, and names the account."""

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
    window: int
    reserve: int
    limits: dict[str, int] = field(default_factory=dict)


def check(spent: dict[str, int], budget: Budget) -> int:
    """Refuse a context that is over. Returns the tokens left for input when it fits."""
    for account, tokens in spent.items():
        limit = budget.limits.get(account)
        if limit is not None and tokens > limit:
            raise OverBudget(account, tokens, limit)
    for_input = budget.window - budget.reserve
    total = sum(spent.values())
    if total > for_input:
        raise OverBudget("the whole input", total, for_input)
    return for_input - total
